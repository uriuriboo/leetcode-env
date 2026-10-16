// LeetCode の C++ 環境を手元で再現するヘッダ。解答（solution.cpp）はこれを include する
//
// LeetCode と同じく、<bits/stdc++.h> と using namespace std を読み込み、ListNode と TreeNode を定義する。
// 中身は leetcode_core.hpp にあり、プリコンパイルして使う。clang のプリコンパイル済みヘッダには
// using namespace std が引き継がれないため、using namespace std だけはこちらに書いている
#ifndef LEETCODE_HPP
#define LEETCODE_HPP

#include "leetcode_core.hpp"

using namespace std;

#endif  // LEETCODE_HPP
