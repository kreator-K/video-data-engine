# Codex Task — Video Data Agent Frontend Integration (Phase 1)

You are working on my existing `kreator-K/video-data-agent` project and should add the `frontend/` directory from the attached **Video Data Agent Frontend Foundation** package. Use the existing codebase as the source of truth and check the latest local branch, which may be ahead of GitHub `main`.

## Context and product vision

Create an elegant, universal video-native brand/product intelligence app for decision-makers in product, R&D, consumer insights, brand and competitive analysis. This is **not a marketing dashboard built around one hardcoded iPhone** and **not a recommendation engine**. The entry point is a single free-form prompt (“What insights would you like to explore today?”), with one expandable optional control to add reference video URLs. No separate YouTube search and URL tabs. The existing agent should perform its own discovery and analysis where supported. Show genuine progress only.

Results appear on one detailed dashboard, with all substantive findings immediately visible:

1. Evidence-backed executive findings.
2. Dynamic product attribute frequency, sentiment, and underlying drivers.
3. **Most compared-with product**, presented prominently and computed from distinct videos with verified **direct product comparisons**, not name mentions, logo detections, or multiple mentions in one video.
4. Comparative product/attribute evidence matrix.
5. Recurring discussion themes and contextual phrases.
6. Video × attribute coverage heatmap, emphasizing source breadth.
7. Visually compelling said/shown/both multimodal moments.
8. Exact source-video and time-bound evidence in an in-page drawer.
9. Optional secondary phrase-cloud and source gallery.

Do not show “What should R&D investigate?”, opportunity or product-friction recommendations. Do not hide the actual findings behind “View detailed insights.” Evidence clicks may open a source drawer, not a new findings page.

## What is in the foundation

`frontend/index.html`, `frontend/styles.css`, `frontend/app.js`, `frontend/analytics.mjs`, `frontend/data/design-preview.json`, `frontend/analytics.test.mjs`, and `frontend/README.md`. It is a **dependency-free UI foundation** runnable with `python -m http.server` from `frontend/`. It supports a synthetic, visibly labeled design fixture, importing a real normalized JSON report, the generic input, and a future `POST /api/analyses` adapter. The live agent is not yet connected; it must not pretend otherwise.

## Grounding: GitHub main inspection

At the time of inspection, GitHub `main` contained `main.py` (single URL pipeline), `run_batch.py`, `src/downloader.py`, `src/transcriber.py`, `src/frame_extractor.py`, `src/vision_analyser.py`, and `src/synthesiser.py`, with a single-video brand report containing brand evidence (visible, audio, description) and a few report fields. It did **not** contain an HTTP API or rich cross-video, evidence-linked attribute sentiment/comparison aggregates. Inspect the **local Codex checkout** before accepting those constraints: its unpushed work could be more complete.

## Implementation sequence

**Task A — Audit without refactoring:** Inspect current pipeline, batch artifacts, saved outputs and source evidence metadata. Map every existing field to the `frontend/README.md` report contract. Record what is present, absent or unreliable. Do not assume a prompt can produce truthful competitor rankings without source-linked direct-comparison evidence.

**Task B — Integrate the frontend:** Add the supplied `frontend/` foundation without changing working agent internals. Confirm desktop/mobile rendering and interaction behavior. Make components data-driven; never hardcode product attributes, phone types, manufacturers, hero images or keywords outside the optional illustrative fixture.

**Task C — Backend presentation adapter:** Build the smallest stable, safe server API that returns normalized, sanitized data from actual existing outputs. `POST /api/analyses` receives `{query,reference_urls}`; implement job identity and real state transitions if live analysis is supported. Add GET status/result routes when asynchronous pipeline processing requires them. If topic discovery is not yet available, do not quietly fabricate it. Report the blocker and implement import/cached-analysis first.

**Task D — Brand and competitive intelligence:** If the backend provides actual evidence-bearing segments, aggregate with source IDs and timestamp references. Canonicalize competitor entities and attribute labels. Count one source **once** per competitor when a direct comparison occurs. Rank the most compared competitor by distinct source-video count. In a tie, show a tie rather than silently declaring a winner. Provide comparison attributes and summaries only when backed by actual segments.

**Task E — Evidence:** Map claims to source URLs, timestamps, transcript excerpts and permitted visual frames. Source-level support is vital. Never display a timestamp, quotation, sentiment percentage, confidence estimate or competitor ranking that cannot be reconstructed from saved evidence.

**Task F — Demo readiness:** Use the existing `iPhone Duo review` input as a **prepared demonstration query**, not hardcoded UI data. Aim for ten eligible reviews only if the real source-discovery and ingestion path supports them. Include failed sources in coverage. Load previously completed analysis without rerunning costly providers. Respect legal/platform restrictions on acquiring and displaying video content.

## Security & IP rules

Prompts, model provider routing, scraping/downloading internals, frame-sampling strategies, API keys, internal reasoning/model traces, proprietary scores and retry policy must remain server-side and absent from browser payloads. Gate expensive live analysis endpoints. Do not replace the existing agent or implement an entirely new agent framework. No fictional reports in a live demo; the synthetic fixture is **design-only** and must always retain its visible disclaimer.

## Acceptance criteria

- Complete, polished, responsive UI works with arbitrary industry/product queries.
- Optional references expand within the one input form.
- Real saved reports can populate all fields actually supported by the backend.
- Comparisons count **direct, source-grounded** matches and do not mistake incidental name mentions for competitor rankings.
- Real video evidence drawer opens exact matching source segments if available.
- Every displayed number is traceable and honest; unsupported charts display unavailable/empty states.
- Live processing uses real backend state; failures are not disguised as success.
- No hardcoded iPhone text in the generic app shell.
- No recommendation or opportunity-map section.
- Build/tests pass, with a short report of what is done, what is blocked, and how to run it.

First examine the local repository. Then integrate and test the supplied frontend. Preserve existing working pipeline functionality. Do not introduce a new framework solely to rewrite the frontend unless you can justify a concrete need.
