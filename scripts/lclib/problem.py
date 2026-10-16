"""問題のディレクトリ（problems/<番号>-<slug>/）

problems/0001-two-sum/
├── problem.md      問題文（LeetCode の HTML をそのまま埋め込んだ Markdown。開くとプレビューで表示される）
├── meta.json       問題の情報（引数と戻り値の型、比較方法、各言語のひな形）
├── solution.cpp    解答（solution.rs・solution.py も同じ場所に作る）
├── tests/          テストケース（sample-1.in / sample-1.out など。.in と .out を置けば自分で足せる）
└── stress/         ランダムテスト（gen.py・naive.py）
"""

import html
import json
import re
from pathlib import Path

from . import paths
from .term import LcError, warn

META = "meta.json"
STATE = paths.CURRENT / "state.json"

# 解答のうち、提出・リモートテストで送る範囲（vscode-leetcode と同じ書き方）
CODE_START = "@lc code=start"
CODE_END = "@lc code=end"

# LeetCode の lang の名前
LEETCODE_LANGS = ("cpp", "rust", "python3")


class Case:
    def __init__(self, name, input_path, output_path):
        self.name = name
        self.input_path = input_path
        self.output_path = output_path

    @property
    def input(self):
        return self.input_path.read_text(encoding="utf-8")

    @property
    def expected(self):
        if self.output_path.is_file():
            return self.output_path.read_text(encoding="utf-8").strip()
        return None


class Problem:
    def __init__(self, directory):
        self.dir = Path(directory).resolve()
        self.meta = json.loads((self.dir / META).read_text(encoding="utf-8"))

    question_id = property(lambda self: str(self.meta["questionId"]))
    frontend_id = property(lambda self: str(self.meta["frontendId"]))
    title = property(lambda self: self.meta["title"])
    slug = property(lambda self: self.meta["slug"])
    url = property(lambda self: self.meta["url"])
    metadata = property(lambda self: self.meta["metaData"])
    tests_dir = property(lambda self: self.dir / "tests")
    stress_dir = property(lambda self: self.dir / "stress")

    @property
    def label(self):
        return "{}. {}".format(self.frontend_id, self.title)

    @property
    def is_design(self):
        return bool(self.metadata.get("systemdesign"))

    @property
    def compare(self):
        return self.meta.get("compare", "exact")

    def snippet(self, leetcode_lang):
        return self.meta.get("snippets", {}).get(leetcode_lang)

    def cases(self):
        """tests/ の *.in を、番号順（sample-2 が sample-10 より前）に返す"""

        def key(p):
            return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", p.stem)]

        files = sorted(self.tests_dir.glob("*.in"), key=key) if self.tests_dir.is_dir() else []
        return [Case(p.stem, p, p.with_suffix(".out")) for p in files]

    def new_case(self, prefix, input_text, expected=None):
        """tests/<prefix>-NNN.in（と .out）を作って Case を返す"""
        self.tests_dir.mkdir(exist_ok=True)
        n = 1
        while (self.tests_dir / "{}-{:03d}.in".format(prefix, n)).exists():
            n += 1
        name = "{}-{:03d}".format(prefix, n)
        case = Case(name, self.tests_dir / (name + ".in"), self.tests_dir / (name + ".out"))
        case.input_path.write_text(input_text.strip() + "\n", encoding="utf-8", newline="\n")
        if expected is not None:
            case.output_path.write_text(expected.strip() + "\n", encoding="utf-8", newline="\n")
        return case

    def warn_if_manual(self):
        if self.metadata.get("manual"):
            warn(
                "この問題は LeetCode で特別な方法で判定される問題（manual）です。"
                "手元のテストが正しく動かないときは、タスク \"test (remote)\" を使ってください"
            )


def find_problem(path):
    """path（ファイルかディレクトリ）を含む問題を探す。見つからなければ None"""
    p = Path(path).resolve()
    for d in [p, *p.parents]:
        if (d / META).is_file():
            return Problem(d)
        if d == paths.ROOT:
            break
    return None


# ---- 最後に使った問題（F5 のデバッグや、問題の外のファイルを開いているときに使う） ----


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(problem, lang_key):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"problem": str(problem.dir), "lang": lang_key}), encoding="utf-8", newline="\n")


def last_problem():
    d = load_state().get("problem")
    if d and (Path(d) / META).is_file():
        return Problem(d)
    return None


# ---- 問題の作成 ----


def dir_name(q):
    fid = str(q["questionFrontendId"])
    prefix = "{:04d}".format(int(fid)) if fid.isdigit() else re.sub(r"\W+", "_", fid)
    return "{}-{}".format(prefix, q["titleSlug"])


def html_to_text(s):
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</(?:p|div|pre|li|ul|ol|h\d)>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).replace("\xa0", " ")


# "Output: [0,1]"（同じ行）と "Output\n[null, ...]"（クラスを設計する問題。次の行）の両方に対応する
OUTPUT_RE = re.compile(r"^[ \t]*Output(?:[ \t]*:[ \t]*(?:\n[ \t]*)?|[ \t]*\n[ \t]*)(\S.*)$", re.M)

# 「順番は問わない」と書いてある問題は、出力の配列を並べ替えて比較する
ANY_ORDER_RE = re.compile(r"\bany order\b|order (?:of [^.]{0,60})?(?:does not|doesn't) matter", re.I)


