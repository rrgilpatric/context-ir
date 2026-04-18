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
- [x] Deterministic raw result record core accepted after 1 correction
- [x] Deterministic multi-run ledger production accepted first-pass
- [x] Deterministic ledger summary rendering accepted after 1 correction
- [x] Deterministic internal eval report artifact accepted first-pass
- [x] Deterministic internal eval pipeline composition accepted after 1 correction
- [x] Deterministic internal eval run manifest accepted first-pass
- [x] Deterministic internal eval bundle directory accepted first-pass
- [x] Methodology-tightened signal smoke eval assets accepted first-pass
- [x] Signal smoke Context IR recovery accepted first-pass
- [x] Signal smoke competitive recovery accepted first-pass
- [x] Second methodology-tightened signal asset and two-asset matrix accepted first-pass
- [x] Two-asset signal evidence review accepted first-pass
- [x] Signal smoke B semantic recovery accepted first-pass
- [x] Third methodology-tightened signal asset and three-asset matrix accepted first-pass
- [x] Three-asset signal evidence review accepted first-pass
- [x] Signal smoke C edit-target recovery accepted first-pass
- [x] Post-recovery triple-matrix evidence review accepted first-pass
- [x] Smoke C 240 budget-envelope widened correction accepted first-pass
- [x] Post-correction triple-matrix evidence review accepted first-pass
- [x] Smoke B support-selection budget-pressure correction accepted with human sign-off
- [x] Post-support-correction triple-matrix evidence review accepted first-pass
- [x] Remaining helper-support budget-pressure correction accepted first-pass
- [x] Post-helper-correction triple-matrix evidence review accepted first-pass
- [x] Core uncertainty-surfacing correction accepted first-pass
- [x] Post-core-correction triple-matrix evidence review accepted first-pass
- [x] Noise-tightening correction accepted first-pass
- [x] Outward-facing artifact planning spike accepted first-pass
- [x] Portfolio technical brief accepted first-pass
- [x] Portfolio-readiness gap assessment spike accepted first-pass
- [x] Portfolio reviewer overview accepted first-pass
- [x] Post-overview portfolio-readiness planning spike accepted first-pass
- [x] Portfolio case-study source accepted first-pass
- [x] Post-case-study portfolio-readiness planning spike accepted after 1 control correction with human sign-off
- [x] Portfolio case study accepted first-pass
- [x] Post-polished-case-study portfolio-readiness planning spike accepted first-pass

## What Is In Progress

- No implementation slice is currently in flight
- Control-lane continuity has been resynced through the accepted post-polished-case-study portfolio-readiness planning review
- The broader four-asset evidence surface is now accepted:
  - `oracle_signal_smoke_d` broadens the surface in the intended method/class/dataclass direction
  - at `200`, `context_ir` now reaches support coverage `0.5` with uncertainty honesty `1.0` and warnings `[]`
  - at `240`, `context_ir` now reaches support coverage `1.0` with uncertainty honesty `1.0` and warnings `[]`
  - quad-matrix provider-average aggregate is now led by `context_ir` at `0.9599139230003012`
  - `context_ir` now leads all `8/8` task-budget rows on the accepted quad matrix
- `EVAL.md` and `README.md` now reflect the accepted deterministic eval harness and current four-asset evidence surface without overclaiming
- `PUBLIC_CLAIMS.md` now externalizes the allowed public-claim envelope, required qualifiers, disallowed phrasings, and evidence map for later portfolio-facing work
- `PORTFOLIO_SOURCE_BRIEF.md` now exists as the derivative portfolio-source scaffold:
  - `PUBLIC_CLAIMS.md` remains the sole claim source
  - outward-facing polished copy still remains out of scope until a later slice is explicitly authorized
- The first outward-facing repo-native artifact is now chosen:
  - `PORTFOLIO_TECHNICAL_BRIEF.md`
  - it remains bounded as a short technical brief derived from `PORTFOLIO_SOURCE_BRIEF.md`
  - it must remain conservative, evidence-linked, and pre-marketing
- `PORTFOLIO_TECHNICAL_BRIEF.md` now exists as the first outward-facing repo-native technical brief:
  - it remains derivative of `PUBLIC_CLAIMS.md` and `PORTFOLIO_SOURCE_BRIEF.md`
  - comparative language remains subordinate to the evidence snapshot
  - the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation remains explicit
