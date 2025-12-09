"""
Options Strategy Backtester
A comprehensive framework for backtesting complex options strategies.
"""

__version__ = "1.0.0"

from .data import MarketData, VolSurface
from .instruments import (
    OptionContract, OptionLeg, OptionStrategy, Portfolio,
    CalendarSpreadStrategy, VerticalSpreadStrategy, ButterflyStrategy,
    IronCondorStrategy, StraddleStrategy, StrangleStrategy
)
from .models import PricingModel, BlackScholesModel, BachelierModel, SABRModel, SurfaceGreeksModel
from .backtest import BacktestEngine, BacktestConfig, RollingStrategy, DeltaHedger
from .metrics import PerformanceMetrics, PnLAttributionEngine, BreakevenAnalyzer
from .visualize import VisualizationEngine

__all__ = [
    'MarketData',
    'VolSurface',
    'OptionContract',
    'OptionLeg',
    'OptionStrategy',
    'Portfolio',
    'CalendarSpreadStrategy',
    'VerticalSpreadStrategy',
    'ButterflyStrategy',
    'IronCondorStrategy',
    'StraddleStrategy',
    'StrangleStrategy',
    'PricingModel',
    'BlackScholesModel',
    'BachelierModel',
    'SABRModel',
    'SurfaceGreeksModel',
    'BacktestEngine',
    'BacktestConfig',
    'RollingStrategy',
    'DeltaHedger',
    'PerformanceMetrics',
    'PnLAttributionEngine',
    'BreakevenAnalyzer',
    'VisualizationEngine',
]
