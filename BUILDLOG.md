# BUILDLOG.md -- Decision Log

Most recent supersession entries override older architectural decisions when they explicitly say so. Older entries remain intact below as history.

## 2026-04-16 -- Deterministic Metric Scoring Core

- Added deterministic per-run eval scoring first-pass
- Added `src/context_ir/eval_metrics.py` with `score_eval_run(setup, result) -> EvalRunMetrics`
- The scorer now computes deterministic per-run outputs over accepted oracle and provider inputs:
  - budget compliance
  - edit coverage
  - support coverage
  - representation adequacy
  - uncertainty honesty
  - credited relevant tokens
  - noise tokens, noise ratio, and noise efficiency
  - aggregate score with weight renormalization when support or uncertainty components are absent
- The scorer uses the accepted deterministic rules for:
  - detail-rank adequacy across `identity`, `summary`, and `source`
  - Context IR structured trace matching
  - whole-file baseline source adequacy
  - selected and omitted uncertainty honesty credit
  - exact source-span token credit
  - overlap merging for source-span credits
- Added `tests/test_eval_metrics.py` covering detail-rank behavior, source-level baseline adequacy, `None` handling for support and uncertainty components, selected and omitted uncertainty credit, exact-span token credit, overlapping-span merge behavior, non-mutation, and internal-only scope boundaries
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 254 passed and 1 deselected
- Raw ledgers, reports, run-matrix execution, and public-claim updates remain deferred
- Acceptance status: first-pass

## 2026-04-16 -- Deterministic Provider/Baseline Infrastructure

- Added deterministic internal eval provider infrastructure after 1 correction
- Added `src/context_ir/eval_providers.py` with:
  - typed provider request, config, metadata, and result dataclasses
  - shared token estimator `max(1, (len(text) + 3) // 4)`
  - deterministic lexical tokenization and lexical file scoring
  - whole-file budget-aware packing for baseline providers
  - Context IR provider delegation through `compile_repository_context(...)` with `embed_fn=None`
  - deterministic `lexical_top_k_files`, `import_neighborhood_files`, and diagnostic `file_order_floor` providers
- Added `tests/test_eval_providers.py` covering token estimation, lexical tokenization, lexical ordering, zero-match behavior, header-aware budget packing, import-neighborhood seed/import behavior, star-import warning behavior, missing/external import handling, diagnostic baseline marking, Context IR facade delegation, no-oracle provider inputs, and internal-only scope boundaries
- Control review initially found one metadata-contract issue:
  - Context IR provider output collapsed selection trace and warnings too aggressively for the later scoring slice
- Correction pass added structured Context IR metadata:
  - `EvalSelectedUnit`
  - `EvalProviderWarning`
  - `EvalProviderMetadata.selected_units`
  - `EvalProviderMetadata.warning_details`
- Context IR provider output now preserves:
  - selected unit `unit_id`, `detail`, `token_count`, `basis`
  - selected unit `reason`, `edit_score`, and `support_score`
  - warning `code`, `unit_id`, and `message`
- `EvalProviderResult` now rejects lossy mismatches between convenience tuples and the structured Context IR metadata
- Validation confirmed after correction:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 243 passed and 1 deselected
- Metric scoring, raw result ledgers, reports, and public-claim updates remain deferred
- Acceptance status: 1 correction

## 2026-04-15 -- Eval Oracle Foundation

- Added the deterministic eval oracle foundation after 1 correction
- Added `src/context_ir/eval_oracles.py` as an internal module with:
  - typed dataclasses for eval tasks, selectors, resolved selector records, and setup results
  - JSON task loading
  - generated runtime-ID field rejection
  - strict unknown-field rejection for task records and selector records
  - selector resolution through `analyze_repository(...)`
  - loud unresolved and ambiguous selector setup failures
- Added durable smoke eval assets under `evals/`:
  - `evals/fixtures/oracle_smoke/main.py`
  - `evals/fixtures/oracle_smoke/pkg/__init__.py`
  - `evals/fixtures/oracle_smoke/pkg/helpers.py`
  - `evals/tasks/oracle_smoke.json`
