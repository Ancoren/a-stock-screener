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

        # 取最近 N+1 天数据检查金叉
        recent = df.tail(self.within_days + 2).copy()
        if len(recent) < 2:
            return None

        # 检查金叉: 之前短均线 <= 长均线, 之后短均线 > 长均线
        for i in range(1, len(recent)):
            prev = recent.iloc[i - 1]
            curr = recent.iloc[i]
            if (prev[short_col] <= prev[long_col] and
                    curr[short_col] > curr[long_col]):
                days_ago = len(recent) - 1 - i
                latest = df.iloc[-1]
                return {
                    "signal": f"MA{self.short}/MA{self.long} 金叉 ({days_ago}天前)",
                    "strength": 4 if days_ago <= 1 else 3,
                    "details": {
                        f"MA{self.short}": round(latest[short_col], 2),
                        f"MA{self.long}": round(latest[long_col], 2),
                        "close": round(latest["close"], 2),
                    }
                }
        return None
