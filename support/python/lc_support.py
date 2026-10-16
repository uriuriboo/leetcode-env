"""LeetCode の Python3 環境を手元で再現する

- LeetCode で自動的に import されるモジュール（collections、heapq、bisect など）を読み込む
- LeetCode で定義済みの ListNode と TreeNode を定義する

解答（solution.py）の先頭で `from lc_support import *` とすると、LeetCode と同じく import なしで
deque や heappush、List などを使える。Pylance が名前を解決できるよう、公開する名前は __all__ に列挙している
"""

import array
import bisect
import collections
import copy
import datetime
import functools
import heapq
import itertools
import math
import operator
import random
import re
import statistics
import string
import sys
import typing

# 公開する名前。下の from ... import * で copy や random などの名前が関数に置き換わるので、その前に作る
__all__ = [
    "ListNode",
    "TreeNode",
    "array",
    "bisect",
    "collections",
    "copy",
    "datetime",
    "functools",
    "heapq",
    "itertools",
    "math",
    "operator",
    "random",
    "re",
    "statistics",
    "string",
    "sys",
    "typing",
]
__all__ += typing.__all__
__all__ += collections.__all__
__all__ += copy.__all__
__all__ += datetime.__all__
__all__ += functools.__all__
__all__ += heapq.__all__
__all__ += operator.__all__
__all__ += random.__all__
__all__ += statistics.__all__
__all__ += string.__all__
# __all__ が無いモジュール
__all__ += ["ArrayType", "typecodes"]
__all__ += ["bisect_left", "bisect_right", "insort", "insort_left", "insort_right"]
__all__ += [
    "accumulate",
    "batched",
    "chain",
    "combinations",
    "combinations_with_replacement",
    "compress",
    "count",
    "cycle",
    "dropwhile",
    "filterfalse",
    "groupby",
    "islice",
    "pairwise",
    "permutations",
    "product",
    "repeat",
    "starmap",
    "takewhile",
    "tee",
    "zip_longest",
]
__all__ += [
    "acos",
    "acosh",
    "asin",
    "asinh",
    "atan",
    "atan2",
    "atanh",
    "cbrt",
    "ceil",
    "comb",
    "copysign",
    "cos",
    "cosh",
    "degrees",
    "dist",
    "e",
    "exp",
    "exp2",
    "expm1",
    "fabs",
    "factorial",
    "floor",
    "fmod",
    "frexp",
    "fsum",
    "gamma",
    "gcd",
    "hypot",
    "inf",
    "isclose",
    "isfinite",
    "isinf",
    "isnan",
    "isqrt",
    "lcm",
    "ldexp",
    "lgamma",
    "log",
    "log10",
    "log1p",
    "log2",
    "modf",
    "nan",
    "nextafter",
    "perm",
    "pi",
    "prod",
    "radians",
    "remainder",
    "sin",
    "sinh",
    "sqrt",
    "sumprod",
    "tan",
    "tanh",
    "tau",
    "trunc",
    "ulp",
]

# typing を先に読み込む（後にすると、Counter や Deque などが collections ではなく typing の別名になる）
from typing import *  # noqa: E402, F403
from array import *  # noqa: E402, F403
from bisect import *  # noqa: E402, F403
from collections import *  # noqa: E402, F403
from copy import *  # noqa: E402, F403
from datetime import *  # noqa: E402, F403
from functools import *  # noqa: E402, F403
from heapq import *  # noqa: E402, F403
from itertools import *  # noqa: E402, F403
from math import *  # noqa: E402, F403
from operator import *  # noqa: E402, F403
from random import *  # noqa: E402, F403
from statistics import *  # noqa: E402, F403
from string import *  # noqa: E402, F403

# math の pow などで組み込み関数が隠れないよう、組み込み関数を読み込み直す
from builtins import *  # noqa: E402, F403


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

    def __repr__(self):
        return "ListNode({})".format(self.val)


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self):
        return "TreeNode({})".format(self.val)
