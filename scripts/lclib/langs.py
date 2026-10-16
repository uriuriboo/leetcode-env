"""言語ごとの処理（解答のひな形、ハーネスの生成、ビルド、実行コマンド）

LeetCode の解答は main の無い関数（class Solution のメソッドなど）なので、手元で動かすために
入力を読んで解答を呼ぶ main（ハーネス）を問題の型情報（meta.json の metaData）から生成する。
- C++   ：.build/cpp/<問題>/main.cpp が leetcode.hpp と solution.cpp を include する
- Rust  ：solution.rs が mod harness; で問題のディレクトリの harness.rs を読み込む
          （設計する問題の struct やメソッドは pub ではないため、子モジュールから呼ぶ必要がある）
- Python：support/python/lc_runner.py が solution.py を読み込んで呼ぶ（生成するものは無い）
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from . import paths
from .problem import CODE_END, CODE_START, META, save_state
from .term import LcError, dim, info, warn

# ---- 共通 ----


def write_if_changed(path, text):
    """内容が同じなら書かない（rust-analyzer の再読み込みや、不要な再コンパイルを避ける）"""
    path = Path(path)
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def header_comment(problem, comment):
    return "\n".join(
        [
            "{} {} ({})".format(comment, problem.label, problem.meta.get("difficulty", "")),
            "{} {}".format(comment, problem.url),
            "{} 提出・リモートテストで送るのは「{}」から「{}」までの間だけ".format(comment, CODE_START, CODE_END),
        ]
    )


def split_params(text):
    """引数リストを、括弧の外のカンマで分ける"""
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch in "<([{":
            depth += 1
        elif ch in ">)]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def fill_bodies(code, is_header, body):
    """ひな形の空の関数本体（空白だけの行）に body（pass や todo!()）を入れて、そのまま動くコードにする"""

    def indent_of(line):
        return " " * (len(line) - len(line.lstrip()) + 4)

    out = []
    for line in code.split("\n"):
        prev = next((x for x in reversed(out) if x.strip()), "")
        if not line.strip() and is_header(prev):
            out.append(indent_of(prev) + body)
        else:
            out.append(line.rstrip() if not line.strip() else line)
    prev = next((x for x in reversed(out) if x.strip()), "")
    if is_header(prev):
        out.append(indent_of(prev) + body)
    return "\n".join(out)


def element_type(t):
    if t.endswith("[]"):
        return t[:-2]
    m = re.fullmatch(r"list<(.+)>", t, re.IGNORECASE)
    return m.group(1) if m else None


class Language:
    key = name = ext = leetcode = ""

    def solution_path(self, problem):
        return problem.dir / "solution.{}".format(self.ext)

    def create(self, problem):
        """解答のひな形を作る。既にあれば何もしない（作ったら True）"""
        path = self.solution_path(problem)
        if path.exists():
            return False
        snippet = problem.snippet(self.leetcode)
        if snippet is None:
            raise LcError("この問題は LeetCode で {} に対応していません".format(self.name))
        path.write_text(self.template(problem, snippet.replace("\r\n", "\n").rstrip()), encoding="utf-8", newline="\n")
        self.prepare(problem)
        return True

    def template(self, problem, snippet):
        raise NotImplementedError

    def prepare(self, problem):
        """ビルドの前に必要なファイルを作る"""

    def build(self, problem, release):
        """ビルドして、実行するコマンドを返す"""
        raise NotImplementedError


# ---- C++ ----

CPP_COMMON = [
    "-std=c++23",
    "-DLOCAL",
    "-Wall",
    "-g",
    # LeetCode と同じく、範囲外アクセスやオーバーフローを実行時に検出して止める
    "-fsanitize=address,undefined",
    "-fno-sanitize-recover=all",
    "-fno-omit-frame-pointer",
]
CPP_DEBUG = ["-O0", "-D_GLIBCXX_ASSERTIONS"]
CPP_RELEASE = ["-O2"]  # LeetCode と同じ最適化

CPP_TYPES = {
    "integer": "int",
    "long": "long long",
    "double": "double",
    "boolean": "bool",
    "string": "string",
    "String": "string",
    "character": "char",
    "ListNode": "ListNode*",
    "TreeNode": "TreeNode*",
}

_versions = {}


def cpp_compiler():
    if os.environ.get("LC_CXX"):
        return os.environ["LC_CXX"]
    # LeetCode と同じ clang 19 を優先する
    for c in ("clang++-19", "clang++", "g++"):
        if shutil.which(c):
            return c
    raise LcError("C++ のコンパイラ（clang++）がありません")


def compiler_version(cxx):
    if cxx not in _versions:
        r = subprocess.run([cxx, "--version"], capture_output=True, text=True)
        _versions[cxx] = r.stdout.strip()
    return _versions[cxx]


def cpp_type(t):
    t = t.strip()
    if t in CPP_TYPES:
        return CPP_TYPES[t]
    inner = element_type(t)
    if inner is not None and cpp_type(inner):
        return "vector<{}>".format(cpp_type(inner))
    return None


def cpp_param_type(param):
    """'vector<int>& nums' → 'vector<int>'（参照と const を外す）"""
    param = param.split("=")[0].strip()
    m = re.fullmatch(r"(.*?)\b[A-Za-z_]\w*\s*", param)
    t = m.group(1) if m and m.group(1).strip() else param
    t = re.sub(r"\bconst\b", "", t).replace("&", "")
    return " ".join(t.split())


def cpp_ctor_types(src, cls):
    """solution.cpp のコンストラクタから引数の型を読む（読めなければ None）"""
    start = re.search(r"\b(?:class|struct)\s+{}\b".format(re.escape(cls)), src)
    if not start:
        return None
    m = re.compile(r"\b{}\s*\(([^)]*)\)".format(re.escape(cls))).search(src, start.end())
    if not m:
        return None
    params = split_params(m.group(1))
    if params == ["void"]:
        return []
    return [cpp_param_type(p) for p in params]


def cpp_main(problem, solution):
    md = problem.metadata
    lines = [
        "// scripts/lc.py が生成するファイル。ビルドのたびに上書きされる",
        '#include "leetcode.hpp"',
        '#include "{}"'.format(solution.resolve().as_posix()),
        "",
    ]
    if not problem.is_design:
        out_param = -1
        if md.get("return", {}).get("type") == "void":
            out_param = md.get("output", {}).get("paramindex", -1)
        lines.append("int main() {{ return lc::run_function<&Solution::{}>({}); }}".format(md["name"], out_param))
        return "\n".join(lines) + "\n"

    cls = md["classname"]
    ctor_params = md.get("constructor", {}).get("params", [])
    src = solution.read_text(encoding="utf-8") if solution.is_file() else ""
    types = cpp_ctor_types(src, cls)
    if types is None or len(types) != len(ctor_params):
        types = [cpp_type(p["type"]) for p in ctor_params]
    if None in types:
        lines.append('#error "コンストラクタの引数の型が分かりません（scripts/lclib/langs.py の CPP_TYPES に追加してください）"')
        return "\n".join(lines) + "\n"
    n = len(types)
    lines += [
        "int main() {",
        "    lc::Reader in(lc::read_all_stdin());",
        "    lc::Output out;",
        '    if (in.at_end()) lc::input_error("入力が空です（input.txt やテストケースに入力を書いてください）");',
        "    while (!in.at_end()) {",
        "        auto names = lc::from_json<std::vector<std::string>>(in.next());",
        "        lc::Json calls = in.next();",
        '        lc::check_design(names, calls, "{}");'.format(cls),
        '        lc::check_arg_count(calls.a[0], {}, "{}");'.format(n, cls),
    ]
    lines += ["        auto p{} = lc::arg<{}>(calls.a[0], {});".format(i, t, i) for i, t in enumerate(types)]
    lines += [
        "        auto *obj = new {}({});".format(cls, ", ".join("p{}".format(i) for i in range(n))),
        '        std::vector<std::string> results{"null"};',
        "        for (size_t i = 1; i < names.size(); i++) {",
        "            const std::string &name = names[i];",
        "            const lc::Json &a = calls.a[i];",
    ]
    for k, m in enumerate(md.get("methods", [])):
        lines.append(
            '            {} (name == "{}") results.push_back(lc::call<&{}::{}>(obj, a, name));'.format(
                "if" if k == 0 else "else if", m["name"], cls, m["name"]
            )
        )
    prefix = "else " if md.get("methods") else ""
    lines += [
        '            {}lc::input_error("{} に ", name, " というメソッドはありません");'.format(prefix, cls),
        "        }",
        "        out.line(lc::join_list(results));",
        "    }",
        "}",
    ]
    return "\n".join(lines) + "\n"


def precompiled_header(cxx, flags, variant):
    """leetcode_core.hpp（<bits/stdc++.h> を含む）をプリコンパイルして、2 回目以降のコンパイルを速くする"""
    is_clang = "clang" in Path(cxx).name
    d = paths.BUILD / "pch" / variant
    out = d / (paths.CPP_CORE.name + (".pch" if is_clang else ".gch"))
    stamp = d / "stamp.json"
    key = json.dumps([cxx, compiler_version(cxx), flags, paths.CPP_CORE.stat().st_mtime_ns])
    if not (out.is_file() and stamp.is_file() and stamp.read_text(encoding="utf-8") == key):
        d.mkdir(parents=True, exist_ok=True)
        info(dim("leetcode_core.hpp をプリコンパイルしています（初回とヘッダを変えたときだけ）..."))
        r = subprocess.run([cxx, *flags, "-x", "c++-header", str(paths.CPP_CORE), "-o", str(out)])
        if r.returncode != 0:
            warn("プリコンパイルに失敗したため、使わずにコンパイルします")
            stamp.unlink(missing_ok=True)
            return []
        stamp.write_text(key, encoding="utf-8", newline="\n")
    # clang は -include-pch で読む。GCC は -include したヘッダと同じ名前の .gch を、include を探すディレクトリから見つけて使う
    # （GCC はヘッダの中から include したものにはプリコンパイル済みヘッダを使わないため、-include で最初に読ませる）
    return ["-include-pch", str(out)] if is_clang else ["-I", str(d), "-include", paths.CPP_CORE.name]


class Cpp(Language):
    key, name, ext, leetcode = "cpp", "C++", "cpp", "cpp"

    def template(self, problem, snippet):
        return "\n".join(
            [
                header_comment(problem, "//"),
                "// LeetCode と同じく、<bits/stdc++.h>・using namespace std・ListNode・TreeNode は leetcode.hpp で用意している",
                '#include "leetcode.hpp"',
                "",
                "// " + CODE_START,
                snippet,
                "// " + CODE_END,
                "",
            ]
        )

    def build(self, problem, release):
        cxx = cpp_compiler()
        variant = "release" if release else "debug"
        flags = CPP_COMMON + (CPP_RELEASE if release else CPP_DEBUG)
        solution = self.solution_path(problem)
        out_dir = paths.BUILD / "cpp" / problem.dir.name
        main = out_dir / "main.cpp"
        write_if_changed(main, cpp_main(problem, solution))
        exe = out_dir / variant / ("main.exe" if os.name == "nt" else "main")
        pch = precompiled_header(cxx, flags, variant)
        cmd = [cxx, *flags, *pch, "-I", str(paths.SUPPORT / "cpp"), str(main), "-o", str(exe)]
        stamp = out_dir / variant / "command.txt"
        newest = max(p.stat().st_mtime for p in (main, solution, paths.CPP_HEADER, paths.CPP_CORE))
        if (
            exe.is_file()
            and stamp.is_file()
            and stamp.read_text(encoding="utf-8") == " ".join(cmd)
            and exe.stat().st_mtime > newest
        ):
            return [str(exe)]
        exe.parent.mkdir(parents=True, exist_ok=True)
        info(dim("C++ をコンパイルしています（{}）...".format(variant)))
        if subprocess.run(cmd).returncode != 0:
            stamp.unlink(missing_ok=True)
            raise LcError("コンパイルに失敗しました")
        stamp.write_text(" ".join(cmd), encoding="utf-8", newline="\n")
        return [str(exe)]


# ---- Rust ----

PACKAGE_TOML = """\
# scripts/lc.py が生成するファイル。edition と依存クレートは LeetCode に合わせている
[package]
name = "{name}"
version = "0.1.0"
edition = "2024"
publish = false

