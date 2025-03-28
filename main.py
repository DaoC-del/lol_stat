from lcu_driver import Connector
import pandas as pd
import logging
import requests
import asyncio
from sqlalchemy import create_engine, inspect, text
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TimeElapsedColumn
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
console = Console()
connector = Connector()

# Database connection (MySQL in Docker)
DB_URL = "mysql+mysqlconnector://lol_user:lol_pass@127.0.0.1:3306/lol_stats"
engine = create_engine(DB_URL)

# Load external mappings
def load_queue_map():
    try:
        resp = requests.get('https://static.developer.riotgames.com/docs/lol/queues.json', timeout=5)
        resp.raise_for_status()
        return {item['queueId']: item['description'] for item in resp.json()}
    except Exception:
        logging.warning("Using fallback queue map.")
        return {420: 'Ranked Solo', 450: 'ARAM', 1700: 'Ascension'}

def load_champion_map():
    try:
        data = requests.get("https://ddragon.leagueoflegends.com/cdn/15.6.1/data/en_US/champion.json", timeout=5).json()['data']
        return {int(v['key']): v['name'] for v in data.values()}
    except Exception:
        logging.warning("Failed to load champion map.")
        return {}

async def fetch_match_history(conn, puuid):
    all_games = []
    beg, page = 0, 100
    with Progress(SpinnerColumn(), BarColumn(), TimeElapsedColumn(), console=console) as prog:
        task = prog.add_task("Fetching match history…", total=None)
        while True:
            resp = await conn.request('GET', f'/lol-match-history/v1/products/lol/{puuid}/matches', params={'begIndex': beg, 'endIndex': beg+page})
            games = (await resp.json()).get('games', {}).get('games', [])
            if not games:
                break
            all_games.extend(games)
            prog.advance(task, len(games))
            if len(games) < page:
                break
            beg += page
    return all_games

async def connect(connection):
    summ = await (await connection.request('GET','/lol-summoner/v1/current-summoner')).json()
    name = summ.get('displayName') or summ.get('summonerName') or summ.get('summonerId')
    console.print(f"Logged in as [bold cyan]{name}[/]")
    puuid = summ['puuid']

    queue_map = load_queue_map()
    champ_map = load_champion_map()
    cached = None

    console.print("Commands: all, solo, aram, duel, status, clear, current, quit")
    while True:
        choice = await asyncio.get_event_loop().run_in_executor(None, input, ">>> ")
        if choice == 'quit': break

        if choice in ('all','solo','aram','duel'):
            if cached is None:
                games = await fetch_match_history(connection, puuid)
                if not games:
                    console.print("No match history found.")
                    continue
                df_game = pd.json_normalize(games)
                df_game['matchType'] = df_game['queueId'].map(queue_map).fillna('Unknown')
                nested_cols = [c for c in df_game.columns if isinstance(df_game.iloc[0].get(c), list)]
                df_game_clean = df_game.drop(columns=nested_cols)
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
                            'championName': champ_map.get(champ_id),
                            **stats
                        })
                df_part = pd.DataFrame(records)
                cached = {'game': df_game_clean, 'participants': df_part}

            df = cached['participants'].merge(cached['game'][['gameId','matchType']], on='gameId')
            if choice=='solo': df = df[df['matchType']==queue_map.get(420)]
            if choice=='aram': df = df[df['matchType']==queue_map.get(450)]
            if choice=='duel': df = df[df['matchType']==queue_map.get(1700)]
            if df.empty:
                console.print(f"No records for '{choice}'.")
                continue
            for name, df_ent in cached.items():
                out = df_ent[df_ent['gameId'].isin(df['gameId'].unique())]
                out.to_sql(name, engine, if_exists='append', index=False)
                console.print(f"✅ Inserted {len(out)} rows into '{name}' table")

        elif choice == 'status':
            inspector = inspect(engine)
            for tbl in inspector.get_table_names():
                count = pd.read_sql(f"SELECT COUNT(*) AS cnt FROM `{tbl}`", engine)['cnt'][0]
                console.print(f"{tbl}: {count:,} rows")

        elif choice == 'clear':
            inspector = inspect(engine)
            with engine.begin() as conn:
                for tbl in inspector.get_table_names():
                    conn.execute(text(f"TRUNCATE TABLE `{tbl}`"))
                    console.print(f"✅ Cleared '{tbl}'")

        elif choice == 'current':
            phase = await (await connection.request('GET','/lol-gameflow/v1/gameflow-phase')).json()
            if phase!='None': console.print(await (await connection.request('GET','/lol-champ-select/v1/session')).json())
            else: console.print("No current game")

        else:
            console.print("Unknown command — try again.")

    await connector.stop()

connector.ready(connect)
connector.start()
