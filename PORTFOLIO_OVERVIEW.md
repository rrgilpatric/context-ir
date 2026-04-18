# Context IR Overview

## What Problem This Project Tackles

Context IR is an in-progress semantic-first Python context compiler for coding
agents. The repo is focused on a specific problem: how to build budgeted
repository context from semantic structure instead of relying only on file-level
lexical retrieval. Today the system analyzes a supported static Python subset
into a `SemanticProgram`, separates proven dependencies from explicit
unresolved or unsupported frontier, and then compiles context under a budget.
The project is still in an evidence-building phase, so this overview is a
reviewer-orientation layer rather than a claim source or case study.

## Why Semantic-First

The design direction matters because the repo’s current thesis is that context
selection should begin from what the analyzer can actually prove about
repository structure. In the current narrow static Python subset, that means
tracking definitions, imports, lexical bindings, direct supported references,
and narrow class-level `@dataclass` handling where it resolves to
`dataclasses.dataclass`. When the analyzer cannot prove a fact, it records
uncertainty explicitly instead of fabricating support. That makes the current
surface more conservative than broad retrieval claims and is the main reason
the semantic-first direction is central to the project.

## What Exists In The Repo Today

The current repo-backed public surface is intentionally small. There is a
low-level `analyze_repository(...)` analyzer, a typed
`compile_repository_context(...)` facade, and a minimal stdio MCP wrapper that
exposes one tested `compile_repository_context` tool. Around that surface, the
repo contains local tests, strict quality gates, and a deterministic internal
eval harness with summary, report, pipeline, manifest, and bundle artifacts
over fixed run specs and JSONL ledgers. The current outward-facing document
stack is the [README.md](README.md), the claim boundary in
[PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md), the derivative
[PORTFOLIO_SOURCE_BRIEF.md](PORTFOLIO_SOURCE_BRIEF.md), and the outward-facing
[PORTFOLIO_TECHNICAL_BRIEF.md](PORTFOLIO_TECHNICAL_BRIEF.md).

## Current Evidence And Boundaries

Current evidence is deterministic internal evidence from repo-local tests,
quality gates, and the internal eval harness. The current top evidence surface
is the accepted internal quad matrix over `oracle_signal_smoke`,
`oracle_signal_smoke_b`, `oracle_signal_smoke_c`, and
`oracle_signal_smoke_d` at budgets `200` and `240` against
`lexical_top_k_files` and `import_neighborhood_files`. Within that accepted
internal quad matrix only, `context_ir` leads all `8/8` task-budget rows and
the top provider-average aggregate. That comparison is intentionally narrow and
subordinate to the rest of the evidence picture. This repo does not currently
claim external benchmark standing, broader MCP interoperability, deployment
maturity, measured efficiency gains, or multi-language analysis.
[PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md) remains the sole claim source.

## Current Limitation

The current evidence surface is not uniformly clean. The accepted limitation is
that `oracle_signal_smoke_b / 200` still records `budget_pressure`, and
`def:pkg/digest.py:pkg.digest.render_assignment_digest` can remain omitted
under that tight budget. This limitation is part of the current honest evidence
state and should be read as a present boundary, not as a hidden footnote.

## Reading Path

Start with [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md) for the exact allowed claim
envelope. Read [PORTFOLIO_TECHNICAL_BRIEF.md](PORTFOLIO_TECHNICAL_BRIEF.md) for
the short technical summary of the public surface and evidence state. Use
[README.md](README.md) for the concrete API and minimal MCP interface. Read
[EVAL.md](EVAL.md) for the evidence ledger, supported claims, unsupported
claims, and future gates. Use [PLAN.md](PLAN.md) for current phase and what is
in or out of scope, and [BUILDLOG.md](BUILDLOG.md) for accepted review history
behind the current repo state.
