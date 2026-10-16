# Save recovery and draft Undo

Implemented 16 October 2026 for the connected internal workshop preview.

## User behavior

- A failed save keeps draft entries and supported dialog fields. Recovery is stored in session storage by workspace and selected leader. Refresh does not create a new operation ID for an unconfirmed save.
- An uncertain save offers **Retry unconfirmed save**. Retry uses the exact original action, payload and ID. A different write cannot replace an unresolved operation. The app reports success only after confirmation.
- A definitive revision conflict retains the local draft and offers a comparison with the latest saved content. **Keep my entries for review** prepares the same draft for an explicit new save; it does not apply an overwrite automatically. **Use latest saved version** discards those retained draft entries. A changed or submitted version cannot be overwritten by an older draft.
- **Undo edit** and **Redo edit** operate on the current draft, with up to 30 in-memory editing steps. Native text-field undo remains available. **Undo last saved draft** restores the prior saved content through a new revision-checked database write. A concurrent newer edit blocks Undo. Undo does not reverse approvals, evidence reviews or recorded decisions.
- Goal submission includes both the reviewed version ID and edit revision. Approval forms carry the version ID they displayed. A different version is rejected rather than silently approved.
- Evidence retries bind a stable upload ID to the actor, workspace, deliverable, checkpoint, file name and SHA-256 file content. After refresh, the user must reselect the same file. Browser security prevents retaining a file picker selection, and file bytes are not placed in recovery storage.
- Demo controls contain one-shot failure tests: fail before sending, or lose confirmation after the real server save. These exercise the normal connected path and are explicitly labeled as tests.

## Boundaries

Session recovery is not cross-device cloud draft autosave. Closing a browser tab, clearing site storage or disabling storage can remove its recovery state. A storage failure displays a warning to keep the tab open. Local undo history is in memory; the last saved-draft undo token survives reload in the same tab. If Save and Submit is interrupted during its save stage, retry confirms that save; the leader still explicitly submits the recovered draft.

The existing server checks reporting scope and mutation authority. The selected persona is still a trusted local simulation, not a verified login. No database grants, bucket visibility or production authentication were changed. The existing Supabase compare-and-swap commit and actor/request-bound mutation lookup remain authoritative. Production concurrency and latency certification remain separate work.

## Connected browser evidence

Using clearly labeled synthetic records and the existing imported reporting structure:

1. Create a goal, lose the successful response, refresh, then retry. The title survived; an independent saved-state read found one matching goal.
2. Edit purpose, Undo and Redo locally, save, Undo the saved draft, then reload. The previous purpose was restored in Supabase and an undo edit event was retained.
3. Open the same draft in two tabs. Save in the second tab, then save the stale first tab. The first save was rejected with both texts visible in the comparison. Explicitly keep, review and save the retained text. A stale saved-draft Undo from the other tab was also rejected.
4. Fail a draft save before sending. The full purpose remained visible and the original retry succeeded.
5. Submit the completed metric-only plan. The designated approver inspected its contract, approved it, lost confirmation and retried. The approval left Hygiene and the goal opened its approved Charter. Independent state verification found one approval for that version.
6. Save a check-in with lost confirmation and retry. The form cleared after success and exactly one check-in was stored.
7. Upload synthetic evidence to private Storage, lose confirmation, refresh, reselect the same file and retry. The checkpoint selection survived and exactly one evidence record was stored. Uploading did not grant new acceptance credit.
8. Ask a question with lost confirmation, retry, then view it as its assigned owner. Exactly one question was stored. The owner posted a reply and recorded its resolution.
9. An unrelated director's server projection did not include the synthetic goal. Recovery ledgers also have automated actor-isolation coverage.

The intentional failure tests do not imply that every browser/network failure mode is covered. They verify real persisted writes and repeat requests, not a local-only imitation of database success.

## Automated verification

Build and TypeScript checks, 13 UI suites, and 63 Python tests pass. Added tests cover durable operation ID reuse, conflicting-write blocking, actor isolation, retained conflict payloads, undo revision binding, stale undo rejection, version identity, stale submission and duplicate-save revision counts. Existing tests continue to cover scope denial, approval rules, evidence authority and shared progress calculations.
