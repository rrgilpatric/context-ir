# PLAN.md -- Context IR Build Plan

## Project

Context IR is a semantically grounded Python context compiler for coding agents. The system is being rebuilt to analyze a supported static subset of a repository, derive proved dependencies plus explicit uncertainty, and only then rank, optimize, and compile context under a budget.

## Current Authority

The April 13 frozen spec is retired and superseded. It remains part of the historical record in BUILDLOG.md, but it is no longer the governing contract for sequencing, acceptance, public positioning, or roadmap control.

### Semantic-First Baseline

- This accepted milestone is the phase 0 foundation for the next program
- Public low-level API: `analyze_repository(repo_root) -> SemanticProgram`
- Mandatory build order: syntax extraction -> semantic contracts and types -> binder and scope model -> resolver and object model -> semantic dependency/frontier derivation -> renderer -> ranking -> optimization -> compilation -> diagnose/recompile
- `p_edit` and `p_support` remain allowed as internal ranking policy after semantic analysis, but they are not the public thesis
- Multi-tier representation remains in scope, but the exact tier count and semantics are not frozen during the rebaseline
- `@dataclass` is in the first supported decorator set, scoped narrowly and explicitly
- If the analyzer cannot prove a semantic fact within the supported subset, it must emit uncertainty or unknown state rather than fabricate a dependency claim

### Capability-Tier North Star

- The new post-milestone program targets broad Python repo coverage through hybrid static + runtime analysis
- The phase 0 foundation remains closed and authoritative for current claims, regression anchors, and reviewer-facing artifacts
- Each capability tier must stay separate from representation tiers:
  - capability tier describes how a fact or unit is justified
  - representation tiers describe how densely a selected unit is rendered
- The future program must keep statically proved, runtime-backed, heuristic/frontier, and unsupported/opaque surfaces explicitly separate
- External benchmark leadership remains contingent on reproducible public methodology and raw results
- Production maturity remains contingent on packaging, compatibility, interoperability, error handling, CI/release evidence, and observability

### Superseded Baseline

- The prior symbol-graph-first frozen spec is retired
- The prior Slice 1 -> Slice 6 correction chain is retired
- Historical retrospective findings still stand as evidence for why the reset was required
- The old `recompile` contract issue is subsumed by the rebaseline and must not be treated as the main control problem anymore

## Current Phase

