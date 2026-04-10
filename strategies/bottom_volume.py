"""
底部放量策略
低位突然放量, 可能是主力建仓
"""
import pandas as pd
from .base import BaseStrategy


class BottomVolumeStrategy(BaseStrategy):

    def __init__(self, params: dict = None):
        super().__init__("底部放量", params)
        self.low_pct = self.params.get("low_pct", 30)
        self.vol_multiplier = self.params.get("vol_multiplier", 2.0)

    def check(self, df: pd.DataFrame) -> dict | None:
        if len(df) < 60:
            return None
        if "VOL_MA" not in df.columns:
            return None

        latest = df.iloc[-1]
        close = latest["close"]
        vol = latest["volume"]
        vol_ma = latest["VOL_MA"]

        if pd.isna(vol_ma) or vol_ma == 0:
            return None

        # 位置: 在60日低点区域 (当前价在60日最低价的 +low_pct% 范围内)
        low_60 = df["low"].tail(60).min()
        range_60 = df["high"].tail(60).max() - low_60
        if range_60 == 0:
            return None
        position = (close - low_60) / range_60 * 100
        if position > self.low_pct:
            return None

        # 放量: 今日量 > 均量 * multiplier
        vol_ratio = vol / vol_ma
        if vol_ratio < self.vol_multiplier:
            return None

        # 收阳更好
        is_positive = close >= latest["open"]
        strength = 4 if (is_positive and vol_ratio >= 3) else 3

        bias_20 = 0
        if "MA20" in latest and not pd.isna(latest["MA20"]):
            bias_20 = (close - latest["MA20"]) / latest["MA20"] * 100

        return {
            "signal": f"底部放量 {vol_ratio:.1f}x {'收阳' if is_positive else '收阴'}",
            "strength": strength,
            "details": {
                "60日位置": f"{position:.1f}%",
                "量比": round(vol_ratio, 2),
                "60日低点": round(low_60, 2),
                "当前价": round(close, 2),
            },
            "buy_price": round(close, 2),
            "stop_loss": round(low_60 * 0.98, 2),
            "target_price": round(close * 1.08, 2),
            "risk_level": "medium",
            "reason": "低位放量，可能是主力建仓信号",
        }
