---
name: ny-ag-charities
description: Perform a gate-aware manual search of New York Attorney General charity registrations and annual reports with exact identity matching.
---

Source: https://charities-search.ag.ny.gov/RegistrySearch . No automated adapter or verification bypass is implemented. Prepare the EIN exactly; record query, filters, UTC time, displayed status and reviewed reporting years. Human verification requires user handoff. Do not treat the pre-search “No rows available” placeholder as a submitted negative result.

If a verified query returns records, match EIN, legal name and document year, download only material public reports, preserve original bytes/hash/URL and record the registry's review/publication lag. Missing results do not establish illegal non-registration: exemptions, alternate names and incomplete coverage need consideration. Do not submit FOIL requests, complaints or contacts without explicit authorization.

Schema: source, query EIN/name, filters, observed_at, submitted boolean, gate/error, matches with document URLs/years, verified identity fields, uncertainty. Limit to the supplied organization and five material report downloads per session, stopping on access/rate failures. No paid calls or keys.

Validation: the 2026-10-19 exact-EIN form was prepared, but verification remained required and Search disabled. Outcome is **blocked before search**, not no match. Once the user completes verification, submit the prepared query and verify the visible result before any registration assertion.