Release authority is split deliberately. The latest pushed code/test release unit is now provider-scoped selected-unit capability-tier accounting at `215b6bb`. The prior capability-tier eval / evidence release unit remains `a605b22`; that release unit includes the tier-aware eval storage-contract slice, the isolated internal `DYNAMIC_IMPORT` eval pilot, the accepted post-pilot planning spike's authorized tier-aware internal-accounting rollout, and the accepted full-regression-gated code/test/pilot release unit. Continuity commits after `a605b22` and before `215b6bb` are docs-only and do not widen any implementation, exposure, schema, scoring, or public-claim boundary.

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
- [x] Capability-tier eval / evidence baseline milestone released to repo-backed authority at `a605b22`
- [x] Tier-aware eval storage-contract slice released at `a605b22`
- [x] Isolated internal `DYNAMIC_IMPORT` eval pilot released at `a605b22`
- [x] Post-pilot capability-tier eval internal-accounting planning spike accepted first-pass
- [x] Tier-aware eval summary/report internal-accounting rollout accepted after 1 correction
- [x] Full regression gate for the enlarged workspace-only eval/evidence unit accepted first-pass
- [x] Commit-gating review for the enlarged workspace-only eval/evidence unit accepted first-pass
- [x] Local commit creation for the coherent capability-tier eval/evidence release unit accepted first-pass at `a605b22`
- [x] Remote push for the coherent capability-tier eval/evidence release unit accepted first-pass at `a605b22`
- [x] Docs-only continuity sync and push authorization accepted after 1 correction
- [x] Docs-only continuity push completed through `d1265fe`
- [x] Post-release provider-scoped capability-tier accounting planning spike accepted first-pass
- [x] Provider-scoped selected-unit capability-tier accounting implementation accepted first-pass
- [x] Full regression gate for provider-scoped selected-unit capability-tier accounting accepted first-pass
- [x] Commit-gating review and local commit creation for provider-scoped selected-unit capability-tier accounting accepted first-pass at `215b6bb`
- [x] Remote push for provider-scoped selected-unit capability-tier accounting completed at `215b6bb`
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
- [x] North-star rebaseline planning spike accepted after 1 control correction with human sign-off
- [x] Capability-tier rebaseline control-state sync accepted first-pass
- [x] Phase-1 capability-tier contract/decomposition slice accepted first-pass
- [x] `SemanticProgram` provenance schema/types slice accepted first-pass
- [x] Runtime-backed evidence admissibility boundary slice accepted first-pass
- [x] Runtime-backed provenance metadata schema alignment slice accepted first-pass
- [x] Runtime-backed acquisition infrastructure slice accepted after 1 correction
- [x] Tier-aware ranking, optimization, and compile propagation slice accepted after 1 correction
- [x] Tier-aware diagnose/recompile and internal evidence gate slice accepted first-pass
- [x] Phase-2 hybrid-coverage priority and decomposition spike accepted after 1 control correction with human sign-off
- [x] Same-class `self.foo()` receiver call-resolution slice accepted first-pass
- [x] Object-model reflection-hook priority and decomposition spike accepted after 1 control correction with human sign-off
- [x] Same-class `__getattribute__` proof-guard slice accepted first-pass
- [x] Same-class hook-aware unsupported-boundary slice accepted first-pass
- [x] Import-rooted module hook-boundary slice accepted first-pass
- [x] Post-hook phase-2 priority and decomposition spike accepted after 1 control correction with human sign-off
- [x] Direct-base inherited `__getattribute__` proof-guard slice accepted first-pass
- [x] Direct-base inherited hook-aware unsupported-boundary slice accepted first-pass
- [x] Direct-base inherited `self.foo()` proof-widening slice accepted first-pass
- [x] Post-direct-base-inherited phase-2 priority and decomposition spike accepted first-pass
- [x] Same-class canonical-self attribute-read proof slice accepted after 1 correction
- [x] Post-same-class-attribute-proof inherited-hook priority and decomposition spike accepted first-pass
- [x] Ancestor-closure `__getattribute__` proof-contraction slice accepted first-pass
- [x] Ancestor-closure hook-aware unsupported-boundary slice accepted first-pass
- [x] Order-free transitive sole-provider inherited `self.foo()` proof-widening slice accepted after 1 correction
- [x] Post-order-free-transitive inherited-call priority and decomposition spike accepted first-pass
- [x] Linear single-chain nearest-provider inherited `self.foo()` proof-widening slice accepted first-pass
- [x] Ordering-aware contract prerequisite spike accepted first-pass
- [x] Ordered direct-base ancestry contract slice accepted first-pass
- [x] Declared-base-order / branch-precedence inherited `self.foo()` selection on linear branch subtrees accepted after 1 correction
- [x] Post-linear-branch-precedence inherited-call priority and decomposition spike accepted first-pass
- [x] Overlapping linear shared-ancestor sole-provider inherited `self.foo()` widening accepted first-pass
- [x] Post-shared-ancestor-overlap inherited-call priority and decomposition spike accepted first-pass
- [x] Later-owner precedence on individually linear overlapping/shared-ancestor inherited `self.foo()` branches accepted after 1 correction
- [x] Post-later-owner-overlap inherited-call priority and decomposition spike accepted first-pass
- [x] First exclusive-branch owner precedence on individually linear overlapping/shared-ancestor inherited `self.foo()` branches accepted first-pass
- [x] Post-first-exclusive-overlap inherited-call priority and decomposition spike accepted first-pass
- [x] First true runtime-backed phase-2 hybrid-coverage priority spike accepted first-pass
- [x] First runtime-backed hybrid implementation slice for existing unsupported `importlib.import_module`-family `DYNAMIC_IMPORT` findings accepted first-pass
- [x] Post-first-runtime-backed-implementation exposure-boundary spike accepted first-pass
- [x] Tool-facade pass-through for accepted `importlib_runtime_observations` seam accepted first-pass
- [x] Post-tool-facade hybrid-entry exposure-boundary spike accepted first-pass
- [x] Reflective-builtin runtime-backed subfamily ranking spike accepted first-pass
- [x] Bounded `hasattr(obj, name)` runtime-backed implementation slice accepted first-pass
- [x] `getattr(...)` runtime-backed form-splitting spike accepted first-pass
- [x] Bounded `getattr(obj, name)` runtime-backed implementation slice accepted first-pass
- [x] `getattr(obj, name, default)` runtime-backed branch-semantics spike accepted first-pass
- [x] Bounded `getattr(obj, name, default)` runtime-backed implementation slice accepted first-pass
- [x] Post-`getattr` runtime-backed next-move spike accepted first-pass
- [x] Bounded `vars(obj)` runtime-backed implementation slice accepted first-pass
- [x] Post-`vars(obj)` runtime-backed next-move spike accepted first-pass
- [x] Zero-argument `vars()` runtime-backed contract spike accepted first-pass
- [x] Bounded zero-argument `vars()` runtime-backed implementation slice accepted first-pass
- [x] Deep-QA / release-gate spike accepted first-pass
- [x] Runtime-backed tranche release-sequencing spike accepted first-pass
- [x] Release-scope broadening decision accepted with human sign-off after hunk-isolation blocker
- [x] Broadened release-gate spike accepted first-pass
- [x] Broadened staged commit-candidate review accepted first-pass
- [x] Broadened local commit creation accepted first-pass
- [x] Broadened release unit remote-state verification accepted first-pass
- [x] `dir(obj)` runtime-backed contract spike accepted first-pass
- [x] Bounded `dir(obj)` runtime-backed implementation slice accepted first-pass
- [x] Zero-argument `dir()` runtime-backed contract spike accepted first-pass
- [x] Bounded zero-argument `dir()` runtime-backed implementation slice accepted first-pass
- [x] Post-reflective `RUNTIME_MUTATION` planning spike accepted first-pass
- [x] Reflective-queue continuity reconciliation accepted first-pass
- [x] Bounded `globals()` runtime-backed implementation slice accepted first-pass
- [x] Bounded `locals()` runtime-backed implementation slice accepted first-pass
- [x] `delattr(obj, name)` vs `setattr(obj, name, value)` mutation-planning spike accepted first-pass
- [x] Bounded `delattr(obj, name)` runtime-backed implementation slice accepted first-pass
- [x] `setattr(obj, name, value)` assigned-value contract spike accepted first-pass
- [x] Bounded `setattr(obj, name, value)` runtime-backed implementation slice accepted first-pass
- [x] `METACLASS_BEHAVIOR` runtime-backed contract spike accepted first-pass
- [x] Bounded `METACLASS_BEHAVIOR` runtime-backed implementation slice accepted first-pass
- [x] Deep-audit correction slice for `PLAN.md` truthfulness and runtime-acquisition negative coverage accepted first-pass
- [x] Runtime-backed tranche release sequencing completed to `origin/main` at `cb1dc65`

