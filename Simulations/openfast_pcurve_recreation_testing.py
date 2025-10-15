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

# Instructions for python shell to update wind speed parameters with each run
inflow_path = '/Users/benhealy/OpenFAST/Simulations/5MW_Baseline/NRELOffshrBsline5MW_InflowWind_12mps_cp_curve.dat' # aerodyn file where wind speed will be adjusted
param_name = 'HWindSpeed'
ws_list = [1, 5, 10, 15, 20, 25]
# ws_list = np.linspace(1, 15, 5)
fst_path = '5MW_Land_BD_DLL_WTurb_CP_Curve_Test.fst'  # Just the filename, since we'll run from the directory
work_dir = '/Users/benhealy/OpenFAST/Simulations/5MW_Land_BD_DLL_Wturb_Cp_Curve_Test'
sim_output_base = '/Users/benhealy/OpenFAST/Simulations/5MW_Land_BD_DLL_Wturb_Cp_Curve_Test/5MW_Land_BD_DLL_WTurb_CP_Curve_Test'
openfast_exe = '/Users/benhealy/OpenFAST/build-testing/glue-codes/openfast/openfast'
conda_env = 'openfast-dev'


def modify_wind_speed(filepath, param_name, new_value):
    """Modify HWindSpeed parameter in the .dat inflow file"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    modified = False
    for i, line in enumerate(lines):
        if param_name in line and not line.strip().startswith('!'):
            parts = line.split()
            if len(parts) >= 2:
                parts[0] = str(new_value)
                lines[i] = '   '.join(parts) + '\n'
                modified = True
                break
    
    if not modified:
        raise ValueError(f"Parameter '{param_name}' not found in {filepath}")
    
    with open(filepath, 'w') as f:
        f.writelines(lines)


def run_openfast(fst_filename, working_directory, openfast_executable, conda_environment):
    """Run OpenFAST simulation with proper conda environment and directory"""
    # Build command that activates conda env and runs openfast
    command = f"source $(conda info --base)/etc/profile.d/conda.sh && conda activate {conda_environment} && cd {working_directory} && {openfast_executable} {fst_filename}"
    
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


def extract_steady_state_values(output_file, columns=['RtAeroCt', 'RtAeroCp', 'GenPwr'], 
                                  steady_state_fraction=0.5):
    """
    Extract steady-state values from OpenFAST output file
    
    Parameters:
    -----------
    output_file : str
        Path to the .out file
    columns : list
        Column names to extract steady-state values for
    steady_state_fraction : float
        Fraction of simulation time to consider as steady-state (default: last 50%)
    
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
        else:
            print(f"Warning: Column '{col}' not found in output file")
            results[f'{col}_mean'] = None
            results[f'{col}_std'] = None
    
    return results


# Backup original .dat file
backup_file = inflow_path + '.backup'
shutil.copy(inflow_path, backup_file)

# Initialize results storage
steady_state_results = []

try:
    for ws in ws_list:
        print(f"\n{'='*60}")
        print(f"Wind Speed: {ws:.1f} m/s")
        print(f"{'='*60}")
        
        # Modify wind speed
        modify_wind_speed(inflow_path, param_name, f"{ws:.2f}")
        print(f"✓ Modified {param_name} = {ws:.2f} m/s")
        
        # Run OpenFAST
        result = run_openfast(fst_path, work_dir, openfast_exe, conda_env)
        
        if result.returncode != 0:
            print(f"ERROR: Simulation failed for wind speed {ws:.1f} m/s")
            print(result.stderr)
            continue
        
        print(f"✓ OpenFAST completed")
        
        # Extract steady-state values from output file
        output_file = f"{sim_output_base}.out"
        ss_values = extract_steady_state_values(output_file)
        ss_values['WindSpeed'] = ws
        steady_state_results.append(ss_values)
        
        print(f"  Steady-state region: t = {ss_values['time_start']:.1f} to {ss_values['time_end']:.1f} s ({ss_values['n_samples']} samples)")
        print(f"  RtAeroCt: {ss_values['RtAeroCt_mean']:.6f} ± {ss_values['RtAeroCt_std']:.6f}")
        print(f"  RtAeroCp: {ss_values['RtAeroCp_mean']:.6f} ± {ss_values['RtAeroCp_std']:.6f}")
        print(f"  GenPwr: {ss_values['GenPwr_mean']:.1f} ± {ss_values['GenPwr_std']:.1f} kW")
        
        # Save results files
        run_name = f"{sim_output_base}_ws{int(ws)}"
        save_results(sim_output_base, run_name)
        
        print(f"✓ All results saved for {ws:.1f} m/s")

