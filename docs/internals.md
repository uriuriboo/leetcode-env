# 仕組みと保守

この環境の作りと、変更するときに守る要件をまとめたもの。使い方は [guide.md](guide.md) を参照。

## ディレクトリ構成

```text
.devcontainer/      Dockerfile（ツールをイメージに入れる）、devcontainer.json、postCreateCommand.bash
.vscode/            tasks.json（タスク）、launch.json（F5）、settings.json、スニペット
.github/            CI（workflows/）と、CI で使うテスト用の問題（ci/problems/）
scripts/lc.py       lc コマンドの入口。タスクはすべてこれを呼ぶ
scripts/lclib/      lc の本体（標準ライブラリだけで書いている）
    api.py          LeetCode の API（問題の取得、リモートでのテスト、提出）
    problem.py      問題のディレクトリ（meta.json、テストケース、提出する範囲の切り出し）
    langs.py        言語ごとの処理（ひな形、ハーネスの生成、ビルド）
    judge.py        手元でのテストの実行と出力の比較
    remote.py       リモートでのテストと提出の結果の表示
    stress.py       ランダムテスト
scripts/visualize.py  木とグラフの可視化
support/cpp/        leetcode.hpp（解答が include する）と leetcode_core.hpp（本体。プリコンパイルする）
support/rust/       leetcode-support クレート（ListNode・TreeNode、入出力の変換）
support/python/     lc_support.py（LeetCode と同じ import と ListNode・TreeNode）、lc_runner.py（解答を呼ぶ）
problems/           解いた問題（gitignore 対象）
.build/             ビルドの成果物（gitignore 対象。devcontainer では名前付きボリューム）
```

ルートの `Cargo.toml`（Rust のワークスペース）は `lc` が生成する（gitignore 対象）。`problems/*/solution.rs` がある問題をメンバーにする。

## 解答を手元で動かす仕組み

LeetCode の解答は main の無い関数（`class Solution` のメソッド）なので、入力を読んで解答を呼ぶ main（ハーネス）を、問題の型情報から生成する。型情報は LeetCode の API が返す `metaData` で、`meta.json` に保存している。

- 普通の問題：`name`（メソッド名）、`params`（引数の名前と型）、`return`（戻り値の型）。戻り値が `void` で引数を書き換える問題は `output.paramindex` に出力する引数の番号がある
- クラスを設計する問題：`systemdesign: true`、`classname`、`constructor.params`、`methods`
- `manual: true` は LeetCode が特別な方法で判定する問題。手元のテストが動かないことがあるので、注意を表示する

### 入出力の決まり

- 入力は LeetCode の形式（引数 1 つにつき 1 つの JSON の値）。値が続いていれば、次のケースとして順に全部実行する
- 結果は 1 ケース 1 行で、LeetCode の形式（JSON。小数は小数点以下 5 桁、文字列と文字は `"`、null の木やリストは `[]`）で書く
- 環境変数 `LC_OUTPUT` があれば結果をそのファイルに書き、無ければ標準出力に書く。テストでは `LC_OUTPUT` を使い、解答の `cout`・`println!`・`print` と結果を分ける
- 入力の形式が正しくないときは、終了コード 3 で終わる

### 言語ごとのハーネス

| 言語 | ハーネス | 引数の型の決め方 |
| --- | --- | --- |
| C++ | `.build/cpp/<問題>/main.cpp`。`leetcode.hpp` と `solution.cpp` を include する | `lc::run_function<&Solution::twoSum>()` がメンバ関数ポインタから型を取り出す。設計する問題のコンストラクタは、`solution.cpp` のコンストラクタの宣言から読む（読めなければ `metaData` の型から決める） |
| Rust | 問題のディレクトリの `harness.rs`。`solution.rs`（bin のルート）が `mod harness;` で読み込む | `input.read()` の型を、解答の関数の引数から型推論で決める。`&mut` の引数は `solution.rs` の宣言から読む |
| Python | 無し（`support/python/lc_runner.py` が `solution.py` を読み込んで呼ぶ） | `metaData` の型（`ListNode`・`TreeNode` などを作る） |

Rust のハーネスを子モジュールにしているのは、設計する問題の struct やメソッド（`fn new` など）が `pub` ではないため。子モジュールからは親の private な項目を使える。ハーネスはビルドのたびに作り直す（`lc sync` でも作り直せる）。

### 出力の比較（`judge.py`）

