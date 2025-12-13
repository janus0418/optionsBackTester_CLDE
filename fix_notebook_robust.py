"""
Robust fix for notebook errors using line-by-line replacement.
"""
import json

notebook_path = "/Users/janussuk/Desktop/Options Backtester/notebooks/07_enhanced_atm_straddle_strategy.ipynb"

# Read the notebook
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

print("Applying robust fixes...")

# Find and fix the DailyStraddleBacktester class
for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source_lines = cell['source']
        source_str = ''.join(source_lines)

        if 'class DailyStraddleBacktester:' in source_str:
            print(f"\nFound DailyStraddleBacktester in cell {idx}")

            modified = False
            new_lines = []
            i = 0

            while i < len(source_lines):
                line = source_lines[i]

                # Fix 1: Add safe access for iv_percentile
                if "straddle['iv_rank'] = day_signal['iv_rank'].iloc[0]" in line:
                    print("  - Fixing iv_percentile access")
                    new_lines.append(line)
                    # Check if next line is the iv_percentile line
                    if i + 1 < len(source_lines) and "straddle['iv_percentile'] = day_signal['iv_percentile'].iloc[0]" in source_lines[i + 1]:
                        # Replace the next line with safe access
                        new_lines.append("                    if 'iv_percentile' in day_signal.columns:\n")
                        new_lines.append("                        straddle['iv_percentile'] = day_signal['iv_percentile'].iloc[0]\n")
                        new_lines.append("                    else:\n")
                        new_lines.append("                        straddle['iv_percentile'] = np.nan\n")
                        i += 2  # Skip the original iv_percentile line
                        modified = True
                        continue

                # Fix 2: Change straddle.get to pos.get in trade dict
                elif "'signal_type': straddle.get('signal_type', 'unknown')" in line:
                    print("  - Fixing straddle reference to pos")
                    new_lines.append(line.replace("straddle.get('signal_type', 'unknown')", "pos.get('signal_type', 'unknown')"))
                    modified = True
                    i += 1
                    continue

                new_lines.append(line)
                i += 1

            if modified:
                notebook['cells'][idx]['source'] = new_lines
                print(f"  ✓ Applied fixes to cell {idx}")

# Save the updated notebook
with open(notebook_path, 'w') as f:
    json.dump(notebook, f, indent=1)

print("\n✓ All fixes applied successfully")
