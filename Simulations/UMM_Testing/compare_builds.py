#!/usr/bin/env python3
"""
Python wrapper to execute OpenFAST simulation executables over several build directories and input parameters

Updates the input .dat and .fst files to modify input parameters and assumptions
Modifies the bash command to swap between fortran builds of OpenFAST

Test matrix:
    - Varying Yaw-Misalignment/Skew Angles
    - Varying free-stream wind velocities
    
Comparision:
    - Standard OpenFAST build using 3D BEM solution to compute axial induction from Glauert Momentum
    - New OpenFAST build using 3D BEM solution to compute axial induction from the Unified Momentum Model (Liew et al 2024)
"""
import os
import pandas as pd
import subprocess
import numpy as np
import shutil
import re
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

# Build to use (single build, iterate SkewMomCorr at runtime)
BUILDS = {
    'UMM': '/Users/benhealy/OpenFAST/build-UMM/glue-codes/openfast/openfast',
}

# SkewMomCorr settings to compare
SKEW_MOM_CORR = {
    'None': 0,      # Classical 1D momentum (no skew correction)
    'Glauert': 1,   # Glauert correction
    'UMM': 2,       # Unified Momentum Model (Liew et al 2024)
}

# Test matrix
YAW_ANGLES = [-30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 30]  # degrees
WIND_SPEEDS = [4, 6, 8, 10, 12, 14, 16, 18]  # m/s

# Quick test (uncomment to use smaller test matrix)
# YAW_ANGLES = [0, 15, 30]
# WIND_SPEEDS = [8, 12]

# Paths
WORK_DIR = '/Users/benhealy/OpenFAST/Simulations/UMM_Testing/results_comp_UMM_full_matrix_20260123/'
FST_FILE = '5MW_Land_BD_DLL_WTurb_Skewed_Loads.fst'
OUTPUT_BASE = os.path.join(WORK_DIR, '5MW_Land_BD_DLL_WTurb_Skewed_Loads')

# Parallelization settings
MAX_WORKERS = 8  # Number of parallel simulations

# Files needed for each simulation (will be copied to temp directories)
INPUT_FILES = {
    'elastodyn': os.path.join(WORK_DIR, 'NRELOffshrBsline5MW_Onshore_ElastoDyn.dat'),
    'elastodyn_bd': os.path.join(WORK_DIR, 'NRELOffshrBsline5MW_Onshore_ElastoDyn_BDoutputs.dat'),
    'servodyn': os.path.join(WORK_DIR, 'NRELOffshrBsline5MW_Onshore_ServoDyn.dat'),
    'aerodyn': os.path.join(WORK_DIR, 'NRELOffshrBsline5MW_Onshore_AeroDyn.dat'),
    'inflow': os.path.join(WORK_DIR, 'NRELOffshrBsline5MW_InflowWind.dat')
}

# Output columns to extract
'''
OUTPUT_COLS = ['GenPwr', 'RtAeroCp', 'RtAeroCt', 'RtAeroFxh', 'B1RootMyr',
               'YawBrMzp', 'TwrBsMyt', 'RotSpeed', 'RtTSR', 'B1Pitch']
'''

