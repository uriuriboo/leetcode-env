// 295. Find Median from Data Stream (Hard)
// https://leetcode.com/problems/find-median-from-data-stream/
// 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
// LeetCode と同じく、<bits/stdc++.h>・using namespace std・ListNode・TreeNode は leetcode.hpp で用意している
#include "leetcode.hpp"

// @lc code=start
class MedianFinder {
    priority_queue<int> lo;
    priority_queue<int, vector<int>, greater<int>> hi;

public:
    MedianFinder() {}

    void addNum(int num) {
        lo.push(num);
        hi.push(lo.top());
        lo.pop();
        if (hi.size() > lo.size()) {
            lo.push(hi.top());
            hi.pop();
        }
    }

    double findMedian() {
        if (lo.size() > hi.size()) return lo.top();
        return (lo.top() + (double)hi.top()) / 2;
    }
};
// @lc code=end
