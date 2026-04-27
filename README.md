# Context IR

Context IR is an in-progress semantic-first Python context compiler for coding
agents.

It currently analyzes a supported static Python subset into a
`SemanticProgram`, derives proven dependencies plus an explicit unresolved or
unsupported frontier, and uses that semantic substrate to rank, optimize, and
compile budgeted context. The repository also includes a minimal MCP stdio
wrapper around the compile facade.

Context IR does not currently make production-readiness, external benchmark,
resolve-rate, token-savings, latency, SWE-bench, or multi-language claims.

## Current Status

The tested local baseline is implemented through:

- `context_ir.analyze_repository(...)`
- package-root semantic contracts exported from `context_ir`
- `context_ir.tool_facade.compile_repository_context(...)`
- a minimal MCP wrapper in `context_ir.mcp_server`
- `EVAL.md` as the evidence and claim-boundary ledger

The accepted semantic-first layers include analyzer orchestration, rendering,
scoring, optimization, compilation, diagnose/recompile contracts, the
tool-facing facade, and the minimal MCP compile tool. They are covered by local
tests and quality gates. The repo also includes deterministic internal eval
infrastructure and a current four-asset signal evidence surface documented in
`EVAL.md`; those artifacts are internal evidence, not external benchmark proof.
`EVAL.md` also records narrow internal runtime-backed pilots for
`DYNAMIC_IMPORT` and narrow `REFLECTIVE_BUILTIN` selectors exercised via
`hasattr(obj, name)`, `getattr(obj, name)`, and narrow internal eval-only
default-return and value-return branches of `getattr(obj, name, default)`, plus
a current internal one-argument `vars(obj)` pilot and a current internal
zero-argument `vars()` pilot, and a current internal eval-only
`RUNTIME_MUTATION` / `globals()` pilot and `locals()` pilot, plus the current
internal eval-only `RUNTIME_MUTATION` / `delattr(obj, name)` pilot, plus
narrow internal eval-only `RUNTIME_MUTATION` /
`setattr(obj, name, value)` evidence, plus a current internal eval-only
one-argument `dir(obj)` pilot, plus a current internal eval-only
zero-argument `dir()` pilot, plus a current internal eval-only
`METACLASS_BEHAVIOR` / preserved `metaclass=...` keyword-site pilot, plus the
current internal eval-only `EXEC_OR_EVAL` / `eval(source)`
evidence, plus the current internal eval-only `EXEC_OR_EVAL` /
`exec(source)` evidence. Those
pilots do not widen the public supported subset, public API, MCP wrapper,
package-export surface, schema, scoring, optimizer, compiler,
winner-selection, product surface, public benchmark claim boundary,
generalized runtime-mutation support, generalized locals() support, or
generalized hybrid-runtime coverage, and they do not make metaclasses part of
the public supported subset. The `EXEC_OR_EVAL` / `eval(source)` release
intentionally adds a narrow lower-layer eval(source) runtime provenance seam in
runtime_acquisition, analyzer, and tool_facade; that seam is internal evidence
plumbing only and does not authorize
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening.
The public-safe quad-matrix comparative boundary remains unchanged, and public
comparative claims remain bounded to the existing quad matrix. The three
existing getattr-family pilot matrices cover only 1 task x 2 budgets x 3
providers at budgets `100` and `220`; the current internal `vars(obj)` pilot
covers only 1 task x 2 budgets x 3 providers at budgets `100` and `220`,
against providers `context_ir`, `lexical_top_k_files`, and
`import_neighborhood_files`, with `lookup_outcome=returned_namespace`. The
current internal zero-argument `vars()` pilot covers only
`oracle_signal_vars_zero_probe_matrix`: 1 task x 2 budgets x 3 providers at
budgets `100` and `220`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`, with
`lookup_outcome=returned_namespace`; selector and selected-unit primary truth
remain `unsupported/opaque`, and runtime-backed provenance is additive only.
The current internal `globals()` pilot covers only
`oracle_signal_globals_probe_matrix`: 1 task x 2 budgets x 3 providers at
budgets `100` and `220`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`, with
`lookup_outcome=returned_namespace`; primary truth remains
`unsupported/opaque`, and runtime-backed provenance is additive only.
The current internal `locals()` pilot covers only
`oracle_signal_locals_probe_matrix`: 1 task x 2 budgets x 3 providers at
budgets `100` and `220`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`, with
`lookup_outcome=returned_namespace`;
selector and selected-unit primary truth remain `unsupported/opaque`, and
runtime-backed provenance is additive only.
The current internal eval-only `RUNTIME_MUTATION` / `delattr(obj, name)` pilot
covers only `oracle_signal_delattr_probe_matrix`: 1 task x 1 budget x 3
providers at budget `220`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
`mutation_outcome=deleted_attribute`; selector and selected-unit primary truth
remain `unsupported/opaque`, and runtime provenance remains additive only.
The current internal eval-only `RUNTIME_MUTATION` /
`setattr(obj, name, value)` evidence is narrow and covers only
`oracle_signal_setattr_probe_matrix`: 1 task x 1 budget x 3 providers at
budget `220`, against providers `context_ir`, `lexical_top_k_files`, and
`import_neighborhood_files`, with runtime payload
`mutation_outcome=returned_none`; selector/runtime-mutation surface and
selected-unit primary truth remain `unsupported/opaque`, runtime provenance
remains additive only, and public comparative claims remain bounded to the
existing quad matrix.
The current internal `dir(obj)` pilot covers only
`oracle_signal_dir_probe_matrix`: 1 task x 1 budget x 3 providers at budget
`220`, against providers `context_ir`, `lexical_top_k_files`, and
`import_neighborhood_files`; durable listing proof is carried by
`durable_payload_reference`, optional `listing_entry_count` is additive summary
only, selector and selected-unit primary truth remain `unsupported/opaque`, and
runtime-backed provenance is additive only.
The current internal zero-argument `dir()` pilot covers only
`oracle_signal_dir_zero_probe_matrix`: 1 task x 1 budget x 3 providers at
budget `220`, against providers `context_ir`, `lexical_top_k_files`, and
`import_neighborhood_files`; runtime proof requires non-empty
`durable_payload_reference`, optional `listing_entry_count` is additive summary
only, primary selector and selected-unit truth remain `unsupported/opaque`,
runtime provenance remains additive only, and public comparative claims remain
bounded to the existing quad matrix.
The current internal eval-only `METACLASS_BEHAVIOR` pilot covers only
`oracle_signal_metaclass_behavior_probe_matrix`: 1 task x 1 budget x 3
providers at budget `220`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
`class_creation_outcome=created_class`; `durable_payload_reference` is required
and non-empty, optional `created_class_qualified_name` and
`selected_metaclass_qualified_name` fields are additive summary only,
attachment is limited to the preserved full `metaclass=...` keyword-site
unsupported construct, selector and selected-unit primary truth remain
`unsupported/opaque`, runtime provenance remains additive only, and public
comparative claims remain bounded to the existing quad matrix.
The current internal eval-only `EXEC_OR_EVAL` / `eval(source)`
evidence covers only `oracle_signal_eval_probe_matrix`: 1 task x 1 budget x 3
providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The runtime
payload/proof boundary is `evaluation_outcome=returned_value`,
`source_shape=literal_expression`, valid `source_sha256`, and non-empty
`durable_payload_reference`; optional `result_type=builtins.str` is additive
summary only. Runtime provenance attaches only to the preserved `EXEC_OR_EVAL`
unsupported finding for `eval(source)`. Primary selector and selected-unit
truth remain `unsupported/opaque`, additive runtime provenance remains
separate from primary truth, and public comparative claims remain bounded to
the existing quad matrix. It does not add generalized eval support, exec
support, `eval(source, globals)` support,
`eval(source, globals, locals)` support, generated-code dependency modeling, or
namespace mutation modeling.
The current internal eval-only `EXEC_OR_EVAL` / `exec(source)` evidence covers
only `oracle_signal_exec_probe_matrix`: 1 task x 1 budget x 3 providers at
budget 220, against providers `context_ir`, `lexical_top_k_files`, and
`import_neighborhood_files`. The fixture/call boundary is `source = "pass"`
and exactly `exec(source)`; the executed source parses as exactly one
`ast.Pass`. This evidence does not cover `exec("pass")`,
`exec(source + suffix)`, `exec(source=source)`, `exec(source, globals)`,
`exec(source, globals, locals)`, `builtins.exec`, or `eval`. The runtime
payload/proof boundary is `execution_outcome=completed`,
`source_shape=literal_statement`, valid `source_sha256` for exact `"pass"`,
and non-empty `durable_payload_reference`; optional `statement_kind=pass` is
additive summary only. Runtime provenance attaches only to the preserved
`EXEC_OR_EVAL` unsupported finding for `exec(source)`. Primary selector and
selected-unit truth remain `unsupported/opaque`, additive runtime provenance
remains separate from primary truth, no dependency edge or symbol is created
from executed source, no namespace mutation modeling is added, no
generated-code dependency modeling is added, and public comparative claims
remain bounded to the existing quad matrix.
The current internal eval-only `DYNAMIC_IMPORT` / root-module
`importlib.import_module(name)` sibling evidence covers only
`oracle_signal_dynamic_import_root_probe_matrix`: 1 task x 1 budget x 3
providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is `import importlib`, `name = "plugins.weather"`, and exactly
`importlib.import_module(name)`. The runtime payload is
`imported_module=plugins.weather`; primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, no
dependency edge or symbol is created from the dynamically imported module, and
public comparative claims remain bounded to the existing quad matrix. This
evidence does not cover `__import__(name)`, imported-name
`import_module(name)`, alias or loader forms, generalized dynamic import
support, or public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening.

## Supported Subset and Limits

The current analyzer targets a narrow static Python subset:

- repository Python files and modules
- imports that can be resolved by the current static repository rules
- function, async function, class, and method definitions
- module, class, and function lexical bindings
- direct supported references for dependency/frontier derivation
- narrow class-level `@dataclass` support when it resolves to
  `dataclasses.dataclass`

When the analyzer cannot prove a fact within that subset, it surfaces
unresolved or unsupported constructs instead of fabricating semantic
dependencies.

Unsupported limits include:

- dynamic imports and reflective module loading
- `exec` and `eval`
- monkey patching and runtime code generation
- metaclasses and runtime attribute injection
- broad decorator semantics beyond the current narrow `@dataclass` support
- broad dynamic Python behavior
- multi-language analysis

The repo does contain narrow internal runtime-backed eval evidence for selected
unsupported `DYNAMIC_IMPORT` cases and narrow `REFLECTIVE_BUILTIN` pilots over
`hasattr(obj, name)`, `getattr(obj, name)`, and the eval-only default-return
and value-return branches of `getattr(obj, name, default)` selectors, plus the
current internal one-argument `vars(obj)` selector and zero-argument `vars()`
selector, plus the current internal eval-only `RUNTIME_MUTATION` / `globals()`
and `locals()` pilots, plus the current internal eval-only `RUNTIME_MUTATION` /
`delattr(obj, name)` pilot, plus the current narrow internal eval-only
`RUNTIME_MUTATION` / `setattr(obj, name, value)` evidence, plus the current
internal one-argument `dir(obj)` pilot, plus the current internal eval-only
zero-argument `dir()` pilot, plus the current internal eval-only
`METACLASS_BEHAVIOR` / preserved `metaclass=...` keyword-site pilot, plus
narrow internal eval-only `EXEC_OR_EVAL` / `eval(source)` and `exec(source)`
evidence, plus narrow internal eval-only `DYNAMIC_IMPORT` / root-module
`importlib.import_module(name)` sibling evidence. The `exec(source)` evidence is bounded to
`oracle_signal_exec_probe_matrix` and the exact `source = "pass"` /
`exec(source)` fixture described in `EVAL.md`.
The root-module dynamic-import sibling evidence is bounded to
`oracle_signal_dynamic_import_root_probe_matrix` and the exact
`import importlib`, `name = "plugins.weather"`,
`importlib.import_module(name)` fixture described in `EVAL.md`.
That evidence is additive internal provenance on
otherwise unsupported/opaque selectors, mutation surfaces, metaclass keyword
sites, preserved `EXEC_OR_EVAL` unsupported findings, and selected units;
it does not make broad dynamic imports, reflection, runtime mutation,
generalized runtime-mutation support, generalized locals() support,
generalized hybrid-runtime coverage, generalized `exec` behavior, generalized
dynamic-import support, or generalized reflective-builtin behavior part of the
public supported subset, and it does not make metaclasses part of the public
supported subset.

## Python API

Use the package root for the public low-level analyzer:

```python
from context_ir import analyze_repository

