# Goal Charter · implemented 16 October 2026

Approved goal links now open a read-only Charter by default. An explicit `/charter` route is available. Unapproved goals still open setup; explicit `/setup` links inspect or edit the latest proposal. Summary cards/table/board, hierarchy map/list, team detail and workstream links use this shared default.

The Charter reads only the existing server-scoped projection. It uses the active approved version for purpose, owner, success basis, dates, measures, effort and resources. A newer proposed version is called out separately and cannot change the approved presentation before approval. No new data access, schema migration or permission grants were introduced.

## Contents and behavior

- Purpose, authorized parent context, optional pillar, priority and approver.
- Delivery or measured-outcome progress from the existing authoritative calculations. Measures include baseline, actual, target, units, weight, source, date and freshness. Unknown is not zero. Outcome and accepted delivery are separate.
- Immediate workstreams and expandable terminal deliverables with owner, due date, effort, definition of done and checkpoint decisions.
- ETA provenance, risk-causing deliverables, next delivery, latest check-in and pending approvals/evidence/questions.
- Expandable approved monthly commitments, private evidence downloads, decisions, support requests and operational KPIs.
- Check-in, propose change, continue proposal, reviewer-only approval/evidence actions, and version history use existing server commands.

Current resource records are still goal-version/month allocations. The Charter labels that limitation explicitly; it does not invent deliverable-level attribution. Existing outcome completion rules are unchanged. Metric-only/combined contracts and the wider registration redesign remain separate planned work.

## Connected verification

A labeled synthetic workshop goal was used. No imported workforce records were modified.

1. Summary opened approved v1 in the Charter; an unfinished goal opened setup.
2. Check-in saved and appeared in the Charter after reload.
3. Propose change created draft v2. Saving its revised description left v1's description and 100% approved delivery unchanged on the Charter.
4. The owner submitted v2. The designated approver opened its exact contract from the Charter and approved it. Reload showed approved v2 and its revised description.
5. Existing revision rules create new checkpoint identities. The v2 Charter correctly showed zero accepted delivery until fresh v2 evidence was reviewed; it did not borrow v1 acceptance.
6. A synthetic text file was uploaded to the private bucket, downloaded from the Charter and byte-compared with its source. Independent acceptance in Hygiene changed the Charter's delivery roll-up to 100%.
7. A measured-outcome parent showed baseline 72%, actual 84%, target 95%, 52.2% attainment and a separate accepted-delivery value. No outcome reading was fabricated or modified.
8. An unrelated leader opening the same Charter URL saw “Goal not available.” A fresh server projection excluded it and a direct check-in attempt returned 403.
9. Map pointer and keyboard links, support-context dialog, resource/evidence disclosures and section navigation were exercised. At 320 CSS pixels, collapsed and expanded deliverables caused no page-level horizontal overflow. Desktop layout was inspected at 1440px. Dialog close restored focus to the Charter trigger after a save.
10. Browser console showed no errors. Build/typecheck, all UI suites including Charter isolation/authority tests, and 50 Python tests passed.

These are targeted checks, not a complete WCAG conformance or performance certification. Authentication remains the trusted local persona simulation.

## Defects found during testing

The fixed workshop date caused check-ins saved after a real midnight to sort behind earlier updates. New check-ins now retain actual UTC `recorded_at` separately and advance the legacy scenario `created_at` ordering key monotonically per goal. Existing cadence and frozen snapshot semantics remain intact; prior records are not rewritten. A regression test covers clock rollover. Production should use real audit timestamps and a distinct effective/scenario date throughout.

A wrapped map title had a non-clickable gap between text lines. Its anchor now occupies the full title block, verified with pointer and keyboard navigation.
