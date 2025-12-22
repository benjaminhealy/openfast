import matplotlib.pyplot as plt
import os
import pandas as pd
import matplotlib.ticker as ticker
import re
import subprocess
from pathlib import Path
import numpy as np
import shutil

# Define path to folder and simulation outputs to plot
base_path = os.getcwd()

# Instructions for python shell to update yaw angle parameters with each run
# Working directory for yaw loading simulations
work_dir = '/Users/benhealy/OpenFAST/Simulations/5MW_Land_BD_DLL_Wturb_yaw_loading'

elastodyn_path = os.path.join(work_dir, 'NRELOffshrBsline5MW_Onshore_ElastoDyn_Skewed_Loads.dat')
elastodyn_bd_path = os.path.join(work_dir, 'NRELOffshrBsline5MW_Onshore_ElastoDyn_BDoutputs_Skewed_Loads.dat')
servodyn_path = os.path.join(work_dir, 'NRELOffshrBsline5MW_Onshore_ServoDyn_Skewed_Loads.dat')
aerodyn_path = os.path.join(work_dir, 'NRELOffshrBsline5MW_Onshore_AeroDyn_Skewed_Loads.dat')

# Yaw angles to test (in degrees)
# Using gradual yaw maneuver approach to handle high yaw angles safely
yaw_angles = [-30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 30]
# yaw_angles = [-30]  # single test run before suite of simulations

# Wind speeds to test (for 2D sensitivity analysis)
# Range covers below-rated (6, 9), near-rated (12), and above-rated (15, 18)
# ws_list = [4, 6, 8, 10, 12, 14, 16, 18]  # m/s
ws_list = [8, 4, 6, 10, 14, 12, 16, 18] # running high ws case first for quick comparison
# ws_list = [18]  # single test run before suite of simulations

# SkewMomCorr settings to test (skewed wake momentum correction)
# Only running SkewMomCorr=True (False was already run with Skew_Mod=0)
skew_corr_settings = [True]  # Run only True with Skew_Mod=1

# Output columns to extract from OpenFAST results
output_columns = [
    'Time',
    'BldPitch1',     # Blade pitch angle (deg)
    'RotSpeed',      # Rotor speed (RPM)
    'RtTSR',         # Tip speed ratio (-)
    'RotTorq',       # Rotor torque (kN-m)
    'GenPwr',        # Generator power (kW)
    'RtAeroCp',      # Power coefficient (-)
    'RtAeroCt',      # Thrust coefficient (-)
    'RtAeroFxh',     # Thrust force (kN)
    'B1RootMxr',     # Blade root in-plane moment (kN-m)
    'B1RootMyr',     # Blade root out-of-plane moment (kN-m)
    'B1RootMzr',     # Blade root torsional moment (kN-m)
    'RtVAvgxh',      # Rotor-avg wind velocity x (m/s)
    'RtVAvgyh',      # Rotor-avg wind velocity y (m/s)
    'RtVAvgzh',      # Rotor-avg wind velocity z (m/s)
    'RtSkew',        # Actual skew angle at rotor (deg)
    'YawBrMzp',      # Yaw bearing moment (kN-m)
    'TwrBsMyt',      # Tower base fore-aft moment (kN-m)
    'TwrBsMxt',      # Tower base side-to-side moment (kN-m)
]

# Paths
fst_path = '5MW_Land_BD_DLL_WTurb_Skewed_Loads.fst'
sim_output_base = os.path.join(work_dir, '5MW_Land_BD_DLL_WTurb_Skewed_Loads')
openfast_exe = '/Users/benhealy/OpenFAST/build-testing/glue-codes/openfast/openfast'
inflow_path = '/Users/benhealy/OpenFAST/Simulations/5MW_Baseline/NRELOffshrBsline5MW_InflowWind_12mps_cp_curve.dat'