- `PORTFOLIO_OVERVIEW.md` now exists as the short reviewer-orientation layer:
  - it remains short, derivative, conservative, and non-promotional
  - it helps a new reviewer understand the project, semantic-first direction, evidence boundary, limitation, and reading path in one pass
  - it remains derivative of `PUBLIC_CLAIMS.md`, `PORTFOLIO_SOURCE_BRIEF.md`, and `PORTFOLIO_TECHNICAL_BRIEF.md`
  - it explains the project, design direction, evidence boundary, current limitation, and reading path without adding claims
  - it does not become a second claim authority
  - it keeps the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation explicit
- `PORTFOLIO_CASE_STUDY_SOURCE.md` now exists as the representative-case source layer:
  - it remains derivative of `PUBLIC_CLAIMS.md` and the accepted outward-facing doc stack
  - it uses `oracle_signal_smoke_d` as an illustrative internal case without generalizing beyond the accepted quad matrix
  - it keeps the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation explicit
- `PORTFOLIO_CASE_STUDY.md` now exists as the polished reviewer-facing case-study layer:
  - it remains derivative of `PUBLIC_CLAIMS.md` and the accepted outward-facing doc stack
  - it uses `oracle_signal_smoke_d` as one illustrative internal case
  - it keeps the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation explicit
- The current outward-facing repo-native stack is now treated as sufficient for frontier-lab technical review:
  - no further repo-native portfolio artifact is currently required
  - no presentation-packaging source layer is authorized now
  - further portfolio-facing work is paused until a concrete downstream presentation channel or new evidence/claim authorization appears
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
- Deterministic per-run raw eval records and JSONL append support now exist over accepted oracle, provider, and metric outputs
- Deterministic multi-run ledger orchestration now exists over accepted run specs, oracle setup, providers, scoring, and raw-record writing
- Deterministic internal ledger loading, aggregate rollups, and Markdown summary rendering now exist over accepted raw JSONL ledgers
- Deterministic internal report artifacts and exact Markdown writing now exist over accepted ledgers and summaries
- Deterministic internal eval pipeline composition now exists over accepted run execution and report writing
- Deterministic internal eval run manifests now exist over accepted pipeline artifacts
- Deterministic internal eval bundle directories now exist over accepted pipeline and manifest artifacts
- A methodology-tightened signal smoke asset set now exists at `evals/fixtures/oracle_signal_smoke/`, `evals/tasks/oracle_signal_smoke.json`, and `evals/run_specs/oracle_signal_smoke_matrix.json`
- The stronger signal smoke now provides a non-trivial tight-budget tradeoff for whole-file baselines while keeping the accepted oracle, run-spec, and bundle plumbing intact
- A first semantic recovery pass now lifts `context_ir` on the stronger signal smoke:
  - non-zero edit coverage at budgets `200` and `240`
  - non-zero support coverage at budget `240`
  - no empty compiled semantic pack at budget `200`
- A competitive recovery pass now closes the remaining material gap on the stronger signal smoke:
  - at budget `200`, `context_ir` reaches support coverage `0.5` and leads on aggregate score
  - at budget `240`, `context_ir` reaches support coverage `1.0` and leads on aggregate score
  - uncertainty honesty remains `0.25` on the accepted smoke
- A second methodology-tightened signal asset now exists at `evals/fixtures/oracle_signal_smoke_b/` with:
  - `evals/tasks/oracle_signal_smoke_b.json`
  - `evals/run_specs/oracle_signal_smoke_b_matrix.json`
  - `evals/run_specs/oracle_signal_pair_matrix.json`
- The accepted pair matrix now provides a deterministic two-asset starting point for broader internal evidence review
- A semantic recovery pass now exists for `oracle_signal_smoke_b`:
  - at budget `200`, `context_ir` now reaches edit coverage `1.0`, representation adequacy `1.0`, and uncertainty honesty `1.0`
  - at budget `240`, `context_ir` now reaches edit coverage `1.0`, support coverage `0.333`, representation adequacy `1.0`, and uncertainty honesty `1.0`
- The accepted pair-matrix evidence now shows:
  - `context_ir` wins both `oracle_signal_smoke` rows
  - `context_ir` wins both `oracle_signal_smoke_b` rows
  - provider-average aggregate across the accepted pair matrix is now led by `context_ir` at `0.803` versus `0.666` and `0.665` for the file baselines
- A third methodology-tightened signal asset now exists at `evals/fixtures/oracle_signal_smoke_c/` with:
  - `evals/tasks/oracle_signal_smoke_c.json`
  - `evals/run_specs/oracle_signal_smoke_c_matrix.json`
  - `evals/run_specs/oracle_signal_triple_matrix.json`
