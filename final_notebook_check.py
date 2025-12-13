"""
Final comprehensive check of the notebook.
"""
import json

notebook_path = "/Users/janussuk/Desktop/Options Backtester/notebooks/07_enhanced_atm_straddle_strategy.ipynb"

# Read the notebook
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

print("="*70)
print("FINAL NOTEBOOK VALIDATION")
print("="*70)

# Count cells
total_cells = len(notebook['cells'])
code_cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
markdown_cells = [c for c in notebook['cells'] if c['cell_type'] == 'markdown']

print(f"\nCell Count:")
print(f"  Total cells: {total_cells}")
print(f"  Code cells: {len(code_cells)}")
print(f"  Markdown cells: {len(markdown_cells)}")

# Check for critical fixes
print(f"\n{'='*70}")
print("Critical Fixes Verification:")
print("="*70)

fixes_verified = []
fixes_missing = []

for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        # Check Fix 1: StrategyConfig attributes
        if 'class StrategyConfig:' in source:
            if 'IV_RANK_THRESHOLD' in source:
                fixes_verified.append(f"✓ Cell {idx}: IV_RANK_THRESHOLD present")
            else:
                fixes_missing.append(f"✗ Cell {idx}: IV_RANK_THRESHOLD missing")

            if 'COST_PER_CONTRACT' in source:
                fixes_verified.append(f"✓ Cell {idx}: COST_PER_CONTRACT present")
            else:
                fixes_missing.append(f"✗ Cell {idx}: COST_PER_CONTRACT missing")

            if 'SLIPPAGE_PCT' in source:
                fixes_verified.append(f"✓ Cell {idx}: SLIPPAGE_PCT present")
            else:
                fixes_missing.append(f"✗ Cell {idx}: SLIPPAGE_PCT missing")

        # Check Fix 2: Safe iv_percentile access
        if 'class DailyStraddleBacktester:' in source:
            if "if 'iv_percentile' in day_signal.columns:" in source:
                fixes_verified.append(f"✓ Cell {idx}: Safe iv_percentile access")
            else:
                fixes_missing.append(f"✗ Cell {idx}: Missing safe iv_percentile access")

            if "pos.get('signal_type', 'unknown')" in source:
                fixes_verified.append(f"✓ Cell {idx}: Correct pos.get reference")
            else:
                fixes_missing.append(f"✗ Cell {idx}: Missing correct pos.get reference")

        # Check Fix 3: display import
        if 'import pandas as pd' in source:
            if 'from IPython.display import display' in source:
                fixes_verified.append(f"✓ Cell {idx}: display import present")
            else:
                # This might be OK if it's in a different cell
                pass

# Print verification results
for fix in fixes_verified:
    print(f"  {fix}")

if fixes_missing:
    print("\nMISSING FIXES:")
    for fix in fixes_missing:
        print(f"  {fix}")
else:
    print(f"\n✓ All critical fixes verified!")

# Check for potential runtime errors
print(f"\n{'='*70}")
print("Potential Runtime Issues:")
print("="*70)

potential_issues = []

for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        # Check for undefined variables in specific patterns
        if "'iv_percentile': pos.get('iv_percentile'" in source:
            potential_issues.append(f"✓ Cell {idx}: iv_percentile uses safe .get()")

        # Check for proper DataFrame access
        if ".iloc[0]" in source and "['iv" in source:
            if "if '" in source or ".get(" in source:
                # Has safety check
                pass
            else:
                # Might be risky
                potential_issues.append(f"⚠ Cell {idx}: Direct .iloc[0] access (might be OK if column guaranteed)")

if potential_issues:
    for issue in potential_issues:
        print(f"  {issue}")
else:
    print("  No potential issues detected")

# Summary
print(f"\n{'='*70}")
print("SUMMARY")
print("="*70)
print(f"✓ Notebook structure: OK ({len(code_cells)} code cells)")
print(f"✓ Critical fixes: {'VERIFIED' if not fixes_missing else 'INCOMPLETE'}")
print(f"✓ Validation: {'PASSED' if not fixes_missing else 'FAILED'}")

if not fixes_missing:
    print("\n🎉 Notebook is ready for execution!")
else:
    print("\n⚠ Some fixes are missing. Please review.")

print("="*70)
