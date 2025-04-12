from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal
import logging
from web.websocket_client_api import call_api


class APIFetchWorker(QThread):
    finished = pyqtSignal(object)
    errorOccurred = pyqtSignal(str)

    def __init__(self, api_name: str):
        super().__init__()
        self.api_name = api_name
        self.actual_api = {
            "api1": "summoner",
            "api2": "match_history"
        }.get(self.api_name, self.api_name)
        logging.debug(f"{self.api_name}: 映射为实际 API -> {self.actual_api}")

    def run(self):
        logging.info(f"{self.api_name}: 子线程开始执行 call_api({self.actual_api})")
        try:
            data = call_api(self.actual_api)
            result = {"status": "success", "api": self.api_name, "data": data}
            logging.info(f"{self.api_name}: 成功获取数据")
            self.finished.emit(result)
        except Exception as e:
            err_msg = f"{self.api_name}: call_api 调用失败，错误: {str(e)}"
            logging.error(err_msg)
            self.errorOccurred.emit(err_msg)
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

    def fetch_data(self):
        logging.info(f"{self.api_name}: 开始新任务")
        self.fetch_button.setEnabled(False)
        self.output.append("Fetching...")

        self.worker = APIFetchWorker(self.api_name)
        self.worker.finished.connect(self.display_result)
        self.worker.errorOccurred.connect(self.display_error)
        self.worker.start()

    def display_result(self, result):
        self.fetch_button.setEnabled(True)
        self.output.append(str(result))
        logging.info(f"{self.api_name}: 任务完成，结果：{result}")

    def display_error(self, message):
        self.output.append(f"Error: {message}")
