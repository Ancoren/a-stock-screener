"""
缩量回踩策略
趋势中的缩量回调到均线支撑位
"""
import pandas as pd
from .base import BaseStrategy


class ShrinkPullbackStrategy(BaseStrategy):

    def __init__(self, params: dict = None):
        super().__init__("缩量回踩", params)
        self.vol_threshold = self.params.get("vol_threshold", 0.7)
        self.bias_threshold = self.params.get("bias_threshold", 2.0)

    def check(self, df: pd.DataFrame) -> dict | None:
        required = ["MA5", "MA10", "MA20", "VOL_MA"]
        for c in required:
            if c not in df.columns:
                return None

        latest = df.iloc[-1]
        close = latest["close"]
        ma5 = latest["MA5"]
        ma10 = latest["MA10"]
        ma20 = latest["MA20"]
        vol = latest["volume"]
        vol_ma = latest["VOL_MA"]

        if pd.isna(ma5) or pd.isna(ma10) or pd.isna(vol_ma) or vol_ma == 0:
            return None

        vol_ratio = vol / vol_ma

        # 前提: 上升趋势 (MA5 > MA10 > MA20)
        if not (ma5 > ma10 > ma20):
            return None

        # 缩量: 当前成交量 < 均量的阈值倍
        if vol_ratio >= self.vol_threshold:
            return None

        # 回踩到 MA5 附近 (1%) 或 MA10 附近 (2%)
        bias_ma5 = abs(close - ma5) / ma5 * 100
        bias_ma10 = abs(close - ma10) / ma10 * 100

        if bias_ma5 <= 1.0:
            support = "MA5"
            support_price = ma5
            strength = 5
        elif bias_ma10 <= 2.0:
            support = "MA10"
            support_price = ma10
            strength = 4
        else:
            return None

        # 乖离率检查: 不追高
        bias_20 = (close - ma20) / ma20 * 100
        if abs(bias_20) > 5:
            return None

        return {
            "signal": f"缩量回踩{support} (量比{vol_ratio:.2f})",
            "strength": strength,
            "details": {
                "支撑位": support,
                "支撑价": round(support_price, 2),
                "量比": round(vol_ratio, 2),
                "乖离率MA20": f"{bias_20:.2f}%",
            },
            "buy_price": round(support_price, 2),
            "stop_loss": round(ma20, 2),
            "target_price": round(close * 1.05, 2),
            "risk_level": self._risk_from_bias(bias_20),
            "reason": f"缩量回踩{support}支撑，趋势延续信号",
        }
