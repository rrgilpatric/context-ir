# BUILDLOG.md -- Decision Log

## 2026-04-13 -- Project Genesis: Context IR

- Concept developed through 3 rounds of research and adversarial review
- Round 1 (ChatGPT): Initial concept development. Identified reference-first context compilation as the thesis. Proposed six-component architecture.
- Round 2 (Claude control lane + execution spike): Competitive landscape validation. Mapped Aider, Codebase-Memory, SWE-agent, Moatless, Agentless. Confirmed gap: no existing tool does budget-aware format selection. Scoped to Option B (MCP server + SWE-bench Mini eval, 4-6 weeks).
- Round 3 (ChatGPT devil's advocate): Sharpened algorithm (symbol-level units, 5-tier hierarchy, dual scoring, dependency-preserving source slices), eval methodology (frozen-input regime, budget curves, ablations), systems engineering signal (recompile loop, compile traces, diagnostics). Confirmed competitive claims (RepoRepair March 2026, SWE-bench Pro preference, Verified submission restrictions).
- Frozen spec locked. Build order: compiler core first, MCP wrapper later.
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
