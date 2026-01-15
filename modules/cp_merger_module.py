import pandas as pd
from pathlib import Path

NAME = "HCS Master Aggregator"
DESCRIPTION = "Merges Cell, Cyto, and Nucleus CSVs across all wells recursively."

MERGE_KEYS = ["ImageNumber", "ObjectNumber"]

def load_and_prefix(file_path: Path, prefix: str, is_metadata_source: bool = False) -> pd.DataFrame:
    df = pd.read_csv(file_path, low_memory=False)
    metadata_cols = [c for c in df.columns if c.startswith("Metadata_") or c in MERGE_KEYS]
    if not is_metadata_source:
        drop_meta = [c for c in metadata_cols if c not in MERGE_KEYS]
        df = df.drop(columns=drop_meta, errors="ignore")
    feature_cols = [c for c in df.columns if c not in metadata_cols]
    df = df.rename(columns={c: f"{prefix}_{c}" for c in feature_cols})
    return df

def run(
    data_path: str,
    output_directory: str = "Analysis_Results",
    cell_csv_name: str = "MyExpt_Cell.csv",
    cyto_csv_name: str = "MyExpt_Cytoplasm.csv",
    nuc_csv_name: str = "MyExpt_Nucleus.csv",
    image_csv_name: str = "MyExpt_Image.csv",
    final_single_cell_name: str = "master_single_cell.csv",
    final_image_level_name: str = "master_image_level.csv",
    progress_callback=None
):
    root = Path(data_path).resolve()
    out_dir = Path(output_directory)
    if not out_dir.is_absolute():
        out_dir = root / output_directory
    out_dir.mkdir(parents=True, exist_ok=True)
    
    well_folders = [f for f in root.iterdir() if f.is_dir() and f != out_dir]
    sc_list, img_list = [], []
    
    for i, folder in enumerate(well_folders):
        well_id = folder.name
        
        # Image data aggregation
        img_f = folder / image_csv_name
        if img_f.exists():
            idf = pd.read_csv(img_f)
            idf["Metadata_WellID"] = well_id # Safe assignment prevents ValueError
            img_list.append(idf)
            
        # Single-cell 3-way merge
        c, cy, n = folder/cell_csv_name, folder/cyto_csv_name, folder/nuc_csv_name
        if all(p.exists() for p in [c, cy, n]):
            m = load_and_prefix(c, "Cell", True).merge(
                load_and_prefix(cy, "Cytoplasm"), on=MERGE_KEYS).merge(
                load_and_prefix(n, "Nucleus"), on=MERGE_KEYS)
            m["Metadata_WellID"] = well_id
            sc_list.append(m)

        if progress_callback:
            progress_callback.emit(int(((i + 1) / len(well_folders)) * 100))

    if sc_list: pd.concat(sc_list, ignore_index=True).to_csv(out_dir/final_single_cell_name, index=False)
    if img_list: pd.concat(img_list, ignore_index=True).to_csv(out_dir/final_image_level_name, index=False)
    
    return f"Export Complete!\nSaved to: {out_dir}"