"""
Optimized Straddle/Strangle Selling Strategy with Walk-Forward Optimization

Based on research from:
- https://www.projectfinance.com/selling-straddles/
- Professional options trading best practices

Key Features:
1. IV Rank filtering
2. Mean reversion entry timing
3. Profit taking and stop losses
4. OTM strangles for reduced gamma risk
5. Walk-forward parameter optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy import stats


@dataclass
class StrategyParameters:
    """Parameters for the optimized straddle selling strategy."""
    iv_rank_threshold: float = 50.0  # Only sell when IV Rank > this
    iv_declining: bool = True  # Require IV to be declining
    delta_call: float = 0.30  # Delta for call strike (0.50 = ATM, 0.30 = OTM)
    delta_put: float = -0.30  # Delta for put strike
    dte_min: int = 25  # Minimum days to expiration
    dte_max: int = 35  # Maximum days to expiration
    profit_target_pct: float = 0.50  # Close at 50% of max profit
    stop_loss_pct: float = 2.00  # Close if loss > 200% of credit
    position_size_pct: float = 0.05  # Use 5% of capital per trade
    max_positions: int = 1  # Maximum concurrent positions


class IVRankCalculator:
    """Calculate IV Rank and related metrics."""

    @staticmethod
    def calculate_iv_rank(iv_series: pd.Series, window: int = 252) -> pd.Series:
        """
        Calculate IV Rank over rolling window.

        IV Rank = (Current IV - Low) / (High - Low) * 100
        """
        iv_high = iv_series.rolling(window, min_periods=50).max()
        iv_low = iv_series.rolling(window, min_periods=50).min()
        iv_rank = ((iv_series - iv_low) / (iv_high - iv_low) * 100)
        return iv_rank

    @staticmethod
    def calculate_iv_percentile(iv_series: pd.Series, window: int = 252) -> pd.Series:
        """Calculate IV Percentile (percentile rank over window)."""
        def percentile_rank(x):
            if len(x) < 2:
                return np.nan
            return stats.percentileofscore(x, x.iloc[-1], kind='rank')

        return iv_series.rolling(window, min_periods=50).apply(percentile_rank)


class OptimizedStraddleStrategy:
    """
    Optimized straddle/strangle selling strategy with adaptive entry/exit.
    """

    def __init__(self, params: StrategyParameters):
        self.params = params
        self.active_positions = []

    def calculate_iv_metrics(self, options_df: pd.DataFrame,
                            spot_prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate IV, IV Rank, and other metrics."""
        results = []

        for date in options_df['date'].unique():
            day_options = options_df[options_df['date'] == date].copy()
            date_ts = pd.Timestamp(date)

            if date_ts not in spot_prices.index:
                continue

            spot = spot_prices.loc[date_ts, 'close']
            day_options['dte'] = (day_options['expiration'] - day_options['date']).dt.days

            # Get near-term ATM IV (14-18 DTE)
            nearterm = day_options[(day_options['dte'] >= 12) & (day_options['dte'] <= 18)]
            if len(nearterm) == 0:
                continue

            nearterm['strike_dist'] = abs(nearterm['strike'] - spot)
            atm_strike = nearterm.loc[nearterm['strike_dist'].idxmin(), 'strike']
            atm_options = nearterm[nearterm['strike'] == atm_strike]

            if len(atm_options) >= 2:
                atm_iv = atm_options['implied_vol'].mean()

                results.append({
                    'date': date,
                    'spot': spot,
                    'atm_iv': atm_iv,
                    'dte': atm_options['dte'].mean()
                })

        df = pd.DataFrame(results).sort_values('date').reset_index(drop=True)

        # Calculate IV metrics
        df['iv_rank'] = IVRankCalculator.calculate_iv_rank(df['atm_iv'])
        df['iv_percentile'] = IVRankCalculator.calculate_iv_percentile(df['atm_iv'])
        df['iv_20d_mean'] = df['atm_iv'].rolling(20).mean()
        df['iv_60d_mean'] = df['atm_iv'].rolling(60).mean()
        df['iv_60d_std'] = df['atm_iv'].rolling(60).std()
        df['iv_zscore'] = (df['atm_iv'] - df['iv_60d_mean']) / df['iv_60d_std']
        df['iv_change_5d'] = df['atm_iv'].pct_change(5)
        df['iv_change_10d'] = df['atm_iv'].pct_change(10)

        return df

    def generate_entry_signals(self, iv_metrics: pd.DataFrame) -> pd.DataFrame:
        """
        Generate entry signals based on IV Rank and mean reversion.

        Entry Conditions:
        1. IV Rank > threshold
        2. IV declining (5-day change < 0) - mean reversion
        3. Not in existing position
        """
        signals = iv_metrics.copy()

        # Basic filters
        signals['iv_rank_filter'] = signals['iv_rank'] > self.params.iv_rank_threshold
        signals['iv_declining_filter'] = signals['iv_change_5d'] < 0 if self.params.iv_declining else True

        # Combined entry signal
        signals['entry_signal'] = (
            signals['iv_rank_filter'] &
            signals['iv_declining_filter']
        )

        return signals

    def find_optimal_strikes(self, options_df: pd.DataFrame, date: pd.Timestamp,
                            spot: float, target_dte: int = 30) -> Optional[Dict]:
        """
        Find optimal strikes for strangle based on delta targets.

        Returns dict with call_strike, put_strike, expiration.
        """
        day_options = options_df[options_df['date'] == date].copy()

        if len(day_options) == 0:
            return None

        day_options['dte'] = (day_options['expiration'] - day_options['date']).dt.days

        # Filter to target DTE range
        suitable = day_options[
            (day_options['dte'] >= self.params.dte_min) &
            (day_options['dte'] <= self.params.dte_max)
        ]

        if len(suitable) == 0:
            return None

        # Get most common expiration
        expiry = suitable['expiration'].mode()[0]
        expiry_options = suitable[suitable['expiration'] == expiry]

        # Split calls and puts
        calls = expiry_options[expiry_options['call_put'] == 'call']
        puts = expiry_options[expiry_options['call_put'] == 'put']

        if len(calls) == 0 or len(puts) == 0:
            return None

        # Find strikes closest to target deltas
        # For OTM strangle: call delta ~0.30, put delta ~-0.30
        calls['delta_diff'] = abs(calls['delta'] - self.params.delta_call)
        puts['delta_diff'] = abs(puts['delta'] - abs(self.params.delta_put))

        call_strike = calls.loc[calls['delta_diff'].idxmin(), 'strike']
        put_strike = puts.loc[puts['delta_diff'].idxmin(), 'strike']

        # Get actual deltas
        call_delta = calls[calls['strike'] == call_strike]['delta'].values[0]
        put_delta = puts[puts['strike'] == put_strike]['delta'].values[0]

        # Get premiums (use mid price)
        call_premium = calls[calls['strike'] == call_strike]['mid_price'].values[0]
        put_premium = puts[puts['strike'] == put_strike]['mid_price'].values[0]

        return {
            'call_strike': call_strike,
            'put_strike': put_strike,
            'call_delta': call_delta,
            'put_delta': put_delta,
            'call_premium': call_premium,
            'put_premium': put_premium,
            'total_premium': call_premium + put_premium,
            'expiration': expiry,
            'dte': (expiry - date).days
        }


