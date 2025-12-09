"""
Options instruments and strategy definitions.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, TYPE_CHECKING
from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
import numpy as np

if TYPE_CHECKING:
    from .data import MarketData
    from .models import PricingModel


@dataclass
class OptionContract:
    """
    Represents a single option contract.

    Attributes:
        underlying: Ticker symbol of the underlying asset
        option_type: 'call' or 'put'
        style: 'european' or 'american'
        strike: Strike price
        expiry: Expiration date
        contract_size: Number of shares per contract (typically 100)
    """
    underlying: str
    option_type: str  # 'call' or 'put'
    style: str = 'european'  # 'european' or 'american'
    strike: float = 100.0
    expiry: pd.Timestamp = None
    contract_size: float = 100.0

    def __post_init__(self):
        """Validate inputs."""
        if self.option_type not in ['call', 'put']:
            raise ValueError(f"Invalid option_type: {self.option_type}")
        if self.style not in ['european', 'american']:
            raise ValueError(f"Invalid style: {self.style}")
        if self.strike <= 0:
            raise ValueError(f"Strike must be positive: {self.strike}")

    def __repr__(self) -> str:
        """String representation."""
        return (f"Option({self.option_type.upper()} {self.underlying} "
                f"${self.strike:.2f} {self.expiry.strftime('%Y-%m-%d')})")

    def is_call(self) -> bool:
        """Check if option is a call."""
        return self.option_type == 'call'

    def is_put(self) -> bool:
        """Check if option is a put."""
        return self.option_type == 'put'

    def intrinsic_value(self, spot: float) -> float:
        """
        Calculate intrinsic value.

        Args:
            spot: Current spot price of underlying

        Returns:
            Intrinsic value per share
        """
        if self.is_call():
            return max(spot - self.strike, 0.0)
        else:
            return max(self.strike - spot, 0.0)

    def payoff(self, spot: float) -> float:
        """
        Calculate payoff at expiration.

        Args:
            spot: Spot price at expiration

        Returns:
            Payoff per share
        """
        return self.intrinsic_value(spot)


class OptionLeg:
    """
    Represents a position in an option contract (a leg of a strategy).

    Attributes:
        contract: The OptionContract
        quantity: Number of contracts (positive for long, negative for short)
        entry_price: Price paid/received per contract at entry (optional)
    """

    def __init__(
        self,
        contract: OptionContract,
        quantity: float,
        entry_price: Optional[float] = None
    ):
        """
        Initialize option leg.

        Args:
            contract: OptionContract instance
            quantity: Number of contracts (positive=long, negative=short)
            entry_price: Entry price per contract
        """
        self.contract = contract
        self.quantity = quantity
        self.entry_price = entry_price

    def __repr__(self) -> str:
        """String representation."""
        direction = "LONG" if self.quantity > 0 else "SHORT"
        return (f"{direction} {abs(self.quantity):.2f}x {self.contract}")

    def is_long(self) -> bool:
        """Check if leg is long."""
        return self.quantity > 0

    def is_short(self) -> bool:
        """Check if leg is short."""
        return self.quantity < 0

    def price(
        self,
        date: pd.Timestamp,
        market_data: 'MarketData',
        model: 'PricingModel'
    ) -> float:
        """
        Calculate the mark-to-market price of this leg.

        Args:
            date: Valuation date
            market_data: Market data
            model: Pricing model

        Returns:
            Total value of the leg (price * quantity * contract_size)
        """
        option_price = model.price(self.contract, date, market_data)
        return option_price * self.quantity * self.contract.contract_size

    def greeks(
        self,
        date: pd.Timestamp,
        market_data: 'MarketData',
        model: 'PricingModel'
    ) -> Dict[str, float]:
        """
        Calculate Greeks for this leg.

        Args:
            date: Valuation date
            market_data: Market data
            model: Pricing model

        Returns:
            Dictionary of Greeks (scaled by quantity and contract size)
        """
        greeks = model.greeks(self.contract, date, market_data)

        # Scale by quantity and contract size
        scaled_greeks = {
            key: value * self.quantity * self.contract.contract_size
            for key, value in greeks.items()
        }
        return scaled_greeks

    def payoff(self, spot: float) -> float:
        """
        Calculate total payoff at expiration.

        Args:
            spot: Spot price at expiration

        Returns:
            Total payoff (including quantity and contract size)
        """
        return (self.contract.payoff(spot) * self.quantity *
                self.contract.contract_size)


class OptionStrategy(ABC):
    """
    Abstract base class for option strategies.

    A strategy is a collection of option legs (and potentially underlying positions).
    """

    def __init__(self, name: str):
        """
        Initialize strategy.

        Args:
            name: Strategy name
        """
        self.name = name
        self.legs: List[OptionLeg] = []

    def add_leg(self, leg: OptionLeg):
        """Add a leg to the strategy."""
        self.legs.append(leg)

    def remove_leg(self, index: int):
        """Remove a leg by index."""
        if 0 <= index < len(self.legs):
            self.legs.pop(index)

    def value(
        self,
        date: pd.Timestamp,
        market_data: 'MarketData',
        model: 'PricingModel'
    ) -> float:
        """
        Calculate total value of the strategy.

        Args:
            date: Valuation date
            market_data: Market data
            model: Pricing model

        Returns:
            Total strategy value
        """
        return sum(leg.price(date, market_data, model) for leg in self.legs)

    def greeks(
        self,
        date: pd.Timestamp,
        market_data: 'MarketData',
        model: 'PricingModel'
    ) -> Dict[str, float]:
        """
        Calculate aggregated Greeks for the strategy.

        Args:
            date: Valuation date
            market_data: Market data
            model: Pricing model

        Returns:
            Dictionary of aggregated Greeks
        """
        if not self.legs:
            return {'delta': 0.0, 'gamma': 0.0, 'vega': 0.0,
                   'theta': 0.0, 'rho': 0.0}

        # Sum up Greeks from all legs
        aggregated = {}
        for leg in self.legs:
            leg_greeks = leg.greeks(date, market_data, model)
            for key, value in leg_greeks.items():
                aggregated[key] = aggregated.get(key, 0.0) + value

        return aggregated

    def payoff(
        self,
        spot: float,
        at_expiry: bool = True
    ) -> float:
        """
        Calculate strategy payoff.

        Args:
            spot: Spot price
            at_expiry: If True, use expiration payoff; else use current value

        Returns:
            Strategy payoff
        """
        if at_expiry:
            return sum(leg.payoff(spot) for leg in self.legs)
        else:
            raise NotImplementedError(
                "Non-expiry payoff requires pricing model")

    def payoff_curve(
        self,
        spot_range: Optional[np.ndarray] = None,
        num_points: int = 100
    ) -> tuple:
        """
        Generate payoff curve at expiration.

        Args:
            spot_range: Array of spot prices (if None, auto-generate)
            num_points: Number of points to generate

        Returns:
            Tuple of (spot_prices, payoffs)
        """
        if spot_range is None:
            # Auto-generate range based on strikes
            strikes = [leg.contract.strike for leg in self.legs]
            min_strike = min(strikes)
            max_strike = max(strikes)
            spot_range = np.linspace(
                min_strike * 0.5, max_strike * 1.5, num_points
            )

        payoffs = np.array([self.payoff(spot) for spot in spot_range])
        return spot_range, payoffs

    def __repr__(self) -> str:
        """String representation."""
        legs_str = "\n  ".join(str(leg) for leg in self.legs)
        return f"{self.name}:\n  {legs_str}"


class Portfolio:
    """
    Portfolio of option strategies and cash.

    Manages:
    - Multiple strategies
    - Cash balance
    - Trade history
    - Position tracking
    """

    def __init__(self, initial_cash: float = 100000.0):
        """
        Initialize portfolio.

        Args:
            initial_cash: Initial cash balance
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.strategies: List[OptionStrategy] = []
        self.trade_history: List[Dict] = []

    def add_strategy(self, strategy: OptionStrategy):
        """Add a strategy to the portfolio."""
        self.strategies.append(strategy)

    def remove_strategy(self, index: int):
        """Remove a strategy by index."""
        if 0 <= index < len(self.strategies):
            self.strategies.pop(index)

    def value(
        self,
        date: pd.Timestamp,
        market_data: 'MarketData',
        model: 'PricingModel'
    ) -> float:
        """
        Calculate total portfolio value (cash + strategies).

        Args:
            date: Valuation date
            market_data: Market data
            model: Pricing model

        Returns:
            Total portfolio value
        """
        strategies_value = sum(
            strategy.value(date, market_data, model)
            for strategy in self.strategies
        )
        return self.cash + strategies_value

    def greeks(
        self,
        date: pd.Timestamp,
        market_data: 'MarketData',
        model: 'PricingModel'
    ) -> Dict[str, float]:
        """
        Calculate portfolio-aggregated Greeks.

        Args:
            date: Valuation date
            market_data: Market data
            model: Pricing model

        Returns:
            Dictionary of aggregated Greeks
        """
        aggregated = {'delta': 0.0, 'gamma': 0.0, 'vega': 0.0,
                     'theta': 0.0, 'rho': 0.0}

        for strategy in self.strategies:
            strategy_greeks = strategy.greeks(date, market_data, model)
            for key in aggregated:
                aggregated[key] += strategy_greeks.get(key, 0.0)

        return aggregated

    def record_trade(
        self,
        date: pd.Timestamp,
        description: str,
        cash_flow: float,
        strategy_index: Optional[int] = None
    ):
        """
        Record a trade in the portfolio.

        Args:
            date: Trade date
            description: Trade description
            cash_flow: Cash flow (positive for inflow, negative for outflow)
            strategy_index: Index of associated strategy (if any)
        """
        self.cash += cash_flow
        self.trade_history.append({
            'date': date,
            'description': description,
            'cash_flow': cash_flow,
            'strategy_index': strategy_index,
            'cash_balance': self.cash
        })

    def get_trade_history(self) -> pd.DataFrame:
        """Get trade history as DataFrame."""
        if not self.trade_history:
            return pd.DataFrame()
        return pd.DataFrame(self.trade_history)

    def __repr__(self) -> str:
        """String representation."""
        return (f"Portfolio(cash=${self.cash:,.2f}, "
                f"strategies={len(self.strategies)})")


