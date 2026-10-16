# 23. Merge k Sorted Lists (Hard)
# https://leetcode.com/problems/merge-k-sorted-lists/
# 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
# LeetCode で自動的に import されるモジュール（collections・heapq など）と ListNode・TreeNode
from lc_support import *  # noqa: F403

# @lc code=start
class Solution:
    def mergeKLists(self, lists: list[ListNode | None]) -> ListNode | None:
        heap = [(node.val, i, node) for i, node in enumerate(lists) if node]
        heapify(heap)
        dummy = tail = ListNode()
        while heap:
            _, i, node = heappop(heap)
            tail.next = tail = node
            if node.next:
                heappush(heap, (node.next.val, i, node.next))
        return dummy.next
# @lc code=end
