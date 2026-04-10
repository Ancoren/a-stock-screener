"""
策略基类
"""
from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):

    def __init__(self, name: str, params: dict = None):
        self.name = name
        self.params = params or {}

    @abstractmethod
    def check(self, df: pd.DataFrame) -> dict | None:
        """
        返回 None 表示不符合, 返回 dict 包含:
          - signal: 信号描述
          - strength: 信号强度 (1-5)
          - details: 具体指标值
          - buy_price: 建议买入价 (可选)
          - stop_loss: 止损价 (可选)
          - target_price: 目标价 (可选)
          - risk_level: low/medium/high (可选)
          - reason: 买入理由 (可选)
        """
        pass

    def _risk_from_bias(self, bias: float) -> str:
        """根据乖离率判断风险"""
        if abs(bias) <= 2:
            return "low"
        elif abs(bias) <= 5:
            return "medium"
        return "high"

    def __repr__(self):
        return f"<{self.name}>"
