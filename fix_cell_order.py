"""
Fix cell order issue - swap cells 4 and 8 so iv_df is defined before it's used
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/07_enhanced_atm_straddle_strategy.ipynb")

print("="*70)
print("FIXING CELL ORDER IN NOTEBOOK 07")
print("="*70)

# Load notebook
with open(NOTEBOOK_PATH, 'r') as f:
    notebook = json.load(f)

print(f"\nLoaded {len(notebook['cells'])} cells")

# The issue: Cell 4 uses iv_df, but Cell 8 defines it
# Solution: Swap the contents of cells 4 and 8

print("\nCurrent situation:")
print("  Cell 4: Signal generation (USES iv_df)")
print("  Cell 8: IV calculation (DEFINES iv_df)")
print("\nProblem: Cell 4 runs before Cell 8, so iv_df is undefined!")

print("\nFixing: Swapping cell contents...")

# Get the cells
cell_4 = notebook['cells'][4]
cell_8 = notebook['cells'][8]

# Verify we have the right cells
cell_4_source = ''.join(cell_4['source'])
cell_8_source = ''.join(cell_8['source'])

assert 'generate_multi_signal_entries' in cell_4_source or 'entry_signal' in cell_4_source, "Cell 4 doesn't look like signal generation"
assert 'calculate_enhanced_iv_metrics' in cell_8_source or 'iv_df =' in cell_8_source, "Cell 8 doesn't look like IV calculation"

# Swap the contents
temp_source = cell_4['source']
cell_4['source'] = cell_8['source']
cell_8['source'] = temp_source

# Also swap outputs to keep them clean
temp_outputs = cell_4.get('outputs', [])
cell_4['outputs'] = cell_8.get('outputs', [])
cell_8['outputs'] = temp_outputs

print("  ✓ Swapped cell 4 and cell 8 contents")

print("\nNew situation:")
print("  Cell 4: IV calculation (DEFINES iv_df)")
print("  Cell 8: Signal generation (USES iv_df)")
print("  → Cell 4 runs first, creating iv_df")
print("  → Cell 8 can now use iv_df successfully")

# Save fixed notebook
with open(NOTEBOOK_PATH, 'w') as f:
    json.dump(notebook, f, indent=1)

print(f"\n✓ Saved fixed notebook to {NOTEBOOK_PATH}")

print("\n" + "="*70)
print("CELL ORDER FIXED")
print("="*70)
print("""
The notebook will now run correctly:
1. Configuration (cells 1-3)
2. IV Calculation (cell 4) → creates iv_df
3. Data loading (cells 5-7)
4. Signal Generation (cell 8) → uses iv_df
5. Rest of notebook...

Try running the notebook now!
""")
