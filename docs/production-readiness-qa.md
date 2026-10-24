# Production readiness and QA audit

Date: 23 October 2026

**Release decision: NO-GO for production deployment.**

The user requested an independent QA agent and an end-to-end regression review.
A QA subagent independently ran the current regression suite, frontend build,
code audit and local browser checks. No deployment, paid model calls or fresh
video processing were performed in this audit. Existing backend behavior was not
modified during the review.

## Verified

- Full Python regression suite: **99 passed in 13.10 seconds**.
- Dependency-free frontend production packaging and frontend logic checks pass.
- Actual local browser: clean initial screen with no saved results, empty-topic
  validation, topic chips and expandable references work.
- Explicit synthetic design preview: charts, rankings, heatmap and evidence drawer
  render; Escape dismisses the drawer and returns focus. The disclaimer stays visible.
- Browser DOM has no displayed U+2014, and the browser title is clean.
- Browser warning/error logs were empty during these checks.
- Automated API tests exercise mocked job completion/failure, persistence,
  interrupted-job handling, empty history, static boundaries and origin rejection.
- Existing CLI search artifact `data/search_runs/20261022T173016211630Z/summary.json`
  records ten selected iPhone Duo sources and ten completed results. All ten
  referenced report files exist with nonempty summaries and no `raw_report` field.
  This confirms artifacts, not independently verified review accuracy or a fresh
  production browser-to-provider run. No dashboard-run artifacts were present.

## Release blockers

| Priority | Gap | Evidence and impact |
| --- | --- | --- |
| P1 | Missing core intelligence output | `src/presentation.py:117` always supplies empty executive insights, attributes, themes and comparisons. A successful run cannot currently deliver the core sentiment, most-compared product or cross-video attribute analysis. Synthetic charts do not close this gap. |
| P1 | Local server is not a production service | `serve_frontend.py:112` rejects public hosts; line 198 binds loopback. There is no deployed service configuration, production process supervision or verified production environment. |
| P1 | No user access boundary or cost authorization | Search submission, job retrieval and report history have no identity or report ownership checks. Host/origin checks protect local use but are not authentication. A single-process active-job lock does not provide per-user quotas, spend limits or deployment-wide rate limiting. Protect access before exposing a generation endpoint. |
| P1 | Jobs are not durable workers | `serve_frontend.py:15` holds active jobs in memory; line 185 launches daemon threads. Restart marks jobs interrupted; it cannot resume work. Multiple workers do not share the execution lock, so duplicate prevention is process-local. External YouTube/model processing needs bounded execution and durable recovery before production. |
| P1 | Evidence is mutable across runs | Downloads use titles as filenames (`src/downloader.py:54`); frames reuse title folders (`src/frame_extractor.py:23`). Presentation source IDs hash those folder names (`src/presentation.py:60`). Saved reports link to frames resolved from current global artifacts, so another run or a same-title video can overwrite the visual evidence of an earlier report. Use immutable video/run identifiers and immutable evidence assets. |
| P1 | Full live journey and content acceptance are not certified | No fresh browser submission was exercised through real discovery, ingestion, transcription, visual analysis, synthesis, completion, reopen and timestamp/frame verification. Review eligibility is not established by `src/youtube_search.py`, which excludes duplicates and live videos but does not validate actual review relevance. Some saved summaries call the product fictional; this is unverified model wording and requires source review, not an assumed fact about the product. |

## Additional findings

- Completed history is sorted by random UUID filenames, not completion time
  (`serve_frontend.py:126`). Persist a completion timestamp for reliable ordering.
- Static em dash enforcement excludes `analytics.mjs` (`build_frontend.py:18`).
  Current displayed text passes, but future literals in that module could escape
  the static scan. Extend build enforcement to every display-producing module.

- `frontend/app.js` uses its display-text escaping helper for both visible copy and
  href/data attributes. The U+2014 display normalization must not rewrite URLs or
  raw evidence identifiers. Separate text normalization from attribute escaping.
- Client polling has no request timeout or automatic reconnection strategy.
  Network failure ends polling and re-enables submission; server deduplication
  helps within a single process, but does not establish robust production recovery.
