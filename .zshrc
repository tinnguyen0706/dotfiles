# Lines configured by zsh-newuser-install
HISTFILE=~/.histfile
HISTSIZE=1000
SAVEHIST=1000
bindkey -e
# End of lines configured by zsh-newuser-install
# The following lines were added by compinstall
zstyle :compinstall filename '/home/tinhiem/.zshrc'

autoload -Uz compinit
compinit
# End of lines added by compinstall
eval "$(starship init zsh)"

# zsh-autosuggestions
source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#2c2226'

# zsh-syntax-highlighting (phải ở cuối cùng)
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# Fastfetch with random quote
alias ff='~/.config/fastfetch/fastfetch.sh'

alias config='git --git-dir=/home/tinhiem/.dotfiles/ --work-tree=/home/tinhiem'

# >>> Codex installer >>>
export PATH="/home/tinhiem/.local/bin:$PATH"
# <<< Codex installer <<<
alias pandock='docker run --rm -v "$(pwd):/data" -u $(id -u):$(id -g) -e HOME=/tmp pandoc-vi'
alias update='~/.config/update-system.sh'
