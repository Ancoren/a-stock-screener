#!/usr/bin/env python3
"""
A 股策略选股系统
用法:
  python main.py                    # 使用默认配置扫描
  python main.py -c config.yaml    # 指定配置文件
  python main.py --pool hs300      # 扫描沪深300
  python main.py --pool custom --codes 600519,000858  # 自定义股票
  python main.py --strategies ma_cross,macd          # 只用指定策略
  python main.py --json            # JSON 输出
  python main.py --no-save         # 不保存文件
"""
import argparse
import logging
import sys
import os

# 确保能找到同目录下的模块和配置
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
from scanner import StockScanner, load_config
from utils.report import format_table, format_json, format_summary, save_results

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="A 股策略选股系统")
    parser.add_argument("-c", "--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--pool", choices=["all", "hs300", "zz500", "custom"],
                        help="股票池覆盖")
    parser.add_argument("--codes", help="自定义股票代码, 逗号分隔")
    parser.add_argument("--strategies", help="启用策略, 逗号分隔")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--no-save", action="store_true", help="不保存文件")
    parser.add_argument("--summary", action="store_true", default=True,
                        help="输出摘要报告")
    return parser.parse_args()


def override_config(config: dict, args) -> dict:
    """命令行参数覆盖配置"""
    if args.pool:
        config["scan"]["pool"] = args.pool
    if args.codes:
        config["scan"]["pool"] = "custom"
        config["scan"]["custom_codes"] = [c.strip() for c in args.codes.split(",")]
    if args.strategies:
        enabled = [s.strip() for s in args.strategies.split(",")]
        for name in config["strategies"]:
            config["strategies"][name]["enabled"] = name in enabled
    return config


def main():
    args = parse_args()

    # 加载并覆盖配置
    config = load_config(args.config)
    config = override_config(config, args)

    # 临时写回覆盖的配置 (scanner 会重新读取)
    import tempfile, os
    tmp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml",
                                              delete=False, encoding="utf-8")
    yaml.dump(config, tmp_config, allow_unicode=True, default_flow_style=False)
    tmp_config.close()

    try:
        # 执行扫描
        scanner = StockScanner(tmp_config.name)
        results = scanner.scan()

        # 输出
        if args.json:
            print(format_json(results))
        else:
            print(format_summary(results))

        # 保存
        if not args.no_save and results:
            paths = save_results(results, config["output"]["output_dir"])
            print(f"\n文件已保存:")
            for fmt, path in paths.items():
                print(f"  {fmt}: {path}")

    finally:
        os.unlink(tmp_config.name)

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
