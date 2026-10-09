"""
print_metadata_figures.py

This module provides functions for visualizing metadata element statistics for metadata created based on ERSmeta.
It generates publication-ready bar charts and boxplots for metadata element usage, priority, and cardinality.
The figures are designed for inclusion in academic reports and LaTeX documents.

Main Features:
- Bar chart (histogram) of element occurrence across metadata sets, colored by priority and position.
- Horizontal boxplots for element type counts, with optional annotation of mean/variance and overlay of maximal values.
- Color utilities for visually distinguishing element priorities and positions.

Functions:
- adjust_color_intensity: Lightens or darkens a base color based on element position.
- get_bar_color: Assigns a color to a bar based on element priority and position.
- save_element_histogram: Creates and saves a bar chart of element occurrence counts.
- save_element_type_boxplots: Creates and saves horizontal boxplots for element type counts, with optional stats and max overlays.

Assumptions and Notes:
- Figures are saved as both PDF and PNG for easy integration into LaTeX or other documents.
- Uses Matplotlib for all plotting.
- Intended for use in the ERSmeta metadata evaluation pipeline.
"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
import matplotlib.lines as mlines
from matplotlib.patches import Patch
import matplotlib.colors as mcolors

def adjust_color_intensity(base_color, position, max_position, lighten=True):
    """
    Adjusts the intensity of a base color by blending it with white (lighten) or black (darken)
    based on the element's position in the list.

    Args:
        base_color (str or tuple): The base color (hex or RGB tuple).
        position (int): The position of the element (0-based).
        max_position (int): The maximum position (for normalization).
        lighten (bool): If True, blend with white; if False, blend with black.

    Returns:
        tuple: The adjusted RGB color.
    """
    rgb = np.array(mcolors.to_rgb(base_color))
    if lighten:
        # Blend with white
        factor = 0.4 + 0.6 * (position / max_position)  # 0.4 (lightest) to 1.0 (base)
        return tuple(rgb * factor + (1 - factor))
    else:
        # Blend with black
        factor = 1.0 - 0.6 * (position / max_position)  # 1.0 (base) to 0.4 (darkest)
        return tuple(rgb * factor)

def get_bar_color(row, max_position):
    """
    Determines the color for a bar in the histogram based on element priority and position.

    Args:
        row (pd.Series): Row from the DataFrame with 'priority' and 'position' fields.
        max_position (int): The maximum position (for normalization).

    Returns:
        tuple: The RGB color for the bar.
    """
    # Define colors for each priority
    color_map = {
        'required': '#e41a1c',      # red
        'recommended': '#377eb8',   # blue
        'optional': '#4daf4a',      # green
    }

    base_color = color_map[row['priority']]
    position = row['position']
    return adjust_color_intensity(base_color, position, max_position, lighten=True)

def save_element_histogram(df_element_counts, max_position, output_pdf_path):
    """
    Creates a horizontal bar chart showing the number of occurrences of each metadata element
    across all metadata sets. Bars are colored by priority and position.

    Args:
        df_element_counts (pd.DataFrame): DataFrame with columns 'property', 'count', 'priority', 'position'.
        max_position (int): The maximum position value for color normalization.
        output_pdf_path (str): Path to the output PDF file.

    Output:
        - Saves the figure as both PDF and PNG at the specified path.
    """
    df_element_counts['count'] = df_element_counts['count'].fillna(0)

    df_sorted = df_element_counts.sort_values(by='count', ascending=False)
    df_sorted = df_sorted[np.isfinite(df_sorted['count']) & np.isfinite(df_sorted['position'])]

    # Change 0 to 0.1 to make a visible bar
    min_bar_height = 0.1  # Small value for zero bars
    df_sorted['count'] = df_sorted['count'].apply(lambda x: min_bar_height if x == 0 else x)

    # Get colors for each bar
    df_sorted['bar_color'] = df_sorted.apply(lambda row: get_bar_color(row, max_position), axis=1)

    fig, ax = plt.subplots(figsize=(10, max(4, len(df_sorted) * 0.25)))
    bars = ax.barh(
        df_sorted['property'],
        df_sorted['count'],
        color=df_sorted['bar_color']
    )
    ax.set_xlabel('Count')
    ax.set_ylabel('Element')
    ax.set_title('Number of Occurrences of Elements over Metadata Sets')
    plt.xticks(rotation=90)

    # Annotate position to the right of each bar
    for i, (count, position) in enumerate(zip(df_sorted['count'], df_sorted['position'])):
        ax.text(
            count + 0.2,  # Slightly to the right of the bar
            i,            # y-position (row index)
            f"Pos: {position}",
            va='center',
            ha='left',
            fontsize=8,
            color='dimgray'
        )

    # Create a custom legend
    color_map = {
        'required': '#e41a1c',      # red
        'recommended': '#377eb8',   # blue
        'optional': '#4daf4a',      # green
    }

    legend_handles = [Patch(color=color, label=label.capitalize()) for label, color in color_map.items()]
    ax.legend(handles=legend_handles, title='Priority')

    plt.tight_layout()
    plt.savefig(output_pdf_path, format='pdf')
    plt.savefig(output_pdf_path.replace('.pdf', '.png'), format='png')
    plt.close()

    
def save_element_type_boxplots(
    df_element_type_counts,
    output_pdf_path,
    annotate_stats=True,
    max_series=None,
    title=None,
    xlabel="Element Count",
    ylabel="Element Type",
    plot_type="box"  # "box" (default) or "dot"
):
    """
    Creates horizontal boxplots for each column in df_element_type_counts and saves as a PDF.
    Optionally annotates the mean and variance next to each boxplot and overlays a vertical line
    for the maximal value per element type.

    Args:
        df_element_type_counts (pd.DataFrame): DataFrame with columns to plot (one per element type).
        output_pdf_path (str): Path to the output PDF file.
        annotate_stats (bool, optional): Whether to annotate mean and variance (default: True).
        max_series (pd.Series or dict, optional): Maximal values for each element type (column).
        title (str, optional): Title of the plot.
        xlabel (str, optional): Label for the x-axis.
        ylabel (str, optional): Label for the y-axis.
        plot_type (str, optional): "box" for boxplots (default) or "dot" for dot-plots.

    Output:
        - Saves the figure as both PDF and PNG at the specified path.
    """
    # Fixed width, dynamic height based on number of columns (element types)
    fixed_width = 8
    row_height = 0.4  # Adjust for more/less vertical space per boxplot
    n_rows = len(df_element_type_counts.columns)
    min_height = 1
    figsize = (fixed_width, max(min_height, n_rows * row_height + 0.7))

    plt.figure(figsize=figsize)
     # Calculate x-axis max candidates early so both plot types can use consistent limits
    if max_series is not None:
        # ensure Series-like
        if not hasattr(max_series, 'index'):
            import pandas as pd
            max_series = pd.Series(max_series)
        max_max = max(max_series.max(), df_element_type_counts.max().max())
    else:
        max_max = df_element_type_counts.max().max()
    x_max = int(np.ceil(max_max)) if np.isfinite(max_max) else 1
    x_right = max(1, x_max * 1.1)

    # Precompute means and medians for explicit plotting (ensures markers always drawn)
    means = df_element_type_counts.mean(skipna=True)
    medians = df_element_type_counts.median(skipna=True)

    if plot_type == "box":
        # Use pandas boxplot (keeps your previous styling)
        ax = df_element_type_counts.boxplot(
            vert=False,
            patch_artist=True,
            return_type='axes',
            showmeans=True,
            meanline=True,
            medianprops={'linewidth': 4, 'color': 'red', 'linestyle': 'solid'},
            meanprops={'linewidth': 3, 'color': 'orange', 'linestyle': 'solid'},
            widths=0.5
        )
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)

        # Draw vertical max lines per row if provided
        if max_series is not None:
            for i, col in enumerate(df_element_type_counts.columns):
                if col in max_series:
                    max_val = max_series[col]
                    y = i + 1  # pandas boxplot uses 1-indexed rows
                    ax.vlines(
                        x=max_val,
                        ymin=y - 0.4,
                        ymax=y + 0.4,
                        colors='green',
                        linestyles='--',
                        linewidth=2,
                        alpha=0.7,
                        label='Max possible value' if i == 0 else None
                    )

        # Explicitly draw mean and median markers so they are always visible
        for i, col in enumerate(df_element_type_counts.columns, start=1):
            m = means.get(col, np.nan)
            med = medians.get(col, np.nan)
            if np.isfinite(m):
                ax.plot(m, i, marker='D', color='orange', markersize=6, zorder=6, label='_nolegend_')
            if np.isfinite(med):
                ax.plot(med, i, marker='s', color='red', markersize=6, zorder=6, label='_nolegend_')



    elif plot_type == "dot":
        # Dot-plot: one horizontal row per column, jittered points for observations
        ax = plt.gca()
        cols = list(df_element_type_counts.columns)
        # Fix vertical mapping so rows center at 1..n_rows
        ax.set_ylim(0.5, n_rows + 0.5)
        ax.set_autoscaley_on(False)

        rng = np.random.default_rng(seed=0)
        jitter_scale = 0.08 if n_rows <= 10 else max(0.02, 0.08 * 10 / n_rows)

        for i, col in enumerate(cols, start=1):
            data = df_element_type_counts[col].dropna().values
            if data.size == 0:
                continue
            x = np.array(data, dtype=float)
            y = np.full(x.shape, i)
            jitter = rng.normal(0, jitter_scale, size=x.size)
            ax.scatter(x, y + jitter, color='black', alpha=0.7, s=18, linewidths=0)

            # Optional: draw a faint horizontal bar/box to indicate row band
            ax.axhline(i, color='lightgray', linewidth=0.5, alpha=0.6)

            # Draw max line for this row if provided
            if max_series is not None and col in max_series:
                max_val = max_series[col]
                ax.vlines(
                    x=max_val,
                    ymin=i - 0.4,
                    ymax=i + 0.4,
                    colors='green',
                    linestyles='--',
                    linewidth=2,
                    alpha=0.7,
                    label='Max possible value' if i == 1 else None
                )

        # Draw mean/median markers for dot plot
        for i, col in enumerate(cols, start=1):
            m = means.get(col, np.nan)
            med = medians.get(col, np.nan)
            if np.isfinite(m):
                ax.plot(m, i, marker='D', color='orange', markersize=6, zorder=6)
            if np.isfinite(med):
                ax.plot(med, i, marker='s', color='red', markersize=6, zorder=6)

        # Y ticks and labels
        ax.set_yticks(list(range(1, n_rows + 1)))
        ax.set_yticklabels(cols, fontsize=10)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)

    else:
        raise ValueError("plot_type must be 'box' or 'dot'")
    
    # Common formatting after plotting
    # Set integer-friendly x-axis ticks and limit
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=8))
    ax.set_xlim(left=0, right=x_right)

    if annotate_stats:
        # Annotate mean and variance for each row
        for i, col in enumerate(df_element_type_counts.columns):
            data = df_element_type_counts[col].dropna()
            if data.empty:
                continue
            mean = data.mean()
            var = data.var()
            # Place annotation to the right of the plotting area
            plt.text(
                x=x_right + 0.5,
                y=(i + 1) if plot_type == "box" else (i + 0.6),
                s=f"mean: {mean:.2f}\nvar: {var:.2f}",
                va='center' if plot_type == "dot" else 'bottom',
                ha='left',
                fontsize=8
            )

    # Legend: mean/median for boxplots, and max-series line if present
    handles = []
    if plot_type == "box":
        median_line = mlines.Line2D([], [], color='red', linewidth=4, linestyle='solid', label='Median')
        mean_line = mlines.Line2D([], [], color='orange', linewidth=3, linestyle='solid', label='Mean')
        handles.extend([mean_line, median_line])
    else:
        # For dot plot show mean/median markers in legend if desired
        mean_marker = mlines.Line2D([], [], color='orange', marker='D', linestyle='None', markersize=6, label='Mean')
        median_marker = mlines.Line2D([], [], color='red', marker='s', linestyle='None', markersize=6, label='Median')
        handles.extend([mean_marker, median_marker])

    if max_series is not None:
        vertical_line = mlines.Line2D([0, 0], [0, 1], color='green', linestyle='--', linewidth=2, alpha=0.7, label='Maximal number of elements')
        handles.append(vertical_line)

    y_anchor = -0.4
    if n_rows > 5:
        y_anchor = -0.1
    if handles:
        ax.legend(
            handles=handles,
            loc='upper center',
            bbox_to_anchor=(0.5, y_anchor),
            ncol=len(handles),
            frameon=True
        )

    plt.tight_layout()
    # If annotations extend beyond figure, expand bottom as before
    if y_anchor < -0.2:
        plt.subplots_adjust(bottom=-y_anchor)
    plt.savefig(output_pdf_path, format='pdf')
    plt.savefig(output_pdf_path.replace('.pdf', '.png'), format='png')
    plt.close()