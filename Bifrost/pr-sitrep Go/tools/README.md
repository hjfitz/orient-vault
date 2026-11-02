# pr-sitrep Go — parity tools

Kept out of the repo on purpose (G1: no cross-app imports). Copy into a scratch dir to use.

- `gen-classify.ts`, `gen-render.ts` regenerate the goldens from the TS app. Run them from
  `apps/pr-sitrep` with `TS_SRC=$PWD/src ./node_modules/.bin/ts-node-transpile-only -O '{"module":"commonjs"}' <gen> <out.json>`.
- `names.py <ts spec> <go tests...>` lists the TS `it(...)` names missing from the Go tests.
- `parity.sh` (G1) runs both apps locally and diffs raw GET bytes, read in the order TS, Go, TS. It needs, beside it:
  - `parity.env` (prod-shaped: `GITHUB_ORGS=gfs-bifrost`, `GITHUB_ALL_AUTHORS=true`,
    `FALLBACK_WINDOW_DAYS=14`, `GITHUB_APP_CLIENT_ID=…`, Slack and merge off);
  - `app-key.pem`, from `gcloud secrets versions access latest --secret pr-sitrep-github-app-key --project bifrost-dev-global1`. Never commit or print it.

  It never POSTs. A pass takes ~15 minutes for 41 PRs, because the sweep is sequential.
