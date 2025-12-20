"""
选股公式策略

基于选股公式(1).txt中的技术指标公式实现的策略。
策略逻辑：
1. 计算多个时间周期的RSV指标（21、37、55日）
2. 计算短线、中线、长线指标
3. 识别底部信号（看底、黄金、吸筹、驻底）
4. 当出现突破信号时买入
5. 当价格跌破止损线或达到止盈目标时卖出
"""

from jqdata import *
import pandas as pd
import numpy as np


def initialize(context):
    """
    策略初始化函数

    在回测开始前调用一次，用于设置策略参数和调度任务
    """
    # 设置基准指数（沪深300）
    set_benchmark("000300.XSHG")

    # 使用真实价格进行回测
    set_option("use_real_price", True)

    # 股票池（可以从指数成分股中选择，或自定义）
    # 这里使用沪深300成分股作为股票池
    g.stock_pool = get_index_stocks("000300.XSHG")

    # 策略参数
    g.max_positions = 5  # 最大持仓数量
    g.position_size = 0.2  # 每个持仓占总资金的比例

    # 止盈止损参数
    g.stop_loss_ratio = -0.05  # 止损比例 -5%
    g.take_profit_ratio = 0.15  # 止盈比例 15%

    # 记录每只股票的买入信号状态
    g.buy_signals = {}  # {stock: {'signal_date': date, 'buy_price': price}}

    # 每天开盘前更新股票池
    run_daily(before_market_open, time="before_open")

    # 每天开盘时执行交易逻辑
    run_daily(market_open, time="open")

    # 每天收盘后处理
    run_daily(after_market_close, time="after_close")


def before_market_open(context):
    """
    开盘前准备

    更新股票池，过滤掉停牌、ST等股票
    """
    # 获取当前数据
    current_data = get_current_data()

    # 过滤股票池
    valid_stocks = []
    for stock in g.stock_pool:
        if stock in current_data:
            # 过滤停牌股票
            if not current_data[stock].paused:
                # 过滤ST股票（如果名称包含ST）
                name = current_data[stock].name
                if name and "ST" not in name and "*ST" not in name:
                    valid_stocks.append(stock)

    g.stock_pool = valid_stocks
    log.info(f"更新股票池，有效股票数量: {len(g.stock_pool)}")


def market_open(context):
    """
    开盘时执行交易逻辑

    根据选股公式计算技术指标，生成买卖信号
    """
    portfolio = context.portfolio
    current_positions = list(portfolio.positions.keys())

    # 遍历股票池，寻找买入信号
    for stock in g.stock_pool:
        # 获取足够的历史数据（需要55天以上）
        df = get_price(
            stock,
            end_date=context.current_dt,
            count=60,  # 获取60天数据，确保有足够数据计算指标
            fields=["open", "high", "low", "close", "volume"],
        )

        if df is None or len(df) < 60:
            continue

        # 计算技术指标
        indicators = calculate_indicators(df)

        if indicators is None:
            continue

        # 判断是否持仓
        is_holding = stock in current_positions

        # 买入信号：突破信号
        if not is_holding and indicators["突破"]:
            # 检查是否已经达到最大持仓数
            if len(current_positions) >= g.max_positions:
                continue

            # 计算买入金额
            buy_value = portfolio.total_value * g.position_size

            # 买入
            order_value(stock, buy_value)

            # 记录买入信号
            g.buy_signals[stock] = {
                "signal_date": context.current_dt.date(),
                "buy_price": df["close"].iloc[-1],
            }

            log.info(
                f"买入信号: {stock}, "
                f"价格={df['close'].iloc[-1]:.2f}, "
                f"短线={indicators['短线']:.2f}, "
                f"中线={indicators['中线']:.2f}, "
                f"长线={indicators['长线']:.2f}"
            )

        # 卖出信号：止盈止损
        elif is_holding:
            position = portfolio.positions[stock]
            current_price = df["close"].iloc[-1]

            # 计算盈亏比例
            profit_ratio = (current_price - position.avg_cost) / position.avg_cost

            # 止损
            if profit_ratio <= g.stop_loss_ratio:
                order_target(stock, 0)
                log.info(f"止损卖出: {stock}, 亏损={profit_ratio:.2%}, 价格={current_price:.2f}")
                if stock in g.buy_signals:
                    del g.buy_signals[stock]

            # 止盈
            elif profit_ratio >= g.take_profit_ratio:
                order_target(stock, 0)
                log.info(f"止盈卖出: {stock}, 盈利={profit_ratio:.2%}, 价格={current_price:.2f}")
                if stock in g.buy_signals:
                    del g.buy_signals[stock]

            # 如果价格跌破SWL（止损线），也卖出
            elif current_price < indicators["SWL"]:
                order_target(stock, 0)
                log.info(
                    f"跌破止损线卖出: {stock}, 价格={current_price:.2f}, SWL={indicators['SWL']:.2f}"
                )
                if stock in g.buy_signals:
                    del g.buy_signals[stock]


