import socket
import json
import numpy as np
import tempfile
import wave
from faster_whisper import WhisperModel

model = WhisperModel("../models/whisper-cpu", device="cpu", compute_type="int8")

def save_wav(frames, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))

def run_socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 8765))
    server.listen(1)
    conn, addr = server.accept()
    frames = []
    while True:
        data = conn.recv(2048)
        if not data:
            break
        if b"__END__" in data:
            data = data.replace(b"__END__", b"")
            if data:
                frames.append(data)
            break
        frames.append(data)
        # Optionally, stream partial transcription here for real-time
        if len(frames) % 10 == 0:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                save_wav(frames, tmp.name)
                segments, _ = model.transcribe(tmp.name)
                text = " ".join([s.text for s in segments])
                msg = json.dumps({"text": text}) + "\n"
                conn.sendall(msg.encode())
    # Final transcription
    if frames:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            save_wav(frames, tmp.name)
            segments, _ = model.transcribe(tmp.name)
            text = " ".join([s.text for s in segments])
            msg = json.dumps({"text": text}) + "\n"
            conn.sendall(msg.encode())
    conn.close()
    server.close()

if __name__ == "__main__":
    import sys
    if "--socket" in sys.argv:
        run_socket_server()
    else:
        # Fallback: file mode for compatibility
        if len(sys.argv) < 2:
            print(json.dumps({"error": "No audio file provided"}))
            sys.exit(1)
        audio_path = sys.argv[1]
        try:
            segments, _ = model.transcribe(audio_path)
            text = " ".join([s.text for s in segments])
            print(json.dumps({"text": text}))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)