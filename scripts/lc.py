#!/usr/bin/env python3
"""LeetCode の問題を手元で解くためのコマンド（VS Code のタスクから呼ぶ。ターミナルからは lc で使える）

    lc new <番号|slug|URL> [--lang cpp|rust|python|all]   問題を取得して、解答のひな形とサンプルを作る
    lc daily [--lang ...]                                 今日の問題（Daily Question）を取得する
    lc test [FILE] [--release]                            tests/ のケースで、手元でテストする
    lc run [FILE] [--release]                             input.txt を入力にして実行する
    lc build [FILE]                                       ビルドして、F5 のデバッグ対象にする
    lc remote [FILE] [--save]                             tests/ の入力を LeetCode のサーバーで実行する
    lc submit [FILE] [--no-test]                          手元でテストしてから提出する
    lc stress init|hack [FILE]                            ランダムテスト
    lc login                                              LeetCode の Cookie を登録する
    lc sync                                               Rust のワークスペースとハーネスを作り直す

FILE は問題のディレクトリの中のファイル（タスクからは開いているファイル）。省略するとカレントディレクトリを使い、
それも問題の中でなければ前回の問題を使う。言語は solution.* の拡張子で決まり、--lang で変えられる
"""

import argparse
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lclib import api, judge, langs, paths, remote, stress  # noqa: E402
from lclib import problem as problems  # noqa: E402
from lclib.term import LcError, bold, dim, green, info, red  # noqa: E402


def target(args):
    problem, lang = problems.resolve(args.file, args.lang, langs.LANGUAGES)
    if not lang.solution_path(problem).is_file():
        raise LcError("{} がありません。タスク \"new problem\" で言語を選んで作ってください".format(paths.rel(lang.solution_path(problem))))
    return problem, lang


def open_in_editor(files):
    code = shutil.which("code")
    if code:
        subprocess.run([code, *map(str, files)])


def cmd_new(args, slug=None):
    selected = langs.parse_langs(args.lang)
    slug = slug or api.resolve_slug(args.problem)
    info(dim("問題を取得しています: {}".format(slug)))
    problem = problems.create(api.question(slug))
    for lang in selected:
        created = lang.create(problem)
        info(("作りました: " if created else "既にあるので作りません: ") + paths.rel(lang.solution_path(problem)))
    problems.save_state(problem, selected[0].key)
    cases = problem.cases()
    if cases:
        # すぐに F5 でデバッグできるよう、1 つ目のサンプルを input.txt に入れる
        paths.INPUT_TXT.write_text(cases[0].input, encoding="utf-8", newline="\n")
    info("")
    info(green(bold("{}（{}）".format(problem.label, problem.meta["difficulty"]))))
    info("  問題文　: {}".format(paths.rel(problem.dir / "problem.md")))
    info("  サンプル: {} ケース（tests/。1 つ目を input.txt に入れました）".format(len(cases)))
    if problem.compare == "unordered":
        info("  出力の順番を問わない問題として比較します（meta.json の \"compare\"）")
    problem.warn_if_manual()
    if not args.no_open:
        open_in_editor([problem.dir / "problem.md"] + [lang.solution_path(problem) for lang in selected])


def cmd_daily(args):
    return cmd_new(args, slug=api.daily_slug())


def python_target(file_arg, problem):
    """Python のデバッグで動かすファイル。開いているのが問題の中の .py（naive.py・gen.py など）ならそれを使う"""
    if file_arg:
        f = Path(file_arg).resolve()
        if f.suffix == ".py" and f.is_file() and problems.find_problem(f) is not None:
            if problems.find_problem(f).dir == problem.dir:
                return f
    return None


def cmd_build(args):
    problem, lang = problems.resolve(args.file, args.lang, langs.LANGUAGES)
    py_target = python_target(args.file, problem) if lang.key == "python" else None
    if py_target is None:
        # 問題の中の .py（naive.py など）をデバッグするときは、solution.py が無くてもよい
        problem, lang = target(args)
    if lang.key == "python":
        command = lang.build(problem, False, target=py_target)
        langs.set_current(problem, lang, command, py_target)
        shown = paths.rel(py_target or lang.solution_path(problem))
    else:
        command = lang.build(problem, False)
        langs.set_current(problem, lang, command)
        shown = paths.rel(lang.solution_path(problem))
    info(green("デバッグの準備ができました: {}（input.txt を入力にして実行します）".format(shown)))


def build_with_hint(problem, lang, release):
    """ビルドする。LeetCode が特別な方法で判定する問題で失敗したら、そのことを補足する"""
    try:
        return lang.build(problem, release)
    except LcError:
        problem.warn_if_manual()
        raise


def cmd_test(args):
    problem, lang = target(args)
    info(bold("{}（{}{}）".format(problem.label, lang.name, "、release" if args.release else "")))
    command = build_with_hint(problem, lang, args.release)
    if not args.release:
        # F5 で、いまテストした問題をデバッグできるようにする
        langs.set_current(problem, lang, command)
    ok = judge.run_tests(command, problem.cases(), problem.compare, args.timeout, args.verbose)
    if not ok:
        problem.warn_if_manual()
    return 0 if ok else 1


