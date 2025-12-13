"""
Script to clear all outputs from the notebook to remove old error messages.
"""
import json

notebook_path = "/Users/janussuk/Desktop/Options Backtester/notebooks/07_enhanced_atm_straddle_strategy.ipynb"

# Read the notebook
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

# Clear outputs from all code cells
cleared_count = 0
for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        if 'outputs' in cell and len(cell['outputs']) > 0:
            cleared_count += 1
        cell['outputs'] = []
        cell['execution_count'] = None

# Save the cleaned notebook
with open(notebook_path, 'w') as f:
    json.dump(notebook, f, indent=1)

print(f"✓ Cleared outputs from {cleared_count} cells")
print(f"✓ Notebook ready for fresh execution")
