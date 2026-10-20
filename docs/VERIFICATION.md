# Verification record — 2026-10-19

## Completed checks

- Current 27 Python checks pass: concurrency and unique claims, idempotency conflicts, stale-lease ownership, dependencies/master pause, adapter isolation, append-only/tamper detection, case-scoped FTS, SSRF/redirect rejection, adapter bounds, authentication/roles/origin/Host checks, cookie logout and MCP initialization/tool inventory. WGS84 one-mile boundary, privacy-scoped Reddit adapter bounds, repeat credential-free export, fenced restore, atomic admission ceilings, dedicated adapter claims, real subprocess heartbeat/restart isolation and admin-only restart requests are included.
- JavaScript syntax and Git whitespace checks pass for the initial console.
- Official MCP SDK client connected over real local HTTP, listed all four tools and called `network_status` without an MCP error. This proves the native SDK/transport path, not enrollment in ChatGPT Desktop.
- Real ProPublica source query completed through the authenticated job API: 5,521 bytes, measured approximately 801 ms, immutable capture and persisted request/health/completion events.
- The original combined Overpass query timed out; an explicitly selected OSM-listed alternative returned HTTP 500 for the combined query. A smaller shop-only query subsequently returned HTTP 200. Provider failures remain visible; no complete census or connected-state invention.
- Bounded website collection archived 223 routes (222 sitemap entries plus homepage). Raw originals and extracted text are private. Page capture coverage is distinct from claim-review coverage.
- Initial private import: 228 captures, 224 searchable documents; all blob hashes and metadata-chain links verified. Subsequent live calls/imports increase these counts.
- Full official IRS annual index files for publication years 2023–2026 were searched for the exact EIN. Matches identify 2021–2023 returns; no match in the downloaded 2025/2026 indexes. This bounded index result does not prove nonfiling or a delinquency.
- Original 2021, 2022 and 2023 XML returns were extracted from official IRS ZIPs using verified HTTP byte ranges. Member CRC, SHA-256, exact archive member, index row and source URL are retained. Direct ProPublica PDF/XML downloads returned 403; no access control was bypassed.
- ORA3/5/6/7 SSH and container/model inventories checked. Existing services preserved.
- ORA6 ARM64 Docker build and initial health succeeded. Gateway memory observed around 66.28 MiB of a 768 MiB limit, CPU about 0.53% at the sampled idle point.
- ORA6 local synthetic scheduler benchmark: 200 job admissions in 0.1567 s (~1,276/s); 32 concurrent claims were all unique. SQLite backup `integrity_check` returned `ok`. This is a short synthetic metadata benchmark, not a sustained acquisition-load result.
- Fourteen selected skills pass the bundled static validator. Manual ad/court browser workflows were exercised; NY AG verification and NY DOS portal failure are explicitly incomplete source outcomes. Automated ad and CourtListener MCP integrations remain pending.

## Separate pending acceptance layers

Authenticated in-app browser sign-in, source canvas, source disable with another source preserved, financial tables and dated role graph were exercised. A real Chromium origin rejection exposed the no-referrer form issue; same-origin referrer policy fixed login while null/untrusted origins remain blocked. Private screenshots exist. The final desktop layout, source controls, full-text search and filtered map were exercised in Chromium. Selecting a near-center map point opens the correct source capture; a marker overlap bug was corrected and keyboard activation was added. Screenshots are retained privately. A 390px browser check exposed an invalid responsive CSS selector; it was corrected, and a readable source picker now opens the same inspector/controls on narrow screens. No horizontal page overflow was observed at 390px; the 1440px layout was also rendered. Map keyboard activation itself has not been independently exercised.

Cloudflare owner-only reusable policy, Access app, connected dedicated tunnel and scoped DNS route are live. Unauthenticated edge API returns 302; direct origin without JWT returns 401. A short-lived application-scoped service token without an app key reaches the app and returns authentication_required/401. With both credentials, the final deployed application revision `f6df459` returned the 260-capture case, 622 places and report capture 260. MCP initialize, tools/list and network_status succeeded. All seven dedicated workers were online; a ProPublica worker restart changed its owner while the other six owners stayed unchanged. Isolated restore matched all 250 initial hashes and ledger tip, integrity ok; the subsequent guarded 260-capture restore also verified every blob and chain link while preserving destination authentication. Initial default urllib user agent returned 403; an explicit OSINTNET agent succeeded. No credential is in code, screenshots or this record.

Paid/credentialed integrations, automated live account-wide quota readers, every individual source's production contract, desktop enrollment, original advertising creative/targeting, state-registry originals, complete public-court coverage, beneficiary/project corroboration and independent forensic/legal review remain distinct from the checks above. The case remains open.

## Additional case and research receipts

The local ledger verifies 260 captures. It includes three original IRS returns, the BMF exact-EIN match, year-specific IRS instructions, the full 223-route website capture, a 100-row CDX index and a 2011 replay with a different EIN, two bounded empty USAspending autocomplete responses, scoped Reddit records, Google advertiser/creative observations, a bounded zero-result RECAP search and a NY DOS error observation. These source outcomes have precise limits; they are not a full registry/court clearance or an exhaustive map/advertising inventory.

