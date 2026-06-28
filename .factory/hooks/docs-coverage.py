#!/usr/bin/env python3
"""
Calculate Python docstring documentation coverage for the codebase.
Runs at SessionEnd to report how well functions/classes are documented.
"""

import os
import re
import sys


def analyze_python_file(file_path):
    """Return (total_functions, documented_functions) counts for a .py file."""
    with open(file_path) as f:
        content = f.read()

    # Find all function/method definitions
    func_defs = re.findall(r"^( *)(?:async )?def (\w+)\(", content, re.MULTILINE)
    total = 0
    documented = 0

    for indent, name in func_defs:
        # Skip private test helpers and dunder methods other than __init__
        if name.startswith("_") and name != "__init__":
            continue
        total += 1

        # Check if there's a docstring right after the def line
        pattern = rf"(?:async )?def {re.escape(name)}\(.*?\).*?:\s*\n\s+\"\"\""
        if re.search(pattern, content, re.DOTALL):
            documented += 1

    return total, documented


def main():
    src_dir = os.environ.get("DROID_PROJECT_DIR", ".")
    package_dir = os.path.join(src_dir, "backend")

    if not os.path.isdir(package_dir):
        # Try generic src/ fallback
        package_dir = os.path.join(src_dir, "src")
        if not os.path.isdir(package_dir):
            sys.exit(0)

    total_functions = 0
    documented_functions = 0

    for root, dirs, files in os.walk(package_dir):
        # Skip caches
        dirs[:] = [d for d in dirs if d not in ["__pycache__", ".pytest_cache"]]

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                total, doc = analyze_python_file(file_path)
                total_functions += total
                documented_functions += doc

    if total_functions > 0:
        coverage = (documented_functions / total_functions) * 100

        print("\n📊 Python Docstring Coverage Report")
        print("   Package: backend")
        print(f"   Documented functions: {documented_functions}/{total_functions}")
        print(f"   Coverage: {coverage:.1f}%")

        if coverage < 50:
            print(
                "\n   ⚠️  Low coverage. Consider adding docstrings to public functions."
            )
        elif coverage < 80:
            print("\n   ✓  Coverage is okay, but could be improved.")
        else:
            print("\n   ✓  Excellent docstring coverage!")
    else:
        print("No public functions found to analyze.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error in docs-coverage: {e}", file=sys.stderr)
    sys.exit(0)
