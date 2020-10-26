import sys

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTabWidget
from PyQt5.QtWebEngineWidgets import *

SITES = ['https://mathus.ru/index.php', 'https://postypashki.ru/']


class OlympPhysics(QMainWindow):
    def __init__(self):
        super(OlympPhysics, self).__init__()
        uic.loadUi('design.ui', self)
        self.tabWidget.tab3.scrollArea.site1.clicked.connect(self.ViewWebSite)

    def ViewWebSite(self):
        ap = QApplication(sys.argv)
        web = QWebEngineView()
        web.load(QUrl(SITES[int(self.sender().text()[-1])]))
        web.show()
        sys.exit(ap.exec())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wnd = OlympPhysics()
    wnd.show()
    sys.exit(app.exec())
