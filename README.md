# ERSmeta Evaluation Scripts

This repository contains scripts and utilities for analyzing survey data and metadata related to the metadata schema [ERSmeta](https://github.com/NFDI4Energy/ERSmeta) and the metadata support tool [SMECS](https://github.com/NFDI4Energy/SMECS). The codebase is designed to process survey CSV files, compute statistics, generate figures (boxplots, pie charts, bar charts), and analyze metadata JSON files according to a defined schema.

Related survey data are published on [Zenodo](https://doi.org/10.5281/zenodo.17935022).

## Features

- **Survey Data Analysis:**  
  - Load and filter survey responses from CSV files.
  - Calculate column statistics and System Usability Scale (SUS) scores.
  - Generate descriptive statistics and visualizations for Likert-scale questions.

- **Metadata Analysis:**  
  - Load and process metadata JSON files using a defined schema (`ersmeta_schema.json`).
  - Count and categorize metadata elements by thematic area.
  - Compute and visualize statistics for metadata sets.

- **Figure Generation:**  
  - Create publication-ready boxplots, pie charts, and bar charts as PDF and PNG files.
  - Grouped and annotated visualizations for survey and metadata results.
  - Figures are styled for easy inclusion in LaTeX documents (see below).


## Usage

1. **Install Requirements**

   Install the required Python packages:
   `pip install -r requirements.txt`

2. **Prepare Data**

   - Place your survey CSV file and metadata JSON files in the appropriate directories.
   - Ensure your metadata schema is available as `ersmeta_schema.json`.

3. **Run the Analysis**

  `python paper_script.py --input your_survey.csv --metadata_input path/to/metadata_jsons --output_dir results`

  - The script will generate all figures and statistics in the specified output directory.

## Output

- Figures are saved as both PDF and PNG files in the output directory.
- Results are suitable for direct inclusion in LaTeX documents.
- All statistics and intermediate results are saved for further analysis.

## Main Scripts
The scripts are the main entry points for running the analysis pipeline. They handle argument parsing, data loading, filtering, and orchestrates the generation of all figures and statistics.

- `evaluation_metadata.py`
  This script analyzes metadata JSON files according to a given schema (ERSmeta) and generates summary statistics and visualizations. It produces histograms and boxplots for element usage, priority, thematical areas, and cardinality, and combines all generated figures into a single PDF for reporting.

- `evaluation_survey.py`
  This script processes and analyzes survey data from a CSV file related to ERSmeta. It generates descriptive statistics, visualizations, and exports for survey responses, including demographics, prior experience, dropout reasons, usability (SUS), behavioral intention, extraction quality, feature requests, and free-text feedback. The script supports filtering participants based on metadata experience and produces publication-ready figures and summary files.

- `paper_script.py`  
  This script orchestrates the analysis and visualization of survey and metadata results for the paper on ERSmeta. It loads survey responses and metadata files, computes descriptive statistics, and generates publication-ready figures (boxplots, histograms) for inclusion in LaTeX documents. The script is designed for reproducible research and produces all outputs in a specified results directory.

- `diss_script.py`  
  This script orchestrates the analysis and visualization of survey and metadata results for the dissertation of Stephan Ferenz. It loads survey responses and metadata files, computes descriptive statistics, and generates publication-ready figures (boxplots, histograms) for inclusion in LaTeX documents. The script is designed for reproducible research and produces all outputs in a specified results directory.


## Main Function files
- `compute_column_statistics.py`, `compute_metadata_statistics.py`  
  Functions for calculating statistics on survey and metadata columns.

- `create_survey_statistics.py`
  Utilities for preparing and summarizing survey statistics.

- `create_analysis_metadata.py`  
   Utilities for preparing metadata of the current analysis.

- `print_figures.py`, `print_metadata_figures.py`  
  Contains functions for generating and saving all figures (boxplots, pie charts, bar charts) using Matplotlib.

- `write_column.py`  
  Helper functions for writing metadata and survey results to files.


## LaTeX Integration

- Figures use the Computer Modern font for seamless integration with standard LaTeX documents.
- To ensure font consistency, the following Matplotlib settings are used:
   `plt.rcParams.update({ "text.usetex": True, "font.family": "serif", "font.serif": ["Computer Modern Roman"], })`
- You need a working LaTeX installation for `text.usetex: True` to work.


## Requirements

- Python 3.7+
- See `requirements.txt` for Python package dependencies.
- LaTeX installation (for LaTeX font rendering in figures, optional but recommended).


## License
This project is licensed under a MIT license.

## Contact

For questions or contributions, please open an issue.
