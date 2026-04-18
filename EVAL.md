# EVAL.md -- Evidence and Methodology Baseline

## Purpose

This file records what the repository currently proves, what it only quality-gates locally, and what remains unevaluated. It is an evidence ledger, not a benchmark report or portfolio narrative.

## Current Evidence Status

The current semantic-first baseline is supported by repo-local tests and
accepted BUILDLOG entries through the deterministic internal eval harness and
the current four-asset signal quad matrix.

Proven by current unit and integration tests:

- Semantic contracts expose `SyntaxProgram`, `SemanticProgram`, proof status, supported-subset, unresolved-frontier, unsupported-construct, diagnostic, optimization, compile, diagnose, and recompile dataclasses.
- Syntax extraction records supported Python source inventory, definitions, imports, parameters, decorators, bases, assignments, call sites, attribute sites, parse diagnostics, and source spans for the tested fixture cases.
- Binder behavior records definition, import, parameter, assignment, and class-attribute bindings by lexical scope while excluding syntax-invalid files from semantic facts.
- Resolver behavior proves supported repository imports, direct simple-name calls, direct attribute references, imported bases, and narrow `dataclasses.dataclass` facts for tested cases.
- Dependency/frontier derivation creates repository-backed import, call, inheritance, and decorator dependencies, and surfaces unresolved or unsupported constructs explicitly for tested frontier cases.
- Semantic renderer, scorer, optimizer, compiler, diagnose, and recompile behavior is covered for the tested scenarios, including uncertainty rendering, bounded scores, budget honesty for emitted documents, grounded miss diagnosis, and conservative ungrounded-evidence handling.
- `analyze_repository(repo_root) -> SemanticProgram` orchestrates the accepted semantic pipeline and is the only promoted package-root function.
- Package-root exports are quarantined to semantic-first contracts; retired graph-first APIs remain directly importable only by explicit legacy module paths.
- `context_ir.tool_facade.compile_repository_context(...)` delegates to the accepted analyzer and semantic compiler, preserves uncertainty, diagnostics, selection trace, omitted units, and budget totals, and avoids retired graph-first APIs in tested cases.
- A minimal MCP wrapper exists over the tool facade with exactly one registered tool, `compile_repository_context`, JSON-safe serialization, invalid-budget handling, optional document omission, and tested local SDK invocation.
- Deterministic internal eval infrastructure exists end to end through typed
  summary, report, pipeline, manifest, and bundle artifacts over reproducible
  run specs and JSONL ledgers.
- Accepted methodology-tightened signal assets now include
  `oracle_signal_smoke`, `oracle_signal_smoke_b`, `oracle_signal_smoke_c`, and
  `oracle_signal_smoke_d`.
- The accepted current broader evidence surface is a quad matrix over 4 tasks x
  2 budgets x 3 providers. Within that fixed internal matrix, `context_ir`
  wins all 8/8 task-budget rows.
- Provider-average aggregate scores for the accepted quad matrix are:
  `context_ir = 0.9599139230003012`,
  `import_neighborhood_files = 0.6228480543023547`, and
  `lexical_top_k_files = 0.6065653086866415`.
- The earlier accepted triple matrix over `oracle_signal_smoke`,
  `oracle_signal_smoke_b`, and `oracle_signal_smoke_c` remains historical prior
  internal evidence, but it is not the current top surface.
- The quad matrix is not uniformly clean: `oracle_signal_smoke_b` at budget
  `200` still records honest `budget_pressure`, and the omitted support unit
  can still be
  `def:pkg/digest.py:pkg.digest.render_assignment_digest`.

Validated by local quality gates, not by benchmark evidence:

- Accepted slices in `BUILDLOG.md` record clean local runs of `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"`.
- The required full local validation gate for this repo is:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"`
- These gates establish lint, formatting, type, and regression-test health. They do not establish benchmark effectiveness, production readiness, external protocol completeness, or SWE-bench relevance.
- These gates are complementary to the deterministic internal eval harness.
  They do not turn the internal quad matrix into an external benchmark,
  production-readiness proof, external protocol completeness claim, or
  SWE-bench result.

Architecturally intended but not yet evaluated:

- Broader task sets beyond the current four accepted signal assets.
- Wider budget-curve measurements beyond the current fixed `200` and `240`
  budgets.
- Additional baseline comparisons beyond the current lexical and
  import-neighborhood providers.
- SWE-bench-style or other external-benchmark methodology, after the internal
  fixture surfaces are intentionally broadened.
- Production packaging, install/run ergonomics, and external MCP client compatibility beyond the tested local wrapper behavior.

## Evidence Categories

- Unit/integration tests: pytest coverage in `tests/` for semantic contracts, parser, binder, resolver, dependency/frontier, renderer, scorer, optimizer, compiler, diagnose/recompile, analyzer, public API, tool facade, and MCP wrapper behavior.
- Static quality gates: ruff lint, ruff format check, mypy strict, and non-slow pytest suite.
- Protocol smoke tests: current MCP evidence is limited to local SDK registration and local tool invocation in `tests/test_mcp_server.py`.
- Deterministic internal eval artifacts: raw JSONL ledger rows, typed summary
  loading and aggregation, Markdown report generation, pipeline composition,
  manifest generation, and nested bundle output are all present and tested.
- Current internal evidence surface: four methodology-tightened signal assets
  run as a 4 task x 2 budget x 3 provider quad matrix.
