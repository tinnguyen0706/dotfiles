# dotfiles

Cấu hình Linux Arch Linux + Zsh + Niri + Kitty + Neovim của tôi.

## Thành phần

| Công cụ | Vị trí |
|---------|--------|
| **Zsh** | `.zshrc`, `.zprofile` |
| **Prompt** | `.config/starship.toml` |
| **Terminal** | `.config/kitty/kitty.conf` |
| **Compositor** | `.config/niri/config.kdl` |
| **Trình soạn thảo** | `.config/nvim/` |
| **File manager** | `.config/yazi/` |
| **Resource monitor** | `.config/btop/` |
| **System fetch** | `.config/fastfetch/config.jsonc` |
| **Theme switcher** | `.config/update-theme.py`, `.config/palette.json` |
| **X resources** | `.Xresources` |
| **VS Code flags** | `.config/code-flags.conf` |
| **Spotify flags** | `.config/spotify-launcher.conf` |

## Cài đặt (trên máy mới)

```bash
sudo pacman -S git zsh kitty neovim yazi niri btop fastfetch starship

git clone --bare https://github.com/tinnguyen0706/dotfiles.git ~/.dotfiles
alias config='git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
config checkout

# Nếu báo conflict (file đã tồn tại):
mv ~/.zshrc ~/.zshrc.bak
config checkout

config config status.showUntrackedFiles no
```

## Sử dụng

```bash
config status        # xem thay đổi
config add ~/.zshrc  # thêm file mới
config commit -m "..." # commit
config push          # push lên GitHub
config pull          # pull từ GitHub (máy mới update)
```

## Phím tắt cơ bản

**Niri:**
- `Super` — launcher
- `Super + Shift + Q` — đóng cửa sổ
- `Super + [1-9]` — chuyển workspace

**Kitty:**
- `Ctrl + Shift + T` — tab mới
- `Ctrl + Shift + Enter` — split ngang
- `Ctrl + Shift + H` — đóng tab

**Yazi:**
- `Q` — quit
- `~` — về home
- `Y` — copy đường dẫn
- Gõ tên — filter

## Theming

```bash
# List themes
ls ~/.config/niri/*.kdl

# Swith theme (nếu đã cấu hình update-theme.py)
~/.config/update-theme.py <tên_theme>
```
