import os
import pandas as pd
from pathlib import Path
from pycytominer import normalize

# Metadata Standards [cite: 41, 42, 43, 44]
NAME = "Well-Level Normalization"
DESCRIPTION = "Apply MAD-Robustize and Standardization to merged well-level CSVs."

def load_dtype_map(dtype_path: Path):
    """Internal helper to categorize columns based on the provided spec."""
    dtype_df = pd.read_csv(dtype_path)
    col_name_field = "Column_Name" if "Column_Name" in dtype_df.columns else "ColumnName"
    col_type_field = "Column_Type" if "Column_Type" in dtype_df.columns else "ColumnType"
    
    dtype_map = dict(
        zip(dtype_df[col_name_field], dtype_df[col_type_field].fillna("").str.lower())
    )
    metadata_cols = [col for col, ctype in dtype_map.items() 
                     if ctype == "metadata" or col.startswith("Metadata_")]
    feature_cols = [col for col, ctype in dtype_map.items() 
                    if ctype != "metadata" and not col.startswith("Metadata_")]
    return metadata_cols, feature_cols

def run(data_path: str, column_dtypes_path: str = "CSVs/column_dtypes.csv", progress_callback=None):
    """
    Standard Plugin Contract [cite: 10, 11, 21]
    
    Args:
        data_path: Automatically receives selected directory [cite: 16]
        column_dtypes_path: Path to the CSV defining feature/metadata types [cite: 32]
        progress_callback: PyQt signal for UI progress bar updates [cite: 17, 40]
    """
    input_dir = Path(data_path)
    dtype_path = Path(column_dtypes_path)
    
    if not dtype_path.exists():
        raise FileNotFoundError(f"Column dtypes not found at {column_dtypes_path}")

    # Load column definitions
    metadata_cols, feature_cols = load_dtype_map(dtype_path)
    
    # Identify all merged CSVs in the folder
    csv_files = list(input_dir.glob("*_joined.csv"))
    if not csv_files:
        print(f"No files ending in '_joined.csv' found in {data_path}")
        return

    total_steps = len(csv_files) * 2
    current_step = 0

    for csv_file in csv_files:
        profiles_df = pd.read_csv(csv_file, low_memory=False)
        
        # Identify columns present in this specific file
        present_features = [c for c in feature_cols if c in profiles_df.columns]
        present_metadata = [c for c in metadata_cols if c in profiles_df.columns]

        methods = ["mad_robustize", "standardize"]
        suffixes = ["_mad", "_std"]

        for method, suffix in zip(methods, suffixes):
            # Update Progress [cite: 40, 48]
            if progress_callback:
                current_step += 1
                progress = int((current_step / total_steps) * 100)
                progress_callback.emit(progress)

            # Perform Normalization
            normalized_df = normalize(
                profiles=profiles_df,
                features=present_features,
                meta_features=present_metadata,
                method=method,
                output_file=None,
            )

            # Reorder: metadata first, then features
            ordered_cols = present_metadata + [c for c in present_features if c in normalized_df.columns]
            normalized_df = normalized_df.loc[:, ordered_cols]

            # Export with distinct naming convention
            output_name = csv_file.stem + suffix + ".csv"
            output_path = input_dir / output_name
            normalized_df.to_csv(output_path, index=False)
            
    print(f"Successfully processed {len(csv_files)} files using both methods.")