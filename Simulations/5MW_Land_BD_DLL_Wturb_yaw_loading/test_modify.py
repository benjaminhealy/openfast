#!/usr/bin/env python3
"""
Test script to validate the modify_parameter function fix
"""
import re
import shutil

def modify_parameter(filepath, param_name, new_value):
    """
    Modify a parameter in an OpenFAST input file
    Preserves exact formatting - only replaces the value, nothing else.
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Pattern to match OpenFAST parameter lines:
    # (leading whitespace)(value)(whitespace)(param_name)(rest of line)
    # We need to match the value and replace only that part
    pattern = r'^(\s*)(\S+)(\s+' + re.escape(param_name) + r'\b)'

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
            print(f"✓ Modified {param_name}")
            print(f"  Old: {repr(line)}")
            print(f"  New: {repr(new_line)}")
            break

    if not modified:
        raise ValueError(f"Parameter '{param_name}' not found in {filepath}")

    with open(filepath, 'w') as f:
        f.writelines(lines)

# Test 1: Modify NacYaw in ElastoDyn file
print("Test 1: Modifying NacYaw to 15.0")
shutil.copy('NRELOffshrBsline5MW_Onshore_ElastoDyn_Skewed_Loads.dat.backup',
            'test_elastodyn.dat')
modify_parameter('test_elastodyn.dat', 'NacYaw', '15.0')

# Verify the change
with open('test_elastodyn.dat', 'r') as f:
    lines = f.readlines()
    print(f"\nLine 34 after modification: {repr(lines[33])}")

# Test 2: Modify RotSpeed
print("\n" + "="*60)
print("Test 2: Modifying RotSpeed to 12.1")
modify_parameter('test_elastodyn.dat', 'RotSpeed', '12.1')

with open('test_elastodyn.dat', 'r') as f:
    lines = f.readlines()
    print(f"\nLine 33 after modification: {repr(lines[32])}")

# Test 3: Modify UA_Mod in AeroDyn file
print("\n" + "="*60)
print("Test 3: Modifying UA_Mod to 0")
shutil.copy('NRELOffshrBsline5MW_Onshore_AeroDyn_Skewed_Loads.dat.backup',
            'test_aerodyn.dat')
modify_parameter('test_aerodyn.dat', 'UA_Mod', '0')

# Verify the change
with open('test_aerodyn.dat', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[45:55], start=46):
        if 'UA_Mod' in line:
            print(f"\nLine {i} after modification: {repr(line)}")
            break

print("\n" + "="*60)
print("All tests completed successfully!")
