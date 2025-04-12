import asyncio
import logging
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QEventLoop
from lcu_driver import Connector
from lcu_driver.connection import Connection
from web.lcu_client import fetch_match_history_page, get_current_summoner


class APICallWorker(QObject):
    resultReady = pyqtSignal(object)

    def __init__(self, api_type: str, api_params: dict = None, timeout=5):
        super().__init__()
        self.api_type = api_type
        self.api_params = api_params or {}
        self.timeout = timeout
        self._cancelled = False
        self.response = {"data": None}
        self.connector = None
        print(f"[DEBUG] APICallWorker initialized with api_type={self.api_type}")

    def cancel(self):
        self._cancelled = True

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.connector = Connector(loop=loop)
        self.connector.ready(self._connect_callback)
        self._cancelled = False

        try:
            self.connector.start()
        except Exception as e:
            print(f"[ERROR] connector.start() failed: {e}")
            self.resultReady.emit(self.response)

    async def _connect_callback(self, connection: Connection):
        print(f"[DEBUG] API type dispatched: {self.api_type}")
        try:
            if self.api_type == "match_history":
                print(f"[DEBUG] match_history branch entered")
                summoner, puuid = await get_current_summoner(connection)
                print(f"[DEBUG] summoner: {summoner.get('displayName')}, puuid: {puuid}")

                page_index = self.api_params.get("page_index", 0)
                page_size = self.api_params.get("page_size", 30)

                games = await fetch_match_history_page(connection, puuid, page_index, page_size)
                print(f"[DEBUG] fetched {len(games)} games")

                if not self._cancelled:
                    self.response = {"data": games}
                    print(f"[DEBUG] Emitting resultReady with data: {self.response}")
                    self.resultReady.emit(self.response)

            elif self.api_type == "summoner":
                print(f"[DEBUG] summoner branch entered")
                summoner, puuid = await get_current_summoner(connection)
                print(f"[DEBUG] summoner: {summoner.get('displayName')}, puuid: {puuid}")
                if not self._cancelled:
                    self.response = {"data": summoner}
                    print(f"[DEBUG] Emitting resultReady with data: {self.response}")
                    self.resultReady.emit(self.response)

        except Exception as e:
            print(f"[ERROR] Exception during API call: {e}")
            self.resultReady.emit(self.response)
        finally:
            await self.connector.stop()


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
