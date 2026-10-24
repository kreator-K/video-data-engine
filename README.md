# Video Data Agent

A video-native brand and product insights studio. Enter a topic, optionally add YouTube references, and analyze up to ten source videos through the existing multimodal pipeline. Findings link to source videos, transcript timestamps, and sampled visual evidence.

## Current status

The [protected hosted app](https://video-data-agent-glomeyo.vercel.app) is approved for **Mac-assisted testing**. The frontend and authenticated API run on Vercel, reports and immutable evidence live in the linked PostgreSQL database, and a worker on the Mac processes queued jobs.

The autonomous Vercel worker is disabled: YouTube rejected downloads from its datacenter environment with a bot-verification challenge. Moving processing to the Mac passed a fresh end-to-end acceptance run. The Mac must remain awake, online, and running the worker. This is not approval for an independently available cloud production service.

Latest verification:

- 139 Python tests passed; one opt-in PostgreSQL test skipped in the standard suite. A separate live PostgreSQL acceptance run passed.
- Frontend logic, build, reconnect, identifier-preservation, and copy checks passed.
- Independent QA verified a fresh one-video Mac run: seven spoken-evidence entries matched original text and timestamps, and three hosted images matched original frame hashes.
- The fresh report contained four grounded attributes and zero direct comparisons. Its completed history entry and report reopened correctly through the hosted API.
- QA also verified the saved ten-video dataset: 223 spoken-evidence entries and 30 source images.

See [independent QA](docs/qa-independent-regression.md), [Mac worker testing](docs/mac-worker-testing.md), and [deployment readiness](docs/production-readiness-qa.md).

## What the studio shows

- Evidence-backed brand insights and product attribute sentiment.
- Direct competitor comparisons and the most-compared product, when supported by explicit source quotations.
- Recurring themes and video-by-attribute coverage.
- Timestamped transcript evidence and sampled visual moments.
- Genuine job progress and completed analysis history.

Only completed jobs enter saved analysis history. Empty or failed runs do not produce invented findings. Comparison coverage counts distinct videos rather than repeated mentions. Sentiment describes coded reviewer observations, not a representative consumer survey. The synthetic design fixture is for local UI preview and is unavailable in production.

Frontend text must never display Unicode U+2014. Dynamic display text is normalized at the rendering boundary; raw evidence, identifiers, URLs, and backend analysis remain intact. The frontend build enforces this rule.

## Architecture

```text
Browser dashboard
    -> authenticated HTTP API on Vercel
    -> durable PostgreSQL job queue
    -> Mac worker claims and renews a job lease
    -> isolated original video pipeline
         yt-dlp download + metadata
         OpenCV frame extraction + timestamp manifest
         local Whisper transcription
         Anthropic frame analysis
         NVIDIA report synthesis, with bounded Anthropic fallback
         transcript-grounded attribute and comparison extraction
    -> persisted report + immutable, content-addressed evidence
    -> dashboard polls status and opens completed results
```

The local dashboard uses SQLite by default and starts a separate worker process. Hosted operation uses PostgreSQL. Jobs have ownership checks, admission quotas, leases, and stale-worker fencing. Interrupted in-flight paid work is not silently replayed; untouched queued sources can resume. Evidence images require access to an owning completed analysis.

## Local setup

On Apple Silicon macOS:

```sh
brew install python@3.11 ffmpeg
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -c requirements-macos-py311.lock.txt
python -m pip install -r requirements-dev.txt
python -m pip check
```

Select `.venv/bin/python` as the editor interpreter. See the [Python environment record](docs/python-environment-migration.md) for environment details.

Create an ignored `.env` in the repository root:

```dotenv
VISION_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key
NVIDIA_API_KEY=your_nvidia_key
```

Optional settings:

```dotenv
ANTHROPIC_VISION_MODEL=claude-sonnet-4-5
ANTHROPIC_REPORT_MODEL=claude-sonnet-4-5
REPORT_MODEL=meta/llama-3.1-8b-instruct
# Use NVIDIA_API_KEYS instead of NVIDIA_API_KEY for comma-separated keys.
# Configure local download authentication only if required:
# YTDLP_COOKIES_BROWSER=chrome
# YTDLP_COOKIES_FILE=/absolute/path/to/cookies.txt
```

No OpenAI API key is needed for the configured Anthropic vision path. Whisper runs locally. Anthropic and NVIDIA calls use the configured accounts and may incur charges. Never commit credentials or export browser cookies to cloud hosting as part of ordinary setup.

NVIDIA is the primary report synthesizer. Context-limit errors and typed provider timeouts fall back to Anthropic with the same evidence prompt. Authentication, rate-limit, and invalid-model errors do not trigger that fallback. Reports retain provider, model, and fallback-reason metadata internally.

### Start the local dashboard

```sh
.venv/bin/python serve_frontend.py
```

Open [localhost:4173](http://127.0.0.1:4173). The server starts a separate local worker unless `--no-worker` is supplied. Starting an analysis can make real provider calls. Keep the server and worker running while processing.

### Process hosted jobs on the Mac

The repository must already be linked to the intended Vercel project. Pull its configuration into an ignored file using an authorized Vercel account:

```sh
vercel env pull .env.vercel.local
caffeinate -i .venv/bin/python scripts/run_mac_worker.py
```

The launcher reads provider and download settings from `.env` and the linked PostgreSQL connection from `.env.vercel.local`. No inbound Mac port or tunnel is required. Stop a foreground worker with Ctrl+C. The cloud daemon currently has an `iad1=0` scaling override to prevent it consuming these test jobs; leave it disabled until cloud ingestion is resolved.

Detailed operational notes and the one-shot acceptance utility are in [Mac worker testing](docs/mac-worker-testing.md).

## Command-line processing

Single video:

```sh
.venv/bin/python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Topic discovery and analysis:

```sh
.venv/bin/python run_search.py "wireless headphones reviews"
```

Discovery selects up to ten unique eligible non-live sources and filters obvious promotional, trailer, and rumor titles for review queries. Eligibility filtering does not guarantee that every result is a substantive review. Failures are recorded and remaining sources continue; displayed coverage reflects actual completed sources.

Batch URLs:

```sh
.venv/bin/python run_batch.py --file urls.txt
```

The batch runner also accepts positional URLs or `--stdin`, with `--dry-run`, `--no-dedupe`, `--stop-on-error`, and `--log-dir` options.

CLI artifacts are written under `data/videos/`, `data/frames/`, `data/search_runs/`, or `data/batch_runs/`. Hosted worker subprocess artifacts use isolated temporary workspaces; completed reports and selected immutable images are persisted to the database before cleanup. Runtime artifacts are excluded from Git.

## API and access

| Endpoint | Purpose |
| --- | --- |
| `POST /api/searches` | Admit a durable analysis job |
| `GET /api/searches/{id}` | Read owned job progress or completed result |
| `GET /api/analyses` | List owned completed analyses |
| `GET /api/analyses/{id}` | Open an owned completed report |
| `GET /api/evidence/{sha256}.jpg` | Retrieve an authorized immutable evidence image |

Hosted requests require application authentication in addition to Vercel deployment protection. User credentials are configured server-side through `STUDIO_USERS_JSON`; they are not embedded in frontend assets. Production fails closed when authentication or database configuration is missing. The local server is restricted to loopback hosts by default.

The normal configured admission limits are one active job per user, three daily jobs per user, ten daily jobs globally, and four pending jobs. Failed admitted jobs count toward daily limits. Disposable acceptance fixtures are managed separately from actual user analyses.

## Validation

```sh
.venv/bin/python -m pytest -q
.venv/bin/python build_frontend.py
```

The standard suite uses deterministic provider stubs and local stores. It does not prove live provider availability. The PostgreSQL acceptance test is opt-in through `QA_POSTGRES_URL`; supply it securely without printing connection details.

For local media processing without model API calls, use an available video and cached Whisper model:

```sh
.venv/bin/python tests/local_video_smoke.py "/absolute/path/to/video.mp4"
```

Historical vision evaluation and reviewed-label workflows remain under `eval/`. Their dataset-specific scores are not a quality guarantee for current studio analysis. See `eval/run_eval.py`, `eval/run_refinement_loop.py`, and `eval/run_model_ab.py`; live evaluations make provider calls. Protected golden datasets must not be modified casually.

## Limits and remaining work

- Autonomous cloud YouTube ingestion remains blocked. Mac availability is required for the current testing topology.
- YouTube formats, access challenges, private videos, and extraction changes can prevent processing. The downloader tries public format/client fallbacks before configured local authentication.
- Long videos and large downloads are bounded in the worker configuration. Runtime varies with duration, transcription, provider latency, and source count; no fixed completion time is promised.
- Whisper can mishear speech, and sampled frames do not cover every visual moment. Exact transcript matching verifies extraction grounding, not that transcription itself is perfect.
- Model extraction can omit findings or classify sentiment imperfectly. Specific comparisons are displayed only with direct quoted support; absent support stays absent.
- The Mac acceptance run validates one source. It does not establish a fresh ten-source cloud run or autonomous production readiness.

## Main files

| Path | Responsibility |
| --- | --- |
| `frontend/` | Dependency-free dashboard and evidence interactions |
| `src/http_app.py`, `app.py`, `serve_frontend.py` | Shared HTTP boundary, hosted adapter, local server |
| `src/job_store.py` | Durable queue, ownership, quotas, leases, reports, image storage |
| `worker.py`, `execute_source.py` | Worker loop and isolated pipeline subprocesses |
| `main.py`, `src/downloader.py`, `src/frame_extractor.py`, `src/transcriber.py` | Original media-processing pipeline |
| `src/vision_analyser.py`, `src/synthesiser.py` | Existing configured model stages |
| `src/grounded_insights.py`, `src/presentation.py` | Grounded extraction, aggregation, and report contract |
| `scripts/run_mac_worker.py` | Hosted-queue worker launcher for this Mac |
| `tests/`, `docs/` | Regression coverage, QA evidence, and operational documentation |