# Concrete strategy implementations

class CalendarSpreadStrategy(OptionStrategy):
    """Calendar spread: same strike, different expiries."""

    def __init__(
        self,
        underlying: str,
        strike: float,
        near_expiry: pd.Timestamp,
        far_expiry: pd.Timestamp,
        option_type: str = 'call',
        quantity: float = 1.0
    ):
        """
        Create a calendar spread.

        Args:
            underlying: Underlying ticker
            strike: Strike price
            near_expiry: Near-term expiry date
            far_expiry: Far-term expiry date
            option_type: 'call' or 'put'
            quantity: Number of spreads
        """
        super().__init__(f"Calendar Spread {strike}")

        # Short near-term option
        near_contract = OptionContract(
            underlying=underlying,
            option_type=option_type,
            strike=strike,
            expiry=near_expiry
        )
        self.add_leg(OptionLeg(near_contract, -quantity))

        # Long far-term option
        far_contract = OptionContract(
            underlying=underlying,
            option_type=option_type,
            strike=strike,
            expiry=far_expiry
        )
        self.add_leg(OptionLeg(far_contract, quantity))


class VerticalSpreadStrategy(OptionStrategy):
    """Vertical spread: different strikes, same expiry."""

    def __init__(
        self,
        underlying: str,
        lower_strike: float,
        upper_strike: float,
        expiry: pd.Timestamp,
        option_type: str = 'call',
        spread_type: str = 'debit',  # 'debit' or 'credit'
        quantity: float = 1.0
    ):
        """
        Create a vertical spread.

        Args:
            underlying: Underlying ticker
            lower_strike: Lower strike price
            upper_strike: Upper strike price
            expiry: Expiry date
            option_type: 'call' or 'put'
            spread_type: 'debit' (bull call/bear put) or 'credit' (bear call/bull put)
            quantity: Number of spreads
        """
        super().__init__(f"{spread_type.capitalize()} Vertical Spread")

        lower_contract = OptionContract(
            underlying=underlying,
            option_type=option_type,
            strike=lower_strike,
            expiry=expiry
        )

        upper_contract = OptionContract(
            underlying=underlying,
            option_type=option_type,
            strike=upper_strike,
            expiry=expiry
        )

        if spread_type == 'debit':
            # Buy lower strike (call) or higher strike (put)
            if option_type == 'call':
                self.add_leg(OptionLeg(lower_contract, quantity))
                self.add_leg(OptionLeg(upper_contract, -quantity))
            else:
                self.add_leg(OptionLeg(upper_contract, quantity))
                self.add_leg(OptionLeg(lower_contract, -quantity))
        else:  # credit spread
            # Sell lower strike (call) or higher strike (put)
            if option_type == 'call':
                self.add_leg(OptionLeg(lower_contract, -quantity))
                self.add_leg(OptionLeg(upper_contract, quantity))
            else:
                self.add_leg(OptionLeg(upper_contract, -quantity))
                self.add_leg(OptionLeg(lower_contract, quantity))


