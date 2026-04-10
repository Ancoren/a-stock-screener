"""
技术指标计算模块
纯 pandas/numpy 实现, 无额外依赖
"""
import pandas as pd
import numpy as np


def calc_ma(df: pd.DataFrame, periods: list[int]) -> pd.DataFrame:
    """计算移动平均线"""
    for p in periods:
        df[f"MA{p}"] = df["close"].rolling(window=p).mean()
    return df


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    """指数移动平均"""
    return series.ewm(span=period, adjust=False).mean()


def calc_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26,
              signal: int = 9) -> pd.DataFrame:
    """MACD 指标"""
    ema_fast = calc_ema(df["close"], fast)
    ema_slow = calc_ema(df["close"], slow)
    df["MACD_DIF"] = ema_fast - ema_slow
    df["MACD_DEA"] = calc_ema(df["MACD_DIF"], signal)
    df["MACD_HIST"] = 2 * (df["MACD_DIF"] - df["MACD_DEA"])
    return df


def calc_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """RSI 相对强弱指标"""
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def calc_bollinger(df: pd.DataFrame, period: int = 20,
                   std_dev: int = 2) -> pd.DataFrame:
    """布林带"""
    ma = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    df["BOLL_MID"] = ma
    df["BOLL_UP"] = ma + std_dev * std
    df["BOLL_LOW"] = ma - std_dev * std
    return df


def calc_volume_ma(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """成交量均线"""
    df["VOL_MA"] = df["volume"].rolling(window=period).mean()
    return df


def calc_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """KDJ 随机指标"""
    low_n = df["low"].rolling(window=n).min()
    high_n = df["high"].rolling(window=n).max()
    rsv = (df["close"] - low_n) / (high_n - low_n).replace(0, np.nan) * 100
    df["KDJ_K"] = rsv.ewm(com=m1 - 1, adjust=False).mean()
    df["KDJ_D"] = df["KDJ_K"].ewm(com=m2 - 1, adjust=False).mean()
    df["KDJ_J"] = 3 * df["KDJ_K"] - 2 * df["KDJ_D"]
    return df


def add_all_indicators(df: pd.DataFrame, ma_periods: list[int] = None,
                        macd_params: dict = None, rsi_period: int = 14,
                        boll_params: dict = None, vol_period: int = 20) -> pd.DataFrame:
    """一次性添加所有常用指标"""
    if ma_periods is None:
        ma_periods = [5, 10, 20, 60]
    if macd_params is None:
        macd_params = {"fast": 12, "slow": 26, "signal": 9}
    if boll_params is None:
        boll_params = {"period": 20, "std_dev": 2}

    df = calc_ma(df, ma_periods)
    df = calc_macd(df, **macd_params)
    df = calc_rsi(df, rsi_period)
    df = calc_bollinger(df, **boll_params)
    df = calc_volume_ma(df, vol_period)
    df = calc_kdj(df)
    return df