program = analyze_repository("/path/to/repo")

print(len(program.resolved_symbols))
print(len(program.proven_dependencies))
print(len(program.unresolved_frontier))
print(len(program.unsupported_constructs))
```

Use the tool facade for repository compile requests:

```python
from context_ir.tool_facade import (
    SemanticContextRequest,
    compile_repository_context,
)

response = compile_repository_context(
    SemanticContextRequest(
        repo_root="/path/to/repo",
        query="Find the code that handles payment retries",
        budget=4000,
    )
)

print(response.compile_result.document)
print(response.compile_total_tokens, response.compile_budget)
print(response.omitted_unit_ids)
print(response.unresolved_frontier)
print(response.unsupported_constructs)
```

The package root intentionally exposes semantic-first contracts and
`analyze_repository(...)`. Semantic module-level APIs remain available from
their explicit modules; they are not all promoted as package-root functions.

## Minimal MCP Usage

After installing the project, run the local stdio MCP server with:

```bash
python -m context_ir.mcp_server
```

The server registers one tool:

- `compile_repository_context`

Key tool inputs:

- `repo_root`: repository path as a string
- `query`: task or information need
- `budget`: positive integer context budget
- `include_document`: optional boolean; when false, trace and uncertainty
  fields are still returned while the compiled document is omitted

The MCP wrapper is intentionally minimal. Current evidence covers local SDK
registration and local invocation of this one compile tool.

## Development and Validation

Requires Python 3.11+.

```bash
pip install -e ".[dev]"
.venv/bin/python -m ruff check src/ tests/
.venv/bin/python -m ruff format --check src/ tests/
.venv/bin/python -m mypy --strict src/
.venv/bin/python -m pytest tests/ -v -m "not slow"
```

The project depends on the Python MCP SDK through `mcp>=1.27.0` in
`pyproject.toml`.

## Evidence and Claims

`EVAL.md` defines what the repository currently proves, what remains internal
evidence only, and what remains future work.

Current evidence includes:

- unit and integration tests in `tests/`
- local quality gates for lint, format, strict typing, and non-slow tests
- local MCP SDK registration and invocation for the minimal compile wrapper
- deterministic internal eval summary, report, pipeline, manifest, and bundle
  artifacts over raw JSONL ledgers
- four accepted methodology-tightened signal assets:
  `oracle_signal_smoke`, `oracle_signal_smoke_b`, `oracle_signal_smoke_c`, and
  `oracle_signal_smoke_d`
- a current quad matrix over 4 tasks x 2 budgets x 3 providers
- capability-tier and provider-scoped selected-unit accounting in the internal
  eval evidence path
- narrow internal runtime-backed pilots for `DYNAMIC_IMPORT` and
  `REFLECTIVE_BUILTIN` / `hasattr(obj, name)`, `getattr(obj, name)`, and the
  eval-only default-return and value-return branches of
  `getattr(obj, name, default)`, plus the current internal one-argument
  `vars(obj)` and zero-argument `vars()` pilots, plus the current internal
  eval-only `RUNTIME_MUTATION` / `globals()` and `locals()` pilots, plus the
  current internal eval-only `RUNTIME_MUTATION` / `delattr(obj, name)` pilot,
  plus the current narrow internal eval-only `RUNTIME_MUTATION` /
  `setattr(obj, name, value)` evidence, plus the current internal one-argument
  `dir(obj)` pilot, plus the current internal zero-argument `dir()` pilot,
  plus the current internal eval-only `METACLASS_BEHAVIOR` / preserved
  `metaclass=...` keyword-site pilot, plus the current internal
  eval-only `EXEC_OR_EVAL` / `eval(source)` evidence, plus the current
  internal eval-only `EXEC_OR_EVAL` / `exec(source)` evidence, plus the
  current internal eval-only `DYNAMIC_IMPORT` / root-module
  `importlib.import_module(name)` sibling evidence
- three existing getattr-family provider/budget matrices limited to budgets
  `100` and `220`; each remains 1 task x 2 budgets x 3 providers, with
  selector and selected-unit primary truth still `unsupported/opaque` and
  runtime-backed provenance additive only
- the current internal `vars(obj)` pilot remains 1 task x 2 budgets x 3 providers
  at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`, selector and selected-unit primary truth
  still `unsupported/opaque`, and runtime-backed provenance additive only
