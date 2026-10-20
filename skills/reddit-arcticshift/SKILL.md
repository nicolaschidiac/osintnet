---
name: reddit-arcticshift
description: Retrieve bounded public Reddit posts and their thread comments through Arctic Shift for source-backed discussion analysis.
---

# Reddit threads through Arctic Shift

First-party contract: https://github.com/ArthurHeitmann/arctic_shift/blob/master/api/README.md, inspected 2026-10-19. Base API: https://arctic-shift.photon-reddit.com. No uptime guarantee. No credential or paid data request is used.

Use `source_query` with adapter `arcticshift`. Supply `{"mode":"posts","ids":["knownpublicid"]}` for at most 20 exact post IDs, or `{"mode":"comments","post_id":"knownpublicid","limit":100}` for a bounded tree. Find relevant public thread URLs before retrieval. No user-profile, cross-user interaction, author-history, or sensitive-affiliation lookup is implemented. Do not turn this into a dossier of commenters.

One GET per job, at least three seconds between calls, eight MB maximum, and the common hourly job limit. Enable explicitly. Preserve original response, request URL, capture timestamp, hash and parser. Tree responses may contain collapsed branches; do not claim all comments or all viewpoints were captured. No automatic older-page expansion or deleted-content recovery is implemented. Stop on access/rate errors; never bypass restrictions.

Posts, praise and criticism are statements by their authors, not verification of charity conduct. Preserve context and competing positions. An ad impression report can corroborate that someone reported an ad; it does not reveal private targeting or establish fraud, synthetic authorship, paid defenders, or coordination. Use timestamps and traceable source IDs for any pattern analysis; do not infer bots from persistence or positive sentiment. Retain material only as allowed by source terms; do not republish a bulk archive by default.

Outputs use the common durable job/capture contract; inspect via `evidence_record`, then source-scoped search. No cross-query HTTP response cache exists; blobs deduplicate. Source health comes from real request outcomes. Run the common security/isolation tests and adapter-bound tests; a live receipt is distinct from passing unit tests.
