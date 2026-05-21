#!/usr/bin/env bash
set -euo pipefail

export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/private/tmp/kamichizu_pycache}"

echo "== py_compile =="
python -m py_compile app.py kamichizu_engine/*.py

echo
echo "== pytest =="
pytest -q -p no:cacheprovider

RG_EXCLUDES=(
  --glob '!.git/**'
  --glob '!venv/**'
  --glob '!__pycache__/**'
  --glob '!.pytest_cache/**'
  --glob '!node_modules/**'
  --glob '!.kamichizu_debug/**'
  --glob '!scripts/verify.sh'
)

OLD_TERMS='review|paper_only|missing_nippou|mismatch|legacy|旧|v1|v2|alignment_v2|v2_to_ui|v2_validate|layer3_modules'
OLD_COMPARISON='aggregate_totals|existing_totals|total_comparison|build_kamichizu_total_comparison|display_rows|paper_map_v1|paper_map_shadow'

echo
echo "== old term check =="
if rg "$OLD_TERMS" . -n "${RG_EXCLUDES[@]}"; then
  echo "Old terms were found. Review the hits above."
else
  echo "No old terms found."
fi

echo
echo "== old comparison entry check =="
if rg "$OLD_COMPARISON" . -n "${RG_EXCLUDES[@]}"; then
  echo "Old comparison entry was found. Failing verification."
  exit 1
else
  echo "No old comparison entries found."
fi

echo
echo "== git status =="
git status --short
