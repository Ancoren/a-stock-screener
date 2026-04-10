"""
技术指标计算模块
纯 pandas/numpy 实现, 无额外依赖
"""
import pandas as pd
import numpy as np


def calc_ma(df: pd.DataFrame, periods: list[int]) -> pd.DataFrame:
    for p in periods:
        df[f"MA{p}"] = df["close"].rolling(window=p).mean()
    return df


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calc_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26,
              signal: int = 9) -> pd.DataFrame:
    ema_fast = calc_ema(df["close"], fast)
    ema_slow = calc_ema(df["close"], slow)
    df["MACD_DIF"] = ema_fast - ema_slow
    df["MACD_DEA"] = calc_ema(df["MACD_DIF"], signal)
    df["MACD_HIST"] = 2 * (df["MACD_DIF"] - df["MACD_DEA"])
    return df


def calc_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
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
    ma = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    df["BOLL_MID"] = ma
    df["BOLL_UP"] = ma + std_dev * std
    df["BOLL_LOW"] = ma - std_dev * std
    return df


def calc_volume_ma(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    df["VOL_MA"] = df["volume"].rolling(window=period).mean()
    return df


def calc_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    low_n = df["low"].rolling(window=n).min()
    high_n = df["high"].rolling(window=n).max()
    rsv = (df["close"] - low_n) / (high_n - low_n).replace(0, np.nan) * 100
    df["KDJ_K"] = rsv.ewm(com=m1 - 1, adjust=False).mean()
    df["KDJ_D"] = df["KDJ_K"].ewm(com=m2 - 1, adjust=False).mean()
    df["KDJ_J"] = 3 * df["KDJ_K"] - 2 * df["KDJ_D"]
    return df


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """ATR 真实波幅"""
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(window=period).mean()
    return df


def calc_deviation_rate(df: pd.DataFrame, period: int = 5) -> pd.DataFrame:
    """乖离率 = (收盘价 - MA) / MA * 100"""
    ma_col = f"MA{period}"
    if ma_col in df.columns:
        df[f"BIAS{period}"] = (df["close"] - df[ma_col]) / df[ma_col] * 100
    return df


def calc_support_resistance(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """计算支撑位和阻力位 (最近N天的高低点)"""
    df["RESISTANCE"] = df["high"].rolling(window=window).max()
    df["SUPPORT"] = df["low"].rolling(window=window).min()
    # 近期高点 (排除最新一天)
    df["RESISTANCE_RECENT"] = df["high"].shift(1).rolling(window=window).max()
    df["SUPPORT_RECENT"] = df["low"].shift(1).rolling(window=window).min()
    return df


def check_bullish_alignment(df: pd.DataFrame) -> bool:
    """检查多头排列 MA5 > MA10 > MA20 > MA60"""
    latest = df.iloc[-1]
    cols = ["MA5", "MA10", "MA20", "MA60"]
    for c in cols:
        if c not in df.columns or pd.isna(latest[c]):
            return False
    return latest["MA5"] > latest["MA10"] > latest["MA20"] > latest["MA60"]


def add_all_indicators(df: pd.DataFrame, ma_periods: list[int] = None,
                        macd_params: dict = None, rsi_period: int = 14,
                        boll_params: dict = None, vol_period: int = 20) -> pd.DataFrame:
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
    df = calc_atr(df)
    df = calc_support_resistance(df)
    # 乖离率
    for p in ma_periods:
        df = calc_deviation_rate(df, p)
    return df
