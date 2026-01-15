import sys
import traceback
from PyQt6.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal

class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""
    finished = pyqtSignal(str)  # Must accept a string for the success message
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

class AnalysisWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
        # Inject the progress_callback into the plugin arguments [cite: 17, 21]
        self.kwargs['progress_callback'] = self.signals.progress

    def run(self):
        """Executes the plugin logic in a separate thread[cite: 9, 39]."""
        try:
            # result is the string returned by the plugin's run function [cite: 50]
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(str(result))
        except Exception as e:
            self.signals.error.emit(str(e))