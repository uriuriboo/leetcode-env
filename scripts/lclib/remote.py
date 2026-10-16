"""LeetCode のサーバーでのテスト（LeetCode の "Run"）と提出"""

from . import api, judge, paths
from .problem import extract_code
from .term import LcError, bold, cyan, dim, green, indent, info, red, yellow

STATUS = {
    10: "Accepted",
    11: "Wrong Answer",
    12: "Memory Limit Exceeded",
    13: "Output Limit Exceeded",
    14: "Time Limit Exceeded",
    15: "Runtime Error",
    16: "Internal Error",
    20: "Compile Error",
    30: "Timeout",
}


def as_list(v):
    if isinstance(v, list):
        return v
    return [] if v in (None, "") else [v]


def show_error(r):
    """コンパイルエラー・実行時エラーなどを表示する（表示したら True）"""
    code = r.get("status_code")
    msg = r.get("status_msg") or STATUS.get(code, "status {}".format(code))
    if code == 20:
        print(red(bold("コンパイルエラー")))
        print(indent(r.get("full_compile_error") or r.get("compile_error") or ""))
        return True
    if code == 15:
        print(red(bold("実行時エラー")))
        print(indent(r.get("full_runtime_error") or r.get("runtime_error") or ""))
        return True
    if code not in (10, 11):
        print(yellow(bold(msg)))
        return True
    return False


def percentile(v):
    try:
        return "{:.1f}% の提出より上".format(float(v))
    except (TypeError, ValueError):
        return "-"


def test(problem, lang, save=False):
    """tests/ の入力を LeetCode で実行し、LeetCode の正解と比べる。全部一致したら True"""
    cases = problem.cases()
    if not cases:
        raise LcError("tests/ にケース（*.in）がありません")
    data_input = "\n".join(c.input.strip() for c in cases)
    code = extract_code(lang.solution_path(problem))
    info(dim("LeetCode のサーバーで {} ケースを実行しています...".format(len(cases))))
    r = api.interpret(problem.slug, problem.question_id, lang.leetcode, code, data_input)
    if show_error(r):
        return False
    answers = as_list(r.get("code_answer"))
    expected = as_list(r.get("expected_code_answer"))
    stdouts = as_list(r.get("std_output_list"))
    all_ok = True
    for i, case in enumerate(cases):
        answer = answers[i] if i < len(answers) else ""
        exp = expected[i] if i < len(expected) else None
        ok = exp is not None and judge.compare(answer, exp, problem.compare)[0]
        all_ok = all_ok and ok
        print("{:<14} {}".format(case.name, green(bold("AC")) if ok else red(bold("WA"))))
        if not ok:
            print(cyan("    入力"))
            print(indent(judge.clip(case.input), "        "))
            print(cyan("    LeetCode の正解"))
            print(indent(exp if exp is not None else "（なし）", "        "))
            print(cyan("    あなたの出力"))
            print(indent(answer or "（なし）", "        "))
            if i < len(stdouts) and stdouts[i].strip():
                print(cyan("    標準出力"))
                print(indent(judge.clip(stdouts[i]), "        "))
        local = case.expected
        if local is not None and exp is not None and not judge.compare(local, exp, problem.compare)[0]:
            print(yellow("    ※ {} の期待する出力が、LeetCode の正解（{}）と違います".format(paths.rel(case.output_path), exp)))
        if save and local is None and exp is not None:
            case.output_path.write_text(exp + "\n", encoding="utf-8", newline="\n")
            print(dim("    LeetCode の正解を {} に保存しました".format(paths.rel(case.output_path))))
    print()
    print(bold("結果: ") + (green("すべて LeetCode の正解と一致") if all_ok else red("一致しないケースがあります")))
    if r.get("status_runtime"):
        print(dim("実行時間 {}".format(r["status_runtime"])))
    return all_ok


def submit(problem, lang):
    """提出する。Accepted なら True。通らなかったケースは tests/submit-NNN に保存する"""
    code = extract_code(lang.solution_path(problem))
    info(dim("提出しています..."))
    submission_id, r = api.submit(problem.slug, problem.question_id, lang.leetcode, code)
    status = r.get("status_code")
    passed = "{} / {}".format(r.get("total_correct", "?"), r.get("total_testcases", "?"))
    if status == 10:
        print(green(bold("Accepted")) + "  （{} ケース）".format(passed))
        print(
            "実行時間 {}（{}）  メモリ {}（{}）".format(
                r.get("status_runtime", "-"),
                percentile(r.get("runtime_percentile")),
                r.get("status_memory", "-"),
                percentile(r.get("memory_percentile")),
            )
        )
    else:
        msg = r.get("status_msg") or STATUS.get(status, "status {}".format(status))
        print(red(bold(msg)) + "  （通ったケース {}）".format(passed))
        if status in (15, 20):
            show_error(r)
        last = r.get("last_testcase")
        if last:
            exp = r.get("expected_output")
            print(cyan("    入力"))
            print(indent(judge.clip(last), "        "))
            if exp:
                print(cyan("    期待する出力"))
                print(indent(judge.clip(exp), "        "))
            if r.get("code_output"):
                print(cyan("    あなたの出力"))
                print(indent(judge.clip(str(r["code_output"])), "        "))
            if r.get("std_output"):
                print(cyan("    標準出力"))
                print(indent(judge.clip(str(r["std_output"])), "        "))
            case = problem.new_case("submit", last, exp or None)
            paths.INPUT_TXT.write_text(last.strip() + "\n", encoding="utf-8", newline="\n")
            print(yellow("このケースを {} に保存し、input.txt にもコピーしました".format(paths.rel(case.input_path))))
    print(dim("https://leetcode.com/submissions/detail/{}/".format(submission_id)))
    return status == 10
