---
name: places-osm
description: Collect a provider-attributed business and amenity directory within a bounded radius.
---

# places-osm

Source: https://wiki.openstreetmap.org/wiki/Overpass_API. Contract reviewed 2026-10-19; provider terms and limits can change.

Use the OSINTNET `source_query` MCP tool or authenticated `POST /api/jobs`. Set `adapter` to `overpass`, choose a case ID, supply `parameters` such as `{"latitude":40.7,"longitude":-73.9,"radius_m":1609.344}`, and a unique idempotency key. A repeated key with different inputs is rejected. Enable this node explicitly before dispatch; integration health remains unknown until a real successful call.

## Bounds and authorization

One GET query; at least 10 seconds; radius <=1609.344 metres; 10 MB; no automatic endpoint rotation. No credential. Retain OSM type/ID, categories, coordinates and capture. ODbL attribution and derivative database obligations apply. Geocoding is separately user-triggered under Nominatim policy.

Only public, authorized records are in scope. Stop on authentication gates, CAPTCHA, 403 or 429; do not rotate endpoints or identities to work around them. No paid inference or paid data calls are implemented by this adapter.

## Evidence and interpretation

OSM is incomplete and includes noncommercial amenities. A business centroid can differ from its footprint. Apply a geodesic final-distance check; proximity does not establish an organizational relationship or personal religion.

Output is a durable job ID/state followed by capture ID, byte count and latency, or a bounded error code. Retrieve provenance through `evidence_record(capture_id)` and search with `evidence_search(case_id, query)`. Raw SHA-256 blobs and chained capture metadata remain separate from derived text. Store issuer, URL, final URL, capture time, hash, parser and precise locator for every downstream assertion. Preserve conflicting and favorable evidence. Source freshness is the capture time, not a claim about when an underlying event occurred.

## Failure and validation

Disabled nodes cannot dispatch new requests; queued work waits. Each job has a lease and bounded GET retries after process failure. Normal source errors finish as failed jobs and require an explicit new query; no blind access-gate retry. Health and request events feed the live console. GET retries can create a second capture; do not count it as independent corroboration. There is no cross-query response cache in this version; raw blobs deduplicate by hash.

Run `.venv/bin/python -m pytest -q`. The common suite checks admission bounds, DNS/redirect refusal, source isolation, durable claims, provenance tampering and authentication. Live source smoke outcomes are recorded separately in `docs/VERIFICATION.md`; passing unit checks does not establish that this provider currently responds.

Default queries select `categories:["shop"]` after combined query failures. Operators may explicitly select a distinct subset of `shop`, `office`, `amenity`; no arbitrary tag/query injection is accepted. Record each category and failed lane as coverage metadata. A shop query is not a complete business census.
