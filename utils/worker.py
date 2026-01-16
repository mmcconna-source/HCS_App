import sys
import traceback
from PyQt6.QtCore import QRunnable, pyqtSlot, pyqtSignal, QObject

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class AnalysisWorker(QRunnable):
    """
    Worker thread for running analysis plugins without freezing the UI.
    """
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Automatically inject the progress_callback signal if the plugin accepts it [cite: 17, 40]
        if 'progress_callback' in self.kwargs:
            self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        """
        Initializes the runner function with passed args and kwargs.
        """
        try:
            # Execute the plugin's run function [cite: 39]
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            # Error Resilience: Catch and report errors without crashing the App 
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()