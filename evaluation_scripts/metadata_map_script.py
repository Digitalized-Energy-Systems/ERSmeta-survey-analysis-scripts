#!/usr/bin/env python3
"""
metadata_statistic_script.py

Creates a presence matrix for metadata elements across metadata JSON files.

For each element (row) and each metadata file (column) the script writes 1 if the
element is present and considered "filled" in that file, otherwise 0.

Output CSV columns:
 - element: element/property name
 - <file1>, <file2>, ... : columns per metadata file with 0/1 entries

Usage:
    python metadata_statistic_script.py --metadata_input path/to/jsons --output_csv results/element_presence.csv
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Dict, Iterable, List, Tuple

import pandas as pd


def is_value_filled(value) -> bool:
    """Return True if a JSON value should be considered 'filled'."""
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict, set, tuple)):
        return len(value) > 0
    # numbers and booleans count as filled
    return True


def load_json_files_with_names(directory: str) -> Iterable[Tuple[str, Dict]]:
    """
    Yield (basename, parsed JSON object) for every .json file in directory (skip index.html).
    Basename excludes extension and is used as column name in the output CSV.
    Files are yielded in sorted order for deterministic output.
    """
    for name in sorted(os.listdir(directory)):
        if name.lower().endswith(".json") and name != "index.html":
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        obj = json.load(fh)
                except Exception as ex:
                    print(f"Warning: failed to parse JSON file: {path} ({ex})")
                    continue
                base = os.path.splitext(name)[0]
                yield base, obj


def collect_element_names_from_schema(schema_path: str) -> List[str]:
    """Return property names from a JSON schema file if available."""
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    props = schema.get("properties", {})
    if isinstance(props, dict):
        return list(props.keys())
    return []


def compute_presence_matrix(metadata_dir: str, schema_path: str | None = None) -> pd.DataFrame:
    """
    Compute a presence matrix DataFrame.

    Rows: element names
    Columns: metadata file basenames
    Values: 1 if element is present and filled in that file, otherwise 0
    """
    files_and_objs = list(load_json_files_with_names(metadata_dir))
    if not files_and_objs:
        raise SystemExit(f"No JSON files found in directory: {metadata_dir}")

    # Determine element names (schema preferred)
    if schema_path and os.path.isfile(schema_path):
        element_names = collect_element_names_from_schema(schema_path)
    else:
        # union of top-level keys across all metadata files
        names = set()
        for _, obj in files_and_objs:
            if isinstance(obj, dict):
                names.update(obj.keys())
        element_names = sorted(names)

    # Initialize matrix data: row per element -> dict of file->0/1
    matrix: Dict[str, Dict[str, int]] = {elem: {} for elem in element_names}

    for base, obj in files_and_objs:
        for elem in element_names:
            present = 0
            if isinstance(obj, dict) and elem in obj and is_value_filled(obj[elem]):
                present = 1
            matrix[elem][base] = present

    # Build DataFrame: index element -> columns file basenames
    df = pd.DataFrame.from_dict(matrix, orient="index")
    df.index.name = "element"
    # Ensure deterministic column order (sorted by filename)
    df = df.reindex(sorted(df.columns), axis=1)
    # Convert any non-numeric to ints (safety)
    df = df.fillna(0).astype(int)

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Create element presence matrix across metadata JSON files.")
    parser.add_argument("--metadata_input", "-m", required=True, help="Directory with metadata JSON files.")
    parser.add_argument(
        "--schema",
        "-s",
        required=False,
        help="Optional path to JSON schema (uses its properties as canonical element list)."
    )
    parser.add_argument(
        "--output_csv",
        "-o",
        default="results/element_presence.csv",
        help="Path to output CSV file (default: results/element_presence.csv)."
    )
    # Default behavior: no header written. Use --header to explicitly write header row.
    parser.add_argument(
        "--header",
        action="store_true",
        help="Write header row in the output CSV (default: no header)."
    )
    args = parser.parse_args()

    metadata_input = args.metadata_input
    schema_path = args.schema
    output_csv = args.output_csv
    # default is no header unless user supplies --header
    omit_header = not args.header

    if not os.path.isdir(metadata_input):
        raise SystemExit(f"metadata_input is not a directory: {metadata_input}")

    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)

    df = compute_presence_matrix(metadata_input, schema_path)

    # Write CSV with 'element' as first column
    df_reset = df.reset_index()
    df_reset.to_csv(output_csv, index=False, header=not omit_header)
    print(f"Wrote element presence CSV to: {output_csv}")


if __name__ == "__main__":
    main()