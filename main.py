import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenu, 
                              QInputDialog, QMessageBox)
from PySide6.QtCore import Qt
from ui.ui_MainWindow import Ui_MainWindow
from database import DatabaseManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.db = DatabaseManager()
        
        # Enable custom context menu for list items
        self.ui.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(self.show_chat_menu)
        
        # Connect signals
        self.ui.newChatButton.clicked.connect(self.create_new_chat)
        self.ui.sendButton.clicked.connect(self.send_message)
        self.ui.listWidget.itemClicked.connect(self.load_chat)
        
        self.load_chats()

    def show_chat_menu(self, pos):
        item = self.ui.listWidget.itemAt(pos)
        if not item:
            return
            
        menu = QMenu()
        
        rename_action = menu.addAction("Rename Chat")
        delete_action = menu.addAction("Delete Chat")
        favorite_action = menu.addAction("Add to Favorites")
        
        action = menu.exec_(self.ui.listWidget.mapToGlobal(pos))
        
        if action == rename_action:
            self.rename_chat(item)
        elif action == delete_action:
            self.delete_chat(item)
        elif action == favorite_action:
            self.add_to_favorites(item)

    def rename_chat(self, item):
        new_name, ok = QInputDialog.getText(
            self, "Rename Chat", "Enter new name:", text=item.text()
        )
        if ok and new_name:
            chat_id = self.get_chat_id(item)
            self.db.rename_chat(chat_id, new_name)
            item.setText(new_name)
            if self.ui.listWidget.currentItem() == item:
                self.ui.chat_title.setText(new_name)

    def delete_chat(self, item):
        reply = QMessageBox.question(
            self, "Delete Chat", 
            "Are you sure you want to delete this chat?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            chat_id = self.get_chat_id(item)
            self.db.delete_chat(chat_id)
            self.ui.listWidget.takeItem(self.ui.listWidget.row(item))
            if self.ui.listWidget.count() == 0:
                self.ui.plainText.clear()
                self.ui.chat_title.setText("No Chat Selected")

    def load_chats(self):
        self.ui.listWidget.clear()
        chats = self.db.get_chats()
        for chat_id, title in chats:
            self.ui.listWidget.addItem(f"{title}")

    def create_new_chat(self):
        chat_id = self.db.add_chat("New Chat")
        self.load_chats()
        self.ui.plainText.clear()

    def load_chat(self, item):
        chat_title = item.text()
        chats = self.db.get_chats()
        chat_id = next((cid for cid, title in chats if title == chat_title), None)
        
        if chat_id:
            messages = self.db.get_messages(chat_id)
            self.ui.plainText.clear()
            for content, sender in messages:
                prefix = "You: " if sender == 'user' else "AI: "
                self.ui.plainText.appendPlainText(f"{prefix}{content}")

    def send_message(self):
        current_item = self.ui.listWidget.currentItem()
        if not current_item:
            return
            
        chat_title = current_item.text()
        chats = self.db.get_chats()
        chat_id = next((cid for cid, title in chats if title == chat_title), None)
        
        if chat_id and self.ui.textInput.text():
            message = self.ui.textInput.text()
            
            # Save user message
            self.db.add_message(chat_id, message, 'user')
            self.ui.plainText.appendPlainText(f"You: {message}")
            self.ui.textInput.clear()
            
            # Simulate AI response
            ai_response = f"I received: {message}"
            self.db.add_message(chat_id, ai_response, 'ai')
            self.ui.plainText.appendPlainText(f"AI: {ai_response}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())