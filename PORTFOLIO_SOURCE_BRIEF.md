# Portfolio Source Brief

## Purpose

This file is a derivative portfolio-source brief built from
`PUBLIC_CLAIMS.md`. It organizes the currently allowed repo-backed claims,
qualifiers, limitations, and evidence anchors for later outward-facing copy.
It is not final outward-facing copy, benchmark prose, or website text.

Evidence: [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md),
[BUILDLOG.md](BUILDLOG.md), [PLAN.md](PLAN.md#what-is-in-progress)

## Usage Rules

- `PUBLIC_CLAIMS.md` is the sole claim source. If there is any tension between
  this brief and any other draft or doc, `PUBLIC_CLAIMS.md` wins.
- Keep wording conservative, technical, and repo-local.
- Do not widen comparisons beyond the fixed internal quad matrix.
- Do not remove current qualifiers or limitations when adapting this brief into
  later copy.

Evidence: [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#allowed-claims),
[PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#required-qualifiers),
[PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#disallowed-phrasings)

## Repo Snapshot

Context IR is currently an in-progress semantic-first Python context compiler
for coding agents. It analyzes a supported static Python subset into a
`SemanticProgram`, derives proven dependencies plus explicit unresolved or
unsupported frontier, and compiles budgeted context. The repo is in the
evidence-building phase after the accepted semantic-first baseline.

Evidence: [README.md](README.md), [PLAN.md](PLAN.md#current-phase),
[EVAL.md](EVAL.md#supported-claims-today)

## Current Public Surface

- Low-level analyzer: `analyze_repository(...)`
- Typed compile facade: `compile_repository_context(...)`
- Minimal MCP stdio wrapper: one tested `compile_repository_context` tool only

This is the current public technical surface. Broader MCP or product framing is
out of scope for later copy unless new evidence gates are cleared first.

Evidence: [README.md](README.md#python-api),
[README.md](README.md#minimal-mcp-usage),
[EVAL.md](EVAL.md#supported-claims-today),
[PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#allowed-claims)

## Current Evidence Surface

The repo contains a deterministic internal eval harness with summary, report,
pipeline, manifest, and bundle artifacts over fixed run specs and JSONL
ledgers. The accepted current top internal evidence surface is the four-asset
quad matrix in
`evals/run_specs/oracle_signal_quad_matrix.json`. The triple matrix remains
prior internal evidence, not the current top surface.

Evidence: [EVAL.md](EVAL.md#current-evidence-status),
[EVAL.md](EVAL.md#evidence-categories),
[evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json),
[evals/run_specs/oracle_signal_triple_matrix.json](evals/run_specs/oracle_signal_triple_matrix.json),
[BUILDLOG.md](BUILDLOG.md)

## Fixed Comparison Frame

The only allowed comparative statement is this fixed-scope internal statement:
within the accepted quad matrix only (`oracle_signal_smoke`,
`oracle_signal_smoke_b`, `oracle_signal_smoke_c`, and
`oracle_signal_smoke_d` at budgets `200` and `240` against
`lexical_top_k_files` and `import_neighborhood_files`), `context_ir` wins all
`8/8` task-budget rows and has the top provider-average aggregate score. Do not
generalize this beyond that matrix.

Evidence: [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#allowed-claims),
[EVAL.md](EVAL.md#supported-claims-today),
[evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json),
[BUILDLOG.md](BUILDLOG.md)

## Current Limitation

- Preserve the accepted tight-budget limitation:
  `oracle_signal_smoke_b / 200` still records `budget_pressure`.
- Preserve the omitted-support caveat:
  `def:pkg/digest.py:pkg.digest.render_assignment_digest` can remain omitted
  under that budget.
- Treat this as a current limitation to carry forward honestly, not as a defect
  to silently optimize away in later copy.

Evidence: [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#required-qualifiers),
[EVAL.md](EVAL.md#current-evidence-status),
[EVAL.md](EVAL.md#supported-claims-today),
[PLAN.md](PLAN.md#what-is-in-progress)

## Non-Claims And Future Gates

Not currently claimable:

- external benchmark or SWE-bench results
- production readiness
- performance, latency, token savings, or cost reduction
- multi-language analysis
- broader MCP or product interoperability claims beyond the minimal tested
  wrapper

Future public expansion requires repo-backed evidence and the gates recorded in
`EVAL.md`. This brief should not pre-claim them.

Evidence: [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#disallowed-phrasings),
[EVAL.md](EVAL.md#unsupported-claims-today),
[EVAL.md](EVAL.md#future-eval-plan),
[EVAL.md](EVAL.md#acceptance-criteria-for-future-public-claims)

## Claim Anchor Table

Evidence: [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#evidence-map),
[README.md](README.md), [EVAL.md](EVAL.md), [PLAN.md](PLAN.md)

| Claim ID | Allowed claim summary | Exact repo anchors |
| --- | --- | --- |
| AC1 | Context IR is an in-progress semantic-first Python context compiler over a supported static Python subset. | [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#evidence-map), [README.md](README.md), [EVAL.md](EVAL.md#supported-claims-today), [PLAN.md](PLAN.md#project) |
| AC2 | Public interface claims are limited to `analyze_repository(...)`, `compile_repository_context(...)`, and one tested MCP compile tool. | [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#evidence-map), [README.md](README.md#python-api), [README.md](README.md#minimal-mcp-usage), [EVAL.md](EVAL.md#supported-claims-today) |
| AC3 | Deterministic internal eval infrastructure exists; the triple matrix is prior internal evidence and the quad matrix is the current top internal surface. | [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#evidence-map), [EVAL.md](EVAL.md#current-evidence-status), [EVAL.md](EVAL.md#evidence-categories), [evals/run_specs/oracle_signal_triple_matrix.json](evals/run_specs/oracle_signal_triple_matrix.json), [evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json) |
| AC4 | The only allowed comparative claim is the fixed-scope quad-matrix statement: within that matrix only, `context_ir` wins all `8/8` task-budget rows and leads the provider-average aggregate. | [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md#evidence-map), [EVAL.md](EVAL.md#supported-claims-today), [evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json), [BUILDLOG.md](BUILDLOG.md) |
