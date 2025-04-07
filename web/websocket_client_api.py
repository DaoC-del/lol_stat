import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEventLoop, QTimer
from .websocket_client_worker import APICallThread

logger = logging.getLogger(__name__)

def call_summoner():
    """
    调用召唤师数据接口，如果 Lol 进程未启动则在超时后返回 None。
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    thread = APICallThread("summoner")
    result = {"data": None}

    def on_result(data):
        result["data"] = data
        logger.info(f"召唤师数据已接收: {data}")

    thread.worker.resultReady.connect(on_result)
    thread.worker.errorOccurred.connect(on_result)
    thread.start()

    loop = QEventLoop()
    thread.worker.resultReady.connect(loop.quit)
    thread.worker.errorOccurred.connect(loop.quit)
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(int(thread.worker.timeout * 1000))
    loop.exec_()
    timer.stop()
    thread.quit()
    thread.wait()
    return result["data"]

def call_match_history():
    """
    调用比赛记录接口，如果 Lol 进程未启动则在超时后返回 None。
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    thread = APICallThread("match_history")
    result = {"data": None}

    def on_result(data):
        result["data"] = data
        logger.info(f"比赛记录已接收: {data}")

    thread.worker.resultReady.connect(on_result)
    thread.worker.errorOccurred.connect(on_result)
    thread.start()

    loop = QEventLoop()
    thread.worker.resultReady.connect(loop.quit)
    thread.worker.errorOccurred.connect(loop.quit)
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(int(thread.worker.timeout * 1000))
    loop.exec_()
    timer.stop()
    thread.quit()
    thread.wait()
    return result["data"]

def call_api(api_name, timeout=5):
    """
    根据 api_name 分发调用：
      - "api1" 调用召唤师数据接口
      - "api2" 调用比赛记录接口
    """
    if api_name == "api1":
        return call_summoner()
    elif api_name == "api2":
        return call_match_history()
    else:
        return {"status": "error", "api": api_name, "data": "未知的 API 调用"}
