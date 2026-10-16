# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## このリポジトリについて

LeetCode の問題を C++・Rust・Python で解くための VS Code devcontainer 環境。アプリケーションではなくテンプレート兼作業場所で、解いた問題（`problems/`）、ルートの `Cargo.toml`・`Cargo.lock`、`.build/`、`input.txt` は gitignore 対象でローカルで生成される。

すべて devcontainer 内（Linux）で動かす前提。ただしスクリプトはワークスペースのパスをハードコードせず、`scripts/lclib/paths.py` がファイルの場所から求める。

## 主なコマンド

```bash
lc new 146 --lang rust     # 問題を取得して problems/0146-lru-cache/ を作る（--lang は cpp・rust・python・all）
lc test problems/0146-lru-cache/solution.rs     # 手元でテスト（--release で LeetCode と同じ最適化）
lc remote / lc submit      # LeetCode のサーバーで実行 / 提出（lc login で Cookie の登録が必要）
lc stress init|hack        # ランダムテスト
lc sync                    # ルートの Cargo.toml と各問題の harness.rs を作り直す
bash .github/ci/test.bash  # CI のテスト（.github/ci/problems/ を problems/ にコピーして全言語をテスト）
```

`lc` は `postCreateCommand.bash` が `/usr/local/bin/lc` に作るラッパーで、`python3 scripts/lc.py` と同じ。VS Code のタスク（`.vscode/tasks.json`）はすべて `scripts/lc.py` を `${file}` 付きで呼び、拡張機能 Tasks（`actboy168.tasks`）がステータスバーのボタンにする（ボタンの設定は各タスクの `options.statusbar`。タスクを足したら付ける）。

## 主な構成

- `scripts/lc.py` が入口で、本体は `scripts/lclib/`（標準ライブラリのみ。system の python3 で動く）。`langs.py` が言語ごとのひな形・ハーネス生成・ビルド、`judge.py` がテストの実行と比較、`api.py` が LeetCode の API、`problem.py` が問題のディレクトリと提出範囲（`@lc code=start`〜`end` の行の間）の切り出し
- 解答は main の無い関数なので、`meta.json` の `metaData`（LeetCode の型情報）からハーネスを生成して呼ぶ。C++ は `.build/cpp/<問題>/main.cpp`（`support/cpp/leetcode_core.hpp` の `lc::run_function` などを使う）、Rust は問題のディレクトリの `harness.rs`（`solution.rs` が `mod harness;` で読む。設計問題の private な項目を呼ぶため子モジュールにしている）、Python は `support/python/lc_runner.py`
- ハーネスは結果を環境変数 `LC_OUTPUT` のファイル（無ければ標準出力）に 1 ケース 1 行で書く。入力の形式エラーは終了コード 3
- C++ は clang 19・C++23・ASan/UBSan。`leetcode_core.hpp` をプリコンパイルする。clang の PCH にはグローバルな `using namespace std;` が残らないので、`leetcode_core.hpp` は `std::` を付けて書き、`using namespace std;` は `leetcode.hpp` に書く
- Rust は 1.88.0（`rust-toolchain.toml`）、各問題が `lc<ディレクトリ名>` というパッケージ。ターゲットは `.build/cargo`（`.cargo/config.toml`）、リンカは mold
- Python は uv で入れた 3.14（`/usr/local/bin/python3.14`）。`support/python/lc_support.py` が LeetCode と同じ import を行う。`__all__` は Pylance が読めるよう、star import の前に組み立てている
- F5 は `launch.json` の preLaunchTask（`lc build`）が `.build/current/` を開いている問題に向け、`launch.json` は書き換えない
- 詳細は `docs/internals.md`（仕組み・ビルド高速化の要件・LeetCode の環境が変わったときに直す場所・CI）、使い方は `docs/guide.md`。タスクや機能を変えたら `Readme.md` と両方のドキュメントを合わせて更新する

## CI

`.github/workflows/check_environment.yml` は、GitHub のランナーと devcontainer（`devcontainers/ci`）の 2 つのジョブで `.github/ci/test.bash` を実行する。ハーネスや `support/` を変えたら `.github/ci/problems/` に問題を足して確かめる。問題文（`problem.md`）は LeetCode の著作物なのでリポジトリに入れない。ドキュメントだけの変更では CI は動かない（`paths-ignore`）。
