# 3304. Find the K-th Character in String Game I (Easy)
# https://leetcode.com/problems/find-the-k-th-character-in-string-game-i/
# 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
# LeetCode で自動的に import されるモジュール（collections・heapq など）と ListNode・TreeNode
from lc_support import *  # noqa: F403

# @lc code=start
class Solution:
    def kthCharacter(self, k: int) -> str:
        return chr(ord("a") + (k - 1).bit_count())
# @lc code=end
