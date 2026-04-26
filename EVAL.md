# EVAL.md -- Evidence and Methodology Baseline

## Purpose

This file records what the repository currently proves, what it only quality-gates locally, and what remains unevaluated. It is an evidence ledger, not a benchmark report or portfolio narrative.

## Current Evidence Status

The current semantic-first baseline is supported by repo-local tests and
accepted BUILDLOG entries through the deterministic internal eval harness and
the current four-asset signal quad matrix.

Release authority is split by artifact type. The `oracle_signal_vars_probe`
evidence described below is a narrow internal `vars(obj)` pilot, and the
`oracle_signal_vars_zero_probe` evidence described below is a narrow internal
zero-argument `vars()` pilot. The `oracle_signal_globals_probe_matrix`
evidence described below is a narrow internal eval-only `RUNTIME_MUTATION` /
`globals()` pilot. The `oracle_signal_locals_probe_matrix` evidence described
below is a narrow internal eval-only `RUNTIME_MUTATION` / `locals()` pilot. The
`oracle_signal_delattr_probe_matrix` evidence described below is a current
internal eval-only `RUNTIME_MUTATION` / `delattr(obj, name)` pilot. The
current internal eval-only `oracle_signal_dir_probe_matrix` evidence is a
narrow `REFLECTIVE_BUILTIN` / `dir(obj)` pilot. The `d8ebdc3` code/test
evidence anchor adds internal eval runtime-outcome accounting over normalized
runtime provenance payload data. The prior `b014595` release carries narrow
internal
`REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` value-return branch
evidence beside the prior `7d43302` default-return branch, the earlier `c592dca`
`getattr(obj, name)` runtime-backed evidence, and the `90dcc15` / `762dd51`
`hasattr(obj, name)` runtime-backed evidence. These reflective pilots, the
current internal `vars(obj)` pilot, the current internal zero-argument
`vars()` pilot, the current internal `globals()` pilot, the current internal
`locals()` pilot, the current internal eval-only `REFLECTIVE_BUILTIN` /
`dir(obj)` pilot, the current internal eval-only `RUNTIME_MUTATION` /
`delattr(obj, name)` pilot, and the runtime-outcome accounting do not widen
public claims, public APIs, MCP behavior, scoring, winner selection, runtime
acquisition, analyzer/tool-facade implementation, schema, or generalized
runtime-mutation support, generalized locals() support, public benchmark
claims, or generalized hybrid-runtime coverage.

The current internal evidence ledger also records a narrow provider/budget
expansion for the existing getattr-family run specs:
`oracle_signal_getattr_probe_matrix`,
`oracle_signal_getattr_default_probe_matrix`, and
`oracle_signal_getattr_default_value_probe_matrix`. Each matrix remains one
existing task only: 1 task x 2 budgets x 3 providers at budgets `100` and
`220`. This is internal eval evidence for existing reflective probes only; it
does not create generalized `getattr` support or widen public/runtime APIs.

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
- This quad matrix is the completed phase 0 internal evidence surface and
  regression anchor for the post-milestone program. It is not external
  benchmark proof.
- Post-phase-0 internal evidence now includes capability-tier storage and
  accounting for statically proved, runtime-backed, heuristic/frontier, and
  unsupported/opaque surfaces.
- Provider-scoped selected-unit capability-tier accounting is supported for
  internal eval summaries/reports, including additive runtime-backed support
  attached to selected units.
- Internal eval runtime-outcome accounting is supported for normalized runtime
  provenance payload fields, so summary/report output can distinguish outcome
  counts such as `lookup_outcome=returned_default_value` and
  `lookup_outcome=returned_value`, and the current internal `vars(obj)` and
  zero-argument `vars()` pilots plus the current internal `RUNTIME_MUTATION` /
  `globals()` and `locals()` pilots record
  `lookup_outcome=returned_namespace`, while the current internal eval-only
  `RUNTIME_MUTATION` / `delattr(obj, name)` pilot records
  `mutation_outcome=deleted_attribute`, preserving existing tier/provider
  additive-provenance accounting.
- The current internal `REFLECTIVE_BUILTIN` / `dir(obj)` pilot records durable
  listing proof through `durable_payload_reference`; optional
  `listing_entry_count` is additive summary only.
