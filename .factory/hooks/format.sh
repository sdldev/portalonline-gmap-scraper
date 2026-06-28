#!/bin/bash
set -e

# PostToolUse Hook: Formats and lints written/edited Python code automatically using Ruff.
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

# Skip if file doesn't exist
if [ ! -f "$file_path" ]; then
  exit 0
fi

# The project uses `uv / ruff`. Use the local venv if available, otherwise just use `ruff` if globally installed.
RUFF_CMD="ruff"
if [ -f "$DROID_PROJECT_DIR/.venv/bin/ruff" ]; then
  RUFF_CMD="$DROID_PROJECT_DIR/.venv/bin/ruff"
fi
if ! command -v "$RUFF_CMD" &> /dev/null; then
  # Fallback to uv tool run if ruff not in path/venv but uv is available
  if command -v uv &> /dev/null; then
    RUFF_CMD="uvx ruff"
  fi
fi

case "$file_path" in
  *.py)
    if command -v $RUFF_CMD &> /dev/null || [[ "$RUFF_CMD" == *"uvx"* ]]; then
      # Format
      $RUFF_CMD format "$file_path" 2>&1
      echo "✓ Formatted with Ruff: $file_path"
      
      # Lint and fix (isort I, UP, etc. as defined in pyproject.toml)
      $RUFF_CMD check --fix "$file_path" 2>&1 || true
      echo "✓ Lint fixes applied with Ruff: $file_path"
    fi
    ;;
esac

exit 0