def split_inputs(q, metadata):
    text = q.get("exampleTestcases") or q.get("sampleTestCase") or ""
    lines = text.split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return []
    k = 2 if metadata.get("systemdesign") else len(metadata.get("params", []))
    if k == 0 or len(lines) % k != 0:
        return ["\n".join(lines)]
    return ["\n".join(lines[i : i + k]) for i in range(0, len(lines), k)]


def extract_outputs(content):
    return [m.group(1).strip() for m in OUTPUT_RE.finditer(html_to_text(content))]


def write_problem_md(d, q, url):
    tags = ", ".join(t["name"] for t in q.get("topicTags") or [])
    lines = [
        "# {}. {}".format(q["questionFrontendId"], q["title"]),
        "",
        "**{}**　|　[LeetCode で開く]({})".format(q["difficulty"], url) + ("　|　" + tags if tags else ""),
        "",
        q["content"].strip(),
        "",
    ]
    for i, hint in enumerate(q.get("hints") or [], 1):
        lines += ["<details><summary>ヒント {}</summary>".format(i), "", hint, "", "</details>", ""]
    (d / "problem.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def create(q):
    """LeetCode から取得した問題でディレクトリを作る（作り直すときも、テストケースと解答は上書きしない）"""
    d = paths.PROBLEMS / dir_name(q)
    d.mkdir(parents=True, exist_ok=True)
    old = json.loads((d / META).read_text(encoding="utf-8")) if (d / META).is_file() else {}
    metadata = json.loads(q["metaData"])
    url = "https://leetcode.com/problems/{}/".format(q["titleSlug"])
    any_order = ANY_ORDER_RE.search(html_to_text(q["content"])) is not None
    meta = {
        "questionId": q["questionId"],
        "frontendId": q["questionFrontendId"],
        "title": q["title"],
        "slug": q["titleSlug"],
        "difficulty": q["difficulty"],
        "url": url,
        # 出力の比較方法。"exact"：そのまま比較、"unordered"：一番外側の配列を並べ替えて比較
        "compare": old.get("compare") or ("unordered" if any_order else "exact"),
        "metaData": metadata,
        "snippets": {s["langSlug"]: s["code"] for s in q.get("codeSnippets") or [] if s["langSlug"] in LEETCODE_LANGS},
    }
    (d / META).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_problem_md(d, q, url)

    problem = Problem(d)
    inputs = split_inputs(q, metadata)
    outputs = extract_outputs(q["content"])
    if len(outputs) != len(inputs):
        warn("問題文からサンプルの出力を読み取れませんでした。tests/*.out を手で書くか、タスク \"test (remote)\" で取得してください")
        outputs = [None] * len(inputs)
    problem.tests_dir.mkdir(exist_ok=True)
    for i, (inp, out) in enumerate(zip(inputs, outputs), 1):
        case = Case("sample-{}".format(i), problem.tests_dir / "sample-{}.in".format(i), problem.tests_dir / "sample-{}.out".format(i))
        if not case.input_path.exists():
            case.input_path.write_text(inp + "\n", encoding="utf-8", newline="\n")
        if out is not None and not case.output_path.exists():
            case.output_path.write_text(out + "\n", encoding="utf-8", newline="\n")
    return problem


# ---- 解答ファイル ----


def is_marker(line, marker):
    """コメント記号とマーカーだけの行か（説明のコメントの中に書いたマーカーの文字列には反応しない）"""
    return re.fullmatch(r"\s*(?://|#)\s*{}\s*".format(re.escape(marker)), line) is not None


def extract_code(path):
    """解答のうち、提出する範囲（@lc code=start と @lc code=end の行の間）を取り出す"""
    text = Path(path).read_text(encoding="utf-8")
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines) if is_marker(line, CODE_START)), None)
    end = next((i for i, line in enumerate(lines) if is_marker(line, CODE_END) and (start is None or i > start)), None)
    if start is None or end is None:
        warn("{} と {} の行が無いため、ファイル全体を送ります".format(CODE_START, CODE_END))
        return text
    return "\n".join(lines[start + 1 : end]).strip("\n") + "\n"


def resolve(file_arg, lang_arg, languages):
    """タスクに渡された ${file}（とあれば --lang）から、問題と言語を決める"""
    path = Path(file_arg) if file_arg else Path.cwd()
    problem = find_problem(path)
    state = load_state()
    if problem is None:
        problem = last_problem()
        if problem is None:
            raise LcError("問題のファイル（problems/ の中）を開いてから実行してください")
        print("開いているファイルから問題が分からないため、前回の問題（{}）を使います".format(paths.rel(problem.dir)))
    if lang_arg:
        return problem, languages[lang_arg]
    if path.is_file() and path.stem == "solution":
        for lang in languages.values():
            if path.suffix == "." + lang.ext:
                return problem, lang
    existing = [lang for lang in languages.values() if lang.solution_path(problem).is_file()]
    if not existing:
        raise LcError("解答ファイルがありません。タスク \"new problem\" で言語を選んで作ってください")
    if state.get("problem") == str(problem.dir):
        for lang in existing:
            if lang.key == state.get("lang"):
                return problem, lang
    return problem, max(existing, key=lambda lang: lang.solution_path(problem).stat().st_mtime)
