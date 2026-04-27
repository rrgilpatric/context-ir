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
  pilots, plus the current internal eval-only `RUNTIME_MUTATION` /
  `delattr(obj, name)` pilot, plus the current narrow internal eval-only
  `RUNTIME_MUTATION` / `setattr(obj, name, value)` evidence, plus the current
  internal eval-only one-argument `dir(obj)` pilot, plus the current internal
  eval-only zero-argument `dir()` pilot, plus the current internal eval-only
  `METACLASS_BEHAVIOR` / preserved `metaclass=...` keyword-site pilot, plus
  the current internal eval-only `EXEC_OR_EVAL` /
  `eval(source)` evidence, plus the current internal eval-only
  `EXEC_OR_EVAL` / `exec(source)` evidence, plus the current internal
  eval-only `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)`
  sibling evidence, plus narrow internal eval-only
  `DYNAMIC_IMPORT` / builtin `__import__(name)` sibling evidence, plus the
  current internal eval-only `DYNAMIC_IMPORT` / imported-name
  `import_module(name)` sibling evidence.
  The three existing
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
  `lookup_outcome=returned_namespace`; the current internal eval-only
  `oracle_signal_delattr_probe_matrix` is limited to 1 task x 1 budget x 3
  providers at budget `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
  `mutation_outcome=deleted_attribute`; the current internal eval-only
  `oracle_signal_setattr_probe_matrix` is narrow `RUNTIME_MUTATION` /
  `setattr(obj, name, value)` evidence limited to 1 task x 1 budget x 3
  providers at budget `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
  `mutation_outcome=returned_none`; selector/runtime-mutation surface and
  selected-unit primary truth remain `unsupported/opaque`, runtime provenance
  remains additive only, and public comparative claims remain bounded to the
  existing quad matrix; the internal
  `oracle_signal_dir_probe_matrix` is limited to 1 task x 1 budget x 3
  providers at budget `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with durable listing
  proof carried by `durable_payload_reference` and optional
  `listing_entry_count` as additive summary only; the internal
  `oracle_signal_dir_zero_probe_matrix` is limited to 1 task x 1 budget x 3
  providers at budget `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with runtime proof
  requiring non-empty `durable_payload_reference` and optional
  `listing_entry_count` as additive summary only; primary selector and
  selected-unit truth remain `unsupported/opaque`, runtime provenance remains
  additive only, and public comparative claims remain bounded to the existing
  quad matrix; the internal
  `oracle_signal_metaclass_behavior_probe_matrix` is limited to 1 task x 1
  budget x 3 providers at budget `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
  `class_creation_outcome=created_class`; `durable_payload_reference` is
  required and non-empty, optional `created_class_qualified_name` and
  `selected_metaclass_qualified_name` fields are additive summary only,
  attachment is limited to the preserved full `metaclass=...` keyword-site
  unsupported construct, selector and selected-unit primary truth remain
  `unsupported/opaque`, runtime provenance remains additive only, and public
  comparative claims remain bounded to the existing quad matrix; the internal
  `oracle_signal_eval_probe_matrix` is limited to 1 task x 1 budget x 3
  providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with runtime
  payload/proof boundary `evaluation_outcome=returned_value`,
  `source_shape=literal_expression`, valid `source_sha256`, and non-empty
  `durable_payload_reference`; optional `result_type=builtins.str` is additive
  summary only, runtime provenance attaches only to the preserved
  `EXEC_OR_EVAL` unsupported finding for `eval(source)`, primary selector and
  selected-unit truth remain `unsupported/opaque`, additive runtime provenance
  remains separate from primary truth, and public comparative claims remain
  bounded to the existing quad matrix; the internal
  `oracle_signal_exec_probe_matrix` is limited to 1 task x 1 budget x 3
  providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with fixture/call
  boundary `source = "pass"` and exactly `exec(source)`, executed source
  parsing as exactly one `ast.Pass`, runtime payload/proof boundary
  `execution_outcome=completed`, `source_shape=literal_statement`, valid
  `source_sha256` for exact `"pass"`, and non-empty
  `durable_payload_reference`; optional `statement_kind=pass` is additive
  summary only, runtime provenance attaches only to the preserved
  `EXEC_OR_EVAL` unsupported finding for `exec(source)`, primary selector and
  selected-unit truth remain `unsupported/opaque`, additive runtime provenance
  remains separate from primary truth, no dependency edge or symbol is created
  from executed source, no namespace mutation modeling is added, no
  generated-code dependency modeling is added, and public comparative claims
  remain bounded to the existing quad matrix; the internal
  `oracle_signal_dynamic_import_root_probe_matrix` is limited to narrow
  eval-only `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)`
  sibling evidence as 1 task x 1 budget x 3 providers at budget 220, against
  providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`, with fixture boundary `import importlib`,
  `name = "plugins.weather"`, and exactly `importlib.import_module(name)`;
  runtime payload `imported_module=plugins.weather`; primary selector and
  selected-unit truth remain `unsupported/opaque`; runtime provenance remains
  additive only; no dependency edge or symbol is created from the dynamically
  imported module; no `__import__(name)`, imported-name
  `import_module(name)`, alias or loader forms, generalized dynamic import
  support, or public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is included.
  The narrow internal eval-only
  `oracle_signal_dynamic_import_builtin_probe_matrix` is limited to narrow
  `DYNAMIC_IMPORT` / builtin `__import__(name)` sibling evidence as 1 task x 1
  budget x 3 providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with fixture boundary
  `name = "plugins.weather"` and exactly `__import__(name)`, with bounded
  `sys.modules[name]` retrieval only; runtime payload
  `imported_module=plugins.weather`; primary selector and selected-unit truth
  remain `unsupported/opaque`; runtime provenance remains additive only; no
  dependency edge or symbol is created from `plugins.weather`; no
  `importlib.import_module(name)`, imported-name `import_module(name)`, alias
  or loader forms, `builtins.__import__`, globals/locals/fromlist forms,
  generalized dynamic import support, or public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is included.
  The current internal eval-only
  `oracle_signal_dynamic_import_imported_name_probe_matrix` is limited to
  narrow `DYNAMIC_IMPORT` / imported-name `import_module(name)` sibling
  evidence as 1 task x 1 budget x 3 providers at budget 220, against
  providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`, with fixture boundary
  `from importlib import import_module`, `name = "plugins.weather"`, and
  exactly `import_module(name)`; runtime payload
  `imported_module=plugins.weather`; primary selector and selected-unit truth
  remain `unsupported/opaque`; runtime provenance remains additive only; no
  dependency edge or selected symbol is created from `plugins.weather`; no
  root-module `importlib.import_module(name)` expansion, literal
  `import_module("plugins.weather")` expansion, alias `load_module(name)`,
  `loader.import_module(name)`, `__import__(name)`, `builtins.__import__`,
  globals/locals/fromlist forms, generalized dynamic import support, or
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is included. These
  pilots must not be described as public benchmark proof, generalized
  dynamic-import support, generalized reflective-builtin support, generalized
  runtime-mutation support, generalized locals() support, or generalized
  hybrid-runtime support. The public-safe quad-matrix comparative boundary
  remains unchanged.
  Evidence: [EVAL.md](EVAL.md#current-evidence-status),
  [EVAL.md](EVAL.md#evidence-categories), [BUILDLOG.md](BUILDLOG.md),
  [evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json),
  [evals/run_specs/oracle_signal_vars_zero_probe_matrix.json](evals/run_specs/oracle_signal_vars_zero_probe_matrix.json),
  [evals/run_specs/oracle_signal_globals_probe_matrix.json](evals/run_specs/oracle_signal_globals_probe_matrix.json),
  [evals/run_specs/oracle_signal_locals_probe_matrix.json](evals/run_specs/oracle_signal_locals_probe_matrix.json),
  [evals/run_specs/oracle_signal_delattr_probe_matrix.json](evals/run_specs/oracle_signal_delattr_probe_matrix.json),
  [evals/run_specs/oracle_signal_setattr_probe_matrix.json](evals/run_specs/oracle_signal_setattr_probe_matrix.json),
  [evals/run_specs/oracle_signal_dir_probe_matrix.json](evals/run_specs/oracle_signal_dir_probe_matrix.json),
  [evals/run_specs/oracle_signal_dir_zero_probe_matrix.json](evals/run_specs/oracle_signal_dir_zero_probe_matrix.json),
  [evals/run_specs/oracle_signal_metaclass_behavior_probe_matrix.json](evals/run_specs/oracle_signal_metaclass_behavior_probe_matrix.json),
  [evals/run_specs/oracle_signal_eval_probe_matrix.json](evals/run_specs/oracle_signal_eval_probe_matrix.json),
  [evals/run_specs/oracle_signal_exec_probe_matrix.json](evals/run_specs/oracle_signal_exec_probe_matrix.json),
  [evals/run_specs/oracle_signal_dynamic_import_root_probe_matrix.json](evals/run_specs/oracle_signal_dynamic_import_root_probe_matrix.json),
  [evals/run_specs/oracle_signal_dynamic_import_builtin_probe_matrix.json](evals/run_specs/oracle_signal_dynamic_import_builtin_probe_matrix.json),
  [evals/run_specs/oracle_signal_dynamic_import_imported_name_probe_matrix.json](evals/run_specs/oracle_signal_dynamic_import_imported_name_probe_matrix.json).
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
  exists for the `DYNAMIC_IMPORT` provider/budget matrix and the current
  root-module `importlib.import_module(name)` sibling matrix, plus the
  `REFLECTIVE_BUILTIN` / `hasattr(obj, name)`, `getattr(obj, name)`, and
  eval-only default-return and value-return `getattr(obj, name, default)`
  pilots, plus the current internal one-argument `vars(obj)` and zero-argument
  `vars()` pilots, plus the current internal eval-only `RUNTIME_MUTATION` /
  `globals()` and `locals()` pilots, plus the current internal eval-only
  `RUNTIME_MUTATION` / `delattr(obj, name)` pilot, plus the current narrow
  internal eval-only `RUNTIME_MUTATION` / `setattr(obj, name, value)` evidence,
  plus the current internal eval-only one-argument `dir(obj)` pilot, plus the
  current internal eval-only zero-argument `dir()` pilot, plus the current
  internal eval-only `METACLASS_BEHAVIOR` / preserved `metaclass=...`
  keyword-site pilot, plus the current internal eval-only
  `EXEC_OR_EVAL` / `eval(source)` evidence, plus the current internal
  eval-only `EXEC_OR_EVAL` / `exec(source)` evidence, plus the narrow
  internal eval-only `DYNAMIC_IMPORT` / builtin
  `__import__(name)` sibling evidence, plus the current internal eval-only
  `DYNAMIC_IMPORT` / imported-name `import_module(name)` sibling evidence.
  For the narrow internal eval-only
  `DYNAMIC_IMPORT` / builtin
  `__import__(name)` sibling matrix, the only accepted provider/budget wording
  is `oracle_signal_dynamic_import_builtin_probe_matrix`: 1 task x 1 budget x
  3 providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with fixture boundary
  `name = "plugins.weather"` and exactly `__import__(name)`, with bounded
  `sys.modules[name]` retrieval only, runtime payload
  `imported_module=plugins.weather`, primary selector and selected-unit truth
  `unsupported/opaque`, additive-only runtime provenance, no dependency edge or
  symbol created from `plugins.weather`, and no
  `importlib.import_module(name)`, imported-name `import_module(name)`, alias
  or loader forms, `builtins.__import__`, globals/locals/fromlist forms,
  generalized dynamic import support, or public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening.
  For the current internal eval-only `DYNAMIC_IMPORT` / imported-name
  `import_module(name)` sibling matrix, the only accepted provider/budget
  wording is `oracle_signal_dynamic_import_imported_name_probe_matrix`: 1 task
  x 1 budget x 3 providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with fixture
  boundary `from importlib import import_module`,
  `name = "plugins.weather"`, and exactly `import_module(name)`, runtime
  payload `imported_module=plugins.weather`, primary selector and
  selected-unit truth `unsupported/opaque`, additive-only runtime provenance,
  no dependency edge or selected symbol created from `plugins.weather`, and no
  root-module `importlib.import_module(name)` expansion, literal
  `import_module("plugins.weather")` expansion, alias `load_module(name)`,
  `loader.import_module(name)`, `__import__(name)`, `builtins.__import__`,
  globals/locals/fromlist forms, generalized dynamic import support, or
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening.
  For the three existing getattr-family matrices, the only accepted
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
  For the current internal eval-only `RUNTIME_MUTATION` /
  `delattr(obj, name)` matrix, the only accepted provider/budget wording is
  `oracle_signal_delattr_probe_matrix`: 1 task x 1 budget x 3 providers at
  budget `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`, with runtime payload
  `mutation_outcome=deleted_attribute`; selector and selected-unit primary
  truth remain `unsupported/opaque`, and runtime provenance remains additive
  only.
  For the current internal eval-only `RUNTIME_MUTATION` /
  `setattr(obj, name, value)` matrix, the only accepted provider/budget wording
  is `oracle_signal_setattr_probe_matrix`: 1 task x 1 budget x 3 providers at
  budget `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`, with runtime payload
  `mutation_outcome=returned_none`; selector/runtime-mutation surface and
  selected-unit primary truth remain `unsupported/opaque`, runtime provenance
  remains additive only, and public comparative claims remain bounded to the
  existing quad matrix.
  For the internal `dir(obj)` matrix, the only accepted provider/budget wording
  is `oracle_signal_dir_probe_matrix`: 1 task x 1 budget x 3 providers at
  budget `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`; the runtime proof boundary is a durable dir
  listing artifact via `durable_payload_reference`, and optional
  `listing_entry_count` is additive summary only.
  For the internal zero-argument `dir()` matrix, the only accepted
  provider/budget wording is `oracle_signal_dir_zero_probe_matrix`: 1 task x 1
  budget x 3 providers at budget `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; runtime proof
  requires non-empty `durable_payload_reference`, optional
  `listing_entry_count` is additive summary only, primary selector and
  selected-unit truth remain `unsupported/opaque`, runtime provenance remains
  additive only, and public comparative claims remain bounded to the existing
  quad matrix.
  For the internal `METACLASS_BEHAVIOR` matrix, the only accepted
  provider/budget wording is `oracle_signal_metaclass_behavior_probe_matrix`:
  1 task x 1 budget x 3 providers at budget `220`, against providers
  `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`, with
  runtime payload `class_creation_outcome=created_class`;
  `durable_payload_reference` is required and non-empty, optional
  `created_class_qualified_name` and `selected_metaclass_qualified_name`
  fields are additive summary only, attachment is limited to the preserved full
  `metaclass=...` keyword-site unsupported construct, selector and
  selected-unit primary truth remain `unsupported/opaque`, runtime provenance
  remains additive only, and public comparative claims remain bounded to the
  existing quad matrix.
  For the current internal eval-only `EXEC_OR_EVAL` /
  `eval(source)` matrix, the only accepted provider/budget wording is
  `oracle_signal_eval_probe_matrix`: 1 task x 1 budget x 3 providers at budget
  220, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`; the runtime payload/proof boundary is
  `evaluation_outcome=returned_value`, `source_shape=literal_expression`,
  valid `source_sha256`, and non-empty `durable_payload_reference`; optional
  `result_type=builtins.str` is additive summary only, runtime provenance
  attaches only to the preserved `EXEC_OR_EVAL` unsupported finding for
  `eval(source)`, primary selector and selected-unit truth remain
  `unsupported/opaque`, additive runtime provenance remains separate from
  primary truth, and public comparative claims remain bounded to the existing
  quad matrix.
  For the current internal eval-only `EXEC_OR_EVAL` /
  `exec(source)` matrix, the only accepted provider/budget wording is
  `oracle_signal_exec_probe_matrix`: 1 task x 1 budget x 3 providers at budget
  220, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`; the fixture/call boundary is
  `source = "pass"` and exactly `exec(source)`, the executed source parses as
  exactly one `ast.Pass`, and the runtime payload/proof boundary is
  `execution_outcome=completed`, `source_shape=literal_statement`, valid
  `source_sha256` for exact `"pass"`, and non-empty
  `durable_payload_reference`; optional `statement_kind=pass` is additive
  summary only, runtime provenance attaches only to the preserved
  `EXEC_OR_EVAL` unsupported finding for `exec(source)`, primary selector and
  selected-unit truth remain `unsupported/opaque`, additive runtime provenance
  remains separate from primary truth, no dependency edge or symbol is created
  from executed source, no namespace mutation modeling is added, no
  generated-code dependency modeling is added, and public comparative claims
  remain bounded to the existing quad matrix.
  For the current internal eval-only `DYNAMIC_IMPORT` / root-module
  `importlib.import_module(name)` sibling matrix, the only accepted
  provider/budget wording is
  `oracle_signal_dynamic_import_root_probe_matrix`: 1 task x 1 budget x 3
  providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; the fixture boundary
  is `import importlib`, `name = "plugins.weather"`, and exactly
  `importlib.import_module(name)`; the runtime payload is
  `imported_module=plugins.weather`; primary selector and selected-unit truth
  remain `unsupported/opaque`, runtime provenance remains additive only, no
  dependency edge or symbol is created from the dynamically imported module,
  no `__import__(name)`, imported-name `import_module(name)`, alias or loader
  forms, generalized dynamic import support, or public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is included.
  Do not convert that into a public supported-subset, benchmark, product, or
  generalized hybrid static + runtime claim.
