import sqlite3
from PySide6.QtCore import QObject, Signal

class DatabaseManager(QObject):
    data_updated = Signal()

    def __init__(self, db_name="chat_app.db"):
        super().__init__()
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    is_favorite BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    content TEXT NOT NULL,
                    sender TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats(id)
                )
            """)
            conn.commit()
            
    def rename_chat(self, chat_id, new_title):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE chats SET title = ? WHERE id = ?",
                (new_title, chat_id))
            conn.commit()
            self.data_updated.emit()

    def toggle_favorite(self, chat_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE chats SET is_favorite = NOT is_favorite WHERE id = ?",
                (chat_id,))
            conn.commit()
            self.data_updated.emit()

    def add_chat(self, title):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO chats (title) VALUES (?)", (title,))
            conn.commit()
            self.data_updated.emit()
            return cursor.lastrowid

    def get_chats(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title FROM chats ORDER BY created_at DESC")
            return cursor.fetchall()

    def add_message(self, chat_id, content, sender='user'):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (chat_id, content, sender) VALUES (?, ?, ?)",
                (chat_id, content, sender)
            )
            conn.commit()
            self.data_updated.emit()

    def get_messages(self, chat_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT content, sender FROM messages WHERE chat_id = ? ORDER BY created_at",
                (chat_id,)
            )
            return cursor.fetchall()