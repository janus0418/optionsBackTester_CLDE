"""
Backtesting engine for options strategies.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .data import MarketData
from .instruments import Portfolio, OptionStrategy
from .models import PricingModel, BlackScholesModel


@dataclass
class BacktestConfig:
    """
    Configuration for backtesting.

    Attributes:
        start_date: Backtest start date
        end_date: Backtest end date
        initial_capital: Starting capital
        rebalancing_frequency: 'daily', 'weekly', 'monthly', or custom
        transaction_cost_per_contract: Fixed cost per contract
        transaction_cost_pct: Percentage cost (of notional)
        slippage_bps: Slippage in basis points
        risk_free_rate: Risk-free rate (if not from data)
        rolling_windows: List of rolling window sizes (in days)
        model: Pricing model to use
    """
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    initial_capital: float = 100000.0
    rebalancing_frequency: str = 'daily'
    transaction_cost_per_contract: float = 0.65
    transaction_cost_pct: float = 0.0001
    slippage_bps: float = 1.0
    risk_free_rate: Optional[float] = None
    rolling_windows: List[int] = field(default_factory=lambda: [20, 60, 252])
    model: Optional[PricingModel] = None

    def __post_init__(self):
        """Set default model if not provided."""
        if self.model is None:
            self.model = BlackScholesModel(use_market_iv=True)


class BacktestEngine:
    """
    Main backtesting engine.

    Orchestrates:
    - Strategy execution over time
    - Portfolio tracking
    - P&L calculation
    - Greeks calculation
    - P&L attribution
    - Performance metrics
    """

    def __init__(
        self,
        market_data: MarketData,
        config: BacktestConfig
    ):
        """
        Initialize backtest engine.

        Args:
            market_data: Historical market data
            config: Backtest configuration
        """
        self.market_data = market_data
        self.config = config
        self.portfolio = Portfolio(initial_cash=config.initial_capital)

        # Results storage
        self.daily_results = []
        self.trades = []

        # State tracking
        self.current_date = None
        self.prev_portfolio_value = config.initial_capital
        self.prev_greeks = {
            'delta': 0.0, 'gamma': 0.0, 'vega': 0.0,
            'theta': 0.0, 'rho': 0.0
        }

    def add_strategy(
        self,
        strategy: OptionStrategy,
        entry_date: pd.Timestamp,
        exit_date: Optional[pd.Timestamp] = None,
        entry_signal: Optional[Callable] = None,
        exit_signal: Optional[Callable] = None
    ):
        """
        Add a strategy to backtest.

        Args:
            strategy: OptionStrategy instance
            entry_date: Date to enter the strategy
            exit_date: Date to exit (None = hold to expiry)
            entry_signal: Optional callable for dynamic entry
            exit_signal: Optional callable for dynamic exit
        """
        self.portfolio.add_strategy(strategy)

        # Record entry trade
        entry_cost = strategy.value(
            entry_date, self.market_data, self.config.model
        )

        # Add transaction costs
        num_contracts = sum(abs(leg.quantity) for leg in strategy.legs)
        txn_cost = (
            num_contracts * self.config.transaction_cost_per_contract +
            abs(entry_cost) * self.config.transaction_cost_pct
        )

        total_cost = entry_cost + txn_cost

        self.portfolio.record_trade(
            date=entry_date,
            description=f"Enter {strategy.name}",
            cash_flow=-total_cost,
            strategy_index=len(self.portfolio.strategies) - 1
        )

    def run(self) -> pd.DataFrame:
        """
        Run the backtest.

        Returns:
            DataFrame with daily results
        """
        # Get trading dates
        trading_dates = self.market_data.time_index[
            (self.market_data.time_index >= self.config.start_date) &
            (self.market_data.time_index <= self.config.end_date)
        ]

        print(f"Running backtest from {self.config.start_date} to {self.config.end_date}")
        print(f"Trading days: {len(trading_dates)}")

        for date in trading_dates:
            self.current_date = date
            self._process_day(date)

        # Convert results to DataFrame
        results_df = pd.DataFrame(self.daily_results)
        if not results_df.empty:
            results_df.set_index('date', inplace=True)

        print(f"\nBacktest complete!")
        print(f"Final portfolio value: ${results_df['portfolio_value'].iloc[-1]:,.2f}")
        print(f"Total return: {results_df['total_return'].iloc[-1]:.2%}")

        return results_df

    def _process_day(self, date: pd.Timestamp):
        """Process a single trading day."""
        # 1. Get market state
        spot = self.market_data.get_spot(date)

        # 2. Calculate portfolio value and Greeks
        portfolio_value = self.portfolio.value(
            date, self.market_data, self.config.model
        )
        portfolio_greeks = self.portfolio.greeks(
            date, self.market_data, self.config.model
        )

        # 3. Calculate P&L
        daily_pnl = portfolio_value - self.prev_portfolio_value
        total_return = (portfolio_value - self.config.initial_capital) / self.config.initial_capital

        # 4. P&L Attribution (if not first day)
        if self.prev_portfolio_value != self.config.initial_capital:
            pnl_attribution = self._calculate_pnl_attribution(
                date, spot, portfolio_greeks
            )
        else:
            pnl_attribution = {
                'pnl_delta': 0.0,
                'pnl_gamma': 0.0,
                'pnl_vega': 0.0,
                'pnl_theta': 0.0,
                'pnl_rho': 0.0,
                'pnl_residual': 0.0
            }

        # 5. Check for expired options and handle expiration
        self._handle_expirations(date)

        # 6. Record daily results
        result = {
            'date': date,
            'spot': spot,
            'portfolio_value': portfolio_value,
            'cash': self.portfolio.cash,
            'daily_pnl': daily_pnl,
            'total_return': total_return,
            **portfolio_greeks,
            **pnl_attribution,
            'num_strategies': len(self.portfolio.strategies),
        }

        self.daily_results.append(result)

        # 7. Update state for next day
        self.prev_portfolio_value = portfolio_value
        self.prev_greeks = portfolio_greeks.copy()

    def _calculate_pnl_attribution(
        self,
        date: pd.Timestamp,
        current_spot: float,
        current_greeks: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Attribute P&L to Greeks using first-order Taylor approximation.

        Args:
            date: Current date
            current_spot: Current spot price
            current_greeks: Current portfolio Greeks

        Returns:
            Dictionary of P&L attributions
        """
        # Get previous day's data
        prev_date = self.current_date - pd.Timedelta(days=1)

        # Try to find actual previous trading day
        try:
            prev_spot = self.market_data.get_spot(prev_date)
        except:
            # If previous day not available, use current
            return {
                'pnl_delta': 0.0,
                'pnl_gamma': 0.0,
                'pnl_vega': 0.0,
                'pnl_theta': 0.0,
                'pnl_rho': 0.0,
                'pnl_residual': 0.0
            }

        # Calculate changes
        dS = current_spot - prev_spot
        dt = 1.0 / 365.0  # One day in years

        # Use previous day's Greeks for attribution
        prev_delta = self.prev_greeks['delta']
        prev_gamma = self.prev_greeks['gamma']
        prev_vega = self.prev_greeks['vega']
        prev_theta = self.prev_greeks['theta']
        prev_rho = self.prev_greeks['rho']

        # P&L components (Taylor series approximation)
        pnl_delta = prev_delta * dS
        pnl_gamma = 0.5 * prev_gamma * (dS ** 2)
        pnl_theta = prev_theta * 1.0  # theta is already per day
        pnl_vega = 0.0  # Would need vol change data
        pnl_rho = 0.0   # Would need rate change data

        # Total explained P&L
        pnl_explained = pnl_delta + pnl_gamma + pnl_theta + pnl_vega + pnl_rho

        # Actual P&L
        actual_pnl = self.daily_results[-1]['daily_pnl'] if self.daily_results else 0.0

        # Residual
        pnl_residual = actual_pnl - pnl_explained

        return {
            'pnl_delta': pnl_delta,
            'pnl_gamma': pnl_gamma,
            'pnl_vega': pnl_vega,
            'pnl_theta': pnl_theta,
            'pnl_rho': pnl_rho,
            'pnl_residual': pnl_residual
        }

    def _handle_expirations(self, date: pd.Timestamp):
        """Handle option expirations."""
        strategies_to_remove = []

        for i, strategy in enumerate(self.portfolio.strategies):
            # Check if any leg has expired
            for leg in strategy.legs:
                if leg.contract.expiry <= date:
                    # Calculate final payoff
                    spot = self.market_data.get_spot(date)
                    final_payoff = leg.payoff(spot)

                    # Settle the position
                    self.portfolio.cash += final_payoff

                    # Mark strategy for removal
                    if i not in strategies_to_remove:
                        strategies_to_remove.append(i)

                    # Record the expiration
                    self.portfolio.record_trade(
                        date=date,
                        description=f"Expiration: {strategy.name}",
                        cash_flow=final_payoff,
                        strategy_index=i
                    )

        # Remove expired strategies (in reverse order to maintain indices)
        for i in sorted(strategies_to_remove, reverse=True):
            self.portfolio.remove_strategy(i)

    def get_results(self) -> pd.DataFrame:
        """
        Get backtest results.

        Returns:
            DataFrame with daily results
        """
        if not self.daily_results:
            return pd.DataFrame()

        df = pd.DataFrame(self.daily_results)
        df.set_index('date', inplace=True)
        return df

    def get_trades(self) -> pd.DataFrame:
        """
        Get trade history.

        Returns:
            DataFrame with trade history
        """
        return self.portfolio.get_trade_history()


