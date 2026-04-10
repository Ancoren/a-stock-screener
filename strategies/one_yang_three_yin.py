"""
一阳三阴策略
一根大阳线后连续缩量小阴线回踩
"""
import pandas as pd
from .base import BaseStrategy


class OneYangThreeYinStrategy(BaseStrategy):

    def __init__(self, params: dict = None):
        super().__init__("一阳三阴", params)
        self.yang_pct = self.params.get("yang_pct", 3.0)

    def check(self, df: pd.DataFrame) -> dict | None:
        if "VOL_MA" not in df.columns:
            return None
        if len(df) < 6:
            return None

        recent = df.tail(5)
        if len(recent) < 5:
            return None

        # 第一天: 大阳线 (涨幅 > yang_pct)
        day1 = recent.iloc[0]
        pct1 = (day1["close"] - day1["open"]) / day1["open"] * 100
        if pct1 < self.yang_pct:
            return None

        # 后面3-4天: 小阴/小阳, 缩量, 不跌破大阳线开盘价
        all_ok = True
        for i in range(1, len(recent)):
            r = recent.iloc[i]
            body = abs(r["close"] - r["open"]) / r["open"] * 100
            # 实体要小
            if body > 2.5:
                all_ok = False
                break
            # 不能跌破大阳线开盘价
            if r["low"] < day1["open"]:
                all_ok = False
                break

        if not all_ok:
            return None

        # 缩量
        latest = df.iloc[-1]
        vol_ma = latest["VOL_MA"]
        if pd.isna(vol_ma) or vol_ma == 0:
            return None
        vol_ratio = latest["volume"] / vol_ma
        if vol_ratio > 1.0:
            return None

        close = latest["close"]
        ma5 = latest.get("MA5", close)
        bias_20 = 0
        if "MA20" in latest and not pd.isna(latest["MA20"]):
            bias_20 = (close - latest["MA20"]) / latest["MA20"] * 100

        return {
            "signal": f"一阳三阴 (大阳+{len(recent)-1}天缩量整理)",
            "strength": 4,
            "details": {
                "大阳涨幅": f"{pct1:.2f}%",
                "大阳开盘": round(day1["open"], 2),
                "量比": round(vol_ratio, 2),
                "当前价": round(close, 2),
            },
            "buy_price": round(close, 2),
            "stop_loss": round(day1["open"], 2),
            "target_price": round(day1["close"] * 1.05, 2),
            "risk_level": self._risk_from_bias(bias_20),
            "reason": "大阳线后缩量整理，蓄势待发",
        }
