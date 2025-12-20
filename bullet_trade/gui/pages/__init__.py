"""
GUI 页面模块
"""

from .backtest_page import BacktestPage
from .live_page import LivePage
from .optimize_page import OptimizePage
from .report_page import ReportPage
from .strategy_page import StrategyPage

__all__ = [
    'BacktestPage',
    'LivePage',
    'OptimizePage',
    'ReportPage',
    'StrategyPage',
]

