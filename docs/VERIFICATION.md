# Verification record · 15 October 2026

## Connected browser checks

A clearly labeled synthetic workstream was created beneath an existing leader-owned goal. Imported workforce records were not modified.

1. Receiving leader accepted, completed and submitted the test plan. The designated approver inspected the success contract, effort, ownership and checkpoint criteria in Hygiene, then approved it. The action disappeared and remained absent after reload.
2. The deliverable owner uploaded a synthetic text file from Hygiene to the private bucket. Status moved to waiting for review with 0% accepted progress.
3. The owner saved a check-in. It disappeared from the due queue and persisted after reload.
4. The owner created a question, reloaded, posted a reply and recorded a resolution. The resolved item left the action queue and appeared in history.
5. The designated reviewer downloaded the stored file. Its bytes exactly matched the upload. After inspecting its content, the reviewer accepted the checkpoint in Hygiene. Its action disappeared. A fresh server read confirmed 100% delivery progress.
6. An unrelated leader's browser queue contained neither the test goal nor its actions. Direct cross-scope approval, check-in, question and checkpoint mutations were rejected with 403. The evidence download was also denied with 403.
7. Browser console had no errors in the verified flow.

These are specific checks, not a claim of exhaustive browser, accessibility or load coverage. The leader selector remains a trusted local simulation of identity.

## Performance measurements

Same local computer and existing connected workshop; network conditions were not controlled. Measurements are not a 100/1,000-user concurrency test.

| Observation | Duration |
|---|---:|
| Earlier startup: roster plus separate state | about 5.7 s |
| Revised combined session, observed cold request | 2.178 s |
| Final sample of 14 session/state requests, median | 0.840 s |
| Final sample, nearest-rank p95 / maximum | 1.595 s |
| Browser private evidence upload | 3.557 s |
| Browser question save | 3.725 s |
| Browser checkpoint acceptance | 3.401 s |

An approval measured 4.355 seconds before lookup/load parallelization. That over-budget result motivated the additional optimization; it is not excluded from the record. The sample is too small to guarantee every future request below four seconds. Instrument and test representative end-to-end workloads before pilot sign-off.

## Automated checks

49 Python tests passed, covering shared domain rules, success calculations, evidence authority, leader projections, support requests, inheritance, monthly allocation constraints, current API origin/Host/nonce protection, one-read session loading and idempotent committed-state responses. UI suites cover Hygiene queues and urgency, history parity, map layout and controls, person hierarchy, Portfolio display, review scoping, Summary scoring and local-file recovery. TypeScript typecheck and Vite build passed.

One old file-entry assertion still expected the removed Overview route. It was corrected to assert Summary as the launcher destination and retain the disconnected-file recovery screen.

## Limitations

No production authentication, multi-tenant rollout, concurrent capacity certification, malware scanning, actual-cost integration or WCAG conformance claim is included. Existing goal setup still needs metric-only/combined success, deliverable-specific allocation and improved charter/registration separation. The private source-derived product plan addresses these gaps.
