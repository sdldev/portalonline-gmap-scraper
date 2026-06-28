#!/bin/bash

# PostToolUse Hook: Detects hardcoded secrets or credentials in the output.
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

if [ -z "$file_path" ] || [ ! -f "$file_path" ]; then
  exit 0
fi

# Skip non-text files or git history
if echo "$file_path" | grep -qE '(\.jpg|\.png|\.gif|\.pdf|\.zip|\.tar|\.gz|\.pyc)$' || echo "$file_path" | grep -qE '\.git/'; then
  exit 0
fi

# Use the actual file on disk since this is PostToolUse
temp_file="$file_path"

secret_patterns=(
  "AKIA[0-9A-Z]{16}"  # AWS Access Key
  "AIza[0-9A-Za-z\-_]{35}"  # Google API Key
  "sk-[a-zA-Z0-9]{32,}"  # OpenAI API Key
  "ghp_[a-zA-Z0-9]{36}"  # GitHub PAT
)

found_secrets=0

for pattern in "${secret_patterns[@]}"; do
  if grep -qE "$pattern" "$temp_file"; then
    echo "❌ Potential secret detected matching pattern: $pattern in $file_path" >&2
    found_secrets=1
  fi
done

# Also check for common variable names assigned to a 10+ length string that isn't empty or totally generic
if grep -iE "(password|secret|api_key|token)\s*=\s*['\"][a-zA-Z0-9_\-=\.]{10,}['\"]" "$temp_file" | grep -v "example_"; then
  echo "⚠️ Suspicious credential-like assignment detected" >&2
  echo "Review assignment in: $file_path" >&2
  found_secrets=1
fi

if [ $found_secrets -eq 1 ]; then
  echo "" >&2
  echo "Please use environment variables (loaded via config.py / python-dotenv) instead of hardcoding secrets." >&2
  # Do not block retroactively (PostToolUse can't block anyway, but outputs the error for context/bot fixing)
fi

exit 0
