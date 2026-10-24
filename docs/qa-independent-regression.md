# Independent regression review, 23 October 2026

Status: approved for protected Mac-assisted testing only. Autonomous cloud-worker production readiness is not approved. See the final acceptance result below; earlier entries record findings and their resolution.

## Executed verification

- Latest independent local Python suite: 139 passed, 1 opt-in PostgreSQL test skipped in 4.53 seconds.
- Frontend build, syntax validation and logic regressions passed.
- Added worker regressions covering durable checkpoint recovery, no replay of interrupted paid work, preservation of untouched queued work during stop, and completed report retrieval after reconstructing the store.
- Added adversarial direct-comparison query mismatch, nonfinite timestamp rejection and expired-worker lease fencing regressions. Implementation fixes made by the primary agent pass these checks.
- Added local DNS-rebinding Host regression. The initial test reproduced unauthorized local access; the primary-agent fix passes local regression verification.
- Earlier actual browser checks covered initial empty history/results, topic validation/chips, optional references, synthetic preview rendering, evidence drawer keyboard dismissal/focus return, and absence of displayed em dashes. Preview content was explicitly synthetic and cannot establish real analytical correctness.
- The browser became unavailable during the subsequent implementation phase, so the revised frontend has automated logic/build verification but has not yet completed a fresh browser review.

## Frontend regressions addressed

Display normalization is separate from markup attribute escaping. Raw URLs and opaque identifiers remain intact; evidence selections use JSON arrays. Polling uses per-request cancellation, retries transient errors, preserves active IDs across outages and exposes Resume analysis after bounded failures. Terminal states clear stale IDs. Completed timestamps come from backend data. Evidence image paths are restricted to authenticated content-addressed blobs and legacy local paths. Build enforcement scans all frontend display source modules.

## Required acceptance before production approval

A fresh authenticated browser-to-API-to-worker-to-provider-to-persisted-report acceptance run remains required. That run must verify real source selection, grounded quotes and sentiment interpretation, source coverage, direct comparisons when supported, immutable image retrieval, refresh/reconnect and reopening completed history. PostgreSQL/container integration and the actual hosted deployment need smoke checks. No paid provider calls or deployment actions were performed by this QA agent.

The previous local ten-video CLI artifacts are historical artifacts only. They do not establish success of the new worker or hosted browser path. Some model summaries describe the focal product as fictional; source/content review is needed before treating those findings as reliable product intelligence.

## Real PostgreSQL check

The opt-in database acceptance test reached the actual configured PostgreSQL database. Three concurrent submissions initially reproduced an InternalError category failure during connection setup; this exposed a concurrency defect in repeated schema/privilege DDL. Schema initialization now executes under the advisory transaction lock. After the user reported database credential rotation, the primary agent reran the actual PostgreSQL acceptance test successfully (1 passed in 7.12 seconds). This latest remote run was performed by the primary agent, not independently rerun by QA. The test cleans up its disposable owner rows and checks deduplication, claims, lease recovery, persisted reports, image ownership, RLS and private-schema grants. A first sandbox connection failure traceback exposed a database password in the execution log; subsequent failures are caught and reported by exception category only. The exposed credential was not approved for production reuse. No provider or deployment call was made by QA.

## Grounded transcript window regression update

Independent tests now cover exact quotations spanning multiple contiguous Whisper segments, timestamp bounds derived from only the overlapped segments, raw transcript preservation, rejection of rewritten punctuation and cross-window joins, rejection of boolean window identifiers, five-segment window splitting and invalid-segment boundaries. Opaque source/evidence identifiers containing punctuation and Unicode remain intact through frontend validation, JSON selection and evidence lookup; displayed text alone is normalized. Seven grounded-insight tests and the frontend build pass.

The primary agent reports a successful preview container build, with the worker daemon inactive in preview, and ongoing real model enrichment of saved local transcripts. These facts do not establish acceptance of the hosted worker, a fresh video pipeline or browser restart/reconnect against production. Staging web and production worker acceptance remain required before blanket deployment approval.

## Staged-worker pre-acceptance review

New API tests verify integer source limits from 1 through 10, rejection of invalid limits without job admission, canonical YouTube reference deduplication, persisted request shape and authenticated per-owner deduplication. Grounded extraction tests verify the broader comparison pass and exact duplicate preference for richer direct evidence. These tests use deterministic provider stubs rather than invented acceptance findings.

Two new adversarial canonicalization regressions initially fail: a same-generation qualifier such as Pro can be lost by a digit-only name guard, and brand-only references can become specific products. Also, two legitimate competitors within one quote can be collapsed to one, despite both needing comparison coverage; attribute sentiment should still count that quote once. These findings were reported to the primary agent before protected staging acceptance. Final signoff remains withheld until fixes and hosted acceptance are verified.