- Internal runtime-backed evidence currently covers narrow pilots only:
  - the `DYNAMIC_IMPORT` internal provider/budget matrix for the
    `oracle_signal_dynamic_import_probe` task
  - the `REFLECTIVE_BUILTIN` / `hasattr(obj, name)` internal pilot for the
    `oracle_signal_hasattr_probe` task
  - the `REFLECTIVE_BUILTIN` / `getattr(obj, name)` internal pilot for the
    `oracle_signal_getattr_probe` task
  - the narrow internal eval-only `REFLECTIVE_BUILTIN` /
    `getattr(obj, name, default)` default-return branch pilot for the
    `oracle_signal_getattr_default_probe` task
  - the narrow internal eval-only `REFLECTIVE_BUILTIN` /
    `getattr(obj, name, default)` value-return sibling pilot for the
    `oracle_signal_getattr_default_value_probe` task
  - the narrow internal `REFLECTIVE_BUILTIN` / `vars(obj)` pilot for the
    `oracle_signal_vars_probe` task
  - the narrow internal `REFLECTIVE_BUILTIN` / zero-argument `vars()` pilot for
    the `oracle_signal_vars_zero_probe` task
  - the narrow internal eval-only `RUNTIME_MUTATION` / `globals()` pilot for
    the `oracle_signal_globals_probe` task
  - the narrow internal eval-only `RUNTIME_MUTATION` / `locals()` pilot for the
    `oracle_signal_locals_probe` task
  - the current internal eval-only `RUNTIME_MUTATION` /
    `delattr(obj, name)` pilot for the `oracle_signal_delattr_probe` task
  - the narrow internal eval-only `REFLECTIVE_BUILTIN` / `dir(obj)` pilot for
    `oracle_signal_dir_probe_matrix`
- The three existing getattr-family provider/budget matrices now cover budgets
  `100` and `220`; each remains 1 task x 2 budgets x 3 providers.
- The current internal `vars(obj)` pilot covers only
  `oracle_signal_vars_probe`: 1 task x 2 budgets x 3 providers at budgets
  `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`.
- The current internal zero-argument `vars()` pilot covers only
  `oracle_signal_vars_zero_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`.
- The current internal `RUNTIME_MUTATION` / `globals()` pilot covers only
  `oracle_signal_globals_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`.
- The current internal `RUNTIME_MUTATION` / `locals()` pilot covers only
  `oracle_signal_locals_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`.
- The current internal eval-only `RUNTIME_MUTATION` / `delattr(obj, name)`
  pilot covers only `oracle_signal_delattr_probe_matrix`: 1 task x 1 budget x
  3 providers at budget `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
  `mutation_outcome=deleted_attribute`.
- The current internal `REFLECTIVE_BUILTIN` / `dir(obj)` pilot covers only
  `oracle_signal_dir_probe_matrix`: 1 task x 1 budget x 3 providers at budget
  `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`. The runtime proof boundary is a durable dir
  listing artifact via `durable_payload_reference`; optional
  `listing_entry_count` is additive summary only.
- In those runtime-backed pilots, the dynamic selector, reflective selector, or
  runtime-mutation surface and selected-unit primary truth remain
  `unsupported/opaque`, and runtime-backed provenance is additive attached
  evidence. This is internal evidence, not a public benchmark, broad
  hybrid-runtime support claim, generalized reflective-builtin support claim,
  generalized runtime-mutation support claim, generalized locals() support
  claim, or generalized dynamic-Python claim. The public-safe quad-matrix
  comparative boundary remains unchanged.

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

- Broader public task sets beyond the current accepted internal signal assets
  and narrow runtime-backed pilot tasks.
- Wider budget-curve measurements beyond the fixed budgets committed in the
  current internal run specs.
- Additional baseline comparisons beyond the current lexical and
  import-neighborhood providers.
- Runtime-backed task families beyond the current narrow `DYNAMIC_IMPORT`,
  `REFLECTIVE_BUILTIN` / `hasattr(obj, name)`, `getattr(obj, name)`, and
  eval-only default-return and value-return `getattr(obj, name, default)`
  internal pilots, plus the current one-argument `vars(obj)`, zero-argument
  `vars()`, one-argument `dir(obj)`, and `RUNTIME_MUTATION` / `globals()`,
  `locals()`, and `delattr(obj, name)` internal pilots.
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
- Phase 0 comparative internal evidence surface: four methodology-tightened
  signal assets run as a 4 task x 2 budget x 3 provider quad matrix.
- Capability-tier internal evidence: tier-aware eval storage and
  provider-scoped selected-unit accounting for statically proved,
  runtime-backed, heuristic/frontier, and unsupported/opaque surfaces.
- Narrow runtime-backed internal pilots: `DYNAMIC_IMPORT` plus
  `REFLECTIVE_BUILTIN` / `hasattr(obj, name)`, `getattr(obj, name)`, and
  eval-only default-return and value-return `getattr(obj, name, default)`
  fixtures, tasks, run specs, and additive runtime provenance, plus the current
  internal one-argument `vars(obj)` fixture, task, run spec, and additive
  runtime provenance, and the current internal zero-argument `vars()` fixture,
  task, run spec, and additive runtime provenance, plus the current internal
  `RUNTIME_MUTATION` / `globals()` fixture, task, run spec, and additive
  runtime provenance, plus the current internal `RUNTIME_MUTATION` /
  `locals()` fixture, task, run spec, and additive runtime provenance, plus the
  current internal eval-only `RUNTIME_MUTATION` / `delattr(obj, name)`
  fixture, task, run spec, and additive runtime provenance, plus the
  current internal one-argument `dir(obj)` `oracle_signal_dir_probe_matrix`
  evidence and additive runtime provenance. These pilots are internal evidence
  surfaces, not public benchmark surfaces.
- Narrow getattr-family provider/budget evidence: the three existing
  getattr-family matrices cover budgets `100` and `220`, and each remains
  1 task x 2 budgets x 3 providers.
- Narrow `vars(obj)` provider/budget evidence: the internal
  `oracle_signal_vars_probe_matrix` covers only 1 task x 2 budgets x 3
  providers at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`.
