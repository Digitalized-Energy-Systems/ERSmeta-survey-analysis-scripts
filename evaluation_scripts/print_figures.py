"""
print_figures.py

This module provides functions for generating publication-ready figures (boxplots, pie charts, bar charts)
from survey and metadata analysis using Matplotlib and pandas. It is designed for use in the ERSmeta
evaluation pipeline and supports Likert-scale data, grouped visualizations, and LaTeX-compatible output.

Main Features:
- Horizontal boxplots for Likert-scale survey responses, with groupings, background regions, and annotated statistics.
- Pie charts for categorical distributions, with descriptive labels and value counts.
- Bar charts for "yes" counts across multiple columns.
- Utilities for combining multiple PDF figures into a single report.
- All figures are saved as both PDF and PNG files for easy inclusion in LaTeX documents.

Functions:
- _plot_boxplots_with_background: Internal helper for boxplot rendering with background and group headings.
- generate_pdf_with_boxplots: Create a multi-row boxplot PDF for multiple columns.
- generate_pdf_with_boxplot_for_series: Create a single boxplot PDF for a data series.
- generate_pdf_sus: Visualize System Usability Scale (SUS) scores as a boxplot with background categories.
- plot_column_pie_chart_pdf: Generate a pie chart for a single column's value distribution.
- plot_pie_chart_from_value_counts: Generate a pie chart from a value_counts Series.
- plot_yes_counts_bar_chart_pdf: Generate a bar chart for "yes" counts in specified columns.
- combine_pdfs_in_folder: Merge all PDF files in a folder into a single PDF.

Assumptions and Notes:
- Likert-scale mapping is defined in LIKERT_MAPPING and used throughout for survey data.
- All output figures are intended for academic publication and LaTeX integration.
- Requires: pandas, numpy, matplotlib, PyPDF2

"""
import pandas as pd
import numpy as np
import textwrap
import os

import matplotlib.pyplot as plt
import matplotlib.lines as mlines

from PyPDF2 import PdfMerger
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch

# Mapping for Likert-scale responses to numeric values
LIKERT_MAPPING = {
    "Strongly Disagree": 1,
    "Disagree": 2,
    "Neutral": 3,
    "Agree": 4,
    "Strongly Agree": 5
}
LIKERT_KEYS = set(LIKERT_MAPPING.keys())
LIKERT_LABELS = [
    "Strongly\nDisagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly\nAgree"
]
LIKERT_TICKS = list(LIKERT_MAPPING.values())

def is_likert_column(series, likert_keys):
    """Return True if all non-null values in the series are Likert keys."""
    unique_vals = set(series.dropna().unique())
    return unique_vals.issubset(likert_keys)

def boxes_overlap(box1, box2):
    """
    Returns True if two boxes overlap.
    Each box is a tuple/list: (x, y, width, height), where (x, y) is the center.
    """
    
    if min_distance_between_boxes(box1, box2) > 0.1:
        return False
    else:
        return True

