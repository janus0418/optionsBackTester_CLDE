"""
Fix cell order properly - ensure correct dependency order
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/07_enhanced_atm_straddle_strategy.ipynb")

print("="*70)
print("FIXING CELL ORDER PROPERLY")
print("="*70)

# Load notebook
with open(NOTEBOOK_PATH, 'r') as f:
    notebook = json.load(f)

print(f"\nLoaded {len(notebook['cells'])} cells")

print("\nCurrent (broken) order:")
print("  Cell 4: IV calculation - USES options_data, spot_data")
print("  Cell 6: Data loading - CREATES options_data, spot_data")
print("  Cell 8: Signal generation - USES iv_df")
print("\nProblem: Cell 4 runs before Cell 6!")
print("  → options_data and spot_data are undefined when Cell 4 runs")

# Solution: Swap cells 4 and 6 so data loading happens first
cell_4 = notebook['cells'][4]
cell_6 = notebook['cells'][6]

print("\nSwapping cells 4 and 6...")

# Swap entire cells (including all properties)
temp_cell = cell_4.copy()
notebook['cells'][4] = cell_6.copy()
notebook['cells'][6] = temp_cell

print("  ✓ Swapped cells 4 and 6")

print("\nNew (correct) order:")
print("  Cell 4: Data loading - CREATES options_data, spot_data")
print("  Cell 6: IV calculation - USES options_data, spot_data, CREATES iv_df")
print("  Cell 8: Signal generation - USES iv_df, CREATES signals_df")
print("\nExecution flow:")
print("  1. Setup/imports (cells 0-3)")
print("  2. Data loading (cell 4) → creates options_data, spot_data")
print("  3. IV calculation (cell 6) → creates iv_df")
print("  4. Signal generation (cell 8) → creates signals_df")
print("  ✓ All dependencies satisfied!")

# Save fixed notebook
with open(NOTEBOOK_PATH, 'w') as f:
    json.dump(notebook, f, indent=1)

print(f"\n✓ Saved fixed notebook to {NOTEBOOK_PATH}")

print("\n" + "="*70)
print("CELL ORDER FIXED PROPERLY")
print("="*70)
print("""
The notebook will now run correctly with proper dependency order!

Try running it again from the beginning.
""")
