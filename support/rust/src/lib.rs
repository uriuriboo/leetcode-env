//! LeetCode の Rust 環境を手元で再現するクレート
//!
//! - LeetCode で定義済みの `ListNode` と `TreeNode`（定義は LeetCode の問題文のコメントと同じ。`new` だけ `pub` にしている）
//! - [`harness`]：LeetCode 形式の入力（引数 1 つにつき 1 行の JSON）を読み、結果を LeetCode の形式で書く。
//!   各問題の `harness.rs`（scripts/lc.py が生成する）から使う

pub mod harness;
pub mod json;

use std::cell::RefCell;
use std::rc::Rc;

#[derive(PartialEq, Eq, Clone, Debug)]
pub struct ListNode {
    pub val: i32,
    pub next: Option<Box<ListNode>>,
}

impl ListNode {
    #[inline]
    pub fn new(val: i32) -> Self {
        ListNode { next: None, val }
    }
}

#[derive(Debug, PartialEq, Eq)]
pub struct TreeNode {
    pub val: i32,
    pub left: Option<Rc<RefCell<TreeNode>>>,
    pub right: Option<Rc<RefCell<TreeNode>>>,
}

impl TreeNode {
    #[inline]
    pub fn new(val: i32) -> Self {
        TreeNode {
            val,
            left: None,
            right: None,
        }
    }
}
