# ARCHITECTURE.md -- Context IR

## Status

Compile contract complete. Diagnose + recompile next.

## Components

### Symbol Graph Parser (src/context_ir/parser.py)

Builds a SymbolGraph from a Python codebase using tree-sitter.

- **parse_repository(root)** -- walks a directory, creates MODULE/FILE nodes, parses each .py file, merges results, resolves cross-file imports
- **parse_file(file_path, repo_root)** -- parses one .py file, extracts all symbol nodes and intra-file edges

**Node types extracted:** FILE, MODULE, FUNCTION, CLASS, METHOD, CONSTANT, IMPORT

**Edge types extracted:** DEFINES (containment), CALLS (function calls, intra-file), IMPORTS (cross-file, best-effort)

**Node ID convention:**
- FILE: file:<relative_path>
- MODULE: module:<relative_path>
- FUNCTION/CLASS/CONSTANT: <relative_path>::<name>
- METHOD: <relative_path>::<class>.<method>
- IMPORT: <relative_path>::import:<line>

**Cross-file resolution:** best-effort matching of Python dotted import paths to files and symbols in the graph. External imports (stdlib, third-party) produce IMPORT nodes but no IMPORTS edges.

**Known limitations:** CALLS edges cover simple identifier calls only (not attribute calls like obj.method()). Relative imports, aliased imports, and multi-line imports have limited resolution. REFERENCES edges not yet implemented.

### View Renderers (src/context_ir/renderer.py)

Renders any SymbolNode at a chosen ViewTier, returning a UnitView with content and estimated token cost.

- **render(node_id, tier, graph, repo_root)** -- single entry point, dispatches by tier
- **estimate_tokens(text)** -- character-based approximation (1 token per ~4 chars), swappable

**Tier behavior:**
- OMIT: `[ref: <node_id>]`
- SUMMARY: signature + docstring first line (callables), header + method count (classes), source line (constants/imports), symbol count (files)
- STUB: `signature: ...` (callables), class header + method stubs (classes), concatenated stubs (files)
- SLICE: symbol source + same-file imports, constants, and called function stubs. Uses CALLS edges for function stubs, word-boundary regex for import/constant relevance. Cross-file dependencies are NOT included (handled by optimizer dependency closure).
- FULL: exact source between start_line/end_line. Entire file for FILE nodes. __init__.py or file listing for MODULE nodes.

**Known limitations:** Import relevance uses text-matching heuristic (could false-positive on string literals). Token estimation is approximate. Multiline signatures collapsed to single line.

### Scoring Engine (src/context_ir/scorer.py)

Computes p_edit and p_support for every node in a SymbolGraph given a natural language query.

- **score_graph(query, graph, repo_root, embed_fn?)** -- single entry point, returns dict[str, EditSupportScores]
- **estimate_tokens(text)** lives in renderer.py (not scorer.py)

**9-step pipeline:**
1. Query term extraction (snake_case/CamelCase splitting, dedup)
2. Symbol text profiles for embedding (name + path + signature + docstring)
3. Lexical scoring (name/path/content match)
4. Structural priors (test files, configs, entry points, symbol kind)
5. Semantic similarity (sentence-transformers, cosine similarity)
6. Weighted combination (lexical 40/30%, structural 10/20%, semantic 50/50%)
7. Graph propagation (2 iterations, 0.3 decay over CALLS/IMPORTS/DEFINES)
8. Container node scoring (FILE/MODULE = max of children)
9. Normalize and clamp to [0.0, 1.0]

**Embedding:** sentence-transformers with all-MiniLM-L6-v2. Lazy loaded on first call. Injectable embed_fn parameter for testing and alternative backends.

**Feature weights:** Hardcoded at module level (W_LEX_EDIT, W_STRUCT_EDIT, W_SEM_EDIT, etc.). Tunable via eval in Slice 9.

### Budget Optimizer (src/context_ir/optimizer.py)

Decides which symbols to include and at what ViewTier given a token budget.

- **optimize(scores, graph, budget, repo_root)** -- single entry point, returns OptimizationResult

**Algorithm: greedy marginal utility per token**
1. Filter to packable nodes (FUNCTION, CLASS, METHOD, CONSTANT)
2. Pre-render all nodes at all tiers to get token costs
3. Build upgrade steps: each consecutive tier pair (excluded->OMIT, OMIT->SUMMARY, ..., SLICE->FULL) with marginal utility and token delta
4. Sort steps by efficiency (marginal_utility / token_delta), descending
5. Multi-pass greedy selection: apply eligible steps until budget exhausted. Multi-pass handles prerequisite ordering (a STUB->SLICE step may sort before the excluded->OMIT step it depends on).
6. Dependency closure: ensure CALLS targets of packed symbols are at minimum STUB
7. Generate trace, warnings, omitted frontier, confidence

**Tier value tables (edit_value / support_value):**
- OMIT: 0.0 / 0.1 -- SUMMARY: 0.1 / 0.5 -- STUB: 0.3 / 0.8 -- SLICE: 0.9 / 0.25 -- FULL: 1.0 / 0.3

Key insight: STUB is optimal for support-heavy symbols (highest support_value). SLICE/FULL are optimal for edit targets. The greedy algorithm naturally assigns the right tier based on p_edit/p_support balance.

