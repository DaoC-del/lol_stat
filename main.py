from lcu_driver import Connector
import pandas as pd
import logging
import requests
import asyncio
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TimeElapsedColumn
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
console = Console()
connector = Connector()


def load_queue_map() -> dict[int, str]:
    """Fetch queueId→description mapping from Riot's static queues.json."""
    url = 'https://static.developer.riotgames.com/docs/lol/queues.json'
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return {item['queueId']: item['description'] for item in resp.json()}
    except Exception:
        logging.warning("Failed to load queue map, using fallback.")
        return {420: 'Ranked Solo', 450: 'ARAM', 1700: 'Ascension', 430: 'Normal', 900: 'URF'}


def load_champion_map(version: str = "15.6.1") -> dict[int, str]:
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return {int(v['key']): v['name'] for v in resp.json().get('data', {}).values()}
    except Exception:
        logging.warning("Failed to load champion map.")
        return {}


async def fetch_match_history(connection, puuid):
    all_games = []
    beg, page = 0, 100
    with Progress(SpinnerColumn(), BarColumn(), TimeElapsedColumn(), console=console) as prog:
        task = prog.add_task("Fetching match history…", total=None)
        while True:
            resp = await connection.request('GET', f'/lol-match-history/v1/products/lol/{puuid}/matches', params={'begIndex': beg, 'endIndex': beg+page})
            data = await resp.json()
            page_list = data.get('games', {}).get('games', [])
            if not page_list:
                break
            all_games.extend(page_list)
            prog.advance(task, len(page_list))
            if len(page_list) < page:
                break
            beg += page
    return all_games


async def connect(connection):
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)

    summ = await (await connection.request('GET', '/lol-summoner/v1/current-summoner')).json()
    name = summ.get('displayName') or summ.get('summonerName') or summ.get('summonerId')
    console.print(f"Logged in as [bold cyan]{name}[/]")
    puuid = summ['puuid']

    queue_map = load_queue_map()
    champ_map = load_champion_map()
    cached = None

    console.print("Available commands: all, solo, aram, duel, current, quit")
    while True:
        choice = await asyncio.get_event_loop().run_in_executor(None, input, ">>> ")
        if choice == 'quit':
            break

        if choice in ('all','solo','aram','duel'):
            if cached is None:
                games = await fetch_match_history(connection, puuid)
                if not games:
                    console.print("No match history found.")
                    continue
                df_game = pd.json_normalize(games)
                df_game['matchType'] = df_game['queueId'].map(queue_map).fillna('Unknown')
                records = []
                for game in games:
                    for ident in game.get('participantIdentities', []):
                        pid = ident['participantId']
                        stats = next((p['stats'] for p in game['participants'] if p['participantId']==pid), {})
                        champ_id = next((p['championId'] for p in game['participants'] if p['participantId']==pid), None)
                        records.append({
                            'gameId': game['gameId'],
                            'summonerName': ident['player'].get('gameName'),
                            'championId': champ_id,
                            'championName': champ_map.get(champ_id, champ_id),
                            **stats
                        })
                df_part = pd.DataFrame(records)
                cached = {'game': df_game, 'participants': df_part}

            df = cached['participants'].merge(cached['game'][['gameId','matchType']], on='gameId')
            if choice=='solo': df = df[df['matchType']==queue_map.get(420)]
            if choice=='aram': df = df[df['matchType']==queue_map.get(450)]
            if choice=='duel': df = df[df['matchType']==queue_map.get(1700)]

            if df.empty:
                console.print(f"No records for '{choice}'.")
                continue

            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            for name, df_ent in cached.items():
                out = df_ent[df_ent['gameId'].isin(df['gameId'].unique())]
                path = data_dir / f"{ts}_{choice}_{name}.csv"
                out.to_csv(path, index=False)
                console.print(f"Saved {name} → {path}")

        elif choice=='current':
            phase = await (await connection.request('GET','/lol-gameflow/v1/gameflow-phase')).json()
            if phase!='None':
                console.print(await (await connection.request('GET','/lol-champ-select/v1/session')).json())
            else:
                console.print("未找到当前对局")
        else:
            console.print("Unknown command — try again.")

    await connector.stop()

connector.ready(connect)
connector.start()
