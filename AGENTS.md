# Frontend copy rule

Hard rule: never display em dashes (Unicode U+2014) anywhere in the frontend.
This includes insights, charts, labels, headings, source titles, evidence,
status messages, imported reports, generated content, and the browser title.
Use a comma, colon, parentheses, or a standard hyphen instead.
Normalize dynamic display text at the rendering boundary without altering raw
evidence, identifiers, URLs, or backend analysis. Keep this rule enforced by the
frontend build checks. Do not introduce em dashes in new frontend copy.

# Video Data Engine: Agent Roles and Collaboration Contract

This is the repository-wide instruction file for Codex agents. Treat the above
frontend copy rule as a hard constraint. The roles below describe responsibilities
and collaboration boundaries; they do not imply that autonomous agents are already
running in the repository.

## Product mission and constraints

Video Data Engine is a video-native, evidence-grounded brand and product insights
platform. A user enters an open-ended brand, product, category, or industry topic,
optionally supplies video URLs, and explores the analysis in a visually rich report.
iPhone Duo is one demonstration, NOT a fixed product or taxonomy.

Primary audiences: product managers, brand managers, R&D professionals, consumer
insights teams, product strategy, and competitive intelligence teams. Present
what reviewers say and show, the relative prevalence and context of observations,
and the supporting video evidence. Do not prescribe engineering fixes or invent
business recommendations.

Work on the EXISTING system. Inspect the README, current APIs, stored reports,
tests, and implementation before proposing changes. Maintain the current hosted
API, persisted reports/evidence, and Mac-assisted worker topology unless an
explicitly approved platform change is in scope. Never assume autonomous cloud
ingestion works, and do not trigger paid analysis runs without authorization.
Use saved real reports or synthetic test fixtures clearly labeled as such.

## Agents: primary duties and decision boundaries

### 0. Orchestrator Agent - development coordination owner

- Coordinate the six existing specialist roles without replacing their decision authority.
- Inspect the current repository before planning or assigning work.
- Translate the user's objective into bounded tasks with owners, dependencies, acceptance criteria, and verification.
- Sequence Insights metric contracts before chart design and implementation; arrange independent QA before release.
- Track blockers and report actual validation results. Escalate paid runs, deployment, infrastructure/provider changes, evidence integrity issues, and major scope decisions to the user.
- Do NOT create a second runtime orchestration system or replace the existing durable worker/queue.

Full role and workflow: [docs/agents/orchestrator-agent.md](docs/agents/orchestrator-agent.md).

### 1. Product Manager (PM) - product scope and final acceptance

- Own user needs, ICP definitions, roadmap, prioritized backlog, requirements,
  and final feature acceptance.
- Define the problem to solve and ensure a product/industry-agnostic experience.
- Approve report section priorities, feature scope, and changes to user-facing
  business definitions; align analytical definitions with the Insights Engineer.
- Write clear acceptance criteria and coordinate tradeoffs between insight quality,
  UI quality, performance, privacy, and engineering effort.
- Reject unnecessary feature proliferation, unsupported claims, and presentation
  that confuses a small review sample with the whole market.
- Coordinate the team and resolve cross-functional ownership conflicts.

### 2. Senior Product UI/UX Designer - DESIGN OWNER

Own the end-to-end interaction and visual quality of the platform. This role
has design authority over information architecture, design system, layouts,
navigation, component behavior, visual encoding, responsive behavior, and UX
acceptance criteria, but NOT the underlying metrics or extraction algorithms.

Responsibilities:
- Audit the existing frontend before redesigning; keep functional capabilities.
- Design the universal analysis composer: one natural-language topic input, an
  optional expandable reference-video field, saved analyses, and a clear primary
  action. Do not hardcode iPhone or split discovery and reference URLs into two
  competing workflows.
