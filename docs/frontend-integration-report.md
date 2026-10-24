# Backend synchronization update, 23 October 2026

The dashboard now uses backend-owned run history rather than browser-owned video
IDs. Completed normalized reports are persisted under ignored
`data/dashboard_runs/`. GET `/api/analyses` returns only completed dashboard runs;
GET `/api/analyses/{run_id}` reopens the whole run. Before the first completion,
the API returns an empty history and the saved-analysis UI stays hidden.

POST `/api/searches` uses the existing search runner and pipeline. Optional
references are passed through, deduplicated, and supplemented with discovery up
to ten videos. Active duplicate submissions reuse the job ID; another query is
rejected while one is active. The browser stores the active job ID and resumes
polling after refresh. Completed jobs survive server restarts; interrupted jobs
are reported as interrupted rather than silently marked successful.

Job responses use sanitized progress labels and generic errors. Provider traces,
raw per-source errors and report paths are not returned. Failed new attempts
cannot reuse old successful reports or contribute evidence/coverage. Source
ordering follows the selected run. No analysis or model architecture was replaced.

Validation: full pre-final suite passed 96 tests; all 10 final API/discovery tests
passed after adding three regression cases. Frontend build and JS checks passed.
The running completed-history endpoint returns an empty list, as expected before
any dashboard run completes. No paid live processing was initiated for verification.
Rich attribute sentiment and direct-comparison records remain backend limitations;
this update does not manufacture them.

The initial integration record below describes the earlier cached-only state.

---

# Frontend integration — 22 October 2026

## Audit and reuse

Integrated the supplied `video-data-agent-frontend-foundation.zip` and followed
`CODEX_NEXT_TASK.md`. The working tree already contained the single-video pipeline,
batch runner, Anthropic visual-analysis integration, NVIDIA synthesis, frame
analysis, timestamped transcripts and existing model regression tests. These were
preserved. No model calls or new video processing were performed for this task.

The local saved library has 55 unique sources: 46 with structured final summaries,
3 with unusable report artifacts and 6 without final reports. This describes
saved-artifact availability, not a fresh end-to-end verification of those runs.
There is no saved iPhone Duo analysis or recorded YouTube discovery order.

## Delivered

- Added the supplied dependency-free frontend and its synthetic design fixture.
- Added `src/presentation.py`: allowlisted adapter over existing metadata, final
  summaries, visual observations and transcript segments. No raw report, prompts,
  routing, provider fields, filesystem paths, recommendations or traces returned.
- Added `serve_frontend.py`: local-only HTTP API and explicit static asset serving.
- Connected the saved-result selector and topic/reference matching to actual
  artifacts; restored the last selected source after reload. Multiple matching
  videos can be retrieved together. Source URLs are deduplicated by video identity.
- Preserved real missing/failed coverage. Unmatched topics return a clear error.
- Kept source summaries separate from unsupported cross-video executive findings.
- Displayed selected genuine analyzed frames and exact saved transcript bounds.
  Timestamp links open the source video at the transcript start. Visual frames
  have no invented time, and no audio/visual alignment is assumed.
- Hardened JSON import references, source URLs, frame paths, source coverage and
  comparison evidence requirements. Direct rankings use distinct sources and show
  tied leaders. Rich normalized imports populate the supplied charts, comparison
  matrix and coverage heatmap. Import validation checks structural provenance;
  it cannot independently establish the factual truth of externally supplied data.
- Added reduced-motion support, keyboard focus indicators, modal focus handling,
  explicit missing-sentiment labels, and removed remote font loading.
- Added a dependency-free validation/packaging build into `frontend/dist/`.

## API

`GET /api/analyses` lists safe saved-source metadata and capabilities.
`GET /api/analyses/{source_id}` returns a normalized saved analysis.
`POST /api/analyses` accepts `{query, reference_urls}` and retrieves cached results
only. It never starts a job or invokes a provider. Unknown topics return 422.
`GET /api/frames/{source_id}/{frame_name}` serves only selected evidence images.

Static serving cannot access `.env`, source code, raw artifacts, or arbitrary
repository paths. Host/origin checks and loopback binding protect local use.
This server is a local demo adapter, not a production public hosting service.

## Missing backend capabilities

The current pipeline does not record source-linked product-attribute sentiment,
direct product comparisons, cross-video executive findings, recurring themes,
frame timestamps, or synchronized said/shown evidence. Brand-level positivity
cannot be truthfully converted to attribute sentiment. Incidental co-detection
cannot establish a direct comparison or the most-compared product. These sections
show unavailable states for existing artifacts. They render supplied normalized
records when present, but no new rich analytical stage was invented.

Automatic topic discovery, live HTTP job processing and a prepared ten-review
Duo corpus are absent. The brief explicitly prioritizes cached/import support
when discovery is missing. Live endpoints remain disabled; no costly calls are
exposed. Existing CLI processing remains available through `main.py`/`run_batch.py`.
Existing machine transcripts may be poor (the saved iPhone 17 excerpt is sparse);
the UI does not silently repair or embellish them.

## Validation

- Python: 80 tests pass, including existing pipeline regressions, adapter evidence
  integrity, unavailable sources, stable identities, URL safety, HTTP boundaries,
  missing-topic errors and origin checks.
- Frontend: logic tests, fixture contract validation, source-linked comparison
  requirements, sentiment counts and JavaScript syntax validation pass.
- Build: `.venv/bin/python build_frontend.py` succeeds.
- Browser: saved iPhone 17 report loaded; original frames and transcript shown;
  evidence drawer opened with exact timestamp link; desktop and 390px mobile
  layouts inspected; saved source restored after reload.

## Launch

From the repository root:

```sh
.venv/bin/python serve_frontend.py
```

Open http://127.0.0.1:4173. Choose an existing saved video, or search saved titles
with a topic such as `iPhone`. `iPhone Duo review` remains a prepared query example,
not a claim that matching reviews were processed. The synthetic preview always
retains its visible disclaimer. No API keys are required to browse cached reports.
