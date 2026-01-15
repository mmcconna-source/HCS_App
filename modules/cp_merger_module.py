import pandas as pd
from pathlib import Path
from typing import List, Optional
import warnings

# Metadata for UI labeling [cite: 41-44]
NAME = "Advanced Well Data Merger"
DESCRIPTION = "Merges WellID folders with duplicate column protection and separate CSV outputs."

# Standard keys for CellProfiler single-cell data [cite: 4, 11]
MERGE_KEYS = ["ImageNumber", "ObjectNumber"]

def load_and_prefix(file_path: Path, prefix: str, is_metadata_source: bool = False) -> pd.DataFrame:
    """Reads a CSV, prefixes features, and keeps merge keys intact [cite: 13-33]."""
    df = pd.read_csv(file_path, low_memory=False)
    
    # Identify metadata: start with 'Metadata_', 'ImageNumber', or 'ObjectNumber'
    metadata_cols = [c for c in df.columns if c.startswith("Metadata_") or c in MERGE_KEYS]

    if not is_metadata_source:
        # Drop all metadata except merge keys to prevent duplication during join
        drop_meta = [c for c in metadata_cols if c not in MERGE_KEYS]
        df = df.drop(columns=drop_meta, errors="ignore")

    # Prefix only the measurement (non-metadata) columns
    feature_cols = [c for c in df.columns if c not in metadata_cols]
    df = df.rename(columns={c: f"{prefix}_{c}" for c in feature_cols})
    
    for key in MERGE_KEYS:
        if key in df.columns:
            df[key] = df[key].astype("int64")
            
    return df

def run(
    data_path: str,
    output_directory: str = "Analysis_Results",
    cell_csv_name: str = "MyExpt_Cell.csv",
    cyto_csv_name: str = "MyExpt_Cytoplasm.csv",
    nuc_csv_name: str = "MyExpt_Nucleus.csv",
    image_csv_name: str = "MyExpt_Image.csv",
    final_cell_filename: str = "merged_single_cell.csv",
    final_image_filename: str = "merged_image_level.csv",
    progress_callback=None
):
    """
    Core logic for merging data across well-folders.
    Type hints 'str' for 'csv_name' or 'directory' will trigger 'Browse' buttons[cite: 32].
    """
    root = Path(data_path).resolve()
    well_folders = [f for f in root.iterdir() if f.is_dir()]
    
    if not well_folders:
        raise ValueError(f"No subfolders found in {data_path}")

    # Create output path relative to selection
    final_out = root / output_directory
    final_out.mkdir(parents=True, exist_ok=True)

    all_sc = []
    all_img = []
    total = len(well_folders)
    
    for i, folder in enumerate(well_folders):
        well_id = folder.name
        
        # 1. Image-Level: Safe assignment to avoid 'already exists' ValueError
        img_path = folder / image_csv_name
        if image_csv_name and img_path.exists():
            img_df = pd.read_csv(img_path)
            # Row ID is set to the folder name (WellID)
            img_df["Metadata_WellID"] = well_id 
            all_img.append(img_df)
            
        # 2. Single-Cell: Requires Cell, Cyto, and Nucleus to exist
        sc_paths = {"Cell": folder / cell_csv_name, "Cyto": folder / cyto_csv_name, "Nuc": folder / nuc_csv_name}
        if all(p.exists() for p in sc_paths.values()):
            c_df = load_and_prefix(sc_paths["Cell"], "Cell", is_metadata_source=True)
            cy_df = load_and_prefix(sc_paths["Cyto"], "Cytoplasm")
            n_df = load_and_prefix(sc_paths["Nuc"], "Nucleus")
            
            merged = c_df.merge(cy_df, on=MERGE_KEYS, how="left").merge(n_df, on=MERGE_KEYS, how="left")
            merged["Metadata_WellID"] = well_id
            all_sc.append(merged)

        # 3. Update UI Progress [cite: 20, 50]
        if progress_callback:
            progress_callback.emit(int(((i + 1) / total) * 100))

    # Save outputs only if data was found
    summary = []
    if all_sc:
        pd.concat(all_sc, ignore_index=True).to_csv(final_out / final_cell_filename, index=False)
        summary.append("Single-Cell CSV saved")
    
    if all_img:
        pd.concat(all_img, ignore_index=True).to_csv(final_out / final_image_filename, index=False)
        summary.append("Image-Level CSV saved")

    return f"Processed {len(well_folders)} folders. " + " & ".join(summary)