class RollingStrategy:
    """
    Helper class for strategies that roll periodically.

    Examples:
    - Monthly calendar spreads
    - Weekly iron condors
    - Daily gamma scalping
    """

    def __init__(
        self,
        strategy_factory: Callable,
        entry_frequency: str = 'monthly',  # 'daily', 'weekly', 'monthly'
        exit_on_expiry: bool = True,
        days_before_expiry: int = 0
    ):
        """
        Initialize rolling strategy.

        Args:
            strategy_factory: Function that creates new strategy instances
            entry_frequency: How often to enter new positions
            exit_on_expiry: Whether to exit at expiration
            days_before_expiry: Days before expiry to exit early
        """
        self.strategy_factory = strategy_factory
        self.entry_frequency = entry_frequency
        self.exit_on_expiry = exit_on_expiry
        self.days_before_expiry = days_before_expiry

    def should_enter(self, date: pd.Timestamp, prev_date: Optional[pd.Timestamp]) -> bool:
        """Determine if should enter new position on this date."""
        if prev_date is None:
            return True

        if self.entry_frequency == 'daily':
            return True
        elif self.entry_frequency == 'weekly':
            # Enter on Mondays
            return date.weekday() == 0
        elif self.entry_frequency == 'monthly':
            # Enter on first trading day of month
            return date.month != prev_date.month
        else:
            return False

    def should_exit(
        self,
        date: pd.Timestamp,
        strategy: OptionStrategy
    ) -> bool:
        """Determine if should exit position on this date."""
        if not self.exit_on_expiry:
            return False

        # Check if any leg is near expiration
        for leg in strategy.legs:
            days_to_expiry = (leg.contract.expiry - date).days
            if days_to_expiry <= self.days_before_expiry:
                return True

        return False


