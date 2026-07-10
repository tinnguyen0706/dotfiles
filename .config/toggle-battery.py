#!/usr/bin/env python3
"""Toggle battery-saver mode for Niri & Kitty.

Usage:
    toggle-battery.py          — toggle between performance / battery
    toggle-battery.py status   — show current state
    toggle-battery.py on       — force battery mode
    toggle-battery.py off      — force performance mode
"""

import os, sys, re

CONFIG = os.path.expanduser("~/.config")
NIRI_FILE = f"{CONFIG}/niri/config.kdl"
KITTY_FILE = f"{CONFIG}/kitty/kitty.conf"

NIRI_BATTERY = 'include "battery.kdl"'
NIRI_PERF    = 'include "noctalia.kdl"'
KITTY_BATTERY = "background_opacity 1.0"
KITTY_PERF    = "background_opacity 0.7"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read(path):
    with open(path) as f:
        return f.read()


def write(path, content):
    with open(path, "w") as f:
        f.write(content)


def replace_in_file(path, old, new):
    content = read(path)
    if old not in content:
        print(f"  ✗ {path}: pattern not found")
        return False
    write(path, content.replace(old, new))
    return True


# ---------------------------------------------------------------------------
# State detection
# ---------------------------------------------------------------------------

def niri_is_battery():
    return NIRI_BATTERY in read(NIRI_FILE)


def kitty_is_battery():
    return KITTY_BATTERY in read(KITTY_FILE)


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def set_niri(battery: bool):
    if battery:
        ok = replace_in_file(NIRI_FILE, NIRI_PERF, NIRI_BATTERY)
    else:
        ok = replace_in_file(NIRI_FILE, NIRI_BATTERY, NIRI_PERF)
    if ok:
        print(f"  {'✓' if battery else '✗'} niri → {'battery.kdl' if battery else 'noctalia.kdl'}")


def set_kitty(battery: bool):
    if battery:
        ok = replace_in_file(KITTY_FILE, KITTY_PERF, KITTY_BATTERY)
    else:
        ok = replace_in_file(KITTY_FILE, KITTY_BATTERY, KITTY_PERF)
    if ok:
        print(f"  {'✓' if battery else '✗'} kitty → opacity {'1.0' if battery else '0.7'}")


def show_status():
    nb = niri_is_battery()
    kb = kitty_is_battery()
    print(f"  niri:  {'BATTERY' if nb else 'PERFORMANCE'}")
    print(f"  kitty: {'BATTERY' if kb else 'PERFORMANCE'}")
    if nb and kb:
        print("  → Đang ở chế độ TIẾT KIỆM PIN")
    elif not nb and not kb:
        print("  → Đang ở chế độ HIỆU NĂNG")
    else:
        print("  → Trạng thái KHÔNG ĐỒNG BỘ")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    # Resolve target state from CLI args
    if not args or args[0] == "toggle":
        nb = niri_is_battery()
        kb = kitty_is_battery()
        # toggle: switch to the opposite of whatever niri is on
        target = not nb
    elif args[0] == "on":
        target = True
    elif args[0] == "off":
        target = False
    elif args[0] == "status":
        show_status()
        return
    else:
        print(f"Dùng: {sys.argv[0]} [status|on|off|toggle]")
        sys.exit(1)

    set_niri(target)
    set_kitty(target)


if __name__ == "__main__":
    main()
