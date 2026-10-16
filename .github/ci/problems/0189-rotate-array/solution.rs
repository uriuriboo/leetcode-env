// 189. Rotate Array (Medium)
// https://leetcode.com/problems/rotate-array/
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
    pub fn rotate(nums: &mut Vec<i32>, k: i32) {
        let n = nums.len();
        nums.rotate_right(k as usize % n);
    }
}
// @lc code=end
