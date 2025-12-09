"""
Utility functions for the backtester.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
from datetime import datetime, timedelta


def generate_expiry_dates(
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    frequency: str = 'monthly',
    day_of_week: Optional[int] = 4  # Friday
) -> List[pd.Timestamp]:
    """
    Generate option expiry dates.

    Args:
        start_date: Start date
        end_date: End date
        frequency: 'weekly' or 'monthly'
        day_of_week: Day of week for weekly (0=Monday, 4=Friday)

    Returns:
        List of expiry dates
    """
    expiries = []

    if frequency == 'weekly':
        # Weekly expiries (typically Fridays)
        current = start_date
        while current <= end_date:
            # Find next Friday
            days_ahead = day_of_week - current.weekday()
            if days_ahead < 0:
                days_ahead += 7
            expiry = current + pd.Timedelta(days=days_ahead)

            if expiry <= end_date:
                expiries.append(expiry)

            current = expiry + pd.Timedelta(days=7)

    elif frequency == 'monthly':
        # Monthly expiries (third Friday of each month)
        current = start_date

        while current <= end_date:
            # Find third Friday of the month
            first_day = current.replace(day=1)
            first_friday = first_day + pd.Timedelta(days=(4 - first_day.weekday()) % 7)
            third_friday = first_friday + pd.Timedelta(days=14)

            if third_friday >= current and third_friday <= end_date:
                expiries.append(third_friday)

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

    return expiries


def calculate_moneyness(
    spot: float,
    strike: float,
    moneyness_type: str = 'simple'
) -> float:
    """
    Calculate moneyness of an option.

    Args:
        spot: Current spot price
        strike: Strike price
        moneyness_type: 'simple', 'log', or 'forward'

    Returns:
        Moneyness value
    """
    if moneyness_type == 'simple':
        return spot / strike
    elif moneyness_type == 'log':
        return np.log(spot / strike)
    elif moneyness_type == 'forward':
        # Forward moneyness would need forward price
        return spot / strike
    else:
        raise ValueError(f"Unknown moneyness type: {moneyness_type}")


def days_to_expiry(
    current_date: pd.Timestamp,
    expiry_date: pd.Timestamp
) -> int:
    """Calculate trading days to expiry."""
    return (expiry_date - current_date).days


def annualize_return(
    total_return: float,
    num_days: int,
    trading_days_per_year: int = 252
) -> float:
    """
    Annualize a return.

    Args:
        total_return: Total return over period
        num_days: Number of days
        trading_days_per_year: Trading days per year

    Returns:
        Annualized return
    """
    years = num_days / trading_days_per_year
    return (1 + total_return) ** (1 / years) - 1


def calculate_var(
    returns: pd.Series,
    confidence_level: float = 0.95,
    method: str = 'historical'
) -> float:
    """
    Calculate Value at Risk (VaR).

    Args:
        returns: Series of returns
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        method: 'historical' or 'parametric'

    Returns:
        VaR value
    """
    if method == 'historical':
        return np.percentile(returns, (1 - confidence_level) * 100)

    elif method == 'parametric':
        from scipy.stats import norm
        mean = returns.mean()
        std = returns.std()
        return norm.ppf(1 - confidence_level, mean, std)

    else:
        raise ValueError(f"Unknown VaR method: {method}")


def calculate_cvar(
    returns: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.

    Args:
        returns: Series of returns
        confidence_level: Confidence level

    Returns:
        CVaR value
    """
    var = calculate_var(returns, confidence_level, method='historical')
    return returns[returns <= var].mean()


def simulate_gbm(
    S0: float,
    mu: float,
    sigma: float,
    T: float,
    n_steps: int,
    n_paths: int = 1,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Simulate Geometric Brownian Motion paths.

    Args:
        S0: Initial price
        mu: Drift (annual return)
        sigma: Volatility (annual)
        T: Time horizon (in years)
        n_steps: Number of time steps
        n_paths: Number of paths to simulate
        seed: Random seed

    Returns:
        Array of shape (n_steps+1, n_paths) with price paths
    """
    if seed is not None:
        np.random.seed(seed)

    dt = T / n_steps
    paths = np.zeros((n_steps + 1, n_paths))
    paths[0] = S0

    for t in range(1, n_steps + 1):
        z = np.random.standard_normal(n_paths)
        paths[t] = paths[t-1] * np.exp(
            (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
        )

    return paths


def bootstrap_resample(
    data: pd.Series,
    n_samples: int = 1000,
    block_size: Optional[int] = None,
    seed: Optional[int] = None
) -> List[pd.Series]:
    """
    Bootstrap resample time series data.

    Args:
        data: Original data series
        n_samples: Number of bootstrap samples
        block_size: Block size for block bootstrap (None for iid)
        seed: Random seed

    Returns:
        List of resampled series
    """
    if seed is not None:
        np.random.seed(seed)

    samples = []

    if block_size is None:
        # Standard bootstrap
        for _ in range(n_samples):
            indices = np.random.choice(len(data), size=len(data), replace=True)
            samples.append(data.iloc[indices].reset_index(drop=True))
    else:
        # Block bootstrap
        n_blocks = len(data) // block_size
        for _ in range(n_samples):
            blocks = []
            for _ in range(n_blocks):
                start = np.random.randint(0, len(data) - block_size)
                blocks.append(data.iloc[start:start+block_size])

            resampled = pd.concat(blocks).reset_index(drop=True)
            samples.append(resampled[:len(data)])

    return samples


def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.2%}"


def format_number(value: float, decimals: int = 2) -> str:
    """Format number with specified decimals."""
    return f"{value:,.{decimals}f}"
