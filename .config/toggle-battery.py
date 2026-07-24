#!/usr/bin/env python3
"""Toggle battery-saver mode for Niri & Kitty.

Usage:
    toggle-battery.py          — toggle
    toggle-battery.py status   — show current state
    toggle-battery.py on       — force battery mode
    toggle-battery.py off      — force performance mode
"""

import os, subprocess, sys

CONFIG = os.path.expanduser("~/.config")
NIRI_FILE = f"{CONFIG}/niri/config.kdl"
KITTY_FILE = f"{CONFIG}/kitty/kitty.conf"

NIRI_BATTERY = 'include "battery.kdl"'
NIRI_PERF    = 'include "noctalia.kdl"'
KITTY_BATTERY = "background_opacity 1.0"
KITTY_PERF    = "background_opacity 0.7"


def read(path):
    with open(path) as f:
        return f.read()


def write(path, content):
    with open(path, "w") as f:
        f.write(content)


def replace_in_file(path, old, new):
    content = read(path)
    if old not in content:
        print(f"  ✗ {os.path.basename(path)}: pattern not found — skip")
        return False
    write(path, content.replace(old, new))
    return True


def niri_is_battery():
    return NIRI_BATTERY in read(NIRI_FILE)


def set_niri(battery: bool):
    if battery:
        ok = replace_in_file(NIRI_FILE, NIRI_PERF, NIRI_BATTERY)
    else:
        ok = replace_in_file(NIRI_FILE, NIRI_BATTERY, NIRI_PERF)
    if ok:
        print(f"  {'✓' if battery else '✗'} niri → {'60Hz' if battery else '144Hz'}")


def set_kitty(battery: bool):
    if battery:
        ok = replace_in_file(KITTY_FILE, KITTY_PERF, KITTY_BATTERY)
    else:
        ok = replace_in_file(KITTY_FILE, KITTY_BATTERY, KITTY_PERF)
    if ok:
        print(f"  {'✓' if battery else '✗'} kitty → opacity {'1.0' if battery else '0.7'}")

def show_status():
    nb = niri_is_battery()
    kitty_opacity = next((l.split()[1] for l in read(KITTY_FILE).splitlines() if l.startswith("background_opacity")), "?")
    pp = subprocess.run(["powerprofilesctl", "get"], capture_output=True, text=True).stdout.strip()
    print(f"  niri:          {'60Hz (BATTERY)' if nb else '144Hz'}")
    print(f"  kitty:         opacity {kitty_opacity}")
    print(f"  power profile: {pp}")
    print(f"  → {'TIẾT KIỆM PIN' if nb else 'HIỆU NĂNG'}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not args or args[0] == "toggle":
        target = not niri_is_battery()
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

    if target:
        print("→ TIẾT KIỆM PIN")
    else:
        print("→ HIỆU NĂNG")

    set_niri(target)
    set_kitty(target)

    os.system("niri msg action reload 2>/dev/null")


if __name__ == "__main__":
    main()
