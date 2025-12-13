"""
Comprehensive check of notebook for all potential issues.
"""
import json
import re

notebook_path = "/Users/janussuk/Desktop/Options Backtester/notebooks/07_enhanced_atm_straddle_strategy.ipynb"

# Read the notebook
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

print("="*70)
print("COMPREHENSIVE NOTEBOOK CHECK")
print("="*70)

# Check 1: Verify all code cells are present
code_cells = [i for i, cell in enumerate(notebook['cells']) if cell['cell_type'] == 'code']
print(f"\n1. Total code cells: {len(code_cells)}")

# Check 2: Look for problematic patterns
print("\n2. Checking for problematic patterns...")
issues = []

for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        # Check for common issues
        if 'undefined' in source.lower() and '#' not in source[:source.lower().index('undefined')]:
            issues.append(f"Cell {idx}: Contains 'undefined'")

        # Check for incomplete code
        if source.strip().endswith('\\'):
            issues.append(f"Cell {idx}: Ends with backslash (incomplete)")

        # Check for unmatched parentheses/brackets
        if source.count('(') != source.count(')'):
            issues.append(f"Cell {idx}: Unmatched parentheses")
        if source.count('[') != source.count(']'):
            issues.append(f"Cell {idx}: Unmatched brackets")
        if source.count('{') != source.count('}'):
            issues.append(f"Cell {idx}: Unmatched braces")

if issues:
    for issue in issues:
        print(f"  ⚠ {issue}")
else:
    print("  ✓ No obvious code issues found")

# Check 3: Verify imports
print("\n3. Checking imports...")
imports_found = False
for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'import pandas' in source or 'import numpy' in source:
            print(f"  ✓ Core imports found in cell {idx}")
            imports_found = True
            break

if not imports_found:
    print("  ⚠ Core imports not found!")

# Check 4: Verify StrategyConfig
print("\n4. Checking StrategyConfig...")
config_found = False
for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'class StrategyConfig:' in source:
            print(f"  ✓ StrategyConfig class found in cell {idx}")

            # Check for all required attributes
            required = ['IV_RANK_THRESHOLD', 'COST_PER_CONTRACT', 'SLIPPAGE_PCT',
                       'DB_PATH', 'TICKER', 'INITIAL_CAPITAL']
            missing = [attr for attr in required if attr not in source]

            if missing:
                print(f"  ⚠ Missing attributes: {missing}")
            else:
                print(f"  ✓ All required attributes present")

            config_found = True
            break

if not config_found:
    print("  ⚠ StrategyConfig class not found!")

# Check 5: Look for backtester class
print("\n5. Checking for backtester class...")
backtester_found = False
for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'class DailyStraddleBacktester' in source or 'class Backtester' in source:
            print(f"  ✓ Backtester class found in cell {idx}")
            backtester_found = True
            break

if not backtester_found:
    print("  ⚠ Backtester class not found")

# Check 6: Verify function imports
print("\n6. Checking function imports from enhanced_straddle_functions...")
funcs_to_check = [
    'calculate_enhanced_iv_metrics',
    'generate_multi_signal_entries',
    'get_signal_summary'
]

for func in funcs_to_check:
    found = False
    for idx, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if func in source and 'from enhanced_straddle_functions' in source:
                print(f"  ✓ {func} imported")
                found = True
                break
    if not found:
        print(f"  ⚠ {func} not imported")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Total cells: {len(notebook['cells'])}")
print(f"Code cells: {len(code_cells)}")
print(f"Issues found: {len(issues)}")

if len(issues) == 0:
    print("\n✓ Notebook appears to be in good shape!")
else:
    print("\n⚠ Please review the issues above")
