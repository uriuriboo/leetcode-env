# 102. Binary Tree Level Order Traversal (Medium)
# https://leetcode.com/problems/binary-tree-level-order-traversal/
# 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
# LeetCode で自動的に import されるモジュール（collections・heapq など）と ListNode・TreeNode
from lc_support import *  # noqa: F403

# @lc code=start
class Solution:
    def levelOrder(self, root: TreeNode | None) -> list[list[int]]:
        res = []
        level = [root] if root else []
        while level:
            res.append([n.val for n in level])
            level = [c for n in level for c in (n.left, n.right) if c]
        return res
# @lc code=end
