#!/bin/bash
set -e

# PostToolUse Hook: Runs tests related to the edited file.
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

# Skip if file doesn't exist
if [ ! -f "$file_path" ]; then
  exit 0
fi

# --- Backend: Python (pytest) ---
if [[ "$file_path" == *.py ]]; then
  echo "🧪 Running Python tests..."
  if [ -f "$DROID_PROJECT_DIR/.venv/bin/pytest" ]; then
    "$DROID_PROJECT_DIR/.venv/bin/pytest" tests/ -v --maxfail=1 2>&1 || true
  else
    if command -v uv &> /dev/null; then
      uv run pytest tests/ -v --maxfail=1 2>&1 || true
    else
      pytest tests/ -v --maxfail=1 2>&1 || true
    fi
  fi
fi

# --- Frontend: TypeScript/Vue (suggest Playwright e2e test manually) ---
if [[ "$file_path" == *.ts || "$file_path" == *.vue ]]; then
  FRONTEND_DIR="$DROID_PROJECT_DIR/frontend"
  PLAYWRIGHT="$FRONTEND_DIR/node_modules/.bin/playwright"
  if [ -f "$PLAYWRIGHT" ]; then
    # Playwright e2e tests are heavy (browser + backend server).
    # Only run in CI or when explicitly requested, not on every edit.
    if [ -n "${CI:-}" ]; then
      echo "🧪 Running Playwright e2e tests (CI mode)..."
      cd "$FRONTEND_DIR" && npx playwright test 2>&1 || true
      echo "✓ Playwright e2e complete"
    else
      echo "💡 Frontend changed. Run e2e tests manually: cd frontend && npx playwright test"
    fi
  fi
fi

exit 0
