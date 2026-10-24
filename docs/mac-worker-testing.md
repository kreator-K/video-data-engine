# Mac worker testing

The hosted frontend and authenticated API remain on Vercel. The Mac runs the existing video pipeline, claims jobs from the shared PostgreSQL queue, and stores completed reports and immutable evidence in that same database. Browser sessions do not receive provider credentials or database credentials. No inbound port or tunnel to the Mac is required.

## Run the worker

From the repository directory, use:

```sh
caffeinate -i .venv/bin/python scripts/run_mac_worker.py
```

The launcher reads local provider settings from `.env` and the linked database connection from `.env.vercel.local`. Existing local download authentication settings remain on the Mac. Stop with Ctrl+C. Keep the Mac connected, awake, and running the worker while testing hosted analysis. Sleep, logout, process termination, or network failure interrupts availability. This setup is for testing and is not an independently available production worker.

The failing Vercel daemon has a scaling override of zero instances in `iad1`, preventing it from consuming Mac test jobs. Do not reset that override until cloud video ingestion is resolved. The queued-job lease prevents concurrent processing and fences expired workers; interrupted paid work is not automatically replayed.

## Acceptance run

`scripts/accept_mac_worker.py` submits and executes a single short real-source acceptance job, then prints its safe terminal status. It temporarily permits eight daily jobs for that process only because earlier failed cloud tests consumed the ordinary demo quota. The hosted API's normal quota is unchanged. This is a test utility, not the regular worker launcher.

The first Mac run successfully downloaded the source and generated transcript/frame artifacts, then failed on NVIDIA report synthesis timeout. Typed NVIDIA timeouts now use the existing Anthropic report fallback with the identical evidence prompt. Authentication failures, invalid models and rate-limit failures are not reclassified as timeouts. The fallback has a deterministic regression test.

A subsequent run reached report synthesis, then exposed macOS temporary-path aliasing (`/var` versus `/private/var`) in the artifact containment check. The worker now resolves its workspace before comparing resolved evidence paths. A filesystem-symlink regression verifies valid aliased workspaces without widening artifact access.

## Accepted result, 23 October 2026

Fresh job `5746cd5c343840d08ae1be9aa2a85743` completed through the original pipeline on the Mac and persisted its result in the shared cloud database. Independent QA verified all seven spoken-evidence entries against freshly captured transcript text and timestamp bounds. All three remotely fetched JPEGs match both their content-addressed digests and original source-frame bytes. The report contains four grounded attributes and zero direct comparisons, reopens identically through the hosted API, and appears in completed history.

The full local suite passes 139 tests with one optional database test skipped; frontend build checks pass. QA approves the protected Mac-assisted testing topology only. The autonomous Vercel worker remains disabled because cloud YouTube ingestion is unresolved. A continuous Mac worker was started with `caffeinate -i`, using the regular launcher and normal admission quotas.

Four explicitly identified disposable failed acceptance jobs were removed with owner/status guards in a transaction, preserving shared image blobs and both completed analyses. The ordinary API quota was not increased. The one-shot acceptance utility's allowance applies only within that test process.
