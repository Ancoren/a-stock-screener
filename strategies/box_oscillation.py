"""
箱体震荡策略
股价在箱体内震荡, 接近下沿时买入
"""
import pandas as pd
from .base import BaseStrategy


class BoxOscillationStrategy(BaseStrategy):

    def __init__(self, params: dict = None):
        super().__init__("箱体震荡", params)
        self.window = self.params.get("window", 20)
        self.range_pct = self.params.get("range_pct", 15)
        self.lower_pct = self.params.get("lower_pct", 25)

    def check(self, df: pd.DataFrame) -> dict | None:
        if len(df) < self.window + 5:
            return None

        window_df = df.tail(self.window)
        high = window_df["high"].max()
        low = window_df["low"].min()
        box_range = (high - low) / low * 100

        # 箱体振幅在合理范围 (range_pct% 以内)
        if box_range < 5 or box_range > self.range_pct:
            return None

        latest = df.iloc[-1]
        close = latest["close"]
        position = (close - low) / (high - low) * 100

        # 当前价格在箱体下沿区域 (lower_pct% 以内)
        if position > self.lower_pct:
            return None

        # 确认是震荡: 最近N天没有突破箱体
        recent_outside = ((window_df["high"] > high * 1.01) | (window_df["low"] < low * 0.99)).any()
        if recent_outside:
            return None

        bias_20 = 0
        if "MA20" in latest and not pd.isna(latest["MA20"]):
            bias_20 = (close - latest["MA20"]) / latest["MA20"] * 100

        return {
            "signal": f"箱体下沿 (位置{position:.0f}%)",
            "strength": 4,
            "details": {
                "箱体高点": round(high, 2),
                "箱体低点": round(low, 2),
                "箱体振幅": f"{box_range:.1f}%",
                "当前位置": f"{position:.0f}%",
            },
            "buy_price": round(close, 2),
            "stop_loss": round(low * 0.97, 2),
            "target_price": round(high, 2),
            "risk_level": self._risk_from_bias(bias_20),
            "reason": "箱体下沿买入，等待向上突破",
        }