- the current internal zero-argument `vars()` pilot remains
  `oracle_signal_vars_zero_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`, selector and selected-unit primary truth
  still `unsupported/opaque`, and runtime-backed provenance additive only
- the current internal `globals()` pilot remains
  `oracle_signal_globals_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`, primary truth still
  `unsupported/opaque`, and runtime-backed provenance additive only
- the current internal `locals()` pilot remains
  `oracle_signal_locals_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`,
  selector and selected-unit primary truth still `unsupported/opaque`, and
  runtime-backed provenance additive only
- the current internal eval-only `RUNTIME_MUTATION` / `delattr(obj, name)`
  pilot remains `oracle_signal_delattr_probe_matrix`: 1 task x 1 budget x 3
  providers at budget `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
  `mutation_outcome=deleted_attribute`, selector and selected-unit primary
  truth still `unsupported/opaque`, and runtime provenance additive only
- the current internal eval-only `RUNTIME_MUTATION` /
  `setattr(obj, name, value)` evidence is narrow and remains
  `oracle_signal_setattr_probe_matrix`: 1 task x 1 budget x 3 providers at
  budget `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`, with runtime payload
  `mutation_outcome=returned_none`, selector/runtime-mutation surface and
  selected-unit primary truth still `unsupported/opaque`, runtime provenance
  additive only, and public comparative claims remain bounded to the existing
  quad matrix
- the current internal `dir(obj)` pilot remains
  `oracle_signal_dir_probe_matrix`: 1 task x 1 budget x 3 providers at budget
  `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`; durable listing proof is carried by
  `durable_payload_reference`, optional `listing_entry_count` is additive
  summary only, selector and selected-unit primary truth still
  `unsupported/opaque`, and runtime-backed provenance additive only
- the current internal zero-argument `dir()` pilot remains
  `oracle_signal_dir_zero_probe_matrix`: 1 task x 1 budget x 3 providers at
  budget `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`; runtime proof requires non-empty
  `durable_payload_reference`, optional `listing_entry_count` is additive
  summary only, primary selector and selected-unit truth still
  `unsupported/opaque`, runtime provenance additive only, and public
  comparative claims remain bounded to the existing quad matrix
- the current internal eval-only `METACLASS_BEHAVIOR` pilot remains
  `oracle_signal_metaclass_behavior_probe_matrix`: 1 task x 1 budget x 3
  providers at budget `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
  `class_creation_outcome=created_class`; `durable_payload_reference` is
  required and non-empty, optional `created_class_qualified_name` and
  `selected_metaclass_qualified_name` fields are additive summary only,
  attachment is limited to the preserved full `metaclass=...` keyword-site
  unsupported construct, selector and selected-unit primary truth still
  `unsupported/opaque`, runtime provenance additive only, and public
  comparative claims remain bounded to the existing quad matrix
