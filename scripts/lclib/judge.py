"""手元でのテストの実行と判定"""

import json
import math
import os
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .term import bold, cyan, dim, green, indent, red, yellow

TIMEOUT = 10  # 秒。サニタイザ付きのデバッグビルドは遅いので長めにしている


class Run:
    """プログラムを 1 回実行した結果"""

    def __init__(self, output, stdout, stderr, returncode, elapsed, timed_out):
        self.output = output  # 結果（ハーネスが LC_OUTPUT に書いたもの）
        self.stdout = stdout  # 解答が print したもの
        self.stderr = stderr
        self.returncode = returncode
        self.elapsed = elapsed
        self.timed_out = timed_out

    @property
    def ok(self):
        return not self.timed_out and self.returncode == 0


def run_program(cmd, input_text, timeout=TIMEOUT):
    env = dict(os.environ)
    # LeetCode の木やリストの問題はメモリを解放しないのが普通なので、リークの検出は切る
    env.setdefault("ASAN_OPTIONS", "detect_leaks=0")
    env.setdefault("UBSAN_OPTIONS", "print_stacktrace=1")
    env.setdefault("RUST_BACKTRACE", "0")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory() as td:
        out_path = Path(td) / "output.txt"
        env["LC_OUTPUT"] = str(out_path)
        start = time.perf_counter()
        try:
            p = subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                env=env,
            )
            stdout, stderr, code, timed_out = p.stdout, p.stderr, p.returncode, False
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
            code, timed_out = None, True
        elapsed = time.perf_counter() - start
        output = out_path.read_text(encoding="utf-8", errors="replace") if out_path.is_file() else ""
    return Run(output, stdout, stderr, code, elapsed, timed_out)


# ---- 出力の比較 ----


def parse(text):
    try:
        return json.loads(text), True
    except ValueError:
        return text.strip(), False


def same(a, b):
    """LeetCode と同じく、小数は誤差 1e-5 まで許す"""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, int) and isinstance(b, int):
            return a == b
        return math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-5)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def _key(v):
    return json.dumps(v, sort_keys=True)


def sort_top(v):
    return sorted(v, key=_key) if isinstance(v, list) else v


def sort_deep(v):
    return sorted((sort_deep(x) for x in v), key=_key) if isinstance(v, list) else v


def compare_line(actual, expected, mode):
    """1 ケース分の出力を比べる。戻り値は (一致したか, 補足)"""
    a, a_json = parse(actual)
    e, e_json = parse(expected)
    if not (a_json and e_json):
        return actual.strip() == expected.strip(), None
    if same(a, e):
        return True, None
    if not (isinstance(a, list) and isinstance(e, list)):
        return False, None
    if mode == "unordered" and same(sort_top(a), sort_top(e)):
        return True, None
    if same(sort_deep(a), sort_deep(e)):
        if mode == "unordered":
            return False, "内側の配列の順番まで並べ替えると一致します（内側の順番も問わない問題なら正解です）"
        return False, (
            "並べ替えると一致します。順番を問わない問題なら、meta.json の \"compare\" を \"unordered\" にすると正解になります"
        )
    return False, None


def compare(actual, expected, mode):
    a_lines = [x for x in actual.splitlines() if x.strip()]
    e_lines = [x for x in expected.splitlines() if x.strip()]
    if len(a_lines) != len(e_lines):
        return False, "出力の行数が違います（{} 行のはずが {} 行）".format(len(e_lines), len(a_lines))
    notes = []
    for a, e in zip(a_lines, e_lines):
        ok, note = compare_line(a, e, mode)
        if not ok:
            return False, note
        if note:
            notes.append(note)
    return True, notes[0] if notes else None


# ---- テストの実行 ----


class Result:
    def __init__(self, case, run, verdict, note=None):
        self.case = case
        self.run = run
        self.verdict = verdict  # AC・WA・RE・TLE・"--"（期待する出力が無い）
        self.note = note

    @property
    def passed(self):
        return self.verdict in ("AC", "--")


def judge(case, run, mode):
    expected = case.expected
    if run.timed_out:
        return Result(case, run, "TLE")
    if run.returncode != 0:
        return Result(case, run, "RE")
    if expected is None:
        return Result(case, run, "--")
    ok, note = compare(run.output, expected, mode)
    return Result(case, run, "AC" if ok else "WA", note)


VERDICT_COLOR = {"AC": green, "WA": red, "RE": red, "TLE": yellow, "--": yellow}


def clip(text, max_lines=30, max_chars=2000):
    lines = text.rstrip("\n").split("\n")
    lines = [x if len(x) <= max_chars else x[:max_chars] + dim(" ...（{} 文字）".format(len(x))) for x in lines]
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [dim("...（ほか {} 行）".format(len(lines) - max_lines))]
    return "\n".join(lines)


def show_details(input_text, expected, run, note=None):
    print(cyan("    入力"))
    print(indent(clip(input_text), "        "))
    if expected is not None:
        print(cyan("    期待する出力"))
        print(indent(clip(expected), "        "))
    print(cyan("    あなたの出力"))
    print(indent(clip(run.output) if run.output.strip() else dim("（なし）"), "        "))
    if note:
        print(yellow("    ※ " + note))
    if run.stdout.strip():
        print(cyan("    標準出力（print など）"))
        print(indent(clip(run.stdout), "        "))
    if run.stderr.strip():
        print(cyan("    標準エラー出力"))
        print(indent(clip(run.stderr, max_lines=60), "        "))


def show(result, verbose=False):
    r = result
    ms = "{:>6.0f} ms".format(r.run.elapsed * 1000)
    head = "{:<14} {} {}".format(r.case.name, VERDICT_COLOR[r.verdict](bold("{:<3}".format(r.verdict))), dim(ms))
    if r.verdict == "RE" and r.run.returncode == 3:
        head += red("  入力の形式が正しくありません")
    print(head)
    if verbose or r.verdict != "AC":
        show_details(r.case.input, r.case.expected, r.run, r.note)


def run_tests(cmd, cases, mode, timeout=TIMEOUT, verbose=False):
    """ケースを並列に実行して、結果を表示する。全部通ったら True"""
    if not cases:
        print(yellow("テストケースがありません（tests/*.in）"))
        return True
    with ThreadPoolExecutor(max_workers=max(1, min(len(cases), os.cpu_count() or 1))) as ex:
        runs = list(ex.map(lambda c: run_program(cmd, c.input, timeout), cases))
    results = [judge(c, r, mode) for c, r in zip(cases, runs)]
    for r in results:
        show(r, verbose)
    counts = {}
    for r in results:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    summary = "  ".join(VERDICT_COLOR[v]("{} {}".format(v, n)) for v, n in counts.items())
    passed = all(r.passed for r in results)
    print()
    print(bold("結果: ") + summary + dim("  （全 {} ケース）".format(len(results))))
    if counts.get("--"):
        print(dim("-- は期待する出力（.out）が無いケースです。タスク \"test (remote)\" で LeetCode の正解を取得できます"))
    return passed
