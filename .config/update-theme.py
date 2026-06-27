#!/usr/bin/env python3
"""Đọc palette.json và cập nhật config của tất cả app."""

import json, os, re

PALETTE = os.path.expanduser("~/.config/palette.json")
CONFIG = os.path.expanduser("~/.config")

with open(PALETTE) as f:
    p = json.load(f)

ok = True

# ── kitty.conf ──────────────────────────────────────────
def update_kitty():
    path = f"{CONFIG}/kitty/kitty.conf"
    keys = {
        "foreground", "background", "cursor",
        "color0","color1","color2","color3","color4","color5","color6","color7",
        "color8","color9","color10","color11","color12","color13","color14","color15",
    }
    palette_map = {
        "foreground": "foreground", "background": "background", "cursor": "cursor",
        "color0": "black", "color1": "red", "color2": "green", "color3": "yellow",
        "color4": "blue", "color5": "magenta", "color6": "cyan", "color7": "white",
        "color8": "bright_black", "color9": "bright_red", "color10": "bright_green",
        "color11": "bright_yellow", "color12": "bright_blue", "color13": "bright_magenta",
        "color14": "bright_cyan", "color15": "bright_white",
    }

    lines = open(path).readlines()
    out = []
    for line in lines:
        m = re.match(r"^(\s*)(\w+)(\s+)(#\w+)", line)
        if m and m.group(2) in keys:
            key = m.group(2)
            palette_key = palette_map[key]
            out.append(f"{m.group(1)}{key}{m.group(3)}{p[palette_key]}\n")
        else:
            out.append(line)
    open(path, "w").writelines(out)
    print("  ✓ kitty.conf")

# ── starship.toml ───────────────────────────────────────
def update_starship():
    path = f"{CONFIG}/starship.toml"
    # directory color = cyan
    old = f'fg:#107a80'
    new = f'fg:{p["cyan"]}'
    text = open(path).read()
    text = text.replace(old, new)
    open(path, "w").write(text)
    print("  ✓ starship.toml")

# ── btop theme ──────────────────────────────────────────
def update_btop():
    path = f"{CONFIG}/btop/themes/catppuccin_latte.theme"
    content = f"""# btop theme - Catppuccin Latte (auto-generated)
# Edit palette.json and run update-theme.py

theme[main_bg]="{p["background"]}"
theme[main_fg]="{p["foreground"]}"
theme[title]="{p["blue"]}"
theme[hi_fg]="{p["cyan"]}"
theme[selected_bg]="#e6e9ef"
theme[selected_fg]="{p["foreground"]}"
theme[inactive_fg]="{p["white"]}"
theme[proc_misc]="{p["black"]}"
theme[cpu_box]="{p["blue"]}"
theme[mem_box]="{p["cyan"]}"
theme[net_box]="{p["magenta"]}"
theme[proc_box]="{p["black"]}"
theme[div_line]="#ccd0da"
theme[temp_start]="{p["green"]}"
theme[temp_mid]="{p["yellow"]}"
theme[temp_end]="{p["red"]}"
theme[cpu_start]="{p["green"]}"
theme[cpu_mid]="{p["yellow"]}"
theme[cpu_end]="{p["red"]}"
theme[free_start]="{p["green"]}"
theme[free_mid]="{p["yellow"]}"
theme[free_end]="{p["red"]}"
theme[cached_start]="{p["green"]}"
theme[cached_mid]="{p["yellow"]}"
theme[cached_end]="{p["red"]}"
theme[available_start]="{p["green"]}"
theme[available_mid]="{p["yellow"]}"
theme[available_end]="{p["red"]}"
theme[used_start]="{p["green"]}"
theme[used_mid]="{p["yellow"]}"
theme[used_end]="{p["red"]}"
theme[download_start]="{p["green"]}"
theme[download_mid]="{p["yellow"]}"
theme[download_end]="{p["red"]}"
theme[upload_start]="{p["green"]}"
theme[upload_mid]="{p["yellow"]}"
theme[upload_end]="{p["red"]}"
"""
    open(path, "w").write(content)
    print("  ✓ btop theme")

