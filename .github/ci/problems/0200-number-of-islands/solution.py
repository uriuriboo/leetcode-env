# 200. Number of Islands (Medium)
# https://leetcode.com/problems/number-of-islands/
# 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
# LeetCode で自動的に import されるモジュール（collections・heapq など）と ListNode・TreeNode
from lc_support import *  # noqa: F403

# @lc code=start
class Solution:
    def numIslands(self, grid: List[List[str]]) -> int:
        h, w = len(grid), len(grid[0])
        count = 0
        for i in range(h):
            for j in range(w):
                if grid[i][j] != "1":
                    continue
                count += 1
                grid[i][j] = "0"
                stack = [(i, j)]
                while stack:
                    y, x = stack.pop()
                    for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                        if 0 <= ny < h and 0 <= nx < w and grid[ny][nx] == "1":
                            grid[ny][nx] = "0"
                            stack.append((ny, nx))
        return count
# @lc code=end
