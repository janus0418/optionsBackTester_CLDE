"""
Market data and volatility surface management.
"""

from typing import Optional, Union, Dict, Callable
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import interpolate
from dataclasses import dataclass


class VolSurface:
    """
    Implied volatility surface with interpolation capabilities.

    Supports:
    - Strike-based interpolation
    - Expiry-based interpolation
    - Delta-based interpolation
    - Moneyness-based interpolation
    """

    def __init__(
        self,
        date: pd.Timestamp,
        underlying: str,
        vol_data: pd.DataFrame,
        interpolation_method: str = 'cubic'
    ):
        """
        Initialize volatility surface.

        Args:
            date: Reference date for the surface
            underlying: Underlying asset ticker
            vol_data: DataFrame with columns ['strike', 'expiry', 'implied_vol']
                     or ['delta', 'expiry', 'implied_vol']
            interpolation_method: Method for interpolation ('linear', 'cubic', 'rbf')
        """
        self.date = date
        self.underlying = underlying
        self.vol_data = vol_data.copy()
        self.interpolation_method = interpolation_method

        # Convert expiry to days if datetime
        if 'expiry' in self.vol_data.columns:
            if isinstance(self.vol_data['expiry'].iloc[0], (datetime, pd.Timestamp)):
                self.vol_data['days_to_expiry'] = (
                    self.vol_data['expiry'] - date
                ).dt.days
            else:
                self.vol_data['days_to_expiry'] = self.vol_data['expiry']

        self._build_interpolator()

    def _build_interpolator(self):
        """Build 2D interpolation function for the vol surface."""
        if 'strike' in self.vol_data.columns:
            x = self.vol_data['strike'].values
            y = self.vol_data['days_to_expiry'].values
            z = self.vol_data['implied_vol'].values

            if self.interpolation_method == 'cubic':
                self.interpolator = interpolate.Rbf(x, y, z, function='cubic', smooth=0.1)
            elif self.interpolation_method == 'linear':
                self.interpolator = interpolate.LinearNDInterpolator(
                    list(zip(x, y)), z, fill_value=np.nan
                )
            else:
                self.interpolator = interpolate.Rbf(x, y, z, function='multiquadric')
        else:
            # Delta-based surface
            self.interpolator = None

    def iv(
        self,
        strike: Optional[float] = None,
        expiry: Optional[Union[pd.Timestamp, int]] = None,
        spot: Optional[float] = None
    ) -> float:
        """
        Get implied volatility for a given strike and expiry.

        Args:
            strike: Strike price
            expiry: Expiry date or days to expiry
            spot: Current spot price (for moneyness calculation)

        Returns:
            Implied volatility as a decimal (e.g., 0.20 for 20%)
        """
        if isinstance(expiry, pd.Timestamp):
            days_to_expiry = (expiry - self.date).days
        else:
            days_to_expiry = expiry

        if days_to_expiry <= 0:
            return 0.0

        try:
            iv_value = float(self.interpolator(strike, days_to_expiry))
            # Clamp to reasonable values
            return np.clip(iv_value, 0.01, 5.0)
        except Exception as e:
            # Fallback to nearest neighbor
            distances = np.sqrt(
                (self.vol_data['strike'] - strike)**2 +
                (self.vol_data['days_to_expiry'] - days_to_expiry)**2
            )
            nearest_idx = distances.idxmin()
            return float(self.vol_data.loc[nearest_idx, 'implied_vol'])

    def iv_by_delta(self, delta: float, expiry: Union[pd.Timestamp, int]) -> float:
        """
        Get implied volatility for a given delta and expiry.

        Args:
            delta: Option delta (0 to 1 for calls, -1 to 0 for puts)
            expiry: Expiry date or days to expiry

        Returns:
            Implied volatility
        """
        if 'delta' not in self.vol_data.columns:
            raise ValueError("Delta-based interpolation not supported for this surface")

        if isinstance(expiry, pd.Timestamp):
            days_to_expiry = (expiry - self.date).days
        else:
            days_to_expiry = expiry

        # Find closest delta and expiry in the data
        mask = self.vol_data['days_to_expiry'] == days_to_expiry
        if not mask.any():
            # Interpolate across expiries
            mask = True

        filtered = self.vol_data[mask]
        delta_diff = np.abs(filtered['delta'] - delta)
        nearest_idx = delta_diff.idxmin()
        return float(filtered.loc[nearest_idx, 'implied_vol'])

    def smile(self, expiry: Union[pd.Timestamp, int], strikes: np.ndarray) -> np.ndarray:
        """
        Get the volatility smile for a given expiry across multiple strikes.

        Args:
            expiry: Expiry date or days to expiry
            strikes: Array of strike prices

        Returns:
            Array of implied volatilities
        """
        return np.array([self.iv(strike, expiry) for strike in strikes])