'''
OUTPUT_COLS = ['GenPwr', 'RtAeroCp', 'RtAeroCt', 'RtAeroFxh', 'B1RootMyr',
               'YawBrMzp', 'TwrBsMyt', 'RotSpeed', 'RtTSR', 'B1N1AxInd',
               'B1N2AxInd', 'B1N3AxInd', 'B1N4AxInd', 'B1N5AxInd', 'B1N6AxInd',
               'B1N7AxInd', 'B1N8AxInd', 'B1N9AxInd', 'B1Pitch']
'''
OUTPUT_COLS = ['GenPwr', 'RtAeroCp', 'RtAeroCt', 'RtAeroFxh', 'B1RootMyr',
               'YawBrMzp', 'TwrBsMyt', 'RotSpeed', 'RtTSR', 'B1N1AxInd',
               'B1N2AxInd', 'B1N3AxInd', 'B1N4AxInd', 'B1N5AxInd', 'B1N6AxInd',
               'B1N7AxInd', 'B1N8AxInd', 'B1N9AxInd', 'B1Pitch', 'B1Azimuth']


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def modify_parameter(filepath, param_name, new_value):
    """Modify parameter in OpenFAST input file"""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    pattern = r'^(\s*)(\S+?)(\s*' + re.escape(param_name) + r'\b)'
    modified = False

    for i, line in enumerate(lines):
        if line.strip().startswith('!'):
            continue
        match = re.match(pattern, line)
        if match:
            lines[i] = match.group(1) + str(new_value) + match.group(3) + line[match.end():]
            modified = True
            break

    if not modified:
        raise ValueError(f"Parameter '{param_name}' not found in {filepath}")

    with open(filepath, 'w') as f:
        f.writelines(lines)


def setup_aerodyn(aerodyn_path, wind_speed, skew_corr):
    """Configure AeroDyn for yaw simulations

    Args:
        aerodyn_path: Path to AeroDyn input file
        wind_speed: Wind speed (m/s)
        skew_corr: SkewMomCorr value (0=None, 1=Glauert, 2=UMM)
    """
    modify_parameter(aerodyn_path, 'UA_Mod', '0')
    modify_parameter(aerodyn_path, 'AIDrag', 'True')
    modify_parameter(aerodyn_path, 'MaxIter', '300')
    modify_parameter(aerodyn_path, 'Skew_Mod', '1')
    modify_parameter(aerodyn_path, 'SkewRedistr_Mod', '1')
    modify_parameter(aerodyn_path, 'SkewMomCorr', str(skew_corr))



def setup_elastodyn(elastodyn_path, wind_speed):
    """Configure ElastoDyn initial conditions"""
    target_tsr = 8.0
    rotor_radius = 63.0
    rated_speed = 12.1
    rated_wind_speed = 11.4

    rotor_speed = (target_tsr * wind_speed * 60.0) / (rotor_radius * 2.0 * np.pi)
    if wind_speed > rated_wind_speed:
        rotor_speed = min(rotor_speed, rated_speed)

    modify_parameter(elastodyn_path, 'RotSpeed', f'{rotor_speed:.2f}')
    modify_parameter(elastodyn_path, 'NacYaw', '0.0')


def setup_servodyn(servodyn_path, target_yaw_angle):
    """Configure ServoDyn for yaw maneuver"""
    modify_parameter(servodyn_path, 'TYawManS', '25.0')
    modify_parameter(servodyn_path, 'YawManRat', '2.0')
    modify_parameter(servodyn_path, 'NacYawF', f'{target_yaw_angle:.1f}')


def calculate_sim_time(yaw_angle):
    """Calculate simulation time based on yaw angle"""
    total_time = 25.0 + abs(yaw_angle) / 2.0 + 30.0
    return max(55.0, np.ceil(total_time / 5.0) * 5.0)


def run_openfast(fst_file, work_dir, exe_path):
    """Run OpenFAST simulation"""
    cmd = f"cd {work_dir} && {exe_path} {fst_file}"
    result = subprocess.run(cmd, shell=True, executable='/bin/bash',
                          capture_output=True, text=True)
    return result


def extract_steady_state(output_file, columns, ss_fraction=0.3):
    """Extract steady-state values from .out file"""
    with open(output_file, 'r') as f:
        lines = f.readlines()

    header_idx = next(i for i, line in enumerate(lines) if line.strip().startswith('Time'))

    df = pd.read_csv(output_file, delim_whitespace=True, skiprows=header_idx, header=0)
    if df.iloc[0].astype(str).str.contains(r'\(').any():
        df = df.iloc[1:]

    df = df.apply(pd.to_numeric, errors='coerce').reset_index(drop=True)

    ss_start = int(len(df) * (1 - ss_fraction))
    df_ss = df.iloc[ss_start:]

    results = {}
    for col in columns:
        if col in df.columns:
            results[f'{col}_mean'] = df_ss[col].mean()
            results[f'{col}_std'] = df_ss[col].std()

    return results


