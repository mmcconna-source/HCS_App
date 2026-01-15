import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QPushButton, QProgressBar, QLabel, QFileDialog, 
    QMessageBox, QScrollArea
)
from PyQt6.QtCore import QThreadPool, pyqtSignal, pyqtSlot
from plugin_manager import discover_plugins, create_plugin_ui
from utils.worker import AnalysisWorker

class HCSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HCS Modular Application")
        self.resize(1000, 700)
        # Threading: Handles heavy processing in separate context [cite: 9]
        self.threadpool = QThreadPool() 
        self.selected_plugin = None
        self.data_path = None
        
        self.init_ui()
        self.load_plugins()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Sidebar: Plugin Discovery [cite: 35-36]
        sidebar = QVBoxLayout()
        sidebar.addWidget(QLabel("Analysis Modules"))
        self.plugin_list = QListWidget()
        self.plugin_list.itemClicked.connect(self.on_plugin_selected)
        sidebar.addWidget(self.plugin_list)
        
        self.btn_browse = QPushButton("Select Data Directory")
        self.btn_browse.clicked.connect(self.browse_data)
        sidebar.addWidget(self.btn_browse)
        
        self.lbl_path = QLabel("No directory selected")
        self.lbl_path.setWordWrap(True)
        sidebar.addWidget(self.lbl_path)
        
        main_layout.addLayout(sidebar, 1)

        # Main Panel: Dynamic UI Generation 
        display_panel = QVBoxLayout()
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.param_container = QWidget()
        self.param_layout = QVBoxLayout(self.param_container)
        self.scroll.setWidget(self.param_container)
        display_panel.addWidget(self.scroll, 5)

        # Footer: Progress and Execution [cite: 38-40]
        footer = QVBoxLayout()
        self.progress_bar = QProgressBar()
        footer.addWidget(self.progress_bar)
        
        self.btn_run = QPushButton("Run Analysis")
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_analysis)
        footer.addWidget(self.btn_run)
        
        display_panel.addLayout(footer)
        main_layout.addLayout(display_panel, 3)

    def load_plugins(self):
        """Discovers modules in the /modules folder[cite: 35]."""
        self.plugins = discover_plugins()
        for name, module in self.plugins.items():
            # Use NAME constant for UI labeling [cite: 42-43]
            display_name = getattr(module, "NAME", name)
            self.plugin_list.addItem(display_name)

    def browse_data(self):
        """Sets the data_path reserved keyword[cite: 16]."""
        path = QFileDialog.getExistingDirectory(self, "Select Root Data Directory")
        if path:
            self.data_path = path
            self.lbl_path.setText(f"Selected: {path}")
            self.check_run_ready()

    def on_plugin_selected(self, item):
        """Clears and rebuilds the parameter panel for the selected plugin[cite: 37]."""
        plugin_name = next(k for k, v in self.plugins.items() if getattr(v, "NAME", k) == item.text())
        self.selected_plugin = self.plugins[plugin_name]
        
        # Clear existing widgets [cite: 37, 47]
        for i in reversed(range(self.param_layout.count())): 
            widget = self.param_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Build new UI [cite: 12, 31-32]
        self.form_layout, self.widgets = create_plugin_ui(self.selected_plugin)
        
        temp_widget = QWidget()
        temp_widget.setLayout(self.form_layout)
        self.param_layout.addWidget(temp_widget)
        self.check_run_ready()

    def check_run_ready(self):
        """Ensures both a plugin and data directory are selected."""
        if self.selected_plugin and self.data_path:
            self.btn_run.setEnabled(True)

    def run_analysis(self):
        """Collects params and executes module in a background thread [cite: 38-39]."""
        # Collection [cite: 38]
        params = {}
        for name, widget in self.widgets.items():
            # Dynamically read values based on widget type [cite: 31-32]
            if hasattr(widget, 'value'): params[name] = widget.value()
            elif hasattr(widget, 'isChecked'): params[name] = widget.isChecked()
            elif hasattr(widget, 'text'): params[name] = widget.text()

        # Inject reserved keyword [cite: 16]
        params['data_path'] = self.data_path
        
        # Threading: Instantiate AnalysisWorker [cite: 9, 39]
        self.btn_run.setEnabled(False)
        worker = AnalysisWorker(self.selected_plugin.run, **params)
        
        # Connect signals for UI updates [cite: 40, 48]
        worker.signals.progress.connect(self.progress_bar.setValue)
        worker.signals.finished.connect(self.on_finished)
        worker.signals.error.connect(self.on_error)
        
        self.threadpool.start(worker)

    @pyqtSlot(str)
    def on_finished(self, message):
        """
        Triggered when the AnalysisWorker completes successfully.
        Receives the status string from the plugin's return statement.
        """
        self.btn_run.setEnabled(True)
        self.progress_bar.setValue(100)
        
        # Display the Notification Pop-up
        msg = QMessageBox(self)
        msg.setWindowTitle("Analysis Complete")
        msg.setText(message)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    @pyqtSlot(str)
    def on_error(self, error_msg):
        """Error handling via Clean Signals[cite: 48, 50]."""
        self.btn_run.setEnabled(True)
        QMessageBox.critical(self, "Analysis Error", error_msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HCSApp()
    window.show()
    sys.exit(app.exec())