// LeetCode の C++ 環境を手元で再現するヘッダの本体（解答からは leetcode.hpp を include する）
//
// - <bits/stdc++.h> を読み込み、LeetCode と同じ ListNode と TreeNode を定義する
// - 名前空間 lc に、LeetCode 形式の入力（引数 1 つにつき 1 行の JSON）を読んで解答を呼び出す処理をまとめている
//   scripts/lc.py が生成する main（.build/cpp/<問題>/main.cpp）から使う
//
// このファイルはプリコンパイルして使う（scripts/lclib/langs.py）。書き換えると、次のビルドで自動的に作り直す。
// clang のプリコンパイル済みヘッダには using namespace std が引き継がれないため、ここには書かず、std:: を付けて書く
#ifndef LEETCODE_CORE_HPP
#define LEETCODE_CORE_HPP

#include <bits/stdc++.h>

// LeetCode で定義済みの構造体（LeetCode の問題文のコメントと同じ定義）
struct ListNode {
    int val;
    ListNode* next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
    ListNode(int x, ListNode* next) : val(x), next(next) {}
};

struct TreeNode {
    int val;
    TreeNode* left;
    TreeNode* right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode* left, TreeNode* right) : val(x), left(left), right(right) {}
};

namespace lc {

// メッセージは引数を並べて書く（std::string の + で連結すると、GCC の -O2 で誤った警告が出るため）
template <class... Args>
[[noreturn]] void input_error(const Args&... args) {
    std::cout.flush();
    std::cerr << "[lc] 入力の形式が正しくありません: ";
    (std::cerr << ... << args) << std::endl;
    std::exit(3);
}

// JSON の値（LeetCode の入出力は JSON とほぼ同じ形式）
struct Json {
    enum Kind { Null, Bool, Number, String, Array };
    Kind kind = Null;
    bool b = false;
    std::string s;  // Number は数値の文字列、String は文字列の中身
    std::vector<Json> a;
};

inline const char* kind_name(Json::Kind k) {
    switch (k) {
        case Json::Null: return "null";
        case Json::Bool: return "真偽値";
        case Json::Number: return "数値";
        case Json::String: return "文字列";
        case Json::Array: return "配列";
    }
    return "?";
}

// 空白や改行で区切られて並んだ JSON の値を、先頭から順に読む
class Reader {
public:
    explicit Reader(std::string text) : t_(std::move(text)) {}

    bool at_end() {
        skip_ws();
        return i_ >= t_.size();
    }

    Json next() {
        if (at_end()) input_error("引数が足りません");
        return value();
    }

private:
    std::string t_;
    size_t i_ = 0;

    void skip_ws() {
        while (i_ < t_.size() && std::isspace(static_cast<unsigned char>(t_[i_]))) i_++;
    }

    bool word(const char* w) {
        size_t n = std::strlen(w);
        if (t_.compare(i_, n, w) != 0) return false;
        i_ += n;
        return true;
    }

    static bool is_number_char(char c) {
        return std::isdigit(static_cast<unsigned char>(c)) || c == '-' || c == '+' || c == '.' || c == 'e' || c == 'E';
    }

    Json value() {
        skip_ws();
        if (i_ >= t_.size()) input_error("値が途中で終わっています");
        Json j;
        char c = t_[i_];
        if (c == '[') {
            j.kind = Json::Array;
            i_++;
            skip_ws();
            if (i_ < t_.size() && t_[i_] == ']') {
                i_++;
                return j;
            }
            while (true) {
                j.a.push_back(value());
                skip_ws();
                if (i_ >= t_.size()) input_error("']' がありません");
                if (t_[i_] == ',') {
                    i_++;
                    continue;
                }
                if (t_[i_] == ']') {
                    i_++;
                    return j;
                }
                input_error("',' か ']' があるはずの場所に '", t_[i_], "' があります");
            }
        }
        if (c == '"') {
            j.kind = Json::String;
            j.s = string_body();
            return j;
        }
        if (word("null")) return j;
        if (word("true")) {
            j.kind = Json::Bool;
            j.b = true;
            return j;
        }
        if (word("false")) {
            j.kind = Json::Bool;
            return j;
        }
        size_t start = i_;
        while (i_ < t_.size() && is_number_char(t_[i_])) i_++;
        if (start == i_) input_error("読めない文字 '", c, "' があります");
        j.kind = Json::Number;
        j.s = t_.substr(start, i_ - start);
        return j;
    }

