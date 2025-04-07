# ui/main_window.py
from PyQt5.QtWidgets import QMainWindow, QTabWidget
from ui.tabs import APITab

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("My Desktop App")
        
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # 创建三个 API 页签，分别为 api1, api2, api3
        self.tab_api1 = APITab("api1")
        self.tab_api2 = APITab("api2")
        self.tab_api3 = APITab("api3")
        
        self.tab_widget.addTab(self.tab_api1, "API 1")
        self.tab_widget.addTab(self.tab_api2, "API 2")
        self.tab_widget.addTab(self.tab_api3, "API 3")
