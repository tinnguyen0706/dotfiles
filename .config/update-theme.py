#!/usr/bin/env python3
"""Sinh palette M3 Tonal Spot có tương phản cao và áp dụng cho các ứng dụng."""

from __future__ import annotations

import argparse
import colorsys
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

CONFIG = Path.home() / ".config"
PALETTE = CONFIG / "palette.json"
SCHEME = "m3-tonal-spot"
MODE = "light"
MIN_TEXT = 7.0
MIN_FOREGROUND = 7.0
KITTY_OPACITY = 0.70
HARMONIZE_AMOUNT = 0.15

ANSI_ANCHORS = {
    "red": "#b80f2e", "green": "#2e801e", "yellow": "#c47a14",
    "blue": "#1a54c4", "magenta": "#a73b88", "cyan": "#107a80",
    "bright_red": "#c93045", "bright_green": "#2e801e",
    "bright_yellow": "#c47a14", "bright_blue": "#175fa8",
    "bright_magenta": "#a73b88", "bright_cyan": "#107a80",
}
REQUIRED_M3 = {
    "source_color", "error", "on_error",
    "primary", "on_primary", "secondary", "on_secondary", "tertiary",
    "on_tertiary", "surface", "on_surface", "surface_container_low",
    "surface_container_high", "on_surface_variant", "outline",
    "outline_variant", "surface_container_highest",
}

ANSI_FAMILIES = {
    "red": (340, 20), "green": (80, 155), "yellow": (25, 75),
    "blue": (195, 260), "magenta": (285, 340), "cyan": (155, 195),
}


def rgb(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError(f"Màu không hợp lệ: {value!r}")
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def hex_color(value: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(x))):02x}" for x in value)


def luminance(value: str) -> float:
    channels = []
    for c in rgb(value):
        v = c / 255
        channels.append(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4)
    return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + .05) / (lo + .05)


def mix(a: str, b: str, amount: float) -> str:
    ar, br = rgb(a), rgb(b)
    return hex_color(tuple(x + (y - x) * amount for x, y in zip(ar, br)))


def composite(fg: str, bg: str, alpha: float) -> str:
    return mix(bg, fg, alpha)


def readable(anchor: str, foreground: str, backgrounds: list[str], threshold: float = MIN_TEXT) -> str:
    """Trộn ít nhất về foreground bằng tìm kiếm nhị phân trong sRGB."""
    if min(contrast(anchor, bg) for bg in backgrounds) >= threshold:
        return anchor.lower()
    if min(contrast(foreground, bg) for bg in backgrounds) < threshold:
        raise ValueError(f"Màu đích không thể đạt ngưỡng {threshold}:1 trên mọi nền")
    low, high = 0.0, 1.0
    for _ in range(24):
        mid = (low + high) / 2
        if min(contrast(mix(anchor, foreground, mid), bg) for bg in backgrounds) >= threshold:
            high = mid
        else:
            low = mid
    return mix(anchor, foreground, high)


def best_text(background: str, preferred: str) -> str:
    candidates = (preferred, "#000000", "#ffffff")
    return max(candidates, key=lambda c: contrast(c, background))


def hue(value: str) -> float:
    r, g, b = (channel / 255 for channel in rgb(value))
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


def in_hue_family(value: str, family: str) -> bool:
    low, high = ANSI_FAMILIES[family]
    angle = hue(value)
    return angle >= low or angle <= high if low > high else low <= angle <= high


def harmonized_anchor(name: str, anchor: str, source: str) -> str:
    """Nhuộm ANSI theo source_color nhưng không để màu rời họ ngữ nghĩa."""
    family = name.removeprefix("bright_")
    amount = HARMONIZE_AMOUNT
    while amount > 0.001:
        candidate = mix(anchor, source, amount)
        if in_hue_family(candidate, family):
            return candidate
        amount /= 2
    return anchor.lower()


def noctalia_tokens(wallpaper: Path) -> dict[str, str]:
    if not wallpaper.is_file():
        raise ValueError(f"Không tìm thấy wallpaper: {wallpaper}")
    result = subprocess.run(
        ["noctalia", "theme", str(wallpaper), "--scheme", SCHEME, "--light"],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Noctalia không sinh được palette")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Noctalia trả về JSON không hợp lệ") from exc
    missing = REQUIRED_M3 - data.keys()
    if missing:
        raise ValueError("Noctalia thiếu token: " + ", ".join(sorted(missing)))
    return data


