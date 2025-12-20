"""
超简单测试策略

最简单的策略示例，用于快速测试GUI功能。
策略逻辑：每天买入固定数量的股票。
"""

from jqdata import *


def initialize(context):
    """策略初始化"""
    # 设置基准
    set_benchmark("000300.XSHG")

    # 设置要交易的股票
    g.stock = "000001.XSHE"  # 平安银行

    # 每天10:00执行交易
    run_daily(trade, time="10:00")


def trade(context):
    """交易函数"""
    # 简单买入100股
    order(g.stock, 100)
    log.info(f"买入 {g.stock} 100股")
