"""LeetCode（leetcode.com）の API

- 問題の取得（GraphQL）はログインなしで使える。ログインしていればプレミアム問題も取れる
- リモートでのテスト（interpret_solution）と提出（submit）には、ブラウザの Cookie（LEETCODE_SESSION と csrftoken）が必要。
  LeetCode のログイン画面は CAPTCHA があるため、ID とパスワードでのログインはせず、タスク "login" で Cookie を貼り付ける
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from .term import LcError

BASE = "https://leetcode.com"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)

# ~/.config はコンテナを作り直すと消える。そのときは "login" をやり直す
COOKIE_FILE = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "leetcode-env" / "cookies.json"
PROBLEM_LIST_CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "leetcode-env" / "problems.json"

QUESTION_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    questionFrontendId
    title
    titleSlug
    content
    isPaidOnly
    difficulty
    exampleTestcases
    sampleTestCase
    metaData
    codeSnippets { langSlug code }
    topicTags { name }
    hints
  }
}
"""

DAILY_QUERY = "query { activeDailyCodingChallengeQuestion { date question { titleSlug } } }"
USER_QUERY = "query { userStatus { isSignedIn username isPremium } }"


# ---- Cookie ----


def load_cookies():
    session = os.environ.get("LEETCODE_SESSION")
    csrf = os.environ.get("LEETCODE_CSRFTOKEN")
    if session and csrf:
        return {"LEETCODE_SESSION": session, "csrftoken": csrf}
    if COOKIE_FILE.is_file():
        try:
            d = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
        except ValueError:
            return None
        if d.get("LEETCODE_SESSION") and d.get("csrftoken"):
            return d
    return None


def save_cookies(session, csrf):
    COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    COOKIE_FILE.write_text(json.dumps({"LEETCODE_SESSION": session, "csrftoken": csrf}), encoding="utf-8", newline="\n")
    try:
        os.chmod(COOKIE_FILE, 0o600)
    except OSError:
        pass


# ---- HTTP ----


def _request(method, url, data=None, referer=None, cookies=None):
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": referer or BASE + "/",
        "Origin": BASE,
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }
    if cookies:
        headers["Cookie"] = "LEETCODE_SESSION={}; csrftoken={}".format(cookies["LEETCODE_SESSION"], cookies["csrftoken"])
        headers["X-CSRFToken"] = cookies["csrftoken"]
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        if e.code in (401, 403) and cookies:
            raise AuthError(
                "LeetCode に拒否されました（HTTP {}）。Cookie の期限が切れている可能性があります。"
                "タスク \"login\" で Cookie を貼り直してください".format(e.code)
            ) from None
        if e.code == 429:
            raise LcError("リクエストが多すぎます（HTTP 429）。少し待ってから実行し直してください") from None
        raise LcError("LeetCode への接続に失敗しました（HTTP {}）: {}\n{}".format(e.code, url, detail)) from None
    except urllib.error.URLError as e:
        raise LcError("LeetCode に接続できません: {}".format(e.reason)) from None
    try:
        return json.loads(text)
    except ValueError:
        raise LcError("LeetCode から想定外の応答がありました: {}".format(text[:300])) from None


class AuthError(LcError):
    pass


def require_login():
    cookies = load_cookies()
    if not cookies:
        raise LcError("ログインしていません。タスク \"login\" で LeetCode の Cookie を登録してください")
    return cookies


def graphql(query, variables=None, referer=None):
    cookies = load_cookies()
    try:
        d = _request("POST", BASE + "/graphql", {"query": query, "variables": variables or {}}, referer, cookies)
    except AuthError:
        # Cookie が古いと拒否されることがある。問題の取得はログインなしでもできるので、Cookie なしでやり直す
        d = _request("POST", BASE + "/graphql", {"query": query, "variables": variables or {}}, referer)
    if d.get("errors"):
        raise LcError("LeetCode の API がエラーを返しました: {}".format(d["errors"]))
    return d["data"]


# ---- 問題 ----


