# Context IR

A budgeted context compiler for long-horizon coding agents.

## Thesis

Under a fixed repair harness, a traceable budgeted representation policy with miss detection and targeted recompile improves utility per token across budgets and exposes why failures happen.

## What It Does

Given a task description, a codebase, and a token budget, Context IR compiles the smallest working set that preserves the information needed for the next decision. It uses:

- **Symbol-level granularity** -- functions, classes, methods as atomic units
- **5-tier representation hierarchy** -- from omit to full source, with interface stubs and dependency-preserving slices in between
- **Dual scoring** -- separate p_edit (edit locus) and p_support (supporting context) scores
- **Budget optimization** -- greedy by marginal utility per token with dependency closure
- **Miss detection and recompilation** -- when the solver discovers gaps, diagnose and recompile with targeted corrections

## Core Contracts

```
compile(query, repo, budget) -> compiled document + trace + warnings + frontier + confidence
diagnose(miss_evidence) -> diagnostic result
recompile(previous_trace, new_evidence, delta_budget) -> updated compiled document
```

## Setup

Requires Python 3.11+.

```bash
# Clone the repo
git clone <repo-url>
cd context-ir

# Install in dev mode with dev dependencies
pip install -e ".[dev]"

# Run validation
ruff check src/ tests/
ruff format --check src/ tests/
mypy --strict src/
pytest tests/ -v
```

## Project Status

Bootstrap phase (Slice 0). Core type definitions are in place. See PLAN.md for the full build plan and backlog.

## Tech Stack

- Python 3.11+ with strict type hints
- ruff for linting and formatting
- mypy --strict for type checking
- pytest for tests
- dataclasses for all data structures