# ── yazi theme.toml ─────────────────────────────────────
def update_yazi():
    path = f"{CONFIG}/yazi/theme.toml"
    content = f"""[app]
overall = {{ bg = "{p["background"]}" }}

[mgr]
cwd = {{ fg = "{p["blue"]}", bold = true }}
find_keyword = {{ fg = "{p["foreground"]}", bg = "{p["yellow"]}", bold = true }}
find_position = {{ fg = "{p["black"]}" }}
symlink_target = {{ fg = "{p["cyan"]}" }}
marker_copied = {{ fg = "{p["blue"]}" }}
marker_cut = {{ fg = "{p["red"]}" }}
marker_marked = {{ fg = "{p["magenta"]}" }}
marker_selected = {{ fg = "{p["magenta"]}" }}
count_copied = {{ fg = "{p["blue"]}" }}
count_cut = {{ fg = "{p["red"]}" }}
count_selected = {{ fg = "{p["magenta"]}" }}
border_symbol = "│"
border_style = {{ fg = "#bcc0cc" }}

[indicator]
parent = {{ fg = "{p["background"]}", bg = "#acb0be" }}
current = {{ fg = "{p["background"]}", bg = "{p["blue"]}" }}
preview = {{ fg = "{p["background"]}", bg = "{p["cyan"]}" }}
padding = {{ open = "▐", close = "▌" }}

[tabs]
active = {{ fg = "{p["foreground"]}", bg = "{p["background"]}" }}
inactive = {{ fg = "{p["white"]}", bg = "#ccd0da" }}
sep_inner = {{ open = "[", close = "]" }}
sep_outer = {{ open = "", close = "" }}

[mode]
normal_main = {{ fg = "{p["background"]}", bg = "{p["blue"]}", bold = true }}
normal_alt = {{ fg = "{p["background"]}", bg = "{p["cyan"]}", bold = true }}
select_main = {{ fg = "{p["background"]}", bg = "{p["magenta"]}", bold = true }}
select_alt = {{ fg = "{p["background"]}", bg = "{p["red"]}", bold = true }}
unset_main = {{ fg = "{p["background"]}", bg = "{p["black"]}", bold = true }}
unset_alt = {{ fg = "{p["background"]}", bg = "{p["white"]}", bold = true }}

[status]
overall = {{ fg = "{p["foreground"]}", bg = "#ccd0da" }}
sep_left = {{ open = "", close = "]" }}
sep_right = {{ open = "[", close = "" }}
perm_type = {{ fg = "{p["white"]}" }}
perm_read = {{ fg = "{p["green"]}" }}
perm_write = {{ fg = "{p["red"]}" }}
perm_exec = {{ fg = "{p["blue"]}" }}
perm_sep = {{ fg = "{p["white"]}" }}
progress_label = {{ fg = "{p["foreground"]}", bold = true }}
progress_normal = {{ fg = "{p["background"]}", bg = "{p["blue"]}" }}
progress_error = {{ fg = "{p["background"]}", bg = "{p["red"]}" }}

[which]
cols = 2
mask = {{ bg = "#e6e9ef" }}
cand = {{ fg = "{p["blue"]}", bold = true }}
rest = {{ fg = "{p["foreground"]}" }}
desc = {{ fg = "{p["white"]}" }}
separator = " -> "
separator_style = {{ fg = "{p["white"]}" }}

[confirm]
border = {{ fg = "{p["foreground"]}", bg = "{p["background"]}" }}
title = {{ fg = "{p["foreground"]}", bg = "{p["background"]}", bold = true }}
body = {{ fg = "{p["foreground"]}", bg = "{p["background"]}" }}
list = {{ fg = "{p["foreground"]}", bg = "{p["background"]}" }}
btn_yes = {{ fg = "{p["background"]}", bg = "{p["blue"]}", bold = true }}
btn_no = {{ fg = "{p["foreground"]}", bg = "#ccd0da", bold = true }}
btn_labels = ["Yes", "No"]

[spot]
border = {{ fg = "{p["foreground"]}", bg = "{p["background"]}" }}
title = {{ fg = "{p["foreground"]}", bg = "{p["background"]}", bold = true }}
tbl_col = {{ fg = "{p["foreground"]}", bg = "#ccd0da" }}
tbl_cell = {{ fg = "{p["foreground"]}", bg = "#e6e9ef" }}

[notify]
title_info = {{ fg = "{p["background"]}", bg = "{p["blue"]}", bold = true }}
title_warn = {{ fg = "{p["background"]}", bg = "{p["yellow"]}", bold = true }}
title_error = {{ fg = "{p["background"]}", bg = "{p["red"]}", bold = true }}

[pick]
border = {{ fg = "{p["foreground"]}", bg = "{p["background"]}" }}
active = {{ fg = "{p["foreground"]}", bg = "#e6e9ef" }}
inactive = {{ fg = "{p["white"]}", bg = "{p["background"]}" }}

[input]
border = {{ fg = "{p["blue"]}", bg = "{p["background"]}" }}
title = {{ fg = "{p["foreground"]}", bg = "{p["background"]}", bold = true }}
value = {{ fg = "{p["foreground"]}", bg = "{p["background"]}" }}
selected = {{ fg = "{p["background"]}", bg = "{p["blue"]}" }}

[cmp]
border = {{ fg = "{p["foreground"]}", bg = "{p["background"]}" }}
active = {{ fg = "{p["foreground"]}", bg = "#e6e9ef" }}
inactive = {{ fg = "{p["white"]}", bg = "{p["background"]}" }}
icon_file = "📄"
icon_folder = "📁"
icon_command = "⚡"

[tasks]
border = {{ fg = "{p["foreground"]}", bg = "{p["background"]}" }}
title = {{ fg = "{p["foreground"]}", bg = "{p["background"]}", bold = true }}
hovered = {{ fg = "{p["foreground"]}", bg = "#e6e9ef" }}

[help]
on = {{ fg = "{p["blue"]}", bold = true }}
run = {{ fg = "{p["foreground"]}" }}
desc = {{ fg = "{p["white"]}" }}
hovered = {{ fg = "{p["foreground"]}", bg = "#e6e9ef" }}
footer = {{ fg = "{p["white"]}", bg = "{p["background"]}" }}

[filetype]
rules = [
  {{ mime = "image/*", fg = "{p["magenta"]}" }},
  {{ mime = "{{audio,video}}/*", fg = "{p["red"]}" }},
  {{ mime = "text/*", fg = "{p["foreground"]}" }},
  {{ mime = "application/{{pdf,zip,rar,7z,tar,gzip,bzip2,xz}}", fg = "{p["yellow"]}" }},
  {{ mime = "inode/empty", fg = "{p["cyan"]}" }},
  {{ url = "*/", fg = "{p["blue"]}", bold = true }},
  {{ url = "*", fg = "{p["foreground"]}" }},
]
"""
    open(path, "w").write(content)
    print("  ✓ yazi theme.toml")

