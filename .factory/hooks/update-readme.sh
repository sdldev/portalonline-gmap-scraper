#!/bin/bash
set -e

# PostToolUse hook to check README sync
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

# Only update on pyproject.toml or README changes
if ! echo "$file_path" | grep -qE '(pyproject\.toml|README\.md)$'; then
  exit 0
fi

# Don't run if README is the file being edited directly
if [ "$file_path" = "README.md" ]; then
  exit 0
fi

echo "📝 Checking README..."

# Update info in README
if [ -f "$DROID_PROJECT_DIR/pyproject.toml" ] && [ -f "$DROID_PROJECT_DIR/README.md" ]; then
  cd "$DROID_PROJECT_DIR"
  # Quick grab of version from pyproject.toml (simple regex)
  version=$(grep -m1 '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
  
  if [ -n "$version" ]; then
    # Check if version in README matches
    if ! grep -q "$version" README.md; then
      echo "⚠️ README version may be out of sync with pyproject.toml" >&2
      echo "Package version is: $version" >&2
      echo "Consider updating README.md or ask me to do it" >&2
    fi
  fi
fi

exit 0
