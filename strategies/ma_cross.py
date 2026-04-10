"""
均线金叉策略
MA5 上穿 MA20 形成金叉
"""
import pandas as pd
from .base import BaseStrategy


class MACrossStrategy(BaseStrategy):

    def __init__(self, params: dict = None):
        super().__init__("均线金叉", params)
        self.short = self.params.get("short_period", 5)
        self.long = self.params.get("long_period", 20)
        self.within_days = self.params.get("within_days", 3)

    def check(self, df: pd.DataFrame) -> dict | None:
        short_col = f"MA{self.short}"
        long_col = f"MA{self.long}"

        if short_col not in df.columns or long_col not in df.columns:
            return None

        recent = df.tail(self.within_days + 2).copy()
        if len(recent) < 2:
            return None

        for i in range(1, len(recent)):
            prev = recent.iloc[i - 1]
            curr = recent.iloc[i]
            if (prev[short_col] <= prev[long_col] and
                    curr[short_col] > curr[long_col]):
                days_ago = len(recent) - 1 - i
                latest = df.iloc[-1]
                close = latest["close"]
                cross_price = curr[short_col]

                # 量能确认
                vol_ok = ""
                if "VOL_MA" in latest and not pd.isna(latest["VOL_MA"]) and latest["VOL_MA"] > 0:
                    vol_ratio = latest["volume"] / latest["VOL_MA"]
                    vol_ok = f"量比{vol_ratio:.1f}"

                bias_20 = 0
                if "MA20" in latest and not pd.isna(latest["MA20"]):
                    bias_20 = (close - latest["MA20"]) / latest["MA20"] * 100

                strength = 4 if days_ago <= 1 else 3

                return {
                    "signal": f"MA{self.short}/MA{self.long} 金叉 ({days_ago}天前) {vol_ok}".strip(),
                    "strength": strength,
                    "details": {
                        f"MA{self.short}": round(latest[short_col], 2),
                        f"MA{self.long}": round(latest[long_col], 2),
                        "close": round(close, 2),
                    },
                    "buy_price": round(cross_price, 2),
                    "stop_loss": round(latest.get(long_col, close * 0.95), 2),
                    "target_price": round(close * 1.06, 2),
                    "risk_level": self._risk_from_bias(bias_20),
                    "reason": f"均线金叉，趋势反转信号",
                }
        return None
