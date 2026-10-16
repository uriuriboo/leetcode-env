// 23. Merge k Sorted Lists (Hard)
// https://leetcode.com/problems/merge-k-sorted-lists/
// 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
// LeetCode と同じく、<bits/stdc++.h>・using namespace std・ListNode・TreeNode は leetcode.hpp で用意している
#include "leetcode.hpp"

// @lc code=start
class Solution {
public:
    ListNode* mergeKLists(vector<ListNode*>& lists) {
        auto cmp = [](ListNode* a, ListNode* b) { return a->val > b->val; };
        priority_queue<ListNode*, vector<ListNode*>, decltype(cmp)> pq(cmp);
        for (auto* l : lists)
            if (l) pq.push(l);
        ListNode dummy;
        ListNode* tail = &dummy;
        while (!pq.empty()) {
            ListNode* n = pq.top();
            pq.pop();
            tail->next = n;
            tail = n;
            if (n->next) pq.push(n->next);
        }
        return dummy.next;
    }
};
// @lc code=end
