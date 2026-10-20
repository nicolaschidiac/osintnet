# Candidate data APIs, MCP servers and data registries — research inventory
Last preflight 2026-10-19. **Candidates, not installed adapters.** Check availability, auth, license, API terms, rate limits, maintenance, architecture and arm64 compatibility before choosing. Prefer one canonical adapter per distinct capability; do not install a bundle blindly.

## Top-priority authoritative primary records
- IRS TEOS: https://www.irs.gov/charities-non-profits/tax-exempt-organization-search ; exemptions, determination letters, Pub 78, revocations, Forms 990/990-N.
- IRS public XML/bulk: https://www.irs.gov/charities-non-profits/public-disclosure-datasets-and-downloads ; supports annual filings with schedules and audited source lineage.
- ProPublica REST API v2: https://projects.propublica.org/nonprofits/api/ ; IRS-backed nonprofit identity and financials; may be directly wrapped rather than installing an unreliable unofficial MCP.
- NY AG charities registry: https://charities-search.ag.ny.gov/RegistrySearch ; annual reports, fundraiser filings, exemptions; browser verification gates are not bypassable.
- NY DOS corporations inquiry: https://apps.dos.ny.gov/publicInquiry/ ; official entity status, dates, registered agent and process address; distinguish from beneficial owners.
- CourtListener official MCP: https://mcp.courtlistener.com/ ; check OAuth and official scope; optional Vaquill fork https://github.com/Vaquill-AI/courtlistener-mcp adds eCFR and alternative self-hosting.
- NYC Databook: docs https://databook.nyc/mcp ; **actual endpoint** https://api.databook.nyc/mcp ; NYC civic records including contracting and people/entities; compare with NYC Open Data Socrata source records.
- NYC property records: https://www.nyc.gov/site/finance/property/acris.page ; use only to validate commercial premise and ownership, not as a dossier of unrelated residents.
- NYC Open Data: https://opendata.cityofnewyork.us/ ; procurement, buildings, tax and regulatory datasets as relevant; reconcile differing address spellings.
- Federal awards: https://www.usaspending.gov/ ; USAspending public API, and https://sam.gov/ for official contractor/award checks where relevant.
- State charity registration requirements: https://ag.ny.gov/resources/government-organizations/charities-nonprofits-fundraisers/charities-registration ; religious exemptions and other lawful reasons for missing data.

## Geographic and corporate attribution
- OpenStreetMap/Overpass/Nominatim: read official usage rules; use self-hosted extract if significant load. Evaluate requested `mcp-server-openstreetmap` implementation and maintained alternatives.
- Google Places Nearby Search (new): https://developers.google.com/maps/documentation/places/web-service/nearby-search ; use tiled/category coverage, pagination and source limits; no promise of every business in one mile.
- HasData remote MCP: https://mcp.hasdata.com/mcp ; verify authorization, pricing, results accuracy and lawful use. Google and OSM provide **listings**, not a complete roster of legal owners.
- OpenCorporates, NY DOS, SEC EDGAR (when applicable), USPTO: entity relationships based on explicit records. CompanyScope https://github.com/Stewyboy1990/companyscope-mcp was archived 2026-04-25; audit and compare to direct APIs.

## Internet graph and content acquisition
- Website respectful crawl via Playwright/Crawlee/Scrapy/Firecrawl/Exa as appropriate; archive original HTML/PDF/assets; robots/ToS compliance, rate limiting.
- Common Crawl / Internet Archive CDX / official Common Crawl index, public RDAP, passive DNS, Certificate Transparency, public DNS histories, sitemap/link graph and page change analysis.
- CrawlGraph MCP https://github.com/pucilpet/crawlgraph-mcp ; API key is **not** among supplied credentials; quarterly snapshot and rate/paid-tier limitations.
- Reddit via existing Arctic Shift MCP when healthy or its documented public REST API under acceptable use; archived comments may be incomplete/removed; no fabricated deleted content.
- Google Ads Transparency Center and Meta Ad Library for published ad creatives where searchable; platform placement/targeting may remain unknowable.
- **New ad-intelligence priority:** see [AD_INTELLIGENCE.md](AD_INTELLIGENCE.md) for verified MCP candidates, the distinction between Google public-ad libraries versus authorized-account Google Ads MCP, region filter limitations and a first lookup plan for `ummafoundation.org`.

## Passive cyber/intelligence and optional bundles
- Existing Shodan MCP user-reported at https://shodan.ziopsyop.tech on ORA3; discover/auth/test without breaking it or exposing keys.
- ZoomEye https://github.com/zoomeye-ai/mcp_zoomeye ; key must be validated *independently*, do not assume it is the same as a Shodan key.
- https://mcpmarket.com/server/awesome-osint ; https://github.com/frishtik/osint-tools-mcp-server ; https://github.com/SOsintOps/claudii-exploratores : audit maintenance, permissions, licenses and overlap before adding.
- Network data used passively on external domains; no unauthorized active attacks, exploits or scans.

## Telemetry, memory, orchestration
- LangSmith pricing https://www.langchain.com/pricing ; traces, evaluations, experiment datasets; current pricing also lists LLM Gateway usage via its own credits. **Do not assume a $100 grant pays model inference**. Verify billing credits, scopes and meter before making requests; cap spend.
- LangSmith MCP https://github.com/langchain-ai/langsmith-mcp-server ; **archived 2026-08-14**. Evaluate read-only support or build maintained internal adapter; do not send raw secrets or confidential PII into traces.
- ROTOXY agent workspace, LightSprint accounts/slots, Cloudflare AI, Bedrock, Oracle workers: discover capabilities, quotas and permissions at runtime before estimating dispatch.