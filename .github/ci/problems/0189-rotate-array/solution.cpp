// 189. Rotate Array (Medium)
// https://leetcode.com/problems/rotate-array/
// 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
// LeetCode と同じく、<bits/stdc++.h>・using namespace std・ListNode・TreeNode は leetcode.hpp で用意している
#include "leetcode.hpp"

// @lc code=start
class Solution {
public:
    void rotate(vector<int>& nums, int k) {
        k %= nums.size();
        std::rotate(nums.begin(), nums.end() - k, nums.end());
    }
};
// @lc code=end