    uint32_t hex4() {
        if (i_ + 4 > t_.size()) input_error("\\u の後ろに 16 進数が 4 桁ありません");
        uint32_t v = 0;
        for (int k = 0; k < 4; k++) {
            char h = t_[i_++];
            v <<= 4;
            if ('0' <= h && h <= '9')
                v |= h - '0';
            else if ('a' <= h && h <= 'f')
                v |= h - 'a' + 10;
            else if ('A' <= h && h <= 'F')
                v |= h - 'A' + 10;
            else
                input_error("\\u の後ろに 16 進数が 4 桁ありません");
        }
        return v;
    }

    static void append_utf8(std::string& out, uint32_t cp) {
        if (cp < 0x80) {
            out += static_cast<char>(cp);
        } else if (cp < 0x800) {
            out += static_cast<char>(0xC0 | (cp >> 6));
            out += static_cast<char>(0x80 | (cp & 0x3F));
        } else if (cp < 0x10000) {
            out += static_cast<char>(0xE0 | (cp >> 12));
            out += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
            out += static_cast<char>(0x80 | (cp & 0x3F));
        } else {
            out += static_cast<char>(0xF0 | (cp >> 18));
            out += static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
            out += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
            out += static_cast<char>(0x80 | (cp & 0x3F));
        }
    }

    std::string string_body() {
        i_++;  // 開きの "
        std::string out;
        while (true) {
            if (i_ >= t_.size()) input_error("文字列が \" で閉じていません");
            char c = t_[i_++];
            if (c == '"') return out;
            if (c != '\\') {
                out += c;
                continue;
            }
            if (i_ >= t_.size()) input_error("文字列が \" で閉じていません");
            char e = t_[i_++];
            switch (e) {
                case '"': out += '"'; break;
                case '\\': out += '\\'; break;
                case '/': out += '/'; break;
                case 'b': out += '\b'; break;
                case 'f': out += '\f'; break;
                case 'n': out += '\n'; break;
                case 'r': out += '\r'; break;
                case 't': out += '\t'; break;
                case 'u': {
                    uint32_t cp = hex4();
                    if (0xD800 <= cp && cp < 0xDC00 && t_.compare(i_, 2, "\\u") == 0) {
                        i_ += 2;
                        uint32_t lo = hex4();
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                    }
                    append_utf8(out, cp);
                    break;
                }
                default: input_error("不明なエスケープ \\", e);
            }
        }
    }
};

template <class T>
struct is_vector : std::false_type {};
template <class T, class A>
struct is_vector<std::vector<T, A>> : std::true_type {};

template <class>
inline constexpr bool always_false = false;

inline void expect(const Json& j, Json::Kind k, const char* type) {
    if (j.kind != k) input_error(type, " を読むところに", kind_name(j.kind), "があります");
}

// ---- 入力：JSON → C++ の値 ----

template <class T>
T from_json(const Json& j);

inline ListNode* build_list(const Json& j) {
    expect(j, Json::Array, "ListNode");
    ListNode dummy;
    ListNode* tail = &dummy;
    for (const Json& v : j.a) {
        tail->next = new ListNode(from_json<int>(v));
        tail = tail->next;
    }
    return dummy.next;
}

// LeetCode の木の形式（レベル順、子が無いところは null）
inline TreeNode* build_tree(const Json& j) {
    expect(j, Json::Array, "TreeNode");
    auto make = [](const Json& v) -> TreeNode* {
        return v.kind == Json::Null ? nullptr : new TreeNode(from_json<int>(v));
    };
    if (j.a.empty()) return nullptr;
    TreeNode* root = make(j.a[0]);
    if (!root) return nullptr;
    std::queue<TreeNode*> q;
    q.push(root);
    size_t i = 1;
    while (!q.empty() && i < j.a.size()) {
        TreeNode* cur = q.front();
        q.pop();
        cur->left = make(j.a[i++]);
        if (cur->left) q.push(cur->left);
        if (i < j.a.size()) {
            cur->right = make(j.a[i++]);
            if (cur->right) q.push(cur->right);
        }
    }
    return root;
}

template <class T>
T from_json(const Json& j) {
    if constexpr (std::is_same_v<T, bool>) {
        expect(j, Json::Bool, "bool");
        return j.b;
    } else if constexpr (std::is_same_v<T, char>) {
        expect(j, Json::String, "char");
        if (j.s.size() != 1) input_error("char には 1 文字の文字列が必要です: \"", j.s, "\"");
        return j.s[0];
    } else if constexpr (std::is_integral_v<T>) {
        expect(j, Json::Number, "整数");
        long long v = 0;
        auto [p, ec] = std::from_chars(j.s.data(), j.s.data() + j.s.size(), v);
        if (ec != std::errc() || p != j.s.data() + j.s.size()) input_error("整数として読めません: ", j.s);
        if (!std::in_range<T>(v)) input_error("整数の範囲を超えています: ", j.s);
        return static_cast<T>(v);
    } else if constexpr (std::is_floating_point_v<T>) {
        expect(j, Json::Number, "小数");
        return static_cast<T>(std::stod(j.s));
    } else if constexpr (std::is_same_v<T, std::string>) {
        expect(j, Json::String, "string");
        return j.s;
    } else if constexpr (std::is_same_v<T, ListNode*>) {
        return build_list(j);
    } else if constexpr (std::is_same_v<T, TreeNode*>) {
        return build_tree(j);
    } else if constexpr (is_vector<T>::value) {
        expect(j, Json::Array, "vector");
        T v;
        v.reserve(j.a.size());
        for (const Json& e : j.a) v.push_back(from_json<typename T::value_type>(e));
        return v;
    } else {
        static_assert(always_false<T>,
                      "この型の引数には対応していません（leetcode.hpp の from_json に追加してください）");
    }
}

// ---- 出力：C++ の値 → LeetCode の形式 ----

inline void write_string(std::string& out, const std::string& s) {
    out += '"';
    for (unsigned char c : s) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if (c < 0x20) {
                    char buf[8];
                    std::snprintf(buf, sizeof buf, "\\u%04x", c);
                    out += buf;
                } else {
                    out += static_cast<char>(c);
                }
        }
    }
    out += '"';
}