class MarketData:
    """
    Comprehensive market data container for backtesting.

    Manages:
    - Spot prices
    - Risk-free rates
    - Dividend yields
    - Implied volatility surfaces
    - Transaction costs
    """

    def __init__(
        self,
        spot_data: pd.DataFrame,
        vol_surfaces: Optional[Dict[pd.Timestamp, VolSurface]] = None,
        risk_free_rates: Optional[pd.Series] = None,
        dividend_yields: Optional[pd.Series] = None,
        underlying: str = "SPY"
    ):
        """
        Initialize market data.

        Args:
            spot_data: DataFrame with datetime index and 'close' column (or underlying ticker column)
            vol_surfaces: Dict mapping dates to VolSurface objects
            risk_free_rates: Series of risk-free rates (indexed by date)
            dividend_yields: Series of dividend yields (indexed by date)
            underlying: Underlying asset ticker
        """
        self.underlying = underlying

        # Ensure datetime index
        if not isinstance(spot_data.index, pd.DatetimeIndex):
            spot_data.index = pd.to_datetime(spot_data.index)

        self.spot_data = spot_data.sort_index()
        self.time_index = self.spot_data.index

        # Set up vol surfaces
        self.vol_surfaces = vol_surfaces or {}

        # Set up rates and dividends
        if risk_free_rates is None:
            self.risk_free_rates = pd.Series(0.05, index=self.time_index)
        else:
            self.risk_free_rates = risk_free_rates.reindex(self.time_index, method='ffill')

        if dividend_yields is None:
            self.dividend_yields = pd.Series(0.0, index=self.time_index)
        else:
            self.dividend_yields = dividend_yields.reindex(self.time_index, method='ffill')

    def get_spot(self, date: pd.Timestamp, underlying: Optional[str] = None) -> float:
        """Get spot price for a given date."""
        underlying = underlying or self.underlying

        # Find nearest date if exact date not available
        if date not in self.spot_data.index:
            nearest_date = self.spot_data.index[self.spot_data.index <= date][-1]
            date = nearest_date

        if underlying in self.spot_data.columns:
            return float(self.spot_data.loc[date, underlying])
        elif 'close' in self.spot_data.columns:
            return float(self.spot_data.loc[date, 'close'])
        else:
            return float(self.spot_data.loc[date].iloc[0])

    def get_forward(
        self,
        date: pd.Timestamp,
        expiry: pd.Timestamp,
        underlying: Optional[str] = None
    ) -> float:
        """
        Calculate forward price.

        F = S * exp((r - q) * T)
        """
        spot = self.get_spot(date, underlying)
        r = self.get_rate(date, expiry)
        q = self.get_dividend_yield(date, expiry)
        T = (expiry - date).days / 365.0

        return spot * np.exp((r - q) * T)

    def get_rate(
        self,
        date: pd.Timestamp,
        tenor: Optional[Union[pd.Timestamp, int]] = None
    ) -> float:
        """Get risk-free rate for a given date and tenor."""
        if date not in self.risk_free_rates.index:
            nearest_date = self.risk_free_rates.index[
                self.risk_free_rates.index <= date
            ][-1]
            date = nearest_date

        return float(self.risk_free_rates.loc[date])

    def get_dividend_yield(
        self,
        date: pd.Timestamp,
        tenor: Optional[Union[pd.Timestamp, int]] = None
    ) -> float:
        """Get dividend yield for a given date and tenor."""
        if date not in self.dividend_yields.index:
            nearest_date = self.dividend_yields.index[
                self.dividend_yields.index <= date
            ][-1]
            date = nearest_date

        return float(self.dividend_yields.loc[date])

    def get_implied_vol(
        self,
        date: pd.Timestamp,
        strike: float,
        expiry: pd.Timestamp,
        spot: Optional[float] = None
    ) -> float:
        """Get implied volatility from the surface."""
        # Find the closest vol surface date
        if date in self.vol_surfaces:
            surface = self.vol_surfaces[date]
        else:
            # Find nearest surface
            surface_dates = sorted(self.vol_surfaces.keys())
            if not surface_dates:
                # Default flat vol if no surface available
                return 0.20

            nearest_date = min(surface_dates, key=lambda d: abs((d - date).days))
            surface = self.vol_surfaces[nearest_date]

        spot = spot or self.get_spot(date)
        return surface.iv(strike, expiry, spot)

    def slice(
        self,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp
    ) -> 'MarketData':
        """Create a slice of market data for a specific date range."""
        mask = (self.spot_data.index >= start_date) & (self.spot_data.index <= end_date)
        sliced_spot = self.spot_data[mask]

        sliced_surfaces = {
            k: v for k, v in self.vol_surfaces.items()
            if start_date <= k <= end_date
        }

        return MarketData(
            spot_data=sliced_spot,
            vol_surfaces=sliced_surfaces,
            risk_free_rates=self.risk_free_rates[mask],
            dividend_yields=self.dividend_yields[mask],
            underlying=self.underlying
        )

    @classmethod
    def from_yahoo(
        cls,
        ticker: str,
        start_date: str,
        end_date: str,
        default_iv: float = 0.20
    ) -> 'MarketData':
        """
        Create MarketData from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            default_iv: Default implied volatility to use

        Returns:
            MarketData instance
        """
        import yfinance as yf

        data = yf.download(ticker, start=start_date, end=end_date, progress=False)

        # Create simple flat vol surfaces
        vol_surfaces = {}
        for date in data.index:
            # Create a simple flat surface
            strikes = np.linspace(data.loc[date, 'Close'] * 0.5,
                                 data.loc[date, 'Close'] * 1.5, 20)
            expiries = [1, 7, 14, 30, 60, 90, 180, 365]  # days

            vol_df = pd.DataFrame([
                {'strike': s, 'expiry': e, 'implied_vol': default_iv}
                for s in strikes for e in expiries
            ])

            vol_surfaces[pd.Timestamp(date)] = VolSurface(
                date=pd.Timestamp(date),
                underlying=ticker,
                vol_data=vol_df
            )

        return cls(
            spot_data=data[['Close']].rename(columns={'Close': 'close'}),
            vol_surfaces=vol_surfaces,
            underlying=ticker
        )
