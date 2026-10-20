# OSINTNET

A self-hosted workspace for public-source research. Queue bounded source queries, preserve original evidence, qualify assertions, inspect dated relationships, and follow actual acquisition events through an authenticated pipeline canvas.

The portable platform is separate from the Umma Foundation case. Case data, credentials and generated reports stay in ignored private storage. Nothing in the platform treats a source mention, allegation or geographic association as a verified finding.

## Run locally

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pytest -q
OSINTNET_WEB_HOSTS=example.org .venv/bin/uvicorn osintnet.app:app --host 127.0.0.1 --port 8780 --no-access-log
```

Open `http://127.0.0.1:8780/login` and choose the generated `private/runtime/operator.key` file. Keep it private. New sources start disabled; pending integrations cannot be enabled. The example web host is an exact acquisition allowlist, not a restriction on viewing publisher links.

## What works

- Seven bounded source adapters: ProPublica, official IRS documents, approved public websites, NYC Socrata, OSM Overpass, Wayback CDX and scoped Arctic Shift threads.
- SHA-256 content-addressed originals, append-only capture/claim/relationship records, chained capture metadata, SQLite FTS, dated financial extractions and provider-attributed geographic directories.
- Durable idempotent jobs, fenced leases, bounded GET recovery, dependencies, independent source controls, master acquisition pause and audit events.
- Authenticated REST, replayable SSE and native MCP using the official Python SDK. Four MCP tools expose status, evidence search/records and operator source queries.
- A pipeline canvas, source inspector, observed request metrics, work queue, financial comparisons, typed graph, geodesic one-mile directory and dated investigation reports.
- A production Compose overlay with one resource-bounded worker process per selected adapter, heartbeats and graceful independent worker restarts. No Docker socket is exposed to the application.

Local development uses two shared source workers. Production isolation uses both `compose.yaml` and `compose.workers.yaml`; the gateway then runs zero acquisition workers. Use an authenticated tunnel overlay for external access. See [operations](docs/OPERATIONS.md), [architecture](docs/ARCHITECTURE_DECISION.md), [capability decisions](docs/CAPABILITY_MATRIX.md) and [verification](docs/VERIFICATION.md).

## Evidence and integration boundaries

Fourteen skills document selected source, manual registry/ad/court, financial, evidence and operator-delegation workflows. A valid skill file does not imply an external gate or API contract passed. The existing Shodan service is preserved. Credentialed CourtListener MCP, automated ad collectors, core ROTOXY dispatch controls, LangSmith credit eligibility and desktop OAuth enrollment remain separate acceptance steps. Live provider balances and model utilization are unknown unless observed; they are not simulated.

The private Umma assessment and source package are generated locally. The case remains open where records, verification gates or transaction evidence are unavailable. See [case scope](cases/umma/CASE_BRIEF.md) and [handoff status](docs/HANDOFF_STATUS.md). The original [master specification](MASTER_PROMPT.md) records the broader requirements and [source catalog](docs/SOURCE_CATALOG.md) preserves candidates, including rejected or deferred integrations.

## Security and publication

Use least-privilege authentication, exact source hosts, source-specific rate/size bounds and private backups. Enforce Cloudflare Access JWT verification at the origin when deploying behind Access. Application roles still require a separate OSINTNET key. Never commit secrets or private case data. Browser verification gates are handed to the operator.

Assess organizational conduct through evidence. Do not profile religion, infer kinship from names, attach unrelated court text matches, or turn neighborhood proximity into ownership or wrongdoing. Preserve contradictory evidence and append corrections.

MIT licensed. Third-party data retains its source terms; OSM data requires attribution and ODbL compliance. The repository does not grant rights to redistribute every captured page or asset.