- Narrow zero-argument `vars()` provider/budget evidence: the internal
  `oracle_signal_vars_zero_probe_matrix` covers only 1 task x 2 budgets x 3
  providers at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`; selector and selected-unit primary truth
  remain `unsupported/opaque`, and runtime-backed provenance is additive only.
- Narrow `globals()` provider/budget evidence: the internal
  `oracle_signal_globals_probe_matrix` covers only 1 task x 2 budgets x 3
  providers at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`; primary truth remains
  `unsupported/opaque`, and runtime-backed provenance is additive only.
- Narrow `locals()` provider/budget evidence: the internal
  `oracle_signal_locals_probe_matrix` covers only 1 task x 2 budgets x 3
  providers at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`; selector and selected-unit primary truth
  remain `unsupported/opaque`, and runtime-backed provenance is additive only.
- Narrow `delattr(obj, name)` provider/budget evidence: the current internal
  eval-only `RUNTIME_MUTATION` / `delattr(obj, name)` pilot covers only
  `oracle_signal_delattr_probe_matrix`: 1 task x 1 budget x 3 providers at
  budget `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`, with runtime payload
  `mutation_outcome=deleted_attribute`; selector and selected-unit primary
  truth remain `unsupported/opaque`, and runtime provenance remains additive
  only.
- Narrow `dir(obj)` provider/budget evidence: the internal
  `oracle_signal_dir_probe_matrix` covers only 1 task x 1 budget x 3 providers
  at budget `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`; durable listing proof is carried by
  `durable_payload_reference`, optional `listing_entry_count` is additive
  summary only, selector and selected-unit primary truth remain
  `unsupported/opaque`, and runtime-backed provenance is additive only.
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
- The current public-safe comparative internal surface is the four-asset
  signal quad matrix over `oracle_signal_smoke`, `oracle_signal_smoke_b`,
  `oracle_signal_smoke_c`, and `oracle_signal_smoke_d`.
- Within that fixed quad matrix only, `context_ir` is the sole winner on all
  8/8 task-budget rows and has the top provider-average aggregate score.
- The current internal evidence surface includes an explicit tight-budget
  blemish: `oracle_signal_smoke_b / 200` still records `budget_pressure`, and
  `def:pkg/digest.py:pkg.digest.render_assignment_digest` can remain omitted.
- Internal capability-tier evidence and accounting exists for selected eval
  units, including provider-scoped accounting that keeps statically proved,
  runtime-backed, heuristic/frontier, and unsupported/opaque support separate.
- Internal runtime-backed eval evidence currently covers the narrow
  `DYNAMIC_IMPORT` provider/budget matrix and the narrow
  `REFLECTIVE_BUILTIN` / `hasattr(obj, name)`, `getattr(obj, name)`, and
  eval-only default-return and value-return `getattr(obj, name, default)`
  pilots. The three getattr-family provider/budget matrices cover budgets
  `100` and `220`, and each remains 1 task x 2 budgets x 3 providers. The
  current internal `REFLECTIVE_BUILTIN` / `vars(obj)` pilot covers only
  `oracle_signal_vars_probe`: 1 task x 2 budgets x 3 providers at budgets
  `100` and `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`, with `lookup_outcome=returned_namespace`. The
  current internal `REFLECTIVE_BUILTIN` / zero-argument `vars()` pilot covers
  only `oracle_signal_vars_zero_probe_matrix`: 1 task x 2 budgets x 3
  providers at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`. The current internal eval-only
  `RUNTIME_MUTATION` / `globals()` pilot covers only
  `oracle_signal_globals_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`. The current internal eval-only
  `RUNTIME_MUTATION` / `locals()` pilot covers only
  `oracle_signal_locals_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`. The current internal eval-only
  `RUNTIME_MUTATION` / `delattr(obj, name)` pilot covers only
  `oracle_signal_delattr_probe_matrix`: 1 task x 1 budget x 3 providers at
  budget `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`, with runtime payload
  `mutation_outcome=deleted_attribute`. The current internal eval-only
  `REFLECTIVE_BUILTIN` / `dir(obj)` pilot covers only
  `oracle_signal_dir_probe_matrix`: 1 task x 1 budget x 3 providers at budget
  `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`, with durable listing proof carried by
  `durable_payload_reference`; optional `listing_entry_count` is additive
  summary only. These
  pilots keep the dynamic selector, reflective selector, or runtime-mutation
  surface and selected-unit primary truth `unsupported/opaque` while attaching
  runtime-backed provenance additively. The public-safe quad-matrix
  comparative boundary remains unchanged.

