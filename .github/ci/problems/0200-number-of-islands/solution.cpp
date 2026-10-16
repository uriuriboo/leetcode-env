// 200. Number of Islands (Medium)
// https://leetcode.com/problems/number-of-islands/
// 提出・リモートテストで送るのは「@lc code=start」から「@lc code=end」までの間だけ
// LeetCode と同じく、<bits/stdc++.h>・using namespace std・ListNode・TreeNode は leetcode.hpp で用意している
#include "leetcode.hpp"

// @lc code=start
class Solution {
public:
    int numIslands(vector<vector<char>>& grid) {
        int h = grid.size(), w = grid[0].size(), count = 0;
        int dy[] = {1, -1, 0, 0}, dx[] = {0, 0, 1, -1};
        for (int i = 0; i < h; i++) {
            for (int j = 0; j < w; j++) {
                if (grid[i][j] != '1') continue;
                count++;
                grid[i][j] = '0';
                vector<pair<int, int>> st{{i, j}};
                while (!st.empty()) {
                    auto [y, x] = st.back();
                    st.pop_back();
                    for (int d = 0; d < 4; d++) {
                        int ny = y + dy[d], nx = x + dx[d];
                        if (ny < 0 || ny >= h || nx < 0 || nx >= w || grid[ny][nx] != '1') continue;
                        grid[ny][nx] = '0';
                        st.push_back({ny, nx});
                    }
                }
            }
        }
        return count;
    }
};
// @lc code=end