class ButterflyStrategy(OptionStrategy):
    """Butterfly spread: 3 strikes."""

    def __init__(
        self,
        underlying: str,
        lower_strike: float,
        middle_strike: float,
        upper_strike: float,
        expiry: pd.Timestamp,
        option_type: str = 'call',
        quantity: float = 1.0
    ):
        """
        Create a butterfly spread.

        Args:
            underlying: Underlying ticker
            lower_strike: Lower strike
            middle_strike: Middle strike (ATM typically)
            upper_strike: Upper strike
            expiry: Expiry date
            option_type: 'call' or 'put'
            quantity: Number of butterflies
        """
        super().__init__(f"Butterfly {middle_strike}")

        lower_contract = OptionContract(
            underlying=underlying,
            option_type=option_type,
            strike=lower_strike,
            expiry=expiry
        )

        middle_contract = OptionContract(
            underlying=underlying,
            option_type=option_type,
            strike=middle_strike,
            expiry=expiry
        )

        upper_contract = OptionContract(
            underlying=underlying,
            option_type=option_type,
            strike=upper_strike,
            expiry=expiry
        )

        # Long 1 lower, short 2 middle, long 1 upper
        self.add_leg(OptionLeg(lower_contract, quantity))
        self.add_leg(OptionLeg(middle_contract, -2 * quantity))
        self.add_leg(OptionLeg(upper_contract, quantity))


