from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

class ViewerWidget(QWidget):

    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.canvas = FigureCanvasQTAgg(self.viewer.fig)
        
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()
        
        layout.addWidget(self.canvas)
        
    