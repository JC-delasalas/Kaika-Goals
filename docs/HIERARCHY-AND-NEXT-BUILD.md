# Kaika: hierarchy refinement and next build

16 October 2026. One accountable builder, JC, supported by AI. Workshop target: 27 October. This is an ordered delivery plan, not a promise that all production work fits before the workshop.

## Product decision

Keep three primary destinations. Summary answers “How are my commitments doing?” Goal Hierarchy answers “How does our work connect?” Hygiene answers “What needs my action?” Goal Charter and Registration remain contextual journeys; Team & allocation remains a supporting workspace. Do not add another Overview, standalone KPI tree, or generic AI chat tab.

The design principle is progressive disclosure over smaller text: show the current commitment, its health, progress and owner, then let the leader narrow or expand the surrounding work. Preserve the distinction between an observed outcome, accepted delivery, an approved plan and a forecast.

## Delivered in this refinement

- Search goals, workstreams, their owners and their attached deliverable titles.
- Intersect goal-owner, health, pillar and approval-state filters. Approval is separate from delivery health, including an approved goal with a pending revision.
- One-click Needs attention and Assigned to me, plus Clear filters and an honest no-results state.
- Keep authorized ancestors as context. Only matching goal branches and their attached deliverables survive the filter. Parent progress and resources still describe the complete approved plan.
- Six children per parent initially; choose three, six or twelve. Show more reveals the remaining branches; Expand all is explicit. Two levels restores shallow disclosure. No hidden goal is deleted or excluded from calculation.
- Share filters and disclosure between map and outline within each leader's session. Switching leaders cannot reuse another leader's filter options or tree. Reload starts a fresh view; saved hierarchy presets are not implemented.
- Move the canvas to the first matching goal after filtering. Retain centering, fit, zoom, native scroll and the linear hierarchy alternative.
- Cursor glide is opt-in and unavailable under reduced-motion preferences. Brief hover color feedback is the only added animation; keyboard actions and layout changes are immediate.

The filters use the existing server-scoped projection. They do not add a database endpoint, widen access, change records, or recompute success percentages from the filtered subset. The no-login leader switcher remains a trusted local demo control, not authentication.

## Design review

JC Design Intelligence, product/Operate polish. Sources: the existing app, approved screenshots and the meeting-derived PRD/build plan already prepared. This pass did not claim a new frame-by-frame video review or a fresh competitor study.

| Before | After | Why |
|---|---|---|
| Every immediate workstream could stretch one row across the map. | Bounded branch disclosure, selectable density and show-more counts. | A leader can explore 20 workstreams without presenting all 20 at once. |
| No way to narrow the hierarchy by responsibility or risk. | Compact filter strip with two common shortcuts. | Start with the decision the leader needs to make. |
| A matching descendant required manual expansion and scrolling. | Matching path opens and the canvas moves to the goal. | Search produces a reachable result. |
| List disclosure used separate native state and rendered every descendant. | List and map use the same collapse and branch limits. | Switching views preserves the exploration and avoids unnecessary hidden rendering. |
| Pointer glide started automatically. | Explicit opt-in, reduced-motion protection and non-drag controls. | Keep the map stable while reading and selecting. |

## What remains, in the order I would build it

### Before the October 27 workshop

| Priority | Work | Concrete acceptance | Suggested focused effort |
|---|---|---|---|
| Delivered 16 Oct | Save recovery and draft Undo. | Connected tests verified retained entries, uncertain-write deduplication, explicit two-tab conflict comparison, local Undo/Redo, saved-draft Undo, and registration → approval → Charter plus private evidence and Hygiene writes. See SAVE-AND-RECOVERY.md. Keyboard focus across all inbox journeys and expired capability renewal remain in the accessibility/operational audit. | Completed workshop scope |
| 2 | Tighten status explanations across Summary, Charter and Hierarchy. | The same goal displays the same health, basis and approved version everywhere; stale check-in, owner forecast and calculated delivery risk are distinct; every warning links to the responsible record. Add concise “Why this status?” where absent. | 1 day |
| 3 | Resource planning clarity. | A month selector compares approved commitments with proposed changes, attributes overload to specific goals, and explicitly marks missing capacity. No claim that unallocated time is available without capacity/leave data. | 1–2 days |
| 4 | Accessibility and long-content audit of complete journeys. | Keyboard-only creation, review and evidence acceptance; focus restoration; visible labels/errors; 320/390px reflow; 200% zoom; screen-reader chart/list equivalents; contrast and reduced-motion checks. Record issues and fixes rather than claim WCAG compliance from a screenshot. | 1–2 days |
| 5 | Workshop rehearsal and stable demo data. | Rehearse director, manager and employee cases with complete, blocked, draft and returned goals. Demonstrate one real database save and independent evidence acceptance. Preserve source workforce data. Separate actual event dates from the scenario date in explanatory copy. | 0.5–1 day |

