// 200. Number of Islands (Medium)
// https://leetcode.com/problems/number-of-islands/
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
    pub fn num_islands(grid: Vec<Vec<char>>) -> i32 {
        let mut grid = grid;
        let (h, w) = (grid.len(), grid[0].len());
        let mut count = 0;
        for i in 0..h {
            for j in 0..w {
                if grid[i][j] != '1' {
                    continue;
                }
                count += 1;
                grid[i][j] = '0';
                let mut stack = vec![(i, j)];
                while let Some((y, x)) = stack.pop() {
                    for (ny, nx) in [
                        (y + 1, x),
                        (y.wrapping_sub(1), x),
                        (y, x + 1),
                        (y, x.wrapping_sub(1)),
                    ] {
                        if ny < h && nx < w && grid[ny][nx] == '1' {
                            grid[ny][nx] = '0';
                            stack.push((ny, nx));
                        }
                    }
                }
            }
        }
        count
    }
}
// @lc code=end