## What Is In Progress

- No implementation slice is currently in flight
- No planning spike is currently in flight
- Repo-backed released state is now explicit and complete:
  - branch `main`
  - the accepted provider-scoped selected-unit capability-tier accounting release unit is `215b6bb`
  - the accepted capability-tier eval / evidence code/test/pilot release unit is `a605b22`
  - the docs-only continuity push completed through `d1265fe`
  - branch tips may move past `215b6bb` only through docs-only continuity commits unless a later code/test release is explicitly accepted
  - docs-only continuity commits after `a605b22` are not implementation release changes
  - the previously accepted runtime-backed tranche at `cb1dc65` remains historical released state and must not be routed as workspace-only work
- The current repo-backed released authority is capability-tier eval / evidence baseline:
  - accepted tier-aware eval storage-contract slice is released in:
    - `src/context_ir/eval_oracles.py`
    - `src/context_ir/eval_providers.py`
    - `src/context_ir/eval_results.py`
    - `tests/test_eval_oracles.py`
    - `tests/test_eval_providers.py`
    - `tests/test_eval_results.py`
    - `tests/test_eval_runs.py`
  - accepted isolated internal `DYNAMIC_IMPORT` eval pilot is released in:
    - `src/context_ir/eval_oracles.py`
    - `src/context_ir/eval_providers.py`
    - `evals/fixtures/oracle_signal_dynamic_import_probe/`
    - `evals/tasks/oracle_signal_dynamic_import_probe.json`
    - `evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json`
    - `tests/test_eval_oracles.py`
    - `tests/test_eval_providers.py`
    - `tests/test_eval_runs.py`
    - `tests/test_eval_signal_dynamic_import_probe.py`
  - accepted tier-aware internal-accounting rollout is released in:
    - `src/context_ir/eval_summary.py`
    - `tests/test_eval_summary.py`
    - `tests/test_eval_report.py`
    - `tests/test_eval_signal_dynamic_import_probe.py`
    - the internal summary/report path now consumes existing raw selector expectation and selected-unit capability-tier fields
    - separate internal accounting now exists for declared selector tier/provenance expectations and actual selected-unit tier/provenance
    - legacy scalar scoring, winner selection, schema version, public claims, and exposure boundaries remain unchanged
  - accepted full-regression gate confirmed the enlarged eval/evidence unit was locally clean before commit and push:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
  - accepted commit-gating review defined the exact coherent release unit now pushed at `a605b22`:
    - `src/context_ir/eval_oracles.py`
    - `src/context_ir/eval_providers.py`
    - `src/context_ir/eval_results.py`
    - `src/context_ir/eval_summary.py`
    - `tests/test_eval_oracles.py`
    - `tests/test_eval_providers.py`
    - `tests/test_eval_report.py`
    - `tests/test_eval_results.py`
    - `tests/test_eval_runs.py`
    - `tests/test_eval_summary.py`
    - `tests/test_eval_signal_dynamic_import_probe.py`
    - `evals/fixtures/oracle_signal_dynamic_import_probe/`
    - `evals/tasks/oracle_signal_dynamic_import_probe.json`
    - `evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json`
  - `PLAN.md` and `BUILDLOG.md` are separate docs-only continuity-sync files outside that pushed release unit
  - the docs-only continuity sync is limited to:
    - `PLAN.md`
    - `BUILDLOG.md`
