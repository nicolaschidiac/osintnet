---
name: propublica
description: Query IRS-derived nonprofit identity and annual filing summaries through ProPublica.
---

# propublica

Source: https://projects.propublica.org/nonprofits/api/. Contract reviewed 2026-10-19; provider terms and limits can change.

Use the OSINTNET `source_query` MCP tool or authenticated `POST /api/jobs`. Set `adapter` to `propublica`, choose a case ID, supply `parameters` such as `{"ein":"123456789"}`, and a unique idempotency key. A repeated key with different inputs is rejected. Enable this node explicitly before dispatch; integration health remains unknown until a real successful call.

## Bounds and authorization

One GET per query; at least 2 seconds between calls; 100 admitted jobs/hour; 8 MB. No credential. EIN must contain exactly nine digits. The organization endpoint returns all indexed filings; search pagination is not implemented.

Only public, authorized records are in scope. Stop on authentication gates, CAPTCHA, 403 or 429; do not rotate endpoints or identities to work around them. No paid inference or paid data calls are implemented by this adapter.

## Evidence and interpretation

Secondary IRS-derived extract. Record tax period, form type and update date; do not call it original IRS XML or infer wrongdoing from financial growth.

Output is a durable job ID/state followed by capture ID, byte count and latency, or a bounded error code. Retrieve provenance through `evidence_record(capture_id)` and search with `evidence_search(case_id, query)`. Raw SHA-256 blobs and chained capture metadata remain separate from derived text. Store issuer, URL, final URL, capture time, hash, parser and precise locator for every downstream assertion. Preserve conflicting and favorable evidence. Source freshness is the capture time, not a claim about when an underlying event occurred.

## Failure and validation

Disabled nodes cannot dispatch new requests; queued work waits. Each job has a lease and bounded GET retries after process failure. Normal source errors finish as failed jobs and require an explicit new query; no blind access-gate retry. Health and request events feed the live console. GET retries can create a second capture; do not count it as independent corroboration. There is no cross-query response cache in this version; raw blobs deduplicate by hash.

Run `.venv/bin/python -m pytest -q`. The common suite checks admission bounds, DNS/redirect refusal, source isolation, durable claims, provenance tampering and authentication. Live source smoke outcomes are recorded separately in `docs/VERIFICATION.md`; passing unit checks does not establish that this provider currently responds.
