// 3304. Find the K-th Character in String Game I (Easy)
// https://leetcode.com/problems/find-the-k-th-character-in-string-game-i/
// 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
// LeetCode と同じく、<bits/stdc++.h>・using namespace std・ListNode・TreeNode は leetcode.hpp で用意している
#include "leetcode.hpp"

// @lc code=start
class Solution {
public:
    char kthCharacter(int k) { return 'a' + __builtin_popcount(k - 1); }
};
// @lc code=end
