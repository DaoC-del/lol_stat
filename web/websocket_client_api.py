# websocket_client_api.py（完整保留：线程封装、API 调用、数据库落库、批量入库）

from PyQt5.QtCore import QThread, QEventLoop
import logging
import concurrent.futures
from web.websocket_client_worker import APICallWorker
from web.match_storage import connect_mysql, insert_match_json
from lcu_driver import Connector
from web.lcu_client import fetch_and_store_history

class APICallThread(QThread):
    def __init__(self, api_name: str, api_params: dict = None, parent=None):
        super().__init__(parent)
        self.api_name = api_name
        self.api_params = api_params or {}
        self.worker = APICallWorker(self.api_name, self.api_params)

    def run(self):
        logging.info(f"{self.api_name}: 工作线程开始执行")
        self.worker.run()

def call_api(api_name: str, api_params: dict = None):
    thread = APICallThread(api_name, api_params)
    loop = QEventLoop()
    result = {}

    def handle_result(data):
        result["data"] = data
        loop.quit()

    thread.worker.resultReady.connect(handle_result)
    thread.start()
    loop.exec_()
    return result.get("data")

def call_api_paginated(
    api_name: str,
    total_range=(0, 300),
    page_size=30,
    max_workers=3,
    progress_callback=None,
    status_callback=None
):
    start, end = total_range
    total_pages = (end - start + page_size - 1) // page_size
    results = []

    def fetch_page(index):
        if status_callback:
            status_callback(f"Fetching page {index + 1}/{total_pages}...")
        page_data = call_api(api_name, {"page_index": index, "page_size": page_size})
        if progress_callback:
            progress_callback(index + 1, total_pages)
        if status_callback:
            status_callback(f"Fetched {len(page_data)} items from page {index + 1}")
        return page_data

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_page, i) for i in range(total_pages)]
        for future in concurrent.futures.as_completed(futures):
            page_data = future.result()
            if page_data:
                results.extend(page_data)

    return results

def call_summoner():
    return call_api("summoner")

def call_match_history():
    return call_api("match_history", {"page_index": 0, "page_size": 30})

def call_match_history_paginated(progress_callback=None, status_callback=None):
    return call_api_paginated(
        "match_history",
        total_range=(0, 300),
        page_size=30,
        max_workers=3,
        progress_callback=progress_callback,
        status_callback=status_callback
    )

def store_match_detail(match_json):
    conn = connect_mysql()
    insert_match_json(match_json, conn)
    conn.close()

# 自动分页拉取并入库（用于 API3）
def call_match_history_and_store():
    connector = Connector()

    @connector.ready
    async def on_ready(connection):
        for page_index in range(5):  # 拉取前 5 页
            await fetch_and_store_history(connection, page_index=page_index, page_size=30)
        await connector.stop()

    connector.start()