**Packing exclusions:** FILE, MODULE, IMPORT nodes are not packed. Imports are included in SLICE-tier renders. File/module context is the compiler's responsibility.

### Compiler (src/context_ir/compiler.py)

End-to-end compile contract. First of the three frozen-spec contracts.

- **compile(query, repo_root, budget, embed_fn?, graph?)** -- orchestrates parse -> score -> optimize -> render -> assemble

**Pipeline:**
1. Parse repository (or use provided graph)
2. Score all nodes via score_graph
3. Optimize packing via optimize
4. Render each packed symbol at its assigned tier
5. Assemble rendered views into a formatted document
6. Return CompileResult

**Document format:**
- Header: query, budget usage, confidence, symbol counts
- Body: file-grouped sections (alphabetical), symbols ordered by start_line within each file
- Each symbol: `### <name> [<TIER>]` followed by rendered content
- Omitted section at end listing excluded symbol IDs

**Stateless:** Parses fresh on each call unless a pre-parsed graph is provided. No internal caching.

## Source Layout

```
src/context_ir/
    __init__.py       # Package init, re-exports public API
    types.py          # Core type definitions (dataclasses, enums)
    parser.py         # tree-sitter-based symbol graph parser
    renderer.py       # 5-tier view renderer
    scorer.py         # Scoring engine (p_edit, p_support)
    optimizer.py      # Budget optimizer (greedy, dependency closure)
    compiler.py       # Compile contract (end-to-end orchestration)
tests/
    test_smoke.py     # Smoke tests for type definitions
    test_parser.py    # Parser unit and integration tests
    test_renderer.py  # Renderer unit and integration tests
    test_scorer.py    # Scorer unit and integration tests
    test_optimizer.py # Optimizer unit and integration tests
    test_compiler.py  # Compiler integration tests
    fixtures/
        sample_repo/  # 4-file Python package for testing
```

## Key Design Decisions

1. **Container nodes as enum values (Slice 1).** FILE and MODULE are values in the SymbolKind enum, not a separate type. This keeps the graph homogeneous -- all nodes are SymbolNode, simplifying traversal and downstream processing. FILE nodes have start_line=1, end_line=last line. MODULE nodes have start_line=0, end_line=0.

2. **DEFINES for containment (Slice 1).** The DEFINES edge kind covers both "file defines function" and "class defines method." Combined with parent_id on SymbolNode for O(1) parent lookup. No separate CONTAINS edge needed.

3. **Best-effort cross-file resolution (Slice 1).** Import resolution matches Python dotted paths to graph nodes. Unresolvable imports (external, relative, aliased) are silently skipped rather than failing. Correctness can be improved incrementally.

4. **Same-file scope for SLICE tier (Slice 2).** The SLICE tier includes only same-file dependencies (imports, constants, called function stubs). Cross-file context is the budget optimizer's responsibility via dependency closure. This keeps individual SLICE views bounded and predictable in token cost.

5. **Token estimation as swappable heuristic (Slice 2).** estimate_tokens() uses len(text) // 4. Isolated in a single function so it can be replaced with tiktoken or a model-specific tokenizer when eval accuracy demands it.

6. **REFERENCES edges not needed for scoring (Slice 3).** Evaluated during Slice 3 planning. CALLS + IMPORTS + DEFINES edges provide sufficient signal for graph propagation. Constants mentioned by name in the query are caught by lexical matching. Revisit only if eval shows gaps.

7. **Injectable embedding function (Slice 3).** score_graph accepts an optional embed_fn parameter. Default uses sentence-transformers (lazy loaded). Tests inject a constant embedder returning identical vectors, which zeros out the semantic signal and isolates lexical/structural/propagation behavior. This pattern keeps the test suite fast (~0.04s without model loading) while still supporting real-model integration testing.

8. **Packable node kinds (Slice 4).** The optimizer only packs FUNCTION, CLASS, METHOD, CONSTANT. FILE, MODULE, and IMPORT nodes are structural and excluded from packing. Imports are already included in SLICE-tier renders. File/module context is added by the compiler.

9. **Multi-pass greedy selection (Slice 4).** A single-pass greedy can miss upgrade opportunities when a high-efficiency step (e.g., STUB->SLICE) is sorted before its prerequisite (excluded->OMIT). Multi-pass iterates until no new steps are applied. At most 5 passes (one per tier level). Terminates because each pass can only upgrade, never downgrade.

10. **Confidence uses actual max utility (Slice 4).** The confidence formula computes max utility per symbol across all tiers, not assuming FULL is always best. For support-heavy symbols, STUB (support_value=0.8) beats FULL (support_value=0.3). This prevents artificially deflated confidence scores.

11. **Compile function naming (Slice 5).** Named `compile` to match the frozen spec and CompileResult type. Shadows Python's built-in `compile`. Users can access the built-in via `builtins.compile` or import from the module directly: `from context_ir.compiler import compile`.

12. **Stateless compilation (Slice 5).** compile() has no internal state or caching. It parses the repo fresh on each call unless a pre-parsed graph is provided. This simplifies reasoning and testing. Persistent caching (e.g., graph reuse across MCP tool calls) is the server's responsibility, not the compiler's.
