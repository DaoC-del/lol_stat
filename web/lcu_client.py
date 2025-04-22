# lcu_client.py（集成容错 match detail 获取 + 插入流程）

import asyncio
from datetime import datetime
from web.match_storage import connect_mysql, insert_match_json
from rich.console import Console

console = Console()

async def fetch_match_history_page(conn, puuid: str, page_index: int, page_size: int = 30):
    beg_index = page_index * page_size
    end_index = beg_index + page_size

    resp = await conn.request(
        'GET',
        f'/lol-match-history/v1/products/lol/{puuid}/matches',
        params={'begIndex': beg_index, 'endIndex': end_index}
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

# ----------------- 新增功能: 实体化 match detail -----------------

async def fetch_match_detail(conn, fallback_summary: dict):
    game_id = fallback_summary.get("gameId")
    print(f'{game_id}')
    try:
        resp = await conn.request('GET', f'/lol-match-history/v1/games/{game_id}')
        detail = await resp.json()

        if all(k in detail for k in ["participants", "teams", "participantIdentities"]):
            print(f"[INFO] Loaded match {game_id} from /games")
            detail["__fallback"] = False
            print(f'{detail}')
            return detail
        else:
            print(f"[WARN] Incomplete detail for match {game_id}, using fallback.")
    except Exception as e:
        print(f"[ERROR] Failed to fetch match {game_id} detail: {e}")

    fallback_summary["__fallback"] = True
    return fallback_summary

# ----------------- 清洁化接口: 批量获取并入库 -----------------

async def fetch_and_store_history(conn, page_index=0, page_size=30):
    summoner, puuid = await get_current_summoner(conn)
    match_list = await fetch_match_history_page(conn, puuid, page_index, page_size)
    
    db = connect_mysql()
    for summary in match_list:
        detail = await fetch_match_detail(conn, summary)
        is_fallback = detail.get("__fallback", False)
        insert_match_json(detail, db, is_fallback=is_fallback)
    db.close()