# ── opencode theme ──────────────────────────────────────
def update_opencode():
    path = f"{CONFIG}/opencode/themes/catppuccin-latte.json"
    content = f"""{{
  "$schema": "https://opencode.ai/theme.json",
  "theme": {{
    "primary": "{p["blue"]}",
    "secondary": "{p["cyan"]}",
    "accent": "{p["magenta"]}",
    "error": "{p["red"]}",
    "warning": "{p["yellow"]}",
    "success": "{p["green"]}",
    "info": "{p["blue"]}",
    "text": "{p["foreground"]}",
    "textMuted": "{p["white"]}",
    "background": "{p["background"]}",
    "backgroundPanel": "#e6e9ef",
    "backgroundElement": "#ccd0da",
    "border": "#bcc0cc",
    "borderActive": "{p["blue"]}",
    "borderSubtle": "#ccd0da",
    "diffAdded": "{p["green"]}",
    "diffRemoved": "{p["red"]}",
    "diffContext": "{p["white"]}",
    "diffHunkHeader": "{p["white"]}",
    "diffHighlightAdded": "{p["green"]}",
    "diffHighlightRemoved": "{p["red"]}",
    "diffAddedBg": "#e6e9ef",
    "diffRemovedBg": "#e6e9ef",
    "diffContextBg": "#e6e9ef",
    "diffLineNumber": "{p["white"]}",
    "diffAddedLineNumberBg": "#e6e9ef",
    "diffRemovedLineNumberBg": "#e6e9ef",
    "markdownText": "{p["foreground"]}",
    "markdownHeading": "{p["blue"]}",
    "markdownLink": "{p["cyan"]}",
    "markdownLinkText": "{p["magenta"]}",
    "markdownCode": "{p["red"]}",
    "markdownBlockQuote": "{p["white"]}",
    "markdownEmph": "{p["yellow"]}",
    "markdownStrong": "#e64553",
    "markdownHorizontalRule": "#bcc0cc",
    "markdownListItem": "{p["blue"]}",
    "markdownListEnumeration": "{p["magenta"]}",
    "markdownImage": "{p["cyan"]}",
    "markdownImageText": "{p["magenta"]}",
    "markdownCodeBlock": "{p["black"]}",
    "syntaxComment": "{p["white"]}",
    "syntaxKeyword": "{p["blue"]}",
    "syntaxFunction": "{p["cyan"]}",
    "syntaxVariable": "{p["magenta"]}",
    "syntaxString": "{p["green"]}",
    "syntaxNumber": "{p["magenta"]}",
    "syntaxType": "{p["cyan"]}",
    "syntaxOperator": "{p["blue"]}",
    "syntaxPunctuation": "{p["black"]}"
  }}
}}
"""
    open(path, "w").write(content)
    print("  ✓ opencode theme")


