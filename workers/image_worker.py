from PySide6.QtCore import QObject, Signal

class ImageWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, sd_pipe, prompt, output_path):
        super().__init__()
        self.sd_pipe = sd_pipe
        self.prompt = prompt
        self.output_path = output_path

    def run(self):
        try:
            image = self.sd_pipe(self.prompt).images[0]
            image.save(self.output_path)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))