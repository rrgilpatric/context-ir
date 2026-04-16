# PLAN.md -- Context IR Build Plan

## Project

Context IR is a semantically grounded Python context compiler for coding agents. The system is being rebuilt to analyze a supported static subset of a repository, derive proved dependencies plus explicit uncertainty, and only then rank, optimize, and compile context under a budget.

## Current Authority

The April 13 frozen spec is retired and superseded. It remains part of the historical record in BUILDLOG.md, but it is no longer the governing contract for sequencing, acceptance, public positioning, or roadmap control.

### Semantic-First Baseline

- Public low-level API: `analyze_repository(repo_root) -> SemanticProgram`
- Mandatory build order: syntax extraction -> semantic contracts and types -> binder and scope model -> resolver and object model -> semantic dependency/frontier derivation -> renderer -> ranking -> optimization -> compilation -> diagnose/recompile
- `p_edit` and `p_support` remain allowed as internal ranking policy after semantic analysis, but they are not the public thesis
- Multi-tier representation remains in scope, but the exact tier count and semantics are not frozen during the rebaseline
- `@dataclass` is in the first supported decorator set, scoped narrowly and explicitly
- If the analyzer cannot prove a semantic fact within the supported subset, it must emit uncertainty or unknown state rather than fabricate a dependency claim

### Superseded Baseline

- The prior symbol-graph-first frozen spec is retired
- The prior Slice 1 -> Slice 6 correction chain is retired
- Historical retrospective findings still stand as evidence for why the reset was required
- The old `recompile` contract issue is subsumed by the rebaseline and must not be treated as the main control problem anymore

## Current Phase

Evidence-building phase after the accepted and released semantic-first baseline.

## What Is Complete

- [x] Slice 0: project bootstrap
- [x] Docs freeze / continuity reset: repo authority now points to the semantic-first baseline instead of the retired frozen spec
- [x] Retrospective findings preserved as historical evidence in BUILDLOG.md
- [x] Semantic contracts and types accepted after 1 correction
- [x] Syntax parser reset accepted after 1 correction
- [x] Syntax parse-failure correction accepted
- [x] Parameter-facts prerequisite correction accepted
- [x] Binder and scope model accepted first-pass
- [x] Resolver and object model accepted after 1 correction
- [x] Semantic dependency graph and frontier accepted first-pass
- [x] Renderer reset accepted first-pass
- [x] Scorer reset accepted first-pass
- [x] Optimizer / compile reset accepted after 1 correction
- [x] Diagnose / recompile reset accepted after 1 correction
- [x] Final-phase MCP / eval / portfolio-facing planning accepted first-pass
- [x] Semantic analyzer public contract accepted first-pass
- [x] Package-root public API and legacy quarantine accepted first-pass
- [x] Tool-facing facade contract accepted first-pass
- [x] Minimal MCP wrapper accepted first-pass after dependency/protocol authorization
- [x] Eval methodology and evidence baseline accepted first-pass
- [x] README / public-claim sync accepted first-pass
- [x] Release sequencing completed to `origin/main` at `9abc57c`
- [x] Deterministic fixture-level eval design accepted after 2 corrections
- [x] Eval oracle foundation accepted after 1 correction
- [x] Deterministic provider/baseline infrastructure accepted after 1 correction
- [x] Deterministic metric scoring core accepted first-pass

## What Is In Progress

- No implementation slice is currently in flight
- Control-lane continuity has been resynced through the accepted metric-scoring slice
- Core semantic-first rebuild is accepted through the planned architecture layers
- The public low-level semantic analysis API now exists
- The package root now points users at the semantic-first public surface
- A typed Python-facing facade now exists for repository compile requests
- A minimal stdio MCP wrapper now exists over the accepted facade
- `EVAL.md` now defines allowed claims, unsupported claims, and future eval gates
- README now matches the accepted semantic-first public surface and evidence boundaries
- Eval oracle assets now use stable selectors resolved through `analyze_repository(...)`, not generated unit IDs
- Deterministic Context IR and file-baseline providers now exist with structured trace metadata for later scoring
- Deterministic per-run scoring now exists over accepted oracle and provider outputs
- The next evidence-building implementation slice is not issued yet and requires explicit control-lane authorization

## Rebaseline Slice Order

1. Docs freeze / continuity reset -- complete in workspace
2. Semantic contracts and types -- accepted after 1 correction
3. Syntax parser reset -- accepted after 1 correction
4. Binder and scope model -- accepted first-pass
5. Resolver and object model -- accepted after 1 correction
6. Semantic dependency graph and frontier -- accepted first-pass
7. Renderer reset -- accepted first-pass
8. Scorer reset -- accepted first-pass
9. Optimizer and compile reset -- accepted after 1 correction
10. Diagnose / recompile reset -- accepted after 1 correction
11. Final-phase MCP / eval / portfolio-facing planning -- accepted first-pass
12. Semantic analyzer public contract -- accepted first-pass
13. Package-root public API and legacy quarantine -- accepted first-pass
14. Tool-facing facade contract -- accepted first-pass
15. MCP wrapper decision and implementation -- accepted first-pass after dependency/protocol authorization
16. Eval methodology and evidence baseline -- accepted first-pass
17. README / public-claim sync -- accepted first-pass
18. Release sequencing -- completed to `origin/main` at `9abc57c`
19. Deterministic fixture-level eval design -- accepted after 2 corrections
20. Eval oracle foundation -- accepted after 1 correction
21. Deterministic provider/baseline infrastructure -- accepted after 1 correction
22. Deterministic metric scoring core -- accepted first-pass

## What Is Next

1. Shape and issue the next eval implementation slice only after explicit authorization
2. The next likely slice should add deterministic per-run result artifacts on top of the accepted scoring contract, such as raw ledger rows or a minimal run-record contract, without public claims unless explicitly scoped
3. Keep Markdown reports and public-claim updates out of the next result-artifact slice unless separately authorized
4. Keep benchmark, performance, and portfolio claims paused unless backed by `EVAL.md`-compatible evidence
5. Do not reopen accepted semantic core contracts while shifting into evidence-building work

## What Is Deferred

- Multi-language analysis beyond Python
- Broader decorator and metaprogramming support beyond the initial explicit subset
- Production packaging and distribution polish
- Portfolio or benchmark claims beyond what the rebaseline can prove
- Markdown reports and public claim updates until deterministic result-ledger and summary-contract slices are accepted

## Historical Notes

- Any earlier Slice 1 or Slice 2 accepted corrections are historical improvements only. They may inform implementation details, but they do not govern the current roadmap.
- Existing workspace modules that reflect the retired baseline are implementation history, not current architectural authority.
- BUILDLOG retrospective findings remain operative evidence for why the reset occurred.

## What Should Not Be Reopened

- The April 13 frozen spec as if it were current authority
- The old Slice 1 -> Slice 6 correction chain
- The claim that exact 5-tier renderer semantics are already frozen
- The framing of `p_edit` / `p_support` as the public thesis instead of internal ranking policy
- The idea that the unresolved `recompile` contract is the primary control issue
- Any heuristic dependency claim that is not backed by the supported semantic layer
- Accepted semantic-contract, syntax, binder, resolver/object-model, dependency/frontier, renderer, scorer, optimizer/compile, and diagnose/recompile contracts unless a later findings-based review proves a concrete defect
