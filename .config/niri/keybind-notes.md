# Note phím đặc biệt — dùng cho cấu hình Niri

> Xác định qua `libinput debug-events` và `evtest` ngày 05/07/2026.

## Phím AI Assistant
- `Super+Shift+XF86Assistant` = Copilot Button

## Dãy Fn+F1 → F12
- `XF86AudioMute` = Fn+F1 (Mute)
- `XF86AudioLowerVolume` = Fn+F2 (Volume Down)
- `XF86AudioRaiseVolume` = Fn+F3 (Volume Up)
- `XF86AudioMicMute` = Fn+F4 (Mic Mute)
- `XF86MonBrightnessDown` = Fn+F5 (Brightness Down)
- `XF86MonBrightnessUp` = Fn+F6 (Brightness Up)
- `Super+P` = Fn+F7 (Project / chuyển màn hình ngoài)
- `XF86RFKill` = Fn+F8 (Airplane mode / RF Kill)
- `XF86Favorites` = Fn+F9 (Favorites)
- `XF86TouchpadOff` = Fn+F10 (Touchpad Toggle)
- `Ctrl+Alt+Tab` = Fn+F11 (Task/Window Switcher)
- `XF86Calculator` = Fn+F12 (Calculator)

## Ghi chú
- `Super+P` và `Ctrl+Alt+Tab` là tổ hợp phím thường (không phải XF86 keysym riêng) → cần kiểm tra xung đột với các bind Super/Ctrl+Alt khác đã có trong `config.kdl`.
- Muốn kiểm tra lại phím nào đó: `sudo libinput debug-events` (nhanh, đủ cho hầu hết phím) hoặc `sudo evtest` (khi thấy `*** (-1)` — tức tổ hợp phím phức tạp libinput không dịch được).
