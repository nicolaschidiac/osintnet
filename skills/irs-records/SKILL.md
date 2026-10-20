---
name: irs-records
description: Capture an original publicly downloadable IRS document from an official IRS host.
---

# irs-records

Source: https://www.irs.gov/charities-non-profits/form-990-series-downloads. Contract reviewed 2026-10-19; provider terms and limits can change.

Use the OSINTNET `source_query` MCP tool or authenticated `POST /api/jobs`. Set `adapter` to `irs-records`, choose a case ID, supply `parameters` such as `{"url":"https://www.irs.gov/pub/irs-pdf/f990.pdf"}`, and a unique idempotency key. A repeated key with different inputs is rejected. Enable this node explicitly before dispatch; integration health remains unknown until a real successful call.

## Bounds and authorization

One GET; at least 2 seconds between calls; 16 MB; explicit document URL. Only www.irs.gov and apps.irs.gov are accepted. No credentials. Large ZIP/index acquisition is a separate bounded operator task; do not load entire bulk datasets into model context.

Only public, authorized records are in scope. Stop on authentication gates, CAPTCHA, 403 or 429; do not rotate endpoints or identities to work around them. No paid inference or paid data calls are implemented by this adapter.

## Evidence and interpretation

Check EIN, tax period, amendments, schedules and source identity. A blank Form 990 template is not a filed return. Distinguish letter issue date from effective exemption date.

Output is a durable job ID/state followed by capture ID, byte count and latency, or a bounded error code. Retrieve provenance through `evidence_record(capture_id)` and search with `evidence_search(case_id, query)`. Raw SHA-256 blobs and chained capture metadata remain separate from derived text. Store issuer, URL, final URL, capture time, hash, parser and precise locator for every downstream assertion. Preserve conflicting and favorable evidence. Source freshness is the capture time, not a claim about when an underlying event occurred.

## Failure and validation

Disabled nodes cannot dispatch new requests; queued work waits. Each job has a lease and bounded GET retries after process failure. Normal source errors finish as failed jobs and require an explicit new query; no blind access-gate retry. Health and request events feed the live console. GET retries can create a second capture; do not count it as independent corroboration. There is no cross-query response cache in this version; raw blobs deduplicate by hash.

Run `.venv/bin/python -m pytest -q`. The common suite checks admission bounds, DNS/redirect refusal, source isolation, durable claims, provenance tampering and authentication. Live source smoke outcomes are recorded separately in `docs/VERIFICATION.md`; passing unit checks does not establish that this provider currently responds.
