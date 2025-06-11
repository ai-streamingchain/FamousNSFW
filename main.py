import os
import sys
import time
import json
import socket
import datetime
import threading
import subprocess

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMenu, QFileDialog,
    QInputDialog, QMessageBox, QListWidgetItem,
)
from PySide6.QtGui import QFont, QIcon, QTextCursor
from PySide6.QtCore import Qt, QSize, QTimer, QMetaObject, QEvent, QThread, QObject, Signal

from ui.ui_MainWindow import Ui_MainWindow
from ui.voice_modal import VoiceModal
from ui.spinner_widget import Spinner
from ui.spinner_overlay import SpinnerOverlay

from database import DatabaseManager

from workers.ai_worker import AIWorker
from workers.image_worker import ImageWorker

class ModelLoaderWorker(QObject):
    finished = Signal(object, object)  # (local_llm, sd_pipe)
    error = Signal(str)

    def run(self):
        try:
            from workers.local_llm import LocalLLM
            local_llm = LocalLLM()
            from diffusers import StableDiffusionPipeline
            import traceback
            import torch, os

            ckpt_path = r"models/stable-diffusion/sd-v1-4.ckpt"
            sd_pipe = StableDiffusionPipeline.from_single_file(
                ckpt_path,
                torch_dtype=torch.float32
            )
            if torch.cuda.is_available():
                sd_pipe = sd_pipe.to("cuda")
            else:
                sd_pipe = sd_pipe.to("cpu")
            self.finished.emit(local_llm, sd_pipe)
        except Exception as e:
            tb = traceback.format_exc()
            print("Model loading error:", tb)
            self.error.emit(f"{e}\n{tb}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.sidebarWidget.installEventFilter(self)
        self.ui.uploadButton.clicked.connect(self.handle_file_upload)

        self.db = DatabaseManager()  # <-- Add this before self.load_chats()

        self.pending_image_path = None
        self.pending_image_filename = None

        self.ui.statusLabel.setText("🔄 Loading models...")  # Show loading status
        self.setEnabled(False)  # Disable UI until ready

        self.model_loader_thread = QThread()
        self.model_loader_worker = ModelLoaderWorker()
        self.model_loader_worker.moveToThread(self.model_loader_thread)
        self.model_loader_worker.finished.connect(self.on_models_loaded)
        self.model_loader_worker.error.connect(self.on_model_load_error)
        self.model_loader_thread.started.connect(self.model_loader_worker.run)
        self.model_loader_thread.start()

        # model_path = os.path.abspath(os.path.join(os.getcwd(), "models", "stable-diffusion"))
        # self.sd_pipe = StableDiffusionPipeline.from_pretrained(
        #     model_path,
        #     torch_dtype=torch.float32  # Use float32 for CPU
        # ).to("cpu")

        # print("unet:", os.listdir("./models/stable-diffusion/unet"))
        # print("vae:", os.listdir("./models/stable-diffusion/vae"))
        # print("text_encoder:", os.listdir("./models/stable-diffusion/text_encoder"))

        # import diffusers; print(diffusers.__version__)
        # import transformers; print(transformers.__version__)
        # import safetensors; print(safetensors.__version__)

        self.voice_modal = None
        
        self.ui.retryButton.clicked.connect(self.retry_ai)
        self.ui.cancelButton.clicked.connect(self.cancel_ai)

        # Enable custom context menu for list items
        self.ui.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(self.show_chat_menu)
        
        # Connect signals
        self.ui.newChatButton.clicked.connect(self.create_new_chat)
        self.ui.sendButton.clicked.connect(self.send_message)
        self.ui.listWidget.itemClicked.connect(self.load_chat)

        self.ui.micOnButton.clicked.connect(self.activate_voice_input)
        self.ui.micOffButton.clicked.connect(self.deactivate_voice_input)
        self.ui.sidebarToggleButton.clicked.connect(self.handle_sidebar_toggle)

        self.spinner_overlay = SpinnerOverlay(self)
        self.spinner_overlay.setGeometry(self.rect())
        self.spinner_overlay.show()
        self.spinner_overlay.raise_()

        # ...existing code...
        self.whisper_process = None
        self.whisper_socket = None
        self.voice_modal = None
        self.audio_buffer = bytearray()
        self.transcribe_thread = None
        # ...rest of your __init__...
        
        self.load_chats()
        self.current_chat_id = None

        self.ui.textInput.sendMessage.connect(self.send_message)

    def transcribe_audio_with_whisper(self, audio_path):
        # Path to your whisper_worker venv python
        whisper_python = r"whisper_worker\.venv\Scripts\python.exe"
        whisper_script = r"whisper_worker\whisper_server.py"
        result = subprocess.run(
            [whisper_python, whisper_script, audio_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return None
        try:
            output = json.loads(result.stdout)
            return output.get("text", "")
        except Exception:
            return None

    def eventFilter(self, watched, event):
        if watched == self.ui.sidebarWidget and event.type() in (QEvent.Hide, QEvent.Show, QEvent.Resize):
            QTimer.singleShot(0, self.position_modal_above_button)
        return super().eventFilter(watched, event)
    
    def handle_file_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if not file_path:
            return

        # Save to /upload with unique name
        upload_dir = os.path.join(os.getcwd(), "upload")
        os.makedirs(upload_dir, exist_ok=True)
        ext = os.path.splitext(file_path)[1]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"upload_{timestamp}{ext}"
        save_path = os.path.join(upload_dir, new_filename)
        with open(file_path, "rb") as src, open(save_path, "wb") as dst:
            dst.write(src.read())

        # Store pending image info
        self.pending_image_path = save_path
        self.pending_image_filename = new_filename

        # Show small preview
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap(save_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ui.imagePreviewLabel.setPixmap(pixmap)
        self.ui.imagePreviewLabel.setVisible(True)

    def position_modal_above_button(self):
        if not self.voice_modal or not self.voice_modal.isVisible():
            return

        button = self.ui.micOffButton if self.ui.micOffButton.isVisible() else self.ui.micOnButton
        pos = button.mapToGlobal(button.rect().topLeft())
        modal = self.voice_modal
        modal_x = pos.x() + 10
        modal_y = pos.y() - modal.height() - 20
        modal.move(modal_x, modal_y)

    def handle_sidebar_toggle(self):
        self.ui.toggle_sidebar()
        
        def reposition():
            QTimer.singleShot(0, self.position_modal_above_button)

        QTimer.singleShot(0, reposition)

    def connect_whisper_socket(self):
        # Connect to the whisper server socket
        self.whisper_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.whisper_socket.connect(("localhost", 8765))

        def on_audio_chunk(chunk):
            try:
                self.whisper_socket.sendall(chunk)
            except Exception as e:
                print("Socket send error:", e)

        def on_stop():
            try:
                self.whisper_socket.sendall(b"__END__")
            except Exception:
                pass

        self.voice_modal = VoiceModal(on_audio_chunk, on_stop, self)
        self.position_modal_above_button()
        self.voice_modal.show()
        QTimer.singleShot(1, self.position_modal_above_button)
        self.voice_modal.start_recording()

        # Start thread to receive transcriptions
        self.transcribe_thread = threading.Thread(target=self.receive_transcriptions, daemon=True)
        self.transcribe_thread.start()

    def activate_voice_input(self):
        self.ui.micOnButton.setVisible(False)
        self.ui.micOffButton.setVisible(True)
        self.audio_buffer = bytearray()

        # Start Whisper server as a subprocess (if not running)
        if not self.whisper_process:
            self.whisper_process = subprocess.Popen(
                [r"whisper_worker\.venv\Scripts\python.exe", r"whisper_worker\whisper_server.py", "--socket"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            # Try to connect, retrying for up to 5 seconds
            for _ in range(50):
                try:
                    self.connect_whisper_socket()
                    break
                except ConnectionRefusedError:
                    time.sleep(0.1)
            else:
                QMessageBox.critical(self, "Whisper Error", "Could not connect to Whisper server.")
                self.ui.micOnButton.setVisible(True)
                self.ui.micOffButton.setVisible(False)
                return
        else:
            self.connect_whisper_socket()

    def receive_transcriptions(self):
        buffer = b""
        while True:
            try:
                data = self.whisper_socket.recv(4096)
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    try:
                        msg = json.loads(line.decode())
                        text = msg.get("text", "")
                        self.ui.textInput.setText(text)
                    except Exception as e:
                        print("Transcription parse error:", e)
            except Exception as e:
                print("Socket receive error:", e)
                break

    def deactivate_voice_input(self):
        self.ui.micOnButton.setVisible(True)
        self.ui.micOffButton.setVisible(False)
        if self.voice_modal:
            try:
                self.voice_modal.stop_recording()
            except Exception as e:
                print("Stop recording error:", e)
            self.voice_modal = None
        if self.whisper_socket:
            try:
                self.whisper_socket.close()
            except Exception:
                pass
            self.whisper_socket = None
        if self.whisper_process:
            try:
                self.whisper_process.terminate()
            except Exception:
                pass
            self.whisper_process = None

    def show_chat_menu(self, pos):
        item = self.ui.listWidget.itemAt(pos)
        if not item:
            return
            
        menu = QMenu()
        
        rename_action = menu.addAction("Rename Chat")
        delete_action = menu.addAction("Delete Chat")
        chat_id = self.get_chat_id(item)
        is_favorite = False
        if chat_id:
            chats = self.db.get_chats()
            for cid, title in chats:
                if cid == chat_id:
                    is_favorite = True if "★" in item.text() else False
                    break

        fav_text = "Remove from Favorites" if is_favorite else "Add to Favorites"
        favorite_action = menu.addAction(fav_text)

        
        action = menu.exec(self.ui.listWidget.mapToGlobal(pos))
        
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
                self.ui.chat_title.setText("Welcome to FamousNSFW!")

    def load_chats(self):
        self.ui.listWidget.clear()

        # === Favorites Section ===
        favorite_chats = self.db.get_chats(only_favorites=True)
        if favorite_chats:
            fav_header = QListWidgetItem("★ Favorites")
            fav_header.setFlags(Qt.NoItemFlags)
            fav_header.setFont(QFont("Arial", 11, QFont.Bold))
            fav_header.setBackground(Qt.lightGray)  
            fav_header.setTextAlignment(Qt.AlignBottom | Qt.AlignLeft)
            self.ui.listWidget.addItem(fav_header)

            for chat_id, title in favorite_chats:
                item = QListWidgetItem(f"{title}")
                self.ui.listWidget.addItem(item)

        # === Regular Chats Section ===
        regular_chats = self.db.get_chats(only_favorites=False)
        if regular_chats:
            all_header = QListWidgetItem("— All Chats")
            all_header.setFlags(Qt.NoItemFlags)
            all_header.setFont(QFont("Arial", 11, QFont.Bold))
            all_header.setSizeHint(QSize(0, 40))
            all_header.setBackground(Qt.lightGray)
            all_header.setTextAlignment(Qt.AlignBottom | Qt.AlignLeft)
            self.ui.listWidget.addItem(all_header)

            for chat_id, title in regular_chats:
                item = QListWidgetItem(title)
                self.ui.listWidget.addItem(item)

    def create_new_chat(self):
        self.current_chat_id = None  # No chat yet
        self.ui.plainText.clear()
        self.ui.chat_title.setText("Welcome!")
        self.ui.plainText.setPlainText("What can I help you with?")
        self.ui.textInput.setFocus()

    def render_image_message(self, filename):
        upload_dir = os.path.join(os.getcwd(), "upload")
        save_path = os.path.join(upload_dir, filename)
        return f'<img src="{save_path}" alt="" style="max-width:200px; max-height:200px; border-radius:16px;"/>'  # No filename

    def load_chat(self, item):
        chat_id = self.get_chat_id(item)
        if not chat_id:
            return
        
        self.current_chat_id = chat_id

        title = item.text().replace("★ ", "")
        self.ui.chat_title.setText(title)  

        messages = self.db.get_messages(chat_id)
        self.ui.plainText.clear()
        for content, sender in messages:
            prefix = "You" if sender == 'user' else "AI"
            if content.startswith("[image:") and content.endswith("]"):
                filename = content[7:-1]
                html = self.render_image_message(filename)
                self.append_message(prefix, html)
            else:
                self.append_message(prefix, content)
        
    def get_chat_id(self, item):
        raw_title = item.text().replace("★ ", "")
        if raw_title in ["★ Favorites", "— All Chats"]:
            return None
        chats = self.db.get_chats()
        for cid, title in chats:
            if title == raw_title:
                return cid
        return None
    
    def update_typing(self, text):
        # If text is a dict, extract the text field
        if isinstance(text, dict):
            text = text.get("text", str(text))
        if self.ui.statusLabel.text() != "✍️ Typing...":
            self.ui.statusLabel.setText("✍️ Typing...")
        cursor = self.ui.plainText.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.ui.plainText.undo()
        self.append_message("AI", text)

    def ai_done(self, text):
        # If text is a dict, extract the text field
        if isinstance(text, dict):
            text = text.get("text", str(text))
        self.ui.statusLabel.setText("")
        cursor = self.ui.plainText.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.ui.plainText.undo()
        self.append_message("AI", text)
        self.db.add_message(self.current_chat_id, text, 'ai')
        self.last_ai_response = text
        self.ui.sendButton.setEnabled(True)
        self.cleanup_ai_thread()

    def ai_error(self, msg):
        self.ui.statusLabel.setText(f"❌ Error: {msg}")
        self.ui.sendButton.setEnabled(True)
        self.ui.cancelButton.setVisible(False)
        self.cleanup_ai_thread()

    def cancel_ai(self):
        if hasattr(self, 'ai_worker'):
            self.ai_worker.stop()

    def retry_ai(self):
        if hasattr(self, 'last_user_message'):
            self.generate_ai_response(self.last_user_message)

    def cleanup_ai_thread(self):
        if self.ai_thread:
            self.ai_thread.quit()
            self.ai_thread.wait()
            self.ai_thread = None
            self.ai_worker = None


    def generate_ai_response(self, prompt):
        if not hasattr(self, "local_llm") or self.local_llm is None:
            self.ui.statusLabel.setText("❌ Model not loaded yet. Please wait.")
            self.ui.sendButton.setEnabled(True)
            return

        self.ui.sendButton.setEnabled(False)
        self.ui.statusLabel.setText("🤖 Thinking...") 
        self.append_message("AI", "🤖 Thinking...", italic=True)

        self.ai_thread = QThread()
        self.ai_worker = AIWorker(self.local_llm.model, prompt)
        self.ai_worker.moveToThread(self.ai_thread)

        self.ai_worker.partial.connect(self.update_typing)
        self.ai_worker.finished.connect(self.ai_done)
        self.ai_worker.error.connect(self.ai_error)
        self.ai_thread.started.connect(self.ai_worker.run)

        self.ai_thread.start()
    
    def append_message(self, sender: str, text: str, italic=False, message_id=None):
        color = "#007acc" if sender == "You" else "#333"
        weight = "bold" if sender == "You" else "normal"
        style = "italic" if italic else "normal"

        html = f"""
        <div id="{message_id or ''}" style="margin-bottom:12px;">
            <span style="color:{color}; font-weight:{weight};">{sender}:</span><br>
            <span style="font-style:{style};">{text}</span>
        </div>
        <br> <!-- Add this for extra spacing -->
        """
        cursor = self.ui.plainText.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(html)
        self.ui.plainText.setTextCursor(cursor)
        QTimer.singleShot(0, lambda: self.ui.plainText.verticalScrollBar().setValue(
            self.ui.plainText.verticalScrollBar().maximum()))
        
    def send_message(self):
        message = self.ui.textInput.toPlainText().strip()
        has_image = self.pending_image_path is not None

        if not message and not has_image:
            return

        # Detect text-to-image request
        image_keywords = ["draw:", "generate image:", "picture of", "show me", "create an image of"]
        if any(message.lower().startswith(k) or k in message.lower() for k in image_keywords):
            prompt = message.split(":", 1)[1].strip()
            output_filename = f"gen_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            output_path = os.path.join(os.getcwd(), "upload", output_filename)
            self.generate_image_from_text(prompt, output_path)
            self.db.add_uploaded_file(self.current_chat_id, output_filename)
            self.db.add_message(self.current_chat_id, f"[image:{output_filename}]", 'user')
            self.append_message("You", self.render_image_message(output_filename))
            self.ui.textInput.clear()
            return

        if self.current_chat_id is None:
            title = self.generate_chat_title(message or "Image")
            self.current_chat_id = self.db.add_chat(title)
            self.load_chats()
            self.select_chat_in_list(self.current_chat_id)
            self.ui.chat_title.setText(title)
            self.ui.plainText.clear()

        # Save text message if present
        if message:
            self.db.add_message(self.current_chat_id, message, 'user')
            self.append_message("You", message)

        # Save image if present
        if has_image:
            self.db.add_uploaded_file(self.current_chat_id, self.pending_image_filename)
            self.db.add_message(self.current_chat_id, f"[image:{self.pending_image_filename}]", 'user')
            self.append_message("You", self.render_image_message(self.pending_image_filename))
            # Clear preview
            self.ui.imagePreviewLabel.clear()
            self.ui.imagePreviewLabel.setVisible(False)
            self.pending_image_path = None
            self.pending_image_filename = None

        self.ui.textInput.clear()

        # Only generate AI response if text or image was sent
        if message or has_image:
            self.last_user_message = message
            self.generate_ai_response(message)

    def generate_image_from_text(self, prompt, output_path):
        self.ui.spinner.start()
        self.ui.spinner.setVisible(True)
        self.setEnabled(False)

        self.image_thread = QThread()
        self.image_worker = ImageWorker(self.sd_pipe, prompt, output_path)
        self.image_worker.moveToThread(self.image_thread)
        self.image_worker.finished.connect(self.on_image_generated)
        self.image_worker.error.connect(self.on_image_error)
        self.image_thread.started.connect(self.image_worker.run)
        self.image_thread.start()

    def on_image_generated(self, output_path):
        self.ui.spinner.stop()
        self.ui.spinner.setVisible(False)
        self.setEnabled(True)
        self.image_thread.quit()
        self.image_thread.wait()
        # You may want to update the UI with the new image here

    def on_image_error(self, msg):
        self.ui.statusLabel.setText(f"❌ Image error: {msg}")
        self.ui.spinner.stop()
        self.ui.spinner.setVisible(False)
        self.setEnabled(True)
        self.image_thread.quit()
        self.image_thread.wait()

    def generate_chat_title(self, text):
        words = text.strip().split()
        if len(words) > 6:
            return " ".join(words[:6]) + "..."
        return text.strip().capitalize()
    
    def select_chat_in_list(self, chat_id):
        for i in range(self.ui.listWidget.count()):
            item = self.ui.listWidget.item(i)
            if item and item.data(Qt.UserRole) == chat_id:
                self.ui.listWidget.setCurrentItem(item)
                break

    def add_to_favorites(self, item):
        chat_id = self.get_chat_id(item)
        if chat_id:
            self.db.toggle_favorite(chat_id)
            self.load_chats()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "spinner_overlay"):
            self.spinner_overlay.setGeometry(self.rect())
        self.position_modal_above_button()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.position_modal_above_button()

    def on_models_loaded(self, local_llm, sd_pipe):
        self.local_llm = local_llm
        self.sd_pipe = sd_pipe
        self.ui.statusLabel.setText("✅ Ready")
        self.spinner_overlay.hide()
        self.setEnabled(True)
        self.model_loader_thread.quit()
        self.model_loader_thread.wait()

    def on_model_load_error(self, msg):
        self.ui.statusLabel.setText(f"❌ Model load error: {msg}")
        self.spinner_overlay.hide()
        self.setEnabled(True)
        self.model_loader_thread.quit()
        self.model_loader_thread.wait()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())