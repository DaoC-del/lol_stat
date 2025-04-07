# commands.py
import asyncio
import pandas as pd
from lcu_driver import Connector
from rich.console import Console
from config.config import engine
from data.db import insert_data, show_status, clear_tables
from web.mappings import load_queue_map, load_champion_map
from web.lcu_client import fetch_match_history, get_current_summoner, get_current_game_phase

console = Console()
connector = Connector()

async def process_commands(connection):
    summ, puuid = await get_current_summoner(connection)
    queue_map = load_queue_map()
    champ_map = load_champion_map()
    cached = None

    console.print("Commands: all, solo, aram, duel, status, clear, current, quit")
    while True:
        choice = await asyncio.get_event_loop().run_in_executor(None, input, ">>> ")
        if choice == 'quit':
            break

        if choice in ('all', 'solo', 'aram', 'duel'):
            if cached is None:
                games = await fetch_match_history(connection, puuid)
                if not games:
                    console.print("No match history found.")
                    continue

                df_game = pd.json_normalize(games)
                df_game['matchType'] = df_game['queueId'].map(queue_map).fillna('Unknown')
                # 去掉嵌套的列
                nested_cols = [c for c in df_game.columns if isinstance(df_game.iloc[0].get(c), list)]
                df_game_clean = df_game.drop(columns=nested_cols)

                records = []
                for game in games:
                    for ident in game.get('participantIdentities', []):
                        pid = ident['participantId']
                        stats = next((p['stats'] for p in game['participants'] if p['participantId'] == pid), {})
                        champ_id = next((p['championId'] for p in game['participants'] if p['participantId'] == pid), None)
                        records.append({
                            'gameId': game['gameId'],
                            'summonerName': ident['player'].get('gameName'),
                            'championId': champ_id,
                            'championName': champ_map.get(champ_id),
                            **stats
                        })
                df_part = pd.DataFrame(records)
                cached = {'game': df_game_clean, 'participants': df_part}

            df = cached['participants'].merge(cached['game'][['gameId', 'matchType']], on='gameId')
            if choice == 'solo': 
                df = df[df['matchType'] == queue_map.get(420)]
            elif choice == 'aram': 
                df = df[df['matchType'] == queue_map.get(450)]
            elif choice == 'duel': 
                df = df[df['matchType'] == queue_map.get(1700)]
                
            if df.empty:
                console.print(f"No records for '{choice}'.")
                continue

            # 根据不同的数据表分别插入
            for name, df_ent in cached.items():
                out = df_ent[df_ent['gameId'].isin(df['gameId'].unique())]
                insert_data(name, out)

        elif choice == 'status':
            show_status()

        elif choice == 'clear':
            clear_tables()

        elif choice == 'current':
            session = await get_current_game_phase(connection)
            console.print(session)

        else:
            console.print("Unknown command — try again.")

async def connect(connection):
    await process_commands(connection)
    await connector.stop()

def run():
    connector.ready(connect)
    connector.start()
