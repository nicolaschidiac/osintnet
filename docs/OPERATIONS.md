# Run OSINTNET

Use Python 3.11 or newer. Development and the pinned Docker image were checked with Python 3.14. From a clone:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pytest -q
OSINTNET_WEB_HOSTS=example.org .venv/bin/uvicorn osintnet.app:app --host 127.0.0.1 --port 8780 --no-access-log
```

Open the local console, then enter the generated key from `private/runtime/operator.key` in its sign-in form. Keep the key out of chat, screenshots and logs. Its hash is stored in `auth.json`; analyst/operator/admin keys can be configured there by the local administrator. New adapters start disabled. Pending integrations cannot be enabled. Exact public web hosts are operator configuration, not a model-controlled arbitrary-URL permission.

The native MCP endpoint is `/mcp/`, using the official Python SDK and a Bearer key. `network_status`, `evidence_search`, `evidence_record` and operator-scoped `source_query` are exposed. Desktop-client enrollment/OAuth is a separate acceptance step; an SDK smoke test is not evidence that a particular desktop client was enrolled.

## Deployment and controls

`docker compose config --quiet` validates configuration. Docker itself validates mount semantics; the initial unquoted tmpfs list was corrected after a staging start rejected it. The gateway binds its published port to host loopback. It runs without root, has a read-only filesystem, a writable private data volume, bounded tmpfs, dropped capabilities and CPU/memory/PID limits. Secrets and case data are excluded from the build context.

For external access, set the exact public origin and Cloudflare Access issuer/audience in the protected `.env`. Create a narrow reusable Access policy and self-hosted app **before** the tunnel/DNS route. Origin JWT validation stays enabled. A remote token-based cloudflared connector should use a protected token file, not a token command argument or browser script. Use a separate service token restricted to this Access application for automated clients; its entitlement does not grant an OSINTNET role without an application key.

The console master control pauses new OSINTNET acquisition and lets in-flight GETs finish. It does not stop the console, evidence storage or unrelated host services. Individual sources can be disabled independently. A failed job does not automatically hammer a provider; use an explicit new query after examining the reason. Lease recovery only retries GET operations, at most three attempts after process failure. Ambiguous external writes are not implemented.

## Backup, restore and rollback

Pause acquisition and wait for active jobs to finish. Use `sqlite3.Connection.backup` to copy the database; copy the blobs directory and protected authentication files into a private backup. Keep a manifest of file hashes. Restore into a fresh isolated directory, run `PRAGMA integrity_check` and `Store.verify`, and compare capture counts and ledger tip before changing service volumes. Do not share or commit backups. Do not copy one instance's login credentials to another deployment implicitly.

Stage releases in separate directories and retain the previous image digest/config. Recreate only the `osintnet` Compose project. Roll back the application image/config and recheck health plus ledger verification. Avoid destructive schema migrations; current schema changes are additive. For an initial deployment failure, stop only the new gateway/tunnel containers and keep the data volume. Withdraw only the new hostname's tunnel/DNS resource if exposure has occurred; never reset host-wide Docker, Tailscale or Cloudflare state.

## Current limitations

The base development service uses two shared workers. The production worker overlay provides separate bounded processes and independent restarts. Roles span the instance's cases. There is no per-source credential editor, automatic model-budget enforcement, live credit-account reader or background LLM orchestration in the core. ROTOXY dispatch is an explicit operator script with durable receipts; provider-reported cost may arrive late. Cached blobs deduplicate content but there is no HTTP response cache. Paid integrations and broad OSINT bundles remain deferred. Consult `VERIFICATION.md` for tested layers and unresolved acceptance gates.

## Independent production source processes

Run `docker compose -f compose.yaml -f compose.workers.yaml up -d --build`. Include the protected tunnel overlay as a third file for the deployed host. The base file alone retains two shared local workers. The worker overlay sets gateway acquisition workers to zero and starts seven individual source containers.

Each source worker has 0.25 CPU, 192 MiB memory, 32 PIDs, a read-only root, no capabilities, bounded tmpfs/logs and no published port. With the gateway cap, configured CPU ceilings total 3.25 cores and memory ceilings total 2,112 MiB, below the measured four-core ORA6 capacity. These are ceilings, not reserved resources or load-test claims. Workers receive public-source configuration only, not Cloudflare service credentials.

An admin can request “Restart worker”. A per-source generation counter lets the worker finish its current GET, record shutdown and exit; its own container restart policy starts a fresh process. It does not restart another adapter or the gateway. Worker heartbeats are separate from the last source-request result; a stale/missing worker is not displayed as a healthy enabled source. Disable prevents new claims while allowing an in-flight read to finish. Master pause prevents every new claim while leaving the console and evidence available.

SSE responses have a 30-second lifetime. EventSource reconnects with Last-Event-ID; this preserves replay and permits bounded graceful shutdown. A 90-second container grace period accommodates an existing bounded GET. Before a release, pause acquisition, confirm no running jobs, back up, and recreate only the OSINTNET project.

## Transfer private evidence without transferring credentials

`scripts/export_workspace.py SOURCE OUTPUT --deployment` takes a consistent SQLite backup, removes sessions/rate-limit/worker runtime records, pauses acquisition and cancels pending execution in the exported copy. It verifies each blob and reuses matching read-only blobs on repeat exports. It does not copy authentication files. Archive only the database, blobs and export manifest.

With the destination gateway and workers stopped, `scripts/restore_workspace.py ARCHIVE DESTINATION --expected-tip HASH` refuses a changed destination, validates archive members and the full ledger, backs up the prior DB, and preserves destination authentication files. The expected tip is a compare-before-replace guard, not a merge mechanism. Never overwrite new destination captures by substituting an old expected tip. Keep source data private; restore only into the named instance. Afterward verify the ledger, application key, Access JWT denial and authorized edge/MCP path separately.

The key-file login option reads a small local key into the password form and retains the selected filename with an explicit ready status. A cancelled file chooser now displays a message, and an invalid replacement clears the previous key. The form sends the key only to this instance's sign-in endpoint. Same-origin referrers keep Chromium login compatible while external publisher links suppress referrers; null and untrusted origins remain rejected.

## Deployed instance handoff (2026-10-19)

The protected dashboard is `https://umma.ziopsyop.tech`. Gateway runtime revision `06c8b4b` runs on ORA6 from `/home/jq/osintnet/releases/20261019-final`, with Compose project `osintnet` and volume `osintnet_osintnet-data`. Include `compose.yaml`, `compose.workers.yaml` and the existing protected `compose.tunnel.yaml` when inspecting or operating that project. Preserve the remote protected environment and tunnel overlay; they are deliberately not distributed with the repository.