- Added `tests/test_eval_oracles.py` covering typed loading, generated-ID rejection, unknown-field rejection, deterministic symbol/frontier/unsupported selector resolution, analyzer usage, unresolved and ambiguous failure paths, no mutation, and no public/package/provider/baseline/scoring/report expansion
- Control review initially found one schema-strictness issue: unknown task and selector fields were silently accepted
- Correction pass added allowed-field validation and tests for unknown top-level, symbol, frontier, and unsupported selector fields
- Validation confirmed after correction:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 229 passed and 1 deselected
- Provider adapters, baseline providers, metric scoring, raw result output, reports, and public-claim updates remain deferred
- Acceptance status: 1 correction

## 2026-04-15 -- Deterministic Fixture-Level Eval Design

- Accepted the read-only deterministic fixture-level eval design slice after 2 corrections
- The accepted design answers the evidence-building question: whether Context IR produces higher-quality context packs than simple deterministic retrieval baselines under fixed budgets on repo-controlled coding-agent fixtures
- Correction 1 froze:
  - deterministic `lexical_top_k_files` and `import_neighborhood_files` baseline algorithms
  - shared token estimator and whole-document budget accounting
  - credited-relevant-token, noise, coverage, representation, and uncertainty metric rules
  - success, failure, negative-evidence, and no-public-claim gates
  - uncertainty scoring policy requiring selected document, selected trace, omitted surface, or optimization-warning evidence rather than dormant facade metadata
- Correction 2 replaced generated unit-ID oracles with stable selector-based task records resolved at run time through `analyze_repository(...)`
- The accepted next implementation slice is narrowed to the eval oracle foundation:
  - eval asset layout
  - task schema or strict loader
  - selector resolver
  - tiny fixtures/task records
  - tests proving symbol, frontier, and unsupported selectors resolve deterministically
  - tests proving unresolved or ambiguous selectors fail setup loudly
- Provider adapters, baseline providers, metric scoring, raw JSONL output, reports, and public-claim updates remain deferred until the oracle foundation is accepted
- No files were changed by the execution research lane; control-lane continuity was updated after acceptance
- Acceptance status: 2 corrections

## 2026-04-15 -- Release Sequencing

- Released the accepted semantic-first baseline to `origin/main`
- Current released commit verified locally: `9abc57c Rebaseline Context IR around semantic analysis`
- Local `main` has no ahead/behind marker relative to `origin/main`
- Release state now distinguishes the accepted/pushed semantic baseline from the next evidence-building phase
- Acceptance status: first-pass

## 2026-04-15 -- README / Public-Claim Sync

- Updated `README.md` to match the accepted semantic-first public surface and `EVAL.md` claim boundaries
- README now describes:
  - Context IR as an in-progress semantic-first Python context compiler
  - supported static Python subset and explicit unsupported limits
  - public analyzer usage through `context_ir.analyze_repository(...)`
  - tool-facing compile usage through `context_ir.tool_facade.compile_repository_context(...)`
  - minimal MCP stdio usage through `python -m context_ir.mcp_server`
  - local development and validation commands
  - evidence limits and unsupported SWE-bench, benchmark, production, performance, and multi-language claims
  - legacy graph-first modules as direct-module compatibility only, not package-root public API
- Removed stale README framing that renderer, ranking, optimizer, compiler, recompile, MCP, and eval work were still all pending
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- Eval Methodology and Evidence Baseline

- Added `EVAL.md` as the repo evidence and methodology baseline
- The evidence ledger distinguishes:
  - behavior proven by current unit/integration tests
  - local quality-gate validation
  - protocol smoke-test evidence
  - architecturally intended but unevaluated work
  - unsupported benchmark, performance, production, multi-language, and portfolio claims
- `EVAL.md` records allowed claims for the accepted semantic-first core, analyzer, package-root quarantine, tool-facing facade, and minimal MCP wrapper
- `EVAL.md` explicitly disallows SWE-bench, benchmark improvement, resolve-rate, production-readiness, multi-language, broad dynamic-Python, performance, and complete-product MCP claims without further evidence
- Future eval slices are scoped as deterministic fixture-level behavioral eval, budget-curve harness design, baseline comparison design, raw result ledger, and only later SWE-bench-style methodology
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- Minimal MCP Wrapper

