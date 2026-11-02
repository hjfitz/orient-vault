#!/usr/bin/env bash
# Parity gate: run the TS and Go apps side by side from one env, fetch each GET format as
# TS, Go, TS, strip generatedAt, and diff raw bytes. Never POSTs. Not committed.
set -euo pipefail
P=$(cd "$(dirname "$0")" && pwd)
W=${WORKTREE:?set WORKTREE}
OUT=${OUT:-$P/out-$(date -u +%Y%m%dT%H%M%S)}
TRIES=${TRIES:-3}
mkdir -p "$OUT"

# A clean environment, so nothing from the calling shell (a GITHUB_TOKEN, say) leaks in.
mapfile -t ENVV < <(grep -v '^#' "$P/parity.env" | grep .)
CLEAN=(env -i PATH="$PATH" HOME="$HOME" "${ENVV[@]}" GITHUB_APP_PRIVATE_KEY="$(cat "$P/app-key.pem")")

(cd "$W/apps/pr-sitrep" && ./node_modules/.bin/tsc >/dev/null)
(cd "$W/apps/pr-sitrep-go" && go build -o "$P/pr-sitrep-go" ./cmd/pr-sitrep)

"${CLEAN[@]}" PORT=3101 node "$W/apps/pr-sitrep/dist/main.js" >"$OUT/ts.log" 2>&1 & TS_PID=$!
"${CLEAN[@]}" PORT=3102 "$P/pr-sitrep-go" >"$OUT/go.log" 2>&1 & GO_PID=$!
trap 'kill $TS_PID $GO_PID 2>/dev/null || true' EXIT
for port in 3101 3102; do
  for _ in $(seq 1 50); do curl -sf "localhost:$port/health" >/dev/null && break; sleep 0.2; done
done

fetch() { # port format file
  curl -s -D "$3.headers" -o "$3" -H "x-correlation-id: parity" "localhost:$1/api/v1/sitrep?format=$2"
  sed -i -E 's/"generatedAt":"[^"]*"/"generatedAt":"<stripped>"/' "$3"
  grep -i '^content-type' "$3.headers" | tr -d '\r' > "$3.ctype"
}

status=0
for format in json markdown slack; do
  ok=0
  for attempt in $(seq 1 "$TRIES"); do
    d="$OUT/$format/$attempt"; mkdir -p "$d"
    fetch 3101 "$format" "$d/ts1"; fetch 3102 "$format" "$d/go"; fetch 3101 "$format" "$d/ts2"
    if ! cmp -s "$d/ts1" "$d/ts2"; then echo "$format attempt $attempt: TS moved between reads, retrying"; continue; fi
    if cmp -s "$d/ts1" "$d/go" && cmp -s "$d/ts1.ctype" "$d/go.ctype"; then
      echo "$format: IDENTICAL ($(wc -c <"$d/go") bytes, $(cat "$d/go.ctype"))"; ok=1; break
    fi
    echo "$format attempt $attempt: DIFFERS"; diff <(cat "$d/ts1.ctype" "$d/ts1") <(cat "$d/go.ctype" "$d/go") | head -20 || true
    ok=2; break
  done
  [ "$ok" = 1 ] || status=1
done
echo "outputs: $OUT"
exit $status