def _problem_list(refresh):
    if not refresh and PROBLEM_LIST_CACHE.is_file():
        return json.loads(PROBLEM_LIST_CACHE.read_text(encoding="utf-8"))
    d = _request("GET", BASE + "/api/problems/all/")
    table = {str(p["stat"]["frontend_question_id"]): p["stat"]["question__title_slug"] for p in d["stat_status_pairs"]}
    PROBLEM_LIST_CACHE.parent.mkdir(parents=True, exist_ok=True)
    PROBLEM_LIST_CACHE.write_text(json.dumps(table), encoding="utf-8", newline="\n")
    return table


def resolve_slug(text):
    """問題番号・slug・URL のどれからでも slug を求める"""
    text = text.strip()
    m = re.search(r"leetcode\.(?:com|cn)/problems/([\w-]+)", text)
    if m:
        return m.group(1)
    if text.isdigit():
        number = str(int(text))
        slug = _problem_list(refresh=False).get(number) or _problem_list(refresh=True).get(number)
        if not slug:
            raise LcError("{} 番の問題が見つかりません".format(text))
        return slug
    if re.fullmatch(r"[a-z0-9-]+", text):
        return text
    raise LcError("問題を指定できません: {}（番号・slug・URL のどれかを入力してください）".format(text))


def question(slug):
    q = graphql(QUESTION_QUERY, {"titleSlug": slug}, referer="{}/problems/{}/".format(BASE, slug))["question"]
    if q is None:
        raise LcError("問題が見つかりません: {}".format(slug))
    if not q.get("content") or not q.get("metaData"):
        if q.get("isPaidOnly"):
            raise LcError("プレミアム会員向けの問題です。プレミアム会員なら、タスク \"login\" で Cookie を登録してから取得してください")
        raise LcError("問題文を取得できませんでした: {}".format(slug))
    return q


def daily_slug():
    return graphql(DAILY_QUERY)["activeDailyCodingChallengeQuestion"]["question"]["titleSlug"]


def user_status(cookies):
    d = _request("POST", BASE + "/graphql", {"query": USER_QUERY}, cookies=cookies)
    if d.get("errors"):
        raise LcError("LeetCode の API がエラーを返しました: {}".format(d["errors"]))
    return d["data"]["userStatus"]


# ---- リモートでのテストと提出 ----


def _poll(run_id, slug):
    cookies = require_login()
    deadline = time.time() + 180
    while True:
        d = _request(
            "GET",
            "{}/submissions/detail/{}/check/".format(BASE, run_id),
            referer="{}/problems/{}/".format(BASE, slug),
            cookies=cookies,
        )
        if d.get("state") == "SUCCESS":
            return d
        if time.time() > deadline:
            raise LcError("LeetCode の判定が終わりません（{}）".format(run_id))
        time.sleep(1)


def interpret(slug, question_id, lang, code, data_input):
    """LeetCode のサーバーで、指定した入力を実行する（LeetCode の "Run"）"""
    cookies = require_login()
    d = _request(
        "POST",
        "{}/problems/{}/interpret_solution/".format(BASE, slug),
        {"lang": lang, "question_id": question_id, "typed_code": code, "data_input": data_input},
        referer="{}/problems/{}/".format(BASE, slug),
        cookies=cookies,
    )
    if not d.get("interpret_id"):
        raise LcError("実行を受け付けてもらえませんでした: {}".format(d))
    return _poll(d["interpret_id"], slug)


def submit(slug, question_id, lang, code):
    """提出する。戻り値は (提出 ID, 判定結果)"""
    cookies = require_login()
    d = _request(
        "POST",
        "{}/problems/{}/submit/".format(BASE, slug),
        {"lang": lang, "question_id": question_id, "typed_code": code},
        referer="{}/problems/{}/".format(BASE, slug),
        cookies=cookies,
    )
    if not d.get("submission_id"):
        raise LcError("提出を受け付けてもらえませんでした: {}".format(d))
    return d["submission_id"], _poll(d["submission_id"], slug)
