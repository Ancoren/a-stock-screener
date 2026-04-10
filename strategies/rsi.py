"""
RSI 超卖反弹 / 超买回调策略
"""
import pandas as pd
from .base import BaseStrategy


class RSIStrategy(BaseStrategy):

    def __init__(self, params: dict = None):
        super().__init__("RSI", params)
        self.oversold = self.params.get("oversold_threshold", 30)
        self.overbought = self.params.get("overbought_threshold", 70)
        self.mode = self.params.get("mode", "oversold_bounce")

    def check(self, df: pd.DataFrame) -> dict | None:
        if "RSI" not in df.columns:
            return None

        recent = df.tail(5)
        if len(recent) < 2:
            return None

        latest_rsi = recent.iloc[-1]["RSI"]

        if self.mode == "oversold_bounce":
            return self._check_oversold_bounce(recent, df)
        elif self.mode == "overbought_reject":
            return self._check_overbought_reject(recent, df)
        return None

    def _check_oversold_bounce(self, recent: pd.DataFrame, full: pd.DataFrame) -> dict | None:
        """超卖反弹: RSI 从超卖区(<=30)回升"""
        for i in range(1, len(recent)):
            prev_rsi = recent.iloc[i - 1]["RSI"]
            curr_rsi = recent.iloc[i]["RSI"]
            if prev_rsi <= self.oversold and curr_rsi > self.oversold:
                latest = full.iloc[-1]
                return {
                    "signal": f"RSI 超卖反弹 (从 {prev_rsi:.1f} 回升至 {curr_rsi:.1f})",
                    "strength": 4 if curr_rsi < 40 else 3,
                    "details": {
                        "RSI": round(latest["RSI"], 2),
                        "阈值": self.oversold,
                    }
                }
        return None

    def _check_overbought_reject(self, recent: pd.DataFrame, full: pd.DataFrame) -> dict | None:
        """超买回调: RSI 从超买区(>=70)回落"""
        for i in range(1, len(recent)):
            prev_rsi = recent.iloc[i - 1]["RSI"]
            curr_rsi = recent.iloc[i]["RSI"]
            if prev_rsi >= self.overbought and curr_rsi < self.overbought:
                latest = full.iloc[-1]
                return {
                    "signal": f"RSI 超买回调 (从 {prev_rsi:.1f} 回落至 {curr_rsi:.1f})",
                    "strength": 3,
                    "details": {
                        "RSI": round(latest["RSI"], 2),
                        "阈值": self.overbought,
                    }
                }
        return None
