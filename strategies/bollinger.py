"""
布林带策略
下轨反弹 / 上轨突破
"""
import pandas as pd
from .base import BaseStrategy


class BollingerStrategy(BaseStrategy):

    def __init__(self, params: dict = None):
        super().__init__("布林带", params)
        self.mode = self.params.get("mode", "lower_bounce")

    def check(self, df: pd.DataFrame) -> dict | None:
        if "BOLL_LOW" not in df.columns:
            return None

        recent = df.tail(5)
        if len(recent) < 2:
            return None

        if self.mode == "lower_bounce":
            return self._check_lower_bounce(recent, df)
        elif self.mode == "upper_break":
            return self._check_upper_break(recent, df)
        return None

    def _check_lower_bounce(self, recent: pd.DataFrame, full: pd.DataFrame) -> dict | None:
        """下轨反弹: 价格触及或跌破下轨后回升到下轨上方"""
        for i in range(1, len(recent)):
            prev_low = recent.iloc[i - 1]["low"]
            prev_boll = recent.iloc[i - 1]["BOLL_LOW"]
            curr_close = recent.iloc[i]["close"]
            curr_boll = recent.iloc[i]["BOLL_LOW"]

            if prev_low <= prev_boll and curr_close > curr_boll:
                latest = full.iloc[-1]
                pct_from_low = (latest["close"] - latest["BOLL_LOW"]) / latest["BOLL_LOW"] * 100
                return {
                    "signal": f"布林带下轨反弹",
                    "strength": 4,
                    "details": {
                        "close": round(latest["close"], 2),
                        "下轨": round(latest["BOLL_LOW"], 2),
                        "距下轨": f"{pct_from_low:.2f}%",
                    }
                }
        return None

    def _check_upper_break(self, recent: pd.DataFrame, full: pd.DataFrame) -> dict | None:
        """上轨突破: 收盘价突破上轨"""
        for i in range(1, len(recent)):
            prev_close = recent.iloc[i - 1]["close"]
            prev_up = recent.iloc[i - 1]["BOLL_UP"]
            curr_close = recent.iloc[i]["close"]
            curr_up = recent.iloc[i]["BOLL_UP"]

            if prev_close <= prev_up and curr_close > curr_up:
                latest = full.iloc[-1]
                return {
                    "signal": "布林带上轨突破",
                    "strength": 4,
                    "details": {
                        "close": round(latest["close"], 2),
                        "上轨": round(latest["BOLL_UP"], 2),
                    }
                }
        return None
