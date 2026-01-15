import os
import importlib.util
import inspect
from PyQt6.QtWidgets import (
    QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox, 
    QLineEdit, QHBoxLayout, QPushButton, QFileDialog, QWidget
)

def discover_plugins(directory="modules"):
    plugins = {}
    if not os.path.exists(directory):
        os.makedirs(directory)
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            spec = importlib.util.spec_from_file_location(module_name, os.path.join(directory, filename))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            plugins[module_name] = module
    return plugins

def update_path(line_edit, arg_name):
    """Triggers file or directory dialogs based on parameter name."""
    if "directory" in arg_name:
        path = QFileDialog.getExistingDirectory(None, f"Select {arg_name.replace('_', ' ').title()}")
    else:
        path, _ = QFileDialog.getOpenFileName(None, f"Select {arg_name.replace('_', ' ').title()}", "", "CSV Files (*.csv);;All Files (*)")
    
    if path:
        # For CSV names, we often just want the filename, not the full path
        if "csv_name" in arg_name:
            line_edit.setText(os.path.basename(path))
        else:
            line_edit.setText(path)

def create_plugin_ui(module):
    """Generates the UI for a plugin based on its 'run' signature [cite: 12, 31-32]."""
    form = QFormLayout()
    widgets = {}
    sig = inspect.signature(module.run)
    
    for name, param in sig.parameters.items():
        if name in ['progress_callback', 'data_path']: # Reserved keywords [cite: 15-17]
            continue
            
        label_text = name.replace("_", " ").title()
        default_val = param.default if param.default != inspect._empty else ""

        if param.annotation == float:
            w = QDoubleSpinBox(); w.setValue(float(default_val or 0.0))
            form.addRow(label_text, w); widgets[name] = w
        elif param.annotation == int:
            w = QSpinBox(); w.setMaximum(1000000); w.setValue(int(default_val or 0))
            form.addRow(label_text, w); widgets[name] = w
        elif param.annotation == bool:
            w = QCheckBox(); w.setChecked(bool(default_val))
            form.addRow(label_text, w); widgets[name] = w
        else:
            # String handling with Search Buttons
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            
            line_edit = QLineEdit(str(default_val))
            layout.addWidget(line_edit)
            
            # Check for path-related keywords to add the Browse button
            if any(key in name.lower() for key in ["path", "directory", "csv_name"]):
                btn = QPushButton("Browse")
                btn.clicked.connect(lambda checked, le=line_edit, n=name: update_path(le, n))
                layout.addWidget(btn)
                
            form.addRow(label_text, container)
            widgets[name] = line_edit
            
    return form, widgets