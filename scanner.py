"""
A股策略选股 - 扫描器核心
"""
import yaml
import logging
import pandas as pd

from data.fetcher import get_stock_list, fetch_all_stocks_history
from utils.indicators import add_all_indicators
from strategies.ma_cross import MACrossStrategy
from strategies.macd import MACDStrategy
from strategies.rsi import RSIStrategy
from strategies.bollinger import BollingerStrategy
from strategies.volume import VolumeSurgeStrategy
from strategies.trend import TrendStrategy
from strategies.shrink_pullback import ShrinkPullbackStrategy
from strategies.one_yang_three_yin import OneYangThreeYinStrategy
from strategies.bottom_volume import BottomVolumeStrategy
from strategies.box_oscillation import BoxOscillationStrategy
from strategies.volume_breakout import VolumeBreakoutStrategy

logger = logging.getLogger(__name__)

STRATEGY_MAP = {
    "ma_cross": MACrossStrategy,
    "macd": MACDStrategy,
    "rsi": RSIStrategy,
    "bollinger": BollingerStrategy,
    "volume": VolumeSurgeStrategy,
    "trend": TrendStrategy,
    "shrink_pullback": ShrinkPullbackStrategy,
    "one_yang_three_yin": OneYangThreeYinStrategy,
    "bottom_volume": BottomVolumeStrategy,
    "box_oscillation": BoxOscillationStrategy,
    "volume_breakout": VolumeBreakoutStrategy,
}


def load_config(path: str = "config.yaml") -> dict:
    """加载配置文件"""
    import os
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class StockScanner:
    """选股扫描器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.strategies = self._build_strategies()

    def _build_strategies(self) -> list:
        """根据配置创建策略实例"""
        instances = []
        for name, params in self.config.get("strategies", {}).items():
            if not params.get("enabled", False):
                continue
            cls = STRATEGY_MAP.get(name)
            if cls:
                instances.append(cls(params))
                logger.info(f"启用策略: {name}")
            else:
                logger.warning(f"未知策略: {name}")
        return instances

    def scan(self) -> list[dict]:
        """执行全量扫描"""
        scan_cfg = self.config.get("scan", {})
        data_cfg = self.config.get("data", {})
        output_cfg = self.config.get("output", {})
        combo = self.config.get("combination", "any")

        # 1. 获取股票列表
        stock_list = get_stock_list(
            pool=scan_cfg.get("pool", "all"),
            exclude_st=scan_cfg.get("exclude_st", True),
            exclude_kcb=scan_cfg.get("exclude_kcb", False),
            exclude_bse=scan_cfg.get("exclude_bse", True),
            custom_codes=scan_cfg.get("custom_codes"),
        )
        codes = stock_list["代码"].tolist()
        name_map = dict(zip(stock_list["代码"], stock_list["名称"]))

        if not codes:
            logger.warning("股票池为空")
            return []

        # 2. 批量获取历史数据
        history_days = data_cfg.get("history_days", 120)
        all_data = fetch_all_stocks_history(codes, days=history_days)

        # 3. 逐只扫描
        results = []
        for code, df in all_data.items():
            if df.empty or len(df) < 30:
                continue

            # 添加技术指标
            ma_periods = [5, 10, 20, 60]
            macd_params = {}
            rsi_period = 14
            boll_params = {}
            vol_period = 20

            strat_cfg = self.config.get("strategies", {})
            if "ma_cross" in strat_cfg:
                ma_periods = list(set(ma_periods + [
                    strat_cfg["ma_cross"].get("short_period", 5),
                    strat_cfg["ma_cross"].get("long_period", 20),
                ]))
            if "macd" in strat_cfg:
                macd_params = {
                    "fast": strat_cfg["macd"].get("fast", 12),
                    "slow": strat_cfg["macd"].get("slow", 26),
                    "signal": strat_cfg["macd"].get("signal", 9),
                }
            if "rsi" in strat_cfg:
                rsi_period = strat_cfg["rsi"].get("period", 14)
            if "bollinger" in strat_cfg:
                boll_params = {
                    "period": strat_cfg["bollinger"].get("period", 20),
                    "std_dev": strat_cfg["bollinger"].get("std_dev", 2),
                }
            if "volume" in strat_cfg:
                vol_period = strat_cfg["volume"].get("period", 20)

            df = add_all_indicators(
                df, ma_periods=ma_periods, macd_params=macd_params,
                rsi_period=rsi_period, boll_params=boll_params,
                vol_period=vol_period,
            )

            # 运行策略
            signals = []
            for strategy in self.strategies:
                try:
                    sig = strategy.check(df)
                    if sig:
                        signals.append({
                            "strategy": strategy.name,
                            **sig,
                        })
                except Exception as e:
                    logger.warning(f"{code} 策略 {strategy.name} 异常: {e}")

            # 组合判定
            if combo == "composite" and len(signals) < len(self.strategies):
                continue
            if not signals:
                continue

            latest = df.iloc[-1]
            score = sum(s.get("strength", 3) for s in signals)

            # 合并交易计划 (取最高分策略的买卖点)
            best_signal = max(signals, key=lambda s: s.get("strength", 0))
            trading_plan = {}
            for field in ["buy_price", "stop_loss", "target_price", "risk_level", "reason"]:
                if field in best_signal:
                    trading_plan[field] = best_signal[field]

            results.append({
                "code": code,
                "name": name_map.get(code, ""),
                "close": round(float(latest["close"]), 2),
                "pct_chg": round(float(latest.get("pct_chg", 0)), 2),
                "signals": signals,
                "score": score,
                **trading_plan,
            })

        # 4. 排序 & 截断
        results.sort(key=lambda x: x["score"], reverse=True)
        max_results = output_cfg.get("max_results", 50)
        results = results[:max_results]

        logger.info(f"扫描完成: {len(results)} 只符合条件")
        return results