class IronCondorStrategy(OptionStrategy):
    """Iron condor: 4 strikes (OTM put spread + OTM call spread)."""

    def __init__(
        self,
        underlying: str,
        put_lower_strike: float,
        put_upper_strike: float,
        call_lower_strike: float,
        call_upper_strike: float,
        expiry: pd.Timestamp,
        quantity: float = 1.0
    ):
        """
        Create an iron condor.

        Args:
            underlying: Underlying ticker
            put_lower_strike: Long put strike (lowest)
            put_upper_strike: Short put strike
            call_lower_strike: Short call strike
            call_upper_strike: Long call strike (highest)
            expiry: Expiry date
            quantity: Number of condors
        """
        super().__init__(f"Iron Condor")

        # OTM put spread (credit)
        long_put = OptionContract(
            underlying=underlying,
            option_type='put',
            strike=put_lower_strike,
            expiry=expiry
        )
        short_put = OptionContract(
            underlying=underlying,
            option_type='put',
            strike=put_upper_strike,
            expiry=expiry
        )

        # OTM call spread (credit)
        short_call = OptionContract(
            underlying=underlying,
            option_type='call',
            strike=call_lower_strike,
            expiry=expiry
        )
        long_call = OptionContract(
            underlying=underlying,
            option_type='call',
            strike=call_upper_strike,
            expiry=expiry
        )

        # Build the condor
        self.add_leg(OptionLeg(long_put, quantity))
        self.add_leg(OptionLeg(short_put, -quantity))
        self.add_leg(OptionLeg(short_call, -quantity))
        self.add_leg(OptionLeg(long_call, quantity))


class StraddleStrategy(OptionStrategy):
    """Straddle: long/short call and put at same strike."""

    def __init__(
        self,
        underlying: str,
        strike: float,
        expiry: pd.Timestamp,
        direction: str = 'long',  # 'long' or 'short'
        quantity: float = 1.0
    ):
        """
        Create a straddle.

        Args:
            underlying: Underlying ticker
            strike: Strike price (typically ATM)
            expiry: Expiry date
            direction: 'long' or 'short'
            quantity: Number of straddles
        """
        super().__init__(f"{direction.capitalize()} Straddle {strike}")

        call_contract = OptionContract(
            underlying=underlying,
            option_type='call',
            strike=strike,
            expiry=expiry
        )

        put_contract = OptionContract(
            underlying=underlying,
            option_type='put',
            strike=strike,
            expiry=expiry
        )

        sign = 1.0 if direction == 'long' else -1.0
        self.add_leg(OptionLeg(call_contract, sign * quantity))
        self.add_leg(OptionLeg(put_contract, sign * quantity))


class StrangleStrategy(OptionStrategy):
    """Strangle: long/short OTM call and put at different strikes."""

    def __init__(
        self,
        underlying: str,
        put_strike: float,
        call_strike: float,
        expiry: pd.Timestamp,
        direction: str = 'long',  # 'long' or 'short'
        quantity: float = 1.0
    ):
        """
        Create a strangle.

        Args:
            underlying: Underlying ticker
            put_strike: Put strike (below spot)
            call_strike: Call strike (above spot)
            expiry: Expiry date
            direction: 'long' or 'short'
            quantity: Number of strangles
        """
        super().__init__(f"{direction.capitalize()} Strangle")

        call_contract = OptionContract(
            underlying=underlying,
            option_type='call',
            strike=call_strike,
            expiry=expiry
        )

        put_contract = OptionContract(
            underlying=underlying,
            option_type='put',
            strike=put_strike,
            expiry=expiry
        )

        sign = 1.0 if direction == 'long' else -1.0
        self.add_leg(OptionLeg(call_contract, sign * quantity))
        self.add_leg(OptionLeg(put_contract, sign * quantity))
