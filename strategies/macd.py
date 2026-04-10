"""
MACD 策略
支持: 金叉 / 零轴上方金叉 / 底背离
"""
import pandas as pd
from .base import BaseStrategy


class MACDStrategy(BaseStrategy):

    def __init__(self, params: dict = None):
        super().__init__("MACD", params)
        self.mode = self.params.get("mode", "golden_cross")

    def check(self, df: pd.DataFrame) -> dict | None:
        if "MACD_DIF" not in df.columns:
            return None

        recent = df.tail(5)
        if len(recent) < 2:
            return None

        if self.mode == "golden_cross":
            return self._check_golden_cross(recent, df)
        elif self.mode == "above_zero":
            return self._check_above_zero(recent, df)
        elif self.mode == "bullish_divergence":
            return self._check_divergence(df)
        return None

    def _check_golden_cross(self, recent: pd.DataFrame, full: pd.DataFrame) -> dict | None:
        """MACD 金叉"""
        for i in range(1, len(recent)):
            prev = recent.iloc[i - 1]
            curr = recent.iloc[i]
            if prev["MACD_DIF"] <= prev["MACD_DEA"] and curr["MACD_DIF"] > curr["MACD_DEA"]:
                latest = full.iloc[-1]
                return {
                    "signal": "MACD 金叉",
                    "strength": 3,
                    "details": {
                        "DIF": round(latest["MACD_DIF"], 4),
                        "DEA": round(latest["MACD_DEA"], 4),
                        "MACD": round(latest["MACD_HIST"], 4),
                    }
                }
        return None

    def _check_above_zero(self, recent: pd.DataFrame, full: pd.DataFrame) -> dict | None:
        """零轴上方金叉 (更强信号)"""
        for i in range(1, len(recent)):
            prev = recent.iloc[i - 1]
            curr = recent.iloc[i]
            if (prev["MACD_DIF"] <= prev["MACD_DEA"] and
                    curr["MACD_DIF"] > curr["MACD_DEA"] and
                    curr["MACD_DEA"] > 0):
                latest = full.iloc[-1]
                return {
                    "signal": "MACD 零轴上方金叉",
                    "strength": 5,
                    "details": {
                        "DIF": round(latest["MACD_DIF"], 4),
                        "DEA": round(latest["MACD_DEA"], 4),
                        "MACD": round(latest["MACD_HIST"], 4),
                    }
                }
        return None

    def _check_divergence(self, df: pd.DataFrame) -> dict | None:
        """底背离: 价格创新低但 MACD DIF 没有创新低"""
        if len(df) < 30:
            return None

        recent_30 = df.tail(30)
        # 找价格的两个低点
        min_idx = recent_30["close"].idxmin()
        if min_idx == recent_30.index[-1]:
            # 当前就是最低点, 往前找另一个低点
            earlier = recent_30.loc[:min_idx - 5] if min_idx - 5 >= recent_30.index[0] else None
            if earlier is None or len(earlier) < 10:
                return None
            prev_min_idx = earlier["close"].idxmin()
        else:
            prev_min_idx = recent_30.loc[:min_idx - 1]["close"].idxmin()

        prev_min_price = recent_30.loc[prev_min_idx, "close"]
        curr_min_price = recent_30.loc[min_idx, "close"]
        prev_min_dif = recent_30.loc[prev_min_idx, "MACD_DIF"]
        curr_min_dif = recent_30.loc[min_idx, "MACD_DIF"]

        # 价格创新低 但 DIF 没创新低
        if curr_min_price < prev_min_price and curr_min_dif > prev_min_dif:
            latest = df.iloc[-1]
            return {
                "signal": "MACD 底背离",
                "strength": 5,
                "details": {
                    "前低": round(prev_min_price, 2),
                    "新低": round(curr_min_price, 2),
                    "前DIF": round(prev_min_dif, 4),
                    "新DIF": round(curr_min_dif, 4),
                }
            }
        return None
