# TMUX Session Automation

## Overview
The `scripts/create_tmux_session.sh` helper automates creation of opinionated tmux sessions for development workflows. It accepts window definitions and optional flags to attach immediately or replace an existing session safely.

## Prerequisites
- `tmux` installed and available on `PATH`.
- Directories referenced in window definitions must already exist.
- Make the script executable: `chmod +x scripts/create_tmux_session.sh`.
- (Optional) Add `scripts/` to your `PATH`, e.g. `export PATH="$PATH:/path/to/claude-sdd-toolkit/scripts"`.

## Usage
```
scripts/create_tmux_session.sh \
  --session mysession \
  --window editor:$PWD \
  --window logs:/var/log \
  --attach
```

### Preconfigured Session Shortcut
For a ready-made setup targeting this repository and the companion `claude-model-chorus` project, run:
```
scripts/create_tmux_default_session.sh --attach
```
This wraps the general script with a session named `claude-dev` containing:
- `toolkit` window rooted at `~/Documents/claude-sdd-toolkit`
- `chorus` window rooted at `~/Documents/claude-model-chorus`

### Flags
- `--session` / `-s`: Override the default session name (`sdd-toolkit`).
- `--window` / `-w`: Provide `NAME:PATH` entries for each window. Repeat for multiple windows. If omitted, a single `editor` window opens in the current directory.
- `--attach`: Attach to the newly created session immediately.
- `--force`: Kill an existing session with the same name before recreating it.
- `--help`: Print usage details.

## Manual Verification
1. Run a smoke test: `scripts/create_tmux_session.sh --session demo --window code:$PWD --window logs:/tmp --attach`.
2. Detach (if attached) and confirm the session exists: `tmux list-sessions`.
3. Attach manually: `tmux attach-session -t demo`, verify window names and their working directories (`pwd` in each window).
4. Clean up when finished: `tmux kill-session -t demo`.

## Edge Cases & Future Enhancements
- The script fails fast when `tmux` is missing, a window definition is malformed, a directory does not exist, or the session already exists (unless `--force` is used).
- Relative paths are resolved from the directory where the script is executed.
- Future ideas:
  - Accept configuration files (e.g. JSON/YAML) to describe sessions.
  - Support pane layouts per window.
  - Offer hooks to run setup commands within windows after creation.
