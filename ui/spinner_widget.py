from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt
import os

class Spinner(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        gif_path = os.path.join(os.path.dirname(__file__), "spinner.gif")
        self.movie = QMovie(gif_path)
        self.setMovie(self.movie)
        self.setAlignment(Qt.AlignCenter)
        self.setVisible(False)

    def start(self):
        self.setVisible(True)
        self.movie.start()

    def stop(self):
        self.movie.stop()
        self.setVisible(False)