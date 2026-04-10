"""
A股数据获取模块
数据源: baostock (主力) + 本地缓存
"""
import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time
import json
import logging
import concurrent.futures

logger = logging.getLogger(__name__)

_bs_logged_in = False
CACHE_DIR = Path(__file__).parent.parent / "cache"
STOCK_LIST_CACHE = CACHE_DIR / "stock_list.json"
HISTORY_CACHE_DIR = CACHE_DIR / "history"


def _ensure_login():
    global _bs_logged_in
    if not _bs_logged_in:
        lg = bs.login()
        if lg.error_code == "0":
            _bs_logged_in = True
            logger.info("baostock login OK")
        else:
            logger.error(f"baostock login failed: {lg.error_msg}")


def _code_to_bs(code: str) -> str:
    if code.startswith("6") or code.startswith("9"):
        return f"sh.{code}"
    else:
        return f"sz.{code}"


# ========== Stock List Cache ==========

def _load_stock_list_cache() -> pd.DataFrame | None:
    if not STOCK_LIST_CACHE.exists():
        return None
    try:
        meta = json.loads(STOCK_LIST_CACHE.with_suffix(".meta.json").read_text("utf-8"))
        cached_date = meta.get("date", "")
        today = datetime.now().strftime("%Y-%m-%d")
        if cached_date != today:
            logger.info("Stock list cache expired, will refresh")
            return None
        df = pd.read_json(STOCK_LIST_CACHE, dtype={"代码": str})
        logger.info(f"Loaded stock list from cache: {len(df)} stocks")
        return df
    except Exception as e:
        logger.warning(f"Failed to load stock list cache: {e}")
        return None


def _save_stock_list_cache(df: pd.DataFrame):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_json(STOCK_LIST_CACHE, orient="records", force_ascii=False, indent=2)
    meta = {"date": datetime.now().strftime("%Y-%m-%d"), "count": len(df)}
    STOCK_LIST_CACHE.with_suffix(".meta.json").write_text(json.dumps(meta), "utf-8")
    logger.info(f"Stock list cached: {len(df)} stocks")


def get_stock_list(pool: str = "all", exclude_st: bool = True,
                   exclude_kcb: bool = False, exclude_bse: bool = True,
                   custom_codes: list = None) -> pd.DataFrame:
    if pool == "custom" and custom_codes:
        return pd.DataFrame({"代码": custom_codes, "名称": [""] * len(custom_codes)})

    # Try cache first
    cached = _load_stock_list_cache()
    if cached is not None:
        result = _filter_pool(cached, pool, exclude_st, exclude_kcb, exclude_bse)
        logger.info(f"Stock pool (cached): {pool}, {len(result)} stocks")
        return result

    # Fetch from baostock
    _ensure_login()
    rs = bs.query_stock_basic(code_name="")
    data = []
    while rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)

    df = df[df["code"].str.match(r"^(sh\.6|sz\.0|sz\.3)")]
    df["代码"] = df["code"].str.replace(r"^(sh|sz)\.", "", regex=True)
    df["名称"] = df["code_name"]

    if exclude_st:
        df = df[~df["名称"].str.contains(r"ST|退", na=False)]
    if exclude_kcb:
        df = df[~df["代码"].str.startswith("688")]
    if exclude_bse:
        df = df[~df["代码"].str.match(r"^8")]
    if "status" in df.columns:
        df = df[df["status"] == "1"]

    full_list = df[["代码", "名称"]].reset_index(drop=True)
    _save_stock_list_cache(full_list)

    result = _filter_pool(full_list, pool, exclude_st, exclude_kcb, exclude_bse)
    logger.info(f"Stock pool: {pool}, {len(result)} stocks")
    return result


def _filter_pool(df: pd.DataFrame, pool: str, exclude_st: bool,
                 exclude_kcb: bool, exclude_bse: bool) -> pd.DataFrame:
    result = df.copy()
    if pool == "hs300":
        result = result.head(300)
    elif pool == "zz500":
        result = result.head(500)
    return result.reset_index(drop=True)


# ========== History Data Cache ==========

def _history_cache_path(code: str) -> Path:
    return HISTORY_CACHE_DIR / f"{code}.csv"


def _load_history_cache(code: str, days: int) -> pd.DataFrame | None:
    path = _history_cache_path(code)
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, parse_dates=["date"])
        if df.empty:
            return None
        # Check freshness: latest date should be within 3 trading days
        latest = df["date"].max()
        now = datetime.now()
        gap = (now - latest).days
        if gap > 5:  # > 5 calendar days = stale (covers weekends)
            return None
        return df.tail(days).reset_index(drop=True)
    except Exception:
        return None


def _save_history_cache(code: str, df: pd.DataFrame):
    HISTORY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(_history_cache_path(code), index=False)


def get_stock_history(code: str, days: int = 120) -> pd.DataFrame:
    # Try cache
    cached = _load_history_cache(code, days)
    if cached is not None and len(cached) >= min(days, 30):
        return cached

    # Fetch from baostock
    _ensure_login()
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")
    bs_code = _code_to_bs(code)

    rs = bs.query_history_k_data_plus(
        bs_code,
        "date,open,high,low,close,volume,amount,turn,pctChg",
        start_date=start_date, end_date=end_date,
        frequency="d", adjustflag="2"
    )
    data = []
    while rs.next():
        data.append(rs.get_row_data())

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data, columns=rs.fields)
    col_map = {
        "date": "date", "open": "open", "close": "close",
        "high": "high", "low": "low", "volume": "volume",
        "amount": "amount", "turn": "turnover", "pctChg": "pct_chg"
    }
    df = df.rename(columns=col_map)
    for col in ["open", "high", "low", "close", "volume", "amount", "turnover", "pct_chg"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["close"])
    df = df.sort_values("date").tail(days).reset_index(drop=True)

    # Save to cache
    _save_history_cache(code, df)
    return df


def get_realtime_quote(codes: list) -> pd.DataFrame:
    _ensure_login()
    today = datetime.now().strftime("%Y-%m-%d")
    all_data = []
    for code in codes:
        bs_code = _code_to_bs(code)
        rs = bs.query_history_k_data_plus(
            bs_code, "date,open,high,low,close,volume",
            start_date=today, end_date=today, frequency="d"
        )
        while rs.next():
            row = rs.get_row_data()
            row.insert(0, code)
            all_data.append(row)
    if not all_data:
        return pd.DataFrame()
    return pd.DataFrame(all_data, columns=["代码", "date", "open", "high", "low", "close", "volume"])


# ========== Parallel Batch Fetch ==========

def _fetch_one(code: str, days: int) -> tuple[str, pd.DataFrame]:
    try:
        df = get_stock_history(code, days)
        return code, df
    except Exception as e:
        logger.warning(f"Failed {code}: {e}")
        return code, pd.DataFrame()


def fetch_all_stocks_history(codes: list, days: int = 120,
                              max_workers: int = 8) -> dict:
    """Batch fetch with threading + local cache"""
    total = len(codes)
    result = {}
    done = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_one, code, days): code for code in codes}
        for future in concurrent.futures.as_completed(futures):
            code, df = future.result()
            if not df.empty:
                result[code] = df
            done += 1
            if done % 200 == 0:
                logger.info(f"Fetched {done}/{total} stocks")

    logger.info(f"Done: {len(result)}/{total} success (cache used where available)")
    return result


def clear_cache():
    """Clear all cached data"""
    import shutil
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
    logger.info("Cache cleared")
