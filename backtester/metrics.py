"""
Performance metrics, P&L attribution, and breakeven analysis.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import optimize

from .data import MarketData
from .instruments import OptionStrategy
from .models import PricingModel


class PerformanceMetrics:
    """
    Calculate performance metrics for backtested strategies.

    Metrics include:
    - Sharpe ratio
    - Sortino ratio
    - Maximum drawdown
    - Calmar ratio
    - Win rate
    - Volatility
    - Rolling metrics
    """

    def __init__(self, results: pd.DataFrame, risk_free_rate: float = 0.05):
        """
        Initialize performance metrics calculator.

        Args:
            results: Backtest results DataFrame
            risk_free_rate: Annual risk-free rate
        """
        self.results = results
        self.risk_free_rate = risk_free_rate

        # Calculate returns if not present
        if 'returns' not in results.columns:
            self.results['returns'] = results['portfolio_value'].pct_change()

    def total_return(self) -> float:
        """Calculate total return."""
        if 'total_return' in self.results.columns:
            return float(self.results['total_return'].iloc[-1])

        initial_value = self.results['portfolio_value'].iloc[0]
        final_value = self.results['portfolio_value'].iloc[-1]
        return (final_value - initial_value) / initial_value

    def annualized_return(self) -> float:
        """Calculate annualized return (CAGR)."""
        total_ret = self.total_return()
        years = len(self.results) / 252.0  # Trading days
        return (1 + total_ret) ** (1 / years) - 1

    def annualized_volatility(self) -> float:
        """Calculate annualized volatility of returns."""
        daily_vol = self.results['returns'].std()
        return daily_vol * np.sqrt(252)

    def sharpe_ratio(self) -> float:
        """
        Calculate Sharpe ratio.

        Sharpe = (Return - RiskFreeRate) / Volatility
        """
        annual_return = self.annualized_return()
        annual_vol = self.annualized_volatility()

        if annual_vol == 0:
            return 0.0

        return (annual_return - self.risk_free_rate) / annual_vol

    def sortino_ratio(self, target_return: float = 0.0) -> float:
        """
        Calculate Sortino ratio (downside deviation only).

        Args:
            target_return: Target/minimum acceptable return

        Returns:
            Sortino ratio
        """
        annual_return = self.annualized_return()
        returns = self.results['returns'].dropna()

        # Downside deviation
        downside_returns = returns[returns < target_return / 252.0]
        if len(downside_returns) == 0:
            return np.inf

        downside_std = downside_returns.std() * np.sqrt(252)

        if downside_std == 0:
            return 0.0

        return (annual_return - target_return) / downside_std

    def max_drawdown(self) -> Tuple[float, pd.Timestamp, pd.Timestamp]:
        """
        Calculate maximum drawdown.

        Returns:
            Tuple of (max_drawdown, peak_date, trough_date)
        """
        portfolio_values = self.results['portfolio_value']
        cumulative_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values - cumulative_max) / cumulative_max

        max_dd = drawdown.min()
        trough_date = drawdown.idxmin()

        # Find peak date (last max before trough)
        peak_date = cumulative_max[:trough_date].idxmax()

        return max_dd, peak_date, trough_date

    def calmar_ratio(self) -> float:
        """
        Calculate Calmar ratio.

        Calmar = Annualized Return / |Max Drawdown|
        """
        annual_return = self.annualized_return()
        max_dd, _, _ = self.max_drawdown()

        if max_dd == 0:
            return np.inf

        return annual_return / abs(max_dd)

    def win_rate(self) -> float:
        """Calculate win rate (percentage of positive return days)."""
        returns = self.results['returns'].dropna()
        if len(returns) == 0:
            return 0.0

        return (returns > 0).sum() / len(returns)

    def profit_factor(self) -> float:
        """
        Calculate profit factor.

        Profit Factor = Sum of Wins / |Sum of Losses|
        """
        returns = self.results['returns'].dropna()

        wins = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())

        if losses == 0:
            return np.inf

        return wins / losses

    def rolling_sharpe(self, window: int = 60) -> pd.Series:
        """
        Calculate rolling Sharpe ratio.

        Args:
            window: Rolling window size (in days)

        Returns:
            Series of rolling Sharpe ratios
        """
        returns = self.results['returns']

        rolling_mean = returns.rolling(window).mean()
        rolling_std = returns.rolling(window).std()

        # Annualize
        annual_mean = rolling_mean * 252
        annual_std = rolling_std * np.sqrt(252)

        rolling_sharpe = (annual_mean - self.risk_free_rate) / annual_std
        return rolling_sharpe

    def rolling_max_drawdown(self, window: int = 60) -> pd.Series:
        """
        Calculate rolling maximum drawdown.

        Args:
            window: Rolling window size (in days)

        Returns:
            Series of rolling max drawdowns
        """
        portfolio_values = self.results['portfolio_value']

        def calc_dd(window_values):
            cummax = window_values.expanding().max()
            dd = (window_values - cummax) / cummax
            return dd.min()

        rolling_dd = portfolio_values.rolling(window).apply(calc_dd, raw=False)
        return rolling_dd

    def rolling_volatility(self, window: int = 60) -> pd.Series:
        """
        Calculate rolling volatility.

        Args:
            window: Rolling window size (in days)

        Returns:
            Series of rolling annualized volatility
        """
        returns = self.results['returns']
        rolling_vol = returns.rolling(window).std() * np.sqrt(252)
        return rolling_vol

    def omega_ratio(self, threshold: float = 0.0) -> float:
        """
        Calculate Omega ratio.

        The Omega ratio is the probability-weighted ratio of gains versus losses
        above/below a threshold. Unlike Sharpe, it considers the entire distribution
        of returns, not just mean and variance.

        Args:
            threshold: Return threshold (default 0.0 for risk-free rate)

        Returns:
            Omega ratio
        """
        returns = self.results['returns'].dropna()

        # Adjust threshold to daily
        daily_threshold = threshold / 252.0

        # Gains and losses relative to threshold
        gains = returns[returns > daily_threshold] - daily_threshold
        losses = daily_threshold - returns[returns <= daily_threshold]

        if len(losses) == 0 or losses.sum() == 0:
            return np.inf

        return gains.sum() / losses.sum()

    def sterling_ratio(self, lookback_years: int = 3) -> float:
        """
        Calculate Sterling ratio.

        Sterling Ratio = Annual Return / Average of Largest Drawdowns

        Args:
            lookback_years: Number of years for average drawdown calculation

        Returns:
            Sterling ratio
        """
        annual_return = self.annualized_return()

        # Calculate drawdowns
        portfolio_values = self.results['portfolio_value']
        cumulative_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values - cumulative_max) / cumulative_max

        # Get largest drawdowns per year (or all if less data)
        years = max(1, int(len(self.results) / 252))
        n_drawdowns = min(years, lookback_years)

        # Find n largest drawdowns
        largest_dds = drawdown.nsmallest(n_drawdowns).values
        avg_dd = abs(largest_dds.mean())

        if avg_dd == 0:
            return np.inf

        return annual_return / avg_dd

    def ulcer_index(self) -> float:
        """
        Calculate Ulcer Index (measure of downside volatility/pain).

        UI = sqrt(mean(drawdown^2))

        Lower is better. Measures depth and duration of drawdowns.

        Returns:
            Ulcer Index
        """
        portfolio_values = self.results['portfolio_value']
        cumulative_max = portfolio_values.expanding().max()
        drawdown_pct = (portfolio_values - cumulative_max) / cumulative_max * 100  # As percentage

        ulcer = np.sqrt((drawdown_pct ** 2).mean())
        return ulcer

    def value_at_risk(self, confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR) at given confidence level.

        VaR is the maximum expected loss over a period at a given confidence level.

        Args:
            confidence: Confidence level (e.g., 0.95 for 95%)

        Returns:
            VaR (as positive number representing loss)
        """
        returns = self.results['returns'].dropna()
        var = -np.percentile(returns, (1 - confidence) * 100)
        return var

    def conditional_var(self, confidence: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR / Expected Shortfall).

        CVaR is the expected loss given that losses exceed VaR threshold.

        Args:
            confidence: Confidence level (e.g., 0.95 for 95%)

        Returns:
            CVaR (as positive number representing expected loss)
        """
        returns = self.results['returns'].dropna()
        var_threshold = np.percentile(returns, (1 - confidence) * 100)

        # Average of returns below VaR threshold
        tail_returns = returns[returns <= var_threshold]

        if len(tail_returns) == 0:
            return 0.0

        cvar = -tail_returns.mean()
        return cvar

    def skewness(self) -> float:
        """
        Calculate skewness of returns distribution.

        Negative skew = more extreme losses than gains
        Positive skew = more extreme gains than losses

        Returns:
            Skewness
        """
        returns = self.results['returns'].dropna()
        from scipy import stats
        return stats.skew(returns)

    def kurtosis(self) -> float:
        """
        Calculate excess kurtosis of returns distribution.

        High kurtosis = fat tails (more extreme events than normal distribution)

        Returns:
            Excess kurtosis
        """
        returns = self.results['returns'].dropna()
        from scipy import stats
        return stats.kurtosis(returns)

    def recovery_factor(self) -> float:
        """
        Calculate Recovery Factor.

        Recovery Factor = Total Return / |Max Drawdown|

        Measures how much profit is made relative to worst drawdown.

        Returns:
            Recovery factor
        """
        total_ret = self.total_return()
        max_dd, _, _ = self.max_drawdown()

        if max_dd == 0:
            return np.inf

        return total_ret / abs(max_dd)

    def expectancy(self) -> float:
        """
        Calculate trading expectancy.

        Expectancy = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)

        Returns:
            Expected value per trade
        """
        returns = self.results['returns'].dropna()

        wins = returns[returns > 0]
        losses = returns[returns < 0]

        if len(returns) == 0:
            return 0.0

        win_rate = len(wins) / len(returns)
        loss_rate = len(losses) / len(returns)

        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0.0

        return (win_rate * avg_win) - (loss_rate * avg_loss)

    def average_win_loss_ratio(self) -> float:
        """
        Calculate average win to average loss ratio.

        Returns:
            Win/Loss ratio
        """
        returns = self.results['returns'].dropna()

        wins = returns[returns > 0]
        losses = returns[returns < 0]

        if len(losses) == 0:
            return np.inf

        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss = abs(losses.mean())

        return avg_win / avg_loss

    def max_consecutive_wins(self) -> int:
        """Calculate maximum consecutive winning days."""
        returns = self.results['returns'].dropna()
        wins = (returns > 0).astype(int)

        max_streak = 0
        current_streak = 0

        for win in wins:
            if win:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    def max_consecutive_losses(self) -> int:
        """Calculate maximum consecutive losing days."""
        returns = self.results['returns'].dropna()
        losses = (returns < 0).astype(int)

        max_streak = 0
        current_streak = 0

        for loss in losses:
            if loss:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    def information_ratio(self, benchmark_returns: Optional[pd.Series] = None) -> float:
        """
        Calculate Information Ratio (IR).

        IR = (Portfolio Return - Benchmark Return) / Tracking Error

        Args:
            benchmark_returns: Benchmark returns series (if None, uses 0)

        Returns:
            Information ratio
        """
        if benchmark_returns is None:
            benchmark_returns = pd.Series(0, index=self.results.index)

        portfolio_returns = self.results['returns'].dropna()

        # Align indices
        portfolio_returns, benchmark_returns = portfolio_returns.align(
            benchmark_returns, join='inner'
        )

        # Excess returns
        excess_returns = portfolio_returns - benchmark_returns

        # Tracking error (std of excess returns)
        tracking_error = excess_returns.std() * np.sqrt(252)

        if tracking_error == 0:
            return 0.0

        # Annualized excess return
        annualized_excess = excess_returns.mean() * 252

        return annualized_excess / tracking_error

    def summary(self) -> Dict[str, float]:
        """
        Generate summary statistics.

        Returns:
            Dictionary of key metrics
        """
        max_dd, peak_date, trough_date = self.max_drawdown()

        return {
            'Total Return': self.total_return(),
            'Annualized Return': self.annualized_return(),
            'Annualized Volatility': self.annualized_volatility(),
            'Sharpe Ratio': self.sharpe_ratio(),
            'Sortino Ratio': self.sortino_ratio(),
            'Omega Ratio': self.omega_ratio(),
            'Max Drawdown': max_dd,
            'Calmar Ratio': self.calmar_ratio(),
            'Sterling Ratio': self.sterling_ratio(),
            'Ulcer Index': self.ulcer_index(),
            'Win Rate': self.win_rate(),
            'Profit Factor': self.profit_factor(),
            'Recovery Factor': self.recovery_factor(),
            'Expectancy': self.expectancy(),
            'Avg Win/Loss': self.average_win_loss_ratio(),
            'Max Consecutive Wins': self.max_consecutive_wins(),
            'Max Consecutive Losses': self.max_consecutive_losses(),
            'VaR (95%)': self.value_at_risk(0.95),
            'CVaR (95%)': self.conditional_var(0.95),
            'Skewness': self.skewness(),
            'Kurtosis': self.kurtosis(),
            'Number of Days': len(self.results),
        }

    def print_summary(self):
        """Print formatted summary."""
        summary = self.summary()

        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)

        for metric, value in summary.items():
            if 'Return' in metric or 'Volatility' in metric or 'Drawdown' in metric or 'VaR' in metric or 'CVaR' in metric or 'Expectancy' in metric:
                print(f"{metric:35s}: {value:>10.2%}")
            elif 'Ratio' in metric or 'Rate' in metric or 'Factor' in metric or 'Skewness' in metric or 'Kurtosis' in metric or 'Index' in metric:
                print(f"{metric:35s}: {value:>10.2f}")
            elif 'Consecutive' in metric or 'Number' in metric:
                print(f"{metric:35s}: {value:>10.0f}")
            else:
                print(f"{metric:35s}: {value:>10.2f}")

        print("="*60)


class PnLAttributionEngine:
    """
    Attribute P&L to different Greeks and risk factors.

    Decomposes daily P&L into:
    - Delta P&L
    - Gamma P&L
    - Vega P&L
    - Theta P&L
    - Rho P&L
    - Residual/unexplained P&L
    """

    def __init__(self, results: pd.DataFrame):
        """
        Initialize P&L attribution engine.

        Args:
            results: Backtest results with Greeks and P&L attribution
        """
        self.results = results

    def total_attribution(self) -> Dict[str, float]:
        """
        Calculate total P&L attribution over the backtest period.

        Returns:
            Dictionary of cumulative P&L by Greek
        """
        attribution = {
            'Delta': self.results['pnl_delta'].sum(),
            'Gamma': self.results['pnl_gamma'].sum(),
            'Vega': self.results['pnl_vega'].sum(),
            'Theta': self.results['pnl_theta'].sum(),
            'Rho': self.results['pnl_rho'].sum(),
            'Residual': self.results['pnl_residual'].sum(),
        }

        total = sum(attribution.values())
        attribution['Total'] = total

        return attribution

    def attribution_percentages(self) -> Dict[str, float]:
        """
        Calculate P&L attribution as percentages.

        Returns:
            Dictionary of attribution percentages
        """
        attribution = self.total_attribution()
        total = attribution['Total']

        if total == 0:
            return {k: 0.0 for k in attribution.keys()}

        return {
            k: v / total for k, v in attribution.items()
        }

    def cumulative_attribution(self) -> pd.DataFrame:
        """
        Calculate cumulative P&L attribution over time.

        Returns:
            DataFrame with cumulative attribution by Greek
        """
        cumulative = pd.DataFrame({
            'Delta': self.results['pnl_delta'].cumsum(),
            'Gamma': self.results['pnl_gamma'].cumsum(),
            'Vega': self.results['pnl_vega'].cumsum(),
            'Theta': self.results['pnl_theta'].cumsum(),
            'Rho': self.results['pnl_rho'].cumsum(),
            'Residual': self.results['pnl_residual'].cumsum(),
        }, index=self.results.index)

        return cumulative

    def print_summary(self):
        """Print attribution summary."""
        attribution = self.total_attribution()
        percentages = self.attribution_percentages()

        print("\n" + "="*60)
        print("P&L ATTRIBUTION SUMMARY")
        print("="*60)

        for greek, value in attribution.items():
            if greek != 'Total':
                pct = percentages[greek]
                print(f"{greek:15s}: ${value:>12,.2f}  ({pct:>6.1%})")

        print("-"*60)
        print(f"{'Total':15s}: ${attribution['Total']:>12,.2f}  (100.0%)")
        print("="*60)


class BreakevenAnalyzer:
    """
    Calculate breakeven levels for strategies at different time horizons.

    Determines the underlying price(s) where strategy P&L = 0 for:
    - Daily horizon (1 day)
    - Weekly horizon (~5 days)
    - Monthly horizon (~21 days)
    - At expiration
    """

    def __init__(
        self,
        strategy: OptionStrategy,
        market_data: MarketData,
        model: PricingModel
    ):
        """
        Initialize breakeven analyzer.

        Args:
            strategy: Option strategy to analyze
            market_data: Market data
            model: Pricing model
        """
        self.strategy = strategy
        self.market_data = market_data
        self.model = model

    def breakeven_at_expiry(
        self,
        current_date: pd.Timestamp,
        spot_range: Optional[np.ndarray] = None
    ) -> List[float]:
        """
        Calculate breakeven points at expiration.

        Args:
            current_date: Current valuation date
            spot_range: Range of spot prices to search

        Returns:
            List of breakeven spot prices
        """
        # Get strikes for range determination
        strikes = [leg.contract.strike for leg in self.strategy.legs]
        min_strike = min(strikes)
        max_strike = max(strikes)

        if spot_range is None:
            spot_range = np.linspace(
                min_strike * 0.5, max_strike * 1.5, 1000
            )

        # Calculate payoffs at expiration
        payoffs = np.array([
            self.strategy.payoff(spot, at_expiry=True)
            for spot in spot_range
        ])

        # Find zero crossings
        breakevens = []
        for i in range(len(payoffs) - 1):
            if payoffs[i] * payoffs[i+1] < 0:  # Sign change
                # Linear interpolation
                x1, x2 = spot_range[i], spot_range[i+1]
                y1, y2 = payoffs[i], payoffs[i+1]
                breakeven = x1 - y1 * (x2 - x1) / (y2 - y1)
                breakevens.append(breakeven)

        return breakevens

    def breakeven_at_horizon(
        self,
        current_date: pd.Timestamp,
        horizon_days: int,
        initial_cost: Optional[float] = None
    ) -> List[float]:
        """
        Calculate breakeven points at a future date.

        Args:
            current_date: Current valuation date
            horizon_days: Number of days in the future
            initial_cost: Initial cost of strategy (if None, calculate current value)

        Returns:
            List of breakeven spot prices
        """
        if initial_cost is None:
            initial_cost = self.strategy.value(
                current_date, self.market_data, self.model
            )

        # Future date
        future_date = current_date + pd.Timedelta(days=horizon_days)

        # Get strikes for range
        strikes = [leg.contract.strike for leg in self.strategy.legs]
        min_strike = min(strikes)
        max_strike = max(strikes)

        spot_range = np.linspace(min_strike * 0.5, max_strike * 1.5, 200)

        def pnl_at_spot(spot):
            """Calculate P&L if underlying is at 'spot' on future_date."""
            # This is simplified - would need to adjust market data with new spot
            # For now, use expiry payoff as approximation
            try:
                # Check if already expired
                min_expiry = min(leg.contract.expiry for leg in self.strategy.legs)
                if future_date >= min_expiry:
                    return self.strategy.payoff(spot, at_expiry=True) - initial_cost

                # Otherwise, would need to re-price with adjusted vol surface
                # Simplified: use linear interpolation between current and expiry
                days_to_expiry = (min_expiry - current_date).days
                weight = horizon_days / days_to_expiry

                current_value = self.strategy.value(
                    current_date, self.market_data, self.model
                )
                expiry_payoff = self.strategy.payoff(spot, at_expiry=True)

                # Interpolate
                future_value = (1 - weight) * current_value + weight * expiry_payoff

                return future_value - initial_cost
            except:
                return 0.0

        # Find breakevens
        breakevens = []

        # Use optimization for each potential breakeven region
        # Split into sections around strikes
        search_points = sorted([min_strike * 0.7] + strikes + [max_strike * 1.3])

        for i in range(len(search_points) - 1):
            try:
                result = optimize.brentq(
                    pnl_at_spot,
                    search_points[i],
                    search_points[i+1],
                    xtol=0.01
                )
                breakevens.append(result)
            except:
                pass

        return breakevens

    def breakeven_schedule(
        self,
        current_date: pd.Timestamp,
        horizons: List[int] = None
    ) -> pd.DataFrame:
        """
        Calculate breakeven schedule across multiple horizons.

        Args:
            current_date: Current date
            horizons: List of horizons in days (default: [1, 5, 21, at expiry])

        Returns:
            DataFrame with breakevens by horizon
        """
        if horizons is None:
            # Default horizons
            min_expiry = min(leg.contract.expiry for leg in self.strategy.legs)
            days_to_expiry = (min_expiry - current_date).days

            horizons = [1, 5, 21, min(days_to_expiry, 252)]

        initial_cost = self.strategy.value(
            current_date, self.market_data, self.model
        )

        results = []

        for horizon in horizons:
            breakevens = self.breakeven_at_horizon(
                current_date, horizon, initial_cost
            )

            for be in breakevens:
                results.append({
                    'horizon_days': horizon,
                    'breakeven': be
                })

        # Add expiry breakevens
        expiry_breakevens = self.breakeven_at_expiry(current_date)
        for be in expiry_breakevens:
            results.append({
                'horizon_days': 'expiry',
                'breakeven': be
            })

        return pd.DataFrame(results)

    def print_breakevens(self, current_date: pd.Timestamp):
        """Print breakeven analysis."""
        schedule = self.breakeven_schedule(current_date)

        print("\n" + "="*50)
        print("BREAKEVEN ANALYSIS")
        print("="*50)

        current_spot = self.market_data.get_spot(current_date)
        print(f"Current Spot: ${current_spot:.2f}\n")

        grouped = schedule.groupby('horizon_days')

        for horizon, group in grouped:
            breakevens = group['breakeven'].values

            if isinstance(horizon, str):
                print(f"At {horizon.upper()}:")
            else:
                print(f"In {horizon} day(s):")

            if len(breakevens) == 0:
                print("  No breakevens found")
            elif len(breakevens) == 1:
                pct_move = (breakevens[0] - current_spot) / current_spot
                print(f"  ${breakevens[0]:.2f} ({pct_move:+.1%})")
            else:
                # Assume lower and upper breakevens
                lower = min(breakevens)
                upper = max(breakevens)
                lower_pct = (lower - current_spot) / current_spot
                upper_pct = (upper - current_spot) / current_spot

                print(f"  Lower: ${lower:.2f} ({lower_pct:+.1%})")
                print(f"  Upper: ${upper:.2f} ({upper_pct:+.1%})")

            print()

        print("="*50)
