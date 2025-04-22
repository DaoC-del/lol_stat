from PyQt5.QtWidgets import QMainWindow, QTabWidget
from ui.tabs import APITab
from web.match_storage import connect_mysql, init_tables_if_missing
from web.websocket_client_api import call_match_history_and_store

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("My Desktop App")

        # 初始化数据库（只执行一次）
        self._init_database()

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.tab_api1 = APITab("api1")
        self.tab_api2 = APITab("api2")
        self.tab_api3 = APITab("api3", callback=call_match_history_and_store)  # 注入数据库回调

        self.tab_widget.addTab(self.tab_api1, "API 1")
        self.tab_widget.addTab(self.tab_api2, "API 2")
        self.tab_widget.addTab(self.tab_api3, "API 3")

    def _init_database(self):
        try:
            print("🛠️ 正在连接数据库...")
            conn = connect_mysql()
            init_tables_if_missing(conn)
            conn.close()
            print("✅ 数据库连接与表结构初始化成功！")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
