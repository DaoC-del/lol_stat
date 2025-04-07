import sys
import asyncio
import logging
import threading
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from lcu_driver import Connector
from web.lcu_client import get_current_summoner, fetch_match_history

logger = logging.getLogger(__name__)

class APICallWorker(QObject):
    resultReady = pyqtSignal(object)
    errorOccurred = pyqtSignal(str)

    def __init__(self, api_type, parent=None, timeout=5):
        """
        :param api_type: "summoner" 或 "match_history"
        :param timeout: 超时时间（秒）
        """
        super().__init__(parent)
        self.api_type = api_type
        self.timeout = timeout  # 单位：秒
        self.connector = None  # 延迟创建
        self._cancelled = False

    async def connect_callback(self, connection):
        if self._cancelled:
            return  # 超时已取消，不再处理后续操作
        try:
            if self.api_type == "summoner":
                summoner, puuid = await get_current_summoner(connection)
                if not self._cancelled:
                    self.resultReady.emit(summoner)
            elif self.api_type == "match_history":
                summoner, puuid = await get_current_summoner(connection)
                games = await fetch_match_history(connection, puuid)
                if not self._cancelled:
                    self.resultReady.emit(games)
            else:
                if not self._cancelled:
                    self.resultReady.emit({"error": "未知的 API 类型"})
        except Exception as e:
            error_msg = f"API 调用异常: {str(e)}"
            logger.error(error_msg)
            if not self._cancelled:
                self.errorOccurred.emit(error_msg)
        finally:
            await self.connector.stop()

    def run(self):
        # 在当前线程中创建并设置事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.connector = Connector(loop=loop)
        self.connector.ready(self.connect_callback)
        self._cancelled = False

        # 将 connector.start() 放入一个子线程中运行
        start_thread = threading.Thread(target=self.connector.start)
        start_thread.start()
        # 等待规定的超时时间
        start_thread.join(timeout=self.timeout)
        if start_thread.is_alive():
            # 超时后认为未找到 Lol 进程，标记取消
            self._cancelled = True
            error_msg = f"Timeout: Lol process not found within {self.timeout} seconds"
            logger.error(error_msg)
            self.errorOccurred.emit(error_msg)
            try:
                self.stop_connector_sync()
            except Exception as e:
                logger.error(f"Error stopping connector: {e}")
            # 发出一个完成信号，返回 None 表示无数据
            self.resultReady.emit(None)

    def stop_connector_sync(self):
        """同步停止 Connector（用于超时情况）"""
        if self.connector is not None:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.connector.stop(), self.connector.loop
                )
                future.result(timeout=2)
                logger.info("Connector has been force-stopped.")
            except Exception as e:
                logger.error(f"Error stopping connector: {e}")

class APICallThread(QThread):
    def __init__(self, api_type, parent=None):
        super().__init__(parent)
        self.worker = APICallWorker(api_type)

    def run(self):
        self.worker.run()
