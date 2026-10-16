// 102. Binary Tree Level Order Traversal (Medium)
// https://leetcode.com/problems/binary-tree-level-order-traversal/
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
use std::cell::RefCell;
use std::collections::VecDeque;
use std::rc::Rc;
impl Solution {
    pub fn level_order(root: Option<Rc<RefCell<TreeNode>>>) -> Vec<Vec<i32>> {
        let mut res = Vec::new();
        let mut q = VecDeque::new();
        if let Some(r) = root {
            q.push_back(r);
        }
        while !q.is_empty() {
            let mut level = Vec::new();
            for _ in 0..q.len() {
                let node = q.pop_front().unwrap();
                let n = node.borrow();
                level.push(n.val);
                if let Some(l) = n.left.clone() {
                    q.push_back(l);
                }
                if let Some(r) = n.right.clone() {
                    q.push_back(r);
                }
            }
            res.push(level);
        }
        res
    }
}
// @lc code=end