# ============================================================================
# PARALLEL JOB EXECUTION
# ============================================================================

def run_simulation_job(job_config):
    """Run single simulation in isolated directory.

    Args:
        job_config: dict with keys:
            - exe_path: Path to OpenFAST executable
            - ws: Wind speed (m/s)
            - yaw: Yaw angle (degrees)
            - skew_name: Name of skew correction method
            - skew_val: SkewMomCorr value (0, 1, or 2)
            - base_work_dir: Original working directory with input files
            - fst_file: Name of .fst file
            - job_id: Unique job identifier

    Returns:
        dict with results or None if failed
    """
    exe_path = job_config['exe_path']
    ws = job_config['ws']
    yaw = job_config['yaw']
    skew_name = job_config['skew_name']
    skew_val = job_config['skew_val']
    base_work_dir = job_config['base_work_dir']
    fst_file = job_config['fst_file']
    job_id = job_config['job_id']

    # Create isolated temp directory inside work directory (preserves relative path structure)
    temp_dir = os.path.join(base_work_dir, f'job_{job_id}')
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Copy all input files to temp directory
        for filename in os.listdir(base_work_dir):
            src = os.path.join(base_work_dir, filename)
            dst = os.path.join(temp_dir, filename)
            if os.path.isfile(src) and not filename.endswith('.backup_compare'):
                shutil.copy2(src, dst)

        # Define paths in temp directory
        temp_fst = os.path.join(temp_dir, fst_file)
        temp_input_files = {
            'elastodyn': os.path.join(temp_dir, 'NRELOffshrBsline5MW_Onshore_ElastoDyn.dat'),
            'elastodyn_bd': os.path.join(temp_dir, 'NRELOffshrBsline5MW_Onshore_ElastoDyn_BDoutputs.dat'),
            'servodyn': os.path.join(temp_dir, 'NRELOffshrBsline5MW_Onshore_ServoDyn.dat'),
            'aerodyn': os.path.join(temp_dir, 'NRELOffshrBsline5MW_Onshore_AeroDyn.dat'),
            'inflow': os.path.join(temp_dir, 'NRELOffshrBsline5MW_InflowWind.dat')
        }

        # Adjust relative paths in all copied files (add ../ since we're one level deeper)
        for filepath in [temp_fst] + list(temp_input_files.values()):
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                # Adjust paths like "../../" and "./../../" to "../../../" and "./../../../"
                content = content.replace('"../../', '"../../../')
                content = content.replace('"./../', '"../../')  # ./.. -> ../..
                with open(filepath, 'w') as f:
                    f.write(content)

        # Configure parameters for this job
        modify_parameter(temp_input_files['inflow'], 'HWindSpeed', f"{ws:.2f}")
        setup_elastodyn(temp_input_files['elastodyn'], ws)
        setup_elastodyn(temp_input_files['elastodyn_bd'], ws)
        setup_aerodyn(temp_input_files['aerodyn'], ws, skew_val)
        setup_servodyn(temp_input_files['servodyn'], yaw)

        sim_time = calculate_sim_time(yaw)
        modify_parameter(temp_fst, 'TMax', f"{sim_time:.1f}")

        # Run simulation
        result = run_openfast(fst_file, temp_dir, exe_path)

        if result.returncode != 0:
            # Get last 20 lines of stderr/stdout for error context
            error_output = (result.stderr or result.stdout or "No output")[-2000:]
            return {
                'success': False,
                'job_id': job_id,
                'skew_corr': skew_name,
                'yaw': yaw,
                'ws': ws,
                'error': f"Exit code {result.returncode}",
                'error_detail': error_output
            }

        # Extract results
        output_file = os.path.join(temp_dir, '5MW_Land_BD_DLL_WTurb_Skewed_Loads.out')
        ss_values = extract_steady_state(output_file, OUTPUT_COLS)
        ss_values['success'] = True
        ss_values['job_id'] = job_id
        ss_values['skew_corr'] = skew_name
        ss_values['yaw'] = yaw
        ss_values['ws'] = ws

        return ss_values

    except Exception as e:
        return {
            'success': False,
            'job_id': job_id,
            'skew_corr': skew_name,
            'yaw': yaw,
            'ws': ws,
            'error': str(e)
        }
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# MAIN COMPARISON LOOP
# ============================================================================