class DeltaHedger:
    """
    Delta hedging utility for volatility strategies.

    Maintains portfolio delta near zero by trading the underlying.
    """

    def __init__(
        self,
        target_delta: float = 0.0,
        tolerance: float = 0.1,
        rebalance_frequency: str = 'daily'
    ):
        """
        Initialize delta hedger.

        Args:
            target_delta: Target delta to maintain
            tolerance: Tolerance before rebalancing
            rebalance_frequency: How often to rebalance
        """
        self.target_delta = target_delta
        self.tolerance = tolerance
        self.rebalance_frequency = rebalance_frequency
        self.underlying_position = 0.0

    def should_rebalance(self, current_delta: float) -> bool:
        """Check if rebalancing is needed."""
        return abs(current_delta - self.target_delta) > self.tolerance

    def calculate_hedge(self, current_delta: float) -> float:
        """
        Calculate required hedge trade.

        Args:
            current_delta: Current portfolio delta

        Returns:
            Number of shares to trade (positive=buy, negative=sell)
        """
        delta_to_hedge = current_delta - self.target_delta
        return -delta_to_hedge

    def execute_hedge(
        self,
        portfolio: Portfolio,
        delta_to_hedge: float,
        spot_price: float,
        date: pd.Timestamp
    ):
        """
        Execute delta hedge trade.

        Args:
            portfolio: Portfolio to hedge
            delta_to_hedge: Delta amount to hedge
            spot_price: Current spot price
            date: Trade date
        """
        shares = self.calculate_hedge(delta_to_hedge)
        cost = shares * spot_price

        # Update underlying position
        self.underlying_position += shares

        # Record trade
        portfolio.record_trade(
            date=date,
            description=f"Delta hedge: {shares:.2f} shares",
            cash_flow=-cost
        )