template <class T>
void write(std::string& out, const T& v) {
    if constexpr (std::is_same_v<T, bool>) {
        out += v ? "true" : "false";
    } else if constexpr (std::is_same_v<T, char>) {
        write_string(out, std::string(1, v));
    } else if constexpr (std::is_integral_v<T>) {
        out += std::to_string(v);
    } else if constexpr (std::is_floating_point_v<T>) {
        // LeetCode と同じく小数点以下 5 桁で出す
        char buf[64];
        std::snprintf(buf, sizeof buf, "%.5f", static_cast<double>(v));
        out += buf;
    } else if constexpr (std::is_same_v<T, std::string>) {
        write_string(out, v);
    } else if constexpr (std::is_same_v<T, ListNode*>) {
        out += '[';
        size_t count = 0;
        for (const ListNode* p = v; p; p = p->next) {
            if (count) out += ',';
            if (++count > 1000000) {
                out += "\"...（長すぎます。リストがループしていませんか）\"";
                break;
            }
            out += std::to_string(p->val);
        }
        out += ']';
    } else if constexpr (std::is_same_v<T, TreeNode*>) {
        std::vector<std::string> items;
        std::queue<const TreeNode*> q;
        q.push(v);
        while (!q.empty()) {
            const TreeNode* n = q.front();
            q.pop();
            if (!n) {
                items.push_back("null");
                continue;
            }
            items.push_back(std::to_string(n->val));
            q.push(n->left);
            q.push(n->right);
        }
        while (!items.empty() && items.back() == "null") items.pop_back();
        out += '[';
        for (size_t i = 0; i < items.size(); i++) {
            if (i) out += ',';
            out += items[i];
        }
        out += ']';
    } else if constexpr (is_vector<T>::value) {
        out += '[';
        bool first = true;
        for (const auto& e : v) {
            if (!first) out += ',';
            first = false;
            write<typename T::value_type>(out, e);
        }
        out += ']';
    } else {
        static_assert(always_false<T>,
                      "この型の戻り値には対応していません（leetcode.hpp の write に追加してください）");
    }
}

inline std::string join_list(const std::vector<std::string>& items) {
    std::string s = "[";
    for (size_t i = 0; i < items.size(); i++) {
        if (i) s += ',';
        s += items[i];
    }
    return s + "]";
}

// 結果の出力先。環境変数 LC_OUTPUT があればそのファイル（テストで、解答のデバッグ出力と分けるため）、なければ標準出力
class Output {
public:
    Output() {
        if (const char* p = std::getenv("LC_OUTPUT"); p && *p) file_.open(p);
    }
    void line(const std::string& s) {
        // 途中のケースで落ちても、それまでの結果が残るように毎回 flush する
        if (file_.is_open())
            file_ << s << std::endl;
        else
            std::cout << s << std::endl;
    }

private:
    std::ofstream file_;
};