- The accepted triple matrix now provides a deterministic three-asset starting point for broader internal evidence review
- The accepted triple-matrix evidence now shows:
  - before correction, `context_ir` won `5/6` task-budget rows but missed `oracle_signal_smoke_c` at budget `240`
- A semantic recovery pass now exists for `oracle_signal_smoke_c`:
  - at budget `240`, `context_ir` now reaches edit coverage `1.0`, support coverage `0.333`, representation adequacy `1.0`, and uncertainty honesty `1.0`
  - at budget `240`, `context_ir` now wins the `oracle_signal_smoke_c` row
  - the accepted triple matrix is now led by `context_ir` across all `6/6` task-budget rows
  - provider-average aggregate across the accepted triple matrix is now led by `context_ir` at `0.757` versus `0.627` and `0.626` for the file baselines
- The accepted post-recovery triple-matrix evidence review now shows:
  - `context_ir` still leads all `6/6` task-budget rows and provider-average aggregate at `0.757`
  - `oracle_signal_smoke_c` remains mixed after recovery:
    - at budget `200`, `context_ir` still misses `main.run_signal_smoke_c` and records edit coverage `0.0`
    - at budget `240`, `context_ir` recovers the edit target but remains support-light at `0.333` with two `budget_pressure` warnings
  - determinism still holds across independent corrected triple-matrix runs after caller-path normalization
- The accepted widened correction now resolves the held smoke_b and smoke_c evidence defects without changing eval semantics:
  - `oracle_signal_smoke_b` / `200` is restored to support coverage `0.0` and uncertainty honesty `1.0`
  - `oracle_signal_smoke_c` / `200` now selects `main.run_signal_smoke_c`, keeps support coverage `0.333`, and restores uncertainty honesty to `1.0`
  - `oracle_signal_smoke_c` / `240` now reaches support coverage `0.667`, restores uncertainty honesty to `1.0`, and remains budget-compliant at `237/240`
  - provider-average aggregate across the accepted triple matrix is now led by `context_ir` at `0.809` versus `0.627` and `0.626` for the file baselines
- The accepted post-correction triple-matrix evidence review now shows:
  - determinism still holds across independent post-correction triple-matrix runs after normalizing caller-chosen artifact paths
  - `context_ir` still leads all `6/6` task-budget rows and provider-average aggregate at `0.809`
  - the corrected three-asset surface is still mixed rather than uniformly strong
  - the weakest remaining area is `oracle_signal_smoke_b` support selection under budget pressure:
    - at budget `200`, `context_ir` still selects no repository-backed support units and remains at support coverage `0.0`
    - at budget `240`, `context_ir` reaches only support coverage `0.333`
  - `oracle_signal_smoke_c` is now materially improved but still has bounded support gaps:
    - at budget `200`, it still omits `pkg.registry.resolve_owner_alias` and `pkg.summary.render_route_summary`
    - at budget `240`, it still omits `pkg.registry.resolve_owner_alias`
  - Ryan approved one bounded correction slice focused on support selection under budget pressure
  - broader evidence expansion remains paused pending that correction and a fresh evidence review
- The accepted smoke_b support-selection correction materially improves the targeted smoke_b rows and preserves the required smoke_c floors:
  - `oracle_signal_smoke_b` / `200` now reaches support coverage `0.333` with uncertainty honesty `1.0`
  - `oracle_signal_smoke_b` / `240` now reaches support coverage `0.667` with uncertainty honesty `1.0`
  - `oracle_signal_smoke_c` / `200` now reaches support coverage `0.667` with uncertainty honesty `1.0`
  - `oracle_signal_smoke_c` / `240` remains at support coverage `0.667` with uncertainty honesty `1.0`
  - `oracle_signal_smoke` / `200` also moved from the previously accepted support coverage `0.5` to `1.0`
  - Ryan explicitly approved accepting that broader improvement as a one-off because control review found no concrete code-risk issue beyond scope reopening
