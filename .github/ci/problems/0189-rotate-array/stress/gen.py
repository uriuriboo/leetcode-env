# 入力を 1 ケース分、LeetCode の形式（引数 1 つにつき 1 行の JSON）で標準出力に書き出す
# 問題の制約に合わせて書き換える。値を小さくしておくと、反例が見つかったときに手で追いやすい
import json
import random
from collections import deque

ALPHABET = "ab"


def out(x):
    print(json.dumps(x, separators=(",", ":")))


def rand_str(k):
    return "".join(random.choice(ALPHABET) for _ in range(k))


def rand_tree(k):
    """ノードが k 個のランダムな二分木を、LeetCode の形式（レベル順、子が無いところは null）で返す"""
    if k == 0:
        return []
    nodes = [[random.randint(1, 10), None, None]]
    slots = [(0, 1), (0, 2)]
    for _ in range(k - 1):
        parent, side = slots.pop(random.randrange(len(slots)))
        nodes.append([random.randint(1, 10), None, None])
        nodes[parent][side] = len(nodes) - 1
        slots += [(len(nodes) - 1, 1), (len(nodes) - 1, 2)]
    res = []
    queue = deque([0])
    while queue:
        i = queue.popleft()
        if i is None:
            res.append(None)
            continue
        res.append(nodes[i][0])
        queue.append(nodes[i][1])
        queue.append(nodes[i][2])
    while res[-1] is None:
        res.pop()
    return res


n = random.randint(1, 8)
nums = [random.randint(1, 10) for _ in range(n)]  # integer[]
k = random.randint(1, 10)  # integer
out(nums)
out(k)
