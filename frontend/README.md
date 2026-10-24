# Integrated frontend  -  local use

Launch from the repository root:

```sh
.venv/bin/python serve_frontend.py
# http://127.0.0.1:4173
```

The server binds to loopback only, serves an explicit asset allowlist, and never
runs providers. Select a saved result, or enter a topic to match saved video
titles. Reference URLs select existing saved videos; unavailable references stay
visible in coverage. This is cached retrieval, not discovery or live analysis.
The last selected library result reopens on refresh. Data remains in the existing
`data/` artifacts. No credentials are needed to browse it.

Connected routes:

- `GET /api/analyses`: sanitized saved-source catalog and capabilities.
- `GET /api/analyses/{source_id}`: normalized saved result, stable source identity.
- `POST /api/analyses`: cached matching only; returns 422 if no completed match.
- `GET /api/frames/{source_id}/{filename}`: only frames explicitly used in evidence.

No async jobs are claimed: live processing and discovery are unavailable.
The adapter exposes source summaries separately from executive findings. Current
legacy outputs do not support attribute sentiment, direct comparison rankings,
recurring cross-video themes, or aligned multimodal timestamps. Those sections
remain empty unless an imported evidence-bearing normalized report supplies them.
Visual frames have no timestamps; transcript excerpts use their saved bounds.
These are machine outputs, not manually verified findings.

Validate/package with `.venv/bin/python build_frontend.py`. The dependency-free
build is written to ignored `frontend/dist/`; Node is needed for syntax and logic
checks. The local API server serves the source assets directly. Run backend tests
with `.venv/bin/python -m pytest -q`.

Synthetic preview stays visibly labeled and never loads automatically. Imported
reports are shape/reference-validated, but their factual provenance still needs
review. Only HTTPS YouTube source links and allowlisted local frame links render.

---

The original foundation contract follows for reference; its historical integration
status below is superseded by the implementation notes above.

# Video Data Agent  -  Frontend Foundation

A dependency-free, responsive frontend foundation designed for the existing Python `video-data-agent` repository. It is an **independent presentation layer**, not a replacement for the agent.

## Preview locally

```bash
cd frontend
python -m http.server 4173
# Visit http://localhost:4173
```

Open **Illustrative design preview** to inspect the visual layout. **Every number, insight, timestamp, and comparison in this preview is synthetic, visibly labeled in the UI, and must not be presented as real evidence.**

Use **Open saved analysis** to import a normalized JSON report matching the format below. This is functional without a server integration.

## Existing backend status

The GitHub `main` branch inspected 2026-10-22 includes `main.py`, `run_batch.py`, `src/downloader.py`, `src/transcriber.py`, `src/vision_analyser.py`, `src/synthesiser.py`, and example single-video `brand_intelligence_report.json` results. It does **not** currently expose an HTTP API, automatic topic discovery, source-level aggregate attribute sentiment, source-level direct comparisons, or full evidence-linked cross-video reports. Your Codex local checkout may be ahead of GitHub; inspect it before planning adapters.

**A single-video `brand_intelligence_report.json` is not sufficient to populate a cross-video 360-degree dashboard.** Do not make up missing fields.

## Minimal API contract (to be implemented against existing agent)

`POST /api/analyses` with:

```json
{ "query": "iPhone Duo reviews", "reference_urls": [] }
```

Returns either `{ "analysis": { ...completed Report... } }` or `{ "id": "run-id" }` for a queued job. The frontend currently displays the returned job ID; add authenticated job polling and result retrieval when the backend adapter is implemented.

The completed report should follow the shape in `data/design-preview.json`, replacing **every synthetic value with genuinely computed observations**:

- `query`: user-requested subject, not hardcoded to iPhone.
- `sources`: `[{id,title,url?,status}]`; completed vs. failed coverage is shown accurately.
- `insights`: `[{title,description,source_ids,evidence_ids,modality}]`.
- `attributes`: `[{name,source_ids,driver,sentiment_counts?}]`. The sentiment must be **attribute-targeted**, not whole-video sentiment.
- `themes`: `[{name,description,source_ids,evidence_ids}]`.
- `comparisons`: `[{competitor,attribute,observation,is_direct,source_ids,evidence_ids}]`.
- `evidence`: `[{id,title,summary,source_id,timestamp,spoken,shown,modality}]`.
- `word_phrases`: optional secondary word-cloud data.

The **Most Compared-With Product** uses only `is_direct === true` comparison records, ranked by the number of **distinct source videos** per competitor; multiple mentions in the same video do not inflate the ranking. Incidental brand mentions never count. Ties are broken deterministically; don't call a tie an undisputed winner if product semantics require exposing joint leaders.

Evidence IDs must resolve to actual time-bound source segments. In the synthetic preview, cards indicate why source links and real video playback are absent. For real data, the evidence drawer should link or embed legally permitted source clips at exact timestamps.

Keep proprietary orchestration, prompts, frame strategies, provider routing, secrets, internal outputs, and unsupported confidence scores **out of the client payload**.

## Next Codex implementation tasks

1. Audit the **local** Codex checkout for newer source discovery and report formats not pushed to GitHub.
2. Adapt saved outputs to the normalized report shape without inventing metrics.
3. Build the minimal server-side API bridge to current agent capabilities, with genuine job state, timeout/error handling, and throttling of expensive runs.
4. Implement `/api/analyses/{id}` polling and authentic source-linked evidence.
5. Validate source counts, competitor ranking, attribute sentiment, and timestamp provenance.
6. Replace the design preview with a real prepared example analysis only after source validation.

## Notes

- Live analysis intentionally reports an unavailable API instead of pretending an analysis has completed.
- The UI shows the full insight text in-page; evidence clicks reveal **provenance**, not hidden insights.
- Product-specific names and charts are driven by report data; the app shell is industry-neutral.
- The fixture is clearly labeled, and no demo results should be published as verified findings.
- Before enabling YouTube ingestion in a public-facing product, review platform access policies and rights to process/display media.