- The accepted post-support triple-matrix evidence review now shows:
  - determinism still holds across independent post-support triple-matrix runs after normalizing caller-chosen artifact paths
  - `context_ir` still leads all `6/6` task-budget rows and provider-average aggregate at `0.882`
  - the current three-asset surface is stronger than materially weak but still mixed rather than uniformly strong
  - `oracle_signal_smoke` now looks strong on support at both budgets
  - the weakest remaining areas are helper-support gaps under budget pressure in the tighter assets:
    - `oracle_signal_smoke_b` still misses `pkg.collector.collect_signal_rows`
    - `oracle_signal_smoke_c` still misses `pkg.registry.resolve_owner_alias`
  - Ryan approved one more bounded correction slice focused on those remaining helper-support gaps
  - broader evidence expansion remains paused pending that correction and a fresh evidence review
- The accepted remaining helper-support correction now closes the last concrete repository-backed support misses on the current triple matrix:
  - `oracle_signal_smoke_b` / `200` now includes `pkg.collector.collect_signal_rows` and reaches support coverage `0.667` with uncertainty honesty `1.0`
  - `oracle_signal_smoke_b` / `240` now includes `pkg.collector.collect_signal_rows` and reaches support coverage `1.0` with uncertainty honesty `1.0`
  - `oracle_signal_smoke_c` / `200` now includes `pkg.registry.resolve_owner_alias` and reaches support coverage `1.0` with uncertainty honesty `1.0`
  - `oracle_signal_smoke_c` / `240` now includes `pkg.registry.resolve_owner_alias` and reaches support coverage `1.0` with uncertainty honesty `1.0`
  - the accepted original smoke surface remains intact at support coverage `1.0`, uncertainty honesty `0.625`, and no warnings
  - provider-average aggregate across the accepted triple matrix is now led by `context_ir` at `0.948` versus `0.627` and `0.626` for the file baselines
- The accepted post-helper triple-matrix evidence review now shows:
  - determinism still holds across independent post-helper triple-matrix runs after normalizing caller-chosen artifact paths
  - `context_ir` still leads all `6/6` task-budget rows and provider-average aggregate at `0.948`
  - the current three-asset surface is still mixed rather than uniformly strong
  - the accepted helper-support correction closed the previously concrete helper-support misses on the reviewed surface
  - the strongest remaining weakness is now persistent uncertainty surfacing on `signal_core_baselines`:
    - at both budgets, support coverage remains `1.0`
    - uncertainty honesty remains `0.625`
    - the omitted expected uncertainty remains `unsupported:import:main.py:2:0:1:*:_`
  - a secondary tighter-budget weakness remains on `signal_digest_baselines` / `200`:
    - support coverage remains `0.667`
    - `budget_pressure` still reports omitted support `pkg.digest.render_assignment_digest`
  - Ryan approved one more bounded correction slice focused on the persistent core uncertainty miss
  - broader evidence expansion remains paused pending that correction and a fresh evidence review
- The accepted core uncertainty-surfacing correction now resolves the persistent core miss on `signal_core_baselines` without reopening helper-support work:
  - at budgets `200` and `240`, `oracle_signal_smoke` now includes `unsupported:import:main.py:2:0:1:*:_`
  - at both budgets, `oracle_signal_smoke` now reaches support coverage `1.0`, uncertainty honesty `1.0`, and warning-free output
  - the accepted helper-support-complete smoke_b and smoke_c rows remain intact:
    - `oracle_signal_smoke_b` stays at support coverage `0.667` / `1.0` with uncertainty honesty `1.0`
    - `oracle_signal_smoke_c` stays at support coverage `1.0` / `1.0` with uncertainty honesty `1.0`
  - provider-average aggregate across the corrected triple matrix is now led by `context_ir` at `0.972` versus `0.627` and `0.626` for the file baselines
- The accepted post-core-correction triple-matrix evidence review now shows:
  - determinism still holds across independent post-core-correction triple-matrix runs after normalizing caller-chosen artifact paths
  - `context_ir` still leads all `6/6` task-budget rows and provider-average aggregate at `0.972`
  - the current three-asset surface is stronger but still not clean enough to treat as broader-evidence-ready
  - the accepted core uncertainty fix holds on `oracle_signal_smoke` at both budgets
  - the remaining weakness is now surplus non-required uncertainty and one residual tight-budget pressure row:
    - `oracle_signal_smoke` / `240` still carries extra uncertainty units `frontier:call:pkg/planner.py:2:20` and `unsupported:call:pkg/presenter.py:2:31`
    - `oracle_signal_smoke_b` / `200` still carries `budget_pressure`, omits `pkg.digest.render_assignment_digest`, and includes extra uncertainty `frontier:call:pkg/collector.py:2:20`
    - `oracle_signal_smoke_c` / `200` still carries extra uncertainty `frontier:call:main.py:6:20`
    - `oracle_signal_smoke_c` / `240` still carries extra uncertainty `frontier:call:main.py:6:20` and `frontier:call:pkg/registry.py:2:23`
  - Ryan approved one narrower noise-tightening follow-up
  - broader evidence expansion remains paused pending that correction and a fresh evidence review
