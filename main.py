import sys
import ctypes

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from ui.main_window import MainWindow


myappid = "dveloz.medicalimagingworkstation.1.0"
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

app = QApplication(sys.argv)

app.setWindowIcon(QIcon("icons/app_icon.png"))
window = MainWindow()
window.show()

sys.exit(app.exec_())