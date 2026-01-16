import re
import concurrent.futures
from pathlib import Path
from collections import defaultdict
import numpy as np
from skimage import filters, io

# 1. Metadata Standards for UI Labeling [cite: 42-44]
NAME = "Smart MIP Filter"
DESCRIPTION = "Generates MIPs by filtering out-of-focus planes. Now with custom output directory support."

# 2. Plugin Contract: The run Signature [cite: 10-14]
def run(data_path: str, 
        output_folder_name: str = "Filtered_MIPs",
        methods_mapping: str = "1:laplacian, 2:variance", 
        threshold_pct: int = 75, 
        num_workers: int = 4,
        progress_callback=None):
    """
    Args:
        data_path: str: Automatically receives the selected directory.
        output_folder_name: str: Name of the sub-folder for results (UI: QLineEdit)[cite: 31, 32].
        methods_mapping: str: Maps channels to methods (e.g., '1:laplacian').
        threshold_pct: int: Focus score threshold (UI: QSpinBox)[cite: 31, 32].
        num_workers: int: CPU threads for parallel processing.
        progress_callback: Emits PyQt signals to update the UI[cite: 17, 40].
    """
    
    # --- Output Directory Logic ---
    # We combine the base data_path with the user-defined folder name
    base_path = Path(data_path)
    mip_dir = base_path / output_folder_name
    mip_dir.mkdir(parents=True, exist_ok=True)

    # --- Parse Configuration ---
    try:
        metric_config = {int(k.strip()): v.strip().lower() 
                         for pair in methods_mapping.split(',') 
                         for k, v in [pair.split(':')]}
    except Exception:
        return "Error: Invalid mapping format. Use 'ChannelID:Method, ChannelID:Method'."

    # --- Discovery Phase [cite: 35] ---
    pattern = re.compile(r'W(\d+)F(\d+)T(\d+)Z(\d+)C(\d+)\.tif')
    groups = defaultdict(list)
    for p in base_path.rglob('*.tif'):
        m = pattern.match(p.name)
        if m:
            w, f, t, z, c = map(int, m.groups())
            if c in metric_config:
                groups[(w, f, c)].append({'path': p, 'z': z})

    if not groups:
        return f"No matching images found in {data_path} for the specified channels."

    tasks = list(groups.items())
    total = len(tasks)

    # --- Internal Worker Logic ---
    def process_group(item):
        (well, field, channel), images = item
        images.sort(key=lambda x: x['z'])
        method = metric_config[channel]
        
        focus_results = []
        for img_data in images:
            img = io.imread(img_data['path'])
            if img.ndim > 2: img = img[..., 0]
            
            # Focus Calculation logic
            if method == 'laplacian':
                score = np.var(filters.laplace(img))
            else:
                score = np.var(img) / np.mean(img) if np.mean(img) != 0 else 0
            
            focus_results.append({'score': score, 'image': img, 'path': img_data['path']})

        scores = np.array([r['score'] for r in focus_results])
        threshold = np.max(scores) * (threshold_pct / 100.0)
        valid_planes = [r for r in focus_results if r['score'] >= threshold]

        if valid_planes:
            mip_img = np.max(np.stack([r['image'] for r in valid_planes]), axis=0)
            # Use regex to rename Z-plane to Z000 for the MIP output
            mip_name = re.sub(r'Z\d{3}', 'Z000', valid_planes[0]['path'].name)
            io.imsave(mip_dir / mip_name, mip_img, check_contrast=False)
        return True

    # --- Execution Workflow [cite: 33, 34, 39] ---
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        for i, _ in enumerate(executor.map(process_group, tasks)):
            if progress_callback:
                # Signal communication between Worker and GUI 
                progress_callback.emit(int(((i + 1) / total) * 100))

    return f"Completed MIPs for {total} stacks. Results saved in: {mip_dir}"