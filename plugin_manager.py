import os
import inspect
import importlib.util
from pathlib import Path
from PyQt6.QtWidgets import QFormLayout, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit, QLabel

# UI Generation Mapping
WIDGET_MAP = {
    int: QSpinBox,
    float: QDoubleSpinBox,
    bool: QCheckBox,
    str: QLineEdit
}

def discover_plugins(directory="modules"):
    """Scans /modules and imports scripts using importlib."""
    plugins = {}
    modules_path = Path(directory)
    
    if not modules_path.exists():
        os.makedirs(modules_path)
        return plugins

    for file_path in modules_path.glob("*.py"):
        if file_path.name == "__init__.py":
            continue
            
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Every analysis module must implement a run function
        if hasattr(module, "run"):
            plugins[module_name] = module
            
    return plugins

def create_plugin_ui(module):
    """Uses introspection to build controls based on the run function."""
    layout = QFormLayout()
    widgets = {}
    
    # Introspect the 'run' function signature
    sig = inspect.signature(module.run)
    
    for name, param in sig.parameters.items():
        # Skip Reserved Keywords
        if name in ['data_path', 'progress_callback']:
            continue
            
        # Mandatory Type Hinting for UI generation
        arg_type = param.annotation
        default_value = param.default if param.default is not inspect.Parameter.empty else None
        
        # Translate Python types into PyQt6 widgets
        widget_class = WIDGET_MAP.get(arg_type, QLineEdit)
        widget = widget_class()
        
        # Initialize with Default Values
        if default_value is not None:
            if isinstance(widget, QCheckBox):
                widget.setChecked(default_value)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setRange(0, 1000000) # Scientific range
                widget.setValue(default_value)
            elif isinstance(widget, QLineEdit):
                widget.setText(str(default_value))

        # UI labeling
        label_text = name.replace("_", " ").title()
        layout.addRow(QLabel(label_text), widget)
        
        # Store references to dynamically created widgets
        widgets[name] = widget
        
    return layout, widgets