#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN=${PYTHON_BIN:-python3}

"$PYTHON_BIN" -m py_compile kamichizu/*.py
"$PYTHON_BIN" -m unittest discover -s tests -p "test_*.py"
