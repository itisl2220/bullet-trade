# 测试策略说明

本目录包含用于测试 BulletTrade GUI 功能的示例策略。

## 策略文件

### 1. `simple_test_strategy.py` - 超简单测试策略

**特点：**
- 最简单的策略示例
- 每天买入固定数量的股票（100股）
- 适合快速测试GUI基本功能

**使用方法：**
- 在GUI中选择此策略文件
- 设置回测日期（建议：2023-01-01 至 2023-12-31）
- 点击"开始回测"

### 2. `test_strategy.py` - 完整测试策略

**特点：**
- 包含完整的策略逻辑
- 多股票等权重持仓
- 自动调仓功能
- 包含日志输出和持仓统计

**策略逻辑：**
- 选择3只股票（平安银行、浦发银行、万科A）
- 每只股票持仓占总资产的1/3
- 每天开盘时检查并调整持仓
- 收盘后打印持仓信息

**使用方法：**
- 在GUI中选择此策略文件
- 设置回测日期（建议：2023-01-01 至 2023-12-31）
- 初始资金建议：100000 或更多
- 点击"开始回测"

## 快速测试步骤

1. **启动GUI**
   ```bash
   python start_gui.py
   # 或
   bullet-trade gui
   ```

2. **打开策略文件**
   - 点击"策略管理"标签
   - 点击"打开策略文件"
   - 选择 `strategies/simple_test_strategy.py` 或 `strategies/test_strategy.py`

3. **运行回测**
   - 切换到"回测"标签
   - 设置回测参数：
     - 开始日期：2023-01-01
     - 结束日期：2023-12-31
     - 初始资金：100000
     - 回测频率：day（日线）
   - 点击"开始回测"

4. **查看结果**
   - 等待回测完成
   - 切换到"报告"标签
   - 选择回测结果目录
   - 生成并查看报告

## 注意事项

- 确保已配置数据源（JQData、MiniQMT等）
- 策略文件需要包含 `initialize(context)` 函数
- 可选包含 `handle_data(context, data)`、`before_trading_start(context)` 等函数
- 回测日期建议选择有交易数据的日期范围

## 策略编写规范

参考 `test_strategy.py` 的代码结构：

```python
from jqdata import *

def initialize(context):
    """初始化函数 - 必需"""
    set_benchmark('000300.XSHG')
    g.stock = '000001.XSHE'
    run_daily(trade, time='10:00')

def trade(context):
    """交易函数"""
    order(g.stock, 100)
```

更多策略示例请参考 `tests/strategies/` 目录。

