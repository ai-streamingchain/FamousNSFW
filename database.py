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
                    is_deleted BOOLEAN DEFAULT 0,
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

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                filename TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    
    def delete_chat(self, chat_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Soft delete: just mark the chat as deleted
            cursor.execute("UPDATE chats SET is_deleted = 1 WHERE id = ?", (chat_id,))
            
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

    def get_chats(self, only_favorites=None):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            if only_favorites is True:
                cursor.execute("""
                    SELECT id, title FROM chats 
                    WHERE is_deleted = 0 AND is_favorite = 1 
                    ORDER BY created_at DESC
                """)
            elif only_favorites is False:
                cursor.execute("""
                    SELECT id, title FROM chats 
                    WHERE is_deleted = 0 AND is_favorite = 0 
                    ORDER BY created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT id, title FROM chats 
                    WHERE is_deleted = 0 
                    ORDER BY created_at DESC
                """)
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
    
    def add_uploaded_file(self, chat_id, filename):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO uploads (chat_id, filename) VALUES (?, ?)",
                (chat_id, filename)
            )
            conn.commit()
            self.data_updated.emit()