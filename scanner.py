"""
选股扫描引擎
"""
import pandas as pd
import yaml
import logging
from pathlib import Path

from data.fetcher import get_stock_list, fetch_all_stocks_history
from utils.indicators import add_all_indicators
from strategies.ma_cross import MACrossStrategy
from strategies.macd import MACDStrategy
from strategies.rsi import RSIStrategy
from strategies.bollinger import BollingerStrategy
from strategies.volume import VolumeSurgeStrategy
from strategies.trend import TrendStrategy

logger = logging.getLogger(__name__)

STRATEGY_MAP = {
    "ma_cross": MACrossStrategy,
    "macd": MACDStrategy,
    "rsi": RSIStrategy,
    "bollinger": BollingerStrategy,
    "volume": VolumeSurgeStrategy,
    "trend": TrendStrategy,
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class StockScanner:
    """股票扫描器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.strategies = self._init_strategies()

    def _init_strategies(self) -> list:
        """初始化启用的策略"""
        strategies = []
        strat_cfg = self.config.get("strategies", {})

        for name, cls in STRATEGY_MAP.items():
            if strat_cfg.get(name, {}).get("enabled", False):
                strategies.append(cls(strat_cfg[name]))
                logger.info(f"启用策略: {name}")

        logger.info(f"共 {len(strategies)} 个策略启用")
        return strategies

    def scan(self) -> list[dict]:
        """执行扫描"""
        scan_cfg = self.config["scan"]
        data_cfg = self.config["data"]

        # 1. 获取股票列表
        logger.info("获取股票列表...")
        stock_list = get_stock_list(
            pool=scan_cfg["pool"],
            exclude_st=scan_cfg["exclude_st"],
            exclude_kcb=scan_cfg["exclude_kcb"],
            exclude_bse=scan_cfg["exclude_bse"],
            custom_codes=scan_cfg.get("custom_codes"),
        )

        if stock_list.empty:
            logger.warning("股票列表为空")
            return []

        codes = stock_list["代码"].tolist()
        # 建立 code -> name 映射
        name_map = dict(zip(stock_list["代码"], stock_list["名称"]))

        # 2. 批量获取历史数据
        logger.info(f"获取 {len(codes)} 只股票历史数据...")
        history = fetch_all_stocks_history(codes, days=data_cfg["history_days"])

        # 3. 计算指标 + 策略扫描
        logger.info("开始策略扫描...")
        results = []
        combination = self.config.get("combination", "single")

        for code, df in history.items():
            if len(df) < 60:  # 数据不足跳过
                continue

            df = add_all_indicators(df)
            signals = self._run_strategies(df, combination)

            if signals:
                latest = df.iloc[-1]
                results.append({
                    "code": code,
                    "name": name_map.get(code, ""),
                    "close": round(latest["close"], 2),
                    "pct_chg": round(latest.get("pct_chg", 0), 2),
                    "volume": latest["volume"],
                    "signals": signals,
                    "score": sum(s["strength"] for s in signals),
                })

        # 按评分排序
        results.sort(key=lambda x: x["score"], reverse=True)

        # 截断
        max_results = self.config["output"].get("max_results", 50)
        results = results[:max_results]

        logger.info(f"扫描完成, 共 {len(results)} 只股票符合策略条件")
        return results

    def _run_strategies(self, df: pd.DataFrame, combination: str) -> list[dict]:
        """对单只股票运行所有策略"""
        signals = []
        for strategy in self.strategies:
            try:
                result = strategy.check(df)
                if result:
                    result["strategy"] = strategy.name
                    signals.append(result)
            except Exception as e:
                logger.warning(f"策略 {strategy.name} 执行异常: {e}")

        if not signals:
            return []

        if combination == "single":
            # 取最强信号
            return [max(signals, key=lambda s: s["strength"])]
        elif combination == "composite":
            # 需要至少2个策略命中
            return signals if len(signals) >= 2 else []
        else:  # any
            return signals
