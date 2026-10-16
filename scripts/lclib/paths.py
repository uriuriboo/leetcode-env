"""リポジトリ内の場所と、外部コマンドの場所

ワークスペースのパスはハードコードせず、このファイルの場所から求める（/workspaces/<フォルダ名> のどこにあっても動く）
"""

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBLEMS = ROOT / "problems"
SUPPORT = ROOT / "support"
INPUT_TXT = ROOT / "input.txt"

# ビルドの成果物。devcontainer では名前付きボリュームにマウントする（Windows の bind mount は I/O が遅いため）
BUILD = ROOT / ".build"
CARGO_TARGET = BUILD / "cargo"  # .cargo/config.toml の target-dir と合わせる
CURRENT = BUILD / "current"  # 最後にビルドした問題（F5 のデバッグはここを見る）

CPP_HEADER = SUPPORT / "cpp" / "leetcode.hpp"
CPP_CORE = SUPPORT / "cpp" / "leetcode_core.hpp"  # プリコンパイルする本体
PY_RUNNER = SUPPORT / "python" / "lc_runner.py"

# 解答を動かす Python。LeetCode と同じ 3.14 を uv で入れている（.devcontainer/Dockerfile）
PYTHON = os.environ.get("LC_PYTHON") or shutil.which("python3.14") or sys.executable


def rel(path):
    """表示用に、リポジトリからの相対パスにする"""
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)
