# Context IR

Context IR is an in-progress semantic-first Python context compiler for coding
agents.

It currently analyzes a supported static Python subset into a
`SemanticProgram`, derives proven dependencies plus an explicit unresolved or
unsupported frontier, and uses that semantic substrate to rank, optimize, and
compile budgeted context. The repository also includes a minimal MCP stdio
wrapper around the compile facade.

Context IR does not currently make production-readiness, benchmark,
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
tests and quality gates, not by benchmark evidence.

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

`EVAL.md` defines what the repository currently proves and what remains future
work.

Current evidence is limited to:

- unit and integration tests in `tests/`
- local quality gates for lint, format, strict typing, and non-slow tests
- local MCP SDK registration and invocation for the minimal compile wrapper

The project currently makes no SWE-bench, benchmark improvement, resolve-rate,
production-readiness, performance, token-savings, cost-reduction, or
multi-language claims. Stronger public claims require the future eval gates and
raw evidence described in `EVAL.md`.

## Legacy API Note

Older graph-first modules remain directly importable by their explicit module
paths as implementation history and legacy compatibility. They are not the
current public package-root API. New usage should start from
`context_ir.analyze_repository(...)` and, for tool-facing compilation,
`context_ir.tool_facade.compile_repository_context(...)`.