finally:
    # Restore original file
    shutil.copy(backup_file, inflow_path)
    print(f"\n✓ Restored original inflow file")

# Create summary DataFrame
results_df = pd.DataFrame(steady_state_results)
results_summary_path = os.path.join(work_dir, 'steady_state_summary.csv')
results_df.to_csv(results_summary_path, index=False)
print(f"\n✓ Steady-state summary saved to: {results_summary_path}")

# Load NREL reference data for comparison
nrel_url = 'https://raw.githubusercontent.com/NREL/turbine-models/main/turbine_models/data/Offshore/NREL_Reference_5MW_126.csv'
nrel_df = pd.read_csv(nrel_url)
nrel_df.columns = nrel_df.columns.str.strip()  # Remove any whitespace from column names

# Prepare simulation results for comparison
sim_comparison = results_df[['WindSpeed', 'RtAeroCt_mean', 'RtAeroCp_mean', 'GenPwr_mean']].copy()
sim_comparison.columns = ['WindSpeed', 'Ct_Sim', 'Cp_Sim', 'Power_Sim']

# Merge with NREL reference data
comparison_df = sim_comparison.merge(
    nrel_df[['Wind Speed [m/s]', 'Ct [-]', 'Cp [-]', 'Power [kW]']],
    left_on='WindSpeed',
    right_on='Wind Speed [m/s]',
    how='left'
)
comparison_df = comparison_df.drop(columns=['Wind Speed [m/s]'])
comparison_df.columns = ['WindSpeed', 'Ct_Sim', 'Cp_Sim', 'Power_Sim', 'Ct_Ref', 'Cp_Ref', 'Power_Ref']

# Calculate differences
comparison_df['Ct_Diff_%'] = ((comparison_df['Ct_Sim'] - comparison_df['Ct_Ref']) / comparison_df['Ct_Ref'] * 100)
comparison_df['Cp_Diff_%'] = ((comparison_df['Cp_Sim'] - comparison_df['Cp_Ref']) / comparison_df['Cp_Ref'] * 100)
comparison_df['Power_Diff_%'] = ((comparison_df['Power_Sim'] - comparison_df['Power_Ref']) / comparison_df['Power_Ref'] * 100)

# Save comparison
comparison_path = os.path.join(work_dir, 'nrel_comparison.csv')
comparison_df.to_csv(comparison_path, index=False)
print(f"✓ Comparison with NREL reference saved to: {comparison_path}")

# Display summary
print("\n" + "="*60)
print("STEADY-STATE RESULTS SUMMARY")
print("="*60)
print(results_df[['WindSpeed', 'RtAeroCt_mean', 'RtAeroCp_mean', 'GenPwr_mean']].to_string(index=False))

# Display comparison
print("\n" + "="*60)
print("COMPARISON WITH NREL REFERENCE DATA")
print("="*60)
print("\nCp (Power Coefficient):")
print(comparison_df[['WindSpeed', 'Cp_Sim', 'Cp_Ref', 'Cp_Diff_%']].to_string(index=False))
print("\nCt (Thrust Coefficient):")
print(comparison_df[['WindSpeed', 'Ct_Sim', 'Ct_Ref', 'Ct_Diff_%']].to_string(index=False))
print("\nPower [kW]:")
print(comparison_df[['WindSpeed', 'Power_Sim', 'Power_Ref', 'Power_Diff_%']].to_string(index=False))