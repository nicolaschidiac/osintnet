# Advertising intelligence research addendum — 2026-10-19

## Purpose and case relevance
A mobile YouTube Gaza-aid ad was reportedly shown while the user's Tailscale connection exited through a Jerusalem Oracle VM. The first question is to identify the exact creative, advertiser identity, verified payor, dates, landing URL and countries where any matched creative has been listed. **A country filter or ad impression must not be misrepresented as the advertiser's private geo-targeting configuration.** A nonprofit may use lawful multilingual or regionally broad campaigns.

## Recommended Google/YouTube MCP candidate (HIGH PRIORITY)
- https://github.com/block-town/google-ads-transparency-mcp — MIT, Python/uvx, unofficial Google Ads Transparency Center scraper, currently documented domain/name search, ad listing, individual creative detail, active ad comparisons, images and YouTube video frame capture via optional yt-dlp/ffmpeg. A country filter accepts ISO alpha-2 values, including `IL` for Israel, `US` and `anywhere`.
- No Google Ads account or API key required according to maintainers. **This is not a Google-supported public API**; code accesses unofficial internal RPC endpoints and may be rate limited or change without notice. Validate terms, README, licensing, outbound requests, security, use of downloaded video, availability, and safe low-rate smoke test. Do not bypass CAPTCHAs or access controls; stop on throttling.
- Baseline free alternative to evaluate for overlap: https://github.com/lionkiii/gads-transparency-mcp (Node/Puppeteer; smaller/newer project). Choose one, not both.
- Evaluate pay-per-use hosted options if free collectors are unreliable: https://github.com/proxy-intell/google-ads-library-mcp ; https://github.com/at-dan/ad-library-mcp (ScrapeCreators paid API; claims multi-platform public data). Explicit cost review and user spending limits.
- Official Google Ads MCP https://github.com/googleads/google-ads-mcp is for authorized account customer data, NOT a general public competitor-ad transparency index.

## Official reference surfaces and other networks
- Google Ads Transparency Center: https://adstransparency.google.com/ ; Google confirms ads served on Search and YouTube can be discovered here: https://support.google.com/adspolicy/answer/9703665 .
- Google's My Ad Center https://myadcenter.google.com/ may show a subset of recently viewed ads if the user is signed in; official instructions for locating previously seen ads: https://support.google.com/google-ads/answer/7660847 .
- If ad reappears, on YouTube choose ad Info/More > My Ad Center > About this advertiser to identify verified payer, and optionally Report ad > Something else > Copy Ad ID without completing report: https://support.google.com/admanager/answer/6161675 .
- Meta Ad Library browser: https://www.facebook.com/ads/library/ ; official API: https://www.facebook.com/ads/library/api/ . API worldwide archive includes ads categorized as political/social issues (and UK/EU ads more broadly), typically requires identity verification, with approximate spend/impressions and reach demographic data only in applicable disclosure classes. Charitable Gaza fundraising may or may not fall within Meta's issue-ad classification.
- Google political/election-ads public BigQuery dataset is official but narrowly covers political ads and is likely **not applicable** to a general humanitarian donation creative unless covered by the program: https://cloud.google.com/blog/topics/developers-practitioners/how-get-started-political-ads-transparency-report-dataset .
- TikTok Commercial Content API: https://developers.tiktok.com/products/commercial-content-api ; eligibility/geography/approvals apply, initial ad library EU-focused. Optional secondary source only.

## Concrete investigation query recipe (no assertion data exists)
1. Search advertiser by `ummafoundation.org`, then by `Umma Foundation`, `Our Umma`, `Our Ummah`, and any verified official alias. Preserve exact matches and advertiser IDs rather than collapsing lookalikes.
2. Query matching Google advertiser creative records for `anywhere`, `IL`, `US`, `LB`; record source query/time, status, format, advertiser ID, creative ID, last shown date, source URLs and source interpretation. Compare country appearance filters, **not hidden targeting selections**.
3. Retrieve matching videos and landing domains if permitted; store hashes, original references, transcript/translation and a truthful synthetic-media assessment, avoiding unsupported 'definitely AI' detection.
4. Corroborate sponsor identity in Google's About this advertiser rather than assuming the brand shown is the legal advertiser; check if fundraiser landing domain differs from disclosed sponsor.
5. Repeat separately for Meta political/issue and active-ad libraries, and if warranted TikTok. Absence from an index is not proof no ad ran.
6. If a copy of the original YouTube ad or its ad ID can be recovered from My Ad Center, match exactly to creative; otherwise clearly flag `original ad unverified`.
7. Store a dated, normalized cross-platform source ledger with advertiser, payer where explicitly disclosed, target country filter, publisher platform, dates and any spend/impression metadata with disclosure restrictions. Distinguish region served versus selected geo-targeting.
8. Compare creative claims with nonprofit disclosures, but **not** purported faith, nationality or neighborhood of advertiser without actual corporate evidence.

## MCP adapter SKILL acceptance
Implement `skills/ad-transparency/SKILL.md`: precise tool spec; authorized public-source scope; source citation and timestamps; a secure server-side wrapper for one chosen Google collector; optional official Meta API; rate limiting, backoff, no CAPTCHA circumvention; credential placeholders only; tests for source data vs inferred labels; immutable creative snapshots with terms-compliant retention; alert and quality metrics. Allow adapter disable/restart without interrupting other MCPs. Export normalized events to OSINTNET graph/report and live topology.