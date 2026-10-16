# 使い方ガイド

この環境で LeetCode の問題を解く流れと、各機能の使い方をまとめています。タスクは、画面下のステータスバーに並ぶボタンをクリックして実行します（`Ctrl+Shift+P` →「タスク: タスクの実行」からも実行できます）。ターミナルでは同じことを `lc` コマンドでできます。

ステータスバーのボタンは、開いているファイルによって変わります。

- 問題のファイル（`solution.cpp` など）を開いているとき：`test`・`run`・`submit`・`remote`・`release`・`new`。ランダムテストや可視化などは「その他」から選ぶ
- それ以外のとき：`new`・`daily`・`tree`・`graph`・`digraph`・`login`

問題文（`problem.md`）はプレビューで開くので、このときは問題のボタンが出ません。解答のファイルのタブに切り替えてから押してください。

## 問題を始める

タスク **new problem** を実行し、問題を入力して言語を選びます。

- 問題は、番号（`1`）・slug（`two-sum`）・URL（`https://leetcode.com/problems/two-sum/`）のどれでも指定できます
- 言語は `cpp`・`rust`・`python`・`all`（3 つとも）から選びます
- 今日の問題（Daily Question）は、タスク **new daily problem** で始められます

`problems/<番号>-<slug>/` に次のファイルができ、問題文と解答のファイルが開きます。

```text
problems/0001-two-sum/
├── problem.md      問題文（開くとプレビューで表示される）
├── meta.json       問題の情報（引数と戻り値の型、出力の比較方法など）
├── solution.cpp    解答（選んだ言語のもの。solution.rs・solution.py）
├── tests/          テストケース（sample-1.in・sample-1.out など）
└── stress/         ランダムテスト（stress: init で作る）
```

Rust を選ぶと、`Cargo.toml` と `harness.rs`（手元で動かすためのファイル。自動で作り直されるので編集しない）もできます。

同じ問題でもう一度 new problem を実行して別の言語を選ぶと、その言語の解答を追加できます。既にあるファイルは上書きしません。1 つ目のサンプルの入力は `input.txt` に入るので、すぐに F5 でデバッグできます。

## 解答を書く

解答のファイルは、LeetCode のコードエディタと同じひな形になっています。**LeetCode に送られるのは `@lc code=start` の行と `@lc code=end` の行の間だけ**です。その外側は手元で動かすための部分なので、消さないでください。

### C++

```cpp
#include "leetcode.hpp"

// @lc code=start
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {

    }
};
// @lc code=end
```

- `leetcode.hpp` で、LeetCode と同じく `<bits/stdc++.h>`・`using namespace std`・`ListNode`・`TreeNode` を用意しています
- 手元のビルドでは `LOCAL` が定義されます。`#ifdef LOCAL` で囲んだデバッグ出力は、そのまま提出しても LeetCode では動きません（スニペット `dbg`）
- よく使うマクロや定数（`ll`、`rep`、`chmin` など）は、スニペット `defs` で `@lc code=start` の直後に入れられます

### Rust

```rust
use leetcode_support::{ListNode, TreeNode};
struct Solution;

mod harness;
fn main() {
    harness::main();
}

// @lc code=start
impl Solution {
    pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {
        todo!()
    }
}
// @lc code=end
```

- 上の部分は、LeetCode で定義済みのもの（`ListNode`・`TreeNode`・`struct Solution`）と、手元で動かすための入口です
- `use std::collections::HashMap;` などは、LeetCode でも必要なので `@lc code=start` の内側に書きます
- LeetCode と同じく、rand・regex・itertools を使えます
- 手元のビルド（debug）では整数のオーバーフローで panic します。`#[cfg(debug_assertions)]` を付けた `eprintln!` は、手元でだけ表示されます（スニペット `dbg`）

### Python

```python
from lc_support import *  # noqa: F403

# @lc code=start
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        pass
# @lc code=end
```

- `from lc_support import *` で、LeetCode と同じく `collections`・`heapq`・`bisect`・`functools`・`itertools`・`math`・`typing` などが import なしで使えます（`deque`、`heappush`、`cache`、`List` など）
- `sortedcontainers` は LeetCode でも import が必要なので、`@lc code=start` の内側に `from sortedcontainers import SortedList` のように書きます