Complete the owner Cloudflare Access sign-in first, then use this instance's OSINTNET key. The remote admin key is inside the gateway at `/data/operator.key`; the local development key is a different credential. An authorized owner can retrieve a private login-file copy without displaying it in the terminal:

```sh
umask 077
mkdir -p private/ora6
ssh ora6 'docker exec osintnet-gateway-1 cat /data/operator.key' > private/ora6/operator.key
```

Choose that file in the production login form. Do not send it in chat or commit it. This command is an explicit owner action, not part of automatic evidence export or deployment. Account selection and one-time login codes remain interactive.

The remote ledger has 266 captures (260 case captures plus six acceptance captures). The older local export has 260. Do not replace the remote database with that older export. Acquisition is paused, all source adapters disabled, and the console remains available. Enabling a source and master acquisition authorizes queued work; inspect the queue first.

Recent images are retained as `osintnet:rollback-5e23d1d` and `osintnet:rollback-f6df459` for UI rollback with the current worker configuration. The original application image is retained as `osintnet:rollback-ab20bc1`; the original release directory is `/home/jq/osintnet/releases/20261019`. Rollback requires the old matching Compose configuration and stopping only the seven new OSINTNET worker services before starting the old shared-worker gateway. Preserve the current data volume and back it up before any rollback; do not restore an old database merely to roll back code. Revalidate the ledger and authorization afterward. Existing Open WebUI, Ollama and other hosts' services are outside this project.

The temporary validation-service entitlement expires at 2026-10-20 07:05:21 UTC. Its expiration does not remove owner access. Owner browser login has passed. Desktop MCP enrollment, NY AG verification and unavailable registry/provider records remain recorded handoff gates.
