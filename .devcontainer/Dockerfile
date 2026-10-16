# イメージ定義の v2 系（2-1）。セキュリティ修正はサポート中の最新の系統にしか入らないため、古い 1 系は使わない
FROM mcr.microsoft.com/devcontainers/rust:2-1-trixie

# uv は公式の推奨どおり、公式イメージからバイナリをコピーする（バージョンは固定する）
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /usr/local/bin/

# LeetCode と同じ言語環境と、その他のツールをイメージに入れる（リポジトリに依存する処理は postCreateCommand.bash で行う）
# - clang-19・libclang-rt-19-dev：LeetCode と同じ C++ コンパイラ（標準ライブラリは GCC 14 の libstdc++）とサニタイザ
# - mold：Rust のリンクを速くする（.cargo/config.toml）
# - graphviz：木やグラフの可視化（scripts/visualize.py）
# - python3：scripts/lc.py を動かす（ベースイメージの python3-minimal には標準ライブラリの一部しか無い）
# - Python 3.14：LeetCode と同じ Python を uv で入れる。LeetCode で使える sortedcontainers も入れる
# - Rust 1.88.0：LeetCode と同じバージョン（rust-toolchain.toml と合わせる）。rust-src は rust-analyzer の補完に必要
RUN apt-get update && \
    apt-get install -y --no-install-recommends clang-19 libclang-rt-19-dev mold graphviz python3 && \
    rm -rf /var/lib/apt/lists/* && \
    env UV_PYTHON_INSTALL_DIR=/opt/uv/python UV_PYTHON_BIN_DIR=/usr/local/bin uv python install 3.14 && \
    uv pip install --python /usr/local/bin/python3.14 --system --break-system-packages sortedcontainers && \
    rustup toolchain install 1.88.0 --profile minimal --component rustfmt,clippy,rust-src && \
    chmod -R g+w "$RUSTUP_HOME" "$CARGO_HOME"
