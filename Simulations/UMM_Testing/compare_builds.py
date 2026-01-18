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

# ============================================================================
# CONFIGURATION
# ============================================================================

# Builds to compare
BUILDS = {
    'baseline': '/Users/benhealy/OpenFAST/build-testing/glue-codes/openfast/openfast',
    'UMM': '/Users/benhealy/OpenFAST/build-UMM/glue-codes/openfast/openfast',
}

# Test matrix
# YAW_ANGLES = [-30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 30]  # degrees
# WIND_SPEEDS = [4, 6, 8, 10, 12, 14, 16, 18]  # m/s

# Quick test (uncomment to use smaller test matrix)
YAW_ANGLES = [30]
WIND_SPEEDS = [8]

# Paths
WORK_DIR = '/Users/benhealy/OpenFAST/Simulations/UMM_Testing/results_comp_1x1_out_params_testing/'
FST_FILE = '5MW_Land_BD_DLL_WTurb_Skewed_Loads.fst'
OUTPUT_BASE = os.path.join(WORK_DIR, '5MW_Land_BD_DLL_WTurb_Skewed_Loads')


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


def setup_aerodyn(aerodyn_path, wind_speed, build_name):
    """Configure AeroDyn for yaw simulations"""
    modify_parameter(aerodyn_path, 'UA_Mod', '0')
    modify_parameter(aerodyn_path, 'AIDrag', 'True')
    modify_parameter(aerodyn_path, 'MaxIter', '300')
    modify_parameter(aerodyn_path, 'Skew_Mod', '1')
    modify_parameter(aerodyn_path, 'SkewRedistr_Mod', '1')
    
    
    if build_name == 'UMM':
        modify_parameter(aerodyn_path, 'SkewMomCorr', '2')
    else:
        modify_parameter(aerodyn_path, 'SkewMomCorr', 'True')



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
# MAIN COMPARISON LOOP
# ============================================================================

def main():
    print("="*80)
    print("OpenFAST Build Comparison")
    print("="*80)
    print(f"\nBuilds to compare:")
    for name, path in BUILDS.items():
        print(f"  {name}: {path}")
    print(f"\nTest matrix: {len(YAW_ANGLES)} yaw angles × {len(WIND_SPEEDS)} wind speeds")
    print(f"Total simulations per build: {len(YAW_ANGLES) * len(WIND_SPEEDS)}")

    # Backup original files
    print("\nBacking up input files...")
    backups = {}
    for key, path in INPUT_FILES.items():
        backup_path = path + '.backup_compare'
        shutil.copy(path, backup_path)
        backups[key] = backup_path

    all_results = []

    # Loop over builds
    for build_name, exe_path in BUILDS.items():
        print(f"\n{'='*80}")
        print(f"Running build: {build_name.upper()}")
        print(f"{'='*80}")

        build_results = []

        for ws in WIND_SPEEDS:
            print(f"\n  Wind Speed: {ws} m/s")

            # Configure input files for this wind speed
            modify_parameter(INPUT_FILES['inflow'], 'HWindSpeed', f"{ws:.2f}")
            setup_aerodyn(INPUT_FILES['aerodyn'], ws, build_name)
            setup_elastodyn(INPUT_FILES['elastodyn'], ws)
            setup_elastodyn(INPUT_FILES['elastodyn_bd'], ws)

            for yaw in YAW_ANGLES:
                print(f"    Yaw: {yaw:+3d}°...", end=' ', flush=True)

                # Configure yaw maneuver
                setup_servodyn(INPUT_FILES['servodyn'], yaw)
                sim_time = calculate_sim_time(yaw)
                modify_parameter(os.path.join(WORK_DIR, FST_FILE), 'TMax', f"{sim_time:.1f}")

                # Run simulation
                result = run_openfast(FST_FILE, WORK_DIR, exe_path)

                if result.returncode != 0:
                    print(f"FAILED (code {result.returncode})")
                    continue

                # Extract results
                output_file = f"{OUTPUT_BASE}.out"
                ss_values = extract_steady_state(output_file, OUTPUT_COLS)
                ss_values['build'] = build_name
                ss_values['yaw'] = yaw
                ss_values['ws'] = ws
                build_results.append(ss_values)

                # Clean up
                if os.path.exists(output_file):
                    os.remove(output_file)

                print("OK")

        all_results.extend(build_results)
        print(f"\n  Completed {len(build_results)} simulations for {build_name}")

    # Save results
    print(f"\n{'='*80}")
    print("Saving results...")
    print(f"{'='*80}")

    df_all = pd.DataFrame(all_results)

    # Save combined results
    combined_csv = os.path.join(WORK_DIR, 'build_comparison_combined.csv')
    df_all.to_csv(combined_csv, index=False)
    print(f"  Combined: {combined_csv}")

    # Save per-build results
    for build_name in BUILDS.keys():
        df_build = df_all[df_all['build'] == build_name]
        build_csv = os.path.join(WORK_DIR, f'build_comparison_{build_name}.csv')
        df_build.to_csv(build_csv, index=False)
        print(f"  {build_name}: {build_csv}")

    # Create difference analysis
    if len(BUILDS) == 2:
        build_names = list(BUILDS.keys())
        df1 = df_all[df_all['build'] == build_names[0]].sort_values(['ws', 'yaw']).reset_index(drop=True)
        df2 = df_all[df_all['build'] == build_names[1]].sort_values(['ws', 'yaw']).reset_index(drop=True)

        diff_data = []
        for col in OUTPUT_COLS:
            mean_col = f'{col}_mean'
            if mean_col in df1.columns and mean_col in df2.columns:
                diff = df2[mean_col] - df1[mean_col]
                pct_diff = 100 * diff / df1[mean_col].abs()

                for idx in range(len(df1)):
                    diff_data.append({
                        'yaw': df1.loc[idx, 'yaw'],
                        'ws': df1.loc[idx, 'ws'],
                        'metric': col,
                        f'{build_names[0]}_value': df1.loc[idx, mean_col],
                        f'{build_names[1]}_value': df2.loc[idx, mean_col],
                        'difference': diff.iloc[idx],
                        'pct_difference': pct_diff.iloc[idx],
                    })

        df_diff = pd.DataFrame(diff_data)
        diff_csv = os.path.join(WORK_DIR, f'build_comparison_diff_{build_names[1]}_vs_{build_names[0]}.csv')
        df_diff.to_csv(diff_csv, index=False)
        print(f"  Differences: {diff_csv}")

        # Print summary statistics
        print(f"\n{'='*80}")
        print(f"Difference Summary: {build_names[1]} vs {build_names[0]}")
        print(f"{'='*80}")
        for col in OUTPUT_COLS:
            metric_data = df_diff[df_diff['metric'] == col]
            if len(metric_data) > 0:
                mean_pct = metric_data['pct_difference'].mean()
                max_pct = metric_data['pct_difference'].abs().max()
                print(f"  {col:15s}: mean diff = {mean_pct:+6.2f}%, max diff = {max_pct:6.2f}%")

    # Restore original files
    print(f"\n{'='*80}")
    print("Restoring original input files...")
    print(f"{'='*80}")
    for key, backup_path in backups.items():
        shutil.copy(backup_path, INPUT_FILES[key])
        os.remove(backup_path)
    print("  Restored")

    print(f"\n{'='*80}")
    print("COMPARISON COMPLETE")
    print(f"{'='*80}")
    print(f"\nTotal simulations: {len(all_results)}")
    print(f"Results saved in: {WORK_DIR}")


if __name__ == '__main__':
    main()
