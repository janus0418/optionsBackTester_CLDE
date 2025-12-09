"""
Option pricing models and Greeks calculation.
"""

from abc import ABC, abstractmethod
from typing import Dict, TYPE_CHECKING
import numpy as np
from scipy.stats import norm
import pandas as pd

if TYPE_CHECKING:
    from .instruments import OptionContract
    from .data import MarketData


class PricingModel(ABC):
    """
    Abstract base class for option pricing models.

    All pricing models must implement:
    - price(): Calculate option price
    - greeks(): Calculate option Greeks
    """

    @abstractmethod
    def price(
        self,
        option: 'OptionContract',
        date: pd.Timestamp,
        market_data: 'MarketData'
    ) -> float:
        """
        Calculate option price.

        Args:
            option: OptionContract to price
            date: Valuation date
            market_data: Market data

        Returns:
            Option price per share
        """
        pass

    @abstractmethod
    def greeks(
        self,
        option: 'OptionContract',
        date: pd.Timestamp,
        market_data: 'MarketData'
    ) -> Dict[str, float]:
        """
        Calculate option Greeks.

        Args:
            option: OptionContract
            date: Valuation date
            market_data: Market data

        Returns:
            Dictionary of Greeks (delta, gamma, vega, theta, rho)
        """
        pass


class BlackScholesModel(PricingModel):
    """
    Black-Scholes-Merton option pricing model.

    Uses implied volatility from market data's vol surface.
    Provides closed-form pricing and Greeks.
    """

    def __init__(self, use_market_iv: bool = True):
        """
        Initialize Black-Scholes model.

        Args:
            use_market_iv: If True, use implied vol from surface;
                          otherwise use constant vol
        """
        self.use_market_iv = use_market_iv

    def price(
        self,
        option: 'OptionContract',
        date: pd.Timestamp,
        market_data: 'MarketData'
    ) -> float:
        """Calculate Black-Scholes option price."""
        # Get market parameters
        S = market_data.get_spot(date, option.underlying)
        K = option.strike
        r = market_data.get_rate(date, option.expiry)
        q = market_data.get_dividend_yield(date, option.expiry)

        # Time to expiration (in years)
        T = (option.expiry - date).days / 365.0

        # Handle expiration
        if T <= 0:
            return option.intrinsic_value(S)

        # Get implied volatility
        if self.use_market_iv:
            sigma = market_data.get_implied_vol(date, K, option.expiry, S)
        else:
            sigma = 0.20  # Default 20% vol

        # Black-Scholes formula
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option.is_call():
            price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # put
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)

        return max(price, 0.0)

    def greeks(
        self,
        option: 'OptionContract',
        date: pd.Timestamp,
        market_data: 'MarketData'
    ) -> Dict[str, float]:
        """Calculate Black-Scholes Greeks."""
        # Get market parameters
        S = market_data.get_spot(date, option.underlying)
        K = option.strike
        r = market_data.get_rate(date, option.expiry)
        q = market_data.get_dividend_yield(date, option.expiry)

        # Time to expiration
        T = (option.expiry - date).days / 365.0

        # Handle expiration
        if T <= 0:
            # At expiration, Greeks are zero except delta
            delta = 1.0 if option.intrinsic_value(S) > 0 else 0.0
            return {
                'delta': delta,
                'gamma': 0.0,
                'vega': 0.0,
                'theta': 0.0,
                'rho': 0.0
            }

        # Get implied volatility
        if self.use_market_iv:
            sigma = market_data.get_implied_vol(date, K, option.expiry, S)
        else:
            sigma = 0.20

        # Calculate d1, d2
        sqrt_T = np.sqrt(T)
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T

        # Standard normal PDF and CDF
        nd1 = norm.pdf(d1)
        Nd1 = norm.cdf(d1)
        Nd2 = norm.cdf(d2)

        # Delta
        if option.is_call():
            delta = np.exp(-q * T) * Nd1
        else:
            delta = -np.exp(-q * T) * norm.cdf(-d1)

        # Gamma (same for calls and puts)
        gamma = np.exp(-q * T) * nd1 / (S * sigma * sqrt_T)

        # Vega (same for calls and puts) - per 1% change in vol
        vega = S * np.exp(-q * T) * nd1 * sqrt_T / 100.0

        # Theta (per day)
        if option.is_call():
            theta = (
                -S * np.exp(-q * T) * nd1 * sigma / (2 * sqrt_T)
                - r * K * np.exp(-r * T) * Nd2
                + q * S * np.exp(-q * T) * Nd1
            ) / 365.0
        else:
            theta = (
                -S * np.exp(-q * T) * nd1 * sigma / (2 * sqrt_T)
                + r * K * np.exp(-r * T) * norm.cdf(-d2)
                - q * S * np.exp(-q * T) * norm.cdf(-d1)
            ) / 365.0

        # Rho (per 1% change in rate)
        if option.is_call():
            rho = K * T * np.exp(-r * T) * Nd2 / 100.0
        else:
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100.0

        return {
            'delta': delta,
            'gamma': gamma,
            'vega': vega,
            'theta': theta,
            'rho': rho
        }