- JSON として読めれば値として比べる。小数は誤差 1e-5（相対・絶対）まで許す
- `meta.json` の `compare` が `unordered` なら、一番外側の配列を並べ替えて比べる。問題文に「any order」などがあれば、new のときに自動で `unordered` にする
- 内側まで並べ替えると一致する場合は、WA のまま補足を表示する

## タスクと lc のサブコマンド

| タスク | 呼ぶもの | ${file} を使うか |
| --- | --- | --- |
| new problem | `lc new <問題> --lang <言語>` | 使わない（問題と言語を入力する） |
| new daily problem | `lc daily --lang <言語>` | 使わない |
| test / test release | `lc test [--release] ${file}` | 使う |
| run (input.txt) | `lc run ${file}` | 使う |
| test (remote) | `lc remote --save ${file}` | 使う |
| submit | `lc submit ${file}` | 使う |
| stress: init / hack | `lc stress init\|hack ${file}` | 使う |
| visualize tree / graph | `scripts/visualize.py tree\|graph input.txt` | 使わない |
| login | `lc login` | 使わない |
| debug: build C++ / Rust / Python（非表示） | `lc build --lang <言語> ${file}` | 使う（F5 の preLaunchTask） |

タスクは、拡張機能 Tasks（`actboy168.tasks`）がステータスバーにボタンとして出す。ボタンの表示は各タスクの `options.statusbar`（`label`・`detail`・`filePattern`）で決め、`settings.json` の `tasks.statusbar.default.hide` で既定を非表示にしているので、`options.statusbar.hide` を `false` にしたタスクだけが出る（rust-analyzer が自動で作る cargo のタスクなどは出ない）。`filePattern` は開いているファイルの絶対パスに対する正規表現で、`/problems/` を含むときだけ出す。前から `tasks.statusbar.limit`（6）個を並べ、残りは「その他」にまとめるので、よく使うタスクを tasks.json の前のほうに置く。`"hide": true` のタスク（F5 用）は出ない。クリックすると、開いているエディタのファイルを `${file}` にしてタスクを実行する。

`${file}` からは、上にたどって `meta.json` のあるディレクトリを問題とする。言語は `solution.*` の拡張子で決め、それ以外のファイル（`problem.md`・`stress/*.py` など）では、前回その問題で使った言語か、解答が 1 つならその言語にする。問題の外のファイル（`input.txt` など）では、前回の問題（`.build/current/state.json`）を使う。

F5 のデバッグは、preLaunchTask の `lc build` が `.build/current/cpp`・`.build/current/rust`（実行ファイルへのシンボリックリンク）と `.build/current/python`（実行する .py のパスを書いたファイル）を書き換え、`launch.json` はそれを実行する。`launch.json` 自体は書き換えない。

## LeetCode の API（`api.py`）

| 用途 | エンドポイント | ログイン |
| --- | --- | --- |
| 問題番号から slug を求める | `GET /api/problems/all/`（`~/.cache/leetcode-env/problems.json` にキャッシュ） | 不要 |
| 問題の取得・今日の問題 | `POST /graphql`（`question`、`activeDailyCodingChallengeQuestion`） | 不要（プレミアム問題は必要） |
| リモートでのテスト | `POST /problems/<slug>/interpret_solution/` | 必要 |
| 提出 | `POST /problems/<slug>/submit/` | 必要 |
| 判定結果 | `GET /submissions/detail/<id>/check/`（`state` が `SUCCESS` になるまで 1 秒ごとに見る） | 必要 |

ログインには Cookie の `LEETCODE_SESSION` と `csrftoken` を使い、`csrftoken` は `X-CSRFToken` ヘッダにも入れる。送るコードは、解答のうち `@lc code=start` の行と `@lc code=end` の行の間だけ（`problem.extract_code`。マーカーはコメント記号とマーカーだけの行に限る）。言語は LeetCode の名前（`cpp`・`rust`・`python3`）で送る。

## ビルドを速くするための要件

環境やツールを変えるときも、次の要件を満たすようにする。

| # | 要件 | 実現している場所 |
| --- | --- | --- |
| 1 | ビルドの成果物を Windows ホストの bind mount に置かない | `devcontainer.json` の `mounts`（`.build/` を名前付きボリュームにする）、`.cargo/config.toml` の `target-dir` |
| 2 | C++ の `<bits/stdc++.h>` を毎回コンパイルしない | `langs.precompiled_header`（`leetcode_core.hpp` をプリコンパイルする） |
| 3 | C++ で、変更が無ければコンパイルしない | `langs.Cpp.build`（コマンドと更新時刻を比べる） |
| 4 | Rust のリンカに mold を使う | `.cargo/config.toml`、`Dockerfile` |
| 5 | rust-analyzer のチェックがワークスペース全体に広がらず、タスクのビルドとロックを取り合わない | `settings.json` の `rust-analyzer.check.workspace` と `rust-analyzer.cargo.targetDir` |
| 6 | コンテナを作るたびにツールを入れ直さない | `Dockerfile`（`postCreateCommand.bash` は無いときだけ入れる） |

