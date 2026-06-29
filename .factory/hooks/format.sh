#!/bin/bash
set -e

# PostToolUse Hook: Formats/lints/type-checks written/edited code automatically.
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

# Skip if file doesn't exist
if [ ! -f "$file_path" ]; then
  exit 0
fi

# --- Backend: Python (Ruff) ---
if [[ "$file_path" == *.py ]]; then
  RUFF_CMD="ruff"
  if [ -f "$DROID_PROJECT_DIR/.venv/bin/ruff" ]; then
    RUFF_CMD="$DROID_PROJECT_DIR/.venv/bin/ruff"
  fi
  if ! command -v "$RUFF_CMD" &> /dev/null; then
    if command -v uv &> /dev/null; then
      RUFF_CMD="uvx ruff"
    fi
  fi
  if command -v $RUFF_CMD &> /dev/null || [[ "$RUFF_CMD" == *"uvx"* ]]; then
    $RUFF_CMD format "$file_path" 2>&1
    echo "✓ Formatted with Ruff: $file_path"
    $RUFF_CMD check --fix "$file_path" 2>&1 || true
    echo "✓ Lint fixes applied with Ruff: $file_path"
  fi
fi

# --- Frontend: TypeScript/Vue (vue-tsc type check) ---
if [[ "$file_path" == *.ts || "$file_path" == *.vue ]]; then
  FRONTEND_DIR="$DROID_PROJECT_DIR/frontend"
  VUE_TSC="$FRONTEND_DIR/node_modules/.bin/vue-tsc"
  if [ -f "$VUE_TSC" ]; then
    echo "🔍 Type-checking frontend..."
    cd "$FRONTEND_DIR" && "$VUE_TSC" --noEmit 2>&1 || true
    echo "✓ Type-check complete for frontend"
  fi
fi

exit 0
