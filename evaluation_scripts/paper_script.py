"""
paper_script.py

This script orchestrates the analysis and visualization of survey and metadata results for the ERSmeta paper.
It loads survey responses and metadata files, computes descriptive statistics, and generates publication-ready
figures (boxplots, histograms) for inclusion in LaTeX documents. The script is designed for reproducible
research and produces all outputs in a specified results directory.

Main Steps:
- Loads survey data from a CSV file and metadata from JSON files.
- Filters survey responses to include only completed surveys.
- Generates grouped boxplots for survey questions on descriptions and value vocabularies.
- Loads the metadata schema and analyzes the presence of elements across metadata sets.
- Categorizes and visualizes element counts by thematical area.
- Computes and visualizes System Usability Scale (SUS) scores for all participants and subgroups.
- Maps Likert-scale responses to numeric values and computes row-wise means for composite variables.
- Generates additional boxplots for perceived usefulness, ease of use, output quality, and behavioral intention.
- All figures are saved as PDF files in the output directory, using Computer Modern font for LaTeX compatibility.

Arguments:
    --input: Path to the survey CSV file (default: "your_large_file.csv")
    --metadata_input: Path to the directory containing metadata JSON files (default: ".")
    --output_dir: Path to the output directory for results (default: "results")

Dependencies:
    - pandas, argparse, os, json, matplotlib
    - Project modules: write_column, compute_column_statistics, print_figures,
      create_analysis_metadata, create_survey_statistics, print_metadata_figures, compute_metadata_statistics

Outputs:
    - PDF figures for survey and metadata analysis in the output directory
    - A metadata file documenting the analysis run

Usage Example:
    python paper_script.py --input survey.csv --metadata_input metadata_dir --output_dir results

"""
import pandas as pd
import argparse
import os
import json
import matplotlib.pyplot as plt

from write_column import *
from compute_column_statistics import *
from print_figures import *
from create_analysis_metadata import *
from create_survey_statistics import *

from print_metadata_figures import *
from compute_metadata_statistics import *

# Set up argument parser
parser = argparse.ArgumentParser(description="Load and analyze a CSV file.")
parser.add_argument(
    "--input",
    type=str,
    default=None,
    help="Path to the CSV file (default: your_large_file.csv)"
)
parser.add_argument(
    "--metadata_input",
    type=str,
    default=None,
    help="Path to the metadata files"
)
parser.add_argument(
    "--metadata_map",
    type=str,
    default=None,
    help="Path to the metadata map file (columns with 1/0 per metadata set)"
)
parser.add_argument(
    "--output_dir",
    type=str,
    default="results",
    help="Path to the output directory"
)
args = parser.parse_args()

# Ensure the output directory exists
os.makedirs(args.output_dir, exist_ok=True)

# Configurate matplotlib:
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman"],
})

# Write metadata about the analysis run
write_metadata_file(
    args.output_dir,
    args.input,
    args.metadata_input
)

# Load survey data
evaluation_df = pd.read_csv(args.input, low_memory=False)

# Filter to only completed surveys
evaluation_df = evaluation_df[(evaluation_df['lastpage'] == 12)]

#######################
# Generate joined figure for description of elements and value vocabularies with line in between
boxplots_metadata = {}
boxplots_metadata['A_description_value_voc']={
    "columns_description": {
        'G01Q20[SQ002]':'I find the descriptions useful for creating the metadata.',
        'G01Q20[SQ003]':'Using the descriptions enables me to describe my research software more quickly.',
        'G01Q20[SQ004]':'I thought there was too much inconsistency in the metadata elements.',
        'G01Q20[SQ005]':'Given the descriptions, it is easy for me to create metadata for my research software.',
        'G05Q21[SQ002]':'I find the provided lists to be flexible to use it to describe my research software.',
        'G05Q21[SQ003]':'I find it easy to use provided lists to describe my research software in the way I want.',
        'G05Q21[SQ004]':'Using the provided lists to describe my research software would enable me to enrich my software with metadata more quickly.',
        'G05Q21[SQ005]':'I find the provided lists useful to describe my research software.'
    },
    "columns_positive_counting": { 
        'G05Q21[SQ004]':True,
        'G05Q21[SQ005]':True,
        'G01Q20[SQ002]':True,
        'G01Q20[SQ003]':True,
        'G01Q20[SQ004]':False,
        'G01Q20[SQ005]':True,
        'G05Q21[SQ002]':True,
        'G05Q21[SQ003]':True,
        'G05Q21[SQ004]':True,
        'G05Q21[SQ005]':True
    },
    "groups": {
        "Descriptions": ['G01Q20[SQ002]','G01Q20[SQ003]','G01Q20[SQ004]','G01Q20[SQ005]'],
        "Value Vocabularies": ['G05Q21[SQ002]','G05Q21[SQ003]','G05Q21[SQ004]','G05Q21[SQ005]']
        }
}