- the current internal eval-only `EXEC_OR_EVAL` /
  `eval(source)` evidence remains `oracle_signal_eval_probe_matrix`: 1 task x
  1 budget x 3 providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; the runtime
  payload/proof boundary is `evaluation_outcome=returned_value`,
  `source_shape=literal_expression`, valid `source_sha256`, and non-empty
  `durable_payload_reference`; optional `result_type=builtins.str` is additive
  summary only, runtime provenance attaches only to the preserved
  `EXEC_OR_EVAL` unsupported finding for `eval(source)`, primary selector and
  selected-unit truth still `unsupported/opaque`, additive runtime provenance
  separate from primary truth, and public comparative claims remain bounded to
  the existing quad matrix
- the current internal eval-only `EXEC_OR_EVAL` /
  `exec(source)` evidence remains `oracle_signal_exec_probe_matrix`: 1 task x
  1 budget x 3 providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; the fixture/call
  boundary is `source = "pass"` and exactly `exec(source)`, the executed source
  parses as exactly one `ast.Pass`, and the runtime payload/proof boundary is
  `execution_outcome=completed`, `source_shape=literal_statement`, valid
  `source_sha256` for exact `"pass"`, and non-empty
  `durable_payload_reference`; optional `statement_kind=pass` is additive
  summary only, runtime provenance attaches only to the preserved
  `EXEC_OR_EVAL` unsupported finding for `exec(source)`, primary selector and
  selected-unit truth still `unsupported/opaque`, additive runtime provenance
  separate from primary truth, no dependency edge or symbol is created from
  executed source, no namespace mutation modeling is added, no generated-code
  dependency modeling is added, and public comparative claims remain bounded
  to the existing quad matrix
