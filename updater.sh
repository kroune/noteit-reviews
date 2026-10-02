#!/bin/bash
# Periodically rebuild the site from scraped data and push updates
# while the scraper process is alive; one final rebuild+push after it exits.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
SCRAPER_PID="$1"
cd "$DIR"

rebuild_push() {
  .venv/bin/python build_site.py || return
  if ! git diff --quiet || ! git diff --cached --quiet; then
    git add -A
    git -c user.name=kroune -c user.email=kroune@users.noreply.github.com \
      commit -qm "data update: $(date -u +%Y-%m-%dT%H:%MZ), $(wc -l < data/reviews_raw.jsonl) reviews"
    git push -q origin main && echo "[updater] pushed $(date +%H:%M:%S)"
  fi
}

while kill -0 "$SCRAPER_PID" 2>/dev/null; do
  sleep 600
  rebuild_push
done
sleep 5
rebuild_push
echo "[updater] scraper finished, final push done"
