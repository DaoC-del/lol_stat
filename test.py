import asyncio
from lcu_driver import Connector
from web.lcu_client import fetch_and_store_history

connector = Connector()

@connector.ready
async def on_ready(connection):
    print("[LCU] Connected to client. Starting match fetch and store test...")
    await fetch_and_store_history(connection, page_index=0, page_size=5)
    print("[✅] All match records processed.")
    await connector.stop()

connector.start()
