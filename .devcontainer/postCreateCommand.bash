#!/bin/bash
# devcontainer を作った後（と CI）に実行する。リポジトリに依存する準備をする
# ツールは Dockerfile でイメージに入れている。ここでは、ツールが無い環境（CI など）でだけインストールする

cd "$(dirname "$0")/.." || exit 1

# .build/ と ~/.config/leetcode-env は名前付きボリューム（devcontainer.json の mounts）で root 所有で作られるため、所有者を変える
# （~/.config も、マウントのために root 所有で作られることがある）
mkdir -p .build problems "$HOME/.config/leetcode-env"
for d in .build "$HOME/.config" "$HOME/.config/leetcode-env"; do
    if [ "$(stat -c %u "$d")" != "$(id -u)" ]; then
        echo "change owner of $d"
        sudo chown -R "$(id -u):$(id -g)" "$d"
    fi
done

# デバッグ実行（F5）の標準入力。gitignore 対象
touch input.txt

# C++ のコンパイラ、Rust のリンカ（mold）、可視化（graphviz）
missing=()
command -v clang++-19 > /dev/null || command -v clang++ > /dev/null || missing+=(clang-19 libclang-rt-19-dev)
command -v mold > /dev/null || missing+=(mold)
command -v dot > /dev/null || missing+=(graphviz)
if [ ${#missing[@]} -gt 0 ]; then
    echo "install ${missing[*]}"
    sudo apt-get update
    sudo apt-get install -y "${missing[@]}"
fi

# 解答を動かす Python 3.14（LeetCode と同じ）。システムの python3 とは別に uv で入れ、/usr/local/bin/python3.14 に置く
# uv は公式のインストーラーで入れる（バージョンは Dockerfile と合わせる）
if ! command -v python3.14 > /dev/null; then
    echo install python3.14
    command -v uv > /dev/null || curl -LsSf https://astral.sh/uv/0.13.1/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh
    sudo env UV_PYTHON_INSTALL_DIR=/opt/uv/python UV_PYTHON_BIN_DIR=/usr/local/bin "$(command -v uv)" python install 3.14
    sudo "$(command -v uv)" pip install --python /usr/local/bin/python3.14 --system --break-system-packages sortedcontainers
fi

# rust-toolchain.toml のツールチェーン（LeetCode と同じ 1.88.0）。Dockerfile で入れていれば何もしない
toolchain=$(sed -n 's/^channel = "\(.*\)"$/\1/p' rust-toolchain.toml)
rustup toolchain install "$toolchain" --profile minimal --component rustfmt,clippy,rust-src

# どこからでも lc コマンド（scripts/lc.py）を使えるようにする
printf '#!/bin/sh\nexec python3 "%s/scripts/lc.py" "$@"\n' "$(pwd)" | sudo tee /usr/local/bin/lc > /dev/null
sudo chmod +x /usr/local/bin/lc

# Rust のワークスペース（ルートの Cargo.toml。gitignore 対象）を作る。rust-analyzer はこれを読む
python3 scripts/lc.py sync

if [ -z "$CI" ]; then
    echo
    echo "準備ができました。LeetCode でのテストや提出には、タスク \"login\" で Cookie を登録してください"
fi
