#!/bin/bash


# rustup component add rustfmt
# rustup component add clippy

# sudo apt-get update
# sudo apt-get install libdbus-1-dev
# sudo apt install nodejs
# cargo install leetcode-cli

sudo chmod a+x /workspaces/leetcode
sudo chmod a+x /workspaces/leetcode/.devcontainer
cd /workspaces/leetcode/.devcontainer/
sudo chmod -R 747 .

sudo apt-get install build-essential gdb 

# The installation of fish is your choice.
# echo install fish and fisher
# sudo apt-add-repository ppa:fish-shell/release-3
# sudo apt-get update
# sudo apt-get install fish
# curl -sL https://git.io/fisher | source && fisher install jorgebucaran/fisher