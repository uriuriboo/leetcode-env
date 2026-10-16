// 2. Add Two Numbers (Medium)
// https://leetcode.com/problems/add-two-numbers/
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
    pub fn add_two_numbers(
        l1: Option<Box<ListNode>>,
        l2: Option<Box<ListNode>>,
    ) -> Option<Box<ListNode>> {
        let (mut a, mut b) = (l1, l2);
        let mut digits = Vec::new();
        let mut carry = 0;
        while a.is_some() || b.is_some() || carry > 0 {
            let mut s = carry;
            if let Some(n) = a {
                s += n.val;
                a = n.next;
            }
            if let Some(n) = b {
                s += n.val;
                b = n.next;
            }
            digits.push(s % 10);
            carry = s / 10;
        }
        let mut head = None;
        for d in digits.into_iter().rev() {
            let mut node = Box::new(ListNode::new(d));
            node.next = head;
            head = Some(node);
        }
        head
    }
}
// @lc code=end
