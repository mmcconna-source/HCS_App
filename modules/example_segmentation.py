import time

def run(data_path: str, threshold: float = 0.45, iterations: int = 10, use_gpu: bool = False, progress_callback=None):
    """
    Example HCS Module.
    The UI creates a DoubleSpinBox for threshold, SpinBox for iterations, and Checkbox for use_gpu.
    """
    print(f"Starting analysis in {data_path}...")
    for i in range(iterations):
        time.sleep(0.3) # Simulate processing
        if progress_callback:
            progress_callback.emit(int((i + 1) / iterations * 100))
    
    return "Success"