- Accepted the minimal MCP wrapper after explicit human authorization for the dependency/protocol path
- Added the official Python MCP SDK dependency: `mcp>=1.27.0`
- Verified local SDK metadata: installed `mcp` version `1.27.0`, `Requires-Python >=3.10`
- Added `src/context_ir/mcp_server.py` using `mcp.server.fastmcp.FastMCP` from the official SDK
- Registered exactly one MCP tool: `compile_repository_context`
- The tool:
  - validates inputs
  - rejects non-positive budgets with JSON-safe errors
  - delegates to `context_ir.tool_facade.compile_repository_context(...)`
  - serializes document, token totals, budget, confidence, selection trace, omitted units, unresolved frontier, unsupported constructs, syntax diagnostics, semantic diagnostics, and optimization warnings
  - supports `include_document=false` while preserving trace and uncertainty output
  - preserves package-root export quarantine
- Added `tests/test_mcp_server.py` covering delegation, JSON-safe serialization, document omission, uncertainty surfacing, parse diagnostics, invalid budget errors, retired API avoidance, package-root non-exposure, and SDK registration/local invocation
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- MCP Wrapper Dependency/Protocol Hold

- MCP wrapper implementation lane returned `NEEDS-CONTROL` with no files changed
- Reason: the repo has no MCP dependency, no existing MCP/server/protocol surface, and neither `mcp` nor `fastmcp` is installed in the local environment
- Control assessment: the execution lane correctly stopped rather than guessing an SDK API or writing a speculative protocol shim
- Human authorization is required before adding a new MCP dependency or declaring a protocol/transport choice
- Recommended next authorized action, if approved:
  - add and verify the official Python MCP SDK dependency
  - use stdio transport for the first server
  - implement one minimal compile tool over `context_ir.tool_facade.compile_repository_context(...)`
  - test JSON-safe output, uncertainty surfacing, invalid-budget errors, and SDK registration/local invocation
- Acceptance status: held

## 2026-04-15 -- Tool-Facing Facade Contract

- Added `src/context_ir/tool_facade.py` with:
  - `SemanticContextRequest`
  - `SemanticContextResponse`
  - `compile_repository_context(...)`
- The facade delegates directly to the accepted public analyzer and semantic compiler:
  - `analyze_repository(...)`
  - `compile_semantic_context(...)`
- The facade response transparently exposes:
  - returned `SemanticProgram`
  - returned `SemanticCompileResult`
  - unresolved frontier
  - unsupported constructs
  - syntax and semantic diagnostics
  - optimization warnings
  - selection trace
  - omitted unit IDs
  - compile budget and total tokens
- Package-root exports were intentionally left unchanged; the facade remains available through `context_ir.tool_facade`
- Added `tests/test_tool_facade.py` to lock delegation, uncertainty surfacing, parse-error truthfulness, budget honesty, retired graph-first API avoidance, optional embedding pass-through, and package-root non-exposure
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- Package-Root Public API and Legacy Quarantine

- Updated `src/context_ir/__init__.py` so package-root exports are semantic-first
- Kept `context_ir.analyze_repository` as the promoted public low-level API
- Root exports now mirror the public semantic contract types from `semantic_types.py`
- Removed retired graph-first root bindings and `__all__` entries for:
  - `compile`
  - `optimize`
  - `parse_file`
  - `parse_repository`
  - `render`
  - `score_graph`
- Preserved direct old-module import compatibility for the retired graph-first modules
- Added `tests/test_public_api.py` to lock:
  - root `__all__` policy
  - root analyzer availability
  - retired graph-first root quarantine
  - direct old-module import compatibility
  - semantic module-level API availability through explicit modules
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- Semantic Analyzer Public Contract

- Added `analyze_repository(repo_root: Path | str) -> SemanticProgram` as the real public low-level semantic analysis API
- Added `src/context_ir/analyzer.py` to orchestrate the accepted semantic-first pipeline:
  - `extract_syntax(repo_root)`
  - `bind_syntax(syntax)`
  - `resolve_semantics(bound_program)`
  - `derive_dependency_frontier(resolved_program)`
- Replaced the `semantic_types.py` placeholder with a lazy wrapper that preserves `from context_ir.semantic_types import analyze_repository`
- Package-root `context_ir.analyze_repository` remains available through the existing export path
- Added analyzer tests for:
  - parity with the accepted manual pipeline
  - `Path` and `str` repo roots
  - package-root and semantic-types import paths
  - parse-error truthfulness
  - presence of derived binder/resolver/dependency/frontier outputs
  - narrow orchestration boundaries
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- Final-Phase Planning

