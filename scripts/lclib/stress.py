"""ランダムテスト：ランダムな入力で解答と愚直解（naive.py）を比べ、出力が食い違う入力（反例）を探す

problems/<問題>/stress/
├── gen.py      入力を 1 ケース分、LeetCode の形式（引数 1 つにつき 1 行の JSON）で標準出力に書く
└── naive.py    愚直解。solution.py と同じ形（class Solution や設計するクラス）で書く
見つけた反例は tests/hack-NNN.in・.out（.out は naive.py の出力）に保存するので、以降は "test" で毎回確かめられる
"""

import json
import os
import sys
import threading
import time

from . import judge, paths
from .langs import LANGUAGES, element_type, fill_bodies
from .term import LcError, bold, green, info, red, yellow

GEN_HEAD = '''\
# 入力を 1 ケース分、LeetCode の形式（引数 1 つにつき 1 行の JSON）で標準出力に書き出す
# 問題の制約に合わせて書き換える。値を小さくしておくと、反例が見つかったときに手で追いやすい
import json
import random
from collections import deque

ALPHABET = "ab"


def out(x):
    print(json.dumps(x, separators=(",", ":")))


def rand_str(k):
    return "".join(random.choice(ALPHABET) for _ in range(k))


def rand_tree(k):
    """ノードが k 個のランダムな二分木を、LeetCode の形式（レベル順、子が無いところは null）で返す"""
    if k == 0:
        return []
    nodes = [[random.randint(1, 10), None, None]]
    slots = [(0, 1), (0, 2)]
    for _ in range(k - 1):
        parent, side = slots.pop(random.randrange(len(slots)))
        nodes.append([random.randint(1, 10), None, None])
        nodes[parent][side] = len(nodes) - 1
        slots += [(len(nodes) - 1, 1), (len(nodes) - 1, 2)]
    res = []
    queue = deque([0])
    while queue:
        i = queue.popleft()
        if i is None:
            res.append(None)
            continue
        res.append(nodes[i][0])
        queue.append(nodes[i][1])
        queue.append(nodes[i][2])
    while res[-1] is None:
        res.pop()
    return res


'''

NAIVE_HEAD = """\
# 愚直解。計算量は気にせず、確実に正しい方法で書く（solution.py と同じく class Solution などを書く）
from lc_support import *  # noqa: F403

"""


def gen_expr(t):
    """LeetCode の型に合わせて、ランダムな値を作る Python の式"""
    t = t.strip()
    simple = {
        "integer": "random.randint(1, 10)",
        "long": "random.randint(1, 10)",
        "double": "round(random.uniform(0, 10), 2)",
        "boolean": "random.choice([True, False])",
        "string": "rand_str(random.randint(1, 8))",
        "String": "rand_str(random.randint(1, 8))",
        "character": "random.choice(ALPHABET)",
        "ListNode": "[random.randint(1, 10) for _ in range(random.randint(0, 8))]",
        "TreeNode": "rand_tree(random.randint(0, 8))",
    }
    if t in simple:
        return simple[t]
    inner = element_type(t)
    if inner is None:
        return "None  # TODO: {} の値を作る".format(t)
    inner2 = element_type(inner)
    if inner2 is not None:
        # 2 次元の配列はグリッドにする
        elem = 'random.choice("01")' if inner2 == "character" else gen_expr(inner2)
        return "[[{} for _ in range(cols)] for _ in range(rows)]".format(elem)
    return "[{} for _ in range(n)]".format(gen_expr(inner))


def size_vars(body):
    """本体で使っている配列の長さの変数（n・rows・cols）を定義する行"""
    lines = []
    if "range(n)" in body:
        lines.append("n = random.randint(1, 8)")
    if "range(rows)" in body:
        lines += ["rows = random.randint(1, 5)", "cols = random.randint(1, 5)"]
    return lines


def gen_template(problem):
    md = problem.metadata
    if not problem.is_design:
        params = md.get("params", [])
        body = ["{} = {}  # {}".format(p["name"], gen_expr(p["type"]), p["type"]) for p in params]
        body += ["out({})".format(p["name"]) for p in params]
    else:
        cls = md["classname"]
        ctor = md.get("constructor", {}).get("params", [])
        methods = md.get("methods", [])
        body = [
            "ops = {}".format(json.dumps([cls])),
            "args = [[{}]]  # {}".format(", ".join(gen_expr(p["type"]) for p in ctor), ", ".join(p["name"] for p in ctor)),
            "for _ in range(random.randint(1, 10)):",
            "    name = random.choice({})".format(json.dumps([m["name"] for m in methods])),
            "    ops.append(name)",
        ]
        for k, m in enumerate(methods):
            ps = m.get("params", [])
            body += [
                '    {} name == "{}":'.format("if" if k == 0 else "elif", m["name"]),
                "        args.append([{}])  # {}".format(
                    ", ".join(gen_expr(p["type"]) for p in ps), ", ".join(p["name"] for p in ps)
                ),
            ]
        body += ["out(ops)", "out(args)"]
    return "\n".join([GEN_HEAD.rstrip("\n"), "", "", *size_vars("\n".join(body)), *body]) + "\n"