# ── vesktop ──────────────────────────────────────────────
def _vesktop_css(palette):
    """Generate CSS with !important on every variable to force override."""
    template = f"""
:root,
.theme-light,
.theme-dark {{
  --background-primary: {p["background"]};
  --background-secondary: #e6e9ef;
  --background-tertiary: #ccd0da;
  --background-accent: {p["blue"]};
  --background-floating: #e6e9ef;
  --background-nested-floating: #e6e9ef;
  --background-modifier-hover: rgba(0, 0, 0, 0.05);
  --background-modifier-active: rgba(0, 0, 0, 0.08);
  --background-modifier-selected: rgba(0, 0, 0, 0.10);
  --background-modifier-accent: rgba(0, 0, 0, 0.06);
  --background-mentioned: rgba(26, 84, 196, 0.08);
  --background-mentioned-hover: rgba(26, 84, 196, 0.12);
  --background-message-hover: rgba(0, 0, 0, 0.03);
  --background-message-automod: rgba(184, 15, 46, 0.08);
  --background-message-automod-hover: rgba(184, 15, 46, 0.12);
  --background-message-highlight: rgba(26, 84, 196, 0.06);
  --background-message-highlight-hover: rgba(26, 84, 196, 0.10);
  --channeltextarea-background: #e6e9ef;
  --input-background: #e6e9ef;
  --text-normal: {p["foreground"]};
  --text-muted: {p["white"]};
  --text-link: {p["cyan"]};
  --text-positive: {p["green"]};
  --text-danger: {p["red"]};
  --text-warning: {p["yellow"]};
  --text-brand: {p["blue"]};
  --header-primary: {p["foreground"]};
  --header-secondary: {p["white"]};
  --channels-default: {p["white"]};
  --channel-icon: {p["white"]};
  --interactive-normal: {p["white"]};
  --interactive-hover: {p["foreground"]};
  --interactive-active: {p["foreground"]};
  --interactive-muted: #bcc0cc;
  --brand-experiment: {p["blue"]};
  --brand-experiment-hover: {p["bright_blue"]};
  --brand-experiment-active: {p["bright_blue"]};
  --brand-experiment-100: #dce0f5;
  --brand-experiment-200: #bcc4ea;
  --brand-experiment-300: {p["blue"]};
  --brand-experiment-400: {p["blue"]};
  --brand-experiment-500: {p["blue"]};
  --brand-experiment-560: {p["blue"]};
  --brand-experiment-600: {p["bright_blue"]};
  --button-danger-background: {p["red"]};
  --button-danger-background-hover: {p["bright_red"]};
  --button-danger-background-active: {p["bright_red"]};
  --button-positive-background: {p["green"]};
  --button-positive-background-hover: #3a9e2a;
  --button-positive-background-active: #3a9e2a;
  --button-outline-danger-border: {p["red"]};
  --button-outline-danger-background: transparent;
  --button-outline-danger-text: {p["red"]};
  --button-secondary-background: #ccd0da;
  --button-secondary-background-hover: #bcc0cc;
  --button-secondary-background-active: #acb0be;
  --scrollbar-thin-thumb: #bcc0cc;
  --scrollbar-thin-track: transparent;
  --scrollbar-auto-thumb: #bcc0cc;
  --scrollbar-auto-track: #e6e9ef;
  --scrollbar-auto-scrollbar-color-thumb: #bcc0cc;
  --scrollbar-auto-scrollbar-color-track: #e6e9ef;
  --deprecated-card-bg: #e6e9ef;
  --deprecated-card-editable-bg: #e6e9ef;
  --deprecated-text-input-bg: #e6e9ef;
  --deprecated-text-input-border: #ccd0da;
  --deprecated-text-input-border-hover: #bcc0dc;
  --deprecated-text-input-border-disabled: #e6e9ef;
  --info-warning-foreground: {p["yellow"]};
  --info-warning-background: rgba(196, 122, 20, 0.08);
  --info-danger-foreground: {p["red"]};
  --info-danger-background: rgba(184, 15, 46, 0.08);
  --info-positive-foreground: {p["green"]};
  --info-positive-background: rgba(46, 128, 30, 0.08);
  --info-help-foreground: {p["blue"]};
  --info-help-background: rgba(26, 84, 196, 0.08);
  --status-green: {p["green"]};
  --status-yellow: {p["yellow"]};
  --status-red: {p["red"]};
  --status-grey: {p["white"]};
}}

/* Hide Vesktop frameless title bar */
[class*="typeWindowsAfterFrame"],
[class*="winButton"] {{
    display: none !important;
}}
[class*="withFrame"] {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
"""
    lines = template.split("\n")
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("--") and "!important" not in stripped:
            line = line.replace(";", " !important;")
        out.append(line)
    return "\n".join(out)


def update_vesktop():
    css = _vesktop_css(p)
    header = """/**
 * @name Catppuccin Latte
 * @author palette.json
 * @description Auto-generated from ~/.config/palette.json. Run update-theme.py to regenerate.
 * @version 1.0.0
 */\n"""
    body = header + css

    theme_path = os.path.expanduser(
        "~/.var/app/dev.vencord.Vesktop/config/vesktop/themes/catppuccin-latte.theme.css"
    )
    open(theme_path, "w").write(body)
    print("  ✓ vesktop theme")

    qcss_path = os.path.expanduser(
        "~/.var/app/dev.vencord.Vesktop/config/vesktop/settings/quickCss.css"
    )
    open(qcss_path, "w").write(body)
    print("  ✓ vesktop quickCss.css")


# ── Run ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("Cập nhật theme từ palette.json...")
    for fn in [update_kitty, update_starship, update_btop, update_yazi, update_opencode, update_vesktop]:
        try:
            fn()
        except Exception as e:
            print(f"  ✗ {fn.__name__}: {e}")
            ok = False
    print("Hoàn tất!" if ok else "Có lỗi xảy ra!")
