from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QTextOption

class ChatTextInput(QTextEdit):
    sendMessage = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Type your message here... (Shift + Enter = Newline)")
        self.setFixedHeight(44)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 10px;
                padding: 8px 10px;
                font-size: 14px;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                color: #333333;
            }
            QTextEdit:focus {
                border: 1px solid #999999;
                background-color: #fefefe;
            }
        """)
        self.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)  # Fixed line
        self.setAcceptRichText(False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
            event.accept()
            self.sendMessage.emit()
        else:
            super().keyPressEvent(event)