class WalkForwardOptimizer:
    """
    Walk-forward optimization framework.

    - In-sample period: Optimize parameters
    - Out-of-sample period: Test with optimized parameters
    - Roll forward and repeat
    """

    def __init__(self, in_sample_days: int = 126,  # 6 months
                 out_sample_days: int = 63):  # 3 months
        self.in_sample_days = in_sample_days
        self.out_sample_days = out_sample_days

    def create_windows(self, data: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Create in-sample / out-of-sample windows.

        Returns list of (in_sample_df, out_sample_df) tuples.
        """
        windows = []
        total_days = len(data)
        window_size = self.in_sample_days + self.out_sample_days

        start_idx = 0
        while start_idx + window_size <= total_days:
            in_sample = data.iloc[start_idx:start_idx + self.in_sample_days]
            out_sample = data.iloc[start_idx + self.in_sample_days:
                                  start_idx + window_size]
            windows.append((in_sample, out_sample))

            # Move forward by out-of-sample period
            start_idx += self.out_sample_days

        return windows

    def optimize_parameters(self, in_sample_data: pd.DataFrame,
                          options_data: pd.DataFrame,
                          spot_data: pd.DataFrame) -> StrategyParameters:
        """
        Optimize parameters on in-sample data using grid search.

        Parameters to optimize:
        - iv_rank_threshold: [40, 50, 60, 70]
        - profit_target_pct: [0.30, 0.50, 0.70]
        - stop_loss_pct: [1.50, 2.00, 2.50]
        - delta (strike selection): [0.25, 0.30, 0.35, 0.40]
        """
        param_grid = {
            'iv_rank_threshold': [40, 50, 60, 70],
            'profit_target_pct': [0.30, 0.50, 0.70],
            'stop_loss_pct': [1.50, 2.00, 2.50],
            'delta_call': [0.25, 0.30, 0.35, 0.40]
        }

        best_sharpe = -np.inf
        best_params = StrategyParameters()

        # Grid search over parameter combinations
        for iv_rank in param_grid['iv_rank_threshold']:
            for profit_target in param_grid['profit_target_pct']:
                for stop_loss in param_grid['stop_loss_pct']:
                    for delta in param_grid['delta_call']:
                        params = StrategyParameters(
                            iv_rank_threshold=iv_rank,
                            profit_target_pct=profit_target,
                            stop_loss_pct=stop_loss,
                            delta_call=delta,
                            delta_put=-delta
                        )

                        # Simulate strategy with these parameters
                        # (simplified - would run full backtest here)
                        sharpe = self._evaluate_parameters(
                            params, in_sample_data, options_data, spot_data
                        )

                        if sharpe > best_sharpe:
                            best_sharpe = sharpe
                            best_params = params

        return best_params

    def _evaluate_parameters(self, params: StrategyParameters,
                           data: pd.DataFrame,
                           options_data: pd.DataFrame,
                           spot_data: pd.DataFrame) -> float:
        """Evaluate parameter set (returns Sharpe ratio)."""
        # Simplified evaluation - count profitable entry signals
        strategy = OptimizedStraddleStrategy(params)
        signals = strategy.generate_entry_signals(data)

        # Simple heuristic: more signals with higher IV Rank = better
        signal_count = signals['entry_signal'].sum()
        avg_iv_rank = signals[signals['entry_signal']]['iv_rank'].mean()

        if signal_count == 0 or np.isnan(avg_iv_rank):
            return -np.inf

        # Heuristic score (would be actual Sharpe in full implementation)
        return avg_iv_rank / 100 * np.log1p(signal_count)


def calculate_trade_pnl(entry_premium: float, exit_premium: float,
                       quantity: float = 1.0, is_short: bool = True) -> float:
    """Calculate P&L for a straddle/strangle trade."""
    if is_short:
        # Short: collect premium at entry, pay premium at exit
        return (entry_premium - exit_premium) * quantity * 100
    else:
        # Long: pay premium at entry, collect at exit
        return (exit_premium - entry_premium) * quantity * 100
