# BulletTrade GUI 使用指南

## 用户认证

BulletTrade GUI 现在支持用户登录认证功能，与后端服务器完全集成：

- **首次启动**: 系统会显示登录对话框
- **后端认证**: 连接后端API进行JWT认证
- **会话管理**: 登录状态保持24小时，支持JWT token
- **记住登录**: 勾选"记住我"可保存登录信息
- **用户菜单**: 登录后在菜单栏显示当前用户信息和登出选项

### 服务器配置

必须配置后端服务器才能使用登录功能：

```bash
# 环境变量
export API_SERVER_HOST=localhost
export API_SERVER_PORT=3000
export API_SERVER_SSL=false

# 或在GUI配置中设置
```

**重要**: GUI完全依赖后端服务器，如后端不可用将无法登录。

## 安装GUI依赖

```bash
pip install bullet-trade[gui]
```

或者单独安装PyQt6：

```bash
pip install PyQt6>=6.4.0
```

## 启动GUI

BulletTrade GUI 支持多种启动方式：

### 方式1：使用CLI命令（推荐）

```bash
bullet-trade gui
```

### 方式2：使用独立入口点

安装后可以使用：

```bash
bullet-trade-gui
```

### 方式3：使用Python模块方式

```bash
python -m bullet_trade.gui
```

### 方式4：直接运行启动脚本

在项目根目录下：

```bash
python start_gui.py
```

### 方式5：在代码中启动

```python
from bullet_trade.gui.app import main
main()
```

## 功能说明

### 1. 策略管理
- 打开、编辑、保存策略文件
- 代码编辑器支持语法高亮
- 实时保存功能

### 2. 回测
- 配置回测参数（日期、资金、频率等）
- **选择数据源**：支持 JQData、QMT、MiniQMT、Tushare
- **唯一结果目录**：每次回测自动创建唯一子目录，避免覆盖
- 实时查看回测日志
- 自动生成报告（CSV/HTML）
- **自动打开报告**：回测完成后自动在WebView窗口中显示HTML报告

**数据源说明：**
- **jqdata**：聚宽数据源（默认，需要账号）
- **qmt/miniqmt**：QMT本地行情数据（需要安装xtquant和配置QMT数据目录）
- **tushare**：Tushare数据源（需要token）

**结果目录说明：**
- 基础目录：`./backtest_results`（可自定义）
- 实际目录：`./backtest_results/20240101_120000_abc12345/`（自动生成唯一子目录）
- 目录命名：`时间戳_唯一标识`，确保每次回测结果独立保存

### 3. 实盘交易
- 配置券商连接
- 启动/停止实盘交易
- 实时查看交易日志
- ⚠️ 包含风险警告提示

### 4. 参数优化
- 配置参数网格
- 多进程并行优化
- 生成优化结果CSV

### 5. 报告
- 从回测结果目录生成报告
- 支持HTML格式
- 一键打开报告

## 使用流程

1. **策略管理** → 打开或创建策略文件
2. **回测** → 配置参数并运行回测
3. **报告** → 查看回测结果报告
4. **参数优化** → 优化策略参数
5. **实盘交易** → 在充分测试后启动实盘

## 注意事项

- GUI需要PyQt6依赖，请确保已正确安装
- 实盘交易前请充分回测验证策略
- 所有功能与CLI命令功能一致

