# PLAN.md -- Context IR Build Plan

## Project

Context IR. A budgeted context compiler for long-horizon coding agents. Given a task description, a codebase, and a token budget, compile the smallest working set that preserves the information needed for the next decision, with adaptive representation density, miss detection, and targeted recompilation.

## Thesis

Under a fixed repair harness, a traceable budgeted representation policy with miss detection and targeted recompile improves utility per token across budgets and exposes why failures happen.

## Frozen Spec

### Core contracts
- compile(query, repo, budget) -> compiled document + compile trace + warnings + omitted frontier + confidence
- diagnose(miss_evidence) -> diagnostic result identifying what was missed and why
- recompile(previous_trace, new_evidence, delta_budget) -> updated compiled document with targeted corrections

### Atomic unit
Symbol-level nodes (function, class, method, constant, import block), plus lightweight file/module container nodes.

### Representation hierarchy (5 tiers)
1. Omit (reference ID only)
2. One-line structural summary
3. Interface stub (signature + type info)
4. Dependency-preserving source slice (body + imports, constants, referenced symbols)
5. Full source

### Scoring
Two separate scores per unit:
- p_edit(u): probability unit u is part of the edit locus
- p_support(u): probability unit u is supporting context for an edit elsewhere

### Features
Lexical hits from issue text (paths, identifiers, exception names, config keys). Semantic similarity between issue text and cached unit summaries/docstrings. Graph propagation over import/call/reference edges. Structural priors (tests, configs, interfaces, entry points, hot helpers). Diversity and anti-redundancy penalties.

### Optimizer
Greedy by marginal utility per token with dependency closure. Must account for downgrade reasons, marginal-utility deltas, and dependency constraints.

### Compiler outputs
Compiled document. Compile trace (candidate units, scores, chosen representation, marginal utility, token cost, downgrade reason per unit). Warnings (HIGH_RISK_OMISSION, BUDGET_FORCED_DOWNGRADE, LOW_CONFIDENCE_CLUSTER, UNRESOLVED_SYMBOL_FRONTIER). Omitted frontier. Confidence score.

### Runtime
One recompile path. Miss triggers: solver requests symbol absent from pack, stack trace points outside pack, proposed patch touches omitted file.

### Eval
- Primary: frozen-input regime (same solver, same harness, same budget, vary context provider)
- Baselines: top-k full-file retrieval, Aider-style graph-ranked repo map, Agentless-style hierarchical funnel
- Ablations: no source-slice tier, one-score instead of edit/support split, no graph propagation, no dependency closure, no recompile loop
- Benchmark: SWE-bench Verified Mini (50 tasks) as dev/ablation suite
- Primary metric: resolve rate as function of total budget (area under curve)

## Current Phase

Ready for Slice 3.

## What Is Complete

- [x] Slice 0: Project bootstrap (first-pass, accepted)
- [x] Slice 1: Symbol graph parser with tree-sitter (1 correction, accepted)
- [x] Slice 2: View renderers, all 5 tiers (first-pass, accepted)

## What Is In Progress

(Nothing currently in progress.)

## What Is Next (Backlog)

1. View renderers (all 5 tiers, with dependency-preserving source slice as key deliverable)
2. Scoring engine (p_edit, p_support, feature extraction, embeddings). Note: evaluate whether REFERENCES edges are needed for scoring quality. If so, add basic constant/variable reference extraction to the parser as part of this slice.
3. Budget optimizer (greedy with dependency closure, trace generation, warnings)
4. Compile contract (end-to-end compile with language-to-state intent parsing)
5. Diagnose + recompile contracts (miss detection, targeted recompilation)
6. MCP server (thin wrapper over three contracts)
7. Eval harness (SWE-bench Mini setup, baselines, metrics framework)
8. Eval runs + analysis (frozen-input comparison, ablations, budget curves)
9. Writeup + repo polish (README, results, public presentation)

## What Is Deferred

- Multi-language support beyond Python repos (start with Python-only targets)
- Multi-turn conversational refinement
- Production hardening / packaging for distribution
- SWE-bench Pro confirmatory slice (only if Mini results justify it)

## What Should Not Be Reopened

- The frozen spec above (locked after 3 rounds of research and adversarial review)
- Operating model (AGENTS.md, adapted from proven WoW)
- Container node decision: FILE and MODULE as SymbolKind enum values (not a separate type)
- Parser edge types: DEFINES, CALLS, IMPORTS cover Slice 1 scope. REFERENCES deferred to Slice 3 evaluation.
- Node ID convention: file:<path>, module:<path>, <path>::<name> pattern
- View tier API: render(node_id, tier, graph, repo_root) -> UnitView
- Token estimation: character-based approximation (1 token per ~4 chars), swappable later
- SLICE tier scope: same-file dependencies only. Cross-file context is the optimizer's job (dependency closure).
