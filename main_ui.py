# main_ui.py
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QTextEdit
from worker import ConnectorThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LCU API UI")
        self.resize(600, 400)
        
        # 用于显示召唤师数据和比赛记录
        self.summonerLabel = QLabel("召唤师数据：等待中...")
        self.matchHistoryEdit = QTextEdit("比赛记录：等待中...")
        self.matchHistoryEdit.setReadOnly(True)
        
        layout = QVBoxLayout()
        layout.addWidget(self.summonerLabel)
        layout.addWidget(self.matchHistoryEdit)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 启动后台连接线程
        self.connectorThread = ConnectorThread()
        # 连接信号
        self.connectorThread.worker.summonerDataReady.connect(self.updateSummonerData)
        self.connectorThread.worker.matchHistoryReady.connect(self.updateMatchHistory)
        self.connectorThread.start()

    def updateSummonerData(self, data):
        # 在 UI 上显示召唤师数据
        self.summonerLabel.setText(f"召唤师数据：{data}")

    def updateMatchHistory(self, games):
        # 在 UI 上显示比赛记录，这里简单显示比赛数量
        self.matchHistoryEdit.setPlainText(f"获取到 {len(games)} 条比赛记录")
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
