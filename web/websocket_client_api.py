from PyQt5.QtCore import QThread, QEventLoop
from web.websocket_client_worker import APICallWorker
import logging


class APICallThread(QThread):
    def __init__(self, api_name: str, api_params: dict = None, parent=None):
        super().__init__(parent)
        self.api_name = api_name
        self.api_params = api_params or {}
        print(f"[DEBUG] Initializing APICallThread with api_name={self.api_name}")
        self.worker = APICallWorker(self.api_name, self.api_params)

    def run(self):
        logging.info(f"{self.api_name}: 工作线程开始执行，触发 call_api")
        self.worker.run()


def call_api(api_name: str, api_params: dict = None):
    print(f"[DEBUG] call_api invoked with api_name={api_name}")
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


def call_api_paginated(api_name: str, total_range=(0, 300), page_size=30):
    start, end = total_range
    total_pages = (end - start + page_size - 1) // page_size
    results = []

    for page_index in range(total_pages):
        params = {"page_index": page_index, "page_size": page_size}
        print(f"[DEBUG] call_api_paginated: dispatch page_index={page_index}")
        thread = APICallThread(api_name, api_params=params)
        loop = QEventLoop()
        result = {}

        def handle_result(data):
            result["data"] = data
            loop.quit()

        thread.worker.resultReady.connect(handle_result)
        thread.start()
        loop.exec_()

        if result.get("data"):
            results.extend(result["data"])

    return results


def call_summoner():
    return call_api("summoner")


def call_match_history():
    return call_api("match_history", {"page_index": 0, "page_size": 30})
