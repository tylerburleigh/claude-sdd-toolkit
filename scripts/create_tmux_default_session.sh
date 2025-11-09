#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SESSION_NAME="claude-dev"
WINDOW_ONE_NAME="toolkit"
WINDOW_ONE_PATH="$HOME/Documents/claude-sdd-toolkit"
WINDOW_TWO_NAME="chorus"
WINDOW_TWO_PATH="$HOME/Documents/claude-model-chorus"

"$SCRIPT_DIR/create_tmux_session.sh" \
  --session "$SESSION_NAME" \
  --window "${WINDOW_ONE_NAME}:${WINDOW_ONE_PATH}" \
  --window "${WINDOW_TWO_NAME}:${WINDOW_TWO_PATH}" \
  "$@"
