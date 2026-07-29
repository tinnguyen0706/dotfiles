# Dotfiles

Dotfiles cho Arch Linux với Zsh, Niri, Noctalia, Kitty, Neovim, Yazi và bộ
profile pin/AC. Repo dùng mô hình bare Git repository: Git directory nằm ở
`~/.dotfiles`, còn `$HOME` là work tree.

## Thành phần chính

| Thành phần | Cấu hình |
| --- | --- |
| Zsh và Starship | `.zshrc`, `.zprofile`, `.config/starship.toml` |
| Niri và Noctalia | `.config/niri/`, `.config/noctalia/` |
| Kitty | `.config/kitty/kitty.conf` |
| System profile | `.config/system-profile.py`, `.local/bin/sp` |
| Waywallen | `.config/systemd/user/waywallen*.{service,path}` |
| Neovim và Yazi | `.config/nvim/`, `.config/yazi/` |
| Dynamic theme | `.config/update-theme.py`, `.config/palette.json` |
| Package snapshot | `.config/dotfiles/packages/` |
| Bootstrap | `.local/bin/bootstrap-dotfiles` |

Runtime files trong `~/.local/state` không được commit. Bootstrap dựng lại chúng
từ template hoặc bằng lệnh `sp sync`.

## Cài trên máy mới

### 1. Checkout dotfiles

```bash
sudo pacman -S --needed git

git clone --bare https://github.com/tinnguyen0706/dotfiles.git ~/.dotfiles
alias config='git --git-dir="$HOME/.dotfiles/" --work-tree="$HOME"'
config checkout
config config status.showUntrackedFiles no
```

Nếu checkout báo file đã tồn tại, sao lưu đúng các file được báo rồi chạy lại.
Ví dụ:

```bash
mkdir -p ~/.dotfiles-backup
mv ~/.zshrc ~/.dotfiles-backup/
config checkout
```

Không xóa toàn bộ `$HOME` để xử lý conflict.

### 2. Cài phần mềm và kích hoạt service

Chế độ portable phù hợp với máy Arch khác phần cứng:

```bash
~/.local/bin/bootstrap-dotfiles
```

Xem trước các thao tác:

```bash
~/.local/bin/bootstrap-dotfiles --dry-run
```

Chỉ dùng chế độ sau cho laptop tương thích Ryzen 7 7435HS + RTX 4050 và hệ
CachyOS hiện tại:

```bash
~/.local/bin/bootstrap-dotfiles --exact-machine
```

Bootstrap sẽ:

- Cài package portable, AUR và Flatpak từ manifests.
- Cài `paru` nếu máy chưa có.
- Sao lưu Noctalia settings hiện hữu rồi cài template đã chuẩn hóa `$HOME`.
- Bật `waywallen-palette.path` và đồng bộ profile hiện tại.
- Với `--exact-machine`, cài driver/kernel tương ứng, bật `auto-cpufreq`, ép
  governor `powersave` và đặt turbo thành `never`.

Một số package phụ thuộc repository CachyOS/Chaotic đang được bật trên máy nguồn.
Nếu package không tồn tại trên máy đích, `paru` sẽ báo lỗi để xử lý thay vì âm
thầm bỏ qua.

### 3. Đăng nhập lại

Đặt Zsh làm shell nếu cần, sau đó đăng xuất/đăng nhập lại:

```bash
chsh -s /bin/zsh
```

Trong phiên Niri mới, kiểm tra:

```bash
sp status
systemctl --user status waywallen-palette.path
niri validate -c ~/.config/niri/config.kdl
noctalia config validate
```

## System profile (`sp`)

```text
sp                         Hiển thị trạng thái
sp power auto              Theo nguồn điện vật lý
sp power battery           Ép profile tiết kiệm pin
sp power ac                Ép profile AC
sp power toggle            Chuyển giữa battery và AC
sp glass on|off|toggle     Điều khiển blur/transparency khi dùng AC
sp sync [battery|ac]       Đồng bộ từ hook Noctalia
sp help                    Xem toàn bộ trợ giúp
```

Profile pin dùng 60 Hz, cửa sổ đục hoàn toàn, tắt blur/shadow/animation và dừng
Waywallen. Profile AC dùng 144 Hz và bật lại Waywallen. Khi chuyển pin sang AC,
glass được bật lại; sau đó vẫn có thể chạy `sp glass off` thủ công mà không tắt
animation hoặc Waywallen.

`auto-cpufreq` độc lập với `sp`. Trên máy nguồn nó luôn bị ép `powersave` và turbo
`never`, kể cả khi cắm sạc.

## Noctalia, Waywallen và theme

Noctalia settings thật nằm tại `~/.local/state/noctalia/settings.toml`. Repo lưu
snapshot tại `.config/noctalia/settings.template.toml`; bootstrap thay `@HOME@`,
loại định danh input riêng của máy và cài snapshot này. File settings cũ được lưu
thành `settings.toml.before-dotfiles`.

Hook Noctalia đồng bộ pin/AC với `sp` và gọi `update-theme.py` khi wallpaper đổi.
Waywallen chạy dưới user service do `sp` điều khiển; watcher palette được bật bằng:

```bash
systemctl --user daemon-reload
systemctl --user enable --now waywallen-palette.path
```

Các lệnh theme:

```bash
~/.config/update-theme.py
~/.config/update-theme.py --wallpaper /path/to/wallpaper.jpg
~/.config/update-theme.py --waywallen
~/.config/update-theme.py --check --wallpaper /path/to/wallpaper.jpg
```

Wallpaper và avatar không được lưu trong Git. Để giao diện giống hoàn toàn, chép
riêng nội dung `~/Pictures/Wallpapers` và avatar, hoặc chọn lại chúng trong
Noctalia. Template hiện tham chiếu output `eDP-1`; máy có tên output khác cần sửa
`.config/niri/monitor.kdl` và Noctalia settings.

## Thiết lập riêng của máy nguồn

Máy nguồn dùng NVIDIA làm GPU hiển thị và boot với:

```text
pcie_aspm=off
```

Bootstrap cố ý không sửa `/etc/kernel/cmdline` hoặc sinh lại bootloader. Đây là
tham số có thể giảm khả năng tiết kiệm điện và chỉ nên sao chép nếu phần cứng mới
thực sự cần nó.

## Quản lý repo

Alias `config` hoạt động như Git nhưng dùng bare repository:

```bash
config status
config add ~/.zshrc
config commit -m "Update shell configuration"
config push
config pull
```

Cache, database, shell history, khóa SSH/GPG, token, browser profiles và dữ liệu
ứng dụng không thuộc phạm vi dotfiles.
