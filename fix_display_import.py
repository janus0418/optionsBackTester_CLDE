"""
Add display import if needed.
"""
import json

notebook_path = "/Users/janussuk/Desktop/Options Backtester/notebooks/07_enhanced_atm_straddle_strategy.ipynb"

# Read the notebook
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

print("Checking for display() import...")

# Check if display is imported in any cell
display_imported = False
import_cell_idx = None

for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'from IPython.display import display' in source:
            display_imported = True
            import_cell_idx = idx
            print(f"  ✓ display() already imported in cell {idx}")
            break
        # Check for the imports cell (usually has pandas, numpy, etc.)
        if 'import pandas as pd' in source and 'import numpy as np' in source:
            import_cell_idx = idx

if not display_imported:
    print(f"  - display() not explicitly imported")

    # Check if it's actually used
    uses_display = []
    for idx, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'display(' in source:
                uses_display.append(idx)

    if uses_display:
        print(f"  - display() used in cells: {uses_display}")

        # In Jupyter notebooks, display() is available by default from IPython
        # But for best practice, we can add it to the imports cell
        if import_cell_idx is not None:
            print(f"  - Adding display import to cell {import_cell_idx}")

            # Get the imports cell
            imports_cell = notebook['cells'][import_cell_idx]
            source_lines = imports_cell['source']

            # Find where to insert (after other imports, before settings)
            insert_idx = 0
            for i, line in enumerate(source_lines):
                if 'import warnings' in line:
                    insert_idx = i + 1
                    break
                elif line.strip().startswith('#') or line.strip() == '':
                    continue
                elif 'import' in line:
                    insert_idx = i + 1

            # Insert the display import
            source_lines.insert(insert_idx, 'from IPython.display import display\n')

            notebook['cells'][import_cell_idx]['source'] = source_lines

            # Save the updated notebook
            with open(notebook_path, 'w') as f:
                json.dump(notebook, f, indent=1)

            print("  ✓ Added display import")
        else:
            print("  ⚠ Could not find appropriate cell for import")
    else:
        print("  - display() not actually used (false positive)")
else:
    print("  ✓ No action needed")