def main():
    print("="*80)
    print("OpenFAST SkewMomCorr Comparison (Parallel Execution)")
    print("="*80)
    print(f"\nBuild: {list(BUILDS.values())[0]}")
    print(f"\nSkewMomCorr settings to compare:")
    for name, val in SKEW_MOM_CORR.items():
        print(f"  {name}: {val}")
    print(f"\nTest matrix: {len(WIND_SPEEDS)} wind speeds × {len(SKEW_MOM_CORR)} skew_corr × {len(YAW_ANGLES)} yaw angles")
    total_sims = len(WIND_SPEEDS) * len(SKEW_MOM_CORR) * len(YAW_ANGLES)
    print(f"Total simulations: {total_sims}")
    print(f"Parallel workers: {MAX_WORKERS}")

    # Get the single build executable
    exe_path = list(BUILDS.values())[0]

    # Build list of all jobs
    jobs = []
    job_id = 0
    for ws in WIND_SPEEDS:
        for skew_name, skew_val in SKEW_MOM_CORR.items():
            for yaw in YAW_ANGLES:
                jobs.append({
                    'exe_path': exe_path,
                    'ws': ws,
                    'yaw': yaw,
                    'skew_name': skew_name,
                    'skew_val': skew_val,
                    'base_work_dir': WORK_DIR,
                    'fst_file': FST_FILE,
                    'job_id': job_id
                })
                job_id += 1

    print(f"\nStarting {len(jobs)} simulations with {MAX_WORKERS} workers...")
    print("-" * 80)

    start_time = time.time()
    all_results = []
    failed_jobs = []
    completed = 0

    # Execute in parallel
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_simulation_job, job): job for job in jobs}

        for future in as_completed(futures):
            job = futures[future]
            completed += 1

            try:
                result = future.result()

                if result.get('success', False):
                    all_results.append(result)
                    status = "OK"
                else:
                    failed_jobs.append(result)
                    status = f"FAILED: {result.get('error', 'Unknown')}"

                print(f"  [{completed:3d}/{len(jobs)}] ws={job['ws']:2d} yaw={job['yaw']:+3d}° {job['skew_name']:8s} ... {status}")

            except Exception as e:
                failed_jobs.append({
                    'job_id': job['job_id'],
                    'skew_corr': job['skew_name'],
                    'yaw': job['yaw'],
                    'ws': job['ws'],
                    'error': str(e)
                })
                print(f"  [{completed:3d}/{len(jobs)}] ws={job['ws']:2d} yaw={job['yaw']:+3d}° {job['skew_name']:8s} ... EXCEPTION: {e}")

    print("-" * 80)
    elapsed_time = time.time() - start_time
    print(f"Completed: {len(all_results)}/{len(jobs)} simulations")
    print(f"Total elapsed time: {elapsed_time/60:.1f} minutes ({elapsed_time:.1f} seconds)")
    print(f"Average per simulation: {elapsed_time/len(jobs):.1f} seconds")
    if failed_jobs:
        print(f"Failed: {len(failed_jobs)} simulations")
        for job in failed_jobs:
            print(f"  - ws={job['ws']}, yaw={job['yaw']}, skew={job['skew_corr']}: {job.get('error', 'Unknown')}")
            if 'error_detail' in job:
                # Print last few lines of error detail
                detail_lines = job['error_detail'].strip().split('\n')[-10:]
                for line in detail_lines:
                    print(f"      {line}")

    if not all_results:
        print("\nNo successful simulations. Exiting.")
        return

    # Save results
    print(f"\n{'='*80}")
    print("Saving results...")
    print(f"{'='*80}")

    # Remove internal tracking fields before creating DataFrame
    for result in all_results:
        result.pop('success', None)
        result.pop('job_id', None)

    df_all = pd.DataFrame(all_results)

    # Save combined results
    combined_csv = os.path.join(WORK_DIR, 'skew_corr_comparison_combined.csv')
    df_all.to_csv(combined_csv, index=False)
    print(f"  Combined: {combined_csv}")

    # Save per-skew_corr results
    for skew_name in SKEW_MOM_CORR.keys():
        df_skew = df_all[df_all['skew_corr'] == skew_name]
        skew_csv = os.path.join(WORK_DIR, f'skew_corr_{skew_name}.csv')
        df_skew.to_csv(skew_csv, index=False)
        print(f"  {skew_name}: {skew_csv}")

    # Create difference analysis (UMM vs None as baseline)
    skew_names = list(SKEW_MOM_CORR.keys())
    baseline_name = 'None'  # Classical 1D momentum as reference

    if baseline_name in skew_names:
        df_baseline = df_all[df_all['skew_corr'] == baseline_name].sort_values(['ws', 'yaw']).reset_index(drop=True)

        for skew_name in skew_names:
            if skew_name == baseline_name:
                continue

            df_compare = df_all[df_all['skew_corr'] == skew_name].sort_values(['ws', 'yaw']).reset_index(drop=True)

            diff_data = []
            for col in OUTPUT_COLS:
                mean_col = f'{col}_mean'
                if mean_col in df_baseline.columns and mean_col in df_compare.columns:
                    diff = df_compare[mean_col] - df_baseline[mean_col]
                    pct_diff = 100 * diff / df_baseline[mean_col].abs().replace(0, np.nan)

                    for idx in range(len(df_baseline)):
                        diff_data.append({
                            'yaw': df_baseline.loc[idx, 'yaw'],
                            'ws': df_baseline.loc[idx, 'ws'],
                            'metric': col,
                            f'{baseline_name}_value': df_baseline.loc[idx, mean_col],
                            f'{skew_name}_value': df_compare.loc[idx, mean_col],
                            'difference': diff.iloc[idx],
                            'pct_difference': pct_diff.iloc[idx],
                        })

            df_diff = pd.DataFrame(diff_data)
            diff_csv = os.path.join(WORK_DIR, f'skew_corr_diff_{skew_name}_vs_{baseline_name}.csv')
            df_diff.to_csv(diff_csv, index=False)
            print(f"  Differences ({skew_name} vs {baseline_name}): {diff_csv}")

        # Print summary statistics
        print(f"\n{'='*80}")
        print(f"Difference Summary vs {baseline_name} (Classical 1D)")
        print(f"{'='*80}")
        for skew_name in skew_names:
            if skew_name == baseline_name:
                continue
            print(f"\n  {skew_name}:")
            diff_csv = os.path.join(WORK_DIR, f'skew_corr_diff_{skew_name}_vs_{baseline_name}.csv')
            df_diff = pd.read_csv(diff_csv)
            for col in ['RtAeroCp', 'RtAeroCt', 'RtAeroFxh']:
                metric_data = df_diff[df_diff['metric'] == col]
                if len(metric_data) > 0:
                    mean_pct = metric_data['pct_difference'].mean()
                    max_pct = metric_data['pct_difference'].abs().max()
                    print(f"    {col:15s}: mean diff = {mean_pct:+6.2f}%, max diff = {max_pct:6.2f}%")

    print(f"\n{'='*80}")
    print("COMPARISON COMPLETE")
    print(f"{'='*80}")
    print(f"\nTotal simulations: {len(all_results)}")
    print(f"Test matrix: {len(WIND_SPEEDS)} ws × {len(SKEW_MOM_CORR)} skew_corr × {len(YAW_ANGLES)} yaw")
    print(f"Results saved in: {WORK_DIR}")


if __name__ == '__main__':
    main()
