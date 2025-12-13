"""
Script to check imports and find potential undefined variable issues.
"""
import json
import re

notebook_path = "/Users/janussuk/Desktop/Options Backtester/notebooks/07_enhanced_atm_straddle_strategy.ipynb"

# Read the notebook
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

print("Checking first few cells for imports and setup...\n")

# Check the first 10 cells
for idx in range(min(10, len(notebook['cells']))):
    cell = notebook['cells'][idx]
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        print(f"Cell {idx}:")
        print("="*70)
        print(source[:500])  # Print first 500 chars
        print("="*70)
        print()

        # Check for specific imports
        if 'import pandas' in source or 'import numpy' in source:
            print("  → Found pandas/numpy imports")
        if 'DoltHubAdapter' in source:
            print("  → Found DoltHubAdapter")
        if 'class' in source:
            print("  → Contains class definition")
        print()
