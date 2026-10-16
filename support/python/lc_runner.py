"""Python の解答（class Solution や設計するクラス）を、LeetCode 形式の入力で呼び出す

使い方: python3.14 lc_runner.py [--stdin FILE] [--meta META_JSON] [--from PATH_FILE] [FILE.py]
  FILE.py      solution.py（stress/naive.py も同じ形）。stress/gen.py などの普通のスクリプトは、そのまま実行する
  --meta       問題の meta.json（省略すると FILE.py のあるディレクトリから上にたどって探す）
  --stdin      標準入力をこのファイルにする（デバッガの debugpy には標準入力を切り替える設定が無いため）
  --from       実行するファイルのパスを、このファイルから読む（デバッグ用。scripts/lc.py が書き出す）

入力は引数 1 つにつき 1 つの JSON の値。複数のケースが並んでいれば順に全部実行する。
結果は環境変数 LC_OUTPUT のファイル（テスト用。解答の print と分けるため）、無ければ標準出力に 1 ケース 1 行で書く
"""

import argparse
import json
import os
import re
import runpy
import sys
from collections import deque
from pathlib import Path

SUPPORT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SUPPORT_DIR))

import lc_support  # noqa: E402

# 深い再帰で、手元だけ RecursionError にならないよう上限を上げる
sys.setrecursionlimit(100000)


def input_error(msg):
    sys.stdout.flush()
    print("[lc] 入力の形式が正しくありません: " + msg, file=sys.stderr)
    sys.exit(3)


def find_meta(path):
    for d in [path.parent, *path.parents]:
        if (d / "meta.json").is_file():
            return d / "meta.json"
    return None


def parse_values(text):
    decoder = json.JSONDecoder()
    values = []
    i = 0
    while True:
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            return values
        try:
            v, i = decoder.raw_decode(text, i)
        except json.JSONDecodeError as e:
            input_error("{} 行目 {} 文字目: {}".format(e.lineno, e.colno, e.msg))
        values.append(v)


# ---- 入力：LeetCode の値 → Python の値 ----


class Converter:
    def __init__(self, namespace):
        # 解答のファイルで ListNode・TreeNode を定義し直していれば、そちらを使う
        self.list_node = namespace.get("ListNode", lc_support.ListNode)
        self.tree_node = namespace.get("TreeNode", lc_support.TreeNode)

    def build_list(self, v):
        if not isinstance(v, list):
            input_error("ListNode を読むところに配列以外の値があります: {!r}".format(v))
        head = None
        for x in reversed(v):
            head = self.list_node(x, head)
        return head

    def build_tree(self, v):
        if not isinstance(v, list):
            input_error("TreeNode を読むところに配列以外の値があります: {!r}".format(v))
        if not v or v[0] is None:
            return None
        root = self.tree_node(v[0])
        queue = deque([root])
        i = 1
        while queue and i < len(v):
            cur = queue.popleft()
            if v[i] is not None:
                cur.left = self.tree_node(v[i])
                queue.append(cur.left)
            i += 1
            if i < len(v) and v[i] is not None:
                cur.right = self.tree_node(v[i])
                queue.append(cur.right)
            i += 1
        return root

    def to_py(self, v, t):
        t = t.strip()
        if t == "ListNode":
            return self.build_list(v)
        if t == "TreeNode":
            return self.build_tree(v)
        inner = element_type(t)
        if inner is not None and isinstance(v, list):
            return [self.to_py(x, inner) for x in v]
        if t == "double" and isinstance(v, int):
            return float(v)
        return v

    def args(self, values, params, name):
        if not isinstance(values, list):
            input_error("{} の引数が配列ではありません".format(name))
        if len(values) != len(params):
            input_error("{} の引数は {} 個のはずが {} 個あります".format(name, len(params), len(values)))
        return [self.to_py(v, p["type"]) for v, p in zip(values, params)]


def element_type(t):
    if t.endswith("[]"):
        return t[:-2]
    m = re.fullmatch(r"list<(.+)>", t, re.IGNORECASE)
    return m.group(1) if m else None


# ---- 出力：Python の値 → LeetCode の形式 ----


def is_list_node(v):
    return hasattr(v, "val") and hasattr(v, "next")


def is_tree_node(v):
    return hasattr(v, "val") and hasattr(v, "left") and hasattr(v, "right")