def modify_parameter(filepath, param_name, new_value):
    """
    Modify a parameter in an OpenFAST input file

    Preserves exact formatting - only replaces the value, nothing else.
    OpenFAST format can be either:
      - value   param_name   - description  (with whitespace)
      - valueParam_name   - description     (no whitespace)

    Parameters:
    -----------
    filepath : str
        Path to the file to modify
    param_name : str
        Name of the parameter to modify
    new_value : float or str
        New value for the parameter
    """
    import re

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Pattern to match OpenFAST parameter lines:
    # (leading whitespace)(value)(optional whitespace)(param_name)(rest of line)
    # We need to match the value and replace only that part
    # Note: Some files have no space between value and param_name (e.g., "12.00HWindSpeed")
    pattern = r'^(\s*)(\S+?)(\s*' + re.escape(param_name) + r'\b)'

    modified = False
    for i, line in enumerate(lines):
        # Skip comment lines
        if line.strip().startswith('!'):
            continue

        # Check if this line contains the parameter
        match = re.match(pattern, line)
        if match:
            # Replace only the value (group 2), keep everything else
            new_line = match.group(1) + str(new_value) + match.group(3) + line[match.end():]
            lines[i] = new_line
            modified = True
            break

    if not modified:
        raise ValueError(f"Parameter '{param_name}' not found in {filepath}")

    with open(filepath, 'w') as f:
        f.writelines(lines)


def setup_initial_conditions_for_yaw(elastodyn_path, aerodyn_path, wind_speed):
    """
    Set up proper initial conditions for gradual yaw maneuver simulations.

    Key changes:
    1. Set initial rotor speed based on TSR=8 for given wind speed
    2. Set initial yaw angle to 0 degrees (will yaw gradually to target)
    3. Disable Unsteady Aerodynamics to avoid Mach number issues
    4. Enable axial drag in BEMT for better stability
    5. Increase BEMT iteration limit

    Parameters:
    -----------
    elastodyn_path : str
        Path to ElastoDyn file
    aerodyn_path : str
        Path to AeroDyn file
    wind_speed : float
        Wind speed in m/s (used to calculate initial rotor speed)
    """
    # Calculate initial rotor speed based on TSR = 8
    # For NREL 5MW: R = 63 m, rated speed = 12.1 RPM at ~11.4 m/s
    # RotSpeed [RPM] = (TSR * V * 60) / (R * 2 * pi)
    target_tsr = 8.0
    rotor_radius = 63.0  # meters (NREL 5MW rotor radius)
    rated_speed = 12.1  # RPM
    rated_wind_speed = 11.4  # m/s

    # Calculate rotor speed for TSR=8
    rotor_speed = (target_tsr * wind_speed * 60.0) / (rotor_radius * 2.0 * np.pi)

    # Don't exceed rated speed for above-rated wind speeds
    if wind_speed > rated_wind_speed:
        rotor_speed = min(rotor_speed, rated_speed)

    # Set initial rotor speed
    modify_parameter(elastodyn_path, 'RotSpeed', f'{rotor_speed:.2f}')

    # Start at zero yaw angle - will gradually yaw to target
    modify_parameter(elastodyn_path, 'NacYaw', '0.0')

    # Disable Unsteady Aerodynamics in AeroDyn to avoid Mach number issues
    modify_parameter(aerodyn_path, 'UA_Mod', '0')

    # Enable axial drag in induction calculations for better stability at high yaw
    modify_parameter(aerodyn_path, 'AIDrag', 'True')

    # Increase max iterations for BEMT convergence
    modify_parameter(aerodyn_path, 'MaxIter', '300')

    # Enable skew model (CRITICAL: SkewMomCorr only works when Skew_Mod=1)
    modify_parameter(aerodyn_path, 'Skew_Mod', '1')

    # Enable wake redistribution for yawed flow (Pitt/Peters model)
    modify_parameter(aerodyn_path, 'SkewRedistr_Mod', '1')

    print(f"Set initial RotSpeed = {rotor_speed:.2f} rpm (TSR={target_tsr:.1f} at {wind_speed:.1f} m/s)")
    print(f"Set initial NacYaw = 0.0 deg (gradual yaw maneuver)")
    print(f"Disabled Unsteady Aerodynamics (UA_Mod = 0)")
    print(f"Enabled axial drag in BEMT (AIDrag = True)")
    print(f"Increased BEMT iterations (MaxIter = 300)")
    print(f"Enabled skew model (Skew_Mod = 1)")
    print(f"Enabled wake redistribution (SkewRedistr_Mod = 1)")


