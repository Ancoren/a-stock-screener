"""
放量突破策略
放量突破阻力位/前高
"""
import pandas as pd
from .base import BaseStrategy


class VolumeBreakoutStrategy(BaseStrategy):

    def __init__(self, params: dict = None):
        super().__init__("放量突破", params)
        self.vol_multiplier = self.params.get("vol_multiplier", 2.0)
        self.window = self.params.get("window", 20)

    def check(self, df: pd.DataFrame) -> dict | None:
        if len(df) < self.window + 5:
            return None
        if "VOL_MA" not in df.columns:
            return None

        latest = df.iloc[-1]
        close = latest["close"]
        vol = latest["volume"]
        vol_ma = latest["VOL_MA"]

        if pd.isna(vol_ma) or vol_ma == 0:
            return None

        vol_ratio = vol / vol_ma

        # 放量
        if vol_ratio < self.vol_multiplier:
            return None

        # 收阳
        is_positive = close >= latest["open"]
        if not is_positive:
            return None

        # 突破前高: 收盘价突破过去N天的最高价
        prev_high = df["high"].iloc[-self.window - 1:-1].max()
        if close <= prev_high:
            return None

        # 强势收盘: 收盘在当日振幅上方30%
        daily_range = latest["high"] - latest["low"]
        if daily_range > 0:
            close_pos = (close - latest["low"]) / daily_range
            if close_pos < 0.3:
                return None

        bias_20 = 0
        if "MA20" in latest and not pd.isna(latest["MA20"]):
            bias_20 = (close - latest["MA20"]) / latest["MA20"] * 100

        # 不能追高
        if abs(bias_20) > 8:
            return None

        strength = 5 if (vol_ratio >= 3 and bias_20 < 5) else 4

        return {
            "signal": f"放量突破 {vol_ratio:.1f}x (突破前高{prev_high:.2f})",
            "strength": strength,
            "details": {
                "前高": round(prev_high, 2),
                "收盘": round(close, 2),
                "量比": round(vol_ratio, 2),
                "乖离率": f"{bias_20:.2f}%",
            },
            "buy_price": round(prev_high, 2),
            "stop_loss": round(prev_high * 0.97, 2),
            "target_price": round(close * 1.08, 2),
            "risk_level": self._risk_from_bias(bias_20),
            "reason": "放量突破前高，趋势加速信号",
        }
