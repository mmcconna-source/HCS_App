import os
import pandas as pd
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from pycytominer.cyto_utils.features import infer_cp_features

# Metadata for UI Labeling [cite: 41, 42]
NAME = "CellProfiler Data Merger"
DESCRIPTION = "Merges Cell, Cytoplasm, and Nucleus CSVs from multiple folders into a single master dataset."

# Internal configuration for CellProfiler output structure
COMPARTMENT_FILES = {
    "Cell": "MyExpt_Cell.csv",
    "Cytoplasm": "MyExpt_Cytoplasm.csv",
    "Nucleus": "MyExpt_Nucleus.csv",
}
MERGE_KEYS = ["ImageNumber", "ObjectNumber"]

def find_profile_dirs(root: Path) -> Iterable[Path]:
    """Yield directories containing all required compartment CSVs."""
    cell_name = COMPARTMENT_FILES["Cell"]
    cyto_name = COMPARTMENT_FILES["Cytoplasm"]
    nuc_name = COMPARTMENT_FILES["Nucleus"]

    for cell_path in root.rglob(cell_name):
        folder = cell_path.parent
        if (folder / cyto_name).is_file() and (folder / nuc_name).is_file():
            yield folder

def load_compartment(file_path: Path, prefix: str, keep_metadata: bool) -> pd.DataFrame:
    """Read CSV, drop redundant metadata, and prefix feature columns."""
    df = pd.read_csv(file_path, low_memory=False)

    try:
        metadata_cols = set(infer_cp_features(df, metadata=True))
    except ValueError:
        metadata_cols = set()
    metadata_cols.update(MERGE_KEYS)

    if not keep_metadata:
        drop_meta = [c for c in metadata_cols if c not in MERGE_KEYS]
        df = df.drop(columns=drop_meta, errors="ignore")

    feature_cols = [c for c in df.columns if c not in metadata_cols]
    rename_map = {c: f"{prefix}_{c}" for c in feature_cols}
    df = df.rename(columns=rename_map)

    for key in MERGE_KEYS:
        df[key] = df[key].astype("int64")

    return df

def run(
    data_path: str, 
    output_dir: str = "output", 
    filename: str = "merged_single_cells.csv", 
    progress_callback=None
):
    """
    Plugin execution logic.
    
    Args:
        data_path: Provided by UI via 'data_path' reserved keyword.
        output_dir: UI generates a QLineEdit[cite: 32].
        filename: UI generates a QLineEdit[cite: 32].
        progress_callback: PyQt signal for progress bars[cite: 17].
    """
    root = Path(data_path).resolve()
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)
    
    merged_tables: List[pd.DataFrame] = []
    
    # 1. Discovery
    all_dirs = list(find_profile_dirs(root))
    total_folders = len(all_dirs)
    
    if total_folders == 0:
        raise ValueError(f"No valid CellProfiler folders found in {data_path}")

    # 2. Processing
    for i, profile_dir in enumerate(all_dirs):
        comp_paths = {name: profile_dir / fname for name, fname in COMPARTMENT_FILES.items()}
        
        # Load and merge compartments
        cell_df = load_compartment(comp_paths["Cell"], "Cell", True)
        cyto_df = load_compartment(comp_paths["Cytoplasm"], "Cytoplasm", False)
        nuc_df = load_compartment(comp_paths["Nucleus"], "Nucleus", False)

        merged = (
            cell_df.merge(cyto_df, on=MERGE_KEYS, how="left", suffixes=("", "_DROP"))
            .merge(nuc_df, on=MERGE_KEYS, how="left", suffixes=("", "_DROP2"))
        )

        # Traceability metadata
        source_col = pd.Series(str(profile_dir), index=merged.index, name="Metadata_SourceFolder")
        merged = pd.concat([merged, source_col], axis=1)

        # Cleanup
        drop_cols = [c for c in merged.columns if c.endswith("_DROP") or c.endswith("_DROP2")]
        if drop_cols:
            merged = merged.drop(columns=drop_cols)

        merged_tables.append(merged)
        
        # 3. Progress Update [cite: 40, 48]
        if progress_callback:
            progress = int(((i + 1) / total_folders) * 100)
            progress_callback.emit(progress)

    # 4. Final Aggregation
    combined = pd.concat(merged_tables, ignore_index=True)
    combined.to_csv(out_path / filename, index=False)
    
    return f"Successfully merged {total_folders} folders into {filename}"