def setup_yaw_maneuver(servodyn_path, target_yaw_angle):
    """
    Configure ServoDyn for gradual yaw maneuver.

    The maneuver starts at t=25s (after rotor spins up and stabilizes)
    and yaws at 2 deg/s to the target angle.

    Parameters:
    -----------
    servodyn_path : str
        Path to ServoDyn file
    target_yaw_angle : float
        Target yaw angle in degrees
    """
    # Time to start yaw maneuver (allow 25s for rotor to stabilize)
    modify_parameter(servodyn_path, 'TYawManS', '25.0')

    # Yaw rate: 2 deg/s (aggressive but not extreme)
    modify_parameter(servodyn_path, 'YawManRat', '2.0')

    # Final yaw angle
    modify_parameter(servodyn_path, 'NacYawF', f'{target_yaw_angle:.1f}')

    yaw_duration = abs(target_yaw_angle) / 2.0  # Time to complete yaw at 2 deg/s
    yaw_complete_time = 25.0 + yaw_duration

    print(f"Yaw maneuver: 0° → {target_yaw_angle:+.1f}° at 2 deg/s")
    print(f"Maneuver starts at t=25s, completes at t={yaw_complete_time:.1f}s")

    return yaw_complete_time


def calculate_simulation_time(yaw_angle):
    """
    Calculate appropriate simulation time for yaw maneuver.

    Timing breakdown:
    - 0-25s: Rotor spin-up and stabilization at 0° yaw
    - 25-X s: Yaw maneuver (duration = |yaw_angle|/2 seconds at 2 deg/s)
    - X-end: Hold at target yaw for steady-state analysis (30s minimum)

    Parameters:
    -----------
    yaw_angle : float
        Target yaw angle in degrees

    Returns:
    --------
    float : Total simulation time in seconds
    """
    startup_time = 25.0  # Rotor stabilization
    yaw_time = abs(yaw_angle) / 2.0  # Yaw at 2 deg/s
    steady_state_time = 30.0  # Hold for steady-state analysis

    total_time = startup_time + yaw_time + steady_state_time

    # Minimum 55 seconds, round up to nearest 5
    total_time = max(55.0, total_time)
    total_time = np.ceil(total_time / 5.0) * 5.0

    return total_time


def run_openfast(fst_filename, working_directory, openfast_executable):
    """Run OpenFAST simulation"""
    command = f"cd {working_directory} && {openfast_executable} {fst_filename}"
    result = subprocess.run(
        command,
        shell=True,
        executable='/bin/bash',
        capture_output=True,
        text=True
    )
    return result


def save_results(base_name, run_name):
    """Copy result files to a unique location"""
    extensions = ['.out', '.outb', '.sum', '.AD.sum', '.ED.sum', '.BD.sum', '.SrvD.sum']

    for ext in extensions:
        src = f"{base_name}{ext}"
        if os.path.exists(src):
            dst = f"{run_name}{ext}"
            shutil.copy(src, dst)


def extract_steady_state_values(output_file, columns=['GenPwr', 'RtAeroFxh', 'B1RootMyr'],
                                steady_state_fraction=0.3):
    """
    Extract steady-state values from OpenFAST output file

    Parameters:
    -----------
    output_file : str
        Path to the .out file
    columns : list
        Column names to extract steady-state values for
        Default: ['GenPwr', 'RtAeroFxh', 'B1RootMyr']
        - GenPwr: Generator power (kW)
        - RtAeroFxh: Rotor aerodynamic thrust force (N)
        - B1RootMyr: Blade 1 root out-of-plane bending moment (N-m)
    steady_state_fraction : float
        Fraction of simulation time to consider as steady-state (default: last 30%)

    Returns:
    --------
    dict : Dictionary with mean values for each column
    """
    # Read the output file
    with open(output_file, "r") as f:
        lines = f.readlines()

    # Find the header line
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("Time"):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError(f"Could not find header in {output_file}")

    # Load data - skip the units row if present
    df = pd.read_csv(output_file,
                    delim_whitespace=True,
                    skiprows=header_idx,
                    header=0)

    # Remove units row if it exists (typically second row with parentheses)
    if df.iloc[0].astype(str).str.contains(r'\(').any():
        df = df.iloc[1:]

    # Convert all columns to numeric, coercing errors
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Reset index after dropping rows
    df = df.reset_index(drop=True)

    # Calculate steady-state region (last X% of simulation)
    total_rows = len(df)
    steady_state_start = int(total_rows * (1 - steady_state_fraction))
    df_steady = df.iloc[steady_state_start:]

    # Extract mean values for steady-state region
    results = {
        'time_start': df_steady['Time'].iloc[0],
        'time_end': df_steady['Time'].iloc[-1],
        'n_samples': len(df_steady)
    }

    for col in columns:
        if col in df.columns:
            results[f'{col}_mean'] = df_steady[col].mean()
            results[f'{col}_std'] = df_steady[col].std()
            results[f'{col}_max'] = df_steady[col].max()
            results[f'{col}_min'] = df_steady[col].min()
        else:
            print(f"Warning: Column '{col}' not found in output file")
            results[f'{col}_mean'] = None
            results[f'{col}_std'] = None
            results[f'{col}_max'] = None
            results[f'{col}_min'] = None

    return results


