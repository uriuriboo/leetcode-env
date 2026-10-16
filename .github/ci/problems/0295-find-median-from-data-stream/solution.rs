// 295. Find Median from Data Stream (Hard)
// https://leetcode.com/problems/find-median-from-data-stream/
// 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
// clippy::ptr_arg は、LeetCode が決めている引数の型（&mut Vec<i32> など）への警告
#![allow(dead_code, unused_imports, clippy::ptr_arg)]

// LeetCode で定義済みのもの
use leetcode_support::{ListNode, TreeNode};

// 手元で動かすための入口（harness.rs は scripts/lc.py がビルドのたびに生成する）
mod harness;
fn main() {
    harness::main();
}

// @lc code=start
use std::cmp::Reverse;
use std::collections::BinaryHeap;

struct MedianFinder {
    lo: BinaryHeap<i32>,
    hi: BinaryHeap<Reverse<i32>>,
}

impl MedianFinder {
    fn new() -> Self {
        MedianFinder {
            lo: BinaryHeap::new(),
            hi: BinaryHeap::new(),
        }
    }

    fn add_num(&mut self, num: i32) {
        self.lo.push(num);
        let top = self.lo.pop().unwrap();
        self.hi.push(Reverse(top));
        if self.hi.len() > self.lo.len() {
            let Reverse(v) = self.hi.pop().unwrap();
            self.lo.push(v);
        }
    }

    fn find_median(&self) -> f64 {
        if self.lo.len() > self.hi.len() {
            *self.lo.peek().unwrap() as f64
        } else {
            (*self.lo.peek().unwrap() as f64 + self.hi.peek().unwrap().0 as f64) / 2.0
        }
    }
}
// @lc code=end
