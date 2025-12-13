"""
Flexible data loaders for various options data sources.

Supports:
- DoltHub databases (via dolt SQL)
- CSV files
- Parquet files
- SQL databases (PostgreSQL, MySQL, SQLite)
- Custom data sources via adapter pattern
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Tuple
import pandas as pd
import numpy as np
from pathlib import Path
import subprocess
import json

from .data import MarketData, VolSurface


class DataSourceAdapter(ABC):
    """
    Abstract base class for data source adapters.

    All data adapters must implement:
    - load_spot_data(): Load underlying price data
    - load_option_data(): Load options chain data
    - load_volatility_data(): Load volatility surface data (optional)
    """

    @abstractmethod
    def load_spot_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Load spot price data.

        Args:
            ticker: Underlying ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with datetime index and columns: open, high, low, close, volume
        """
        pass

    @abstractmethod
    def load_option_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        option_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load options chain data.

        Args:
            ticker: Underlying ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            option_type: Filter by 'call' or 'put' (None = both)

        Returns:
            DataFrame with columns: date, strike, expiration, option_type,
                                   bid, ask, volume, open_interest, iv, greeks...
        """
        pass

    def load_volatility_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Load volatility surface/history data (optional).

        Args:
            ticker: Underlying ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with volatility data or None if not available
        """
        return None


class DoltHubAdapter(DataSourceAdapter):
    """
    Adapter for loading data from DoltHub databases.

    Specifically designed for post-no-preference/options database.
    """

    def __init__(self, database_path: str):
        """
        Initialize DoltHub adapter.

        Args:
            database_path: Path to cloned dolt database directory
        """
        self.database_path = Path(database_path)
        if not self.database_path.exists():
            raise ValueError(f"Database path does not exist: {database_path}")

    def _execute_sql(self, query: str) -> pd.DataFrame:
        """Execute SQL query using dolt and return DataFrame."""
        result = subprocess.run(
            ['dolt', 'sql', '-q', query, '-r', 'json'],
            cwd=str(self.database_path),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Dolt SQL error: {result.stderr}")

        # Parse JSON output
        if result.stdout.strip():
            data = json.loads(result.stdout)
            if data.get('rows'):
                return pd.DataFrame(data['rows'])

        return pd.DataFrame()

    def load_spot_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Load spot data from options dataset.

        Note: DoltHub options database doesn't have dedicated spot data,
        so we'll use underlying price info from ATM options or rely on
        external sources like yfinance.
        """
        # For now, use yfinance as fallback
        import yfinance as yf
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)

        if data.empty:
            raise ValueError(f"No spot data available for {ticker}")

        # Standardize column names
        # Handle both single-ticker and multi-ticker downloads
        if isinstance(data.columns, pd.MultiIndex):
            # Multi-ticker format
            df = pd.DataFrame({
                'open': data[('Open', ticker)],
                'high': data[('High', ticker)],
                'low': data[('Low', ticker)],
                'close': data[('Close', ticker)],
                'volume': data[('Volume', ticker)]
            })
        else:
            # Single ticker format
            df = pd.DataFrame({
                'open': data['Open'],
                'high': data['High'],
                'low': data['Low'],
                'close': data['Close'],
                'volume': data['Volume']
            })

        return df

    def load_option_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        option_type: Optional[str] = None
    ) -> pd.DataFrame:
        """Load options data from DoltHub option_chain table."""
        # Build SQL query
        query = f"""
        SELECT
            date,
            act_symbol,
            expiration,
            strike,
            call_put,
            bid,
            ask,
            vol as implied_vol,
            delta,
            gamma,
            theta,
            vega,
            rho
        FROM option_chain
        WHERE act_symbol = '{ticker}'
        AND date >= '{start_date}'
        AND date <= '{end_date}'
        """

        if option_type:
            opt_type = 'Call' if option_type.lower() == 'call' else 'Put'
            query += f" AND call_put = '{opt_type}'"

        query += " ORDER BY date, expiration, strike;"

        df = self._execute_sql(query)

        if df.empty:
            raise ValueError(f"No option data available for {ticker}")

        # Convert numeric columns
        numeric_cols = ['strike', 'bid', 'ask', 'implied_vol', 'delta', 'gamma', 'theta', 'vega', 'rho']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Standardize column names
        df['option_type'] = df['call_put'].str.lower()
        df['date'] = pd.to_datetime(df['date'])
        df['expiration'] = pd.to_datetime(df['expiration'])

        # Calculate mid price
        df['mid_price'] = (df['bid'] + df['ask']) / 2.0

        return df

    def load_volatility_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Load volatility history from DoltHub volatility_history table."""
        query = f"""
        SELECT
            date,
            act_symbol,
            hv_current,
            hv_week_ago,
            hv_month_ago,
            hv_year_high,
            hv_year_low,
            iv_current,
            iv_week_ago,
            iv_month_ago,
            iv_year_high,
            iv_year_low
        FROM volatility_history
        WHERE act_symbol = '{ticker}'
        AND date >= '{start_date}'
        AND date <= '{end_date}'
        ORDER BY date;
        """

        df = self._execute_sql(query)

        if df.empty:
            return pd.DataFrame()

        df['date'] = pd.to_datetime(df['date'])

        return df


class CSVAdapter(DataSourceAdapter):
    """
    Adapter for loading data from CSV files.

    Expected CSV formats:
    - Spot data: date, open, high, low, close, volume
    - Option data: date, strike, expiration, option_type, bid, ask, iv, delta, gamma, ...
    """

    def __init__(self, data_dir: str):
        """
        Initialize CSV adapter.

        Args:
            data_dir: Directory containing CSV files
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise ValueError(f"Data directory does not exist: {data_dir}")

    def load_spot_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Load spot data from CSV file."""
        csv_path = self.data_dir / f"{ticker}_spot.csv"

        if not csv_path.exists():
            raise ValueError(f"Spot data file not found: {csv_path}")

        df = pd.read_csv(csv_path, parse_dates=['date'], index_col='date')

        # Filter by date range
        mask = (df.index >= start_date) & (df.index <= end_date)
        df = df[mask]

        return df

    def load_option_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        option_type: Optional[str] = None
    ) -> pd.DataFrame:
        """Load options data from CSV file."""
        csv_path = self.data_dir / f"{ticker}_options.csv"

        if not csv_path.exists():
            raise ValueError(f"Option data file not found: {csv_path}")

        df = pd.read_csv(csv_path, parse_dates=['date', 'expiration'])

        # Filter by date range
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        df = df[mask]

        # Filter by option type
        if option_type:
            df = df[df['option_type'].str.lower() == option_type.lower()]

        return df