The primary agent fixed the canonicalization findings. Independent rerun: all 27 targeted HTTP/grounded tests pass, and the full suite reports 127 passed with the real PostgreSQL test skipped by default. Model generations and qualifiers remain distinct; brand-only entities cannot be promoted into a specific model; legitimate brand-prefix aliases can merge without modifying quotes. Multiple competitors in one quote retain comparison coverage while the attribute quote is counted once. Frontend build passes. Hosted worker acceptance and promotion approval are still outstanding.

## Protected hosted smoke check

Independent checks against the initial protected production-runtime deployment returned HTTP 500 for both unauthenticated and authenticated root-page requests. No healthy application acceptance was inferred. The primary agent identified the web container port mismatch and is redeploying a correction. Requests to the superseded deployment were stopped. These checks did not submit an analysis or invoke any model provider. Local regression remains 127 passed, 1 skipped, and the frontend build passes. Authentication, history, evidence serving and fresh worker execution must be rechecked against the corrected deployment before promotion.

## Corrected hosted verification

Independent HTTP verification passed on the corrected protected deployment: unauthenticated root/API return 401, authenticated page/history/static assets return 200, and raw environment/source files plus the production synthetic fixture return 404. The existing persisted ten-video report passes source/evidence/comparison reference validation and internal-key exclusion. Its immutable image endpoint returns 200 with authentication and 401 without it.

The served existing report contains 10 completed sources, 253 evidence items, 30 images, 18 attributes and 3 comparison records. An additional independent grounding check matched all 223 spoken evidence items to exact original local transcript text and timestamp bounds, with zero mismatches. All 30 immutable image digests match the original local source JPEG bytes. These checks make no provider calls and do not establish completion of a fresh worker job.

The primary agent reports user-approved protected activation for worker QA. Fresh hosted job 384e2f7c2fec459d9ad42fcc3a805b59 remains a separate acceptance requirement. Final readiness approval is still withheld until its genuine worker execution completes and its report is verified.

The fresh hosted job was claimed by the worker and failed. Independent failure-path verification confirms status failed, no analysis payload, only allowlisted public fields, and exclusion from completed history. The existing grounded report remains independently verified, but it is not a substitute for a successful fresh worker pipeline. The primary agent is diagnosing the runtime/download failure and running a bounded retry. Successful-path acceptance and final readiness approval remain pending.

## Mac-assisted worker acceptance

After cloud download/runtime failures, the user approved testing on the Mac. The cloud daemon is disabled. The first Mac run downloaded media, extracted frames and transcribed audio, then failed on a typed NVIDIA synthesis timeout. The primary agent added an Anthropic fallback for typed timeout causes while preserving rejection of authentication, rate-limit and invalid-model errors. Independent tests verify typed timeout recognition, original prompt preservation, rejection of message-only timeout text, and termination of cyclic exception traversal; all 17 report-fallback tests pass.

Fresh source transcripts and JPEGs for the retry were captured from its isolated workspace for independent grounding checks. Retry job ef430d9749964ca4a993439d46d6e1ff must complete before successful-path acceptance. A passing Mac-assisted run would validate that execution topology only; it would not establish autonomous cloud-worker readiness while the cloud daemon remains disabled.

## Independent fresh Mac acceptance result

Fresh job 5746cd5c343840d08ae1be9aa2a85743 completed one newly downloaded source through the original pipeline using the approved Mac worker. Independent hosted verification passes:

- All 7 spoken evidence items match the captured fresh transcript text and exact timestamp bounds.
- All 3 remotely retrieved JPEG bodies match their content-address hashes and the original source frame bytes.
- Report coverage and finding/evidence references resolve to its completed source.
- The report contains 4 attributes and 0 direct comparisons; no missing comparison was fabricated.
- The completed report reopens identically through its saved-analysis endpoint and appears in completed history.

A macOS temporary-directory alias mismatch was fixed by canonicalizing the workspace path before containment checks. Independent regressions confirm that both direct outside paths and symlinks escaping the workspace remain rejected. The latest local suite passes 139 tests, with the opt-in PostgreSQL test skipped, and the frontend build passes.

QA outcome: approved for protected testing with the Mac-assisted worker. Autonomous cloud-worker production readiness is not approved: the cloud daemon remains disabled and cloud media retrieval did not pass acceptance. Availability depends on the Mac worker remaining running, connected and awake. The freshly exercised path used one source; a fresh hosted ten-source pipeline, hosted browser/UI acceptance and load testing have not been completed. Earlier ten-source persisted-report grounding checks are documented separately above.

The primary agent is removing only the four explicitly identified disposable failed QA runs with owner and failed-status guards, preserving the original saved report, successful fresh report and shared image blobs. This restores the normal demo quota without broadening production admission policy.
