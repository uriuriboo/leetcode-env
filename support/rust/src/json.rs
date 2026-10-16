//! LeetCode の入出力（JSON とほぼ同じ形式）を読む

use std::fmt::Write as _;

#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    Null,
    Bool(bool),
    /// 数値は文字列のまま持ち、読む型に合わせて変換する
    Number(String),
    Str(String),
    Array(Vec<Value>),
}

impl Value {
    pub fn kind(&self) -> &'static str {
        match self {
            Value::Null => "null",
            Value::Bool(_) => "真偽値",
            Value::Number(_) => "数値",
            Value::Str(_) => "文字列",
            Value::Array(_) => "配列",
        }
    }
}

pub fn input_error(msg: &str) -> ! {
    eprintln!("[lc] 入力の形式が正しくありません: {msg}");
    std::process::exit(3);
}

/// 空白や改行で区切られて並んだ JSON の値を、先頭から順に読む
pub struct Reader {
    s: Vec<u8>,
    i: usize,
}

impl Reader {
    pub fn new(text: &str) -> Self {
        Reader {
            s: text.as_bytes().to_vec(),
            i: 0,
        }
    }

    pub fn at_end(&mut self) -> bool {
        self.skip_ws();
        self.i >= self.s.len()
    }

    pub fn next_value(&mut self) -> Value {
        if self.at_end() {
            input_error("引数が足りません");
        }
        self.value()
    }

    fn skip_ws(&mut self) {
        while self.i < self.s.len() && self.s[self.i].is_ascii_whitespace() {
            self.i += 1;
        }
    }

    fn word(&mut self, w: &str) -> bool {
        if self.s[self.i..].starts_with(w.as_bytes()) {
            self.i += w.len();
            true
        } else {
            false
        }
    }

    fn value(&mut self) -> Value {
        self.skip_ws();
        if self.i >= self.s.len() {
            input_error("値が途中で終わっています");
        }
        let c = self.s[self.i];
        if c == b'[' {
            self.i += 1;
            let mut items = Vec::new();
            self.skip_ws();
            if self.i < self.s.len() && self.s[self.i] == b']' {
                self.i += 1;
                return Value::Array(items);
            }
            loop {
                items.push(self.value());
                self.skip_ws();
                match self.s.get(self.i) {
                    Some(b',') => self.i += 1,
                    Some(b']') => {
                        self.i += 1;
                        return Value::Array(items);
                    }
                    Some(&c) => input_error(&format!(
                        "',' か ']' があるはずの場所に '{}' があります",
                        c as char
                    )),
                    None => input_error("']' がありません"),
                }
            }
        }
        if c == b'"' {
            return Value::Str(self.string_body());
        }
        if self.word("null") {
            return Value::Null;
        }
        if self.word("true") {
            return Value::Bool(true);
        }
        if self.word("false") {
            return Value::Bool(false);
        }
        let start = self.i;
        while self.i < self.s.len()
            && (self.s[self.i].is_ascii_digit() || b"+-.eE".contains(&self.s[self.i]))
        {
            self.i += 1;
        }
        if start == self.i {
            input_error(&format!("読めない文字 '{}' があります", c as char));
        }
        Value::Number(String::from_utf8_lossy(&self.s[start..self.i]).into_owned())
    }

    fn hex4(&mut self) -> u32 {
        if self.i + 4 > self.s.len() {
            input_error("\\u の後ろに 16 進数が 4 桁ありません");
        }
        let h = std::str::from_utf8(&self.s[self.i..self.i + 4]).unwrap_or("");
        let v = u32::from_str_radix(h, 16)
            .unwrap_or_else(|_| input_error("\\u の後ろに 16 進数が 4 桁ありません"));
        self.i += 4;
        v
    }

    fn string_body(&mut self) -> String {
        self.i += 1; // 開きの "
        let mut out: Vec<u8> = Vec::new();
        loop {
            let Some(&c) = self.s.get(self.i) else {
                input_error("文字列が \" で閉じていません");
            };
            self.i += 1;
            match c {
                b'"' => break,
                b'\\' => {
                    let Some(&e) = self.s.get(self.i) else {
                        input_error("文字列が \" で閉じていません");
                    };
                    self.i += 1;
                    let ch = match e {
                        b'"' => '"',
                        b'\\' => '\\',
                        b'/' => '/',
                        b'b' => '\u{8}',
                        b'f' => '\u{c}',
                        b'n' => '\n',
                        b'r' => '\r',
                        b't' => '\t',
                        b'u' => {
                            let mut cp = self.hex4();
                            if (0xD800..0xDC00).contains(&cp)
                                && self.s[self.i..].starts_with(b"\\u")
                            {
                                self.i += 2;
                                let lo = self.hex4();
                                cp = 0x10000 + ((cp - 0xD800) << 10) + (lo.wrapping_sub(0xDC00));
                            }
                            char::from_u32(cp).unwrap_or('\u{FFFD}')
                        }
                        _ => input_error(&format!("不明なエスケープ \\{}", e as char)),
                    };
                    let mut buf = [0u8; 4];
                    out.extend_from_slice(ch.encode_utf8(&mut buf).as_bytes());
                }
                _ => out.push(c),
            }
        }
        String::from_utf8(out).unwrap_or_else(|_| input_error("文字列が UTF-8 ではありません"))
    }
}

/// 文字列を LeetCode の形式（JSON の文字列）にする
pub fn quote(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => {
                let _ = write!(out, "\\u{:04x}", c as u32);
            }
            c => out.push(c),
        }
    }
    out.push('"');
    out
}
