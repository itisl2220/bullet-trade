"""
测试策略 - 简单买入持有策略

这是一个用于测试GUI功能的简单策略示例。
策略逻辑：选择几只股票，买入并持有。
"""

from jqdata import *


def initialize(context):
    """
    策略初始化函数

    在回测开始前调用一次，用于设置策略参数和调度任务
    """
    # 设置基准指数（沪深300）
    set_benchmark("000300.XSHG")

    # 使用真实价格进行回测
    set_option("use_real_price", True)

    # 设置手续费和滑点（可选，使用默认值也可以）
    # set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003,
    #                          close_commission=0.0003, min_commission=5), type='stock')

    # 选择要交易的股票池
    # 这里选择几只知名股票作为示例
    g.stocks = [
        "000001.XSHE",  # 平安银行
        "600000.XSHG",  # 浦发银行
        "000002.XSHE",  # 万科A
    ]

    # 每只股票的持仓比例（等权重）
    g.position_size = 1.0 / len(g.stocks)

    # 记录交易次数
    g.trade_count = 0

    # 每天开盘时执行交易逻辑
    run_daily(trade, time="open")

    # 每天收盘后打印持仓信息（可选）
    run_daily(after_market_close, time="after_close")


def trade(context):
    """
    交易函数

    每个交易日开盘时调用，执行交易逻辑
    """
    # 获取当前账户信息
    portfolio = context.portfolio

    # 遍历股票池
    for stock in g.stocks:
        # 获取当前持仓（如果不存在则创建空持仓）
        if stock not in portfolio.positions:
            from bullet_trade.core.models import Position

            portfolio.positions[stock] = Position(security=stock)
        position = portfolio.positions[stock]

        # 计算目标持仓市值（总资产的固定比例）
        target_value = portfolio.total_value * g.position_size

        # 获取当前价格
        current_data = get_current_data()
        if stock not in current_data:
            continue

        current_price = current_data[stock].last_price
        if current_price is None or current_price <= 0:
            continue

        # 计算目标持仓数量
        target_amount = int(target_value / current_price / 100) * 100  # 按手买入

        # 计算需要调整的数量
        current_amount = position.total_amount if position else 0
        need_amount = target_amount - current_amount

        # 如果持仓偏差超过1手，则调整
        if abs(need_amount) >= 100:
            if need_amount > 0:
                # 买入
                order(stock, need_amount)
                g.trade_count += 1
                log.info(f"买入 {stock}: {need_amount}股, 价格: {current_price:.2f}")
            elif need_amount < 0:
                # 卖出
                order(stock, need_amount)
                g.trade_count += 1
                log.info(f"卖出 {stock}: {abs(need_amount)}股, 价格: {current_price:.2f}")


def after_market_close(context):
    """
    收盘后调用

    用于打印每日持仓信息或进行其他统计
    """
    portfolio = context.portfolio

    # 打印账户信息
    log.info(
        f"总资产: {portfolio.total_value:.2f}, "
        f"可用资金: {portfolio.available_cash:.2f}, "
        f"持仓市值: {portfolio.total_value - portfolio.available_cash:.2f}"
    )

    # 打印持仓详情
    for stock in g.stocks:
        position = portfolio.positions.get(stock)
        if position and position.total_amount > 0:
            log.info(
                f"{stock}: 持仓{position.total_amount}股, "
                f"成本{position.avg_cost:.2f}, "
                f"当前价{position.price:.2f}, "
                f"盈亏{(position.price - position.avg_cost) * position.total_amount:.2f}"
            )


# 可选：实盘初始化函数
def process_initialize(context):
    """
    实盘/模拟盘初始化函数

    仅在实盘或模拟盘运行时调用，用于实盘特定的初始化
    """
    log.info("实盘初始化完成")
