#!/bin/bash
# CI のテスト（GitHub のランナーと devcontainer の中の両方で実行する。先に postCreateCommand.bash を済ませておく）
# .github/ci/problems/ の問題を problems/ にコピーし、3 つの言語の解答が手元のテストを通ることなどを確かめる
# LeetCode にはつながない
set -euo pipefail
cd "$(dirname "$0")/../.."

cp -r .github/ci/problems/. problems/
lc sync

for d in .github/ci/problems/*/; do
    p="problems/$(basename "$d")"
    for f in solution.cpp solution.rs solution.py; do
        lc test "$p/$f"
    done
done

# LeetCode と同じ最適化でのビルド
lc test --release problems/0146-lru-cache/solution.cpp
lc test --release problems/0146-lru-cache/solution.rs

# F5 のデバッグの準備（.vscode/launch.json が見る .build/current/）
lc build problems/0001-two-sum/solution.cpp
lc build problems/0001-two-sum/solution.rs
lc build problems/0189-rotate-array/stress/naive.py
test -x .build/current/cpp
test -x .build/current/rust
grep -q naive.py .build/current/python

# ランダムテスト（正しい解答なので、反例は見つからない）
lc stress hack problems/0189-rotate-array/solution.cpp --max 30

# 木とグラフの可視化
printf '[3,9,20,null,null,15,7]\n' > input.txt
python3 scripts/visualize.py tree input.txt
printf '[[0,1],[1,2],[2,0]]\n3\n' > input.txt
python3 scripts/visualize.py graph input.txt

# Rust の自動フォーマット（support/rust と、テスト用の解答）
cargo fmt --all --check
