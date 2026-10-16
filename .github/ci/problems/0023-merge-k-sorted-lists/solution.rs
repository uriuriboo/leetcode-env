// 23. Merge k Sorted Lists (Hard)
// https://leetcode.com/problems/merge-k-sorted-lists/
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
use std::cmp::Reverse;
use std::collections::BinaryHeap;
impl Solution {
    pub fn merge_k_lists(lists: Vec<Option<Box<ListNode>>>) -> Option<Box<ListNode>> {
        let mut heap = BinaryHeap::new();
        for list in lists {
            let mut cur = list;
            while let Some(mut node) = cur {
                cur = node.next.take();
                heap.push(Reverse(node.val));
            }
        }
        let mut vals = Vec::new();
        while let Some(Reverse(v)) = heap.pop() {
            vals.push(v);
        }
        let mut head = None;
        for v in vals.into_iter().rev() {
            let mut node = Box::new(ListNode::new(v));
            node.next = head;
            head = Some(node);
        }
        head
    }
}
// @lc code=end
