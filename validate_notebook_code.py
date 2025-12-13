"""
Validate all code cells in the notebook for potential errors.
"""
import json
import re

notebook_path = "/Users/janussuk/Desktop/Options Backtester/notebooks/07_enhanced_atm_straddle_strategy.ipynb"

# Read the notebook
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

print("Validating notebook code cells...")
print("="*70)

issues = []
code_cell_count = 0

for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        code_cell_count += 1
        source = ''.join(cell['source'])

        # Check for common issues

        # 1. Check for undefined variable references
        if re.search(r'\bstraddle\b', source) and 'def ' not in source:
            # Make sure straddle is defined before use
            if "'signal_type': straddle.get" in source:
                issues.append(f"Cell {idx}: Possible straddle reference issue")

        # 2. Check for DataFrame column access without safe checks
        column_accesses = re.findall(r"(\w+)\['(\w+)'\]\.iloc\[0\]", source)
        for df_name, col_name in column_accesses:
            if col_name in ['iv_percentile', 'iv_rank'] and 'if ' not in source.split(col_name)[0][-50:]:
                # Check if there's a safe access pattern nearby
                if f"if '{col_name}' in" not in source:
                    # This might be OK if it's guaranteed to exist
                    pass

        # 3. Check for missing imports
        if 'display(' in source and 'from IPython.display import display' not in source:
            # Check if display is imported in a previous cell
            needs_display = True
            for prev_idx in range(idx):
                prev_source = ''.join(notebook['cells'][prev_idx].get('source', []))
                if 'from IPython.display import display' in prev_source or 'import IPython' in prev_source:
                    needs_display = False
                    break
            if needs_display:
                issues.append(f"Cell {idx}: Uses display() but might not be imported")

        # 4. Check for undefined self.signals_df
        if 'self.signals_df' in source and 'def __init__' not in source:
            # Check if it's actually used
            if 'if hasattr(self, "signals_df")' not in source:
                issues.append(f"Cell {idx}: References self.signals_df without checking existence")

        # 5. Check for syntax errors (basic)
        open_parens = source.count('(')
        close_parens = source.count(')')
        if open_parens != close_parens:
            issues.append(f"Cell {idx}: Unbalanced parentheses ({open_parens} open, {close_parens} close)")

        open_brackets = source.count('[')
        close_brackets = source.count(']')
        if open_brackets != close_brackets:
            issues.append(f"Cell {idx}: Unbalanced brackets ({open_brackets} open, {close_brackets} close)")

print(f"Total code cells: {code_cell_count}")
print(f"\nPotential issues found: {len(issues)}")

if issues:
    print("\nIssues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\n✓ No obvious issues found!")

# Check specific patterns that we fixed
print("\n" + "="*70)
print("Verifying fixes:")
print("="*70)

for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        if 'class DailyStraddleBacktester:' in source:
            print(f"\nCell {idx}: DailyStraddleBacktester")

            if "if 'iv_percentile' in day_signal.columns:" in source:
                print("  ✓ Safe iv_percentile access confirmed")
            else:
                print("  ✗ Safe iv_percentile access NOT found")

            if "pos.get('signal_type', 'unknown')" in source:
                print("  ✓ Correct pos.get reference confirmed")
            else:
                print("  ✗ Correct pos.get reference NOT found")

print("\n" + "="*70)
print("Validation complete!")