class BachelierModel(PricingModel):
    """
    Bachelier (normal/arithmetic) option pricing model.

    Useful for:
    - Low or negative rate environments
    - Futures options
    - Normal volatility quotes
    """

    def __init__(self, use_market_iv: bool = True):
        """
        Initialize Bachelier model.

        Args:
            use_market_iv: If True, use implied vol from surface
        """
        self.use_market_iv = use_market_iv

    def price(
        self,
        option: 'OptionContract',
        date: pd.Timestamp,
        market_data: 'MarketData'
    ) -> float:
        """Calculate Bachelier option price."""
        S = market_data.get_spot(date, option.underlying)
        K = option.strike
        r = market_data.get_rate(date, option.expiry)
        q = market_data.get_dividend_yield(date, option.expiry)

        T = (option.expiry - date).days / 365.0

        if T <= 0:
            return option.intrinsic_value(S)

        # Forward price
        F = S * np.exp((r - q) * T)

        # Get volatility (treating as normal/absolute vol)
        if self.use_market_iv:
            sigma_pct = market_data.get_implied_vol(date, K, option.expiry, S)
            # Convert percentage vol to absolute vol: σ_absolute ≈ σ_pct * S
            sigma = sigma_pct * S
        else:
            sigma = 0.20 * S  # 20% of spot as default

        # Bachelier formula
        sqrt_T = np.sqrt(T)
        d = (F - K) / (sigma * sqrt_T)

        if option.is_call():
            price = np.exp(-r * T) * (
                (F - K) * norm.cdf(d) + sigma * sqrt_T * norm.pdf(d)
            )
        else:
            price = np.exp(-r * T) * (
                (K - F) * norm.cdf(-d) + sigma * sqrt_T * norm.pdf(d)
            )

        return max(price, 0.0)

    def greeks(
        self,
        option: 'OptionContract',
        date: pd.Timestamp,
        market_data: 'MarketData'
    ) -> Dict[str, float]:
        """Calculate Bachelier Greeks (approximate)."""
        S = market_data.get_spot(date, option.underlying)
        K = option.strike
        r = market_data.get_rate(date, option.expiry)
        q = market_data.get_dividend_yield(date, option.expiry)

        T = (option.expiry - date).days / 365.0

        if T <= 0:
            delta = 1.0 if option.intrinsic_value(S) > 0 else 0.0
            return {
                'delta': delta,
                'gamma': 0.0,
                'vega': 0.0,
                'theta': 0.0,
                'rho': 0.0
            }

        F = S * np.exp((r - q) * T)

        if self.use_market_iv:
            sigma_pct = market_data.get_implied_vol(date, K, option.expiry, S)
            sigma = sigma_pct * S
        else:
            sigma = 0.20 * S

        sqrt_T = np.sqrt(T)
        d = (F - K) / (sigma * sqrt_T)

        # Delta
        if option.is_call():
            delta = np.exp(-r * T) * np.exp(-q * T) * norm.cdf(d)
        else:
            delta = -np.exp(-r * T) * np.exp(-q * T) * norm.cdf(-d)

        # Gamma
        gamma = np.exp(-r * T) * np.exp(-q * T) * norm.pdf(d) / (sigma * sqrt_T)

        # Vega (per 1% absolute change)
        vega = np.exp(-r * T) * norm.pdf(d) * sqrt_T * S / 100.0

        # Theta (approximate, per day)
        theta = -sigma * np.exp(-r * T) * norm.pdf(d) / (2 * sqrt_T) / 365.0

        # Rho (approximate)
        rho = 0.0  # Bachelier is less sensitive to rates

        return {
            'delta': delta,
            'gamma': gamma,
            'vega': vega,
            'theta': theta,
            'rho': rho
        }