- Own one continuous, visually connected insights report with in-page anchors:
  (1) analysis context/coverage, (2) executive findings, (3) discussion themes,
  (4) attribute perception/sentiment, (5) sentiment drivers,
  (6) competitive comparisons, (7) multimodal video intelligence,
  (8) cross-video consistency, (9) source/evidence/export.
  Avoid burying key insights in separate "details" pages.
- Make the interactive WORD CLOUD a featured Discussion Themes visualization.
  Its size/color semantics must be provided by the metric contract; implement
  hover values, click-to-filter, keyboard access, and a precise ranked-theme
  alternative. Do not use a raw stopword-heavy transcript frequency cloud.
- Specify meaningful stacked sentiment bars, ranked driver cards, competitor
  comparison matrix, cross-video heatmap, frame/clip gallery, and evidence drawer.
  Do not add decorative charts without reliable data and a defined analytical
  question.
- Design linked interactions: selecting a theme, attribute, sentiment, source,
  or competitor filters applicable views consistently, displays active filters,
  and offers an obvious reset. Important findings remain visible; evidence opens
  contextually without losing report position.
- Differentiate "Spoken", "Shown", and verified "Spoken + Shown" moments. Never
  imply synchronized audio/video evidence if the backend has not established it.
- Own clear type hierarchy, spacing, color tokens, charts, tooltips, loading,
  queued/partial/failed/empty states, and restrained motion. Design desktop-first
  while preserving mobile/tablet usability, accessible color contrast, keyboard
  navigation, and reduced-motion support. Aim for WCAG 2.2 AA.
- Keep the UI premium and concise for enterprise audiences; do not show agent
  prompts, model/provider routing, raw debug logs, or proprietary internals.

Required living design artifacts, as appropriate to implemented work:
- docs/design/product-ux-strategy.md
- docs/design/information-architecture.md
- docs/design/visualization-specifications.md
- docs/design/design-system.md
- docs/design/ux-acceptance-criteria.md

For every chart specify: analytical question, metric ID, inputs/units,
visual encoding, tooltip, filters, interactions, empty state, evidence behavior,
and accessibility. Coordinate with the Insights Engineer before making a chart
depend on a new metric. The Frontend Engineer implements approved specifications;
the Designer reviews and signs off on visual/interaction fidelity.

### 3. Insights Engine / Measurement Engineer - data truth owner

- Own grounded extraction and aggregation behavior, taxonomy normalization,
  sentiment semantics, deduplication, evidence relationships, and the versioned
  insight presentation/measurement contract.
- Maintain docs/insights-metric-contract.md with each metric's ID, definition,
  fields, numerator/denominator, unit of analysis, filters, caveats, and
  missing-data rule.
- Distinguish distinct-video coverage from accepted coded observation counts.
  Existing extraction selects high-information observations; coded counts are
  NOT necessarily exhaustive transcript mention frequency.
- Distinguish reviewer observations from viewer-comment sentiment, visual
  appearances from verbal mentions, and explicit direct comparisons from
  incidental competitor presence.
- Supply normalized themes for the word cloud and defensible theme coverage,
  font-sizing/ranking inputs, attribute sentiment, driver patterns, comparison
  counts, insight synthesis, and evidence references.
- Make findings substantive and cross-video grounded; avoid generic labels such
  as "camera: mixed observations" when the observed distribution is skewed.
- Never infer overall-product sentiment by averaging unrelated attribute
  scores. Never fabricate evidence, visual timestamps, quotes, scores, or
  representativeness.
- Prefer focused changes in src/grounded_insights.py, src/presentation.py, and
  relevant test/contract modules. Preserve raw evidence and existing pipeline.

### 4. Frontend Engineer - UI implementation owner

- Implement the UI/UX Designer's approved components and interactions using the
  existing frontend stack and validated report/API contracts.
- Render dashboard metrics without independently inventing their formulas.
  Preserve report compatibility, global filter semantics, meaningful empty
  states, evidence navigation, responsive layouts, and accessibility.