- Accepted final-phase decomposition planning for MCP / eval / portfolio-facing work
- Planning confirmed current repo reality:
  - `analyze_repository(repo_root) -> SemanticProgram` remains the approved public low-level API but is still a loud placeholder
  - semantic-first core APIs exist as module-level surfaces, while package-root exports still include retired graph-first APIs
  - no MCP server, CLI, tool-facing adapter, eval harness, benchmark suite, or console entry point exists yet
  - README remains stale relative to the accepted semantic-first core
  - accepted semantic-first work is present in the workspace but not yet committed or pushed
- Control decision: the next implementation slice is the semantic analyzer public contract
- Planned later slices remain separate:
  - package-root API and legacy quarantine
  - tool-facing facade contract
  - MCP wrapper decision and implementation
  - eval methodology and evidence baseline
  - README / portfolio-facing claim sync
  - final release and continuity sequencing
- Public claims, benchmark framing, and MCP protocol work remain paused until their dedicated evidence-backed slices
- Acceptance status: first-pass

## 2026-04-14 -- Diagnose and Recompile Reset

- Added semantic-first diagnose/recompile contracts in `src/context_ir/semantic_types.py`:
  - `SemanticMissKind`
  - `SemanticMissEvidence`
  - `SemanticDiagnosticResult`
  - `SemanticRecompileResult`
  - narrow `SemanticCompileContext`
- Updated `compile_semantic_context(...)` to persist the prior query in `SemanticCompileResult.compile_context`
- Added `diagnose_semantic_miss(...)` and `recompile_semantic_context(...)` in `src/context_ir/semantic_diagnostics.py`
- Diagnose now grounds supported miss evidence only to accepted semantic unit IDs and distinguishes:
  - omitted units
  - selected-but-too-shallow units
  - already sufficient units
  - ungrounded evidence
- Recompile now re-scores from the prior query, applies conservative miss-driven boosts, and recompiles under `previous_result.budget + delta_budget` without mutating inputs
- Correction pass fixed two reviewed P1 grounding defects:
  - inconsistent stack traces with mismatched file/function clues no longer ground to unrelated units
  - path grounding now rejects arbitrary substrings and only accepts conservative path-shaped matches
- Validation confirmed after correction: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: 1 correction

## 2026-04-14 -- Optimizer and Compile Reset

- Added semantic-first optimization and compile contracts in `src/context_ir/semantic_types.py` for:
  - `SemanticSelectionRecord`
  - `SemanticOptimizationWarning`
  - `SemanticOptimizationResult`
  - `SemanticCompileResult`
- Added `optimize_semantic_units(program, scoring, budget) -> SemanticOptimizationResult` in `src/context_ir/semantic_optimizer.py`
- Added `compile_semantic_context(program, query, budget, *, scoring=None, embed_fn=None) -> SemanticCompileResult` in `src/context_ir/semantic_compiler.py`
- The new optimizer/compiler stack now operates only on accepted semantic unit IDs and accepted semantic render details (`identity`, `summary`, `source`)
- Correction pass fixed a reviewed P1 contract-honesty defect:
  - compile token accounting now reflects the emitted document, not only selected unit render cost
  - compilation re-optimizes against reserved document-assembly overhead until the emitted artifact fits the requested budget
  - impossibly small budgets now fail loudly rather than returning an over-budget artifact with misleading totals
- `SemanticOptimizationResult.total_tokens` continues to represent selected-unit render cost, while `SemanticCompileResult.total_tokens` now represents the assembled artifact cost
- Validation confirmed after correction: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: 1 correction

## 2026-04-14 -- Scorer Reset

- Added `score_semantic_units(program: SemanticProgram, query: str, *, embed_fn: Callable[[list[str]], list[list[float]]] | None = None) -> SemanticScoringResult` in `src/context_ir/semantic_scorer.py` as the semantic-first scorer entry point on top of the accepted renderer baseline
- Established a minimal separate scorer-result contract with:
  - `SemanticUnitScore` carrying `unit_id`, `p_edit`, and `p_support`
  - `SemanticScoringResult` carrying the query plus the score map
- The scorer now ranks every renderable semantic unit ID:
  - proven symbols
  - unresolved frontier items
  - unsupported constructs
- Direct relevance drives `p_edit`, one-hop propagation over accepted `proven_dependencies` raises only `p_support`, and uncertainty items may gain support from a directly relevant enclosing scope
- Scores remain bounded in `[0.0, 1.0]`, the scorer does not mutate `SemanticProgram`, and embedding-based similarity remains optional through injected `embed_fn`
- Boundary note: package-root exposure for the new semantic scorer remains deferred; the retired `score_graph(...)` surface was intentionally left untouched in this slice
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-14 -- Renderer Reset