Two opposing delegated financial reviews and one final text QA were reviewed. Final text QA cost delta was about USD 0.0173, as reported by its session. The requested final marker was absent, so completion was accepted only after idle state and the actual new assistant artifact were inspected. It found one authorship-inference wording issue; the report was corrected by adding a new ledger version. No fresh primary-source verification by that text reviewer is claimed.

## Final production acceptance

The receipt at 2026-10-19 08:56:57 UTC (11:56:57 Beirut) records one real query per adapter in a separate acceptance case:

| Adapter | Outcome | Captured bytes | Measured request latency |
| --- | --- | ---: | ---: |
| ProPublica | Complete | 5,521 | 437 ms |
| Public web | Complete | 39,461 | 163 ms |
| IRS records | Complete | 1,225,670 | 292 ms |
| NYC Socrata | Complete, empty response | 3 | 399 ms |
| Overpass | Failed, HTTP 500 | — | — |
| Wayback CDX | Complete | 16,520 | 1,825 ms |
| Arctic Shift | Complete | 1,974 | 1,863 ms |

The Overpass failure is retained; the earlier 622-place map is sourced from a successful acquisition, not this failed request. The NYC result is only the bounded query result, not proof that no business exists at the address. No provider was silently rotated. All jobs finished in one attempt. Master acquisition was paused and all seven sources disabled afterward. Six new acceptance captures bring the remote ledger to 266; the case itself remains 260 captures. All 266 hashes/chain entries verified, tip `97423aa5cc75b3af00443e0a7a8a7ac1a17b0ba00d1e933c1ce768f6556fd995`.

A later resumption check on 2026-10-19 found the gateway and seven workers healthy, unrelated Open WebUI/Ollama containers still running, absent/forged origin JWTs rejected with 401, and unauthenticated edge access redirected with 302. The 27 Python tests passed again. Source-process health does not imply provider availability. Idle samples were about 66 MiB for the gateway and 21 MiB per worker, not sustained-load measurements.

Authenticated local browser rendering and authenticated remote REST/MCP are separate proofs. The owner completed Cloudflare Access sign-in, then the production application key-file login succeeded in Chromium. The destination key was retrieved into a mode-0600 local file at the owner's request; its value was never displayed. Temporary validation-service entitlement expires 2026-10-20 07:05:21 UTC; it does not replace the owner policy or the app key.

A fresh Git clone of `f516c1c`, with a new virtual environment and the pinned requirements, passed all 27 tests in 12.03 seconds. No private files are tracked or cloned; the test import generated an empty runtime with zero captures and new instance authentication. Subsequent changes are limited to responsive HTML/CSS/JavaScript and handoff documentation. JavaScript syntax and Git whitespace checks pass. A targeted high-precision secret-pattern scan found no matches in 77 tracked files; this is a bounded scan, not a guarantee against every secret format.

## Responsive follow-up and current browser boundary

The user reported poor narrow-screen layout and an unspecified server-error message during the release. The gateway restarted during deployment; subsequent container logs contained startup messages without an application traceback, authenticated API calls passed, and the ledger was unchanged. A transient release interruption is a plausible explanation, not a captured diagnosis of that exact message.

The narrow layout now presents readable source status cards and the source picker below 901px, instead of shrinking the entire canvas. The summary counts remain visible, and selecting a card opens the existing independent controls. This card layout was rendered and exercised locally at an observed 577px width without horizontal overflow. The earlier picker/CSS release was exercised at 390px and the production view at 710px. A later viewport override did not hold its requested 390px size; no final 390px card-layout claim is made. The wide canvas remains available above that breakpoint. Server 5xx responses now receive an actionable message; status polling continues, while submitted queries are not replayed automatically.

The NY AG page subsequently displayed “Verified ✓” with Search enabled. Submitting the exact-EIN search was then blocked by the desktop app reporting “Local browser use is disabled in Work settings.” No registry result was obtained. The same setting currently blocks the final production visual follow-up; server-side deployment checks remain possible. Re-enable local browser use to resume those two browser checks without changing credentials or registry search scope.

Final UI deployment receipt: gateway `06c8b4b` serves the responsive-card HTML/CSS/JavaScript through authenticated HTTPS; seven existing workers remain online; REST and MCP network_status pass; master and source controls remain paused/disabled. All 266 captures verify against the same tip, and the original case still has 260 captures. Only the gateway was recreated for this UI-only patch. Final production rendering remains unverified because browser control is disabled.

Key-file follow-up: Chrome reported a click followed by cancel with zero selected files during the user reproduction; the form had no key or status. The file reader itself passed an in-browser synthetic-file diagnostic. The updated login retains the filename, shows reading/ready/error/cancel feedback, prevents submission while reading and clears a stale key on invalid replacement. Chromium checks with synthetic valid/invalid files and cancellation passed; no real key contents were logged. This fixes silent feedback and selection ambiguity; it does not claim to repair a native chooser that fails to return a file.
