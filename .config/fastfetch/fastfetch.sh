#!/bin/bash

quote=$(fortune -s 2>/dev/null || fortune 2>/dev/null || echo "No quote today.")

max_width=42
inner_max=$((max_width - 4))

format_lines() {
  local raw="$1"
  local lines=()
  local author=""

  while IFS= read -r line; do
    if echo "$line" | grep -qP '^\s+--\s'; then
      author="${line#"${line%%[! ]*}"}"
    elif [ -n "$(echo "$line" | sed 's/^[[:space:]]*//')" ]; then
      lines+=("$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')")
    fi
  done <<< "$raw"

  local result=()
  local current=""
  for line in "${lines[@]}"; do
    local words=($line)
    for word in "${words[@]}"; do
      if [ -z "$current" ]; then
        current="$word"
      elif [ $((${#current} + 1 + ${#word})) -le $inner_max ]; then
        current+=" $word"
      else
        result+=("$current")
        current="$word"
      fi
    done
  done
  [ -n "$current" ] && result+=("$current")

  if [ -n "$author" ]; then
    author=$(echo "$author" | sed 's/^[[:space:]]*--[[:space:]]*/-- /')
    result+=("")
    result+=("$author")
  fi

  # Generate quote module lines (one custom module per line)
  local modules=()
  modules+=("{\"type\":\"custom\",\"format\":\"┌$(printf '─%.0s' $(seq 1 $max_width))┐\"}")
  for text in "${result[@]}"; do
    modules+=("{\"type\":\"custom\",\"format\":\"  $text\"}")
  done
  modules+=("{\"type\":\"custom\",\"format\":\"└$(printf '─%.0s' $(seq 1 $max_width))┘\"}")
  modules+=("{\"type\":\"custom\",\"format\":\"\"}")

  printf '%s\n' "${modules[@]}"
}

quote_modules=$(format_lines "$quote")
config_file="/tmp/fastfetch_config_$$.jsonc"

jq --argjson modules "$(echo "$quote_modules" | jq -R -s 'split("\n") | map(select(length > 0) | fromjson)' )" '.modules = $modules + .modules' ~/.config/fastfetch/config.jsonc > "$config_file"

/usr/bin/fastfetch --config "$config_file" "$@"
rm -f "$config_file"