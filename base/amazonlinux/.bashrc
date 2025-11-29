# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# User specific environment
if ! [[ "$PATH" =~ "$HOME/.local/bin:$HOME/bin:" ]]
then
    PATH="$HOME/.local/bin:$HOME/bin:$PATH"
fi
export PATH

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
if [ -d ~/.bashrc.d ]; then
	for rc in ~/.bashrc.d/*; do
		if [ -f "$rc" ]; then
			. "$rc"
		fi
	done
fi

unset rc

# ====================================================
# [User Custom Settings]
# ====================================================

# 1. Aliases
alias ll="ls -avl"
alias hs="history"
alias rp="realpath"

# Git Aliases
alias gl="git log --stat --graph --decorate --all"
alias gll="git log --stat --graph --decorate --all -p"
alias gli="git log --graph --decorate --abbrev-commit --format=oneline"
alias gs="git status --branch --show-stash"
alias gd="git diff"
alias gb="git branch -vv -al"
alias gr="git remote -v"
alias gf="git fetch -v"

# Python Venv Helper
alias dev="source ~/venv/dev/bin/activate"
alias test="source ~/venv/test/bin/activate"

# 2. Environment Variables

# 3. JAVA & PATH Auto-configuration
# JAVA_HOME이 설정되어 있지 않다면, java 명령어를 추적해서 자동 설정
if [[ -z "$JAVA_HOME" ]]; then
  if command -v java > /dev/null 2>&1; then
    export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
  fi
fi

# JAVA_HOME이 설정되었고, PATH에 없다면 추가 (중복 방지)
if [[ -n "$JAVA_HOME" ]] && [[ ":$PATH:" != *":$JAVA_HOME/bin:"* ]]; then
  export PATH="$JAVA_HOME/bin:$PATH"
fi

# sbin 경로 누락 방지 (Amazon Linux 일부 이미지 대응)
if [[ ":$PATH:" != *":/usr/local/sbin:"* ]]; then
  export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:$PATH"
fi
