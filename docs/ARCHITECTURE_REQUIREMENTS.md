# Target platform behavior (not an imposed implementation choice)

## Architecture discovery before commitment
An architect agent must compare one-VM vs distributed ORA6+ORA7 vs other options, inspect actual ARM/architecture, free resources and CrewAI/Docker workloads, security boundaries, rate limits, tool semantics and costs. Preserve existing ORA3 Shodan and any other production services. Decouple adapters so individual node disable/restart doesn't interrupt unrelated tools.

## Product separation
Core portable OSINTNET tools/configurations are case-neutral and documented for other users. `cases/umma` is a standalone investigative workspace, not hardwired into core. All case data must be local/private by default. Portable deploy targets, versioned tool specifications and extensible skill directory.

## Animated operations console
One login-protected web page at `umma.ziopsyop.tech`, visual palette inspired by n8n: smooth bendable animated pipes/edges, source/internet/crawler/MCP/agent/storage/model/telemetry nodes, panning/zoom and progressive discovery, clear live statuses and motion indicating **verified** data flow. Include authenticated per-node start, stop, disconnect, reconnect, refresh, inspect config, errors and quotas. Add tool-level metrics, aggregate logs, RBAC, audit trail, per-node isolation, maintenance mode, security alerts, redacted request examples and observable throughput/latency. User controls should not break other nodes. Up/down master controls are graceful stop/start, not unsafe host-wide system commands. Use actual events/metrics with timestamps and disconnected/offline states, never cosmetic invented activity.

## Data and skills
Evaluate PostgreSQL, DuckDB, object storage, optional graph projection, structured entity IDs and FTS/vector indexing; select by tested requirements. Event-sourced ingestion and immutable WARC/raw evidence artifacts, controlled schema migrations, worker leases, retries, source dedup, fine-grained snapshots. Every chosen capability must have a maintained adapter and `SKILL.md` including scope, schema, source, rate limits, error behavior, provenance and tests. Preserve auth in vault/environment injected at runtime.

## Gateway and tunnel
Cloudflare Tunnel with least-privilege service tokens + Cloudflare Access where practical; enforce TLS and audit logs. Never make backend admin ports or raw MCPs publicly accessible without authentication. Independent health endpoints and service-level caps; no token embedded in browser JS. Test real ChatGPT Desktop-compatible MCP endpoint/transport; use negotiated auth. A Cloudflare global API key is unnecessary if a suitable scoped token works.

## Reliability
Benchmarks on ORA6 before distributing, resource limits, no automatic overcommit, graceful shutdown, service restart and retry recovery. Synthetic traces must be marked as synthetic and cannot be displayed as live production work. Telemetry private and scrubbed before LangSmith export.