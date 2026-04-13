# ARCHITECTURE.md -- Context IR

## Status

Symbol graph parser complete. View renderers next.

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

## Source Layout

```
src/context_ir/
    __init__.py       # Package init, re-exports parse_repository/parse_file
    types.py          # Core type definitions (dataclasses, enums)
    parser.py         # tree-sitter-based symbol graph parser
tests/
    test_smoke.py     # Smoke tests for type definitions
    test_parser.py    # Parser unit and integration tests
    fixtures/
        sample_repo/  # 4-file Python package for parser testing
```

## Key Design Decisions

1. **Container nodes as enum values (Slice 1).** FILE and MODULE are values in the SymbolKind enum, not a separate type. This keeps the graph homogeneous -- all nodes are SymbolNode, simplifying traversal and downstream processing. FILE nodes have start_line=1, end_line=last line. MODULE nodes have start_line=0, end_line=0.

2. **DEFINES for containment (Slice 1).** The DEFINES edge kind covers both "file defines function" and "class defines method." Combined with parent_id on SymbolNode for O(1) parent lookup. No separate CONTAINS edge needed.

3. **Best-effort cross-file resolution (Slice 1).** Import resolution matches Python dotted paths to graph nodes. Unresolvable imports (external, relative, aliased) are silently skipped rather than failing. Correctness can be improved incrementally.
