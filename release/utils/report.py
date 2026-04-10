"""
报告格式化输出
"""
import json
import csv
from datetime import datetime
from pathlib import Path
from tabulate import tabulate


def format_table(results: list[dict]) -> str:
    """表格格式输出"""
    if not results:
        return "未找到符合条件的股票"

    rows = []
    for r in results:
        signal_str = " | ".join(
            f"[{s['strategy']}] {s['signal']}" for s in r["signals"]
        )
        rows.append([
            r["code"],
            r["name"],
            r["close"],
            f"{r['pct_chg']}%",
            signal_str,
            r["score"],
        ])

    headers = ["代码", "名称", "现价", "涨跌幅", "信号", "评分"]
    return tabulate(rows, headers=headers, tablefmt="grid", stralign="left")


def format_json(results: list[dict]) -> str:
    """JSON 格式输出"""
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
    """CSV 格式输出"""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["代码", "名称", "现价", "涨跌幅", "信号", "评分"])
        for r in results:
            signal_str = " | ".join(
                f"[{s['strategy']}] {s['signal']}" for s in r["signals"]
            )
            writer.writerow([r["code"], r["name"], r["close"],
                             f"{r['pct_chg']}%", signal_str, r["score"]])
    return path


def format_summary(results: list[dict]) -> str:
    """生成摘要报告"""
    if not results:
        return "📊 扫描完成, 未找到符合条件的股票"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"📊 A 股策略选股报告",
        f"时间: {now}",
        f"符合条件: {len(results)} 只",
        "=" * 50,
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

    lines.append("=" * 50)
    lines.append("")

    # 列出前 10 只
    for i, r in enumerate(results[:10], 1):
        signal_str = " + ".join(s["strategy"] for s in r["signals"])
        lines.append(
            f"{i:2d}. {r['code']} {r['name']}  "
            f"¥{r['close']} ({r['pct_chg']:+.2f}%)  "
            f"评分:{r['score']}  [{signal_str}]"
        )

    if len(results) > 10:
        lines.append(f"    ... 还有 {len(results) - 10} 只")

    return "\n".join(lines)


def save_results(results: list[dict], output_dir: str = "output",
                  fmt: str = "table"):
    """保存结果到文件"""
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # 始终保存 JSON
    json_path = f"{output_dir}/scan_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(format_json(results))

    # 保存 CSV
    csv_path = f"{output_dir}/scan_{timestamp}.csv"
    format_csv(results, csv_path)

    # 保存摘要
    summary_path = f"{output_dir}/scan_{timestamp}_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(format_summary(results))

    return {
        "json": json_path,
        "csv": csv_path,
        "summary": summary_path,
    }