- The accepted noise-tightening correction now removes the reviewed surplus uncertainty without reopening accepted evidence floors:
  - `oracle_signal_smoke` / `200` and `/240` now both keep the exact required 5-unit surface with warnings `[]`
  - `oracle_signal_smoke_b` / `200` keeps the accepted 4-unit floor, drops `frontier:call:pkg/collector.py:2:20`, and still honestly retains `budget_pressure`
  - `oracle_signal_smoke_b` / `240` keeps the clean 5-unit surface with warnings `[]`
  - `oracle_signal_smoke_c` / `200` and `/240` now both keep the exact required 5-unit surface with warnings `[]`
  - provider-average aggregate across the corrected triple matrix is now led by `context_ir` at `0.9786343641862341` versus `0.627` and `0.626` for the file baselines
- The held post-noise-tightening triple-matrix evidence review now shows:
  - determinism still holds across two fresh current-workspace bundle executions after normalizing only the caller-chosen `ledger_path` and `report_path`
  - raw `manifest.json` differences are limited to those caller-chosen artifact paths
  - `context_ir` still leads all `6/6` task-budget rows and provider-average aggregate at `0.9786343641862341`
  - five `context_ir` rows are now clean exact 5-unit surfaces with support coverage `1.0`, uncertainty honesty `1.0`, and warnings `[]`
  - the only residual blemish is `oracle_signal_smoke_b` / `200`, which keeps the accepted 4-unit floor, support coverage `0.667`, uncertainty honesty `1.0`, and honest `budget_pressure` for omitted support `def:pkg/digest.py:pkg.digest.render_assignment_digest`
  - lexical baseline ordering remains unchanged overall and on every task-budget row: `lexical_top_k_files` still narrowly leads `import_neighborhood_files`
- Ryan explicitly accepted the single bounded `oracle_signal_smoke_b` / `200` blemish as sufficient for broader evidence work under the current accepted contracts
- The held smoke_b `/200` feasibility review now shows the row is structurally impossible to clean through optimizer-only work under the current accepted contracts:
  - the exact oracle-clean 5-selector surface requires:
    - `def:main.py:main.run_signal_smoke_b` at `source`
    - `def:pkg/collector.py:pkg.collector.collect_signal_rows` at `source`
    - `def:pkg/labels.py:pkg.labels.build_priority_labels` at `summary`
    - `def:pkg/digest.py:pkg.digest.render_assignment_digest` at `source`
    - `frontier:call:main.py:10:4` at `identity`
  - that exact assembled document is `239` tokens under the accepted compile envelope
  - even a hypothetical zero-framing join of those rendered unit contents is still `221` tokens
  - therefore no narrower optimizer or selection-order follow-up can make the row clean without reopening accepted renderer, compiler-envelope, token-budget, or signal-asset contracts
- Broader evidence expansion is now authorized without reopening accepted contracts; public-claim and portfolio-claim work remain gated pending later evidence and claim-sync decisions

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
23. Deterministic raw result record core -- accepted after 1 correction
24. Deterministic multi-run ledger production -- accepted first-pass
25. Deterministic ledger summary rendering -- accepted after 1 correction
26. Deterministic internal eval report artifact -- accepted first-pass
27. Deterministic internal eval pipeline composition -- accepted after 1 correction
28. Deterministic internal eval run manifest -- accepted first-pass
29. Deterministic internal eval bundle directory -- accepted first-pass
30. Methodology-tightened signal smoke eval assets -- accepted first-pass
31. Signal smoke Context IR recovery -- accepted first-pass
32. Signal smoke competitive recovery -- accepted first-pass
33. Second methodology-tightened signal asset and two-asset matrix -- accepted first-pass
34. Two-asset signal evidence review -- accepted first-pass
35. Signal smoke B semantic recovery -- accepted first-pass
36. Third methodology-tightened signal asset and three-asset matrix -- accepted first-pass
37. Three-asset signal evidence review -- accepted first-pass
38. Signal smoke C edit-target recovery -- accepted first-pass
39. Post-recovery triple-matrix evidence review -- accepted first-pass
40. Smoke C 240 budget-envelope widened correction -- accepted first-pass
41. Post-correction triple-matrix evidence review -- accepted first-pass
42. Smoke B support-selection budget-pressure correction -- accepted with human sign-off
43. Post-support-correction triple-matrix evidence review -- accepted first-pass
44. Remaining helper-support budget-pressure correction -- accepted first-pass
45. Post-helper-correction triple-matrix evidence review -- accepted first-pass
46. Core uncertainty-surfacing correction -- accepted first-pass
47. Post-core-correction triple-matrix evidence review -- accepted first-pass
48. Noise-tightening correction -- accepted first-pass

