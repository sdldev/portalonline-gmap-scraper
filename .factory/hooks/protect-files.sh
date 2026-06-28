#!/bin/bash

# PreToolUse Hook: Blocks edits to sensitive or auto-generated infrastructure files.
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

# Skip if no file path
if [ -z "$file_path" ]; then
  exit 0
fi

# List of protected patterns
protected_patterns=(
  "\.env"
  "\.env\."
  "uv\.lock"
  "\.git/"
  "\.venv/"
  "__pycache__/"
  "\.pytest_cache/"
)

# Check if file matches any protected pattern
for pattern in "${protected_patterns[@]}"; do
  if echo "$file_path" | grep -qE "$pattern"; then
    echo "❌ Cannot modify protected file: $file_path" >&2
    echo "This file is protected by project policy (e.g. .env, uv.lock, .git, .venv)." >&2
    echo "If you need to modify it, please do so manually outside of Droid." >&2
    exit 2  # Exit code 2 blocks the operation
  fi
done

exit 0