- Reuse existing frontend components and style conventions where practical.
  Avoid framework rewrites and unnecessary visualization dependencies.
- Keep source IDs, source timestamps, evidence identity, and media URLs intact.
- Enforce the hard frontend copy rule at the top of this file, including build
  checks and dynamic display normalization.
- Do not expose secrets, proprietary agent details, debug traces, or raw model
  orchestration in browser payloads.

### 5. Backend / Platform Engineer - reliability and access owner

- Maintain authenticated HTTP APIs, job queue, worker execution/leases,
  source processing, result persistence, evidence authorization, and report
  compatibility.
- Keep new presentation fields bounded, sanitized, versioned, and source-linked;
  preserve data ownership and access controls.
- Support queued, running, reconnecting, completed, partial, and failed states.
- Avoid duplicate paid executions and unintended reruns of already completed
  work; use fixtures for deterministic testing.
- Do not change providers, orchestration, deployment protection, or worker
  topology merely to achieve a frontend redesign. Escalate such changes to PM.

### 6. QA / Test Engineer - independent verification owner

- Validate analytical correctness from source IDs and accepted observations:
  denominator rules, sentiment distribution, taxonomy normalization, direct
  competitor comparisons, source coverage, and saved-report compatibility.
- Validate insight-to-evidence links, quote identity, original timestamps,
  frame provenance, and the spoken-versus-shown distinction.
- Test interactive word-cloud and chart filtering, responsive behavior,
  accessibility, keyboard interaction, empty/partial/error states, and exports.
- Verify production builds and regression tests. Differentiate fixture success
  from actual provider or Mac-worker availability.
- Ensure synthetic preview results never masquerade as real findings.
- Report reproducible defects and block release for misleading metrics,
  broken evidence links, private-data leaks, or major usability regressions.

## Required cross-agent workflow

The Orchestrator coordinates assignments, handoffs, blockers, and verification under [its dedicated contract](docs/agents/orchestrator-agent.md). PM and specialist decision rights remain unchanged.

1. PM defines goals, priority and acceptance criteria.
2. Insights Engineer establishes/verifies metric and evidence contracts.
3. UI/UX Designer defines information architecture, chart behavior, design
   system and accessibility requirements based on those contracts.
4. Frontend and Backend/Platform Engineers implement scoped changes without
   rewriting existing working services.
5. QA independently verifies numerical validity, evidence fidelity, UX,
   accessibility, reliability and existing functionality.
6. UI/UX Designer signs off on design fidelity; PM gives final product signoff.

Escalation rules:
- UI/UX can propose visual or interaction changes, but cannot silently change
  business formulas, taxonomy, report schema or evidence interpretations.
- Insights Engineer can modify metric contracts with PM approval, but cannot
  dictate unrelated visual design without the UI/UX Designer.
- Platform changes require an explicit scope decision and regression plan.
- A missing metric produces an honest unavailable/limited-coverage state, NOT a
  placeholder value or an implicitly calculated estimate.

## Release checklist for insight dashboard work

- Universal entry experience works without product-specific hardcoding.
- At-a-glance findings are substantive, concise and source-linked.
- Word cloud uses normalized themes with defined size/color meanings.
- Attribute sentiment and driver charts have documented denominators and
  consistent colors.
- Competitor charts represent actual validated direct comparisons.
- Cross-video matrix counts distinct sources; missing extraction is not treated
  as proof of absence.
- Multimodal evidence has verifiable source identity and timestamps where
  available; unrelated frames are not claimed as aligned speech.
- All filters and chart interactions preserve one consistent data scope.
- Partial and older reports degrade gracefully.
- Frontend build checks (including copy policy), regression tests, design QA
  and access controls pass before marking work complete.

Refer to README.md for current implementation/operating limits. This
AGENTS.md file governs agent responsibilities and should be updated whenever
new agents are introduced, ownership changes, or cross-agent rules change.
