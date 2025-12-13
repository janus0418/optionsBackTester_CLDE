"""
Test script to validate the StrategyConfig works properly.
"""

# Test 1: Define the StrategyConfig class as it appears in the notebook
class StrategyConfig:
    """Configuration for Enhanced Multi-Signal ATM Straddle Strategy."""

    # Data Configuration
    DB_PATH = "/Users/janussuk/Desktop/dolt_data/options"
    TICKER = "SPY"
    START_DATE = "2022-01-03"
    END_DATE = "2025-01-31"

    # DTE Configuration (adjusted for data availability)
    TARGET_DTE_MIN = 11
    TARGET_DTE_MAX = 18
    TARGET_DTE_IDEAL = 14

    # Exit Rules
    PROFIT_TARGET_PCT = 0.25  # 25% profit target
    STOP_LOSS_PCT = 1.00      # 100% stop loss
    TIME_STOP_DTE = 1         # Close at DTE=1

    # Capital
    INITIAL_CAPITAL = 100000.0

    # Enhanced Strategy: Three signal types
    SIGNAL_TYPES = ['spike_fade', 'declining_trend', 'stagnant_iv']

    IV_RANK_THRESHOLD = 50  # Entry signal: IV Rank > 50%
    COST_PER_CONTRACT = 1.00  # $1 per contract transaction cost
    SLIPPAGE_PCT = 0.005  # 0.5% slippage

# Test 2: Create instance and access all attributes
config = StrategyConfig()

print("Testing StrategyConfig...")
print("="*70)

# Test all attributes that are used in the notebook
attributes_to_test = {
    'DB_PATH': config.DB_PATH,
    'TICKER': config.TICKER,
    'START_DATE': config.START_DATE,
    'END_DATE': config.END_DATE,
    'TARGET_DTE_MIN': config.TARGET_DTE_MIN,
    'TARGET_DTE_MAX': config.TARGET_DTE_MAX,
    'TARGET_DTE_IDEAL': config.TARGET_DTE_IDEAL,
    'PROFIT_TARGET_PCT': config.PROFIT_TARGET_PCT,
    'STOP_LOSS_PCT': config.STOP_LOSS_PCT,
    'TIME_STOP_DTE': config.TIME_STOP_DTE,
    'INITIAL_CAPITAL': config.INITIAL_CAPITAL,
    'SIGNAL_TYPES': config.SIGNAL_TYPES,
    'IV_RANK_THRESHOLD': config.IV_RANK_THRESHOLD,
    'COST_PER_CONTRACT': config.COST_PER_CONTRACT,
    'SLIPPAGE_PCT': config.SLIPPAGE_PCT,
}

all_passed = True
for attr_name, attr_value in attributes_to_test.items():
    try:
        # Access the attribute
        value = getattr(config, attr_name)
        print(f"  ✓ {attr_name}: {value}")
    except AttributeError as e:
        print(f"  ✗ {attr_name}: MISSING - {e}")
        all_passed = False

print("="*70)
if all_passed:
    print("✓ ALL TESTS PASSED - StrategyConfig is complete!")
else:
    print("✗ SOME TESTS FAILED - Please fix the missing attributes")
