# Public Claims

This file is the conservative public-claim envelope for frontier-lab-facing
copy. It is a source constraint, not portfolio prose. Every allowed claim below
stays scoped to repo-local evidence only.

## Allowed Claims

- Safe top-line descriptor: Context IR is an in-progress semantic-first Python
  context compiler for coding agents that analyzes a supported static Python
  subset into a `SemanticProgram`, derives proven dependencies plus explicit
  unresolved or unsupported frontier, and compiles budgeted context. Evidence:
  [README.md](README.md), [EVAL.md](EVAL.md#supported-claims-today),
  [PLAN.md](PLAN.md).
- Safe interface descriptor: The current public surface is a low-level
  `analyze_repository(...)` analyzer, a typed
  `compile_repository_context(...)` facade, and a minimal stdio MCP wrapper
  that exposes one tested `compile_repository_context` tool. Evidence:
  [README.md](README.md#python-api),
  [README.md](README.md#minimal-mcp-usage),
  [EVAL.md](EVAL.md#supported-claims-today).
- Safe evidence descriptor: The repo contains a deterministic internal eval
  harness with summary, report, pipeline, manifest, and bundle artifacts over
  fixed run specs and JSONL ledgers. The current public-safe comparative
  evidence surface remains the four-asset quad matrix defined in
  [evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json).
  Later internal runtime-backed evidence is limited to narrow
  `DYNAMIC_IMPORT` plus `REFLECTIVE_BUILTIN` pilots for `hasattr(obj, name)`
  and `getattr(obj, name)`, plus narrow internal eval-only default-return and
  value-return branch pilots for `getattr(obj, name, default)`, and the current
  internal one-argument `vars(obj)` and zero-argument `vars()` pilots, plus the
  current internal eval-only `RUNTIME_MUTATION` / `globals()` and `locals()`
  pilots. The three existing
  getattr-family pilot matrices
  (`oracle_signal_getattr_probe_matrix`,
  `oracle_signal_getattr_default_probe_matrix`, and
  `oracle_signal_getattr_default_value_probe_matrix`) are limited to 1 task x
  2 budgets x 3 providers at budgets `100` and `220`; the internal
  `oracle_signal_vars_probe_matrix` is limited to 1 task x 2 budgets x 3
  providers at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`; the internal
  `oracle_signal_vars_zero_probe_matrix` is limited to 1 task x 2 budgets x 3
  providers at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`; the internal
  `oracle_signal_globals_probe_matrix` is limited to 1 task x 2 budgets x 3
  providers at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`; the internal
  `oracle_signal_locals_probe_matrix` is limited to 1 task x 2 budgets x 3
  providers at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`. These
  pilots must not be described as public benchmark proof, generalized
  reflective-builtin support, generalized runtime-mutation support,
  generalized locals() support, or generalized hybrid-runtime support. The
  public-safe quad-matrix comparative boundary remains unchanged.
  Evidence: [EVAL.md](EVAL.md#current-evidence-status),
  [EVAL.md](EVAL.md#evidence-categories), [BUILDLOG.md](BUILDLOG.md),
  [evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json),
  [evals/run_specs/oracle_signal_vars_zero_probe_matrix.json](evals/run_specs/oracle_signal_vars_zero_probe_matrix.json),
  [evals/run_specs/oracle_signal_globals_probe_matrix.json](evals/run_specs/oracle_signal_globals_probe_matrix.json),
  [evals/run_specs/oracle_signal_locals_probe_matrix.json](evals/run_specs/oracle_signal_locals_probe_matrix.json).
- Safe comparative descriptor: Within the fixed internal quad matrix only
  (`oracle_signal_smoke`, `oracle_signal_smoke_b`, `oracle_signal_smoke_c`,
  and `oracle_signal_smoke_d` at budgets `200` and `240` against
  `lexical_top_k_files` and `import_neighborhood_files`), `context_ir` wins
  all `8/8` task-budget rows and has the top provider-average aggregate score.
  Evidence: [EVAL.md](EVAL.md#supported-claims-today),
  [BUILDLOG.md](BUILDLOG.md),
  [evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json).

## Required Qualifiers

- Always say "supported static Python subset" or "narrow static Python subset."
  Do not collapse this to unqualified "Python analysis." The supported subset
  is repo-static and narrow, including narrow class-level `@dataclass` support
  only where it resolves to `dataclasses.dataclass`.
- Always frame the current evidence as deterministic internal evidence from
  repo-local tests, quality gates, and the internal eval harness. Do not
  restate it as external benchmark proof.
- Preserve the accepted current limitation: `oracle_signal_smoke_b / 200`
  still records `budget_pressure`, and
  `def:pkg/digest.py:pkg.digest.render_assignment_digest` can remain omitted
  under that tight budget.
- When referencing evidence history, treat
  [evals/run_specs/oracle_signal_triple_matrix.json](evals/run_specs/oracle_signal_triple_matrix.json)
  as the prior internal surface and
  [evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json)
  as the current public-safe comparative internal surface.
- When referencing runtime-backed work, say only that narrow internal evidence
  exists for the `DYNAMIC_IMPORT` provider/budget matrix and the
  `REFLECTIVE_BUILTIN` / `hasattr(obj, name)`, `getattr(obj, name)`, and
  eval-only default-return and value-return `getattr(obj, name, default)`
  pilots, plus the current internal one-argument `vars(obj)` and zero-argument
  `vars()` pilots, plus the current internal eval-only `RUNTIME_MUTATION` /
  `globals()` and `locals()` pilots. For
  the three existing getattr-family matrices, the only accepted
  provider/budget wording is 1 task x 2 budgets x 3 providers at budgets `100`
  and `220`. For the internal `vars(obj)` matrix, the only accepted
  provider/budget wording is 1 task x 2 budgets x 3 providers at budgets `100`
  and `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`. For the internal zero-argument `vars()` matrix,
  the only accepted provider/budget wording is 1 task x 2 budgets x 3 providers
  at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`. For the internal `globals()` matrix,
  the only accepted provider/budget wording is
  `oracle_signal_globals_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`.
  For the internal `locals()` matrix, the only accepted provider/budget wording
  is `oracle_signal_locals_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`.
  Do not convert that into a public supported-subset, benchmark, product, or
  generalized hybrid static + runtime claim.
- For reflective-builtin pilot wording, preserve that selector and
  selected-unit primary truth remains `unsupported/opaque`. For the
  `RUNTIME_MUTATION` / `globals()` and `locals()` pilots,
  selector/runtime-mutation surface and selected-unit primary truth also remain
  `unsupported/opaque`. Runtime-backed provenance is additive only.
- Any comparative sentence must stay explicitly scoped to the accepted internal
  quad matrix. Do not generalize the current `8/8` result beyond that fixed
  four-task, two-budget, three-provider surface.

## Disallowed Phrasings

- Do not say "benchmark winner," "state of the art," "SOTA," or any external
  benchmark leadership phrasing.
- Do not say "production ready," "deployment ready," or "enterprise ready."
- Do not say "complete MCP product," "full MCP interoperability," or otherwise
  imply more than one tested compile tool in a minimal wrapper.
- Do not say "100% win rate," "task win rate," "benchmark improvement,"
  "resolve rate," or similar generalized score language.
- Do not say "full Python semantics," "broad decorator support," or
  "multi-language analysis."
- Do not say "hybrid runtime coverage," "runtime-backed Python coverage," or
  similar broad runtime wording without the narrow internal-pilot qualifier.
- Do not say "latency reduction," "token savings," or "cost reduction."

## Evidence Map

| ID | Allowed claim | Repo anchors |
| --- | --- | --- |
| AC1 | Context IR is an in-progress semantic-first Python context compiler over a supported static subset. | [README.md](README.md), [EVAL.md](EVAL.md#supported-claims-today), [PLAN.md](PLAN.md) |
| AC2 | Public interface claims are limited to `analyze_repository(...)`, `compile_repository_context(...)`, and one tested MCP compile tool. | [README.md](README.md#python-api), [README.md](README.md#minimal-mcp-usage), [EVAL.md](EVAL.md#supported-claims-today) |
| AC3 | Deterministic internal eval infrastructure exists; the quad matrix remains the current public-safe comparative internal surface, while runtime-backed evidence is limited to narrow internal `DYNAMIC_IMPORT` plus `REFLECTIVE_BUILTIN` pilots for `hasattr(obj, name)`, `getattr(obj, name)`, eval-only default-return and value-return branches of `getattr(obj, name, default)`, the current internal one-argument `vars(obj)` and zero-argument `vars()` pilots, and the current internal eval-only `RUNTIME_MUTATION` / `globals()` and `locals()` pilots. The three existing getattr-family pilot matrices cover only 1 task x 2 budgets x 3 providers at budgets `100` and `220`; the internal `vars(obj)` pilot covers only 1 task x 2 budgets x 3 providers at budgets `100` and `220`, against providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`; the internal zero-argument `vars()` pilot covers only `oracle_signal_vars_zero_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `100` and `220`, against providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`, with `lookup_outcome=returned_namespace`; the internal `globals()` pilot covers only `oracle_signal_globals_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `100` and `220`, against providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`, with `lookup_outcome=returned_namespace`; the internal `locals()` pilot covers only `oracle_signal_locals_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `100` and `220`, against providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`, with `lookup_outcome=returned_namespace`. Selector, runtime-mutation surface, and selected-unit primary truth remain `unsupported/opaque`, and runtime-backed provenance is additive only. | [EVAL.md](EVAL.md#current-evidence-status), [EVAL.md](EVAL.md#evidence-categories), [BUILDLOG.md](BUILDLOG.md), [evals/run_specs/oracle_signal_triple_matrix.json](evals/run_specs/oracle_signal_triple_matrix.json), [evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json), [evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json](evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json), [evals/run_specs/oracle_signal_hasattr_probe_matrix.json](evals/run_specs/oracle_signal_hasattr_probe_matrix.json), [evals/run_specs/oracle_signal_getattr_probe_matrix.json](evals/run_specs/oracle_signal_getattr_probe_matrix.json), [evals/run_specs/oracle_signal_getattr_default_probe_matrix.json](evals/run_specs/oracle_signal_getattr_default_probe_matrix.json), [evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json](evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json), [evals/run_specs/oracle_signal_vars_probe_matrix.json](evals/run_specs/oracle_signal_vars_probe_matrix.json), [evals/run_specs/oracle_signal_vars_zero_probe_matrix.json](evals/run_specs/oracle_signal_vars_zero_probe_matrix.json), [evals/run_specs/oracle_signal_globals_probe_matrix.json](evals/run_specs/oracle_signal_globals_probe_matrix.json), [evals/run_specs/oracle_signal_locals_probe_matrix.json](evals/run_specs/oracle_signal_locals_probe_matrix.json) |
| AC4 | The only allowed comparative claim is the fixed-scope quad-matrix claim: within that matrix only, `context_ir` wins all `8/8` task-budget rows and leads the provider-average aggregate. | [EVAL.md](EVAL.md#supported-claims-today), [BUILDLOG.md](BUILDLOG.md), [evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json) |
