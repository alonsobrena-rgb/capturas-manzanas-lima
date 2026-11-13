#!/usr/bin/env bash
# Sube al tracker las capturas nuevas del visor (fichas por manzana). Silencioso; para correrlo en segundo plano.
cd "$(dirname "$0")/.." || exit 1
exec 9>/tmp/publicar_v2.lock; flock -n 9 || exit 0
python3 src/fichas.py >/dev/null 2>&1 && FECHA="$(date +%d-%m-%Y)" python3 src/build.py >/dev/null 2>&1
git add -A >/dev/null 2>&1
git diff --cached --quiet && exit 0
git commit -qm "Capturas nuevas del visor $(date +%H:%M)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SrvV2CGVPtQjUvtsbfAr4i" && git pull -q --rebase && git push -q