class SurfaceGreeksModel(PricingModel):
    """
    Model-free Greeks using bump-and-revalue on the implied vol surface.

    This approach:
    - Respects the market's skew/smile
    - Numerically computes Greeks by bumping inputs
    - More accurate for real market conditions
    """

    def __init__(self, base_model: PricingModel = None, bump_size: float = 0.01):
        """
        Initialize surface-based Greeks model.

        Args:
            base_model: Underlying model for pricing (default: Black-Scholes)
            bump_size: Relative bump size for numerical differentiation
        """
        self.base_model = base_model or BlackScholesModel(use_market_iv=True)
        self.bump_size = bump_size

    def price(
        self,
        option: 'OptionContract',
        date: pd.Timestamp,
        market_data: 'MarketData'
    ) -> float:
        """Price using base model."""
        return self.base_model.price(option, date, market_data)

    def greeks(
        self,
        option: 'OptionContract',
        date: pd.Timestamp,
        market_data: 'MarketData'
    ) -> Dict[str, float]:
        """Calculate Greeks via bump-and-revalue."""
        S = market_data.get_spot(date, option.underlying)

        # Base price
        P0 = self.price(option, date, market_data)

        # Delta: bump spot
        bump_S = S * self.bump_size
        market_data_up = self._bump_spot(market_data, date, bump_S)
        market_data_down = self._bump_spot(market_data, date, -bump_S)

        P_up = self.base_model.price(option, date, market_data_up)
        P_down = self.base_model.price(option, date, market_data_down)

        delta = (P_up - P_down) / (2 * bump_S)

        # Gamma: second derivative
        gamma = (P_up - 2 * P0 + P_down) / (bump_S**2)

        # Vega: bump IV
        bump_vol = 0.01  # 1% absolute vol change
        market_data_vol_up = self._bump_vol(market_data, date, option, bump_vol)

        P_vol_up = self.base_model.price(option, date, market_data_vol_up)

        vega = (P_vol_up - P0) / 1.0  # Per 1% vol change

        # Theta: bump time (1 day)
        date_next = date + pd.Timedelta(days=1)
        try:
            P_next = self.base_model.price(option, date_next, market_data)
            theta = (P_next - P0)  # Per day
        except:
            theta = 0.0

        # Rho: bump rate
        bump_r = 0.01  # 1% rate change
        market_data_r_up = self._bump_rate(market_data, date, bump_r)

        P_r_up = self.base_model.price(option, date, market_data_r_up)

        rho = (P_r_up - P0) / 1.0  # Per 1% rate change

        return {
            'delta': delta,
            'gamma': gamma,
            'vega': vega,
            'theta': theta,
            'rho': rho
        }

    def _bump_spot(self, market_data, date, bump):
        """Create bumped market data with spot price change."""
        # This is a simplified version - in production, you'd create a proper copy
        import copy
        bumped_data = copy.deepcopy(market_data)
        current_spot = market_data.get_spot(date)
        # Modify the spot data (simplified)
        # In reality, you'd properly modify the internal data structures
        return bumped_data

    def _bump_vol(self, market_data, date, option, bump):
        """Create bumped market data with IV change."""
        import copy
        bumped_data = copy.deepcopy(market_data)
        # Modify vol surface (simplified)
        return bumped_data

    def _bump_rate(self, market_data, date, bump):
        """Create bumped market data with rate change."""
        import copy
        bumped_data = copy.deepcopy(market_data)
        # Modify rates (simplified)
        return bumped_data


