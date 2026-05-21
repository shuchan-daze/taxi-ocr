#!/usr/bin/env bash
set -euo pipefail

echo "== verify =="
"$(dirname "$0")/verify.sh"

echo
echo "== git diff --stat =="
git diff --stat

echo
echo "== git diff --name-status =="
git diff --name-status

echo
echo "== git status --short =="
git status --short

echo
echo "== staged generated artifact check =="
if git diff --cached --name-only | rg '(^|/)(reconciled_report_|streamlit_qr)|(^|/)\.kamichizu_debug(/|$)'; then
  echo "Generated artifact is staged. Failing done check."
  exit 1
else
  echo "No generated artifacts are staged."
fi