def naive_template(problem):
    snippet = problem.snippet("python3")
    if snippet is None:
        raise LcError("この問題には Python のひな形が無いため、naive.py を自分で書いてください")
    body = fill_bodies(
        snippet.replace("\r\n", "\n").rstrip(),
        lambda prev: prev.lstrip().startswith("def ") and prev.rstrip().endswith(":"),
        "pass",
    )
    return NAIVE_HEAD + body + "\n"


def init(problem):
    d = problem.stress_dir
    d.mkdir(exist_ok=True)
    for name, make in (("gen.py", gen_template), ("naive.py", naive_template)):
        path = d / name
        if path.exists():
            info("既にあるので作りません: " + paths.rel(path))
            continue
        path.write_text(make(problem), encoding="utf-8", newline="\n")
        info("作りました: " + paths.rel(path))
    info("gen.py を問題の制約に合わせ、naive.py に愚直解を書いてから、タスク \"stress: hack\" を実行してください")


def hack(problem, cmd, max_iterations=0, timeout=judge.TIMEOUT):
    gen = problem.stress_dir / "gen.py"
    naive = problem.stress_dir / "naive.py"
    for f in (gen, naive):
        if not f.is_file():
            raise LcError("{} がありません。先にタスク \"stress: init\" を実行してください".format(paths.rel(f)))
    gen_cmd = [paths.PYTHON, str(gen)]
    naive_cmd = LANGUAGES["python"].build(problem, False, target=naive)

    stop = threading.Event()
    lock = threading.Lock()
    count = {"started": 0, "tried": 0}
    found = []

    def report(kind, input_text, expected_run=None, actual_run=None):
        with lock:
            if not stop.is_set():
                found.append((kind, input_text, expected_run, actual_run))
                stop.set()

    def worker():
        while not stop.is_set():
            with lock:
                if max_iterations and count["started"] >= max_iterations:
                    return
                count["started"] += 1
            g = judge.run_program(gen_cmd, "", timeout)
            if not g.ok:
                report("gen", g.stdout, actual_run=g)
                return
            input_text = g.stdout
            e = judge.run_program(naive_cmd, input_text, timeout)
            if not e.ok:
                report("naive", input_text, actual_run=e)
                return
            a = judge.run_program(cmd, input_text, timeout)
            with lock:
                count["tried"] += 1
            if not a.ok:
                report("TLE" if a.timed_out else "RE", input_text, e, a)
                return
            ok, _ = judge.compare(a.output, e.output, problem.compare)
            if not ok:
                report("WA", input_text, e, a)
                return

    # 1 回の試行で 3 つのプロセスを順に動かすので、コア数と同じだけ並列に動かす
    threads = [threading.Thread(target=worker, daemon=True) for _ in range(os.cpu_count() or 2)]
    for t in threads:
        t.start()
    info("反例を探しています。止めるときは Ctrl+C")
    try:
        while any(t.is_alive() for t in threads):
            time.sleep(0.5)
            sys.stdout.write("\r試した入力: {} 個".format(count["tried"]))
            sys.stdout.flush()
    except KeyboardInterrupt:
        stop.set()
        print()
        info("中断しました（試した入力: {} 個）".format(count["tried"]))
        return False
    print()

    if not found:
        info(green("反例は見つかりませんでした（試した入力: {} 個）".format(count["tried"])))
        return True
    kind, input_text, expected_run, actual_run = found[0]
    if kind == "gen":
        print(red("gen.py がエラーになりました"))
        print(actual_run.stderr)
        return False
    paths.INPUT_TXT.write_text(input_text, encoding="utf-8", newline="\n")
    if kind == "naive":
        print(red("naive.py がエラーになりました（入力を input.txt に書きました）"))
        judge.show_details(input_text, None, actual_run)
        return False
    case = problem.new_case("hack", input_text, expected_run.output)
    print(bold(red("反例が見つかりました（{}）".format(kind))))
    judge.show_details(input_text, expected_run.output, actual_run)
    info(yellow("{} に保存し、input.txt にもコピーしました（F5 でそのままデバッグできます）".format(paths.rel(case.input_path))))
    return False