- Release-boundary holds remain unchanged:
  - keep `context_ir.tool_facade` as the highest exposed hybrid entry point
  - do not widen package-root/public low-level runtime-observation exposure
  - do not widen MCP runtime-observation exposure
  - keep public claim boundaries unchanged from the accepted internal-eval state
- Further inherited-call reopening remains on explicit hold: no next implementation slice is authorized beyond the accepted first-exclusive-branch overlap reopening
- Push for `a605b22` is complete; the docs-only continuity push through `d1265fe` is complete
- The accepted post-release planning spike found no concrete defect requiring `a605b22` to be reopened
- Provider-scoped selected-unit capability-tier accounting is released in:
  - `src/context_ir/eval_summary.py`
  - `tests/test_eval_summary.py`
  - `tests/test_eval_report.py`
  - `tests/test_eval_signal_dynamic_import_probe.py`
- The accepted provider-scoped accounting slice:
  - adds provider selected-unit totals and attached-runtime-provenance totals
  - adds provider plus actual-primary-tier selected-unit totals and attached-runtime-provenance totals
  - preserves legacy scalar provider aggregates, task-budget rows, ledger-wide tier tables, schema version, scoring, winner selection, public claims, and exposure holds
- Full regression passed on the workspace containing the accepted provider-scoped accounting slice:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
  - pytest result: `539 passed, 1 deselected`
- Commit-gating review accepted the exact local code/test release unit now committed at `215b6bb`:
  - `src/context_ir/eval_summary.py`
  - `tests/test_eval_summary.py`
  - `tests/test_eval_report.py`
  - `tests/test_eval_signal_dynamic_import_probe.py`
- Remote push for `215b6bb` is complete

## What Is Next

1. Next substantive move after the authorized docs-only continuity push: hold for explicit authorization before any further push or new planning/implementation lane.
2. Treat pushed commit `215b6bb` as the current code/test release authority:
   - provider-scoped selected-unit capability-tier accounting
   - full regression gate over the provider-scoped accounting slice
   - commit-gating and remote push of the provider-scoped accounting release unit
