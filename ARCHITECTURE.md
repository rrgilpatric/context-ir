# ARCHITECTURE.md -- Context IR

## Status

Stub. Will be filled as components are built.

## Planned Components

- **Symbol graph** -- tree-sitter parsing, node types, relationship edges
- **View renderers** -- 5-tier representation hierarchy
- **Scoring engine** -- p_edit, p_support, feature extraction
- **Budget optimizer** -- greedy with dependency closure
- **Compiler contracts** -- compile, diagnose, recompile
- **MCP server** -- tool definitions, protocol compliance
- **Eval harness** -- SWE-bench setup, baselines, metrics
- **Observability** -- compile traces, warnings, diagnostics

## Source Layout

```
src/context_ir/
    __init__.py
    types.py          # Core type definitions (dataclasses, enums)
    (future modules)
tests/
    test_smoke.py     # Smoke test for type definitions
    (future tests)
```

## Key Design Decisions

(To be recorded as they are made.)