def build_palette(tokens: dict[str, str], wallpaper: Path) -> dict[str, str]:
    surface = tokens["surface"]
    surfaces = [surface, tokens["surface_container_low"], tokens["surface_container_high"]]
    transparent = [composite(surface, "#000000", KITTY_OPACITY),
                   composite(surface, "#ffffff", KITTY_OPACITY)]
    text_backgrounds = surfaces + transparent
    foreground = readable(tokens["on_surface"], "#000000", text_backgrounds, MIN_FOREGROUND)
    p: dict[str, str] = {
        "source": str(wallpaper.resolve()), "scheme": SCHEME, "mode": MODE,
        "source_color": tokens["source_color"],
        "background": surface, "foreground": foreground, "cursor": foreground,
        "surface_low": tokens["surface_container_low"], "surface": surface,
        "surface_high": tokens["surface_container_high"],
        "muted": readable(tokens["on_surface_variant"], foreground, text_backgrounds),
        "border": tokens["outline"],
        "border_subtle": tokens["outline_variant"],
        "selection": tokens["surface_container_highest"],
        "selection_text": readable(foreground, "#000000", [tokens["surface_container_highest"]]),
    }
    for name in ("primary", "secondary", "tertiary"):
        p[name] = readable(tokens[name], foreground, text_backgrounds)
        p[f"on_{name}"] = best_text(p[name], tokens[f"on_{name}"])
    for name, anchor in ANSI_ANCHORS.items():
        anchor = harmonized_anchor(name, anchor, tokens["source_color"])
        # Darken về đen thay vì foreground để vẫn giữ hue ANSI trên nền light.
        p[name] = readable(anchor, "#000000", text_backgrounds)
    p.update({
        "black": readable("#38384a", "#000000", text_backgrounds),
        "white": readable(p["muted"], "#000000", text_backgrounds),
        "bright_black": readable(p["muted"], "#000000", text_backgrounds),
        "bright_white": readable(mix("#6b6b78", tokens["source_color"], HARMONIZE_AMOUNT),
                                 "#000000", text_backgrounds),
    })
    for name in ("red", "green", "yellow"):
        p[f"on_{name}"] = best_text(p[name], tokens["on_error"])
    validate_palette(p, text_backgrounds)
    return p


def validate_palette(p: dict[str, str], text_backgrounds: list[str] | None = None) -> None:
    surfaces = [p["background"], p["surface_low"], p["surface"], p["surface_high"]]
    if text_backgrounds is None:
        text_backgrounds = surfaces + [
            composite(p["background"], "#000000", KITTY_OPACITY),
            composite(p["background"], "#ffffff", KITTY_OPACITY),
        ]
    text_roles = ["foreground", "muted", "primary", "secondary", "tertiary",
                  "red", "green", "yellow", "blue", "magenta", "cyan"]
    checks = [(f"{name}/text", p[name], bg, MIN_TEXT)
              for name in text_roles for bg in text_backgrounds]
    checks += [(name, p[f"on_{name}"], p[name], MIN_TEXT)
               for name in ("primary", "secondary", "tertiary")]
    checks += [(f"on_{name}", p[f"on_{name}"], p[name], MIN_TEXT)
               for name in ("red", "green", "yellow")]
    checks.append(("selection", p["selection_text"], p["selection"], MIN_TEXT))
    ansi = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
            "bright_black", "bright_red", "bright_green", "bright_yellow", "bright_blue",
            "bright_magenta", "bright_cyan", "bright_white"]
    checks += [(f"{name}/terminal", p[name], bg, MIN_TEXT) for name in ansi for bg in text_backgrounds]
    failed = [(name, contrast(fg, bg), threshold) for name, fg, bg, threshold in checks
              if contrast(fg, bg) + 1e-6 < threshold]
    wrong_hues = [name for name in ANSI_ANCHORS
                  if not in_hue_family(p[name], name.removeprefix("bright_"))]
    if wrong_hues:
        raise ValueError("ANSI rời họ màu: " + ", ".join(wrong_hues))
    if failed:
        detail = "; ".join(f"{n}={ratio:.2f} < {limit}" for n, ratio, limit in failed[:8])
        raise ValueError("Kiểm tra tương phản thất bại: " + detail)


