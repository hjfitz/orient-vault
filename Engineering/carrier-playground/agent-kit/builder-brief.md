**Where to work.** Use the git worktree named below. Work only there: never touch /home/harry/code/merak/carrier-playground itself or any other worktree, since other agents are building other mocks in parallel. Never run git switch, stash, rebase or push. When you're done, commit, staging explicit paths only (never `git add -A` or `.`). End the commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. A commit hook rejects multi-line comment blocks, so a comment is either one line of non-obvious "why" or nothing. Never put ticket numbers in code.

**Setup.** `cd` into the worktree, then run `mise install`. Install with `env "npm_config_//npm.pkg.github.com/:_authToken=$(gh auth token)" mise x -- pnpm install`, and use `mise x -- pnpm …` for every pnpm command. Plain installs can drop `optional: true` / `peerDependenciesMeta` markers from pnpm-lock.yaml, so finish with `mise x -- pnpm install --lockfile-only --fix-lockfile` and check that `git diff origin/main -- pnpm-lock.yaml` shows only your additions.

**Read first.**
- AGENTS.md is the contract: the same external contract, lookups and logic as the real proxy; every upstream mocked; all data fake; never log request or response bodies, labels, keys or credentials.
- README.md.
- Use apps/fedex-proxy and apps/dpd-europe-proxy as the newest templates: their app layout, log-safety tests, README "deviations" and "production behaviour mirrored on purpose" sections, and dockerfile.
- Also the mock upstreams in apps/mock-upstreams/src/*, packages/mock-kit (logger, makeLabelPdf, installUpstreamAuth) and packages/apiky-client.

**Data rule.**
- Production config and source may hold real addresses, names, phone numbers, account ids and keys. Never copy any of it.
- Every fixture and config value must be obviously fake (`Testville`, `TE1 1ST`, `example.test`, `07000000000`, `MOCK…`).

**Mocking rules.**
- Databases, KMS and secret stores become fixtures.
- Every carrier/API call goes to a new mock under `apps/mock-upstreams/src/<carrier>/**`, with fixtures under `apps/mock-upstreams/fixtures/<carrier>/**`. Its labels are MOCK PDFs or PNGs from mock-kit, and it has magic inputs for the failure paths.
- mock-upstreams is shared by every carrier, so nothing may crash or stall it:
  - async handlers pass errors to `next(e)`;
  - bound every user-controlled size, including page and package counts;
  - use `Object.hasOwn` for lookups on user input;
  - refuse XML DOCTYPEs if it parses XML.

**What to deliver.** You own exactly these paths:
1. `apps/<app>/**`:
   - the proxy, on the port given;
   - vitest tests, one behaviour per test, including a log-safety test that runs error paths and a malformed-JSON body and asserts that no address, contact, token or credential appears in captured logs;
   - a house-style README;
   - a dockerfile copied from apps/fedex-proxy/dockerfile.
2. The mock upstream and fixtures, `apps/mock-upstreams/fixtures/apiky/<carrier>.json` with fake keys, and the one mount line in `apps/mock-upstreams/src/server.ts`.
3. `iac/projects/mock-<carrier>/**`, copied from iac/projects/mock-fedex. Logs go to GFS Datadog only: no `datadog_api_key_ilg`, no `datadog_additional_api_key`. Every value is fake.
4. In `iac/projects/mock-edge/edge.tf`, add your entry to `local.proxies` (`<key> = "<host label>"`). Only add entries; never remove or rename any.
5. Workflow rows:
   - in `.github/workflows/deploy-dev.yaml`, a docker-push include and your project in the terraform-proxies matrix, plus the header image count;
   - in `tf-plan-pr.yaml`, your project in the matrix.
6. A section in `scripts/smoke.mts` (`<CARRIER>_URL`, default http://localhost:<port>) covering the happy paths and no-key refused. Also the README proxy table row, intro list and Dev name list, and the AGENTS.md layout line.

**Done means.**
- `mise x -- pnpm lint`, `typecheck` and `test` pass for the whole repo.
- Your proxy and mock-upstreams images build with `docker build -f <dockerfile> --secret id=github_token,env=GH_TOKEN .` (GH_TOKEN=$(gh auth token)). If buildx is missing, link mise's buildx through a scratch DOCKER_CONFIG and leave ~/.docker untouched.
- With both containers running, your smoke checks pass. Stop everything you started.
- The container logs contain no bodies, labels, keys, tokens, addresses or phones.
- Then commit.

**Report back** in under 250 words: the commit sha, test counts, what you verified and how, every deviation from the source, likely prod bugs you mirrored, and anything you were unsure about. If the source does something you can't mirror safely, stop and report rather than guess.
