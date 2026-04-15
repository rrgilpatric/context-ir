# EVAL.md -- Evidence and Methodology Baseline

## Purpose

This file records what the repository currently proves, what it only quality-gates locally, and what remains unevaluated. It is an evidence ledger, not a benchmark report or portfolio narrative.

## Current Evidence Status

The current semantic-first baseline is supported by repo-local tests and accepted BUILDLOG entries through the minimal MCP wrapper slice.

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

Validated by local quality gates, not by benchmark evidence:

- Accepted slices in `BUILDLOG.md` record clean local runs of `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"`.
- The required full local validation gate for this repo is:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"`
- These gates establish lint, formatting, type, and regression-test health. They do not establish benchmark effectiveness, production readiness, external protocol completeness, or SWE-bench relevance.

Architecturally intended but not yet evaluated:

- Fixture-level behavioral evals that score compile output against deterministic task expectations.
- Budget-curve measurements across fixed task sets.
- Baseline comparisons against alternative context-selection strategies.
- SWE-bench-style methodology, after local fixture evals exist.
- Production packaging, install/run ergonomics, and external MCP client compatibility beyond the tested local wrapper behavior.

## Evidence Categories

- Unit/integration tests: pytest coverage in `tests/` for semantic contracts, parser, binder, resolver, dependency/frontier, renderer, scorer, optimizer, compiler, diagnose/recompile, analyzer, public API, tool facade, and MCP wrapper behavior.
- Static quality gates: ruff lint, ruff format check, mypy strict, and non-slow pytest suite.
- Protocol smoke tests: current MCP evidence is limited to local SDK registration and local tool invocation in `tests/test_mcp_server.py`.
- Fixture-level behavioral evals: not implemented yet. Existing fixtures support tests, not an eval harness with scoring criteria.
- Benchmark/effectiveness evals: not implemented yet. No benchmark task set, baseline, metric, seed policy, or raw result ledger exists.
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

## Unsupported Claims Today

The following claims are not currently allowed:

- No SWE-bench, SWE-bench Mini, SWE-bench Verified, or SWE-bench-style improvement claims.
- No benchmark improvement claims of any kind.
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

1. Deterministic fixture-level behavioral eval: define a tiny fixed repository fixture set, task prompts, expected semantic units, expected uncertainty surfaces, and pass/fail scoring for compile output.
2. Budget-curve harness design: specify budgets, output metrics, raw-result format, and how omitted uncertainty and dependency coverage are counted.
3. Baseline comparison design: define simple baselines, such as whole-file inclusion, lexical matching, or package-local inclusion, before comparing Context IR output.
4. Raw result ledger: add a reproducible location and schema for eval runs before any public quantitative claim is made.
5. SWE-bench-style methodology: design only after fixture-level evals exist and have stable pass conditions.

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