def cmd_run(args):
    problem, lang = target(args)
    command = lang.build(problem, args.release)
    if not args.release:
        langs.set_current(problem, lang, command)
    if not paths.INPUT_TXT.is_file() or not paths.INPUT_TXT.read_text(encoding="utf-8").strip():
        raise LcError("input.txt に入力を書いてください（LeetCode の形式で、引数 1 つにつき 1 行）")
    info(dim("{}（{}）を input.txt を入力にして実行します".format(problem.label, lang.name)))
    env = dict(os.environ)
    env.setdefault("ASAN_OPTIONS", "detect_leaks=0")
    env.setdefault("UBSAN_OPTIONS", "print_stacktrace=1")
    with open(paths.INPUT_TXT, encoding="utf-8") as f:
        return subprocess.run(command, stdin=f, env=env).returncode


def cmd_remote(args):
    problem, lang = target(args)
    api.require_login()
    return 0 if remote.test(problem, lang, args.save) else 1


def cmd_submit(args):
    problem, lang = target(args)
    api.require_login()
    if not args.no_test:
        info(bold("提出の前に、手元でテストします"))
        command = lang.build(problem, False)
        if not judge.run_tests(command, problem.cases(), problem.compare, args.timeout):
            raise LcError(
                "手元のテストが通らないため、提出しませんでした。"
                "それでも提出するときは、ターミナルで lc submit --no-test {} を実行してください".format(
                    paths.rel(lang.solution_path(problem))
                )
            )
        info("")
    return 0 if remote.submit(problem, lang) else 1


def cmd_stress(args):
    problem, lang = target(args)
    if args.action == "init":
        stress.init(problem)
        return 0
    info(bold("{}（{}）".format(problem.label, lang.name)))
    command = lang.build(problem, False)
    langs.set_current(problem, lang, command)
    return 0 if stress.hack(problem, command, args.max) else 1


def cmd_login(args):
    info("ブラウザで https://leetcode.com にログインし、開発者ツール（F12）の")
    info("「Application（Firefox は Storage）」→「Cookies」→「https://leetcode.com」から、次の 2 つの値をコピーして貼り付けてください")
    info(dim("（入力した文字は表示されません。値は {} に保存します）".format(api.COOKIE_FILE)))
    session = getpass.getpass("LEETCODE_SESSION: ").strip()
    csrf = getpass.getpass("csrftoken: ").strip()
    if not session or not csrf:
        raise LcError("値が空です")
    status = api.user_status({"LEETCODE_SESSION": session, "csrftoken": csrf})
    if not status or not status.get("isSignedIn"):
        raise LcError("ログインできませんでした。Cookie の値を確かめてください")
    api.save_cookies(session, csrf)
    info(green("ログインしました: {}{}".format(status["username"], "（プレミアム）" if status.get("isPremium") else "")))


def cmd_sync(args):
    langs.sync_workspace()
    info("Rust のワークスペース（Cargo.toml）とハーネス（harness.rs）を作り直しました")


def main():
    parser = argparse.ArgumentParser(prog="lc", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, func, help_text, action=None):
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(func=func)
        if action:
            p.add_argument("action", choices=action)
        p.add_argument("file", nargs="?", help="問題のディレクトリの中のファイル（省略するとカレントディレクトリ）")
        p.add_argument("--lang", choices=sorted(langs.LANGUAGES), help="言語（省略するとファイルから決める）")
        return p

    for name, func, help_text in (("new", cmd_new, "問題を取得して、解答のひな形とサンプルを作る"), ("daily", cmd_daily, "今日の問題を取得する")):
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(func=func)
        if name == "new":
            p.add_argument("problem", help="問題番号・slug・URL")
        p.add_argument("--lang", default=os.environ.get("LC_LANG", "cpp"), help="cpp・rust・python・all（カンマ区切りで複数）")
        p.add_argument("--no-open", action="store_true", help="作ったファイルを VS Code で開かない")

    p = add("test", cmd_test, "tests/ のケースで、手元でテストする")
    p.add_argument("--release", action="store_true", help="LeetCode と同じ最適化でビルドする（実行時間の確認用）")
    p.add_argument("--timeout", type=float, default=judge.TIMEOUT, help="1 ケースの制限時間（秒）")
    p.add_argument("-v", "--verbose", action="store_true", help="AC のケースも入出力を表示する")
    p = add("run", cmd_run, "input.txt を入力にして実行する")
    p.add_argument("--release", action="store_true")
    add("build", cmd_build, "ビルドして、F5 のデバッグ対象にする")
    p = add("remote", cmd_remote, "tests/ の入力を LeetCode のサーバーで実行する")
    p.add_argument("--save", action="store_true", help="期待する出力（.out）が無いケースに、LeetCode の正解を保存する")
    p = add("submit", cmd_submit, "手元でテストしてから提出する")
    p.add_argument("--no-test", action="store_true", help="手元のテストをしないで提出する")
    p.add_argument("--timeout", type=float, default=judge.TIMEOUT)
    p = add("stress", cmd_stress, "ランダムテスト（init：gen.py・naive.py を作る、hack：反例を探す）", ["init", "hack"])
    p.add_argument("--max", type=int, default=0, help="試す入力の数の上限（0 は見つかるまで）")
    p = sub.add_parser("login", help="LeetCode の Cookie を登録する")
    p.set_defaults(func=cmd_login)
    p = sub.add_parser("sync", help="Rust のワークスペースとハーネスを作り直す")
    p.set_defaults(func=cmd_sync)

    args = parser.parse_args()
    try:
        sys.exit(args.func(args) or 0)
    except LcError as e:
        print(red("エラー: ") + str(e), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
