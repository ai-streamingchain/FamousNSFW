import sounddevice as sd
import numpy as np
import tempfile
import wave
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer

sd.default.device = (None, None)

class VoiceModal(QDialog):
    def __init__(self, on_audio_chunk, on_stop, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(False)
        self.setWindowModality(Qt.NonModal)
        self.setFixedSize(300, 100)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 16px;
                border: 1px solid #ccc;
            }
        """)

        layout = QVBoxLayout(self)
        self.label = QLabel("Listening...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size: 15px; color: #222; padding: 10px;")
        layout.addWidget(self.label)

        self.running = False
        self.error_state = False
        self.on_audio_chunk = on_audio_chunk  # Called with each audio chunk (bytes)
        self.on_stop = on_stop                # Called when recording stops

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_waveform)
        self.last_volume = 0

    def start_recording(self):
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            if not input_devices:
                self.label.setText("⚠️ <b style='color:#cc0000;'>Device not found</b><br><span style='color:#555;'>Please check your devices or settings.</span>")
                self.error_state = True
                self.stream = None
                return

            self.running = True
            self.error_state = False

            self.stream = sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype='int16',
                callback=self.audio_callback,
                blocksize=1024
            )
            self.stream.start()
            self.timer.start(100)
        except Exception as e:
            print("Device start error:", e)
            self.label.setText("⚠️ <b style='color:#cc0000;'>Device not found</b><br><span style='color:#555;'>Please check your devices or settings.</span>")
            self.error_state = True
            self.stream = None

    def audio_callback(self, indata, frames, time, status):
        if status:
            print("Audio stream warning:", status)
        if self.running:
            # Calculate volume for visualization
            self.last_volume = np.linalg.norm(indata)
            # Send audio chunk to main app (as bytes)
            self.on_audio_chunk(indata.tobytes())

    def update_waveform(self):
        bars = int(min(30, self.last_volume / 1000))
        waveform = "▁" * bars + " " * (30 - bars)
        self.label.setText(f"🎤 {waveform}")

    def stop_recording(self):
        self.running = False
        self.timer.stop()
        if hasattr(self, "stream") and self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                print("Stream close error:", e)
        self.on_stop()
        self.close()