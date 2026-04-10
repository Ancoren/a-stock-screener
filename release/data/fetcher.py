"""
A 股数据获取模块
数据源: baostock (主力) + akshare (备选)
"""
import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

_bs_logged_in = False


def _ensure_login():
    global _bs_logged_in
    if not _bs_logged_in:
        lg = bs.login()
        if lg.error_code == "0":
            _bs_logged_in = True
            logger.info("baostock 登录成功")
        else:
            logger.error(f"baostock 登录失败: {lg.error_msg}")


def _code_to_bs(code: str) -> str:
    """将股票代码转为 baostock 格式: 600519 -> sh.600519"""
    if code.startswith("6") or code.startswith("9"):
        return f"sh.{code}"
    else:
        return f"sz.{code}"


def get_stock_list(pool: str = "all", exclude_st: bool = True,
                   exclude_kcb: bool = False, exclude_bse: bool = True,
                   custom_codes: list = None) -> pd.DataFrame:
    """获取股票列表 (baostock)"""
    if pool == "custom" and custom_codes:
        return pd.DataFrame({"代码": custom_codes, "名称": [""] * len(custom_codes)})

    _ensure_login()

    # baostock 获取所有股票
    today = datetime.now().strftime("%Y-%m-%d")
    rs = bs.query_stock_basic(code_name="")

    data = []
    while rs.next():
        data.append(rs.get_row_data())

    df = pd.DataFrame(data, columns=rs.fields)

    # 只保留 A 股, 去掉指数
    df = df[df["code"].str.match(r"^(sh\.6|sz\.0|sz\.3)")]
    df["代码"] = df["code"].str.replace(r"^(sh|sz)\.", "", regex=True)
    df["名称"] = df["code_name"]

    # 排除 ST
    if exclude_st:
        df = df[~df["名称"].str.contains(r"ST|退", na=False)]

    # 排除科创板
    if exclude_kcb:
        df = df[~df["代码"].str.startswith("688")]

    # 排除北交所
    if exclude_bse:
        df = df[~df["代码"].str.match(r"^8")]

    # 排除已退市
    if "status" in df.columns:
        df = df[df["status"] == "1"]

    result = df[["代码", "名称"]].reset_index(drop=True)

    if pool == "hs300":
        # 沪深300: 简单取市值大的 (需要额外查询)
        result = result.head(300)
    elif pool == "zz500":
        result = result.head(500)

    logger.info(f"股票池: {pool}, 共 {len(result)} 只")
    return result


def get_stock_history(code: str, days: int = 120) -> pd.DataFrame:
    """获取单只股票的历史日线数据 (baostock)"""
    _ensure_login()

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")

    bs_code = _code_to_bs(code)

    rs = bs.query_history_k_data_plus(
        bs_code,
        "date,open,high,low,close,volume,amount,turn,pctChg",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="2"  # 前复权
    )

    data = []
    while rs.next():
        data.append(rs.get_row_data())

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data, columns=rs.fields)

    # 标准化列名
    col_map = {
        "date": "date", "open": "open", "close": "close",
        "high": "high", "low": "low", "volume": "volume",
        "amount": "amount", "turn": "turnover", "pctChg": "pct_chg"
    }
    df = df.rename(columns=col_map)

    # 类型转换
    for col in ["open", "high", "low", "close", "volume", "amount", "turnover", "pct_chg"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["close"])
    df = df.sort_values("date").tail(days).reset_index(drop=True)
    return df


def get_realtime_quote(codes: list) -> pd.DataFrame:
    """获取实时行情 (baostock)"""
    _ensure_login()
    today = datetime.now().strftime("%Y-%m-%d")

    all_data = []
    for code in codes:
        bs_code = _code_to_bs(code)
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,volume",
            start_date=today, end_date=today,
            frequency="d"
        )
        while rs.next():
            row = rs.get_row_data()
            row.insert(0, code)
            all_data.append(row)

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data, columns=["代码", "date", "open", "high", "low", "close", "volume"])
    return df


def fetch_all_stocks_history(codes: list, days: int = 120,
                              batch_sleep: float = 0.2) -> dict:
    """批量获取历史数据, 返回 {code: DataFrame}"""
    _ensure_login()
    result = {}
    total = len(codes)

    for i, code in enumerate(codes):
        try:
            df = get_stock_history(code, days)
            if not df.empty:
                result[code] = df
        except Exception as e:
            logger.warning(f"获取 {code} 失败: {e}")

        if (i + 1) % 100 == 0:
            logger.info(f"已获取 {i + 1}/{total} 只股票数据")
        time.sleep(batch_sleep)

    logger.info(f"数据获取完成: {len(result)}/{total} 成功")
    return result
