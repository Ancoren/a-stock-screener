"""
趋势策略
多头排列: MA5 > MA10 > MA20 > MA60
"""
import pandas as pd
from .base import BaseStrategy


class TrendStrategy(BaseStrategy):

    def __init__(self, params: dict = None):
        super().__init__("趋势", params)
        self.mode = self.params.get("mode", "bullish_alignment")

    def check(self, df: pd.DataFrame) -> dict | None:
        required = ["MA5", "MA10", "MA20", "MA60"]
        if not all(col in df.columns for col in required):
            return None

        latest = df.iloc[-1]
        ma5, ma10, ma20, ma60 = latest["MA5"], latest["MA10"], latest["MA20"], latest["MA60"]

        if any(pd.isna(v) for v in [ma5, ma10, ma20, ma60]):
            return None

        if self.mode == "bullish_alignment":
            if ma5 > ma10 > ma20 > ma60:
                # 计算排列强度: 各均线间距
                spread_5_10 = (ma5 - ma10) / ma10 * 100
                spread_10_20 = (ma10 - ma20) / ma20 * 100
                spread_20_60 = (ma20 - ma60) / ma60 * 100
                avg_spread = (spread_5_10 + spread_10_20 + spread_20_60) / 3

                # 检查是否刚形成多头排列 (近5天内)
                recent_5 = df.tail(10)
                was_not_aligned = False
                for i in range(len(recent_5) - 5):
                    row = recent_5.iloc[i]
                    if not (row["MA5"] > row["MA10"] > row["MA20"] > row["MA60"]):
                        was_not_aligned = True
                        break

                strength = 5 if was_not_aligned else 3

                return {
                    "signal": f"多头排列 {'(新形成)' if was_not_aligned else '(持续)'}",
                    "strength": strength,
                    "details": {
                        "MA5": round(ma5, 2),
                        "MA10": round(ma10, 2),
                        "MA20": round(ma20, 2),
                        "MA60": round(ma60, 2),
                        "间距": f"{avg_spread:.2f}%",
                    }
                }
        return None