def report(p: dict[str, str]) -> None:
    backgrounds = [p["surface_low"], p["surface"], p["surface_high"],
                   composite(p["background"], "#000000", KITTY_OPACITY),
                   composite(p["background"], "#ffffff", KITTY_OPACITY)]
    print(f"Nguồn: {p.get('source', 'palette.json')} | {p.get('scheme', SCHEME)} | {p.get('mode', MODE)}")
    for name in ("foreground", "muted", "red", "green", "yellow", "blue", "magenta", "cyan"):
        ratios = [contrast(p[name], bg) for bg in backgrounds]
        print(f"  {name:15} {p[name]}  min={min(ratios):.2f}:1")
    for name in ("primary", "secondary", "tertiary"):
        print(f"  on_{name:12} / {name}: {contrast(p['on_' + name], p[name]):.2f}:1")
    print(f"  ✓ Tất cả role chữ đạt ≥ {MIN_TEXT:.1f}:1 (gồm Kitty opacity {KITTY_OPACITY:.2f})")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    except Exception:
        try: os.unlink(temp)
        except FileNotFoundError: pass
        raise


def replace_setting(path: Path, key: str, value: str) -> None:
    text = path.read_text()
    pattern = rf"(?m)^(\s*{re.escape(key)}\s*=\s*)[^#\n]+"
    if not re.search(pattern, text):
        raise ValueError(f"Không tìm thấy trường {key} trong {path}")
    atomic_write(path, re.sub(pattern, rf'\g<1>"{value}"', text, count=1))


