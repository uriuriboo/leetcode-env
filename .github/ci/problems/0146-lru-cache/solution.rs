// 146. LRU Cache (Medium)
// https://leetcode.com/problems/lru-cache/
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
use std::collections::{BTreeMap, HashMap};

struct LRUCache {
    cap: usize,
    time: u64,
    map: HashMap<i32, (i32, u64)>,
    order: BTreeMap<u64, i32>,
}

impl LRUCache {
    fn new(capacity: i32) -> Self {
        LRUCache {
            cap: capacity as usize,
            time: 0,
            map: HashMap::new(),
            order: BTreeMap::new(),
        }
    }

    fn touch(&mut self, key: i32, value: i32) {
        if let Some(&(_, t)) = self.map.get(&key) {
            self.order.remove(&t);
        }
        self.time += 1;
        self.map.insert(key, (value, self.time));
        self.order.insert(self.time, key);
    }

    fn get(&mut self, key: i32) -> i32 {
        match self.map.get(&key) {
            Some(&(v, _)) => {
                self.touch(key, v);
                v
            }
            None => -1,
        }
    }

    fn put(&mut self, key: i32, value: i32) {
        self.touch(key, value);
        if self.map.len() > self.cap {
            let (&t, &k) = self.order.iter().next().unwrap();
            self.order.remove(&t);
            self.map.remove(&k);
        }
    }
}
// @lc code=end
