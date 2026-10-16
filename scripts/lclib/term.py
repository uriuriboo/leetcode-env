"""ターミナルへの表示"""

import os
import sys

_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _wrap(code):
    def f(s):
        return "\033[{}m{}\033[0m".format(code, s) if _COLOR else str(s)

    return f


red = _wrap("31")
green = _wrap("32")
yellow = _wrap("33")
blue = _wrap("34")
cyan = _wrap("36")
bold = _wrap("1")
dim = _wrap("2")


class LcError(Exception):
    """利用者に見せるエラー（トレースバックを出さずにメッセージだけ表示して終了する）"""


def info(msg):
    print(msg, flush=True)


def warn(msg):
    print(yellow("注意: ") + msg, flush=True)


def indent(text, prefix="    "):
    lines = text.rstrip("\n").split("\n") if text else []
    return "\n".join(prefix + line for line in lines)
