"""
Post-processing script to compare skew model effects.

Computes differences between:
- Baseline: Skew_Mod=0 (no skew model)
- Rev2: Skew_Mod=1, SkewMomCorr=True, SkewRedistr_Mod=1 (full skew physics)

Generates difference heatmaps showing the impact of the skew model.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path

# Configuration
work_dir = Path('/Users/benhealy/OpenFAST/Simulations/5MW_Land_BD_DLL_Wturb_yaw_loading')
baseline_csv = work_dir / 'summary_skewmod0_skewcorr_true.csv'
rev2_csv = work_dir / 'summary_rev2_skewcorr_true.csv'
output_folder = work_dir / 'comparison_plots'
output_folder.mkdir(exist_ok=True)

# Variables to compare (using mean values) - matches openfast_yaw_loads_comparison.py heatmaps
variables_to_compare = {
    'BldPitch1': 'Pitch Angle (deg)',
    'RtTSR': 'Tip Speed Ratio (-)',
    'GenPwr': 'Power Output (kW)',
    'RtAeroCp': 'Power Coefficient Cp (-)',
    'RtAeroCt': 'Thrust Coefficient Ct (-)',
    'B1RootMyr': 'Blade Root Moment (kN·m)',
    'RotSpeed': 'Rotor Speed (RPM)',
    'RotTorq': 'Rotor Torque (kN·m)',
    'RtAeroFxh': 'Thrust Force (kN)',
    'YawBrMzp': 'Yaw Bearing Moment (kN·m)',
    'TwrBsMyt': 'Tower Base Moment (kN·m)',
}


def load_and_merge_data():
    """Load baseline and Rev2 data, merge on wind speed and yaw angle."""
    print("Loading data...")

    # Load CSVs
    baseline = pd.read_csv(baseline_csv)
    rev2 = pd.read_csv(rev2_csv)

    print(f"  Baseline: {len(baseline)} simulations")
    print(f"  Rev2: {len(rev2)} simulations")

    # Merge on YawAngle and WindSpeed
    merged = baseline.merge(
        rev2,
        on=['YawAngle', 'WindSpeed'],
        suffixes=('_baseline', '_rev2')
    )

    print(f"  Merged: {len(merged)} matching simulations")

    return merged


def compute_differences(merged_df):
    """Compute absolute and percentage differences."""
    print("\nComputing differences...")

    diff_data = {
        'YawAngle': merged_df['YawAngle'],
        'WindSpeed': merged_df['WindSpeed'],
    }

    # Compute differences for each variable
    for var_key in variables_to_compare.keys():
        baseline_col = f"{var_key}_mean_baseline"
        rev2_col = f"{var_key}_mean_rev2"

        if baseline_col in merged_df.columns and rev2_col in merged_df.columns:
            # Absolute difference: Rev2 - Baseline
            diff_data[f'{var_key}_diff'] = merged_df[rev2_col] - merged_df[baseline_col]

            # Percentage difference: (Rev2 - Baseline) / |Baseline| * 100
            # Use absolute value in denominator for proper relative percentage
            # Avoid division by zero
            baseline_vals = merged_df[baseline_col]
            pct_diff = np.where(
                np.abs(baseline_vals) > 1e-10,
                (merged_df[rev2_col] - baseline_vals) / np.abs(baseline_vals) * 100,
                np.nan
            )
            diff_data[f'{var_key}_pct_diff'] = pct_diff

    diff_df = pd.DataFrame(diff_data)

    # Save to CSV
    output_csv = output_folder / 'skew_model_differences.csv'
    diff_df.to_csv(output_csv, index=False)
    print(f"  ✓ Saved differences to: {output_csv}")

    return diff_df


def create_heatmap(data, wind_speeds, yaw_angles, var_name, var_label,
                   diff_type='absolute', cmap='RdBu_r', vmin=None, vmax=None):
    """Create a single heatmap showing differences."""

    # Reshape data into 2D array [wind_speed, yaw_angle]
    heatmap_data = np.full((len(wind_speeds), len(yaw_angles)), np.nan)

    for i, ws in enumerate(wind_speeds):
        for j, yaw in enumerate(yaw_angles):
            mask = (data['WindSpeed'] == ws) & (data['YawAngle'] == yaw)
            if mask.any():
                col_name = f'{var_name}_diff' if diff_type == 'absolute' else f'{var_name}_pct_diff'
                heatmap_data[i, j] = data.loc[mask, col_name].values[0]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create heatmap
    im = ax.imshow(heatmap_data, aspect='auto', origin='lower', cmap=cmap,
                   vmin=vmin, vmax=vmax, interpolation='nearest')

    # Set ticks
    ax.set_xticks(np.arange(len(yaw_angles)))
    ax.set_yticks(np.arange(len(wind_speeds)))
    ax.set_xticklabels([f'{int(y):+d}°' for y in yaw_angles])
    ax.set_yticklabels([f'{int(ws)}' for ws in wind_speeds])

    # Labels
    ax.set_xlabel('Yaw Angle (deg)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Wind Speed (m/s)', fontsize=14, fontweight='bold')

    # Title
    if diff_type == 'absolute':
        title = f'{var_label}\n(With Skew Correction - Without Skew Correction) [Absolute]'
    else:
        title = f'{var_label}\n(With Skew Correction - Without Skew Correction) [%]'
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    if diff_type == 'absolute':
        cbar.set_label('Absolute Difference', fontsize=12, fontweight='bold')
    else:
        cbar.set_label('Percent Difference (%)', fontsize=12, fontweight='bold')

    # Add text annotations for each cell
    for i in range(len(wind_speeds)):
        for j in range(len(yaw_angles)):
            if not np.isnan(heatmap_data[i, j]):
                value = heatmap_data[i, j]
                # Choose text color based on background
                text_color = 'white' if abs(value) > 0.5 * np.nanmax(np.abs(heatmap_data)) else 'black'

                if diff_type == 'absolute':
                    # Format based on magnitude
                    if abs(value) > 100:
                        text = f'{value:.0f}'
                    elif abs(value) > 1:
                        text = f'{value:.1f}'
                    else:
                        text = f'{value:.2f}'
                else:
                    text = f'{value:.1f}%'

                ax.text(j, i, text, ha='center', va='center',
                       color=text_color, fontsize=8, fontweight='bold')

    plt.tight_layout()

    return fig


def generate_all_heatmaps(diff_df):
    """Generate heatmaps for all variables."""
    print("\nGenerating heatmaps...")

    # Get unique wind speeds and yaw angles
    wind_speeds = sorted(diff_df['WindSpeed'].unique())
    yaw_angles = sorted(diff_df['YawAngle'].unique())

    print(f"  Wind speeds: {wind_speeds}")
    print(f"  Yaw angles: {yaw_angles}")

    for var_key, var_label in variables_to_compare.items():
        print(f"\n  Creating heatmaps for: {var_label}")

        # Check if data exists
        if f'{var_key}_diff' not in diff_df.columns:
            print(f"    ⚠ Skipping {var_key} - data not found")
            continue

        # Absolute difference heatmap
        fig_abs = create_heatmap(
            diff_df, wind_speeds, yaw_angles, var_key, var_label,
            diff_type='absolute', cmap='RdBu_r'
        )

        output_file_abs = output_folder / f'diff_absolute_{var_key}.png'
        fig_abs.savefig(output_file_abs, dpi=150, bbox_inches='tight')
        plt.close(fig_abs)
        print(f"    ✓ Saved: {output_file_abs.name}")

        # Percentage difference heatmap
        fig_pct = create_heatmap(
            diff_df, wind_speeds, yaw_angles, var_key, var_label,
            diff_type='percentage', cmap='RdBu_r'
        )

        output_file_pct = output_folder / f'diff_percentage_{var_key}.png'
        fig_pct.savefig(output_file_pct, dpi=150, bbox_inches='tight')
        plt.close(fig_pct)
        print(f"    ✓ Saved: {output_file_pct.name}")


def create_combined_subplot(diff_df, diff_type='percentage'):
    """Create a combined subplot showing all key differences."""
    print(f"\n  Creating combined {diff_type} difference subplot...")

    # Get unique wind speeds and yaw angles
    wind_speeds = sorted(diff_df['WindSpeed'].unique())
    yaw_angles = sorted(diff_df['YawAngle'].unique())

    # All variables for combined plot (matches original heatmaps)
    key_variables = {
        'BldPitch1': 'Pitch (deg)',
        'RtTSR': 'TSR (-)',
        'GenPwr': 'Power (kW)',
        'RtAeroCp': 'Cp (-)',
        'RtAeroCt': 'Ct (-)',
        'B1RootMyr': 'Blade Root (kN·m)',
        'RotSpeed': 'RotSpeed (RPM)',
        'RotTorq': 'Torque (kN·m)',
        'RtAeroFxh': 'Thrust (kN)',
        'YawBrMzp': 'Yaw Moment (kN·m)',
        'TwrBsMyt': 'Tower Base (kN·m)',
    }

    # Create figure with subplots (3 rows x 4 cols for 11 variables)
    fig, axes = plt.subplots(4, 3, figsize=(22, 14))
    axes = axes.flatten()

    for idx, (var_key, var_label) in enumerate(key_variables.items()):
        ax = axes[idx]

        # Prepare data
        col_name = f'{var_key}_diff' if diff_type == 'absolute' else f'{var_key}_pct_diff'

        if col_name not in diff_df.columns:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(var_label, fontsize=12, fontweight='bold')
            continue

        # Reshape data into 2D array [wind_speed, yaw_angle]
        heatmap_data = np.full((len(wind_speeds), len(yaw_angles)), np.nan)

        for i, ws in enumerate(wind_speeds):
            for j, yaw in enumerate(yaw_angles):
                mask = (diff_df['WindSpeed'] == ws) & (diff_df['YawAngle'] == yaw)
                if mask.any():
                    heatmap_data[i, j] = diff_df.loc[mask, col_name].values[0]

        # Determine colormap range for consistent scaling within each variable
        vmax = np.nanmax(np.abs(heatmap_data))
        vmin = -vmax if diff_type != 'percentage' or vmax < 50 else -50
        vmax = vmax if diff_type != 'percentage' or vmax < 50 else 50

        # Create heatmap
        im = ax.imshow(heatmap_data, aspect='auto', origin='lower',
                       cmap='RdBu_r', vmin=vmin, vmax=vmax, interpolation='nearest')

        # Set ticks
        ax.set_xticks(np.arange(len(yaw_angles)))
        ax.set_yticks(np.arange(len(wind_speeds)))
        ax.set_xticklabels([f'{int(y):+d}' for y in yaw_angles], fontsize=8)
        ax.set_yticklabels([f'{int(ws)}' for ws in wind_speeds], fontsize=8)

        # Labels
        if idx >= 9:  # Bottom row (row 4: indices 9, 10, 11)
            ax.set_xlabel('Yaw Angle (°)', fontsize=10)
        if idx % 3 == 0:  # Left column
            ax.set_ylabel('Wind Speed (m/s)', fontsize=10)

        # Title
        ax.set_title(var_label, fontsize=11, fontweight='bold', pad=8)

        # Colorbar for each subplot
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.ax.tick_params(labelsize=8)
        if diff_type == 'percentage':
            cbar.set_label('%', fontsize=9, rotation=0, labelpad=15)

        # Add value annotations (smaller font for combined plot)
        for i in range(len(wind_speeds)):
            for j in range(len(yaw_angles)):
                if not np.isnan(heatmap_data[i, j]):
                    value = heatmap_data[i, j]

                    # Choose text color
                    text_color = 'white' if abs(value) > 0.5 * vmax else 'black'

                    # Format text
                    if diff_type == 'absolute':
                        if abs(value) > 100:
                            text = f'{value:.0f}'
                        elif abs(value) > 1:
                            text = f'{value:.1f}'
                        else:
                            text = f'{value:.2f}'
                    else:
                        text = f'{value:.1f}'

                    ax.text(j, i, text, ha='center', va='center',
                           color=text_color, fontsize=6, fontweight='bold')

    # Hide unused subplot (last position in 4x3 grid)
    axes[11].axis('off')

    # Overall title
    if diff_type == 'absolute':
        fig.suptitle('Classical Momentum Results (With Skew Correction - Without Skew Correction) [Absolute]',
                    fontsize=18, fontweight='bold', y=0.996)
    else:
        fig.suptitle('Classical Momentum Results (With Skew Correction - Without Skew Correction) [%]',
                    fontsize=18, fontweight='bold', y=0.996)

    plt.tight_layout(rect=[0, 0, 1, 0.993])

    return fig


def create_compact_subplot(diff_df, diff_type='percentage'):
    """Create a compact 2x2 subplot with 4 key variables for PowerPoint."""
    print(f"\n  Creating compact {diff_type} difference subplot (2x2)...")

    # Get unique wind speeds and yaw angles
    wind_speeds = sorted(diff_df['WindSpeed'].unique())
    yaw_angles = sorted(diff_df['YawAngle'].unique())

    # Select 4 most important variables for compact view
    key_variables = {
        'RtAeroCp': 'Cp (-)',
        'RtAeroCt': 'Ct (-)',
        'GenPwr': 'Power (kW)',
        'YawBrMzp': 'Yaw Moment (kN·m)',
    }

    # Create figure with 2x2 subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for idx, (var_key, var_label) in enumerate(key_variables.items()):
        ax = axes[idx]

        # Prepare data
        col_name = f'{var_key}_diff' if diff_type == 'absolute' else f'{var_key}_pct_diff'

        if col_name not in diff_df.columns:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(var_label, fontsize=14, fontweight='bold')
            continue

        # Reshape data into 2D array
        heatmap_data = np.full((len(wind_speeds), len(yaw_angles)), np.nan)

        for i, ws in enumerate(wind_speeds):
            for j, yaw in enumerate(yaw_angles):
                mask = (diff_df['WindSpeed'] == ws) & (diff_df['YawAngle'] == yaw)
                if mask.any():
                    heatmap_data[i, j] = diff_df.loc[mask, col_name].values[0]

        # Determine colormap range
        vmax = np.nanmax(np.abs(heatmap_data))
        vmin = -vmax if diff_type != 'percentage' or vmax < 50 else -50
        vmax = vmax if diff_type != 'percentage' or vmax < 50 else 50

        # Create heatmap
        im = ax.imshow(heatmap_data, aspect='auto', origin='lower',
                       cmap='RdBu_r', vmin=vmin, vmax=vmax, interpolation='nearest')

        # Set ticks
        ax.set_xticks(np.arange(len(yaw_angles)))
        ax.set_yticks(np.arange(len(wind_speeds)))
        ax.set_xticklabels([f'{int(y):+d}' for y in yaw_angles], fontsize=10)
        ax.set_yticklabels([f'{int(ws)}' for ws in wind_speeds], fontsize=10)

        # Labels
        ax.set_xlabel('Yaw Angle (°)', fontsize=12)
        ax.set_ylabel('Wind Speed (m/s)', fontsize=12)

        # Title
        ax.set_title(var_label, fontsize=14, fontweight='bold', pad=10)

        # Colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.ax.tick_params(labelsize=10)
        if diff_type == 'percentage':
            cbar.set_label('%', fontsize=11, rotation=0, labelpad=15)

        # Add value annotations
        for i in range(len(wind_speeds)):
            for j in range(len(yaw_angles)):
                if not np.isnan(heatmap_data[i, j]):
                    value = heatmap_data[i, j]
                    text_color = 'white' if abs(value) > 0.5 * vmax else 'black'

                    if diff_type == 'absolute':
                        if abs(value) > 100:
                            text = f'{value:.0f}'
                        elif abs(value) > 1:
                            text = f'{value:.1f}'
                        else:
                            text = f'{value:.2f}'
                    else:
                        text = f'{value:.1f}'

                    ax.text(j, i, text, ha='center', va='center',
                           color=text_color, fontsize=8, fontweight='bold')

    # Overall title
    if diff_type == 'absolute':
        fig.suptitle('Classical Momentum Results (With Skew Correction - Without Skew Correction) [Absolute]',
                    fontsize=16, fontweight='bold', y=0.995)
    else:
        fig.suptitle('Classical Momentum Results (With Skew Correction - Without Skew Correction) [%]',
                    fontsize=16, fontweight='bold', y=0.995)

    plt.tight_layout(rect=[0, 0, 1, 0.985])

    return fig


def create_yaw_comparison_lineplot(merged_df):
    """Create line plots comparing yaw angle effects on power and thrust at 8 and 14 m/s."""
    print("\n  Creating yaw angle comparison line plots...")

    # Select wind speeds to compare
    wind_speeds = [8, 14]

    # Create 2x2 subplot: rows for wind speeds, columns for variables
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Variables to plot
    variables = [
        ('GenPwr_mean', 'Power (kW)'),
        ('RtAeroFxh_mean', 'Thrust (kN)')
    ]

    for row_idx, ws in enumerate(wind_speeds):
        # Filter data for this wind speed
        ws_data = merged_df[merged_df['WindSpeed'] == ws].sort_values('YawAngle')

        if len(ws_data) == 0:
            continue

        yaw_angles = ws_data['YawAngle'].values

        for col_idx, (var_name, var_label) in enumerate(variables):
            ax = axes[row_idx, col_idx]

            baseline_col = f'{var_name}_baseline'
            rev2_col = f'{var_name}_rev2'

            if baseline_col in ws_data.columns and rev2_col in ws_data.columns:
                # Plot both lines
                ax.plot(yaw_angles, ws_data[baseline_col], 'o-',
                       linewidth=2.5, markersize=8, label='Without Skew Correction',
                       color='#1f77b4', markeredgewidth=1.5, markeredgecolor='white')
                ax.plot(yaw_angles, ws_data[rev2_col], 's-',
                       linewidth=2.5, markersize=8, label='With Skew Correction',
                       color='#ff7f0e', markeredgewidth=1.5, markeredgecolor='white')

                # Formatting
                ax.set_xlabel('Yaw Angle (deg)', fontsize=12, fontweight='bold')
                ax.set_ylabel(var_label, fontsize=12, fontweight='bold')
                ax.set_title(f'{var_label} at {ws} m/s', fontsize=13, fontweight='bold', pad=10)
                ax.grid(True, alpha=0.3, linestyle='--')
                ax.legend(fontsize=10, loc='best', framealpha=0.9)

                # Set x-axis to show all yaw angles
                ax.set_xticks(yaw_angles[::2])  # Show every other tick to avoid crowding
                ax.set_xticklabels([f'{int(y):+d}°' for y in yaw_angles[::2]])

    fig.suptitle('Yaw Angle Effects on Performance: Skew Model Comparison',
                fontsize=16, fontweight='bold', y=0.995)

    plt.tight_layout(rect=[0, 0, 1, 0.985])

    return fig


def print_summary_statistics(diff_df):
    """Print summary statistics of differences."""
    print("\n" + "="*80)
    print("SUMMARY STATISTICS: Impact of Full Skew Model")
    print("="*80)
    print("\nAbsolute Differences (Rev2 - Baseline):")
    print("-" * 80)

    for var_key, var_label in variables_to_compare.items():
        col = f'{var_key}_diff'
        if col in diff_df.columns:
            data = diff_df[col].dropna()
            if len(data) > 0:
                print(f"\n{var_label}:")
                print(f"  Mean:   {data.mean():>12.3f}")
                print(f"  Std:    {data.std():>12.3f}")
                print(f"  Min:    {data.min():>12.3f}")
                print(f"  Max:    {data.max():>12.3f}")

    print("\n" + "="*80)
    print("Percentage Differences [(Rev2 - Baseline) / Baseline × 100%]:")
    print("-" * 80)

    for var_key, var_label in variables_to_compare.items():
        col = f'{var_key}_pct_diff'
        if col in diff_df.columns:
            data = diff_df[col].dropna()
            if len(data) > 0:
                print(f"\n{var_label}:")
                print(f"  Mean:   {data.mean():>12.3f}%")
                print(f"  Std:    {data.std():>12.3f}%")
                print(f"  Min:    {data.min():>12.3f}%")
                print(f"  Max:    {data.max():>12.3f}%")

    print("\n" + "="*80)


def main():
    """Main execution function."""
    print("="*80)
    print("SKEW MODEL COMPARISON POST-PROCESSING")
    print("="*80)
    print("\nComparing:")
    print("  Baseline: Skew_Mod=0 (no skew model)")
    print("  Rev2:     Skew_Mod=1, SkewMomCorr=True, SkewRedistr_Mod=1")
    print("="*80)

    # Load and merge data
    merged_df = load_and_merge_data()

    # Compute differences
    diff_df = compute_differences(merged_df)

    # Generate heatmaps
    generate_all_heatmaps(diff_df)

    # Create combined subplots
    print("\nGenerating combined subplots...")

    # Full 4x3 grid - Percentage differences
    fig_pct_combined = create_combined_subplot(diff_df, diff_type='percentage')
    output_pct_combined = output_folder / 'combined_percentage_differences.png'
    fig_pct_combined.savefig(output_pct_combined, dpi=150, bbox_inches='tight')
    plt.close(fig_pct_combined)
    print(f"  ✓ Saved: {output_pct_combined.name}")

    # Full 4x3 grid - Absolute differences
    fig_abs_combined = create_combined_subplot(diff_df, diff_type='absolute')
    output_abs_combined = output_folder / 'combined_absolute_differences.png'
    fig_abs_combined.savefig(output_abs_combined, dpi=150, bbox_inches='tight')
    plt.close(fig_abs_combined)
    print(f"  ✓ Saved: {output_abs_combined.name}")

    # Compact 2x2 grid - Percentage differences (for PowerPoint)
    fig_pct_compact = create_compact_subplot(diff_df, diff_type='percentage')
    output_pct_compact = output_folder / 'compact_percentage_differences.png'
    fig_pct_compact.savefig(output_pct_compact, dpi=150, bbox_inches='tight')
    plt.close(fig_pct_compact)
    print(f"  ✓ Saved: {output_pct_compact.name}")

    # Compact 2x2 grid - Absolute differences (for PowerPoint)
    fig_abs_compact = create_compact_subplot(diff_df, diff_type='absolute')
    output_abs_compact = output_folder / 'compact_absolute_differences.png'
    fig_abs_compact.savefig(output_abs_compact, dpi=150, bbox_inches='tight')
    plt.close(fig_abs_compact)
    print(f"  ✓ Saved: {output_abs_compact.name}")

    # Line plot comparison at 8 and 14 m/s
    fig_lineplot = create_yaw_comparison_lineplot(merged_df)
    output_lineplot = output_folder / 'yaw_comparison_lineplot.png'
    fig_lineplot.savefig(output_lineplot, dpi=150, bbox_inches='tight')
    plt.close(fig_lineplot)
    print(f"  ✓ Saved: {output_lineplot.name}")

    # Print summary statistics
    print_summary_statistics(diff_df)

    print("\n" + "="*80)
    print("✓ COMPARISON COMPLETE")
    print(f"✓ All plots saved to: {output_folder}")
    print("="*80)


if __name__ == '__main__':
    main()