- Historical prior surface: the accepted pair/triple signal matrices remain
  useful historical internal evidence, but they are not the current top
  surface.
- External benchmark surfaces: still absent. The repo does not yet carry
  SWE-bench or other external benchmark task sets, public benchmark reporting,
  or public benchmark ledgers.
- Portfolio/public claims: must be limited to claims backed by the categories above.

## Supported Claims Today

The following claims are allowed because current repo artifacts support them:

- Context IR analyzes a supported static Python subset into a `SemanticProgram`.
- The analyzer composes syntax extraction, binding, resolving, and dependency/frontier derivation in that order.
- The supported subset includes repository Python modules, imports, functions, async functions, classes, methods, lexical bindings, and narrow class-level `@dataclass` support for tested forms.
- The analyzer surfaces unresolved and unsupported constructs explicitly instead of fabricating proof for tested frontier cases.
- Proven semantic dependencies are distinct from heuristic ranking candidates.
- Semantic rendering can emit identity, summary, and source-backed views for tested proven symbols, unresolved frontier items, and unsupported constructs.
- Semantic scoring ranks proven symbols, unresolved frontier items, and unsupported constructs without turning ranking signals into proof claims.
- The optimizer and compiler preserve budget honesty for emitted documents under tested scenarios.
- Diagnose/recompile can ground supported miss evidence to semantic units, distinguish omitted, too-shallow, and sufficient units, and keep ungrounded evidence honest in tested scenarios.
- The package root exposes semantic-first contracts and `analyze_repository(...)`, while retired graph-first APIs are quarantined from root exports.
- A typed tool-facing facade exists for semantic repository compile requests.
- A minimal MCP wrapper exists over the semantic compile facade with one tested compile tool.
- A deterministic internal eval harness exists through summary, report,
  pipeline, manifest, and bundle artifacts over fixed run specs and JSONL
  ledgers.
- The current top internal evidence surface is the four-asset signal quad
  matrix over `oracle_signal_smoke`, `oracle_signal_smoke_b`,
  `oracle_signal_smoke_c`, and `oracle_signal_smoke_d`.
- Within that fixed quad matrix only, `context_ir` is the sole winner on all
  8/8 task-budget rows and has the top provider-average aggregate score.
- The current internal evidence surface includes an explicit tight-budget
  blemish: `oracle_signal_smoke_b / 200` still records `budget_pressure`, and
  `def:pkg/digest.py:pkg.digest.render_assignment_digest` can remain omitted.

## Unsupported Claims Today

The following claims are not currently allowed:

- No SWE-bench, SWE-bench Mini, SWE-bench Verified, or SWE-bench-style improvement claims.
- No external benchmark improvement claims of any kind.
- No resolve-rate, edit-success-rate, retrieval-quality, area-under-budget-curve, or task-win-rate claims.
- No production-readiness claims.
- No multi-language claims.
- No broad Python dynamic-semantics claims, including dynamic imports, reflection, `exec`, `eval`, monkey patching, metaclasses, runtime attribute injection, or general decorator semantics.
- No claim that the MCP wrapper is a complete product integration beyond the minimal tested compile tool.
- No claim that the old graph-first stack or exact 5-tier renderer thesis is the current architecture.
- No claim that `p_edit` or `p_support` is the public thesis; they are internal ranking policy only.
- No performance, latency, token-savings, or cost-reduction claims without measured data.
- No claim that README or portfolio positioning has been fully synchronized with the accepted final-phase state.

## Future Eval Plan

Next smallest eval slices:

1. Expand beyond the current four accepted signal assets only when new tasks and
   claim boundaries are validated.
2. Broaden budget coverage beyond the current fixed `200` and `240` budgets
   with explicit raw-result storage and pass conditions.
3. Add further baseline families only if they can be introduced without
   weakening determinism or claim discipline.
4. Design external benchmark methodology only after the internal fixture
   surfaces are intentionally broadened and stabilized.
5. Add performance, token, or latency measurement only if raw measurements and
   environment notes are committed alongside them.

These are planned slices, not completed eval evidence.

## Acceptance Criteria for Future Public Claims

Benchmark claims require:

- A reproducible harness committed to the repo.
- A fixed task set and immutable fixture inputs.
- Explicit baseline definitions.
- Seed, model, environment, and control-condition recording where applicable.
- Raw result files plus summarized metrics.
- A reviewable method for failed, skipped, or inconclusive cases.

MCP claims beyond the current minimal wrapper require:

- Install and run instructions.
- Protocol-level smoke coverage using the intended transport.
- At least one external-client or end-to-end invocation path, if claiming client interoperability.
- Error-case coverage for invalid inputs and failed compilation.

Performance or budget-efficiency claims require:

- Measured timing, token, and output-size metrics.
- Fixed hardware or environment notes when timing is claimed.
- Repeated-run or variance handling for non-deterministic components.
- Raw measurements stored in the repo or another durable, reviewable artifact.

Production-readiness claims require:

- Packaging and startup documentation.
- Operational error handling expectations.
- Compatibility matrix for supported Python and MCP environments.
- CI or release evidence that matches the claim.

Portfolio or README claims require:

- A direct link from each claim to tests, eval output, accepted BUILDLOG entries, or architecture documentation.
- Conservative language that distinguishes proven behavior from planned methodology.
- Removal or qualification of any claim that lacks durable evidence.