def after_market_close(context):
    """
    收盘后处理

    打印持仓信息
    """
    portfolio = context.portfolio

    if len(portfolio.positions) > 0:
        log.info(f"总资产: {portfolio.total_value:.2f}, 持仓数量: {len(portfolio.positions)}")
        for stock, position in portfolio.positions.items():
            if position.total_amount > 0:
                log.info(
                    f"{stock}: 持仓{position.total_amount}股, "
                    f"成本{position.avg_cost:.2f}, "
                    f"当前价{position.price:.2f}, "
                    f"盈亏{(position.price - position.avg_cost) * position.total_amount:.2f}"
                )


def calculate_indicators(df):
    """
    计算选股公式中的所有技术指标

    Args:
        df: DataFrame，包含open, high, low, close, volume列

    Returns:
        dict: 包含所有指标的字典，如果计算失败返回None
    """
    try:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        open_price = df["open"]

        # VAR1:=MA(CLOSE,27)
        VAR1 = close.rolling(window=27).mean()

        # VAR2:=(CLOSE-VAR1)/VAR1*100
        VAR2 = (close - VAR1) / VAR1 * 100

        # RSV1:=(CLOSE-LLV(LOW,21))/(HHV(HIGH,21)-LLV(LOW,21))*100
        LLV_21 = low.rolling(window=21).min()
        HHV_21 = high.rolling(window=21).max()
        RSV1 = (close - LLV_21) / (HHV_21 - LLV_21) * 100

        # RSV2:=(CLOSE-LLV(LOW,37))/(HHV(HIGH,37)-LLV(LOW,37))*100
        LLV_37 = low.rolling(window=37).min()
        HHV_37 = high.rolling(window=37).max()
        RSV2 = (close - LLV_37) / (HHV_37 - LLV_37) * 100

        # RSV3:=(CLOSE-LLV(LOW,55))/(HHV(HIGH,55)-LLV(LOW,55))*100
        LLV_55 = low.rolling(window=55).min()
        HHV_55 = high.rolling(window=55).max()
        RSV3 = (close - LLV_55) / (HHV_55 - LLV_55) * 100

        # VARA:=MA(VAR2,2)
        VARA = VAR2.rolling(window=2).mean()

        # VARB:=BARSLAST(CROSS(-10,VARA)=1)
        # VARC:=BARSLAST(CROSS(VARA,10)=1)
        # 计算交叉：CROSS(A,B)表示A上穿B（这里CROSS(-10,VARA)表示-10上穿VARA，即VARA下穿-10）
        cross_down = (VARA.shift(1) >= -10) & (VARA < -10)  # VARA下穿-10
        cross_up = (VARA.shift(1) <= 10) & (VARA > 10)  # VARA上穿10

        # BARSLAST: 上一次条件成立到现在的周期数
        # 使用更高效的方法计算
        def barslast(condition):
            """计算BARSLAST：上一次条件成立到现在的周期数"""
            result = pd.Series(index=df.index, dtype=float)
            last_index = -1
            for i in range(len(df)):
                if condition.iloc[i]:
                    last_index = i
                result.iloc[i] = i - last_index if last_index >= 0 else np.nan
            return result

        VARB = barslast(cross_down)
        VARC = barslast(cross_up)

        # VARD:=VARA<-10 AND VARB>3 (原公式中的变量，策略中未直接使用)
        # VARD = (VARA < -10) & (VARB > 3)

        # VARE:=VARA>10 AND VARC>3 (原公式中的变量，策略中未直接使用)
        # VARE = (VARA > 10) & (VARC > 3)

        # 短线:=SMA(SMA(RSV1,3,1),3,1)+3*STD(CLOSE,21)
        # SMA(X,N,M) 表示对X进行N周期移动平均，权重为M
        # 这里简化为使用pandas的ewm（指数加权移动平均）来近似SMA
        # 实际上SMA(RSV1,3,1)可以理解为对RSV1进行3周期平滑
        SMA_RSV1_1 = RSV1.ewm(span=3, adjust=False).mean()  # 近似SMA
        SMA_RSV1_2 = SMA_RSV1_1.ewm(span=3, adjust=False).mean()  # 二次平滑
        STD_21 = close.rolling(window=21).std()
        短线 = SMA_RSV1_2 + 3 * STD_21

        # 中线:=SMA(RSV2,5,1)+2*STD(CLOSE,37)
        SMA_RSV2 = RSV2.ewm(span=5, adjust=False).mean()
        STD_37 = close.rolling(window=37).std()
        中线 = SMA_RSV2 + 2 * STD_37

        # 中长线:=-100*(HHV(HIGH,40)-CLOSE)/(HHV(HIGH,40)-LLV(LOW,40))
        HHV_40 = high.rolling(window=40).max()
        LLV_40 = low.rolling(window=40).min()
        中长线 = -100 * (HHV_40 - close) / (HHV_40 - LLV_40)

        # 长线:=SMA(RSV3,5,1)
        长线 = RSV3.ewm(span=5, adjust=False).mean()

        # 看底:=中线<15
        看底 = 中线 < 15

        # 黄金:=短线<20 AND 中线<20 AND 长线<20
        黄金 = (短线 < 20) & (中线 < 20) & (长线 < 20)

        # 吸筹:=REF(NOT(看底 OR 黄金),1) AND (看底 OR 黄金)
        # REF(X,1)表示前1期的X值
        ref_看底或黄金 = (看底 | 黄金).shift(1)
        吸筹 = (~ref_看底或黄金) & (看底 | 黄金)

        # 驻底:=EVERY(看底 OR 黄金,1)
        # EVERY(X,1)表示最近1期一直满足X
        驻底 = 看底 | 黄金

        # SWL:=(EMA(CLOSE,10)*7+EMA(CLOSE,20)*3)/10
        EMA_10 = close.ewm(span=10, adjust=False).mean()
        EMA_20 = close.ewm(span=20, adjust=False).mean()
        SWL = (EMA_10 * 7 + EMA_20 * 3) / 10

        # 突破:CROSS(C,SWL) AND (C/O-1)*100>=5
        # CROSS(C,SWL)表示收盘价上穿SWL
        cross_swl = (close.shift(1) <= SWL.shift(1)) & (close > SWL)
        price_change = (close / open_price - 1) * 100
        突破 = cross_swl & (price_change >= 5)

        # 返回最新一期的指标值
        return {
            "短线": 短线.iloc[-1],
            "中线": 中线.iloc[-1],
            "中长线": 中长线.iloc[-1],
            "长线": 长线.iloc[-1],
            "看底": 看底.iloc[-1],
            "黄金": 黄金.iloc[-1],
            "吸筹": 吸筹.iloc[-1],
            "驻底": 驻底.iloc[-1],
            "SWL": SWL.iloc[-1],
            "突破": 突破.iloc[-1],
        }
    except Exception as e:
        log.error(f"计算指标失败: {e}")
        return None
