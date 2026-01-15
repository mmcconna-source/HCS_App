import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QLabel, 
                             QFileDialog, QProgressBar, QGroupBox)
from PyQt6.QtCore import QThreadPool
import plugin_manager
from utils.worker import AnalysisWorker

class HCSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("High-Content Analysis Shell")
        self.resize(1100, 700)
        self.threadpool = QThreadPool()
        self.selected_dir = None
        self.active_widgets = {}

        # Main Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # Sidebar
        sidebar = QVBoxLayout()
        sidebar.addWidget(QLabel("<b>Analysis Modules</b>"))
        self.plugin_list = QListWidget()
        self.plugin_list.itemClicked.connect(self.load_module_ui)
        sidebar.addWidget(self.plugin_list)
        
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.refresh_plugins)
        sidebar.addWidget(refresh_btn)
        layout.addLayout(sidebar, 1)

        # Main Content
        content = QVBoxLayout()
        self.path_label = QLabel("No Directory Selected")
        load_btn = QPushButton("1. Load Data Directory")
        load_btn.clicked.connect(self.select_dir)
        content.addWidget(load_btn)
        content.addWidget(self.path_label)

        self.param_group = QGroupBox("2. Module Parameters")
        self.param_layout = QVBoxLayout()
        self.param_group.setLayout(self.param_layout)
        content.addWidget(self.param_group)

        self.progress = QProgressBar()
        content.addWidget(self.progress)

        self.run_btn = QPushButton("3. Run Analysis")
        self.run_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; height: 40px;")
        self.run_btn.clicked.connect(self.run_analysis)
        content.addWidget(self.run_btn)
        
        layout.addLayout(content, 3)
        self.refresh_plugins()

    def select_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Data")
        if path:
            self.selected_dir = path
            self.path_label.setText(f"Active: {path}")

    def refresh_plugins(self):
        self.plugins = plugin_manager.discover_plugins()
        self.plugin_list.clear()
        self.plugin_list.addItems(self.plugins.keys())

    def load_module_ui(self, item):
        # Clear old UI
        for i in reversed(range(self.param_layout.count())): 
            self.param_layout.itemAt(i).widget().setParent(None)
        
        module = self.plugins[item.text()]
        form, self.active_widgets = plugin_manager.create_plugin_ui(module)
        container = QWidget()
        container.setLayout(form)
        self.param_layout.addWidget(container)

    def run_analysis(self):
        if not self.selected_dir or not self.plugin_list.currentItem(): return
        
        module = self.plugins[self.plugin_list.currentItem().text()]
        params = {name: (w.value() if hasattr(w, 'value') else w.isChecked() if hasattr(w, 'isChecked') else w.text()) 
                  for name, w in self.active_widgets.items()}
        params['data_path'] = self.selected_dir

        worker = AnalysisWorker(module.run, **params)
        worker.signals.progress.connect(self.progress.setValue)
        worker.signals.finished.connect(lambda: self.progress.setValue(100))
        self.threadpool.start(worker)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HCSApp()
    window.show()
    sys.exit(app.exec())