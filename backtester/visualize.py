"""
Visualization tools for backtest results and strategy analysis.
"""

from typing import Optional, List, Dict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .instruments import OptionStrategy
from .data import MarketData
from .models import PricingModel


class VisualizationEngine:
    """
    Comprehensive visualization engine for options backtesting.

    Provides:
    - P&L plots
    - Drawdown curves
    - Greeks over time
    - P&L attribution charts
    - Risk profile diagrams
    - Breakeven visualization
    """

    def __init__(self, use_plotly: bool = True):
        """
        Initialize visualization engine.

        Args:
            use_plotly: If True, use plotly for interactive charts;
                       otherwise use matplotlib
        """
        self.use_plotly = use_plotly

        # Set matplotlib style
        if not use_plotly:
            plt.style.use('seaborn-v0_8-darkgrid')

    def plot_equity_curve(
        self,
        results: pd.DataFrame,
        title: str = "Portfolio Equity Curve"
    ):
        """
        Plot portfolio value over time.

        Args:
            results: Backtest results DataFrame
            title: Chart title
        """
        if self.use_plotly:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=results.index,
                y=results['portfolio_value'],
                mode='lines',
                name='Portfolio Value',
                line=dict(color='blue', width=2)
            ))

            fig.update_layout(
                title=title,
                xaxis_title="Date",
                yaxis_title="Portfolio Value ($)",
                hovermode='x unified',
                template='plotly_white'
            )

            fig.show()

        else:
            fig, ax = plt.subplots(figsize=(12, 6))

            ax.plot(
                results.index,
                results['portfolio_value'],
                color='blue',
                linewidth=2,
                label='Portfolio Value'
            )

            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel('Portfolio Value ($)')
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

    def plot_returns_distribution(
        self,
        results: pd.DataFrame,
        title: str = "Returns Distribution"
    ):
        """Plot distribution of daily returns."""
        returns = results['returns'].dropna()

        if self.use_plotly:
            fig = go.Figure()

            fig.add_trace(go.Histogram(
                x=returns,
                nbinsx=50,
                name='Returns',
                marker_color='lightblue',
                marker_line_color='darkblue',
                marker_line_width=1
            ))

            fig.update_layout(
                title=title,
                xaxis_title="Daily Returns",
                yaxis_title="Frequency",
                template='plotly_white'
            )

            fig.show()

        else:
            fig, ax = plt.subplots(figsize=(10, 6))

            ax.hist(returns, bins=50, color='lightblue',
                   edgecolor='darkblue', alpha=0.7)

            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel('Daily Returns')
            ax.set_ylabel('Frequency')
            ax.axvline(0, color='red', linestyle='--', alpha=0.7)
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

    def plot_drawdown(
        self,
        results: pd.DataFrame,
        title: str = "Drawdown"
    ):
        """Plot drawdown curve."""
        portfolio_values = results['portfolio_value']
        cumulative_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values - cumulative_max) / cumulative_max

        if self.use_plotly:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=results.index,
                y=drawdown * 100,
                fill='tozeroy',
                mode='lines',
                name='Drawdown',
                line=dict(color='red'),
                fillcolor='rgba(255, 0, 0, 0.2)'
            ))

            fig.update_layout(
                title=title,
                xaxis_title="Date",
                yaxis_title="Drawdown (%)",
                hovermode='x unified',
                template='plotly_white'
            )

            fig.show()

        else:
            fig, ax = plt.subplots(figsize=(12, 6))

            ax.fill_between(
                results.index,
                drawdown * 100,
                0,
                color='red',
                alpha=0.3
            )

            ax.plot(
                results.index,
                drawdown * 100,
                color='red',
                linewidth=2
            )

            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel('Drawdown (%)')
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

    def plot_greeks(
        self,
        results: pd.DataFrame,
        greeks: List[str] = None,
        title: str = "Greeks Over Time"
    ):
        """
        Plot Greeks evolution over time.

        Args:
            results: Backtest results
            greeks: List of Greeks to plot (default: all)
            title: Chart title
        """
        if greeks is None:
            greeks = ['delta', 'gamma', 'vega', 'theta', 'rho']

        if self.use_plotly:
            fig = make_subplots(
                rows=len(greeks),
                cols=1,
                subplot_titles=[g.capitalize() for g in greeks],
                vertical_spacing=0.05
            )

            for i, greek in enumerate(greeks, 1):
                if greek in results.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=results.index,
                            y=results[greek],
                            mode='lines',
                            name=greek.capitalize(),
                            line=dict(width=2)
                        ),
                        row=i,
                        col=1
                    )

                    fig.update_yaxes(title_text=greek.capitalize(), row=i, col=1)

            fig.update_layout(
                title=title,
                height=300 * len(greeks),
                showlegend=False,
                template='plotly_white'
            )

            fig.show()

        else:
            n_greeks = len(greeks)
            fig, axes = plt.subplots(n_greeks, 1, figsize=(12, 4 * n_greeks))

            if n_greeks == 1:
                axes = [axes]

            for ax, greek in zip(axes, greeks):
                if greek in results.columns:
                    ax.plot(
                        results.index,
                        results[greek],
                        linewidth=2
                    )

                    ax.set_ylabel(greek.capitalize())
                    ax.grid(True, alpha=0.3)
                    ax.axhline(0, color='black', linestyle='--', alpha=0.5)

            axes[0].set_title(title, fontsize=14, fontweight='bold')
            axes[-1].set_xlabel('Date')

            plt.tight_layout()
            plt.show()

    def plot_pnl_attribution(
        self,
        results: pd.DataFrame,
        cumulative: bool = True,
        title: str = "P&L Attribution"
    ):
        """
        Plot P&L attribution by Greek.

        Args:
            results: Backtest results
            cumulative: If True, show cumulative attribution
            title: Chart title
        """
        greeks = ['pnl_delta', 'pnl_gamma', 'pnl_vega',
                 'pnl_theta', 'pnl_rho', 'pnl_residual']

        labels = ['Delta', 'Gamma', 'Vega', 'Theta', 'Rho', 'Residual']

        # Filter to existing columns
        available_greeks = [g for g in greeks if g in results.columns]
        available_labels = [labels[greeks.index(g)] for g in available_greeks]

        if cumulative:
            data = {label: results[greek].cumsum()
                   for greek, label in zip(available_greeks, available_labels)}
        else:
            data = {label: results[greek]
                   for greek, label in zip(available_greeks, available_labels)}

        df = pd.DataFrame(data, index=results.index)

        if self.use_plotly:
            fig = go.Figure()

            for column in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode='lines',
                    name=column,
                    stackgroup='one' if not cumulative else None
                ))

            fig.update_layout(
                title=title,
                xaxis_title="Date",
                yaxis_title="P&L ($)",
                hovermode='x unified',
                template='plotly_white'
            )

            fig.show()

        else:
            fig, ax = plt.subplots(figsize=(12, 6))

            if cumulative:
                for column in df.columns:
                    ax.plot(df.index, df[column], label=column, linewidth=2)
            else:
                ax.stackplot(
                    df.index,
                    *[df[col] for col in df.columns],
                    labels=df.columns,
                    alpha=0.7
                )

            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel('P&L ($)')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            ax.axhline(0, color='black', linestyle='--', alpha=0.5)

            plt.tight_layout()
            plt.show()

    def plot_risk_profile(
        self,
        strategy: OptionStrategy,
        current_date: pd.Timestamp,
        market_data: MarketData,
        model: PricingModel,
        spot_range: Optional[np.ndarray] = None,
        time_points: Optional[List[int]] = None,
        title: str = "Risk Profile"
    ):
        """
        Plot strategy risk profile (P&L vs spot) at different time points.

        Args:
            strategy: Option strategy
            current_date: Current date
            market_data: Market data
            model: Pricing model
            spot_range: Range of spot prices to plot
            time_points: List of days in future to show profiles for
            title: Chart title
        """
        current_spot = market_data.get_spot(current_date)

        # Generate spot range
        strikes = [leg.contract.strike for leg in strategy.legs]
        min_strike = min(strikes)
        max_strike = max(strikes)

        if spot_range is None:
            spot_range = np.linspace(
                min_strike * 0.7, max_strike * 1.3, 100
            )

        # Current value for P&L calculation
        current_value = strategy.value(current_date, market_data, model)

        # Time points
        if time_points is None:
            min_expiry = min(leg.contract.expiry for leg in strategy.legs)
            days_to_expiry = (min_expiry - current_date).days
            time_points = [0, days_to_expiry // 4, days_to_expiry // 2, days_to_expiry]

        if self.use_plotly:
            fig = go.Figure()

            # Plot profiles for each time point
            for days in time_points:
                if days == 0:
                    label = "Today"
                elif days >= (min_expiry - current_date).days:
                    label = "At Expiry"
                else:
                    label = f"In {days} days"

                pnls = []
                for spot in spot_range:
                    if days >= (min_expiry - current_date).days:
                        # At expiry
                        pnl = strategy.payoff(spot, at_expiry=True) - current_value
                    else:
                        # Before expiry (simplified - would need time adjustment)
                        pnl = strategy.payoff(spot, at_expiry=True) - current_value

                    pnls.append(pnl)

                fig.add_trace(go.Scatter(
                    x=spot_range,
                    y=pnls,
                    mode='lines',
                    name=label,
                    line=dict(width=2)
                ))

            # Add current spot marker
            fig.add_vline(
                x=current_spot,
                line_dash="dash",
                line_color="gray",
                annotation_text="Current Spot"
            )

            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="black")

            fig.update_layout(
                title=title,
                xaxis_title="Underlying Price ($)",
                yaxis_title="P&L ($)",
                hovermode='x unified',
                template='plotly_white'
            )

            fig.show()

        else:
            fig, ax = plt.subplots(figsize=(12, 7))

            for days in time_points:
                if days == 0:
                    label = "Today"
                elif days >= (min_expiry - current_date).days:
                    label = "At Expiry"
                else:
                    label = f"In {days} days"

                pnls = []
                for spot in spot_range:
                    if days >= (min_expiry - current_date).days:
                        pnl = strategy.payoff(spot, at_expiry=True) - current_value
                    else:
                        pnl = strategy.payoff(spot, at_expiry=True) - current_value

                    pnls.append(pnl)

                ax.plot(spot_range, pnls, label=label, linewidth=2)

            ax.axvline(current_spot, color='gray', linestyle='--',
                      alpha=0.7, label='Current Spot')
            ax.axhline(0, color='black', linestyle='--', alpha=0.5)

            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel('Underlying Price ($)')
            ax.set_ylabel('P&L ($)')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

    def plot_rolling_metrics(
        self,
        results: pd.DataFrame,
        metric: str = 'sharpe',
        window: int = 60,
        title: Optional[str] = None
    ):
        """
        Plot rolling performance metric.

        Args:
            results: Backtest results
            metric: Metric to plot ('sharpe', 'volatility', 'drawdown')
            window: Rolling window size
            title: Chart title
        """
        from .metrics import PerformanceMetrics

        perf = PerformanceMetrics(results)

        if metric == 'sharpe':
            rolling_data = perf.rolling_sharpe(window)
            ylabel = "Rolling Sharpe Ratio"
        elif metric == 'volatility':
            rolling_data = perf.rolling_volatility(window)
            ylabel = "Rolling Volatility"
        elif metric == 'drawdown':
            rolling_data = perf.rolling_max_drawdown(window)
            ylabel = "Rolling Max Drawdown"
        else:
            raise ValueError(f"Unknown metric: {metric}")

        if title is None:
            title = f"Rolling {metric.capitalize()} ({window}-day window)"

        if self.use_plotly:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=rolling_data.index,
                y=rolling_data,
                mode='lines',
                name=ylabel,
                line=dict(width=2, color='blue')
            ))

            fig.update_layout(
                title=title,
                xaxis_title="Date",
                yaxis_title=ylabel,
                hovermode='x unified',
                template='plotly_white'
            )

            fig.show()

        else:
            fig, ax = plt.subplots(figsize=(12, 6))

            ax.plot(rolling_data.index, rolling_data,
                   linewidth=2, color='blue')

            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel(ylabel)
            ax.grid(True, alpha=0.3)

            if metric in ['sharpe', 'drawdown']:
                ax.axhline(0, color='black', linestyle='--', alpha=0.5)

            plt.tight_layout()
            plt.show()

    def create_dashboard(
        self,
        results: pd.DataFrame,
        strategy: Optional[OptionStrategy] = None,
        market_data: Optional[MarketData] = None,
        model: Optional[PricingModel] = None
    ):
        """
        Create comprehensive dashboard with multiple charts.

        Args:
            results: Backtest results
            strategy: Option strategy (for risk profile)
            market_data: Market data (for risk profile)
            model: Pricing model (for risk profile)
        """
        from .metrics import PerformanceMetrics, PnLAttributionEngine

        # Print performance summary
        perf = PerformanceMetrics(results)
        perf.print_summary()

        # Print P&L attribution
        attribution = PnLAttributionEngine(results)
        attribution.print_summary()

        # Plot equity curve
        self.plot_equity_curve(results)

        # Plot drawdown
        self.plot_drawdown(results)

        # Plot Greeks
        self.plot_greeks(results)

        # Plot P&L attribution
        self.plot_pnl_attribution(results, cumulative=True)

        # Plot rolling Sharpe
        self.plot_rolling_metrics(results, metric='sharpe', window=60)

        # Plot risk profile if strategy provided
        if strategy and market_data and model:
            self.plot_risk_profile(
                strategy,
                results.index[-1],
                market_data,
                model
            )
