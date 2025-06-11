from PySide6.QtCore import QObject, Signal
import time

class AIWorker(QObject):
    partial = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, llm, prompt):
        super().__init__()
        self.llm = llm
        self.prompt = prompt
        self._abort = False

    def run(self):
        try:
            output = ""
            for word in self.llm.ask(self.prompt, stream=True):
                if self._abort:
                    self.finished.emit("[⚠️ Cancelled]")
                    return
                output += word
                self.partial.emit(output)
                time.sleep(0.01)  # smooth typing
            self.finished.emit(output)
        except Exception as e:
            self.error.emit(str(e))

    def abort(self):
        self._abort = True