# 1. Two Sum (Easy)
# https://leetcode.com/problems/two-sum/
# 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
# LeetCode で自動的に import されるモジュール（collections・heapq など）と ListNode・TreeNode
from lc_support import *  # noqa: F403

# @lc code=start
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                print("found", i)  # デバッグ出力が結果と混ざらないことの確認
                return [i, seen[target - x]]  # 順番を逆にして、順不同の比較を確かめる
            seen[x] = i
        return []
# @lc code=end
