#!/usr/bin/env bash

set -euo pipefail

DEFAULT_SESSION_NAME="sdd-toolkit"
DEFAULT_WINDOW_NAME="editor"

print_usage() {
  cat <<'EOF'
Usage: create_tmux_session.sh [options]

Options:
  -s, --session NAME        Name of the tmux session to create (default: sdd-toolkit)
  -w, --window NAME:PATH    Define a window name and working directory (repeatable)
      --attach              Attach to the session after creating it
      --force               Kill any existing session with the same name before creating
  -h, --help                Show this help message and exit

Examples:
  create_tmux_session.sh --session mysession \
    --window editor:$PWD \
    --window logs:/var/log \
    --attach
EOF
}

error() {
  echo "Error: $1" >&2
  exit 1
}

SESSION_NAME="$DEFAULT_SESSION_NAME"
ATTACH=false
FORCE=false
declare -a WINDOWS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--session)
      [[ $# -ge 2 ]] || error "Missing value for $1"
      SESSION_NAME="$2"
      shift 2
      ;;
    -w|--window)
      [[ $# -ge 2 ]] || error "Missing value for $1"
      WINDOWS+=("$2")
      shift 2
      ;;
    --attach)
      ATTACH=true
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    -h|--help)
      print_usage
      exit 0
      ;;
    *)
      error "Unknown option: $1"
      ;;
  esac
done

[[ -n "$SESSION_NAME" ]] || error "Session name cannot be empty"

if [[ ${#WINDOWS[@]} -eq 0 ]]; then
  WINDOWS+=("${DEFAULT_WINDOW_NAME}:$PWD")
fi

if ! command -v tmux >/dev/null 2>&1; then
  error "tmux is not installed or not on PATH"
fi

declare -a WINDOW_NAMES=()
declare -a WINDOW_PATHS=()

for entry in "${WINDOWS[@]}"; do
  if [[ "$entry" != *:* ]]; then
    error "Invalid window format '$entry'. Expected NAME:PATH."
  fi

  window_name="${entry%%:*}"
  window_path="${entry#*:}"

  [[ -n "$window_name" ]] || error "Window name cannot be empty in '$entry'"
  [[ -n "$window_path" ]] || error "Window path cannot be empty in '$entry'"

  if ! resolved_path=$(cd "$window_path" 2>/dev/null && pwd); then
    error "Directory '$window_path' does not exist or is not accessible"
  fi

  WINDOW_NAMES+=("$window_name")
  WINDOW_PATHS+=("$resolved_path")
done

if tmux has-session -t="$SESSION_NAME" 2>/dev/null; then
  if [[ "$FORCE" == true ]]; then
    tmux kill-session -t "$SESSION_NAME"
  else
    error "tmux session '$SESSION_NAME' already exists. Use --force to replace it."
  fi
fi

first_window_name="${WINDOW_NAMES[0]}"
first_window_path="${WINDOW_PATHS[0]}"

tmux new-session -d -s "$SESSION_NAME" -c "$first_window_path" -n "$first_window_name"

for (( idx = 1; idx < ${#WINDOW_NAMES[@]}; idx++ )); do
  tmux new-window -t "${SESSION_NAME}:" -c "${WINDOW_PATHS[$idx]}" -n "${WINDOW_NAMES[$idx]}"
done

tmux select-window -t "${SESSION_NAME}:${first_window_name}"

echo "Created tmux session '$SESSION_NAME' with ${#WINDOW_NAMES[@]} window(s)."

if [[ "$ATTACH" == true ]]; then
  tmux attach-session -t "$SESSION_NAME"
else
  echo "Attach with: tmux attach-session -t $SESSION_NAME"
fi