class MarketDataLoader:
    """
    High-level loader for creating MarketData objects from various sources.

    Usage:
        loader = MarketDataLoader(DoltHubAdapter("/path/to/db"))
        market_data = loader.load("AAPL", "2023-01-01", "2023-12-31")
    """

    def __init__(self, adapter: DataSourceAdapter):
        """
        Initialize market data loader.

        Args:
            adapter: DataSourceAdapter instance
        """
        self.adapter = adapter

    def load(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        build_vol_surface: bool = True
    ) -> MarketData:
        """
        Load complete market data for backtesting.

        Args:
            ticker: Underlying ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            build_vol_surface: Whether to build implied vol surfaces

        Returns:
            MarketData instance ready for backtesting
        """
        print(f"Loading market data for {ticker}...")

        # Load spot data
        print("  Loading spot prices...")
        spot_data = self.adapter.load_spot_data(ticker, start_date, end_date)

        # Load option data
        print("  Loading options chain...")
        option_data = self.adapter.load_option_data(ticker, start_date, end_date)

        # Load volatility data (if available)
        print("  Loading volatility data...")
        vol_data = self.adapter.load_volatility_data(ticker, start_date, end_date)

        # Build volatility surfaces
        vol_surfaces = {}
        if build_vol_surface and not option_data.empty:
            print("  Building volatility surfaces...")
            vol_surfaces = self._build_vol_surfaces(option_data, spot_data)

        # Create MarketData object
        market_data = MarketData(
            spot_data=spot_data[['close']].rename(columns={'close': 'close'}),
            vol_surfaces=vol_surfaces,
            underlying=ticker
        )

        print(f"  Loaded {len(spot_data)} days of spot data")
        print(f"  Loaded {len(option_data)} option records")
        print(f"  Built {len(vol_surfaces)} volatility surfaces")

        return market_data

    def _build_vol_surfaces(
        self,
        option_data: pd.DataFrame,
        spot_data: pd.DataFrame
    ) -> Dict[pd.Timestamp, VolSurface]:
        """Build implied volatility surfaces from option data."""
        vol_surfaces = {}

        # Group by date
        for date, group in option_data.groupby('date'):
            date = pd.Timestamp(date)

            # Calculate days to expiry
            group = group.copy()
            group['days_to_expiry'] = (group['expiration'] - date).dt.days

            # Filter out expired options
            group = group[group['days_to_expiry'] > 0]

            if group.empty:
                continue

            # Prepare vol surface data
            vol_df = pd.DataFrame({
                'strike': group['strike'],
                'expiry': group['days_to_expiry'],
                'implied_vol': group['implied_vol']
            })

            # Remove NaN values
            vol_df = vol_df.dropna()

            if len(vol_df) < 3:  # Need minimum points for interpolation
                continue

            try:
                vol_surface = VolSurface(
                    date=date,
                    underlying=option_data['act_symbol'].iloc[0],
                    vol_data=vol_df,
                    interpolation_method='cubic'
                )
                vol_surfaces[date] = vol_surface
            except Exception as e:
                # Skip if surface building fails
                continue

        return vol_surfaces

    def get_option_chain(
        self,
        ticker: str,
        date: str,
        expiration: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get option chain for a specific date and expiration.

        Args:
            ticker: Underlying ticker
            date: Query date (YYYY-MM-DD)
            expiration: Expiration date (YYYY-MM-DD), None for all

        Returns:
            DataFrame with option chain data
        """
        option_data = self.adapter.load_option_data(ticker, date, date)

        if expiration:
            option_data = option_data[
                option_data['expiration'] == pd.Timestamp(expiration)
            ]

        return option_data

    def get_available_expirations(
        self,
        ticker: str,
        date: str
    ) -> List[pd.Timestamp]:
        """
        Get available expiration dates for a given date.

        Args:
            ticker: Underlying ticker
            date: Query date (YYYY-MM-DD)

        Returns:
            List of available expiration dates
        """
        option_data = self.adapter.load_option_data(ticker, date, date)
        expirations = sorted(option_data['expiration'].unique())
        return [pd.Timestamp(exp) for exp in expirations]

    def get_strikes_for_expiration(
        self,
        ticker: str,
        date: str,
        expiration: str,
        option_type: Optional[str] = None
    ) -> List[float]:
        """
        Get available strikes for a given expiration.

        Args:
            ticker: Underlying ticker
            date: Query date (YYYY-MM-DD)
            expiration: Expiration date (YYYY-MM-DD)
            option_type: Filter by 'call' or 'put'

        Returns:
            List of available strike prices
        """
        option_data = self.adapter.load_option_data(
            ticker, date, date, option_type
        )

        option_data = option_data[
            option_data['expiration'] == pd.Timestamp(expiration)
        ]

        strikes = sorted(option_data['strike'].unique())
        return strikes