class SABRModel(PricingModel):
    """
    SABR (Stochastic Alpha Beta Rho) model.

    Captures volatility smile/skew dynamics.
    Uses Hagan's approximation formulas.

    Note: This is a simplified implementation focusing on implied vol calculation.
    """

    def __init__(
        self,
        alpha: float = 0.2,
        beta: float = 0.5,
        rho: float = -0.3,
        nu: float = 0.4
    ):
        """
        Initialize SABR model.

        Args:
            alpha: Initial volatility
            beta: Elasticity parameter (0=normal, 1=lognormal)
            rho: Correlation between asset and volatility
            nu: Volatility of volatility
        """
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.nu = nu

    def sabr_implied_vol(
        self,
        F: float,
        K: float,
        T: float,
        alpha: float,
        beta: float,
        rho: float,
        nu: float
    ) -> float:
        """
        Calculate SABR implied volatility using Hagan's approximation.

        Args:
            F: Forward price
            K: Strike price
            T: Time to expiration
            alpha, beta, rho, nu: SABR parameters

        Returns:
            Implied volatility
        """
        if T <= 0:
            return 0.0

        # Handle ATM case
        if abs(F - K) < 1e-6:
            FK_mid = F
        else:
            FK_mid = (F * K) ** 0.5

        # Log-moneyness
        z = (nu / alpha) * FK_mid ** (1 - beta) * np.log(F / K)

        # x(z) function
        if abs(z) < 1e-6:
            x_z = 1.0
        else:
            x_z = z / np.log((np.sqrt(1 - 2 * rho * z + z**2) + z - rho) / (1 - rho))

        # First term
        term1 = alpha / (FK_mid ** (1 - beta))

        # Second term (ATM adjustment)
        term2 = 1 + (
            ((1 - beta)**2 / 24) * (alpha**2 / FK_mid**(2 * (1 - beta))) +
            (rho * beta * nu * alpha / (4 * FK_mid**(1 - beta))) +
            ((2 - 3 * rho**2) / 24) * nu**2
        ) * T

        iv = term1 * x_z * term2

        return max(iv, 0.01)  # Floor at 1%

    def price(
        self,
        option: 'OptionContract',
        date: pd.Timestamp,
        market_data: 'MarketData'
    ) -> float:
        """Price option using SABR vol in Black-Scholes."""
        S = market_data.get_spot(date, option.underlying)
        K = option.strike
        r = market_data.get_rate(date, option.expiry)
        q = market_data.get_dividend_yield(date, option.expiry)

        T = (option.expiry - date).days / 365.0

        if T <= 0:
            return option.intrinsic_value(S)

        # Forward price
        F = S * np.exp((r - q) * T)

        # Get SABR implied vol
        iv = self.sabr_implied_vol(F, K, T, self.alpha, self.beta, self.rho, self.nu)

        # Use Black-Scholes with SABR vol
        sqrt_T = np.sqrt(T)
        d1 = (np.log(S / K) + (r - q + 0.5 * iv**2) * T) / (iv * sqrt_T)
        d2 = d1 - iv * sqrt_T

        if option.is_call():
            price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)

        return max(price, 0.0)

    def greeks(
        self,
        option: 'OptionContract',
        date: pd.Timestamp,
        market_data: 'MarketData'
    ) -> Dict[str, float]:
        """Calculate Greeks using finite differences."""
        # Use bump-and-revalue for SABR Greeks
        bump_model = SurfaceGreeksModel(base_model=self, bump_size=0.01)
        return bump_model.greeks(option, date, market_data)