- For reflective-builtin pilot wording, preserve that selector and
  selected-unit primary truth remains `unsupported/opaque`; for the
  zero-argument `dir()` matrix, runtime proof requires non-empty
  `durable_payload_reference` and `listing_entry_count` is additive summary
  only. For the
  `RUNTIME_MUTATION` / `globals()`, `locals()`, `delattr(obj, name)`, and
  `setattr(obj, name, value)` pilots, selector/runtime-mutation surface and
  selected-unit primary truth also remain `unsupported/opaque`. Runtime-backed
  provenance is additive only. For the `METACLASS_BEHAVIOR` pilot, attachment
  is limited to the preserved full `metaclass=...` keyword-site unsupported
  construct, selector and selected-unit primary truth remain
  `unsupported/opaque`, and runtime provenance remains additive only. For the
  current `EXEC_OR_EVAL` / `eval(source)` matrix, runtime provenance attaches
  only to the preserved unsupported finding and remains additive only. For the
  current `EXEC_OR_EVAL` / `exec(source)` matrix, runtime provenance also
  attaches only to the preserved unsupported finding and remains additive only.
  For the current root-module `importlib.import_module(name)` sibling matrix,
  dynamic selector and selected-unit primary truth remain
  `unsupported/opaque`, runtime provenance remains additive only, and no
  static dependency or symbol is created from the dynamically imported module.
  For the narrow builtin `__import__(name)` sibling matrix,
  dynamic selector and selected-unit primary truth remain
  `unsupported/opaque`, runtime provenance remains additive only, and no
  static dependency or symbol is created from `plugins.weather`.
  For the current imported-name `import_module(name)` sibling matrix, dynamic
  selector and selected-unit primary truth remain `unsupported/opaque`,
  runtime provenance remains additive only, and no static dependency or
  selected symbol is created from `plugins.weather`.
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
- Do not describe the root-module `importlib.import_module(name)` sibling
  matrix as generalized dynamic import support or as covering `__import__`,
  imported-name `import_module(name)`, alias, or loader forms.
