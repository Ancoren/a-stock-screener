#!/usr/bin/env python3
"""A股策略选股系统 - 可执行入口"""
import sys
import os

# 确保能找到同目录下的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    sys.exit(main())
