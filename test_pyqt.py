from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import sys

# main window class

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OpenLog")

        self.label = QLabel()

        self.input = QLineEdit()

        button = QPushButton("Update Text")
        button.clicked.connect(self.buttonClicked)

        layout = QVBoxLayout()
        layout.addWidget(self.input)
        layout.addWidget(self.label)
        layout.addWidget(button)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

    def contextMenuEvent(self, event):
        menu = QMenu()
        updateTextAction =QAction("Update Text", self)
        menu.addAction(updateTextAction)
        menu.exec(event.globalPos())

    def buttonClicked(self):
        self.label.setText(self.input.text())

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()