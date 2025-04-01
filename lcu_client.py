# lcu_client.py
import asyncio
import pandas as pd
from rich.progress import Progress, SpinnerColumn, BarColumn, TimeElapsedColumn
from rich.console import Console

console = Console()

async def fetch_match_history(conn, puuid):
    all_games = []
    beg, page = 0, 100
    with Progress(SpinnerColumn(), BarColumn(), TimeElapsedColumn(), console=console) as prog:
        task = prog.add_task("Fetching match history…", total=None)
        while True:
            resp = await conn.request('GET', f'/lol-match-history/v1/products/lol/{puuid}/matches',
                                       params={'begIndex': beg, 'endIndex': beg+page})
            games = (await resp.json()).get('games', {}).get('games', [])
            if not games:
                break
            all_games.extend(games)
            prog.advance(task, len(games))
            if len(games) < page:
                break
            beg += page
    return all_games

async def get_current_summoner(conn):
    summ = await (await conn.request('GET','/lol-summoner/v1/current-summoner')).json()
    name = summ.get('displayName') or summ.get('summonerName') or summ.get('summonerId')
    puuid = summ['puuid']
    console.print(f"Logged in as [bold cyan]{name}[/]")
    return summ, puuid

async def get_current_game_phase(conn):
    phase = await (await conn.request('GET','/lol-gameflow/v1/gameflow-phase')).json()
    if phase != 'None':
        session = await (await conn.request('GET','/lol-champ-select/v1/session')).json()
        return session
    return "No current game"