### デバッグ出力

`cout`・`println!`・`print` で出力したものは、テストの判定には使わず「標準出力」として別に表示します。デバッグ用の出力を残したままテストできます（LeetCode でも判定には影響しません）。

## 手元でテストする

解答のファイルを開いた状態で、タスク **test** を実行します。`tests/` のケースを並列に実行し、結果を表示します。

```text
sample-1       AC      15 ms
sample-2       WA      12 ms
    入力
        [3,2,4]
        6
    期待する出力
        [1,2]
    あなたの出力
        [0,0]
```

| 結果 | 意味 |
| --- | --- |
| AC | 期待する出力と一致した |
| WA | 一致しなかった |
| RE | 実行時エラー（C++ のサニタイザが検出した範囲外アクセスや、Rust の panic、Python の例外など） |
| TLE | 10 秒以内に終わらなかった |
| -- | 期待する出力（`.out`）が無いので、出力だけを表示した |

- **test release** は LeetCode と同じ最適化（C++ は `-O2`、Rust は opt-level 2）でビルドします。実行時間の目安を見るときに使います。test（debug ビルド）は、C++ では範囲外アクセスなどを細かく検出する代わりに遅くなります
- **run (input.txt)** は `input.txt` を入力にして実行し、出力をそのまま表示します

### 出力の比較

- 小数は誤差 1e-5 まで許します
- 問題文に「any order」などと書いてある問題は、一番外側の配列を並べ替えてから比べます（`meta.json` の `"compare": "unordered"`）。並べ替えると一致するのに `"exact"` になっている問題では、WA の下にその旨を表示するので、`meta.json` を書き換えてください

### テストケースを足す

`tests/` に `.in`（入力）と `.out`（期待する出力）を置くと、テストに加わります。形式は LeetCode の「Testcase」と同じで、引数 1 つにつき 1 行の JSON です。クラスを設計する問題は、メソッド名の配列と引数の配列の 2 行です。

```text
[2,7,11,15]
9
```

期待する出力が分からないときは `.in` だけを置き、タスク **test (remote)** を実行すると、LeetCode の正解が `.out` に保存されます。

## デバッグする

「実行とデバッグ」ビューで構成（**Debug C++**・**Debug Rust**・**Debug Python**）を選び、F5 を押します。開いている問題をビルドし、`input.txt` を標準入力にしてデバッガで実行します。

- `input.txt` は LeetCode の形式（引数 1 つにつき 1 行）で書きます。複数のケースを続けて書くと、順に全部実行します
- `input.txt` などの問題の外のファイルを開いているときは、最後にテスト・ビルドした問題をデバッグします
- Debug Python では、`stress/naive.py` を開いていれば愚直解を、`stress/gen.py` を開いていれば入力の生成をデバッグできます
- C++ でサニタイザがエラーを検出すると、その場所でデバッガが止まります

## LeetCode で確かめる・提出する

### LeetCode にログインする

LeetCode のログイン画面には CAPTCHA があるため、ブラウザの Cookie を使います。

1. ブラウザで <https://leetcode.com> にログインする
2. 開発者ツール（F12）を開き、「Application」（Firefox は「Storage」）→「Cookies」→「`https://leetcode.com`」を選ぶ
3. タスク **login** を実行し、`LEETCODE_SESSION` と `csrftoken` の値を順に貼り付ける（入力した文字は表示されません）

Cookie は Docker のボリューム（`~/.config/leetcode-env/cookies.json`）に保存するので、コンテナを作り直しても残ります。期限が切れたら（「LeetCode に拒否されました」と表示されたら）、もう一度 login します。環境変数 `LEETCODE_SESSION` と `LEETCODE_CSRFTOKEN` でも指定できます。

### test (remote)

`tests/` のすべての入力を LeetCode のサーバーで実行し（LeetCode の「Run」と同じ）、LeetCode の正解と比べます。期待する出力（`.out`）が無いケースには、LeetCode の正解を保存します。手元のテストが動かない問題や、自分で作ったケースの正解を知りたいときに使います。