def process_and_save_timeseries(output_file, yaw_angle, wind_speed, output_folder, max_rows=600):
    """
    Extract timeseries data from OpenFAST output, downsample, and save to CSV.

    Parameters:
    -----------
    output_file : str
        Path to .out file
    yaw_angle : float
        Nacelle yaw angle (deg)
    wind_speed : float
        Wind speed (m/s)
    output_folder : str
        Folder to save CSV file
    max_rows : int
        Maximum number of rows in output CSV (default 600)

    Returns:
    --------
    pd.DataFrame : Downsampled timeseries data
    """
    # Read output file
    df = pd.read_csv(output_file, sep='\s+', skiprows=[0, 1, 2, 3, 4, 5, 7])

    # Convert all columns to numeric
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Add configuration columns
    df['YawAngle'] = yaw_angle
    df['WindSpeed'] = wind_speed

    # Select only the columns we need
    columns_to_keep = ['Time', 'YawAngle', 'WindSpeed'] + [col for col in output_columns if col in df.columns and col != 'Time']
    df = df[columns_to_keep]

    # Downsample if necessary
    if len(df) > max_rows:
        stride = len(df) // max_rows
        df = df.iloc[::stride]

    # Save to CSV
    os.makedirs(output_folder, exist_ok=True)
    csv_filename = os.path.join(output_folder, f'timeseries_ws{int(wind_speed):02d}_yaw{int(yaw_angle):+03d}.csv')
    df.to_csv(csv_filename, index=False)

    return df


