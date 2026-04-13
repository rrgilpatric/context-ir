# ARCHITECTURE.md -- Context IR

## Status

View renderers complete. Scoring engine next.

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

## Source Layout

```
src/context_ir/
    __init__.py       # Package init, re-exports parse_repository, parse_file, render
    types.py          # Core type definitions (dataclasses, enums)
    parser.py         # tree-sitter-based symbol graph parser
    renderer.py       # 5-tier view renderer
tests/
    test_smoke.py     # Smoke tests for type definitions
    test_parser.py    # Parser unit and integration tests
    test_renderer.py  # Renderer unit and integration tests
    fixtures/
        sample_repo/  # 4-file Python package for testing
```

## Key Design Decisions

1. **Container nodes as enum values (Slice 1).** FILE and MODULE are values in the SymbolKind enum, not a separate type. This keeps the graph homogeneous -- all nodes are SymbolNode, simplifying traversal and downstream processing. FILE nodes have start_line=1, end_line=last line. MODULE nodes have start_line=0, end_line=0.

2. **DEFINES for containment (Slice 1).** The DEFINES edge kind covers both "file defines function" and "class defines method." Combined with parent_id on SymbolNode for O(1) parent lookup. No separate CONTAINS edge needed.

3. **Best-effort cross-file resolution (Slice 1).** Import resolution matches Python dotted paths to graph nodes. Unresolvable imports (external, relative, aliased) are silently skipped rather than failing. Correctness can be improved incrementally.

4. **Same-file scope for SLICE tier (Slice 2).** The SLICE tier includes only same-file dependencies (imports, constants, called function stubs). Cross-file context is the budget optimizer's responsibility via dependency closure. This keeps individual SLICE views bounded and predictable in token cost.

5. **Token estimation as swappable heuristic (Slice 2).** estimate_tokens() uses len(text) // 4. Isolated in a single function so it can be replaced with tiktoken or a model-specific tokenizer when eval accuracy demands it.
