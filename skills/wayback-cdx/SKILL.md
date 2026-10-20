---
name: wayback-cdx
description: Discover dated historical public URL captures through the Internet Archive CDX index.
---

# wayback-cdx

Source: https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server. Contract reviewed 2026-10-19; provider terms and limits can change.

Use the OSINTNET `source_query` MCP tool or authenticated `POST /api/jobs`. Set `adapter` to `wayback-cdx`, choose a case ID, supply `parameters` such as `{"domain":"example.org"}`, and a unique idempotency key. A repeated key with different inputs is rejected. Enable this node explicitly before dispatch; integration health remains unknown until a real successful call.

## Bounds and authorization

At most 100 index rows, collapsed by digest; one GET; at least 3 seconds; 8 MB. No credentials. This initial adapter has no automatic pagination or replay downloads. Preserve query, response and timestamps; an access error stops the query.

Only public, authorized records are in scope. Stop on authentication gates, CAPTCHA, 403 or 429; do not rotate endpoints or identities to work around them. No paid inference or paid data calls are implemented by this adapter.

## Evidence and interpretation

CDX is an index. A row does not prove the replay body is accessible or that a historical claim is true. Absence from this bounded result is not evidence of absence.

Output is a durable job ID/state followed by capture ID, byte count and latency, or a bounded error code. Retrieve provenance through `evidence_record(capture_id)` and search with `evidence_search(case_id, query)`. Raw SHA-256 blobs and chained capture metadata remain separate from derived text. Store issuer, URL, final URL, capture time, hash, parser and precise locator for every downstream assertion. Preserve conflicting and favorable evidence. Source freshness is the capture time, not a claim about when an underlying event occurred.

## Failure and validation

Disabled nodes cannot dispatch new requests; queued work waits. Each job has a lease and bounded GET retries after process failure. Normal source errors finish as failed jobs and require an explicit new query; no blind access-gate retry. Health and request events feed the live console. GET retries can create a second capture; do not count it as independent corroboration. There is no cross-query response cache in this version; raw blobs deduplicate by hash.

Run `.venv/bin/python -m pytest -q`. The common suite checks admission bounds, DNS/redirect refusal, source isolation, durable claims, provenance tampering and authentication. Live source smoke outcomes are recorded separately in `docs/VERIFICATION.md`; passing unit checks does not establish that this provider currently responds.
