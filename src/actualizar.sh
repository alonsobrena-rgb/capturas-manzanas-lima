#!/usr/bin/env bash
# Recalcula capturas, copia las nuevas, regenera index.html y publica. Idempotente.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 src/capt.py
python3 src/vis.py
FECHA="${FECHA:-$(date +%d-%m-%Y)}" python3 src/build.py
git add -A
if git diff --cached --quiet; then echo "Sin cambios."; exit 0; fi
git commit -m "Actualiza capturas $(date +%Y-%m-%d)"
git push
