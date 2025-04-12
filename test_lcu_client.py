import asyncio
from lcu_driver import Connector
from web.lcu_client import get_current_summoner, fetch_match_history_page

connector = Connector()

@connector.ready
async def on_ready(connection):
    print("[READY] Connected to LCU API")

    try:
        summoner, puuid = await get_current_summoner(connection)
        print(f"[TEST] Summoner: {summoner.get('displayName')}, PUUID: {puuid}")

        page_index = 0
        page_size = 20

        games = await fetch_match_history_page(connection, puuid, page_index, page_size)
        print(f"[TEST] Fetched {len(games)} games:")
        for g in games[:3]:
            print(f"  - gameId: {g.get('gameId')}")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
    finally:
        await connector.stop()

async def main():
    await connector.start()

if __name__ == "__main__":
    asyncio.run(main())