### submit

まず手元でテストし、すべて通ったら提出します。手元で通らないときは提出しません（それでも提出するときは、ターミナルで `lc submit --no-test <ファイル>`）。

- Accepted なら、実行時間とメモリ、それぞれ何 % の提出より上かを表示します
- 通らなかったときは、そのケースを `tests/submit-NNN.in`（と、分かれば `.out`）に保存し、`input.txt` にもコピーします。そのまま test や F5 で調べられます

## ランダムテスト

サンプルは通るのに提出すると落ちるときに、ランダムな入力で愚直解と比べて反例を探します。

1. タスク **stress: init** を実行すると、`stress/gen.py`（入力の生成）と `stress/naive.py`（愚直解）のひな形ができる
2. `gen.py` を問題の制約に合わせて書き換える。ひな形は引数の型から作ってあり、値は小さめ（1〜10、長さ 1〜8）にしてある
3. `naive.py` に、計算量を気にしない確実な解き方を Python で書く（`solution.py` と同じく `class Solution` の形）
4. タスク **stress: hack** を実行する。反例が見つかるまで繰り返す（止めるときは `Ctrl+C`）

反例が見つかると、入力と `naive.py` の出力を `tests/hack-NNN.in`・`.out` に保存し、`input.txt` にもコピーします。以降は test で毎回確かめられ、F5 でそのままデバッグできます。値を小さくしておくと、反例を手で追いやすくなります。

## 木やグラフを図にする

`input.txt` に問題の入力を貼り、タスクを実行すると `graph.png` を作って開きます。

- **visualize tree**：`[3,9,20,null,null,15,7]` のような二分木（レベル順、子が無いところは null）
- **visualize graph**：`[[0,1],[1,2]]` のような辺のリスト（3 つ目の値は重みとして表示）。clone-graph の `[[2,4],[1,3],[2,4],[1,3]]` のような隣接リスト（i 番目が頂点 i から出る辺の行き先）も、自動で見分けて描く。整数だけの行があれば頂点数とみなし、辺の無い頂点も描く
- **visualize graph (directed)**：有向グラフとして描く

## ターミナルから使う

`lc` コマンドで、タスクと同じことができます。ファイルを省略するとカレントディレクトリから問題を探し、それも問題の中でなければ前回の問題を使います。

```bash
lc new 146 --lang rust      # 問題を始める（--lang は cpp・rust・python・all。カンマ区切りで複数）
lc daily --lang python      # 今日の問題
lc test                     # 手元でテスト（-v で AC のケースも入出力を表示、--release で最適化）
lc run                      # input.txt で実行
lc remote --save            # LeetCode のサーバーで実行
lc submit                   # 提出
lc stress init / lc stress hack --max 1000
lc login
lc --help
```

## 困ったとき

- **「LeetCode に拒否されました（HTTP 403）」**：Cookie の期限が切れています。タスク login でもう一度登録してください
- **プレミアム問題を取得できない**：プレミアム会員のアカウントで login してから new problem を実行してください
- **手元のテストが動かない問題**：グラフの複製（clone-graph）やインタラクティブな問題（guess-number など）は、LeetCode が特別な方法で判定するため、手元のテストが動かないことがあります（new problem のときに注意を表示します）。test (remote) と submit は使えます
- **Rust の補完が効かない**：ルートの `Cargo.toml`（自動で作るワークスペース）が無いか古い可能性があります。ターミナルで `lc sync` を実行し、`Ctrl+Shift+P` →「rust-analyzer: Restart server」を実行してください
- **スクリプトが `$'\r': command not found` で動かない**：改行が CRLF になっています。このリポジトリは `.gitattributes` で改行を LF にそろえているので、`.gitattributes` が入る前に clone した場合は clone し直してください
- **ビルドの成果物を消したい**：`.build/` は Docker のボリュームです。コンテナを止めてから、ホストで `docker volume rm leetcode-env-build` を実行します（フォルダ名を変えている場合は `<フォルダ名>-build`）。Cookie を消すときは `docker volume rm leetcode-env-config` です
