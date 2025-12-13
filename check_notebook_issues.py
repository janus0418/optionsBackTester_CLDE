"""
Script to check for common issues in the notebook.
"""
import json
import re

notebook_path = "/Users/janussuk/Desktop/Options Backtester/notebooks/07_enhanced_atm_straddle_strategy.ipynb"

# Read the notebook
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

print("Checking notebook for potential issues...\n")

# Track defined variables
defined_vars = set()
imported_modules = set()
issues_found = []

for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        # Track imports
        import_matches = re.findall(r'^(?:from|import)\s+(\w+)', source, re.MULTILINE)
        imported_modules.update(import_matches)

        # Track class definitions
        class_matches = re.findall(r'^class\s+(\w+)', source, re.MULTILINE)
        defined_vars.update(class_matches)

        # Track variable assignments
        var_matches = re.findall(r'^(\w+)\s*=', source, re.MULTILINE)
        defined_vars.update(var_matches)

        # Check for undefined variables (simple heuristic)
        # Look for variables used but not defined
        used_vars = re.findall(r'\b([a-z_][a-z0-9_]*)\s*[=\(]', source)

        # Check specific issues
        if 'AttributeError' in source:
            issues_found.append(f"Cell {idx}: Contains AttributeError in output")

        if 'NameError' in source:
            issues_found.append(f"Cell {idx}: Contains NameError in output")

        if 'undefined' in source.lower():
            issues_found.append(f"Cell {idx}: Contains 'undefined' text")

print(f"Imported modules: {sorted(imported_modules)}")
print(f"\nDefined variables/classes: {sorted(list(defined_vars)[:20])}...")
print(f"\nTotal cells: {len(notebook['cells'])}")

# Check for cells with errors in outputs
cells_with_errors = 0
for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code' and 'outputs' in cell:
        for output in cell['outputs']:
            if output.get('output_type') == 'error':
                cells_with_errors += 1
                ename = output.get('ename', 'Unknown')
                evalue = output.get('evalue', 'Unknown')
                issues_found.append(f"Cell {idx}: {ename}: {evalue}")

print(f"\nCells with error outputs: {cells_with_errors}")

if issues_found:
    print("\n" + "="*70)
    print("ISSUES FOUND:")
    print("="*70)
    for issue in issues_found:
        print(f"  - {issue}")
else:
    print("\n✓ No obvious issues found in cell outputs")

# Check for common undefined variables
print("\n" + "="*70)
print("Checking for commonly undefined variables...")
print("="*70)

common_vars_to_check = [
    'pd', 'np', 'plt', 'DoltHubAdapter',
    'config', 'options_data', 'spot_data',
    'iv_metrics', 'signals_df'
]

for var in common_vars_to_check:
    if var in defined_vars or var in imported_modules:
        print(f"  ✓ {var} is defined")
    else:
        print(f"  ✗ {var} might not be defined")