[[bin]]
name = "{name}"
path = "solution.rs"
test = false
bench = false

[dependencies]
leetcode-support = {{ path = "../../support/rust" }}
# LeetCode で使えるクレート
rand = "0.8"
regex = "1"
itertools = "0.14"
"""

WORKSPACE_TOML = """\
# scripts/lc.py が生成するファイル（problems/ の Rust の解答をワークスペースのメンバーにする）。手で書き換えても上書きされる
[workspace]
resolver = "3"
members = [
{members}]

# LeetCode は opt-level 2 でコンパイルする（test release で使う）
[profile.release]
opt-level = 2
"""


def snake_case(name):
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def rust_fn_name(name, sources):
    """LeetCode のメソッド名（twoSum）に当たる Rust の関数名（two_sum）を、解答とひな形から探す"""
    for src in sources:
        for fn in re.findall(r"\bfn\s+([A-Za-z_]\w*)", src or ""):
            if fn.replace("_", "").lower() == name.replace("_", "").lower():
                return fn
    return snake_case(name)


def rust_param_refs(src, fn):
    """関数の引数ごとに、渡し方（""・"&"・"&mut "）を返す。in-place の問題は &mut Vec<i32> を受け取る"""
    m = re.search(r"\bfn\s+{}\s*(?:<[^>]*>)?\s*\(".format(re.escape(fn)), src or "")
    if not m:
        return None
    depth, j = 1, m.end()
    while j < len(src) and depth:
        if src[j] == "(":
            depth += 1
        elif src[j] == ")":
            depth -= 1
        j += 1
    refs = []
    for p in split_params(src[m.end() : j - 1]):
        if p.endswith("self"):
            continue
        t = p.split(":", 1)[1].strip() if ":" in p else ""
        refs.append("&mut " if t.startswith("&mut") else "&" if t.startswith("&") else "")
    return refs


def rust_harness(problem, solution):
    md = problem.metadata
    src = solution.read_text(encoding="utf-8") if solution.is_file() else ""
    sources = [src, problem.snippet("rust")]
    lines = [
        "// scripts/lc.py が生成するファイル。ビルドのたびに上書きされる",
        "#![allow(unused_mut, clippy::all)]",
        "use super::*;",
        "use leetcode_support::harness::{Input, Output, ToLc};",
        "",
        "pub fn main() {",
        "    let mut input = Input::stdin();",
        "    let mut out = Output::new();",
    ]
    if not problem.is_design:
        fn = rust_fn_name(md["name"], sources)
        n = len(md.get("params", []))
        refs = rust_param_refs(src, fn) or rust_param_refs(problem.snippet("rust"), fn)
        if refs is None or len(refs) != n:
            refs = [""] * n
        args = ", ".join("{}p{}".format(refs[i], i) for i in range(n))
        out_param = md.get("output", {}).get("paramindex") if md.get("return", {}).get("type") == "void" else None
        lines.append("    loop {")
        lines += ["        let mut p{} = input.read();".format(i) for i in range(n)]
        if out_param is not None:
            lines += ["        Solution::{}({});".format(fn, args), "        out.line(&p{}.to_lc());".format(out_param)]
        else:
            lines += ["        let ret = Solution::{}({});".format(fn, args), "        out.line(&ret.to_lc());"]
        lines += ["        if !input.has_next() {", "            break;", "        }", "    }", "}"]
        return "\n".join(lines) + "\n"

    cls = md["classname"]
    nctor = len(md.get("constructor", {}).get("params", []))
    lines += [
        "    while input.has_next() {",
        "        let mut obj: Option<{}> = None;".format(cls),
        "        let mut results = Vec::new();",
        '        for (name, mut a) in input.next_design("{}") {{'.format(cls),
        "            let r = match name.as_str() {",
        "                _ if obj.is_none() => {",
        "                    obj = Some({}::new({}));".format(cls, ", ".join(["a.read()"] * nctor)),
        '                    "null".to_string()',
        "                }",
    ]
    for m in md.get("methods", []):
        lines.append(
            '                "{}" => obj.as_mut().unwrap().{}({}).to_lc(),'.format(
                m["name"], rust_fn_name(m["name"], sources), ", ".join(["a.read()"] * len(m.get("params", [])))
            )
        )
    lines += [
        "                _ => a.unknown(),",
        "            };",
        "            a.finish();",
        "            results.push(r);",
        "        }",
        '        out.line(&format!("[{}]", results.join(",")));',
        "    }",
        "}",
    ]
    return "\n".join(lines) + "\n"


def rust_package_name(problem_dir):
    return "lc" + re.sub(r"[^a-z0-9_-]", "-", Path(problem_dir).name.lower())


def sync_workspace():
    """Rust の解答がある問題を、ルートの Cargo.toml のワークスペースに入れる"""
    from .problem import Problem

    members = []
    for solution in sorted(paths.PROBLEMS.glob("*/solution.rs")):
        d = solution.parent
        if not (d / META).is_file():
            continue
        write_if_changed(d / "Cargo.toml", PACKAGE_TOML.format(name=rust_package_name(d)))
        write_if_changed(d / "harness.rs", rust_harness(Problem(d), solution))
        members.append('    "problems/{}",\n'.format(d.name))
    write_if_changed(paths.ROOT / "Cargo.toml", WORKSPACE_TOML.format(members="".join(members)))


class Rust(Language):
    key, name, ext, leetcode = "rust", "Rust", "rs", "rust"

    def template(self, problem, snippet):
        snippet = fill_bodies(snippet, lambda prev: "fn " in prev and prev.rstrip().endswith("{"), "todo!()")
        lines = [
            header_comment(problem, "//"),
            "// clippy::ptr_arg は、LeetCode が決めている引数の型（&mut Vec<i32> など）への警告",
            "#![allow(dead_code, unused_imports, clippy::ptr_arg)]",
            "",
            "// LeetCode で定義済みのもの",
            "use leetcode_support::{ListNode, TreeNode};",
        ]
        if not problem.is_design:
            lines.append("struct Solution;")
        lines += [
            "",
            "// 手元で動かすための入口（harness.rs は scripts/lc.py がビルドのたびに生成する）",
            "mod harness;",
            "fn main() {",
            "    harness::main();",
            "}",
            "",
            "// " + CODE_START,
            snippet,
            "// " + CODE_END,
            "",
        ]
        return "\n".join(lines)

    def prepare(self, problem):
        sync_workspace()

    def build(self, problem, release):
        if shutil.which("cargo") is None:
            raise LcError("cargo がありません")
        self.prepare(problem)
        package = rust_package_name(problem.dir)
        info(dim("Rust をビルドしています（{}。初回は依存クレートのビルドに時間がかかります）...".format("release" if release else "debug")))
        cmd = ["cargo", "build", "--quiet", "-p", package] + (["--release"] if release else [])
        if subprocess.run(cmd, cwd=paths.ROOT).returncode != 0:
            raise LcError("コンパイルに失敗しました")
        exe = paths.CARGO_TARGET / ("release" if release else "debug") / package
        if os.name == "nt":
            exe = exe.with_suffix(".exe")
        return [str(exe)]


# ---- Python ----


class Python(Language):
    key, name, ext, leetcode = "python", "Python", "py", "python3"

    def template(self, problem, snippet):
        snippet = fill_bodies(
            snippet, lambda prev: prev.lstrip().startswith("def ") and prev.rstrip().endswith(":"), "pass"
        )
        return "\n".join(
            [
                header_comment(problem, "#"),
                "# LeetCode で自動的に import されるモジュール（collections・heapq など）と ListNode・TreeNode",
                "from lc_support import *  # noqa: F403",
                "",
                "# " + CODE_START,
                snippet,
                "# " + CODE_END,
                "",
            ]
        )

    def build(self, problem, release, target=None):
        target = Path(target or self.solution_path(problem))
        # 文法の誤りは、テストのケースごとではなく 1 回だけ表示する
        check = "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')"
        if subprocess.run([paths.PYTHON, "-c", check, str(target)]).returncode != 0:
            raise LcError("{} に文法の誤りがあります".format(target.name))
        return [paths.PYTHON, str(paths.PY_RUNNER), "--meta", str(problem.dir / META), str(target)]


LANGUAGES = {lang.key: lang for lang in (Cpp(), Rust(), Python())}


def parse_langs(text):
    if text in (None, "", "all"):
        return list(LANGUAGES.values()) if text == "all" else [LANGUAGES["cpp"]]
    langs = []
    for k in text.split(","):
        k = {"c++": "cpp", "rs": "rust", "py": "python", "python3": "python"}.get(k.strip().lower(), k.strip().lower())
        if k not in LANGUAGES:
            raise LcError("言語は cpp・rust・python・all のどれかです: {}".format(k))
        langs.append(LANGUAGES[k])
    return langs


def set_current(problem, lang, command, target=None):
    """F5 のデバッグ対象（.vscode/launch.json が見る .build/current/）を、この問題にする"""
    save_state(problem, lang.key)
    if lang.key == "python":
        (paths.CURRENT / "python").write_text(str(target or lang.solution_path(problem)), encoding="utf-8", newline="\n")
        return
    link = paths.CURRENT / lang.key
    tmp = paths.CURRENT / (lang.key + ".tmp")
    try:
        tmp.unlink(missing_ok=True)
        os.symlink(command[0], tmp)
        os.replace(tmp, link)
    except OSError as e:
        warn("デバッグ用のリンクを作れませんでした: {}".format(e))
