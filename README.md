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

Màu được sinh từ wallpaper bằng Noctalia `m3-tonal-spot` ở light mode. `palette.json`
là nguồn màu chung cho Kitty, Starship, Zsh, btop, Yazi, OpenCode, Vesktop và Neovim.
Các surface được tint 15% bằng `primary` gốc để màu nền thay đổi rõ theo wallpaper;
mọi role chữ vẫn phải đạt tương phản tối thiểu `7:1`, kể cả Kitty opacity `0.70`.

```bash
# Áp dụng lại palette.json hiện có
~/.config/update-theme.py

# Sinh palette từ wallpaper rồi cập nhật tất cả ứng dụng
~/.config/update-theme.py --wallpaper /đường/dẫn/wallpaper.jpg

# Chỉ kiểm tra màu và tương phản, không ghi file
~/.config/update-theme.py --check --wallpaper /đường/dẫn/wallpaper.jpg
```

### Hook đổi wallpaper của Noctalia

Noctalia lưu cấu hình đang hoạt động tại `~/.local/state/noctalia/settings.toml`.
Trên máy mới, thêm hook sau vào section `[hooks]`:

```toml
[hooks]
wallpaper_changed = "~/.config/update-theme.py --wallpaper \"$NOCTALIA_WALLPAPER_PATH\""
```

Trong section `[theme]`, dùng cùng scheme với script:

```toml
[theme]
mode = "light"
source = "wallpaper"
wallpaper_scheme = "m3-tonal-spot"
```

Chỉ dùng `wallpaper_changed`; không thêm đồng thời `colors_changed`, nếu không một lần
đổi wallpaper có thể chạy cập nhật theme nhiều lần.

Kiểm tra cấu hình và theo dõi hook:

```bash
noctalia config validate ~/.local/state/noctalia/settings.toml
tail -f ~/.cache/noctalia/noctalia.log \
  | rg --line-buffered 'wallpaper_changed|changing'
```

Khi hoạt động đúng, log sẽ có `hook 'wallpaper_changed' running 1 command(s)` và
trường `source` trong `~/.config/palette.json` sẽ trỏ tới wallpaper vừa chọn.
