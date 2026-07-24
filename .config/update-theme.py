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
import time

from PIL import Image, ImageOps

CONFIG = Path.home() / ".config"
PALETTE = CONFIG / "palette.json"
SCHEME = "m3-tonal-spot"
MIN_TEXT = 4.5
MIN_TEXT_LIGHT = 7.0
MIN_FOREGROUND = 7.0
KITTY_OPACITY = 0.70
HARMONIZE_AMOUNT = 0.15
MODE_LUMA_THRESHOLD = 0.50
GENERATOR_VERSION = 4
WALLPAPER_ENGINE_STATE = (
    Path.home() / ".config/Linux Wallpaper Engine/active-wallpapers.json"
)
WALLPAPER_ENGINE_PREVIEWS = (
    "preview.png", "preview.jpg", "preview.jpeg", "preview.webp", "preview.gif",
)

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
    "outline_variant", "surface_container_highest", "secondary_container",
    "on_secondary_container",
}

ANSI_FAMILIES = {
    "red": (340, 20), "green": (80, 155), "yellow": (25, 75),
    # Chừa biên cyan/blue cho sai số lượng tử khi màu bị darken gần #000000.
    "blue": (200, 260), "magenta": (285, 340), "cyan": (155, 205),
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


def readable_hue(anchor: str, backgrounds: list[str], lighten: bool,
                 threshold: float = MIN_TEXT) -> str:
    """Đổi lightness tối thiểu nhưng giữ hue/saturation của màu ANSI."""
    if min(contrast(anchor, bg) for bg in backgrounds) >= threshold:
        return anchor.lower()
    r, g, b = (channel / 255 for channel in rgb(anchor))
    h, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    target = 1.0 if lighten else 0.0

    def candidate(amount: float) -> str:
        nr, ng, nb = colorsys.hls_to_rgb(
            h, lightness + (target - lightness) * amount, saturation,
        )
        return hex_color((nr * 255, ng * 255, nb * 255))

    if min(contrast(candidate(1.0), bg) for bg in backgrounds) < threshold:
        raise ValueError(f"Màu ANSI không thể đạt ngưỡng {threshold}:1 trên mọi nền")
    low, high = 0.0, 1.0
    for _ in range(24):
        mid = (low + high) / 2
        if min(contrast(candidate(mid), bg) for bg in backgrounds) >= threshold:
            high = mid
        else:
            low = mid
    return candidate(high)


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


def wallpaper_luma(wallpaper: Path) -> float:
    """Tính perceived sRGB luma trung bình để chọn light/dark theo chính ảnh."""
    with Image.open(wallpaper) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((128, 128), Image.Resampling.LANCZOS)
        pixels = image.get_flattened_data()
        total = sum((.2126 * r + .7152 * g + .0722 * b) / 255 for r, g, b in pixels)
        return total / (image.width * image.height)


def read_json_retry(path: Path, attempts: int = 6, delay: float = 0.10) -> dict:
    """Đọc JSON có retry vì Wallpaper Engine có thể đang thay nội dung file."""
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            data = json.loads(path.read_text())
            if not isinstance(data, dict):
                raise ValueError(f"JSON gốc trong {path} không phải object")
            return data
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(delay)
    raise ValueError(f"Không đọc được JSON {path}: {last_error}")


def resolve_wallpaper_engine(connector: str) -> tuple[Path, dict]:
    state = read_json_retry(WALLPAPER_ENGINE_STATE)
    active = state.get("activeWallpapers")
    if not isinstance(active, dict) or not active:
        raise ValueError("Wallpaper Engine chưa có wallpaper đang hoạt động")

    selected_connector = connector
    selected = active.get(connector)
    if not isinstance(selected, dict) and len(active) == 1:
        selected_connector, selected = next(iter(active.items()))
    if not isinstance(selected, dict):
        available = ", ".join(sorted(active))
        raise ValueError(f"Không có connector {connector}; hiện có: {available}")

    background_id = selected.get("backgroundId")
    if not isinstance(background_id, str) or not background_id:
        raise ValueError(f"Wallpaper Engine thiếu backgroundId cho {selected_connector}")
    project_dir = Path(background_id).expanduser().resolve()
    if not project_dir.is_dir():
        raise ValueError(f"Project Wallpaper Engine không tồn tại: {project_dir}")

    project_file = project_dir / "project.json"
    project = read_json_retry(project_file)
    candidates: list[Path] = []
    configured_preview = project.get("preview")
    if isinstance(configured_preview, str) and configured_preview:
        candidates.append((project_dir / configured_preview).resolve())
    candidates.extend(project_dir / name for name in WALLPAPER_ENGINE_PREVIEWS)

    preview = next(
        (path for path in candidates if path.is_file() and path.is_relative_to(project_dir)),
        None,
    )
    if preview is None:
        raise ValueError(f"Không tìm thấy preview an toàn trong project {project_dir.name}")

    stat = preview.stat()
    metadata = {
        "connector": selected_connector,
        "project_id": project_dir.name,
        "background_id": str(project_dir),
        "title": project.get("title", project_dir.name),
        "preview": str(preview),
        "preview_mtime_ns": stat.st_mtime_ns,
        "preview_size": stat.st_size,
    }
    return preview, metadata


def same_wallpaper_engine_source(metadata: dict) -> bool:
    try:
        palette = json.loads(PALETTE.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return (
        palette.get("generator_version") == GENERATOR_VERSION
        and palette.get("wallpaper_engine") == metadata
    )


def noctalia_variants(wallpaper: Path) -> tuple[dict[str, dict[str, str]], str, float]:
    if not wallpaper.is_file():
        raise ValueError(f"Không tìm thấy wallpaper: {wallpaper}")
    result = subprocess.run(
        ["noctalia", "theme", str(wallpaper), "--scheme", SCHEME, "--both"],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Noctalia không sinh được palette")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Noctalia trả về JSON không hợp lệ") from exc
    luma = wallpaper_luma(wallpaper)
    mode = "dark" if luma < MODE_LUMA_THRESHOLD else "light"
    variants: dict[str, dict[str, str]] = {}
    for variant in ("light", "dark"):
        tokens = data.get(variant)
        if not isinstance(tokens, dict):
            raise ValueError(f"Noctalia thiếu variant {variant}")
        missing = REQUIRED_M3 - tokens.keys()
        if missing:
            raise ValueError(
                f"Noctalia variant {variant} thiếu token: "
                + ", ".join(sorted(missing))
            )
        variants[variant] = tokens
    return variants, mode, luma


def build_palette(tokens: dict[str, str], wallpaper: Path, mode: str, luma: float) -> dict[str, str]:
    # Dùng trực tiếp neutral surface đã được Tonal Spot nhuộm theo wallpaper.
    surface = tokens["surface"]
    surface_low = tokens["surface_container_low"]
    surface_high = tokens["surface_container_high"]
    selection = tokens["secondary_container"]
    surfaces = [surface, surface_low, surface_high]
    transparent = [composite(surface, "#000000", KITTY_OPACITY),
                   composite(surface, "#ffffff", KITTY_OPACITY)]
    text_backgrounds = surfaces + transparent
    text_threshold = MIN_TEXT_LIGHT if mode == "light" else MIN_TEXT
    foreground_target = "#ffffff" if mode == "dark" else "#000000"
    foreground = readable(tokens["on_surface"], foreground_target, surfaces, MIN_FOREGROUND)
    p: dict[str, str | float] = {
        "generator_version": GENERATOR_VERSION,
        "source": str(wallpaper.resolve()), "scheme": SCHEME, "mode": mode,
        "text_contrast_target": text_threshold,
        "wallpaper_luma": round(luma, 4), "mode_luma_threshold": MODE_LUMA_THRESHOLD,
        "source_color": tokens["source_color"],
        "background": surface, "foreground": foreground, "cursor": foreground,
        "surface_low": surface_low, "surface": surface, "surface_high": surface_high,
        "muted": readable(tokens["on_surface_variant"], foreground, text_backgrounds, text_threshold),
        "border": tokens["outline"],
        "border_subtle": tokens["outline_variant"],
        "selection": selection,
        "selection_text": readable(tokens["on_secondary_container"], foreground, [selection]),
        "error": tokens["error"], "on_error": best_text(tokens["error"], tokens["on_error"]),
    }
    for name in ("primary", "secondary", "tertiary"):
        p[name] = readable(tokens[name], foreground, text_backgrounds, text_threshold)
        p[f"on_{name}"] = best_text(p[name], tokens[f"on_{name}"])
    for name, anchor in ANSI_ANCHORS.items():
        anchor = harmonized_anchor(name, anchor, tokens["source_color"])
        p[name] = readable_hue(anchor, text_backgrounds, mode == "dark", text_threshold)
    p.update({
        "black": readable("#38384a", foreground, text_backgrounds, text_threshold),
        "white": readable(p["muted"], foreground, text_backgrounds, text_threshold),
        "bright_black": readable(p["muted"], foreground, text_backgrounds, text_threshold),
        "bright_white": readable(mix("#6b6b78", tokens["source_color"], HARMONIZE_AMOUNT),
                                 foreground, text_backgrounds, text_threshold),
    })
    for name in ("red", "green", "yellow"):
        p[f"on_{name}"] = best_text(p[name], tokens["on_error"])
    validate_palette(p, text_backgrounds)
    return p


def validate_palette(p: dict[str, str], text_backgrounds: list[str] | None = None) -> None:
    if p.get("mode") not in ("light", "dark"):
        raise ValueError("Mode palette phải là light hoặc dark")
    surfaces = [p["background"], p["surface_low"], p["surface"], p["surface_high"]]
    if text_backgrounds is None:
        text_backgrounds = surfaces + [
            composite(p["background"], "#000000", KITTY_OPACITY),
            composite(p["background"], "#ffffff", KITTY_OPACITY),
        ]
    text_roles = ["foreground", "muted", "primary", "secondary", "tertiary",
                  "red", "green", "yellow", "blue", "magenta", "cyan"]
    text_threshold = MIN_TEXT_LIGHT if p["mode"] == "light" else MIN_TEXT
    checks = [(f"{name}/text", p[name], bg, text_threshold)
              for name in text_roles for bg in text_backgrounds]
    checks += [("foreground/surface", p["foreground"], bg, MIN_FOREGROUND)
               for bg in surfaces]
    checks += [(name, p[f"on_{name}"], p[name], MIN_TEXT)
               for name in ("primary", "secondary", "tertiary")]
    checks += [(f"on_{name}", p[f"on_{name}"], p[name], MIN_TEXT)
               for name in ("red", "green", "yellow")]
    checks.append(("selection", p["selection_text"], p["selection"], MIN_TEXT))
    ansi = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
            "bright_black", "bright_red", "bright_green", "bright_yellow", "bright_blue",
            "bright_magenta", "bright_cyan", "bright_white"]
    checks += [(f"{name}/terminal", p[name], bg, text_threshold)
               for name in ansi for bg in text_backgrounds]
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
    print(f"Nguồn: {p.get('source', 'palette.json')} | {p.get('scheme', SCHEME)} | {p.get('mode')}")
    print(f"  wallpaper luma  {p.get('wallpaper_luma', '?')}  (ngưỡng {MODE_LUMA_THRESHOLD:.2f})")
    print(f"  background      {p['background']}  (Tonal Spot surface)")
    for name in ("foreground", "muted", "red", "green", "yellow", "blue", "magenta", "cyan"):
        ratios = [contrast(p[name], bg) for bg in backgrounds]
        print(f"  {name:15} {p[name]}  min={min(ratios):.2f}:1")
    for name in ("primary", "secondary", "tertiary"):
        print(f"  on_{name:12} / {name}: {contrast(p['on_' + name], p[name]):.2f}:1")
    target = MIN_TEXT_LIGHT if p["mode"] == "light" else MIN_TEXT
    print(f"  ✓ Tất cả role chữ đạt ≥ {target:.1f}:1 (gồm Kitty opacity {KITTY_OPACITY:.2f})")


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


def replace_setting(path: Path, section: str, key: str, value: str) -> None:
    text = path.read_text()
    block = re.search(rf"(?ms)^\[{re.escape(section)}\]\n(.*?)(?=^\[|\Z)", text)
    if not block:
        raise ValueError(f"Không tìm thấy section [{section}] trong {path}")
    pattern = rf"(?m)^(\s*{re.escape(key)}\s*=\s*)[^#\n]+"
    if not re.search(pattern, block.group(1)):
        raise ValueError(f"Không tìm thấy trường [{section}].{key} trong {path}")
    body = re.sub(pattern, rf'\g<1>"{value}"', block.group(1), count=1)
    atomic_write(path, text[:block.start(1)] + body + text[block.end(1):])


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

    socket_reloads = 0
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        for socket in Path(runtime_dir).glob("kitty-*.sock"):
            result = subprocess.run(
                ["kitten", "@", "--to", f"unix:{socket}", "load-config"],
                text=True, capture_output=True, check=False,
            )
            if result.returncode == 0:
                socket_reloads += 1

    # Giữ signal làm fallback cho các instance được mở trước khi listen_on được bật.
    reload_result = subprocess.run(
        ["pkill", "-SIGUSR1", "-x", "kitty"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    if socket_reloads:
        print(f"  ↻ Reload {socket_reloads} instance Kitty qua socket")
    elif reload_result.returncode == 1:
        print("  ~ Chưa reload được Kitty; hãy restart Kitty một lần để tạo socket")
    elif reload_result.returncode != 0:
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
overall = {{ bg = "reset" }}
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
            "text": p["foreground"], "textMuted": p["muted"], "background": "none",
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


def selected_terminal_palette(p: dict[str, str]) -> dict[str, str]:
    """Lấy palette động của TUI; palette root luôn là light."""
    terminal = p.get("terminal")
    if terminal is None:
        # Tương thích palette generator v3 trong lần chuyển đổi đầu tiên.
        terminal = p.get("kitty")
    if terminal is None:
        return p
    if not isinstance(terminal, dict) or not isinstance(terminal.get("colors"), dict):
        raise ValueError("palette.json: terminal.colors không hợp lệ")
    result = dict(p)
    result.update(terminal["colors"])
    result["mode"] = terminal.get("mode", "light")
    return result


def apply_apps(p: dict[str, str]) -> None:
    terminal = selected_terminal_palette(p)
    apps = (
        ("Kitty", update_kitty, terminal),
        ("Starship", update_starship, terminal), ("Zsh", update_zsh, terminal),
        ("btop", update_btop, terminal), ("Yazi", update_yazi, terminal),
        ("OpenCode", update_opencode, terminal), ("Vesktop", update_vesktop, p),
        ("Neovim", update_neovim, p),
    )
    for name, fn, palette in apps:
        fn(palette)
        print(f"  ✓ {name}")


def sync_noctalia_mode(mode: str) -> None:
    """Đồng bộ shell Noctalia; không làm hỏng palette khi daemon chưa chạy."""
    result = subprocess.run(
        ["noctalia", "msg", "theme-mode-set", mode],
        text=True, capture_output=True, check=False,
    )
    if result.returncode == 0:
        print(f"  ✓ Noctalia mode → {mode}")
    else:
        detail = (result.stderr or result.stdout).strip().splitlines()
        message = detail[-1] if detail else "Noctalia chưa chạy"
        settings = Path.home() / ".local/state/noctalia/settings.toml"
        try:
            replace_setting(settings, "theme", "mode", mode)
            print(f"  ~ Noctalia IPC: {message}; đã lưu mode={mode} vào settings.toml")
        except (OSError, ValueError) as exc:
            print(f"  ~ Không thể đổi Noctalia mode: {message}; fallback lỗi: {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--wallpaper", type=Path, help="Ảnh dùng để sinh M3 Tonal Spot")
    source.add_argument(
        "--wallpaper-engine", action="store_true",
        help="Lấy preview của project đang chạy trong Linux Wallpaper Engine",
    )
    parser.add_argument(
        "--connector", default="eDP-1",
        help="Connector Wallpaper Engine quyết định palette (mặc định: eDP-1)",
    )
    parser.add_argument("--check", action="store_true", help="Chỉ kiểm tra, không ghi file")
    args = parser.parse_args()
    if args.check and not (args.wallpaper or args.wallpaper_engine):
        parser.error("--check cần --wallpaper PATH hoặc --wallpaper-engine")
    return args


def main() -> int:
    args = parse_args()
    try:
        source_path = args.wallpaper
        engine_metadata = None
        if args.wallpaper_engine:
            source_path, engine_metadata = resolve_wallpaper_engine(args.connector)
            print(
                f"Wallpaper Engine: {engine_metadata['project_id']} — "
                f"{engine_metadata['title']} ({engine_metadata['connector']})"
            )
            print(f"  preview: {source_path}")
            if not args.check and same_wallpaper_engine_source(engine_metadata):
                print("  = Project và preview không đổi; bỏ qua cập nhật palette")
                return 0

        if source_path:
            variants, kitty_mode, luma = noctalia_variants(source_path)
            # Palette chia sẻ và mọi ứng dụng khác luôn dùng light. Chỉ Kitty
            # chọn light/dark theo độ sáng trung bình của wallpaper.
            p = build_palette(variants["light"], source_path, "light", luma)
            kitty_p = build_palette(
                variants[kitty_mode], source_path, kitty_mode, luma,
            )
            p["terminal"] = {
                "mode": kitty_mode,
                "colors": {
                    key: value for key, value in kitty_p.items()
                    if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value)
                },
            }
            if engine_metadata is not None:
                p["wallpaper_engine"] = engine_metadata
            report(p)
            print(
                f"  Terminal         {kitty_mode} "
                f"(chọn theo wallpaper, ngưỡng {MODE_LUMA_THRESHOLD:.2f})"
            )
            if args.check:
                return 0
            atomic_write(PALETTE, json.dumps(p, indent=2, ensure_ascii=False) + "\n")
            print("  ✓ palette.json (ghi nguyên tử)")
        else:
            p = json.loads(PALETTE.read_text())
            validate_palette(p)
            validate_palette(selected_terminal_palette(p))
        apply_apps(p)
        if source_path:
            sync_noctalia_mode("light")
        print("Hoàn tất!")
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
