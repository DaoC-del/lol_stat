import logging
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QSizePolicy, QMessageBox
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from web.websocket_client import call_api

class APITab(QWidget):
    def __init__(self, api_name, parent=None):
        super().__init__(parent)
        self.api_name = api_name  # 例如 "api1", "api2", "api3"
        self.layout = QVBoxLayout(self)
        
        self.fetch_button = QPushButton(f"调用 {api_name}")
        self.fetch_button.clicked.connect(self.fetch_data)
        
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.layout.addWidget(self.fetch_button)
        self.layout.addWidget(self.result_area)
        
        # 保存线程和 worker 引用，避免提前销毁
        self.apiThread = None
        self.apiWorker = None

    def fetch_data(self):
        logging.info(f"{self.api_name}: 开始新任务")
        self.apiThread = QThread(self)
        self.apiWorker = APIFetchWorker(self.api_name)
        self.apiWorker.moveToThread(self.apiThread)
        
        self.apiThread.started.connect(self.apiWorker.run)
        self.apiWorker.finished.connect(self.handle_result)
        self.apiWorker.errorOccurred.connect(self.handle_error)
        self.apiWorker.finished.connect(self.apiThread.quit)
        self.apiWorker.finished.connect(self.apiWorker.deleteLater)
        self.apiThread.finished.connect(lambda: setattr(self, "apiThread", None))
        self.apiThread.finished.connect(self.apiThread.deleteLater)
        self.apiThread.start()
        
    def handle_result(self, result):
        logging.info(f"{self.api_name}: 任务完成，结果：{result}")
        # 无论成功或失败，更新界面数据；失败时 result 可能为 None 或错误信息
        self.result_area.setText(json.dumps(result, ensure_ascii=False, indent=2))

    def handle_error(self, error_msg):
        logging.error(f"{self.api_name}: 出现错误：{error_msg}")
        # 更新 UI 显示错误状态，避免保留旧数据
        error_result = {"status": "fail", "api": self.api_name, "data": None}
        self.result_area.setText(json.dumps(error_result, ensure_ascii=False, indent=2))
        QMessageBox.critical(self, "API 调用错误", error_msg)

class APIFetchWorker(QObject):
    finished = pyqtSignal(dict)
    errorOccurred = pyqtSignal(str)
    
    def __init__(self, api_name, parent=None):
        super().__init__(parent)
        self.api_name = api_name

    def run(self):
        logging.info(f"{self.api_name}: 工作线程开始执行，触发 call_api")
        try:
            data = call_api(self.api_name)
            result = {"status": "success", "api": self.api_name, "data": data}
            logging.info(f"{self.api_name}: call_api 调用完成，结果：{result}")
            self.finished.emit(result)
        except Exception as e:
            err_msg = f"{self.api_name}: call_api 调用失败，错误: {str(e)}"
            logging.error(err_msg)
            self.errorOccurred.emit(err_msg)
            # 同时更新 finished 信号，以便 UI 更新数据（设为 null）
            self.finished.emit({"status": "fail", "api": self.api_name, "data": None})
