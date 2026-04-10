# A 股策略选股系统

轻量级 A 股技术面策略选股工具，内置 6 种经典技术策略，支持组合筛选。

## 策略列表

| 策略 | 说明 | 信号 |
|------|------|------|
| 均线金叉 | MA5 上穿 MA20 | 买入信号 |
| MACD | 金叉 / 零轴上方金叉 / 底背离 | 买入信号 |
| RSI | 超卖反弹 / 超买回调 | 买卖信号 |
| 布林带 | 下轨反弹 / 上轨突破 | 买卖信号 |
| 放量 | 成交量突破均量 N 倍 | 关注信号 |
| 趋势 | MA5>MA10>MA20>MA60 多头排列 | 持仓信号 |

## 快速开始

```bash
# 安装依赖
pip install baostock pandas numpy tabulate pyyaml

# 运行 (默认扫描全市场)
python main.py

# 扫描指定股票
python main.py --pool custom --codes 600519,000858,000001

# 只用指定策略
python main.py --strategies ma_cross,macd

# JSON 输出
python main.py --json
```

## 配置

编辑 `config.yaml` 自定义：

- `scan.pool`: 股票池 (all/hs300/zz500/custom)
- `scan.exclude_st`: 排除 ST 股
- `strategies.*.enabled`: 启用/禁用策略
- `strategies.*.mode`: 策略模式
- `combination`: single(单策略)/composite(多策略交集)/any(并集)
- `output.max_results`: 最大结果数

## 输出

- 终端: 摘要报告
- 文件: `output/scan_YYYYMMDD_HHMM.json` + `.csv` + `_summary.txt`

## 项目结构

```
a-stock-screener/
├── main.py              # 入口
├── config.yaml          # 配置
├── scanner.py           # 扫描引擎
├── data/
│   └── fetcher.py       # 数据获取 (baostock)
├── strategies/
│   ├── base.py          # 策略基类
│   ├── ma_cross.py      # 均线金叉
│   ├── macd.py          # MACD
│   ├── rsi.py           # RSI
│   ├── bollinger.py     # 布林带
│   ├── volume.py        # 放量
│   └── trend.py         # 趋势
├── utils/
│   ├── indicators.py    # 技术指标计算
│   └── report.py        # 报告输出
└── output/              # 结果文件
```

## 定时运行

```bash
# 每个交易日 15:30 运行 (收盘后)
30 15 * * 1-5 cd /root/a-stock-screener && python3 main.py
```
