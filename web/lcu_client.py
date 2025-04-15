# lcu_client.py
import asyncio
import pandas as pd
from rich.progress import Progress, SpinnerColumn, BarColumn, TimeElapsedColumn
from rich.console import Console

console = Console()

async def fetch_match_history_page(conn, puuid: str, page_index: int, page_size: int = 30):
    beg_index = page_index * page_size
    end_index = beg_index + page_size

    resp = await conn.request(
        'GET',
        f'/lol-match-history/v1/products/lol/{puuid}/matches',
        params={'begIndex': beg_index, 'endIndex': end_index}  # ✅ 修复拼写
    )

    try:
        json_data = await resp.json()
        return json_data.get('games', {}).get('games', [])
    except Exception as e:
        print(f"Failed to parse match history: {e}")
        return []

async def get_current_summoner(conn):
    summ = await (await conn.request('GET','/lol-summoner/v1/current-summoner')).json()
    name = summ.get('displayName') or summ.get('summonerName') or summ.get('summonerId')
    puuid = summ.get('puuid')
    
    print(f"[DEBUG] Summoner info: name={name}, puuid={puuid}")
    
    return summ, puuid

async def get_current_game_phase(conn):
    phase = await (await conn.request('GET','/lol-gameflow/v1/gameflow-phase')).json()
    if phase != 'None':
        session = await (await conn.request('GET','/lol-champ-select/v1/session')).json()
        return session
    return "No current game"
