---
name: courtlistener
description: Search public RECAP records with precise organization aliases and preserve query-specific coverage limitations.
---

Use the official public UI and documentation at https://www.courtlistener.com/ and https://wiki.free.law/c/courtlistener/help/api/rest/v4/search . The selected hosted MCP/OAuth integration remains pending; a browser search is not an authenticated API test. Official API examples require a token. No PACER purchases, private credentials or scraping gates are authorized by this skill.

Inputs: verified legal names/aliases and desired data type. RECAP type `r` searches federal cases/filings; it is not a state-court or complete PACER search. Use exact quoted organization names with corporate suffixes, inspect entity context, and exclude generic phrase matches. A document's allegation is not a finding or proof that a similarly named subject is the target.

Schema: query/type/filters, source URL, UTC observed_at, displayed count, candidate docket/court/filing dates, identity match, document-level citations, case posture and limitations. Preserve originals when materially relevant; retain a clean rendered observation for a bounded zero result. Do not build unrelated-person or religious-association dossiers.

Limit to three organization aliases, two result pages and five material documents unless expanded explicitly. Stop on fees, access/rate failures or verification gates. Follow the provider's cache guidance; no polling monitor is installed.

Validation: the 2026-10-19 quoted organization-name query returned zero RECAP results. A broader generic phrase query produced unrelated text matches and was excluded. Neither result establishes absence of litigation; separately address unindexed federal filings and relevant state systems.