These estimates overlap only where work is independent. Preserve a buffer for defects and George's feedback. Defer cosmetic extras if they displace a reliable commitment journey. The existing Charter, five-step registration, reasoned inheritance pushback, three success contracts, deliverable-linked allocations, avatars and quarterly history are implemented; they should not remain on a “not started” backlog.

### Gate for the 100-person internal pilot

| Priority | Work | Acceptance gate |
|---|---|---|
| P0 | Verified identity and authorization | Approved corporate identity provider; server derives actor and roles; leader switching restricted to permitted demo/admin contexts; cross-person access and mutation denial tests. The local preview must not simply be hosted publicly. |
| P0 | Scoped database reads and concurrent writes | Fetch only the actor's permitted data with indexed queries and pagination; search roster server-side; per-goal/version concurrency replaces workspace-wide contention. Tenant identifiers and authorization assumptions are explicit in the model. |
| P0 | Performance and recovery | Measure action-to-usable-render p50/p95/p99 under representative 100-user load, including cold start, large trees and concurrent writes. Target p95 usable startup ≤3 seconds and ordinary confirmed actions ≤4 seconds in the release sample. File transfers get a separate size/bandwidth budget. No current guarantee that every operation meets four seconds. |
| P0 | Operational evidence and audit | Actual immutable event timestamps, correlated errors without HR payloads, storage orphan reconciliation, file scanning policy, tested backup/restore and retention controls. |
| P1 | Reminder and review cadence | In-app reminders first, clear snooze/owner/escalation rules; outbound notifications only after an approved integration and delivery semantics. Existing follow-up records are not email delivery. |
| P1 | Saved hierarchy preferences | Explicit save/reset of filters, density and view with owner-scoped persistence; stale owners and deleted goals recover safely. Current filters are session-local. |
| P1 | Grounded AI assistance | After provider/data approval: goal and measure suggestions, plan-gap explanations and review drafts using only authorized records. Show sources, allow edits, require human application, measure cost/quality and cache by permission/version. Retain deterministic calculations and approval rules. Current assistant remains the requested offline demonstration. |

### Gate for 1,000+ leaders / multi-tenancy

Tenant-bound authorization for every row, file, cache, job and AI context; normalized production data contracts and migration reconciliation; representative concurrent load tests; background export and AI queues; tenant provisioning/retention; observability and recovery rehearsals. Incrementally migrate shared rendering/state into typed modules. The current concatenated JavaScript UI and whole-workshop read are workshop architecture, not proof of organization-wide scale.

## Decisions that still need business input

- Confirm the Pulse score's business interpretation and weights with George. Preserve current arithmetic until that decision; do not make cosmetic changes to the score.
- Select the corporate identity integration and approved AI provider before pilot connections are added.
- Confirm capacity sources, leave/BAU assumptions, independent review/delegation rules, retention and reminder policy. Record assumptions until evidence exists.

## Verification record

- Build, TypeScript transport checking and all 12 UI suites and 60 Python tests passed.
- Added a synthetic 20-workstream unit scenario covering branch limits, show-more reachability, ancestor retention, goal/deliverable search, intersecting filters, empty/clear states, leader isolation and immutable source trees.
- Connected-browser tests exercised risk filtering, owner/status intersections, personal shortcut, draft approval filtering, deliverable search, ancestor context, map/list parity, keyboard submission and focus restoration. Existing saved progress stayed unchanged.
- The larger scoped director view showed 19 goals; branch size three produced working show-more controls. Another director's view showed eight goals with only its three goal owners offered in the filter.
- Desktop 1440px and mobile 390px layouts were inspected. The mobile document had no horizontal page overflow. The canvas remains deliberately scrollable.
- This is functional verification of the changed journey, not an exhaustive accessibility or performance certification. A slow-connection warning was observed during a connected reload; latency remains a pilot gate.
