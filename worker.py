# worker.py 部分修改（或单独编写一个 API 调用的异步方法）
import asyncio
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from lcu_driver import Connector
from lcu_client import get_current_summoner, fetch_match_history

class ConnectorWorker(QObject):
    # 用于通知 UI 层获取到召唤师数据和比赛记录
    summonerDataReady = pyqtSignal(dict)
    matchHistoryReady = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.connector = Connector()

    async def connect_callback(self, connection):
        # 连接成功后，先获取召唤师数据
        summoner, puuid = await get_current_summoner(connection)
        # 通过信号传递召唤师数据给 UI
        self.summonerDataReady.emit(summoner)
        
        # 获取战绩数据
        games = await fetch_match_history(connection, puuid)
        # 通过信号传递比赛记录给 UI
        self.matchHistoryReady.emit(games)
        
        # 当 API 调用完成后可以根据需求停止连接
        await self.connector.stop()

    def run(self):
        # 注册 ready 回调，并直接调用 connector.start()（在独立线程中运行）
        self.connector.ready(self.connect_callback)
        self.connector.start()

class ConnectorThread(QThread):
    def __init__(self):
        super().__init__()
        self.worker = ConnectorWorker()

    def run(self):
        self.worker.run()