3. Treat pushed commit `a605b22` as the prior capability-tier eval/evidence code/test/pilot release authority:
   - tier-aware eval storage-contract slice
   - isolated internal `DYNAMIC_IMPORT` eval pilot
   - accepted post-pilot planning spike that authorizes the tier-aware internal-accounting rollout boundary
   - accepted tier-aware eval summary/report internal-accounting rollout
   - accepted full-regression gate over the enlarged workspace-only unit
   - accepted commit-gating review over the enlarged workspace-only unit
   - local commit creation for the coherent code/test/pilot release unit
   - remote push of the coherent code/test/pilot release unit
   - docs-only continuity sync in `PLAN.md` and `BUILDLOG.md`
4. The next lane, if later authorized, must not reopen:
   - the accepted code/test/pilot release unit at `a605b22`
   - the accepted provider-scoped accounting release unit at `215b6bb`
   - public claim boundaries
   - package-root/public low-level runtime-observation exposure
   - MCP runtime-observation exposure
   - further inherited-call work
   - scoring, winner selection, raw schema, run specs, tasks, fixtures, providers, or runtime-acquisition breadth
5. Keep `215b6bb` as the latest repo-backed code/test release unit; docs-only continuity commits before or after it are continuity state, not implementation release changes.
6. Keep `context_ir.tool_facade` as the highest exposed hybrid entry point, keep package-root/public low-level plus MCP runtime-observation widening on explicit hold, and keep public claim boundaries unchanged.
7. Maintain the accepted hold on further inherited-call reopening beyond the accepted first-exclusive-branch overlap boundary.

## What Is Deferred

- Multi-language analysis beyond Python
- Broader decorator and metaprogramming support beyond the initial explicit subset
- Production packaging and distribution polish under the completed current milestone; broader production-grade delivery scope now awaits the new north-star rebaseline plan
- Portfolio or benchmark claims beyond what the rebaseline can prove
- Public claim updates until evidence-generating and claim-gating slices are accepted
- Any claim of benchmark leadership or production maturity until the corresponding post-milestone phases land with durable proof

## Historical Notes

- Any earlier Slice 1 or Slice 2 accepted corrections are historical improvements only. They may inform implementation details, but they do not govern the current roadmap.
- Existing workspace modules that reflect the retired baseline are implementation history, not current architectural authority.
- BUILDLOG retrospective findings remain operative evidence for why the reset occurred.

## What Should Not Be Reopened

- The accepted bounded runtime-backed tranche work for `DYNAMIC_IMPORT`, `REFLECTIVE_BUILTIN`, `RUNTIME_MUTATION`, and `METACLASS_BEHAVIOR` unless a later findings-based review proves a concrete defect
- The accepted tier-aware eval storage-contract slice unless a later findings-based review proves a concrete defect
- The accepted isolated internal `DYNAMIC_IMPORT` eval pilot unless a later findings-based review proves a concrete defect
- The accepted package-root/public low-level runtime-observation hold unless a later bounded planning spike explicitly authorizes widening
- The accepted MCP runtime-observation hold unless a later bounded planning spike explicitly authorizes widening
- The completed push decision for `cb1dc65`
- The completed phase 0 foundation as if it were incomplete or invalid
- The accepted quad matrix as anything other than the current top internal evidence surface
- The accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation as if it were undocumented or silently fixed
- The current README / `PUBLIC_CLAIMS.md` / portfolio stack unless later evidence gates explicitly justify changes
- The April 13 frozen spec as if it were current authority
- The old Slice 1 -> Slice 6 correction chain
- The claim that exact 5-tier renderer semantics are already frozen
- The framing of `p_edit` / `p_support` as the public thesis instead of internal ranking policy
- The idea that the unresolved `recompile` contract is the primary control issue
- Any heuristic dependency claim that is not backed by the supported semantic layer
- The accepted bounded builtin-specific `dir` seam, the accepted bounded builtin-specific `globals` seam, the accepted bounded builtin-specific `locals` seam, the accepted bounded builtin-specific `delattr` seam, the accepted bounded builtin-specific `setattr` seam, and the completed current reflective-builtin/runtime-mutation runtime-backed queues unless a later findings-based review proves a concrete defect
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
