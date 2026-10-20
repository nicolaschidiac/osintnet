---
name: rotoxy-research
description: Dispatch bounded independent text research through an existing ROTOXY LightSprint workspace and validate durable receipts, cost observations and final artifacts.
---

Use the existing encrypted local ROTOXY runtime. Never print, copy into prompts, commit or pass bearer tokens on the command line. The operator script resolves tokens internally through StateStore and the existing LightSprint MCP client. Do not install another provider, choose an OAuth identity, or silently consume native subagent/subscription quota.

Supply a JSON array of `[lane, brief]` entries, at most four distinct available sessions. Lane names contain only lowercase letters, digits and hyphens. Keep case details in the case config, outside the platform core. Example:

```sh
node scripts/rotoxy-research.mjs dispatch cases/umma/discovery-briefs.json
node scripts/rotoxy-research.mjs status cases/umma/discovery-briefs.json
```

Use `OSINTNET_DISPATCH_DIR` for a separate private receipt lane and `ROTOXY_RUNTIME` only for an existing trusted installation. Receipts prevent blind redispatch. Require idle/readiness before sending. Each brief has a scope owner, no-edit/no-contact/no-purchase limits, source contract, output limit, prompt budget, lease and completion marker. Current script requests at most USD 0.50 existing prepaid credits and eight source calls per brief; these are prompt/supervisor limits, not an atomic provider billing cap.

Inspect status, heartbeat/turn timestamps, provider-reported session cost delta, failure and artifacts. Match completion markers only to assistant turns starting after dispatch. A connected tool, accepted prompt or old completion marker does not prove the new assignment completed. Stop/cancel on observed budget/lease depletion, but reconcile any ambiguous dispatch before retrying. Do not infer live account balance or slot denominator from a successful session.

Validate every report against primary source evidence and keep inference uncertainty. Do not send credentials, private beneficiary details or unnecessary personal records to remote research. Public-source text only in the demonstrated workflow. Validation: four architecture/source discovery briefs, two opposing financial reviews and bounded final-text QA used existing sessions; receipts and artifacts are private. The core dashboard's native ROTOXY control node remains pending until a production adapter contract exists.