- Added `render_semantic_unit(program: SemanticProgram, unit_id: str, detail: RenderDetail) -> RenderedUnit` in `src/context_ir/semantic_renderer.py` as the semantic-first renderer entry point on top of the accepted dependency/frontier substrate
- Established a minimal semantic-first representation baseline with three detail levels:
  - `IDENTITY` for concise identity plus provenance
  - `SUMMARY` for semantic summary plus provenance
  - `SOURCE` for exact source-backed rendering or truthful source-unavailable fallback
- The renderer now supports one unified API across:
  - proven repository-backed symbols
  - unresolved frontier items
  - unsupported constructs
- Proven dataclass support and dataclass field facts are surfaced in rendered symbol summaries when present in accepted lower-layer facts
- Each rendered unit now carries positive token accounting for later optimizer work
- Boundary note: unsupported constructs do not currently carry a lower-layer reference context, so renderer output surfaces `context: unavailable` instead of inventing missing context
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-14 -- Semantic Dependency Graph and Frontier

- Added `derive_dependency_frontier(program: SemanticProgram) -> SemanticProgram` as the dependency/frontier derivation entry point on top of the accepted resolver substrate
- The slice now derives repository-backed semantic dependencies for:
  - imports from the owning module/class/function/method scope
  - calls from the owning module/function/method scope
  - proven base-class references
  - proven decorator references
- The slice now surfaces explicit frontier/unsupported records for:
  - supported-but-unresolved simple-name and direct-attribute decorator/base/call surfaces
  - star imports
  - unsupported decorator/base/call target shapes outside the accepted direct grammar
- Parse-error files remain excluded from dependency/frontier facts
- Boundary note: ordinary unresolved non-star imports still do not have a dedicated honest frontier surface in the current contracts; this slice stayed conservative and did not force those cases into misleading records
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-14 -- Resolver and Object Model

- Added `resolve_semantics(program: SemanticProgram) -> SemanticProgram` as the resolver / object-model entry point on top of the accepted binder substrate
- Resolver now records proven import targets, proven decorator/base/call references for supported direct forms, and narrow dataclass object facts using only binder output plus `SemanticProgram.syntax`
- Narrow dataclass support is now mirrored onto the owning class `ResolvedSymbol` when the resolver can actually prove `dataclasses.dataclass`
- Correction pass fixed three reviewed P1 defects:
  - proven dataclass support now reaches the class symbol
  - bare module imports no longer become proven decorator/base references
  - non-aliased dotted imports require proof of the full dotted module path before a `ResolvedImport` is recorded
- `proven_dependencies` remains empty by design in this slice; semantic dependency/frontier derivation remains the next layer
- Validation confirmed after correction: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: 1 correction

## 2026-04-14 -- Binder and Scope Model

- Added `bind_syntax(syntax: SyntaxProgram) -> SemanticProgram` as the binder / scope-model entry point
- Binder reuses syntax-backed definition IDs as stable semantic symbol IDs and carries `SemanticProgram.syntax` through unchanged
- Binder emits definition, parameter, import, simple identifier assignment, and provable class-attribute binding facts with ordered binding history preserved for later shadowing resolution
- Files with `SyntaxDiagnosticCode.PARSE_ERROR` do not contribute binder-owned semantic facts
- Narrow prerequisite contract correction landed with this slice: `ImportFact` now carries `scope_id`, and parser population of that field keeps nested import bindings in the correct lexical scope
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-14 -- Parameter-Facts Prerequisite Correction

- Accepted follow-up parser correction to preserve parameter declaration order, parameter kinds, default metadata, and source sites needed by binder and resolver work
- Validation remained clean after the correction
- Acceptance status: first-pass

## 2026-04-14 -- Syntax Parse-Failure Correction

- Accepted follow-up parser correction to emit explicit `SyntaxDiagnosticCode.PARSE_ERROR` diagnostics for syntax-invalid files
- Parse-error files remain in source inventory but are excluded from trustworthy semantic fact production beyond the syntax-level scaffold
- Validation remained clean after the correction
- Acceptance status: first-pass

## 2026-04-14 -- Syntax Parser Reset