def to_lc(v, t=None):
    t = (t or "").strip()
    if v is None:
        return "[]" if t in ("ListNode", "TreeNode") else "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) or (t == "double" and isinstance(v, int)):
        # LeetCode と同じく小数点以下 5 桁で出す
        return "{:.5f}".format(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if is_tree_node(v):
        items = []
        queue = deque([v])
        while queue:
            n = queue.popleft()
            if n is None:
                items.append("null")
                continue
            items.append(to_lc(n.val))
            queue.append(n.left)
            queue.append(n.right)
        while items and items[-1] == "null":
            items.pop()
        return "[" + ",".join(items) + "]"
    if is_list_node(v):
        items = []
        while v is not None:
            if len(items) >= 1000000:
                items.append(json.dumps("...（長すぎます。リストがループしていませんか）", ensure_ascii=False))
                break
            items.append(to_lc(v.val))
            v = v.next
        return "[" + ",".join(items) + "]"
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    try:
        items = list(v)
    except TypeError:
        return json.dumps(str(v), ensure_ascii=False)
    inner = element_type(t)
    return "[" + ",".join(to_lc(x, inner) for x in items) + "]"


class Output:
    def __init__(self):
        path = os.environ.get("LC_OUTPUT")
        self.file = open(path, "w", encoding="utf-8") if path else None

    def line(self, s):
        # 途中のケースで落ちても、それまでの結果が残るように毎回 flush する
        if self.file:
            self.file.write(s + "\n")
            self.file.flush()
        else:
            print(s, flush=True)


# ---- 解答の呼び出し ----


def run_function(namespace, meta, values, out):
    name = meta["name"]
    params = meta.get("params", [])
    ret = meta.get("return", {}).get("type", "void")
    output_param = meta.get("output", {}).get("paramindex")
    cls = namespace.get("Solution")
    if cls is None:
        sys.exit("[lc] class Solution が見つかりません")
    conv = Converter(namespace)
    n = len(params)
    if n > 0 and not values:
        input_error("入力が空です（input.txt やテストケースに入力を書いてください）")
    i = 0
    while True:
        if i + n > len(values):
            input_error("引数が足りません（{} 個ずつのはずが、残りが {} 個です）".format(n, len(values) - i))
        args = [conv.to_py(v, p["type"]) for v, p in zip(values[i : i + n], params)]
        i += n
        method = getattr(cls(), name, None)
        if method is None:
            sys.exit("[lc] Solution に {} というメソッドがありません".format(name))
        r = method(*args)
        if ret == "void" and output_param is not None:
            out.line(to_lc(args[output_param], params[output_param]["type"]))
        else:
            out.line(to_lc(r, ret))
        if i >= len(values):
            return


def run_design(namespace, meta, values, out):
    classname = meta["classname"]
    cls = namespace.get(classname)
    if cls is None:
        sys.exit("[lc] class {} が見つかりません".format(classname))
    ctor_params = meta.get("constructor", {}).get("params", [])
    methods = {m["name"]: m for m in meta.get("methods", [])}
    conv = Converter(namespace)
    if not values:
        input_error("入力が空です（input.txt やテストケースに入力を書いてください）")
    if len(values) % 2 != 0:
        input_error("メソッド名の配列と引数の配列が、2 行 1 組になっていません")
    for k in range(0, len(values), 2):
        names, calls = values[k], values[k + 1]
        if not isinstance(names, list) or not isinstance(calls, list):
            input_error("メソッド名と引数は配列で書いてください")
        if not names or len(names) != len(calls):
            input_error("メソッド名と引数の配列の長さが違います")
        if names[0] != classname:
            input_error("1 つ目のメソッド名は {} のはずが {} になっています".format(classname, names[0]))
        obj = cls(*conv.args(calls[0], ctor_params, classname))
        results = ["null"]
        for name, a in zip(names[1:], calls[1:]):
            m = methods.get(name)
            if m is None:
                input_error("{} に {} というメソッドはありません".format(classname, name))
            r = getattr(obj, name)(*conv.args(a, m.get("params", []), name))
            results.append(to_lc(r, m.get("return", {}).get("type")))
        out.line("[" + ",".join(results) + "]")


def redirect_stdin(path):
    # input()・sys.stdin・open(0) のどれで読んでも path から読めるよう、ファイル記述子 0 を差し替える
    fd = os.open(path, os.O_RDONLY)
    os.dup2(fd, 0)
    os.close(fd)
    sys.stdin = open(0, encoding="utf-8", closefd=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?")
    parser.add_argument("--meta")
    parser.add_argument("--stdin")
    parser.add_argument("--from", dest="from_file")
    args = parser.parse_args()

    if args.from_file:
        target = Path(Path(args.from_file).read_text(encoding="utf-8").strip())
    elif args.file:
        target = Path(args.file)
    else:
        parser.error("実行するファイルを指定してください")
    target = target.resolve()
    if args.stdin:
        redirect_stdin(args.stdin)

    meta_path = Path(args.meta) if args.meta else find_meta(target)
    sys.path.insert(0, str(target.parent))
    if target.name == "gen.py" or meta_path is None:
        # 入力の生成など、普通のスクリプトはそのまま実行する
        sys.argv = [str(target)]
        runpy.run_path(str(target), run_name="__main__")
        return

    meta = json.loads(meta_path.read_text(encoding="utf-8"))["metaData"]
    namespace = runpy.run_path(str(target), run_name="solution")
    values = parse_values(sys.stdin.read())
    out = Output()
    if meta.get("systemdesign"):
        run_design(namespace, meta, values, out)
    else:
        run_function(namespace, meta, values, out)


if __name__ == "__main__":
    main()
