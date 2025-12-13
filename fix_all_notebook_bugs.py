"""
Fix ALL bugs in Notebook 07 - Add missing StrategyConfig attributes
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/07_enhanced_atm_straddle_strategy.ipynb")

print("="*70)
print("FIXING STRATEGYCONFIG - ADDING MISSING ATTRIBUTES")
print("="*70)

# Load notebook
with open(NOTEBOOK_PATH, 'r') as f:
    notebook = json.load(f)

print(f"\nLoaded {len(notebook['cells'])} cells")

# Find the cell with StrategyConfig class definition
config_cell_idx = None
for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'class StrategyConfig:' in source:
            config_cell_idx = idx
            print(f"\n✓ Found StrategyConfig class at cell {idx}")
            break

if config_cell_idx is None:
    print("ERROR: Could not find StrategyConfig class!")
    exit(1)

# Get the current cell source lines
cell = notebook['cells'][config_cell_idx]
source_lines = cell['source']

# Check if attributes already exist
source_text = ''.join(source_lines)
if 'IV_RANK_THRESHOLD' in source_text and 'COST_PER_CONTRACT' in source_text:
    print("\n✓ All required attributes already exist. No changes needed.")
else:
    # Find where to insert (after SIGNAL_TYPES line)
    insert_idx = None
    for i, line in enumerate(source_lines):
        if 'SIGNAL_TYPES' in line and '[' in line:
            insert_idx = i + 1
            print(f"\n✓ Will insert after line {i}: {line.strip()}")
            break

    if insert_idx is None:
        print("ERROR: Could not find SIGNAL_TYPES line!")
        exit(1)

    # Define the new attributes to add
    new_attributes = [
        "\n",
        "    # IV Rank Configuration\n",
        "    IV_RANK_THRESHOLD = 50  # Entry when IV Rank > 50%\n",
        "    \n",
        "    # Transaction Costs\n",
        "    COST_PER_CONTRACT = 0.65  # Commission per contract\n",
        "    SLIPPAGE_PCT = 0.005      # 0.5% slippage\n"
    ]

    # Insert the new attributes
    source_lines[insert_idx:insert_idx] = new_attributes

    # Update the cell
    notebook['cells'][config_cell_idx]['source'] = source_lines

    print("\n✓ Added missing attributes to StrategyConfig:")
    print("    - IV_RANK_THRESHOLD = 50")
    print("    - COST_PER_CONTRACT = 0.65")
    print("    - SLIPPAGE_PCT = 0.005")

# Clear error outputs from cells with AttributeError
errors_cleared = 0
for cell in notebook['cells']:
    if cell['cell_type'] == 'code' and 'outputs' in cell:
        for output in cell.get('outputs', []):
            if output.get('output_type') == 'error':
                evalue = output.get('evalue', '')
                if any(attr in str(evalue) for attr in ['IV_RANK_THRESHOLD', 'COST_PER_CONTRACT', 'SLIPPAGE_PCT']):
                    cell['outputs'] = []
                    errors_cleared += 1
                    break

if errors_cleared > 0:
    print(f"\n✓ Cleared {errors_cleared} error output(s)")

# Save fixed notebook
print(f"\n{'='*70}")
print("Saving fixed notebook...")
with open(NOTEBOOK_PATH, 'w') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"✓ Saved to {NOTEBOOK_PATH}")
print("="*70)

print("""
✅ StrategyConfig class has been fixed!

Added attributes:
  • IV_RANK_THRESHOLD = 50  (Entry when IV Rank > 50%)
  • COST_PER_CONTRACT = 0.65  (Commission per contract)
  • SLIPPAGE_PCT = 0.005  (0.5% slippage)

The notebook should now run without AttributeError!
""")