- Accepted the semantic-first parser reset after 1 correction
- `extract_syntax(...)` and `extract_syntax_file(...)` now produce `SyntaxProgram` facts for supported Python files instead of feeding the retired heuristic symbol-graph contract
- Syntax extraction now preserves source inventory, raw definitions, imports, decorators, base expressions, assignments, call sites, attribute sites, and other source-backed facts needed for later semantic analysis
- Legacy `parse_file(...)` and `parse_repository(...)` compatibility entry points remain compiling during the rebaseline so the old stack can stay importable while it is being replaced slice by slice
- Acceptance status: 1 correction

## 2026-04-14 -- Semantic Contracts and Types

- Accepted the semantic contracts / types slice after 1 correction
- Introduced the `SyntaxProgram` and `SemanticProgram` contract surfaces plus the shared dataclasses and enums needed for later parser, binder, resolver, dependency, renderer, ranking, optimization, compiler, and diagnostics work
- Established explicit supported-subset, proof-status, unresolved-frontier, and unsupported-construct surfaces so later slices can report uncertainty without fabricating semantic claims
- Recorded `@dataclass` as the first explicitly supported decorator set in the semantic-first baseline
- Acceptance status: 1 correction

## 2026-04-13 -- Semantic-First Baseline Supersedes Frozen Spec

- Prior April 13 frozen spec retired and superseded as the current authority for planning, architecture, and acceptance
- Human-approved control decisions recorded:
  - Replace the old frozen baseline with the new semantic-first baseline
  - Keep `p_edit` / `p_support`, but only as internal ranking policy rather than the public thesis
  - Keep the multi-tier representation idea, but do not keep the exact 5-tier semantics frozen yet
  - Make `analyze_repository(...) -> SemanticProgram` a public low-level API
  - Include `@dataclass` in the first supported decorator set, scoped narrowly and explicitly
- Control decision: future execution follows the new slice plan:
  1. Docs freeze / continuity reset
  2. Semantic contracts and types
  3. Syntax parser reset
  4. Binder and scope model
  5. Resolver and object model
  6. Semantic dependency graph and frontier
  7. Renderer reset
  8. Scorer reset
  9. Optimizer and compile reset
  10. Diagnose / recompile reset
  11. Only then MCP / eval / portfolio-facing work
- Prior retrospective findings still stand as evidence for why the reset was required
- Earlier slice entries, including any accepted corrections or historical parser/renderer improvements, remain historical record only and do not override the new control state
- Alternatives considered:
  - Continue the old Slice 1 -> Slice 6 correction chain on top of the retired frozen spec
  - Patch only the public `recompile` contract while keeping the prior architecture
  - Rebaseline the system around semantic analysis before resuming higher layers
- Reasoning:
  - Retrospective evidence showed the failure was architectural, not a single top-layer contract issue
  - Semantic contracts, binder behavior, and resolver behavior must exist before ranking, optimization, compilation, or `recompile` can make truthful claims
  - Public positioning must shift from heuristic budget packing to semantically grounded compilation with explicit uncertainty handling
- Acceptance status: first-pass

## 2026-04-13 -- Project Genesis: Context IR

