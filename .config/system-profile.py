#!/usr/bin/env python3
"""Manage power and visual profiles for Niri, Kitty and Noctalia.

Commands:
    system-profile.py status
    system-profile.py power auto|battery|ac|toggle
    system-profile.py glass on|off|toggle
    system-profile.py sync [battery|ac]
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


HOME = Path.home()
CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))
STATE_HOME = Path(os.environ.get("XDG_STATE_HOME", HOME / ".local/state"))

STATE_DIR = STATE_HOME / "system-profile"
STATE_FILE = STATE_DIR / "state.json"
LOCK_FILE = STATE_DIR / "lock"
NIRI_RUNTIME = STATE_DIR / "niri.kdl"
KITTY_RUNTIME = STATE_DIR / "kitty.conf"
NIRI_CONFIG = CONFIG_HOME / "niri/config.kdl"
NOCTALIA_SETTINGS = STATE_HOME / "noctalia/settings.toml"
WAYWALLEN_UNIT = "waywallen.service"
WAYWALLEN_APP = "org.waywallen.waywallen"
WAYWALLEN_DISPLAY_PATTERN = r"(^|/)waywallen-layer-shell( |$)"

DEFAULT_STATE = {
    "power_policy": "auto",
    "active_power": "ac",
    "glass": True,
}


class ProfileError(RuntimeError):
    pass


class CLIParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"sp: error: {message}", file=sys.stderr)
        print("Run 'sp help' for usage.", file=sys.stderr)
        raise SystemExit(2)


HELP_TEXT = """\
Usage:
  sp [status]
  sp power auto|battery|ac|toggle
  sp glass on|off|toggle
  sp sync [battery|ac]
  sp help

Commands:
  status                         Show the current source, profile, visuals,
                                 Kitty opacity, and Waywallen state.
  power auto                     Follow the physical AC/battery source.
  power battery                  Force the battery-saving profile.
  power ac                       Force the AC profile.
  power toggle                   Toggle between forced battery and AC profiles.
  glass on                       Enable blur and transparency on AC.
  glass off                      Disable blur and transparency on AC while
                                 keeping animations, shadows, and Waywallen.
  glass toggle                   Toggle the AC glass preference.
  sync [battery|ac]              Synchronize from Noctalia hooks. With no source,
                                 detect the physical power source.

Automatic behavior:
  Battery                        60 Hz; glass, shadows, Niri/Noctalia animations,
                                 and Waywallen are turned off.
  AC                             144 Hz; full visuals and Waywallen are restored.
  Battery -> AC                  Resets the glass preference to on.

Compatibility:
  effects on|off|toggle          Deprecated alias for glass.

Examples:
  sp                             Show status.
  sp glass toggle               Toggle blur and transparency while on AC.
  sp power battery              Force maximum graphical battery savings.
  sp power auto                 Return control to automatic source detection.

Help:
  sp help, sp -h, sp --help, and help requested after any command all display
  this same page.
