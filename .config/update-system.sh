#!/usr/bin/env bash
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

failures=()

run_update() {
  local label="$1"
  shift

  echo -e "\n${YELLOW}[${label}]${NC}"
  if "$@" 2>&1; then
    echo -e "${GREEN}${label} completed${NC}"
  else
    local status=$?
    failures+=("${label} (exit code ${status})")
    echo -e "${RED}${label} failed; continuing with the next update${NC}"
  fi
}

trap 'exit 130' INT
trap 'exit 143' TERM

echo -e "${CYAN}Starting updates...${NC}"

if sudo -v; then
  :
else
  status=$?
  failures+=("sudo (exit code ${status})")
  echo -e "${RED}Sudo authentication failed; continuing with the remaining updates${NC}"
fi

run_update "paru" paru -Syu
run_update "flatpak" flatpak update
run_update "codex" codex update
run_update "copilot" copilot update
run_update "agy" agy update

if (( ${#failures[@]} > 0 )); then
  echo -e "\n${RED}Updates completed with errors:${NC}"
  printf '  - %s\n' "${failures[@]}"
  exit 1
fi

echo -e "\n${GREEN}All updates completed successfully.${NC}"
