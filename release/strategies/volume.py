"""
放量策略
成交量突然放大
"""
import pandas as pd
from .base import BaseStrategy


class VolumeSurgeStrategy(BaseStrategy):

    def __init__(self, params: dict = None):
        super().__init__("放量", params)
        self.multiplier = self.params.get("surge_multiplier", 2.0)

    def check(self, df: pd.DataFrame) -> dict | None:
        if "VOL_MA" not in df.columns or "volume" not in df.columns:
            return None

        recent = df.tail(3)
        if len(recent) < 1:
            return None

        latest = recent.iloc[-1]
        vol_ma = latest["VOL_MA"]

        if pd.isna(vol_ma) or vol_ma == 0:
            return None

        ratio = latest["volume"] / vol_ma

        if ratio >= self.multiplier:
            # 检查是否收阳
            is_positive = latest["close"] >= latest["open"]
            strength = 4 if (ratio >= 3.0 and is_positive) else 3
            return {
                "signal": f"放量 {ratio:.1f}x {'收阳' if is_positive else '收阴'}",
                "strength": strength,
                "details": {
                    "成交量": f"{latest['volume'] / 10000:.0f}万",
                    "均量": f"{vol_ma / 10000:.0f}万",
                    "倍数": round(ratio, 2),
                    "涨跌幅": f"{latest.get('pct_chg', 0):.2f}%",
                }
            }
        return None
