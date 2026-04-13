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
