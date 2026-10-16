# LeetCode env

VS Code の Dev Container で、LeetCode の問題を C++・Rust・Python で解くための環境です。問題の取得から、手元でのテスト・デバッグ、LeetCode での実行・提出までを、VS Code のタスクから行えます。

使い方の詳細は[使い方ガイド](docs/guide.md)に、仕組みと保守の情報は[仕組みと保守](docs/internals.md)にまとめています。

## この環境でできること

VS Code で Dev Container として開くだけで、LeetCode と同じ言語環境ができます。普段の操作は、画面下のステータスバーに並ぶタスクのボタン（拡張機能 [Tasks](https://marketplace.visualstudio.com/items?itemName=actboy168.tasks)）から行います。

### 用意されるもの

- LeetCode と同じ言語環境
  - C++：clang 19、C++23、標準ライブラリは GCC 14 の libstdc++。LeetCode と同じくアドレスサニタイザ付きで動かす
  - Rust：1.88.0（edition 2024）。LeetCode で使える rand・regex・itertools
  - Python：3.14。LeetCode で使える sortedcontainers
- `lc` コマンド（`scripts/lc.py`）：問題の取得、手元でのテスト、LeetCode での実行と提出
- 補完と保存時の自動フォーマット（C++ は cpptools、Rust は rust-analyzer と clippy、Python は Pylance と Ruff）
- デバッガ（C++・Rust は CodeLLDB、Python は debugpy）
- graphviz（木やグラフの可視化）、mold（Rust のリンクを速くする）

### タスクランナーでできること

`solution.cpp` などを開いた状態で実行すると、ファイルの場所（`problems/0001-two-sum/solution.cpp` など）から問題と言語を判定します。test や submit などのボタンは、問題のファイルを開いているときだけ表示されます。ボタンは 6 個まで並び、残りはステータスバーの「その他」から選べます。タスクは `Ctrl+Shift+P` →「タスク: タスクの実行」からも実行できます。

| タスク | ボタン | 内容 |
| --- | --- | --- |
| new problem | new | 問題の番号・slug・URL を入力し、言語を選ぶと、問題文・サンプル・解答のひな形を作る |
| new daily problem | daily | 今日の問題（Daily Question）で new problem をする |
| test | test | 開いている問題を、サンプル（と自分で足したケース）で手元でテストする |
| test release | release | LeetCode と同じ最適化でビルドしてテストする（実行時間の確認用） |
| run (input.txt) | run | `input.txt` を入力にして実行し、出力をそのまま表示する |
| test (remote) | remote | テストケースの入力を LeetCode のサーバーで実行し、LeetCode の正解と比べる |
| submit | submit | 手元でテストしてから提出する。通らなかったケースはテストケースとして保存する |
| stress: init / hack | stress init / hack | ランダムな入力で愚直解と比べ、サンプル以外の反例を探す |
| visualize tree / graph | tree / graph / digraph | `input.txt` の木やグラフを画像にして表示する |
| login | login | LeetCode の Cookie を登録する（test (remote) と submit に必要） |

### 便利にしている点

- **手元でテストできる**：LeetCode の解答は main の無い関数ですが、入力を読んで解答を呼ぶ main を問題の型情報から自動で作ります。連結リスト・二分木・クラスを設計する問題（LRU Cache など）・引数を書き換える問題にも対応しています
- **3 つの言語で同じ問題を解ける**：1 つの問題のディレクトリに `solution.cpp`・`solution.rs`・`solution.py` を並べられ、テストケースも共通です
- **出力の比較が賢い**：小数は誤差 1e-5 まで許し、「順番は問わない」と書いてある問題は並べ替えて比べます
- **すぐにデバッグできる**：F5 で、開いている問題を `input.txt` を入力にしてデバッグできます。新しい問題を作ると、1 つ目のサンプルが `input.txt` に入ります
- **落ちたケースを手元に残す**：提出して通らなかったケースやランダムテストの反例は、テストケースとして保存され、以降の test で毎回確かめられます
- **ビルドが速い**：C++ は `<bits/stdc++.h>` をプリコンパイルし、Rust は mold でリンクします。ビルドの成果物は Windows でも I/O が速い Docker のボリュームに置き、ツールは Docker イメージに入れています

## はじめかた

1. VS Code に拡張機能 Dev Containers を入れ、このリポジトリを開いて「コンテナーで再度開く」を選ぶ
2. LeetCode でテストや提出をするなら、タスク **login** で Cookie を登録する（[手順](docs/guide.md#leetcode-にログインする)）
3. タスク **new problem** を実行し、問題番号（例：`1`）を入力して言語を選ぶ
4. 開いた `solution.*` の `@lc code=start` と `@lc code=end` の間に解答を書き、タスク **test** でテストする
5. 通ったらタスク **submit** で提出する

ターミナルからは `lc` コマンドでも同じことができます（`lc new 1 --lang rust`、`lc test` など。`lc --help` で一覧）。

## 注意

- LeetCode のログイン画面には CAPTCHA があるため、ID とパスワードではログインしません。ブラウザでログインして、Cookie（`LEETCODE_SESSION` と `csrftoken`）をタスク login で貼り付けます。Cookie は Docker のボリュームに保存するので、コンテナを作り直しても残ります
- グラフの複製（clone-graph）やインタラクティブな問題など、LeetCode が特別な方法で判定する問題は、手元のテストが動かないことがあります。そのときは test (remote) を使ってください
- 解いた問題（`problems/`）は gitignore 対象です。自分の解答を Git で管理したいときは、`.gitignore` の `/problems/` の行を消してください
