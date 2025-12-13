"""
Script to verify the StrategyConfig class has all necessary attributes.
"""
import json

notebook_path = "/Users/janussuk/Desktop/Options Backtester/notebooks/07_enhanced_atm_straddle_strategy.ipynb"

# Read the notebook
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

# Find the StrategyConfig cell
for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'class StrategyConfig:' in source:
            print(f"Found StrategyConfig in cell {idx}")
            print("="*70)
            print(source)
            print("="*70)

            # Check for required attributes
            required_attrs = [
                'IV_RANK_THRESHOLD',
                'COST_PER_CONTRACT',
                'SLIPPAGE_PCT',
                'DB_PATH',
                'TICKER',
                'START_DATE',
                'END_DATE',
                'TARGET_DTE_MIN',
                'TARGET_DTE_MAX',
                'TARGET_DTE_IDEAL',
                'PROFIT_TARGET_PCT',
                'STOP_LOSS_PCT',
                'TIME_STOP_DTE',
                'INITIAL_CAPITAL',
                'SIGNAL_TYPES'
            ]

            print("\nAttribute Check:")
            for attr in required_attrs:
                if f'{attr} =' in source or f'{attr}=' in source:
                    print(f"  ✓ {attr}")
                else:
                    print(f"  ✗ {attr} MISSING")
            break