def update_kitty(p: dict[str, str]) -> None:
    path = CONFIG / "kitty/kitty.conf"
    mapping = {"foreground": "foreground", "background": "background", "cursor": "cursor"}
    for i, key in enumerate(("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
                             "bright_black", "bright_red", "bright_green", "bright_yellow", "bright_blue",
                             "bright_magenta", "bright_cyan", "bright_white")):
        mapping[f"color{i}"] = key
    lines = []
    opacity_found = False
    for line in path.read_text().splitlines(keepends=True):
        opacity = re.match(r"^(\s*)background_opacity(\s+).*$", line)
        if opacity:
            line = f"{opacity.group(1)}background_opacity{opacity.group(2)}{KITTY_OPACITY:.2f}\n"
            opacity_found = True
        m = re.match(r"^(\s*)(\w+)(\s+)#[0-9a-fA-F]{6}", line)
        if m and m.group(2) in mapping:
            line = f"{m.group(1)}{m.group(2)}{m.group(3)}{p[mapping[m.group(2)]]}\n"
        lines.append(line)
    if not opacity_found:
        raise ValueError("Không tìm thấy background_opacity trong kitty.conf")
    atomic_write(path, "".join(lines))
    reload_result = subprocess.run(
        ["pkill", "-SIGUSR1", "-x", "kitty"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    if reload_result.returncode not in (0, 1):
        raise RuntimeError("Không thể reload Kitty bằng SIGUSR1")


def update_starship(p: dict[str, str]) -> None:
    path = CONFIG / "starship.toml"
    text = path.read_text()
    section = re.search(r"(?ms)^\[directory\]\n(.*?)(?=^\[|\Z)", text)
    if not section:
        raise ValueError("Thiếu [directory] trong starship.toml")
    directory_color = r"(?m)^(format\s*=.*?fg:)#[0-9a-fA-F]{6}"
    if not re.search(directory_color, section.group(1)):
        raise ValueError("Thiếu màu fg trong [directory].format")
    body = re.sub(directory_color, rf"\g<1>{p['primary']}", section.group(1), count=1)
    text = text[:section.start(1)] + body + text[section.end(1):]
    def recolor_section(source: str, name: str, rules: list[tuple[str, str]]) -> str:
        match = re.search(rf"(?ms)^\[{re.escape(name)}\]\n(.*?)(?=^\[|\Z)", source)
        if not match:
            raise ValueError(f"Thiếu [{name}] trong starship.toml")
        section_body = match.group(1)
        for line_pattern, color in rules:
            section_body = re.sub(
                rf"(?m)^({line_pattern}.*?)(?:#[0-9a-fA-F]{{6}})",
                rf"\g<1>{color}", section_body,
            )
        return source[:match.start(1)] + section_body + source[match.end(1):]

    text = recolor_section(text, "git_branch", [(r"format\s*=", p["muted"])])
    text = recolor_section(text, "git_status", [
        (r"format\s*=", p["primary"]), (r"style\s*=", p["surface_high"]),
    ])
    text = recolor_section(text, "time", [(r"format\s*=", p["muted"])])
    text = "\n".join(
        line if line.lstrip().startswith("#") else re.sub(r"\bdimmed\s*", "", line)
        for line in text.split("\n")
    )
    atomic_write(path, text)


def update_zsh(p: dict[str, str]) -> None:
    path = Path.home() / ".zshrc"
    text = path.read_text()
    line = f"ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg={p['muted']}'"
    pattern = r"(?m)^ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE=.*$"
    text = re.sub(pattern, line, text) if re.search(pattern, text) else text.rstrip() + "\n\n" + line + "\n"
    atomic_write(path, text)


def update_btop(p: dict[str, str]) -> None:
    fields = {
        "main_bg": "background", "main_fg": "foreground", "title": "primary", "hi_fg": "secondary",
        "selected_bg": "selection", "selected_fg": "selection_text", "inactive_fg": "muted",
        "proc_misc": "muted", "cpu_box": "primary", "mem_box": "secondary", "net_box": "tertiary",
        "proc_box": "border", "div_line": "border_subtle", "temp_start": "green",
        "temp_mid": "yellow", "temp_end": "red", "cpu_start": "green", "cpu_mid": "yellow",
        "cpu_end": "red", "free_start": "green", "free_mid": "yellow", "free_end": "red",
        "cached_start": "green", "cached_mid": "yellow", "cached_end": "red",
        "available_start": "green", "available_mid": "yellow", "available_end": "red",
        "used_start": "green", "used_mid": "yellow", "used_end": "red",
        "download_start": "green", "download_mid": "yellow", "download_end": "red",
        "upload_start": "green", "upload_mid": "yellow", "upload_end": "red",
    }
    body = "# btop theme - auto-generated from palette.json\n" + "\n".join(
        f'theme[{field}]="{p[key]}"' for field, key in fields.items()) + "\n"
    atomic_write(CONFIG / "btop/themes/catppuccin_latte.theme", body)


def update_yazi(p: dict[str, str]) -> None:
    body = f'''# Auto-generated from palette.json
[app]
overall = {{ bg = "{p['background']}" }}
[mgr]
cwd = {{ fg = "{p['primary']}", bold = true }}
find_keyword = {{ fg = "{p['selection_text']}", bg = "{p['selection']}", bold = true }}
border_style = {{ fg = "{p['border']}" }}
[indicator]
parent = {{ fg = "{p['on_secondary']}", bg = "{p['secondary']}" }}
current = {{ fg = "{p['on_primary']}", bg = "{p['primary']}" }}
preview = {{ fg = "{p['on_tertiary']}", bg = "{p['tertiary']}" }}
[tabs]
active = {{ fg = "{p['foreground']}", bg = "{p['surface_low']}" }}
inactive = {{ fg = "{p['muted']}", bg = "{p['surface_high']}" }}
[mode]
normal_main = {{ fg = "{p['on_primary']}", bg = "{p['primary']}", bold = true }}
select_main = {{ fg = "{p['on_tertiary']}", bg = "{p['tertiary']}", bold = true }}
unset_main = {{ fg = "{p['on_secondary']}", bg = "{p['secondary']}", bold = true }}
[status]
overall = {{ fg = "{p['foreground']}", bg = "{p['surface_high']}" }}
perm_read = {{ fg = "{p['green']}" }}
perm_write = {{ fg = "{p['red']}" }}
perm_exec = {{ fg = "{p['blue']}" }}
[which]
mask = {{ bg = "{p['surface_low']}" }}
cand = {{ fg = "{p['primary']}", bold = true }}
rest = {{ fg = "{p['foreground']}" }}
desc = {{ fg = "{p['muted']}" }}
[confirm]
border = {{ fg = "{p['border']}", bg = "{p['surface']}" }}
title = {{ fg = "{p['foreground']}", bg = "{p['surface']}", bold = true }}
body = {{ fg = "{p['foreground']}", bg = "{p['surface']}" }}
btn_yes = {{ fg = "{p['on_primary']}", bg = "{p['primary']}", bold = true }}
btn_no = {{ fg = "{p['foreground']}", bg = "{p['surface_high']}" }}
[notify]
title_info = {{ fg = "{p['on_primary']}", bg = "{p['primary']}" }}
title_warn = {{ fg = "{p['on_yellow']}", bg = "{p['yellow']}" }}
title_error = {{ fg = "{p['on_red']}", bg = "{p['red']}" }}
[input]
border = {{ fg = "{p['primary']}", bg = "{p['surface']}" }}
value = {{ fg = "{p['foreground']}", bg = "{p['surface']}" }}
selected = {{ fg = "{p['selection_text']}", bg = "{p['selection']}" }}
[help]
on = {{ fg = "{p['primary']}", bold = true }}
run = {{ fg = "{p['foreground']}" }}
desc = {{ fg = "{p['muted']}" }}
'''
    atomic_write(CONFIG / "yazi/theme.toml", body)


def update_opencode(p: dict[str, str]) -> None:
    theme = {
        "$schema": "https://opencode.ai/theme.json",
        "theme": {
            "primary": p["primary"], "secondary": p["secondary"], "accent": p["tertiary"],
            "error": p["red"], "warning": p["yellow"], "success": p["green"], "info": p["blue"],
            "text": p["foreground"], "textMuted": p["muted"], "background": p["background"],
            "backgroundPanel": p["surface_low"], "backgroundElement": p["surface_high"],
            "border": p["border"], "borderActive": p["primary"], "borderSubtle": p["border_subtle"],
            "diffAdded": p["green"], "diffRemoved": p["red"], "diffContext": p["muted"],
            "markdownText": p["foreground"], "markdownHeading": p["primary"],
            "markdownLink": p["secondary"], "markdownCode": p["red"], "syntaxComment": p["muted"],
            "syntaxKeyword": p["primary"], "syntaxFunction": p["secondary"],
            "syntaxVariable": p["tertiary"], "syntaxString": p["green"], "syntaxNumber": p["magenta"],
        },
    }
    atomic_write(CONFIG / "opencode/themes/catppuccin-latte.json", json.dumps(theme, indent=2) + "\n")


def update_vesktop(p: dict[str, str]) -> None:
    variables = {
        "background-primary": "background", "background-secondary": "surface_low",
        "background-tertiary": "surface_high", "background-floating": "surface_low",
        "channeltextarea-background": "surface_low", "input-background": "surface_low",
        "text-normal": "foreground", "text-muted": "muted", "text-link": "primary",
        "text-positive": "green", "text-danger": "red", "text-warning": "yellow",
        "header-primary": "foreground", "header-secondary": "muted", "channels-default": "muted",
        "interactive-normal": "muted", "interactive-hover": "foreground", "interactive-active": "foreground",
        "interactive-muted": "muted", "brand-experiment": "primary",
        "button-danger-background": "red", "button-positive-background": "green",
        "button-danger-text": "on_red", "button-positive-text": "on_green",
        "scrollbar-thin-thumb": "border", "scrollbar-auto-thumb": "border",
        "scrollbar-auto-track": "surface_low", "status-green": "green", "status-yellow": "yellow",
        "status-red": "red", "status-grey": "muted",
    }
    css = "/** Auto-generated from ~/.config/palette.json */\n:root,.theme-light,.theme-dark {\n"
    css += "\n".join(f"  --{name}: {p[key]} !important;" for name, key in variables.items())
    css += "\n}\n[class*=\"typeWindowsAfterFrame\"],[class*=\"winButton\"] { display:none !important; }\n"
    base = Path.home() / ".var/app/dev.vencord.Vesktop/config/vesktop"
    atomic_write(base / "themes/catppuccin-latte.theme.css", css)
    atomic_write(base / "settings/quickCss.css", css)


def update_neovim(_: dict[str, str]) -> None:
    subprocess.run(["pkill", "-SIGUSR1", "nvim"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def apply_apps(p: dict[str, str]) -> None:
    for name, fn in (("Kitty", update_kitty), ("Starship", update_starship), ("Zsh", update_zsh),
                     ("btop", update_btop), ("Yazi", update_yazi), ("OpenCode", update_opencode),
                     ("Vesktop", update_vesktop), ("Neovim", update_neovim)):
        fn(p)
        print(f"  ✓ {name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wallpaper", type=Path, help="Ảnh dùng để sinh M3 Tonal Spot")
    parser.add_argument("--check", action="store_true", help="Chỉ kiểm tra, không ghi file")
    args = parser.parse_args()
    if args.check and not args.wallpaper:
        parser.error("--check cần --wallpaper PATH")
    return args


def main() -> int:
    args = parse_args()
    try:
        if args.wallpaper:
            p = build_palette(noctalia_tokens(args.wallpaper), args.wallpaper)
            report(p)
            if args.check:
                return 0
            atomic_write(PALETTE, json.dumps(p, indent=2, ensure_ascii=False) + "\n")
            print("  ✓ palette.json (ghi nguyên tử)")
        else:
            p = json.loads(PALETTE.read_text())
            validate_palette(p)
        apply_apps(p)
        print("Hoàn tất!")
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