- the current internal eval-only `DYNAMIC_IMPORT` / root-module
  `importlib.import_module(name)` sibling evidence remains
  `oracle_signal_dynamic_import_root_probe_matrix`: 1 task x 1 budget x 3
  providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; the fixture boundary
  is `import importlib`, `name = "plugins.weather"`, and exactly
  `importlib.import_module(name)`; the runtime payload is
  `imported_module=plugins.weather`; primary selector and selected-unit truth
  still `unsupported/opaque`, runtime provenance additive only, no dependency
  edge or symbol is created from the dynamically imported module, and public
  comparative claims remain bounded to the existing quad matrix
- within the fixed quad matrix, `context_ir` wins all 8/8 task-budget
  rows; provider-average aggregate scores are
  `0.9599139230003012` for `context_ir`,
  `0.6228480543023547` for `import_neighborhood_files`, and
  `0.6065653086866415` for `lexical_top_k_files`

Earlier signal pair/triple matrices remain historical internal evidence. The
current public-safe comparative surface is the four-asset quad matrix
documented in `EVAL.md`. That surface is broader than the previous public
summary, but it is still not uniformly clean: `oracle_signal_smoke_b` at budget
`200` still records honest `budget_pressure`, and
`def:pkg/digest.py:pkg.digest.render_assignment_digest` can remain omitted under
that tight budget.

The project currently makes no SWE-bench, external benchmark improvement,
resolve-rate, production-readiness, performance, token-savings, cost-reduction,
or multi-language claims. The runtime-backed pilots are internal evidence only;
stronger public claims require the claim gates and raw evidence described in
`EVAL.md`.

## Legacy API Note

Older graph-first modules remain directly importable by their explicit module
paths as implementation history and legacy compatibility. They are not the
current public package-root API. New usage should start from
`context_ir.analyze_repository(...)` and, for tool-facing compilation,
`context_ir.tool_facade.compile_repository_context(...)`.