def plot_timeseries(df, yaw_angle, wind_speed, output_folder):
    """
    Create 8-panel subplot showing key timeseries variables.

    Subplots:
    1. RtSkew (deg)
    2. B1RootMyr (kN-m)
    3. RtAeroFxh (kN)
    4. BldPitch1 (deg)
    5. RtTSR (-)
    6. RotTorq (kN-m)
    7. GenPwr (kW)
    8. RtAeroCt (-)
    """
    fig, axes = plt.subplots(4, 2, figsize=(14, 12))
    fig.suptitle(f'Yaw Angle: {yaw_angle:+.1f}° | Wind Speed: {wind_speed:.1f} m/s', fontsize=14, fontweight='bold')

    # Flatten axes for easier indexing
    axes = axes.flatten()

    # Plot configurations: (column_name, ylabel, title)
    plot_config = [
        ('RtSkew', 'RtSkew (deg)', 'Rotor Skew Angle'),
        ('B1RootMyr', 'Moment (kN-m)', 'Blade Root Out-of-Plane Moment'),
        ('RtAeroFxh', 'Force (kN)', 'Rotor Thrust Force'),
        ('BldPitch1', 'Pitch (deg)', 'Blade Pitch Angle'),
        ('RtTSR', 'TSR (-)', 'Tip Speed Ratio'),
        ('RotTorq', 'Torque (kN-m)', 'Rotor Torque'),
        ('GenPwr', 'Power (kW)', 'Generator Power'),
        ('RtAeroCt', 'CT (-)', 'Thrust Coefficient'),
    ]

    for idx, (col, ylabel, title) in enumerate(plot_config):
        ax = axes[idx]
        if col in df.columns:
            ax.plot(df['Time'], df[col], 'b-', linewidth=0.8)
            ax.set_ylabel(ylabel, fontsize=10)
            ax.set_title(title, fontsize=10, fontweight='bold')
            ax.grid(True, alpha=0.3)

            if idx >= 6:  # Bottom row
                ax.set_xlabel('Time (s)', fontsize=10)
        else:
            ax.text(0.5, 0.5, f'{col}\nNot Available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title, fontsize=10)

    plt.tight_layout()

    # Save plot
    os.makedirs(output_folder, exist_ok=True)
    png_filename = os.path.join(output_folder, f'timeseries_ws{int(wind_speed):02d}_yaw{int(yaw_angle):+03d}.png')
    plt.savefig(png_filename, dpi=150, bbox_inches='tight')
    plt.close()


def create_heatmaps(results_df, skew_corr_label, output_folder):
    """
    Create heatmaps showing steady-state values across wind speed and yaw angle matrix.

    Creates both combined figure (4×3 grid) and individual full-size heatmaps.

    Parameters:
    -----------
    results_df : pd.DataFrame
        DataFrame with columns: YawAngle, WindSpeed, and steady-state mean values
    skew_corr_label : str
        Label for SkewMomCorr setting (e.g., 'true' or 'false')
    output_folder : str
        Folder to save heatmap figures
    """
    # Variables to create heatmaps for
    heatmap_vars = [
        ('BldPitch1_mean', 'Pitch Angle (deg)', 'pitch'),
        ('RtTSR_mean', 'Tip Speed Ratio (-)', 'tsr'),
        ('GenPwr_mean', 'Power Output (kW)', 'power'),
        ('RtAeroCp_mean', 'Power Coefficient Cp (-)', 'cp'),
        ('RtAeroCt_mean', 'Thrust Coefficient Ct (-)', 'ct'),
        ('B1RootMyr_mean', 'Blade Root Moment (kN-m)', 'blade_moment'),
        ('RotSpeed_mean', 'Rotor Speed (RPM)', 'rotor_speed'),
        ('RotTorq_mean', 'Rotor Torque (kN-m)', 'rotor_torque'),
        ('RtAeroFxh_mean', 'Thrust Force (kN)', 'thrust'),
        ('YawBrMzp_mean', 'Yaw Bearing Moment (kN-m)', 'yaw_moment'),
        ('TwrBsMyt_mean', 'Tower Base Moment (kN-m)', 'tower_moment'),
    ]

    os.makedirs(output_folder, exist_ok=True)

    # Create pivot tables for each variable
    pivot_tables = {}
    for var_col, _, var_name in heatmap_vars:
        if var_col in results_df.columns:
            pivot = results_df.pivot(index='WindSpeed', columns='YawAngle', values=var_col)
            pivot_tables[var_name] = (pivot, var_col)

    # Create combined heatmap figure (4×3 grid)
    fig, axes = plt.subplots(4, 3, figsize=(18, 20))
    fig.suptitle(f'Steady-State Performance Maps (SkewMomCorr={skew_corr_label})',
                 fontsize=16, fontweight='bold')
    axes = axes.flatten()

    for idx, (var_col, var_label, var_name) in enumerate(heatmap_vars):
        ax = axes[idx]
        if var_name in pivot_tables:
            pivot, _ = pivot_tables[var_name]
            im = ax.pcolormesh(pivot.columns, pivot.index, pivot.values, shading='auto', cmap='RdYlBu_r')
            ax.set_xlabel('Yaw Angle (deg)', fontsize=10)
            ax.set_ylabel('Wind Speed (m/s)', fontsize=10)
            ax.set_title(var_label, fontsize=11, fontweight='bold')
            cbar = plt.colorbar(im, ax=ax)
            cbar.ax.tick_params(labelsize=9)
        else:
            ax.text(0.5, 0.5, f'{var_label}\nData Not Available',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(var_label, fontsize=11)

    plt.tight_layout()
    combined_filename = os.path.join(output_folder, 'heatmap_combined.png')
    plt.savefig(combined_filename, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved combined heatmap: {combined_filename}")

    # Create individual full-size heatmaps
    for var_col, var_label, var_name in heatmap_vars:
        if var_name in pivot_tables:
            pivot, _ = pivot_tables[var_name]

            fig, ax = plt.subplots(figsize=(10, 6))
            im = ax.pcolormesh(pivot.columns, pivot.index, pivot.values, shading='auto', cmap='RdYlBu_r')
            ax.set_xlabel('Yaw Angle (deg)', fontsize=12)
            ax.set_ylabel('Wind Speed (m/s)', fontsize=12)
            ax.set_title(f'{var_label} (SkewMomCorr={skew_corr_label})', fontsize=14, fontweight='bold')

            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label(var_label, fontsize=11)
            cbar.ax.tick_params(labelsize=10)

            plt.tight_layout()
            individual_filename = os.path.join(output_folder, f'heatmap_{var_name}.png')
            plt.savefig(individual_filename, dpi=150, bbox_inches='tight')
            plt.close()

    print(f"Saved {len(pivot_tables)} individual heatmaps")


# Verify all required files exist before starting
required_files = {
    'ElastoDyn': elastodyn_path,
    'ElastoDyn_BDoutputs': elastodyn_bd_path,
    'ServoDyn': servodyn_path,
    'AeroDyn': aerodyn_path,
    'InflowWind': inflow_path,
    'FST': os.path.join(work_dir, fst_path)
}

print("Checking required files...")
missing_files = []
for name, path in required_files.items():
    if os.path.exists(path):
        print(f"{name}: {path}")
    else:
        print(f"  {name}: {path} NOT FOUND")
        missing_files.append(name)

if missing_files:
    raise FileNotFoundError(f"Missing required files: {', '.join(missing_files)}")

print("\nAll required files found. Proceeding with simulations...\n")

# Backup original files
fst_full_path = os.path.join(work_dir, fst_path)
backup_elastodyn = elastodyn_path + '.backup'
backup_elastodyn_bd = elastodyn_bd_path + '.backup'
backup_servodyn = servodyn_path + '.backup'
backup_aerodyn = aerodyn_path + '.backup'
backup_inflow = inflow_path + '.backup'
backup_fst = fst_full_path + '.backup'

shutil.copy(elastodyn_path, backup_elastodyn)
shutil.copy(elastodyn_bd_path, backup_elastodyn_bd)
shutil.copy(servodyn_path, backup_servodyn)
shutil.copy(aerodyn_path, backup_aerodyn)
shutil.copy(inflow_path, backup_inflow)
shutil.copy(fst_full_path, backup_fst)
print("✓ Backup files created\n")

# Loop over SkewMomCorr settings
for skew_corr in skew_corr_settings:
    skew_corr_label = 'true' if skew_corr else 'false'

    print(f"\n{'#'*80}")
    print(f"# REV2: SKEW_MOD=1, SKEWMOMCORR = {skew_corr_label.upper()}")
    print(f"{'#'*80}\n")

    # Create output folders for this SkewMomCorr setting (Rev2 with Skew_Mod=1)
    timeseries_folder = os.path.join(work_dir, f'timeseries_rev2_skewcorr_{skew_corr_label}')
    heatmaps_folder = os.path.join(work_dir, f'heatmaps_rev2_skewcorr_{skew_corr_label}')

    # Initialize results storage for this SkewMomCorr setting
    steady_state_results = []

    try:
        for ws in ws_list:
            # Set wind speed for this batch of yaw angle tests
            modify_parameter(inflow_path, 'HWindSpeed', f"{ws:.2f}")
            print(f"\n{'='*80}")
            print(f"WIND SPEED: {ws:.1f} m/s | SkewMomCorr: {skew_corr}")
            print(f"{'='*80}")

            # Set up initial conditions for gradual yaw maneuver (do this once per wind speed)
            print(f"\nConfiguring initial conditions for gradual yaw maneuvers...")
            setup_initial_conditions_for_yaw(elastodyn_path, aerodyn_path, ws)
            # Also update the BDoutputs file
            setup_initial_conditions_for_yaw(elastodyn_bd_path, aerodyn_path, ws)

            # Set SkewMomCorr parameter in AeroDyn (must use True/False, not 0/1)
            skew_corr_value = 'True' if skew_corr else 'False'
            modify_parameter(aerodyn_path, 'SkewMomCorr', skew_corr_value)
            print(f"Set SkewMomCorr = {skew_corr_value}")

            for yaw in yaw_angles:
                print(f"\n{'-'*60}")
                print(f"Yaw Angle: {yaw:+.1f}° | Wind Speed: {ws:.1f} m/s")
                print(f"{'-'*60}")

                # Configure gradual yaw maneuver in ServoDyn
                yaw_complete_time = setup_yaw_maneuver(servodyn_path, yaw)

                # Calculate appropriate simulation time
                sim_time = calculate_simulation_time(yaw)
                modify_parameter(os.path.join(work_dir, fst_path), 'TMax', f"{sim_time:.1f}")
                print(f"Set TMax = {sim_time:.1f}s")

                # Run OpenFAST
                result = run_openfast(fst_path, work_dir, openfast_exe)

                if result.returncode != 0:
                    print(f"ERROR: Simulation failed for yaw angle {yaw:.1f} deg")
                    print(f"Return code: {result.returncode}")
                    print(f"STDOUT (last 100 lines):\n{result.stdout[-5000:]}")
                    print(f"STDERR:\n{result.stderr}")
                    continue

                print(f"✓ OpenFAST completed successfully")

                # Process timeseries data
                output_file = f"{sim_output_base}.out"

                # Extract and save downsampled timeseries CSV
                df_timeseries = process_and_save_timeseries(output_file, yaw, ws, timeseries_folder, max_rows=600)
                print(f"Saved timeseries CSV ({len(df_timeseries)} rows)")

                # Create timeseries subplot
                plot_timeseries(df_timeseries, yaw, ws, timeseries_folder)
                print(f"Saved timeseries plot")

                # Extract steady-state values from output file
                ss_values = extract_steady_state_values(output_file, columns=output_columns)
                ss_values['YawAngle'] = yaw
                ss_values['WindSpeed'] = ws
                steady_state_results.append(ss_values)

                print(f"  Steady-state: t = {ss_values['time_start']:.1f}-{ss_values['time_end']:.1f}s ({ss_values['n_samples']} samples)")

                # Delete large .out file to save space
                if os.path.exists(output_file):
                    os.remove(output_file)
                    print(f"Deleted .out file (saved space)")

                print(f"Completed simulation: ws={ws} m/s, yaw={yaw:+.1f}°")

    except Exception as e:
        print(f"\nFATAL ERROR during SkewMomCorr={skew_corr_label} simulations:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Create summary DataFrame and save
        print(f"GENERATING OUTPUTS FOR REV2 (SKEW_MOD=1, SKEWMOMCORR={skew_corr_label.upper()})")

        if len(steady_state_results) > 0:
            results_df = pd.DataFrame(steady_state_results)

            # Save summary CSV (Rev2 with Skew_Mod=1)
            summary_csv_path = os.path.join(work_dir, f'summary_rev2_skewcorr_{skew_corr_label}.csv')
            results_df.to_csv(summary_csv_path, index=False)
            print(f"\n✓ Summary CSV saved: {summary_csv_path}")
            print(f"  ({len(results_df)} successful simulations)")

            # Generate heatmaps
            print(f"\nGenerating heatmaps...")
            heatmap_label = f'rev2_skewcorr_{skew_corr_label}'
            create_heatmaps(results_df, heatmap_label, heatmaps_folder)
        else:
            print(f"\nNo successful simulations for Rev2 (Skew_Mod=1, SkewMomCorr={skew_corr_label})")

# Restore original backup files
print(f"\n{'='*80}")
print(f"RESTORING ORIGINAL FILES")
print(f"{'='*80}")
shutil.copy(backup_elastodyn, elastodyn_path)
shutil.copy(backup_elastodyn_bd, elastodyn_bd_path)
shutil.copy(backup_servodyn, servodyn_path)
shutil.copy(backup_aerodyn, aerodyn_path)
shutil.copy(backup_inflow, inflow_path)
shutil.copy(backup_fst, fst_full_path)
print("✓ Restored original input files")

print(f"\n{'='*80}")
print(f"ALL SIMULATIONS COMPLETE")
print(f"{'='*80}")
print("\nOutput Summary:")
print(f"  - Timeseries CSVs and plots in timeseries_rev2_skewcorr_*/")
print(f"  - Heatmaps in heatmaps_rev2_skewcorr_*/")
print(f"  - Summary CSVs: summary_rev2_skewcorr_*.csv")
print(f"\nTotal simulations: {len(skew_corr_settings)} × {len(ws_list)} × {len(yaw_angles)} = {len(skew_corr_settings) * len(ws_list) * len(yaw_angles)}")
print(f"\nNote: Previous baseline data (Skew_Mod=0) preserved in *_skewmod0_* folders")