- Do not describe the builtin `__import__(name)` sibling matrix as generalized
  dynamic import support or as covering `importlib.import_module(name)`,
  imported-name `import_module(name)`, alias, loader, `builtins.__import__`, or
  globals/locals/fromlist forms.
- Do not describe the imported-name `import_module(name)` sibling matrix as
  generalized dynamic import support or as covering root-module
  `importlib.import_module(name)` expansion, literal
  `import_module("plugins.weather")` expansion, alias `load_module(name)`,
  `loader.import_module(name)`, `__import__(name)`, `builtins.__import__`, or
  globals/locals/fromlist forms.
- Do not say "latency reduction," "token savings," or "cost reduction."

## Evidence Map

| ID | Allowed claim | Repo anchors |
| --- | --- | --- |
| AC1 | Context IR is an in-progress semantic-first Python context compiler over a supported static subset. | [README.md](README.md), [EVAL.md](EVAL.md#supported-claims-today), [PLAN.md](PLAN.md) |
| AC2 | Public interface claims are limited to `analyze_repository(...)`, `compile_repository_context(...)`, and one tested MCP compile tool. | [README.md](README.md#python-api), [README.md](README.md#minimal-mcp-usage), [EVAL.md](EVAL.md#supported-claims-today) |
| AC3 | Deterministic internal eval infrastructure exists; the quad matrix remains the current public-safe comparative internal surface, while runtime-backed evidence is limited to narrow internal `DYNAMIC_IMPORT`, `REFLECTIVE_BUILTIN`, `RUNTIME_MUTATION`, `METACLASS_BEHAVIOR`, and `EXEC_OR_EVAL` pilots enumerated in `EVAL.md`. The internal `oracle_signal_dir_zero_probe_matrix` covers only zero-argument `dir()` evidence as 1 task x 1 budget x 3 providers at budget `220`, against providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`; runtime proof requires non-empty `durable_payload_reference`, `listing_entry_count` is additive summary only, primary selector and selected-unit truth remain `unsupported/opaque`, runtime provenance remains additive only, and public comparative claims remain bounded to the existing quad matrix. The internal `oracle_signal_metaclass_behavior_probe_matrix` covers only 1 task x 1 budget x 3 providers at budget `220`, against providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload `class_creation_outcome=created_class`; `durable_payload_reference` is required and non-empty, optional `created_class_qualified_name` and `selected_metaclass_qualified_name` fields are additive summary only, attachment is limited to the preserved full `metaclass=...` keyword-site unsupported construct, selector and selected-unit primary truth remain `unsupported/opaque`, runtime provenance remains additive only, and public comparative claims remain bounded to the existing quad matrix. The internal `oracle_signal_eval_probe_matrix` covers only narrow eval-only `EXEC_OR_EVAL` / `eval(source)` evidence as 1 task x 1 budget x 3 providers at budget 220, against providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload/proof boundary `evaluation_outcome=returned_value`, `source_shape=literal_expression`, valid `source_sha256`, and non-empty `durable_payload_reference`; optional `result_type=builtins.str` is additive summary only, runtime provenance attaches only to the preserved `EXEC_OR_EVAL` unsupported finding for `eval(source)`, primary selector and selected-unit truth remain `unsupported/opaque`, additive runtime provenance remains separate from primary truth, and public comparative claims remain bounded to the existing quad matrix. The internal `oracle_signal_exec_probe_matrix` covers only narrow eval-only `EXEC_OR_EVAL` / `exec(source)` evidence as 1 task x 1 budget x 3 providers at budget 220, against providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`, with fixture/call boundary `source = "pass"` and exactly `exec(source)`, executed source parsing as exactly one `ast.Pass`, runtime payload/proof boundary `execution_outcome=completed`, `source_shape=literal_statement`, valid `source_sha256` for exact `"pass"`, and non-empty `durable_payload_reference`; optional `statement_kind=pass` is additive summary only, runtime provenance attaches only to the preserved `EXEC_OR_EVAL` unsupported finding for `exec(source)`, primary selector and selected-unit truth remain `unsupported/opaque`, additive runtime provenance remains separate from primary truth, no dependency edge or symbol is created from executed source, no namespace mutation modeling is added, no generated-code dependency modeling is added, and public comparative claims remain bounded to the existing quad matrix. The internal `oracle_signal_dynamic_import_root_probe_matrix` covers only narrow eval-only `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)` sibling evidence as 1 task x 1 budget x 3 providers at budget 220, against providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`, with fixture boundary `import importlib`, `name = "plugins.weather"`, and exactly `importlib.import_module(name)`, runtime payload `imported_module=plugins.weather`, primary selector and selected-unit truth `unsupported/opaque`, additive-only runtime provenance, and no dependency edge or symbol created from the dynamically imported module; it excludes `__import__(name)`, imported-name `import_module(name)`, alias or loader forms, and generalized dynamic import support. The narrow internal `oracle_signal_dynamic_import_builtin_probe_matrix` covers only narrow eval-only `DYNAMIC_IMPORT` / builtin `__import__(name)` sibling evidence as 1 task x 1 budget x 3 providers at budget 220, against providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`, with fixture boundary `name = "plugins.weather"`, exactly `__import__(name)`, and bounded `sys.modules[name]` retrieval only, runtime payload `imported_module=plugins.weather`, primary selector and selected-unit truth `unsupported/opaque`, additive-only runtime provenance, and no dependency edge or symbol created from `plugins.weather`; it excludes `importlib.import_module(name)`, imported-name `import_module(name)`, alias or loader forms, `builtins.__import__`, globals/locals/fromlist forms, and generalized dynamic import support. The internal `oracle_signal_dynamic_import_imported_name_probe_matrix` covers only narrow eval-only `DYNAMIC_IMPORT` / imported-name `import_module(name)` sibling evidence as 1 task x 1 budget x 3 providers at budget 220, against providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`, with fixture boundary `from importlib import import_module`, `name = "plugins.weather"`, and exactly `import_module(name)`, runtime payload `imported_module=plugins.weather`, primary selector and selected-unit truth `unsupported/opaque`, additive-only runtime provenance, and no dependency edge or selected symbol created from `plugins.weather`; it excludes root-module `importlib.import_module(name)` expansion, literal `import_module("plugins.weather")` expansion, alias `load_module(name)`, `loader.import_module(name)`, `__import__(name)`, `builtins.__import__`, globals/locals/fromlist forms, and generalized dynamic import support. | [EVAL.md](EVAL.md#current-evidence-status), [EVAL.md](EVAL.md#evidence-categories), [BUILDLOG.md](BUILDLOG.md), [evals/run_specs/oracle_signal_triple_matrix.json](evals/run_specs/oracle_signal_triple_matrix.json), [evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json), [evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json](evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json), [evals/run_specs/oracle_signal_hasattr_probe_matrix.json](evals/run_specs/oracle_signal_hasattr_probe_matrix.json), [evals/run_specs/oracle_signal_getattr_probe_matrix.json](evals/run_specs/oracle_signal_getattr_probe_matrix.json), [evals/run_specs/oracle_signal_getattr_default_probe_matrix.json](evals/run_specs/oracle_signal_getattr_default_probe_matrix.json), [evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json](evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json), [evals/run_specs/oracle_signal_vars_probe_matrix.json](evals/run_specs/oracle_signal_vars_probe_matrix.json), [evals/run_specs/oracle_signal_vars_zero_probe_matrix.json](evals/run_specs/oracle_signal_vars_zero_probe_matrix.json), [evals/run_specs/oracle_signal_globals_probe_matrix.json](evals/run_specs/oracle_signal_globals_probe_matrix.json), [evals/run_specs/oracle_signal_locals_probe_matrix.json](evals/run_specs/oracle_signal_locals_probe_matrix.json), [evals/run_specs/oracle_signal_delattr_probe_matrix.json](evals/run_specs/oracle_signal_delattr_probe_matrix.json), [evals/run_specs/oracle_signal_setattr_probe_matrix.json](evals/run_specs/oracle_signal_setattr_probe_matrix.json), [evals/run_specs/oracle_signal_dir_probe_matrix.json](evals/run_specs/oracle_signal_dir_probe_matrix.json), [evals/run_specs/oracle_signal_dir_zero_probe_matrix.json](evals/run_specs/oracle_signal_dir_zero_probe_matrix.json), [evals/run_specs/oracle_signal_metaclass_behavior_probe_matrix.json](evals/run_specs/oracle_signal_metaclass_behavior_probe_matrix.json), [evals/run_specs/oracle_signal_eval_probe_matrix.json](evals/run_specs/oracle_signal_eval_probe_matrix.json), [evals/run_specs/oracle_signal_exec_probe_matrix.json](evals/run_specs/oracle_signal_exec_probe_matrix.json), [evals/run_specs/oracle_signal_dynamic_import_root_probe_matrix.json](evals/run_specs/oracle_signal_dynamic_import_root_probe_matrix.json), [evals/run_specs/oracle_signal_dynamic_import_builtin_probe_matrix.json](evals/run_specs/oracle_signal_dynamic_import_builtin_probe_matrix.json), [evals/run_specs/oracle_signal_dynamic_import_imported_name_probe_matrix.json](evals/run_specs/oracle_signal_dynamic_import_imported_name_probe_matrix.json) |
| AC4 | The only allowed comparative claim is the fixed-scope quad-matrix claim: within that matrix only, `context_ir` wins all `8/8` task-budget rows and leads the provider-average aggregate. | [EVAL.md](EVAL.md#supported-claims-today), [BUILDLOG.md](BUILDLOG.md), [evals/run_specs/oracle_signal_quad_matrix.json](evals/run_specs/oracle_signal_quad_matrix.json) |
