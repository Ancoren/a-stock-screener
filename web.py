"""
A股策略选股系统 - Web 可视化界面
用法: python web.py [--port 8080]
"""
import sys
import os
import json
import argparse
import logging
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify, request
from scanner import StockScanner, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 全局缓存
_cache = {"results": None, "timestamp": None, "config": None}


def parse_args():
    parser = argparse.ArgumentParser(description="A股选股系统 Web 界面")
    parser.add_argument("-p", "--port", type=int, default=8080, help="端口号")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    return parser.parse_args()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config")
def api_config():
    config = load_config()
    return jsonify({
        "strategies": {k: {"enabled": v.get("enabled", False), "params": {pk: pv for pk, pv in v.items() if pk != "enabled"}}
                       for k, v in config.get("strategies", {}).items()},
        "pool": config.get("scan", {}).get("pool", "all"),
        "combination": config.get("combination", "any"),
    })


@app.route("/api/scan", methods=["POST"])
def api_scan():
    try:
        data = request.get_json(silent=True) or {}
        pool = data.get("pool")
        strategies = data.get("strategies")
        combination = data.get("combination")

        config = load_config()
        if pool:
            config["scan"]["pool"] = pool
        if combination:
            config["combination"] = combination
        if strategies:
            for name in config["strategies"]:
                config["strategies"][name]["enabled"] = name in strategies

        # 写临时配置
        import tempfile, yaml
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8")
        yaml.dump(config, tmp, allow_unicode=True, default_flow_style=False)
        tmp.close()

        scanner = StockScanner(tmp.name)
        results = scanner.scan()
        os.unlink(tmp.name)

        _cache["results"] = results
        _cache["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _cache["config"] = {
            "pool": pool or config["scan"]["pool"],
            "strategies": [k for k, v in config["strategies"].items() if v.get("enabled")],
            "combination": combination or config["combination"],
        }

        return jsonify({
            "success": True,
            "count": len(results),
            "timestamp": _cache["timestamp"],
            "results": results,
        })
    except Exception as e:
        logger.exception("扫描失败")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/results")
def api_results():
    return jsonify({
        "results": _cache["results"],
        "timestamp": _cache["timestamp"],
        "config": _cache["config"],
    })


@app.route("/api/stock/<code>")
def api_stock_detail(code):
    """获取单只股票的K线数据"""
    try:
        from data.fetcher import get_stock_history
        from utils.indicators import add_all_indicators

        days = int(request.args.get("days", 120))
        df = get_stock_history(code, days=days)
        if df.empty:
            return jsonify({"error": "未找到数据"}), 404

        df = add_all_indicators(df)

        # 转为 JSON
        klines = []
        for _, row in df.iterrows():
            klines.append({
                "date": row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"]),
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
                "volume": int(row["volume"]) if row["volume"] == row["volume"] else 0,
                "ma5": round(float(row.get("MA5", 0)), 2) if row.get("MA5") == row.get("MA5") else None,
                "ma10": round(float(row.get("MA10", 0)), 2) if row.get("MA10") == row.get("MA10") else None,
                "ma20": round(float(row.get("MA20", 0)), 2) if row.get("MA20") == row.get("MA20") else None,
                "ma60": round(float(row.get("MA60", 0)), 2) if row.get("MA60") == row.get("MA60") else None,
                "macd_dif": round(float(row.get("MACD_DIF", 0)), 4) if row.get("MACD_DIF") == row.get("MACD_DIF") else None,
                "macd_dea": round(float(row.get("MACD_DEA", 0)), 4) if row.get("MACD_DEA") == row.get("MACD_DEA") else None,
                "macd_hist": round(float(row.get("MACD_HIST", 0)), 4) if row.get("MACD_HIST") == row.get("MACD_HIST") else None,
                "rsi": round(float(row.get("RSI", 0)), 2) if row.get("RSI") == row.get("RSI") else None,
            })

        return jsonify({"code": code, "klines": klines})
    except Exception as e:
        logger.exception(f"获取 {code} 数据失败")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    args = parse_args()
    logger.info(f"启动 Web 界面: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
