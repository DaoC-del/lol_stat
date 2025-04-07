# main.py
import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
import logging
import config.config  

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")



def main():
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
