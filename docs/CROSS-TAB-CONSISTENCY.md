# Cross-tab consistency and assignment avatars

Implemented 16 October 2026. Summary, Goal Hierarchy and Hygiene share the approved contract and distinguish any newer proposal.

## Display contract

| Concept | Summary / Hierarchy | Hygiene |
|---|---|---|
| Metric-only | Current measured target attainment; no required delivery gate | Metrics and cadence checked; no fabricated delivery requirement |
| Delivery-based | Effort-weighted accepted checkpoints | Delivery, evidence and reviewer actions use the approved version |
| Combined (including legacy `outcome`) | Outcome attainment and accepted delivery shown separately; both required | Proposed success basis shown when reviewing or completing setup |
| Proposal | Approved values stay in force; a separate version/state label exposes draft, pending or returned revisions | Owner sees setup/returned items; approver sees decision actions; submitted owner sees a waiting item |
| Resources | Unique contributor avatars and expandable version-specific commitments, dates, month and linked deliverable | Review uses the submitted version; setup checks use the latest proposal. Monthly overcommitment is flagged without counting the replaced baseline twice |
| History | Frozen allocations and recorded plan states compared alongside existing progress/ETA changes | Decisions are retained in history |

No new arithmetic substitutes delivery for outcomes. Allocation percentages are never progress weights. Resources on a workstream remain its own commitments; support does not add progress weight. Lifecycle filtering can find a submitted or returned revision even when the approved goal remains achieved.

New snapshots include approvals. Older snapshots without approval records show the decision as not recorded. History does not reconstruct missing decisions from current data, and later approvals do not rewrite saved snapshots.

## Avatars

Every person receives a deterministic, generic illustrated avatar generated locally. The illustration is not a likeness and does not infer personal traits. Owner/assignee/reviewer/resource identity remains in adjacent text; overlapping stacks expose names and deduplicate repeated people.

The shared component accepts a bounded embedded PNG/JPEG/WebP `photo_data_url` from a scoped person record. External URLs and user-supplied SVG are rejected; image failure falls back to initials. The default SVG is generated entirely from application constants. No third-party avatar service, new public bucket, or access expansion is involved.

The current Workday import contains no photos. A profile editor, avatar selection persistence and Workday photo synchronization are later work; they are not claimed as implemented by this presentation change.

## Verification

- UI regression suites and typecheck pass, including shared rendering for all success types, approved/proposed version isolation, resource deduplication, lifecycle filters, avatar escaping and unsafe-source rejection.
- 34 targeted Python tests pass for registration, persistence, scoped records, goal types, outcome calculation and snapshot capture.
- Connected browser journey: revise an approved combined goal; change a linked monthly allocation from 10% to 15%; submit; observe owner waiting state; return with reason; revise/resubmit; approve with designated approver.
- Summary retained the approved allocation and both progress values during proposal. Approval switched to the new contract. New metric observation reached the target without automatically completing delivery. Private written evidence was uploaded, downloaded/inspected and accepted by the reviewer; both completion gates then reached 100%.
- Summary Cards/Table/Board and Hierarchy map/list show the same saved contract. Centered map, expansion and read-size controls remained usable.
- A real saved snapshot retained the prior allocation and decisions; comparison exposed resource and approval changes without changing the score formula.
- A question was assigned, resolved by its assignee, and removed from the action queue. A check-in was saved and cleared its due item. Independent API reload confirmed persistence.
- An unrelated leader's browser did not display the test goal. Server denied foreign revision and private evidence download with 403.
- Desktop three-column cards and phone-width reflow inspected. Keyboard disclosure tested. No browser runtime errors observed. This is focused verification, not a full WCAG conformance audit or organization-scale performance certification.

Only clearly identified workshop goal activity was changed. No workforce source records, authentication model, private storage access rules or production goals were changed.