def min_distance_between_boxes(box1, box2):
    """
    Returns the minimum distance between two boxes.
    Each box is a tuple/list: (x, y, width, height), where (x, y) is the center.
    If boxes overlap, the distance is 0.
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    # Calculate the half-widths and half-heights
    hw1, hh1 = w1 / 2, h1 / 2
    hw2, hh2 = w2 / 2, h2 / 2

    # Calculate the distance between box edges along x and y
    dx = max(abs(x1 - x2) - (hw1 + hw2), 0)
    dy = max(abs(y1 - y2) - (hh1 + hh2), 0)

    # If boxes overlap, dx or dy will be 0, so distance is 0
    return np.hypot(dx, dy)

def _resolve_horizontal_overlap(boxes, ax, step=0.01, max_attempts=30):
    """
    Shift overlapping boxes left/right in display (pixel) coordinates until no overlap remains.
    Each box: (x, y, width, height) in axes coordinates.
    Returns new list of (x, y, width, height) in axes coordinates.
    """
    
    # Work on a copy to avoid mutating the input
    boxes_shifted = [list(box) for box in boxes]

    for attempt in range(max_attempts):
        moved = False
        n = len(boxes_shifted)
        for i in range(n):
            for j in range(i + 1, n):
                if boxes_overlap(boxes_shifted[i], boxes_shifted[j]):
                    # Determine which box is left and which is right
                    if boxes_shifted[i][0] <= boxes_shifted[j][0]:
                        left_idx, right_idx = i, j
                    else:
                        left_idx, right_idx = j, i
                    # Shift left box further left, right box further right
                    boxes_shifted[left_idx][0] -= step / 2
                    boxes_shifted[right_idx][0] += step / 2
                    moved = True

    return boxes_shifted

def _plot_boxplots_with_background(
    ax,
    boxplot_data,
    ytick_labels,
    means,
    variances,
    overall_title=None,
    couting_factor=None,
    columns=None,
    show_ylabels=True,
    group_names=None,
    group_lengths=None,
    fig=None,
    plot_type="box"  # "box" or "dot"
):
    """
    Internal helper to plot horizontal boxplots with background color regions per row.
    Supports group headings, mean/variance annotation, and custom background for positive/negative items.

    Args:
        ax (matplotlib.axes.Axes): The axes to plot on.
        boxplot_data (list of pd.Series): Data for each boxplot.
        ytick_labels (list of str): Y-tick labels for each boxplot.
        means (list of float): Mean values for annotation.
        variances (list of float): Variance values for annotation.
        overall_title (str, optional): Title for the plot.
        couting_factor (dict, optional): Dict mapping column names to bool for background direction.
        columns (list, optional): List of column names (for background coloring).
        show_ylabels (bool): Whether to show y-tick labels.
        group_names (list, optional): Names of groups for grouped boxplots.
        group_lengths (list, optional): Lengths of each group.
        fig (matplotlib.figure.Figure, optional): Figure object for setting suptitle.
        plot_type (str): "box" (default) draws boxplots, "dot" draws dot-plots (scatter with jitter).
    """

    num_plots = len(boxplot_data)
    if columns is None:
        columns = [str(i) for i in range(num_plots)]
    if couting_factor is None:
        couting_factor = {}

    # Draw background color regions for each row based on couting_factor
    for i, col in enumerate(columns):
        y_bottom = i + 0.5
        y_top = i + 1.5
        is_normal = couting_factor.get(col, True)
        if is_normal:
            # Not acceptable (1-3)
            ax.axvspan(1, 3, ymin=(y_bottom-0.5)/num_plots, ymax=(y_top-0.5)/num_plots, color='#ffcccc', alpha=0.4)
            # Acceptable (3-5)
            ax.axvspan(3, 5, ymin=(y_bottom-0.5)/num_plots, ymax=(y_top-0.5)/num_plots, color='#d9ead3', alpha=0.4)
        else:
            # Acceptable (1-3)
            ax.axvspan(1, 3, ymin=(y_bottom-0.5)/num_plots, ymax=(y_top-0.5)/num_plots, color='#d9ead3', alpha=0.4)
            # Not acceptable (3-5)
            ax.axvspan(3, 5, ymin=(y_bottom-0.5)/num_plots, ymax=(y_top-0.5)/num_plots, color='#ffcccc', alpha=0.4)

    # Create horizontal boxplots
    # bplots = ax.boxplot(
    #     boxplot_data,
    #     vert=False,
    #     patch_artist=True,
    #     labels=ytick_labels if show_ylabels else [''] * len(ytick_labels),
    #     showmeans=True,
    #     meanline=True,
    #     medianprops={'linewidth': 3, 'color': 'red', 'linestyle': 'solid'},
    #     meanprops={'linewidth': 3, 'color': 'orange', 'linestyle': 'solid'},
    #     widths=0.5
    # )

    # if show_ylabels:
    #     ax.set_yticklabels(ytick_labels, fontsize=10)
    # else:
    #     ax.set_yticklabels([])

        rng = np.random.default_rng(seed=0)  # deterministic jitter
    jitter_scale = 0.08 if num_plots <= 10 else max(0.03, 0.08 * 10 / num_plots)

 # Branch: boxplots or dot-plots
    if plot_type == "box":
        # Create horizontal boxplots
        bplots = ax.boxplot(
            boxplot_data,
            vert=False,
            patch_artist=True,
            labels=ytick_labels if show_ylabels else [''] * len(ytick_labels),
            showmeans=True,
            meanline=True,
            medianprops={'linewidth': 3, 'color': 'red', 'linestyle': 'solid'},
            meanprops={'linewidth': 3, 'color': 'orange', 'linestyle': 'solid'},
            widths=0.5
        )

        # Set y-labels (boxplot already used labels but ensure font size)
        if show_ylabels:
            ax.set_yticklabels(ytick_labels, fontsize=10)
        else:
            ax.set_yticklabels([])

    else:
        # Dot-plot implementation (scatter with vertical jitter)
        rng = np.random.default_rng(seed=0)  # deterministic jitter
        jitter_scale = 0.08 if num_plots <= 10 else max(0.03, 0.08 * 10 / num_plots)

        y_positions = []
        for i, series in enumerate(boxplot_data, start=1):
            data = np.array(series.dropna(), dtype=float)
            if data.size > 0:
                jitter = rng.normal(0, jitter_scale, size=data.size)
                ax.scatter(
                    data, np.full(data.shape, i) + jitter,
                    color='black',
                    alpha=0.55,
                    s=18,
                    linewidths=0
                )
            y_positions.append(i)

        # Configure y-ticks / labels for dot plot
        if show_ylabels:
            ax.set_yticks(y_positions)
            ax.set_yticklabels(ytick_labels, fontsize=10)
        else:
            ax.set_yticks(y_positions)
            ax.set_yticklabels([''] * len(y_positions))

    ax.set_xticks(LIKERT_TICKS)
    ax.set_xticklabels(LIKERT_LABELS, rotation=0)

    # Annotate mean and variance, and draw mean/median markers for both plot types
    for i, (mean, var, series) in enumerate(zip(means, variances, boxplot_data), start=1):
        # mean/median markers (computed from series to be consistent)
        try:
            median = np.nanmedian(np.array(series.dropna(), dtype=float))
        except Exception:
            median = np.nan

        if not np.isnan(mean):
            ax.plot(mean, i, marker='D', color='orange', markersize=8, label='_nolegend_')
        if not np.isnan(median):
            ax.plot(median, i, marker='s', color='red', markersize=6, label='_nolegend_')

        # right-side annotation
        if not np.isnan(mean):
            ax.text(LIKERT_TICKS[-1] + 0.3, i, f"mean: {mean:.2f}\nvar: {var:.2f}", va='center', fontsize=10)

    # Draw dotted line between groups and add group headings
    if group_names and group_lengths and len(group_lengths) > 1:
        y_offset = 0
        for idx, (gname, glen) in enumerate(zip(group_names, group_lengths)):
            # Add rotated group heading
            #x_pos = -0.52  # Position to the left of y-axis
            x_pos = -1.27  # Position to the left of y-axis
            y_center = y_offset + (glen) + 0.3
            #y_center = y_offset + (glen)

            if gname == "Usefulness of Elements":
                y_center = y_center - 1
            elif gname == "Descriptions":
                y_center = y_center - 0.7
            elif gname == "Value Vocabularies":
                y_center = y_center - 0.3

            ax.text(
                x_pos, y_center, gname,
                va='center', ha='right',
                fontsize=12, fontweight='bold',
                rotation=90, rotation_mode='anchor',
                transform=ax.get_yaxis_transform()
            )
            y_offset += glen
            # Draw dotted line after each group except the last
            if idx < len(group_lengths) - 1:
                ax.axhline(
                    y=y_offset + 0.5, 
                    color='black', 
                    linestyle='dotted', 
                    linewidth=1, 
                    xmin=x_pos-0.1,  # extend a bit to the left of the axes
                    xmax=1.3,
                    clip_on=False
                )

    # Create custom legend handles for mean and median
    median_line = mlines.Line2D([], [], color='red', linewidth=3, linestyle='solid', label='Median')
    mean_line = mlines.Line2D([], [], color='orange', linewidth=3, linestyle='solid', label='Mean')
    handles = [mean_line, median_line]

    # Add the legend below the x-axis
    ax.legend(
        handles=handles,
        loc='upper center',
        bbox_to_anchor=(0.5, -0.1),  # Place legend below the axes
        ncol=len(handles),
        frameon=True
    )
    if overall_title and fig:
        # Adjust width as needed (e.g., 60 characters)
        wrapped_title = "\n".join(textwrap.wrap(overall_title, width=70))
        fig.suptitle(wrapped_title, fontsize=16, fontweight='bold', y=0.98, x=0.1)


    #plt.subplots_adjust(left=0.25, right=0.55, top=0.92, bottom=0.10)

    #plt.tight_layout(rect=[0.15, 0, 0.95, 1])

def generate_pdf_with_boxplots(
    df,
    columns,
    output_pdf,
    column_description_dict=None,
    overall_title=None,
    couting_factor=None,
    groups=None,
    plot_type="box"  # "box" or "dot"
):
    """
    Generates a PDF with one row per column: description (or name), mean, variance, and a horizontal box plot.
    Converts Likert-scale enums to numeric values for statistics, but displays original labels on the x-axis.
    Supports grouping and background coloring for positive/negative items.

    Args:
        df (pd.DataFrame): DataFrame with data.
        columns (list of str): Columns to analyze.
        output_pdf (str): Path to output PDF file.
        column_description_dict (dict, optional): Dictionary mapping column names to descriptions.
        overall_title (str, optional): Overall title to display as a single title page.
        couting_factor (dict, optional): Dict mapping column names to bool for background direction.
        groups (dict, optional): Grouping of columns for visual separation.
    """
    # Invert the order of columns at the beginning
    columns = list(columns)[::-1]

    boxplot_data = []
    ytick_labels = []
    means = []
    variances = []

    max_desc_width = 60
    max_desc_lines = 5

    # Deal with group information
    if groups is not None:
        # Build ensure the group order matches the column order
        column_to_group = {}
        for group_name, cols in groups.items():
            for col in cols:
                column_to_group[col] = group_name
        group_order = []
        seen = set()
        for col in columns:
            group = column_to_group.get(col)
            if group and group not in seen:
                group_order.append(group)
                seen.add(group)
        group_names = group_order
        group_columns = [groups[name] for name in group_names]
        group_lengths = [len(cols) for cols in group_columns]
    else:
        group_names = None
        group_lengths = None

    # Calculate total number of valid answers (non-NaN) across all columns
    n_answers = int(df[columns].notna().any(axis=1).sum())
    if overall_title:
        overall_title = f"{overall_title} (n={n_answers})"

    max_lines = 1
    for col in columns:
        col_data = df[col]
        if is_likert_column(col_data, LIKERT_KEYS):
            data = col_data.map(LIKERT_MAPPING).dropna()
        else:
            data = pd.to_numeric(col_data, errors='coerce').dropna()

        if len(data) == 0:
            data = pd.Series([np.nan])
        boxplot_data.append(data)
        desc = column_description_dict.get(col, col) if column_description_dict else col
        wrapped = textwrap.wrap(desc, width=max_desc_width)
        num_lines = len(wrapped)
        if num_lines > max_desc_lines:
            wrapped = wrapped[:max_desc_lines]
            wrapped[-1] += '...'
        if num_lines > max_lines:
            max_lines = num_lines
        ytick_labels.append('\n'.join(wrapped))
        means.append(data.mean())
        variances.append(data.var())

    line_height = 0.6
    if max_lines > 3:
        line_height = 0.8

    num_plots = len(boxplot_data)
    fig_height = max(2, line_height * num_plots)
    fig, ax = plt.subplots(figsize=(4, fig_height))
    #fig.subplots_adjust(left=0.32) 

    _plot_boxplots_with_background(
        ax,
        boxplot_data,
        ytick_labels,
        means,
        variances,
        overall_title=overall_title,
        couting_factor=couting_factor,
        columns=columns,
        show_ylabels=True,
        group_names=group_names,
        group_lengths=group_lengths,
        fig=fig,
        plot_type=plot_type
    )

    with PdfPages(output_pdf) as pdf:
        pdf.savefig(fig, bbox_inches='tight')
        fig.savefig(output_pdf.replace('.pdf', '.svg'), bbox_inches='tight')
    plt.close(fig)

def generate_pdf_with_boxplot_for_series(
    data_series,
    output_pdf,
    description="",
    overall_title=None,
    couting_factor=None
):
    """
    Generates a PDF with a single boxplot for a data series, with background color regions.
    Useful for visualizing aggregated or composite scores.

    Args:
        data_series (pd.Series): The data to plot.
        output_pdf (str): Path to output PDF file.
        description (str): Description for the y-tick label.
        overall_title (str, optional): Overall title to display as the figure heading.
        couting_factor (dict, optional): Dict mapping the series name to bool for background direction.
    """
    n_answers = int(data_series.notna().sum())
    if overall_title:
        overall_title = f"{overall_title} (n={n_answers})"

    data = data_series
    if len(data) == 0:
        data = pd.Series([np.nan])
    boxplot_data = [data]
    ytick_labels = [description]
    if len(description) > 2:
        show_ylabels=True
    else:
        show_ylabels=False
    means = [data.mean()]
    variances = [data.var()]
    columns = [data_series.name if data_series.name else "Value"]

    fig, ax = plt.subplots(figsize=(10, 3))

    _plot_boxplots_with_background(
        ax,
        boxplot_data,
        ytick_labels,
        means,
        variances,
        overall_title=overall_title,
        couting_factor=couting_factor,
        columns=columns,
        show_ylabels=show_ylabels,
        fig=fig
    )

    with PdfPages(output_pdf) as pdf:
        pdf.savefig(fig, bbox_inches='tight')
        fig.savefig(output_pdf.replace('.pdf', '.svg'), bbox_inches='tight')
    plt.close(fig)

def generate_pdf_sus(sus_input, output_pdf, title=None):
    """
    Visualizes the SUS (System Usability Scale) scores as a boxplot with background categories:
    - Acceptable (70-100, green)
    - Marginal (50-70, yellow)
    - Not acceptable (0-50, red)
    Handles both single series and dicts of series for grouped SUS visualizations.

    Args:
        sus_input (pd.Series or dict): Series containing SUS scores, or dict of {label: pd.Series}.
        output_pdf (str): Path to the output PDF file.
        title (str, optional): Title for the plot.
    """
    # Handle single series or dict of series      
    if isinstance(sus_input, dict):
        sus_dict = sus_input
    else:
        sus_dict = {title: sus_input}

    # Prepare cleaned data, means, variances, and n per group
    series_list = []
    labels = []
    means = []
    variances = []
    ns = []
    n_answers_max = 0

    for label, series in sus_dict.items():
        sus_clean = series.dropna()
        n = int(sus_clean.shape[0])
        if n > n_answers_max:
            n_answers_max = n
        series_list.append(sus_clean)
        labels.append(f"{label} (n={n})")
        means.append(sus_clean.mean() if n > 0 else np.nan)
        variances.append(sus_clean.var() if n > 0 else np.nan)
        ns.append(n)

    num_plots = len(series_list)
    fig_height = max(2.5, 0.6 * num_plots + 1.5)
    fig, ax = plt.subplots(figsize=(10, fig_height))

    # FIX: lock vertical mapping so row centers 1..num_plots align with background bands
    ax.set_ylim(0.5, num_plots + 0.5)
    ax.set_autoscaley_on(False)

    # If more than one boxplot, draw dotted line after first one
    if len(series_list) > 1:
        y_offset = len(series_list) - 1
        ax.axhline(
            y=y_offset + 0.5,
            color='black',
            linestyle='dotted',
            linewidth=1,
            xmin=-2,
            xmax=1.3,
            clip_on=False
        )

    # Draw background category regions
    for i in range(num_plots):
        y_bottom = i + 0.5
        y_top = i + 1.5
        ax.axvspan(0, 50, ymin=(y_bottom-0.5)/num_plots, ymax=(y_top-0.5)/num_plots, color='#ffcccc', alpha=0.5)
        ax.axvspan(50, 70, ymin=(y_bottom-0.5)/num_plots, ymax=(y_top-0.5)/num_plots, color='#fff2cc', alpha=0.5)
        ax.axvspan(70, 100, ymin=(y_bottom-0.5)/num_plots, ymax=(y_top-0.5)/num_plots, color='#d9ead3', alpha=0.5)

    # Deterministic RNG for jitter
    rng = np.random.default_rng(seed=0)
    jitter_scale = 0.08 if num_plots <= 10 else max(0.03, 0.08 * 10 / num_plots)

    # Plot each row: dot plot for small n, boxplot otherwise
    for idx, series in enumerate(series_list, start=1):
        clean = np.array(series.dropna(), dtype=float)
        n = ns[idx - 1]

        if n == 0:
            # nothing to plot; leave an empty row
            continue

        if n < 20:
            # Dot-plot with small vertical jitter
            y = np.full(clean.shape, idx)
            jitter = rng.normal(0, jitter_scale, size=clean.size) if clean.size > 0 else np.array([])
            ax.scatter(clean, y + jitter, color='black', alpha=0.65, s=36, linewidths=0)
        else:
            # Individual boxplot at the correct y-position
            # Use positions so boxplot appears on the same row index
            bplot = ax.boxplot(
                [clean],
                positions=[idx],
                vert=False,
                patch_artist=True,
                showmeans=True,
                meanline=True,
                medianprops={'linewidth': 3, 'color': 'red', 'linestyle': 'solid'},
                meanprops={'linewidth': 3, 'color': 'orange', 'linestyle': 'solid'},
                widths=0.6
            )
            # Optional: style the box facecolor to transparent to match dot-plot aesthetic
            for patch in bplot.get('boxes', []):
                patch.set_facecolor('#ffffff')
                patch.set_alpha(0.6)

        # Plot mean and median markers for every row for consistency
        mean = means[idx - 1]
        try:
            median = np.nanmedian(clean) if clean.size > 0 else np.nan
        except Exception:
            median = np.nan

        if not np.isnan(mean):
            ax.plot(mean, idx, marker='D', color='orange', markersize=8, label='_nolegend_')
        if not np.isnan(median):
            ax.plot(median, idx, marker='s', color='red', markersize=6, label='_nolegend_')

    # Y-axis labels and ticks
    y_positions = list(range(1, num_plots + 1))
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=12)
    for label in ax.get_xticklabels():
        label.set_fontsize(12)
    ax.set_xlabel("SUS Score", fontsize=12)
    if title:
        if isinstance(sus_input, dict):
            ax.set_title(f"{title} (total n={n_answers_max})", fontsize=14, fontweight='bold')
        else:
            ax.set_title(title, fontsize=14, fontweight='bold')

    # --- ensure no left padding before 0 ---
    # set the x-limits explicitly and remove x-margin (call after all drawing)
    ax.set_xlim(0, 100)
    ax.margins(x=0)            # remove automatic padding
    ax.set_xmargin(0)         # alternative explicit call
    ax.set_autoscalex_on(False)

    # Annotate mean and variance for each boxplot
    for i, (mean, var) in enumerate(zip(means, variances), start=1):
        if not np.isnan(mean):
            #ax.text(102, i, f"Mean: {mean:.2f}\nVar: {var:.2f}", va='center', fontsize=9)
            ax.text(102, i, f"mean: {mean:.2f}", va='center', fontsize=12)

    # Add category labels above the plot
    y_text = 1.02  # Slightly above the axes
    ax.text(25, y_text, "Not acceptable", ha='center', va='bottom', fontsize=13, fontweight='bold', color='#b22222', transform=ax.get_xaxis_transform())
    ax.text(60, y_text, "Marginal", ha='center', va='bottom', fontsize=13, fontweight='bold', color='#b8860b', transform=ax.get_xaxis_transform())
    ax.text(85, y_text, "Acceptable", ha='center', va='bottom', fontsize=13, fontweight='bold', color='#38761d', transform=ax.get_xaxis_transform())

    # Custom legend for categories
 #  legend_elements = [
 #       Patch(facecolor='#d9ead3', edgecolor='gray', alpha=0.5, label='Acceptable (70-100)'),
 #       Patch(facecolor='#fff2cc', edgecolor='gray', alpha=0.5, label='Marginal (50-70)'),
#        Patch(facecolor='#ffcccc', edgecolor='gray', alpha=0.5, label='Not acceptable (0-50)')
#    ]

    # Create custom legend handles for mean and median
    median_line = mlines.Line2D([], [], color='red', linewidth=3, linestyle='solid', label='Median')
    mean_line = mlines.Line2D([], [], color='orange', linewidth=3, linestyle='solid', label='Mean')
    handles = [mean_line, median_line] #+ legend_elements

    # # Add the legend below the x-axis
    # ax.legend(
    #     handles=handles,
    #     loc='upper right',
    #     frameon=True,
    #     fontsize=12,
    #     ncol = 2
    # )

    # Add the legend below the x-axis
    delta_y = -0.45
    if num_plots > 2:
        delta_y = -0.2

    ax.legend(
        handles=handles,
        loc='upper center',
        bbox_to_anchor=(0.5, delta_y),  # Place legend below the axes
        ncol=len(handles),
        frameon=True
    )

    plt.tight_layout()
    with PdfPages(output_pdf) as pdf:
        pdf.savefig(fig, bbox_inches='tight')
        fig.savefig(output_pdf.replace('.pdf', '.svg'), bbox_inches='tight')
    plt.close(fig)

def plot_column_pie_chart_pdf(df, column, output_pdf, column_description_dict):
    """
    Prepares value counts and calls plot_pie_chart_from_value_counts to generate a pie chart PDF.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        column (str): The column name to analyze.
        output_pdf (str): The path to save the pie chart PDF.
        column_description_dict (dict): Dictionary mapping column names to descriptions.
    """
     # Replace empty strings and NaN with 'No information provided'
    col_data = df[column].replace('', pd.NA)
    col_data = col_data.fillna('No information provided')
    value_counts = col_data.value_counts(dropna=False)
    n_answers = len(col_data)
    title = f"Distribution of {column_description_dict.get(column, column)} (n={n_answers})"
    plot_pie_chart_from_value_counts(value_counts, output_pdf, column_description_dict, title)

def plot_pie_chart_from_value_counts(value_counts, output_pdf, column_description_dict, title):
    """
    Plots a pie chart from a value_counts Series and saves it as a PDF.
    Each slice is annotated with its description and value count.

    Args:
        value_counts (pd.Series): Value counts for categories.
        output_pdf (str): Path to save the pie chart PDF.
        column_description_dict (dict): Dictionary mapping category names to descriptions.
        title (str): Title for the chart.
    """
     # Prepare descriptions for each category
    plt.cm.get_cmap('Set3')

    categories = value_counts.index.astype(str)
    descriptions = []
    max_box_width = 30  # characters per line in the box
    max_box_lines = 4   # max lines per box
    fontsize = 10

    for cat in categories:
        desc = column_description_dict.get(cat, cat)
        # Line-break the description
        wrapped = textwrap.wrap(desc, width=max_box_width)
        # Limit to max_box_lines, add ellipsis if too long
        if len(wrapped) > max_box_lines:
            wrapped = wrapped[:max_box_lines]
            wrapped[-1] += '...'
        descriptions.append('\n'.join(wrapped))

    # Set up a fixed-size figure for consistency
    fig, ax = plt.subplots(figsize=(8, 8))

    # Pie chart
    pie_radius = 0.8
    wedges, _ = ax.pie(
        value_counts.values,
        labels=None,
        startangle=90,
        counterclock=False,
        radius=pie_radius,  # smaller pie
        wedgeprops=dict(width=pie_radius, edgecolor='w')
    )
    ax.set_title(title)
    ax.axis('equal')  # Equal aspect ratio for a perfect circle

     # Draw description boxes next to corresponding pie slices
    # Calculate the angle for each wedge to position the box
    total = sum(value_counts.values)
    angles = []
    current_angle = 90  # startangle
    for count in value_counts.values:
        angle = 360 * count / total
        angles.append((current_angle - angle / 2) % 360)
        current_angle -= angle

    # Compute box sizes based on text
    box_positions = []
    box_sizes = []
    renderer = fig.canvas.get_renderer()
    for i, desc in enumerate(descriptions):
        value = value_counts.values[i]
        percent = 100 * value / total if total > 0 else 0
        box_text = f"{desc}\n{value} ({percent:.1f}%)"
        t = ax.text(0, 0, box_text, fontsize=fontsize, ha='center', va='center', bbox=dict(boxstyle="round,pad=0.5"))
        bbox_disp = t.get_window_extent(renderer=renderer)
        # Convert display (pixel) to axes coordinates
        inv = ax.transData.inverted()
        bbox_data = inv.transform([[bbox_disp.x0, bbox_disp.y0], [bbox_disp.x1, bbox_disp.y1]])
        box_width = abs(bbox_data[1][0] - bbox_data[0][0])
        box_height = abs(bbox_data[1][1] - bbox_data[0][1])
        box_sizes.append((box_width, box_height))
        t.remove()

    # Place boxes, moving outward if they overlap the pie
    min_r = 0.95
    max_r = 1.35
    step_r = 0.02
    final_positions = []
    for i, angle in enumerate(angles):
        theta = np.deg2rad(angle)
        box_width, box_height = box_sizes[i]
        r = min_r
        while r <= max_r:
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            # Check all 4 corners
            overlap = False
            for dx in [-box_width/2, box_width/2]:
                for dy in [-box_height/2, box_height/2]:
                    dist = np.sqrt((x+dx)**2 + (y+dy)**2)
                    if dist < (pie_radius+0.05):
                        overlap = True
            if not overlap:
                break
            r += step_r
        final_positions.append([x, y, box_width, box_height])

    # Now resolve box-on-box overlap, preferring horizontal movement if less than vertical
    final_positions = _resolve_horizontal_overlap(final_positions, ax)

    # Place description boxes at adjusted positions
    for i, (x, y, box_width, box_height) in enumerate(final_positions):
        desc = descriptions[i]
        value = value_counts.values[i]
        percent = 100 * value / total if total > 0 else 0
        box_text = f"{desc}\n{value} ({percent:.1f}\%)"
        bbox_props = dict(boxstyle="round,pad=0.5", fc=wedges[i].get_facecolor(), ec="gray", alpha=0.25)
        ax.text(
            x, y, box_text,
            ha='center', va='center', fontsize=fontsize,
            bbox=bbox_props, wrap=True
        )

    # Remove all axis ticks and labels
    ax.set_xticks([])
    ax.set_yticks([])

    plt.tight_layout()
    with PdfPages(output_pdf) as pdf:
        pdf.savefig(fig, bbox_inches='tight')
        fig.savefig(output_pdf.replace('.pdf', '.svg'), bbox_inches='tight')
    plt.close(fig)

def plot_yes_counts_bar_chart_pdf(df, columns, column_description_dict, output_pdf, chart_title):
    """
    Counts 'yes' values in specified columns and plots them as a bar chart in a PDF.
    Uses column descriptions for bar labels.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        columns (list of str): List of column names to analyze.
        column_description_dict (dict): Dictionary mapping column names to descriptions.
        output_pdf (str): Path to save the bar chart PDF (e.g., 'yes_counts.pdf').
        chart_title (str): Title for the bar chart.
    """
    # Count 'yes' in each column
    yes_counts = []
    bar_labels = []

    n_answers = int(df[columns].notna().any(axis=1).sum())
    chart_title = f"{chart_title} (n={n_answers})"

    for col in columns:
        count = (df[col].str.lower() == 'yes').sum()
        yes_counts.append(count)
        bar_labels.append(column_description_dict.get(col, col))

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(bar_labels, yes_counts, color='skyblue')
    ax.set_ylabel("Number")
    ax.set_title(f"{chart_title}")

    # Rotate and align x-tick labels, and ensure they fit
    plt.xticks(rotation=45, ha='right', fontsize=10, wrap=True)
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Leave space for title
    plt.tight_layout()
    with PdfPages(output_pdf) as pdf:
        pdf.savefig(fig, bbox_inches='tight')
        fig.savefig(output_pdf.replace('.pdf', '.svg'), bbox_inches='tight')
    plt.close(fig)

def combine_pdfs_in_folder(folder_path, output_pdf):
    """
    Combines all PDF files in the specified folder into a single PDF.

    Args:
        folder_path (str): Path to the folder containing PDF files.
        output_pdf (str): Path to the output combined PDF file.
    """
    merger = PdfMerger()
    # List all PDF files in the folder, sorted alphabetically
    pdf_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')])
    for pdf_file in pdf_files:
        merger.append(os.path.join(folder_path, pdf_file))
    merger.write(output_pdf)
    merger.close()