"""LeetCode の入力（input.txt）にある木やグラフを Graphviz で PNG にする

使い方:
    python3 visualize.py tree  input.txt                 二分木（[3,9,20,null,null,15,7] の形式）
    python3 visualize.py graph input.txt [--directed]    グラフ

input.txt の各行を JSON として読み、使えそうな行を自動で選ぶ
- tree : 数値と null だけが並んだ配列の行
- graph: 配列の配列の行。隣接リスト（i 番目が頂点 i から出る辺の行き先。clone-graph などの形式）として
         辻褄が合えば隣接リスト、そうでなければ辺のリスト（[u, v] か [u, v, 重み]）として読む
         整数だけの行があれば頂点数 n とみなし、辺の無い頂点も描く
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections import deque


def read_values(path):
    values = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                values.append(json.loads(line))
            except ValueError:
                pass
    return values


def is_tree_row(v):
    return isinstance(v, list) and all(x is None or (isinstance(x, int) and not isinstance(x, bool)) for x in v)


def is_nested_int_row(v):
    return isinstance(v, list) and v and all(isinstance(r, list) and all(isinstance(x, (int, float)) for x in r) for r in v)


def tree_dot(level):
    """レベル順の配列から木を作る。子が片方だけのときは、反対側に見えない頂点を置いて左右が分かるようにする"""
    out = ["digraph T {", "  node [shape=circle];", "  ordering=out;"]
    if not level or level[0] is None:
        out.append('  empty [shape=plaintext, label="（空の木）"];')
        return "\n".join(out + ["}"]) + "\n"
    out.append('  n0 [label="{}"];'.format(level[0]))
    queue = deque([0])
    i = 1
    while queue and i < len(level):
        parent = queue.popleft()
        children = [j if j < len(level) and level[j] is not None else None for j in (i, i + 1)]
        i += 2
        if children == [None, None]:
            continue
        for side, j in zip("LR", children):
            if j is None:
                out.append('  x{}{} [style=invis, label=""];'.format(parent, side))
                out.append("  n{} -> x{}{} [style=invis];".format(parent, parent, side))
            else:
                out.append('  n{} [label="{}"];'.format(j, level[j]))
                out.append("  n{} -> n{};".format(parent, j))
                queue.append(j)
    return "\n".join(out + ["}"]) + "\n"


def adjacency_base(rows):
    """rows が隣接リスト（i 番目が頂点 i から出る辺の行き先）なら頂点番号の始まり（0 か 1）、そうでなければ None"""
    n = len(rows)
    values = [v for r in rows for v in r]
    if any(not isinstance(v, int) for v in values):
        return None
    for base in (1, 0):
        if all(base <= v < base + n for v in values) and all(
            i + base in rows[v - base] for i, r in enumerate(rows) for v in r
        ):
            return base
    return None


def graph_dot(rows, n, directed):
    kind, arrow = ("digraph", "->") if directed else ("graph", "--")
    out = [kind + " G {", "  node [shape=circle];"]
    base = adjacency_base(rows)
    if base is None and not all(len(r) in (2, 3) for r in rows):
        # 長さがそろっていないので隣接リスト。0 が出てくれば 0 始まり
        base = 0 if any(v == 0 for r in rows for v in r) else 1
    if base is None:
        # 辺のリスト（[u, v] か [u, v, 重み]）
        edges = [(r[0], r[1], r[2] if len(r) == 3 else None) for r in rows]
        nodes = {u for u, v, _ in edges} | {v for u, v, _ in edges}
        if n is not None:
            # 0 始まりか 1 始まりかを、辺に出てくる頂点番号から決める
            start = 1 if nodes and min(nodes) >= 1 and max(nodes) == n else 0
            nodes |= set(range(start, start + n))
    else:
        # 隣接リスト（clone-graph は 1 始まり、is-graph-bipartite は 0 始まり）。無向なら同じ辺を 2 回描かない
        edges = [(i + base, v, None) for i, r in enumerate(rows) for v in r if directed or i + base <= v]
        nodes = set(range(base, base + len(rows)))
    for v in sorted(nodes):
        out.append("  {};".format(v))
    for u, v, w in edges:
        label = ' [label="{}"]'.format(w) if w is not None else ""
        out.append("  {} {} {}{};".format(u, arrow, v, label))
    return "\n".join(out + ["}"]) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["tree", "graph"])
    parser.add_argument("input")
    parser.add_argument("--directed", action="store_true", help="有向グラフとして描く")
    parser.add_argument("--out", help="出力する PNG（既定: 入力と同じ場所の graph.png）")
    args = parser.parse_args()

    values = read_values(args.input)
    if args.mode == "tree":
        rows = [v for v in values if is_tree_row(v)]
        if not rows:
            sys.exit("input.txt に木（[3,9,20,null,null,15,7] のような配列）の行がありません")
        dot = tree_dot(rows[0])
    else:
        rows = [v for v in values if is_nested_int_row(v)]
        if not rows:
            sys.exit("input.txt にグラフ（[[0,1],[1,2]] のような配列の配列）の行がありません")
        n = next((v for v in values if isinstance(v, int) and not isinstance(v, bool)), None)
        dot = graph_dot(rows[0], n, args.directed)

    out_png = args.out or os.path.join(os.path.dirname(os.path.abspath(args.input)), "graph.png")
    out_dot = os.path.splitext(out_png)[0] + ".dot"
    with open(out_dot, "w", encoding="utf-8") as f:
        f.write(dot)
    if shutil.which("dot") is None:
        sys.exit("dot コマンドがありません。sudo apt-get install -y graphviz を実行してください")
    subprocess.run(["dot", "-Tpng", out_dot, "-o", out_png], check=True)
    print("出力しました: " + out_png)
    if shutil.which("code"):
        subprocess.run(["code", out_png])


if __name__ == "__main__":
    main()
