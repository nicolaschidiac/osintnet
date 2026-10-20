---
name: case-evidence
description: Record and search provenance-aware case assertions, financial observations and documented relationships in OSINTNET.
---

# Case evidence

Use `osintnet.store.Store` for local operator imports; authenticated MCP tools expose search and capture metadata. Records stay private by default. Never put the runtime database, operator key or raw case corpus in Git.

Capture originals before deriving claims. `Store.capture` creates a SHA-256 blob and chained metadata row; title/text and parser are separate searchable derivatives. `Store.verify` rechecks all blobs and the metadata chain. SQLite triggers reject changes/deletions to evidence, text, assertions, financial observations, relationships and events. These controls are tamper evident; a privileged host administrator can still modify storage. Back up with SQLite's backup API and immutable blobs together.

Use assertion states reported, verified, inferred, contradicted or unknown. Attach capture ID, exact XPath/page/paragraph locator and limitations. Corrections are new assertions with an explicit prior assertion ID in the locator, never silent edits. Relationship edges require source/target entity IDs, typed relationship, capture ID, status and limitations. Shared surnames, hosts, addresses or nearby premises do not establish ownership, kinship, religion or wrongdoing.

Financial rows retain year, tax period, nullable fields, exact source capture and basis. Distinguish an IRS original, a secondary renderer and a summary extract. Reconcile assets minus liabilities and revenue minus expenses, then test reporting-period and classification explanations; preserve nulls instead of zero. Promotion to a finding requires independent reproduction and competent evidence.

Search is scoped to a supplied case ID and returns original URLs and capture IDs; quoted FTS input does not accept search operators. Current role access spans the local workspace's cases; deploy separate instances if separate case permissions are required.

Verify with `tests/test_store.py`. Test archive restore and hash verification before deployment. Do not export raw evidence to hosted model traces or assume a passed integrity check verifies an underlying statement.
