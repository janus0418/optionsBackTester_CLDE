"""
Enhanced ATM Straddle Strategy Functions
Three signal types: Spike Fade, Declining Trend, Stagnant IV
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Optional

def calculate_trend_slope(series: pd.Series, window: int = 10) -> pd.Series:
    """
    Calculate regression slope over rolling window.

    Args:
        series: Time series data (e.g., IV)
        window: Rolling window size

    Returns:
        Series of slopes
    """
    slopes = []
    for i in range(len(series)):
        if i < window - 1:
            slopes.append(np.nan)
        else:
            y = series.iloc[i-window+1:i+1].values
            x = np.arange(window)
            slope, _, _, _, _ = stats.linregress(x, y)
            slopes.append(slope)
    return pd.Series(slopes, index=series.index)


def calculate_percentile_rank(series: pd.Series, window: int) -> pd.Series:
    """
    Calculate percentile rank within rolling window.

    Args:
        series: Time series data
        window: Rolling window size

    Returns:
        Series of percentile ranks (0-100)
    """
    result = []
    for i in range(len(series)):
        if i < window - 1:
            result.append(np.nan)
        else:
            window_data = series.iloc[max(0, i-window+1):i+1]
            current = series.iloc[i]
            if len(window_data) > 0:
                pct = (window_data < current).sum() / len(window_data) * 100
            else:
                pct = np.nan
            result.append(pct)
    return pd.Series(result, index=series.index)


def calculate_enhanced_iv_metrics(options_df: pd.DataFrame,
                                  spot_prices: pd.DataFrame,
                                  lookback_days: int = 252) -> pd.DataFrame:
    """
    Calculate comprehensive IV metrics for enhanced strategy.

    Includes:
    - IV Rank (52-week)
    - IV Trend (10d and 20d slopes)
    - IV Volatility (vol-of-vol)
    - IV Changes (5d, 10d)
    - Moving averages
    - Percentile rankings

    Args:
        options_df: Options data with implied_vol
        spot_prices: Spot price data
        lookback_days: Days for IV Rank calculation (default 252)

    Returns:
        DataFrame with all IV metrics
    """
    results = []

    for date in options_df['date'].unique():
        day_options = options_df[options_df['date'] == date].copy()
        date_ts = pd.Timestamp(date)

        if date_ts not in spot_prices.index:
            continue

        spot = spot_prices.loc[date_ts, 'close']
        day_options['dte'] = (day_options['expiration'] - day_options['date']).dt.days

        # Get ATM IV from 11-18 DTE options
        nearterm = day_options[(day_options['dte'] >= 11) & (day_options['dte'] <= 18)]

        if len(nearterm) == 0:
            continue

        nearterm['strike_dist'] = abs(nearterm['strike'] - spot)
        atm_strike = nearterm.loc[nearterm['strike_dist'].idxmin(), 'strike']
        atm_opts = nearterm[nearterm['strike'] == atm_strike]

        if len(atm_opts) >= 1 and not atm_opts['implied_vol'].isna().all():
            atm_iv = atm_opts['implied_vol'].mean()

            results.append({
                'date': date,
                'spot': spot,
                'atm_strike': atm_strike,
                'atm_iv': atm_iv,
                'dte': atm_opts['dte'].mean()
            })

    df = pd.DataFrame(results).sort_values('date').reset_index(drop=True)

    if len(df) == 0:
        return df

    # === BASIC METRICS ===
    # IV Rank (52-week)
    df['iv_52w_high'] = df['atm_iv'].rolling(lookback_days, min_periods=20).max()
    df['iv_52w_low'] = df['atm_iv'].rolling(lookback_days, min_periods=20).min()
    df['iv_rank'] = ((df['atm_iv'] - df['iv_52w_low']) /
                     (df['iv_52w_high'] - df['iv_52w_low']) * 100)

    # === TREND METRICS ===
    # IV trend slopes (regression)
    df['iv_trend_10d'] = calculate_trend_slope(df['atm_iv'], window=10)
    df['iv_trend_20d'] = calculate_trend_slope(df['atm_iv'], window=20)

    # Moving averages
    df['iv_10d_ma'] = df['atm_iv'].rolling(10).mean()
    df['iv_20d_ma'] = df['atm_iv'].rolling(20).mean()

    # === VOLATILITY-OF-VOLATILITY METRICS ===
    # Standard deviation of IV (vol-of-vol)
    df['iv_10d_std'] = df['atm_iv'].rolling(10).std()
    df['iv_20d_std'] = df['atm_iv'].rolling(20).std()

    # Percentile rank of vol-of-vol (relative to 60-day history)
    df['iv_vol_percentile'] = calculate_percentile_rank(df['iv_10d_std'], window=60)

    # === CHANGE METRICS ===
    df['iv_5d_change'] = df['atm_iv'].pct_change(5)
    df['iv_10d_change'] = df['atm_iv'].pct_change(10)
    df['iv_1d_change'] = df['atm_iv'].pct_change(1)

    # === Z-SCORE ===
    df['iv_60d_mean'] = df['atm_iv'].rolling(60).mean()
    df['iv_60d_std'] = df['atm_iv'].rolling(60).std()
    df['iv_zscore'] = (df['atm_iv'] - df['iv_60d_mean']) / df['iv_60d_std']

    return df


def generate_multi_signal_entries(iv_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate three types of entry signals:
    1. Spike Fade: High IV Rank + declining
    2. Declining Trend: Sustained IV downtrend
    3. Stagnant IV: Low vol-of-vol + stable IV

    Args:
        iv_df: DataFrame with IV metrics

    Returns:
        DataFrame with signal columns added
    """
    signals = iv_df.copy()

    # === SIGNAL 1: SPIKE FADE ===
    # High IV Rank + IV declining (mean reversion after spike)
    signals['signal_spike_fade'] = (
        (signals['iv_rank'] > 50) &  # High IV Rank
        (signals['iv_5d_change'] < -0.02) &  # IV declining > 2%
        (signals['iv_1d_change'] < 0)  # Still declining today
    )

    # === SIGNAL 2: DECLINING TREND ===
    # Sustained IV downtrend (trend continuation)
    signals['signal_declining_trend'] = (
        (signals['iv_trend_10d'] < -0.0001) &  # Negative 10d slope
        (signals['iv_trend_20d'] < 0) &  # Negative 20d slope (confirmation)
        (signals['iv_rank'] > 25) &  # Not at rock-bottom
        (signals['iv_rank'] < 60) &  # Not entering at peak
        (signals['atm_iv'] < signals['iv_20d_ma'])  # Below MA
    )

    # === SIGNAL 3: STAGNANT IV ===
    # Low volatility-of-volatility (stable premium environment)
    signals['signal_stagnant_iv'] = (
        (signals['iv_vol_percentile'] < 30) &  # Low vol-of-vol
        (signals['iv_rank'] > 20) &  # Minimum IV level
        (signals['iv_rank'] < 50) &  # Not too high
        (abs(signals['iv_5d_change']) < 0.05) &  # Stable (< 5% change)
        (signals['iv_10d_std'] < signals['iv_20d_std'])  # Vol contracting
    )

    # === COMBINED SIGNAL ===
    signals['entry_signal'] = (
        signals['signal_spike_fade'] |
        signals['signal_declining_trend'] |
        signals['signal_stagnant_iv']
    )

    # === SIGNAL TYPE (for tracking) ===
    def get_signal_type(row):
        if pd.isna(row['entry_signal']) or not row['entry_signal']:
            return None
        if row['signal_spike_fade']:
            return 'spike_fade'
        elif row['signal_declining_trend']:
            return 'declining_trend'
        elif row['signal_stagnant_iv']:
            return 'stagnant_iv'
        return None

    signals['signal_type'] = signals.apply(get_signal_type, axis=1)

    return signals


def get_signal_summary(signals_df: pd.DataFrame) -> Dict:
    """
    Get summary statistics of generated signals.

    Args:
        signals_df: DataFrame with signal columns

    Returns:
        Dictionary with signal counts and percentages
    """
    total_days = len(signals_df)

    summary = {
        'total_days': total_days,
        'spike_fade': signals_df['signal_spike_fade'].sum(),
        'declining_trend': signals_df['signal_declining_trend'].sum(),
        'stagnant_iv': signals_df['signal_stagnant_iv'].sum(),
        'total_signals': signals_df['entry_signal'].sum()
    }

    # Calculate percentages
    if total_days > 0:
        summary['spike_fade_pct'] = summary['spike_fade'] / total_days * 100
        summary['declining_trend_pct'] = summary['declining_trend'] / total_days * 100
        summary['stagnant_iv_pct'] = summary['stagnant_iv'] / total_days * 100
        summary['total_signals_pct'] = summary['total_signals'] / total_days * 100

    return summary