# Create all boxplots for the columns
for file_name, data in boxplots_metadata.items():
    columns = data["columns_description"].keys()
    generate_pdf_with_boxplots(
        evaluation_df,
        columns,
        f"{args.output_dir}/{file_name}.pdf",
        data["columns_description"],
        couting_factor=data["columns_positive_counting"],
        groups=data["groups"]
    )

#################
# Figure: Element counts per metadata set categorized in thematical area
if args.metadata_map is not None or args.metadata_input is not None:
    json_path = "./ersmeta_schema.json" 
    if not os.path.isfile(json_path):
        raise SystemExit(f"Schema file not found: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        metadata_schema = json.load(f)
    element_names = list(metadata_schema['properties'].keys())

    # Define thematical areas for elements (shared by both input methods)
    element_types = {
        'General': get_element_subset(element_names, 'name', 'inLanguage'),
        'GeneralDescription': get_element_subset(element_names, 'abstract', 'copyrightHolder'),
        'Provenance': get_element_subset(element_names, 'dateCreated', 'maintainer'),
        'Usage': get_element_subset(element_names, 'downloadUrl', 'example'),
        'Community': get_element_subset(element_names, 'usedInPublication', 'communityInteractions'),
        'Quality': get_element_subset(element_names, 'review', 'validation'),
        'Interface': get_element_subset(element_names, 'output', 'usedData'),
        'Functionalities': get_element_subset(element_names, 'purpose', 'usedOptimization'),
        'TechnicalRequirements': get_element_subset(element_names, 'typicalHardware', 'fileSize'),
        'MetaMetadata': get_element_subset(element_names, 'metadataVersion', 'sdLicense')
    }
    element_types = dict(reversed(list(element_types.items())))

    # Series with the number of elements for each element type (max possible per area)
    max_series = pd.Series({name: len(element_list) for name, element_list in element_types.items()})

    # df_element_type_counts will be created by one of the branches below
    df_element_type_counts = None

    # Branch A: aggregated per-element presence-map CSV (rows = element, cols = metadata sets)
    if args.metadata_map is not None:
        # Read CSV where first column is element name and remaining columns are file identifiers
        # Expect a header row with file basenames; if your map has no header re-run generator with header or pass a header.
        df_map = pd.read_csv(args.metadata_map, index_col=0, low_memory=False)

        # Normalize values to 0/1 ints (tolerant to "0"/"1", True/False, NaN)
        df_map = df_map.fillna(0)
        # Attempt coercion: treat any non-zero/False-like as 1
        df_map = df_map.applymap(lambda v: 1 if (str(v).strip() not in ("", "0", "False", "false", "nan", "None")) else 0).astype(int)

        # Build per-file (per-metadata-set) thematic counts: rows = metadata set ids, cols = thematic areas
        area_series_map = {}
        for area_name, elems in element_types.items():
            # pick only elements present in the map
            elems_in_map = [e for e in elems if e in df_map.index]
            if elems_in_map:
                # sum presence across the elements for each file => Series indexed by file basename
                s = df_map.loc[elems_in_map].sum(axis=0).astype(int)
            else:
                # no elements from this area in the map -> zero series with same index as df_map.columns
                s = pd.Series(0, index=df_map.columns, dtype=int)
            area_series_map[area_name] = s

        # Compose DataFrame: index = metadata set (file basenames), columns = thematic areas
        df_element_type_counts = pd.DataFrame(area_series_map)
        # Ensure column order matches element_types order
        df_element_type_counts = df_element_type_counts[list(element_types.keys())]

    # Branch B: raw metadata JSON directory -> compute per-file counts per thematic area (one row per file)
    elif args.metadata_input is not None:
        # Load all metadata JSON files from the input directory into an array
        metadata_files = [
            f for f in os.listdir(args.metadata_input)
            if f != 'index.html' and os.path.isfile(os.path.join(args.metadata_input, f))
        ]

        metadata_list = []
        for filename in metadata_files:
            file_path = os.path.join(args.metadata_input, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                metadata_list.append(metadata)

        # Create a DataFrame with the element counts for all element_types
        element_type_counts = [
            count_elements_per_metadata(element_list, metadata_list, name)
            for name, element_list in element_types.items()
        ]

        df_element_type_counts = pd.concat(element_type_counts, axis=1)   

    save_element_type_boxplots(
        df_element_type_counts, 
        os.path.join(args.output_dir, 'B_element_thematical_areas.pdf'), 
        max_series=max_series,
        ylabel="Thematical Areas of Elements",
        xlabel="Filled Elements",
        plot_type="dot")  

# Figure SUS Score: Joined and Separate
# Compute SUS scores for all, with, and without metadata experience
evaluation_df_with_md_experience = evaluation_df[
        evaluation_df['G02Q06'].notna() & (evaluation_df['G02Q06'] != 'I am not familiar with metadata schemas.')
    ]
evaluation_df_without_md_experience = evaluation_df[
        (evaluation_df['G02Q06'] == 'I am not familiar with metadata schemas.')
    ]

columns_positive_counting = { 
    'G04Q11[SQ010]':True,
    'G04Q11[SQ011]':False,
    'G04Q11[SQ002]':True,
    'G04Q11[SQ003]':False,
    'G04Q11[SQ004]':True,
    'G04Q11[SQ005]':False,
    'G04Q11[SQ006]':True,
    'G04Q11[SQ007]':False,
    'G04Q11[SQ008]':True,
    'G04Q11[SQ009]':False,
    'G04Q11[SQ010]':True,
    'G04Q11[SQ011]':False
}
sus_data_total = calculate_sus(evaluation_df, columns_positive_counting)
sus_data_with_md_experience = calculate_sus(evaluation_df_with_md_experience, columns_positive_counting)
sus_data_without_md_experience = calculate_sus(evaluation_df_without_md_experience, columns_positive_counting)

sus_dict = {
    "Participants without metadata experience": sus_data_without_md_experience,
    "Participants with metadata experience": sus_data_with_md_experience,
    "All participants":sus_data_total}

generate_pdf_sus(sus_dict, f"{args.output_dir}/C_SUS.pdf")

# Joined figure: usefulness of elements, impression on the amount of elements
likert_columns = ['G05Q19[SQ002]', 'G05Q19[SQ003]','G05Q19[SQ004]', 'G05Q19[SQ005]','G05Q19[SQ007]', 'G05Q19[SQ008]','G05Q19[SQ009]', 'G05Q19[SQ010]']

# Map Likert-scale columns to numeric values
evaluation_df[[col for col in likert_columns]] =  evaluation_df[likert_columns].applymap(LIKERT_MAPPING.get)

# Compute row-wise means for composite variables
evaluation_df['G05Q19[SQ023]'] = evaluation_df[['G05Q19[SQ002]', 'G05Q19[SQ003]']].mean(axis=1)
evaluation_df['G05Q19[SQ045]'] = evaluation_df[['G05Q19[SQ004]', 'G05Q19[SQ005]']].mean(axis=1)
evaluation_df['G05Q19[SQ078]'] = evaluation_df[['G05Q19[SQ007]', 'G05Q19[SQ008]']].mean(axis=1)
evaluation_df['G05Q19[SQ910]'] = evaluation_df[['G05Q19[SQ009]', 'G05Q19[SQ010]']].mean(axis=1)

boxplots_metadata['D_Elements']={
    "columns_description": {
        'G05Q18[SQ002]':'I find the overall number of elements useful to describe my research software',
        'G05Q18[SQ003]':'The amount of elements is too high',
        'G05Q19[SQ023]':'Perceived Usefulness: 1) Using the metadata schema to describe my research software would enable me to enrich my software with metadata more quickly. 2) I find the metadata schema useful to describe my research software.',
        'G05Q19[SQ045]':'Perceived Ease of Use: 1) I find it easy to use the metadata schema to describe my research software in the way I want. 2) I find the metadata schema to be flexible to use it.',
        'G05Q19[SQ006]':'I missed certain elements in the metadata schema to describe my research software.',
        'G05Q19[SQ078]':'Output Quality: 1) The quality of the created metadata is high. 2) I have no problem with the quality of the created metadata.',
        'G05Q19[SQ910]':'Behavioral Intention: 1) Assuming I have access to the metadata schema, I intend to use it to describe my software. 2) Given that I have access to the metadata schema, I predict that I would use it to describe my software.',
    },
    "columns_positive_counting": { 
        'G05Q18[SQ002]':True,
        'G05Q18[SQ003]':False,
        'G05Q19[SQ023]':True,
        'G05Q19[SQ045]':True,
        'G05Q19[SQ006]':False,
        'G05Q19[SQ078]':True,
        'G05Q19[SQ910]':True,
    },
    "groups": {
        "Usefulness of Elements": ['G05Q19[SQ023]','G05Q19[SQ045]','G05Q19[SQ006]','G05Q19[SQ078]','G05Q19[SQ910]'],
        "Amount of\nElements": ['G05Q18[SQ002]', 'G05Q18[SQ003]']
        }
}

# Create all boxplots for the columns
for file_name, data in boxplots_metadata.items():
    columns = data["columns_description"].keys()
    generate_pdf_with_boxplots(
        evaluation_df,
        columns,
        f"{args.output_dir}/{file_name}.pdf",
        data["columns_description"],
        couting_factor=data["columns_positive_counting"],
        groups=data["groups"],
        plot_type="dot"
    )