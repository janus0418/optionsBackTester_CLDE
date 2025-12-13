"""
Script to fix missing attributes in the notebook's StrategyConfig class.
"""
import json
import re

notebook_path = "/Users/janussuk/Desktop/Options Backtester/notebooks/07_enhanced_atm_straddle_strategy.ipynb"

# Read the notebook
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

# Find all config.ATTRIBUTE_NAME references in the notebook
config_attributes = set()
for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        # Find all config.SOMETHING patterns
        matches = re.findall(r'config\.([A-Z_]+)', source)
        config_attributes.update(matches)

print("Found config attributes being used:")
for attr in sorted(config_attributes):
    print(f"  - {attr}")

# Find the cell with StrategyConfig class definition
config_cell_idx = None
for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'class StrategyConfig:' in source:
            config_cell_idx = idx
            print(f"\nFound StrategyConfig in cell {idx}")
            break

if config_cell_idx is not None:
    # Get the current StrategyConfig cell content
    current_source = ''.join(notebook['cells'][config_cell_idx]['source'])

    # Check which attributes are missing
    missing_attrs = []
    for attr in config_attributes:
        if f'{attr} =' not in current_source:
            missing_attrs.append(attr)

    print(f"\nMissing attributes: {missing_attrs}")

    # Add missing attributes to StrategyConfig
    if missing_attrs:
        # Find where to insert (after SIGNAL_TYPES or before the end of class)
        lines = current_source.split('\n')

        # Find the insertion point (before config = StrategyConfig())
        insert_idx = None
        for i, line in enumerate(lines):
            if 'SIGNAL_TYPES' in line:
                insert_idx = i + 1
                break

        if insert_idx is None:
            # Find the last attribute line
            for i in range(len(lines) - 1, -1, -1):
                if '=' in lines[i] and not lines[i].strip().startswith('#'):
                    insert_idx = i + 1
                    break

        # Add missing attributes with appropriate defaults
        additions = []
        if 'IV_RANK_THRESHOLD' in missing_attrs:
            additions.append("    IV_RANK_THRESHOLD = 50  # Entry signal: IV Rank > 50%")
        if 'COST_PER_CONTRACT' in missing_attrs:
            additions.append("    COST_PER_CONTRACT = 1.00  # $1 per contract transaction cost")
        if 'SLIPPAGE_PCT' in missing_attrs:
            additions.append("    SLIPPAGE_PCT = 0.005  # 0.5% slippage")

        if insert_idx and additions:
            # Insert a blank line first, then additions
            lines.insert(insert_idx, "")
            for i, addition in enumerate(additions):
                lines.insert(insert_idx + 1 + i, addition)

            # Update the notebook cell
            notebook['cells'][config_cell_idx]['source'] = [line + '\n' for line in lines[:-1]] + [lines[-1]]

            print(f"\nAdded {len(additions)} missing attributes")

            # Save the updated notebook
            with open(notebook_path, 'w') as f:
                json.dump(notebook, f, indent=1)

            print(f"✓ Notebook updated successfully")
        else:
            print("Could not find insertion point or no additions needed")
else:
    print("ERROR: Could not find StrategyConfig class definition")
