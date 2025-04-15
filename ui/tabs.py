from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal
import logging
from web.websocket_client_api import call_summoner, call_match_history_paginated


class APIFetchWorker(QThread):
    finished = pyqtSignal(object)
    errorOccurred = pyqtSignal(str)
    progressUpdated = pyqtSignal(int, int)  # current, total
    statusMessage = pyqtSignal(str)

    def __init__(self, api_name: str):
        super().__init__()
        self.api_name = api_name

    def run(self):
        logging.info(f"{self.api_name}: 子线程开始执行")
        try:
            if self.api_name == "api1":
                data = call_summoner()
                result = {"status": "success", "api": self.api_name, "data": data}
            elif self.api_name == "api2":
                data = call_match_history_paginated(
                    progress_callback=self.progressUpdated.emit,
                    status_callback=self.statusMessage.emit
                )
                result = {"status": "success", "api": self.api_name, "data": data}
            else:
                raise ValueError(f"Unknown API name: {self.api_name}")
            self.finished.emit(result)
        except Exception as e:
            msg = f"{self.api_name}: API 调用失败: {str(e)}"
            self.errorOccurred.emit(msg)
            self.finished.emit({"status": "fail", "api": self.api_name, "data": None})


class APITab(QWidget):
    def __init__(self, api_name: str):
        super().__init__()
        self.api_name = api_name

        self.layout = QVBoxLayout(self)

        self.fetch_button = QPushButton(f"Fetch {self.api_name}")
        self.fetch_button.clicked.connect(self.fetch_data)
        self.layout.addWidget(self.fetch_button)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.layout.addWidget(self.output)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

    def fetch_data(self):
        logging.info(f"{self.api_name}: 开始任务")
        self.fetch_button.setEnabled(False)
        self.output.append("Fetching...")

        self.worker = APIFetchWorker(self.api_name)
        self.worker.finished.connect(self.display_result)
        self.worker.errorOccurred.connect(self.display_error)
        self.worker.progressUpdated.connect(self.update_progress)
        self.worker.statusMessage.connect(self.output.append)
        self.worker.start()

    def update_progress(self, current, total):
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        if current >= total:
            self.progress_bar.setVisible(False)

    def display_result(self, result):
        self.fetch_button.setEnabled(True)
        data = result.get("data")

        if self.api_name == "api1" and isinstance(data, dict):
            name = data.get("displayName", "Unknown")
            level = data.get("summonerLevel", "?")
            self.output.append(f"Summoner: {name} (Level {level})")

        elif self.api_name == "api2" and isinstance(data, list):
            self.output.append(f"Fetched total: {len(data)} games.")  # ✅ 只输出总件数

        # ❌ 完全移除 fallback，不再打印 data 内容
        # else:
        #     self.output.append(str(data))


    def display_error(self, message):
        self.fetch_button.setEnabled(True)
        self.output.append(f"Error: {message}")
