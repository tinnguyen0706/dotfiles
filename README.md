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
| **Theme generator** | `.config/update-theme.py`, `.config/palette.json` |
| **Wallpaper watcher** | `.config/systemd/user/waywallen-palette.*` |
| **X resources** | `.Xresources` |
| **VS Code flags** | `.config/code-flags.conf` |
| **Spotify flags** | `.config/spotify-launcher.conf` |

## Cài đặt (trên máy mới)

```bash
sudo pacman -S git zsh kitty neovim yazi niri btop fastfetch starship python-pillow
paru -S waywallen waywallen-display open-wallpaper-engine

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

Màu được sinh từ wallpaper bằng Noctalia `m3-tonal-spot`. `palette.json` chứa hai lớp:

- Palette root luôn là **light**, dành cho Noctalia, Vesktop và ứng dụng GUI.
- `terminal` tự chọn **light/dark** theo độ sáng wallpaper, dùng chung cho Kitty,
  Starship, Zsh, btop, Yazi, OpenCode và Neovim.

Role chữ của light palette đạt tối thiểu `7:1`; dark terminal palette đạt tối thiểu
`4.5:1`. Yazi, btop, OpenCode và Neovim kế thừa nền trong suốt của Kitty thay vì
tự phủ nền chính.

```bash
# Áp dụng lại palette.json hiện có
~/.config/update-theme.py

# Sinh palette từ wallpaper rồi cập nhật tất cả ứng dụng
~/.config/update-theme.py --wallpaper /đường/dẫn/wallpaper.jpg

# Sinh palette từ preview của wallpaper Waywallen đang chạy
~/.config/update-theme.py --waywallen

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

### Waywallen + Open Wallpaper Engine

Open Wallpaper Engine cung cấp renderer scene/web dưới dạng plugin của Waywallen.
Script lấy item đang hoạt động từ cấu hình và tra preview trong database:

```text
~/.config/waywallen/config.toml
~/.local/share/waywallen/waywallen-v2.db
```

Niri tự chạy `waywallen --no-ui` để phục hồi wallpaper mà không mở cửa sổ quản lý.
Hai user unit theo dõi config và sinh lại palette khi đổi wallpaper:

```bash
systemctl --user daemon-reload
systemctl --user enable --now waywallen-palette.path
systemctl --user status waywallen-palette.path
```

Watcher dùng `preview_path` của item để lấy màu. Phiên Kitty đang mở được reload qua
Unix socket; sau lần cài đầu tiên cần đóng toàn bộ Kitty và mở lại một lần để socket
được tạo. Yazi, btop và OpenCode nhận theme mới ở lần mở kế tiếp.

## Transparency và blur

Niri dùng chung blur `passes 2`, `offset 2.0`, `noise 0.015` cho mọi cửa sổ. App GUI
dùng opacity `0.82` cả khi focus và không focus. Kitty giữ opacity cửa sổ `1.0` để
chữ luôn rõ, đồng thời dùng `background_opacity 0.70` để wallpaper hiện qua phần nền.
