#!/bin/bash
set -e

# PostToolUse Hook: Runs tests related to the edited file.
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

# Skip if file doesn't exist or isn't Python
if [ ! -f "$file_path" ] || [[ "$file_path" != *.py ]]; then
  exit 0
fi

echo "🧪 Running tests related to: $file_path"

# We run pytest against the tests directory to ensure nothing broke.
# Using --maxfail=1 to fail fast and save CPU/time during rapid edits.
if [ -f "$DROID_PROJECT_DIR/.venv/bin/pytest" ]; then
    "$DROID_PROJECT_DIR/.venv/bin/pytest" tests/ -v --maxfail=1 2>&1 || true
else
    # Fallback to system pytest or uv run
    if command -v uv &> /dev/null; then
        uv run pytest tests/ -v --maxfail=1 2>&1 || true
    else
        pytest tests/ -v --maxfail=1 2>&1 || true
    fi
fi

exit 0