## What Is Next

1. Hold portfolio-facing execution here: the current outward-facing repo-native stack is sufficient for now, and no further slice is authorized until a concrete downstream presentation channel or new evidence/claim authorization appears
2. Keep `PUBLIC_CLAIMS.md` as the sole claim source, and keep `PORTFOLIO_SOURCE_BRIEF.md`, `PORTFOLIO_TECHNICAL_BRIEF.md`, `PORTFOLIO_OVERVIEW.md`, `PORTFOLIO_CASE_STUDY_SOURCE.md`, and `PORTFOLIO_CASE_STUDY.md` as derivative artifacts only
3. Keep `evals/run_specs/oracle_signal_triple_matrix.json` as the accepted prior multi-asset regression/evidence anchor and `evals/run_specs/oracle_signal_quad_matrix.json` as the current broader-evidence surface
4. Preserve the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` blemish as an explicit documented tight-budget limit rather than a defect to silently optimize away
5. Keep public claims conservative and strictly backed by `EVAL.md`-compatible evidence
6. Keep benchmark, performance, and broader portfolio claims paused until a later control review explicitly authorizes any further outward-facing copy, presentation, or packaging slice
7. Do not reopen accepted metric semantics, renderer/compiler contracts, budgets, accepted signal assets, or the accepted public-claim envelope unless a later findings-based review proves a concrete defect

## What Is Deferred

- Multi-language analysis beyond Python
- Broader decorator and metaprogramming support beyond the initial explicit subset
- Production packaging and distribution polish
- Portfolio or benchmark claims beyond what the rebaseline can prove
- Public claim updates until evidence-generating and claim-gating slices are accepted

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
- Accepted raw-ledger, metric, and deterministic internal summary-rendering contracts unless a later findings-based review proves a concrete defect
- Accepted internal eval-report artifact and exact Markdown-write contracts unless a later findings-based review proves a concrete defect
- Accepted internal eval-pipeline composition and caller-path handling contracts unless a later findings-based review proves a concrete defect
- Accepted internal eval-run manifest and JSON-write contracts unless a later findings-based review proves a concrete defect
- Accepted internal eval bundle-directory filenames and path-alignment contracts unless a later findings-based review proves a concrete defect
- Accepted methodology-tightened signal smoke assets and their tight-budget baseline tradeoff unless a later findings-based review proves a concrete defect
- Accepted first recovery pass for `context_ir` on the signal smoke unless a later findings-based review proves a concrete defect
- Accepted competitive recovery for `context_ir` on the signal smoke unless a later findings-based review proves a concrete defect
- Accepted second methodology-tightened signal asset and pair-matrix orchestration unless a later findings-based review proves a concrete defect
- Accepted two-asset signal evidence review unless a later findings-based review proves a concrete defect
- Accepted semantic recovery for `context_ir` on `oracle_signal_smoke_b` unless a later findings-based review proves a concrete defect
- Accepted third methodology-tightened signal asset and triple-matrix orchestration unless a later findings-based review proves a concrete defect
- Accepted three-asset signal evidence review unless a later findings-based review proves a concrete defect
- Accepted `oracle_signal_smoke_c` edit-target recovery unless a later findings-based review proves a concrete defect
- Accepted post-recovery triple-matrix evidence review unless a later findings-based review proves a concrete defect
- Accepted smoke_c `240` budget-envelope widened correction unless a later findings-based review proves a concrete defect
- Accepted post-correction triple-matrix evidence review unless a later findings-based review proves a concrete defect
- Accepted smoke_b support-selection budget-pressure correction unless a later findings-based review proves a concrete defect
- Accepted post-support-correction triple-matrix evidence review unless a later findings-based review proves a concrete defect
- Accepted remaining helper-support budget-pressure correction unless a later findings-based review proves a concrete defect
- Accepted post-helper-correction triple-matrix evidence review unless a later findings-based review proves a concrete defect
