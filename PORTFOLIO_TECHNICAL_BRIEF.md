# Context IR Technical Brief

## What It Is

Context IR is an in-progress semantic-first Python context compiler for coding
agents. It analyzes a supported static Python subset into a `SemanticProgram`,
derives proven dependencies plus explicit unresolved or unsupported frontier,
and compiles budgeted context. The current brief is a conservative technical
summary of the repo's public surface and evidence state, not a new claim
authority.

## Current Public Surface

The current outward-facing surface is intentionally narrow:

- `analyze_repository(...)` as the low-level analyzer
- `compile_repository_context(...)` as the typed compile facade
- a minimal MCP stdio wrapper that exposes one tested
  `compile_repository_context` tool

This is the present technical interface boundary. It should not be read as a
broader MCP or product claim.

## Current Evidence Snapshot

Current evidence is deterministic internal evidence from repo-local tests,
quality gates, and the eval harness. The repo includes summary, report,
pipeline, manifest, and bundle artifacts over fixed run specs and JSONL
ledgers. The current top evidence surface is the accepted internal quad matrix.

Within that fixed internal quad matrix only, `context_ir` leads all `8/8`
task-budget rows and has the top provider-average aggregate. That comparison is
limited to the accepted matrix over `oracle_signal_smoke`,
`oracle_signal_smoke_b`, `oracle_signal_smoke_c`, and
`oracle_signal_smoke_d` at budgets `200` and `240` against
`lexical_top_k_files` and `import_neighborhood_files`.

## Current Limitation

The current surface is not uniformly clean. `oracle_signal_smoke_b / 200`
still records `budget_pressure`, and
`def:pkg/digest.py:pkg.digest.render_assignment_digest` can remain omitted
under that tight budget. This limitation is part of the accepted current
evidence state and should be carried forward honestly.

## What It Does Not Claim

This brief does not claim broader Python semantics beyond the supported subset,
broader MCP interoperability than the minimal wrapper, multi-language analysis,
external evaluation leadership, or measured performance and efficiency
outcomes. `PUBLIC_CLAIMS.md` remains the sole claim source; this document is a
repo-native summary for external technical review.

## Repo Anchors

- [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md) is the claim boundary and sole claim
  source.
- [PORTFOLIO_SOURCE_BRIEF.md](PORTFOLIO_SOURCE_BRIEF.md) is the derivative
  source brief for this document.
- [README.md](README.md) documents the current public interface and minimal MCP
  wrapper.
- [EVAL.md](EVAL.md) records the current evidence surface, supported claims,
  and current limitation.
- [PLAN.md](PLAN.md) records current phase and accepted project state.
- [BUILDLOG.md](BUILDLOG.md) records accepted evidence-review decisions.
