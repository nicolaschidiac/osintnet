---
name: finance-990
description: Extract and reconcile original IRS Form 990 XML with exact field paths, reporting periods and qualified financial interpretation.
---

# Form 990 financial comparison

Use `osintnet.filings.extract_990(raw)` only on captured original XML with a known IRS source. It verifies the filer EIN and tax year, rejects non-990 forms and XML entities, preserves missing amounts as null, and returns named field paths, officer disclosures, schedules and explicit arithmetic discrepancies. An IRS renderer or ProPublica extract is a distinct secondary representation, not a substitute source label.

Locate originals using the official annual index at https://www.irs.gov/charities-non-profits/form-990-series-downloads. Publication year differs from tax year. If only a large public ZIP is available, `scripts/irs_zip_extract.py` can retrieve a single exact object member using verified HTTP byte ranges, a 32 MB total transfer cap, an eight MB uncompressed member cap and ZIP CRC validation. It refuses a server that ignores Range. Keep range receipts, original XML hash, archive URL/member and matched index row. No credentials, payment or access-gate circumvention is involved.

Reconcile revenue minus expenses, assets minus liabilities, and functional expense columns. Preserve discrepancies instead of adjusting a filed number. Program-services expenses may include advertising; a high program ratio does not by itself establish the percentage received by beneficiaries. Advertising size, zero salaries/fundraising, government-grant classification or a missing schedule is a question requiring definitions and source workpapers, not a fraud finding.

Read the instructions for the actual tax year before interpreting a field. Compare the exact line mapping and applicable thresholds. Separate current campaign claims from an older annual return. Match entity identifiers, accounting basis, amendments, restricted funds and reporting periods. Public Form 990 data cannot reconstruct private donor lists or bank transactions.

Store every annual observation with source capture ID and basis. Filed names/roles are professional-role disclosures; do not infer kinship from surnames or treat a historical role as current. Independent review should reproduce formulas and test the strongest benign explanation alongside material questions.

Run `tests/test_filings.py` plus the evidence-ledger tests. Verify a known original against its official archive and secondary rendering. Unit success does not validate whether the filer’s underlying transactions occurred as reported.