- Concept developed through 3 rounds of research and adversarial review
- Round 1 (ChatGPT): Initial concept development. Identified reference-first context compilation as the thesis. Proposed six-component architecture.
- Round 2 (Claude control lane + execution spike): Competitive landscape validation. Mapped Aider, Codebase-Memory, SWE-agent, Moatless, Agentless. Confirmed gap: no existing tool does budget-aware format selection. Scoped to Option B (MCP server + SWE-bench Mini eval, 4-6 weeks).
- Round 3 (ChatGPT devil's advocate): Sharpened algorithm (symbol-level units, 5-tier hierarchy, dual scoring, dependency-preserving source slices), eval methodology (frozen-input regime, budget curves, ablations), systems engineering signal (recompile loop, compile traces, diagnostics). Confirmed competitive claims (RepoRepair March 2026, SWE-bench Pro preference, Verified submission restrictions).
- Frozen spec locked.
- Build order: compiler core first, MCP wrapper later.
- Tech stack: Python 3.11+, ruff, mypy strict, pytest
- Acceptance status: spec accepted after adversarial review convergence

## 2026-04-13 -- Slice 0: Project Bootstrap

- Initialized Python project with pyproject.toml (Python 3.11+, src layout, setuptools)
- Created adapted AGENTS.md from personal website WoW reference
- Created PLAN.md with frozen spec and full backlog
- Created BUILDLOG.md with genesis entry
- Created ARCHITECTURE.md stub with planned components
- Created README.md with thesis, contracts, setup instructions
- Created CI pipeline (GitHub Actions: ruff, mypy, pytest across Python 3.11/3.12/3.13)
- Core type definitions: 17 types (6 enums + 11 dataclasses) in src/context_ir/types.py
- 9 smoke tests, all passing
- Noted finding: SymbolKind missing FILE/MODULE container kinds (deferred to Slice 1)
- Acceptance status: first-pass

## 2026-04-13 -- Slice 1: Symbol Graph Parser

- Created tree-sitter-based parser (src/context_ir/parser.py)
- Added FILE and MODULE to SymbolKind enum (resolved container node question)
- Decision: container nodes as additional enum values, not a separate type. Keeps graph homogeneous -- all nodes are SymbolNode.
- Parser extracts FUNCTION, CLASS, METHOD, CONSTANT, IMPORT nodes with DEFINES, CALLS, IMPORTS edges
- Cross-file import resolution via best-effort Python path matching
- Node ID convention established: file:<path>, module:<path>, <path>::<name>
- Added tree-sitter and tree-sitter-python as runtime dependencies
- Test fixtures: 4-file sample Python package in tests/fixtures/sample_repo/
- 14 new parser tests (23 total), all passing
- Review finding: dead code (_extract_imported_names never called) removed in correction pass
- Accepted gap: REFERENCES edges not implemented (deferred to Slice 3 evaluation, Ryan sign-off given)
- Accepted gap: relative imports, aliased imports, multi-line imports have limited resolution (best-effort scope)
- Acceptance status: 1 correction

## 2026-04-13 -- Slice 2: View Renderers

- Created 5-tier view renderer (src/context_ir/renderer.py)
- OMIT: reference ID. SUMMARY: signature + docstring + structural counts. STUB: signature with ... body. SLICE: source + same-file imports, constants, called function stubs. FULL: exact source from disk.
- SLICE tier (key deliverable) uses graph edges (CALLS, DEFINES) and text-matching heuristic for import relevance
- Token estimation: max(1, len(text) // 4). Isolated in estimate_tokens() for later replacement.
- tree-sitter reused for robust signature extraction (multiline, decorated definitions)
- 18 new tests (41 total), all passing
- Execution chat reported mypy errors but verification showed clean pass in project venv (reporting discrepancy, not a code issue)
- Acceptance status: first-pass

## 2026-04-13 -- Slice 3: Scoring Engine

- Created scoring engine (src/context_ir/scorer.py) with score_graph() public API
- 9-step pipeline: query term extraction, symbol text profiles, lexical scoring, structural priors, semantic similarity, weighted combination, graph propagation, container node scoring, normalization
- Lexical features: name match (exact/substring), path match (with dotted-path normalization), content match (query terms in source)
- Structural priors: test file p_support boost + p_edit penalty, config file boost, entry point boost, kind-based base probabilities
- Semantic similarity: sentence-transformers (all-MiniLM-L6-v2), lazy loaded, injectable embed_fn for testing
- Graph propagation: 2 iterations, 0.3 decay. CALLS/IMPORTS -> p_support on target. DEFINES -> p_edit upward to parent.
- Container scoring: FILE/MODULE get max of children's scores
- Feature weights: lexical 40%/30%, structural 10%/20%, semantic 50%/50% (edit/support). Weights sum to 1.0.
- Design decision: REFERENCES edges evaluated and determined not needed. CALLS + IMPORTS + DEFINES provide sufficient propagation signal.
- sentence-transformers 5.x ships type stubs, so no type: ignore[import-untyped] needed
- 14 new tests (55 total), all passing. Real model integration test runs in ~3.6s.
- Acceptance status: first-pass

## 2026-04-13 -- Slice 4: Budget Optimizer

- Created budget optimizer (src/context_ir/optimizer.py) with optimize() public API
- Added OptimizationResult dataclass to types.py
- Greedy algorithm: marginal utility per token, sorted by efficiency, multi-pass to handle prerequisite ordering of upgrade steps
- Tier value tables: OMIT(0.0/0.1), SUMMARY(0.1/0.5), STUB(0.3/0.8), SLICE(0.9/0.25), FULL(1.0/0.3) for edit/support
- Dependency closure: one-hop CALLS edges, ensures targets at minimum STUB. Can exceed budget.
- Warning generation: HIGH_RISK_OMISSION (p_edit > 0.5, excluded), BUDGET_FORCED_DOWNGRADE (p_edit > 0.3, at STUB or below), UNRESOLVED_SYMBOL_FRONTIER (non-packable targets of edges from packed symbols)
- Trace: one CompileTraceEntry per packable symbol with downgrade reasons (DEPENDENCY_ONLY, LOW_RELEVANCE, BUDGET_PRESSURE)
- Confidence: achieved utility / max possible utility across all tiers (not always FULL, since STUB is optimal for support-heavy symbols)
- Packs FUNCTION, CLASS, METHOD, CONSTANT only. FILE, MODULE, IMPORT excluded from packing.
- Execution chat fixed: prerequisite ordering bug (multi-pass), confidence formula (actual max tier, not always FULL)
- 14 new tests + 1 smoke test (70 total), all passing
- Acceptance status: first-pass

## 2026-04-13 -- Slice 5: Compile Contract

- Created compiler module (src/context_ir/compiler.py) with compile() public API
- Orchestrates full pipeline: parse -> score -> optimize -> render -> assemble
- Document format: metadata header, file-grouped sections (alphabetical), symbols ordered by start_line, tier labels ([FULL], [SLICE], [STUB], [SUMMARY], [OMIT]), omitted section at end
- Optional pre-parsed graph parameter (skips re-parsing)
- Optional embed_fn pass-through to scorer
- First of three frozen-spec contracts (compile, diagnose, recompile)
- 12 new integration tests (82 total), all passing
- Execution chat reported mypy errors but verification showed clean pass in project venv (same pattern as Slice 2)
- Acceptance status: first-pass

## 2026-04-13 -- Retrospective Audit: Slice 1 Rejected

- Prior acceptance withdrawn after retrospective audit.
- Proven issue classes: parser-layer correctness gaps, contract/documentation overclaim, and insufficient acceptance evidence for the symbol/edge extraction baseline that later slices depended on.
- Downstream consequence: Slice 2 onward cannot remain accepted on top of this unresolved lower layer.
- Acceptance status: rejected

## 2026-04-13 -- Retrospective Audit: Slice 2 Rejected

- Prior acceptance withdrawn after retrospective audit.
- Proven issue classes: renderer tier-behavior and source-slice contract gaps, acceptance notes that outran verified repo reality, and dependency on a rejected parser baseline.
- Downstream consequence: Slice 3 onward cannot remain accepted on top of this unresolved layer.
- Acceptance status: rejected

## 2026-04-13 -- Retrospective Audit: Slice 3 Rejected

- Prior acceptance withdrawn after retrospective audit.
- Proven issue classes: scoring-behavior and feature-contract overclaim, insufficient acceptance basis for claimed propagation/feature behavior, and reliance on rejected lower layers.
- Downstream consequence: Slice 4 onward cannot remain accepted on top of this unresolved layer.
- Acceptance status: rejected

## 2026-04-13 -- Retrospective Audit: Slice 4 Rejected

- Prior acceptance withdrawn after retrospective audit.
- Proven issue classes: optimizer trace/warning/confidence contract gaps, architecture claims that outran verified behavior, and reliance on rejected upstream layers.
- Downstream consequence: Slice 5 onward cannot remain accepted on top of this unresolved layer.
- Acceptance status: rejected

## 2026-04-13 -- Retrospective Audit: Slice 5 Rejected

- Prior acceptance withdrawn after retrospective audit.
- Proven issue classes: compile-contract and output-guarantee overclaim, acceptance based on an invalid lower-layer foundation, and architecture/docs that presented the slice as settled when it is not.
- Downstream consequence: Slice 6 cannot advance as a clean top-layer continuation.
- Acceptance status: rejected

## 2026-04-13 -- Retrospective Audit: Slice 6 Held

- Prior forward-progress framing withdrawn after retrospective audit.
- Proven issue classes: public `recompile` contract remains unresolved, lower-layer corrections must land first, and architecture/docs had already overclaimed Slice 6 behavior as if accepted.
- Control decision at that time: hold Slice 6 until Slices 1-5 are corrected in order and the control lane makes an explicit public-contract decision.
- Historical note: this hold remains part of the evidence trail, but future execution now follows the semantic-first rebaseline recorded above rather than the retired correction chain.
- Acceptance status: held
