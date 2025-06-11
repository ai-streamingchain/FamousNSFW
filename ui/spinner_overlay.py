from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt
import os

class SpinnerOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: rgba(255,255,255,0.95);")
        self.spinner = QLabel(self)
        gif_path = os.path.join(os.path.dirname(__file__), "spinner.gif")
        self.movie = QMovie(gif_path)
        self.spinner.setMovie(self.movie)
        self.spinner.setAlignment(Qt.AlignCenter)
        self.movie.start()

    def resizeEvent(self, event):
        size = self.spinner.sizeHint()
        self.spinner.move(
            (self.width() - size.width()) // 2,
            (self.height() - size.height()) // 2
        )