## Unsupported Claims Today

The following claims are not currently allowed:

- No SWE-bench, SWE-bench Mini, SWE-bench Verified, or SWE-bench-style improvement claims.
- No external benchmark improvement claims of any kind.
- No resolve-rate, edit-success-rate, retrieval-quality, area-under-budget-curve, or task-win-rate claims.
- No production-readiness claims.
- No multi-language claims.
- No broad or public Python dynamic-semantics claims, including generalized
  dynamic imports, reflection, `exec`, `eval`, monkey patching, metaclasses,
  runtime attribute injection, or general decorator semantics. The narrow
  internal `DYNAMIC_IMPORT`, `hasattr(obj, name)`, `getattr(obj, name)`, and
  eval-only default-return and value-return `getattr(obj, name, default)`
  pilots, plus the current internal one-argument `vars(obj)`, zero-argument
  `vars()`, one-argument `dir(obj)`, and `RUNTIME_MUTATION` / `globals()`,
  `locals()`, and `delattr(obj, name)` pilots, do not change this public
  boundary.
- No claim that the MCP wrapper is a complete product integration beyond the minimal tested compile tool.
- No claim that the old graph-first stack or exact 5-tier renderer thesis is the current architecture.
- No claim that `p_edit` or `p_support` is the public thesis; they are internal ranking policy only.
- No performance, latency, token-savings, or cost-reduction claims without measured data.
- No claim that README or portfolio positioning has been fully synchronized with the accepted final-phase state.
- No public claim that hybrid static + runtime analysis is generally
  implemented today.
- No capability-tier claim beyond the accepted internal accounting/evidence
  surfaces and explicit uncertainty handling.
- No claim that runtime-backed, heuristic/frontier, or unsupported/opaque
  surfaces have broad benchmarked coverage or production-grade handling.

## Future Eval Plan

Next smallest eval slices for the post-milestone program:

1. Continue hardening eval semantics for each capability tier and keep
   capability-tier accounting separate from representation-tier rendering
   choices.
2. Broaden hybrid static + runtime analysis evidence beyond the current narrow
   `DYNAMIC_IMPORT`, `REFLECTIVE_BUILTIN` / `hasattr(obj, name)`,
   `getattr(obj, name)`, and eval-only default-return and value-return
   `getattr(obj, name, default)` pilots, plus the current internal one-argument
   `vars(obj)`, zero-argument `vars()`, and `RUNTIME_MUTATION` / `globals()`,
   `locals()`, and `delattr(obj, name)` pilots, only through reproducible
   runtime-backed fixtures, probes, and raw evidence storage.
3. Broaden task, budget, and baseline coverage only after the tiered internal
   eval model is stable and claim-bounded.
4. Publish external benchmark methodology only after the internal tiered
   surfaces are stable enough to support reproducible public comparisons and
   raw result release.
5. Add production-maturity evidence only through packaging, compatibility,
   interoperability, error handling, CI/release, and observability artifacts.

These are planned slices, not completed eval evidence.

## Acceptance Criteria for Future Public Claims

Capability-tier or hybrid-analysis claims require:

- A declared capability tier for each reported unit or aggregate.
- Separate accounting for statically proved, runtime-backed, heuristic/frontier, and unsupported/opaque surfaces.
- Raw evidence artifacts that preserve provenance rather than collapsing all tiers into one score.
- Reproducible runtime-backed methodology, including environment notes and probe inputs, for any runtime-backed claim.

Benchmark claims require:

- A reproducible harness committed to the repo.
- A fixed task set and immutable fixture inputs.
- Explicit baseline definitions.
- Seed, model, environment, and control-condition recording where applicable.
- Raw result files plus summarized metrics.
- A reviewable method for failed, skipped, or inconclusive cases.
- Publicly reviewable methodology and raw results before any external benchmark leadership wording.

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
- Compatibility matrix for supported Python and MCP environments.
- Interoperability evidence for claimed client or transport surfaces.
- Operational error handling expectations.
- CI or release evidence that matches the claim.
- Observability evidence that matches the claim.

Portfolio or README claims require:

- A direct link from each claim to tests, eval output, accepted BUILDLOG entries, or architecture documentation.
- Conservative language that distinguishes proven behavior from planned methodology.
- Removal or qualification of any claim that lacks durable evidence.
