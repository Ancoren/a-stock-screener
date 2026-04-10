"""
报告格式化输出
"""
import json
import csv
from datetime import datetime
from pathlib import Path
from tabulate import tabulate


def format_table(results: list[dict]) -> str:
    if not results:
        return "未找到符合条件的股票"

    rows = []
    for r in results:
        signal_str = " | ".join(
            f"[{s['strategy']}] {s['signal']}" for s in r["signals"]
        )
        risk = r.get("risk_level", "-")
        risk_map = {"low": "低", "medium": "中", "high": "高"}
        rows.append([
            r["code"], r["name"], r["close"],
            f"{r['pct_chg']}%", signal_str,
            r.get("buy_price", "-"), r.get("stop_loss", "-"),
            r.get("target_price", "-"), risk_map.get(risk, risk),
            r["score"],
        ])

    headers = ["代码", "名称", "现价", "涨跌幅", "信号", "买入价", "止损", "目标价", "风险", "评分"]
    return tabulate(rows, headers=headers, tablefmt="grid", stralign="left")


def format_json(results: list[dict]) -> str:
    def _convert(obj):
        import numpy as np
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    return json.dumps(results, ensure_ascii=False, indent=2, default=_convert)


def format_csv(results: list[dict], path: str) -> str:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["代码", "名称", "现价", "涨跌幅", "信号", "买入价", "止损", "目标价", "风险", "评分"])
        for r in results:
            signal_str = " | ".join(
                f"[{s['strategy']}] {s['signal']}" for s in r["signals"]
            )
            writer.writerow([
                r["code"], r["name"], r["close"],
                f"{r['pct_chg']}%", signal_str,
                r.get("buy_price", ""), r.get("stop_loss", ""),
                r.get("target_price", ""), r.get("risk_level", ""),
                r["score"],
            ])
    return path


def format_summary(results: list[dict]) -> str:
    if not results:
        return "扫描完成，未找到符合条件的股票"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"A股策略选股报告",
        f"时间: {now}",
        f"符合条件: {len(results)} 只",
        "=" * 60,
    ]

    # 按策略分组统计
    strategy_count = {}
    for r in results:
        for s in r["signals"]:
            name = s["strategy"]
            strategy_count[name] = strategy_count.get(name, 0) + 1

    lines.append("策略命中统计:")
    for name, count in sorted(strategy_count.items(), key=lambda x: -x[1]):
        lines.append(f"  {name}: {count} 只")

    # 风险分布
    risk_count = {"low": 0, "medium": 0, "high": 0}
    for r in results:
        risk = r.get("risk_level", "medium")
        risk_count[risk] = risk_count.get(risk, 0) + 1
    lines.append(f"风险分布: 低风险{risk_count['low']} | 中风险{risk_count['medium']} | 高风险{risk_count['high']}")

    lines.append("=" * 60)
    lines.append("")

    # 列出前15只，带交易计划
    risk_map = {"low": "低", "medium": "中", "high": "高"}
    for i, r in enumerate(results[:15], 1):
        signal_str = " + ".join(s["strategy"] for s in r["signals"])
        buy = f"买入:{r['buy_price']}" if r.get("buy_price") else ""
        sl = f"止损:{r['stop_loss']}" if r.get("stop_loss") else ""
        tp = f"目标:{r['target_price']}" if r.get("target_price") else ""
        risk = f"风险:{risk_map.get(r.get('risk_level',''), '-')}" if r.get("risk_level") else ""
        plan = " | ".join(x for x in [buy, sl, tp, risk] if x)

        lines.append(
            f"{i:2d}. {r['code']} {r['name']}  "
            f"¥{r['close']} ({r['pct_chg']:+.2f}%)  "
            f"评分:{r['score']}  [{signal_str}]"
        )
        if plan:
            lines.append(f"    >>> {plan}")
        if r.get("reason"):
            lines.append(f"    >>> 理由: {r['reason']}")

    if len(results) > 15:
        lines.append(f"    ... 还有 {len(results) - 15} 只")

    return "\n".join(lines)


def save_results(results: list[dict], output_dir: str = "output", fmt: str = "table"):
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    json_path = f"{output_dir}/scan_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(format_json(results))

    csv_path = f"{output_dir}/scan_{timestamp}.csv"
    format_csv(results, csv_path)

    summary_path = f"{output_dir}/scan_{timestamp}_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(format_summary(results))

    return {
        "json": json_path,
        "csv": csv_path,
        "summary": summary_path,
    }