- Source metadata and saved-job JSON are trusted for shape when reading from disk.
  Corrupt artifacts and storage failures need explicit tested behavior.
- Search references are supplemented with discovery, but the progress string still
  says all processing follows YouTube order. Reference-first ordering should be
  described accurately.
- The initial integration documentation contains historical cached-only statements;
  release documentation should be consolidated once the deployment target is chosen.

## What the passing tests do not establish

Many pipeline and job tests replace download, transcription or provider calls with
mocks. These are valid regression tests for logic and integration contracts. They
are not proof that provider credentials, current YouTube access, full video runtime,
resource limits, long-running worker recovery, concurrent users, production hosting
or analytical accuracy work together. Existing generated reports likewise do not
certify a current real end-to-end run.

No production load, browser network-interruption, multi-worker, deployment smoke,
or disaster-recovery acceptance test has been completed.

## Required release sequence

1. Implement the missing evidence-bearing analytical outputs and validate claims
   against source timestamps and frames, preserving the existing agent workflow.
2. Isolate immutable per-video/per-run artifacts and fix identifier/URL rendering.
3. Protect the demo with authorized access and cost limits; establish production
   runtime, storage, job execution, recovery and monitoring.
4. Run a controlled real provider-backed staging analysis. Validate all selected
   source identities, failures, coverage, insights, comparison denominators,
   timestamp links, frames and saved-result reopening.
5. Re-run automated regression and browser tests, then add concurrent submission,
   network interruption, worker restart, missing credentials, provider/download
   failure, corrupted artifact and production deployment smoke checks.
6. Obtain a clean QA acceptance report before approving a production release.

Production deployment has not been performed or approved by this audit.

## Protected production runtime validation, 23 October 2026

The user approved a protected production-environment deployment with `--prod --skip-domain`, reserving final promotion for QA acceptance. The first staged container built successfully but returned HTTP 500 during independent hosted checks. The web process bound port 8080 while Vercel's container runtime expects port 80 unless configured otherwise. `Dockerfile.vercel` now exposes and binds port 80; the corrected protected revision is rebuilding.

Current deterministic verification: 127 Python tests pass, one opt-in PostgreSQL test is skipped in the standard suite, and frontend logic/build checks pass. A separate actual PostgreSQL acceptance run passed after schema setup concurrency was fixed. These results do not establish successful hosted video processing. Hosted authentication, real report/image access, fresh worker processing and QA acceptance remain release gates.

The corrected protected revision `video-data-agent-a0ju4d5ay-glomeyo.vercel.app` passes hosted application authentication and history checks. A real one-source request was accepted (202) and remains queued. Vercel's daemon documentation states that daemon rollout occurs when a deployment becomes active production, including promotion; a STAGED production-target deployment does not start the worker. The previous assumption that `--prod --skip-domain` would start the daemon was incorrect. Controlled protected activation has been requested explicitly; no final readiness claim is made. See https://vercel.com/docs/daemons.

## Controlled activation result

The user explicitly approved protected activation for QA. Deployment `dpl_D9R9h1xP1YVdXQcHjnkmAVRVi7oG` was activated, with app authentication and Vercel protection retained. The daemon claimed the queued real source request, proving queue-to-worker connectivity. Two bounded attempts failed during YouTube download: the remote service returned a sign-in/bot-verification challenge for all configured public client fallbacks. No transcript/provider success or fresh report completion is claimed.

Independent QA verified hosted authentication, source-file boundaries, completed-report contracts, and image access. All 223 spoken evidence entries match original transcript text and timestamp bounds, and all 30 served image digests match original JPEG bytes. Failed jobs expose only safe public status fields and do not enter completed history. QA explicitly withheld production-readiness approval because successful fresh-worker processing remains unverified.

Release blocker: provide an approved and reliable video-ingestion path reachable from the cloud worker. Do not export browser cookies or user session credentials without explicit authorization. Do not fabricate a successful analysis or replay cached artifacts as fresh-worker acceptance. The currently protected deployment is a QA/demo deployment, not a production-ready release. Rolling back to the previous revision would restore the known incorrect-port outage, so it is not a usable recovery target.
