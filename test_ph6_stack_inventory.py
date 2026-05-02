#!/usr/bin/env python3
import ast
import json
import os
import pathlib
import py_compile
import subprocess
import sys
import time

ROOT = pathlib.Path.cwd()

FILES = {
    "frame_filter/frame_filter.py": "Main filter loop",
    "frame_filter/cram_writer.py": "CRAM write layer",
    "frame_filter/ph6lite/backend.py": "Backend logic",
    "frame_filter/ph6lite/advisory_client.py": "Advisory channel",
    "frame_filter/ph6lite/schema_validator.py": "Schema enforcement",
    "frame_filter/test_ph6lite_phase2.py": "Phase 2 test harness",
    "frame_filter/tests/cram_speed_test.py": "CRAM speed bench",
    "frame_filter/tests/cram_fsync_worstcase.py": "fsync worst-case test",
    "frame_filter/virtual_tokens.py": "Virtual token logic",
    "frame_filter/jetson_service/app.py": "Jetson/Ollama service",
}

REPORT = {
    "schema": "ph6.stack_inventory_test.v1",
    "authority": "NONE",
    "lane": "TEST_ONLY",
    "timestamp_unix": time.time(),
    "root": str(ROOT),
    "results": [],
    "summary": {},
}

def analyze_file(rel, role):
    path = ROOT / rel
    result = {
        "file": rel,
        "role": role,
        "exists": path.exists(),
        "syntax": None,
        "imports": [],
        "functions": [],
        "classes": [],
        "status": "DROP",
        "reasons": [],
    }

    if not path.exists():
        result["reasons"].append("MISSING_FILE")
        return result

    try:
        py_compile.compile(str(path), doraise=True)
        result["syntax"] = "PASS"
    except Exception as e:
        result["syntax"] = "DROP"
        result["reasons"].append(f"SYNTAX_FAIL: {e}")
        return result

    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    result["imports"].append(n.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                result["imports"].append(mod)
            elif isinstance(node, ast.FunctionDef):
                result["functions"].append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                result["functions"].append(node.name)
            elif isinstance(node, ast.ClassDef):
                result["classes"].append(node.name)
    except Exception as e:
        result["reasons"].append(f"AST_PARSE_WARN: {e}")

    result["status"] = "PASS"
    return result

for rel, role in FILES.items():
    REPORT["results"].append(analyze_file(rel, role))

passed = sum(1 for r in REPORT["results"] if r["status"] == "PASS")
dropped = sum(1 for r in REPORT["results"] if r["status"] == "DROP")
missing = sum(1 for r in REPORT["results"] if not r["exists"])

REPORT["summary"] = {
    "total": len(REPORT["results"]),
    "pass": passed,
    "drop": dropped,
    "missing": missing,
    "overall": "PASS" if dropped == 0 else "DROP",
}

out = ROOT / "ph6_stack_inventory_report.json"
out.write_text(json.dumps(REPORT, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

print(json.dumps(REPORT["summary"], indent=2))
print(f"\nReport written: {out}")

for r in REPORT["results"]:
    print(f"{r['status']:4} | {r['file']} | {r['role']}")
    if r["reasons"]:
        for reason in r["reasons"]:
            print(f"     - {reason}")
