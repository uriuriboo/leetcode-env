// 1. Two Sum (Easy)
// https://leetcode.com/problems/two-sum/
// 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
// LeetCode と同じく、<bits/stdc++.h>・using namespace std・ListNode・TreeNode は leetcode.hpp で用意している
#include "leetcode.hpp"

// @lc code=start
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> seen;
        for (int i = 0; i < (int)nums.size(); i++) {
            auto it = seen.find(target - nums[i]);
            if (it != seen.end()) {
                cout << "found " << i << endl;
                return {i, it->second};
            }
            seen[nums[i]] = i;
        }
        return {};
    }
};
// @lc code=end
