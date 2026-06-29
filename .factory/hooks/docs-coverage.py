#!/usr/bin/env python3
"""
Calculate documentation coverage for the monorepo codebase.
Runs at SessionEnd to report how well functions/components are documented.
Covers both backend (Python docstrings) and frontend (Vue/TS component count).
"""

import os
import re
import sys


def _progress_bar(pct: float, width: int = 20) -> str:
    """Return a visual progress bar string for a percentage."""
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def analyze_python_file(file_path: str) -> tuple[int, int]:
    """Return (total_functions, documented_functions) counts for a .py file."""
    with open(file_path) as f:
        content = f.read()

    func_defs = re.findall(r"^( *)(?:async )?def (\w+)\(", content, re.MULTILINE)
    total = 0
    documented = 0

    for indent, name in func_defs:
        if name.startswith("_") and name != "__init__":
            continue
        total += 1
        pattern = rf"(?:async )?def {re.escape(name)}\(.*?\).*?:\s*\n\s+\"\"\""
        if re.search(pattern, content, re.DOTALL):
            documented += 1

    return total, documented


def _count_dir(path: str, exts: tuple[str, ...]) -> int:
    """Recursively count files with given extensions in a directory."""
    if not os.path.isdir(path):
        return 0
    total = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.endswith(exts) and not f.startswith("."):
                total += 1
    return total


def analyze_frontend() -> dict[str, int]:
    """Count frontend components, pages, stores, composables (recursive)."""
    src_dir = os.path.join(os.environ.get("DROID_PROJECT_DIR", "."), "frontend", "src")
    if not os.path.isdir(src_dir):
        return {}

    counts = {}
    for folder in ["components", "pages", "stores", "composables", "services"]:
        path = os.path.join(src_dir, folder)
        counts[folder] = _count_dir(path, (".vue", ".ts"))

    return counts


def main() -> None:
    src_dir = os.environ.get("DROID_PROJECT_DIR", ".")

    # --- Backend: Python docstring coverage ---
    package_dir = os.path.join(src_dir, "backend")
    if not os.path.isdir(package_dir):
        package_dir = os.path.join(src_dir, "src")
    if os.path.isdir(package_dir):
        total_functions = 0
        documented_functions = 0
        file_stats: list[tuple[str, int, int]] = []  # (rel_path, total, documented)
        skip_dirs = {"__pycache__", ".pytest_cache", ".venv", "venv", ".tox", "node_modules"}
        for root, dirs, files in os.walk(package_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    t, d = analyze_python_file(filepath)
                    total_functions += t
                    documented_functions += d
                    if t > 0:
                        rel = os.path.relpath(filepath, src_dir)
                        file_stats.append((rel, t, d))

        if total_functions > 0:
            coverage = (documented_functions / total_functions) * 100
            bar = _progress_bar(coverage)
            print(f"\n📊 Python Docstring Coverage Report")
            print(f"   Package: backend")
            print(f"   Coverage: {coverage:.1f}% [{bar}] {documented_functions}/{total_functions} documented")

            # Per-file breakdown: show files with undocumented functions
            undocumented_files = [(p, t, d) for p, t, d in file_stats if d < t]
            if undocumented_files:
                undocumented_files.sort(key=lambda x: x[1] - x[2], reverse=True)
                print(f"\n   Files with undocumented functions ({len(undocumented_files)} files):")
                for rel_path, total, documented in undocumented_files:
                    missing = total - documented
                    file_pct = (documented / total) * 100 if total else 0
                    file_bar = _progress_bar(file_pct, width=10)
                    print(f"   [{file_bar}] {rel_path} ({missing}/{total} undocumented)")
            elif coverage >= 100:
                print(f"\n   ✅  All functions are documented!")

            # Severity message
            if coverage < 50:
                print(f"\n   ⚠️  Low coverage ({coverage:.0f}%). Add docstrings to public functions.")
            elif coverage < 80:
                print(f"\n   ✓   Coverage is okay ({coverage:.0f}%), but could be improved.")
            else:
                print(f"\n   ✅  Excellent docstring coverage! ({coverage:.0f}%)")

    # --- Frontend: Component stats ---
    frontend_counts = analyze_frontend()
    if frontend_counts:
        print(f"\n📊 Frontend Component Stats")
        total = sum(frontend_counts.values())
        for folder, count in frontend_counts.items():
            print(f"   {folder}: {count}")
        print(f"   Total: {total} modules")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error in docs-coverage: {e}", file=sys.stderr)
    sys.exit(0)
