//! 各問題の harness.rs（scripts/lc.py が生成する）から使う、入力の読み込みと結果の出力

use crate::json::{Reader, Value, input_error, quote};
use crate::{ListNode, TreeNode};
use std::cell::RefCell;
use std::collections::VecDeque;
use std::fs::File;
use std::io::{Read, Write};
use std::rc::Rc;

fn mismatch(v: &Value, ty: &str) -> ! {
    input_error(&format!("{ty} を読むところに{}があります", v.kind()))
}

// ---- 入力：LeetCode の値 → Rust の値 ----

/// LeetCode の入力の値から作れる型
pub trait FromJson: Sized {
    fn from_json(v: &Value) -> Self;
}

macro_rules! impl_number {
    ($($t:ty),*) => {$(
        impl FromJson for $t {
            fn from_json(v: &Value) -> Self {
                match v {
                    Value::Number(s) => s.parse().unwrap_or_else(|_| {
                        input_error(&format!("{} として読めません: {s}", stringify!($t)))
                    }),
                    _ => mismatch(v, stringify!($t)),
                }
            }
        }
    )*};
}
impl_number!(
    i8, i16, i32, i64, i128, isize, u8, u16, u32, u64, u128, usize, f32, f64
);

impl FromJson for bool {
    fn from_json(v: &Value) -> Self {
        match v {
            Value::Bool(b) => *b,
            _ => mismatch(v, "bool"),
        }
    }
}

impl FromJson for char {
    fn from_json(v: &Value) -> Self {
        match v {
            Value::Str(s) => {
                let mut it = s.chars();
                match (it.next(), it.next()) {
                    (Some(c), None) => c,
                    _ => input_error(&format!("char には 1 文字の文字列が必要です: {}", quote(s))),
                }
            }
            _ => mismatch(v, "char"),
        }
    }
}

impl FromJson for String {
    fn from_json(v: &Value) -> Self {
        match v {
            Value::Str(s) => s.clone(),
            _ => mismatch(v, "String"),
        }
    }
}

impl<T: FromJson> FromJson for Vec<T> {
    fn from_json(v: &Value) -> Self {
        match v {
            Value::Array(items) => items.iter().map(T::from_json).collect(),
            _ => mismatch(v, "Vec"),
        }
    }
}

impl FromJson for Option<Box<ListNode>> {
    fn from_json(v: &Value) -> Self {
        let Value::Array(items) = v else {
            mismatch(v, "ListNode")
        };
        let mut head = None;
        for x in items.iter().rev() {
            let mut node = Box::new(ListNode::new(i32::from_json(x)));
            node.next = head;
            head = Some(node);
        }
        head
    }
}

fn tree_node(v: &Value) -> Option<Rc<RefCell<TreeNode>>> {
    match v {
        Value::Null => None,
        _ => Some(Rc::new(RefCell::new(TreeNode::new(i32::from_json(v))))),
    }
}

/// LeetCode の木の形式（レベル順、子が無いところは null）
impl FromJson for Option<Rc<RefCell<TreeNode>>> {
    fn from_json(v: &Value) -> Self {
        let Value::Array(items) = v else {
            mismatch(v, "TreeNode")
        };
        let root = tree_node(items.first()?)?;
        let mut queue = VecDeque::from([root.clone()]);
        let mut rest = items[1..].iter();
        while let Some(cur) = queue.pop_front() {
            let Some(l) = rest.next() else { break };
            let left = tree_node(l);
            if let Some(n) = &left {
                queue.push_back(n.clone());
            }
            cur.borrow_mut().left = left;
            let Some(r) = rest.next() else { break };
            let right = tree_node(r);
            if let Some(n) = &right {
                queue.push_back(n.clone());
            }
            cur.borrow_mut().right = right;
        }
        Some(root)
    }
}

// ---- 出力：Rust の値 → LeetCode の形式 ----

/// LeetCode の形式で出力できる型
pub trait ToLc {
    fn to_lc(&self) -> String;
}

macro_rules! impl_int_to_lc {
    ($($t:ty),*) => {$(
        impl ToLc for $t {
            fn to_lc(&self) -> String {
                self.to_string()
            }
        }
    )*};
}
impl_int_to_lc!(
    i8, i16, i32, i64, i128, isize, u8, u16, u32, u64, u128, usize
);

/// LeetCode と同じく小数点以下 5 桁で出す
impl ToLc for f64 {
    fn to_lc(&self) -> String {
        format!("{self:.5}")
    }
}

impl ToLc for f32 {
    fn to_lc(&self) -> String {
        format!("{self:.5}")
    }
}

impl ToLc for bool {
    fn to_lc(&self) -> String {
        self.to_string()
    }
}

impl ToLc for char {
    fn to_lc(&self) -> String {
        quote(&self.to_string())
    }
}

impl ToLc for str {
    fn to_lc(&self) -> String {
        quote(self)
    }
}

impl ToLc for String {
    fn to_lc(&self) -> String {
        quote(self)
    }
}

/// 戻り値が無いメソッド（クラスを設計する問題）は null
impl ToLc for () {
    fn to_lc(&self) -> String {
        "null".to_string()
    }
}

