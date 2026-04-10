"""
策略基类
"""
from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    """策略基类"""

    def __init__(self, name: str, params: dict = None):
        self.name = name
        self.params = params or {}

    @abstractmethod
    def check(self, df: pd.DataFrame) -> dict | None:
        """
        检查股票是否符合策略条件
        返回 None 表示不符合, 返回 dict 表示信号详情
        dict 中应包含:
          - signal: 信号描述
          - strength: 信号强度 (1-5)
          - details: 具体指标值
        """
        pass

    def __repr__(self):
        return f"<{self.name}>"
