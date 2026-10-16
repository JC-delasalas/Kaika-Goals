# Profiles and quarterly Summary

Implemented and verified 16 October 2026.

## Profile experience

The avatar beside the leader switcher and the sidebar's Customize your profile action open the same editor. People can choose one of six illustrated color variants, upload a JPEG/PNG/WebP image, or restore their default avatar. The preview is center-cropped before saving. Assignments use the shared person component across Summary, hierarchy, Hygiene, Team, Charter, setup and resource details.

Profile settings belong to Kaika, not the Workday import. The private `kaika_workshop.profiles` table is keyed by workspace and worker. Settings survive refreshes of workforce attributes. A revision check prevents an old editor from overwriting a newer change; mutation IDs make retries idempotent.

The current preview has no verified login. The selected persona may edit only its own profile. Photo reads enforce that persona's recursive reporting scope in the database. Switching personas remains a trusted-computer preview control.

## Image handling and delivery

- The browser accepts files up to 5 MB and produces a small center-cropped preview.
- The gateway decodes the supplied raster, validates its format and dimensions, strips metadata and re-encodes a 160 × 160 JPEG. Invalid images, external URLs and SVG uploads are rejected.
- Only the bounded thumbnail is retained, at most 32 KB of JPEG bytes, in a private table. There is no original-photo archive and no public image bucket.
- The initial workspace load carries profile metadata only. The browser requests thumbnails for rendered people in batches of at most 24, with an in-memory cache keyed by person and revision. Leader changes clear the cache.
- The existing private deliverable evidence bucket and evidence approval flow are unchanged.
- Workday photo synchronization and user-controlled crop positioning are not implemented.

## Summary experience

One compact panel combines Goals Pulse, Execution by quarter, comparison signals and an outcome context strip. Objective cards retain status, approved success basis, progress, ETA, next deliverable and expandable details. Cards, Table and Board remain available. Filters and recorded change details use progressive disclosure.

The score calculation is unchanged: 40% healthy approved priorities, 40% unique deliverables clear of risk, 20% current check-ins, normalized over available signals. Outcome attainment remains a separate contextual mean of measured approved top-level priorities, not an additional health-score input.

A quarter is a calendar quarter in Asia/Manila using the actual snapshot capture timestamp. A point is the latest available saved snapshot in that quarter, not an average or a claim that the snapshot was taken at quarter-end. The default shows four quarters; All quarters expands the history. Missing quarters have no value or connecting line. The current unsaved view is an outlined point. Snapshot capture time and the underlying workshop as-of date remain distinct.

Comparisons use the same leader, filter selection and scoring method as the existing snapshot contract. The comparison picker includes every saved snapshot, including earlier captures within the same quarter. Recorded differences include approved resources and approval states without adding those fields to the score.

## Verification evidence

- All 12 UI regression suites and TypeScript checks passed, including new quarter boundary, last-capture selection, empty quarter and live-point tests.
- Profile tests cover raster validation, resized dimensions, metadata removal, stale revision rejection, foreign-person denial and connected metadata projection.
- Connected browser: selected and saved avatar, reloaded, uploaded a synthetic PNG, saved it in Supabase, reloaded the photo in the editor, observed the same image on assignments and in the manager's Team view, switched to an unrelated leader and confirmed its absence, then restored the default avatar. No test photo remains assigned to a real worker.
- Independent connected API checks returned 403 for unrelated profile reads and foreign-person edits. A fresh repository instance loaded the saved thumbnail metadata. The main state contained no image bytes. One measured scoped state response took 1.207 seconds; this is a measurement, not an end-to-end performance guarantee. The first request immediately after Edge Function deployment encountered a cold-start timeout; retry succeeded.
- Browser: inspected prior resource/approval changes, saved a real new snapshot, verified one saved quarterly point despite multiple captures, exercised Cards/Table/Board and tested the 390px mobile layout with no page-level horizontal overflow.
- Supabase migration applied, Edge Function deployed, anonymous execution of the profile RPC denied. RLS has no direct-access policies by design. The security advisor also reported an existing unrelated `rls_auto_enable` function privilege warning; this change did not alter that function. [Advisor explanation](https://supabase.com/docs/guides/database/database-linter?lint=0028_anon_security_definer_function_executable).

No backdated snapshots or earlier-quarter values were generated for presentation.
