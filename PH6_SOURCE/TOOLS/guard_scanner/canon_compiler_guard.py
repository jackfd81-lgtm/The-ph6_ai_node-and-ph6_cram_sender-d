#!/usr/bin/env python3
"""
PH6CRAM Canon Guard Scanner — checks all Python modules enforce if-main execution guards.
Separate from canon_compiler.py (manifest generator). Run from PH6_SOURCE/.
PROPOSED artifact. Ratified_by: null.
"""

import ast
import os
import sys
from pathlib import Path

SKIP_DIRS = {".venv", ".git", "__pycache__", ".ruff_cache"}


def _is_module_docstring(node: ast.stmt, is_first: bool) -> bool:
    return (
        is_first
        and isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def check_script_guards(file_path: str) -> bool:
    """Parses module to enforce if-main execution block on top-level non-constant statements."""
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            syntax_tree = ast.parse(f.read(), filename=file_path)
        except SyntaxError:
            print(f"[CRITICAL BOUNDARY FAULT] Syntax error parsing: {file_path}")
            return False

    has_loose_execution = False
    has_main_guard = False

    for idx, node in enumerate(syntax_tree.body):
        # Skip module docstring
        if _is_module_docstring(node, idx == 0):
            continue

        # Skip import statements
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        # Skip uppercase global constants
        if isinstance(node, ast.Assign):
            if all(
                isinstance(t, ast.Name) and t.id.isupper()
                for t in node.targets
            ):
                continue

        # Skip function/class definitions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue

        # Detect if __name__ == "__main__" guard
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            test = node.test
            if (
                isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value == "__main__"
            ):
                has_main_guard = True
                continue

        # Anything else at module level is loose execution
        has_loose_execution = True

    if has_loose_execution and not has_main_guard:
        return False
    return True


def execute_canon_guard_scan(scan_root: str = ".") -> int:
    print("==============================================================")
    print("PH6CRAM CANON GUARD SCANNER: SCANNING EXECUTION BOUNDARIES")
    print(f"  root: {scan_root}")
    print("==============================================================")

    invalid_modules = 0
    for directory_root, dirs, targets in os.walk(scan_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for target_file in targets:
            if not target_file.endswith(".py"):
                continue
            module_path = os.path.join(directory_root, target_file)
            if not check_script_guards(module_path):
                print(f"[BOUNDARY FAULT] Missing if-main guard: {module_path}")
                invalid_modules += 1

    if invalid_modules > 0:
        print(f"\n[RESULT] {invalid_modules} module(s) violate if-main guard rules.")
        return 1

    print("[SUCCESS] All execution boundaries validated. COURTROOM READY.")
    print("==============================================================")
    return 0


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(execute_canon_guard_scan(root))
