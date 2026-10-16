# 愚直解。計算量は気にせず、確実に正しい方法で書く（solution.py と同じく class Solution などを書く）
from lc_support import *  # noqa: F403


class Solution:
    def rotate(self, nums: list[int], k: int) -> None:
        for _ in range(k):
            nums.insert(0, nums.pop())
