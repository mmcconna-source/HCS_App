import os
import importlib.util
import inspect
from PyQt6.QtWidgets import QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox, QLineEdit

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
def create_widget_with_search(arg_name, default_val):
    layout = QHBoxLayout()
    line_edit = QLineEdit(str(default_val))
    
    # Identify if a search button is needed based on naming convention [cite: 32]
    if "directory" in arg_name or "path" in arg_name:
        btn = QPushButton("Browse")
        btn.clicked.connect(lambda: update_path(line_edit, arg_name))
        layout.addWidget(line_edit)
        layout.addWidget(btn)
        return layout, line_edit
    
    return line_edit, line_edit

def update_path(line_edit, arg_name):
    if "directory" in arg_name:
        path = QFileDialog.getExistingDirectory(None, "Select Directory")
    else:
        path, _ = QFileDialog.getOpenFileName(None, "Select File")
    
    if path:
        line_edit.setText(path)

def create_plugin_ui(module):
    form = QFormLayout()
    widgets = {}
    sig = inspect.signature(module.run)
    for name, param in sig.parameters.items():
        if name in ['progress_callback', 'data_path']: continue
        label = name.replace("_", " ").title()
        if param.annotation == float:
            w = QDoubleSpinBox(); w.setValue(param.default if param.default != inspect._empty else 0.0)
        elif param.annotation == int:
            w = QSpinBox(); w.setMaximum(10000); w.setValue(param.default if param.default != inspect._empty else 0)
        elif param.annotation == bool:
            w = QCheckBox(); w.setChecked(param.default if param.default != inspect._empty else False)
        else:
            w = QLineEdit(); w.setText(str(param.default) if param.default != inspect._empty else "")
        form.addRow(label, w)
        widgets[name] = w
    return form, widgets