impl<T: ToLc + ?Sized> ToLc for &T {
    fn to_lc(&self) -> String {
        (**self).to_lc()
    }
}

impl<T: ToLc> ToLc for [T] {
    fn to_lc(&self) -> String {
        let items: Vec<String> = self.iter().map(ToLc::to_lc).collect();
        format!("[{}]", items.join(","))
    }
}

impl<T: ToLc> ToLc for Vec<T> {
    fn to_lc(&self) -> String {
        self.as_slice().to_lc()
    }
}

impl ToLc for Option<Box<ListNode>> {
    fn to_lc(&self) -> String {
        let mut items = Vec::new();
        let mut cur = self;
        while let Some(node) = cur {
            if items.len() >= 1_000_000 {
                items.push(quote("...（長すぎます。リストがループしていませんか）"));
                break;
            }
            items.push(node.val.to_string());
            cur = &node.next;
        }
        format!("[{}]", items.join(","))
    }
}

impl ToLc for Option<Rc<RefCell<TreeNode>>> {
    fn to_lc(&self) -> String {
        let mut items = Vec::new();
        let mut queue = VecDeque::from([self.clone()]);
        while let Some(node) = queue.pop_front() {
            match node {
                None => items.push("null".to_string()),
                Some(n) => {
                    let n = n.borrow();
                    items.push(n.val.to_string());
                    queue.push_back(n.left.clone());
                    queue.push_back(n.right.clone());
                }
            }
        }
        while items.last().is_some_and(|s| s == "null") {
            items.pop();
        }
        format!("[{}]", items.join(","))
    }
}

// ---- 入力の読み込みと結果の出力 ----

/// 標準入力に並んだ LeetCode 形式の値を、順に読む
pub struct Input {
    reader: Reader,
}

impl Input {
    pub fn stdin() -> Self {
        let mut s = String::new();
        std::io::stdin()
            .read_to_string(&mut s)
            .unwrap_or_else(|e| input_error(&format!("標準入力を読めません: {e}")));
        let mut reader = Reader::new(&s);
        if reader.at_end() {
            input_error("入力が空です（input.txt やテストケースに入力を書いてください）");
        }
        Input { reader }
    }

    pub fn has_next(&mut self) -> bool {
        !self.reader.at_end()
    }

    pub fn read<T: FromJson>(&mut self) -> T {
        T::from_json(&self.reader.next_value())
    }

    /// クラスを設計する問題の 1 ケース分（1 行目がメソッド名の配列、2 行目が引数の配列）
    pub fn next_design(&mut self, class: &str) -> Vec<(String, Args)> {
        let names: Vec<String> = self.read();
        let calls = self.reader.next_value();
        let Value::Array(calls) = calls else {
            mismatch(&calls, "メソッドの引数の配列")
        };
        if names.is_empty() {
            input_error("メソッド名の配列が空です");
        }
        if names.len() != calls.len() {
            input_error("メソッド名と引数の配列の長さが違います");
        }
        if names[0] != class {
            input_error(&format!(
                "1 つ目のメソッド名は {class} のはずが {} になっています",
                names[0]
            ));
        }
        names
            .into_iter()
            .zip(calls)
            .map(|(name, call)| {
                let Value::Array(items) = call else {
                    mismatch(&call, "メソッドの引数")
                };
                let args = Args {
                    name: name.clone(),
                    items,
                    pos: 0,
                };
                (name, args)
            })
            .collect()
    }
}

/// メソッド 1 回分の引数
pub struct Args {
    name: String,
    items: Vec<Value>,
    pos: usize,
}

impl Args {
    pub fn read<T: FromJson>(&mut self) -> T {
        let Some(v) = self.items.get(self.pos) else {
            input_error(&format!("{} の引数が足りません", self.name))
        };
        self.pos += 1;
        T::from_json(v)
    }

    pub fn finish(&self) {
        if self.pos != self.items.len() {
            input_error(&format!(
                "{} の引数は {} 個のはずが {} 個あります",
                self.name,
                self.pos,
                self.items.len()
            ));
        }
    }

    pub fn unknown(&self) -> ! {
        input_error(&format!("{} というメソッドはありません", self.name))
    }
}

/// 結果の出力先。環境変数 LC_OUTPUT があればそのファイル（テストで、解答のデバッグ出力と分けるため）、なければ標準出力
pub struct Output {
    file: Option<File>,
}

impl Output {
    pub fn new() -> Self {
        let file = match std::env::var("LC_OUTPUT") {
            Ok(path) if !path.is_empty() => Some(
                File::create(&path)
                    .unwrap_or_else(|e| input_error(&format!("{path} を作れません: {e}"))),
            ),
            _ => None,
        };
        Output { file }
    }

    /// 途中のケースで落ちても、それまでの結果が残るように毎回 flush する
    pub fn line(&mut self, s: &str) {
        match &mut self.file {
            Some(f) => {
                let _ = writeln!(f, "{s}");
                let _ = f.flush();
            }
            None => {
                let mut stdout = std::io::stdout().lock();
                let _ = writeln!(stdout, "{s}");
                let _ = stdout.flush();
            }
        }
    }
}

impl Default for Output {
    fn default() -> Self {
        Self::new()
    }
}