inline std::string read_all_stdin() {
    std::stringstream ss;
    ss << std::cin.rdbuf();
    return ss.str();
}

// ---- 解答の呼び出し ----

// メンバ関数ポインタから、クラス・戻り値・引数の型を取り出す
template <class C, class R, class... A>
struct Method {
    using Class = C;
    using Ret = R;
    using Args = std::tuple<std::decay_t<A>...>;
    static constexpr size_t N = sizeof...(A);
};
template <class C, class R, class... A>
Method<C, R, A...> method_info(R (C::*)(A...));
template <class C, class R, class... A>
Method<C, R, A...> method_info(R (C::*)(A...) const);

// 波括弧の初期化は左から順に評価されるので、引数は入力の順に読まれる
template <class Args, size_t... I>
Args read_args(Reader& in, std::index_sequence<I...>) {
    return Args{from_json<std::tuple_element_t<I, Args>>(in.next())...};
}

template <class Args, size_t... I>
Args args_from_array(const Json& a, std::index_sequence<I...>) {
    return Args{from_json<std::tuple_element_t<I, Args>>(a.a[I])...};
}

template <class Tuple, size_t... I>
void write_nth(std::string& out, const Tuple& t, size_t n, std::index_sequence<I...>) {
    ((I == n ? write(out, std::get<I>(t)) : void()), ...);
}

// class Solution の問題。入力に複数のケースが並んでいれば、順に全部実行する
// F: 呼び出すメソッド（&Solution::twoSum など）
// output_param: 戻り値が void で、引数を書き換える問題（in-place）のときに出力する引数の番号
template <auto F>
int run_function(int output_param = -1) {
    using M = decltype(method_info(F));
    using C = typename M::Class;
    using R = typename M::Ret;
    using Args = typename M::Args;
    constexpr auto idx = std::make_index_sequence<M::N>{};

    Reader in(read_all_stdin());
    Output out;
    if (M::N > 0 && in.at_end()) input_error("入力が空です（input.txt やテストケースに入力を書いてください）");
    do {
        Args args = read_args<Args>(in, idx);
        C obj;
        std::string s;
        if constexpr (std::is_void_v<R>) {
            std::apply([&](auto&... a) { (obj.*F)(a...); }, args);
            if (output_param >= 0)
                write_nth(s, args, static_cast<size_t>(output_param), idx);
            else
                s = "null";
        } else {
            auto&& r = std::apply([&](auto&... a) -> decltype(auto) { return (obj.*F)(a...); }, args);
            write(s, r);
        }
        out.line(s);
    } while (!in.at_end());
    return 0;
}

// クラスを設計する問題（1 行目がメソッド名の配列、2 行目が引数の配列）
inline void check_design(const std::vector<std::string>& names, const Json& calls, const std::string& cls) {
    expect(calls, Json::Array, "メソッドの引数の配列");
    if (names.empty()) input_error("メソッド名の配列が空です");
    if (names.size() != calls.a.size()) input_error("メソッド名と引数の配列の長さが違います");
    if (names[0] != cls) input_error("1 つ目のメソッド名は ", cls, " のはずが ", names[0], " になっています");
    for (const Json& c : calls.a) expect(c, Json::Array, "メソッドの引数");
}

inline void check_arg_count(const Json& a, size_t n, const std::string& name) {
    if (a.a.size() != n) input_error(name, " の引数は ", n, " 個のはずが ", a.a.size(), " 個あります");
}

template <class T>
T arg(const Json& a, size_t k) {
    return from_json<T>(a.a[k]);
}

// F: 呼び出すメソッド（&LRUCache::get など）
template <auto F, class Obj>
std::string call(Obj* obj, const Json& a, const std::string& name) {
    using M = decltype(method_info(F));
    check_arg_count(a, M::N, name);
    auto args = args_from_array<typename M::Args>(a, std::make_index_sequence<M::N>{});
    if constexpr (std::is_void_v<typename M::Ret>) {
        std::apply([&](auto&... x) { (obj->*F)(x...); }, args);
        return "null";
    } else {
        std::string s;
        auto&& r = std::apply([&](auto&... x) -> decltype(auto) { return (obj->*F)(x...); }, args);
        write(s, r);
        return s;
    }
}

}  // namespace lc

#endif  // LEETCODE_CORE_HPP
