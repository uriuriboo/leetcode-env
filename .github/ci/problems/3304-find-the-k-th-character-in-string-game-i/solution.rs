// 3304. Find the K-th Character in String Game I (Easy)
// https://leetcode.com/problems/find-the-k-th-character-in-string-game-i/
// 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
// clippy::ptr_arg は、LeetCode が決めている引数の型（&mut Vec<i32> など）への警告
#![allow(dead_code, unused_imports, clippy::ptr_arg)]

// LeetCode で定義済みのもの
use leetcode_support::{ListNode, TreeNode};
struct Solution;

// 手元で動かすための入口（harness.rs は scripts/lc.py がビルドのたびに生成する）
mod harness;
fn main() {
    harness::main();
}

// @lc code=start
impl Solution {
    pub fn kth_character(k: i32) -> char {
        (b'a' + (k - 1).count_ones() as u8) as char
    }
}
// @lc code=end
