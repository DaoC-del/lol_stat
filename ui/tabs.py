from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

class APITab(QWidget):
    def __init__(self, api_name, callback=None):
        super().__init__()
        self.api_name = api_name
        self.callback = callback
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.label = QLabel(f"This is the {self.api_name} tab")
        layout.addWidget(self.label)

        if self.callback:
            self.button = QPushButton(f"Run {self.api_name}")
            self.button.clicked.connect(self.callback)
            layout.addWidget(self.button)

        self.setLayout(layout)