"""


def atomic_write(path: Path, content: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    old_mode = path.stat().st_mode & 0o777 if path.exists() else None
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode if mode is not None else (old_mode or 0o644))
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def read_state() -> dict[str, object]:
    state = DEFAULT_STATE.copy()
    if STATE_FILE.exists():
        try:
            loaded = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                state.update(loaded)
        except (OSError, json.JSONDecodeError):
            pass
    if state.get("power_policy") not in {"auto", "battery", "ac"}:
        state["power_policy"] = "auto"
    if state.get("active_power") not in {"battery", "ac"}:
        state["active_power"] = "ac"
    # Migrate state written by the first system-profile.py version.
    if "glass" not in state and "effects" in state:
        state["glass"] = bool(state["effects"])
    state.pop("effects", None)
    state["glass"] = bool(state.get("glass", True))
    return state


def detect_power_source() -> str:
    supplies = Path("/sys/class/power_supply")
    candidates: list[Path] = []
    if supplies.exists():
        for supply in supplies.iterdir():
            try:
                if (supply / "type").read_text().strip() == "Mains":
                    candidates.append(supply)
            except OSError:
                continue
    for supply in sorted(candidates):
        try:
            if (supply / "online").read_text().strip() == "1":
                return "ac"
        except OSError:
            continue
    if candidates:
        return "battery"
    raise ProfileError("No AC power supply found in /sys/class/power_supply")


def render_niri(power: str, glass: bool) -> str:
    refresh = "1920x1080@60.001" if power == "battery" else "1920x1080@144.003"
    battery = power == "battery"
    effective_glass = glass and not battery
    if not battery:
        animation = '''animations {
    on
    slowdown 1.0
    window-open { curve "cubic-bezier" 0.25 0.1 0.25 1.0; }
    config-notification-open-close { curve "cubic-bezier" 0.25 0.1 0.25 1.0; }
    window-close { curve "cubic-bezier" 0.25 0.1 0.25 1.0; }
    window-movement { curve "cubic-bezier" 0.25 0.1 0.25 1.0; }
    window-resize { curve "cubic-bezier" 0.25 0.1 0.25 1.0; }
    workspace-switch { curve "cubic-bezier" 0.25 0.1 0.25 1.0; }
    horizontal-view-movement { curve "cubic-bezier" 0.25 0.1 0.25 1.0; }
    overview-open-close { curve "cubic-bezier" 0.25 0.1 0.25 1.0; }
    screenshot-ui-open { curve "cubic-bezier" 0.25 0.1 0.25 1.0; }
}'''
        shadow_state = "on"
    else:
        animation = "animations {\n    off\n}"
        shadow_state = "off"

    if effective_glass:
        blur_passes = 2
        opacity = "0.82"
        background_effect = '''
    background-effect {
        blur true
        xray false
    }'''
    else:
        blur_passes = 0
        opacity = "1.0"
        background_effect = ""

    return f'''// Generated by ~/.config/system-profile.py. Do not edit.
output "eDP-1" {{
    mode "{refresh}"
}}

layout {{
    shadow {{
        {shadow_state}
        softness 40
        spread 2
        offset x=0 y=6
        color "#00000050"
    }}
}}

{animation}

blur {{
    passes {blur_passes}
    offset 2.0
    noise 0.015
}}

window-rule {{
    geometry-corner-radius 20
    clip-to-geometry true
    draw-border-with-background false
    opacity {opacity}{background_effect}
}}

window-rule {{
    match is-focused=true
    opacity {opacity}{background_effect}
}}

// Kitty controls its own background opacity.
window-rule {{
    match app-id="kitty"
    opacity 1.0
}}
'''


def render_kitty(power: str, glass: bool) -> str:
    opacity = "0.70" if power == "ac" and glass else "1.0"
    return f"# Generated by ~/.config/system-profile.py. Do not edit.\nbackground_opacity {opacity}\n"


def update_noctalia_animation(content: str, enabled: bool) -> str:
    value = "true" if enabled else "false"
    lines = content.splitlines(keepends=True)
    table_re = re.compile(r"^\s*\[([^]]+)]\s*(?:#.*)?$")
    table_start = None
    table_end = len(lines)
    for index, line in enumerate(lines):
        match = table_re.match(line.rstrip("\n"))
        if not match:
            continue
        if match.group(1).strip() == "shell.animation":
            table_start = index
            continue
        if table_start is not None:
            table_end = index
            break

    if table_start is None:
        suffix = "" if not content or content.endswith("\n") else "\n"
        separator = "" if not content else "\n"
        return f"{content}{suffix}{separator}[shell.animation]\nenabled = {value}\n"

    enabled_re = re.compile(r"^(\s*)enabled\s*=.*$")
    for index in range(table_start + 1, table_end):
        match = enabled_re.match(lines[index].rstrip("\n"))
        if match:
            lines[index] = f"{match.group(1)}enabled = {value}\n"
            return "".join(lines)
    lines.insert(table_start + 1, f"enabled = {value}\n")
    return "".join(lines)


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def waywallen_status() -> tuple[bool, bool]:
    daemon = False
    display = False
    if shutil.which("flatpak"):
        result = run(["flatpak", "ps", "--columns=application"])
        daemon = WAYWALLEN_APP in result.stdout.splitlines()
    if shutil.which("pgrep"):
        # Linux truncates the process comm field to 15 bytes, so match argv.
        display = run(["pgrep", "-u", str(os.getuid()), "-f", WAYWALLEN_DISPLAY_PATTERN]).returncode == 0
    return daemon, display


def set_waywallen(enabled: bool) -> list[str]:
    """Apply Waywallen lifecycle and return non-fatal warnings."""
    warnings: list[str] = []
    if not shutil.which("systemctl"):
        return ["systemctl was not found; cannot manage Waywallen"]
    action = "start" if enabled else "stop"
    result = run(["systemctl", "--user", action, WAYWALLEN_UNIT])
    if result.returncode:
        warnings.append((result.stderr or result.stdout).strip() or f"could not {action} {WAYWALLEN_UNIT}")
    if not enabled:
        # Also clean up processes launched by the legacy Niri autostart.
        if shutil.which("flatpak"):
            run(["flatpak", "kill", WAYWALLEN_APP])
        if shutil.which("pkill"):
            run(["pkill", "-u", str(os.getuid()), "-f", WAYWALLEN_DISPLAY_PATTERN])
    daemon, display = waywallen_status()
    if enabled and not (daemon and display):
        warnings.append("Waywallen daemon and display are not both running")
    if not enabled and (daemon or display):
        warnings.append("Waywallen processes remain after stop")
    return warnings


def update_running_kitty(opacity: str) -> list[str]:
    """Apply opacity to every live Kitty instance without blocking profiles."""
    if not shutil.which("kitty"):
        return ["kitty was not found; existing windows were not updated"]
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime:
        return ["XDG_RUNTIME_DIR is not set; only new Kitty windows will use the opacity"]
    warnings: list[str] = []
    for socket in sorted(Path(runtime).glob("kitty-*.sock")):
        result = run([
            "kitty", "@", "--to", f"unix:{socket}",
            "set-background-opacity", "--all", opacity,
        ])
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()
            warnings.append(f"{socket.name}: {detail or 'could not update opacity'}")
    return warnings


def validate_configs() -> None:
    if shutil.which("niri") and NIRI_CONFIG.exists():
        result = run(["niri", "validate", "-c", str(NIRI_CONFIG)])
        if result.returncode:
            raise ProfileError(f"Niri rejected the configuration:\n{result.stderr or result.stdout}")
    if shutil.which("noctalia"):
        result = run(["noctalia", "config", "validate"])
        if result.returncode:
            raise ProfileError(f"Noctalia rejected the configuration:\n{result.stderr or result.stdout}")


def restore(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(path, previous.decode("utf-8"))


def apply_state(state: dict[str, object], *, notify: bool = True) -> None:
    old_state = read_state()
    policy = str(state["power_policy"])
    if policy == "auto":
        active = str(state.get("requested_source") or detect_power_source())
    else:
        active = policy
    if active not in {"battery", "ac"}:
        raise ProfileError(f"Invalid power source: {active}")
    # A real battery -> AC transition restores the full glass appearance.
    if active == "ac" and old_state.get("active_power") == "battery":
        state["glass"] = True
    glass = bool(state["glass"])
    animations = active == "ac"

    targets = (NIRI_RUNTIME, KITTY_RUNTIME, NOCTALIA_SETTINGS)
    previous = {path: path.read_bytes() if path.exists() else None for path in targets}
    noctalia_content = previous[NOCTALIA_SETTINGS].decode("utf-8") if previous[NOCTALIA_SETTINGS] else ""

    try:
        atomic_write(NIRI_RUNTIME, render_niri(active, glass))
        atomic_write(KITTY_RUNTIME, render_kitty(active, glass))
        atomic_write(NOCTALIA_SETTINGS, update_noctalia_animation(noctalia_content, animations))
        validate_configs()
    except Exception:
        for path in targets:
            restore(path, previous[path])
        raise

    state.pop("requested_source", None)
    state["active_power"] = active
    atomic_write(STATE_FILE, json.dumps(state, ensure_ascii=False, indent=2) + "\n")

    run(["niri", "msg", "action", "reload"])
    run(["noctalia", "msg", "config-reload"])
    kitty_opacity = "0.70" if active == "ac" and glass else "1.0"
    kitty_warnings = update_running_kitty(kitty_opacity)
    lifecycle_warnings = set_waywallen(active == "ac")

    changed = old_state.get("active_power") != active or bool(old_state.get("glass")) != glass
    if notify and changed and shutil.which("notify-send"):
        power_label = "Battery · 60 Hz" if active == "battery" else "AC · 144 Hz"
        glass_label = "Glass on" if active == "ac" and glass else "Glass off"
        run(["notify-send", "-r", "4901", "System Profile", f"{power_label} · {glass_label}"])
    for warning in lifecycle_warnings:
        print(f"Waywallen warning: {warning}", file=sys.stderr)
    for warning in kitty_warnings:
        print(f"Kitty warning: {warning}", file=sys.stderr)


def print_status(state: dict[str, object]) -> None:
    try:
        source = detect_power_source()
    except ProfileError:
        source = "unknown"
    policy = str(state["power_policy"])
    active = str(state["active_power"])
    glass = bool(state["glass"])
    effective_glass = active == "ac" and glass
    animations = active == "ac"
    refresh = "60.001 Hz" if active == "battery" else "144.003 Hz"
    print(f"Physical source:  {source}")
    print(f"Power policy:     {policy}")
    print(f"Active profile:   {active} ({refresh})")
    print(f"AC glass setting: {'on' if glass else 'off'}")
    print(f"Effective glass:  {'on' if effective_glass else 'off'}")
    print(f"  Niri:           opacity {'0.82' if effective_glass else '1.0'}, blur {'on' if effective_glass else 'off'}, shadows/animations {'on' if animations else 'off'}")
    print(f"  Kitty:          opacity {'0.70' if effective_glass else '1.0'}")
    print(f"  Noctalia:       animations {'on' if animations else 'off'}")
    daemon, display = waywallen_status()
    print(f"  Waywallen:      daemon {'on' if daemon else 'off'}, display {'on' if display else 'off'}")
    warnings: list[str] = []
    expected = {
        NIRI_RUNTIME: render_niri(active, glass),
        KITTY_RUNTIME: render_kitty(active, glass),
    }
    for path, wanted in expected.items():
        if not path.exists():
            warnings.append(f"missing generated file: {path}")
        elif path.read_text(encoding="utf-8") != wanted:
            warnings.append(f"{path} does not match the saved state")
    if NOCTALIA_SETTINGS.exists():
        value = "true" if animations else "false"
        content = NOCTALIA_SETTINGS.read_text(encoding="utf-8")
        table = re.search(
            r"(?ms)^\s*\[shell\.animation]\s*$\n(.*?)(?=^\s*\[|\Z)", content
        )
        if not table or not re.search(rf"(?m)^\s*enabled\s*=\s*{value}\s*$", table.group(1)):
            warnings.append("Noctalia animation setting does not match the saved state")
    else:
        warnings.append(f"missing Noctalia settings file: {NOCTALIA_SETTINGS}")
    if active == "ac" and not (daemon and display):
        warnings.append("Waywallen should be running on AC")
    if active == "battery" and (daemon or display):
        warnings.append("Waywallen should be stopped on battery")
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    argv = sys.argv[1:]
    if (argv and argv[0] == "help") or any(arg in {"-h", "--help"} for arg in argv):
        print(HELP_TEXT, end="")
        raise SystemExit(0)

    parser = CLIParser(prog="sp", add_help=False)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status", add_help=False)
    power = sub.add_parser("power", add_help=False)
    power.add_argument("mode", choices=("auto", "battery", "ac", "toggle"))
    glass = sub.add_parser("glass", add_help=False)
    glass.add_argument("mode", choices=("on", "off", "toggle"))
    sync = sub.add_parser("sync", add_help=False)
    sync.add_argument("source", nargs="?", choices=("battery", "ac"))
    if argv and argv[0] == "effects":
        argv[0] = "glass"
        print("Note: 'effects' has been renamed to 'glass'", file=sys.stderr)
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_state()
        try:
            if args.command in {None, "status"}:
                print_status(state)
                return 0
            if args.command == "power":
                mode = args.mode
                if mode == "toggle":
                    mode = "battery" if state["active_power"] == "ac" else "ac"
                state["power_policy"] = mode
                apply_state(state)
            elif args.command == "glass":
                if state["active_power"] == "battery":
                    raise ProfileError("The battery profile forces glass off; change it after switching to AC")
                enabled = bool(state["glass"])
                state["glass"] = not enabled if args.mode == "toggle" else args.mode == "on"
                apply_state(state)
            elif args.command == "sync":
                if args.source:
                    state["requested_source"] = args.source
                apply_state(state, notify=args.source is not None)
            print_status(read_state())
            return 0
        except (ProfileError, OSError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