- `.build/` のボリュームは root 所有で作られるので、`postCreateCommand.bash` で所有者を変える。ホストからは中身が見えない
- 2 の注意：clang のプリコンパイル済みヘッダには、グローバルな `using namespace std;` が引き継がれない。そのため本体の `leetcode_core.hpp` は `std::` を付けて書き、`using namespace std;` は薄い `leetcode.hpp` に書いている。プリコンパイル済みヘッダはフラグごと（debug・release）に作り、コンパイラのバージョン・フラグ・ヘッダの更新時刻が変わると作り直す。clang は `-include-pch`、GCC は `-include` と `.gch` で読む（GCC はヘッダの中から include したものには使わないため）
- 5 の注意：rust-analyzer 用に依存クレートを別にビルドするので、ディスクの使用量は約 2 倍になる

## LeetCode の言語環境が変わったときに直す場所

LeetCode の言語環境は [What are the environments for the programming languages?](https://support.leetcode.com/hc/en-us/articles/360011833974-What-are-the-environments-for-the-programming-languages) にある。バージョンが上がったら、次をまとめて直す。

- C++（clang のバージョン）：`Dockerfile` と `postCreateCommand.bash` の `clang-19`、`langs.cpp_compiler` の `clang++-19`、`settings.json` の `C_Cpp.default.compilerPath`、`CPP_COMMON` の `-std`
- Rust：`rust-toolchain.toml` と `Dockerfile` の `1.88.0`、`langs.PACKAGE_TOML` の edition と依存クレート
- Python：`Dockerfile` と `postCreateCommand.bash` の `3.14`、`paths.PYTHON`、`settings.json` の `python.defaultInterpreterPath`、`launch.json` の `python`。自動で import されるモジュールが変わったら `support/python/lc_support.py`

## ツールのバージョンを上げるとき

LeetCode に合わせているもの（上の節）とは別に、次のバージョンを固定している。

- ベースイメージ：`Dockerfile` の `mcr.microsoft.com/devcontainers/rust:2-1-trixie`。セキュリティ修正はサポート中の最新の系統（いまは `2-1`）にしか入らないので、イメージ定義のメジャーバージョンが上がったら合わせる
- uv：`Dockerfile` の `COPY --from=ghcr.io/astral-sh/uv:<版>` と、`postCreateCommand.bash` のインストーラーの URL（`https://astral.sh/uv/<版>/install.sh`）の 2 か所
- GitHub Actions：`check_environment.yml` の `actions/checkout` と `devcontainers/ci`

非推奨になった拡張機能は置き換える（これまでに、Task Explorer を Tasks に、Even Better TOML を Tombi に置き換えた）。ベースイメージの feature が入れる拡張機能は、`devcontainer.json` の一覧に `-` を付けて書くと入らない（Even Better TOML は `-tamasfe.even-better-toml` で外している）。

## CI

`.github/workflows/check_environment.yml` は 2 つのジョブで `.github/ci/test.bash` を実行する。

- runner：GitHub のランナーで `postCreateCommand.bash` を実行して（ツールが無ければ入れる）テストする。最後に LeetCode から問題を取得できるかを確かめる（LeetCode 側の都合で失敗することがあるので、失敗しても続ける）
- devcontainer：`devcontainers/ci` で `Dockerfile` からイメージを作り、コンテナの中でテストする

`test.bash` は `.github/ci/problems/` の問題（連結リスト、木、クラスの設計、引数の書き換え、小数、文字のグリッドなど）を `problems/` にコピーし、3 つの言語の解答が手元のテストを通ること、release ビルド、F5 の準備、ランダムテスト、可視化、`cargo fmt` を確かめる。ハーネスや `support/` を変えたら、ここに問題を足して確かめる。テスト用の問題は `lc new` で作り、`@lc code=start` と `@lc code=end` の間に解答を書いて、`problem.md` 以外をコピーする（問題文は LeetCode の著作物なのでリポジトリに入れない）。
