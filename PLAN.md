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

### Canonical Active Release-State Block

Current pushed release authority is the latest
`Sync task 1 ranking push routing` continuity commit. The latest pushed
source/contract authority is
`ba1b468 Tune semantic ranking for direct anchors`. Live git refs and worktree
state must still be verified from git during control intake; do not infer them
from committed prose.

Pushed corrected Task 1 ranking release:
`ba1b468 Tune semantic ranking for direct anchors`. This commit contains the
accepted, corrected-audit-cleared, full-regression-cleared,
commit-gating-cleared, locally committed, and pushed scorer/optimizer ranking
correction that made Task 1 select the required evidence path at budget `260`
without making eval evidence package-root public API. Ryan explicitly
authorized the push, and `git push origin main` advanced remote `main` from
`cb34fa9` through `efda06b Sync task 1 ranking local routing`; this continuity
entry records the post-push state. Do not route `56bc336`, `5b64cbf`,
`8662074`, `4f0ee80`, `92a285a`, `ba1b468`, or `efda06b` back to
release-unit audit, full regression, commit-gating, staging, local commit
creation, or push absent new findings.

Active next route:

- the Task 1 portfolio artifact-update slice is workspace-only accepted
- release-unit audit is cleared for the exact six-file artifact/control
  release unit
- full regression is cleared
- commit-gating is cleared
- stage exactly the six-file release unit and create the local release commit
- do not push without explicit Ryan authorization
- do not run Tasks 2-3 or update public/demo claims before local release state
  is clear

Pushed Task 0 product-differentiation evidence bundle release:
`9407d63 Add task 0 differentiation evidence bundle`. This commit contains
the accepted, audit-cleared, full-regression-cleared, commit-gating-cleared,
locally committed, and pushed internal evidence bundle for Task 0 of the
product-differentiation portfolio. It was pushed with explicit Ryan
authorization through `cb34fa9 Sync task 0 evidence bundle push routing`. Do
not route `9407d63`, `36227e9`, or `cb34fa9` back to release-unit audit, full
regression, commit-gating, staging, local commit creation, or push absent new
findings.

Historical Task 1 portfolio checkpoint returned FAIL and controlled the
correction route:

- Task 1 query:
  `Fix discover_semantic_eval_runtime_evidence so compact oracle_signal_hasattr_probe evidence renders additive runtime=additive attribute_present=true without becoming public API`
- budgets checked:
  - primary: `260`
  - ceiling: `360`
- providers checked:
  - `context_ir`
  - `lexical_top_k_files`
  - `import_neighborhood_files`
- returned result:
  - `context_ir` missed the primary Task 1 target at both budgets
  - at budget `260`, `context_ir` used `254` tokens in about `112.720s` and
    selected seven unrelated runtime-probe/test helper units
  - at budget `360`, `context_ir` used `360` tokens in about `120.061s` and
    still selected unrelated runtime-probe/dependency-frontier helper units
  - `context_ir` did not select `discover_semantic_eval_runtime_evidence`,
    compact `oracle_signal_hasattr_probe` evidence, internal semantic eval
    evidence contracts, the semantic rendering path for `runtime=additive`,
    package-root export-boundary evidence, or `attribute_present=true`
  - lexical and import baselines also selected zero files/units under both
    budgets, but `context_ir` failure means this cannot be STRONG or PARTIAL
- scratch artifacts reported by the checkpoint:
  - `/private/tmp/context_ir_portfolio_001_task1_primary260_runs.jsonl`
  - `/private/tmp/context_ir_portfolio_001_task1_primary260_summary.json`
  - `/private/tmp/context_ir_portfolio_001_task1_primary260_documents/`
  - `/private/tmp/context_ir_portfolio_001_task1_ceiling360_runs.jsonl`
  - `/private/tmp/context_ir_portfolio_001_task1_ceiling360_summary.json`
  - `/private/tmp/context_ir_portfolio_001_task1_ceiling360_documents/`
- control decision:
  - accept this as a failed checkpoint result, not as product-level evidence
  - hold Tasks 2-3 and any demo/report/public-claim advancement
  - do not update `evals/product_differentiation/portfolio_001/` artifacts
    until an explicit artifact-update slice is authorized
  - do not treat the Task 0 STRONG result as repeated product-level proof
- next route:
  - Ryan explicitly agreed that the Task 1 failure must be investigated before
    further north-star advancement
  - the read-only targeting diagnosis has now returned DONE
  - diagnosis result is accepted as the active route:
    - primary root cause is scorer/optimizer ranking failure
    - target evidence path exists, is discovered, renderable, and scored
    - optimizer selection is dominated by saturated `p_support` from
      runtime-probe/test helper dependency hubs
    - secondary issue is query/rubric ambiguity around `runtime`,
      `probe`, `oracle_signal_hasattr_probe`, `attribute_present`, and
      `public API` terms
    - not primarily renderer, compiler/evidence discovery, or budget pressure
      alone
  - expected path evidence from the diagnosis:
    - `discover_semantic_eval_runtime_evidence` exists in `eval_evidence.py`
    - compact eval evidence renders `primary=unsupported/opaque`,
      `runtime=additive`, and `payload=attribute_present=true`
    - `SemanticEvalRuntimeEvidence` exists as an internal semantic contract
    - package-root `context_ir.__all__` does not export those internal types
  - hold Tasks 2-3 and any demo/report/public-claim advancement
  - Ryan authorized one focused implementation correction:
    - make direct edit/contract anchors beat saturated helper support when the
      query names exact implementation or contract surfaces
    - keep the correction general to support-saturation behavior, not a
      one-off Task 1 overfit
    - likely scope: `semantic_scorer.py`, `semantic_optimizer.py`, focused
      scorer/optimizer tests, and a Task 1 regression check
    - do not update product-differentiation artifacts, public/demo claims,
      providers, runtime support, compiler contracts, package-root exports, or
      eval assets in this slice
  - if a focused correction cannot make Task 1 pass under the declared budgets,
    pause strategy rather than continuing the portfolio

Accepted Task 1 post-push product-differentiation checkpoint:

- checkpoint returned DONE and is accepted with no control findings
- repo truth:
  - branch `main`
  - `HEAD` and `origin/main` both resolved to
    `f99a12f Sync task 1 ranking push routing`
  - worktree, index, and untracked files were clean
  - `git diff --check`: clean
- Task 1 query:
  `Fix discover_semantic_eval_runtime_evidence so compact oracle_signal_hasattr_probe evidence renders additive runtime=additive attribute_present=true without becoming public API`
- budget:
  - primary `260`; ceiling `360` was not run because primary reached STRONG
- verdict:
  - STRONG
- `context_ir` result:
  - `247 / 260` tokens
  - about `118.783s`
  - selected five semantic units:
    - `def:src/context_ir/eval_evidence.py:src.context_ir.eval_evidence.discover_semantic_eval_runtime_evidence`
    - `def:src/context_ir/semantic_renderer.py:src.context_ir.semantic_renderer._render_eval_runtime_evidence`
    - `def:src/context_ir/semantic_types.py:src.context_ir.semantic_types.SemanticEvalRuntimeEvidence`
    - `def:src/context_ir/__init__.py:src.context_ir`
    - `eval_evidence:oracle_signal_hasattr_probe:hasattr:main.py:2:11`
  - rendered context includes
    `primary=unsupported/opaque; runtime=additive; payload=attribute_present=true`
  - package-root `context_ir` does not expose
    `discover_semantic_eval_runtime_evidence`
- baseline result:
  - `lexical_top_k_files`: selected zero files/units at budget `260`
  - `import_neighborhood_files`: selected zero files/units at budget `260`
    and emitted `import_not_resolved`
  - top omitted baseline candidates were whole test files ranging from
    thousands to more than thirteen thousand tokens, so they materially
    overincluded under the checkpoint budget
- scratch artifacts:
  - `/private/tmp/context_ir_portfolio_001_task1_postpush_primary260_runs.jsonl`
  - `/private/tmp/context_ir_portfolio_001_task1_postpush_primary260_summary.json`
  - `/private/tmp/context_ir_portfolio_001_task1_postpush_primary260_documents/`
- caveat:
  - `context_ir` remains much slower than baselines
  - several support units are summaries under budget pressure, though the
    discovery function is selected as source and all required waypoints are
    present
- release/artifact state:
  - checkpoint accepted in control state: yes
  - portfolio artifact updated: no
  - public/demo claims updated: no
- next route:
  - ask Ryan whether to authorize a separate artifact-update slice for
    `evals/product_differentiation/portfolio_001/`
  - do not run Tasks 2-3 or update public/demo claims before that artifact
    decision is made

Task 1 portfolio artifact update is workspace-only accepted:

- implementation lane returned DONE and was reviewed by control with no
  findings
- accepted release-unit files:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `evals/product_differentiation/portfolio_001/README.md`
  - `evals/product_differentiation/portfolio_001/manifest.json`
  - `evals/product_differentiation/portfolio_001/runs.jsonl`
  - `evals/product_differentiation/portfolio_001/evidence.md`
- accepted behavior:
  - preserves Task 0 evidence
  - adds the accepted STRONG Task 1 post-push checkpoint
  - records exactly three Task 1 provider rows at budget `260`
  - keeps Tasks 2-3 marked not run
  - keeps public claims held and frames the bundle as internal-only portfolio
    evidence, not broad product proof
- control validation:
  - live repo state verified as branch `main`, `HEAD` and `origin/main` both
    at `f99a12f`
  - dirty set exactly matched the six-file release unit
  - no staged files and no untracked files
  - `git diff --check`: clean
  - `manifest.json` parsed as JSON
  - every `runs.jsonl` line parsed as JSON
  - `runs.jsonl` contains six rows total: three Task 0 rows and exactly three
    Task 1 rows
  - Task 1 rows preserve provider names, budget `260`, token counts, selected
    unit IDs, baseline omissions, warnings, rendered additive evidence, and
    STRONG classification
  - recorded `runs.jsonl` checksum matches the current file
  - `README.md` and `evidence.md` preserve internal-only, public-claims-held,
    and Tasks 2-3 not-run statements
  - no diffs found in source, tests, public docs/claims, package exports, eval
    assets outside the portfolio bundle, or runtime/provider/compiler/scorer
    behavior
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: no
  - full regression cleared: no
  - commit-gating cleared: no
  - local commit not created
  - pushed: no
- next route:
  - run a read-only release-unit audit over the exact six-file release unit
  - do not stage, commit, push, run Tasks 2-3, or update public/demo claims
    before the normal gates clear

Task 1 portfolio artifact update release-unit audit is cleared:

- dedicated read-only release-unit audit returned PASS with no findings
- audit scope confirmed exactly the six-file release unit:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `evals/product_differentiation/portfolio_001/README.md`
  - `evals/product_differentiation/portfolio_001/manifest.json`
  - `evals/product_differentiation/portfolio_001/runs.jsonl`
  - `evals/product_differentiation/portfolio_001/evidence.md`
- audit confirmed no changes in source, tests, runtime/provider/compiler/
  scorer/optimizer code, public docs/claims, package exports, eval
  fixtures/tasks/run specs, or unrelated eval assets
- audit validation:
  - live repo state matched expected branch `main`, `HEAD=f99a12f`, and
    `origin/main=f99a12f`
  - no staged files and no untracked files
  - dirty set exactly matched the six-file release unit
  - `git diff --check`: clean
  - `manifest.json`: valid JSON
  - `runs.jsonl`: six valid JSON rows, exactly three Task 0 rows and three
    Task 1 rows
  - Task 1 preserved the accepted STRONG checkpoint: budget `260`,
    `context_ir` at `247` tokens, exact five required selected units,
    rendered `primary=unsupported/opaque; runtime=additive; payload=attribute_present=true`,
    zero selected files/units for both baselines, and `import_not_resolved`
    on the import baseline
  - `README.md` and `evidence.md` preserve internal-only/public-claims-held
    caveats and state Tasks 2-3 were not run
  - no broad product/public/demo claim was introduced
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full regression cleared: no
  - commit-gating cleared: no
  - local commit not created
  - pushed: no
- next route:
  - run full regression from the top
  - if full regression passes, proceed to commit-gating over the exact
    six-file release unit
  - do not stage, commit, push, run Tasks 2-3, or update public/demo claims
    before the normal gates clear

Task 1 portfolio artifact update full regression is cleared:

- full regression passed after release-unit audit clearance
- validation:
  - `.venv/bin/python -m ruff check src/ tests/`: passed
  - `.venv/bin/python -m ruff format --check src/ tests/`: passed,
    `114 files already formatted`
  - `.venv/bin/python -m mypy --strict src/`: passed, no issues in 39 source
    files
  - `.venv/bin/python -m pytest tests/ -v`: passed, `1723 passed` in about
    `141.11s`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full regression cleared: yes, first-pass after audit
  - commit-gating cleared: no
  - local commit not created
  - pushed: no
- next route:
  - run commit-gating over the exact six-file release unit
  - if commit-gating passes, stage exactly the six-file release unit and
    create the local release commit
  - do not push without explicit Ryan authorization
  - do not run Tasks 2-3 or update public/demo claims before local release
    state is clear

Task 1 portfolio artifact update commit-gating is cleared:

- commit-gating passed after audit and full regression clearance
- checks:
  - dirty set exactly matched the six-file release unit
  - no staged files before staging
  - no untracked files
  - `git diff --check`: clean
  - excluded source, tests, public docs/claims, package exports, eval
    fixtures/tasks/run specs, runtime/provider/compiler/scorer/optimizer
    code, and unrelated eval assets remained unchanged
  - structured artifact check confirmed `runs.jsonl` has exactly six rows,
    Task 0 and Task 1 provider/budget rows are present, Tasks 2-3 remain not
    run, and manifest artifact line count remains six
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full regression cleared: yes, first-pass after audit
  - commit-gating cleared: yes, first-pass after full regression
  - local commit not created
  - pushed: no
- next route:
  - stage exactly the six-file release unit and create the local release commit
  - do not push without explicit Ryan authorization
  - do not run Tasks 2-3 or update public/demo claims before local release
    state is clear

Task 1 ranking correction is workspace-only accepted:

- implementation lane returned DONE and was reviewed by control
- accepted release-unit files:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `src/context_ir/semantic_scorer.py`
  - `src/context_ir/semantic_optimizer.py`
  - `tests/test_semantic_scorer.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_semantic_compiler.py`
- accepted behavior:
  - direct implementation, contract, renderer-output, and package-root API
    boundary anchors now outrank saturated helper support
  - correction remains general to direct anchors versus support saturation and
    is not accepted as a hardcoded Task 1 special case
  - internal eval evidence remains internal and is not exported from
    package-root `context_ir`
  - compact eval evidence still preserves `primary=unsupported/opaque` and
    runtime evidence as additive
- control validation rerun:
  - focused `ruff check`: passed
  - focused `ruff format --check`: passed
  - `.venv/bin/python -m mypy --strict src/`: passed
  - focused pytest over scorer, optimizer, compiler: `55 passed` in about
    `116.12s`
  - exact Task 1 real-repo smoke at budget `260`: passed with `247 / 260`
    tokens
- exact Task 1 selected units after correction:
  - `def:src/context_ir/eval_evidence.py:src.context_ir.eval_evidence.discover_semantic_eval_runtime_evidence`
  - `def:src/context_ir/semantic_renderer.py:src.context_ir.semantic_renderer._render_eval_runtime_evidence`
  - `def:src/context_ir/semantic_types.py:src.context_ir.semantic_types.SemanticEvalRuntimeEvidence`
  - `def:src/context_ir/__init__.py:src.context_ir`
  - `eval_evidence:oracle_signal_hasattr_probe:hasattr:main.py:2:11`
- Task 1 smoke waypoint result:
  - `discover_semantic_eval_runtime_evidence`: pass
  - compact `oracle_signal_hasattr_probe` evidence: pass
  - `SemanticEvalRuntimeEvidence` contract surface: pass
  - semantic renderer `runtime=additive`: pass
  - package-root export-boundary evidence: pass
  - `attribute_present=true`: pass
  - package-root export remains absent: pass
- known release risk:
  - the new real-repo Task 1 regression adds about two minutes to the focused
    semantic test path; keep this visible during audit and full regression
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: no
  - full regression cleared: no
  - commit-gating cleared: no
  - local commit not created
  - pushed: no
- next route:
  - run a read-only release-unit audit over the seven-file release unit
  - do not run Tasks 2-3, update product-differentiation artifacts, stage,
    commit, push, or update public/demo claims until this correction release
    clears the normal gates

Task 1 ranking correction release-unit audit is cleared:

- dedicated read-only release-unit audit returned PASS with no findings
- audit scope confirmed exactly the seven-file release unit:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `src/context_ir/semantic_scorer.py`
  - `src/context_ir/semantic_optimizer.py`
  - `tests/test_semantic_scorer.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_semantic_compiler.py`
- audit confirmed no excluded-surface diffs in `README.md`, `EVAL.md`,
  `PUBLIC_CLAIMS.md`, `ARCHITECTURE.md`, eval assets, package-root exports,
  MCP/API/schema/config, providers, runtime support, or compiler source
  contracts
- audit reran or inspected:
  - `git diff --check`: clean
  - focused ruff check and format: passed
  - `.venv/bin/python -m mypy --strict src/`: passed
  - focused pytest: `55 passed` in about `126.50s`
  - exact Task 1 smoke: passed in about `2:07`, selected the five expected
    units, used `247 / 260` tokens, and rendered
    `primary=unsupported/opaque`, `runtime=additive`, and
    `attribute_present=true`
- audit accepted the two-minute real-repo regression cost as notable but not a
  finding because it directly guards the accepted failure mode
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full regression cleared: no
  - commit-gating cleared: no
  - local commit not created
  - pushed: no
- next route:
  - run full regression from the top
  - if full regression passes, proceed to commit-gating over the exact
    seven-file release unit
  - do not stage, commit, push, run Tasks 2-3, or update public/demo claims
    until the normal gates clear

Task 1 ranking correction full regression failed:

- full regression static gates passed:
  - `.venv/bin/python -m ruff check src/ tests/`: passed
  - `.venv/bin/python -m ruff format --check src/ tests/`: passed
  - `.venv/bin/python -m mypy --strict src/`: passed
- full pytest failed:
  - `.venv/bin/python -m pytest tests/ -v`: `3 failed, 1718 passed`
- failing tests:
  - `tests/test_eval_signal_smoke_d.py::test_signal_quad_bundle_preserves_provider_lead_and_smoke_b_budget_pressure`
  - `tests/test_eval_signal_vars_type_error_probe.py::test_vars_type_error_probe_run_preserves_additive_runtime_fields`
  - `tests/test_eval_signal_vars_type_error_probe.py::test_vars_type_error_probe_summary_keeps_runtime_additive`
- findings:
  - smoke_d budget `240` regressed by selecting
    `def:pkg/service.py:pkg.service.EnvelopeCompiler` instead of the expected
    support method `def:pkg/base.py:pkg.base.LayoutBase.format_digest`
  - vars type-error probe regressed by selecting
    `unsupported:call:main.py:2:11` as a selected unit and reordering
    selected symbols; prior contract expected only the two statically proved
    symbols `render_probe_digest` and `probe_namespace`
  - selected-unit tier accounting then exposed an `unsupported/opaque`
    selected-unit aggregate, violating the prior additive-runtime selected-unit
    boundary for that probe
- control decision:
  - release is held
  - release-unit audit clearance remains historical, but full-regression
    clearance is failed and must be rerun after correction
  - do not run commit-gating, stage, commit, push, run Tasks 2-3, or update
    product/public/demo artifacts
- recommended correction:
  - narrow the direct-anchor/support-saturation correction so Task 1 still
    selects its five required waypoints under budget `260`
  - preserve prior eval contracts that support methods outrank irrelevant
    class containers when support is required
  - preserve prior vars type-error behavior where runtime evidence remains
    selector-additive and unsupported units are not selected by the
    context-ir provider for that fixture
  - rerun the three failing tests, focused semantic tests, exact Task 1 smoke,
    and full regression from the top

Task 1 ranking correction full-regression correction is workspace-only accepted:

- correction lane returned DONE and was reviewed by control with no findings
- corrected behavior:
  - weak literal snake-case direct boosts are limited to more specific names
  - redundant enclosing class containers are suppressed after a method focus is
    already selected when the class lacks enough support
  - Task 1 budget-`260` success is preserved
  - smoke_d budget-`240` support selection is restored to
    `LayoutBase.format_digest`
  - vars type-error provider selection is restored to the two statically
    proved symbols, keeping runtime evidence selector-additive and preventing
    unsupported selected-unit tier accounting
- validation rerun:
  - focused `ruff check`: passed
  - focused `ruff format --check`: passed
  - `.venv/bin/python -m mypy --strict src/`: passed
  - targeted full-regression failures: `3 passed`
  - focused semantic scorer/optimizer/compiler suite: `57 passed` in about
    `131.41s`
  - exact Task 1 regression test: passed in about `129.75s`
  - `git diff --check`: clean before correction acceptance
- release state:
  - accepted in workspace: yes, after one full-regression correction
  - prior release-unit audit clearance predates the correction and must be
    rerun
  - full regression cleared: no, rerun required from the top after corrected
    audit
  - commit-gating cleared: no
  - local commit not created
  - pushed: no
- next route:
  - rerun a dedicated read-only release-unit audit over the corrected
    seven-file release unit
  - if corrected audit passes, rerun full regression from the top
  - do not run commit-gating, stage, commit, push, run Tasks 2-3, or update
    product/public/demo artifacts before corrected gates clear

Corrected Task 1 ranking release-unit audit is cleared:

- corrected dedicated read-only release-unit audit returned PASS with no
  findings
- audit confirmed corrected production changes remain general:
  - literal surface matching
  - output surface matching
  - contract-name matching
  - package-root boundary matching
  - direct-anchor ordering
  - redundant enclosing-class suppression
- audit found no Task 1 fixture/function hardcoding in production code
- audit scope confirmed exactly the seven-file release unit:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `src/context_ir/semantic_scorer.py`
  - `src/context_ir/semantic_optimizer.py`
  - `tests/test_semantic_scorer.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_semantic_compiler.py`
- package-root exports and public/API surfaces remain unchanged
- audit validation:
  - git state checks matched expected dirty set
  - `git diff --check`: clean
  - focused ruff check and format: passed
  - `.venv/bin/python -m mypy --strict src/`: passed
  - targeted prior failures: `3 passed`
  - focused scorer/optimizer/compiler tests: `57 passed` in about `125.44s`
  - exact Task 1 budget-`260` smoke: `247 / 260`, selected the five expected
    units, and rendered `primary=unsupported/opaque`, `runtime=additive`, and
    `payload=attribute_present=true`
  - additional inspection confirmed smoke_d budget `240` includes
    `LayoutBase.format_digest` with support coverage `1.0`
  - additional inspection confirmed vars type-error budgets `220` and `100`
    select only `render_probe_digest` and `probe_namespace`, do not select the
    unsupported unit, and keep unsupported selector runtime evidence additive
- risk:
  - the roughly two-minute Task 1 regression cost remains visible and accepted
    as non-blocking for this release because it guards the exact failure mode
- release state:
  - accepted in workspace: yes, after one full-regression correction
  - release-unit audit cleared: yes, corrected audit first-pass
  - full regression cleared: no
  - commit-gating cleared: no
  - local commit not created
  - pushed: no
- next route:
  - run full regression from the top
  - if full regression passes, proceed to commit-gating over the exact
    seven-file release unit
  - do not stage, commit, push, run Tasks 2-3, or update product/public/demo
    artifacts before gates clear

Corrected Task 1 ranking full regression is cleared:

- full regression passed after corrected release-unit audit clearance
- validation:
  - `.venv/bin/python -m ruff check src/ tests/`: passed
  - `.venv/bin/python -m ruff format --check src/ tests/`: passed,
    `114 files already formatted`
  - `.venv/bin/python -m mypy --strict src/`: passed, no issues in 39 source
    files
  - `.venv/bin/python -m pytest tests/ -v`: passed, `1723 passed` in about
    `137.54s`
- release state:
  - accepted in workspace: yes, after one full-regression correction
  - release-unit audit cleared: yes, corrected audit first-pass
  - full regression cleared: yes, first-pass after corrected audit
  - commit-gating cleared: no
  - local commit not created
  - pushed: no
- next route:
  - run commit-gating over the exact seven-file release unit
  - if commit-gating passes, stage exactly the seven-file release unit and
    create the local release commit
  - do not push without explicit Ryan authorization
  - do not run Tasks 2-3 or update product/public/demo artifacts before local
    release state is clear

Corrected Task 1 ranking commit-gating is cleared:

- commit-gating passed after corrected audit and full regression clearance
- checks:
  - dirty set exactly matched the seven-file release unit
  - no staged files before staging
  - no untracked files
  - `git diff --check`: clean
  - excluded public/API/runtime/provider surfaces remained unchanged
  - package-root `context_ir` does not export
    `discover_semantic_eval_runtime_evidence`
  - production scorer/optimizer code contains no Task 1 fixture/function
    hardcoding; only generic eval evidence field references were present
- release state:
  - accepted in workspace: yes, after one full-regression correction
  - release-unit audit cleared: yes, corrected audit first-pass
  - full regression cleared: yes, first-pass after corrected audit
  - commit-gating cleared: yes, first-pass after corrected full regression
  - local commit not created
  - pushed: no
- next route:
  - stage exactly the seven-file release unit and create the local release
    commit
  - do not push without explicit Ryan authorization
  - do not run Tasks 2-3 or update product/public/demo artifacts before local
    commit state is clear

Corrected Task 1 ranking local release commit is created:

- local release commit:
  `ba1b468 Tune semantic ranking for direct anchors`
- commit contents:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `src/context_ir/semantic_scorer.py`
  - `src/context_ir/semantic_optimizer.py`
  - `tests/test_semantic_scorer.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_semantic_compiler.py`
- pre-commit gates:
  - workspace acceptance: yes, after one full-regression correction
  - corrected release-unit audit: passed first-pass
  - corrected full regression: passed first-pass after corrected audit
  - commit-gating: passed first-pass after corrected full regression
- post-commit state verified by git:
  - local `HEAD` resolved to `ba1b468`
  - `origin/main` remained `cb34fa9`
  - branch `main` was ahead of `origin/main` by six local commits
  - worktree, index, and untracked files were clean
- release state:
  - accepted in workspace: yes
  - release-unit audit cleared: yes
  - full regression cleared: yes
  - commit-gating cleared: yes
  - locally committed: yes, `ba1b468`
  - pushed: no
- next route:
  - wait for explicit Ryan authorization before pushing local commits
  - do not run Tasks 2-3 or update product/public/demo artifacts until push
    state is clear

Pushed semantic eval-evidence integration release:
`fc2ddc6 Integrate compact eval evidence into semantic context`. This commit
contains the accepted, audit-cleared, full-regression-cleared,
commit-gating-cleared, locally committed, and pushed semantic integration of
compact eval runtime evidence into context compilation. It was pushed with
explicit Ryan authorization through
`0145ef6 Sync semantic eval evidence push routing`. Do not route `fc2ddc6`,
`b6be7e5`, or `0145ef6` back to release-unit audit, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Accepted post-push evidence-path baseline comparison checkpoint:

- read-only checkpoint returned DONE and is accepted as routing evidence
- verdict: STRONG differentiated signal
- repo truth reported by the checkpoint and verified by control:
  - branch `main`
  - local `HEAD` and `origin/main` both resolved to
    `0145ef6 Sync semantic eval evidence push routing`
  - worktree, index, and untracked files clean
  - `git diff --check` clean
- exact query:
  `Fix _selected_unit_metadata and eval report accounting so unsupported hasattr runtime provenance remains visible in selected unit metadata`
- primary budget: `220` tokens
- provider comparison:
  - `context_ir`: about `113.023s`, `219` tokens, 6 selected units, warnings
    `budget_pressure` and `omitted_uncertainty`
  - `lexical_top_k_files`: about `0.256s`, `74` tokens, selected zero files
    and zero units
  - `import_neighborhood_files`: about `0.260s`, `79` tokens, selected zero
    files and zero units with `import_not_resolved`
- required `context_ir` evidence path passed under budget:
  - selected `_selected_unit_metadata`
  - selected `EvalSelectedUnit`
  - selected eval-summary report accounting via
    `_build_runtime_provenance_record_lookup`
  - selected compact `oracle_signal_hasattr_probe` eval evidence
  - rendered `attribute_present=true`
  - preserved `unsupported/opaque` as primary truth and runtime evidence as
    additive
  - total tokens `219 / 220`
- selected `context_ir` units included:
  - `_selected_unit_metadata`
  - `EvalSelectedUnit`
  - `EvalProviderMetadata`
  - `EvalProviderResult`
  - `eval_summary._build_runtime_provenance_record_lookup`
  - `eval_evidence:oracle_signal_hasattr_probe:hasattr:main.py:2:11`
- baseline result:
  - both baselines failed the exact evidence path at budget `220`
  - lexical top candidates were whole test files such as
    `tests/test_eval_signal_hasattr_probe.py` at about `6903` estimated tokens
    and `tests/test_eval_signal_getattr_probe.py` at about `2656`, so reaching
    the evidence through those candidates would massively exceed the budget and
    overinclude irrelevant context
- control decision:
  - this is the first accepted STRONG, meaningful differentiation evidence for
    the north-star checkpoint
  - it proves the narrow product thesis for this checkpoint: materially better
    task context with truthful uncertainty under budget where baselines fail or
    overinclude
  - it does not prove the full product is complete, public-claim-ready, or
    latency-solved
  - caveat remains: `context_ir` used summaries under budget pressure, and the
    compact eval evidence unit is an internal evidence surface rather than a
    selected unsupported runtime-attached source unit
- next route:
  - demo/report/public-claim work is no longer blocked by lack of meaningful
    differentiation proof
  - next authorized planning move should define the smallest tangible internal
    artifact that presents this STRONG checkpoint honestly, with caveats and no
    public-claim widening
  - do not broaden claims beyond this checkpoint without additional evidence

Accepted product-level differentiation proof plan:

- Ryan agreed to the control plan to move from one STRONG checkpoint toward
  product-level differentiation evidence
- product-level differentiation is not established by one checkpoint alone
- defensible product-level evidence requires:
  - an internal artifact that preserves exact commands, artifacts, selected
    context, baseline outputs, timing, budget, and caveats for the accepted
    STRONG checkpoint
  - a small portfolio of additional real repo tasks, predeclared before
    running, that represent more than one utility mode
  - the same meaningful-differentiation standard applied consistently:
    materially better task context with truthful uncertainty under budget
    where baselines fail or overinclude
  - clear failure criteria that stop or trigger a research pause if the
    advantage does not repeat
- current product-level claim boundary:
  - it is now fair internally to say `context_ir` has one strong real-repo
    differentiation checkpoint
  - it is not yet fair to claim general superiority over modern coding
    harnesses, IDE repo assistants, or public benchmark baselines
  - public claims remain held until repeated evidence and a reviewable artifact
    are accepted
- next route:
  - Ryan approval is required before creating the internal evidence bundle or
    running the additional portfolio tasks
  - if Ryan approves, create the internal evidence bundle preserving Task 0
    first, then run the additional proof tasks sequentially with
    stop-on-first-finding review
  - no implementation, docs/public-claim updates, demo polishing, MCP/API
    changes, or benchmark claims are authorized by this planning route

Accepted product-differentiation proof-plan lane result:

- read-only proof-plan lane returned DONE and is accepted with no findings
- recommended internal evidence bundle shape:
  - `evals/product_differentiation/portfolio_001/README.md`
  - `evals/product_differentiation/portfolio_001/manifest.json`
  - `evals/product_differentiation/portfolio_001/runs.jsonl`
  - `evals/product_differentiation/portfolio_001/evidence.md`
- artifact boundary:
  - internal evidence bundle, not a public report
  - first entry should preserve the accepted STRONG Task 0 checkpoint exactly,
    including budget, query, selected units, baseline failures/overinclude
    analysis, warnings, timing, and caveats
- accepted task portfolio:
  - Task 0, accepted checkpoint:
    `_selected_unit_metadata` / `hasattr` runtime-provenance evidence path,
    budget `220`
  - Task 1, compact eval evidence discovery/rendering:
    `Fix discover_semantic_eval_runtime_evidence so compact oracle_signal_hasattr_probe evidence renders additive runtime=additive attribute_present=true without becoming public API`
    with primary budget `260` and ceiling `360`
  - Task 2, runtime probe recompile path:
    `Fix default local Python subprocess recompile so exec(source) runtime probe results attach additive provenance to unsupported EXEC_OR_EVAL units without promoting primary truth`
    with primary budget `320` and ceiling `480`
  - Task 3, static semantic dependency/frontier path:
    `Fix transitive sole-provider self-call resolution for MemberSignalCompiler.compile_member_digest while preserving alias_chain frontier on pkg_alias.labels.build_member_label`
    with primary budget `280` and ceiling `400`
  - optional Task 4 only if evidence is too concentrated: eval artifact
    reproducibility around `eval_bundle`, `eval_pipeline`, `eval_manifest`,
    and `eval_report`
- accepted rubric:
  - compare `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - STRONG means `context_ir` stays within primary budget, selects every
    predeclared evidence waypoint at useful detail, preserves
    uncertainty/runtime truth honestly, and baselines fail under the same
    budget or require materially larger/irrelevant whole-file context
  - PARTIAL means `context_ir` finds the main edit target and most support but
    needs ceiling budget or omits noncritical support with honest
    `budget_pressure`
  - FAIL means it misses the primary target, loses required
    runtime/uncertainty truth, exceeds budget, or baselines provide comparable
    context under the same budget
- accepted stop conditions:
  - move to internal demo/report only if at least 3 of 4 total tasks are STRONG
    across at least three utility modes, and the remaining task is no worse
    than PARTIAL with a bounded caveat
  - trigger research pause if fewer than 3 STRONG results appear, any task
    exposes incorrect primary truth, baselines match or beat `context_ir` on
    two tasks, wins depend only on exact-name coincidence, or evidence cannot
    be reproduced from captured commands/artifacts
- control verification:
  - live state during review remained branch `main`
  - local `HEAD` was `e014400`; `origin/main` was `0145ef6`
  - worktree, index, and untracked files were clean before this continuity
    update
  - searched repo surfaces for all proposed task anchors; Task 1, Task 2, and
    Task 3 anchors exist in current repo/eval assets
- next route:
  - Ryan approved this artifact shape and portfolio
  - next authorized execution slice is to create the internal evidence bundle
    and preserve Task 0 only
  - do not run Tasks 1-3, update public/demo claims, or broaden MCP/API/schema
    behavior in the Task 0 artifact slice

Ryan-approved Task 0 evidence bundle slice:

- Ryan explicitly approved the accepted artifact shape and portfolio
- next execution slice:
  - create `evals/product_differentiation/portfolio_001/`
  - add the internal bundle files:
    - `README.md`
    - `manifest.json`
    - `runs.jsonl`
    - `evidence.md`
  - preserve/reproduce Task 0 only:
    `_selected_unit_metadata` / `hasattr` runtime-provenance evidence path,
    budget `220`
  - compare `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - capture exact commands, repo state, provider outputs or stable artifact
    references, selected units/files, warnings, omitted candidates, timing,
    budgets, caveats, and pass/fail classification
- Task 0 expected result remains STRONG only if:
  - `context_ir` selects `_selected_unit_metadata`
  - `context_ir` selects `EvalSelectedUnit`
  - `context_ir` selects eval-summary report accounting
  - `context_ir` selects compact `oracle_signal_hasattr_probe` eval evidence
  - rendered context includes `attribute_present=true`
  - unsupported/opaque remains primary truth and runtime evidence remains
    additive
  - total tokens stay within `220`
  - baselines fail under the same budget or require materially larger and
    irrelevant whole-file context
- non-goals:
  - do not run or record Tasks 1-3 in this slice
  - do not make public claims
  - do not update README, EVAL, PUBLIC_CLAIMS, ARCHITECTURE, MCP/API/schema,
    runtime/provider behavior, scoring, optimizer, compiler, or package exports
  - do not create a polished demo
- after the Task 0 artifact slice returns:
  - review the bundle under the quality gate
  - only after acceptance decide whether to run Task 1 as the next sequential
    portfolio slice

Pushed Task 0 evidence bundle release unit:

- release unit files:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `evals/product_differentiation/portfolio_001/README.md`
  - `evals/product_differentiation/portfolio_001/manifest.json`
  - `evals/product_differentiation/portfolio_001/runs.jsonl`
  - `evals/product_differentiation/portfolio_001/evidence.md`
- accepted behavior:
  - created the internal-only product-differentiation evidence bundle for
    Task 0
  - reproduced only Task 0 at budget `220`
  - recorded `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files` provider outputs
  - classified Task 0 as STRONG
  - preserved selected `context_ir` evidence path:
    `_selected_unit_metadata`, `EvalSelectedUnit`, eval-summary report
    accounting, compact `oracle_signal_hasattr_probe` evidence, and
    `attribute_present=true`
  - preserved the main truth boundary: `unsupported/opaque` remains primary
    and runtime evidence remains additive
  - recorded baseline failure/overinclude evidence under budget `220`
  - kept public claims held and stated caveats, including latency,
    summary-level selected repo units, and compact eval evidence being an
    internal evidence surface
- artifact review evidence:
  - live state during review: branch `main`, local `HEAD` `64203e5`,
    `origin/main` `0145ef6`
  - only the four bundle files were untracked before this continuity update
  - no staged files
  - no tracked implementation/source/test/docs changes outside
    `PLAN.md` and `BUILDLOG.md`
  - `manifest.json` is valid JSON
  - `runs.jsonl` contains exactly three valid JSON rows, one per provider
  - structured consistency check passed:
    - manifest classification is `STRONG`
    - manifest task budget is `220`
    - all run rows use the same query and budget
    - provider order is `context_ir`, `lexical_top_k_files`,
      `import_neighborhood_files`
    - required `context_ir` selected units are present
    - `context_ir` tokens are `219 / 220`
    - rendered context includes `attribute_present=true`,
      `primary=unsupported/opaque`, and `runtime=additive`
    - baseline rows selected zero files and zero units
  - artifact whitespace/final-newline check passed for all four bundle files
  - `README.md` and `evidence.md` mention internal-only scope, public claims
    held, classification, Tasks 1-3 not run, and caveats
  - `git diff --check` remained clean for tracked diffs
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass with `1714 passed`
  - commit-gating cleared: yes, first-pass
  - locally committed: yes, `9407d63 Add task 0 differentiation evidence bundle`
  - local release routing committed: yes,
    `36227e9 Sync task 0 evidence bundle local routing`
  - pushed: yes, with explicit Ryan authorization
- push evidence:
  - before push, branch `main` was ahead of `origin/main` by six local commits
  - Ryan explicitly authorized push
  - `git push origin main` succeeded, advancing remote `main` from `0145ef6`
    to `36227e9`
  - after push, local `HEAD` and `origin/main` both resolved to `36227e9`
  - worktree, index, and untracked files were clean
- local commit evidence:
  - staged exactly the six-file evidence bundle release unit
  - verified staged file set, no unstaged files, no untracked files, and
    `git diff --cached --check` before commit
  - created local artifact release commit
    `9407d63 Add task 0 differentiation evidence bundle`
  - after commit, local `HEAD` resolved to `9407d63`, `origin/main` remained
    `0145ef6`, and the branch was ahead by five local commits
- commit-gating evidence:
  - live state during commit-gating remained branch `main`, local `HEAD`
    `64203e5`, and `origin/main` `0145ef6`
  - exact release unit remained `PLAN.md`, `BUILDLOG.md`, and the four Task 0
    bundle artifact files
  - no staged files before staging
  - no excluded surfaces changed: `README.md`, `EVAL.md`, `PUBLIC_CLAIMS.md`,
    `ARCHITECTURE.md`, `src`, `tests`, and `pyproject.toml` had no diff
  - `git diff --check` was clean
  - structured artifact consistency check passed for classification, query,
    budget, provider order, selected units, token budget, rendered payload,
    truth boundary, and baseline zero-selection results
- full-regression evidence:
  - after release-unit audit clearance, full regression passed:
    - `ruff check src/ tests/`
    - `ruff format --check src/ tests/`
    - `mypy --strict src/`
    - `pytest tests/ -v` with `1714 passed`
- audit evidence:
  - read-only release-unit audit returned PASS with no findings
  - live state matched expected:
    - branch `main`
    - local `HEAD` `64203e5`
    - `origin/main` `0145ef6`
    - branch ahead by four local continuity commits
    - no staged files
    - dirty/untracked files exactly matched the six-file release unit
  - no diffs found in `README.md`, `EVAL.md`, `PUBLIC_CLAIMS.md`,
    `ARCHITECTURE.md`, `src`, `tests`, or `pyproject.toml`
  - validation rerun passed:
    - `git diff --check`
    - `manifest.json` JSON parse and structured checks
    - `runs.jsonl` line count exactly 3
    - `runs.jsonl` structured checks for provider order, Task 0 query, budget
      `220`, STRONG evidence shape, `context_ir` token budget `219 / 220`,
      required selected units, `attribute_present=true`,
      `primary=unsupported/opaque`, and `runtime=additive`
    - baseline checks for zero selected files/units plus candidate/omitted
      evidence
    - internal-only, public-claims-held, Tasks 1-3-not-run, caveat, and
      no-broad-superiority wording checks
    - artifact trailing-whitespace/final-newline hygiene
- next route:
  - Task 0 bundle is pushed and should not be reopened absent new findings
  - next authorized portfolio move is Task 1 only: compact eval evidence
    discovery/rendering checkpoint at primary budget `260`, ceiling `360`
  - do not run Tasks 2-3 or update public/demo claims before Task 1 is run,
    reviewed, and accepted

Pushed eval evidence catalog discovery release:
`241f7ea Add eval evidence catalog discovery`. This commit contains the
accepted, audit-cleared, full-regression-cleared, commit-gating-cleared,
locally committed, and pushed catalog-discovery prerequisite for the compact
eval-evidence path. It was pushed with explicit Ryan authorization through
`4ff58c7 Sync eval evidence catalog local routing`. Do not route `241f7ea`
or `4ff58c7` back to release-unit audit, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Pushed selected-unit runtime accounting release:
`8efec26 Add selected-unit runtime accounting`. This commit contains the
accepted, audit-cleared, full-regression-cleared, commit-gating-cleared,
locally committed, and pushed report-accounting prerequisite for the compact
eval-evidence path. It was pushed with explicit Ryan authorization through
`7f7476c Sync selected-unit accounting local routing`. Do not route `8efec26`
or `7f7476c` back to release-unit audit, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Pushed exact identifier edit-anchor release:
`2a8cf10 Add exact identifier edit anchor`. This commit contains the accepted,
audit-cleared, full-regression-cleared, commit-gating-cleared, locally
committed, and pushed scorer targeting release unit. It was pushed with
explicit Ryan authorization through
`edf8e55 Sync identifier anchor local release routing`. Do not route `2a8cf10`
or `edf8e55` back to release-unit audit, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Pushed exact identifier edit-anchor release evidence:

- scorer now applies a bounded exact identifier edit floor for code-like
  identifier mentions only
- exact floor remains limited to resolved function, async-function, class, and
  method candidates
- leading-underscore names such as `_selected_unit_metadata` can anchor
- qualified names, digit-bearing names, and multi-part Camel/Pascal names can
  anchor
- bare single Titlecase command/prose words such as `Fix` do not anchor
- unqualified non-leading snake_case names such as `probe_directory` and
  `probe_namespace` do not receive the exact edit floor in this pilot
- exact real-repo budget-`220` smoke selected:
  `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers._selected_unit_metadata`
- no eval fixtures, run specs, tasks, optimizer, compiler, provider, runtime,
  public docs/claims, MCP/API/schema/config, package export, or benchmark/demo
  artifacts were widened
- release state:
  - accepted in workspace: yes, after 2 corrections
  - release-unit audit cleared: yes, first-pass after second correction
  - full-regression cleared: yes, first-pass after second correction with
    `1693 passed`
  - commit-gating cleared: yes, first-pass
  - source/test locally committed: yes, `2a8cf10`
  - local release routing committed: yes, `edf8e55`
  - pushed: yes, with explicit Ryan authorization
- next route:
  - hold north-star advancement, demo/report artifact work, public claim work,
    and broad fixture expansion because the post-push checkpoint remains only a
    partial differentiated signal
  - next authorized work should be a narrow planning/research slice to identify
    the smallest change needed for the checkpoint to surface the end-to-end
    path, including report accounting context and concrete unsupported
    `hasattr` runtime provenance evidence
  - broad fixture-by-fixture expansion remains paused unless Ryan reauthorizes
    it

Accepted post-push real-repo value checkpoint after exact identifier release:

- read-only checkpoint returned DONE and was accepted as routing evidence
- verdict: PARTIAL differentiated signal
- repo truth reported by the checkpoint and verified by control:
  - branch `main`
  - local `HEAD` and `origin/main` both resolved to
    `e7bcc9c Sync identifier anchor push routing`
  - worktree clean
- exact query:
  `Fix _selected_unit_metadata and eval report accounting so unsupported hasattr runtime provenance remains visible in selected unit metadata`
- budget-`220` result:
  - `context_ir` elapsed about `118.335s`, used `218` tokens, selected the
    exact target, and emitted `budget_pressure x2` plus
    `omitted_uncertainty x6`
  - lexical baseline elapsed about `0.262s`, used `76` tokens, and selected no
    useful file/unit
  - import-neighborhood baseline elapsed about `0.267s`, used `81` tokens, and
    selected no useful file/unit with `import_not_resolved`
  - baselines at budgets `600` and `1000` still selected no useful file/unit
- context-ir selected the target:
  `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers._selected_unit_metadata`
- context-ir selected the exact target and `EvalSelectedUnit`, plus unresolved
  frontier attribute units around `_selected_unit_metadata`
- target selected-unit metadata was present, including tier/origin/replay and
  runtime-provenance fields, but the target itself correctly had
  `has_attached_runtime_provenance=false`
- remaining gaps before tangible internal demo/report:
  - the budget-`220` context did not also surface `eval_summary.py` report
    accounting context
  - it did not surface concrete unsupported `hasattr` runtime-provenance
    evidence
  - exact target and `EvalSelectedUnit` were still summaries under severe
    budget pressure
- Ryan and control agree:
  - do not proceed further toward north-star demo/report/public-claim work on
    this partial signal
  - require full, meaningful differentiated evidence before advancement
  - "smallest change" means the least amount of principled work that unlocks
    full differentiation on this exact checkpoint
  - next move must diagnose whether that smallest change exists and, if it
    does, identify it concretely enough for one bounded implementation slice
  - if no small principled fix can make the checkpoint surface the end-to-end
    path, stop and reassess strategy rather than continuing incremental work

Accepted no-small-fix unlock diagnosis:

- read-only unlock diagnosis returned DONE and was accepted as routing evidence
- verdict: NO SMALL FIX
- root cause:
  - `_selected_unit_metadata`, `EvalSelectedUnit`, and eval summary/report
    accounting already implement the needed metadata and rollups
  - the partial checkpoint is caused by selection and representation behavior
    under budget `220`, not broken selected-unit metadata or report accounting
  - concrete `hasattr` runtime payload evidence exists in eval fixture JSON and
    tests, but the compiler currently models only eligible Python source files
  - therefore the concrete non-Python evidence artifact is outside the compact
    semantic unit universe today
- meaningful differentiation definition for this checkpoint:
  - the win condition is materially better task context with truthful
    uncertainty, under budget, where baselines fail or overinclude
  - `context_ir` must provide the compact evidence path a coding agent would
    need to make or verify the fix, while lexical/import baselines do not
  - the selected context must include the edit target `_selected_unit_metadata`
  - it must include the relevant `EvalSelectedUnit` runtime-provenance data
    contract
  - it must include the report-accounting path in `eval_summary.py`
  - it must include one concrete unsupported `hasattr` runtime-provenance
    evidence surface or an accepted compact equivalent
  - it must preserve additive-only runtime evidence while keeping
    unsupported/opaque as primary truth
  - it must fit under the same budget-`220` checkpoint unless Ryan explicitly
    accepts a revised budget as the product-relevant threshold
  - lexical and import baselines must still fail to provide the same actionable
    evidence path
- control decision:
  - no further north-star advancement, demo/report artifact work, public-claim
    work, or broad fixture expansion is authorized
  - next authorized lane is a bounded design spike for compact eval-evidence
    units or cross-artifact evidence relationships
  - if that design cannot identify a principled bounded implementation path to
    full differentiation, pause and reassess the strategy before further
    implementation

Accepted compact eval-evidence design spike:

- read-only design spike returned DONE and was accepted as routing evidence
- verdict: BOUNDED DESIGN FOUND
- clarification:
  - this does not contradict the prior NO SMALL FIX result
  - there is no small tweak to `_selected_unit_metadata` or `eval_summary.py`
    that proves full differentiation
  - the bounded path requires adding a compact, principled evidence surface
    that the compiler can select under budget
- confirmed blockers:
  - budget-`220` repo-root smoke still selects only `_selected_unit_metadata`,
    `EvalSelectedUnit`, and local `eval_providers.py` frontier/attribute
    uncertainty
  - it selects no `eval_summary.py` report-accounting path
  - it selects no concrete `hasattr` runtime evidence
  - runtime records in that pack are `0`
  - analyzer discovery is Python-only
  - renderable semantic units are currently only proven symbols, unresolved
    frontier, and unsupported constructs
  - concrete `hasattr` evidence exists in fixture JSON and tests but is not
    selectable in a repo-root compile
  - `EvalLedgerSelectedUnit` currently drops `unit_id` and
    `attached_runtime_provenance_record_ids`, so summary/report accounting can
    count runtime payloads globally but cannot join payloads back to
    selected-unit attachments
- accepted design direction:
  - add compact eval-evidence units derived from existing eval assets
  - add a selected-unit runtime-accounting join in `eval_summary.py`
  - integrate compact eval-evidence and report-accounting support into
    semantic rendering/scoring/optimization so the exact budget-`220`
    checkpoint can select the full evidence path by replacing low-value local
    frontier spillover
- principled boundary:
  - mechanism should work across existing `*_runtime_observations` families by
    joining task selectors, fixture observations, normalized payloads, and run
    specs
  - preserve unsupported/opaque as primary truth and runtime evidence as
    additive
  - do not edit fixtures, tasks, run specs, runtime provider support, public
    claims, or demo/report artifacts
- implementation sequence:
  - first slice: selected-unit runtime attachment accounting in
    `eval_summary.py`
  - second slice: `eval_evidence.py` catalog discovery for existing eval
    task/fixture/run-spec artifacts
  - later slice: integrate compact eval-evidence units into semantic rendering,
    scoring, and optimization
  - final checkpoint/regression slice: prove the exact budget-`220` evidence
    path while lexical/import baselines still fail
- next route:
  - selected-unit runtime attachment accounting is pushed as the first
    implementation slice
  - `eval_evidence.py` catalog discovery is accepted in workspace as the second
    implementation slice
  - run a read-only release-unit audit over the exact accepted four-file catalog
    discovery unit before full regression, commit-gating, staging, local commit
    creation, or push
  - do not proceed to north-star demo/report/public-claim work until the full
    evidence-path checkpoint passes

Pushed eval evidence catalog discovery release unit:

- release unit files:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `src/context_ir/eval_evidence.py`
  - `tests/test_eval_evidence.py`
- accepted behavior:
  - `discover_eval_runtime_evidence(...)` builds deterministic compact runtime
    evidence records from existing eval task, fixture runtime-observation, and
    run-spec assets
  - current repo assets produce `26` catalog records
  - `oracle_signal_hasattr_probe` compact evidence includes
    `attribute_present=true`
  - `oracle_signal_eval_probe` compact evidence includes
    `evaluation_outcome=returned_value`
  - unsupported/opaque remains primary truth and runtime evidence remains
    additive
  - missing or ambiguous joins and malformed payloads fail closed
- review evidence:
  - focused validation rerun passed:
    - `ruff check src/context_ir/eval_evidence.py tests/test_eval_evidence.py`
    - `ruff format --check src/context_ir/eval_evidence.py tests/test_eval_evidence.py`
    - `mypy --strict src/`
    - `pytest tests/test_eval_evidence.py tests/test_eval_oracles.py tests/test_eval_runs.py -v`
    - `git diff --check`
  - scratch catalog check confirmed `26` records and compact render output for
    `hasattr`, `eval`, and `metaclass_behavior`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass with `1708 passed`
  - commit-gating cleared: yes, first-pass
  - locally committed: yes, `241f7ea Add eval evidence catalog discovery`
  - pushed: yes, with explicit Ryan authorization through
    `4ff58c7 Sync eval evidence catalog local routing`
- audit evidence:
  - read-only release-unit audit returned PASS with no findings
  - dirty/untracked set remained limited to the four release-unit files
  - validation rerun passed:
    - `git diff --check`
    - `ruff check src/context_ir/eval_evidence.py tests/test_eval_evidence.py`
    - `ruff format --check src/context_ir/eval_evidence.py tests/test_eval_evidence.py`
    - `mypy --strict src/`
    - `pytest tests/test_eval_evidence.py tests/test_eval_oracles.py tests/test_eval_runs.py -v`
  - scratch catalog check confirmed `26` records,
    `attribute_present=true` for `oracle_signal_hasattr_probe`, and
    `evaluation_outcome=returned_value` for `oracle_signal_eval_probe`
- next required action:
  - continue to the semantic eval-evidence integration slice as the next
    compact eval-evidence path prerequisite
  - keep north-star demo/report/public-claim work held until the final
    budget-`220` evidence-path checkpoint passes

Pushed semantic eval-evidence integration release unit:

- release unit files:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `src/context_ir/semantic_types.py`
  - `src/context_ir/eval_evidence.py`
  - `src/context_ir/semantic_renderer.py`
  - `src/context_ir/semantic_scorer.py`
  - `src/context_ir/semantic_optimizer.py`
  - `src/context_ir/semantic_compiler.py`
  - `tests/test_eval_evidence.py`
  - `tests/test_semantic_renderer.py`
  - `tests/test_semantic_scorer.py`
  - `tests/test_semantic_types.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_semantic_compiler.py`
- accepted behavior:
  - compact eval runtime evidence records become internal semantic support
    units
  - renderer exposes those records as unsupported-primary, additive runtime
    evidence without promoting runtime payloads to primary proof
  - scorer makes compact eval evidence searchable for runtime-provenance
    queries and adds a bounded eval-report/accounting anchor
  - optimizer can prefer one compact eval evidence surface and eval-summary
    accounting support over low-value frontier spillover under tight budgets
  - compiler-owned scoring discovers compact eval evidence; callers that pass
    explicit scoring keep the existing explicit-scoring contract
  - repos without eval assets still compile normally
  - malformed discovered eval assets continue to fail closed through
    `EvalEvidenceError`
- review evidence:
  - live git state during review: branch `main`, local `HEAD` and
    `origin/main` both resolved to `989c8f0`
  - no staged files
  - no untracked files
  - dirty set before this continuity update was exactly the 11 declared
    source/test files
  - focused validation rerun passed:
    - `ruff check` on the 11 touched source/test files
    - `ruff format --check` on the 11 touched source/test files
    - `mypy --strict src/`
    - `pytest tests/test_semantic_renderer.py tests/test_semantic_scorer.py tests/test_semantic_optimizer.py tests/test_semantic_compiler.py tests/test_eval_evidence.py -v`
      with `67 passed`
    - additional `pytest tests/test_semantic_types.py -v` with `24 passed`
    - `git diff --check`
  - exact real-repo budget-`220` smoke rerun passed:
    - query:
      `Fix _selected_unit_metadata and eval report accounting so unsupported hasattr runtime provenance remains visible in selected unit metadata`
    - elapsed: `107.911s`
    - total tokens: `219 / 220`
    - selected units:
      - `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers._selected_unit_metadata`
      - `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers.EvalSelectedUnit`
      - `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers.EvalProviderMetadata`
      - `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers.EvalProviderResult`
      - `def:src/context_ir/eval_summary.py:src.context_ir.eval_summary._build_runtime_provenance_record_lookup`
      - `eval_evidence:oracle_signal_hasattr_probe:hasattr:main.py:2:11`
    - required checks all true:
      `_selected_unit_metadata`, `EvalSelectedUnit`, eval report-accounting
      path, compact `oracle_signal_hasattr_probe` evidence,
      `attribute_present=true`, and budget compliance
- correction evidence:
  - full regression found an export-surface boundary issue after first-pass
    audit clearance:
    - `semantic_types.__all__` included
      `SemanticEvalRuntimeEvidence` and `SemanticEvalRuntimeEvidenceField`
    - `context_ir.__all__` intentionally did not include them
    - this caused 43 full-regression failures against the package-root export
      invariant and violated the no-public-export-widening boundary
  - accepted correction keeps compact eval-evidence semantic dataclasses
    internal:
    - removed `SemanticEvalRuntimeEvidence` and
      `SemanticEvalRuntimeEvidenceField` from `semantic_types.__all__`
    - did not add either type to `context_ir.__all__`
    - direct imports from `context_ir.semantic_types` remain available
    - added `tests/test_semantic_types.py` coverage for the internal-only
      boundary
  - focused correction validation passed:
    - `ruff check src/context_ir/semantic_types.py tests/test_semantic_types.py`
    - `ruff format --check src/context_ir/semantic_types.py tests/test_semantic_types.py`
    - `mypy --strict src/`
    - focused pytest over semantic-types, public API, MCP/facade, eval-summary,
      and `hasattr` eval-signal tests with `117 passed`
    - scratch export-boundary check confirmed direct imports remain available,
      neither type is package-root exported, and
      `tuple(context_ir.__all__) == tuple(semantic_types.__all__)`
    - `git diff --check`
- boundary:
  - no eval fixture, task, run-spec, provider, runtime/probe worker,
    `eval_summary.py`, public docs/claims, MCP/API/schema/config,
    package-root export, or demo/report artifact changes are included
  - this slice does not make a public claim or produce a demo artifact
  - real-repo latency remains about two minutes for this checkpoint
- release state:
  - accepted in workspace: yes, after 1 export-surface correction
  - release-unit audit cleared: yes, first-pass after export-surface
    correction
  - full-regression cleared: yes, first-pass after corrected audit with
    `1714 passed`
  - commit-gating cleared: yes, first-pass
  - locally committed: yes, `fc2ddc6 Integrate compact eval evidence into semantic context`
  - local release routing committed: yes,
    `b6be7e5 Sync semantic eval evidence local routing`
  - pushed: yes, with explicit Ryan authorization
- push evidence:
  - before push, branch `main` was ahead of `origin/main` by two commits:
    `fc2ddc6` and `b6be7e5`
  - Ryan explicitly authorized push
  - `git push origin main` succeeded, advancing remote `main` from `989c8f0`
    to `b6be7e5`
  - after push, local `HEAD` and `origin/main` both resolved to `b6be7e5`
  - worktree, index, and untracked files were clean
- local commit evidence:
  - staged exactly the corrected 14-file release unit
  - verified staged file set, no unstaged files, no untracked files, and
    `git diff --cached --check` before commit
  - created local release commit
    `fc2ddc6 Integrate compact eval evidence into semantic context`
  - after commit, local `HEAD` resolved to `fc2ddc6`, `origin/main` remained
    `989c8f0`, and the branch was ahead by one commit
- commit-gating evidence:
  - live state during commit-gating remained branch `main` with local `HEAD`
    and `origin/main` at `989c8f0`
  - no staged files
  - no untracked files
  - dirty files exactly matched the corrected 14-file release unit
  - `git diff --check` remained clean
  - diff stat was limited to the expected semantic eval-evidence integration,
    tests, and continuity docs
  - export-boundary smoke confirmed:
    - `SemanticEvalRuntimeEvidence` direct import works
    - `SemanticEvalRuntimeEvidenceField` direct import works
    - neither name is present in `semantic_types.__all__`
    - neither name is present in `context_ir.__all__`
    - `tuple(context_ir.__all__) == tuple(semantic_types.__all__)`
  - no public docs, eval fixtures/tasks/run specs, provider/runtime paths,
    MCP/API/schema/config, package-root export, or demo/report artifacts were
    modified
- full-regression evidence:
  - after corrected audit clearance, full regression passed:
    - `ruff check src/ tests/`
    - `ruff format --check src/ tests/`
    - `mypy --strict src/`
    - `pytest tests/ -v` with `1714 passed`
- corrected audit evidence:
  - read-only release-unit audit returned PASS with no findings
  - live state matched expected:
    - branch `main`
    - local `HEAD` and `origin/main` both resolved to `989c8f0`
    - no staged files
    - no untracked files
    - dirty files exactly matched the corrected 14-file release unit
    - `git diff --check` was clean
  - no eval fixture, task, run-spec, provider/runtime path, public doc, API,
    MCP, schema/config, package-root export, or demo/report artifact changes
    were present
  - export-boundary smoke confirmed `SemanticEvalRuntimeEvidence` and
    `SemanticEvalRuntimeEvidenceField` remain directly importable from
    `context_ir.semantic_types`, but absent from both `semantic_types.__all__`
    and `context_ir.__all__`
  - exact budget-`220` evidence path rerun passed with `219 / 220` tokens,
    selecting `_selected_unit_metadata`, `EvalSelectedUnit`, eval-summary
    `_build_runtime_provenance_record_lookup`, compact
    `oracle_signal_hasattr_probe` evidence, and rendering
    `attribute_present=true`
- prior audit evidence, superseded for release readiness by the later
  source/test correction:
  - read-only release-unit audit returned PASS with no findings
  - live state matched expected:
    - branch `main`
    - local `HEAD` and `origin/main` both resolved to `989c8f0`
    - no staged files
    - no untracked files
    - dirty set exactly matched the 13-file release unit
  - no excluded eval fixtures/tasks/run-specs, provider/runtime paths, public
    docs/claims, API/MCP/schema/config/export, or demo/report artifacts changed
  - validation rerun passed:
    - `git diff --check`
    - focused `ruff check`
    - focused `ruff format --check`
    - `mypy --strict src/`
    - focused pytest with `91 passed`
  - exact budget-`220` smoke passed with `219 / 220` tokens and selected the
    required full evidence path including `attribute_present=true`
- next required action:
  - run the post-push evidence-path baseline comparison checkpoint for the
    exact budget-`220` query
  - confirm whether `context_ir` now gives materially better task context with
    truthful uncertainty under budget while lexical/import baselines fail or
    overinclude
  - keep demo/report/public-claim work held until that post-push checkpoint is
    reviewed and accepted
  - keep north-star demo/report/public-claim work held until the final
    evidence-path checkpoint with baselines passes

Pushed selected-unit runtime accounting release unit:

- release unit files:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `src/context_ir/eval_summary.py`
  - `tests/test_eval_summary.py`
- accepted behavior:
  - ledger selected units retain `unit_id`
  - ledger selected units retain `attached_runtime_provenance_record_ids`
  - selected-unit runtime provenance links fail closed when they cannot join
    deterministically to row runtime records
  - selected-unit runtime payload outcomes render in a compact deterministic
    `Selected-Unit Runtime Outcomes` table
  - older ledgers without selected-unit runtime IDs remain compatible
  - boolean tier/provider runtime aggregate accounting remains unchanged
- review evidence:
  - focused validation rerun passed:
    - `ruff check`
    - `ruff format --check`
    - `mypy --strict src/`
    - `pytest tests/test_eval_summary.py tests/test_eval_signal_hasattr_probe.py -v`
    - `git diff --check`
  - scratch review confirmed the actual `oracle_signal_hasattr_probe` report
    now joins the selected unsupported unit to `attribute_present=true`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass with `1697 passed`
  - commit-gating cleared: yes, first-pass
  - locally committed: yes, `8efec26 Add selected-unit runtime accounting`
  - pushed: yes, with explicit Ryan authorization through `7f7476c`
- audit evidence:
  - read-only release-unit audit returned PASS with no findings
  - dirty set remained exactly the four release-unit files
  - validation rerun passed:
    - `git diff --check`
    - `ruff check`
    - `ruff format --check`
    - `mypy --strict src/`
    - `pytest tests/test_eval_summary.py tests/test_eval_signal_hasattr_probe.py -v`
  - actual `oracle_signal_hasattr_probe` summary join was verified as
    `('unsupported:call:main.py:2:11', 'attribute_present', 'true', 2)`
- next required action:
  - continue to the `eval_evidence.py` catalog discovery implementation slice
    as the next compact eval-evidence path prerequisite
  - keep north-star demo/report/public-claim work held until the final
    budget-`220` evidence-path checkpoint passes

Pushed optimizer/render latency release:
`204173a Optimize semantic compile candidate selection`. This commit contains
the accepted, audit-cleared, full-regression-cleared, commit-gating-cleared,
locally committed, and pushed optimizer/render caching correction release unit.
It was pushed with explicit Ryan authorization through
`77424ca Sync optimizer render push routing`. Do not route `204173a`,
`cda9fa9`, or `77424ca` back to release-unit audit, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Pushed optimizer/render latency release evidence:

- request-scoped semantic render session builds renderer lookup indexes once
  per optimizer run
- optimizer candidate construction caches rendered `(unit_id, detail)`
  materialization locally
- public `render_semantic_unit(...)` behavior remains unchanged
- optimizer avoids repeated full pending-candidate sorting each loop using
  `_CandidateSortState`
- optimizer walks pending candidates by cursor rather than repeated `pop(0)`
  list shifting
- remaining suffix is re-sorted only when focus-dependent dynamic sort state
  changes
- existing optimizer selection/order/warning/token behavior is preserved by
  focused regressions
- exact real-repo smoke for the full `_selected_unit_metadata` query at budget
  `220` produced a non-empty in-budget pack before the `180s` alarm
- no scoring, targeting, source discovery, eval provider, runtime behavior,
  public docs/claims, MCP/API/schema/config, package export, compiler contract,
  or winner-selection widening is included
- release state:
  - accepted in workspace: yes, first-pass correction acceptance
  - release-unit audit cleared: yes, after 1 documentation correction
  - full-regression cleared: yes, first-pass with `1687 passed`
  - commit-gating cleared: yes, first-pass
  - locally committed: yes, `204173a`
  - pushed: yes, with explicit Ryan authorization
- next route:
  - superseded by the pushed exact identifier edit-anchor release route above
  - do not proceed to demo/report artifact or public claim work yet

Accepted targeting/budget research spike after optimizer/render release:

- read-only targeting/budget research spike returned DONE and was accepted as
  routing evidence
- repo truth reported by the spike and verified by control:
  - branch `main`
  - local `HEAD` and `origin/main` both resolved to
    `77424ca Sync optimizer render push routing`
  - worktree was clean before this control-state update
- exact real-repo compile evidence:
  - exact query:
    `Fix _selected_unit_metadata and eval report accounting so unsupported hasattr runtime provenance remains visible in selected unit metadata`
  - budget: `220`
  - compile completed in about `135.552s`
  - total tokens: `218 / 220`
  - selected units: `6`
  - target selected: no
  - target omitted: yes
- target evidence:
  - target:
    `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers._selected_unit_metadata`
  - score: `p_edit=0.305577`, `p_support=0.114591`
  - ranks: final strongest-score `186`, edit-rank `23`, direct-edit-rank
    `20`, support-rank `3040`
  - render costs: identity `70`, summary `32`, source `287`
  - target has no incoming dependency support and points outward only to
    `EvalSelectedUnit`
- root cause:
  - targeting/ranking issue, not metadata/report serialization
  - dependency-propagated `p_support` saturates support-heavy helper/test units
  - no-focus optimizer order ranks by `max(p_edit, p_support)` before edit
    intent, so high-support helpers outrank the edit target
  - scorer does not strongly anchor a raw exact identifier such as
    `_selected_unit_metadata` when it appears literally in the query
  - not caused by compiler binary search, selected-unit metadata serialization,
    eval ledger serialization, or report accounting
- recommended next slice pending Ryan authorization:
  - add a narrow exact-identifier edit anchor for raw symbol names in queries,
    especially snake_case names such as `_selected_unit_metadata`
  - require the exact real-repo budget-`220` smoke to select
    `_selected_unit_metadata` within budget
  - keep eval assets, providers, runtime support, MCP/API/schema/config,
    public docs/claims, package exports, benchmark/demo artifacts, and broad
    ranking rewrites out of scope
  - do not reopen the pushed optimizer/render latency release absent new
    findings

Held exact-identifier edit-anchor implementation review:

- returned implementation added a narrow exact-identifier edit anchor in
  `src/context_ir/semantic_scorer.py` with focused tests in
  `tests/test_semantic_scorer.py`
- reported validation passed:
  - ruff check over touched scorer/test paths
  - ruff format check over touched scorer/test paths
  - strict mypy over `src/`
  - focused pytest over semantic scorer, semantic optimizer, and eval provider
    tests with `49 passed`
  - `git diff --check`
- reported exact real-repo smoke passed for the full `_selected_unit_metadata`
  query at budget `220`, with target selected and total tokens `218 / 220`
- control review found a boundary defect:
  - `src/context_ir/semantic_scorer.py` treats any uppercase token as a
    code-like identifier mention
  - sentence-start prose such as `Fix` can become an exact identifier anchor
  - a temporary repro with `def Fix()` and `def _selected_unit_metadata()`
    showed query `Fix _selected_unit_metadata` assigning `p_edit=1.0` to both
    symbols
  - this violates the slice boundary that the exact identifier anchor must not
    apply to arbitrary words
- Ryan agreed with the finding
- release state:
  - accepted in workspace: no, held on audit finding
  - release-unit audit cleared: no
  - full-regression cleared: no
  - commit-gating cleared: no
  - locally committed: no
  - pushed: no
- next route:
  - issue one narrow correction slice that preserves snake_case, qualified-name,
    digit-bearing, and real multi-part PascalCase/CamelCase exact anchors, but
    prevents single Titlecase prose words such as `Fix` or `Update` from
    triggering the exact-identifier edit floor
  - add regression coverage proving a function or class named `Fix` is not
    boosted by the command word in `Fix _selected_unit_metadata`, while the
    `_selected_unit_metadata` target remains selected in the exact real-repo
    budget-`220` smoke

Workspace-only exact-identifier edit-anchor correction acceptance:

- correction result reviewed findings-first against live repo state and
  accepted first-pass
- accepted release-unit files:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `src/context_ir/semantic_scorer.py`
  - `tests/test_semantic_scorer.py`
- corrected behavior:
  - exact raw identifier anchors now still qualify via `_`, `.`, digits, or
    multi-part Camel/Pascal shape
  - bare single Titlecase words such as `Fix` no longer qualify solely because
    they are capitalized
  - exact anchors remain limited to function/class/method symbol names or
    qualified names
  - imported names, locals, attributes, arbitrary prose, and substrings remain
    unanchored
- control validation:
  - live repo state verified: branch `main`, local `HEAD` and `origin/main`
    both `77424ca`, no staged files, no untracked files
  - false-positive repro now gives `p_edit=0.046667` for `main.Fix` and
    `p_edit=1.0` for `main._selected_unit_metadata`
  - multi-part `EvalSelectedUnit` still receives the exact anchor
  - ruff check passed over touched scorer/test plus semantic optimizer and eval
    provider tests
  - ruff format check passed over the same paths
  - strict mypy passed over `src/`
  - focused pytest passed with `50 passed`
  - exact real-repo budget-`220` smoke passed in `132.343s` with total tokens
    `218 / 220`, selected count `10`, and target selected:
    `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers._selected_unit_metadata`
  - `git diff --check` passed
- release state:
  - accepted in workspace: yes, after 1 correction
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: no, held on 3 eval-signal regressions
  - commit-gating cleared: no
  - locally committed: no
  - pushed: no
- next route:
  - issue one narrow scorer correction to preserve the real-repo
    `_selected_unit_metadata` anchor while avoiding unqualified snake_case
    anchor effects on existing oracle eval fixture queries such as
    `probe_directory` and `probe_namespace`
  - rerun focused validation and then full regression from the top
  - do not stage, commit, or push before those gates clear
  - push remains Ryan-gated

Full-regression hold for exact-identifier edit-anchor release unit:

- full regression was run after release-unit audit clearance
- passed before pytest:
  - `ruff check src/ tests/`
  - `ruff format --check src/ tests/`
  - `mypy --strict src/`
- full pytest result:
  - `1687 passed`
  - `3 failed`
- failing tests:
  - `tests/test_eval_signal_dir_zero_probe.py::test_dir_zero_probe_run_executes_with_additive_runtime_provenance`
  - `tests/test_eval_signal_vars_type_error_probe.py::test_vars_type_error_probe_run_preserves_additive_runtime_fields`
  - `tests/test_eval_signal_vars_type_error_probe.py::test_vars_type_error_probe_summary_keeps_runtime_additive`
- finding:
  - the exact identifier anchor is still too broad for this release unit
  - unqualified snake_case names in existing eval run-spec queries, including
    `probe_directory` and `probe_namespace`, now receive exact edit-anchor
    treatment
  - that changes existing context-ir selected-unit ordering/composition in the
    dir-zero and vars-TypeError eval probes
  - accepting the new outputs would widen existing eval behavior and evidence
    beyond the intended `_selected_unit_metadata` targeting pilot
- release state remains held before commit-gating, staging, local commit
  creation, or push
- next route:
  - correct the scorer anchor to keep the exact real-repo
    `_selected_unit_metadata` smoke passing while avoiding the existing eval
    probe regressions
  - do not update eval expectations to match the broader behavior without an
    explicit Ryan-approved scope expansion

Workspace-only exact-identifier edit-anchor second correction acceptance:

- second correction result reviewed findings-first against live repo state and
  accepted first-pass
- accepted release-unit files remain:
  - `PLAN.md`
  - `BUILDLOG.md`
  - `src/context_ir/semantic_scorer.py`
  - `tests/test_semantic_scorer.py`
- corrected behavior:
  - exact identifier anchors still qualify for leading-underscore names such as
    `_selected_unit_metadata`
  - qualified-name anchors remain supported, such as `main.probe_directory`
  - digit-bearing anchors remain supported
  - multi-part Camel/Pascal anchors remain supported, such as
    `EvalSelectedUnit`
  - bare single Titlecase command/prose words such as `Fix` remain unanchored
  - unqualified non-leading snake_case names such as `probe_directory` and
    `probe_namespace` no longer receive the exact edit floor in this pilot
- control validation:
  - live repo state verified: branch `main`, local `HEAD` and `origin/main`
    both `77424ca`, no staged files, no untracked files
  - `git diff --check` passed
  - ruff check passed over touched scorer/test, semantic optimizer, eval
    provider, dir-zero eval-signal, and vars-TypeError eval-signal tests
  - ruff format check passed over the same paths
  - strict mypy passed over `src/`
  - focused pytest passed with `70 passed`, including the three previously
    failing eval-signal tests
  - exact real-repo budget-`220` smoke passed in `110.879s` with total tokens
    `218 / 220`, selected count `10`, and target selected:
    `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers._selected_unit_metadata`
- release state:
  - accepted in workspace: yes, after 2 corrections
  - release-unit audit cleared: yes, first-pass after second correction
  - full-regression cleared: yes, first-pass after second correction with
    `1693 passed`
  - commit-gating cleared: yes, first-pass after final routing correction
  - source/test locally committed: yes, `2a8cf10 Add exact identifier edit anchor`
  - local release routing committed: yes,
    `edf8e55 Sync identifier anchor local release routing`
  - pushed: yes, with explicit Ryan authorization
- next route:
  - post-push continuity sync records this release as pushed
  - next substantive route is the pushed exact identifier edit-anchor release
    route in the canonical active release-state block

Pushed source-discovery hygiene release:
`7261d02 Add eligible Python source discovery`. This commit contains the
accepted source-discovery hygiene fix that prunes dependency/generated/cache
directories from repo-root syntax extraction, legacy parsing, and eval
baseline discovery. It was pushed with explicit Ryan authorization through
`eb4ba7e Sync source discovery local release routing`. Do not route `7261d02`
or `eb4ba7e` back to release-unit audit, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Pushed source-discovery hygiene release evidence:

- one shared internal eligible Python source-discovery helper is used by:
  - `extract_syntax(...)`
  - legacy `parse_repository(...)`
  - `_discover_baseline_files(...)`
- dependency/generated/cache directories are pruned, including `.venv`,
  `venv`, `env`, `.git`, `__pycache__`, `.mypy_cache`, `.pytest_cache`,
  `.ruff_cache`, `build`, `dist`, and `node_modules`
- explicit single-file parsing remains intact for caller-selected files inside
  skipped directories
- root-level smoke checks before commit showed `181` syntax files, `181`
  baseline files, and no `.venv` paths
- no eval assets, public docs/claims, exports, MCP/API/schema/config, scoring,
  optimizer, renderer, compiler, runtime/provider support, or package exports
  were widened
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass with `1684 passed`
  - commit-gating cleared: yes, first-pass
  - locally committed: yes, `7261d02`
  - pushed: yes, with explicit Ryan authorization
- next route:
  - the real-repo value checkpoint rerun on the pushed source-discovery
    release is complete and accepted as a partial signal result
  - route next to optimizer/render caching before targeting research
  - broad fixture-by-fixture expansion remains paused

Accepted real-repo checkpoint rerun after source discovery:

- read-only real-repo checkpoint rerun returned PARTIAL real-repo
  differentiated signal and was accepted first-pass as a routing spike result
- repo truth reported by the spike:
  - branch `main`
  - local `HEAD` and `origin/main` both resolved to
    `a46fa94 Sync source discovery push routing`
  - worktree, index, untracked files, and `git diff --check` were clean
- source-discovery proof:
  - raw repo `*.py` files: `11,871`
  - raw `.venv` `*.py` files: `11,690`
  - eligible syntax files: `181`
  - baseline files: `181`
  - forbidden dependency/cache/generated paths in eligible syntax: `0`
  - syntax diagnostics: `0`
- performance evidence:
  - source discovery count completed in about `0.54s`
  - `extract_syntax(".")` completed in about `13.6-13.8s`
  - `analyze_repository(".")` completed in about `14.8-15.6s`
  - `score_semantic_units(...)` completed in about `75.9s` total
  - full `context_ir` compile/provider path at budget `220` did not produce a
    pack within the bounded run
  - stack sample identified
    `optimize_semantic_units -> _build_candidates -> render_semantic_unit ->
    _unresolved_by_id`
- comparison evidence:
  - lexical and import baselines completed quickly at budgets `220`, `600`,
    and `1000`, but selected no files under those budgets
  - target file ranked `31` for lexical whole-file packing and was outside the
    top-8 candidate set
  - import-neighborhood did not seed the target
  - the exact target function
    `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers._selected_unit_metadata`
    was visible to semantic scoring but ranked `180th`
- routing decision:
  - do not proceed to an internal demo/report artifact yet
  - do not resume broad fixture-by-fixture expansion yet
  - next implementation slice is optimizer/render candidate-materialization
    caching only
  - targeting/budget research on the same `_selected_unit_metadata` query
    remains the follow-up after compile latency is corrected
  - no public docs/claims should be widened from this partial result

Workspace-only optimizer/render caching implementation review:

- returned implementation added a request-scoped semantic render session and
  local `(unit_id, detail)` render cache for optimizer candidate construction
- focused validation passed:
  - ruff check over touched optimizer/renderer/test files
  - ruff format check over touched optimizer/renderer/test files
  - strict mypy over `src/`
  - focused pytest over semantic optimizer, renderer, and compiler tests with
    `33 passed`
  - `git diff --check`
- control reran a bounded real-repo compile smoke on the same
  `_selected_unit_metadata` query at budget `220`
- smoke evidence:
  - analysis completed in about `14.849s`
  - scoring completed in about `75.048s`
  - compile still did not produce a pack before the `180s` alarm
  - timeout now landed in
    `optimize_semantic_units -> pending_candidates.sort ->
    _candidate_sort_key`
- review decision:
  - held with finding, not accepted
  - the render-session work appears useful but does not yet satisfy the
    real-repo latency objective
  - do not run release-unit audit, full regression, commit-gating, staging,
    local commit creation, or push for this unit yet
  - next route is a narrow correction pass for optimizer selection-loop
    sorting/repeated-optimization latency, preserving the render-session work
    unless the correction proves it must change

Workspace-only optimizer/render caching correction acceptance:

- correction result reviewed findings-first and accepted first-pass
- accepted behavior:
  - optimizer candidate construction keeps the request-scoped render session
    and local `(unit_id, detail)` render cache from the prior implementation
  - optimizer selection no longer repeatedly sorts the full pending-candidate
    list on every loop iteration
  - optimizer selection uses a `_CandidateSortState` guard and cursor over the
    pending list
  - remaining suffix is re-sorted only when focus-dependent dynamic sort state
    changes
  - repeated `pop(0)` list shifting is removed from the selection loop
  - existing optimizer selection/order/warning/token behavior remains covered
    by focused regressions
- validation rerun by control:
  - focused ruff check passed
  - focused ruff format check passed with `6 files already formatted`
  - strict mypy over `src/` passed with no issues in `38 source files`
  - focused pytest over semantic optimizer, renderer, and compiler tests passed
    with `34 passed`
  - `git diff --check` passed
- bounded real-repo smoke rerun by control:
  - exact query:
    `Fix _selected_unit_metadata and eval report accounting so unsupported hasattr runtime provenance remains visible in selected unit metadata`
  - budget: `220`
  - command shape: analyze `Path(".")`, score semantic units with the exact
    query, then call `compile_semantic_context(..., budget=220, scoring=scoring)`
  - compile produced a pack before the `180s` alarm
  - total elapsed time observed by control was about `126.863s`
  - the pack was non-empty and within budget with `total_tokens <= 220`
  - exact selected-unit, warning, token, and omitted counts are descriptive
    smoke output only, not release-state invariants
- release-unit audit correction:
  - first audit failed because this block previously shortened the query to
    `_selected_unit_metadata` and recorded exact pack counts as if they were
    invariants
  - corrected pass condition is exact-query latency, non-empty pack, and budget
    compliance before the `180s` alarm
  - release-unit audit must be rerun from the top before full regression,
    commit-gating, staging, local commit creation, or push
- accepted release unit:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/semantic_optimizer.py`
  - `src/context_ir/semantic_renderer.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_semantic_renderer.py`
- release/control state:
  - accepted in workspace: yes, first-pass correction acceptance
  - release-unit audit cleared: yes, after 1 documentation correction
  - full-regression cleared: yes, first-pass after audit clearance
  - commit-gating cleared: yes, first-pass
  - locally committed: yes, `204173a`
  - pushed: yes, with explicit Ryan authorization
- next route:
  - run targeting/budget research on the same `_selected_unit_metadata` query
  - do not proceed to demo/report artifact or public claim work yet

Pushed exact `hasattr` provider/checkpoint release:
`3fb8b15 Add hasattr default subprocess eval provider`. This commit contains
the accepted exact `oracle_signal_hasattr_probe` support inside the internal
`context_ir_default_local_python_subprocess` provider and includes the
`oracle_signal_hasattr_probe` row in the internal tangible checkpoint bundle.
It was pushed with explicit Ryan authorization through
`97c48c0 Sync hasattr provider local release routing`. Do not route `3fb8b15`
or `97c48c0` back to release-unit audit, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Pushed exact `hasattr` provider/checkpoint release evidence:

- provider support remains exact to `oracle_signal_hasattr_probe`:
  - miss evidence is `hasattr(obj, name)`
  - family is `RuntimeProbeFamily.REFLECTIVE_BUILTIN`
  - form is `reflective_builtin:hasattr/2`
  - boundary is `hasattr(obj, name)`
  - subject is `unsupported:call:main.py:2:11`
  - replay target seed is `main.probe_attribute`
  - replay inputs remain `object_type=builtins.int` and
    `attribute_name=bit_length` through `request_replay_payload_fields`
  - normalized payload is `attribute_present=true`
  - initial compile remains runtime-fixture-free
  - recompile uses `sys.executable`, `delta_budget=0`, and the real worker
    subprocess invocation
    `(sys.executable, "-m", "context_ir.runtime_probe_worker")`
  - provider-owned runtime provenance comes from the recompiled response
  - unsupported/opaque primary truth remains preserved with additive runtime
    provenance
  - unsupported task IDs remain fail-closed
- checkpoint support:
  - `context_ir.eval_checkpoint` now enumerates eight exact default-subprocess
    rows, including `oracle_signal_hasattr_probe`
- no eval assets, public docs/claims, exports, MCP, schema/config, compiler,
  scoring, runtime worker, or generalized runtime/provider support surfaces
  were widened
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass with `1681 passed`
  - commit-gating cleared: yes, first-pass
  - locally committed: yes, `3fb8b15`
  - pushed: yes, with explicit Ryan authorization
- next route:
  - run the value checkpoint spike to test actual differentiated behavior
    against simple baselines on a realistic coding task
  - if the value checkpoint is weak, pause implementation expansion and run a
    serious research/debug spike before adding more internal fixtures
  - do not continue broad fixture-by-fixture expansion before the value
    checkpoint

Accepted value checkpoint spike result:

- read-only value checkpoint spike returned PARTIAL differentiated signal and
  was accepted first-pass
- artifacts:
  - checkpoint:
    `/private/tmp/context-ir-value-checkpoint.1824ca8-spike-001/checkpoint`
  - comparison:
    `/private/tmp/context-ir-value-checkpoint.1824ca8-spike-001/comparison`
  - qualitative probe:
    `/private/tmp/context-ir-value-checkpoint.1824ca8-spike-001/repo_probe_relevant_modules/summary.json`
- evidence:
  - eight exact default-subprocess checkpoint probes produced runtime payloads
  - budget-100 comparison showed `context_ir` aggregate `0.957`,
    `context_ir_default_local_python_subprocess` aggregate `0.790`, and
    lexical/import baselines aggregate `0.298`
  - context providers preserved uncertainty/runtime evidence while
    lexical/import baselines had uncertainty honesty `0.000`
  - repo-realistic qualitative probe showed `context_ir` could send a tight
    symbol-level pack where file baselines selected no files under budget
  - the same real-repo probe still omitted the exact
    `_selected_unit_metadata` target under budget pressure
  - direct full-root probing failed because analyzer traversal reached `.venv`
    and hit a non-UTF-8 Python file
  - broader tracked/package probes were too slow for the bounded spike
- routing decision:
  - do not make public claims from this checkpoint
  - do not continue broad fixture-by-fixture expansion yet
  - next route is a deeper research/debug spike focused on:
    full-root source exclusion, repo-scale analysis latency, and one
    repeatable real-repo qualitative eval that completes without a hand-built
    mini-snapshot

Accepted source-discovery research/debug spike result:

- deeper read-only research/debug spike returned a concrete implementation
  route and was accepted first-pass
- findings:
  - full-root failure is source-discovery hygiene:
    `extract_syntax(...)` uses unfiltered `root.rglob("*.py")`
  - repo-root analysis walks `.venv`; live scale check showed `11,690` Python
    files under `.venv` versus `181` tracked Python files
  - the non-UTF-8 crash is a consequence of dependency traversal under `.venv`
  - `_discover_baseline_files(...)` in `eval_providers.py` duplicates raw
    `repo_root.rglob("*.py")` traversal and UTF-8 reads for baselines
  - legacy `parse_repository(...)` also uses raw `root.rglob("*.py")`
  - after source exclusion, repo-scale latency still needs follow-up work in
    optimizer/render candidate materialization
  - the prior `_selected_unit_metadata` miss was budget/targeting behavior, not
    a broken metadata serializer
- next implementation route:
  - add one shared eligible Python source-discovery helper
  - use it in `extract_syntax(...)`, `_discover_baseline_files(...)`, and
    legacy `parse_repository(...)`
  - tests must prove ignored `.venv` and non-UTF-8 dependency files are
    skipped
- held follow-ups:
  - optimizer/render caching and repo-scale latency improvement
  - repeatable real-repo qualitative eval after source discovery is fixed
  - broad fixture-by-fixture expansion remains paused

Workspace-only source-discovery hygiene implementation acceptance:

- implementation result reviewed findings-first and accepted first-pass with
  no findings
- accepted behavior:
  - one shared internal eligible Python source-discovery helper was added in
    `src/context_ir/parser.py`
  - `extract_syntax(...)`, legacy `parse_repository(...)`, and eval baseline
    discovery now use the shared helper
  - dependency/generated/cache directories are pruned, including `.venv`,
    `venv`, `env`, `.git`, `__pycache__`, `.mypy_cache`, `.pytest_cache`,
    `.ruff_cache`, `build`, `dist`, and `node_modules`
  - explicit single-file parsing still works for caller-selected files inside
    skipped directories
  - skipped non-UTF-8 dependency/cache files do not crash repo-root syntax
    extraction, legacy parsing, or baseline discovery
- accepted release unit:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/parser.py`
  - `src/context_ir/eval_providers.py`
  - `tests/test_parser.py`
  - `tests/test_eval_providers.py`
- validation rerun by control:
  - focused ruff check passed
  - focused ruff format check passed with `4 files already formatted`
  - strict mypy over `src/` passed with no issues in `38 source files`
  - focused pytest passed with `84 passed`
  - `git diff --check` passed
  - root-level smoke check showed `extract_syntax(".")` discovers `181`
    source files and no `.venv` paths
  - baseline-discovery smoke check showed `181` source files and no `.venv`
    paths
- release/control state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: no
  - full-regression cleared: no
  - commit-gating cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run dedicated read-only release-unit audit over the exact six-file release
    unit before full regression, commit-gating, staging, local commit, or push

Workspace-only source-discovery hygiene release-unit audit clearance:

- dedicated read-only release-unit audit returned PASS
- findings: none
- audit-cleared release unit remains exactly:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/parser.py`
  - `src/context_ir/eval_providers.py`
  - `tests/test_parser.py`
  - `tests/test_eval_providers.py`
- audit evidence:
  - shared source-discovery helper is bounded and deterministic
  - dependency/generated/cache directories are pruned, including `.venv`
  - `extract_syntax(...)`, legacy `parse_repository(...)`, and
    `_discover_baseline_files(...)` use the shared source boundary
  - explicit single-file parsing remains intact
  - no scoring, optimizer, renderer, compiler, runtime/provider support,
    public docs/claims, MCP/API/schema/config, or package export behavior was
    widened
  - actual-repo smoke check found `181` syntax files, `181` baseline files, no
    forbidden-dir paths, and deterministic discovery
- live repo/workspace state was verified:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `1824ca8 Sync hasattr provider push routing`
  - no staged files
  - no untracked files
  - dirty set exactly matches the accepted release unit
  - `git diff --check` passed
- release/control state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: no
  - commit-gating cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run full regression before commit-gating, staging, local commit, or push

Workspace-only source-discovery hygiene full regression clearance:

- full regression gate passed first-pass after release-unit audit clearance
- validation:
  - `.venv/bin/python -m ruff check src/ tests/` passed
  - `.venv/bin/python -m ruff format --check src/ tests/` passed with
    `112 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed with no issues in
    `38 source files`
  - `.venv/bin/python -m pytest tests/ -v` passed with `1684 passed`
- release/control state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass
  - commit-gating cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run commit-gating review over the exact six-file release unit before
    staging, local commit, or push

Workspace-only source-discovery hygiene commit-gating clearance:

- commit-gating review passed first-pass with no findings
- commit-gating evidence:
  - dirty file set exactly matches the accepted six-file release unit
  - no staged files were present during review
  - no untracked files were present during review
  - local `HEAD` and `origin/main` both resolved to
    `1824ca8 Sync hasattr provider push routing`
  - `git diff --check` passed
  - implementation diff is limited to `parser.py`, `eval_providers.py`, and
    focused parser/eval-provider tests
  - `extract_syntax(...)`, legacy `parse_repository(...)`, and
    `_discover_baseline_files(...)` now use the shared eligible Python source
    boundary
  - explicit single-file parsing remains intact
  - remaining raw fixture hashing traversal in `eval_results.py` is outside
    the repo-root source-discovery/baseline path and was not changed
  - no eval assets, public docs/claims, package-root exports, MCP,
    schema/config, scoring, optimizer, renderer, compiler, runtime/provider
    support, or package export surfaces have diffs
- release/control state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass
  - commit-gating cleared: yes, first-pass
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - stage exactly the six-file release unit and create a local release commit
  - do not push without explicit Ryan authorization

Locally committed source-discovery hygiene release:

- local release commit:
  - `7261d02 Add eligible Python source discovery`
- committed release unit:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/parser.py`
  - `src/context_ir/eval_providers.py`
  - `tests/test_parser.py`
  - `tests/test_eval_providers.py`
- live repo/workspace state immediately after local commit:
  - branch `main`
  - local `HEAD` resolves to `7261d02`
  - `origin/main` resolves to `1824ca8 Sync hasattr provider push routing`
  - branch is ahead of `origin/main` by one commit before this continuity sync
  - no staged files
  - no untracked files
- release/control state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass
  - commit-gating cleared: yes, first-pass
  - locally committed: yes, `7261d02`
  - pushed: no
- next route:
  - push the local release commit only after explicit Ryan authorization
  - do not route `7261d02` back to release-unit audit, full regression,
    commit-gating, staging, or local commit creation absent new findings
  - after this release is pushed, rerun the real-repo value checkpoint path
    before optimizer/render caching or broader fixture expansion

Pushed exact `hasattr/2` replay-input bridge release:
`2140cf5 Add exact hasattr replay-input bridge`. This commit contains the
accepted lower-layer exact replay-input bridge for only
`oracle_signal_hasattr_probe` / `reflective_builtin:hasattr/2`. It was pushed
with explicit Ryan authorization through
`dc02adf Sync hasattr bridge local release routing`. Do not route `2140cf5` or
`dc02adf` back to release-unit audit, full regression, commit-gating, staging,
local commit creation, or push absent new findings.

Pushed exact `hasattr/2` release evidence:

- implemented exact pre-observation replay-input bridge:
  - parent runtime-probe execution appends only
    `object_type=builtins.int` and `attribute_name=bit_length` for the exact
    `RuntimeProbeFamily.REFLECTIVE_BUILTIN`,
    `reflective_builtin:hasattr/2`, boundary `hasattr(obj, name)`, subject
    `unsupported:call:main.py:2:11`, replay target seed
    `main.probe_attribute` request
  - the pair travels through existing `request_replay_payload_fields`
  - the worker consumes only that exact pair and calls
    `main.probe_attribute(1, "bit_length")`
  - existing zero-argument `hasattr` behavior remains preserved
  - `observed_replay_inputs` remains exec/eval-only
- provider support remains intentionally deferred:
  - `src/context_ir/eval_providers.py` was not changed
  - `oracle_signal_hasattr_probe` was not added to the default provider
    fixture map
- no eval assets, public docs/claims, exports, MCP, schema/config, compiler,
  scoring, dynamic-import, runtime-mutation, or generalized provider/runtime
  support was widened
- release state:
  - accepted in workspace: yes, including correction
  - release-unit audit cleared: yes, first-pass after correction
  - full-regression cleared: yes, first-pass with `1678 passed`
  - commit-gating cleared: yes, first-pass
  - locally committed: yes, `2140cf5`
  - pushed: yes, with explicit Ryan authorization
- next route:
  - select the next bounded north-star lane from the pushed exact bridge state

Workspace-only post-`32a4c67` route selection:

- live repo/workspace state was verified:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `32a4c67 Sync hasattr bridge push routing`
  - no source/test/control diff was present before this route-selection update
  - no staged files
  - no untracked files
  - `git diff --check` passed
- route-selection finding:
  - the pushed exact lower-layer `hasattr/2` bridge completed the prerequisite
    for default local-Python subprocess provider support
  - existing `oracle_signal_hasattr_probe` eval assets already define the exact
    fixture source, task, run spec, replay inputs, and normalized payload
  - a live confidence check over the lower exact `hasattr` subprocess path
    passed with `4 passed`
  - provider support remains absent by design:
    `oracle_signal_hasattr_probe` is not in
    `_DEFAULT_LOCAL_PYTHON_SUBPROCESS_FIXTURES`
  - the internal tangible checkpoint currently enumerates the prior seven
    default-subprocess fixtures, so adding provider support should update the
    checkpoint's exact supported fixture list in the same bounded lane
- selected next bounded north-star lane:
  - extend `context_ir_default_local_python_subprocess` to exactly
    `oracle_signal_hasattr_probe`
  - update `context_ir.eval_checkpoint` to include the exact
    `oracle_signal_hasattr_probe` row in the internal checkpoint bundle
- expected exact provider behavior:
  - miss evidence `hasattr(obj, name)`
  - `RuntimeProbeFamily.REFLECTIVE_BUILTIN`
  - form `reflective_builtin:hasattr/2`
  - boundary `hasattr(obj, name)`
  - subject `unsupported:call:main.py:2:11`
  - replay target seed `main.probe_attribute`
  - exact pre-observation replay inputs remain
    `object_type=builtins.int` and `attribute_name=bit_length` through
    `request_replay_payload_fields`
  - normalized payload exactly `attribute_present=true`
  - initial compile remains runtime-fixture-free
  - recompile uses `sys.executable`, `delta_budget=0`, and the real worker
    subprocess invocation
    `(sys.executable, "-m", "context_ir.runtime_probe_worker")`
  - provider-owned runtime provenance comes from the recompiled response
  - unsupported/opaque primary truth remains preserved with additive runtime
    provenance
  - unsupported task IDs remain fail-closed
- selected implementation file scope:
  - `src/context_ir/eval_providers.py`
  - `src/context_ir/eval_checkpoint.py`
  - `tests/test_eval_signal_hasattr_probe.py`
  - `tests/test_eval_checkpoint.py`
  - existing default-subprocess fail-closed wording tests only if needed:
    `tests/test_eval_signal_locals_probe.py`,
    `tests/test_eval_signal_globals_probe.py`,
    `tests/test_eval_signal_vars_zero_probe.py`,
    `tests/test_eval_signal_dir_zero_probe.py`, and
    `tests/test_eval_signal_metaclass_behavior_probe.py`
- out of scope:
  - eval fixtures, eval tasks, committed run specs, public README/EVAL/
    PUBLIC_CLAIMS/ARCHITECTURE updates, package-root exports, MCP, product
    CLI, schema/config, compiler, scoring, dynamic-import, runtime-mutation,
    exec/eval, metaclass, other reflective-builtin forms, generalized
    replay-input support, generalized provider/runtime support, release gate,
    staging, local commit, or push
- release/control state:
  - route selected in workspace-only control state
  - no implementation result has been returned yet
  - no release gate, staging, local commit, or push is authorized from this
    route selection

Workspace-only exact `hasattr` provider/checkpoint acceptance:

- implementation result reviewed findings-first against live repo state and
  accepted first-pass with no findings
- implemented exact `oracle_signal_hasattr_probe` support inside
  `context_ir_default_local_python_subprocess`
- provider behavior:
  - miss evidence is exactly `hasattr(obj, name)`
  - planned request validation remains exact:
    `RuntimeProbeFamily.REFLECTIVE_BUILTIN`,
    `reflective_builtin:hasattr/2`, boundary `hasattr(obj, name)`, subject
    `unsupported:call:main.py:2:11`, and replay target seed
    `main.probe_attribute`
  - exact replay inputs remain `object_type=builtins.int` and
    `attribute_name=bit_length` through `request_replay_payload_fields`
  - normalized payload is exactly `attribute_present=true`
  - initial compile remains runtime-fixture-free
  - recompile uses `sys.executable`, `delta_budget=0`, and the real worker
    subprocess invocation
    `(sys.executable, "-m", "context_ir.runtime_probe_worker")`
  - provider-owned runtime provenance comes from the recompiled response
  - unsupported/opaque primary truth remains preserved with additive runtime
    provenance
  - temporary single-provider run-spec dispatch works without editing
    committed eval assets
  - unsupported task IDs remain fail-closed
- checkpoint behavior:
  - `context_ir.eval_checkpoint` now includes `oracle_signal_hasattr_probe`
    as the eighth exact default-subprocess checkpoint row
  - checkpoint normalized payload for that row is
    `attribute_present=true`
- accepted release unit is exactly:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/eval_providers.py`
  - `src/context_ir/eval_checkpoint.py`
  - `tests/test_eval_signal_hasattr_probe.py`
  - `tests/test_eval_checkpoint.py`
  - `tests/test_eval_signal_locals_probe.py`
  - `tests/test_eval_signal_globals_probe.py`
  - `tests/test_eval_signal_vars_zero_probe.py`
  - `tests/test_eval_signal_dir_zero_probe.py`
  - `tests/test_eval_signal_metaclass_behavior_probe.py`
- validation rerun by control:
  - focused ruff check passed
  - focused ruff format check passed
  - strict mypy over `src/` passed with no issues in `38 source files`
  - requested pytest subset passed with `99 passed`
  - `git diff --check` passed
- program routing decision:
  - after this release unit is audit-cleared, full-regression-cleared,
    commit-gating-cleared, locally committed, and pushed, pause broad
    fixture-by-fixture expansion
  - next program gate after this release is a value checkpoint spike to test
    actual differentiated behavior against simple baselines on a realistic
    coding task
  - if the value checkpoint is weak, pause implementation expansion and run a
    serious research/debug spike before adding more internal fixtures
- release/control state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: no
  - full-regression cleared: no
  - commit-gating cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run dedicated read-only release-unit audit over the exact eleven-file
    release unit before full regression, commit-gating, staging, local commit,
    or push

Workspace-only exact `hasattr` provider/checkpoint release-unit audit clearance:

- dedicated read-only release-unit audit returned PASS
- findings: none
- audit-cleared release unit remains exactly:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/eval_providers.py`
  - `src/context_ir/eval_checkpoint.py`
  - `tests/test_eval_signal_hasattr_probe.py`
  - `tests/test_eval_checkpoint.py`
  - `tests/test_eval_signal_locals_probe.py`
  - `tests/test_eval_signal_globals_probe.py`
  - `tests/test_eval_signal_vars_zero_probe.py`
  - `tests/test_eval_signal_dir_zero_probe.py`
  - `tests/test_eval_signal_metaclass_behavior_probe.py`
- audit evidence:
  - provider support is limited to `oracle_signal_hasattr_probe`
  - exact planned-request identity, replay target, replay inputs, payload
    validation, provider-owned provenance from the recompiled response, and
    fail-closed unsupported-task behavior are preserved
  - checkpoint now enumerates eight exact default-subprocess rows including
    `oracle_signal_hasattr_probe`
  - no eval assets, public docs/claims, exports, MCP, schema/config, compiler,
    scoring, runtime worker, or generalized runtime/provider support surfaces
    were widened
- live repo/workspace state was verified:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `32a4c67 Sync hasattr bridge push routing`
  - no staged files
  - no untracked files
  - dirty set exactly matches the accepted release unit
  - `git diff --check` passed
- release/control state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: no
  - commit-gating cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run full regression before commit-gating, staging, local commit, or push

Workspace-only exact `hasattr` provider/checkpoint full regression clearance:

- full regression gate passed first-pass after release-unit audit clearance
- validation:
  - `.venv/bin/python -m ruff check src/ tests/` passed
  - `.venv/bin/python -m ruff format --check src/ tests/` passed with
    `112 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed with no issues in
    `38 source files`
  - `.venv/bin/python -m pytest tests/ -v` passed with `1681 passed`
- release/control state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass
  - commit-gating cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run commit-gating review over the exact eleven-file release unit before
    staging, local commit, or push

Workspace-only exact `hasattr` provider/checkpoint commit-gating clearance:

- commit-gating review passed first-pass with no findings
- commit-gating evidence:
  - dirty file set exactly matches the accepted eleven-file release unit
  - no staged files were present during review
  - no untracked files were present during review
  - local `HEAD` and `origin/main` both resolved to
    `32a4c67 Sync hasattr bridge push routing`
  - `git diff --check` passed
  - provider diff is limited to exact `oracle_signal_hasattr_probe`
    fixture-map support and fail-closed support-list wording
  - checkpoint diff is limited to adding the exact
    `oracle_signal_hasattr_probe` checkpoint row and expected payload
  - tests cover exact request identity, replay inputs, real subprocess
    invocation, provider-owned runtime provenance, run-spec dispatch, and
    unsupported-task fail-closed behavior
  - no eval assets, public docs/claims, package-root exports, MCP,
    schema/config, compiler, scoring, runtime worker, runtime execution,
    runtime observation recompile, tool facade, or generalized runtime/provider
    support surfaces have diffs
- release/control state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass
  - commit-gating cleared: yes, first-pass
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - stage exactly the eleven-file release unit and create a local release
    commit
  - do not push without explicit Ryan authorization

Locally committed exact `hasattr` provider/checkpoint release:

- local release commit:
  - `3fb8b15 Add hasattr default subprocess eval provider`
- committed release unit:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/eval_providers.py`
  - `src/context_ir/eval_checkpoint.py`
  - `tests/test_eval_signal_hasattr_probe.py`
  - `tests/test_eval_checkpoint.py`
  - `tests/test_eval_signal_locals_probe.py`
  - `tests/test_eval_signal_globals_probe.py`
  - `tests/test_eval_signal_vars_zero_probe.py`
  - `tests/test_eval_signal_dir_zero_probe.py`
  - `tests/test_eval_signal_metaclass_behavior_probe.py`
- live repo/workspace state immediately after local commit:
  - branch `main`
  - local `HEAD` resolves to `3fb8b15`
  - `origin/main` resolves to `32a4c67 Sync hasattr bridge push routing`
  - branch is ahead of `origin/main` by one commit before this continuity sync
  - no staged files
  - no untracked files
- release/control state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass
  - commit-gating cleared: yes, first-pass
  - locally committed: yes, `3fb8b15`
  - pushed: no
- next route:
  - push the local release commit only after explicit Ryan authorization
  - do not route `3fb8b15` back to release-unit audit, full regression,
    commit-gating, staging, or local commit creation absent new findings
  - after this release is pushed, proceed to the value checkpoint spike rather
    than broad fixture-by-fixture expansion

Pushed internal default local-Python subprocess dir-zero eval provider release:
`686dd18 Add dir-zero default subprocess eval provider`. This commit contains
the accepted exact `oracle_signal_dir_zero_probe` support inside the internal
`context_ir_default_local_python_subprocess` provider. It is pushed with
explicit Ryan authorization and must not be routed back to release-unit audit,
full regression, commit-gating, staging, local commit, or push absent new
findings.

Pushed dir-zero provider release evidence:

- live repo/workspace state was verified after push:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `bda2800 Sync dir-zero provider release routing`
  - no source/test/control diff remains
  - no staged files
  - no untracked files
  - `git diff --check` passed
- implemented bounded north-star lane:
  - extend the existing internal
    `context_ir_default_local_python_subprocess` provider to exactly
    `oracle_signal_dir_zero_probe`
- release evidence:
  - exact fixture-map support added for `oracle_signal_dir_zero_probe`
  - provider validation requires miss evidence `dir()`,
    `RuntimeProbeFamily.REFLECTIVE_BUILTIN`, `reflective_builtin:dir/0`,
    boundary `dir()`, subject `unsupported:call:main.py:2:11`, replay target
    seed `main.probe_directory`, one planned request, one runner attempt, one
    observed result, and normalized payload `listing_entry_count=0`
  - initial compile remains runtime-fixture-free
  - recompile uses `sys.executable`, `delta_budget=0`, and the real
    subprocess invocation `(sys.executable, "-m",
    "context_ir.runtime_probe_worker")`
  - provider-owned runtime provenance comes from the recompiled response
  - unsupported/opaque primary truth remains preserved with additive runtime
    provenance
  - temporary single-provider run-spec dispatch works without editing
    committed eval assets
  - unsupported task IDs remain fail-closed
  - no eval fixture, task, committed run-spec, public docs/claims, export, MCP,
    schema/config, scoring, compiler, runtime worker, probe-form,
    dynamic-import, runtime-mutation, exec/eval, metaclass, other
    reflective-builtin form, or generalized provider/runtime support files
    changed
- release state: accepted, release-unit-audit-cleared,
  full-regression-cleared, commit-gating-cleared, locally committed, and
  pushed with explicit Ryan authorization
- next route:
  - route the Ryan-authorized tangible north-star checkpoint before continuing
    broad fixture-by-fixture provider expansion
  - do not route `686dd18` or `bda2800` back to release-unit audit, full
    regression, commit-gating, staging, local commit, or push absent new
    findings

Pushed internal tangible runtime-evidence checkpoint release:

- live repo/workspace state was verified after push:
  - branch `main`
  - local `HEAD` and `origin/main` both resolved to
    `2afe7a9 Sync checkpoint local release routing`
  - no source/test/control diff remained before this post-push continuity sync
  - no staged files
  - no untracked files
  - `git diff --check` passed
- pushed release/source-contract authority:
  - `8b6923a Add tangible runtime evidence checkpoint`
- pushed control-state authority:
  - `2afe7a9 Sync checkpoint local release routing`
- pushed release evidence:
  - added internal `context_ir.eval_checkpoint` module
  - provides `python -m context_ir.eval_checkpoint --output-dir <dir>`
  - writes generated output-local `run_spec.json`, `ledger.jsonl`,
    `report.md`, `manifest.json`, and `checkpoint.md`
  - reuses existing eval bundle/pipeline/report/manifest machinery
  - fails closed when target artifact files already exist
  - checkpoint scope is exactly the seven currently supported
    `context_ir_default_local_python_subprocess` fixtures at budget `100`:
    locals, globals, vars-zero, dir-zero, exec, eval, and metaclass behavior
  - public docs/claims, package-root exports, console scripts, committed eval
    assets, provider/runtime support, compiler, scoring, MCP, schema/config,
    and semantic support were not widened
- release state: accepted, release-unit-audit-cleared,
  full-regression-cleared, commit-gating-cleared, locally committed, and
  pushed with explicit Ryan authorization
- next route:
  - select the next bounded north-star lane from the pushed checkpoint state
  - do not route `8b6923a` or `2afe7a9` back to release-unit audit, full
    regression, commit-gating, staging, local commit, or push absent new
    findings

Workspace-only post-`13d5472` route selection:

- live repo/workspace state was verified:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `13d5472 Sync checkpoint push routing`
  - no source/test/control diff was present before this route-selection update
  - no staged files
  - no untracked files
  - `git diff --check` passed
- route-selection finding:
  - the pushed checkpoint gives a tangible seven-probe artifact over the exact
    default local-Python subprocess provider fixtures already supported
  - the next provider-expansion candidates are not simple fixture-map-only
    siblings
  - read-only dry runs for exact non-zero reflective-builtin and
    runtime-mutation candidates planned one correct request each, then returned
    non-proof crashed subprocess results with return code `78`
  - checked candidates included `oracle_signal_hasattr_probe`,
    `oracle_signal_getattr_probe`, `oracle_signal_getattr_default_probe`,
    `oracle_signal_getattr_default_value_probe`,
    `oracle_signal_vars_probe`, `oracle_signal_dir_probe`,
    `oracle_signal_setattr_probe`, and `oracle_signal_delattr_probe`
  - those forms need a deliberate replay-input contract for exact non-zero
    argument replay; the current observed replay-input validation is explicitly
    scoped to exact exec/eval source proof
  - dynamic-import candidates remain less ready for the default provider route:
    simple ABSENT_SYMBOL dry runs for `importlib.import_module(name)` and
    `__import__(name)` produced no planned requests in this check
- selected next bounded north-star lane:
  - run one read-only contract/decomposition spike for exact non-zero replay
    inputs in the default local-Python subprocess path
  - use `oracle_signal_hasattr_probe` / `reflective_builtin:hasattr/2` as the
    first pilot candidate because it is the smallest non-zero reflective form
    with existing fixture replay inputs and a boolean payload
- required spike output:
  - decide the smallest safe implementation slice for the replay-input bridge
  - identify exact files/tests to change
  - state whether `oracle_signal_hasattr_probe` provider support can be in the
    same implementation slice or must follow after the bridge
  - preserve runtime-fixture-free initial compile, unsupported/opaque primary
    truth, additive runtime provenance, no public claim widening, and
    fail-closed unsupported task IDs
- release/control state:
  - route selected in workspace-only control state
  - no implementation is authorized before the read-only spike returns
  - no release gate, staging, local commit, or push is authorized from this
    route selection

Workspace-only exact `hasattr/2` non-zero replay-input bridge spike
acceptance:

- read-only spike result reviewed against live repo state and accepted
  first-pass
- spike findings:
  - the crash is not a provider fixture-map problem yet
  - the lower default subprocess path plans the exact
    `reflective_builtin:hasattr/2` request, but runner preparation only
    materializes request identity fields into `request_replay_payload_fields`
  - the existing worker has an exact `hasattr/2` handler, but its observation
    path assumes a zero-argument target and calls `target()`
  - the actual `oracle_signal_hasattr_probe` target is
    `probe_attribute(obj, name)` and the fixture replay inputs are exactly
    `object_type=builtins.int` and `attribute_name=bit_length`
  - `observed_replay_inputs` is the wrong seam because it is post-observation
    proof and remains intentionally fail-closed to exact exec/eval source proof
- selected implementation lane:
  - implement one lower-layer bridge for pre-observation request replay inputs
    for exactly `oracle_signal_hasattr_probe` /
    `reflective_builtin:hasattr/2`
  - append exactly `object_type=builtins.int` and
    `attribute_name=bit_length` to the request replay fields
  - pass those fields through the existing default local-Python subprocess
    request payload path
  - consume only that exact pair in the worker and call
    `main.probe_attribute(1, "bit_length")`
  - preserve the existing zero-argument `hasattr` behavior covered by
    lower-layer tests
  - keep `observed_replay_inputs` unchanged and exec/eval-only
  - defer adding `oracle_signal_hasattr_probe` to
    `_DEFAULT_LOCAL_PYTHON_SUBPROCESS_FIXTURES`
- implementation file scope:
  - `src/context_ir/runtime_probe_execution.py`
  - `src/context_ir/runtime_probe_worker.py`
  - `src/context_ir/runtime_observation_recompile.py`
  - `src/context_ir/tool_facade.py`
  - `tests/test_runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
  - `tests/test_runtime_observation_recompile.py`
  - `tests/test_tool_facade.py`
- out of scope:
  - `src/context_ir/eval_providers.py`
  - `tests/test_eval_signal_hasattr_probe.py`
  - all `evals/fixtures`, `evals/tasks`, and committed run specs
  - README, ARCHITECTURE, EVAL, PUBLIC_CLAIMS, package-root exports, MCP,
    CLI, schema/config, compiler, scoring, dynamic-import, generalized
    reflective-builtin support, generalized runtime-mutation support, and
    generalized provider/runtime behavior
- release/control state:
  - spike accepted in workspace-only control state
  - implementation route selected in workspace-only control state
  - no implementation result has been returned yet
  - no release gate, staging, local commit, or push is authorized from this
    route selection

Workspace-only exact `hasattr/2` non-zero replay-input bridge acceptance:

- implementation result reviewed findings-first against live repo state and
  accepted first-pass with no findings
- implemented the lower-layer exact replay-input bridge for only the
  `oracle_signal_hasattr_probe` / `reflective_builtin:hasattr/2` pilot
- bridge behavior:
  - parent runtime-probe execution appends exactly
    `object_type=builtins.int` and `attribute_name=bit_length` to
    `request_replay_payload_fields` only for the exact request identity:
    `RuntimeProbeFamily.REFLECTIVE_BUILTIN`,
    `reflective_builtin:hasattr/2`, boundary `hasattr(obj, name)`, subject
    `unsupported:call:main.py:2:11`, and replay target seed
    `main.probe_attribute`
  - those fields travel through runner request, invocation, transport, and
    worker payload via the existing `request_replay_payload_fields` path
  - the worker consumes only that exact pair to call
    `main.probe_attribute(1, "bit_length")`
  - wrong, missing, duplicate, or extra replay-input keys for the exact pilot
    are rejected
  - existing zero-argument `hasattr` worker behavior remains covered and
    preserved
  - `observed_replay_inputs` remains unchanged and exec/eval-only
- provider support remains intentionally deferred:
  - `src/context_ir/eval_providers.py` was not changed
  - `oracle_signal_hasattr_probe` was not added to
    `_DEFAULT_LOCAL_PYTHON_SUBPROCESS_FIXTURES`
- accepted release unit is exactly:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/runtime_probe_execution.py`
  - `src/context_ir/runtime_probe_worker.py`
  - `tests/test_runtime_observation_recompile.py`
  - `tests/test_runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
  - `tests/test_tool_facade.py`
- validation rerun by control:
  - focused ruff check passed
  - focused ruff format check passed
  - strict mypy over the requested source files passed
  - targeted pytest passed with `69 passed, 781 deselected`
  - `git diff --check` passed
- release/control state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: failed, one finding
  - full-regression cleared: no
  - commit-gating cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - issue one narrow correction for the stale
    `runtime_probe_worker.py` exact-hasattr observation docstring
  - rerun focused validation after the correction
  - rerun the dedicated read-only release-unit audit from the top before full
    regression, commit-gating, staging, local commit, or push

Release-unit audit failure for exact `hasattr/2` non-zero replay-input bridge:

- dedicated read-only release-unit audit returned FAIL with one finding:
  - `src/context_ir/runtime_probe_worker.py` has a stale docstring at the exact
    hasattr observation helper, still saying "Observe one zero-argument target"
    even though this release unit now routes the exact replay-input pilot
    through `target_args` and can call
    `main.probe_attribute(1, "bit_length")`
- audit stopped on first finding, as required
- scope boundary before audit stop:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `13d5472 Sync checkpoint push routing`
  - no staged files
  - no untracked files
  - dirty set exactly matches the eight accepted release-unit files
- release/control state:
  - accepted in workspace: yes, but release held on audit finding
  - release-unit audit cleared: no
  - full-regression cleared: no
  - commit-gating cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run one narrow correction slice for the stale docstring only
  - rerun focused validation
  - rerun release-unit audit from the top

Workspace-only exact `hasattr/2` audit-finding correction acceptance:

- narrow correction reviewed findings-first against live repo state and
  accepted first-pass with no findings
- corrected finding:
  - the exact hasattr observation helper docstring no longer says it observes
    only one zero-argument target
  - it now covers both preserved zero-argument behavior and exact pilot replay
    inputs
  - no runtime behavior change was introduced by the correction
- live repo/workspace state was verified:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `13d5472 Sync checkpoint push routing`
  - no staged files
  - no untracked files
  - dirty set remains exactly the eight accepted release-unit files
  - `git diff --check` passed
- validation rerun by control:
  - focused ruff check on `src/context_ir/runtime_probe_worker.py` passed
  - focused ruff format check on `src/context_ir/runtime_probe_worker.py`
    passed
  - strict mypy on `src/context_ir/runtime_probe_worker.py` passed
  - `pytest tests/test_runtime_probe_worker.py -k "hasattr" -v` passed with
    `37 passed, 421 deselected`
- release/control state:
  - accepted in workspace: yes, including correction
  - release-unit audit cleared: no, rerun required from the top
  - full-regression cleared: no
  - commit-gating cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - rerun the dedicated read-only release-unit audit over the exact eight-file
    release unit from the top before full regression, commit-gating, staging,
    local commit, or push

Workspace-only exact `hasattr/2` release-unit audit clearance:

- rerun dedicated read-only release-unit audit returned PASS
- findings: none
- audit-cleared release unit remains exactly:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/runtime_probe_execution.py`
  - `src/context_ir/runtime_probe_worker.py`
  - `tests/test_runtime_observation_recompile.py`
  - `tests/test_runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
  - `tests/test_tool_facade.py`
- audit evidence:
  - prior stale-docstring finding is corrected
  - bridge remains exact to `oracle_signal_hasattr_probe` /
    `reflective_builtin:hasattr/2`
  - exact replay inputs remain `object_type=builtins.int` and
    `attribute_name=bit_length` through `request_replay_payload_fields`
  - worker consumption maps the exact pilot to
    `main.probe_attribute(1, "bit_length")`
  - zero-argument `hasattr` behavior remains covered and preserved
  - `observed_replay_inputs` remains exec/eval-only
  - no eval provider support, public docs/claims, eval assets, exports, MCP,
    schema/config, compiler, scoring, dynamic-import, runtime-mutation, or
    generalized provider/runtime support was widened
- live repo/workspace state was verified:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `13d5472 Sync checkpoint push routing`
  - no staged files
  - no untracked files
  - dirty set remains exactly the eight accepted release-unit files
  - `git diff --check` passed
- release/control state:
  - accepted in workspace: yes, including correction
  - release-unit audit cleared: yes, first-pass after correction
  - full-regression cleared: no
  - commit-gating cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run full regression before commit-gating, staging, local commit, or push

Workspace-only exact `hasattr/2` full regression clearance:

- full regression gate passed first-pass
- commands:
  - `ruff check src/ tests/` passed
  - `ruff format --check src/ tests/` passed with `112 files already
    formatted`
  - `mypy --strict src/` passed with no issues in `38 source files`
  - `pytest tests/ -v` passed with `1678 passed`
- release/control state:
  - accepted in workspace: yes, including correction
  - release-unit audit cleared: yes, first-pass after correction
  - full-regression cleared: yes, first-pass
  - commit-gating cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run commit-gating review over the exact eight-file release unit before
    staging, local commit, or push

Workspace-only exact `hasattr/2` commit-gating clearance:

- commit-gating review passed first-pass with no findings
- commit-gated release unit remains exactly:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/runtime_probe_execution.py`
  - `src/context_ir/runtime_probe_worker.py`
  - `tests/test_runtime_observation_recompile.py`
  - `tests/test_runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
  - `tests/test_tool_facade.py`
- commit-gating evidence:
  - dirty set exactly matches the audit-cleared and full-regression-cleared
    release unit
  - no staged files
  - no untracked files
  - `git diff --check` passed
  - no eval provider support, eval assets, public docs/claims, exports, MCP,
    schema/config, compiler, scoring, dynamic-import, runtime-mutation, or
    generalized provider/runtime widening
- release/control state:
  - accepted in workspace: yes, including correction
  - release-unit audit cleared: yes, first-pass after correction
  - full-regression cleared: yes, first-pass
  - commit-gating cleared: yes, first-pass
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - stage the exact eight-file release unit and create the local release commit
  - push remains Ryan-gated

Workspace-only post-`65cf927` tangible north-star checkpoint route selection:

- live repo/workspace state was verified:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `65cf927 Sync dir-zero provider push routing`
  - no source/test/control diff remains before this route-selection update
  - no staged files
  - no untracked files
  - `git diff --check` passed
- selected next bounded north-star lane:
  - add an internal tangible runtime-evidence checkpoint command/module
- rationale:
  - Ryan explicitly asked to start seeing inspectable results after the
    foundation work
  - existing internal eval bundle, pipeline, report, summary, manifest, and
    run-spec machinery are already present and tested
  - exact default local-Python subprocess provider support is now pushed for
    locals, globals, vars-zero, dir-zero, exec, eval, and metaclass behavior
  - the smallest useful checkpoint is a generated internal artifact bundle
    over those accepted exact provider fixtures, not new runtime semantics
- selected checkpoint shape:
  - a `python -m context_ir.eval_checkpoint --output-dir ...` run path
  - generated `run_spec.json`, `ledger.jsonl`, `report.md`, `manifest.json`,
    and compact `checkpoint.md` artifacts in the caller-selected output
    directory
  - a compact evidence table showing the exact supported probes and payloads
  - an explicit unsupported/remaining-gap statement
- non-goals for the selected lane:
  - no public claim widening or benchmark claim
  - no README, EVAL, PUBLIC_CLAIMS, or ARCHITECTURE update
  - no package-root export or product CLI/console-script addition
  - no eval fixture, task, or committed run-spec change
  - no new runtime-probe form, runtime worker, compiler, scoring, MCP,
    schema/config, dynamic-import, runtime-mutation, exec/eval, metaclass,
    reflective-builtin semantics, or generalized runtime/provider support
    change
- release/control state:
  - route selected in workspace-only control state
  - no implementation result has been returned yet
  - no release gate, staging, local commit, or push is authorized from this
    route selection

Workspace-only tangible runtime checkpoint acceptance:

- implementation result reviewed findings-first against live repo state and
  accepted first-pass with no findings
- added internal `context_ir.eval_checkpoint` module with:
  - `python -m context_ir.eval_checkpoint --output-dir <dir>` run path
  - generated output-local `run_spec.json`
  - existing eval bundle/pipeline/report/manifest reuse
  - `ledger.jsonl`, `report.md`, `manifest.json`, and compact
    `checkpoint.md` artifacts
  - fail-closed protection when target artifact files already exist
- checkpoint scope is exactly the currently supported
  `context_ir_default_local_python_subprocess` fixtures at budget `100`:
  - `oracle_signal_locals_probe`
  - `oracle_signal_globals_probe`
  - `oracle_signal_vars_zero_probe`
  - `oracle_signal_dir_zero_probe`
  - `oracle_signal_exec_probe`
  - `oracle_signal_eval_probe`
  - `oracle_signal_metaclass_behavior_probe`
- `checkpoint.md` includes:
  - internal-checkpoint / not-public-benchmark caveat
  - artifact path table
  - exact supported-probe evidence table with normalized payloads
  - unsupported/remaining-gap statement
- no public docs/claims, package-root export, console-script/product CLI, eval
  fixture, task, committed run-spec, runtime worker, runtime-probe form,
  compiler, scoring, MCP, schema/config, dynamic-import, runtime-mutation,
  exec/eval, metaclass, reflective-builtin semantic widening, or generalized
  runtime/provider support changed
- accepted release unit is exactly:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/eval_checkpoint.py`
  - `tests/test_eval_checkpoint.py`
- validation rerun by control:
  - requested ruff check passed
  - requested ruff format check passed
  - `.venv/bin/python -m mypy --strict src/` passed with no issues in
    38 source files
  - requested pytest subset passed with `69 passed`
  - fresh module run succeeded under
    `/private/tmp/context-ir-eval-checkpoint.review.XwUNGH`
  - generated checkpoint contained seven supported-probe evidence rows and the
    required internal-only/remaining-gap language
  - `git diff --check` passed
- dedicated read-only release-unit audit passed first-pass with no findings:
  - release unit exactly matched the four requested paths
  - no staged files
  - new module and test remained untracked before staging, as expected
  - no README, EVAL, PUBLIC_CLAIMS, ARCHITECTURE, package-root export, console
    script, eval asset, provider/runtime, compiler, scoring, MCP,
    schema/config, or semantic-widening changes were detected
  - audit reran `git diff --check`, focused ruff check, focused ruff format
    check, strict mypy with cache outside the repo, focused pytest with
    `3 passed`, a fresh module run producing all five artifacts and seven
    ledger rows, and a same-output-dir rerun proving fail-closed behavior
- full regression passed first-pass:
  - `.venv/bin/python -m ruff check src/ tests/` passed
  - `.venv/bin/python -m ruff format --check src/ tests/` passed
  - `.venv/bin/python -m mypy --strict src/` passed with no issues in
    38 source files
  - `.venv/bin/python -m pytest tests/ -v` passed with `1665 passed`
  - `git diff --check` passed
- commit-gating passed first-pass with no findings:
  - live repo/workspace state was verified before the gate
  - branch was `main`
  - local `HEAD` and `origin/main` both resolved to
    `65cf927 Sync dir-zero provider push routing`
  - dirty set exactly matched the four-file release unit
  - staged files: none
  - untracked files were exactly the new checkpoint module and test
  - no README, EVAL, PUBLIC_CLAIMS, ARCHITECTURE, package-root export,
    console script, committed eval asset, provider/runtime, compiler,
    scoring, MCP, schema/config, or semantic-widening changes were present
  - source review confirmed the checkpoint remains internal, output-local,
    fail-closed on existing artifacts, and bounded to the seven exact
    default local-Python subprocess provider fixtures at budget `100`
  - test review confirmed coverage for generated run-spec shape, ledger rows,
    exact normalized payloads, artifact rendering, fail-closed behavior, and
    package-root/public-surface non-widening
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass
  - commit-gating cleared: yes, first-pass
  - staged: completed as part of local release commit
  - locally committed: yes, `8b6923a Add tangible runtime evidence checkpoint`
  - pushed: no
- next route:
  - await explicit Ryan authorization before pushing the local tangible runtime
    checkpoint release
  - do not push without explicit Ryan authorization

Pushed dir-zero evidence correction release:

- live repo/workspace state was verified after push:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `accdb89 Sync dir-zero correction release routing`
  - no source/test/control diff remains
  - no staged files
  - no untracked files
  - `git diff --check` passed
- pushed release/source-contract authority:
  - `c3e08c4 Correct dir-zero eval runtime evidence`
- pushed control-state authority:
  - `accdb89 Sync dir-zero correction release routing`
- release evidence:
  - corrected runtime evidence and active claim docs from
    `listing_entry_count=3` to `listing_entry_count=0`
  - direct fixture execution prints `dir:0`
  - focused tests prove exact default local-Python subprocess facade planning
    for `RuntimeProbeFamily.REFLECTIVE_BUILTIN`,
    `reflective_builtin:dir/0`, boundary `dir()`, subject
    `unsupported:call:main.py:2:11`, replay target seed
    `main.probe_directory`, and observed payload `listing_entry_count=0`
  - focused tests prove
    `context_ir_default_local_python_subprocess` remains fail-closed for
    `oracle_signal_dir_zero_probe`
  - no provider source, runtime worker, schema, MCP, run-spec, task, fixture
    source, or generalized support files changed
- release state: accepted, release-unit-audit-cleared,
  full-regression-cleared, commit-gating-cleared, locally committed, and
  pushed with explicit Ryan authorization
- do not route `c3e08c4` or `accdb89` back to release-unit audit, full
  regression, commit-gating, staging, local commit, or push absent new
  findings

Workspace-only post-`accdb89` route selection:

- live repo/workspace state was verified:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `accdb89 Sync dir-zero correction release routing`
  - no source/test/control diff remains before this route-selection update
  - no staged files
  - no untracked files
  - `git diff --check` passed
- route-selection finding:
  - the committed continuity before this workspace-only update still described
    the dir-zero correction as awaiting push and still named `0650bb8` as the
    current pushed authority
  - live git refs supersede that stale pre-push routing text, and this
    workspace-only control-state update records the corrected active route
- selected next bounded north-star lane:
  - extend the internal
    `context_ir_default_local_python_subprocess` provider to support exactly
    `oracle_signal_dir_zero_probe`
- rationale:
  - the pushed dir-zero correction resolved the prior
    fixture/runtime truth mismatch
  - lower-layer exact `reflective_builtin:dir/0` local-Python subprocess
    support is already pushed and reverified by the focused dir-zero tests
  - the existing default local-Python subprocess facade plans exactly
    `RuntimeProbeFamily.REFLECTIVE_BUILTIN`, `reflective_builtin:dir/0`,
    boundary `dir()`, subject `unsupported:call:main.py:2:11`, and replay
    target seed `main.probe_directory`
  - the same facade observes normalized payload
    `listing_entry_count=0`
  - the provider currently remains fail-closed for
    `oracle_signal_dir_zero_probe`, making exact provider support the smallest
    next bounded lane
- non-goals for the selected lane:
  - no eval fixture, task, or committed run-spec changes
  - no public docs/claims, package-root exports, MCP, schema/config, scoring,
    compiler, runtime worker, runtime-probe form, dynamic-import,
    runtime-mutation, exec/eval, metaclass, other reflective-builtin forms, or
    generalized runtime/provider support change
- release/control state:
  - route selected in workspace-only control state
  - no implementation result has been returned yet
  - no release gate, staging, local commit, or push is authorized from this
    route selection

Ryan-authorized tangible north-star checkpoint direction:

- Ryan explicitly requested a tangible checkpoint after roughly two weeks of
  careful foundation work so the program starts producing an inspectable
  result, not only internal proof machinery
- this does not interrupt the in-flight exact
  `oracle_signal_dir_zero_probe` provider-support lane
- after that lane returns and is reviewed under the normal quality gate, the
  next control route should favor a bounded tangible checkpoint before
  continuing broad fixture-by-fixture provider expansion
- acceptable checkpoint shapes include:
  - one command or run path that exercises the supported runtime-backed
    eval/provider set
  - a compact evidence table showing what Context IR now proves
  - a small fixture-demo walkthrough showing static unsupported/opaque truth
    plus additive runtime-backed provenance
  - a clear unsupported/remaining-gap statement
- checkpoint constraints:
  - no public claim widening without evidence and review
  - no generalized runtime-analysis claim unless implemented and proven
  - no release-gate bypass for the in-flight provider lane

Workspace-only exact `oracle_signal_dir_zero_probe` provider-support
acceptance:

- implementation result reviewed findings-first against live repo state and
  accepted first-pass with no findings
- added exact fixture-map support for `oracle_signal_dir_zero_probe` inside
  `context_ir_default_local_python_subprocess`
- provider validation now requires:
  - miss evidence `dir()`
  - `RuntimeProbeFamily.REFLECTIVE_BUILTIN`
  - `reflective_builtin:dir/0`
  - boundary `dir()`
  - subject `unsupported:call:main.py:2:11`
  - replay target seed `main.probe_directory`
  - one planned request, one runner attempt, one observed result
  - normalized payload `listing_entry_count=0`
- tests prove:
  - the initial compile remains runtime-fixture-free
  - recompile uses `sys.executable`, `delta_budget=0`, and the real
    subprocess invocation `(sys.executable, "-m",
    "context_ir.runtime_probe_worker")`
  - provider-owned runtime provenance comes from the recompiled response
  - unsupported/opaque primary truth remains preserved with additive runtime
    provenance
  - temporary single-provider run-spec dispatch works without editing
    committed eval assets
  - unsupported task IDs remain fail-closed
- accepted release unit is exactly:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/eval_providers.py`
  - `tests/test_eval_signal_dir_zero_probe.py`
  - `tests/test_eval_signal_locals_probe.py`
  - `tests/test_eval_signal_globals_probe.py`
  - `tests/test_eval_signal_vars_zero_probe.py`
  - `tests/test_eval_signal_metaclass_behavior_probe.py`
- validation rerun by control:
  - requested ruff check passed
  - requested ruff format check passed
  - `.venv/bin/python -m mypy --strict src/` passed
  - requested pytest subset passed with `101 passed`
  - `git diff --check` passed
- dedicated read-only release-unit audit passed first-pass with no findings:
  - workspace diff exactly matched the eight-file release unit
  - no staged files
  - no untracked files
  - scope stayed inside exact dir-zero provider support and fail-closed test
    wording updates
  - no eval fixtures, tasks, committed run specs, public docs/claims, exports,
    MCP, schema/config, scoring, compiler, runtime worker, probe-form,
    dynamic-import, runtime-mutation, exec/eval, metaclass, or generalized
    provider/runtime support changes were present
  - audit reran `git diff --check`, focused ruff check, focused ruff format
    check, strict mypy, and focused pytest with `46 passed`
- full regression passed first-pass:
  - `.venv/bin/python -m ruff check src/ tests/` passed
  - `.venv/bin/python -m ruff format --check src/ tests/` passed with
    `110 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed with no issues in
    37 source files
  - `.venv/bin/python -m pytest tests/ -v` passed with `1662 passed`
  - `git diff --check` passed
- commit-gating passed first-pass with no findings:
  - dirty set exactly matched the eight-file release unit
  - no staged files
  - no untracked files
  - no eval fixtures, tasks, committed run specs, public docs/claims, exports,
    MCP, schema/config, scoring, compiler, runtime worker, probe-form,
    dynamic-import, runtime-mutation, exec/eval, metaclass, or generalized
    provider/runtime support files changed
  - exact dir-zero provider support is limited to the fixture map and
    fail-closed wording updates
  - `git diff --check` passed
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass
  - commit-gating cleared: yes, first-pass
  - staged: completed as part of local release commit
  - locally committed: yes,
    `686dd18 Add dir-zero default subprocess eval provider`
  - pushed: yes, with release routing through
    `bda2800 Sync dir-zero provider release routing`
- next route:
  - route toward the Ryan-authorized tangible north-star checkpoint before
    continuing broad fixture-by-fixture provider expansion
  - do not route `686dd18` or `bda2800` back to release-unit audit, full
    regression, commit-gating, staging, local commit creation, or push absent
    new findings

Pushed internal default local-Python subprocess metaclass eval provider release:
`0650bb8 Add metaclass default subprocess eval provider`. This commit contains
the accepted exact `oracle_signal_metaclass_behavior_probe` support inside the
internal `context_ir_default_local_python_subprocess` provider. It is pushed
with explicit Ryan authorization and must not be routed back to release-unit
audit, full regression, commit-gating, staging, local commit, or push absent
new findings.

Pushed metaclass provider release evidence:

- live repo/workspace state was verified after push:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `0650bb8 Add metaclass default subprocess eval provider`
  - no source/test/control diff remains
  - no staged files
  - no untracked files
  - `git diff --check` passed
- implemented bounded north-star lane:
  - extend the existing internal
    `context_ir_default_local_python_subprocess` provider to exactly
    `oracle_signal_metaclass_behavior_probe`
- rationale:
  - the pushed provider now supports exact locals/globals/vars-zero/exec/eval
    fixtures
  - lower-layer exact `metaclass_behavior:keyword` local-Python subprocess
    support is already pushed
  - the metaclass eval fixture already exists with a stable unsupported
    `metaclass=Meta` boundary and additive runtime provenance contract
  - a read-only control dry run planned exactly
    `RuntimeProbeFamily.METACLASS_BEHAVIOR`, `metaclass_behavior:keyword`,
    boundary `metaclass=Meta`, subject
    `unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1`, and replay
    target seed `main.Example`
  - the same dry run through the default local-Python subprocess facade emitted
    normalized payload `class_creation_outcome=created_class`,
    `created_class_qualified_name=main.Example`, and
    `selected_metaclass_qualified_name=main.Meta`
- non-goals for the selected lane:
  - no run-spec asset or fixture changes
  - no provider support beyond exact `oracle_signal_metaclass_behavior_probe`
  - no public docs/claims, package-root exports, MCP, run-spec schema/config,
    scoring, compiler, runtime worker, runtime-probe form, dynamic-import,
    reflective-builtin, runtime-mutation, exec/eval, or generalized
    runtime/provider support change
- implementation is accepted in workspace first-pass with no findings:
  - exact metaclass fixture-map support is added to
    `context_ir_default_local_python_subprocess`
  - provider validation requires the planned request to match
    `RuntimeProbeFamily.METACLASS_BEHAVIOR`, `metaclass_behavior:keyword`,
    boundary `metaclass=Meta`, subject
    `unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1`, and
    replay target seed `main.Example`
  - initial compile remains runtime-fixture-free, recompile uses
    `sys.executable` and `delta_budget=0`, one planned request, one runner
    attempt, one observed result, and provider-owned runtime provenance from
    the recompiled response
  - normalized payload is exactly
    `class_creation_outcome=created_class`,
    `created_class_qualified_name=main.Example`, and
    `selected_metaclass_qualified_name=main.Meta`
  - unsupported/opaque primary truth remains preserved, additive runtime
    provenance is attached, and `def:main.py:main.Meta` is not selected
  - focused validation passed: ruff check, ruff format check, strict mypy,
    targeted pytest with `77 passed`, and clean `git diff --check`
- accepted release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/eval_providers.py`,
  `tests/test_eval_signal_metaclass_behavior_probe.py`,
  `tests/test_eval_signal_locals_probe.py`,
  `tests/test_eval_signal_globals_probe.py`, and
  `tests/test_eval_signal_vars_zero_probe.py`
- release state: accepted, release-unit-audit-cleared,
  full-regression-cleared, commit-gating-cleared, locally committed, and
  pushed at `0650bb8 Add metaclass default subprocess eval provider`
- dedicated read-only release-unit audit passed first-pass with no findings
- full regression passed first-pass: ruff check, ruff format check, strict
  mypy, full pytest with `1657 passed`, and clean final `git diff --check`
- commit-gating passed first-pass with no findings
- workspace-only post-`0650bb8` route-selection findings:
  - local control state has one docs-only continuity commit ahead of
    `origin/main`; the pushed source/contract authority remains
    `0650bb8 Add metaclass default subprocess eval provider`
  - a read-only control dry run rejected exact
    `oracle_signal_dir_zero_probe` provider support as the immediate next
    implementation lane: the existing default local-Python subprocess facade
    plans `RuntimeProbeFamily.REFLECTIVE_BUILTIN`,
    `reflective_builtin:dir/0`, boundary `dir()`, subject
    `unsupported:call:main.py:2:11`, and replay target seed
    `main.probe_directory`, but the live subprocess payload is
    `listing_entry_count=0` while the committed eval fixture expects
    `listing_entry_count=3`; direct fixture execution also returns `dir:0`
  - read-only dry runs for remaining non-zero reflective-builtin and
    runtime-mutation fixtures plan to exact lower-layer forms but do not
    produce observed results through the runtime-fixture-free default facade
    because the planned requests have no observed replay inputs
  - read-only dry runs for remaining dynamic-import fixtures plan to exact
    lower-layer forms but return non-proof crashed subprocess results through
    the same default facade
- release/control state:
  - Ryan approved advancing from the route-selection hold on 2026-05-15
  - no provider implementation prompt is currently selected; the next lane is
    a prerequisite correction slice
  - no release gate, staging, local commit, or push is authorized from these
    findings
- recommended next route:
  - run one bounded correction lane to resolve the
    `oracle_signal_dir_zero_probe` fixture/runtime truth mismatch and add a
    focused regression guard before selecting another exact
    `context_ir_default_local_python_subprocess` provider implementation slice

Workspace-only `oracle_signal_dir_zero_probe` evidence correction acceptance:

- implementation result reviewed findings-first against live repo state and
  accepted first-pass with no findings
- corrected runtime evidence and active claim docs from
  `listing_entry_count=3` to `listing_entry_count=0`
- added focused tests proving:
  - fixture source executes as `dir:0`
  - the default local-Python subprocess facade plans exact
    `RuntimeProbeFamily.REFLECTIVE_BUILTIN`, `reflective_builtin:dir/0`,
    boundary `dir()`, subject `unsupported:call:main.py:2:11`, replay target
    seed `main.probe_directory`, and observes payload
    `listing_entry_count=0`
  - `context_ir_default_local_python_subprocess` remains fail-closed and does
    not support `oracle_signal_dir_zero_probe`
- accepted release unit is exactly:
  - `ARCHITECTURE.md`
  - `BUILDLOG.md`
  - `EVAL.md`
  - `PLAN.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `evals/fixtures/oracle_signal_dir_zero_probe/eval_runtime_observations.json`
  - `tests/test_eval_signal_dir_zero_probe.py`
- validation rerun by control:
  - direct fixture execution printed `dir:0`
  - focused ruff check passed
  - focused ruff format check passed
  - strict mypy over `src/` passed
  - focused pytest passed with `49 passed`
  - `git diff --check` passed
- dedicated read-only release-unit audit passed first-pass with no findings:
  - dirty set exactly matched the declared eight-file correction unit
  - active docs and fixture evidence now agree on `listing_entry_count=0`
  - tests prove direct fixture truth, exact `dir/0` subprocess facade replay,
    additive runtime provenance, and fail-closed provider behavior
  - no provider source, runtime worker, schema, MCP, run-spec, task, fixture
    source, or generalized support files changed
- full regression passed first-pass:
  - `.venv/bin/python -m ruff check src/ tests/` passed
  - `.venv/bin/python -m ruff format --check src/ tests/` passed with
    `110 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed with no issues in
    37 source files
  - `.venv/bin/python -m pytest tests/ -v` passed with `1660 passed`
- commit-gating passed first-pass with no findings:
  - dirty set exactly matched the eight-file correction unit
  - active dir-zero docs and fixture evidence agree on `listing_entry_count=0`
  - no active dir-zero `listing_entry_count=3` claims remain
  - provider source, runtime worker, schema, MCP, run-spec, task, fixture
    source, and generalized support files are unchanged
  - `context_ir_default_local_python_subprocess` remains fail-closed for
    `oracle_signal_dir_zero_probe`
  - `git diff --check` passed
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit audit cleared: yes, first-pass
  - full-regression cleared: yes, first-pass
  - commit-gating cleared: yes, first-pass
  - staged: completed as part of local release commit
  - locally committed: yes, `c3e08c4 Correct dir-zero eval runtime evidence`
  - pushed: no
- next route:
  - hold for Ryan push authorization
  - do not route `c3e08c4` back to release-unit audit, full regression,
    commit-gating, staging, or local commit creation absent new findings
  - after Ryan-authorized push, select the next bounded north-star lane from
    the pushed authority

Pushed internal default local-Python subprocess exec/eval eval provider release:
`125c44e Add exec/eval default subprocess eval provider`. This commit contains
the accepted exact `oracle_signal_exec_probe` and `oracle_signal_eval_probe`
support inside the internal `context_ir_default_local_python_subprocess`
provider. It is pushed with explicit Ryan authorization and must not be routed
back to release-unit audit, full regression, commit-gating, staging, local
commit, or push absent new findings.

Pushed exec/eval observed replay-input preservation correction release:
`53c82df Preserve exec/eval observed replay inputs`. This commit contains the
accepted correction that preserves exact exec/eval `observed_replay_inputs`
through runtime-probe execution attempt revalidation and runner-request result
assembly. It is pushed with explicit Ryan authorization and must not be routed
back to release-unit audit, full regression, commit-gating, staging, local
commit, or push absent new findings.

Pushed internal default local-Python subprocess vars-zero eval provider release:
`eef7173 Add vars-zero default subprocess eval provider`. This commit contains
the accepted exact `oracle_signal_vars_zero_probe` support inside the internal
`context_ir_default_local_python_subprocess` provider. It is pushed with
explicit Ryan authorization and must not be routed back to release-unit audit,
full regression, commit-gating, staging, local commit, or push absent new
findings.

Workspace-only post-`eef7173` routing state:

- live repo/workspace state was verified after push:
  - branch `main`
  - local `HEAD` and `origin/main` both resolve to
    `eef7173 Add vars-zero default subprocess eval provider`
  - no source/test implementation diff remains
- next route: select the next bounded north-star lane from the pushed
  `eef7173` authority

Workspace-only post-`eef7173` route selection:

- reviewed live repo/workspace state, default subprocess provider scope, the
  default local-Python subprocess facade, and remaining replay-equivalent
  fixture candidates; findings below
- exact `oracle_signal_exec_probe` and `oracle_signal_eval_probe` both plan
  correctly through diagnostics:
  - `RuntimeProbeFamily.EXEC_OR_EVAL` / `exec_or_eval:exec/1`, boundary
    `exec(source)`, subject `unsupported:call:main.py:3:4`
  - `RuntimeProbeFamily.EXEC_OR_EVAL` / `exec_or_eval:eval/1`, boundary
    `eval(source)`, subject `unsupported:call:main.py:3:11`
- both exec/eval default-facade dry runs fail with
  `ValueError: exec/eval runtime probe observations require observed replay
  inputs`
- root-cause inspection found `_validate_execution_attempt()` reconstructs a
  `RuntimeProbeExecutionAttempt` without copying `observed_replay_inputs`,
  so exact exec/eval observed attempts can fail during result-batch assembly
  even when the worker/runner emitted exact source proof
- exact `oracle_signal_metaclass_behavior_probe` dry-runs successfully through
  the default facade, but provider expansion is deferred because the exec/eval
  issue is a more foundational integration gap in already-pushed exact forms
- selected next bounded north-star lane: fix exact exec/eval observed
  replay-input preservation through runtime probe execution attempt
  revalidation and default local-Python subprocess facade recompile
- non-goals for the selected lane:
  - no provider support for exec/eval
  - no metaclass provider support
  - no public docs/claims, package-root, MCP, run-spec schema/config, eval
    asset, scoring, compiler, runtime worker, or new runtime-probe form change
- correction implementation is accepted in workspace first-pass with no
  findings:
  - `_validate_execution_attempt()` preserves `observed_replay_inputs`
  - runner-attempt collection validation accepts only replay-artifact identity
    or the exact observed replay-input merge form for observed results
  - regression coverage proves exact `exec(source)` and `eval(source)` through
    runner-request assembly and default local-Python subprocess recompile
- accepted release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_observation_recompile.py`
- control validation passed: focused ruff check, focused ruff format check,
  strict mypy, targeted pytest with `388 passed`, and clean
  `git diff --check`
- dedicated read-only release-unit audit passed first-pass with no findings
- full regression passed first-pass: ruff check, ruff format check, strict
  mypy, full pytest with `1650 passed`, and clean final `git diff --check`
- commit-gating passed after one continuity correction that removed a stale
  active vars-zero provider staging route from `PLAN.md`
- release state: accepted, release-unit-audit-cleared,
  full-regression-cleared, commit-gating-cleared, locally committed, and
  pushed at `53c82df Preserve exec/eval observed replay inputs`
- next route: select the next bounded north-star lane from the pushed
  `53c82df` authority; selected route is exact exec/eval provider support
  inside `context_ir_default_local_python_subprocess`

Pushed internal default local-Python subprocess globals eval provider release:
`037e64b Add globals default subprocess eval provider`. This commit contains
the accepted exact `oracle_signal_globals_probe` support inside the internal
`context_ir_default_local_python_subprocess` provider. It is pushed with
explicit Ryan authorization and must not be routed back to release-unit audit,
full regression, commit-gating, staging, local commit, or push absent new
findings.

Workspace-only post-`037e64b` route selection:

- reviewed live repo/workspace state and adjacent eval/provider surfaces;
  findings: none
- selected next bounded north-star lane: extend the existing internal
  `context_ir_default_local_python_subprocess` provider to exact
  `oracle_signal_vars_zero_probe`
- reason:
  - the pushed provider currently supports exact `oracle_signal_locals_probe`
    and `oracle_signal_globals_probe`
  - `oracle_signal_vars_zero_probe` is the closest low-risk sibling because it
    is an existing internal eval fixture with existing exact
    `reflective_builtin:vars/0` subprocess support
  - a live read-only dry run through the default local-Python subprocess
    facade planned exactly `RuntimeProbeFamily.REFLECTIVE_BUILTIN` form
    `reflective_builtin:vars/0`, boundary text `vars()`, subject
    `unsupported:call:main.py:2:11`, observed
    `lookup_outcome=returned_namespace`, selected the unsupported `vars()`
    unit, and produced one runtime provenance record
  - this increases internal eval-provider evidence depth without changing
    run-spec schema/config, eval assets, package-root exports, MCP,
    CLI/product, public docs/claims, scoring formulas, compiler behavior,
    runtime-probe forms, or generalized provider support
- alternatives deferred:
  - run-spec/provider configuration
  - broad multi-fixture subprocess provider support
  - `exec`, `eval`, or metaclass provider support where the proof channels and
    payload checks are materially different
  - dynamic-import, one-argument reflective/runtime-mutation, and dir-listing
    provider support where replay-equivalence, argument materialization, or
    payload shape is riskier
  - public docs/claims updates
- next route: exact `oracle_signal_vars_zero_probe` provider-support
  implementation lane

Workspace-only accepted exact `oracle_signal_vars_zero_probe` provider-support
slice:

- reviewed the returned implementation slice; findings: none
- accepted first-pass as workspace-only state
- release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/eval_providers.py`,
  `tests/test_eval_signal_globals_probe.py`,
  `tests/test_eval_signal_locals_probe.py`, and
  `tests/test_eval_signal_vars_zero_probe.py`
- `src/context_ir/eval_providers.py` keeps the provider name
  `context_ir_default_local_python_subprocess` and supports exactly
  `oracle_signal_locals_probe`, `oracle_signal_globals_probe`, and
  `oracle_signal_vars_zero_probe`
- unsupported task IDs still fail closed
- the vars-zero path:
  - builds the initial compile request without fixture runtime observations
  - diagnoses exact `vars()`
  - requires one planned `RuntimeProbeFamily.REFLECTIVE_BUILTIN` request with
    form `reflective_builtin:vars/0`, boundary `vars()`, and subject
    `unsupported:call:main.py:2:11`
  - uses the pushed default local-Python subprocess facade with
    `sys.executable` and `delta_budget=0`
  - validates one observed result with normalized payload
    `lookup_outcome=returned_namespace`
  - returns provider-owned runtime provenance records from the recompiled
    response
- focused tests prove real worker subprocess invocation through
  `(sys.executable, "-m", "context_ir.runtime_probe_worker")`, provider-owned
  runtime provenance, and preserved `unsupported/opaque` primary truth
- no durable eval fixture, task, run spec, run-spec schema/config,
  package-root, MCP/tool facade, public docs/claims, scoring formula,
  compiler, runtime-probe form, or generalized provider/runtime surface was
  changed
- focused control validation passed:
  - ruff check over the touched provider and focused eval tests
  - ruff format check over the same files
  - strict mypy over `src/`
  - targeted pytest over vars-zero/globals/locals provider tests plus eval runs
    and results, `57 passed`
  - `git diff --check`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: no
  - full-regression-cleared: no
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route: dedicated read-only release-unit audit over the exact six-file
  release unit

Release-unit audit for exact `oracle_signal_vars_zero_probe` provider-support
release unit:

- reviewed the returned read-only release-unit audit; findings: none
- audit passed first-pass for the exact six-file release unit:
  `BUILDLOG.md`, `PLAN.md`, `src/context_ir/eval_providers.py`,
  `tests/test_eval_signal_globals_probe.py`,
  `tests/test_eval_signal_locals_probe.py`, and
  `tests/test_eval_signal_vars_zero_probe.py`
- audit confirmed provider name, exact locals/globals/vars-zero scope,
  fail-closed unsupported task IDs, exact vars-zero request/payload/provenance
  behavior, real worker subprocess proof, preserved `unsupported/opaque`
  primary truth, and no excluded-surface widening
- audit-side validation passed:
  - `git diff --check`
  - focused ruff check
  - focused ruff format check
  - focused pytest over vars-zero/globals/locals tests, `28 passed`
  - focused strict mypy on `src/context_ir/eval_providers.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: no
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route: full regression gate for the exact six-file release unit

Full regression gate for exact `oracle_signal_vars_zero_probe` provider-support
release unit:

- reviewed the returned full regression gate; findings: none
- gate passed first-pass after release-unit audit clearance:
  - `.venv/bin/python -m ruff check src/ tests/` passed
  - `.venv/bin/python -m ruff format --check src/ tests/` passed,
    `110 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed,
    `37 source files clean`
  - `.venv/bin/python -m pytest tests/ -v` passed,
    `1646 passed`
  - `git diff --check` passed
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route: commit-gating review over the exact six-file release unit

Commit-gating review for exact `oracle_signal_vars_zero_probe` provider-support
release unit:

- performed commit-gating review after release-unit audit and full regression
  clearance
- gate passed first-pass with no findings
- gate confirmed exact six-file release unit:
  `BUILDLOG.md`, `PLAN.md`, `src/context_ir/eval_providers.py`,
  `tests/test_eval_signal_globals_probe.py`,
  `tests/test_eval_signal_locals_probe.py`, and
  `tests/test_eval_signal_vars_zero_probe.py`
- gate confirmed no staged files, no untracked files, clean `git diff --check`,
  unchanged excluded surfaces, exact locals/globals/vars-zero provider scope,
  and accurate release-state continuity
- accepted commit message:
  - subject: `Add vars-zero default subprocess eval provider`
  - body:
    `Extend the internal default local-Python subprocess provider to the exact
    oracle_signal_vars_zero_probe fixture so vars/0 runtime evidence is
    covered through the same provider-owned provenance path as
    locals/globals.`

    `Keep provider support fail-closed to the exact locals, globals, and
    vars-zero fixtures while preserving unsupported/opaque primary truth.`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: yes, first-pass
  - staged: no
  - locally committed: no
  - pushed: no
- next route: stage exactly the six release-unit files and create the local
  commit

Local commit action for exact `oracle_signal_vars_zero_probe` provider-support
release unit:

- the release unit is accepted, release-unit-audit-cleared,
  full-regression-cleared, and commit-gating-cleared
- local commit creation is the selected next release action
- stage exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/eval_providers.py`,
  `tests/test_eval_signal_globals_probe.py`,
  `tests/test_eval_signal_locals_probe.py`, and
  `tests/test_eval_signal_vars_zero_probe.py`
- accepted commit message:
  - subject: `Add vars-zero default subprocess eval provider`
  - body:
    `Extend the internal default local-Python subprocess provider to the exact
    oracle_signal_vars_zero_probe fixture so vars/0 runtime evidence is
    covered through the same provider-owned provenance path as
    locals/globals.`

    `Keep provider support fail-closed to the exact locals, globals, and
    vars-zero fixtures while preserving unsupported/opaque primary truth.`
- if live git shows this release unit is already locally committed, do not
  route it back to staging or local commit creation; hold for explicit Ryan
  push authorization
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: yes, first-pass
  - staged: pending local action
  - locally committed: pending local action
  - pushed: no

Pushed internal default local-Python subprocess eval provider release:
`5133ac8 Add default local-Python subprocess eval provider`. This commit
contains the accepted internal
`context_ir_default_local_python_subprocess` provider release unit. It is
pushed with explicit Ryan authorization and must not be routed back to
release-unit audit, full regression, commit-gating, staging, local commit, or
push absent new findings.

Workspace-only post-`5133ac8` route selection:

- reviewed live repo/workspace state and adjacent eval/provider surfaces;
  findings: none
- selected next bounded north-star lane: extend the existing internal
  `context_ir_default_local_python_subprocess` provider to exact
  `oracle_signal_globals_probe`
- reason:
  - the pushed provider currently supports only exact
    `oracle_signal_locals_probe`
  - `oracle_signal_globals_probe` is the closest low-risk sibling because it
    is an existing internal eval fixture with existing exact
    `runtime_mutation:globals/0` subprocess support
  - a live read-only dry run through the default local-Python subprocess
    facade planned exactly `RuntimeProbeFamily.RUNTIME_MUTATION` form
    `runtime_mutation:globals/0`, boundary text `globals()`, subject
    `unsupported:call:main.py:2:11`, observed
    `lookup_outcome=returned_namespace`, and produced runtime provenance
  - this increases internal eval-provider evidence depth without changing
    run-spec schema/config, eval assets, package-root exports, MCP,
    CLI/product, public docs/claims, scoring formulas, compiler behavior,
    runtime-probe forms, or generalized provider support
- alternatives deferred:
  - run-spec/provider configuration
  - broad multi-fixture subprocess provider support
  - dynamic-import, one-argument reflective/runtime-mutation, and dir-listing
    provider support where replay-equivalence or payload shape is riskier
  - public docs/claims updates
- next route: exact `oracle_signal_globals_probe` provider-support
  implementation lane

Workspace-only accepted exact `oracle_signal_globals_probe` provider-support
slice:

- reviewed the returned implementation slice; findings: none
- accepted first-pass as workspace-only state
- release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/eval_providers.py`, and
  `tests/test_eval_signal_globals_probe.py`
- `src/context_ir/eval_providers.py` keeps the provider name
  `context_ir_default_local_python_subprocess` and supports exactly
  `oracle_signal_locals_probe` and `oracle_signal_globals_probe`
- unsupported task IDs still fail closed
- the globals path:
  - builds the initial compile request without fixture runtime observations
  - diagnoses exact `globals()`
  - requires one planned `RuntimeProbeFamily.RUNTIME_MUTATION` request with
    form `runtime_mutation:globals/0`, boundary `globals()`, and subject
    `unsupported:call:main.py:2:11`
  - uses the pushed default local-Python subprocess facade with
    `sys.executable` and `delta_budget=0`
  - validates one observed result with normalized payload
    `lookup_outcome=returned_namespace`
  - returns provider-owned runtime provenance records from the recompiled
    response
- focused tests prove real worker subprocess invocation through
  `(sys.executable, "-m", "context_ir.runtime_probe_worker")`, provider-owned
  runtime provenance, and preserved `unsupported/opaque` primary truth
- no durable eval fixture, task, run spec, run-spec schema/config,
  package-root, MCP, CLI/product, public docs/claims, scoring formula,
  compiler, runtime-probe form, or generalized provider/runtime surface was
  changed
- focused control validation passed:
  - ruff check over the touched provider and focused eval tests
  - ruff format check over the same files
  - strict mypy over `src/`
  - targeted pytest over globals/locals provider tests plus eval runs,
    metrics, and results, `60 passed`
  - `git diff --check`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: no
  - full-regression-cleared: no
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route: dedicated read-only release-unit audit over the exact four-file
  release unit

Release-unit audit for exact `oracle_signal_globals_probe` provider-support
release unit:

- reviewed the returned read-only release-unit audit; findings: none
- audit passed first-pass for the exact four-file release unit:
  `BUILDLOG.md`, `PLAN.md`, `src/context_ir/eval_providers.py`, and
  `tests/test_eval_signal_globals_probe.py`
- audit confirmed provider name, exact locals/globals scope, fail-closed
  unsupported task IDs, exact globals request/payload/provenance behavior, real
  worker subprocess proof, preserved `unsupported/opaque` primary truth, and
  no excluded-surface widening
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: no
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route: full regression gate for the exact four-file release unit

Full regression gate for exact `oracle_signal_globals_probe` provider-support
release unit:

- ran the full regression gate after first-pass release-unit audit clearance
- gate passed first-pass:
  - `.venv/bin/python -m ruff check src/ tests/` passed
  - `.venv/bin/python -m ruff format --check src/ tests/` passed,
    `110 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed,
    `Success: no issues found in 37 source files`
  - `.venv/bin/python -m pytest tests/ -v` passed,
    `1643 passed in 15.74s`
  - final `git diff --check` passed
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route: commit-gating review over the exact four-file release unit

Commit-gating review for exact `oracle_signal_globals_probe` provider-support
release unit:

- performed commit-gating review after release-unit audit and full regression
  clearance
- gate passed first-pass with no findings
- gate confirmed exact four-file release unit:
  `BUILDLOG.md`, `PLAN.md`, `src/context_ir/eval_providers.py`, and
  `tests/test_eval_signal_globals_probe.py`
- gate confirmed no staged files, no untracked files, clean `git diff --check`,
  unchanged excluded surfaces, and accurate release-state continuity
- accepted commit message:
  - subject: `Add globals default subprocess eval provider`
  - body:
    `Extend the internal default local-Python subprocess eval provider to
    replay the globals fixture through the pushed worker facade while
    preserving unsupported/opaque primary truth and provider-owned runtime
    provenance.`

    `Keep scope limited to existing provider dispatch and focused tests without
    widening eval assets, run specs, public surfaces, scoring, compiler, or
    runtime-probe forms.`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: yes, first-pass
  - staged: no
  - locally committed: no
  - pushed: no
- next route: stage exactly the four release-unit files and create the local
  commit

Ryan-authorized release action for exact `oracle_signal_globals_probe`
provider-support release unit:

- Ryan authorized staging exactly the four release-unit files, creating the
  local commit with the accepted commit message, and pushing `main`
- if live git shows the release unit is already locally committed and pushed,
  do not route it back to audit, full regression, commit-gating, staging,
  local commit, or push
- after a verified push, route to selection of the next bounded north-star lane

Pushed internal eval provider/result provenance-carrier release:
`165bb43 Carry eval runtime provenance in provider results`. This commit
contains the accepted internal eval provider/result provenance-carrier release
unit. It is pushed with explicit Ryan authorization and must not be routed back
to release-unit audit, full regression, commit-gating, staging, local commit,
or push absent new findings.

Pushed test-only eval-fixture subprocess proof release:
`667fcdc Prove locals fixture through default subprocess facade`. This commit
contains the accepted `oracle_signal_locals_probe` fixture proof through the
default local-Python subprocess facade.

Pushed `dynamic_import:loader.__import__/1` local-Python subprocess release:

- reviewed the returned implementation slice; findings: none
- committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- `src/context_ir/runtime_probe_worker.py` now accepts exactly seven
  local-Python dynamic-import worker forms:
  `dynamic_import:importlib.import_module/1`,
  `dynamic_import:loader.import_module/1`,
  `dynamic_import:import_module/1`, `dynamic_import:load_module/1`,
  `dynamic_import:builtins.__import__/1`,
  `dynamic_import:loader.__import__/1`, and
  `dynamic_import:__import__/1`
- the worker default handler table registers all seven exact forms through the
  existing dynamic-import handler adapter and concrete observer
- the loader-builtin worker path imports the source module, resolves the replay
  target, requires source-module global `loader` to be present and identical
  to the real `builtins` module, then reuses the existing controlled
  `builtins.__import__` hook plus bounded `sys.modules[name]`
  insertion/restoration core
- the worker restores source-module global `loader`, `builtins.__import__`,
  and prior `sys.modules[name]` state on success and failure, and fails closed
  if target execution mutates either the source global or `builtins.__import__`
- `src/context_ir/runtime_probe_execution.py` now has
  `make_runtime_probe_dynamic_import_local_python_subprocess_runner(...)`
  register `dynamic_import:loader.__import__/1` alongside the six pushed
  dynamic-import subprocess forms
- focused coverage proves the real `python -m context_ir.runtime_probe_worker`
  subprocess path observes exact `loader.__import__(name)` as
  `imported_module=...`
- generalized builtins aliases and adjacent non-selected `__import__` forms
  remain fail-closed
- no request schema, package-root export, MCP, README, EVAL, PUBLIC_CLAIMS,
  public benchmark, scoring, compiler, admission, recompile, tool-facade,
  result-assembly, additional builtins-alias support, or generalized
  dynamic-import support was added
- focused control validation passed:
  - ruff check
  - ruff format check, `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, `tests/test_dependency_frontier.py`,
    and `tests/test_runtime_acquisition.py`, `494 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1235 passed`
  - Gate 3 commit-gating passed for the exact six-file unit
- local commit creation completed at
  `82bbb59 Add loader builtin import subprocess support`
- Ryan-authorized push completed for
  `82bbb59 Add loader builtin import subprocess support`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `82bbb59 Add loader builtin import subprocess support`
  - pushed: yes
  - next route: read-only planning/decomposition for the first
    post-dynamic-import runtime-probe family subprocess slice

Workspace-only post-`82bbb59` routing decision:

- selected one read-only planning/decomposition spike as the next bounded
  north-star lane
- dynamic-import subprocess support is treated as closed for the pushed exact
  seven forms absent a new finding
- the planning lane must choose the smallest truthful next runtime-probe
  subprocess family/slice, likely among reflective builtins, runtime mutation,
  exec/eval, metaclass behavior, or a focused integration-gap correction if
  live code shows dynamic-import subprocess integration is incomplete
- no implementation, staging, commit, push, public-claim update, package-root
  export, MCP change, schema change, scoring change, compiler change, or
  generalized dynamic-runtime support is authorized by this routing decision

Workspace-only accepted post-dynamic-import next-family planning result:

- reviewed the returned read-only planning/decomposition spike; findings: none
- accepted recommendation: implement exact
  `reflective_builtin:hasattr/2` local-Python subprocess support as the first
  post-dynamic-import runtime-probe family slice
- reason:
  - the current worker and parent runner are dynamic-import-only, while
    `hasattr(obj, name)` is already an attachable planned/admissible
    reflective-builtin runtime observation
  - this opens the reflective-builtin subprocess family with one exact form,
    without request schema, admission, tool facade, MCP, package-root,
    public-claim, scoring, compiler, docs, eval, or generalized runtime
    support widening
- alternatives deferred:
  - dynamic-import correction: no concrete live integration gap found
  - `vars/0`, `globals/0`, and `locals/0`: mechanically small but weaker
    north-star proof value than reflective attribute behavior
  - `exec`/`eval`: larger because replay inputs and durable proof contracts
    are family-specific
  - `dir`, `setattr`, and metaclass behavior: larger because they pull in
    durable artifact or broader runtime semantics
- next route: exact `reflective_builtin:hasattr/2` local-Python subprocess
  implementation lane

Pushed `reflective_builtin:hasattr/2` local-Python subprocess release:

- reviewed the returned implementation slice; findings: none
- current proposed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- `src/context_ir/runtime_probe_worker.py` now registers one exact
  reflective-builtin local-Python worker form:
  `reflective_builtin:hasattr/2`
- the worker validates exact reflective metadata, reason
  `REFLECTIVE_BUILTIN`, unsupported-finding subject kind, replay identity,
  and boundary text `hasattr(obj, name)` before replay execution
- the concrete worker observer imports the replay target source module,
  resolves a zero-argument target, temporarily wraps `builtins.hasattr`,
  captures exactly one two-argument call, restores `builtins.hasattr` on
  success and failure, and emits normalized payload
  `attribute_present=true` or `attribute_present=false`
- source modules with a shadowing global `hasattr`, target-time global
  `hasattr` mutation, builtin mutation, malformed metadata, boundary drift,
  required-argument targets, target exceptions, non-selected reflective forms,
  and dynamic-import requests through the reflective runner remain fail-closed
- `src/context_ir/runtime_probe_execution.py` now has
  `make_runtime_probe_reflective_hasattr_local_python_subprocess_runner(...)`
  as a narrow parent runner factory for exactly
  `reflective_builtin:hasattr/2`
- no generalized reflective-builtin support, `getattr`, `vars`, `dir`,
  runtime-mutation, `exec`/`eval`, metaclass support, public API,
  package-root export, schema, MCP, tool facade, scoring, compiler,
  admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or run-spec
  change was added
- focused control validation passed:
  - `ruff check src/ tests/`
  - `ruff format --check src/ tests/`, `110 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`,
    `tests/test_runtime_probe_requests.py`,
    `tests/test_runtime_observation_admission.py`, and
    `tests/test_runtime_acquisition.py`, `563 passed`
  - `git diff --check`
- release state:
  - accepted in workspace: yes, after 1 correction
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `b9f7bb6 Add reflective hasattr subprocess support`
  - pushed: yes
  - Gate 1 finding:
    `_restore_runtime_probe_reflective_hasattr_builtin()` reads
    `builtins.hasattr` before the restore `try` block, so deletion of
    `builtins.hasattr` by replay target code can raise `AttributeError`
    before restoration
  - correction accepted:
    `_restore_runtime_probe_reflective_hasattr_builtin()` now uses a missing
    sentinel for pre-restore and post-restore inspection and always attempts
    restoration; focused coverage proves target-time deletion of
    `builtins.hasattr` fails closed after restoration
  - combined read-only release gate passed with no findings:
    - Gate 1 release-unit audit passed and confirmed the prior deletion
      finding is closed
    - Gate 2 full regression passed, including full pytest reporting
      `1267 passed`
    - Gate 3 commit-gating passed for the exact six-file unit
  - Ryan-authorized push completed for
    `b9f7bb6 Add reflective hasattr subprocess support`
  - next route: select the next bounded north-star lane

Workspace-only post-`b9f7bb6` route selection:

- reviewed live repo state after pushed
  `b9f7bb6 Add reflective hasattr subprocess support`; findings: none
- selected next bounded north-star lane: exact
  `reflective_builtin:getattr/2` local-Python subprocess support
- reason:
  - `getattr(obj, name)` is already a planned and admissible
    reflective-builtin runtime observation with existing internal eval evidence
  - it is the closest attribute-reflection sibling to the pushed exact
    `hasattr(obj, name)` subprocess path
  - the current worker and parent runner still only support reflective
    subprocess execution for `hasattr/2`, so this is a focused one-form
    expansion rather than generalized runtime support
- alternatives deferred:
  - `reflective_builtin:getattr/3`: defer until two-argument `getattr` is
    proven through the subprocess path; the default branch has additional
    outcome distinctions
  - `reflective_builtin:vars/0`, `reflective_builtin:vars/1`,
    `reflective_builtin:dir/0`, and `reflective_builtin:dir/1`: defer because
    they prove namespace or listing behavior rather than direct attribute
    lookup behavior
  - `runtime_mutation:globals/0` and `runtime_mutation:locals/0`: defer until
    the reflective-builtin attribute lookup path is expanded beyond `hasattr`
  - `exec_or_eval:*` and `metaclass_behavior:keyword`: defer because they
    require durable proof, replay-input, or broader behavior-specific handling
- non-goals for the next lane:
  - no generalized reflective-builtin support
  - no `getattr/3`, `vars`, `dir`, runtime-mutation, `exec`/`eval`, or
    metaclass subprocess support
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or
    run-spec changes
- next route: exact `reflective_builtin:getattr/2` local-Python subprocess
  implementation lane

Workspace-only accepted `reflective_builtin:getattr/2` local-Python subprocess
release unit:

- reviewed the returned implementation slice; findings: none
- repo-backed truth during acceptance:
  - branch `main`
  - local `HEAD` and `origin/main` at
    `b9f7bb6 Add reflective hasattr subprocess support`
  - dirty files are exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - staged files: none
  - untracked files: none
  - `git diff --check` clean
- accepted implementation:
  - `src/context_ir/runtime_probe_worker.py` now registers exact
    `reflective_builtin:getattr/2` in the default local-Python worker table
  - the worker validates exact reflective metadata, reason
    `REFLECTIVE_BUILTIN`, unsupported-finding subject kind, replay identity,
    and boundary text `getattr(obj, name)` before replay execution
  - the concrete worker observer imports the replay target source module,
    resolves a zero-argument target, temporarily wraps `builtins.getattr`,
    captures exactly one two-argument lookup, restores `builtins.getattr` on
    success and failure, and emits normalized payload
    `lookup_outcome=returned_value` or
    `lookup_outcome=raised_attribute_error`
  - source modules with a shadowing global `getattr`, target-time global
    `getattr` mutation, builtin mutation/deletion, malformed metadata,
    boundary drift, required-argument targets, target exceptions, non-selected
    reflective forms, and dynamic-import requests through the reflective
    runner remain fail-closed
  - `src/context_ir/runtime_probe_execution.py` now has
    `make_runtime_probe_reflective_getattr_local_python_subprocess_runner(...)`
    as a narrow parent runner factory for exactly
    `reflective_builtin:getattr/2`
  - no generalized reflective-builtin support, `getattr/3`, `vars`, `dir`,
    runtime-mutation, `exec`/`eval`, metaclass support, public API,
    package-root export, schema, MCP, tool facade, scoring, compiler,
    admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or run-spec
    change was added
- focused control validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_worker.py src/context_ir/runtime_probe_execution.py tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_worker.py src/context_ir/runtime_probe_execution.py tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py`,
    `4 files already formatted`
  - `.venv/bin/python -m mypy --strict src/`, `Success: no issues found in
    37 source files`
  - `.venv/bin/python -m pytest tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py tests/test_runtime_probe_requests.py tests/test_runtime_observation_admission.py tests/test_runtime_acquisition.py -v`,
    `592 passed`
  - `git diff --check`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `50daeab Add reflective getattr subprocess support`
  - pushed: yes
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed and confirmed the unit is bounded to
    exact `reflective_builtin:getattr/2` local-Python subprocess support
  - Gate 2 full regression passed, including full pytest reporting
    `1295 passed`
  - Gate 3 commit-gating passed for the exact six-file unit
- next route:
  - select the next bounded north-star lane
  - do not reopen this pushed release absent a new finding

Workspace-only post-`50daeab` route selection:

- reviewed live repo state after pushed
  `50daeab Add reflective getattr subprocess support`; findings: none
- selected next bounded north-star lane: exact
  `reflective_builtin:getattr/3` local-Python subprocess support
- reason:
  - `getattr(obj, name, default)` is already a planned and admissible
    reflective-builtin runtime observation
  - existing evidence/docs already distinguish the defaulted `getattr`
    value-return and default-return branches through
    `lookup_outcome=returned_value` and
    `lookup_outcome=returned_default_value`
  - it is the closest exact-form sibling to the pushed `getattr(obj, name)`
    subprocess path and reuses the same reflective-builtin worker/runner
    architecture without generalized reflective-builtin support
- alternatives deferred:
  - `reflective_builtin:vars/0`, `reflective_builtin:vars/1`,
    `reflective_builtin:dir/0`, and `reflective_builtin:dir/1`: defer because
    they prove namespace/listing behavior and in some cases require durable
    artifacts or additional branch semantics
  - `runtime_mutation:globals/0` and `runtime_mutation:locals/0`: defer until
    the reflective-builtin attribute lookup family is completed through the
    defaulted `getattr` form
  - `runtime_mutation:setattr/3`, `runtime_mutation:delattr/2`,
    `exec_or_eval:*`, and `metaclass_behavior:keyword`: defer because they
    require mutation, durable proof, replay-input, or broader
    behavior-specific handling
- non-goals for the next lane:
  - no generalized reflective-builtin support
  - no `vars`, `dir`, runtime-mutation, `exec`/`eval`, or metaclass
    subprocess support
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or
    run-spec changes
- next route: exact `reflective_builtin:getattr/3` local-Python subprocess
  implementation lane

Workspace-only accepted `reflective_builtin:getattr/3` local-Python subprocess
release unit:

- reviewed the returned implementation slice; findings: none
- repo-backed truth during acceptance:
  - branch `main`
  - local `HEAD` and `origin/main` at
    `50daeab Add reflective getattr subprocess support`
  - dirty files are exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - staged files: none
  - untracked files: none
  - `git diff --check` clean
- accepted implementation:
  - `src/context_ir/runtime_probe_worker.py` now registers exact
    `reflective_builtin:getattr/3` in the default local-Python worker table
  - the worker validates exact reflective metadata, reason
    `REFLECTIVE_BUILTIN`, unsupported-finding subject kind, replay identity,
    and boundary text `getattr(obj, name, default)` before replay execution
  - the concrete worker observer imports the replay target source module,
    resolves a zero-argument target, temporarily wraps `builtins.getattr`,
    captures exactly one three-argument lookup, restores `builtins.getattr`
    on success and failure, and emits normalized payload
    `lookup_outcome=returned_value` or
    `lookup_outcome=returned_default_value`
  - source-global `getattr` shadowing or target-time drift, builtin mutation
    or deletion, malformed metadata, boundary drift, required-argument
    targets, target exceptions, adjacent reflective forms, and dynamic-import
    requests through the reflective runner all fail closed
  - dynamic-import subprocess behavior, exact `hasattr/2`, and exact
    `getattr/2` behavior remain covered
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task,
    run-spec, or generalized runtime-support widening was introduced
- focused control validation passed:
  - `ruff check` on the four touched source/test files
  - `ruff format --check` on the four touched source/test files,
    `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`,
    `tests/test_runtime_probe_requests.py`,
    `tests/test_runtime_observation_admission.py`, and
    `tests/test_runtime_acquisition.py`, `622 passed`
  - `git diff --check`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: no
  - full-regression-cleared: no
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run one combined read-only release gate over the exact six-file unit
  - the release-gate lane must stop on the first finding and must not edit,
    stage, commit, or push

Combined read-only release gate for `reflective_builtin:getattr/3`
local-Python subprocess release unit:

- reviewed the returned release-gate result; findings: none
- release-unit audit cleared:
  - confirmed the diff is bounded to exact
    `reflective_builtin:getattr/3` local-Python subprocess support
  - confirmed no generalized reflective-builtin support or adjacent surface
    widening
- full regression cleared:
  - `ruff check src/ tests/`: passed
  - `ruff format --check src/ tests/`: passed,
    `110 files already formatted`
  - `mypy --strict src/`: passed over 37 source files
  - `pytest tests/ -v`: passed, `1325 passed`
  - `git diff --check`: passed
- commit-gating cleared:
  - modified files are exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - staged files: none
  - untracked files: none
  - scope widening: none found
- repo-backed truth during gate acceptance:
  - branch `main`
  - local `HEAD` and `origin/main` at
    `50daeab Add reflective getattr subprocess support`
  - live control verification matched the returned gate report
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file unit
  - push remains Ryan-gated

Local commit for `reflective_builtin:getattr/3` local-Python subprocess
release unit:

- local commit creation completed for the exact six-file unit after
  release-unit audit, full regression, and commit-gating cleared
- local commit:
  - `24cb38b Add reflective getattr default subprocess support`
- repo-backed truth after local commit and before this continuity sync:
  - branch `main`
  - local `HEAD` at
    `24cb38b Add reflective getattr default subprocess support`
  - `origin/main` remains at
    `50daeab Add reflective getattr subprocess support`
  - local branch is ahead of `origin/main` by 1 commit
  - worktree clean before this docs-only continuity sync
  - staged files: none before this docs-only continuity sync
  - untracked files: none before this docs-only continuity sync
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `24cb38b Add reflective getattr default subprocess support`
  - pushed: no
- next route:
  - Ryan authorization for push, or an explicit hold without pushing

Pushed `reflective_builtin:getattr/3` local-Python subprocess release:

- Ryan-authorized push completed for
  `24cb38b Add reflective getattr default subprocess support`
- pushed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `24cb38b Add reflective getattr default subprocess support`
  - pushed: yes
  - next route: select the next bounded north-star lane

Workspace-only post-`24cb38b` route selection:

- reviewed live repo state after pushed
  `24cb38b Add reflective getattr default subprocess support`; findings:
  none
- selected next bounded north-star lane: exact
  `reflective_builtin:vars/1` local-Python subprocess support
- reason:
  - `vars(obj)` is already a planned and admissible reflective-builtin
    runtime observation with existing internal evidence for
    `lookup_outcome=returned_namespace` and
    `lookup_outcome=raised_type_error`
  - it is the smallest strong reflective-builtin follow-on after completing
    the exact attribute lookup sequence through `hasattr/2`, `getattr/2`,
    and `getattr/3`
  - the one-argument form can preserve target semantics by wrapping
    `builtins.vars`, calling the original one-argument builtin, returning the
    namespace on success, and re-raising `TypeError` for target-handled error
    branches
  - it avoids the caller-frame semantics required by zero-argument `vars()`
    and avoids durable listing artifacts required by `dir()`
- alternatives deferred:
  - `reflective_builtin:vars/0`: defer because exact zero-argument `vars()`
    requires caller-frame namespace semantics that are more delicate than the
    one-argument builtin wrapper
  - `reflective_builtin:dir/0` and `reflective_builtin:dir/1`: defer because
    the accepted proof boundary requires durable listing evidence
  - `runtime_mutation:globals/0` and `runtime_mutation:locals/0`: defer until
    the reflective-builtin namespace-introspection path starts with `vars/1`
  - `runtime_mutation:setattr/3`, `runtime_mutation:delattr/2`,
    `exec_or_eval:*`, and `metaclass_behavior:keyword`: defer because they
    require mutation, durable proof, replay-input, or broader
    behavior-specific handling
- non-goals for the next lane:
  - no generalized reflective-builtin support
  - no `vars/0`, `dir`, runtime-mutation, `exec`/`eval`, or metaclass
    subprocess support
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or
    run-spec changes
- next route: exact `reflective_builtin:vars/1` local-Python subprocess
  implementation lane

Workspace-only accepted `reflective_builtin:vars/1` local-Python subprocess
release unit:

- reviewed the returned implementation slice; findings: none
- repo-backed truth during acceptance:
  - branch `main`
  - local `HEAD` and `origin/main` at
    `24cb38b Add reflective getattr default subprocess support`
  - dirty files are exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - staged files: none
  - untracked files: none
  - `git diff --check` clean
- accepted implementation:
  - `src/context_ir/runtime_probe_worker.py` now registers exact
    `reflective_builtin:vars/1` in the default local-Python worker table
  - the worker validates exact reflective metadata, reason
    `REFLECTIVE_BUILTIN`, unsupported-finding subject kind, replay identity,
    and boundary text `vars(obj)` before replay execution
  - the concrete worker observer imports the replay target source module,
    resolves a zero-argument target, temporarily wraps `builtins.vars`,
    captures exactly one one-argument lookup, restores `builtins.vars` on
    success and failure, and emits normalized payload
    `lookup_outcome=returned_namespace` or
    `lookup_outcome=raised_type_error`
  - successful original `vars(obj)` calls return the original namespace to
    target code; original `TypeError` from `vars(obj)` is captured and
    re-raised so target-handled error branches remain real
  - source-global `vars` shadowing or target-time drift, builtin mutation or
    deletion, malformed metadata, boundary drift, required-argument targets,
    target exceptions, missing capture, multiple captures, wrong arity,
    `vars()`/kwargs, adjacent reflective forms, and dynamic-import requests
    through the reflective runner all fail closed
  - dynamic-import subprocess behavior, exact `hasattr/2`, exact
    `getattr/2`, and exact `getattr/3` behavior remain covered
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task,
    run-spec, or generalized runtime-support widening was introduced
- focused control validation passed:
  - `ruff check` on the four touched source/test files
  - `ruff format --check` on the four touched source/test files,
    `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`,
    `tests/test_runtime_probe_requests.py`,
    `tests/test_runtime_observation_admission.py`, and
    `tests/test_runtime_acquisition.py`, `655 passed`
  - `git diff --check`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: no
  - full-regression-cleared: no
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run one combined read-only release gate over the exact six-file unit
  - the release-gate lane must stop on the first finding and must not edit,
    stage, commit, or push

Combined read-only release gate for `reflective_builtin:vars/1` local-Python
subprocess release unit:

- reviewed the returned release-gate result; findings: none
- release-unit audit cleared:
  - confirmed the diff is bounded to exact
    `reflective_builtin:vars/1` local-Python subprocess support
  - confirmed no `vars/0`, `dir`, runtime-mutation, `exec`/`eval`,
    metaclass, schema, MCP, tool facade, scoring, compiler, admission,
    README, EVAL, PUBLIC_CLAIMS, fixture, task, run-spec, package-root
    export, public/API, or generalized runtime-support widening
- full regression cleared:
  - `ruff check src/ tests/`: passed
  - `ruff format --check src/ tests/`: passed,
    `110 files already formatted`
  - `mypy --strict src/`: passed over 37 source files
  - `pytest tests/ -v`: passed, `1358 passed`
  - `git diff --check`: passed
- commit-gating cleared:
  - modified files are exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - staged files: none
  - untracked files: none
  - scope widening: none found
- repo-backed truth during gate acceptance:
  - branch `main`
  - local `HEAD` and `origin/main` at
    `24cb38b Add reflective getattr default subprocess support`
  - live control verification matched the returned gate report
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file unit
  - push remains Ryan-gated

Local commit for `reflective_builtin:vars/1` local-Python subprocess release
unit:

- local commit creation completed for the exact six-file unit after
  release-unit audit, full regression, and commit-gating cleared
- local commit:
  - `3b8053f Add reflective vars subprocess support`
- repo-backed truth after local commit and before this continuity sync:
  - branch `main`
  - local `HEAD` at
    `3b8053f Add reflective vars subprocess support`
  - `origin/main` remains at
    `24cb38b Add reflective getattr default subprocess support`
  - local branch is ahead of `origin/main` by 1 commit
  - worktree clean before this docs-only continuity sync
  - staged files: none before this docs-only continuity sync
  - untracked files: none before this docs-only continuity sync
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `3b8053f Add reflective vars subprocess support`
  - pushed: no
- next route:
  - Ryan authorization for push, or an explicit hold without pushing

Pushed `reflective_builtin:vars/1` local-Python subprocess release:

- Ryan-authorized push completed for
  `3b8053f Add reflective vars subprocess support`
- pushed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `3b8053f Add reflective vars subprocess support`
  - pushed: yes
  - next route: select the next bounded north-star lane

Workspace-only post-`3b8053f` route selection:

- reviewed live repo state after pushed
  `3b8053f Add reflective vars subprocess support`; findings: none
- selected next bounded north-star lane: exact
  `reflective_builtin:vars/0` local-Python subprocess support
- reason:
  - `vars()` is already a planned and admissible reflective-builtin runtime
    observation with existing internal evidence for
    `lookup_outcome=returned_namespace`
  - it is the closest exact-form sibling to the pushed `vars(obj)` subprocess
    path and completes the reflective namespace-introspection pair
  - it stays in the current reflective-builtin worker/runner architecture
    before opening durable-listing `dir` work or a new runtime family
  - the implementation must preserve zero-argument `vars()` caller-frame
    semantics by returning the replay target caller frame namespace rather than
    calling original zero-argument `vars()` from inside the wrapper
- alternatives deferred:
  - `reflective_builtin:dir/0` and `reflective_builtin:dir/1`: defer because
    they require durable listing evidence
  - `runtime_mutation:globals/0` and `runtime_mutation:locals/0`: defer
    because they open a new runtime family and are less direct than completing
    the reflective `vars` pair
  - `runtime_mutation:setattr/3`, `runtime_mutation:delattr/2`,
    `exec_or_eval:*`, and `metaclass_behavior:keyword`: defer because they
    require mutation, durable proof, replay-input, or broader
    behavior-specific handling
- non-goals for the next lane:
  - no generalized reflective-builtin support
  - no `dir`, runtime-mutation, `exec`/`eval`, or metaclass subprocess support
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or
    run-spec changes
- next route: exact `reflective_builtin:vars/0` local-Python subprocess
  implementation lane

Workspace-only accepted `reflective_builtin:vars/0` local-Python subprocess
release unit:

- reviewed the returned implementation slice; findings: none
- repo-backed truth during acceptance:
  - branch `main`
  - local `HEAD` and `origin/main` at
    `3b8053f Add reflective vars subprocess support`
  - dirty files are exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - staged files: none
  - untracked files: none
  - `git diff --check` clean
- accepted implementation:
  - `src/context_ir/runtime_probe_worker.py` now registers exact
    `reflective_builtin:vars/0` in the default local-Python worker table
  - the worker validates exact reflective metadata, reason
    `REFLECTIVE_BUILTIN`, unsupported-finding subject kind, replay identity,
    and boundary text `vars()` before replay execution
  - the concrete worker observer imports the replay target source module,
    resolves a zero-argument target, temporarily wraps `builtins.vars`,
    captures exactly one zero-argument call, restores `builtins.vars` on
    success and failure, and emits normalized payload
    `lookup_outcome=returned_namespace`
  - the zero-argument wrapper returns caller-frame namespace data to target
    code and does not call original zero-argument `vars()` from inside the
    wrapper
  - source-global `vars` shadowing or target-time drift, builtin mutation or
    deletion, malformed metadata, boundary drift, required-argument targets,
    target exceptions, missing capture, multiple captures, wrong arity,
    argument/kwargs forms, adjacent reflective forms, and dynamic-import
    requests through the reflective runner all fail closed
  - `src/context_ir/runtime_probe_execution.py` now has
    `make_runtime_probe_reflective_vars_zero_local_python_subprocess_runner(...)`
    as a narrow parent runner factory for exactly
    `reflective_builtin:vars/0`
  - dynamic-import subprocess behavior, exact `hasattr/2`, exact
    `getattr/2`, exact `getattr/3`, and exact `vars/1` behavior remain
    covered
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task,
    run-spec, or generalized runtime-support widening was introduced
- focused control validation passed:
  - `ruff check` on the four touched source/test files
  - `ruff format --check` on the four touched source/test files,
    `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`,
    `tests/test_runtime_probe_requests.py`,
    `tests/test_runtime_observation_admission.py`, and
    `tests/test_runtime_acquisition.py`, `683 passed`
  - `git diff --check`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file unit
  - push remains Ryan-gated

Combined read-only release gate for `reflective_builtin:vars/0` local-Python
subprocess release unit:

- reviewed the returned release-gate result; findings: none
- release-unit audit cleared:
  - confirmed the diff is bounded to exact
    `reflective_builtin:vars/0` local-Python subprocess support plus
    continuity updates
  - confirmed no `dir`, runtime mutation, `exec`/`eval`, metaclass, schema,
    MCP, tool facade, scoring, compiler, admission, README, EVAL,
    PUBLIC_CLAIMS, fixture, task, run-spec, package-root export, public/API,
    or generalized runtime-support widening
- full regression cleared:
  - `ruff check src/ tests/`: passed
  - `ruff format --check src/ tests/`: passed,
    `110 files already formatted`
  - `mypy --strict src/`: passed over 37 source files
  - `pytest tests/ -v`: passed, `1386 passed`
  - `git diff --check`: passed
- commit-gating cleared:
  - modified files are exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - staged files: none
  - untracked files: none
  - cached diff: empty
  - scope widening: none found
- repo-backed truth during gate acceptance:
  - branch `main`
  - local `HEAD` and `origin/main` at
    `3b8053f Add reflective vars subprocess support`
  - live control verification matched the returned gate report
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file unit
  - push remains Ryan-gated

Local commit for `reflective_builtin:vars/0` local-Python subprocess release
unit:

- local commit creation completed for the exact six-file unit after
  release-unit audit, full regression, and commit-gating cleared
- local commit:
  - `230c8cf Add reflective vars zero subprocess support`
- repo-backed truth after local commit and before this continuity sync:
  - branch `main`
  - local `HEAD` at
    `230c8cf Add reflective vars zero subprocess support`
  - `origin/main` remains at
    `3b8053f Add reflective vars subprocess support`
  - local branch is ahead of `origin/main` by 1 commit
  - worktree clean before this docs-only continuity sync
  - staged files: none before this docs-only continuity sync
  - untracked files: none before this docs-only continuity sync
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `230c8cf Add reflective vars zero subprocess support`
  - pushed: no
- next route:
  - Ryan authorization for push, or an explicit hold without pushing

Pushed `reflective_builtin:vars/0` local-Python subprocess release:

- Ryan-authorized push completed for
  `230c8cf Add reflective vars zero subprocess support`
- pushed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `230c8cf Add reflective vars zero subprocess support`
  - pushed: yes
  - next route: select the next bounded north-star lane

Workspace-only post-`230c8cf` route selection:

- reviewed live repo state after pushed
  `230c8cf Add reflective vars zero subprocess support`; findings: none
- selected next bounded north-star lane: exact
  `reflective_builtin:dir/1` local-Python subprocess support
- reason:
  - `dir(obj)` is already a planned and admissible reflective-builtin runtime
    observation with existing internal evidence for
    `listing_entry_count=...` and a non-empty durable payload reference
  - it is the smallest direct follow-on after the pushed `vars(obj)` and
    `vars()` subprocess paths because it stays in the reflective-builtin
    family while proving the durable listing-reference stdout path
  - it avoids zero-argument `dir()` caller-frame semantics until the
    one-argument listing path is proven
  - it avoids opening a new runtime-mutation, exec/eval, or metaclass
    subprocess family
- alternatives deferred:
  - `reflective_builtin:dir/0`: defer until one-argument `dir(obj)` proves the
    durable listing-reference subprocess path; zero-argument `dir()` also has
    caller-frame namespace semantics
  - `runtime_mutation:globals/0` and `runtime_mutation:locals/0`: defer
    because they open a new runtime family and are less direct than completing
    the reflective listing path
  - `runtime_mutation:setattr/3`, `runtime_mutation:delattr/2`,
    `exec_or_eval:*`, and `metaclass_behavior:keyword`: defer because they
    require mutation, durable proof, replay-input, or broader
    behavior-specific handling
- non-goals for the next lane:
  - no generalized reflective-builtin support
  - no `dir/0`, runtime-mutation, `exec`/`eval`, or metaclass subprocess
    support
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or
    run-spec changes
- next route: exact `reflective_builtin:dir/1` local-Python subprocess
  implementation lane

Workspace-only accepted `reflective_builtin:dir/1` local-Python subprocess
release unit:

- reviewed the returned implementation slice; findings: none
- current proposed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- `src/context_ir/runtime_probe_worker.py` now registers exact
  `reflective_builtin:dir/1` in the default local-Python worker handler table
- the worker validates exact reflective metadata, reason
  `REFLECTIVE_BUILTIN`, unsupported-finding subject kind, replay identity, and
  boundary text `dir(obj)` before replay execution
- the concrete worker observer imports the replay target source module under
  request-local `cwd` and `sys.path`, resolves a zero-argument target,
  temporarily wraps `builtins.dir`, captures exactly one one-argument
  `dir(obj)` call, restores `builtins.dir` on success and failure, and emits
  normalized payload `listing_entry_count=<decimal>`
- successful observations carry deterministic durable artifact reference
  `artifact://runtime-probe/dir-listing/{request_id}.json`
- source modules with a shadowing global `dir`, target-time global `dir`
  mutation, builtin mutation or deletion, malformed metadata, boundary drift,
  required-argument targets, target exceptions, zero-argument `dir()`, kwargs
  forms, missing capture, multiple captures, non-selected reflective forms,
  and dynamic-import requests through the reflective runner remain fail-closed
- `src/context_ir/runtime_probe_execution.py` now has
  `make_runtime_probe_reflective_dir_local_python_subprocess_runner(...)` as a
  narrow parent runner factory for exactly `reflective_builtin:dir/1`
- no generalized reflective-builtin support, `dir/0`, runtime-mutation,
  `exec`/`eval`, metaclass support, public API, package-root export, schema,
  MCP, tool facade, scoring, compiler, admission, docs, README, EVAL,
  PUBLIC_CLAIMS, fixture, task, or run-spec change was added
- focused control validation passed:
  - ruff check
  - ruff format check, `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`,
    `tests/test_runtime_probe_requests.py`,
    `tests/test_runtime_observation_admission.py`, and
    `tests/test_runtime_acquisition.py`, `726 passed`
  - `git diff --check`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: no
  - full-regression-cleared: no
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run one combined read-only release gate over the exact six-file unit
  - the release-gate lane must stop on the first finding and must not edit,
    stage, commit, or push

Release-gate-cleared `reflective_builtin:dir/1` local-Python subprocess
release unit:

- reviewed the returned combined read-only release-gate result; findings: none
- release-unit audit cleared:
  - unit is bounded to exact `reflective_builtin:dir/1` local-Python
    subprocess support plus continuity updates
  - no `dir/0`, runtime-mutation, `exec`/`eval`, metaclass, public API,
    schema, MCP, scoring, compiler, admission, README, EVAL, PUBLIC_CLAIMS,
    fixture, task, run-spec, package-root export, or generalized
    runtime-support widening found
- full regression cleared:
  - `ruff check src/ tests/`: passed
  - `ruff format --check src/ tests/`: passed,
    `110 files already formatted`
  - `mypy --strict src/`: passed over 37 source files
  - `pytest tests/ -v`: passed, `1429 passed`
  - `git diff --check`: passed
- commit-gating cleared:
  - exact six modified files verified
  - staged files: none
  - untracked files: none
  - no late scope widening found
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file unit
  - push remains Ryan-gated

Local commit for `reflective_builtin:dir/1` local-Python subprocess release
unit:

- local commit creation completed for the exact six-file unit after
  release-unit audit, full regression, and commit-gating cleared
- local commit:
  - `01c2907 Add reflective dir subprocess support`
- repo-backed truth after local commit and before this continuity sync:
  - branch `main`
  - local `HEAD` at
    `01c2907 Add reflective dir subprocess support`
  - `origin/main` remains at
    `230c8cf Add reflective vars zero subprocess support`
  - local branch is ahead of `origin/main` by 1 commit
  - worktree clean before this docs-only continuity sync
  - staged files: none before this docs-only continuity sync
  - untracked files: none before this docs-only continuity sync
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `01c2907 Add reflective dir subprocess support`
  - pushed: no
- next route:
  - Ryan authorization for push, or an explicit hold without pushing

Pushed `reflective_builtin:dir/1` local-Python subprocess release:

- Ryan-authorized push completed for
  `01c2907 Add reflective dir subprocess support`
- pushed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `01c2907 Add reflective dir subprocess support`
  - pushed: yes
  - next route: select the next bounded north-star lane

Workspace-only post-`01c2907` route selection:

- reviewed live repo state after pushed
  `01c2907 Add reflective dir subprocess support`; findings: none
- selected next bounded north-star lane: exact
  `reflective_builtin:dir/0` local-Python subprocess support
- reason:
  - `dir()` is already a planned and admissible reflective-builtin runtime
    observation with existing internal evidence for
    `listing_entry_count=...` and a non-empty durable payload reference
  - the pushed `dir(obj)` subprocess release proves the durable listing
    reference path, so zero-argument `dir()` is now the smallest same-family
    follow-on
  - this completes the currently planned reflective-builtin listing pair
    without opening runtime-mutation, exec/eval, or metaclass subprocess
    families
- alternatives deferred:
  - `runtime_mutation:globals/0` and `runtime_mutation:locals/0`: defer
    because they open a new runtime family and are not required to complete
    the reflective listing path
  - `runtime_mutation:setattr/3` and `runtime_mutation:delattr/2`: defer
    because they require mutation-specific restoration and outcome contracts
  - `exec_or_eval:*`: defer because they require replay-source validation and
    source digest/durable proof contracts
  - `metaclass_behavior:keyword`: defer because class-creation behavior and
    durable proof make it larger than a same-family reflective builtin slice
- non-goals for the next lane:
  - no generalized reflective-builtin support
  - no runtime-mutation, `exec`/`eval`, or metaclass subprocess support
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or
    run-spec changes
- next route: exact `reflective_builtin:dir/0` local-Python subprocess
  implementation lane

Workspace-only accepted `reflective_builtin:dir/0` local-Python subprocess
release unit:

- reviewed the returned implementation slice; findings: none
- repo-backed truth during acceptance:
  - branch `main`
  - local `HEAD` and `origin/main` at
    `01c2907 Add reflective dir subprocess support`
  - dirty files are exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - staged files: none
  - untracked files: none
  - `git diff --check` clean
- accepted implementation:
  - `src/context_ir/runtime_probe_worker.py` now registers exact
    `reflective_builtin:dir/0` in the default local-Python worker table
  - the worker validates exact reflective metadata, reason
    `REFLECTIVE_BUILTIN`, unsupported-finding subject kind, replay identity,
    and boundary text `dir()` before replay execution
  - the concrete worker observer imports the replay target source module,
    resolves a zero-argument target, temporarily wraps `builtins.dir`,
    captures exactly one zero-argument `dir()` call with caller-frame
    semantics, restores `builtins.dir` on success and failure, and emits
    `listing_entry_count=<decimal>`
  - successful observations carry deterministic durable artifact reference
    `artifact://runtime-probe/dir-listing/{request_id}.json`
  - source-global `dir` shadowing or target-time drift, builtin mutation or
    deletion, malformed metadata, boundary drift, required-argument targets,
    target exceptions, missing capture, multiple captures, wrong-arity and
    kwargs forms, adjacent reflective forms, and dynamic-import requests
    through the reflective runner all fail closed
  - `src/context_ir/runtime_probe_execution.py` now has
    `make_runtime_probe_reflective_dir_zero_local_python_subprocess_runner(...)`
    as a narrow parent runner factory for exactly `reflective_builtin:dir/0`
  - dynamic-import subprocess behavior, exact `hasattr/2`, exact
    `getattr/2`, exact `getattr/3`, exact `vars/1`, exact `vars/0`, and exact
    `dir/1` behavior remain covered
  - no generalized reflective-builtin support, runtime-mutation, `exec`/`eval`,
    metaclass support, public API, package-root export, schema, MCP, tool
    facade, scoring, compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS,
    fixture, task, or run-spec change was added
- focused control validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_worker.py src/context_ir/runtime_probe_execution.py tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_worker.py src/context_ir/runtime_probe_execution.py tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py`,
    `4 files already formatted`
  - `.venv/bin/python -m mypy --strict src/`, `Success: no issues found in
    37 source files`
  - `.venv/bin/python -m pytest tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py tests/test_runtime_probe_requests.py tests/test_runtime_observation_admission.py tests/test_runtime_acquisition.py -v`,
    `748 passed`
  - `git diff --check`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: no
  - full-regression-cleared: no
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run one combined read-only release gate over the exact six-file unit
  - the release-gate lane must stop on the first finding and must not edit,
    stage, commit, or push

Combined read-only release gate for `reflective_builtin:dir/0` local-Python
subprocess release unit:

- reviewed the returned combined read-only release-gate result; findings: none
- release-unit audit:
  - passed and confirmed the unit is bounded to exact
    `reflective_builtin:dir/0` local-Python subprocess support plus
    continuity updates
  - confirmed no runtime-mutation, `exec`/`eval`, metaclass, public API,
    schema, MCP, scoring, compiler, admission, README, EVAL, PUBLIC_CLAIMS,
    fixture, task, run-spec, package-root export, or generalized
    runtime-support widening
  - confirmed pushed dynamic-import subprocess forms, exact `hasattr/2`,
    exact `getattr/2`, exact `getattr/3`, exact `vars/1`, exact `vars/0`,
    and exact `dir/1` behavior remain preserved
- full regression:
  - `.venv/bin/python -m ruff check src/ tests/`: passed
  - `.venv/bin/python -m ruff format --check src/ tests/`: passed,
    `110 files already formatted`
  - `.venv/bin/python -m mypy --strict src/`: passed,
    `Success: no issues found in 37 source files`
  - `.venv/bin/python -m pytest tests/ -v`: passed, `1451 passed`
  - `git diff --check`: passed
- commit-gating:
  - passed for exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - staged files: none
  - untracked files: none
- repo-backed truth during gate acceptance:
  - branch `main`
  - local `HEAD` and `origin/main` at
    `01c2907 Add reflective dir subprocess support`
  - live control verification matched the returned gate report
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file unit
  - push remains Ryan-gated

Local commit for `reflective_builtin:dir/0` local-Python subprocess release
unit:

- local commit creation completed for the exact six-file unit after
  release-unit audit, full regression, and commit-gating cleared
- local commit:
  - `64de22b Add reflective dir zero subprocess support`
- repo-backed truth after local commit and before this continuity sync:
  - branch `main`
  - local `HEAD` at
    `64de22b Add reflective dir zero subprocess support`
  - `origin/main` remains at
    `01c2907 Add reflective dir subprocess support`
  - local branch is ahead of `origin/main` by 1 commit
  - worktree clean before this docs-only continuity sync
  - staged files: none before this docs-only continuity sync
  - untracked files: none before this docs-only continuity sync
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `64de22b Add reflective dir zero subprocess support`
  - pushed: no
- next route:
  - Ryan authorization for push, or an explicit hold without pushing

Pushed `reflective_builtin:dir/0` local-Python subprocess release:

- Ryan-authorized push completed for
  `64de22b Add reflective dir zero subprocess support`
- pushed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `64de22b Add reflective dir zero subprocess support`
  - pushed: yes
  - next route: select the next bounded north-star lane

Workspace-only post-`64de22b` route selection:

- reviewed live repo state after pushed
  `64de22b Add reflective dir zero subprocess support`; findings: none
- selected next bounded north-star lane: exact
  `runtime_mutation:globals/0` local-Python subprocess support
- reason:
  - dynamic-import subprocess support and the currently planned
    reflective-builtin subprocess queue are closed for the pushed exact forms
    absent a new finding
  - `runtime_mutation:globals/0` is already emitted by runtime-probe request
    construction and admitted as `GlobalsRuntimeObservation`
  - existing runtime-acquisition/admission contracts require
    `lookup_outcome=returned_namespace` for matched `globals()`
    observations
  - `globals()` is the smallest truthful first runtime-mutation subprocess
    slice because it opens the family with one zero-argument namespace form
    while avoiding the frame-local semantics of `locals()`, object-state
    mutation/restoration contracts of `setattr`/`delattr`, replay-source
    proof for `exec`/`eval`, and class-creation proof for metaclass behavior
- alternatives deferred:
  - `runtime_mutation:locals/0`: defer until `globals/0` proves the
    runtime-mutation subprocess family path; it carries local-frame namespace
    semantics
  - `runtime_mutation:setattr/3` and `runtime_mutation:delattr/2`: defer
    because they need mutation-specific restoration and outcome contracts
  - `exec_or_eval:*`: defer because replay input and durable source-proof
    contracts are family-specific
  - `metaclass_behavior:keyword`: defer because it needs class-creation
    behavior and durable proof
- non-goals for the next lane:
  - no generalized runtime-mutation support
  - no `locals`, `setattr`, `delattr`, `exec`/`eval`, or metaclass subprocess
    support
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or
    run-spec changes
- next route: exact `runtime_mutation:globals/0` local-Python subprocess
  implementation lane

Workspace-only accepted `runtime_mutation:globals/0` local-Python subprocess
release unit:

- reviewed the returned implementation slice; findings: none
- repo-backed truth during acceptance:
  - branch `main`
  - local `HEAD` and `origin/main` at
    `64de22b Add reflective dir zero subprocess support`
  - dirty files are exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - staged files: none
  - untracked files: none
  - `git diff --check` clean
- accepted implementation:
  - `src/context_ir/runtime_probe_worker.py` now registers exact
    `runtime_mutation:globals/0` in the default local-Python worker table
  - the worker validates exact runtime-mutation metadata, reason
    `RUNTIME_MUTATION`, unsupported-finding subject kind, replay identity, and
    boundary text `globals()` before replay execution
  - the concrete worker observer imports the replay target source module,
    resolves a zero-argument target, temporarily wraps `builtins.globals`,
    captures exactly one zero-argument call, restores `builtins.globals` on
    success and failure, and preserves caller source-module global-namespace
    semantics
  - the success payload is normalized as
    `lookup_outcome=returned_namespace`
  - required-argument targets, target exceptions, malformed metadata, boundary
    drift, shadowed source-module `globals`, target-time source global drift,
    non-selected runtime-mutation forms, wrong arity, kwargs, missing capture,
    multiple captures, and builtin mutation/deletion during replay fail closed
  - `src/context_ir/runtime_probe_execution.py` now exposes the narrow parent
    runner factory
    `make_runtime_probe_runtime_mutation_globals_zero_local_python_subprocess_runner(...)`
- preserved non-goals:
  - no generalized runtime-mutation support
  - no `locals`, `setattr`, `delattr`, `exec`/`eval`, or metaclass subprocess
    support
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or
    run-spec changes
- focused control validation passed:
  - ruff check over the four in-scope files
  - ruff format check over the four in-scope files, `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over runtime probe worker, execution, request, admission,
    and acquisition tests, `776 passed`
  - `git diff --check`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file release unit
  - push remains Ryan-gated

Release gate for `runtime_mutation:globals/0` local-Python subprocess release
unit:

- reviewed the returned combined read-only release-gate result; findings: none
- release-unit audit passed
- full regression passed:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`,
    `110 files already formatted`
  - `.venv/bin/python -m mypy --strict src/`,
    `Success: no issues found in 37 source files`
  - `.venv/bin/python -m pytest tests/ -v`, `1479 passed`
  - `git diff --check`
- commit-gating passed:
  - dirty set exactly the six-file release unit
  - staged files: none
  - untracked files: none
  - scope widening: none detected
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file unit
  - push remains Ryan-gated

Local commit for `runtime_mutation:globals/0` local-Python subprocess release
unit:

- local commit creation completed for the exact six-file unit after
  release-unit audit, full regression, and commit-gating cleared
- local commit:
  - `5804c98 Add runtime globals subprocess support`
- repo-backed truth after local commit and before this continuity sync:
  - branch `main`
  - local `HEAD` at
    `5804c98 Add runtime globals subprocess support`
  - `origin/main` remains at
    `64de22b Add reflective dir zero subprocess support`
  - local branch is ahead of `origin/main` by 1 commit
  - worktree clean before this docs-only continuity sync
  - staged files: none before this docs-only continuity sync
  - untracked files: none before this docs-only continuity sync
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `5804c98 Add runtime globals subprocess support`
  - pushed: no
- next route:
  - Ryan authorization for push, or an explicit hold without pushing

Pushed `runtime_mutation:globals/0` local-Python subprocess release:

- Ryan-authorized push completed for
  `5804c98 Add runtime globals subprocess support`
- pushed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `5804c98 Add runtime globals subprocess support`
  - pushed: yes
  - next route: select the next bounded north-star lane

Workspace-only post-`5804c98` route selection:

- reviewed live repo state after pushed
  `5804c98 Add runtime globals subprocess support`; findings: none
- selected next bounded north-star lane: exact
  `runtime_mutation:locals/0` local-Python subprocess support
- reason:
  - `runtime_mutation:globals/0` is now pushed and proves the first
    runtime-mutation subprocess namespace form
  - `runtime_mutation:locals/0` is already emitted by runtime-probe request
    construction and admitted as `LocalsRuntimeObservation`
  - existing runtime-acquisition/admission contracts require
    `lookup_outcome=returned_namespace` for matched `locals()`
    observations
  - `locals()` is the smallest truthful next runtime-mutation subprocess
    slice because it keeps the zero-argument namespace payload shape while
    adding the focused caller-frame local-namespace semantics that `globals()`
    intentionally avoided
- alternatives deferred:
  - `runtime_mutation:setattr/3` and `runtime_mutation:delattr/2`: defer
    because they need mutation-specific restoration and outcome contracts
  - `exec_or_eval:*`: defer because replay input and durable source-proof
    contracts are family-specific
  - `metaclass_behavior:keyword`: defer because it needs class-creation
    behavior and durable proof
- non-goals for the next lane:
  - no generalized runtime-mutation support
  - no `setattr`, `delattr`, `exec`/`eval`, or metaclass subprocess support
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or
    run-spec changes
- next route: exact `runtime_mutation:locals/0` local-Python subprocess
  implementation lane

Workspace-only accepted `runtime_mutation:locals/0` local-Python subprocess
release unit:

- reviewed the returned implementation slice; findings: none
- repo-backed truth during acceptance:
  - branch `main`
  - local `HEAD` and `origin/main` at
    `5804c98 Add runtime globals subprocess support`
  - dirty files are exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - staged files: none
  - untracked files: none
  - `git diff --check` clean
- accepted implementation:
  - `src/context_ir/runtime_probe_worker.py` now registers exact
    `runtime_mutation:locals/0` in the default local-Python worker table
  - the worker validates exact runtime-mutation metadata, reason
    `RUNTIME_MUTATION`, unsupported-finding subject kind, replay identity, and
    boundary text `locals()` before replay execution
  - the concrete worker observer imports the replay target source module,
    resolves a zero-argument target, temporarily wraps `builtins.locals`,
    captures exactly one zero-argument call, restores `builtins.locals` on
    success and failure, and preserves caller target-frame local-namespace
    semantics
  - the success payload is normalized as
    `lookup_outcome=returned_namespace`
  - required-argument targets, target exceptions, malformed metadata, boundary
    drift, shadowed source-module `locals`, target-time source global drift,
    non-selected runtime-mutation forms, wrong arity, kwargs, missing capture,
    multiple captures, and builtin mutation/deletion during replay fail closed
  - `src/context_ir/runtime_probe_execution.py` now exposes the narrow parent
    runner factory
    `make_runtime_probe_runtime_mutation_locals_zero_local_python_subprocess_runner(...)`
- preserved non-goals:
  - no generalized runtime-mutation support
  - no `setattr`, `delattr`, `exec`/`eval`, or metaclass subprocess support
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, admission, docs, README, EVAL, PUBLIC_CLAIMS, fixture, task, or
    run-spec changes
- focused control validation passed:
  - ruff check over the four in-scope files
  - ruff format check over the four in-scope files, `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over runtime probe worker, execution, request, admission,
    and acquisition tests, `803 passed`
  - `git diff --check`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file release unit
  - push remains Ryan-gated

Release gate for `runtime_mutation:locals/0` local-Python subprocess release
unit:

- reviewed the returned combined read-only release-gate result; findings: none
- release-unit audit passed
- full regression passed:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`,
    `110 files already formatted`
  - `.venv/bin/python -m mypy --strict src/`,
    `Success: no issues found in 37 source files`
  - `.venv/bin/python -m pytest tests/ -v`, `1506 passed`
  - `git diff --check`
- commit-gating passed:
  - dirty set exactly the six-file release unit
  - staged files: none
  - untracked files: none
  - scope widening: none detected
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file unit
  - push remains Ryan-gated

Local commit for `runtime_mutation:locals/0` local-Python subprocess release
unit:

- local commit creation completed for the exact six-file unit after
  release-unit audit, full regression, and commit-gating cleared
- local commit:
  - `4f6b7e3 Add runtime locals subprocess support`
- repo-backed truth after local commit and before this continuity sync:
  - branch `main`
  - local `HEAD` at
    `4f6b7e3 Add runtime locals subprocess support`
  - `origin/main` remains at
    `5804c98 Add runtime globals subprocess support`
  - local branch is ahead of `origin/main` by 1 commit
  - worktree clean before this docs-only continuity sync
  - staged files: none before this docs-only continuity sync
  - untracked files: none before this docs-only continuity sync
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `4f6b7e3 Add runtime locals subprocess support`
  - pushed: no
- next route:
  - Ryan authorization for push, or an explicit hold without pushing

Pushed `runtime_mutation:locals/0` local-Python subprocess release:

- Ryan-authorized push completed for
  `4f6b7e3 Add runtime locals subprocess support`
- pushed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `4f6b7e3 Add runtime locals subprocess support`
  - pushed: yes
  - next route: select the next bounded north-star lane

Workspace-only post-`4f6b7e3` route selection:

- selected next bounded north-star lane:
  exact `runtime_mutation:delattr/2` local-Python subprocess support
- selection state:
  - repo-backed current pushed release/source-contract authority remains
    `4f6b7e3 Add runtime locals subprocess support`
  - dirty workspace-only control files are `BUILDLOG.md` and `PLAN.md`
  - staged files: none
  - untracked files: none
  - `git diff --check` clean
- reasoning:
  - pushed `runtime_mutation:globals/0` and `runtime_mutation:locals/0`
    prove the zero-argument namespace side of runtime-mutation subprocess
    handling
  - `runtime_mutation:delattr/2` is already planned by runtime-probe
    request construction and admitted as `DelattrRuntimeObservation`
  - runtime-acquisition contracts require
    `mutation_outcome=deleted_attribute` for matched `delattr(obj, name)`
    observations
  - this is narrower than `runtime_mutation:setattr/3`, which also needs
    assigned-value replay and durable assigned-value proof
- next route:
  - issue one implementation lane for exact `runtime_mutation:delattr/2`
    local-Python subprocess support
  - do not widen into `setattr`, `exec`/`eval`, metaclass behavior, public
    API, package-root export, schema, MCP, tool facade, scoring, compiler,
    admission, docs, README, EVAL, PUBLIC_CLAIMS, fixtures, tasks, run specs,
    or generalized dynamic-runtime support

Workspace-only accepted `runtime_mutation:delattr/2` local-Python subprocess
slice:

- accepted first-pass after control review of the returned implementation
  lane
- accepted source/test implementation files:
  - `src/context_ir/runtime_probe_execution.py`
  - `src/context_ir/runtime_probe_worker.py`
  - `tests/test_runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
- continuity files included in the proposed release unit:
  - `BUILDLOG.md`
  - `PLAN.md`
- repo-backed current pushed release/source-contract authority remains
  `4f6b7e3 Add runtime locals subprocess support`
- acceptance validation:
  - targeted ruff check passed
  - targeted ruff format check passed
  - strict mypy passed over `src/`
  - focused pytest passed, `833 passed`
  - `git diff --check` clean
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: no
  - full-regression-cleared: no
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run the release gate for the exact six-file release unit

Release gate for `runtime_mutation:delattr/2` local-Python subprocess release
unit:

- combined read-only release-gate lane completed after workspace-only
  acceptance
- release unit is exactly:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/runtime_probe_execution.py`
  - `src/context_ir/runtime_probe_worker.py`
  - `tests/test_runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
- release-unit audit passed:
  - bounded to exact `runtime_mutation:delattr/2` local-Python subprocess
    support plus continuity
  - no source/API/schema/MCP/scoring/compiler/admission/public-claim/fixture/
    task/run-spec/generalized runtime widening found
- full regression passed:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`,
    `110 files already formatted`
  - `.venv/bin/python -m mypy --strict src/`,
    `Success: no issues found in 37 source files`
  - `.venv/bin/python -m pytest tests/ -v`, `1536 passed in 12.65s`
  - `git diff --check`
- commit-gating passed:
  - dirty set exactly the six-file release unit
  - staged files: none
  - untracked files: none
  - scope widening: none detected
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file unit
  - push remains Ryan-gated

Pushed `runtime_mutation:delattr/2` local-Python subprocess release:

- Ryan-authorized push completed for
  `5b8da0a Add runtime delattr subprocess support`
- pushed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `5b8da0a Add runtime delattr subprocess support`
  - pushed: yes
  - next route: select the next bounded north-star lane

Workspace-only post-`5b8da0a` route selection:

- selected next bounded north-star lane:
  exact `runtime_mutation:setattr/3` local-Python subprocess support
- selection state:
  - repo-backed current pushed release/source-contract authority remains
    `5b8da0a Add runtime delattr subprocess support`
  - dirty workspace-only control files are `BUILDLOG.md` and `PLAN.md`
  - staged files: none
  - untracked files: none
  - `git diff --check` clean
- reasoning:
  - pushed `runtime_mutation:globals/0`, `runtime_mutation:locals/0`, and
    `runtime_mutation:delattr/2` prove the namespace plus deletion sides of
    runtime-mutation subprocess handling
  - `runtime_mutation:setattr/3` is already planned by runtime-probe request
    construction and admitted as `SetattrRuntimeObservation`
  - runtime-acquisition contracts require `mutation_outcome=returned_none` and
    a non-empty durable payload reference for matched
    `setattr(obj, name, value)` observations
  - this completes the already admitted runtime-mutation builtin set before
    moving to broader `exec`/`eval` or metaclass proof contracts
- next route:
  - issue one implementation lane for exact `runtime_mutation:setattr/3`
    local-Python subprocess support
  - do not widen into `exec`/`eval`, metaclass behavior, public API,
    package-root export, schema, MCP, tool facade, scoring, compiler,
    admission, docs, README, EVAL, PUBLIC_CLAIMS, fixtures, tasks, run specs,
    or generalized dynamic-runtime support

Workspace-only accepted `runtime_mutation:setattr/3` local-Python subprocess
slice:

- accepted first-pass after control review of the returned implementation
  lane
- accepted source/test implementation files:
  - `src/context_ir/runtime_probe_execution.py`
  - `src/context_ir/runtime_probe_worker.py`
  - `tests/test_runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
- continuity files included in the proposed release unit:
  - `BUILDLOG.md`
  - `PLAN.md`
- repo-backed current pushed release/source-contract authority remains
  `5b8da0a Add runtime delattr subprocess support`
- acceptance validation:
  - targeted ruff check passed
  - targeted ruff format check passed
  - strict mypy passed over `src/`
  - focused pytest passed, `863 passed`
  - `git diff --check` clean
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: no
  - full-regression-cleared: no
  - commit-gating-cleared: no
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - run the release gate for the exact six-file release unit

Release gate for `runtime_mutation:setattr/3` local-Python subprocess release
unit:

- combined read-only release-gate lane completed after workspace-only
  acceptance
- release unit is exactly:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/runtime_probe_execution.py`
  - `src/context_ir/runtime_probe_worker.py`
  - `tests/test_runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
- Gate 1 release-unit audit passed with no findings
- Gate 2 full regression passed:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`,
    `110 files already formatted`
  - `.venv/bin/python -m mypy --strict src/`,
    `Success: no issues found in 37 source files`
  - `.venv/bin/python -m pytest tests/ -v`, `1566 passed`
  - `git diff --check`
- Gate 3 commit-gating review passed with no findings:
  - dirty files exactly match the six release-unit files
  - staged files: none
  - untracked files: none
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - create one local commit for the exact six-file release unit
  - push remains Ryan-gated

Pushed `runtime_mutation:setattr/3` local-Python subprocess release:

- Ryan-authorized push completed for
  `1f4b9e3 Add runtime setattr subprocess support`
- pushed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `1f4b9e3 Add runtime setattr subprocess support`
  - pushed: yes
  - next route: select the next bounded north-star lane

Workspace-only post-`1f4b9e3` route selection:

- reviewed live repo state after pushed
  `1f4b9e3 Add runtime setattr subprocess support`; findings: none
- selected next bounded north-star lane:
  read-only `EXEC_OR_EVAL` local-Python subprocess source-proof contract
  planning spike
- reason:
  - pushed dynamic-import, exact reflective-builtin, and exact
    runtime-mutation subprocess forms are closed for the accepted exact forms
    absent a new finding
  - `EXEC_OR_EVAL` is the next runtime-probe family with existing planned
    forms and already accepted lower-layer observation/admission contracts
    for `eval(source)` and `exec(source)`
  - admissible `EXEC_OR_EVAL` observations require runtime-captured source
    proof in replay inputs (`source_shape` and `source_sha256`) plus
    durable payload references
  - the current local-Python worker stdout/result path carries normalized
    payload and durable artifact reference but not worker-supplied replay
    inputs, so direct implementation would need a narrow internal contract
    decision before code changes
  - `metaclass_behavior:keyword` remains broader because it is a non-call
    class-creation replay and durable-proof problem
- next route:
  - issue one read-only planning lane to select the exact first
    `EXEC_OR_EVAL` subprocess form and the minimal source-proof/result
    assembly contract
  - do not implement `eval`, `exec`, metaclass behavior, stdout protocol
    changes, result assembly changes, public API, package-root export, schema,
    MCP, tool facade, scoring, compiler, admission, docs, README, EVAL,
    PUBLIC_CLAIMS, fixtures, tasks, run specs, or generalized runtime support
    in that planning lane

Workspace-only accepted `EXEC_OR_EVAL` local-Python subprocess source-proof
planning result:

- accepted first-pass after control review of the returned read-only planning
  lane
- repo-backed pushed release/source-contract authority at planning acceptance
  time was
  `1f4b9e3 Add runtime setattr subprocess support`
- accepted findings:
  - the current worker stdout protocol carries `normalized_payload` and
    optional `durable_artifact_reference`, but no worker-supplied replay
    inputs
  - admission already supports `exec_or_eval:exec/1` and
    `exec_or_eval:eval/1` when the proof appears in
    `RuntimeProbeObservedResult.replay_artifact.replay_inputs`
  - current execution inputs intentionally keep replay inputs as
    request-identity fields
  - a worker-only `EXEC_OR_EVAL` implementation would not become admissible
    because `source_shape` and `source_sha256` would still be missing
- selected next implementation:
  - exact `exec_or_eval:exec/1` local-Python subprocess support
  - reason: `exec(source)` has the narrower deterministic proof contract:
    `source_shape=literal_statement`, `source_sha256=sha256(b"pass")`,
    `execution_outcome=completed`, optional `statement_kind=pass`, and a
    non-empty durable artifact reference
- required implementation contract:
  - add a backward-compatible observed replay-input channel from local-Python
    worker stdout through parent parsing/result assembly
  - merge observed proof fields into
    `RuntimeProbeObservedResult.replay_artifact.replay_inputs` at observed
    result assembly time
  - do not mutate `RuntimeProbeExecutionInput`
  - do not broaden `_replay_inputs_for_request`
  - reject duplicate replay-input keys
  - restrict exact `exec_or_eval:exec/1` observed proof to
    `source_shape=literal_statement` and
    `source_sha256=sha256(b"pass")`
- next implementation file boundary:
  - `src/context_ir/runtime_probe_worker.py`
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
  - `tests/test_runtime_probe_execution.py`
  - `tests/test_runtime_observation_admission.py`
  - optional `tests/test_runtime_acquisition.py` only if needed for
    end-to-end proof
- non-goals:
  - no `exec_or_eval:eval/1`
  - no generalized exec/eval support
  - no metaclass subprocess support
  - no source/admission behavior changes absent a concrete finding
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, docs, README, EVAL, PUBLIC_CLAIMS, fixtures, tasks, run specs,
    or generalized runtime support

Pushed exact `exec_or_eval:exec/1` local-Python subprocess release:

- accepted first-pass after control review of the returned implementation lane;
  findings: none
- repo-backed current pushed release/source-contract authority is now
  `07bb58f Add runtime exec subprocess support`
- committed release unit is exactly:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/runtime_probe_worker.py`
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
  - `tests/test_runtime_probe_execution.py`
- accepted behavior:
  - default worker registers exactly `RuntimeProbeFamily.EXEC_OR_EVAL` plus
    `exec_or_eval:exec/1`
  - parent runner exposes a narrow exact-exec subprocess factory
  - worker stdout can carry optional `observed_replay_inputs`, restricted to
    `source_shape=literal_statement` and
    `source_sha256=d74ff0ee8da3b9806b18c877dbf29bbde50b5bd8e4dad7a3a725000feb82e8f1`
  - parent result assembly merges observed source proof into observed result
    replay inputs without mutating `RuntimeProbeExecutionInput` or broadening
    `_replay_inputs_for_request`
  - the concrete worker observes exactly one zero-argument target call that
    performs one one-argument `exec(source)` with source exactly `"pass"`,
    restores `builtins.exec`, and fails closed for adjacent exec/eval forms,
    malformed metadata, wrong arity/kwargs, bad source, missing/multiple
    captures, target failures, and exec shadow/drift cases
- control validation rerun after implementation review:
  - ruff check passed
  - ruff format check passed, `6 files already formatted`
  - strict mypy passed over 37 source files
  - targeted pytest passed, `898 passed`
  - `git diff --check` passed
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: yes, first-pass
  - staged: yes, then committed
  - locally committed: yes,
    `07bb58f Add runtime exec subprocess support`
  - pushed: yes
- next route:
  - select the next bounded north-star lane after the pushed exact
    `exec_or_eval:exec/1` release

Workspace-only post-`07bb58f` route selection:

- reviewed live repo state after pushed
  `07bb58f Add runtime exec subprocess support`; findings: none
- selected next bounded north-star lane: exact
  `exec_or_eval:eval/1` local-Python subprocess support with a narrow
  observed replay-input source-proof path for the eval source
- reason:
  - `eval(source)` is already a planned and admissible `EXEC_OR_EVAL`
    runtime observation form
  - the exact `exec_or_eval:exec/1` subprocess release already proved the
    worker-to-parent observed replay-input source-proof pattern
  - the eval fixture and admission contract have a narrower deterministic
    expression proof than metaclass behavior:
    `source_shape=literal_expression`,
    `source_sha256=c40df915dac30fcea0f6f3394139e5608eb1e7af6f94838bd401ce1370856199`,
    `evaluation_outcome=returned_value`, and optional
    `result_type=builtins.str`
  - metaclass behavior is deferred because it needs a different class-creation
    proof model, selected-metaclass summary validation, and class import/replay
    semantics rather than the already-proven eval/exec source-proof channel
- next route:
  - issue one implementation lane for exact `exec_or_eval:eval/1`
    local-Python subprocess support
- non-goals for the next lane:
  - no generalized eval support
  - no `eval(source, globals)` or `eval(source, globals, locals)`
  - no additional `exec` support beyond pushed exact `exec_or_eval:exec/1`
  - no metaclass subprocess support
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, docs, README, EVAL, PUBLIC_CLAIMS, fixtures, tasks, run specs,
    or generalized runtime support

Workspace-only accepted exact `exec_or_eval:eval/1` local-Python subprocess
implementation:

- accepted first-pass after control review of the returned implementation lane;
  findings: none
- repo-backed current pushed release/source-contract authority remains
  `07bb58f Add runtime exec subprocess support`
- accepted implementation files are exactly:
  - `src/context_ir/runtime_probe_worker.py`
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
  - `tests/test_runtime_probe_execution.py`
- existing dirty control-state files `PLAN.md` and `BUILDLOG.md` are included
  in the proposed release unit as continuity/routing updates
- accepted behavior:
  - default worker registers exactly `RuntimeProbeFamily.EXEC_OR_EVAL` plus
    `exec_or_eval:eval/1`
  - parent runner exposes a narrow exact-eval subprocess factory
  - worker stdout reuses optional `observed_replay_inputs`, restricted for eval
    to `source_shape=literal_expression` and
    `source_sha256=c40df915dac30fcea0f6f3394139e5608eb1e7af6f94838bd401ce1370856199`
  - parent result assembly merges observed eval source proof into observed
    result replay inputs without mutating `RuntimeProbeExecutionInput` or
    broadening `_replay_inputs_for_request`
  - the concrete worker observes exactly one zero-argument target call that
    performs one one-argument `eval(source)` with source exactly
    `"eval-probe-value"` as a quoted literal expression, restores
    `builtins.eval`, preserves target caller-frame evaluation context, and
    fails closed for adjacent forms, malformed metadata, wrong arity/kwargs,
    bad source, non-string result, missing/multiple captures, target failures,
    and eval shadow/drift cases
  - pushed exact `exec_or_eval:exec/1`, dynamic-import, reflective-builtin,
    runtime-mutation, and metaclass behavior are preserved
- control validation rerun after implementation review:
  - ruff check passed
  - ruff format check passed, `6 files already formatted`
  - strict mypy passed over 37 source files
  - targeted pytest passed, `919 passed`
  - `git diff --check` passed
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: yes, first-pass
  - staged: yes, then committed
  - locally committed: yes,
    `f3467e5 Add runtime eval subprocess support`
  - pushed: yes
- next route:
  - select the next bounded north-star lane after exact
    `exec_or_eval:eval/1` subprocess support
  - do not treat this post-push continuity sync as implementation,
    release-gate, staging, commit, or push authorization

Workspace-only post-`f3467e5` route selection:

- reviewed live repo state after pushed
  `f3467e5 Add runtime eval subprocess support`; findings: none
- selected next bounded north-star lane: exact
  `metaclass_behavior:keyword` local-Python subprocess support
- reason:
  - `metaclass_behavior:keyword` is already planned by
    `derive_runtime_probe_requests(...)` and admissible as a
    `MetaclassBehaviorRuntimeObservation`
  - current worker and parent subprocess factories cover pushed dynamic-import,
    reflective-builtin, runtime-mutation, exec, and eval forms, but do not yet
    expose the planned metaclass-behavior family through local-Python
    subprocess execution
  - exact metaclass behavior is now the remaining north-star runtime family
    with internal eval evidence and no subprocess worker path
- alternatives deferred:
  - integration-gap correction: no live contradiction found in the pushed
    eval release or active route state
  - generalized metaclass support: defer; implement only the exact
    `metaclass_behavior:keyword` form
  - public/API/package-root/schema/MCP/scoring/compiler/docs/fixtures/tasks/
    run-spec changes: out of scope
- non-goals for the next lane:
  - no generalized metaclass behavior support
  - no new exec/eval, dynamic-import, reflective-builtin, or runtime-mutation
    subprocess forms
  - no public API, package-root export, schema, MCP, tool facade, scoring,
    compiler, docs, README, EVAL, PUBLIC_CLAIMS, fixtures, tasks, run specs,
    or generalized runtime support
- next route:
  - issue one implementation lane for exact `metaclass_behavior:keyword`
    local-Python subprocess support

Workspace-only accepted exact `metaclass_behavior:keyword` local-Python
subprocess implementation:

- accepted first-pass after control review of the returned implementation lane;
  findings: none
- repo-backed current pushed release/source-contract authority remains
  `f3467e5 Add runtime eval subprocess support`
- accepted implementation files are exactly:
  - `src/context_ir/runtime_probe_worker.py`
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_worker.py`
  - `tests/test_runtime_probe_execution.py`
- existing dirty control-state files `PLAN.md` and `BUILDLOG.md` are included
  in the proposed release unit as continuity/routing updates
- accepted behavior:
  - default worker registers exactly `RuntimeProbeFamily.METACLASS_BEHAVIOR`
    plus `metaclass_behavior:keyword`
  - parent runner exposes a narrow exact-metaclass-keyword subprocess factory
  - concrete worker validates exact metaclass metadata, imports the source
    module under a temporary `builtins.__build_class__` wrapper, captures the
    target class creation without calling the class or an arbitrary replay
    target callable, and restores `__build_class__` on success and failure
  - normalized payload is exactly `class_creation_outcome=created_class`,
    `created_class_qualified_name=...Example`, and
    `selected_metaclass_qualified_name=...Meta`, with deterministic
    `artifact://runtime-probe/metaclass-selection/{request_id}.json`
  - the exec/eval `observed_replay_inputs` proof channel remains narrow and is
    not used for metaclass observations
  - pushed exact dynamic-import, reflective-builtin, runtime-mutation,
    `exec_or_eval:exec/1`, and `exec_or_eval:eval/1` subprocess behavior is
    preserved
- control validation rerun after implementation review:
  - ruff check passed
  - ruff format check passed, `6 files already formatted`
  - strict mypy passed over 37 source files
  - targeted pytest passed, `938 passed`
  - `git diff --check` passed
- first release-unit audit found one P1 issue:
  - worker capture rejected the canonical
    `class Example(Base, metaclass=Meta)` fixture shape because the
    `__build_class__` guard allowed only the no-base target class form
- correction accepted in workspace:
  - worker capture now accepts
    `__build_class__(func, "Example", *bases, metaclass=Meta)` while still
    requiring exact target class name `Example`, exact `metaclass` keyword,
    and exact selected source-module `Meta`
  - added coverage for `class Example(Base, metaclass=Meta)` through both the
    concrete worker observer and parent-runner subprocess path
  - correction validation passed: ruff check, ruff format check, strict mypy,
    requested pytest set with `940 passed`, and `git diff --check`
- corrected release-unit audit passed:
  - findings: none
  - confirmed the prior code P1 and continuity P1 are closed
  - targeted base-class audit tests passed, `2 passed`
- full regression passed:
  - ruff check passed
  - ruff format check passed, `110 files already formatted`
  - strict mypy passed over 37 source files
  - full pytest passed, `1626 passed`
  - `git diff --check` passed
- commit-gating review passed:
  - findings: none
  - confirmed the exact six-file release unit and no staged or untracked files
  - confirmed no scope widening into generalized metaclass support,
    non-selected forms, public API, package-root export, schema, MCP, scoring,
    compiler, fixtures, tasks, run specs, or public claims
- release state:
  - accepted in workspace: yes, after 1 correction
  - release-unit-audit-cleared: yes, after corrected audit
  - full-regression-cleared: yes, first-pass after corrected audit
  - commit-gating-cleared: yes, first-pass
  - staged: yes, then committed
  - locally committed: yes,
    `20e6f55 Add metaclass keyword subprocess support`
  - pushed: yes
- next route:
  - superseded by the pushed parent-side exact default local-Python
    subprocess runner release at
    `92824aa Add default local-Python subprocess runner`
  - current route is the newer post-`92824aa` selection below: issue one
    implementation lane for an internal default local-Python subprocess
    recompile helper

Workspace-only accepted parent-side exact default local-Python subprocess
runner:

- accepted first-pass after control review of the returned implementation
  lane; findings: none
- repo-backed current pushed release/source-contract authority remains
  `20e6f55 Add metaclass keyword subprocess support`
- accepted implementation files are exactly:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
- existing dirty control-state files `PLAN.md` and `BUILDLOG.md` are included
  in the proposed release unit as continuity/routing updates
- accepted behavior:
  - `make_runtime_probe_default_local_python_subprocess_runner(...)` composes
    existing local-Python subprocess handler entries into one parent-side
    dispatching runner
  - the runner registers exactly the currently pushed exact subprocess forms
    across dynamic import, reflective builtins, runtime mutation, exec/eval,
    and metaclass keyword behavior
  - unsupported/non-selected forms produce the existing missing-handler
    non-proof attempt without reaching the subprocess worker
  - all per-form runner factories are preserved
  - the helper is module-level only in `context_ir.runtime_probe_execution` and
    remains absent from the package root
  - no source changes were made to `src/context_ir/runtime_probe_worker.py`
  - no runtime request, replay-input, admission, acquisition, recompile helper,
    tool-facade, package-root export, MCP, schema, scoring, compiler, docs,
    fixture, task, run-spec, public-claim, generalized runtime, or new-form
    behavior was widened
- validation basis:
  - implementation lane reported ruff check passed, ruff format check passed,
    strict mypy passed, requested pytest set passed with `1015 passed`, and
    `git diff --check` passed
  - control reran focused ruff check and format check over
    `src/context_ir/runtime_probe_execution.py` and
    `tests/test_runtime_probe_execution.py`
  - control reran the four new default-runner tests, `4 passed`
  - `git diff --check` passed
  - read-only release-unit audit passed first-pass with no findings
  - full regression passed first-pass:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`,
      `110 files already formatted`
    - `.venv/bin/python -m mypy --strict src/`,
      `Success: no issues found in 37 source files`
    - `.venv/bin/python -m pytest tests/ -v`,
      `1630 passed in 15.16s`
  - commit-gating review passed first-pass with no findings
- proposed release unit:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: yes, first-pass
  - staged: yes, then committed
  - locally committed: yes,
    `92824aa Add default local-Python subprocess runner`
  - pushed: yes
- next route:
  - superseded by the audit-cleared internal default local-Python subprocess
    recompile helper route below; full regression and commit-gating have now
    cleared
  - stage exactly the four release-unit files and create the local commit
  - do not widen tool facade, package-root exports, MCP, schema, scoring,
    compiler, docs, fixtures, tasks, run specs, public claims, generalized
    runtime support, or new runtime-probe forms
  - do not treat this workspace acceptance as push authorization

Workspace-only accepted internal default local-Python subprocess recompile
helper:

- accepted first-pass after control review of the returned implementation
  lane; findings: none
- repo-backed current pushed release/source-contract authority remains
  `92824aa Add default local-Python subprocess runner`
- accepted implementation files are exactly:
  - `src/context_ir/runtime_observation_recompile.py`
  - `tests/test_runtime_observation_recompile.py`
- existing dirty control-state files `PLAN.md` and `BUILDLOG.md` are included
  in the proposed release unit as continuity/routing updates
- accepted behavior:
  - `apply_default_local_python_subprocess_for_diagnostic_and_recompile(...)`
    is an internal helper in `context_ir.runtime_observation_recompile`
  - the helper mirrors the existing dynamic-import helper signature, builds
    `make_runtime_probe_default_local_python_subprocess_runner(...)`, and
    delegates through the existing generic runner-callable recompile bridge
  - focused coverage proves a real `python -m context_ir.runtime_probe_worker`
    subprocess for exact non-dynamic `runtime_mutation:locals/0` flows through
    observed result, admission, and attached-runtime recompile
  - the helper remains absent from `runtime_observation_recompile.__all__` and
    the package root
  - no source changes were made to `src/context_ir/runtime_probe_worker.py` or
    `src/context_ir/runtime_probe_execution.py`
  - no runtime request, replay-input, admission, acquisition, analyzer,
    tool-facade, package-root export, MCP, schema, scoring, compiler, docs,
    fixture, task, run-spec, public-claim, generalized runtime, or new-form
    behavior was widened
- validation basis:
  - implementation lane reported ruff check passed, ruff format check passed,
    strict mypy passed, requested pytest set passed with `1016 passed`, and
    `git diff --check` passed
  - control reran focused ruff check and format check over
    `src/context_ir/runtime_observation_recompile.py` and
    `tests/test_runtime_observation_recompile.py`
  - control reran the new subprocess proof and internal-surface tests,
    `2 passed`
  - `git diff --check` passed
- proposed release unit:
  - `BUILDLOG.md`
  - `PLAN.md`
  - `src/context_ir/runtime_observation_recompile.py`
  - `tests/test_runtime_observation_recompile.py`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: yes, first-pass
  - staged: yes, then committed
  - locally committed: yes,
    `0334911 Add default local-Python recompile helper`
  - pushed: yes
- next route:
  - superseded by the post-`0334911` route selection below: issue one
    implementation lane for a tool-facing default local-Python subprocess
    recompile wrapper
  - do not route the pushed `0334911` release back to release-unit audit, full
    regression, commit-gating, staging, local commit, or push handling absent
    new findings

Workspace-only post-`0334911` route selection:

- selected one implementation lane for a tool-facing default local-Python
  subprocess recompile wrapper in `src/context_ir/tool_facade.py`
- current evidence:
  - exact local-Python subprocess support is pushed for the current
    dynamic-import, reflective-builtin, runtime-mutation, exec/eval, and
    metaclass-keyword probe forms
  - `src/context_ir/runtime_probe_worker.py` has the default exact worker
    handler table
  - `src/context_ir/runtime_probe_execution.py` has
    `make_runtime_probe_default_local_python_subprocess_runner(...)`
  - `src/context_ir/runtime_observation_recompile.py` has
    `apply_default_local_python_subprocess_for_diagnostic_and_recompile(...)`
  - `src/context_ir/tool_facade.py` still exposes only the dynamic-import
    local-Python subprocess recompile wrapper at the tool-facing module layer
- rationale:
  - the tool-facing default subprocess wrapper is the next layer after the
    pushed internal default recompile helper
  - package-root and MCP exposure should wait until the tool-facing module
    wrapper exists and is reviewed in isolation
- authorized next implementation scope:
  - `src/context_ir/tool_facade.py`
  - `tests/test_tool_facade.py`
- explicit non-goals for the next implementation lane:
  - no source changes to `src/context_ir/runtime_probe_worker.py`
  - no source changes to `src/context_ir/runtime_probe_execution.py`
  - no source changes to `src/context_ir/runtime_observation_recompile.py`
  - no runtime request, replay-input, admission, acquisition, analyzer,
    package-root export, MCP, schema, scoring, compiler, docs, fixture, task,
    run-spec, public-claim, generalized runtime, or new-form changes
- release state:
  - selected in workspace: yes
  - implementation accepted: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: yes, first-pass
  - staged: yes, then committed
  - locally committed: yes,
    `7ee092b Add default local-Python recompile facade`
  - pushed: yes
- next route:
  - superseded by the post-`7ee092b` push state: select the next bounded
    north-star lane
  - do not route the pushed `7ee092b` release back to release-unit audit, full
    regression, commit-gating, staging, local commit, or push handling absent
    new findings

Workspace-only post-`7ee092b` route selection:

- selected one read-only exposure-boundary planning/decomposition spike as the
  next bounded north-star lane
- current evidence:
  - exact local-Python subprocess support is pushed through the worker, parent
    default runner, internal recompile helper, and
    `context_ir.tool_facade` wrapper
  - `src/context_ir/tool_facade.py` now exposes
    `SemanticDefaultLocalPythonSubprocessRecompileRequest`,
    `SemanticDefaultLocalPythonSubprocessRecompileResponse`, and
    `recompile_repository_context_with_default_local_python_subprocess(...)`
    from `context_ir.tool_facade.__all__`
  - `src/context_ir/__init__.py` still intentionally excludes those facade
    names from package-root exports
  - `src/context_ir/mcp_server.py` still registers exactly one minimal MCP
    tool, `compile_repository_context`
  - `README.md`, `EVAL.md`, and `PUBLIC_CLAIMS.md` continue to describe the
    MCP wrapper as minimal and public claims as bounded
- rationale:
  - the next possible moves touch package-root, MCP, CLI/product, docs/claims,
    or an explicit exposure hold
  - package-root and MCP are public/stable exposure boundaries and should not be
    widened as a mechanical follow-on to the tool-facade wrapper
  - a read-only planning lane is the smallest truthful move that can authorize
    a bounded implementation lane without broadening scope prematurely
- selected planning scope:
  - inspect `src/context_ir/tool_facade.py`, `src/context_ir/__init__.py`,
    `src/context_ir/mcp_server.py`, `tests/test_tool_facade.py`,
    `tests/test_mcp_server.py`, `tests/test_public_api.py`, `README.md`,
    `ARCHITECTURE.md`, `EVAL.md`, and `PUBLIC_CLAIMS.md`
  - decide whether the next implementation should be package-root exposure, an
    MCP tool, a CLI/product-facing path, a docs/claims hold, or no exposure
    change yet
  - return one exact next implementation prompt only if a bounded next
    implementation lane is justified
- explicit non-goals for the planning lane:
  - no implementation
  - no edits to source, tests, docs, eval artifacts, run specs, fixtures, or
    public claims
  - no staging, commit, push, reset, restore, or discard
  - no package-root, MCP, schema, scoring, compiler, runtime-probe,
    recompile-helper, facade, docs, README, EVAL, PUBLIC_CLAIMS, fixture,
    task, run-spec, generalized runtime, or new-form changes
- release state:
  - selected in workspace: yes
  - planning result accepted: yes, first-pass
  - implementation authorized: no exposure implementation authorized
  - release-unit-audit-cleared: not applicable
  - full-regression-cleared: not applicable
  - commit-gating-cleared: not applicable
  - staged: no
  - locally committed: no
  - pushed: no
- next route:
  - issue one read-only non-public north-star planning/decomposition spike
  - choose the next internal runtime-backed or evidence/ergonomics lane after
    accepting the no-exposure boundary
  - do not issue package-root, MCP, CLI/product, or public-claims
    implementation absent explicit Ryan authorization

Workspace-only accepted non-public north-star planning result:

- reviewed the returned read-only non-public north-star planning/decomposition
  spike after the accepted no-exposure decision; findings: none
- accepted decision:
  - keep `context_ir.tool_facade` as the highest exposed boundary for the
    default local-Python subprocess recompile capability
  - do not open package-root, MCP, CLI/product, or public-claims
    implementation absent explicit Ryan authorization
  - the concrete non-public gap is evidence depth: the default subprocess
    facade has real-subprocess facade proof for exact `runtime_mutation:locals/0`,
    but not yet against an accepted internal eval asset
  - the internal eval harness still uses fixture-loaded runtime observations,
    not subprocess-derived observations
- selected next bounded lane:
  - one test-only internal eval proof in `tests/test_eval_signal_locals_probe.py`
  - prove that
    `recompile_repository_context_with_default_local_python_subprocess(...)`
    can replay the existing `oracle_signal_locals_probe` fixture through a
    real `python -m context_ir.runtime_probe_worker` subprocess and attach
    additive runtime provenance through recompile
- rationale:
  - this uses existing eval assets and existing facade machinery
  - it does not require source changes, eval provider/run-spec design, public
    exposure, docs/claims updates, or a new runtime-probe form
- alternatives deferred:
  - non-public caller ergonomics
  - broader runtime evidence hardening
  - full subprocess eval provider/run-spec integration
  - docs/claims update
- explicit non-goals for the implementation lane:
  - no source changes
  - no eval fixture, task, or run-spec changes
  - no package-root, MCP, CLI/product, docs, README, EVAL, PUBLIC_CLAIMS,
    schema, scoring, compiler, eval-provider, generalized runtime, or
    runtime-probe form changes
- release state:
  - selected in workspace: yes
  - implementation accepted: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: yes, first-pass
  - staged: yes, then committed
  - locally committed: yes,
    `667fcdc Prove locals fixture through default subprocess facade`
  - pushed: yes
- next route:
  - superseded by the pushed `667fcdc` state: select the next bounded
    north-star lane
  - do not route this pushed release back to audit, regression,
    commit-gating, staging, local commit, or push absent new findings

Workspace-only post-`92824aa` route selection:

- selected one implementation lane for an internal default local-Python
  subprocess recompile helper in
  `src/context_ir/runtime_observation_recompile.py`
- current evidence:
  - exact local-Python subprocess support is pushed for the current
    dynamic-import, reflective-builtin, runtime-mutation, exec/eval, and
    metaclass-keyword probe forms
  - `src/context_ir/runtime_probe_worker.py` has the default exact worker
    handler table
  - `src/context_ir/runtime_probe_execution.py` has
    `make_runtime_probe_default_local_python_subprocess_runner(...)`
  - `src/context_ir/runtime_observation_recompile.py` has the generic
    runner-callable recompile bridge and a dynamic-import-only convenience
    helper
  - `src/context_ir/tool_facade.py` remains dynamic-import-specific for
    local-Python subprocess integration
- rationale:
  - the internal recompile helper is the smallest next layer after the pushed
    default parent runner
  - tool-facade widening should wait until the internal default recompile
    helper exists and is reviewed in isolation
- authorized next implementation scope:
  - `src/context_ir/runtime_observation_recompile.py`
  - `tests/test_runtime_observation_recompile.py`
- explicit non-goals for the next implementation lane:
  - no source changes to `src/context_ir/runtime_probe_worker.py`
  - no source changes to `src/context_ir/runtime_probe_execution.py` unless a
    concrete import/typing issue makes a tiny compatibility edit unavoidable
  - no runtime request, replay-input, admission, acquisition, analyzer,
    tool-facade, package-root export, MCP, schema, scoring, compiler, docs,
    fixture, task, run-spec, public-claim, generalized runtime, or new-form
    changes
- release state:
  - selected in workspace: yes
  - implementation accepted: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: yes, first-pass
  - staged: yes, then committed
  - locally committed: yes,
    `0334911 Add default local-Python recompile helper`
  - pushed: yes

Workspace-only post-`20e6f55` route selection:

- selected one implementation lane for a parent-side exact default
  local-Python subprocess runner factory in
  `src/context_ir/runtime_probe_execution.py`
- current evidence:
  - exact local-Python subprocess support is pushed for the current
    dynamic-import, reflective-builtin, runtime-mutation, exec/eval, and
    metaclass-keyword probe forms
  - `src/context_ir/runtime_probe_worker.py` already has a default worker
    handler table for the exact selected forms
  - `src/context_ir/runtime_probe_execution.py` has only per-form parent
    runner factories, with dynamic import as the only multi-form helper
  - `src/context_ir/runtime_observation_recompile.py` and
    `src/context_ir/tool_facade.py` remain dynamic-import-specific for
    local-Python subprocess integration
- rationale:
  - composing the existing exact parent runner entries is the smallest
    post-subprocess integration step
  - recompile and facade widening should wait until the combined parent
    runner exists and is reviewed in isolation
- authorized next implementation scope:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
- explicit non-goals for the next implementation lane:
  - no source changes to `src/context_ir/runtime_probe_worker.py`
  - no runtime request, replay-input, admission, acquisition, recompile helper,
    tool-facade, package-root export, MCP, schema, scoring, compiler, docs,
    fixture, task, run-spec, public-claim, generalized runtime, or new-form
    changes
- release state:
  - selected in workspace: yes
  - implementation accepted: yes, first-pass
  - release-unit-audit-cleared: yes, first-pass
  - full-regression-cleared: yes, first-pass
  - commit-gating-cleared: yes, first-pass
  - staged: yes, then committed
  - locally committed: yes,
    `92824aa Add default local-Python subprocess runner`
  - pushed: yes

Pushed `dynamic_import:builtins.__import__/1` local-Python subprocess release:

- `src/context_ir/runtime_probe_worker.py` now accepts exactly six
  local-Python dynamic-import worker forms:
  `dynamic_import:importlib.import_module/1`,
  `dynamic_import:loader.import_module/1`,
  `dynamic_import:import_module/1`, `dynamic_import:load_module/1`,
  `dynamic_import:builtins.__import__/1`, and
  `dynamic_import:__import__/1`
- the worker default handler table registers all six exact forms through the
  existing dynamic-import handler adapter and concrete observer
- the builtins-attribute worker path imports the source module, resolves the
  replay target, requires source-module global `builtins` to be present and
  identical to the real `builtins` module, then reuses the existing controlled
  `builtins.__import__` hook plus bounded `sys.modules[name]`
  insertion/restoration core
- the worker restores source-module global `builtins`, `builtins.__import__`,
  and prior `sys.modules[name]` state on success and failure, and fails closed
  if target execution mutates either the source global or `builtins.__import__`
- `src/context_ir/runtime_probe_execution.py` now has
  `make_runtime_probe_dynamic_import_local_python_subprocess_runner(...)`
  register `dynamic_import:builtins.__import__/1` alongside the five pushed
  dynamic-import subprocess forms
- focused coverage proves the real `python -m context_ir.runtime_probe_worker`
  subprocess path observes exact `builtins.__import__(name)` as
  `imported_module=...`
- adjacent `dynamic_import:loader.__import__/1` remains fail-closed in worker
  and parent runner coverage
- no request schema, package-root export, MCP, README, EVAL, PUBLIC_CLAIMS,
  public benchmark, scoring, compiler, admission, recompile, tool-facade,
  result-assembly, builtins-alias support, loader `__import__` support, or
  generalized dynamic-import support was added
- implementation review accepted the slice first-pass
- focused control validation passed:
  - ruff check
  - ruff format check, `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, `tests/test_dependency_frontier.py`,
    and `tests/test_runtime_acquisition.py`, `481 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1222 passed`
  - Gate 3 commit-gating passed for the exact six-file unit
- local commit creation completed at
  `9a88794 Add builtins attribute import subprocess support`
- Ryan-authorized push completed for
  `9a88794 Add builtins attribute import subprocess support`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `9a88794 Add builtins attribute import subprocess support`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: exact `dynamic_import:loader.__import__/1` local-Python
    subprocess implementation lane

Pushed `dynamic_import:__import__/1` local-Python subprocess release:

- `src/context_ir/runtime_probe_worker.py` now accepts exactly five
  local-Python dynamic-import worker forms:
  `dynamic_import:importlib.import_module/1`,
  `dynamic_import:loader.import_module/1`,
  `dynamic_import:import_module/1`, `dynamic_import:load_module/1`, and
  `dynamic_import:__import__/1`
- the worker default handler table registers all five exact forms through the
  existing dynamic-import handler adapter and concrete observer
- the bare builtin worker path imports the source module, resolves the replay
  target, verifies the source module does not shadow global `__import__`,
  temporarily hooks `builtins.__import__` during target execution, inserts a
  controlled `sys.modules[name]` module entry for the observed name, and
  restores both `builtins.__import__` and prior `sys.modules[name]` state on
  success and failure
- the worker fails closed if the target mutates `builtins.__import__` during
  execution
- `src/context_ir/runtime_probe_execution.py` now has
  `make_runtime_probe_dynamic_import_local_python_subprocess_runner(...)`
  register `dynamic_import:__import__/1` alongside the four pushed
  importlib-family forms
- focused coverage proves the real `python -m context_ir.runtime_probe_worker`
  subprocess path observes bare `__import__(name)` as `imported_module=...`
- adjacent builtin attribute and alias forms remain fail-closed:
  `dynamic_import:builtins.__import__/1` and
  `dynamic_import:loader.__import__/1`
- no request schema, package-root export, MCP, public claim, eval, scoring,
  compiler, admission, recompile, tool-facade, result-assembly, builtins
  attribute/alias support, or generalized dynamic-import support was added
- implementation review accepted the slice first-pass
- focused control validation passed:
  - ruff check
  - ruff format check, `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, `tests/test_dependency_frontier.py`,
    and `tests/test_runtime_acquisition.py`, `472 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1213 passed`
  - Gate 3 commit-gating passed for the exact six-file unit
- local commit creation completed at
  `1b08bb9 Add bare builtin import subprocess support`
- Ryan-authorized push completed for
  `1b08bb9 Add bare builtin import subprocess support`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `1b08bb9 Add bare builtin import subprocess support`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: superseded by the accepted workspace-only
    `dynamic_import:builtins.__import__/1` release-gate route above

Pushed `dynamic_import:load_module/1` local-Python subprocess release:

- `src/context_ir/runtime_probe_worker.py` now accepts exactly four
  local-Python dynamic-import worker forms:
  `dynamic_import:importlib.import_module/1`,
  `dynamic_import:loader.import_module/1`,
  `dynamic_import:import_module/1`, and
  `dynamic_import:load_module/1`
- the worker default handler table registers all four exact forms through the
  existing dynamic-import handler adapter and concrete observer
- the imported-alias worker path imports the source module, resolves the
  replay target, temporarily rebinds only the source module global
  `load_module` to the existing controlled import-module observer while
  executing the replay target, and restores the original global on success and
  failure
- the worker fails closed if the source module global `load_module` is absent,
  is not the imported `importlib.import_module` function object, or changes
  during target execution
- `src/context_ir/runtime_probe_execution.py` now has
  `make_runtime_probe_dynamic_import_local_python_subprocess_runner(...)`
  register `dynamic_import:load_module/1` alongside the three previously
  pushed exact forms
- focused coverage proves the real `python -m context_ir.runtime_probe_worker`
  subprocess path observes imported-alias `load_module(...)` as
  `imported_module=...`
- adjacent builtin forms including `dynamic_import:__import__/1`,
  `dynamic_import:builtins.__import__/1`, and
  `dynamic_import:loader.__import__/1` remain fail-closed
- no request schema, MCP/schema, package-root export, README, EVAL,
  PUBLIC_CLAIMS, public benchmark, scoring, compiler, admission, recompile,
  tool-facade, result-assembly, builtin-import, generalized alias, or
  generalized dynamic-import support was added
- implementation review initially found stale private helper docstrings in
  `src/context_ir/runtime_probe_worker.py`; a narrow correction updated the
  helper docstrings to describe exact `import_module`/`load_module` source
  globals without changing behavior
- corrected implementation review accepted the slice after 1 correction
- focused control validation passed:
  - ruff check
  - ruff format check, `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py` and
    `tests/test_runtime_probe_execution.py`, `345 passed`
  - scoped `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1200 passed`
  - Gate 3 commit-gating passed for the exact six-file unit
- local commit creation completed at
  `a0f46f3 Add imported-alias dynamic import subprocess support`
- Ryan-authorized push completed for
  `a0f46f3 Add imported-alias dynamic import subprocess support`
- release state:
  - accepted in workspace: yes, after 1 correction
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `a0f46f3 Add imported-alias dynamic import subprocess support`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: exact `dynamic_import:__import__/1` local-Python subprocess
    implementation lane

Pushed `dynamic_import:import_module/1` local-Python subprocess release:

- `src/context_ir/runtime_probe_worker.py` now accepts exactly three
  local-Python dynamic-import worker forms:
  `dynamic_import:importlib.import_module/1`,
  `dynamic_import:loader.import_module/1`, and
  `dynamic_import:import_module/1`
- the worker default handler table registers all three exact forms through the
  existing dynamic-import handler adapter and concrete observer
- the imported-name worker path imports the source module, resolves the replay
  target, temporarily rebinds only the source module global `import_module` to
  the existing controlled import-module observer while executing the replay
  target, and restores the original global on success and failure
- the worker fails closed if the source module global `import_module` is
  absent, is not the imported `importlib.import_module` function object, or
  changes during target execution
- `src/context_ir/runtime_probe_execution.py` now has
  `make_runtime_probe_dynamic_import_local_python_subprocess_runner(...)`
  register `dynamic_import:import_module/1` alongside the two previously
  pushed exact forms
- focused coverage proves the real `python -m context_ir.runtime_probe_worker`
  subprocess path observes imported-name `import_module(...)` as
  `imported_module=...`
- adjacent forms including `dynamic_import:load_module/1`,
  `dynamic_import:__import__/1`,
  `dynamic_import:builtins.__import__/1`, and
  `dynamic_import:loader.__import__/1` remain fail-closed
- no request schema, MCP/schema, package-root export, README, EVAL,
  PUBLIC_CLAIMS, public benchmark, scoring, compiler, admission, recompile,
  tool-facade, result-assembly, imported-alias, builtin-import, or generalized
  dynamic-import support was added
- implementation review accepted the slice first-pass
- focused control validation passed:
  - ruff check
  - ruff format check, `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py` and
    `tests/test_runtime_probe_execution.py`, `340 passed`
  - scoped `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1195 passed`
  - Gate 3 commit-gating passed for the exact six-file unit
- local commit creation completed at
  `2035f4f Add imported-name dynamic import subprocess support`
- Ryan-authorized push completed for
  `2035f4f Add imported-name dynamic import subprocess support`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `2035f4f Add imported-name dynamic import subprocess support`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: exact `dynamic_import:load_module/1` local-Python subprocess
    implementation slice

Pushed `dynamic_import:loader.import_module/1` local-Python subprocess release:

- `src/context_ir/runtime_probe_worker.py` now accepts exactly two
  local-Python dynamic-import worker forms:
  `dynamic_import:importlib.import_module/1` and
  `dynamic_import:loader.import_module/1`
- the worker default handler table registers both exact forms through the
  existing dynamic-import handler adapter and concrete observer
- `src/context_ir/runtime_probe_execution.py` now has
  `make_runtime_probe_dynamic_import_local_python_subprocess_runner(...)`
  register both exact dynamic-import local-Python subprocess forms
- the new root-module alias form reuses the existing
  `importlib.import_module` interception harness
- focused coverage proves the real `python -m context_ir.runtime_probe_worker`
  subprocess path observes `loader.import_module(...)` as
  `imported_module=...`
- adjacent forms including `dynamic_import:load_module/1`,
  `dynamic_import:__import__/1`,
  `dynamic_import:builtins.__import__/1`, and non-dynamic reflective forms
  remain fail-closed
- no request schema, MCP/schema, package-root export, README, EVAL,
  PUBLIC_CLAIMS, public benchmark, scoring, compiler, admission, recompile,
  result-assembly, generalized alias, imported-name/imported-alias, or
  builtin-import subprocess support was added
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1186 passed`
  - Gate 3 commit-gating passed for the exact six-file unit
- local commit creation completed at
  `db3eb8b Add loader import_module subprocess support`
- Ryan-authorized push completed for
  `db3eb8b Add loader import_module subprocess support`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `db3eb8b Add loader import_module subprocess support`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: superseded by accepted workspace-only
    `dynamic_import:import_module/1` local-Python subprocess release
    candidate above

Pushed dynamic-import local-Python tool facade release:

- `src/context_ir/tool_facade.py` now has
  `SemanticDynamicImportLocalPythonSubprocessRecompileRequest`,
  `SemanticDynamicImportLocalPythonSubprocessRecompileResponse`, and
  `recompile_repository_context_with_dynamic_import_local_python_subprocess`
- the facade delegates to
  `apply_dynamic_import_local_python_subprocess_for_diagnostic_and_recompile(...)`
- caller inputs remain explicit for the Python executable, invocation and
  completion revisions, repository snapshot basis, probe contract revision,
  runtime assumptions, runner contract revision, timeout, runner environment,
  runner assumptions, and optional embedding function
- the response mirrors nested runner preparation, attempt collection,
  result-batch admission, observation application, recompile result, compile
  result, diagnostic, budget, and selected/upgraded unit identities
- tests in `tests/test_tool_facade.py` prove real subprocess behavior,
  explicit-input delegation, mirror-field enforcement, package-root export
  quarantine, and unchanged MCP exports
- new names are added to `tool_facade.__all__` only
- package-root exports and MCP exports remain unchanged
- the slice does not add README, EVAL, PUBLIC_CLAIMS, public benchmark, eval,
  scoring, compiler, stdout-protocol, worker behavior, admission contract,
  result-assembly, automatic environment discovery, default `sys.executable`
  policy, generalized dynamic-import support claim, or a new runtime
  family/form
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1178 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `88f7c74 Add dynamic import tool facade`
- Ryan-authorized push completed for
  `88f7c74 Add dynamic import tool facade`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `88f7c74 Add dynamic import tool facade`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/tool_facade.py`, and `tests/test_tool_facade.py`
  - next route: control selection of the next bounded north-star lane

Pushed dynamic-import local-Python recompile helper release:

- `src/context_ir/runtime_observation_recompile.py` now has internal helper
  `apply_dynamic_import_local_python_subprocess_for_diagnostic_and_recompile`
- the helper composes
  `make_runtime_probe_dynamic_import_local_python_subprocess_runner(...)` with
  the existing `apply_runtime_probe_runner_for_diagnostic_and_recompile(...)`
  bridge
- the Python executable, invocation contract revision, completion contract
  revision, repository snapshot basis, probe contract revision, runtime
  assumptions, runner contract revision, timeout, runner environment, and
  runner assumptions remain explicit inputs
- tests in `tests/test_runtime_observation_recompile.py` prove the helper runs
  a real `python -m context_ir.runtime_probe_worker` subprocess through the
  pushed default dynamic-import worker path, admits the observed
  `imported_module=plugins.recompile_subprocess` payload, and recompiles the
  runtime-backed diagnostic boundary
- export-boundary assertions keep the helper out of package-root exports and
  `runtime_observation_recompile.__all__`
- the slice does not add public API, MCP, tool facade, package-root export,
  schema, eval, scoring, compiler, public-claim, stdout-protocol, worker
  behavior, admission contract, result-assembly, automatic environment
  discovery, default `sys.executable` policy, or new runtime family/form
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1176 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `842ddda Add dynamic import recompile helper`
- Ryan-authorized push completed for
  `842ddda Add dynamic import recompile helper`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `842ddda Add dynamic import recompile helper`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_observation_recompile.py`, and
    `tests/test_runtime_observation_recompile.py`
  - next route: control selection of the next bounded north-star lane

Pushed dynamic-import local-Python subprocess runner factory release:

- `src/context_ir/runtime_probe_execution.py` now has module-local
  `make_runtime_probe_dynamic_import_local_python_subprocess_runner`
- the helper composes the existing dispatching runner with exactly one
  existing local-Python subprocess handler entry
- the registered handler is limited to `RuntimeProbeFamily.DYNAMIC_IMPORT` and
  `dynamic_import:importlib.import_module/1`
- the helper invokes the existing worker module
  `context_ir.runtime_probe_worker` with no module argv by default
- the Python executable plus invocation and completion contract revisions
  remain explicit inputs
- tests in `tests/test_runtime_probe_execution.py` prove the helper reaches
  the worker's default dynamic-import handler through a real
  `python -m context_ir.runtime_probe_worker` subprocess and does not register
  adjacent family/form requests
- package-root exports remain unchanged
- the slice does not add a recompile convenience wrapper, automatic runner
  selection, tool facade, public API, package-root export, MCP, schema, eval,
  scoring, compiler, public-claim, admission, result-assembly,
  stdout-protocol, worker behavior, or new runtime family/form
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1175 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `6d4e04c Add dynamic import subprocess runner factory`
- Ryan-authorized push completed for
  `6d4e04c Add dynamic import subprocess runner factory`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `6d4e04c Add dynamic import subprocess runner factory`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`, and
    `tests/test_runtime_probe_execution.py`
  - next route: control selection of the next bounded north-star lane

Pushed local Python dynamic-import source module import harness release:

- `src/context_ir/runtime_probe_worker.py` now has module-local
  `import_runtime_probe_dynamic_import_replay_target_source_module(...)`
- the helper accepts a validated
  `RuntimeProbeLocalPythonDynamicImportReplayTarget`
- the helper imports exactly `replay_target.source_module_name` using the
  request working directory and ordered Python path entries
- module-import stdout and stderr are redirected away from worker stdout/stderr,
  so worker stdout protocol output cannot be contaminated by source module
  import prints
- `sys.path` and the process working directory are restored on success and
  failure
- the imported result must be a `ModuleType` whose `__name__` matches
  `replay_target.source_module_name`
- request/replay-target drift, import failures, malformed import results, and
  source-module name drift are rejected with deterministic worker-local errors
- package-root exports remain unchanged
- the slice does not resolve the replay target attribute path, execute the
  resolved callable, run dynamic-import interception, add concrete observer
  wiring, add default/global handler registration, change worker stdout
  protocol shape, change parent executor/parser behavior, or broaden API, MCP,
  schema, eval, scoring, compiler, docs, public-claim, admission, recompile, or
  result assembly surfaces
- implementation review accepted the slice first-pass
- focused validation passed:
  - ruff check over the two touched source/test files
  - ruff format check over the two touched source/test files
  - strict mypy over `src/`
  - targeted pytest over `tests/test_runtime_probe_worker.py` and
    `tests/test_runtime_probe_execution.py`, reporting `303 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1154 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `f0eb9e1 Add dynamic import source module importer`
- Ryan-authorized push completed for
  `f0eb9e1 Add dynamic import source module importer`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `f0eb9e1 Add dynamic import source module importer`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: control selection of the next bounded north-star lane

Pushed local Python dynamic-import concrete observer composition release:

- `src/context_ir/runtime_probe_worker.py` now has module-local
  `observe_runtime_probe_dynamic_import_worker_request(...)`
- the helper accepts a validated
  `RuntimeProbeLocalPythonDynamicImportWorkerRequest`
- the helper materializes the replay target, imports the replay target source
  module under request-local import state, resolves the replay target callable,
  executes that callable under the existing import-interception harness, and
  returns the existing
  `RuntimeProbeLocalPythonDynamicImportWorkerObservation`
- it composes only the already-pushed worker-local helpers and focused tests
  in `tests/test_runtime_probe_worker.py`
- it remains injectable through
  `build_runtime_probe_dynamic_import_worker_handler_entry(...)`
- it does not add default/global worker handler registration, parent executor
  or parser changes, stdout protocol shape changes, package-root exports, MCP,
  public API, schema, eval, scoring, compiler, admission, recompile, result
  assembly, docs, or public-claim changes
- implementation review accepted the slice first-pass
- focused validation passed:
  - ruff check over the two touched source/test files
  - ruff format check over the two touched source/test files
  - strict mypy over `src/`
  - targeted pytest over `tests/test_runtime_probe_worker.py` and
    `tests/test_runtime_probe_execution.py`, reporting `315 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1166 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `79b635b Compose dynamic import worker observer`
- Ryan-authorized push completed for
  `79b635b Compose dynamic import worker observer`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `79b635b Compose dynamic import worker observer`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: control selection of the next bounded north-star lane

Pushed local Python dynamic-import default worker handler registration release:

- `context_ir.runtime_probe_worker.main()` now uses the concrete
  dynamic-import observer through the existing handler adapter when
  `handler_entries` is omitted
- explicit injected `handler_entries` behavior is preserved for tests and
  future callers, including explicit empty-handler-table failure
- default registration is limited to
  `RuntimeProbeFamily.DYNAMIC_IMPORT` plus
  `dynamic_import:importlib.import_module/1`
- a valid dynamic-import worker stdin request can produce
  the existing stdout success protocol through the default `main()` path
  without passing injected handlers
- fail-closed behavior is preserved for malformed requests, unsupported
  family/form combinations, handler construction drift, observer failures, and
  stdout/stderr shielding
- package-root exports remain unchanged
- the slice does not change parent executor/parser behavior, stdout protocol shape,
  package-root exports, MCP, public API, schema, eval, scoring, compiler,
  admission, recompile, result assembly, docs, or public claims
- implementation review accepted the slice first-pass
- focused validation passed:
  - ruff check over the two touched source/test files
  - ruff format check over the two touched source/test files
  - strict mypy over `src/`
  - targeted pytest over `tests/test_runtime_probe_worker.py` and
    `tests/test_runtime_probe_execution.py`, reporting `319 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1170 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `2c21798 Register dynamic import worker default handler`
  - Ryan-authorized push completed for
    `2c21798 Register dynamic import worker default handler`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: control selection of the next bounded north-star lane

Pushed parent-side dynamic-import worker subprocess proof release:

- focused coverage in `tests/test_runtime_probe_execution.py` creates a
  temporary repository source module and drives the existing local-Python
  subprocess handler through the dispatching runner
- the subprocess path runs `python -m context_ir.runtime_probe_worker` without
  injected worker handlers
- the worker uses the pushed default dynamic-import handler for
  `RuntimeProbeFamily.DYNAMIC_IMPORT` and
  `dynamic_import:importlib.import_module/1`
- the parent materializes an observed `RuntimeProbeExecutionAttempt` through
  the existing stdout protocol with normalized payload
  `imported_module=plugins.parent_subprocess`
- no changes were made to `src/context_ir/runtime_probe_worker.py`,
  `src/context_ir/runtime_probe_execution.py`, package-root exports, MCP,
  public API, schema, eval, scoring, compiler, docs, public claims, admission,
  recompile, or result assembly surfaces
- implementation review accepted the slice first-pass
- focused validation passed:
  - ruff check over `src/context_ir/runtime_probe_execution.py` and
    `tests/test_runtime_probe_execution.py`
  - ruff format check over `src/context_ir/runtime_probe_execution.py` and
    `tests/test_runtime_probe_execution.py`
  - strict mypy over `src/`
  - targeted pytest over `tests/test_runtime_probe_execution.py` and
    `tests/test_runtime_probe_worker.py`, reporting `320 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1171 passed`
  - Gate 3 commit-gating passed for the exact three-file unit
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `cee4e9f Prove dynamic import worker subprocess path`
  - Ryan-authorized push completed for
    `cee4e9f Prove dynamic import worker subprocess path`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`, and
    `tests/test_runtime_probe_execution.py`
  - next route: control selection of the next bounded north-star lane

Pushed runtime probe real-subprocess recompile bridge proof release:

- focused coverage in `tests/test_runtime_observation_recompile.py` creates a
  temporary repository with a zero-argument replay target that calls
  `importlib.import_module("plugins.recompile_subprocess")`
- the test derives the diagnostic runtime-probe request plan through the
  existing semantic compile/diagnose path
- the test builds the existing dispatching runner with the existing
  local-Python subprocess handler entry for `RuntimeProbeFamily.DYNAMIC_IMPORT`
  and `dynamic_import:importlib.import_module/1`
- the test runs `apply_runtime_probe_runner_for_diagnostic_and_recompile(...)`
  using a real `python -m context_ir.runtime_probe_worker` subprocess
- the observed attempt, result, admission, and recompile chain carries
  `imported_module=plugins.recompile_subprocess`
- non-proof result separation remains empty for the proof case
- the diagnostic boundary upgrades to attached runtime support through the
  existing recompile path
- no source, worker, runtime execution, admission, recompile, tool facade,
  package-root export, MCP, schema, eval, scoring, compiler, public-claim,
  stdout-protocol, or result-assembly surface was widened
- implementation review accepted the slice first-pass
- focused validation passed:
  - ruff check over `src/context_ir/runtime_observation_recompile.py` and
    `tests/test_runtime_observation_recompile.py`
  - ruff format check over `src/context_ir/runtime_observation_recompile.py`
    and `tests/test_runtime_observation_recompile.py`
  - strict mypy over `src/`
  - targeted pytest over `tests/test_runtime_observation_recompile.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`, reporting `335 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1172 passed`
  - Gate 3 commit-gating passed for the exact three-file unit
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `ced8850 Prove runtime probe subprocess recompile bridge`
  - Ryan-authorized push completed for
    `ced8850 Prove runtime probe subprocess recompile bridge`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`, and
    `tests/test_runtime_observation_recompile.py`
  - next route: control selection of the next bounded north-star lane

Local Python dynamic-import replay target attribute resolver release:

- `src/context_ir/runtime_probe_worker.py` now has module-local
  `resolve_runtime_probe_dynamic_import_replay_target_callable(...)`
- the helper accepts a validated
  `RuntimeProbeLocalPythonDynamicImportReplayTarget`
- the helper accepts an injected `ModuleType` source module object and
  validates that `source_module.__name__` matches
  `replay_target.source_module_name`
- the helper resolves `replay_target.replay_target_attribute_path` by normal
  attribute lookup without executing the resolved object
- the helper returns the callable target expected by the existing import
  interception harness
- non-module source objects, source-module name drift,
  request/replay-target drift, missing attributes, and noncallable final
  targets are rejected
- package-root exports remain unchanged
- the slice does not import repository source modules, execute the resolved
  callable, run import interception, add concrete observer wiring, add
  default/global handler registration, change worker stdout protocol shape,
  change parent executor/parser behavior, or broaden API, MCP, schema, eval,
  scoring, compiler, docs, public-claim, admission, recompile, or result
  assembly surfaces
- implementation review accepted the slice first-pass
- focused validation passed:
  - ruff check over the two touched source/test files
  - ruff format check over the two touched source/test files
  - strict mypy over `src/`
  - targeted pytest over `tests/test_runtime_probe_worker.py` and
    `tests/test_runtime_probe_execution.py`, reporting `297 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1148 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `bd2ba92 Add dynamic import replay target resolver`
- Ryan-authorized push completed for
  `bd2ba92 Add dynamic import replay target resolver`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `bd2ba92 Add dynamic import replay target resolver`
  - pushed: yes
  - release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - release-gate status is no-active-gate for `bd2ba92`
  - next route: control selection of the next bounded north-star lane

Local Python dynamic-import import interception harness release:

- `src/context_ir/runtime_probe_worker.py` now has module-local
  `materialize_runtime_probe_dynamic_import_worker_observation_from_target(...)`
- the helper accepts either a validated
  `RuntimeProbeLocalPythonDynamicImportWorkerRequest` or
  `RuntimeProbeLocalPythonDynamicImportReplayTarget`
- the helper accepts an injected zero-argument target callable and runs it
  under a controlled `importlib.import_module` wrapper
- the wrapper captures exactly one absolute dotted imported module name and
  returns a fake `ModuleType` with that name, so no repository module import is
  performed by this harness
- the helper materializes the existing
  `RuntimeProbeLocalPythonDynamicImportWorkerObservation` contract
- target stdout and stderr are redirected away from worker stdout/stderr, so
  worker stdout protocol output cannot be contaminated by target prints
- `importlib.import_module` is restored on success and failure
- zero captured imports, multiple captured imports, malformed module names,
  relative imports, package imports, noncallable targets, and replay-target
  drift are rejected
- package-root exports remain unchanged
- the slice does not add repository source-module import, repository attribute
  lookup, concrete observer replay-target resolution, default/global handler
  registration, subprocess behavior changes, parent executor/parser changes,
  stdout protocol shape changes, API, MCP, schema, eval, scoring, compiler,
  docs, public-claim, admission, recompile, or result assembly changes
- implementation review accepted the slice first-pass
- focused validation passed:
  - ruff check over the two touched source/test files
  - ruff format check over the two touched source/test files
  - strict mypy over `src/`
  - targeted pytest over `tests/test_runtime_probe_worker.py` and
    `tests/test_runtime_probe_execution.py`, reporting `290 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1141 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `5fb6cf8 Add dynamic import interception harness`
- Ryan-authorized push completed for
  `5fb6cf8 Add dynamic import interception harness`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `5fb6cf8 Add dynamic import interception harness`
  - pushed: yes
  - release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - release-gate status is no-active-gate for `5fb6cf8`
  - next route: control selection of the next bounded north-star lane

Local Python dynamic-import worker replay target contract release:

- `src/context_ir/runtime_probe_worker.py` now has frozen module-local
  `RuntimeProbeLocalPythonDynamicImportReplayTarget`
- `materialize_runtime_probe_dynamic_import_replay_target(...)` consumes
  `RuntimeProbeLocalPythonDynamicImportWorkerRequest` and derives the
  repository replay target shape needed by a future concrete observer
- the contract derives strict source module names from repository-relative
  Python source paths, including top-level modules, nested modules, and
  package `__init__.py` files
- the contract derives replay target attribute paths from dotted
  `replay_target_seed` values only when rooted at the derived source module
  name
- request identity, source file path, replay target seed, replay selector
  seed, invocation identity, and request replay payload fields are preserved
- unsupported `source:...` fallback seeds, absolute or traversal source paths,
  non-Python source paths, blank or malformed module and attribute path
  segments, source-module drift, request drift, and direct-constructor drift
  are rejected
- package-root exports remain unchanged
- the release does not add `importlib` imports, repository-code execution,
  module import attempts, attribute lookup, concrete observer implementation,
  default/global handler registration, subprocess behavior changes, parent
  executor/parser changes, API, MCP, schema, eval, scoring, compiler, docs,
  public-claim, admission, recompile, or result assembly changes
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1130 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `7fe4f76 Add dynamic import replay target contract`
- Ryan-authorized push completed with release routing through
  `ad3ed71 Sync dynamic import replay target routing`
- release unit is exactly `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_worker.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `7fe4f76`

Local Python dynamic-import worker handler adapter release:

- `src/context_ir/runtime_probe_worker.py` now has module-local
  `RuntimeProbeLocalPythonDynamicImportWorkerObserver`
- `RuntimeProbeLocalPythonDynamicImportWorkerHandlerAdapter` adapts typed
  worker payloads into the dynamic-import worker request contract, calls an
  injected observer, validates the returned observation against the adapted
  request, and materializes the existing worker success response
- `build_runtime_probe_dynamic_import_worker_handler_entry(...)` returns a
  `RuntimeProbeLocalPythonWorkerHandlerEntry` for
  `RuntimeProbeFamily.DYNAMIC_IMPORT` and exact form
  `dynamic_import:importlib.import_module/1`
- existing worker dispatch and `main(...)` can consume injected fake observers
  through the factory
- default `main(...)` remains fail-closed without default handlers
- package-root exports remain unchanged
- the release does not add `importlib` imports, repository-code execution,
  module import attempts, concrete observer implementation, default/global
  handler registration, subprocess behavior changes, parent executor/parser
  changes, API, MCP, schema, eval, scoring, compiler, docs, public-claim,
  admission, recompile, or result assembly changes
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1109 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `73feb5f Add dynamic import worker handler adapter`
- Ryan-authorized push completed with release routing through
  `196188b Sync dynamic import handler routing`
- release unit is exactly `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_worker.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `73feb5f`

Local Python dynamic-import worker observation success-response contract
release:

- `src/context_ir/runtime_probe_worker.py` now has a frozen typed
  `RuntimeProbeLocalPythonDynamicImportWorkerObservation`
- `materialize_runtime_probe_dynamic_import_worker_observation(...)` derives
  validated worker-local dynamic-import observation metadata from
  `RuntimeProbeLocalPythonDynamicImportWorkerRequest`
- `materialize_runtime_probe_dynamic_import_worker_success_response(...)`
  emits the existing worker stdout success-response contract with exactly one
  deterministic normalized payload field, `imported_module`
- the observation preserves the validated request identity, plan/request
  identity, replay target and selector seeds, invocation contract revision,
  invocation identity, original request replay fields, and observed imported
  module name
- imported module metadata is validated as non-empty, stripped,
  control-character free, absolute dotted module syntax, non-empty segments,
  and identifier-like module-name segments
- direct construction, request drift, malformed imported-module metadata,
  frozen behavior, deterministic success payload, no-importlib boundary, and
  package-root export quarantine are covered by tests
- package-root exports remain unchanged
- the release does not add `importlib` imports, repository-code execution,
  module import attempts, concrete handler implementation, default/global
  handler registration, subprocess behavior changes, parent executor/parser
  changes, API, MCP, schema, eval, scoring, compiler, docs, public-claim,
  admission, recompile, or result assembly changes
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1102 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `6e8d04f Add dynamic import worker observation contract`
- Ryan-authorized push completed with release routing through
  `c47832c Sync dynamic import observation routing`
- release unit is exactly `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_worker.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `6e8d04f`

Local Python dynamic-import worker request contract release:

- `src/context_ir/runtime_probe_worker.py` now has a frozen typed
  `RuntimeProbeLocalPythonDynamicImportWorkerRequest`
- `materialize_runtime_probe_dynamic_import_worker_request(...)` derives the
  worker-local request from `RuntimeProbeLocalPythonWorkerRequestPayload`
- the contract accepts only `RuntimeProbeFamily.DYNAMIC_IMPORT` with exact
  form label `dynamic_import:importlib.import_module/1`
- the request preserves plan/request identity, subject identity, source-site
  identity and span, reason code, boundary text, replay target and selector
  seeds, argv, working directory, ordered Python path entries, timeout
  seconds, invocation contract revision, invocation identity, and original
  request replay fields
- drifted, missing, duplicate, blank, malformed source-span, and malformed
  invocation identity metadata are rejected before any execution behavior
  exists
- first review found missing direct-constructor validation coverage; the
  correction added focused `dataclasses.replace(...)` coverage for the
  frozen contract's `__post_init__` path
- package-root exports remain unchanged
- the release does not add `importlib` imports, repository-code execution,
  module import attempts, concrete proof-producing handlers, default/global
  handler registration, subprocess changes, stdout success emission from real
  behavior, parent executor/parser changes, API, MCP, schema, eval, scoring,
  compiler, docs, public-claim, admission, recompile, or result assembly
  changes
- implementation review accepted the slice after one correction
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1084 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `c134b85 Add dynamic import worker request contract`
- Ryan-authorized push completed with release routing through
  `077c91a Sync dynamic import worker request routing`
- release unit is exactly `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_worker.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `c134b85`

Local Python worker stdout success egress contract release:

- `src/context_ir/runtime_probe_worker.py` now has a frozen typed
  `RuntimeProbeLocalPythonWorkerSuccessResponse`
- `serialize_runtime_probe_local_python_worker_success_response(...)` emits
  the existing parent stdout success protocol with deterministic JSON key
  order and no trailing newline
- matching injected worker handlers may return the success response;
  `main(...)` writes deterministic stdout protocol JSON and returns zero
- emitted stdout shape remains compatible with the existing parent parser:
  `runtime_probe_stdout_protocol_revision`, ordered `normalized_payload`, and
  optional `durable_artifact_reference`
- durable-only success is supported
- default `main(...)` with no handlers remains fail-closed with nonzero exit
  status, sanitized stderr, and empty stdout
- malformed stdin, missing handler, duplicate handler, malformed handler,
  handler exception, invalid response, and malformed success metadata paths
  remain fail-closed, nonzero, sanitized, and empty-stdout
- package-root exports remain unchanged
- the release does not add concrete family/form behavior, dynamic import
  execution, repository-code execution, global registration, parent executor
  changes, parent stdout parser changes, API, MCP, schema, eval, scoring,
  compiler, docs, public-claim, admission, recompile, or result assembly
  changes
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1066 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `9c6a3b5 Add worker stdout success egress`
- Ryan-authorized push completed with release routing through
  `0ea7ca5 Sync worker stdout egress release routing`
- release unit is exactly `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_worker.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `9c6a3b5`

Fail-closed local Python worker-side dispatch contract release:

- `src/context_ir/runtime_probe_worker.py` now has frozen typed worker response
  and handler-entry contracts
- the worker dispatches parsed
  `RuntimeProbeLocalPythonWorkerRequestPayload` values by family/form metadata
- default `main(...)` behavior remains fail-closed with no registered
  handlers, nonzero exit status, sanitized stderr, and empty stdout
- matching injected handlers are called only after strict stdin payload parsing
- valid handler responses still fail closed without stdout proof
- missing handler, duplicate handler, malformed handler, handler exception,
  and invalid handler response paths fail closed with deterministic sanitized
  stderr and empty stdout
- package-root exports remain unchanged
- the release does not add concrete family/form behavior, dynamic import
  execution, repository-code execution, stdout success protocol emission,
  global registration, parent executor changes, API, MCP, schema, eval,
  scoring, compiler, docs, public-claim, admission, recompile, or result
  assembly changes
- implementation review accepted the slice first-pass
- combined read-only release gate passed after one continuity correction:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1061 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `7eefba2 Add fail-closed worker dispatch`
- Ryan-authorized push completed with release routing through
  `d3c16d1 Sync worker dispatch release routing`
- release unit is exactly `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_worker.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `7eefba2`

Fail-closed local Python worker ingress release:

- `src/context_ir/runtime_probe_worker.py` now exists as the importable
  `context_ir.runtime_probe_worker` subprocess target module
- the worker exposes a testable `main(...)` entrypoint
- the worker reads stdin and parses request payloads only through
  `parse_runtime_probe_local_python_worker_request_payload(...)`
- valid worker request payloads parse successfully and then fail closed with
  deterministic nonzero exit status, empty stdout, and sanitized stderr
- malformed stdin fails closed with deterministic nonzero exit status, empty
  stdout, and sanitized stderr
- stderr does not leak raw stdin, tracebacks, exception messages, environment
  names, or local path details
- worker output does not emit the success stdout protocol and cannot produce
  observed proof
- package-root exports remain unchanged
- the release does not add concrete handler logic, dynamic import execution,
  worker dispatch registry, stdout protocol extension, global handler
  registration, filesystem IO, subprocess execution in tests, docs, public
  claims, API, MCP, schema, eval, scoring, optimizer, compiler, admission,
  recompile, or result assembly changes
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1054 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `f67e5f8 Add fail-closed runtime probe worker`
- Ryan-authorized push completed with release routing through
  `1cc925a Sync fail-closed worker release routing`
- release unit is exactly `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_worker.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `f67e5f8`

Local Python subprocess stdin execution wiring release:

- `execute_runtime_probe_local_python_subprocess_invocation(...)` now
  materializes `RuntimeProbeLocalPythonWorkerRequestStdinTransport` before
  subprocess launch
- the raw executor passes `stdin_transport.stdin_text` to
  `subprocess.run(...)` through text-mode `input=...`
- existing argv, cwd, child environment, timeout, `shell=False`,
  `capture_output=True`, `text=True`, `check=False`, raw completion
  materialization, and raw executor exception propagation are preserved
- invocation, completion contract revision, worker request payload, and stdin
  transport validation happen before subprocess launch
- invocation/stdin/payload drift is rejected before `subprocess.run(...)`
- success, nonzero completion, timeout, generic exception, malformed stdout,
  handler adapter, and dispatch paths continue through the existing typed
  materializers
- the release does not add worker modules, concrete family/form semantics,
  global registration, temp files, filesystem IO, stdout protocol changes,
  `RuntimeProbeObservedResult` synthesis, result assembly changes, admission,
  recompile, facade, MCP, package-root, schema, eval, scoring, optimizer,
  compiler, docs, or public claims
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1049 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `41f5df9 Pass worker requests through stdin`
- Ryan-authorized push completed with release routing through
  `132647b Sync local Python stdin execution routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `41f5df9`

Local Python worker request stdin transport contract release:

- `RuntimeProbeLocalPythonWorkerRequestStdinTransport` is a frozen
  module-local request handoff contract for the exact text future local-Python
  worker subprocesses receive over stdin
- transports materialize from typed
  `RuntimeProbeLocalPythonSubprocessInvocation` values after revalidating the
  invocation
- materialization internally derives
  `RuntimeProbeLocalPythonWorkerRequestPayload`, serializes it through the
  deterministic strict JSON helper, and parses it back through the strict
  parser as a drift check
- transports preserve invocation identity, the typed payload, deterministic
  stdin text, argv, working directory, ordered Python path entries, timeout
  seconds, request identity, family/form labels, replay seeds, and ordered
  replay payload fields
- direct construction rejects invocation/payload/stdin-text drift, malformed
  stdin text, blank or unsupported transport revision, extra trailing newline
  drift, and attempts to bypass strict payload validation
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not add `subprocess.run(input=...)`, executor behavior
  changes, handler adapter changes, worker modules, concrete family/form
  semantics, temp files, filesystem IO, stdout protocol changes,
  `RuntimeProbeObservedResult` synthesis, result assembly changes, admission,
  recompile, facade, MCP, package-root, schema, eval, scoring, optimizer,
  compiler, docs, or public claims
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1047 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `0a3c4c6 Add local Python worker stdin transport`
- Ryan-authorized push completed with release routing through
  `9a25fbf Sync local Python stdin transport release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `0a3c4c6`

Local Python worker request payload contract release:

- `RuntimeProbeLocalPythonWorkerRequestPayload` is a frozen module-local strict
  JSON request payload contract for future local-Python subprocess worker
  modules
- payloads materialize from typed
  `RuntimeProbeLocalPythonSubprocessInvocation` values after revalidating the
  invocation and carried `RuntimeProbeRunnerRequest`
- payloads preserve request identity, family/form, source-site identity,
  boundary text, reason code, replay target and selector seeds, request replay
  payload fields, runtime assumptions, runner environment, runner assumptions,
  runner contract revision, invocation contract revision, invocation identity,
  argv, working directory, ordered Python path entries, and timeout seconds
- request replay fields must contain exactly one required request identity key,
  including source-site identity, source span, `reason_code`, and
  `boundary_text`
- deterministic strict JSON serialization and parsing helpers reject malformed
  JSON, duplicate JSON keys, non-object payloads, missing or unknown top-level
  keys, invalid enum labels, invalid replay fields, missing required replay
  identity fields, and invocation/payload drift
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not add filesystem IO, stdin/stdout transport wiring,
  subprocess behavior changes, temp files, worker modules, concrete family/form
  semantics, global dispatch registration, `RuntimeProbeObservedResult`
  synthesis, result assembly changes, admission, recompile, facade, MCP,
  package-root, schema, eval, scoring, optimizer, compiler, docs, or public
  claims
- implementation review accepted the slice after two correction passes
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1033 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `4d155ec Add local Python worker payload contract`
- Ryan-authorized push completed with release routing through
  `20d8af3 Sync local Python worker payload release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `4d155ec`

Local Python runner handler adapter release:

- `RuntimeProbeLocalPythonSubprocessHandlerConfig` is a frozen module-local
  handler metadata contract for local-Python subprocess workers
- `make_runtime_probe_local_python_subprocess_handler_entry(...)` returns a
  dispatch-consumable `RuntimeProbeRunnerHandlerEntry`
- configured metadata includes family label, form label, Python executable,
  module name, invocation contract revision, completion contract revision, and
  optional module argv
- produced handlers revalidate runner requests and reject family/form drift
  before subprocess execution
- handlers materialize invocations through existing
  `materialize_runtime_probe_local_python_subprocess_invocation(...)`
- handlers execute and normalize attempts through existing
  `execute_runtime_probe_local_python_subprocess_invocation_attempt(...)`
- module argv order is preserved in the shell-free invocation argv
- success, nonzero, timeout, generic exception, and malformed stdout paths
  continue to flow through existing typed local-Python attempt materializers
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not add concrete family/form probe logic, worker modules,
  global dispatch registration, request payload transport, temp-file or stdin
  IO, `RuntimeProbeObservedResult` synthesis, result assembly changes,
  admission, recompile, facade, MCP, package-root, schema, eval, scoring,
  optimizer, compiler, docs, or public claims
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1009 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `9b9b5cd Add local Python probe handler adapter`
- Ryan-authorized push completed with release routing through
  `2f63f7f Sync local Python handler adapter release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `9b9b5cd`

Local Python executor-to-attempt wrapper release:

- `execute_runtime_probe_local_python_subprocess_invocation_attempt(...)` is a
  module-local helper that consumes typed
  `RuntimeProbeLocalPythonSubprocessInvocation` values plus
  `completion_contract_revision`
- the helper revalidates invocation and completion revision before subprocess
  launch
- execution flows through existing
  `execute_runtime_probe_local_python_subprocess_invocation(...)`
- subprocess timeouts and generic subprocess exceptions map through
  `materialize_runtime_probe_local_python_subprocess_exception_attempt(...)`
- nonzero completions map through
  `materialize_runtime_probe_local_python_process_completion_attempt(...)`
- zero-returncode valid stdout protocol maps through
  `materialize_runtime_probe_local_python_stdout_protocol_result(...)` and
  `materialize_runtime_probe_local_python_stdout_protocol_attempt(...)`
- zero-returncode malformed stdout protocol maps through
  `materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(...)`
- observed success preserves runner request identity, request object,
  execution input, ordered normalized payload, and durable artifact reference
- failure attempts remain non-proof and sanitized without raw stdout, stderr,
  exception message, traceback text, temporary paths, PIDs, or process-local
  data
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not add concrete family/form handlers, dispatch
  registration, `RuntimeProbeObservedResult` synthesis, result assembly
  changes, admission, recompile, facade, MCP, package-root, schema, eval,
  scoring, optimizer, compiler, docs, or public claims
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `999 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `8625186 Execute local Python subprocess attempts`
- Ryan-authorized push completed with release routing through
  `cd103ae Sync local Python executor attempt release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `8625186`

Local Python stdout protocol failure-normalization release:

- `materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(...)`
  is a module-local helper that consumes typed
  `RuntimeProbeLocalPythonProcessCompletion` values plus a parsing or
  validation `Exception`
- the helper requires zero return code at this boundary; nonzero completion
  mapping remains owned by
  `materialize_runtime_probe_local_python_process_completion_attempt(...)`
- the helper revalidates completion, invocation, and runner request before
  materializing the attempt
- the helper returns non-proof `RuntimeProbeExecutionAttempt` values,
  defaulting to `RuntimeProbeResultOutcome.SETUP_FAILED`
- configured non-proof outcomes are supported and `OBSERVED` is rejected
- runner request identity, request object, and execution input are preserved
- failure summary/detail fields are deterministic and sanitized without raw
  stdout, stderr, exception message, traceback text, temporary paths, PIDs, or
  process-local data
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not change stdout protocol parsing, observed-attempt
  materialization, subprocess execution, nonzero completion mapping, executor
  wrapper orchestration, concrete family/form handlers, dispatch registration,
  `RuntimeProbeObservedResult` synthesis, result assembly, admission,
  recompile, facade, MCP, package-root, schema, eval, scoring, optimizer,
  compiler, docs, or public claims
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `993 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `d8cf97b Normalize local Python stdout protocol failures`
- Ryan-authorized push completed with release routing through
  `d5de659 Sync local Python stdout failure release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `d8cf97b`

Local Python stdout protocol observed-attempt materialization release:

- `materialize_runtime_probe_local_python_stdout_protocol_attempt(...)` is a
  module-local helper that consumes typed
  `RuntimeProbeLocalPythonStdoutProtocolResult` values
- the helper revalidates the stdout protocol result, carried completion,
  subprocess invocation, and runner request before materializing the attempt
- the helper returns `RuntimeProbeExecutionAttempt` with
  `RuntimeProbeResultOutcome.OBSERVED`
- runner request identity, request object, execution input, ordered normalized
  payload, and durable artifact reference are preserved
- observed attempts produced by this helper carry no failure summary or failure
  detail fields
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not change subprocess execution, stdout parsing, non-proof
  failure mapping, `RuntimeProbeObservedResult` synthesis, result-batch
  assembly, concrete family/form handlers, dispatch registration, executor
  wrapper orchestration, admission, recompile, facade, MCP, package-root,
  schema, eval, scoring, optimizer, compiler, docs, or public claims
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `985 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `81a3ce3 Materialize local Python observed attempts`
- Ryan-authorized push completed with release routing through
  `cc5ca86 Sync local Python observed attempt release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `81a3ce3`

Local Python stdout/result protocol contract release:

- `RuntimeProbeLocalPythonStdoutProtocolResult` is a frozen module-local
  contract for strict internal local-Python stdout success metadata
- `materialize_runtime_probe_local_python_stdout_protocol_result(...)`
  consumes typed `RuntimeProbeLocalPythonProcessCompletion` values only
- the materializer requires zero return code before parsing stdout success
  metadata
- stdout is parsed as a strict internal JSON object with explicit stdout
  protocol revision, ordered `normalized_payload`, and optional
  `durable_artifact_reference`
- at least one proof channel is required: normalized payload or durable
  artifact reference
- normalized payload order and the carried completion object are preserved
- completion, invocation, and runner-request contracts are revalidated before
  accepting protocol data
- malformed JSON, non-object JSON, missing/blank/unsupported protocol
  revision, unknown top-level keys, malformed payload entries, blank replay
  fields, malformed durable references, empty proof metadata, nonzero
  completions, and request/completion drift are rejected
- both parser and direct frozen-contract construction reject malformed durable
  references
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not synthesize `RuntimeProbeExecutionAttempt` values,
  synthesize observed results, implement concrete family/form handlers,
  register dispatch handlers, add executor wrapper orchestration, or change
  admission, recompile, facade, MCP, package-root, schema, eval, scoring,
  optimizer, compiler, docs, or public claims
- implementation review accepted the slice after one durable-reference
  validation correction
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `982 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `0c4a654 Add local Python stdout protocol contract`
- Ryan-authorized push completed with release routing through
  `d0e9b89 Sync local Python stdout protocol release routing` and post-push
  state through `9277d2b Sync local Python stdout protocol post-push state`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `0c4a654`

Local Python subprocess non-proof attempt normalization release:

- module-local helpers convert local Python subprocess failure facts into typed
  non-proof `RuntimeProbeExecutionAttempt` values
- `subprocess.TimeoutExpired` maps to `TIMED_OUT`
- other local subprocess execution exceptions map to sanitized `CRASHED`
  attempts
- nonzero `RuntimeProbeLocalPythonProcessCompletion.returncode` maps to a
  non-proof attempt, defaulting to `CRASHED`
- configured non-proof outcomes for nonzero completions are supported
- `RuntimeProbeResultOutcome.OBSERVED` is rejected at this helper boundary
- zero-returncode completions reject as deferred
- invocation and completion contracts are revalidated before attempt
  materialization
- produced attempts preserve runner request, request object, and execution
  input identity, and intentionally do not carry invocation or completion
  object identity
- failure summary/detail fields are deterministic and do not leak raw stdout,
  stderr, traceback text, temporary paths, PIDs, or process-local data
- raw executor behavior remains unchanged and still returns raw completions
  while propagating subprocess exceptions
- the release does not parse stdout/stderr, synthesize observed results,
  implement family/form handlers, register handlers, or change admission,
  recompile, facade, MCP, package-root, schema, eval, scoring, optimizer,
  compiler, docs, or public claims
- implementation review accepted the slice after one implementation correction
  and one continuity/spec correction
- combined read-only release gate rerun passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `961 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `5b10728 Normalize local Python subprocess failures`
- Ryan-authorized push completed with `origin/main` advanced through
  `c471fd1 Sync local Python failure normalization release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `5b10728`

Local Python raw subprocess execution boundary release:

- `execute_runtime_probe_local_python_subprocess_invocation(...)` is a
  module-local executor that consumes a validated
  `RuntimeProbeLocalPythonSubprocessInvocation`
- the executor validates `completion_contract_revision` before subprocess
  execution and rejects invalid revision metadata before any child process can
  launch
- execution uses shell-free `subprocess.run(...)` with invocation argv, working
  directory, timeout seconds, text capture, `capture_output=True`,
  `check=False`, and `shell=False`
- the child environment is copied from ambient `os.environ` with deterministic
  `PYTHONPATH` override from ordered `invocation.python_path_entries`
- raw return code, stdout text, and stderr text are materialized through
  `materialize_runtime_probe_local_python_process_completion(...)`
- subprocess exceptions propagate for later mapping slices
- the release remains raw and non-interpreting: no stdout/stderr parsing, no
  return-code outcome normalization, no timeout-to-attempt/result mapping, no
  `RuntimeProbeExecutionAttempt` synthesis, no observed/non-proof result
  synthesis, no family/form handler implementation or dispatch registration,
  and no admission, recompile, facade, MCP, package-root, schema, eval,
  scoring, optimizer, compiler, benchmark, docs, or public-claim changes
- implementation review accepted the slice after one correction for pre-run
  completion revision validation
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `954 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `d0a009b Execute local Python subprocess invocations`
- Ryan-authorized push completed with `origin/main` advanced through
  `8ae13f6 Sync local Python subprocess execution release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `d0a009b`

Local Python process completion contract release:

- `RuntimeProbeLocalPythonProcessCompletion` is a frozen module-local raw
  completion contract for future local Python subprocess execution
- `materialize_runtime_probe_local_python_process_completion(...)` revalidates
  the carried invocation and materializes raw returncode/stdout/stderr fields
  without executing or interpreting anything
- the contract preserves invocation identity, argv, working directory, ordered
  Python path entries, timeout seconds, raw return code, raw stdout/stderr
  text, completion contract revision, and request replay payload fields
- empty stdout/stderr and nonzero return codes remain valid uninterpreted raw
  process facts
- the release remains non-executing and non-interpreting: no subprocess import
  or execution, no timeout enforcement, no stdout/stderr parsing, no
  `RuntimeProbeExecutionAttempt` synthesis, no observed/non-proof result
  synthesis, no family/form handler implementation or dispatch registration,
  and no admission, recompile, facade, MCP, package-root, schema, eval,
  scoring, optimizer, compiler, benchmark, or public-claim changes
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `949 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `e9f87fc Add local Python process completion contract`
- Ryan-authorized push completed with `origin/main` advanced through
  `928ea13 Sync local Python process completion routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `e9f87fc`

Local Python subprocess invocation contract release:

- `RuntimeProbeLocalPythonSubprocessInvocation` is a frozen module-local
  shell-free invocation contract for future local Python runtime probe handlers
- `materialize_runtime_probe_local_python_subprocess_invocation(...)`
  revalidates `RuntimeProbeRunnerRequest`, derives the existing local Python
  environment context, validates an absolute Python executable, validates
  dotted module names and argv tokens, and builds deterministic `python -m ...`
  argv without executing anything
- the contract preserves the original runner request, derived environment
  context, working directory, ordered Python path entries, timeout seconds,
  invocation contract revision, and replay payload fields
- blank or whitespace-only invocation contract revisions reject through tested
  validation
- the release remains non-executing: no subprocess import or execution, no
  in-process repository imports, no timeout enforcement, no stdout/stderr
  parsing, no observed-result synthesis, no family/form handler implementation
  or dispatch registration, and no admission, recompile, facade, MCP,
  package-root, schema, eval, scoring, optimizer, compiler, benchmark, or
  public-claim changes
- implementation review accepted the slice first-pass after one audit
  correction for the missing blank-revision negative test
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `939 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `ea6ff8e Add local Python subprocess invocation contract`
- Ryan-authorized push completed with `origin/main` advanced through
  `07cc3ce Sync local Python invocation release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `ea6ff8e`

Prior pushed runtime probe execution-input materialization release:

- `RuntimeProbeExecutionInput` is a frozen internal non-executing work item for
  one planned runtime probe request
- `RuntimeProbeExecutionInputBatch` is a frozen ordered internal batch for one
  runtime request plan
- `materialize_runtime_probe_execution_input_batch(...)` materializes
  replay-ready inputs from a `RuntimeProbeRequestPlan`,
  `RepositorySnapshotBasis`, probe contract revision, and explicit runtime
  assumptions
- materialization preserves plan ID, request IDs, request object identity,
  source-site identity, family/form labels, replay target and selector seeds,
  deterministic plan order, and the existing `RuntimeProbeReplayArtifact`
  replay metadata contract
- replay inputs carry plan/request identity, subject identity, source site/span,
  reason code, boundary text, family/form, replay target seed, and replay
  selector seed
- plan/request drift, duplicate request IDs, blank probe metadata, empty runtime
  assumptions, replay metadata drift, and batch/input plan mismatch reject
  through typed constructors or materialization gates
- empty request plans remain valid and deterministic when explicit runtime
  assumptions and probe metadata are supplied
- the helper remains internal to `context_ir.runtime_probe_execution`; no
  package-root, tool facade, MCP, JSON/schema, serialization, eval, scoring,
  optimizer, compiler, winner-selection, product, benchmark, or public-claim
  surface changed
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting
    `177 passed`
  - Gate 2 full regression passed, including full pytest reporting
    `857 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, no untracked drift, and clean `git diff --check`
- local commit creation completed at
  `cfed3c7 Add runtime probe execution input materialization`
- Ryan-authorized push completed with `origin/main` advanced through
  `d2e3e81 Sync runtime probe execution release routing`
- release files are `src/context_ir/runtime_probe_execution.py` and
  `tests/test_runtime_probe_execution.py`, plus control continuity in
  `PLAN.md` and `BUILDLOG.md`
- release-gate status is no-active-gate for `cfed3c7`

Runtime probe execution-attempt result assembly release:

- `RuntimeProbeExecutionAttempt` is a frozen internal normalized runner-output
  record for one materialized `RuntimeProbeExecutionInput`
- `assemble_runtime_probe_result_batch_from_execution_attempts(...)` converts
  a complete typed attempt set for a `RuntimeProbeExecutionInputBatch` into
  deterministic input-batch order `RuntimeProbeResultBatch`
- observed attempts become `RuntimeProbeObservedResult` only when they carry
  normalized payload or durable artifact reference
- crashed, timed-out, missing-environment, and setup-failed attempts become
  `RuntimeProbeNonProofResult` and remain non-proof
- assembly preserves plan ID, request IDs, request object identity, planned
  execution-input identity, replay artifact identity, input-batch order, and
  result-batch identity
- unplanned, duplicate, missing, plan-drifted, input-drifted, request-drifted,
  blank, malformed, and unsupported attempt metadata rejects through typed
  constructors or assembly gates
- exports remain module-local to `context_ir.runtime_probe_execution.__all__`;
  package-root, tool facade, MCP, JSON/schema, serialization, eval, scoring,
  optimizer, compiler, winner-selection, product, benchmark, and public-claim
  surfaces remain unchanged
- implementation review accepted the slice first-pass in workspace-only state
- focused validation passed, including targeted pytest reporting `189 passed`
- corrected combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting `189 passed`
  - Gate 2 full regression passed, including full pytest reporting
    `869 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, no untracked files, no ref drift, and clean
    `git diff --check`
- local commit creation completed at
  `86be8d7 Assemble runtime probe execution attempts`
- Ryan-authorized push completed with `origin/main` advanced through
  `44b05c8 Sync runtime probe attempt release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-unit-audit, full-regression, commit-gating, staging, and local commit
  are complete for `86be8d7`
- release-gate status is no-active-gate for `86be8d7`

Runtime probe result-batch recompile bridge release:

- `RuntimeProbeResultBatchRecompileApplication` is a frozen internal envelope
  carrying result-batch admission, preserved non-proof results, runtime
  observation application, and semantic recompile result
- `apply_runtime_probe_result_batch_for_diagnostic_and_recompile(...)` requires
  the diagnostic's planned runtime probe request plan, admits the
  `RuntimeProbeResultBatch` through the existing result-batch admission bridge,
  attaches only observed proof-bearing results, preserves non-proof results
  separately, and recompiles with the updated program
- non-proof-only and partial mixed batches keep non-proof results out of
  runtime-backed proof while preserving deterministic plan-order admissions
- existing plan, request, source-site, family/form, duplicate result, negative
  budget, and missing compile-context gates propagate through the composed path
- the helper remains internal to `context_ir.runtime_observation_recompile`;
  package-root, tool facade, MCP, JSON/schema, serialization, eval, scoring,
  optimizer, compiler, winner-selection, docs, and public-claim surfaces remain
  unchanged
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting
    `232 passed`
  - Gate 2 full regression passed, including full pytest reporting
    `847 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, no untracked files, and clean `git diff --check`
- local commit creation completed at
  `591c09b Compose runtime probe result batch recompile`
- Ryan-authorized push completed with `origin/main` advanced through
  `5913bf0 Sync runtime probe batch recompile release routing`
- release files are
  `src/context_ir/runtime_observation_recompile.py` and
  `tests/test_runtime_observation_recompile.py`, plus control continuity in
  `PLAN.md` and `BUILDLOG.md`
- release-gate status is no-active-gate for `591c09b`

Prior pushed runtime probe result admission bridge release:

- `admit_runtime_probe_result_batch_for_plan(...)` bridges
  `RuntimeProbeResultBatch` into deterministic plan-ordered
  `RuntimeObservationAdmission` records
- only proof-bearing `RuntimeProbeObservedResult` values become typed
  `RuntimeObservation` values
- `RuntimeProbeNonProofResult` values are preserved separately as non-proof and
  are never admitted as runtime-backed proof
- plan ID, request ID, carried request identity, source-site identity, and
  family/form compatibility are revalidated
- probe identity, probe contract revision, repository snapshot basis, replay
  target/selector, replay inputs, runtime assumptions, normalized payload, and
  durable artifact reference are copied into the existing typed observation
  shape
- required `RuntimeAttachmentLink` values are derived deterministically from
  result identity or durable artifact reference
- the bridge remains internal to
  `context_ir.runtime_observation_admission`; package-root, facade, MCP, JSON
  schema, serialization, eval, scoring, optimizer, compiler, winner-selection,
  docs, and public-claim surfaces remain unchanged
- implementation review accepted the slice after 1 correction
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting
    `174 passed`
  - Gate 2 full regression passed, including full pytest reporting
    `842 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation completed at
  `ccd417a Add runtime probe result admission bridge`
- Ryan-authorized push completed with `origin/main` advanced through
  `6023220 Sync runtime probe admission release routing`

Released four-file unit:

- `src/context_ir/runtime_observation_admission.py`
- `tests/test_runtime_observation_admission.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `ccd417a`.

Prior pushed runtime probe execution-result/replay-artifact contract:

Released runtime probe execution-result/replay-artifact contract:

- `RuntimeProbeReplayField` provides typed replay and payload fields without
  `Any`
- `RuntimeProbeReplayArtifact` records stable probe identity, probe contract
  revision, repository snapshot basis, replay target/selector, replay inputs,
  and runtime assumptions
- `RuntimeProbeObservedResult` preserves `plan_id`, `request_id`, and carried
  `RuntimeProbeRequest` identity, validates request-ID drift, requires replay
  inputs/runtime assumptions, and requires normalized payload or durable
  artifact reference
- `RuntimeProbeNonProofResult` represents crash, timeout, missing-environment,
  and setup-failure outcomes without making them admissible runtime-backed
  proof
- `RuntimeProbeResultBatch` keeps ordered mixed proof and non-proof outcomes
  under one plan ID and rejects plan drift or duplicate request IDs
- the new contract is frozen and exported only from module-local
  `context_ir.runtime_probe_results.__all__`
- no probe execution, `RuntimeObservation` conversion, provenance attachment,
  `SemanticProgram` mutation, `tool_facade.py`, `mcp_server.py`,
  `context_ir/__init__.py`, eval, JSON schema, public claims, package-root,
  MCP, or public/API surface changed
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting
    `111 passed`
  - Gate 2 full regression passed, including full pytest reporting
    `833 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation and Ryan-authorized push completed at
  `eb6def0 Add runtime probe result contracts`

Released four-file unit:

- `src/context_ir/runtime_probe_results.py`
- `tests/test_runtime_probe_results.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `eb6def0`.

Prior released typed facade runtime recompile:


- `SemanticRuntimeObservationRecompileRequest` and
  `SemanticRuntimeObservationRecompileResponse` provide a frozen typed
  `context_ir.tool_facade` surface for applying typed runtime observations
  before semantic recompile
- `recompile_repository_context_with_runtime_observations(...)` delegates to
  `apply_runtime_observations_for_diagnostic_and_recompile(...)`
- delegation uses the previous `SemanticContextResponse` program and compile
  result
- optional `embed_fn` is forwarded
- response mirror fields are guarded against drift from the underlying runtime
  observation application and semantic recompile result
- existing admission, application, and recompile gates propagate through the
  facade
- empty observations preserve original-program application behavior while still
  recompiling
- successful runtime observation satisfaction does not re-plan the already
  satisfied diagnostic runtime request
- `context_ir.mcp_server`, `context_ir.__init__`, package-root exports, and
  JSON serialization remain unchanged
- no probe execution, runtime observation collection, execution-result
  contract, schema, scoring policy, compiler contract, optimizer,
  winner-selection, eval, product, benchmark, or public-claim surface changed
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting `58 passed`
  - Gate 2 full regression passed, including full pytest reporting `816 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation and Ryan-authorized push completed at
  `8ac3b46 Add typed runtime recompile facade`

Released four-file unit:

- `src/context_ir/tool_facade.py`
- `tests/test_tool_facade.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `8ac3b46`.

Released runtime observation recompile composition:

- `RuntimeObservationRecompileApplication` is a frozen internal result
  envelope in `src/context_ir/runtime_observation_recompile.py`
- `apply_runtime_observations_for_diagnostic_and_recompile(...)` composes
  `apply_runtime_observations_for_diagnostic(...)` with
  `recompile_semantic_context(...)`
- the helper applies observations through the existing diagnostic-gated
  admission/application path, then recompiles with
  `application.updated_program`
- optional `embed_fn` is forwarded to semantic recompile
- the returned envelope carries both the runtime observation application and
  the semantic recompile result
- successful runtime observation satisfaction does not re-plan the already
  satisfied diagnostic runtime request
- empty observations preserve existing empty-application behavior and
  recompile the original program
- missing diagnostic plans, unmatched observation sites, duplicate observation
  sites, family/form mismatches, negative budget deltas, and missing prior
  compile context reject through existing gates
- input `SemanticProgram`, previous compile result, diagnostic, plan, request,
  and observations are not mutated
- the new helper is exported only from module-local `__all__`; no package-root,
  analyzer, tool-facade, or MCP surface is widened
- no probe execution, execution-result contract, runtime observation
  collection, eval, schema, scoring policy, compiler contract, optimizer,
  winner-selection, product, public benchmark, or public-claim surface changed
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting `87 passed`
  - Gate 2 full regression passed, including full pytest reporting `811 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation and Ryan-authorized push completed at
  `b279b00 Compose runtime observation recompile flow`

Released four-file unit:

- `src/context_ir/runtime_observation_recompile.py`
- `tests/test_runtime_observation_recompile.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `b279b00`.

Prior released diagnostic trace refresh:

- `diagnose_semantic_miss(previous_result, evidence, current_program)` now
  classifies runtime support from the supplied current `SemanticProgram` using
  diagnose-visible provenance
- `previous_result` remains the source for prior selected detail, preserving
  prior depth/status semantics
- runtime-backed support remains additive: unsupported and frontier boundaries
  keep their primary non-proof tiers
- stale prior warning or selection trace summaries no longer make
  post-application diagnostics deny or fabricate current runtime support
- already satisfied diagnostic runtime requests are not planned again
- recompile with an updated program compiles that updated program and carries
  attached runtime support in selected trace summaries when selected
- no probe execution, execution-result contract, runtime observation
  collection, analyzer/tool-facade behavior, package-root API, MCP, eval,
  schema, scoring policy, compiler contract, winner-selection, product,
  public benchmark, or public-claim surface changed
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact five-file release unit
  - focused validation passed, including targeted pytest reporting `101 passed`
  - Gate 2 full regression passed, including full pytest reporting `806 passed`
  - Gate 3 commit-gating passed with the exact five-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation and Ryan-authorized push completed at
  `74aadd7 Refresh diagnostic runtime trace support`

Released five-file unit:

- `src/context_ir/semantic_diagnostics.py`
- `src/context_ir/semantic_optimizer.py`
- `tests/test_semantic_diagnostics.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `74aadd7`.

Prior released diagnostic runtime observation application:

- `RuntimeObservationApplication` is a frozen internal result envelope in
  `src/context_ir/runtime_observation_admission.py`
- `apply_runtime_observations_for_diagnostic(program, diagnostic, observations)`
  composes `admit_runtime_observations_for_diagnostic(...)` with
  `attach_admitted_runtime_observations(...)`
- application requires the diagnostic's planned runtime probe request plan
  through the existing diagnostic admission path
- admissions preserve diagnostic plan order, request IDs, request object
  identity, and observation object identity
- empty admitted batches return the original `SemanticProgram` object through
  the existing attachment behavior
- missing plans, unmatched observation source sites, duplicate observation
  source sites, and family/form mismatches reject through existing gates
- input `SemanticProgram`, `SemanticDiagnosticResult`, planned requests, and
  observations are not mutated
- no probe execution, execution-result contract, runtime observation
  collection, analyzer/tool-facade behavior, semantic recompile behavior,
  package-root API, MCP, eval, schema, scoring, optimizer, compiler,
  winner-selection, product, public benchmark, or public-claim surface changed
- implementation review accepted the slice first-pass
- control-lane focused validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_observation_admission.py tests/test_runtime_observation_admission.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_observation_admission.py tests/test_runtime_observation_admission.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_observation_admission.py tests/test_runtime_acquisition.py tests/test_runtime_probe_requests.py tests/test_semantic_diagnostics.py -v`
    reporting `165 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting `165 passed`
  - Gate 2 full regression passed, including full pytest reporting `805 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation and Ryan-authorized push completed at
  `95f7545 Apply diagnostic runtime observations`

Released four-file unit:

- `src/context_ir/runtime_observation_admission.py`
- `tests/test_runtime_observation_admission.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `95f7545`.

Current route:

- Runtime probe result-batch recompile bridge is pushed at
  `591c09b Compose runtime probe result batch recompile` with no active gate.
- Runtime probe result admission bridge is pushed at
  `ccd417a Add runtime probe result admission bridge` with no active gate.
- Runtime probe execution-result/replay-artifact contract is pushed at
  `eb6def0` with no active gate.
- Typed facade runtime recompile is pushed at `8ac3b46` with no active gate.
- Runtime probe execution-input materialization is pushed at
  `cfed3c7 Add runtime probe execution input materialization` with no active
  gate.
- Runtime probe execution-attempt result assembly is pushed at
  `86be8d7 Assemble runtime probe execution attempts` with no active gate.
- Runtime probe runner-request materialization is pushed at
  `68a8e73 Materialize runtime probe runner requests` with no active gate.
  The release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- Combined read-only release gate passed with no findings for that exact
  four-file runner-request materialization unit, and Ryan-authorized push is
  complete.
- Runtime probe runner-request attempt/result assembly is pushed at
  `3363929 Assemble runtime probe runner request attempts` with no active
  gate. The release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- Combined read-only release gate passed with no findings for that exact
  four-file runner-request attempt/result assembly unit, and Ryan-authorized
  push is complete.
- Runtime probe diagnostic runner-request preparation is pushed at
  `fd0f6d8 Prepare runtime probe diagnostic runner requests` with no active
  gate. The release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- The combined read-only release gate passed with no findings for that exact
  four-file diagnostic runner-request preparation unit: Gate 1 release-unit
  audit passed, focused validation passed with `205 passed`, Gate 2 full
  regression passed with `885 passed`, and Gate 3 commit-gating passed.
- Ryan-authorized push is complete for the diagnostic runner-request
  preparation release, with `origin/main` advanced through
  `74d84fb Sync runtime probe diagnostic runner request release routing`.
- Runtime probe runner-callable attempt collection is pushed at
  `32f6220 Collect runtime probe runner attempts` with no active gate. The
  release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- The combined read-only release gate passed with no findings for that exact
  four-file runner-callable attempt collection unit: Gate 1 release-unit audit
  passed, focused validation passed with `211 passed`, Gate 2 full regression
  passed with `891 passed`, and Gate 3 commit-gating passed.
- Ryan-authorized push is complete for the runner-callable attempt collection
  release, with `origin/main` advanced through
  `e9b5b5a Sync runtime probe runner attempt collection release routing`.
- Runtime probe diagnostic runner-callable recompile bridge is pushed at
  `74fb275 Compose runtime probe runner callable recompile` with no active
  gate. The release unit is exactly
  `src/context_ir/runtime_observation_recompile.py`,
  `tests/test_runtime_observation_recompile.py`, `PLAN.md`, and
  `BUILDLOG.md`.
- Control-lane focused validation passed for that workspace-only unit:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_observation_recompile.py tests/test_runtime_observation_recompile.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_observation_recompile.py tests/test_runtime_observation_recompile.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_observation_recompile.py tests/test_runtime_observation_admission.py tests/test_runtime_probe_execution.py tests/test_runtime_probe_results.py tests/test_runtime_probe_requests.py tests/test_public_api.py tests/test_mcp_server.py tests/test_tool_facade.py -v`
    reporting `215 passed`
  - `git diff --check`
- The combined read-only release gate passed with no findings for that exact
  four-file diagnostic runner-callable recompile bridge unit: Gate 1
  release-unit audit passed, focused validation passed with `215 passed`,
  Gate 2 full regression passed with `895 passed`, and Gate 3 commit-gating
  passed.
- Local commit creation completed at
  `74fb275 Compose runtime probe runner callable recompile`.
- Ryan-authorized push completed with `origin/main` advanced through
  `f463df7 Sync runtime probe callable recompile release routing`.
- Release-gate status is no-active-gate for `74fb275`.
- Runtime probe runner failure-normalization adapter is pushed at
  `93456b6 Normalize runtime probe runner failures` with no active gate. The
  release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- Control-lane focused validation passed for that workspace-only unit:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_execution.py tests/test_runtime_probe_execution.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_execution.py tests/test_runtime_probe_execution.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_execution.py tests/test_runtime_probe_results.py tests/test_runtime_probe_requests.py tests/test_runtime_observation_admission.py tests/test_runtime_observation_recompile.py tests/test_public_api.py tests/test_mcp_server.py tests/test_tool_facade.py -v`
    reporting `223 passed`
  - `git diff --check`
- The combined read-only release gate passed with no findings for that exact
  four-file runtime probe runner failure-normalization adapter unit: Gate 1
  release-unit audit passed, focused validation passed with `223 passed`,
  Gate 2 full regression passed with `903 passed`, and Gate 3 commit-gating
  passed.
- Local commit creation completed at
  `93456b6 Normalize runtime probe runner failures`.
- Ryan-authorized push completed with `origin/main` advanced through
  `4f13fac Sync runtime probe failure normalization routing`.
- Release-gate status is no-active-gate for `93456b6`.
- The accepted slice adds an internal
  runtime probe runner failure-normalization adapter in
  `src/context_ir/runtime_probe_execution.py` and
  `tests/test_runtime_probe_execution.py`. This route preserves the
  strict runner-callable path while adding an explicit opt-in wrapper that
  converts runner-raised exceptions into typed non-proof
  `RuntimeProbeExecutionAttempt` values. It does not implement subprocess
  execution, in-process repository probe execution, timeout enforcement,
  family/form-specific probe logic, admission or recompile rule changes,
  facade/MCP/package-root export, schema, eval, scoring, optimizer, compiler,
  benchmark, or public claims.
- Runtime probe runner dispatch table implementation slice is accepted
  first-pass in workspace-only state. It adds an internal frozen typed
  family/form handler registry and dispatching `RuntimeProbeRunnerCallable`.
  Missing handlers produce deterministic non-proof attempts rather than
  runtime-backed proof. Focused control-lane validation passed with
  `232 passed`.
- The combined read-only release gate passed with no findings for the exact
  four-file runtime probe runner dispatch table release unit:
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
  Focused validation passed with `232 passed`; full regression passed with
  `912 passed`; commit-gating passed.
- Local commit creation completed at
  `3751df1 Add runtime probe runner dispatch table`.
- Ryan-authorized push completed with `origin/main` advanced through
  `d7fe447 Sync runtime probe dispatch routing`.
- Release-gate status is no-active-gate for `3751df1`.
- Runtime probe runner environment context implementation slice is accepted
  first-pass in workspace-only state. It adds a frozen typed local Python
  environment context and derivation helper in
  `src/context_ir/runtime_probe_execution.py`, with focused tests in
  `tests/test_runtime_probe_execution.py`. Focused control-lane validation
  passed with `163 passed`.
- Proposed release unit is exactly:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release state for the environment context unit:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes, full pytest `925 passed`
  - commit-gating-cleared: yes
  - staged: no
  - locally committed at `f75196e Add runtime probe runner environment context`
  - pushed with `origin/main` advanced through
    `646298b Sync runtime probe environment context local routing`
  - release-gate status is no-active-gate
  - next route: select the next bounded control action after the pushed release
- Do not route `591c09b`, `ccd417a`, `eb6def0`, `8ac3b46`, `b279b00`,
  `74aadd7`, `95f7545`,
  `35c440d`, `f5c8df0`, `8706f2e`, `b0a5ec5`, `6d5fc47`, `fce09b0`,
  `7c46f48`, `4ba06ad`, `97dc0f6`, `744bf0e`, `3df02c6`, `49fa461`,
  `a819cf5`, `2e448ea`, `f6c66e4`, or `546a4da` back to docs review,
  release-unit audit, focused validation, full regression, commit-gating,
  staging, local commit creation, or push absent new findings
- Push remains Ryan-gated for any future release

Released planned runtime probe request plan source-site indexing:

- `index_runtime_probe_request_plan_by_source_site(plan)` indexes a
  `RuntimeProbeRequestPlan` by the same source-site identity tuple used by
  runtime acquisition matching
- the helper preserves request object identity and plan insertion order
- full plans, diagnostic-filtered plans, and empty plans are supported
- duplicate source-site ambiguity raises `ValueError`
- request IDs, plan IDs, plan order, planned-only status, and empty-plan
  behavior are preserved
- tests cover full, diagnostic-filtered, and empty plans; duplicate sites;
  request/plan ID stability; planned-only status; object identity; insertion
  order; and non-mutation of the plan
- the helper is exported only from module-local
  `context_ir.runtime_probe_requests.__all__`; no package-root export is added
- no probe execution, execution-result contract, observation-admission
  contract, runtime provenance attachment, analyzer/tool-facade behavior, MCP,
  package-root API, eval, schema, scoring, optimizer, compiler,
  winner-selection, product, public benchmark, or public-claim surface changed
- implementation review accepted the slice first-pass in workspace-only state
- control-lane focused validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_requests.py tests/test_semantic_diagnostics.py -v`
    reporting `41 passed`
  - `git diff --check`
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `41 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `746 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Local commit creation and Ryan-authorized push completed at
  `6d5fc47 Index runtime probe plans by source site`

Release-gate status is no-active-gate for
`6d5fc47 Index runtime probe plans by source site`. Do not route `6d5fc47`
back to docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Released semantic diagnostic runtime probe request plan surfacing:

- `SemanticDiagnosticResult` now has optional
  `planned_runtime_probe_request_plan`
- the new field is typed through `TYPE_CHECKING` to avoid runtime import cycles
- `SemanticDiagnosticResult` rejects mismatches between
  `planned_runtime_probe_request_plan.requests` and
  `planned_runtime_probe_requests`
- `diagnose_semantic_miss(...)` derives the deterministic diagnostic request
  plan and sets `planned_runtime_probe_requests` from `plan.requests`
- ungrounded and requestless diagnostics expose the deterministic empty plan
- `recompile_semantic_context(...)` carries the diagnostic plan through
  `result.diagnostic`
- tests cover non-empty plans, empty plans, stable request IDs and plan IDs,
  mismatch rejection, and recompile carry-through
- no probe execution, execution-result contract, observation-admission
  contract, runtime provenance attachment, status widening,
  request-ID/plan-ID derivation change, `RuntimeProbeRequestPlan` contract
  change, `SemanticProgram` mutation, analyzer/tool facade, MCP,
  package-root export, eval, schema, scoring, optimizer, compiler,
  winner-selection, product, public benchmark, or public-claim surface changed
- Implementation review accepted the slice first-pass in workspace-only state
- Control-lane focused validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/semantic_types.py src/context_ir/semantic_diagnostics.py tests/test_semantic_diagnostics.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/semantic_types.py src/context_ir/semantic_diagnostics.py tests/test_semantic_diagnostics.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_semantic_diagnostics.py tests/test_runtime_probe_requests.py -v`
    reporting `37 passed`
  - `git diff --check`
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `37 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `742 passed`
  - Gate 3 commit-gating passed and approved the exact five-file unit
- Local commit creation and Ryan-authorized push completed at
  `7c46f48 Surface semantic diagnostic probe plans`

Release-gate status is no-active-gate for
`7c46f48 Surface semantic diagnostic probe plans`. Do not route `7c46f48` back
to docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Prior pushed source/contract release authority is
`744bf0e Add runtime probe request plans`. It supersedes the workspace-only
planned runtime probe request plan release-gate route for active control
routing only. Live git refs and worktree state must still be verified from git
during control intake.

Repo-backed release truth verified during post-push continuity sync: branch
`main`, `HEAD` and `origin/main` at
`744bf0e Add runtime probe request plans`, clean worktree, and nothing staged.

Released planned runtime probe request plan contract:

- `RuntimeProbeRequestPlan` is a frozen internal planned-only request batch
  envelope
- Internal contract version is `runtime_probe_request_plan:v1`
- `build_runtime_probe_request_plan(requests)` preserves input request order
  as a tuple
- The plan exposes ordered `request_ids` from stable
  `RuntimeProbeRequest.request_id`
- `plan_id` is deterministic over the contract version and ordered request IDs
- Duplicate request IDs raise `ValueError` through the existing request ID
  indexer path
- Empty plans are valid and deterministic
- The helper and plan type are exported only from module-local
  `context_ir.runtime_probe_requests.__all__`; no package-root export is added
- Tests cover full plans, empty plans, duplicate-ID rejection,
  diagnostic-filtered plans, ID/order stability, and input purity
- The slice does not execute probes, add execution-result or
  observation-admission contracts, attach runtime provenance, add statuses,
  change request-ID derivation, mutate `SemanticProgram`, mutate diagnostics,
  mutate unsupported/frontier/provenance state, change compile/recompile
  behavior, or widen analyzer, tool facade, MCP, package-root exports, eval,
  schema, scoring, optimizer, compiler, winner-selection, product, public
  benchmark, or public-claim surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `33 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `738 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Control-lane focused validation before release gate passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_requests.py tests/test_semantic_diagnostics.py -v`
    reporting `33 passed`
  - `git diff --check`
- Local commit creation and Ryan-authorized push completed at
  `744bf0e Add runtime probe request plans`

Release-gate status is no-active-gate for
`744bf0e Add runtime probe request plans`. Do not route `744bf0e` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Prior pushed source/contract release authority is
`3df02c6 Index runtime probe requests by ID`. It supersedes the
workspace-only planned runtime probe request ID indexing release-gate route for
active control routing only. Live git refs and worktree state must still be
verified from git during control intake.

Repo-backed release truth verified during post-push continuity sync: branch
`main`, `HEAD` and `origin/main` at
`3df02c6 Index runtime probe requests by ID`, clean worktree, and nothing
staged.

Released planned runtime probe request ID indexing:

- `index_runtime_probe_requests_by_id(requests)` returns planned runtime probe
  requests keyed by stable `RuntimeProbeRequest.request_id`
- Input iteration order is preserved through normal dictionary insertion order
- Duplicate request IDs raise `ValueError`
- The helper is exported only from module-local
  `context_ir.runtime_probe_requests.__all__`; no package-root export is added
- Tests cover full-plan indexing, key order, duplicate rejection, no mutation,
  and diagnostic-filtered request indexing
- The slice does not execute probes, add execution-result or
  observation-admission contracts, attach runtime provenance, add statuses,
  change request-ID derivation, mutate `SemanticProgram`, mutate diagnostics,
  mutate unsupported/frontier/provenance state, change compile/recompile
  behavior, or widen analyzer, tool facade, MCP, package-root exports, eval,
  schema, scoring, optimizer, compiler, winner-selection, product, public
  benchmark, or public-claim surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `29 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `734 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Control-lane focused validation before release gate passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_requests.py tests/test_semantic_diagnostics.py -v`
    reporting `29 passed`
  - `git diff --check`
- Local commit creation and Ryan-authorized push completed at
  `3df02c6 Index runtime probe requests by ID`

Release-gate status is no-active-gate for
`3df02c6 Index runtime probe requests by ID`. Do not route `3df02c6` back to
docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Prior pushed source/contract release authority is
`49fa461 Add runtime probe request identities`. It supersedes the
workspace-only post-`bea0a1a` stable planned runtime probe request identity
release-gate route for active control routing only. Live git refs and worktree
state must still be verified from git during control intake.

Repo-backed release truth verified during post-push continuity sync: branch
`main`, `HEAD` and `origin/main` at
`49fa461 Add runtime probe request identities`, clean worktree, and nothing
staged.

Released stable planned runtime probe request identity:

- `RuntimeProbeRequest.request_id` is a computed stable internal identity for
  planned runtime probe requests
- Request IDs are SHA-256 based and derived from canonical planned-request
  identity fields only: subject identity, source site, reason code, boundary
  text, family/form labels, and replay target/selector seeds
- Constructor call sites are unchanged
- IDs are deterministic across repeated derivation from the same program and
  unique across a derived request set
- Diagnostic-filtered requests preserve the same IDs as their underlying
  planned requests
- Tests cover repeated-derivation stability, uniqueness, diagnostic filtering
  preservation, and ID presence across all currently supported runtime probe
  families
- The slice does not execute probes, add execution-result or
  observation-admission contracts, attach runtime provenance, add statuses,
  mutate `SemanticProgram`, mutate diagnostics, mutate unsupported/frontier/
  provenance state, change compile/recompile behavior, or widen analyzer,
  tool facade, MCP, package-root exports, eval, schema, scoring, optimizer,
  compiler, winner-selection, product, public benchmark, or public-claim
  surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `27 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `732 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Local commit creation and Ryan-authorized push completed at
  `49fa461 Add runtime probe request identities`

Release-gate status is no-active-gate for
`49fa461 Add runtime probe request identities`. Do not route `49fa461` back to
docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Prior pushed source/contract release authority is
`a819cf5 Surface diagnostic runtime probe requests`. It supersedes the
workspace-only post-`e94cd5d` diagnose/recompile planned runtime probe request
consumption release-gate route for active control routing only. Live git refs
and worktree state must still be verified from git during control intake.

Repo-backed release truth verified during post-push continuity sync: branch
`main`, `HEAD` and `origin/main` at
`a819cf5 Surface diagnostic runtime probe requests`, clean worktree, and
nothing staged.

Released diagnose/recompile planned runtime probe request consumption:

- `SemanticDiagnosticResult` now carries
  `planned_runtime_probe_requests` as a planned-only diagnostic result
  contract
- The result contract is typed without runtime import cycles and guarded so
  planned requests must target grounded diagnostic boundaries that still need
  runtime-backed support
- `diagnose_semantic_miss(...)` derives planned runtime probe requests through
  the existing `derive_diagnostic_runtime_probe_requests(program, diagnostic)`
  bridge after boundary classification
- `recompile_semantic_context(...)` carries the diagnostic result through
  unchanged via `result.diagnostic`
- Tests cover attachable omitted dynamic import, attached runtime support,
  non-attachable unsupported boundaries, heuristic frontier, statically proved
  units, ungrounded evidence, and mutation-free recompile carry-through
- The slice does not execute probes, attach runtime provenance, mutate
  `SemanticProgram`, mutate previous compile results, create dependency edges,
  add selected symbols or units, or widen analyzer, tool facade, package-root
  export, MCP, eval, schema, scoring, optimizer, compiler, winner-selection,
  product, public benchmark, or public-claim surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `27 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `732 passed`
  - Gate 3 commit-gating passed and approved the exact five-file unit
- Local commit creation and Ryan-authorized push completed at
  `a819cf5 Surface diagnostic runtime probe requests`

Release-gate status is no-active-gate for
`a819cf5 Surface diagnostic runtime probe requests`. Do not route `a819cf5`
back to docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Prior route superseded by the pushed `49fa461` request-ID release above:

- The bounded post-`a819cf5` North Star planning/control decision is complete;
  it selected stable planned runtime probe request identity as the next
  smallest meaningful capability slice; that slice is now released at
  `49fa461 Add runtime probe request identities`
- Do not route `49fa461`, `a819cf5`, `2e448ea`, `f6c66e4`, or `546a4da` back
  to docs review, release-unit audit, focused validation, full regression,
  commit-gating, staging, local commit creation, or push absent new findings
- Push remains Ryan-gated for any future release

Prior pushed source/contract release authority is
`2e448ea Add diagnostic runtime probe request bridge`. It supersedes the
workspace-only post-`38f3841` diagnostic runtime probe-request release-gate
route for active control routing only. Live git refs and worktree state must
still be verified from git during control intake.

Repo-backed release truth verified during post-push continuity sync: branch
`main`, `HEAD` and `origin/main` at
`2e448ea Add diagnostic runtime probe request bridge`, clean worktree, and
nothing staged.

Released internal diagnostic runtime probe-request bridge:

- `derive_diagnostic_runtime_probe_requests(program, diagnostic)` derives
  existing planned runtime probe requests and filters them to grounded
  diagnostic boundary units that still need runtime-backed support
- The bridge preserves `derive_runtime_probe_requests(program)` planned-only
  request semantics, deterministic ordering, attachable-only behavior, and
  `planned_not_executed` status
- It ignores statically proved diagnostic units, already runtime-supported
  boundaries, frontier items without attachable unsupported probe requests, and
  unsupported boundaries that are not attachable
- It does not execute probes, attach runtime provenance, mutate
  `SemanticProgram`, mutate `SemanticDiagnosticResult`, or widen analyzer,
  tool facade, package-root API, MCP, eval, schema, scoring, optimizer,
  compiler, winner-selection, product, public benchmark, or public-claim
  surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `6 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `729 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Local commit creation and Ryan-authorized push completed at
  `2e448ea Add diagnostic runtime probe request bridge`

Release-gate status is no-active-gate for
`2e448ea Add diagnostic runtime probe request bridge`. Do not route `2e448ea`
back to docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Prior pushed continuity authority is
`38f3841 Sync runtime probe request release routing`. Prior pushed
source/contract release authority is
`f6c66e4 Add runtime probe request planning contract`.

Prior pushed runtime probe-request planning contract:

- Repo-backed release truth verified during post-push continuity sync: branch
  `main`, `HEAD` and `origin/main` at
  `f6c66e4 Add runtime probe request planning contract`, clean worktree, and
  nothing staged.
- `derive_runtime_probe_requests(program)` emits deterministic planned-only
  requests for already-attachable unsupported runtime boundaries
- Request records include unsupported subject kind/id, source site, reason
  code, boundary text, runtime family/form labels, replay target/selector
  seeds, and explicit `planned_not_executed` status
- Covered families are current attachable `DYNAMIC_IMPORT`,
  `REFLECTIVE_BUILTIN`, `RUNTIME_MUTATION`, `EXEC_OR_EVAL`, and
  `METACLASS_BEHAVIOR` boundaries
- The function does not execute probes, attach runtime provenance, mutate
  unsupported/frontier/provenance state, or widen public/package-root/MCP
  surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `2 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `725 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Local commit creation and Ryan-authorized push completed at
  `f6c66e4 Add runtime probe request planning contract`

Prior pushed code/eval release authority is
`546a4da Add reflective builtin branch eval probes`.

The completed and pushed release unit is the full 16-file internal eval-only
`REFLECTIVE_BUILTIN` tranche:

- Six docs:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- Five `hasattr_false` eval/test assets:
  - `evals/fixtures/oracle_signal_hasattr_false_probe/main.py`
  - `evals/fixtures/oracle_signal_hasattr_false_probe/eval_runtime_observations.json`
  - `evals/tasks/oracle_signal_hasattr_false_probe.json`
  - `evals/run_specs/oracle_signal_hasattr_false_probe_matrix.json`
  - `tests/test_eval_signal_hasattr_false_probe.py`
- Five `vars_type_error` eval/test assets:
  - `evals/fixtures/oracle_signal_vars_type_error_probe/main.py`
  - `evals/fixtures/oracle_signal_vars_type_error_probe/eval_runtime_observations.json`
  - `evals/tasks/oracle_signal_vars_type_error_probe.json`
  - `evals/run_specs/oracle_signal_vars_type_error_probe_matrix.json`
  - `tests/test_eval_signal_vars_type_error_probe.py`

`hasattr(obj, name)` false-branch implementation/evidence state:

- Matrix `oracle_signal_hasattr_false_probe_matrix` is exactly 1 task x 2
  budgets x 3 providers
- Budgets are `[220, 100]`
- Providers are `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`
- Fixture call boundary is exactly `hasattr(obj, name)`
- Runtime payload is exactly `attribute_present=false`
- Deterministic digest is `hasattr_false:missing`
- Selector and selected-unit primary truth remain `unsupported/opaque`
- Runtime provenance is additive runtime provenance only
- Empty baselines remain empty at both budgets
- Missing-attribute no-edge/no-symbol/no-unit boundary: no
  missing-attribute dependency edge, selected symbol, or selected unit is
  introduced
- No source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/
  winner-selection/product/public benchmark widening is authorized

`vars(obj)` raised-`TypeError` implementation/evidence state:

- Matrix `oracle_signal_vars_type_error_probe_matrix` is exactly 1 task x 2
  budgets x 3 providers
- Budgets are `[220, 100]`
- Providers are `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`
- Fixture boundary is exactly `vars(obj)`
- Runtime payload is exactly `lookup_outcome=raised_type_error`
- Deterministic digest is `vars_type_error:raised_type_error`
- Selector primary truth remains `unsupported/opaque`
- Runtime provenance is additive runtime provenance only
- Empty baselines remain empty at both budgets
- Failed-namespace no-edge/no-symbol/no-unit boundary: no namespace
  dependency edge, selected symbol, or selected unit is introduced from the
  failed `vars()` lookup
- Dependency guard uses `site:call:main.py:2:11`
- No source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/
  winner-selection/product/public benchmark widening is authorized

Release state for `546a4da`:

- Implementation review accepted the accumulated eval-only tranche in
  workspace
- Docs/evidence/continuity reconciliation was accepted after one correction
- Combined read-only release gate passed:
  - Gate 1 release-unit audit passed with no findings
  - focused validation passed with targeted pytest reporting `13 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `723 passed`
  - Gate 3 commit-gating passed and approved the exact 16-file unit
- Local commit creation completed at
  `546a4da Add reflective builtin branch eval probes`
- Ryan-authorized push completed at
  `546a4da Add reflective builtin branch eval probes`
- Release-facing docs remain state-neutral
- Public comparative claims remain bounded to the existing public claim
  boundary
- No source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/
  winner-selection/product/public benchmark widening is authorized

Prior route superseded by the pushed `a819cf5` release state above:

- The bounded diagnose/recompile bridge-consumption implementation slice has
  completed, passed release gates, been locally committed, and been pushed at
  `a819cf5 Surface diagnostic runtime probe requests`
- Release-gate status is no-active-gate for
  `a819cf5 Surface diagnostic runtime probe requests`
- Do not route `a819cf5` back to docs review, release-unit audit, focused
  validation, full regression, commit-gating, staging, local commit creation,
  or push absent new findings
- Release-gate status is no-active-gate for
  `2e448ea Add diagnostic runtime probe request bridge`
- Do not route `2e448ea` back to docs review, release-unit audit, focused
  validation, full regression, commit-gating, staging, local commit creation,
  or push absent new findings
- Release-gate status is no-active-gate for
  `f6c66e4 Add runtime probe request planning contract`
- Do not route `f6c66e4` back to docs review, release-unit audit, focused
  validation, full regression, commit-gating, staging, local commit creation,
  or push absent new findings
- Release-gate status is no-active-gate for
  `546a4da Add reflective builtin branch eval probes`
- Do not route `546a4da` back to docs review, release-unit audit, focused
  validation, full regression, commit-gating, staging, local commit creation,
  or push absent new findings
- No active route remains to release-unit audit, focused validation, full
  regression, commit-gating, staging, local commit creation, or push for
  `49fa461`, `a819cf5`, `2e448ea`, `f6c66e4`, or `546a4da` absent new findings
- Push remains Ryan-gated for any future release

Latest pushed source/contract release authority is
`49fa461 Add runtime probe request identities`. Prior pushed continuity
authority is `bea0a1a Sync diagnostic probe request surface routing`. Prior
pushed source/contract release authority is
`a819cf5 Surface diagnostic runtime probe requests`; earlier pushed
source/contract release authorities are
`2e448ea Add diagnostic runtime probe request bridge` and
`f6c66e4 Add runtime probe request planning contract`. Prior pushed code/eval
release authority is `546a4da Add reflective builtin branch eval probes`.
Prior pushed continuity authority is
`5537a81 Sync original dynamic import release routing`. Prior code/eval
release authority is
`d73cde4 Expand original dynamic import budget coverage`; earlier pushed
code/eval release authority is
`e2f3dcf Expand dir-zero and metaclass budget coverage`; prior pushed
continuity authority is `8aa38d5 Sync dir-zero metaclass release routing`.
There is no active route back to release-unit audit, full regression,
commit-gating, staging, local commit creation, or push for `e2f3dcf` absent new
findings.

Prior pushed continuity authority is
`642b6f9 Sync exec eval release routing`. Prior pushed code/eval authority is
`21f2dc5 Expand exec and eval budget coverage`, which is no-active-gate. Do
not route `21f2dc5` back to docs review, release-unit audit, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

`9fffc5e Sync dynamic import release routing` remains an older pushed
continuity authority. The completed and pushed internal eval-only
`DYNAMIC_IMPORT` sibling budget-pressure release at
`c2c1898 Expand dynamic import sibling eval budget coverage` remains an older
pushed code/eval authority and is no-active-gate. Latest pushed process-doc
authority remains `98edc4a Codify release gate continuity controls`.

The completed and pushed internal eval-only `RUNTIME_MUTATION` /
`delattr(obj, name)` and `setattr(obj, name, value)` budget-pressure expansion
release at `b8e126e Expand runtime mutation eval budget coverage` remains the
older pushed code/eval authority and is:

- Release unit:
  - `ARCHITECTURE.md`
  - `BUILDLOG.md`
  - `EVAL.md`
  - `PLAN.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `evals/run_specs/oracle_signal_delattr_probe_matrix.json`
  - `evals/run_specs/oracle_signal_setattr_probe_matrix.json`
  - `tests/test_eval_signal_delattr_probe.py`
  - `tests/test_eval_signal_setattr_probe.py`
- `oracle_signal_delattr_probe_matrix` expands from `[220]` to `[220, 100]`
- `oracle_signal_setattr_probe_matrix` expands from `[220]` to `[220, 100]`
- Each matrix remains 1 task x 2 budgets x 3 providers
- Providers remain `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`
- Fixtures, tasks, queries, and runtime payloads are unchanged
- `delattr` runtime payload remains `mutation_outcome=deleted_attribute`
- `setattr` runtime payload remains `mutation_outcome=returned_none`
- Selector and selected-unit truth remain `unsupported/opaque`
- Runtime provenance remains additive only
- Baseline providers remain empty at both budgets
- No source/API/MCP/package-export/schema/scoring/optimizer/compiler/
  winner-selection/product/public benchmark widening is authorized
- This release supersedes older historical routing notes that rejected
  `delattr` budget `100` expansion before a specific comparison need existed

Release state for `b8e126e`: docs/evidence/continuity reconciliation was
accepted after one correction; release-unit audit cleared first-pass; full
regression cleared first-pass with `ruff check src/ tests/`,
`ruff format --check src/ tests/`, `mypy --strict src/`, and
`pytest tests/ -v` reporting `709 passed`; commit-gating completed; local
commit creation completed at `b8e126e`; and Ryan-authorized push completed at
`b8e126e`.

Release-gate status is no-active-gate for `b8e126e`: do not route back to docs
review, release-unit audit, full regression, commit-gating, staging, local
commit creation, or push for this tranche absent new findings. No active route
remains to docs review, release-unit audit, full regression, commit-gating,
staging, local commit creation, or push for `b8e126e` absent new findings.
Do not reopen `c2c1898`, `b8e126e`, `98edc4a`, `ad9db8d`, or earlier pushed
releases absent new findings.

The completed and pushed process-doc release at
`98edc4a Codify release gate continuity controls` remains the pushed
process-doc authority. It preserves the tranche batching / throughput
discipline codified by `125f088` and adds release gate continuity controls
while preserving sequential implementation slices, findings-first gates, Ryan
authorization requirements, and push discipline. Release-gate status is
no-active-gate for `98edc4a`: do not route it back to release-unit audit, full
regression, commit-gating, staging, local commit creation, or push absent new
findings.

The completed and pushed internal eval-only `REFLECTIVE_BUILTIN` / `dir(obj)`
budget-pressure expansion release at
`ad9db8d Expand dir eval budget coverage` remains an older code/eval
authority:

- Matrix: `oracle_signal_dir_probe_matrix`
- Shape: `[220, 100]`: 1 task x 2 budgets x 3 providers
- Providers: `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`
- Fixture, task, query, and runtime payload remain unchanged
- Runtime payload remains `listing_entry_count=74`
- Selector and selected-unit truth remain `unsupported/opaque`
- Runtime provenance remains additive only
- Baseline providers remain empty at both budgets
- Released budget-pressure expansion files:
  - `evals/run_specs/oracle_signal_dir_probe_matrix.json`
  - `tests/test_eval_signal_dir_probe.py`

No source/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark claim widening is authorized. Release-facing docs remain
state-neutral for this eval-only expansion. Docs/evidence/continuity
reconciliation completed first-pass. Release-unit audit cleared first-pass.
Full regression cleared first-pass with `ruff check`, `ruff format --check`,
`mypy --strict`, and `pytest tests/ -v` reporting `709 passed`.
Commit-gating completed; local commit creation completed at `ad9db8d`; and
Ryan-authorized push completed at `ad9db8d`.

Release-gate status is no-active-gate for `ad9db8d`: do not route back to
docs review, release-unit audit, full regression, commit-gating, staging,
local commit creation, or push for this tranche absent new findings. No active
route remains to commit-gating, staging, local commit creation, or push for
`ad9db8d` absent new findings.

`43d0439 Expand getattr AttributeError eval budget coverage` is an older
pushed code/eval release authority for the internal eval-only
`REFLECTIVE_BUILTIN` / `getattr(obj, name)` raised-`AttributeError`
budget-pressure expansion at `[220, 100]`: 1 task x 2 budgets x 3 providers.
There is no active release gate for `43d0439` absent new findings.

`5bd0616 Add getattr AttributeError eval probe` is an older pushed code/eval
release authority for the initial internal eval-only `REFLECTIVE_BUILTIN` /
`getattr(obj, name)` raised-`AttributeError` pilot at budget 220. `6ac1e28 Add
builtins-alias dynamic import eval probe` remains the earlier pushed release
authority for the internal eval-only `DYNAMIC_IMPORT` /
builtins-alias `loader.__import__(name)` probe. `3dfc355 Add
builtins-attribute dynamic import eval probe` remains an older pushed
builtins-attribute release authority. `b85f038 Add root-alias dynamic import
eval probe` remains an older root-module alias dynamic-import release
authority. `4030845 Add imported-alias dynamic import eval probe`,
`ee71a82 Add imported-name dynamic import eval probe`, `397c7dd Add builtin
dynamic import eval probe`, and `14b362e Add dynamic import root runtime eval
pilot` remain earlier released dynamic-import authorities and must not be
reopened absent new findings.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` /
builtins-alias `loader.__import__(name)` release at `6ac1e28` is:

- Source/contract prerequisite accepted first-pass:
  - exact unshadowed `import builtins as loader` plus exactly
    `loader.__import__(name)` is classified as unsupported `DYNAMIC_IMPORT`
  - runtime provenance can attach to that exact unsupported boundary
  - existing `import builtins` plus `builtins.__import__(name)` behavior is
    preserved
  - shadowed/rebound/non-builtins/wrong-arity/literal forms remain generic or
    deferred
  - changed files are `src/context_ir/dependency_frontier.py`,
    `src/context_ir/runtime_acquisition.py`,
    `tests/test_dependency_frontier.py`, and
    `tests/test_runtime_acquisition.py`
- Eval-only sibling accepted first-pass:
  - matrix is `oracle_signal_dynamic_import_builtins_alias_probe_matrix`
  - shape is 1 task x 1 budget x 3 providers at budget 220
  - providers are `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `import builtins as loader`,
    `name = "plugins.weather"`, and exactly `loader.__import__(name)`, with
    bounded `sys.modules[name]`
    retrieval only
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or selected symbol is created from `plugins.weather`
  - asset/test files are:
    - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/eval_runtime_observations.json`
    - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/main.py`
    - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/plugins/__init__.py`
    - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/plugins/weather.py`
    - `evals/run_specs/oracle_signal_dynamic_import_builtins_alias_probe_matrix.json`
    - `evals/tasks/oracle_signal_dynamic_import_builtins_alias_probe.json`
    - `tests/test_eval_signal_dynamic_import_builtins_alias_probe.py`

The docs/evidence/continuity reconciliation was accepted after one
correction. The release-unit audit cleared first-pass. Full regression cleared
first-pass with `702 passed`. The first commit-gating review rejected with P1
stale-routing findings in `PLAN.md` and `BUILDLOG.md`; a later PLAN-only
stale-route correction was accepted first-pass; corrected commit-gating cleared
first-pass; local commit creation completed at `6ac1e28`; and Ryan-authorized
push completed at `6ac1e28`.

There is no active release gate for `6ac1e28`: do not route back to
release-unit audit, full regression, commit-gating, staging, local commit
creation, or push for this tranche absent new findings. The post-`6ac1e28`
route is superseded by the completed and pushed `5bd0616` getattr
AttributeError release.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` / root-module
alias `loader.import_module(name)` sibling pilot was released at
`b85f038 Add root-alias dynamic import eval probe`. Its pilot assets are:

- `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/eval_runtime_observations.json`
- `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/main.py`
- `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/plugins/__init__.py`
- `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/plugins/weather.py`
- `evals/run_specs/oracle_signal_dynamic_import_root_alias_probe_matrix.json`
- `evals/tasks/oracle_signal_dynamic_import_root_alias_probe.json`
- `tests/test_eval_signal_dynamic_import_root_alias_probe.py`

The released matrix is
`oracle_signal_dynamic_import_root_alias_probe_matrix`: 1 task x 1 budget x 3
providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary is
`import importlib as loader`, `name = "plugins.weather"`, and exactly
`loader.import_module(name)`. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, and no
dependency edge or selected symbol is created from `plugins.weather`. No
root-module `importlib.import_module(name)` expansion, imported-name
`import_module(name)` expansion, imported-alias `load_module(name)` expansion,
literal dynamic import expansion, `__import__(name)`, `builtins.__import__`,
globals/locals/fromlist forms, namespace mutation, generated-code dependency
modeling, generalized dynamic import support,
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening, product surface, schema, scoring, optimizer, compiler, or
winner-selection widening is authorized.

The first docs/evidence/continuity reconciliation for the root-module alias
pilot was rejected with a P1 state-neutrality finding because release-facing
docs described the evidence with live workspace-state wording. The corrected
docs/evidence/continuity reconciliation is accepted; release-facing docs remain
state-neutral. The root-module alias implementation/assets were accepted
workspace-only before release; the corrected docs reconciliation was accepted
after one P1 state-neutrality correction; the release-unit audit cleared
first-pass; full regression cleared first-pass with `688 passed`;
commit-gating cleared first-pass; local commit creation completed at
`b85f038`; and Ryan-authorized push completed at `b85f038`.

There is no active release gate for `b85f038`: do not route back to
release-unit audit, full regression, commit-gating, staging, local commit
creation, or push for this tranche absent new findings.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` / imported-alias
`load_module(name)` sibling pilot was released at
`4030845 Add imported-alias dynamic import eval probe`. Its pilot assets are:

- `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/eval_runtime_observations.json`
- `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/main.py`
- `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/plugins/__init__.py`
- `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/plugins/weather.py`
- `evals/run_specs/oracle_signal_dynamic_import_imported_alias_probe_matrix.json`
- `evals/tasks/oracle_signal_dynamic_import_imported_alias_probe.json`
- `tests/test_eval_signal_dynamic_import_imported_alias_probe.py`

The released matrix is
`oracle_signal_dynamic_import_imported_alias_probe_matrix`: 1 task x 1 budget
x 3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is `from importlib import import_module as load_module`,
`name = "plugins.weather"`, and exactly `load_module(name)`. The runtime
payload is `imported_module=plugins.weather`. Primary selector and
selected-unit truth remain `unsupported/opaque`, runtime provenance remains
additive only, and no dependency edge or selected symbol is created from
`plugins.weather`. No root-module `importlib.import_module(name)` expansion,
imported-name `import_module(name)` expansion, literal
`load_module("plugins.weather")` expansion, `loader.import_module(name)`,
`__import__(name)`, `builtins.__import__`, globals/locals/fromlist forms,
namespace mutation, generated-code dependency modeling, generalized dynamic
import support,
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening, product surface, schema, scoring, optimizer, compiler, or
winner-selection widening is authorized.

The release-unit audit for `4030845` cleared first-pass. Full regression
cleared first-pass with `682 passed`. The first commit-gating review rejected
with P1 stale-routing findings in `PLAN.md` and `BUILDLOG.md`; the continuity
correction was accepted first-pass; corrected commit-gating cleared
first-pass; local commit creation completed at `4030845`; Ryan-authorized push
completed at `4030845`.

There is no active release gate for `4030845`: do not route back to
release-unit audit, full regression, commit-gating, staging, local commit
creation, or push for this tranche absent new findings. The prior fresh
post-imported-alias next-move route is superseded by the completed
root-module alias release at `b85f038` and the post-root-alias
planning/control route above.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` / imported-name
`import_module(name)` sibling pilot was released at
`ee71a82 Add imported-name dynamic import eval probe`. Its pilot assets are:

- `evals/fixtures/oracle_signal_dynamic_import_imported_name_probe/`
- `evals/tasks/oracle_signal_dynamic_import_imported_name_probe.json`
- `evals/run_specs/oracle_signal_dynamic_import_imported_name_probe_matrix.json`
- `tests/test_eval_signal_dynamic_import_imported_name_probe.py`

The released matrix is
`oracle_signal_dynamic_import_imported_name_probe_matrix`: 1 task x 1 budget x
3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary is
`from importlib import import_module`, `name = "plugins.weather"`, and exactly
`import_module(name)`. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, and no
dependency edge or selected symbol is created from `plugins.weather`. No
root-module `importlib.import_module(name)` expansion, literal
`import_module("plugins.weather")` expansion, alias `load_module(name)`,
`loader.import_module(name)`, `__import__(name)`, `builtins.__import__`,
globals/locals/fromlist forms, generalized dynamic import support,
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening, product surface, schema, scoring, optimizer, compiler, or
winner-selection widening is authorized.

The release-unit audit for `ee71a82` cleared first-pass. Full regression
passed: `ruff check`, `ruff format --check`, `mypy --strict`, and
`pytest tests/ -v` with `676 passed`. The first commit-gating review returned
P1 continuity findings; the continuity correction was accepted; corrected
commit-gating cleared; local commit creation completed; Ryan-authorized push
completed at `ee71a82`.

There is no active release gate for `ee71a82` or `4030845`: do not route back
to release-unit audit, full regression, commit-gating, staging, local commit
creation, or push for those tranches absent new findings. The
post-imported-alias route should move to a fresh bounded next-move
planning/control decision, not implementation and not release handling. Do
not reopen `4030845`, `ee71a82`, `397c7dd`, `14b362e`, `bcd6d68`, or
`96fc03a` absent new findings.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` / root-module
`importlib.import_module(name)` sibling pilot was released at
`14b362e Add dynamic import root runtime eval pilot`. Its pilot assets are:

- `evals/fixtures/oracle_signal_dynamic_import_root_probe/`
- `evals/tasks/oracle_signal_dynamic_import_root_probe.json`
- `evals/run_specs/oracle_signal_dynamic_import_root_probe_matrix.json`
- `tests/test_eval_signal_dynamic_import_root_probe.py`

The pushed matrix is `oracle_signal_dynamic_import_root_probe_matrix`: 1 task x
1 budget x 3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is `import importlib`, `name = "plugins.weather"`, and exactly
`importlib.import_module(name)`. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, and no
dependency edge or symbol is created from the dynamically imported module. No
`__import__(name)`, imported-name `import_module(name)`, alias or loader forms,
generalized dynamic import support, public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening, product surface, schema, scoring, optimizer, compiler, or
winner-selection widening is authorized.

The release-unit audit for `14b362e` cleared first-pass. Full regression passed:
`ruff check`, `ruff format --check`, `mypy --strict`, and
`pytest tests/ -v` with `664 passed`. Commit-gating cleared first-pass. Local
commit creation and Ryan-authorized push completed at `14b362e`.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` / builtin
`__import__(name)` sibling pilot was released at
`397c7dd Add builtin dynamic import eval probe`. Its pilot assets are:

- `evals/fixtures/oracle_signal_dynamic_import_builtin_probe/`
- `evals/tasks/oracle_signal_dynamic_import_builtin_probe.json`
- `evals/run_specs/oracle_signal_dynamic_import_builtin_probe_matrix.json`
- `tests/test_eval_signal_dynamic_import_builtin_probe.py`

The released matrix is `oracle_signal_dynamic_import_builtin_probe_matrix`: 1
task x 1 budget x 3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is `name = "plugins.weather"` and exactly `__import__(name)`, with bounded
`sys.modules[name]` retrieval only. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, and no
dependency edge or symbol is created from `plugins.weather`. No
`importlib.import_module(name)`, imported-name `import_module(name)`, alias or
loader forms, `builtins.__import__`, globals/locals/fromlist forms,
generalized dynamic import support, public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening, product surface, schema, scoring, optimizer, compiler, or
winner-selection widening is authorized.

The release-unit audit for `397c7dd` cleared first-pass. Full regression
passed: `ruff check`, `ruff format --check`, `mypy --strict`, and
`pytest tests/ -v` with `670 passed`. Commit-gating cleared first-pass. Local
commit creation and Ryan-authorized push completed at `397c7dd`.

`bcd6d68 Add exec source runtime eval pilot` remains the prior pushed
exec(source) release. It adds the narrow internal eval-only `EXEC_OR_EVAL` /
`exec(source)` evidence through `oracle_signal_exec_probe_matrix`: 1 task x 1
budget x 3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture/call
boundary is `source = "pass"` and exactly `exec(source)`; the executed source
parses as exactly one `ast.Pass`. The runtime proof boundary is
`execution_outcome=completed`, `source_shape=literal_statement`,
`source_sha256 == sha256(b"pass")`, and non-empty
`durable_payload_reference`; optional `statement_kind=pass` is additive
summary only. Runtime provenance attaches only to the preserved `EXEC_OR_EVAL`
unsupported finding for `exec(source)`. Primary selector and selected-unit
truth remain `unsupported/opaque`, additive runtime provenance remains
separate from primary truth, no dependency edge or symbol is created from
executed source, no namespace mutation modeling is added, no generated-code
dependency modeling is added, and public comparative claims remain bounded to
the existing quad matrix. The release-unit audit initially found one P1
digest-boundary issue; the correction pinned `source_sha256` to
`sha256(b"pass")`; the audit rerun cleared; full regression passed;
commit-gating cleared; local commit creation completed; Ryan-authorized push
completed. Do not reopen `bcd6d68` exec(source) absent new findings.

`96fc03a Add eval runtime eval pilot` remains the prior eval(source) release
authority. It adds the narrow internal eval-only `EXEC_OR_EVAL` /
`eval(source)` evidence through `oracle_signal_eval_probe_matrix`: 1 task x 1
budget x 3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The runtime
payload/proof boundary is `evaluation_outcome=returned_value`,
`source_shape=literal_expression`, valid `source_sha256`, and non-empty
`durable_payload_reference`; optional `result_type=builtins.str` is additive
summary only. Runtime provenance attaches only to the preserved
`EXEC_OR_EVAL` unsupported finding for `eval(source)`. Primary selector and
selected-unit truth remain `unsupported/opaque`, additive runtime provenance
remains separate from primary truth, and public comparative claims remain
bounded to the existing quad matrix. Do not reopen `96fc03a` eval(source)
absent new findings.

There is no active release gate for `bcd6d68` or `96fc03a`.

Prior pushed release anchors remain: `f0efbef` for the internal eval-only
`REFLECTIVE_BUILTIN` / zero-argument `dir()` provider matrix; `19d9a32` for
the internal eval-only
`METACLASS_BEHAVIOR` / preserved `metaclass=...` keyword-site provider matrix;
`38e9d5f` for the initial internal
eval-only `RUNTIME_MUTATION` / `locals()` pilot; `5f74ede` for the internal
eval-only `RUNTIME_MUTATION` / `globals()` budget expansion; `631a303` for the
initial `globals()` pilot; `9eec985` for the zero-argument `vars()` budget
expansion; `71db72e` for the initial zero-argument `vars()` pilot; `2c6b54a`
for the `vars(obj)` budget expansion; `ead239d` for the initial `vars(obj)`
pilot; `1b555ef` for the `getattr` family budget expansion; `d8ebdc3` for
runtime-outcome accounting; `b014595`, `7d43302`, and `c592dca` for the
accepted `getattr` runtime-backed family releases; `762dd51` and `90dcc15` for
`hasattr(obj, name)`; `9a52b46` for `DYNAMIC_IMPORT`; `215b6bb` for
provider-scoped selected-unit capability-tier accounting; and `a605b22` for
the capability-tier eval / evidence baseline.

The active release model is tranche-based, not slice-by-slice. Accepted slices may accumulate locally with continuity synced in workspace until they form one coherent release unit. For a future release unit that has not already cleared gates, the control lane should request one dedicated findings-first deep release-unit audit over the whole accumulated diff, then run the full regression gate, then do commit-gating, commit, and push. The `c1a12d7` dir(obj) release has already completed those gates and must not reopen audit, regression, commit-gating, staging, local commit, or push handling absent new findings.

## Evidence-Building Cadence Guardrails

These streamlining guardrails standardize repeatable mechanics without
weakening findings-first review, release-unit audit, full regression,
commit-gating, human push authorization, or claim-boundary discipline.

During the current internal evidence-building mode, future control lanes may
reuse a standard eval-pilot packet for repeated internal evidence slices: one
bounded task/fixture/run-spec packet, explicit provider and budget shape,
runtime proof boundary, selector/selected-unit truth boundary, docs
reconciliation checklist, and the exact validation commands needed for that
pilot. The packet is a prompt scaffold only; it does not open the next lane or
widen scope by itself.

Docs reconciliation for these pilots should use stable wording: name the
matrix, state task x budget x provider shape, list providers and budgets, state
runtime proof as additive, preserve `unsupported/opaque` primary truth when
applicable, and restate the public claim boundary. Avoid recording every
transient handoff; after several related pilots, consolidate at the family
level when the durable evidence story is clearer.

Before commit-gating any accumulated evidence release unit, the control lane
must run an explicit release-state checklist: branch/HEAD/origin state,
staged/unstaged file set, included/excluded files, active holds,
release-unit audit status, full-regression status, and whether human push
sign-off exists. Common guard checks should also look for dirty-file surprises,
forbidden diffs outside the slice/doc set, stale routing language, run-spec
shape drift, and claim widening.

Budget expansion remains a control question, not an automatic next step.
Consider it only when a first-budget pilot leaves a specific unanswered
comparison or coverage question, the run-spec shape can stay bounded, and
claim boundaries remain unchanged.

This section is a standing process note only. It does not change `AGENTS.md`,
alter any pushed dir(obj) release authority, claim new evidence or capability,
or route to commit or push. It does not require a follow-on continuity pass.

The `2dd8404` locals budget-expansion release passed implementation review,
same-tranche docs reconciliation, release-unit audit, full regression,
corrected commit-gating, local commit creation, and Ryan-authorized push. It is
no longer pending any release gate. The next lane should make a fresh control
decision on the next north-star move rather than reopen release sequencing for
`2dd8404` absent new findings.

The `c1a12d7 Add dir(obj) eval pilot` release passed implementation review,
docs/evidence reconciliation after correction, process guardrail note
acceptance, release-unit audit, full regression after one formatting correction
with `607 passed`, corrected commit-gating, local commit creation, and
Ryan-authorized push. It is no longer pending any release gate. The next lane
should make a fresh control-lane north-star decision rather than reopen release
sequencing for `c1a12d7` absent new findings.

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
- [x] Post-provider-scoped `DYNAMIC_IMPORT` evidence-broadening planning spike accepted first-pass
- [x] Internal `DYNAMIC_IMPORT` provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review for internal `DYNAMIC_IMPORT` provider/budget matrix expansion accepted first-pass
- [x] Release-unit audit workflow correction accepted with human sign-off
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` provider/budget matrix expansion accepted first-pass
- [x] Local commit creation for internal `DYNAMIC_IMPORT` provider/budget matrix expansion accepted first-pass at `9a52b46`
- [x] Remote push for internal `DYNAMIC_IMPORT` provider/budget matrix expansion completed at `9a52b46`
- [x] Execution-lane overreach continuity correction accepted first-pass
- [x] Control review of `hasattr(obj, name)` runtime-backed eval pilot recommendation accepted first-pass
- [x] Internal `hasattr(obj, name)` runtime-backed eval pilot implementation accepted first-pass as workspace-only state
- [x] Payload-shape correction for internal `hasattr(obj, name)` runtime-backed eval pilot accepted first-pass
- [x] Corrected release-unit audit for internal `hasattr(obj, name)` runtime-backed eval pilot accepted first-pass
- [x] Full regression gate for internal `hasattr(obj, name)` runtime-backed eval pilot accepted first-pass
- [x] Commit-gating review and local commit creation for internal `hasattr(obj, name)` runtime-backed eval pilot accepted first-pass at `90dcc15`
- [x] Remote push for internal `hasattr(obj, name)` runtime-backed eval pilot completed at `90dcc15`
- [x] Runtime-backed evidence/claim docs reconciliation accepted first-pass
- [x] Commit-gating review and local commit creation for runtime-backed evidence/claim docs reconciliation accepted first-pass at `3291268`
- [x] Remote push for runtime-backed evidence/claim docs reconciliation completed at `3291268`
- [x] Continuity-loop correction and tranche-cadence reset accepted first-pass at `8133e0a`
- [x] Post-`hasattr`-pilot matrix-broadening planning spike accepted first-pass
- [x] Internal `hasattr(obj, name)` provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for internal `hasattr(obj, name)` provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review and local commit creation for internal `hasattr(obj, name)` provider/budget matrix expansion accepted first-pass at `762dd51`
- [x] Remote push for internal `hasattr(obj, name)` provider/budget matrix expansion completed at `762dd51`
- [x] Post-`762dd51` runtime-family planning spike accepted first-pass
- [x] Internal `getattr(obj, name)` runtime-backed eval pilot implementation accepted after 1 correction as workspace-only tranche state
- [x] Post-`getattr(obj, name)` same-tranche docs/evidence reconciliation decision accepted first-pass
- [x] Same-tranche docs/evidence reconciliation for internal `getattr(obj, name)` tranche accepted first-pass
- [x] Release-unit audit for internal `getattr(obj, name)` tranche accepted first-pass
- [x] Full regression gate for internal `getattr(obj, name)` tranche accepted first-pass
- [x] Commit-gating review and local commit creation for internal `getattr(obj, name)` tranche accepted first-pass at `c592dca`
- [x] Remote push for internal `getattr(obj, name)` tranche completed at `c592dca`
- [x] Post-`c592dca` defaulted `getattr(obj, name, default)` eval planning spike accepted first-pass
- [x] `EVAL.md` authority correction accepted first-pass as workspace-only tranche state
- [x] Internal defaulted `getattr(obj, name, default)` eval pilot implementation accepted first-pass as workspace-only tranche state
- [x] Same-tranche docs/evidence reconciliation for defaulted `getattr(obj, name, default)` accepted first-pass as workspace-only tranche state
- [x] Release-unit audit for defaulted `getattr(obj, name, default)` tranche accepted first-pass
- [x] Full regression gate for defaulted `getattr(obj, name, default)` tranche accepted first-pass
- [x] Release-doc wording correction for defaulted `getattr(obj, name, default)` accepted first-pass after human sign-off
- [x] Commit-gating review for defaulted `getattr(obj, name, default)` tranche accepted first-pass
- [x] Local commit creation for defaulted `getattr(obj, name, default)` tranche accepted first-pass at `7d43302`
- [x] Remote push for defaulted `getattr(obj, name, default)` tranche completed at `7d43302`
- [x] Post-`7d43302` defaulted `getattr(obj, name, default)` value-return branch planning spike accepted first-pass
- [x] Internal defaulted `getattr(obj, name, default)` value-return branch eval pilot implementation accepted first-pass as workspace-only tranche state
- [x] Same-tranche docs/evidence reconciliation for defaulted `getattr(obj, name, default)` value-return branch accepted first-pass as workspace-only tranche state
- [x] Release-unit audit for defaulted `getattr(obj, name, default)` value-return branch tranche accepted first-pass
- [x] Full regression gate for defaulted `getattr(obj, name, default)` value-return branch tranche accepted first-pass
- [x] Commit-gating review for defaulted `getattr(obj, name, default)` value-return branch tranche accepted first-pass
- [x] Local commit creation for defaulted `getattr(obj, name, default)` value-return branch tranche accepted first-pass at `b014595`
- [x] Remote push for defaulted `getattr(obj, name, default)` value-return branch tranche completed at `b014595`
- [x] Post-`b014595` runtime-outcome methodology/reporting planning spike accepted first-pass
- [x] Runtime-outcome methodology/reporting hardening implementation accepted first-pass as workspace-only state
- [x] Release-unit audit for runtime-outcome methodology/reporting hardening accepted first-pass
- [x] Full regression gate for runtime-outcome methodology/reporting hardening accepted first-pass
- [x] Commit-gating review for runtime-outcome methodology/reporting hardening accepted first-pass
- [x] Local commit creation for runtime-outcome methodology/reporting hardening accepted first-pass at `d8ebdc3`
- [x] Remote push for runtime-outcome methodology/reporting hardening completed at `d8ebdc3`
- [x] Post-`d8ebdc3` `getattr` family evidence-broadening planning spike accepted after 1 control correction
- [x] `EVAL.md` release-anchor attribution correction accepted first-pass as workspace-only state
- [x] `getattr` family provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for the `getattr` family provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Release-unit audit for the `getattr` family provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for the `getattr` family provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review for the `getattr` family provider/budget matrix expansion accepted first-pass
- [x] Local commit creation for the `getattr` family provider/budget matrix expansion accepted first-pass at `1b555ef`
- [x] Remote push for the `getattr` family provider/budget matrix expansion completed at `1b555ef`
- [x] Post-`d9be4d5` `vars(obj)` internal eval evidence planning spike accepted first-pass
- [x] Internal `vars(obj)` runtime-backed eval pilot implementation accepted first-pass
- [x] Same-tranche docs/evidence reconciliation for internal `vars(obj)` pilot accepted after 1 correction
- [x] Release-unit audit for internal `vars(obj)` tranche accepted first-pass
- [x] Full regression gate for internal `vars(obj)` tranche accepted first-pass
- [x] Commit-gating review for internal `vars(obj)` tranche accepted first-pass
- [x] Post-`ead239d` `vars(obj)` budget-expansion planning spike accepted first-pass
- [x] Internal `vars(obj)` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `vars(obj)` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Corrected release-unit audit for internal `vars(obj)` provider/budget matrix expansion accepted after 1 correction
- [x] Full regression gate for internal `vars(obj)` provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review for internal `vars(obj)` provider/budget matrix expansion accepted first-pass
- [x] Internal zero-argument `vars()` eval pilot implementation accepted first-pass for the accumulated release candidate
- [x] Same-tranche docs/evidence reconciliation for internal zero-argument `vars()` pilot accepted first-pass for the accumulated release candidate
- [x] Release-unit audit for internal zero-argument `vars()` release candidate accepted first-pass
- [x] Full regression gate for internal zero-argument `vars()` release candidate accepted first-pass
- [x] Commit-gating review for internal zero-argument `vars()` release candidate accepted first-pass
- [x] Post-`71db72e` zero-argument `vars()` budget-expansion planning spike accepted first-pass
- [x] Internal zero-argument `vars()` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal zero-argument `vars()` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Release-unit audit for internal zero-argument `vars()` provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for internal zero-argument `vars()` provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review for internal zero-argument `vars()` provider/budget matrix expansion accepted first-pass
- [x] Post-`9eec985` globals-family planning spike accepted first-pass
- [x] Internal `globals()` eval pilot implementation accepted first-pass
- [x] Same-tranche docs/evidence reconciliation for internal `globals()` eval pilot accepted first-pass
- [x] Release-unit audit for internal `globals()` eval pilot accepted first-pass
- [x] Full regression gate for internal `globals()` eval pilot accepted first-pass
- [x] Commit-gating review for internal `globals()` eval pilot accepted first-pass
- [x] Post-`631a303` globals budget-expansion planning spike accepted first-pass
- [x] Internal `globals()` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `globals()` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Release-unit audit for internal `globals()` provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for internal `globals()` provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review for internal `globals()` provider/budget matrix expansion accepted first-pass
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
- [x] Internal `locals()` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `locals()` provider/budget matrix expansion completed first-pass as workspace-only state
- [x] Release-unit audit for internal `locals()` provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for internal `locals()` provider/budget matrix expansion accepted first-pass
- [x] Corrected commit-gating review for internal `locals()` provider/budget matrix expansion accepted after 1 correction
- [x] Local commit creation for internal `locals()` provider/budget matrix expansion accepted at `2dd8404`
- [x] Ryan-authorized remote push for internal `locals()` provider/budget matrix expansion completed at `2dd8404`
- [x] Post-`2dd8404` release-authority sync completed first-pass
- [x] `delattr(obj, name)` vs `setattr(obj, name, value)` mutation-planning spike accepted first-pass
- [x] Bounded `delattr(obj, name)` runtime-backed implementation slice accepted first-pass
- [x] `setattr(obj, name, value)` assigned-value contract spike accepted first-pass
- [x] Bounded `setattr(obj, name, value)` runtime-backed implementation slice accepted first-pass
- [x] `METACLASS_BEHAVIOR` runtime-backed contract spike accepted first-pass
- [x] Bounded `METACLASS_BEHAVIOR` runtime-backed implementation slice accepted first-pass
- [x] Deep-audit correction slice for `PLAN.md` truthfulness and runtime-acquisition negative coverage accepted first-pass
- [x] Runtime-backed tranche release sequencing completed to `origin/main` at `cb1dc65`
- [x] Internal `dir(obj)` eval-only provider matrix implementation accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `dir(obj)` eval-only provider matrix accepted after 1 correction as workspace-only state
- [x] Evidence-building process guardrail note accepted first-pass as workspace-only continuity state
- [x] Release-unit audit for internal `dir(obj)` eval-only provider matrix accepted first-pass with no findings
- [x] Full regression gate for internal `dir(obj)` eval-only provider matrix accepted first-pass after one formatting correction with `607 passed`
- [x] Corrected commit-gating review for internal `dir(obj)` eval-only provider matrix accepted first-pass
- [x] Local commit creation for internal `dir(obj)` eval-only provider matrix accepted at `c1a12d7`
- [x] Ryan-authorized remote push for internal `dir(obj)` eval-only provider matrix completed at `c1a12d7`
- [x] Internal `delattr(obj, name)` eval-only provider matrix implementation accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `delattr(obj, name)` eval-only provider matrix completed first-pass as workspace-only state
- [x] Release-unit audit for internal `delattr(obj, name)` eval-only provider matrix accepted first-pass with no findings
- [x] Full regression gate for internal `delattr(obj, name)` eval-only provider matrix accepted first-pass with `612 passed, 1 deselected`
- [x] Commit-gating review for internal `delattr(obj, name)` eval-only provider matrix accepted first-pass
- [x] Local commit creation and Ryan-authorized push for internal `delattr(obj, name)` eval-only provider matrix completed at `41f6b57`
- [x] Post-`41f6b57` runtime-mutation next-move planning spike accepted first-pass
- [x] Internal `setattr(obj, name, value)` eval-only provider matrix implementation accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `setattr(obj, name, value)` eval-only provider matrix accepted first-pass as workspace-only state
- [x] Release-unit audit for internal `setattr(obj, name, value)` eval-only provider matrix accepted first-pass with no findings
- [x] Full regression gate for internal `setattr(obj, name, value)` eval-only provider matrix accepted first-pass with `619 passed`
- [x] Commit-gating review for internal `setattr(obj, name, value)` eval-only provider matrix accepted first-pass
- [x] Local commit creation and Ryan-authorized push for internal `setattr(obj, name, value)` eval-only provider matrix completed at `f67bab7`
- [x] Post-`f67bab7` metaclass eval-matrix next-move planning spike accepted first-pass
- [x] Internal `METACLASS_BEHAVIOR` eval-only provider matrix implementation accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `METACLASS_BEHAVIOR` eval-only provider matrix accepted first-pass as workspace-only state
- [x] Release-unit audit for internal `METACLASS_BEHAVIOR` eval-only provider matrix accepted first-pass with no findings
- [x] Full regression gate for internal `METACLASS_BEHAVIOR` eval-only provider matrix accepted first-pass with `624 passed`
- [x] Commit-gating review for internal `METACLASS_BEHAVIOR` eval-only provider matrix accepted first-pass
- [x] Local commit creation and Ryan-authorized push for internal `METACLASS_BEHAVIOR` eval-only provider matrix completed at `19d9a32`
- [x] Internal zero-argument `dir()` eval-only provider matrix implementation accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence/continuity reconciliation for internal zero-argument `dir()` eval-only provider matrix accepted after 1 correction
- [x] Release-unit audit for internal zero-argument `dir()` eval-only provider matrix cleared with no findings
- [x] Full regression gate for internal zero-argument `dir()` eval-only provider matrix cleared with `629 passed`
- [x] Corrected commit-gating review for internal zero-argument `dir()` eval-only provider matrix accepted first-pass
- [x] Local commit creation and Ryan-authorized push for internal zero-argument `dir()` eval-only provider matrix completed at `f0efbef`
- [x] `EXEC_OR_EVAL` / `eval(source)` contract spike accepted first-pass
- [x] Lower-layer `EXEC_OR_EVAL` / `eval(source)` runtime provenance seam accepted workspace-only after 1 correction
- [x] `oracle_signal_eval_probe_matrix` implementation/assets accepted workspace-only first-pass
- [x] Docs/evidence/continuity reconciliation for accumulated internal eval-only `EXEC_OR_EVAL` / `eval(source)` release unit accepted first-pass as workspace-only state
- [x] Local commit creation and Ryan-authorized push for internal `EXEC_OR_EVAL` / `eval(source)` runtime eval pilot completed at `96fc03a`
- [x] Lower-layer `EXEC_OR_EVAL` / `exec(source)` runtime provenance seam accepted first-pass and released at `bcd6d68`
- [x] `oracle_signal_exec_probe_matrix` implementation/assets accepted first-pass and released at `bcd6d68`
- [x] Docs/evidence/continuity reconciliation for accumulated internal eval-only `EXEC_OR_EVAL` / `exec(source)` release unit accepted first-pass
- [x] Release-unit audit for internal `EXEC_OR_EVAL` / `exec(source)` runtime eval pilot initially found one P1 digest-boundary issue; correction pinned `source_sha256` to `sha256(b"pass")`
- [x] Corrected release-unit audit for internal `EXEC_OR_EVAL` / `exec(source)` runtime eval pilot cleared
- [x] Full regression gate for internal `EXEC_OR_EVAL` / `exec(source)` runtime eval pilot passed
- [x] Commit-gating review for internal `EXEC_OR_EVAL` / `exec(source)` runtime eval pilot cleared
- [x] Local commit creation and Ryan-authorized push for internal `EXEC_OR_EVAL` / `exec(source)` runtime eval pilot completed at `bcd6d68`
- [x] Accepted workspace-only `EXEC_OR_EVAL` budget-pressure implementation
  first-pass: `oracle_signal_eval_probe_matrix` and
  `oracle_signal_exec_probe_matrix` expanded from `[220]` to `[220, 100]`
- [x] Internal eval-only `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)` sibling implementation accepted first-pass and released at `14b362e`
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)` runtime eval pilot cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)` runtime eval pilot passed with `664 passed`
- [x] Commit-gating review for internal `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)` runtime eval pilot cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)` runtime eval pilot completed at `14b362e`
- [x] Post-`14b362e` / `ad22ea6` builtin `__import__(name)` sibling planning and implementation slice accepted first-pass and released at `397c7dd`
- [x] Internal eval-only `DYNAMIC_IMPORT` / builtin `__import__(name)` sibling pilot released at `397c7dd` for `oracle_signal_dynamic_import_builtin_probe_matrix`
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / builtin `__import__(name)` runtime eval pilot cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / builtin `__import__(name)` runtime eval pilot passed with `670 passed`
- [x] Commit-gating review for internal `DYNAMIC_IMPORT` / builtin `__import__(name)` runtime eval pilot cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / builtin `__import__(name)` runtime eval pilot completed at `397c7dd`
- [x] Internal eval-only `DYNAMIC_IMPORT` / imported-name `import_module(name)` sibling implementation/assets accepted as workspace-only state for `oracle_signal_dynamic_import_imported_name_probe_matrix`
- [x] Docs/evidence/continuity reconciliation for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` accepted as workspace-only state
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot passed with `676 passed`
- [x] First commit-gating review for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot returned P1 continuity findings
- [x] Continuity correction for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot accepted
- [x] Corrected commit-gating review for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot cleared
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot completed at `ee71a82`
- [x] Post-`ee71a82` release routing sync completed at `5d2d7e4`
- [x] Internal eval-only `DYNAMIC_IMPORT` / imported-alias `load_module(name)` sibling implementation/assets accepted as workspace-only state for `oracle_signal_dynamic_import_imported_alias_probe_matrix`
- [x] Docs/evidence/continuity reconciliation for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` accepted as workspace-only state
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit cleared first-pass with `682 passed`
- [x] First commit-gating review for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit rejected with P1 stale-routing findings in `PLAN.md` and `BUILDLOG.md`
- [x] Continuity correction for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit accepted first-pass
- [x] Corrected commit-gating review for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit completed at `4030845`
- [x] Internal eval-only `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` sibling implementation/assets accepted as workspace-only state for `oracle_signal_dynamic_import_root_alias_probe_matrix`
- [x] Corrected docs/evidence/continuity reconciliation for internal `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` accepted after 1 correction
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` release unit cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` release unit cleared first-pass with `688 passed`
- [x] Commit-gating review for internal `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` release unit cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` release unit completed at `b85f038`
- [x] Source/contract prerequisite for exact unshadowed `import builtins` plus `builtins.__import__(name)` accepted first-pass as workspace-only state
- [x] Eval-only sibling `oracle_signal_dynamic_import_builtins_attr_probe_matrix` accepted first-pass as workspace-only state
- [x] Docs/evidence/continuity reconciliation for internal `DYNAMIC_IMPORT` / builtins-attribute `builtins.__import__(name)` accepted first-pass
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / builtins-attribute `builtins.__import__(name)` release candidate cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / builtins-attribute `builtins.__import__(name)` release candidate cleared first-pass with `696 passed`
- [x] Commit-gating review for internal `DYNAMIC_IMPORT` / builtins-attribute `builtins.__import__(name)` release unit cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / builtins-attribute `builtins.__import__(name)` release unit completed at `3dfc355`
- [x] Source/contract prerequisite for exact unshadowed `import builtins as loader` plus `loader.__import__(name)` accepted first-pass as workspace-only state
- [x] Eval-only sibling `oracle_signal_dynamic_import_builtins_alias_probe_matrix` accepted first-pass as workspace-only state
- [x] Corrected docs/evidence/continuity reconciliation for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` accepted after 1 correction
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate cleared first-pass with `702 passed`
- [x] First commit-gating review for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate rejected with P1 stale-routing findings in `PLAN.md` and `BUILDLOG.md`
- [x] Continuity routing correction for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate accepted first-pass
- [x] Corrected commit-gating review for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate rejected with one P1 stale-route finding in `PLAN.md`
- [x] PLAN-only stale-route correction for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate accepted first-pass
- [x] Corrected commit-gating review for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release unit cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release unit completed at `6ac1e28`
- [x] Internal eval-only `REFLECTIVE_BUILTIN` / `getattr(obj, name)`
  raised-`AttributeError` pilot implementation accepted first-pass as
  workspace-only state for `oracle_signal_getattr_attribute_error_probe_matrix`
- [x] Docs/evidence/continuity reconciliation for internal
  `REFLECTIVE_BUILTIN` / `getattr(obj, name)` raised-`AttributeError` pilot
  accepted after 2 corrections
- [x] Release-unit audit for internal `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot cleared first-pass
- [x] Full regression gate for internal `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot cleared first-pass with
  `709 passed`
- [x] First commit-gating review for internal `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot rejected with P1
  stale-routing findings in `PLAN.md` and `BUILDLOG.md`
- [x] Routing correction for internal `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot accepted first-pass
- [x] Corrected commit-gating review for internal `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal
  `REFLECTIVE_BUILTIN` / `getattr(obj, name)` raised-`AttributeError`
  release unit completed at `5bd0616`
- [x] Post-5bd0616 North Star planning/control decision selected the
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion as the next smallest evidence-building capability wedge
- [x] Bounded `oracle_signal_getattr_attribute_error_probe_matrix`
  budget-pressure expansion from `[220]` to `[220, 100]` accepted first-pass
  as workspace-only state
- [x] Docs/evidence/continuity reconciliation for the workspace-only accepted
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion accepted first-pass
- [x] Release-unit audit for the workspace-only accepted
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion cleared first-pass
- [x] Full regression gate for the workspace-only accepted
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion cleared first-pass with `709 passed`
- [x] Commit-gating review for the
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion release unit completed
- [x] Local commit creation and Ryan-authorized push for the
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion release unit completed at `43d0439`
- [x] Post-43d0439 North Star planning/control selected the
  `oracle_signal_dir_probe_matrix` budget-pressure expansion as the next
  smallest evidence-building capability wedge
- [x] Bounded `oracle_signal_dir_probe_matrix` budget-pressure expansion from
  `[220]` to `[220, 100]` accepted first-pass as workspace-only state
- [x] Docs/evidence/continuity reconciliation for the workspace-only accepted
  `oracle_signal_dir_probe_matrix` budget-pressure expansion accepted
  first-pass
- [x] Release-unit audit for the workspace-only accepted
  `oracle_signal_dir_probe_matrix` budget-pressure expansion cleared
  first-pass
- [x] Full regression gate for the workspace-only accepted
  `oracle_signal_dir_probe_matrix` budget-pressure expansion cleared
  first-pass with `709 passed`
- [x] Commit-gating review for the `oracle_signal_dir_probe_matrix`
  budget-pressure expansion release unit completed
- [x] Local commit creation and Ryan-authorized push for the
  `oracle_signal_dir_probe_matrix` budget-pressure expansion release unit
  completed at `ad9db8d`
- [x] Tranche batching / throughput discipline process-doc slice accepted
  first-pass by control review as workspace-only state
- [x] Corrected tranche batching / throughput discipline process-doc release
  unit passed the dedicated read-only release-unit audit rerun first-pass after
  one correction
- [x] Full regression over the current workspace for the corrected
  tranche-batching / throughput discipline process-doc release unit cleared
  first-pass with `ruff check`, `ruff format --check`, `mypy --strict`, and
  `pytest tests/ -v` reporting `709 passed`
- [x] First commit-gating review for the tranche-batching / throughput
  discipline process-doc release unit rejected with stale routing findings in
  `PLAN.md` and `BUILDLOG.md`
- [x] Corrected commit-gating review over `AGENTS.md`, `PLAN.md`, and
  `BUILDLOG.md` completed
- [x] Local commit creation and Ryan-authorized push for the tranche-batching /
  throughput discipline process-doc release unit completed at `125f088`
- [x] Internal eval-only `RUNTIME_MUTATION` / `delattr(obj, name)` budget
  expansion from `[220]` to `[220, 100]` accepted as workspace-only state
- [x] Internal eval-only `RUNTIME_MUTATION` / `setattr(obj, name, value)`
  budget expansion from `[220]` to `[220, 100]` accepted as workspace-only
  state
- [x] Findings-first control review for the docs/evidence/continuity
  reconciliation over the accepted workspace-only `delattr` and `setattr`
  budget expansion tranche accepted
- [x] Release-unit audit for the `RUNTIME_MUTATION` delattr/setattr
  budget-pressure tranche passed first-pass
- [x] Full regression gate for the audit-cleared `RUNTIME_MUTATION`
  delattr/setattr budget-pressure tranche cleared first-pass with
  `ruff check`, `ruff format --check`, `mypy --strict`, and
  `pytest tests/ -v` reporting `709 passed`
- [x] Commit-gating review for the `RUNTIME_MUTATION` delattr/setattr
  budget-pressure tranche completed
- [x] Local commit creation and Ryan-authorized push for the
  `RUNTIME_MUTATION` delattr/setattr budget-pressure release unit completed at
  `b8e126e`
- [x] Internal eval-only `DYNAMIC_IMPORT` sibling budget-pressure expansion
  across seven run specs and seven tests accepted after 1 correction as
  workspace-only state
- [x] Docs/evidence/continuity review for the `DYNAMIC_IMPORT` sibling
  budget-pressure release unit completed after 1 correction
- [x] Combined read-only release gate for the `DYNAMIC_IMPORT` sibling
  budget-pressure release unit completed
- [x] Full regression gate for the `DYNAMIC_IMPORT` sibling budget-pressure
  release unit cleared with `pytest tests/ -v` reporting `709 passed`
- [x] Commit-gating review for the `DYNAMIC_IMPORT` sibling budget-pressure
  release unit completed
- [x] Local commit creation and Ryan-authorized push for
  `c2c1898 Expand dynamic import sibling eval budget coverage` completed
- [x] Docs reconciliation for the internal `EXEC_OR_EVAL` eval/exec
  budget-pressure tranche accepted
- [x] Combined release-unit audit for the internal `EXEC_OR_EVAL` eval/exec
  budget-pressure release unit completed
- [x] Full regression gate for the internal `EXEC_OR_EVAL` eval/exec
  budget-pressure release unit cleared with `pytest tests/ -v` reporting
  `709 passed`
- [x] Commit-gating review for the internal `EXEC_OR_EVAL` eval/exec
  budget-pressure release unit completed
- [x] Local commit creation and Ryan-authorized push for
  `21f2dc5 Expand exec and eval budget coverage` completed
- [x] Internal eval-only zero-argument `dir()` and `METACLASS_BEHAVIOR`
  budget-pressure tranche implementation accepted first-pass
- [x] Docs/evidence/continuity reconciliation for the zero-argument `dir()` and
  `METACLASS_BEHAVIOR` budget-pressure tranche accepted after 1 correction
- [x] Combined release-unit audit for
  `e2f3dcf Expand dir-zero and metaclass budget coverage` passed
- [x] Full regression gate for
  `e2f3dcf Expand dir-zero and metaclass budget coverage` passed with
  `pytest tests/ -v` reporting `709 passed`
- [x] Commit-gating review for
  `e2f3dcf Expand dir-zero and metaclass budget coverage` passed
- [x] Local commit creation and Ryan-authorized push for
  `e2f3dcf Expand dir-zero and metaclass budget coverage` completed
- [x] Release-unit audit for
  `d73cde4 Expand original dynamic import budget coverage` completed
- [x] Focused validation for
  `d73cde4 Expand original dynamic import budget coverage` completed
- [x] Full regression gate for
  `d73cde4 Expand original dynamic import budget coverage` passed with
  `pytest tests/ -v` reporting `710 passed`
- [x] Commit-gating review for
  `d73cde4 Expand original dynamic import budget coverage` completed
- [x] Local commit creation and Ryan-authorized push for
  `d73cde4 Expand original dynamic import budget coverage` completed
- [x] Internal eval-only `REFLECTIVE_BUILTIN` `hasattr(obj, name)` false-branch
  and `vars(obj)` raised-`TypeError` tranche released at
  `546a4da Add reflective builtin branch eval probes`
- [x] Combined release gate for
  `546a4da Add reflective builtin branch eval probes` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `546a4da Add reflective builtin branch eval probes` completed
- [x] Runtime probe-request planning implementation accepted first-pass in
  workspace-only state
- [x] Combined release gate for
  `f6c66e4 Add runtime probe request planning contract` passed with no
  findings
- [x] Local commit creation and Ryan-authorized push for
  `f6c66e4 Add runtime probe request planning contract` completed
- [x] Diagnostic runtime probe-request bridge implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for
  `2e448ea Add diagnostic runtime probe request bridge` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `2e448ea Add diagnostic runtime probe request bridge` completed
- [x] Diagnose/recompile planned runtime probe request consumption
  implementation accepted first-pass in workspace-only state
- [x] Combined release gate for
  `a819cf5 Surface diagnostic runtime probe requests` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `a819cf5 Surface diagnostic runtime probe requests` completed
- [x] Stable planned runtime probe request identity implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for
  `49fa461 Add runtime probe request identities` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `49fa461 Add runtime probe request identities` completed
- [x] Planned runtime probe request ID indexing implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for
  `3df02c6 Index runtime probe requests by ID` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `3df02c6 Index runtime probe requests by ID` completed
- [x] Planned runtime probe request plan implementation accepted first-pass in
  workspace-only state
- [x] Combined release gate for
  `744bf0e Add runtime probe request plans` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `744bf0e Add runtime probe request plans` completed
- [x] Diagnostic runtime probe request plan bridge implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for
  `97dc0f6 Add diagnostic runtime probe request plans` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `97dc0f6 Add diagnostic runtime probe request plans` completed
- [x] Semantic diagnostic runtime probe request plan surfacing implementation
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact five-file
  `SemanticDiagnosticResult.planned_runtime_probe_request_plan` tranche
- [x] Local commit creation and Ryan-authorized push for the
  `SemanticDiagnosticResult.planned_runtime_probe_request_plan` tranche
- [x] Post-`7c46f48` North Star planning/control selected planned-side source-site
  indexing for runtime probe request plans
- [x] Planned runtime probe request plan source-site indexing implementation
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file planned runtime probe
  request plan source-site indexing tranche
- [x] Local commit creation and Ryan-authorized push for the planned runtime
  probe request plan source-site indexing tranche
- [x] Ryan authorized bounded internal observation-admission contract scope
- [x] Runtime observation admission read-model implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file internal runtime
  observation admission read-model tranche
- [x] Local commit creation and Ryan-authorized push for the internal runtime
  observation admission read-model tranche
- [x] Post-`b0a5ec5` North Star planning/control selected the diagnostic
  runtime observation admission bridge
- [x] Diagnostic runtime observation admission bridge implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file diagnostic runtime
  observation admission bridge tranche
- [x] Local commit creation and Ryan-authorized push for the diagnostic runtime
  observation admission bridge tranche
- [x] Post-`8706f2e` North Star planning/control selected runtime observation
  admission compatibility validation
- [x] Runtime observation admission compatibility validation implementation
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime observation
  admission compatibility validation tranche
- [x] Local commit creation and Ryan-authorized push for the runtime observation
  admission compatibility validation tranche
- [x] Post-`f5c8df0` North Star planning/control selected the internal
  admitted-runtime-observation provenance attachment bridge
- [x] Admitted runtime observation provenance attachment bridge implementation
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file admitted runtime
  observation provenance bridge tranche
- [x] Local commit creation and Ryan-authorized push for the admitted runtime
  observation provenance bridge tranche
- [x] Post-`35c440d` North Star planning/control selected the diagnostic runtime
  observation application helper
- [x] Diagnostic runtime observation application helper implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file diagnostic runtime
  observation application tranche
- [x] Local commit creation and Ryan-authorized push for the diagnostic runtime
  observation application tranche
- [x] Post-`95f7545` runtime-applied recompile consumption spike accepted
  first-pass
- [x] Diagnostic trace-refresh implementation slice accepted first-pass in
  workspace-only state
- [x] Combined release gate for the exact five-file diagnostic trace-refresh
  release unit
- [x] Local commit creation and Ryan-authorized push for the diagnostic
  trace-refresh release unit
- [x] Post-`74aadd7` North Star planning/control selected the internal runtime
  observation recompile composition helper
- [x] Runtime observation recompile composition helper implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime observation
  recompile composition release unit
- [x] Local commit creation and Ryan-authorized push for the runtime
  observation recompile composition release unit
- [x] Post-`b279b00` North Star planning/control selected a read-only
  exposed-consumption boundary spike
- [x] Exposed-consumption boundary spike accepted first-pass
- [x] Typed facade runtime observation recompile request/response slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file typed facade runtime
  recompile release unit
- [x] Local commit creation and Ryan-authorized push for the typed facade
  runtime recompile release unit
- [x] Post-`8ac3b46` execution-boundary spike accepted first-pass
- [x] Runtime probe execution-result/replay-artifact contract slice accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe result
  contract release unit
- [x] Local commit creation and Ryan-authorized push for the runtime probe
  result contract release unit
- [x] Post-`eb6def0` planning/control selected the internal execution-result
  to typed-observation admission boundary
- [x] Runtime probe result admission bridge implementation slice accepted after
  1 correction in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe result
  admission bridge release unit
- [x] Local commit creation and Ryan-authorized push for the runtime probe
  result admission bridge release unit
- [x] Post-`ccd417a` planning/control selected the internal result-batch to
  runtime recompile bridge
- [x] Runtime probe result-batch recompile bridge implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe result-batch
  recompile bridge release unit
- [x] Local commit creation and Ryan-authorized push for the runtime probe
  result-batch recompile bridge release unit
- [x] Post-`591c09b` planning/control selected the internal non-executing
  runtime probe execution-input materialization boundary
- [x] Runtime probe execution-input materialization implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe
  execution-input materialization release unit
- [x] Local commit creation for the runtime probe execution-input
  materialization release unit
- [x] Ryan-authorized push for the runtime probe
  execution-input materialization release unit
- [x] Post-`cfed3c7` planning/control selected the internal non-executing
  runtime probe execution-attempt to result-batch assembly boundary
- [x] Runtime probe execution-attempt result assembly implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe
  execution-attempt result assembly release unit
- [x] Local commit creation for the runtime probe execution-attempt result
  assembly release unit
- [x] Ryan-authorized push for the runtime probe execution-attempt result
  assembly release unit
- [x] Post-`86be8d7` planning/control selected the internal non-executing
  runtime probe runner-request materialization boundary
- [x] Runtime probe runner-request materialization implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe
  runner-request materialization release unit
- [x] Local commit creation for the runtime probe runner-request
  materialization release unit
- [x] Ryan-authorized push for the runtime probe runner-request
  materialization release unit
- [x] Post-`68a8e73` planning/control selected the internal non-executing
  runner-request attempt/result assembly gate
- [x] Runtime probe runner-request attempt/result assembly implementation
  slice accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe
  runner-request attempt/result assembly release unit
- [x] Local commit creation for the runtime probe runner-request attempt/result
  assembly release unit
- [x] Ryan-authorized push for the runtime probe runner-request attempt/result
  assembly release unit
- [x] Post-`3363929` planning/control selected the internal non-executing
  diagnostic runner-request preparation boundary
- [x] Runtime probe diagnostic runner-request preparation implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe diagnostic
  runner-request preparation release unit
- [x] Local commit creation for the runtime probe diagnostic runner-request
  preparation release unit
- [x] Ryan-authorized push for the runtime probe diagnostic runner-request
  preparation release unit
- [x] Post-`fd0f6d8` planning/control selected the internal runner-callable
  attempt collection boundary
- [x] Runtime probe runner-callable attempt collection implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe
  runner-callable attempt collection release unit
- [x] Local commit creation for the runtime probe runner-callable attempt
  collection release unit
- [x] Ryan-authorized push for the runtime probe runner-callable attempt
  collection release unit
- [x] Post-`32f6220` planning/control selected the internal diagnostic
  runner-callable recompile bridge
- [x] Runtime probe diagnostic runner-callable recompile bridge implementation
  slice accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe diagnostic
  runner-callable recompile bridge release unit
- [x] Local commit creation for the runtime probe diagnostic runner-callable
  recompile bridge release unit
- [x] Ryan-authorized push for the runtime probe diagnostic runner-callable
  recompile bridge release unit
- [x] Post-`74fb275` planning/control selected the internal runtime probe
  runner failure-normalization adapter
- [x] Runtime probe runner failure-normalization adapter implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe runner
  failure-normalization adapter release unit
- [x] Local commit creation for the runtime probe runner failure-normalization
  adapter release unit
- [x] Ryan-authorized push for the runtime probe runner failure-normalization
  adapter release unit
- [x] Post-`93456b6` planning/control selected the internal runtime probe
  runner dispatch table
- [x] Runtime probe runner dispatch table implementation slice accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe runner
  dispatch table release unit
- [x] Local commit creation for the runtime probe runner dispatch table
  release unit
- [x] Ryan-authorized push for the runtime probe runner dispatch table release
  unit
- [x] Post-`3751df1` planning/control selected the internal runtime probe
  runner environment context
- [x] Runtime probe runner environment context implementation slice accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe runner
  environment context release unit
- [x] Local commit creation for the runtime probe runner environment context
  release unit
- [x] Ryan-authorized push for the runtime probe runner environment context
  release unit
- [x] Post-`f75196e` planning/control selected the local Python runner
  execution-boundary spike
- [x] Local Python runner execution-boundary spike accepted first-pass
- [x] Local Python subprocess invocation contract implementation slice accepted
  first-pass in workspace-only state
- [x] Blank invocation revision negative-test correction for the local Python
  subprocess invocation contract
- [x] Combined release gate for the exact four-file local Python subprocess
  invocation contract release unit
- [x] Local commit creation for the local Python subprocess invocation
  contract release unit
- [x] Ryan-authorized push for the local Python subprocess invocation
  contract release unit
- [x] Post-`ea6ff8e` planning/control selected the local Python subprocess
  execution-boundary spike
- [x] Local Python subprocess execution-boundary spike accepted first-pass
- [x] Local Python process completion/result contract implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file local Python process
  completion contract release unit
- [x] Local commit creation for the local Python process completion contract
  release unit
- [x] Ryan-authorized push for the local Python process completion contract
  release unit
- [x] Post-`e9f87fc` planning/control selected the raw local Python subprocess
  execution boundary
- [x] Raw local Python subprocess execution boundary implementation slice
  accepted in workspace after one correction
- [x] Completion revision pre-run validation correction for the raw local
  Python subprocess execution boundary
- [x] Combined release gate for the exact four-file raw local Python
  subprocess execution boundary release unit
- [x] Local commit creation for the raw local Python subprocess execution
  boundary release unit
- [x] Ryan-authorized push for the raw local Python subprocess execution
  boundary release unit
- [x] Post-`d0a009b` planning/control selected the post-subprocess execution
  boundary next-move spike
- [x] Post-subprocess execution boundary next-move spike accepted first-pass
- [x] Local Python subprocess non-proof attempt normalization implementation
  slice accepted in workspace after one correction
- [x] Ryan decision on nonzero completion outcome-parameter test coverage
  finding
- [x] Nonzero completion outcome-parameter test coverage correction
- [x] Ryan decision on the local Python subprocess non-proof attempt
  normalization release-gate identity overclaim finding
- [x] Continuity/spec correction for the local Python subprocess non-proof
  attempt normalization identity claim
- [x] Combined release gate rerun for the exact four-file local Python
  subprocess non-proof attempt normalization release unit
- [x] Local commit creation for the local Python subprocess non-proof attempt
  normalization release unit
- [x] Ryan-authorized push for the local Python subprocess non-proof attempt
  normalization release unit
- [x] Post-`5b10728` planning/control selected a local Python success-boundary
  next-move spike
- [x] Local Python success-boundary next-move spike accepted first-pass
- [x] Local Python stdout/result protocol contract implementation slice accepted
  in workspace after one correction
- [x] Ryan decision on local Python stdout protocol durable-reference contract
  validation finding
- [x] Local Python stdout protocol durable-reference contract correction
- [x] Combined release gate for the exact four-file local Python stdout/result
  protocol contract release unit
- [x] Local commit creation for the local Python stdout/result protocol
  contract release unit
- [x] Ryan-authorized push for the local Python stdout/result protocol
  contract release unit
- [x] Post-`0c4a654` control selected local Python stdout protocol observed
  attempt materialization
- [x] Local Python stdout protocol observed-attempt materialization
  implementation slice
- [x] Combined release gate for the exact four-file local Python stdout
  protocol observed-attempt materialization release unit
- [x] Local commit creation for the local Python stdout protocol
  observed-attempt materialization release unit
- [x] Ryan-authorized push for the local Python stdout protocol
  observed-attempt materialization release unit
- [x] Post-`81a3ce3` control selected local Python stdout protocol failure
  normalization
- [x] Local Python stdout protocol failure-normalization implementation slice
- [x] Combined release gate for the exact four-file local Python stdout
  protocol failure-normalization release unit
- [x] Local commit creation for the local Python stdout protocol
  failure-normalization release unit
- [x] Ryan-authorized push for the local Python stdout protocol
  failure-normalization release unit
- [x] Post-`d8cf97b` control selected local Python executor-to-attempt wrapper
- [x] Local Python executor-to-attempt wrapper implementation slice accepted
  first-pass as workspace-only state
- [x] Combined release gate for the exact four-file local Python
  executor-to-attempt wrapper release unit
- [x] Local commit creation for the local Python executor-to-attempt wrapper
  release unit
- [x] Ryan-authorized push for the local Python executor-to-attempt wrapper
  release unit
- [x] Post-`8625186` control selected local Python runner handler adapter
- [x] Local Python runner handler adapter implementation slice accepted
  first-pass as workspace-only state
- [x] Combined release gate for the exact four-file local Python runner handler
  adapter release unit
- [x] Local commit creation for the local Python runner handler adapter release
  unit
- [x] Ryan-authorized push for the local Python runner handler adapter release
  unit
- [x] Post-`9b9b5cd` control selected local Python worker request payload
  contract
- [x] First local Python worker request payload implementation lane returned
  `NEEDS-CONTROL` on prompt wording
- [x] Clarified local Python worker request payload contract implementation
  slice accepted after two corrections as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  worker request payload contract release unit
- [x] Local commit creation for the local Python worker request payload
  contract release unit
- [x] Ryan-authorized push for the local Python worker request payload contract
  release unit
- [x] Post-`4d155ec` control selected local Python worker request stdin
  transport contract
- [x] Local Python worker request stdin transport contract implementation slice
  accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  worker request stdin transport contract release unit
- [x] Local commit creation for the local Python worker request stdin transport
  contract release unit
- [x] Ryan-authorized push for the local Python worker request stdin transport
  contract release unit
- [x] Post-`0a3c4c6` control selected local Python subprocess stdin execution
  wiring
- [x] Local Python subprocess stdin execution wiring implementation slice
  accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  subprocess stdin execution wiring release unit
- [x] Local commit creation for the local Python subprocess stdin execution
  wiring release unit
- [x] Ryan-authorized push for the local Python subprocess stdin execution
  wiring release unit
- [x] Post-`41f5df9` control selected local Python worker next-move spike
- [x] Local Python worker post-stdin-execution next-move spike accepted
  first-pass
- [x] Fail-closed local Python worker ingress skeleton implementation slice
  accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file fail-closed local
  Python worker ingress skeleton release unit
- [x] Local commit creation for the fail-closed local Python worker ingress
  skeleton release unit
- [x] Ryan-authorized push for the fail-closed local Python worker ingress
  skeleton release unit
- [x] Fail-closed local Python worker-side dispatch contract implementation
  slice accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file fail-closed local
  Python worker-side dispatch contract release unit
- [x] Local commit creation for the fail-closed local Python worker-side
  dispatch contract release unit
- [x] Ryan-authorized push for the fail-closed local Python worker-side
  dispatch contract release unit
- [x] Post-`7eefba2` control selected local Python worker stdout success egress
  contract
- [x] Local Python worker stdout success egress contract implementation slice
  accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  worker stdout success egress contract release unit
- [x] Local commit creation for the local Python worker stdout success egress
  contract release unit
- [x] Ryan-authorized push for the local Python worker stdout success egress
  contract release unit
- [x] Post-`9c6a3b5` control selected local Python dynamic-import worker
  request contract
- [x] Local Python dynamic-import worker request contract implementation slice
  accepted after one correction as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  dynamic-import worker request contract release unit
- [x] Local commit creation for the local Python dynamic-import worker request
  contract release unit
- [x] Ryan-authorized push for the local Python dynamic-import worker request
  contract release unit
- [x] Post-`c134b85` control selected local Python dynamic-import worker
  observation success-response contract
- [x] Local Python dynamic-import worker observation success-response contract
  implementation slice accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  dynamic-import worker observation success-response contract release unit
- [x] Local commit creation for the local Python dynamic-import worker
  observation success-response contract release unit
- [x] Ryan-authorized push for the local Python dynamic-import worker
  observation success-response contract release unit
- [x] Post-`6e8d04f` control selected local Python dynamic-import worker
  handler adapter
- [x] Local Python dynamic-import worker handler adapter implementation slice
  accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  dynamic-import worker handler adapter release unit
- [x] Local commit creation for the local Python dynamic-import worker handler
  adapter release unit
- [x] Ryan-authorized push for the local Python dynamic-import worker handler
  adapter release unit
- [x] Post-`73feb5f` control selected local Python dynamic-import worker
  replay target contract
- [x] Local Python dynamic-import worker replay target contract implementation
  slice accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  dynamic-import worker replay target contract release unit
- [x] Local commit creation for the local Python dynamic-import worker replay
  target contract release unit
- [x] Ryan-authorized push for the local Python dynamic-import worker replay
  target contract release unit
- [x] Post-`7fe4f76` control selected local Python dynamic-import import
  interception harness
- [x] Local Python dynamic-import import interception harness implementation
  slice accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  dynamic-import import interception harness release unit
- [x] Local commit creation for the local Python dynamic-import import
  interception harness release unit
- [x] Ryan-authorized push for the local Python dynamic-import import
  interception harness release unit
- [x] Post-`5fb6cf8` control selected local Python dynamic-import replay
  target attribute resolver
- [x] Local Python dynamic-import replay target attribute resolver
  implementation slice accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  dynamic-import replay target attribute resolver release unit
- [x] Local commit creation for the local Python dynamic-import replay target
  attribute resolver release unit
- [x] Ryan-authorized push for the local Python dynamic-import replay target
  attribute resolver release unit
- [x] Post-`bd2ba92` control selected local Python dynamic-import source module
  import harness
- [x] Local Python dynamic-import source module import harness implementation
  slice accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  dynamic-import source module import harness release unit
- [x] Local commit creation for the local Python dynamic-import source module
  import harness release unit
- [x] Ryan-authorized push for the local Python dynamic-import source module
  import harness release unit
- [x] Post-`f0eb9e1` control selected local Python dynamic-import concrete
  observer composition
- [x] Local Python dynamic-import concrete observer composition implementation
  slice acceptance
- [x] Combined read-only release gate for the exact four-file local Python
  dynamic-import concrete observer composition release unit
- [x] Local commit creation for the local Python dynamic-import concrete
  observer composition release unit
- [x] Ryan-authorized push for the local Python dynamic-import concrete
  observer composition release unit
- [x] Post-`79b635b` control selected local Python dynamic-import default
  worker handler registration
- [x] Local Python dynamic-import default worker handler registration
  implementation slice acceptance
- [x] Combined read-only release gate for the exact four-file local Python
  dynamic-import default worker handler registration release unit
- [x] Local commit creation for the local Python dynamic-import default worker
  handler registration release unit
- [x] Ryan-authorized push for the local Python dynamic-import default worker
  handler registration release unit
- [x] Post-`2c21798` control selected parent-side real-subprocess proof for
  the pushed dynamic-import default worker handler
- [x] Parent-side real-subprocess proof implementation slice accepted
  first-pass as workspace-only state
- [x] Combined read-only release gate for the exact three-file parent-side
  real-subprocess proof release unit
- [x] Local commit creation for the parent-side real-subprocess proof release
  unit
- [x] Ryan-authorized push for the parent-side real-subprocess proof release
  unit
- [x] Post-`cee4e9f` control selection of the next bounded north-star lane
- [x] Runtime probe real-subprocess recompile bridge proof implementation slice
  accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact three-file runtime probe
  real-subprocess recompile bridge proof release unit
- [x] Local commit creation for the runtime probe real-subprocess recompile
  bridge proof release unit
- [x] Ryan-authorized push for the runtime probe real-subprocess recompile
  bridge proof release unit
- [x] Post-`ced8850` control selected dynamic-import local-Python subprocess
  runner factory
- [x] Dynamic-import local-Python subprocess runner factory implementation
  slice accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file dynamic-import
  local-Python subprocess runner factory release unit
- [x] Local commit creation for the dynamic-import local-Python subprocess
  runner factory release unit
- [x] Ryan-authorized push for the dynamic-import local-Python subprocess
  runner factory release unit
- [x] Post-`6d4e04c` control selected dynamic-import local-Python recompile
  helper
- [x] Dynamic-import local-Python recompile helper implementation slice
  accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file dynamic-import
  local-Python recompile helper release unit
- [x] Local commit creation for the dynamic-import local-Python recompile
  helper release unit
- [x] Ryan-authorized push for the dynamic-import local-Python recompile
  helper release unit
- [x] Post-`842ddda` control selected dynamic-import local-Python tool facade
- [x] Dynamic-import local-Python tool-facade implementation slice accepted
  first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file dynamic-import
  local-Python tool-facade release unit
- [x] Local commit creation for the dynamic-import local-Python tool-facade
  release unit
- [x] Ryan-authorized push for the dynamic-import local-Python tool-facade
  release unit
- [x] Post-`88f7c74` control selection of the next bounded north-star lane
- [x] Read-only post-tool-facade dynamic-import subprocess form-broadening
  planning spike
- [x] Exact `dynamic_import:loader.import_module/1` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `dynamic_import:loader.import_module/1` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `dynamic_import:loader.import_module/1` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `dynamic_import:loader.import_module/1` local-Python subprocess release unit
- [x] Post-`db3eb8b` control selection of the next bounded north-star lane
- [x] Read-only post-`db3eb8b` dynamic-import subprocess next-form
  planning/decomposition lane
- [x] Exact `dynamic_import:import_module/1` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `dynamic_import:import_module/1` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `dynamic_import:import_module/1` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `dynamic_import:import_module/1` local-Python subprocess release unit
- [x] Post-`2035f4f` control selection of the next bounded north-star lane
- [x] Exact `dynamic_import:load_module/1` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `dynamic_import:load_module/1` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `dynamic_import:load_module/1` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `dynamic_import:load_module/1` local-Python subprocess release unit
- [x] Post-`a0f46f3` control selection of the next bounded north-star lane
- [x] Read-only planning/decomposition lane for the first exact builtin
  `__import__` local-Python subprocess form
- [x] Exact `dynamic_import:__import__/1` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `dynamic_import:__import__/1` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `dynamic_import:__import__/1` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `dynamic_import:__import__/1` local-Python subprocess release unit
- [x] Post-`1b08bb9` control selection of the next bounded north-star lane
- [x] Exact `dynamic_import:builtins.__import__/1` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `dynamic_import:builtins.__import__/1` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `dynamic_import:builtins.__import__/1` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `dynamic_import:builtins.__import__/1` local-Python subprocess release unit
- [x] Post-`9a88794` control selection of the next bounded north-star lane
- [x] Exact `dynamic_import:loader.__import__/1` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `dynamic_import:loader.__import__/1` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `dynamic_import:loader.__import__/1` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `dynamic_import:loader.__import__/1` local-Python subprocess release unit
- [x] Post-`82bbb59` control selection of the next bounded north-star lane
- [x] Read-only post-dynamic-import runtime-probe next-family planning and
  decomposition spike
- [x] Exact `reflective_builtin:hasattr/2` local-Python subprocess
  implementation slice
- [x] Correction for `reflective_builtin:hasattr/2` target-time
  `builtins.hasattr` deletion restoration
- [x] Combined read-only release gate for the exact six-file
  `reflective_builtin:hasattr/2` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `reflective_builtin:hasattr/2` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `reflective_builtin:hasattr/2` local-Python subprocess release unit
- [x] Post-`b9f7bb6` control selection of the next bounded north-star lane
- [x] Exact `reflective_builtin:getattr/2` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `reflective_builtin:getattr/2` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `reflective_builtin:getattr/2` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `reflective_builtin:getattr/2` local-Python subprocess release unit
- [x] Post-`50daeab` control selection of the next bounded north-star lane
- [x] Exact `reflective_builtin:getattr/3` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `reflective_builtin:getattr/3` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `reflective_builtin:getattr/3` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `reflective_builtin:getattr/3` local-Python subprocess release unit
- [x] Post-`24cb38b` control selection of the next bounded north-star lane
- [x] Exact `reflective_builtin:vars/1` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `reflective_builtin:vars/1` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `reflective_builtin:vars/1` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `reflective_builtin:vars/1` local-Python subprocess release unit
- [x] Post-`3b8053f` control selection of the next bounded north-star lane
- [x] Exact `reflective_builtin:vars/0` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `reflective_builtin:vars/0` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `reflective_builtin:vars/0` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `reflective_builtin:vars/0` local-Python subprocess release unit
- [x] Post-`230c8cf` control selection of the next bounded north-star lane
- [x] Exact `reflective_builtin:dir/1` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `reflective_builtin:dir/1` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `reflective_builtin:dir/1` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `reflective_builtin:dir/1` local-Python subprocess release unit
- [x] Post-`01c2907` control selection of the next bounded north-star lane
- [x] Exact `reflective_builtin:dir/0` local-Python subprocess
  implementation slice
- [x] Combined read-only release gate for the exact six-file
  `reflective_builtin:dir/0` local-Python subprocess release unit
- [x] Local commit creation for the exact six-file
  `reflective_builtin:dir/0` local-Python subprocess release unit
- [x] Ryan-authorized push for the exact six-file
  `reflective_builtin:dir/0` local-Python subprocess release unit
- [x] Post-`64de22b` control selection of the next bounded north-star lane
- [x] Exact `runtime_mutation:globals/0` local-Python subprocess implementation
  slice
- [x] Release-unit audit for exact `runtime_mutation:globals/0` local-Python
  subprocess release unit
- [x] Full regression gate for exact `runtime_mutation:globals/0` local-Python
  subprocess release unit
- [x] Commit-gating review for exact `runtime_mutation:globals/0` local-Python
  subprocess release unit
- [x] Local commit creation for exact `runtime_mutation:globals/0` local-Python
  subprocess release unit
- [x] Ryan-authorized remote push for exact `runtime_mutation:globals/0`
  local-Python subprocess release unit
- [x] Post-`5804c98` control selection of the next bounded north-star lane
- [x] Exact `runtime_mutation:locals/0` local-Python subprocess implementation
  slice
- [x] Release-unit audit for exact `runtime_mutation:locals/0` local-Python
  subprocess release unit
- [x] Full regression gate for exact `runtime_mutation:locals/0` local-Python
  subprocess release unit
- [x] Commit-gating review for exact `runtime_mutation:locals/0` local-Python
  subprocess release unit
- [x] Local commit creation for exact `runtime_mutation:locals/0` local-Python
  subprocess release unit
- [x] Ryan-authorized remote push for exact `runtime_mutation:locals/0`
  local-Python subprocess release unit
- [x] Post-`4f6b7e3` control selection of the next bounded north-star lane
- [x] Exact `runtime_mutation:delattr/2` local-Python subprocess implementation
  slice
- [x] Release-unit audit for exact `runtime_mutation:delattr/2` local-Python
  subprocess release unit
- [x] Full regression gate for exact `runtime_mutation:delattr/2` local-Python
  subprocess release unit
- [x] Commit-gating review for exact `runtime_mutation:delattr/2` local-Python
  subprocess release unit
- [x] Local commit creation for exact `runtime_mutation:delattr/2` local-Python
  subprocess release unit
- [x] Ryan-authorized remote push for exact `runtime_mutation:delattr/2`
  local-Python subprocess release unit
- [x] Post-`5b8da0a` control selection of the next bounded north-star lane
- [x] Exact `runtime_mutation:setattr/3` local-Python subprocess implementation
  slice
- [x] Release-unit audit for exact `runtime_mutation:setattr/3` local-Python
  subprocess release unit
- [x] Full regression gate for exact `runtime_mutation:setattr/3` local-Python
  subprocess release unit
- [x] Commit-gating review for exact `runtime_mutation:setattr/3` local-Python
  subprocess release unit
- [x] Local commit creation for exact `runtime_mutation:setattr/3` local-Python
  subprocess release unit
- [x] Ryan-authorized remote push for exact `runtime_mutation:setattr/3`
  local-Python subprocess release unit
- [x] Post-`1f4b9e3` control selection of the next bounded north-star lane
- [x] Read-only `EXEC_OR_EVAL` local-Python subprocess source-proof contract
  planning spike
- [x] Exact `exec_or_eval:exec/1` local-Python subprocess implementation slice
- [x] Release-unit audit for exact `exec_or_eval:exec/1` local-Python
  subprocess release unit
- [x] Full regression gate for exact `exec_or_eval:exec/1` local-Python
  subprocess release unit
- [x] Commit-gating review for exact `exec_or_eval:exec/1` local-Python
  subprocess release unit
- [x] Local commit creation for exact `exec_or_eval:exec/1` local-Python
  subprocess release unit
- [x] Ryan-authorized remote push for exact `exec_or_eval:exec/1`
  local-Python subprocess release unit
- [x] Post-`07bb58f` control selection of the next bounded north-star lane
- [x] Exact `exec_or_eval:eval/1` local-Python subprocess implementation slice
- [x] Release-unit audit for exact `exec_or_eval:eval/1` local-Python
  subprocess release unit
- [x] Full regression gate for exact `exec_or_eval:eval/1` local-Python
  subprocess release unit
- [x] Commit-gating review for exact `exec_or_eval:eval/1` local-Python
  subprocess release unit
- [x] Local commit creation for exact `exec_or_eval:eval/1` local-Python
  subprocess release unit
- [x] Ryan-authorized remote push for exact `exec_or_eval:eval/1`
  local-Python subprocess release unit
- [x] Post-`f3467e5` control selection of the next bounded north-star lane
- [x] Exact `metaclass_behavior:keyword` local-Python subprocess
  implementation slice
- [x] First release-unit audit for exact `metaclass_behavior:keyword`
  local-Python subprocess release unit returned P1 base-class finding
- [x] Correction slice for exact `metaclass_behavior:keyword` local-Python
  subprocess base-class support
- [x] Corrected release-unit audit for exact `metaclass_behavior:keyword`
  local-Python subprocess release unit
- [x] Full regression gate for exact `metaclass_behavior:keyword` local-Python
  subprocess release unit
- [x] Commit-gating review for exact `metaclass_behavior:keyword` local-Python
  subprocess release unit
- [x] Local commit creation for exact `metaclass_behavior:keyword`
  subprocess release unit
- [x] Ryan-authorized remote push for exact `metaclass_behavior:keyword`
  local-Python subprocess release unit
- [x] Post-`20e6f55` control selection of the next bounded north-star lane
- [x] Parent-side exact default local-Python subprocess runner factory
  implementation slice
- [x] Release-unit audit for parent-side exact default local-Python subprocess
  runner factory release unit
- [x] Full regression gate for parent-side exact default local-Python
  subprocess runner factory release unit
- [x] Commit-gating review for parent-side exact default local-Python
  subprocess runner factory release unit
- [x] Local commit creation for parent-side exact default local-Python
  subprocess runner factory release unit
- [x] Ryan-authorized remote push for parent-side exact default local-Python
  subprocess runner factory release unit
- [x] Post-`92824aa` control selection of the next bounded north-star lane
- [x] Internal default local-Python subprocess recompile helper implementation
  slice
- [x] Release-unit audit for internal default local-Python subprocess
  recompile helper release unit
- [x] Full regression gate for internal default local-Python subprocess
  recompile helper release unit
- [x] Commit-gating review for internal default local-Python subprocess
  recompile helper release unit
- [x] Local commit creation for internal default local-Python subprocess
  recompile helper release unit
- [x] Ryan-authorized remote push for internal default local-Python subprocess
  recompile helper release unit
- [x] Post-`0334911` control selection of the next bounded north-star lane
- [x] Tool-facing default local-Python subprocess recompile wrapper
  implementation slice
- [x] Release-unit audit for tool-facing default local-Python subprocess
  recompile wrapper release unit
- [x] Full regression gate for tool-facing default local-Python subprocess
  recompile wrapper release unit
- [x] Commit-gating review for tool-facing default local-Python subprocess
  recompile wrapper release unit
- [x] Local commit creation for tool-facing default local-Python subprocess
  recompile wrapper release unit
- [x] Ryan-authorized remote push for tool-facing default local-Python subprocess
  recompile wrapper release unit
- [x] Post-`7ee092b` control selection of the next bounded north-star lane
- [x] Exposure-boundary planning spike after default local-Python facade
- [x] Non-public north-star planning spike after no-exposure decision
- [x] Test-only eval-fixture subprocess proof for default local-Python facade
- [x] Combined read-only release gate for test-only eval-fixture subprocess
  proof release unit
- [x] Local commit creation for test-only eval-fixture subprocess proof release
  unit
- [x] Ryan-authorized remote push for test-only eval-fixture subprocess proof
  release unit
- [x] Post-`667fcdc` control selection of the next bounded north-star lane
- [x] Read-only eval-provider/run-spec subprocess integration planning spike
- [x] Ryan authorization for internal eval provider/result provenance-carrier
  contract slice
- [x] Internal eval provider/result provenance-carrier implementation slice
- [x] Release-unit audit for internal eval provider/result provenance-carrier
  release unit
- [x] Full regression gate for internal eval provider/result provenance-carrier
  release unit
- [x] Commit-gating review for internal eval provider/result provenance-carrier
  release unit
- [x] Local commit creation for internal eval provider/result provenance-carrier
  release unit
- [x] Ryan-authorized remote push for internal eval provider/result
  provenance-carrier release unit
- [x] Post-`165bb43` control selection of the next bounded north-star lane
- [x] Internal `context_ir_default_local_python_subprocess` provider slice for
  exact `oracle_signal_locals_probe`
- [x] Release-unit audit for internal default local-Python subprocess eval
  provider release unit
- [x] Full regression gate for internal default local-Python subprocess eval
  provider release unit
- [x] Commit-gating review for internal default local-Python subprocess eval
  provider release unit
- [x] Local commit creation for internal default local-Python subprocess eval
  provider release unit
- [x] Ryan-authorized remote push for internal default local-Python subprocess
  eval provider release unit
- [x] Post-`5133ac8` control selection of the next bounded north-star lane
- [x] Internal `context_ir_default_local_python_subprocess` provider slice for
  exact `oracle_signal_globals_probe`
- [x] Release-unit audit for internal default local-Python subprocess globals
  provider release unit
- [x] Full regression gate for internal default local-Python subprocess globals
  provider release unit
- [x] Commit-gating review for internal default local-Python subprocess globals
  provider release unit
- [x] Local commit creation for internal default local-Python subprocess globals
  provider release unit
- [x] Ryan-authorized remote push for internal default local-Python subprocess
  globals provider release unit
- [x] Post-`037e64b` control selection of the next bounded north-star lane
- [x] Internal `context_ir_default_local_python_subprocess` provider slice for
  exact `oracle_signal_vars_zero_probe`
- [x] Release-unit audit for internal default local-Python subprocess vars-zero
  provider release unit
- [x] Full regression gate for internal default local-Python subprocess
  vars-zero provider release unit
- [x] Commit-gating review for internal default local-Python subprocess
  vars-zero provider release unit
- [x] Local commit creation for internal default local-Python subprocess
  vars-zero provider release unit
- [x] Ryan-authorized remote push for internal default local-Python subprocess
  vars-zero provider release unit
- [x] Post-`eef7173` control selection of the next bounded north-star lane
- [x] Exec/eval observed replay-input preservation correction for default
  local-Python subprocess recompile
- [x] Release-unit audit for exec/eval observed replay-input preservation
  correction release unit
- [x] Full regression gate for exec/eval observed replay-input preservation
  correction release unit
- [x] Commit-gating review for exec/eval observed replay-input preservation
  correction release unit
- [x] Local commit creation for exec/eval observed replay-input preservation
  correction release unit
- [x] Ryan-authorized remote push for exec/eval observed replay-input
  preservation correction release unit
- [x] Post-`53c82df` control selection of the next bounded north-star lane
- [x] Internal `context_ir_default_local_python_subprocess` provider slice for
  exact `oracle_signal_exec_probe` and `oracle_signal_eval_probe`
- [x] Release-unit audit for internal default local-Python subprocess exec/eval
  provider release unit
- [x] Full regression gate for internal default local-Python subprocess exec/eval
  provider release unit
- [x] Commit-gating review for internal default local-Python subprocess exec/eval
  provider release unit
- [x] Local commit creation for internal default local-Python subprocess exec/eval
  provider release unit
- [x] Ryan-authorized remote push for internal default local-Python subprocess
  exec/eval provider release unit
- [x] Post-`125c44e` control selection of the next bounded north-star lane
- [x] Internal `context_ir_default_local_python_subprocess` provider slice for
  exact `oracle_signal_metaclass_behavior_probe`
- [x] Release-unit audit for internal default local-Python subprocess metaclass
  provider release unit
- [x] Full regression gate for internal default local-Python subprocess
  metaclass provider release unit
- [x] Commit-gating review for internal default local-Python subprocess
  metaclass provider release unit
- [x] Local commit creation for internal default local-Python subprocess
  metaclass provider release unit
- [x] Ryan-authorized remote push for internal default local-Python subprocess
  metaclass provider release unit
- [ ] Post-`0650bb8` control selection of the next bounded north-star lane

## What Is In Progress

- Exact `oracle_signal_exec_probe` and `oracle_signal_eval_probe` support
  inside `context_ir_default_local_python_subprocess` is locally committed and
  pushed at `125c44e Add exec/eval default subprocess eval provider` with
  explicit Ryan authorization. Do not route it back to release-unit audit, full
  regression, commit-gating, staging, local commit, or push absent new findings.
- Post-`125c44e` route selection is complete and superseded by the pushed
  `0650bb8 Add metaclass default subprocess eval provider` release. It
  selected the exact internal provider-support slice for
  `oracle_signal_metaclass_behavior_probe`, and that slice has now completed
  all release gates, local commit creation, and Ryan-authorized push.
- Exact `oracle_signal_metaclass_behavior_probe` support inside
  `context_ir_default_local_python_subprocess` is locally committed and pushed
  at `0650bb8 Add metaclass default subprocess eval provider` with explicit
  Ryan authorization. The release unit is `BUILDLOG.md`,
  `PLAN.md`, `src/context_ir/eval_providers.py`,
  `tests/test_eval_signal_metaclass_behavior_probe.py`,
  `tests/test_eval_signal_locals_probe.py`,
  `tests/test_eval_signal_globals_probe.py`, and
  `tests/test_eval_signal_vars_zero_probe.py`. The implementation adds only
  the exact metaclass fixture-map entry, validates the exact
  `RuntimeProbeFamily.METACLASS_BEHAVIOR` / `metaclass_behavior:keyword`
  planned request, requires boundary `metaclass=Meta`, subject
  `unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1`, replay
  target seed `main.Example`, one runner attempt, one observed result, and the
  expected created-class payload, uses `sys.executable` with `delta_budget=0`,
  returns provider-owned runtime provenance, preserves unsupported/opaque
  primary truth, and does not select `def:main.py:main.Meta`. Focused control
  validation passed with ruff, format check, strict mypy, targeted pytest
  reporting `77 passed`, and clean `git diff --check`. A dedicated read-only
  release-unit audit passed first-pass with no findings. Full regression passed
  first-pass with ruff, format check, strict mypy, full pytest reporting
  `1657 passed`, and clean final `git diff --check`. This release unit is
  release-unit-audit-cleared, full-regression-cleared,
  commit-gating-cleared, locally committed, and pushed. Do not route it back
  to release-unit audit, full regression, commit-gating, staging, local commit,
  or push absent new findings. Next route is control selection of the next
  bounded north-star lane from the pushed `0650bb8` authority.
- No implementation or release-gate lane is currently in progress. The active
  control action is selecting the next bounded north-star lane from the pushed
  `0650bb8` authority.
- Exact exec/eval observed replay-input preservation for default local-Python
  subprocess recompile is locally committed and pushed at
  `53c82df Preserve exec/eval observed replay inputs` with explicit Ryan
  authorization. Do not route it back to release-unit audit, full regression,
  commit-gating, staging, local commit, or push absent new findings.

## Historical Active Notes

- Post-`eef7173` control selection is accepted in workspace first-pass. Live
  git state was verified as branch `main`, `HEAD` and `origin/main` at
  `eef7173 Add vars-zero default subprocess eval provider`, no staged files,
  no untracked files, and only `BUILDLOG.md` and `PLAN.md` dirty before that
  route update. The selected correction implementation is now accepted
  workspace-only; do not add provider support, metaclass support, public
  docs/claims, package-root exports, MCP, run-spec schema/config, eval assets,
  scoring, compiler, runtime worker, or new runtime-probe forms in this
  release unit.
- Exact `oracle_signal_vars_zero_probe` support inside
  `context_ir_default_local_python_subprocess` is locally committed and pushed
  at `eef7173 Add vars-zero default subprocess eval provider` with explicit
  Ryan authorization. Do not route it back to release-unit audit, full
  regression, commit-gating, staging, local commit, or push absent new
  findings. Route next to selection of the next bounded north-star lane from
  the pushed `eef7173` authority.
- Exact `oracle_signal_globals_probe` support inside
  `context_ir_default_local_python_subprocess` is locally committed and pushed
  at `037e64b Add globals default subprocess eval provider` with explicit Ryan
  authorization. Do not route it back to release-unit audit, full regression,
  commit-gating, staging, local commit, or push absent new findings.
- Post-`037e64b` control selection is accepted in workspace first-pass. Live
  git state was verified as branch `main`, `HEAD` and `origin/main` at
  `037e64b Add globals default subprocess eval provider`, clean worktree, no
  staged files, no untracked files, and clean `git diff --check` before this
  route update. The selected next bounded north-star lane is one exact
  internal provider-support slice: extend
  `context_ir_default_local_python_subprocess` from exact
  `oracle_signal_locals_probe` and `oracle_signal_globals_probe` to exact
  `oracle_signal_vars_zero_probe`. A live read-only dry run through the
  existing default local-Python subprocess facade proved the vars-zero fixture
  plans `RuntimeProbeFamily.REFLECTIVE_BUILTIN` /
  `reflective_builtin:vars/0` for boundary `vars()`, subject
  `unsupported:call:main.py:2:11`, observes
  `lookup_outcome=returned_namespace`, selects the unsupported `vars()` unit,
  and produces one runtime provenance record. Do not widen package-root
  exports, MCP, CLI/product, public docs/claims, run-spec schema/config, eval
  assets, scoring formulas, compiler behavior, runtime-probe forms, or
  generalized provider support in this lane.
- Historical post-`5133ac8` control selection was accepted in workspace
  first-pass and is now closed by the pushed `037e64b` globals-provider
  release. Live
  git state was verified as branch `main`, `HEAD` and `origin/main` at
  `5133ac8 Add default local-Python subprocess eval provider`, no staged
  files, no untracked files, and only `BUILDLOG.md` and `PLAN.md` dirty before
  this route update. The selected next bounded north-star lane is one exact
  internal provider-support slice: extend
  `context_ir_default_local_python_subprocess` from
  `oracle_signal_locals_probe` to exact `oracle_signal_globals_probe`. A live
  read-only dry run through the existing default local-Python subprocess
  facade proved the globals fixture plans `runtime_mutation:globals/0` for
  boundary `globals()` and observes `lookup_outcome=returned_namespace`.
  Do not widen package-root exports, MCP, CLI/product, public docs/claims,
  run-spec schema/config, eval assets, scoring formulas, compiler behavior,
  runtime-probe forms, or generalized provider support in this lane. This
  route is historical and must not override the post-`037e64b` vars-zero
  route above.
- Internal `context_ir_default_local_python_subprocess` provider implementation
  is accepted in workspace first-pass. The accepted release unit is
  `BUILDLOG.md`, `PLAN.md`, `src/context_ir/eval_metrics.py`,
  `src/context_ir/eval_providers.py`, `src/context_ir/eval_runs.py`,
  `tests/test_eval_metrics.py`, `tests/test_eval_runs.py`, and
  `tests/test_eval_signal_locals_probe.py`. The slice adds one internal exact
  provider for `oracle_signal_locals_probe`, registers it through the existing
  provider-name dispatch path, compiles the initial fixture without
  fixture-loaded runtime observations, diagnoses exact `locals()`, runs the
  pushed default local-Python subprocess facade with `sys.executable` and
  `delta_budget=0`, validates `lookup_outcome=returned_namespace`, carries
  provider-owned runtime provenance records, and treats the new provider as a
  semantic selected-unit provider for eval metrics without changing scoring
  formulas. Focused validation passed, including strict mypy and targeted
  pytest with `51 passed`. The release-unit audit passed first-pass with no
  findings. Full regression passed first-pass with `1640 passed`.
  Commit-gating passed first-pass with no findings. The release unit is
  locally committed and pushed at
  `5133ac8 Add default local-Python subprocess eval provider` with explicit
  Ryan authorization. Do not route this pushed release back to release-unit
  audit, full regression, commit-gating, staging, local commit, or push absent
  new findings.
- Internal eval provider/result provenance-carrier implementation is accepted
  in workspace first-pass, release-unit-audit-cleared first-pass, and
  full-regression-cleared first-pass, and commit-gating-cleared first-pass.
  The accepted release unit is `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/eval_providers.py`, `src/context_ir/eval_results.py`,
  `tests/test_eval_results.py`, and
  `tests/test_eval_signal_locals_probe.py`. The slice adds a default-empty
  provider-owned runtime provenance carrier to `EvalProviderResult`, keeps raw
  eval JSON top-level keys compatible, resolves attached runtime provenance
  from fixture-loaded setup records first and provider-owned records second,
  fails closed on missing attached runtime provenance IDs, and proves
  subprocess-derived `oracle_signal_locals_probe` provenance serialization
  without fixture-loaded setup provenance. It does not add a provider, modify
  run specs/tasks/fixtures, widen public/package-root/MCP surfaces, change
  docs/claims/scoring/compiler behavior, add generalized runtime support, or
  add runtime-probe forms. Full regression passed with `1636 passed`. It is
  locally committed and pushed at
  `165bb43 Carry eval runtime provenance in provider results` with explicit
  Ryan authorization. Do not route this pushed release back to release-unit
  audit, full regression, commit-gating, staging, local commit, or push absent
  new findings.
- Ryan-authorized internal eval provider/result provenance-carrier contract
  implementation is consumed by the pushed `165bb43` release. It added
  provider-owned runtime provenance carrying so future subprocess-backed
  providers do not depend on fixture-loaded provenance IDs, without adding a
  new provider, modifying run specs/tasks/fixtures, widening public,
  package-root, or MCP surfaces, changing scoring/compiler/docs/claims, adding
  generalized runtime support, or adding runtime-probe forms.
- The read-only eval-provider/run-spec subprocess integration planning spike is
  accepted first-pass and consumed by the pushed `165bb43` internal
  provenance-carrier release. The accepted finding was that a
  subprocess-backed eval provider is not honest until `EvalProviderResult` /
  eval record serialization can carry provider-derived runtime provenance
  records instead of resolving all attached runtime provenance IDs against the
  fixture-loaded oracle setup program. The recommended narrow internal
  provenance-carrier contract slice has been implemented, release-gated,
  locally committed, and pushed with explicit Ryan authorization.
- Post-`165bb43` control selected the next bounded north-star lane: one
  internal exact provider named
  `context_ir_default_local_python_subprocess`, scoped initially to
  `oracle_signal_locals_probe`. The provider must replay the existing locals
  fixture through the pushed default local-Python subprocess facade, return
  provider-owned runtime provenance records, and register through the existing
  run-spec provider-name mechanism. The slice may update semantic-provider
  metric classification so the new provider is scored like `context_ir`, but
  it must not add run-spec configuration fields, edit durable eval assets,
  widen public/package-root/MCP surfaces, change docs/claims/scoring formulas,
  add generalized runtime support, add runtime-probe forms, or broaden beyond
  the exact locals fixture.
- Post-`667fcdc` control selected one read-only planning/decomposition spike
  as the next bounded north-star lane. The spike should decide whether and how
  to integrate the pushed default local-Python subprocess facade into the
  internal eval provider/run-spec path. This is not an implementation lane.
  It must not widen package-root, MCP, CLI/product, public claims, schema,
  scoring, compiler, docs, eval fixtures, tasks, run specs, generalized
  runtime, or runtime-probe forms. The concrete question is how to move beyond
  fixture-loaded runtime observations in `src/context_ir/eval_providers.py`
  without broadening public exposure or losing additive-only runtime
  provenance discipline.
- Test-only eval-fixture subprocess proof for the default local-Python facade
  is accepted in workspace first-pass and has passed release-unit audit, full
  regression, commit-gating, local commit creation, and Ryan-authorized remote
  push first-pass. The
  accepted release unit is exactly `BUILDLOG.md`, `PLAN.md`, and
  `tests/test_eval_signal_locals_probe.py`. The test builds the existing
  `oracle_signal_locals_probe` fixture response without fixture-loaded runtime
  observations, diagnoses exact `locals()`, proves the planned request is
  exact `runtime_mutation:locals/0`, invokes the real
  `python -m context_ir.runtime_probe_worker` path through
  `recompile_repository_context_with_default_local_python_subprocess(...)`,
  and confirms additive runtime provenance while primary truth remains
  `unsupported/opaque`. The accepted slice did not touch `src/`, eval assets,
  provider/schema/run-specs, package-root, MCP, CLI/product, docs, README,
  EVAL, PUBLIC_CLAIMS, scoring, compiler, generalized runtime, or new
  runtime-probe forms. It is locally committed at
  `667fcdc Prove locals fixture through default subprocess facade` and pushed
  with explicit Ryan authorization. Do not route it back to release gates
  absent new findings.
- Non-public north-star planning after the no-exposure decision is accepted
  first-pass with no findings. The selected next lane is one test-only internal
  eval proof in `tests/test_eval_signal_locals_probe.py`: prove that the pushed
  default local-Python subprocess facade can replay the existing
  `oracle_signal_locals_probe` fixture through a real
  `python -m context_ir.runtime_probe_worker` subprocess and attach additive
  runtime provenance through recompile. This is not a source/API, eval-provider,
  run-spec, public exposure, docs/claims, or generalized runtime slice.
- Exposure-boundary planning after `7ee092b` is accepted first-pass with no
  findings. The accepted decision is no exposure change yet:
  `context_ir.tool_facade` remains the highest exposed boundary for the default
  local-Python subprocess recompile capability. Package-root exposure, MCP
  recompile tooling, CLI/product exposure, and public-claims updates are held
  absent explicit Ryan authorization or a new control finding. The next bounded
  lane is one read-only non-public north-star planning/decomposition spike to
  choose the next internal runtime-backed or evidence/ergonomics move.
- The prior post-`7ee092b` route selection has been consumed by the accepted
  exposure-boundary planning result. It has release-gate status no-active-gate
  and must not be rerun absent a new finding.
- Tool-facing default local-Python subprocess recompile wrapper is accepted,
  release-gate-cleared, locally committed, and pushed at
  `7ee092b Add default local-Python recompile facade`. The committed release
  unit is
  `src/context_ir/tool_facade.py` and `tests/test_tool_facade.py`; `PLAN.md`
  and `BUILDLOG.md` were included as continuity/routing files. The wrapper
  composes the pushed
  `apply_default_local_python_subprocess_for_diagnostic_and_recompile(...)`
  helper, exposes request/response/function names only through
  `context_ir.tool_facade.__all__`, and proves exact non-dynamic
  `runtime_mutation:locals/0` through real local-Python subprocess execution,
  worker observation, admission, and attached-runtime recompile. The accepted
  slice did not widen package-root exports, MCP, schema, scoring, compiler,
  docs, fixtures, tasks, run specs, public claims, generalized runtime
  support, or new runtime-probe forms. Full regression passed first-pass with
  `1633 passed`. Commit-gating passed first-pass with no findings.
  Ryan-authorized push completed. It has release-gate status no-active-gate.
- Internal default local-Python subprocess recompile helper is pushed at
  `0334911 Add default local-Python recompile helper`. The helper composes the
  pushed
  `make_runtime_probe_default_local_python_subprocess_runner(...)` with the
  existing generic runner-callable recompile bridge and remains internal to
  `context_ir.runtime_observation_recompile`. Focused coverage proves exact
  non-dynamic `runtime_mutation:locals/0` through real local-Python subprocess
  execution, observed result, admission, and attached-runtime recompile. The
  accepted slice did not widen `src/context_ir/runtime_probe_worker.py`,
  `src/context_ir/runtime_probe_execution.py`, runtime request/replay
  assembly, admission, acquisition, analyzer, tool facade, package-root
  exports, MCP, schema, scoring, compiler, docs, fixtures, tasks, run specs,
  public claims, generalized runtime support, or new runtime-probe forms. It
  has release-gate status no-active-gate.
- Parent-side exact default local-Python subprocess runner factory is
  accepted, release-gate-cleared, locally committed, and pushed at
  `92824aa Add default local-Python subprocess runner`. The committed release
  unit is `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`, and
  `tests/test_runtime_probe_execution.py`. The helper composes the currently
  pushed exact local-Python subprocess forms through the existing default
  worker and dispatching runner mechanism, while preserving all per-form
  factories and package-root non-exposure. The accepted slice did not widen
  `src/context_ir/runtime_probe_worker.py`, runtime request/replay assembly,
  admission, acquisition, recompile helpers, tool facade, package-root
  exports, MCP, schema, scoring, compiler, docs, fixtures, tasks, run specs,
  public claims, generalized runtime support, or new runtime-probe forms. The
  read-only release-unit audit passed first-pass with no findings. Full
  regression passed first-pass with `1630 passed`. Commit-gating review passed
  first-pass with no findings. Ryan-authorized push completed. It has
  release-gate status no-active-gate.
- Exact `metaclass_behavior:keyword` local-Python subprocess support is
  accepted, release-gate-cleared, locally committed, and pushed at
  `20e6f55 Add metaclass keyword subprocess support`. The pushed release unit is
  `BUILDLOG.md`, `PLAN.md`, `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`. The first release-unit audit returned
  a P1 base-class finding, and the correction is accepted in workspace: the
  worker now accepts the existing canonical
  `class Example(Base, metaclass=Meta)` probe shape while preserving exact
  target class name, exact `metaclass` keyword, and exact selected
  source-module `Meta` checks. The corrected release-unit audit passed with no
  findings, closing both the code P1 and continuity P1. Full regression passed
  first-pass after corrected audit with `1626 passed`. Commit-gating review
  passed first-pass with no findings. Local commit creation completed at
  `20e6f55 Add metaclass keyword subprocess support`, and Ryan-authorized push
  completed. It has release-gate status no-active-gate.
- Exact `exec_or_eval:eval/1` local-Python subprocess support is accepted
  first-pass, release-gate-cleared, locally committed, and pushed at
  `f3467e5 Add runtime eval subprocess support`. The committed release unit is
  `BUILDLOG.md`, `PLAN.md`, `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`. It is release-unit-audit-cleared
  first-pass with no findings, full-regression-cleared first-pass with
  `1605 passed`, commit-gating-cleared first-pass with no findings, and has
  release-gate status no-active-gate.
- Exact `exec_or_eval:exec/1` local-Python subprocess support is completed and
  pushed at `07bb58f Add runtime exec subprocess support`. The release unit is
  `BUILDLOG.md`, `PLAN.md`, `src/context_ir/runtime_probe_execution.py`,
  `src/context_ir/runtime_probe_worker.py`,
  `tests/test_runtime_probe_execution.py`, and
  `tests/test_runtime_probe_worker.py`. It is release-unit-audit-cleared
  first-pass with no findings and full-regression-cleared first-pass with
  `1584 passed`. Commit-gating review cleared first-pass with no findings. It
  is staged, locally committed, pushed, and has release-gate status
  no-active-gate.
- Runtime probe execution-attempt result assembly is completed and pushed at
  `86be8d7 Assemble runtime probe execution attempts`.
- The released unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- Release-gate status is no-active-gate for `86be8d7`.
- Runtime probe execution-input materialization is completed and pushed at
  `cfed3c7 Add runtime probe execution input materialization`.
- Released unit:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `cfed3c7`.
- No release gate, staging, local commit, or push is active for `86be8d7`.
- Runtime probe runner-request materialization is accepted first-pass in
  workspace-only state, release-gate-cleared, locally committed, and pushed:
  - release unit is exactly `src/context_ir/runtime_probe_execution.py`,
    `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
  - release-unit audit passed with no findings
  - full regression passed with `876 passed`
  - commit-gating passed with the exact four-file unit
  - local commit is `68a8e73 Materialize runtime probe runner requests`
  - Ryan-authorized push completed with `origin/main` advanced through
    `7eb5304 Sync runtime probe runner request release routing`
  - release-gate status is no-active-gate for `68a8e73`
- The active next action may choose the next bounded runtime-probe
  execution-loop planning or implementation lane. Do not reopen `68a8e73`
  release gates absent new findings.
- Runtime probe runner-request attempt/result assembly is accepted first-pass
  in workspace-only state, release-gate-cleared, locally committed, and pushed:
  - release unit is exactly `src/context_ir/runtime_probe_execution.py`,
    `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
  - release-unit audit passed with no findings
  - full regression passed with `882 passed`
  - commit-gating passed with the exact four-file unit
  - local commit is
    `3363929 Assemble runtime probe runner request attempts`
  - Ryan-authorized push completed with `origin/main` advanced through
    `0d37074 Sync runtime probe runner attempt release routing`
  - release-gate status is no-active-gate for `3363929`
- The active next action may choose the next bounded runtime-probe
  execution-loop planning or implementation lane. Do not reopen `3363929`
  release gates absent new findings.
- Runtime probe diagnostic runner-request preparation is accepted first-pass,
  release-gate-cleared, locally committed, and pushed:
  - release unit is exactly `src/context_ir/runtime_probe_execution.py`,
    `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
  - release-unit audit passed with no findings
  - focused validation passed with `205 passed`
  - full regression passed with `885 passed`
  - commit-gating passed with the exact four-file unit
  - local commit is `fd0f6d8 Prepare runtime probe diagnostic runner requests`
  - Ryan-authorized push completed with `origin/main` advanced through
    `74d84fb Sync runtime probe diagnostic runner request release routing`
  - release-gate status is no-active-gate for `fd0f6d8`
- Runtime probe runner-callable attempt collection is accepted first-pass,
  release-gate-cleared, locally committed, and pushed:
  - release unit is exactly `src/context_ir/runtime_probe_execution.py`,
    `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
  - release-unit audit passed with no findings
  - focused validation passed with `211 passed`
  - full regression passed with `891 passed`
  - commit-gating passed with the exact four-file unit
  - local commit is `32f6220 Collect runtime probe runner attempts`
  - Ryan-authorized push completed with `origin/main` advanced through
    `e9b5b5a Sync runtime probe runner attempt collection release routing`
  - release-gate status is no-active-gate for `32f6220`
- The next implementation slice is an internal diagnostic runner-callable
  recompile bridge in `src/context_ir/runtime_observation_recompile.py` and
  `tests/test_runtime_observation_recompile.py`.
- `PLAN.md` and `BUILDLOG.md` are dirty control-lane continuity state for this
  route. They should not be edited by the implementation lane.
- Runtime probe result-batch recompile bridge is completed and pushed at
  `591c09b Compose runtime probe result batch recompile`.
- Release-gate status is no-active-gate for `591c09b`.
- Runtime probe execution-result/replay-artifact contract is completed and
  pushed at `eb6def0`.
- Runtime probe result admission bridge is completed and pushed at `ccd417a`.
- Typed facade runtime observation recompile is completed and pushed at
  `8ac3b46`:
  - `src/context_ir/tool_facade.py`
  - `tests/test_tool_facade.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `8ac3b46`.
- No release gate is active for the pushed runtime observation recompile
  composition tranche.
- The runtime observation recompile composition tranche is completed and
  pushed at `b279b00`:
  - `src/context_ir/runtime_observation_recompile.py`
  - `tests/test_runtime_observation_recompile.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `b279b00`.
- No release gate is active for the pushed diagnostic trace-refresh tranche.
- The diagnostic trace-refresh tranche is completed and pushed at `74aadd7`:
  - `src/context_ir/semantic_diagnostics.py`
  - `src/context_ir/semantic_optimizer.py`
  - `tests/test_semantic_diagnostics.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `74aadd7`.
- No release gate is active for the pushed diagnostic runtime observation
  application tranche.
- The diagnostic runtime observation application tranche is completed and
  pushed at `95f7545`:
  - `src/context_ir/runtime_observation_admission.py`
  - `tests/test_runtime_observation_admission.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `95f7545`.
- No release gate is active for the pushed admitted runtime observation
  provenance bridge tranche.
- The admitted runtime observation provenance bridge tranche is completed and
  pushed at `35c440d`:
  - `src/context_ir/runtime_observation_admission.py`
  - `tests/test_runtime_observation_admission.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `35c440d`.
- No release gate is active for the pushed runtime observation admission
  read-model tranche.
- No release gate is active for the pushed diagnostic runtime observation
  admission bridge tranche.
- No release gate is active for the pushed runtime observation admission
  compatibility validation tranche.
- The runtime observation admission compatibility validation tranche is
  completed and pushed at `f5c8df0`:
  - `src/context_ir/runtime_observation_admission.py`
  - `tests/test_runtime_observation_admission.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `f5c8df0`.
- The diagnostic runtime observation admission bridge tranche is completed and
  pushed at `8706f2e`:
  - `src/context_ir/runtime_observation_admission.py`
  - `tests/test_runtime_observation_admission.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `8706f2e`.
- Active next route is bounded post-`95f7545` North Star planning/control to
  choose the next smallest meaningful capability slice.
- The pushed admitted-runtime-observation bridge only attaches already-admitted
  observations through existing additive provenance helpers. It still does not
  authorize probe execution, execution-result contracts, runtime observation
  collection, analyzer or tool-facade behavior, package-root API, MCP, eval,
  schema, scoring, optimizer, compiler, winner-selection, product, public
  benchmark, or public-claim changes.
- The internal runtime observation admission read-model tranche is completed
  and pushed at `b0a5ec5`:
  - `src/context_ir/runtime_observation_admission.py`
  - `tests/test_runtime_observation_admission.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `b0a5ec5`.
- Push remains Ryan-gated for any future release.
- The planned runtime probe request plan source-site indexing tranche is
  completed and pushed at `6d5fc47`:
  - `src/context_ir/runtime_probe_requests.py`
  - `tests/test_runtime_probe_requests.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `6d5fc47`.
- The `SemanticDiagnosticResult.planned_runtime_probe_request_plan` tranche is
  completed and pushed at `7c46f48`:
  - `src/context_ir/semantic_types.py`
  - `src/context_ir/semantic_diagnostics.py`
  - `tests/test_semantic_diagnostics.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `7c46f48`.
- The diagnostic runtime probe request plan bridge tranche is completed and
  pushed at `97dc0f6` with release-gate status no-active-gate.
- The planned runtime probe request plan tranche is completed and pushed at
  `744bf0e` with release-gate status no-active-gate.
- The planned runtime probe request ID indexing tranche is completed and
  pushed at `3df02c6` with release-gate status no-active-gate.
- The stable planned runtime probe request identity tranche is completed and
  pushed at `49fa461` with release-gate status no-active-gate.
- The diagnose/recompile planned runtime probe request consumption tranche is
  completed and pushed at `a819cf5`:
  - `src/context_ir/semantic_diagnostics.py`
  - `src/context_ir/semantic_types.py`
  - `tests/test_semantic_diagnostics.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `a819cf5`.
- The internal diagnostic runtime probe-request bridge tranche is completed and
  pushed at `2e448ea`:
  - `src/context_ir/runtime_probe_requests.py`
  - `tests/test_runtime_probe_requests.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `2e448ea`.
- No implementation slice, staging, local commit creation, or push is currently
  in progress.
- The internal runtime probe-request planning tranche is completed and pushed
  at `f6c66e4`:
  - `src/context_ir/runtime_probe_requests.py`
  - `tests/test_runtime_probe_requests.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `f6c66e4`.
- No implementation slice, staging, local commit creation, or push is currently
  in progress.
- The 16-file internal eval-only `REFLECTIVE_BUILTIN` tranche is completed and
  pushed at `546a4da`; release-gate status is no-active-gate.
- The current nine-file `DYNAMIC_IMPORT` original budget-pressure tranche is
  completed and pushed at `d73cde4`; release-gate status is no-active-gate.
- The zero-argument `dir()` plus `METACLASS_BEHAVIOR` budget-pressure release
  is pushed at `e2f3dcf` and has release-gate status no-active-gate. It is
  historical pushed authority, not the active route. Do not route `e2f3dcf`
  back to docs review, release-unit audit, full regression, commit-gating,
  staging, local commit creation, or push absent new findings.
- Fresh control lanes should use the canonical active release-state block above
  for current routing, and should treat older conflicting routing notes as
  historical when superseded by that block or by newer BUILDLOG entries.

## Historical Superseded Routing Notes

The following older routing notes remain as historical context only. They do not
override the canonical active release-state block above or newer BUILDLOG
supersession entries.

- Prior code/eval release state is complete and pushed for the internal
  eval-only
  `REFLECTIVE_BUILTIN` / `dir(obj)` budget-pressure expansion at
  `ad9db8d Expand dir eval budget coverage`.
- Release-gate status is no-active-gate for `ad9db8d`. Do not route
  `ad9db8d` back to docs review, release-unit audit, full regression,
  commit-gating, staging, local commit creation, or push absent new findings.
- No active route remains to commit-gating, staging, local commit creation, or
  push for `ad9db8d` absent new findings.
- The bounded post-43d0439 North Star planning/control decision is complete
  and released. It selected a budget-pressure expansion of
  `oracle_signal_dir_probe_matrix` to `[220, 100]`: 1 task x 2 budgets x 3
  providers, preserving providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`.
- Fixture, task, query, and runtime payload remain unchanged; runtime payload
  remains `listing_entry_count=74`.
- Selector and selected-unit truth remain `unsupported/opaque`; runtime
  provenance remains additive only; baseline providers remain empty at both
  budgets.
- No source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is authorized.
- Docs/evidence/continuity reconciliation for this expansion was accepted
  first-pass.
- Release-unit audit for this expansion cleared first-pass.
- Full regression for this expansion cleared first-pass with `709 passed`.
- Commit-gating, local commit creation, and Ryan-authorized push for this
  expansion are complete at `ad9db8d`.
- Completed getattr AttributeError release state:
  - implementation accepted first-pass
  - docs/evidence/continuity reconciliation accepted after 2 corrections
  - release-unit audit cleared first-pass
  - full regression cleared first-pass with `709 passed`
  - first commit-gating review rejected with P1 stale-routing findings
  - routing correction accepted first-pass
  - corrected commit-gating cleared first-pass
  - local commit creation and Ryan-authorized push completed at `5bd0616`
- Prior completed builtins-alias release state:
  - source/contract prerequisite and eval-only sibling accepted first-pass
  - docs/evidence/continuity reconciliation accepted after one correction
  - release-unit audit cleared first-pass
  - full regression cleared first-pass with `702 passed`
  - first commit-gating review rejected with P1 stale-routing findings
  - first continuity routing correction accepted first-pass
  - corrected commit-gating review rejected with one P1 stale-route finding
  - PLAN-only stale-route correction accepted first-pass
  - corrected commit-gating review cleared first-pass
  - local commit creation and Ryan-authorized push completed at `6ac1e28`
- Prior completed builtins-attribute release state:
  - implementation/assets were accepted workspace-only before release
  - docs/evidence/continuity reconciliation was accepted first-pass
  - release-unit audit cleared first-pass
  - full regression cleared first-pass
  - commit-gating cleared first-pass
  - local commit creation and Ryan-authorized push completed at `3dfc355`
  - no docs-only post-push sync is required merely to record that live git refs
    already show the pushed release commit
- Prior completed root-module alias release state:
  - implementation/assets were accepted workspace-only before release
  - corrected docs/evidence/continuity reconciliation was accepted after one
    P1 state-neutrality correction
  - release-unit audit cleared first-pass
  - full regression cleared first-pass
  - commit-gating cleared first-pass
  - local commit creation completed at `b85f038`
  - Ryan-authorized push completed at `b85f038`
- Full regression evidence:
  - `ruff check` passed
  - `ruff format --check` passed
  - `mypy --strict src/` passed
  - `pytest tests/ -v` passed with `688 passed`
- The released root-module alias implementation/assets are:
  - `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/main.py`
  - `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/plugins/__init__.py`
  - `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/plugins/weather.py`
  - `evals/run_specs/oracle_signal_dynamic_import_root_alias_probe_matrix.json`
  - `evals/tasks/oracle_signal_dynamic_import_root_alias_probe.json`
  - `tests/test_eval_signal_dynamic_import_root_alias_probe.py`
- The released matrix is
  `oracle_signal_dynamic_import_root_alias_probe_matrix`: 1 task x 1 budget x
  3 providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`
- The fixture boundary is `import importlib as loader`,
  `name = "plugins.weather"`, and exactly `loader.import_module(name)`
- Runtime payload is `imported_module=plugins.weather`; primary selector and
  selected-unit truth remain `unsupported/opaque`; runtime provenance remains
  additive only; no dependency edge or selected symbol is created from
  `plugins.weather`
- Non-goals remain no root-module `importlib.import_module(name)` expansion,
  no imported-name `import_module(name)` expansion, no imported-alias
  `load_module(name)` expansion, no literal dynamic import expansion, no
  `__import__(name)`, no `builtins.__import__`, no globals/locals/fromlist
  forms, no namespace mutation, no generated-code dependency modeling, no
  generalized dynamic import support, and no
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening
- No active release gate remains for `b85f038 Add root-alias dynamic import
  eval probe` absent new findings.
- Do not reopen `b85f038`, `4030845`, `ee71a82`, `397c7dd`, `14b362e`,
  `bcd6d68`, or `96fc03a` absent new findings
- `5d2d7e4 Sync imported-name dynamic import release routing` remains the prior
  pushed continuity authority
- `ca191c8 Sync builtin dynamic import release routing` remains the prior
  builtin dynamic-import continuity authority
- `397c7dd Add builtin dynamic import eval probe` is the prior builtin
  dynamic-import eval/test/docs release authority and must not be reopened
  absent new findings
- `14b362e Add dynamic import root runtime eval pilot` is the prior root-module
  dynamic-import eval/test/docs release authority and must not be reopened
  absent new findings
- `bcd6d68 Add exec source runtime eval pilot` is the prior exec(source) release
  and must not be reopened absent new findings
- `96fc03a Add eval runtime eval pilot` remains the prior eval(source)
  release authority and must not be reopened absent new findings
- The internal eval-only `EXEC_OR_EVAL` / `exec(source)` release unit is
  completed and pushed at `bcd6d68`
- The exec matrix is `oracle_signal_exec_probe_matrix`, 1 task x 1 budget x 3
  providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`
- The fixture/call boundary is `source = "pass"` and exactly `exec(source)`;
  executed source parses as exactly one `ast.Pass`; no `exec("pass")`,
  `exec(source + suffix)`, `exec(source=source)`, `exec(source, globals)`,
  `exec(source, globals, locals)`, `builtins.exec`, or `eval` is included
- Runtime proof is `execution_outcome=completed`,
  `source_shape=literal_statement`, `source_sha256 == sha256(b"pass")`, and
  non-empty `durable_payload_reference`; optional `statement_kind=pass` is
  additive summary only
- Provenance attaches only to the preserved `EXEC_OR_EVAL` unsupported finding
  for `exec(source)`
- Primary selector and selected-unit truth remain `unsupported/opaque`;
  additive runtime provenance remains separate from primary truth
- No dependency edge or symbol is created from executed source, no namespace
  mutation modeling is added, and no generated-code dependency modeling is
  added
- Scope remains exactly simple-name builtin `exec(source)` with one positional
  argument; no broader `exec` forms are included, no generalized exec support
  is included, and public comparative claims remain bounded to the existing
  quad matrix
- No
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is authorized
- Release-unit audit initially found one P1 digest-boundary issue; the
  correction pinned `source_sha256` to `sha256(b"pass")`; audit rerun cleared;
  full regression passed; commit-gating cleared; local commit creation
  completed; Ryan-authorized push completed
- The prior post-imported-alias next-move route is superseded by the completed
  root-module alias release at `b85f038` and the post-root-alias
  planning/control route above
- The runtime-outcome methodology/reporting hardening release unit is pushed to `origin/main` at `d8ebdc3`
- Live git refs and worktree state are intentionally verified from git rather than kept as mutable committed continuity fields
- The `getattr` family matrix expansion release unit is pushed at `1b555ef`
- The same-tranche docs/evidence reconciliation released in `1b555ef` includes:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The `getattr` family matrix expansion released in `1b555ef` includes:
  - `evals/run_specs/oracle_signal_getattr_probe_matrix.json`
  - `evals/run_specs/oracle_signal_getattr_default_probe_matrix.json`
  - `evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json`
  - `tests/test_eval_signal_getattr_probe.py`
  - `tests/test_eval_signal_getattr_default_probe.py`
  - `tests/test_eval_signal_getattr_default_value_probe.py`
  - `tests/test_eval_runs.py`
  - `tests/test_eval_report.py`
- The release-unit audit over the accumulated `getattr` family matrix expansion tranche is accepted first-pass
- The accepted `getattr` family matrix expansion:
  - add budget `100` to `evals/run_specs/oracle_signal_getattr_probe_matrix.json`
  - add budget `100` to `evals/run_specs/oracle_signal_getattr_default_probe_matrix.json`
  - add budget `100` to `evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json`
  - update focused tests only as needed
- The full regression gate over the accumulated `getattr` family matrix expansion tranche is accepted first-pass
- Commit-gating over the exact intended release file set is accepted first-pass
- Local commit creation over the exact intended release file set is accepted first-pass at `1b555ef`
- Remote push of `1b555ef` is accepted first-pass after explicit Ryan authorization
- The post-push continuity anchor for the `1b555ef` release state is `159e363`
- The post-`1b555ef` / `d9be4d5` bounded planning boundary is complete
- The post-`d9be4d5` `vars(obj)` planning decision is accepted first-pass
- The accepted `vars(obj)` eval pilot includes:
  - `src/context_ir/eval_oracles.py`
  - `src/context_ir/eval_providers.py`
  - `evals/fixtures/oracle_signal_vars_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_vars_probe/main.py`
  - `evals/tasks/oracle_signal_vars_probe.json`
  - `evals/run_specs/oracle_signal_vars_probe_matrix.json`
  - `tests/test_eval_signal_vars_probe.py`
- The accepted same-tranche docs/evidence reconciliation for the `vars(obj)` pilot includes:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The accepted `vars(obj)` pilot is one internal eval-only task at budget `220` across `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- The accepted `vars(obj)` pilot keeps selector and selected-unit primary truth `unsupported/opaque` with additive runtime-backed provenance only
- The accepted `vars(obj)` tranche does not widen package-root APIs, MCP behavior, analyzer/runtime-acquisition/tool-facade behavior, schema, scoring, winner selection, public claims, public comparison boundaries, or zero-argument `vars()` / sibling reflective families
- The release-unit audit over the accumulated `vars(obj)` tranche is accepted first-pass
- The full regression gate over the accumulated `vars(obj)` tranche is accepted first-pass
- Commit-gating over the exact intended `vars(obj)` release file set is accepted first-pass
- The accumulated `vars(obj)` tranche has passed planning, implementation review, docs reconciliation, release-unit audit, full regression, and commit-gating
- Local commit and remote push state for the tranche are verified from git, not maintained as mutable continuity prose
- If git shows the release commit is local-only, push remains explicitly Ryan-gated
- If git shows the release commit is already pushed, route to the next bounded planning/evidence move
- Do not create a docs-only post-push commit merely to record the push
- The post-`ead239d` `vars(obj)` budget-expansion planning decision is accepted first-pass
- The accepted workspace-only `vars(obj)` budget expansion currently includes:
  - `evals/run_specs/oracle_signal_vars_probe_matrix.json`
  - `tests/test_eval_signal_vars_probe.py`
- The accepted workspace-only budget expansion changes only the existing `oracle_signal_vars_probe_matrix` from budget `[220]` to `[220, 100]`
- The budget `100` row preserves the expected `unsupported/opaque` selected unit with additive runtime provenance
- The accepted same-tranche docs/evidence reconciliation for the `vars(obj)` budget expansion currently includes:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The accepted docs/evidence reconciliation describes the `vars(obj)` pilot as 1 task x 2 budgets x 3 providers at budgets `100` and `220`
- The accepted budget expansion does not widen fixtures, tasks, providers, source, package-root APIs, MCP behavior, runtime-acquisition/analyzer/tool-facade behavior, schema, scoring, winner selection, public claims, zero-argument `vars()`, or sibling runtime families
- The corrected release-unit audit over this budget expansion tranche is accepted after 1 correction
- The full regression gate over this budget expansion tranche is accepted first-pass
- Commit-gating over the exact 8-file release-unit candidate is accepted first-pass
- Local commit creation and remote push for that budget-expansion tranche completed at `2c6b54a`
- The accepted zero-argument `vars()` eval pilot implementation includes:
  - `src/context_ir/eval_oracles.py`
  - `evals/fixtures/oracle_signal_vars_zero_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_vars_zero_probe/main.py`
  - `evals/tasks/oracle_signal_vars_zero_probe.json`
  - `evals/run_specs/oracle_signal_vars_zero_probe_matrix.json`
  - `tests/test_eval_signal_vars_zero_probe.py`
- The accepted zero-argument `vars()` pilot is one internal eval-only task at budget `220` across `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- The accepted zero-argument `vars()` pilot keeps selector and selected-unit primary truth `unsupported/opaque` with additive runtime-backed provenance only
- The accepted zero-argument `vars()` pilot does not widen runtime acquisition, analyzer, tool facade behavior, MCP, package-root APIs, schema, scoring, winner selection, public claims, or sibling runtime families
- The accepted same-tranche docs/evidence reconciliation for the zero-argument `vars()` pilot includes:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The accepted docs/evidence reconciliation describes the zero-argument `vars()` pilot as `oracle_signal_vars_zero_probe_matrix`: 1 task x 1 budget x 3 providers at budget `220`
- The accepted docs/evidence reconciliation keeps release-facing wording neutral: no live workspace, local commit, or push-state claim belongs in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, or `ARCHITECTURE.md`
- The release-unit audit over the accumulated zero-argument `vars()` release candidate is accepted first-pass
- The full regression gate over the accumulated zero-argument `vars()` release candidate is accepted first-pass with `590 passed`
- Commit-gating over the exact accumulated zero-argument `vars()` release-candidate file set is accepted first-pass
- The accepted staging set is:
  - `src/context_ir/eval_oracles.py`
  - `evals/fixtures/oracle_signal_vars_zero_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_vars_zero_probe/main.py`
  - `evals/tasks/oracle_signal_vars_zero_probe.json`
  - `evals/run_specs/oracle_signal_vars_zero_probe_matrix.json`
  - `tests/test_eval_signal_vars_zero_probe.py`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- The accepted commit message is `Add zero-argument vars eval pilot`
- The accumulated zero-argument `vars()` release candidate has implementation, docs/evidence, release-unit audit, full-regression, and commit-gating acceptance, but local commit and remote push state must be verified from git rather than inferred from continuity prose
- Local commit and remote push state for this tranche must be verified from git; do not create a docs-only post-push continuity commit merely to record the push
- Local commit creation and remote push for the initial zero-argument `vars()` pilot completed at `71db72e`
- The accepted workspace-only zero-argument `vars()` budget expansion currently includes:
  - `evals/run_specs/oracle_signal_vars_zero_probe_matrix.json`
  - `tests/test_eval_signal_vars_zero_probe.py`
- The accepted workspace-only budget expansion changes only the existing `oracle_signal_vars_zero_probe_matrix` from budget `[220]` to budgets `[220, 100]`
- The budget `100` row preserves the expected `unsupported/opaque` selected unit with additive `lookup_outcome=returned_namespace` runtime provenance
- Baseline providers remain empty at both budgets
- The accepted budget expansion does not widen fixtures, tasks, providers, source, package-root APIs, MCP behavior, runtime-acquisition/analyzer/tool-facade behavior, schema, scoring, winner selection, public claims, or sibling runtime families
- The accepted same-tranche docs/evidence reconciliation for the zero-argument `vars()` budget expansion includes:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The accepted docs/evidence reconciliation describes the zero-argument `vars()` pilot as 1 task x 2 budgets x 3 providers at budgets `100` and `220`
- The accepted docs/evidence reconciliation keeps release-facing wording neutral: no live workspace, local commit, or push-state claim belongs in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, or `ARCHITECTURE.md`
- The release-unit audit over the accumulated zero-argument `vars()` budget-expansion release candidate is accepted first-pass
- The full regression gate over the accumulated zero-argument `vars()` budget-expansion release candidate is accepted first-pass with `590 passed`
- Commit-gating over the exact accumulated zero-argument `vars()` budget-expansion release-candidate file set is accepted first-pass
- The accepted staging set is:
  - `evals/run_specs/oracle_signal_vars_zero_probe_matrix.json`
  - `tests/test_eval_signal_vars_zero_probe.py`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- The accepted commit message is `Expand zero-argument vars budget matrix`
- The accumulated zero-argument `vars()` budget-expansion release candidate has implementation, docs/evidence, release-unit audit, full-regression, and commit-gating acceptance, but local commit and remote push state must be verified from git rather than inferred from continuity prose
- Local commit creation and remote push for the zero-argument `vars()` budget expansion completed at `9eec985`
- The accepted `globals()` eval pilot includes:
  - `src/context_ir/eval_oracles.py`
  - `src/context_ir/eval_providers.py`
  - `evals/fixtures/oracle_signal_globals_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_globals_probe/main.py`
  - `evals/tasks/oracle_signal_globals_probe.json`
  - `evals/run_specs/oracle_signal_globals_probe_matrix.json`
  - `tests/test_eval_signal_globals_probe.py`
- The accepted `globals()` pilot is one internal eval-only task at budget `220` across `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- The accepted `globals()` pilot keeps selector and selected-unit primary truth `unsupported/opaque` with additive `lookup_outcome=returned_namespace` runtime provenance only
- The accepted `globals()` pilot does not widen runtime acquisition, analyzer, tool facade implementation, MCP, package-root APIs, schema, scoring, winner selection, public claims, or sibling runtime families
- Same-tranche docs/evidence reconciliation for the accepted `globals()` pilot is complete in:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The release-unit audit over the accumulated `globals()` release candidate is accepted first-pass
- The full regression gate over the accumulated `globals()` release candidate is accepted first-pass with `595 passed`
- The commit-gating review over the accumulated `globals()` release candidate is accepted first-pass
- The accepted commit message is `Add globals runtime eval pilot`
- Local commit creation and remote push for the initial `globals()` pilot completed at `631a303`
- The pushed `globals()` budget expansion at `5f74ede` includes:
  - `evals/run_specs/oracle_signal_globals_probe_matrix.json`
  - `tests/test_eval_signal_globals_probe.py`
- The pushed `globals()` budget expansion changes only the existing `oracle_signal_globals_probe_matrix` from budget `[220]` to budgets `[220, 100]`
- The pushed `globals()` budget expansion keeps the existing task, fixture, query, provider set, selector, and runtime provenance shape unchanged
- The pushed `globals()` budget expansion preserves `unsupported/opaque` selected-unit primary truth, additive `lookup_outcome=returned_namespace` runtime provenance, empty baseline selected units, and summary/report accounting over the expanded two-budget matrix
- The pushed `globals()` budget expansion does not widen runtime acquisition, analyzer, tool facade implementation, MCP, package-root APIs, schema, scoring, winner selection, public claims, or sibling runtime families
- Same-tranche docs/evidence reconciliation for the accepted `globals()` budget expansion is complete in:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The release-unit audit over the accepted `globals()` budget expansion is accepted first-pass
- The full regression gate over the accepted `globals()` budget expansion is accepted first-pass with `596 passed`
- The commit-gating review over the accepted `globals()` budget expansion is accepted first-pass
- The accepted commit message is `Expand globals eval budget matrix`
- Local commit creation and remote push for the `globals()` budget expansion completed at `5f74ede`
- The latest pushed `locals()` eval/test/docs release authority is `2dd8404
  Expand locals eval budget matrix`; `38e9d5f` remains the initial one-budget
  `locals()` pilot anchor
- The pushed `2dd8404` `locals()` budget expansion includes:
  - `evals/run_specs/oracle_signal_locals_probe_matrix.json`
  - `tests/test_eval_signal_locals_probe.py`
- The pushed budget expansion changes only the existing
  `oracle_signal_locals_probe_matrix` from budget `[220]` to budgets
  `[220, 100]`
- The pushed budget expansion describes `oracle_signal_locals_probe_matrix` as
  1 task x 2 budgets x 3 providers at budgets `100` and `220`
- The budget `100` row preserves the expected `unsupported/opaque` selected
  unit with additive `lookup_outcome=returned_namespace` runtime provenance;
  baseline providers remain empty at the selected-unit layer
- The pushed budget expansion does not widen fixtures, tasks, providers,
  source, runtime acquisition, analyzer, tool facade implementation, MCP,
  package-root APIs, schema, scoring, winner selection, public claims,
  generalized locals() support, or sibling runtime families
- Same-tranche docs/evidence reconciliation for the pushed `locals()` budget
  expansion is complete in:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- The pushed docs/evidence reconciliation keeps selector, runtime-mutation
  surface, and selected-unit primary truth `unsupported/opaque`; keeps
  runtime-backed provenance additive only; preserves
  `lookup_outcome=returned_namespace`; and leaves the public-safe quad-matrix
  comparative boundary unchanged
- The `2dd8404` locals budget-expansion release passed implementation review,
  same-tranche docs reconciliation, release-unit audit, full regression,
  corrected commit-gating, local commit creation, and Ryan-authorized push
- Do not route future control work to release gates for `2dd8404` unless a
  later findings-based review identifies a concrete defect
- Pushed implementation release `d8ebdc3` contains the runtime-outcome methodology/reporting hardening implementation release unit:
  - `src/context_ir/eval_results.py`
  - `src/context_ir/eval_summary.py`
  - `tests/test_eval_report.py`
  - `tests/test_eval_results.py`
  - `tests/test_eval_runs.py`
  - `tests/test_eval_signal_getattr_default_probe.py`
  - `tests/test_eval_signal_getattr_default_value_probe.py`
  - `tests/test_eval_summary.py`
- Pushed implementation release `b014595` contains the accepted value-return branch tranche after pushed `7d43302`:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `evals/fixtures/oracle_signal_getattr_default_value_probe/`
  - `evals/tasks/oracle_signal_getattr_default_value_probe.json`
  - `evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json`
  - `tests/test_eval_providers.py`
  - `tests/test_eval_runs.py`
  - `tests/test_eval_signal_getattr_default_value_probe.py`
  - the accepted post-`7d43302` planning decision was implemented as one bounded internal eval-only sibling pilot for the value-return branch of `getattr(obj, name, default)`
  - add a new sibling `oracle_signal_getattr_default_value_probe` fixture/task/run-spec/test set
  - keep the existing `oracle_signal_getattr_default_probe` default-return fixture unchanged
  - keep the pilot at `1 task x 1 budget x 3 providers` with budget `220`
  - keep providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
  - assert selector and selected-unit primary truth remains `unsupported/opaque`
  - keep runtime-backed provenance additive only
  - do not widen package-root APIs, MCP exposure, analyzer/tool-facade behavior, runtime acquisition, schema, scoring, winner selection, public benchmark claims, or public product boundaries
  - the value-return pilot covers `lookup_outcome=returned_value`
  - selector and selected-unit primary truth remains `unsupported/opaque`
  - runtime-backed provenance remains additive only
  - no package-root API, MCP, analyzer/tool-facade behavior, runtime-acquisition, schema, scoring, winner-selection, public benchmark claim, or public product-boundary surface changed
  - execution-lane validation passed:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_signal_getattr_default_value_probe.py -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v`
    - pytest result: `575 passed`
  - control-lane validation passed:
    - `git diff --check`
    - JSON validation for the new runtime observation, task, and run-spec files
    - forbidden-surface diff check over source, public docs, package-root, MCP, runtime-acquisition, analyzer/tool-facade, schema, scoring, and winner-selection surfaces
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_signal_getattr_default_value_probe.py -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_runs.py tests/test_eval_providers.py -k getattr_default_value_probe -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_providers.py -k "defaulted_getattr_value_probe or getattr_value_probe" -q`
  - the accepted value-return implementation slice is audit-cleared, full-regression-cleared, commit-gating-cleared, committed locally, and pushed
  - same-tranche docs/evidence reconciliation is included:
  - after post-push release-doc correction, names `b014595` as pushed code/test evidence authority and keeps `7d43302` as the prior default-return branch anchor
  - adds release-neutral wording for the narrow internal eval-only `getattr(obj, name, default)` value-return branch pilot beside the default-return branch
  - keeps public-safe quad-matrix comparative boundaries unchanged
  - keeps selector and selected-unit primary truth `unsupported/opaque`
  - keeps runtime-backed provenance additive only
  - does not widen public claims, public APIs, MCP behavior, runtime acquisition, analyzer/tool-facade behavior, schema, scoring, winner selection, or product positioning
  - docs/evidence validation passed:
    - `git diff --check -- EVAL.md PUBLIC_CLAIMS.md README.md ARCHITECTURE.md`
    - no `workspace-only`, `workspace tranche`, or `accepted workspace` wording remains in release docs
    - targeted boundary grep checks confirmed default-return, value-return, `unsupported/opaque`, additive provenance, public-safe quad-matrix, public API, MCP, and winner-selection boundary wording
  - release-unit audit passed with no findings
  - full regression passed:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v`
    - pytest result: `575 passed`
  - commit-gating passed with no findings
  - exact release-unit files approved for staging:
    - `ARCHITECTURE.md`
    - `EVAL.md`
    - `PUBLIC_CLAIMS.md`
    - `README.md`
    - `tests/test_eval_providers.py`
    - `tests/test_eval_runs.py`
    - `tests/test_eval_signal_getattr_default_value_probe.py`
    - `evals/fixtures/oracle_signal_getattr_default_value_probe/eval_runtime_observations.json`
    - `evals/fixtures/oracle_signal_getattr_default_value_probe/main.py`
    - `evals/tasks/oracle_signal_getattr_default_value_probe.json`
    - `evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json`
  - continuity files `PLAN.md` and `BUILDLOG.md` are excluded from the release-unit commit candidate
  - local commit creation passed at `b014595`
  - remote push completed at `b014595`
  - the accumulated accepted tranche is audit-cleared, full-regression-cleared, commit-gating-cleared, committed locally, and pushed
- Pushed implementation release `7d43302` contains the accepted defaulted `getattr(obj, name, default)` tranche after pushed `c592dca`:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `src/context_ir/eval_oracles.py`
  - `evals/fixtures/oracle_signal_getattr_default_probe/`
  - `evals/tasks/oracle_signal_getattr_default_probe.json`
  - `evals/run_specs/oracle_signal_getattr_default_probe_matrix.json`
  - `tests/test_eval_oracles.py`
  - `tests/test_eval_providers.py`
  - `tests/test_eval_runs.py`
  - `tests/test_eval_signal_getattr_default_probe.py`
  - the accepted planning decision behind this tranche is to extend the eval layer, not the lower runtime layer, with one narrow defaulted `getattr(obj, name, default)` pilot
  - the `EVAL.md` correction updates the evidence ledger so `c592dca` is the latest pushed code/test authority and the pushed `getattr(obj, name)` pilot is no longer described as workspace-only
  - eval eligibility is widened only from simple-name `getattr` with `argument_count == 2` to include the simple-name defaulted form with `argument_count == 3`
  - the new pilot remains exactly `1 task x 1 budget x 3 providers` with budget `220`
  - providers remain `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
  - this eval pilot covers only the default-return branch via `lookup_outcome=returned_default_value`
  - the defaulted `getattr(obj, name, default)` selector and selected unit remain primary `unsupported/opaque`, with runtime-backed provenance attached additively only
  - the docs/evidence reconciliation keeps the public-safe quad-matrix comparative surface unchanged and describes the defaulted `getattr(obj, name, default)` work only as narrow internal eval-only evidence
  - targeted validation passed:
    - `.venv/bin/python -m ruff check src/context_ir/eval_oracles.py src/context_ir/eval_providers.py tests/test_eval_oracles.py tests/test_eval_providers.py tests/test_eval_runs.py tests/test_eval_signal_getattr_default_probe.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/eval_oracles.py src/context_ir/eval_providers.py tests/test_eval_oracles.py tests/test_eval_providers.py tests/test_eval_runs.py tests/test_eval_signal_getattr_default_probe.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/eval_oracles.py src/context_ir/eval_providers.py`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_oracles.py -k "getattr or dynamic_import or hasattr" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_providers.py -k "getattr or dynamic_import or hasattr" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_runs.py -k "getattr_default_probe or getattr_probe or dynamic_import_probe or hasattr_probe" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_signal_getattr_default_probe.py -q`
  - docs/evidence validation passed:
    - `git diff --check -- EVAL.md PUBLIC_CLAIMS.md README.md ARCHITECTURE.md`
  - release-unit audit passed with no findings
  - full regression passed:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v`
    - pytest result: `567 passed`
  - release-doc wording correction passed:
    - `git diff --check -- EVAL.md PUBLIC_CLAIMS.md README.md ARCHITECTURE.md`
    - no `workspace-only`, `workspace tranche`, or `accepted workspace` wording remains in the release docs
  - commit-gating passed with no findings
  - local commit creation passed at `7d43302`
  - remote push completed at `7d43302`
- Prior pushed implementation release `c592dca` remains the `getattr(obj, name)` release anchor:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `evals/fixtures/oracle_signal_getattr_probe/`
  - `evals/tasks/oracle_signal_getattr_probe.json`
  - `evals/run_specs/oracle_signal_getattr_probe_matrix.json`
  - `src/context_ir/eval_oracles.py`
  - `src/context_ir/eval_providers.py`
  - `tests/test_eval_oracles.py`
  - `tests/test_eval_providers.py`
  - `tests/test_eval_runs.py`
  - `tests/test_eval_signal_getattr_probe.py`
  - it adds a narrow internal `REFLECTIVE_BUILTIN` / `getattr(obj, name)` eval pilot at `1 task x 1 budget x 3 providers`
  - the budget is `220`
  - providers are `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
  - eligibility is constrained to simple-name `getattr` with `argument_count == 2`
  - the `getattr(obj, name)` unsupported selector and selected unit remain primary `unsupported/opaque`, with runtime-backed provenance attached additively only
  - the same-tranche docs/evidence reconciliation updates `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md` to cover the accepted internal `getattr(obj, name)` pilot without widening public claims, package-root exports, MCP behavior, schema, scoring, or winner selection
  - release-unit audit found no issues
  - full regression passed:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v`
  - pytest result: `558 passed`
  - commit-gating review passed
  - local commit creation passed at `c592dca`
  - remote push completed at `c592dca`
- The only current local workspace modifications should be:
  - `PLAN.md`
  - `BUILDLOG.md`
- Prior pushed implementation release `762dd51` remains the `hasattr(obj, name)` provider/budget matrix authority:
  - `evals/run_specs/oracle_signal_hasattr_probe_matrix.json`
  - `tests/test_eval_signal_hasattr_probe.py`
  - `tests/test_eval_runs.py`
  - the `hasattr(obj, name)` internal pilot now runs `1 task x 2 budgets x 3 providers`
  - the budgets are `220` and `100`
  - `context_ir` still carries the intended `unsupported/opaque` selected unit with additive runtime provenance at both budgets
  - both baselines remain structurally empty for this pilot, including the tighter `100` budget row
  - summary/report-facing assertions still prove additive-only runtime provenance and no primary `runtime_backed` selected-unit tier
  - the slice passed targeted validation, full regression, commit-gating review, local commit creation, and remote push
  - it does not widen source boundaries, public claims, package-root exports, MCP behavior, schema, scoring, winner selection, tasks, or fixtures
- Prior pushed implementation release `90dcc15` has passed corrected release-unit audit, full regression, commit-gating review, local commit creation, and remote push:
  - `src/context_ir/eval_oracles.py`
  - `src/context_ir/eval_providers.py`
  - `evals/fixtures/oracle_signal_hasattr_probe/`
  - `evals/tasks/oracle_signal_hasattr_probe.json`
  - `evals/run_specs/oracle_signal_hasattr_probe_matrix.json`
  - `tests/test_eval_signal_hasattr_probe.py`
  - `tests/test_eval_oracles.py`
  - `tests/test_eval_providers.py`
  - `tests/test_eval_runs.py`
  - this release adds fixture-local `hasattr_runtime_observations` loading and Context IR provider pass-through via the existing tool facade seam
  - the pilot is one task x one budget (`220`) x three providers (`context_ir`, `lexical_top_k_files`, `import_neighborhood_files`)
  - the `hasattr(obj, name)` unsupported selector remains primary `unsupported/opaque`, with runtime-backed provenance only as additive attached evidence
  - baselines expose no structured selected units or attached runtime provenance for this pilot
  - package-root exports, public claims, MCP, analyzer, tool-facade, source runtime-acquisition semantics, scoring, winner selection, existing dynamic-import matrix boundaries, and schema version remain unchanged
  - corrected release-unit audit, full regression, commit-gating review, and local commit creation have passed
  - remote push has passed
- The first read-only release-unit audit for the `hasattr` pilot found one P2 issue:
  - `evals/fixtures/oracle_signal_hasattr_probe/eval_runtime_observations.json` uses `normalized_payload` fields `lookup_outcome=attribute_present` and `result=true`
  - accepted `hasattr(obj, name)` runtime evidence uses the minimal boolean shape `attribute_present=true|false`
  - narrow correction is accepted: the fixture now uses `attribute_present=true`, and `tests/test_eval_signal_hasattr_probe.py` asserts the exact loaded fixture payload
  - corrected audit accepted the release unit with no findings
  - full regression passed:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v`
    - pytest result: `549 passed`
  - commit-gating review passed and pushed commit `90dcc15` contains only the implementation release unit
- Pushed implementation release `9a52b46` has passed release-unit audit, full regression, commit-gating review, local commit creation, and remote push:
  - `evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json`
  - `tests/test_eval_signal_dynamic_import_probe.py`
  - `tests/test_eval_runs.py`
  - the dynamic-import pilot now runs 1 task x 2 budgets (`220`, `180`) x 3 providers (`context_ir`, `lexical_top_k_files`, `import_neighborhood_files`)
  - provider-scoped accounting assertions preserve the distinction between scalar winner selection and additive runtime-provenance accounting
  - the implementation remains internal-only and does not alter source code, public claims, schema, scoring, winner selection, package-root exports, MCP, or runtime-acquisition breadth
  - release-unit audit found no issues and recommended acceptance
  - full regression passed:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
  - commit-gating review found the implementation release unit is limited to the three authorized files and separable from continuity docs
  - pushed commit `9a52b46` contains only the three implementation files
- Docs-only continuity sync records:
  - the execution-lane overreach correction
  - the control-reviewed `hasattr` pilot planning decision
  - the `hasattr` implementation acceptance, correction, audit, regression, commit, and push
  - the pushed `90dcc15` release state
  - the pushed docs-only runtime-backed evidence/claim reconciliation commit `3291268`
  - the pushed continuity/process correction commit `8133e0a`
  - the pushed `762dd51` `hasattr` matrix expansion release state
- Pushed workflow authority exists in:
  - `AGENTS.md`
  - `AGENTS.md` codifies that slice acceptance is workspace-only by default, commits happen at coherent release-unit boundaries, and a release-unit audit is the default pre-commit quality gate
- Repo-backed and local release state is now explicit and complete:
  - historical pushed runtime-outcome accounting release authority is `d8ebdc3`
  - prior pushed defaulted `getattr(obj, name, default)` default-return branch release authority is `7d43302`
  - latest pushed docs-only continuity/process correction commit in the current release chain is `8133e0a`
  - latest pushed docs-only evidence/claim reconciliation commit remains `3291268`
  - prior pushed `getattr(obj, name)` release authority remains `c592dca`
  - prior pushed `hasattr` pilot release authority remains `90dcc15`
  - the accepted internal `DYNAMIC_IMPORT` provider/budget matrix expansion release unit remains `9a52b46`
  - the accepted provider-scoped selected-unit capability-tier accounting release unit is `215b6bb`
  - the accepted capability-tier eval / evidence code/test/pilot release unit is `a605b22`
  - docs-only continuity commits after `a605b22`, including pushed continuity through `6435434`, pushed evidence-doc reconciliation `3291268`, and pushed process correction `8133e0a`, are not implementation release changes
  - the previously accepted runtime-backed tranche at `cb1dc65` remains historical released state and must not be routed as workspace-only work
- The prior capability-tier eval / evidence baseline remains repo-backed at `a605b22`:
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
- Push for `a605b22` is complete; docs-only continuity pushes through `6435434`, evidence-doc reconciliation `3291268`, and process correction `8133e0a` are complete; implementation pushes for `9a52b46`, `90dcc15`, and `762dd51` are complete
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

Immediate next route: select the next bounded north-star lane from the pushed
`0650bb8 Add metaclass default subprocess eval provider` authority.
Current pushed release authority and latest pushed source/contract authority are
`0650bb8 Add metaclass default subprocess eval provider`.

The pushed metaclass provider release is closed/no-active-gate at
`0650bb8 Add metaclass default subprocess eval provider`; do not route it back
to release-unit audit, full regression, commit-gating, staging, local commit,
or push absent new findings.

The pushed exec/eval provider release is closed/no-active-gate at
`125c44e Add exec/eval default subprocess eval provider`; do not route it back
to release-unit audit, full regression, commit-gating, staging, local commit,
or push absent new findings.

The pushed exec/eval replay-input correction release is closed/no-active-gate
at `53c82df Preserve exec/eval observed replay inputs`; do not route it back
to release-unit audit, full regression, commit-gating, staging, local commit,
or push absent new findings.

The pushed vars-zero provider release is closed/no-active-gate at
`eef7173 Add vars-zero default subprocess eval provider`; do not route it back
to release-unit audit, full regression, commit-gating, staging, local commit,
or push absent new findings.

The metaclass provider-support release is pushed at
`0650bb8 Add metaclass default subprocess eval provider`. The exact release
unit is `BUILDLOG.md`,
`PLAN.md`, `src/context_ir/eval_providers.py`,
`tests/test_eval_signal_metaclass_behavior_probe.py`,
`tests/test_eval_signal_locals_probe.py`,
`tests/test_eval_signal_globals_probe.py`, and
`tests/test_eval_signal_vars_zero_probe.py`. Focused validation passed with
ruff, format check, strict mypy, targeted pytest with `77 passed`, and clean
`git diff --check`. Dedicated read-only release-unit audit passed first-pass
with no findings. Full regression passed first-pass with ruff, format check,
strict mypy, full pytest reporting `1657 passed`, and clean final
`git diff --check`. It is release-unit-audit-cleared,
full-regression-cleared, commit-gating-cleared, locally committed, and pushed
at `0650bb8 Add metaclass default subprocess eval provider`.

Historical vars-zero provider release unit was exactly `BUILDLOG.md`, `PLAN.md`,
`src/context_ir/eval_providers.py`,
`tests/test_eval_signal_globals_probe.py`,
`tests/test_eval_signal_locals_probe.py`, and
`tests/test_eval_signal_vars_zero_probe.py`. The vars-zero implementation was
accepted first-pass and focused validation passed, including strict mypy and
targeted pytest with `57 passed`. The release-unit audit
passed first-pass with no findings. Full regression passed first-pass with
`1646 passed`. Commit-gating passed first-pass with no findings. The exact
release unit was locally committed as
`eef7173 Add vars-zero default subprocess eval provider` and pushed with
explicit Ryan authorization. Do not reopen this pushed release absent new
findings.

The prior parent-side exact default local-Python subprocess runner factory is
pushed at `92824aa Add default local-Python subprocess runner`, and the
internal default recompile helper is pushed at
`0334911 Add default local-Python recompile helper`. Do not route those pushed
releases back to release-unit audit, full regression, commit-gating, staging,
local commit, or push handling absent new findings.

The accepted workspace slice adds one facade wrapper in
`src/context_ir/tool_facade.py` and focused tests in
`tests/test_tool_facade.py`. It exposes the new default-local-Python
request/response/function names through `context_ir.tool_facade.__all__` only,
proves the real subprocess path for exact non-dynamic `runtime_mutation:locals/0`,
and keeps package-root exports, MCP, schema, docs, fixtures, tasks, run specs,
public claims, scoring, compiler, generalized runtime support, and new
runtime-probe forms unchanged. The proposed release unit is `BUILDLOG.md`,
`PLAN.md`, `src/context_ir/tool_facade.py`, and `tests/test_tool_facade.py`.
The release-unit audit passed first-pass with no findings. Full regression
passed first-pass with `1633 passed`. Commit-gating passed first-pass with no
findings. The exact release unit was locally committed as
`7ee092b Add default local-Python recompile facade` and pushed with explicit
Ryan authorization. It has release-gate status no-active-gate.

The exposure-boundary planning result is accepted with no findings:
no exposure change is justified. Do not open package-root, MCP, CLI/product, or
public-claims implementation from that spike. The next planning lane should
stay non-public and decide the smallest internal north-star move, likely among
default-subprocess internal eval proof, non-public caller ergonomics, runtime
evidence hardening, or an explicit hold.

The non-public planning result is also accepted with no findings. The selected
implementation slice is test-only in `tests/test_eval_signal_locals_probe.py`:
prove the existing `oracle_signal_locals_probe` fixture can be replayed through
the default local-Python subprocess facade and recompiled with additive runtime
provenance. No source, eval asset, provider, run-spec, package-root, MCP,
CLI/product, docs, public-claims, schema, scoring, compiler, generalized
runtime, or new-form change is authorized.

That test-only implementation slice is accepted in workspace first-pass with no
findings. Focused validation passed: ruff check, ruff format check, targeted
pytest over `tests/test_eval_signal_locals_probe.py`, `tests/test_tool_facade.py`,
and `tests/test_runtime_observation_recompile.py` with `65 passed`, and
`git diff --check`. The exact release unit is `BUILDLOG.md`, `PLAN.md`, and
`tests/test_eval_signal_locals_probe.py`. The combined read-only release gate
passed first-pass: release-unit audit PASS, full regression PASS with
`1634 passed`, and commit-gating PASS with no findings. The exact release unit
was locally committed as
`667fcdc Prove locals fixture through default subprocess facade` and pushed
with explicit Ryan authorization.

The accepted planning result recommends one bounded internal contract slice:
add provider-owned runtime provenance carrying to `EvalProviderResult` and eval
record serialization, proved only with `oracle_signal_locals_probe`. This is
not a public schema, package-root, MCP, CLI/product, docs, scoring, compiler,
fixture, task, run-spec, or new-runtime-form lane, but it is still an internal
eval provider/result contract change. Ryan authorization has been granted for
the implementation prompt, and the implementation is accepted in workspace
first-pass. Release-unit audit passed first-pass with no findings; full
regression passed first-pass with `1636 passed`; commit-gating passed
first-pass with no findings. The exact release unit was locally committed as
`165bb43 Carry eval runtime provenance in provider results` and pushed with
explicit Ryan authorization. Do not route it back to release gates, staging,
local commit, or push absent new findings.

The post-`165bb43` route selection is accepted with no findings. The next
implementation lane is one internal provider/run-spec integration slice: add a
new provider name `context_ir_default_local_python_subprocess`, support only
the exact `oracle_signal_locals_probe` task at first, replay through the real
default local-Python subprocess facade inside the requested eval budget, and
carry provider-owned runtime provenance into raw eval records. The slice must
also make eval metrics treat the new provider as a semantic selected-unit
provider. It must not change durable eval run specs, tasks, fixtures, public
interfaces, MCP, package-root exports, docs/claims, scoring formulas,
compiler behavior, generalized runtime support, or runtime-probe forms.

That implementation slice is accepted in workspace first-pass with no
findings. Focused validation passed: ruff check, ruff format check, strict
mypy, targeted pytest over `tests/test_eval_signal_locals_probe.py`,
`tests/test_eval_runs.py`, `tests/test_eval_metrics.py`, and
`tests/test_eval_results.py` with `51 passed`, and `git diff --check`. The
proposed release unit is `BUILDLOG.md`, `PLAN.md`,
`src/context_ir/eval_metrics.py`, `src/context_ir/eval_providers.py`,
`src/context_ir/eval_runs.py`, `tests/test_eval_metrics.py`,
`tests/test_eval_runs.py`, and `tests/test_eval_signal_locals_probe.py`.
The release-unit audit passed first-pass with no findings. Run full regression
passed first-pass with `1640 passed`. Commit-gating passed first-pass with no
findings. The exact release unit was locally committed as
`5133ac8 Add default local-Python subprocess eval provider` and pushed with
explicit Ryan authorization. Do not route it back to release gates, staging,
local commit, or push absent new findings.

Pushed `dynamic_import:builtins.__import__/1` local-Python subprocess behavior:

- worker and parent runner register exactly the new
  `dynamic_import:builtins.__import__/1` form alongside the five pushed
  dynamic-import subprocess forms
- the concrete worker observer requires source-module global `builtins` to be
  present and identical to the real `builtins` module before using the shared
  controlled `builtins.__import__` plus bounded `sys.modules[name]` capture
  core
- source modules with missing, rebound, shadowed, or non-builtins `builtins`
  globals fail closed
- target-time source global `builtins` mutation and `builtins.__import__`
  mutation fail closed after restoration
- adjacent `dynamic_import:loader.__import__/1` remains fail-closed
- no request schema, package-root export, MCP, README, EVAL, PUBLIC_CLAIMS,
  public benchmark, scoring, compiler, admission, recompile, tool-facade,
  result-assembly, builtins-alias support, loader `__import__` support, or
  generalized dynamic-import support was added
- focused control validation passed:
  - ruff check
  - ruff format check, `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, `tests/test_dependency_frontier.py`,
    and `tests/test_runtime_acquisition.py`, `481 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - release-unit audit cleared
  - full regression cleared with `1222 passed`
  - commit-gating cleared for the exact six-file unit
- local commit creation completed at
  `9a88794 Add builtins attribute import subprocess support`
- Ryan-authorized push completed for
  `9a88794 Add builtins attribute import subprocess support`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `9a88794 Add builtins attribute import subprocess support`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: control selection of the next bounded north-star lane

Pushed `dynamic_import:__import__/1` local-Python subprocess release:

- worker and parent runner register exactly the new
  `dynamic_import:__import__/1` form alongside the four pushed importlib-family
  forms
- the concrete worker observer handles bare `__import__(name)` by temporarily
  hooking `builtins.__import__` during replay target execution, inserting a
  controlled `sys.modules[name]` entry, then restoring both hook and
  `sys.modules[name]` state on success and failure
- source modules that shadow global `__import__` fail closed
- target-time `builtins.__import__` mutation fails closed after restoration
- adjacent builtin attribute and alias forms remain fail-closed:
  `dynamic_import:builtins.__import__/1` and
  `dynamic_import:loader.__import__/1`
- no request schema, package-root export, MCP, public claim, eval, scoring,
  compiler, admission, recompile, tool-facade, result-assembly,
  builtins-attribute/alias support, or generalized dynamic-import support was
  added
- focused control validation passed:
  - ruff check
  - ruff format check, `4 files already formatted`
  - strict mypy over 37 source files
  - targeted pytest over `tests/test_runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, `tests/test_dependency_frontier.py`,
    and `tests/test_runtime_acquisition.py`, `472 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - release-unit audit cleared
  - full regression cleared with `1213 passed`
  - commit-gating cleared for the exact six-file unit
- local commit creation completed at
  `1b08bb9 Add bare builtin import subprocess support`
- Ryan-authorized push completed for
  `1b08bb9 Add bare builtin import subprocess support`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `1b08bb9 Add bare builtin import subprocess support`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: control selection of the next bounded north-star lane

Pushed `dynamic_import:load_module/1` local-Python subprocess release:

- worker and parent runner register exactly the new
  `dynamic_import:load_module/1` form alongside the three already-pushed exact
  forms
- the concrete worker observer handles imported-alias `load_module(name)` by
  rebinding only the replay target source module global `load_module` to the
  existing controlled import-module observer for target execution, then
  restoring it
- missing, mismatched, or target-mutated `load_module` globals fail closed
- adjacent builtin forms remain fail-closed, including
  `dynamic_import:__import__/1`,
  `dynamic_import:builtins.__import__/1`, and
  `dynamic_import:loader.__import__/1`
- no request schema, MCP/schema, package-root export, README, EVAL,
  PUBLIC_CLAIMS, public benchmark, scoring, compiler, admission, recompile,
  tool-facade, result-assembly, builtin-import, generalized alias, or
  generalized dynamic-import support was added
- corrected control validation passed with `345 passed` for the targeted
  pytest pair
- combined read-only release gate passed with no findings:
  - release-unit audit cleared
  - full regression cleared with `1200 passed`
  - commit-gating cleared for the exact six-file unit
- release state:
  - accepted in workspace: yes, after 1 correction
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `a0f46f3 Add imported-alias dynamic import subprocess support`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: read-only planning/decomposition for the first exact builtin
    `__import__` local-Python subprocess form

Pushed `dynamic_import:import_module/1` local-Python subprocess release:

- worker and parent runner register exactly the new
  `dynamic_import:import_module/1` form alongside the two already-pushed exact
  forms
- the concrete worker observer handles imported-name `import_module(name)` by
  rebinding only the replay target source module global `import_module` to the
  existing controlled import-module observer for target execution, then
  restoring it
- missing, mismatched, or target-mutated `import_module` globals fail closed
- adjacent forms remain fail-closed, including
  `dynamic_import:load_module/1`, `dynamic_import:__import__/1`,
  `dynamic_import:builtins.__import__/1`, and
  `dynamic_import:loader.__import__/1`
- no request schema, MCP/schema, package-root export, README, EVAL,
  PUBLIC_CLAIMS, public benchmark, scoring, compiler, admission, recompile,
  tool-facade, result-assembly, imported-alias, builtin-import, or generalized
  dynamic-import support was added
- focused control validation passed with `340 passed` for the targeted pytest
  pair
- combined read-only release gate passed with no findings:
  - release-unit audit cleared
  - full regression cleared with `1195 passed`
  - commit-gating cleared for the exact six-file unit
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `2035f4f Add imported-name dynamic import subprocess support`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: control selection of the next bounded north-star lane

Pushed `dynamic_import:loader.import_module/1` local-Python subprocess
release:

- add exact root-module alias subprocess support for
  `dynamic_import:loader.import_module/1`
- `src/context_ir/runtime_probe_worker.py` now accepts exactly the existing
  `dynamic_import:importlib.import_module/1` form and new
  `dynamic_import:loader.import_module/1` form
- worker default handler registration covers both exact forms through the
  existing dynamic-import handler adapter and concrete observer
- `src/context_ir/runtime_probe_execution.py` now has
  `make_runtime_probe_dynamic_import_local_python_subprocess_runner(...)`
  registers both exact dynamic-import forms
- the implementation reuses the existing `importlib.import_module`
  interception harness and does not add new interception families
- focused coverage in `tests/test_runtime_probe_worker.py` and
  `tests/test_runtime_probe_execution.py` proves a real
  `python -m context_ir.runtime_probe_worker` subprocess observes
  `loader.import_module(...)` as `imported_module=...`
- adjacent forms such as `dynamic_import:load_module/1`,
  `dynamic_import:__import__/1`, `dynamic_import:builtins.__import__/1`, and
  non-dynamic reflective forms remain fail-closed
- no request schema, MCP/schema, package-root export, README, EVAL,
  PUBLIC_CLAIMS, public benchmark, scoring, compiler, admission, recompile,
  result-assembly, generalized alias, imported-name/imported-alias, or
  builtin-import subprocess support is authorized
- validation passed under focused ruff, format check, strict mypy, targeted
  pytest `331 passed`, and `git diff --check`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes, full pytest `1186 passed`
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `db3eb8b Add loader import_module subprocess support`
  - Ryan-authorized push completed for
    `db3eb8b Add loader import_module subprocess support`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`,
    `src/context_ir/runtime_probe_worker.py`,
    `tests/test_runtime_probe_execution.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: superseded by accepted workspace-only
    `dynamic_import:import_module/1` local-Python subprocess release candidate

Pushed dynamic-import local-Python tool facade:

- `src/context_ir/tool_facade.py` now has
  `SemanticDynamicImportLocalPythonSubprocessRecompileRequest`,
  `SemanticDynamicImportLocalPythonSubprocessRecompileResponse`, and
  `recompile_repository_context_with_dynamic_import_local_python_subprocess`
- the facade delegates to
  `apply_dynamic_import_local_python_subprocess_for_diagnostic_and_recompile(...)`
- caller inputs remain explicit for the Python executable, invocation and
  completion revisions, repository snapshot basis, probe contract revision,
  runtime assumptions, runner contract revision, timeout, runner environment,
  runner assumptions, and optional embedding function
- the response mirrors nested runner preparation, attempt collection,
  result-batch admission, observation application, recompile result, compile
  result, diagnostic, budget, and selected/upgraded unit identities
- tests in `tests/test_tool_facade.py` prove real subprocess behavior,
  explicit-input delegation, mirror-field enforcement, package-root export
  quarantine, and unchanged MCP exports
- new names are added to `tool_facade.__all__` only
- package-root exports and MCP exports remain unchanged
- no README, EVAL, PUBLIC_CLAIMS, public benchmark, eval, scoring, compiler,
  stdout-protocol, worker behavior, admission contract, result-assembly,
  automatic environment discovery, default `sys.executable` policy,
  generalized dynamic-import support claim, or new runtime family/form was
  added
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes, full pytest `1178 passed`
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `88f7c74 Add dynamic import tool facade`
  - Ryan-authorized push completed for
    `88f7c74 Add dynamic import tool facade`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/tool_facade.py`, and `tests/test_tool_facade.py`
  - next route: control selection of the next bounded north-star lane

Pushed dynamic-import local-Python recompile helper:

- `src/context_ir/runtime_observation_recompile.py` now has internal helper
  `apply_dynamic_import_local_python_subprocess_for_diagnostic_and_recompile`
- the helper composes
  `make_runtime_probe_dynamic_import_local_python_subprocess_runner(...)` with
  the existing `apply_runtime_probe_runner_for_diagnostic_and_recompile(...)`
  bridge
- the Python executable, invocation contract revision, completion contract
  revision, repository snapshot basis, probe contract revision, runtime
  assumptions, runner contract revision, timeout, runner environment, and
  runner assumptions remain explicit caller inputs
- tests in `tests/test_runtime_observation_recompile.py` prove the helper runs
  a real `python -m context_ir.runtime_probe_worker` subprocess through the
  pushed default dynamic-import worker path, admits the observed
  `imported_module=plugins.recompile_subprocess` payload, and recompiles the
  runtime-backed diagnostic boundary
- export-boundary assertions keep the helper out of package-root exports and
  `runtime_observation_recompile.__all__`
- no public API, MCP, tool facade, package-root export, schema, eval, scoring,
  compiler, public-claim, stdout-protocol, worker behavior, admission
  contract, result-assembly, automatic environment discovery, default
  `sys.executable` policy, or new runtime family/form was added
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes, full pytest `1176 passed`
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `842ddda Add dynamic import recompile helper`
  - Ryan-authorized push completed for
    `842ddda Add dynamic import recompile helper`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_observation_recompile.py`, and
    `tests/test_runtime_observation_recompile.py`
  - next route: control selection of the next bounded north-star lane

Pushed dynamic-import local-Python subprocess runner factory:

- `src/context_ir/runtime_probe_execution.py` now has module-local
  `make_runtime_probe_dynamic_import_local_python_subprocess_runner`
- the helper composes the existing dispatching runner with exactly one
  existing local-Python subprocess handler entry
- the registered handler is limited to `RuntimeProbeFamily.DYNAMIC_IMPORT` and
  `dynamic_import:importlib.import_module/1`
- the helper invokes the existing worker module
  `context_ir.runtime_probe_worker` with no module argv by default
- the Python executable plus invocation and completion contract revisions
  remain explicit inputs
- tests in `tests/test_runtime_probe_execution.py` prove the helper reaches
  the worker's default dynamic-import handler through a real
  `python -m context_ir.runtime_probe_worker` subprocess and does not register
  adjacent family/form requests
- package-root exports remain unchanged
- no recompile convenience wrapper, automatic runner selection, tool facade,
  public API, package-root export, MCP, schema, eval, scoring, compiler,
  public-claim, admission, result-assembly, stdout-protocol, worker behavior,
  or new runtime family/form was added
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes, full pytest `1175 passed`
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `6d4e04c Add dynamic import subprocess runner factory`
  - Ryan-authorized push completed for
    `6d4e04c Add dynamic import subprocess runner factory`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_execution.py`, and
    `tests/test_runtime_probe_execution.py`
  - next route: control selection of the next bounded north-star lane

Pushed runtime probe real-subprocess recompile bridge proof release:

- focused coverage in `tests/test_runtime_observation_recompile.py` creates a
  temporary repository with a zero-argument replay target that calls
  `importlib.import_module("plugins.recompile_subprocess")`
- the test derives the diagnostic runtime-probe request plan through the
  existing semantic compile/diagnose path
- the test builds the existing dispatching runner with the existing
  local-Python subprocess handler entry for `RuntimeProbeFamily.DYNAMIC_IMPORT`
  and `dynamic_import:importlib.import_module/1`
- the test runs `apply_runtime_probe_runner_for_diagnostic_and_recompile(...)`
  using a real `python -m context_ir.runtime_probe_worker` subprocess
- the observed attempt, result, admission, and recompile chain carries
  `imported_module=plugins.recompile_subprocess`
- non-proof result separation remains empty for the proof case
- the diagnostic boundary upgrades to attached runtime support through the
  existing recompile path
- no source, worker, runtime execution, admission, recompile, tool facade,
  package-root export, MCP, schema, eval, scoring, compiler, public-claim,
  stdout-protocol, or result-assembly surface was widened
- focused validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_observation_recompile.py tests/test_runtime_observation_recompile.py`
    passed
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_observation_recompile.py tests/test_runtime_observation_recompile.py`
    passed, reporting `2 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed, reporting 37 source
    files
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_observation_recompile.py tests/test_runtime_probe_execution.py tests/test_runtime_probe_worker.py -q`
    passed, reporting `335 passed`
  - `git diff --check` passed
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes, full pytest `1172 passed`
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `ced8850 Prove runtime probe subprocess recompile bridge`
  - Ryan-authorized push completed for
    `ced8850 Prove runtime probe subprocess recompile bridge`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`, and
    `tests/test_runtime_observation_recompile.py`
  - next route: control selection of the next bounded north-star lane

Pushed parent-side real-subprocess proof release:

- focused coverage in `tests/test_runtime_probe_execution.py` creates a
  temporary repository source module and drives the existing local-Python
  subprocess handler through the dispatching runner
- the subprocess path runs `python -m context_ir.runtime_probe_worker` without
  injected worker handlers
- the worker uses the pushed default dynamic-import handler for
  `RuntimeProbeFamily.DYNAMIC_IMPORT` and
  `dynamic_import:importlib.import_module/1`
- the parent materializes an observed `RuntimeProbeExecutionAttempt` through
  the existing stdout protocol with normalized payload
  `imported_module=plugins.parent_subprocess`
- no changes were made to `src/context_ir/runtime_probe_worker.py`,
  `src/context_ir/runtime_probe_execution.py`, package-root exports, MCP,
  public API, schema, eval, scoring, compiler, docs, public claims, admission,
  recompile, or result assembly surfaces
- focused validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_execution.py tests/test_runtime_probe_execution.py`
    passed
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_execution.py tests/test_runtime_probe_execution.py`
    passed, reporting `2 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed, reporting 37 source
    files
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_execution.py tests/test_runtime_probe_worker.py -q`
    passed, reporting `320 passed`
  - `git diff --check` passed
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest `1171 passed`
  - Gate 3 commit-gating passed for the exact three-file unit
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `cee4e9f Prove dynamic import worker subprocess path`
  - Ryan-authorized push completed for
    `cee4e9f Prove dynamic import worker subprocess path`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`, and
    `tests/test_runtime_probe_execution.py`
  - next route: control selection of the next bounded north-star lane

Pushed local Python dynamic-import default worker handler registration
release:

- omitted `handler_entries` in `context_ir.runtime_probe_worker.main()`
  resolves to a module-local default handler table
- the default handler table registers only the concrete dynamic-import
  observer for `RuntimeProbeFamily.DYNAMIC_IMPORT` and
  `dynamic_import:importlib.import_module/1`
- explicit injected handler entries, including `handler_entries=()`, preserve
  their existing fail-closed behavior
- valid dynamic-import worker stdin can emit the existing stdout success
  protocol through the default `main()` path
- malformed stdin, unsupported family/form requests, explicit handler-table
  behavior, observer failures, stdout/stderr shielding, and package-root
  export quarantine remain covered
- parent executor/parser behavior, subprocess runner behavior, stdout protocol
  shape, package-root exports, MCP, public API, schema, eval, scoring,
  compiler, docs, public-claim, admission, recompile, and result assembly
  surfaces are unchanged
- focused validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed, reporting `2 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed, reporting 37 source
    files
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py -q`
    passed, reporting `319 passed`
  - `git diff --check` passed
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest `1170 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `2c21798 Register dynamic import worker default handler`
  - Ryan-authorized push completed for
    `2c21798 Register dynamic import worker default handler`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: control selection of the next bounded north-star lane

Pushed local Python dynamic-import concrete observer composition release:

- adds module-local
  `observe_runtime_probe_dynamic_import_worker_request(...)`
- accepts and validates a
  `RuntimeProbeLocalPythonDynamicImportWorkerRequest`
- materializes the replay target, imports the replay target source module,
  resolves the replay target callable, executes the callable under the
  existing import-interception harness, and returns the existing
  `RuntimeProbeLocalPythonDynamicImportWorkerObservation`
- remains injectable through
  `build_runtime_probe_dynamic_import_worker_handler_entry(...)`
- preserves worker stdout/stderr shielding and import/cwd/path restoration
  through the already-pushed helpers
- does not add default/global worker handler registration, parent
  executor/parser changes, stdout protocol shape changes, package-root
  exports, MCP, public API, schema, eval, scoring, compiler, docs,
  public-claim, admission, recompile, or result assembly changes
- focused validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed, reporting `2 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed, reporting 37 source
    files
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py -q`
    passed, reporting `315 passed`
  - `git diff --check` passed
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest `1166 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `79b635b Compose dynamic import worker observer`
- Ryan-authorized push completed for
  `79b635b Compose dynamic import worker observer`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `79b635b Compose dynamic import worker observer`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: control selection of the next bounded north-star lane

Pushed local Python dynamic-import source module import harness release:

- adds module-local
  `import_runtime_probe_dynamic_import_replay_target_source_module(...)`
- accepts a validated
  `RuntimeProbeLocalPythonDynamicImportReplayTarget`
- imports exactly `replay_target.source_module_name` using the request working
  directory and ordered Python path entries
- redirects module-import stdout and stderr away from worker stdout/stderr
- restores `sys.path` and the process working directory on success and failure
- validates the imported result is a `ModuleType` whose `__name__` matches
  `replay_target.source_module_name`
- rejects request/replay-target drift, import failures, malformed import
  results, and source-module name drift with deterministic worker-local errors
- package-root exports remain unchanged
- no replay-target attribute resolution, resolved callable execution,
  dynamic-import interception run, concrete observer wiring, default/global
  handler registration, worker stdout protocol shape change, parent
  executor/parser change, API, MCP, schema, eval, scoring, compiler, docs,
  public-claim, admission, recompile, or result assembly change is included
- control reran focused validation:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed, reporting `2 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed, reporting 37 source
    files
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py -q`
    passed, reporting `303 passed`
  - `git diff --check` passed
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest `1154 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `f0eb9e1 Add dynamic import source module importer`
- Ryan-authorized push completed for
  `f0eb9e1 Add dynamic import source module importer`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `f0eb9e1 Add dynamic import source module importer`
  - pushed: yes
  - committed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - next route: control selection of the next bounded north-star lane

Accepted workspace-only local Python dynamic-import replay target attribute
resolver slice:

- adds module-local
  `resolve_runtime_probe_dynamic_import_replay_target_callable(...)`
- accepts a validated
  `RuntimeProbeLocalPythonDynamicImportReplayTarget`
- accepts an injected `ModuleType` source module object and validates that
  `source_module.__name__` matches `replay_target.source_module_name`
- resolves `replay_target.replay_target_attribute_path` by normal attribute
  lookup without executing the resolved object
- returns the callable target expected by the existing import interception
  harness
- rejects non-module source objects, source-module name drift,
  request/replay-target drift, missing attributes, and noncallable final
  targets
- package-root exports remain unchanged
- no repository source-module import, target callable execution, import
  interception run, concrete observer wiring, default/global handler
  registration, worker stdout protocol shape change, parent executor/parser
  change, API, MCP, schema, eval, scoring, compiler, docs, public-claim,
  admission, recompile, or result assembly change is included
- control reran focused validation:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed, reporting `2 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed, reporting 37 source
    files
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py -q`
    passed, reporting `297 passed`
  - `git diff --check` passed
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest `1148 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `bd2ba92 Add dynamic import replay target resolver`
- Ryan-authorized push completed for
  `bd2ba92 Add dynamic import replay target resolver`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `bd2ba92 Add dynamic import replay target resolver`
  - pushed: yes
  - release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - release-gate status is no-active-gate for `bd2ba92`
  - next route: control selection of the next bounded north-star lane

Accepted workspace-only local Python dynamic-import import interception
harness slice:

- adds module-local
  `materialize_runtime_probe_dynamic_import_worker_observation_from_target(...)`
- accepts either a validated
  `RuntimeProbeLocalPythonDynamicImportWorkerRequest` or
  `RuntimeProbeLocalPythonDynamicImportReplayTarget`
- accepts an injected zero-argument target callable and runs it under a
  controlled `importlib.import_module` wrapper
- captures exactly one absolute dotted imported module name and materializes
  the existing `RuntimeProbeLocalPythonDynamicImportWorkerObservation`
  contract
- shields target stdout and stderr so worker stdout protocol output cannot be
  contaminated
- restores `importlib.import_module` on success and failure
- rejects zero captured imports, multiple captured imports, malformed module
  names, relative imports, package imports, noncallable targets, and
  replay-target drift
- package-root exports remain unchanged
- no repository source-module import, repository attribute lookup, concrete
  observer replay-target resolution, default/global handler registration,
  subprocess behavior change, parent executor/parser change, stdout protocol
  shape change, API, MCP, schema, eval, scoring, compiler, docs, public-claim,
  admission, recompile, or result assembly change is included
- control reran focused validation:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed, reporting `2 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed, reporting 37 source
    files
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py -q`
    passed, reporting `290 passed`
  - `git diff --check` passed
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest `1141 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `5fb6cf8 Add dynamic import interception harness`
- Ryan-authorized push completed for
  `5fb6cf8 Add dynamic import interception harness`
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `5fb6cf8 Add dynamic import interception harness`
  - pushed: yes
  - release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - release-gate status is no-active-gate for `5fb6cf8`
  - next route: control selection of the next bounded north-star lane

Accepted workspace-only local Python dynamic-import worker replay target
contract slice:

- adds module-local frozen
  `RuntimeProbeLocalPythonDynamicImportReplayTarget`
- adds `materialize_runtime_probe_dynamic_import_replay_target(...)`, which
  consumes
  `RuntimeProbeLocalPythonDynamicImportWorkerRequest` and derives the
  repository replay target shape needed by a future concrete observer
- derives a strict source module name from the request source file path, for
  example `main.py` -> `main`, `pkg/runtime.py` -> `pkg.runtime`, and
  `pkg/__init__.py` -> `pkg`
- derives the target attribute path from `replay_target_seed` only when it is a
  dotted target rooted at the derived source module name
- preserves request identity, source file path, replay target seed, replay
  selector seed, invocation identity, and request replay payload fields
- rejects unsupported replay targets such as `source:...` fallback seeds,
  blank or malformed module/attribute segments, absolute or traversal source
  paths, non-`.py` source files, source-module drift, request drift, and
  direct-constructor drift
- valid derivation for top-level modules, nested modules, and package
  `__init__.py`, frozen behavior, request revalidation, direct-constructor
  drift, malformed source paths, `source:...` fallback rejection,
  source-module drift, malformed target segments, module-local availability,
  package-root non-export, and no-importlib boundary are covered by tests
- control reran focused validation:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed, reporting `2 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed, reporting 37 source
    files
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py -q`
    passed, reporting `279 passed`
  - `rg -n "^(import importlib|from importlib)" src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    produced no matches
  - `git diff --check` passed
- no `importlib` imports, repository code execution, module import attempts,
  attribute lookup, concrete observer implementation, default/global handler
  registration, subprocess changes, parent executor/parser changes,
  package-root export, docs, eval, schema, scoring, compiler, API, MCP, public
  claims, admission, recompile, or result assembly changes are included
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes, full pytest `1130 passed`
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `7fe4f76 Add dynamic import replay target contract`
  - pushed: yes, with release routing through
    `ad3ed71 Sync dynamic import replay target routing`
  - proposed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - push completed after explicit Ryan authorization
  - next route: control selection of the next bounded north-star lane

Accepted workspace-only local Python dynamic-import worker handler adapter
slice:

- adds a module-local non-executing handler adapter/factory for the exact
  `RuntimeProbeFamily.DYNAMIC_IMPORT` form
  `dynamic_import:importlib.import_module/1`
- the adapter consumes `RuntimeProbeLocalPythonWorkerRequestPayload`
  values, materializes
  `RuntimeProbeLocalPythonDynamicImportWorkerRequest`, calls an injected
  observer callable, validates the returned
  `RuntimeProbeLocalPythonDynamicImportWorkerObservation`, and returns the
  existing `RuntimeProbeLocalPythonWorkerSuccessResponse`
- the observer callable remains injected behavior only; the slice does not
  implement actual `importlib.import_module(...)`
- provides a factory returning a `RuntimeProbeLocalPythonWorkerHandlerEntry`
  suitable for the existing worker-side dispatch
- factory metadata, noncallable observer rejection, direct adapter success,
  validated request delivery, dispatch/main success with injected fake
  observer, observer exception sanitization, drifted observation fail-closed
  behavior, module-local availability, package-root non-export, and
  no-importlib boundary are covered by tests
- default `main(...)` remains fail-closed without default handlers
- control reran focused validation:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    passed, reporting `2 files already formatted`
  - `.venv/bin/python -m mypy --strict src/` passed, reporting 37 source
    files
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py -q`
    passed, reporting `258 passed`
  - `rg -n "^(import importlib|from importlib)" src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
    produced no matches
  - `git diff --check` passed
- no `importlib` imports, repository code execution, module import attempts,
  concrete observer implementation, default/global handler registration,
  subprocess changes, parent executor/parser changes, package-root export,
  docs, eval, schema, scoring, compiler, API, MCP, public claims, admission,
  recompile, or result assembly changes are included
- release state:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes, full pytest `1109 passed`
  - commit-gating-cleared: yes
  - staged: yes, then committed
  - locally committed: yes,
    `73feb5f Add dynamic import worker handler adapter`
  - pushed: yes, with release routing through
    `196188b Sync dynamic import handler routing`
  - proposed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
    `src/context_ir/runtime_probe_worker.py`, and
    `tests/test_runtime_probe_worker.py`
  - push completed after explicit Ryan authorization
  - next route: control selection of the next bounded north-star lane

Prior dynamic-import request and observation route notes, plus worker ingress,
dispatch, and stdout-egress route notes below, are historical continuity and
are superseded for active routing by the accepted dynamic-import worker
handler adapter slice above.

Accepted local Python worker post-stdin-execution spike:

- recommendation: add a fail-closed `context_ir.runtime_probe_worker` ingress
  skeleton before worker-side dispatch, concrete family/form behavior, stdout
  failure protocol changes, or global registration
- rationale: generic request handoff is complete, but no module exists at the
  configured worker module name; a fail-closed ingress proves valid and
  malformed stdin cannot become runtime proof
- valid worker request payloads should parse through the existing strict
  payload parser and then return deterministic nonzero fail-closed status with
  empty stdout
- malformed stdin should return deterministic sanitized failure with empty
  stdout and no raw payload, traceback, path, or environment leakage
- nonzero completion remains safe because existing parent-side handling
  normalizes it as non-proof

Accepted workspace-only fail-closed local Python worker ingress implementation
slice:

- adds `src/context_ir/runtime_probe_worker.py`
- adds `tests/test_runtime_probe_worker.py`
- implements a testable worker entrypoint that reads stdin, parses only with
  `parse_runtime_probe_local_python_worker_request_payload(...)`, and always
  fails closed without emitting stdout proof
- invalid stdin and valid-but-unimplemented requests both exit nonzero,
  deterministically, with sanitized stderr
- keeps package root unchanged; no `context_ir.__all__` export
- no concrete handler logic, dynamic import execution, worker dispatch
  registry, stdout protocol extension, global handler registration,
  subprocess execution in tests, filesystem IO, docs, public claims, API, MCP,
  schema, eval, scoring, optimizer, compiler, admission, recompile, or result
  assembly changes

Current release state for the selected worker ingress skeleton slice:

- selected by control: yes
- spike lane launched: yes
- spike returned: yes
- spike accepted by control: yes, first-pass
- implementation lane launched: yes
- implementation returned: yes
- accepted in workspace: yes, first-pass
- implementation validation reported by execution lane: passed, including
  targeted suite reporting `203 passed`
- focused control validation: passed with `5 passed`
- focused control ruff and format checks: passed
- release-unit-audit-cleared: yes
- full-regression-cleared: yes, full pytest `1054 passed`
- commit-gating-cleared: yes
- staged: yes, then committed
- locally committed: yes, `f67e5f8 Add fail-closed runtime probe worker`
- pushed: yes, with release routing through
  `1cc925a Sync fail-closed worker release routing`
- expected implementation files:
  `src/context_ir/runtime_probe_worker.py` and
  `tests/test_runtime_probe_worker.py`
- control-route continuity files:
  `PLAN.md` and `BUILDLOG.md`
- proposed release unit is exactly:
  `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_worker.py`, and
  `tests/test_runtime_probe_worker.py`
- push completed after explicit Ryan authorization
- next route: fail-closed worker-side dispatch contract implementation lane

Selected next worker-side dispatch contract slice:

- add a small internal dispatch table/handler-entry contract inside
  `src/context_ir/runtime_probe_worker.py`
- dispatch from parsed `RuntimeProbeLocalPythonWorkerRequestPayload`
  family/form metadata only
- default `main(...)` remains fail-closed with no registered handlers and no
  stdout proof
- missing-handler, handler-exception, duplicate-handler, malformed-handler,
  and invalid-response paths must fail closed with deterministic sanitized
  stderr and empty stdout
- no concrete family/form worker behavior, dynamic import execution, stdout
  success protocol emission, global registration, parent executor changes,
  API/MCP/package-root/schema/eval/scoring/compiler/docs/public-claim changes,
  admission, recompile, or result assembly changes

Accepted workspace-only local Python worker-side dispatch contract slice:

- adds frozen typed worker response and handler-entry contracts in
  `src/context_ir/runtime_probe_worker.py`
- adds a fail-closed dispatching worker keyed by parsed
  `RuntimeProbeLocalPythonWorkerRequestPayload.family_label` and `form_label`
- default `main(...)` behavior remains fail-closed with no registered handlers,
  nonzero exit status, sanitized stderr, and empty stdout
- matching injected handlers are called only after strict stdin payload parsing
- valid handler responses still fail closed without stdout proof
- missing handler, duplicate handler, malformed handler, handler exception,
  and invalid handler response paths fail closed with deterministic sanitized
  stderr and empty stdout
- package-root exports remain unchanged
- no concrete family/form behavior, dynamic import execution, repository-code
  execution, stdout success protocol emission, global registration, parent
  executor changes, API, MCP, schema, eval, scoring, compiler, docs,
  public-claim, admission, recompile, or result assembly changes
- implementation validation reported by the execution lane passed, including
  targeted suite reporting `210 passed`
- focused control validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py -q`,
    reporting `210 passed`
  - `git diff --check`
- combined read-only release gate passed after one continuity correction:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1061 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- release-unit-audit-cleared: yes
- full-regression-cleared: yes, full pytest `1061 passed`
- commit-gating-cleared: yes
- staged: yes, then committed
- locally committed: yes, `7eefba2 Add fail-closed worker dispatch`
- pushed: yes, with release routing through
  `d3c16d1 Sync worker dispatch release routing`
- proposed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_worker.py`, and
  `tests/test_runtime_probe_worker.py`
- push completed after explicit Ryan authorization
- next route: local Python worker stdout success egress contract

Selected next worker stdout success egress contract slice:

- add a typed worker success response/serialization contract in
  `src/context_ir/runtime_probe_worker.py`
- the emitted stdout shape must match the existing parent parser:
  `runtime_probe_stdout_protocol_revision`,
  ordered `normalized_payload`, and optional `durable_artifact_reference`
- matching injected handlers may return the new success response and `main(...)`
  may write the deterministic stdout protocol and return zero
- default `main(...)` with no handlers remains fail-closed with empty stdout
- malformed request, missing handler, duplicate handler, malformed handler,
  handler exception, invalid response, and malformed success metadata paths
  remain fail-closed, nonzero, sanitized, and empty-stdout
- no concrete family/form worker behavior, dynamic import execution,
  repository-code execution, global registration, parent executor changes,
  API/MCP/package-root/schema/eval/scoring/compiler/docs/public-claim changes,
  admission, recompile, or result assembly changes

Accepted workspace-only local Python worker stdout success egress contract
slice:

- adds frozen typed
  `RuntimeProbeLocalPythonWorkerSuccessResponse` in
  `src/context_ir/runtime_probe_worker.py`
- adds deterministic serialization through
  `serialize_runtime_probe_local_python_worker_success_response(...)`
- matching injected handlers can return the success response; `main(...)`
  writes the existing parent stdout success protocol and returns zero
- emitted stdout shape matches the existing parent parser:
  `runtime_probe_stdout_protocol_revision`, ordered `normalized_payload`, and
  optional `durable_artifact_reference`
- stdout is deterministic and has no trailing newline
- parent parser compatibility is tested through the existing parent
  `RuntimeProbeLocalPythonProcessCompletion`,
  `RuntimeProbeLocalPythonStdoutProtocolResult`, and observed-attempt
  materializers
- durable-only success is supported
- default `main(...)` with no handlers remains fail-closed with nonzero exit
  status, sanitized stderr, and empty stdout
- malformed stdin, missing handler, duplicate handler, malformed handler,
  handler exception, invalid response, and malformed success metadata paths
  remain fail-closed, nonzero, sanitized, and empty-stdout
- package-root exports remain unchanged
- no concrete family/form behavior, dynamic import execution, repository-code
  execution, global registration, parent executor changes, parent stdout
  parser changes, API, MCP, schema, eval, scoring, compiler, docs,
  public-claim, admission, recompile, or result assembly changes
- implementation validation reported by the execution lane passed
- focused control validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_worker.py tests/test_runtime_probe_worker.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_worker.py tests/test_runtime_probe_execution.py -q`,
    reporting `215 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1066 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- release-unit-audit-cleared: yes
- full-regression-cleared: yes, full pytest `1066 passed`
- commit-gating-cleared: yes
- staged: yes, then committed
- locally committed: yes, `9c6a3b5 Add worker stdout success egress`
- pushed: yes, with release routing through
  `0ea7ca5 Sync worker stdout egress release routing`
- proposed release unit is exactly `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_worker.py`, and
  `tests/test_runtime_probe_worker.py`
- push completed after explicit Ryan authorization
- next route: local Python dynamic-import worker request contract

The local Python subprocess non-proof attempt normalization slice is accepted
in workspace after one correction. It adds pure module-local helpers that
convert local Python subprocess failure facts into non-proof
`RuntimeProbeExecutionAttempt` values:

- `subprocess.TimeoutExpired` maps to `TIMED_OUT`
- other local subprocess execution exceptions map to non-proof attempts,
  defaulting to `CRASHED`
- nonzero `RuntimeProbeLocalPythonProcessCompletion.returncode` maps to a
  non-proof attempt, defaulting to `CRASHED`
- configured non-proof outcomes for nonzero completions are supported
- `RuntimeProbeResultOutcome.OBSERVED` is rejected at the helper boundary
- zero-returncode completions reject or remain deferred

Release-gate finding and correction:

- Gate 1 found that the accepted release-unit wording overclaims identity
  preservation
- the produced `RuntimeProbeExecutionAttempt` preserves runner request,
  request object, and execution input identity, but it has no fields for
  invocation or completion object identity
- the materializers revalidate invocation/completion contracts before attempt
  materialization, but they do not preserve those objects in the resulting
  attempt
- Ryan authorized the recommended narrow continuity/spec correction
- active wording now states that invocation/completion contracts are revalidated
  while runner request, request object, and execution input identity are
  preserved in the produced attempt

Corrected boundary:

- do not widen `RuntimeProbeExecutionAttempt` to carry invocation or completion
  identity in this slice; that would expand the source contract beyond the
  intended non-proof failure-normalization boundary
- rerun the combined read-only release gate over the exact four-file unit

Current release state for the proposed local Python subprocess non-proof
attempt normalization unit:

- selected by control: yes
- implementation lane launched: yes
- implementation returned: yes
- review finding: missing configured-outcome and observed-outcome rejection
  coverage
- correction authorized by Ryan: yes
- correction returned: yes
- release-gate finding: identity preservation overclaim in continuity/spec
  wording, corrected after Ryan authorization
- accepted in workspace: yes, after one implementation correction and one
  continuity/spec correction
- focused validation: passed with `199 passed`
- release-unit-audit-cleared: yes
- full-regression-cleared: yes, full pytest `961 passed`
- commit-gating-cleared: yes
- staged: yes, then committed
- locally committed: yes, `5b10728`
- pushed: yes, with `origin/main` advanced through `c471fd1`
- next route: bounded read-only local Python success-boundary next-move spike

The runtime probe runner-request attempt/result assembly release is pushed at
`3363929 Assemble runtime probe runner request attempts` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

Released unit:

- `src/context_ir/runtime_probe_execution.py`
- `tests/test_runtime_probe_execution.py`
- `PLAN.md`
- `BUILDLOG.md`

The runtime probe runner-request materialization release is pushed at
`68a8e73 Materialize runtime probe runner requests` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

Released unit:

- `src/context_ir/runtime_probe_execution.py`
- `tests/test_runtime_probe_execution.py`
- `PLAN.md`
- `BUILDLOG.md`

The runtime probe execution-attempt result assembly release is pushed at
`86be8d7 Assemble runtime probe execution attempts` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

Released unit:

- `src/context_ir/runtime_probe_execution.py`
- `tests/test_runtime_probe_execution.py`
- `PLAN.md`
- `BUILDLOG.md`

The corrected combined read-only release gate passed with no findings, full
regression passed with `869 passed`, local commit creation is complete, and
Ryan-authorized push is complete.

The runtime probe execution-input materialization release is pushed at
`cfed3c7 Add runtime probe execution input materialization` and has
release-gate status no-active-gate. It should not be reopened absent new
findings.

The released slice adds internal non-executing typed execution-attempt records
tied to `RuntimeProbeExecutionInput` and a deterministic helper that
converts a complete attempt set for a `RuntimeProbeExecutionInputBatch` into
`RuntimeProbeResultBatch`. It does not execute probes, collect runtime
observations, admit observations, attach provenance, recompile, serialize
JSON/schema, widen `tool_facade.py`, `mcp_server.py`, `context_ir/__init__.py`,
or touch eval, scoring, optimizer, compiler, package-root, product, benchmark,
or public-claim surfaces.

The runner-request materialization slice is workspace-only accepted first-pass
and release-gate-cleared, local commit creation is complete at
`68a8e73 Materialize runtime probe runner requests`. It adds frozen internal
runner-request records tied to `RuntimeProbeExecutionInput` and a deterministic
helper that turns a complete `RuntimeProbeExecutionInputBatch` into an ordered
runner-request batch. It does not execute probes. The runner-request contract
preserves plan ID, request IDs, request object identity, execution-input object
identity, replay artifact identity, batch order, explicit runner contract
revision, timeout, and explicit runner environment/assumption fields. It
rejects drift, duplicates, blank metadata, invalid timeout, empty runner
environment, and empty runner assumptions. The combined read-only release gate
passed with no findings: Gate 1 release-unit audit passed, Gate 2 full
regression passed with `876 passed`, Gate 3 commit-gating passed, and
Ryan-authorized push is complete.

The runner-request attempt/result assembly slice is workspace-only accepted
first-pass and release-gate-cleared, local commit creation is complete at
`3363929 Assemble runtime probe runner request attempts`, and Ryan-authorized
push is complete. It adds an internal helper that accepts a
`RuntimeProbeRunnerRequestBatch` plus typed `RuntimeProbeExecutionAttempt`
values, validates attempts against the runner requests, and returns a
deterministic `RuntimeProbeResultBatch` in runner-request plan order. It does
not execute probes. It preserves runner request order, plan ID, request IDs,
request object identity, execution-input object identity, replay artifact
identity, and existing observed/non-proof result behavior. It rejects
unplanned, duplicate, missing, plan-drifted, request-drifted,
execution-input-drifted, runner-request-drifted, blank, and malformed attempt
metadata.

The combined read-only release gate passed with no findings: Gate 1
release-unit audit passed, Gate 2 full regression passed with `882 passed`,
and Gate 3 commit-gating passed.

Ryan-authorized push is complete.

The runtime probe diagnostic runner-request preparation slice is
workspace-only accepted first-pass, release-gate-cleared, locally committed at
`fd0f6d8 Prepare runtime probe diagnostic runner requests`, and pushed. It
adds a frozen internal preparation envelope and helper that take a
`SemanticDiagnosticResult` with an attached `planned_runtime_probe_request_plan`,
materialize the corresponding `RuntimeProbeExecutionInputBatch`, and then
materialize the corresponding `RuntimeProbeRunnerRequestBatch`. It does not
execute probes. It preserves diagnostic object identity, request plan object
identity, request object identities, plan IDs, request IDs,
execution-input identity, replay artifact identity, runner metadata, and
deterministic plan order. It rejects missing diagnostic plans,
diagnostic/request-plan drift, blank probe or runner metadata, empty runtime
assumptions, invalid timeout, and drift already rejected by the pushed
input/runner-request materialization contracts.

Release state for the diagnostic runner-request preparation unit:

- proposed release unit is exactly:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- workspace-only accepted
- release-unit-audit-cleared
- full-regression-cleared with `885 passed`
- commit-gating-cleared
- locally committed at `fd0f6d8`
- Ryan-authorized push completed with `origin/main` advanced through
  `74d84fb Sync runtime probe diagnostic runner request release routing`
- release-gate status is no-active-gate

The runtime probe runner-callable attempt collection slice is workspace-only
accepted first-pass, release-gate-cleared, locally committed at
`32f6220 Collect runtime probe runner attempts`, and pushed. It adds an
internal strict runner-callable attempt collection boundary. It accepts a
`RuntimeProbeRunnerRequestBatch` and a typed runner callable, validates the
batch before invocation, calls the runner exactly once per
`RuntimeProbeRunnerRequest` in runner-request order, collects only typed
`RuntimeProbeExecutionAttempt` values, validates and assembles them through the
existing runner-request-gated result-batch helper, and returns a frozen
internal envelope preserving the runner request batch, ordered attempts, and
result batch. It supports empty runner-request batches without invoking the
callable. It does not implement subprocess execution, in-process probe
execution, family/form-specific probe logic, timeout enforcement,
exception-to-result synthesis, admission, recompile, facade/MCP/package-root
export, schema, eval, scoring, optimizer, compiler, benchmark, or public
claims. Runner exceptions propagate; failure outcomes remain the
responsibility of a runner callable that returns typed non-proof attempts.

Release state for the runner-callable attempt collection unit:

- proposed release unit is exactly:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- workspace-only accepted
- release-unit-audit-cleared
- full-regression-cleared with `891 passed`
- commit-gating-cleared
- locally committed at `32f6220`
- Ryan-authorized push completed with `origin/main` advanced through
  `e9b5b5a Sync runtime probe runner attempt collection release routing`
- release-gate status is no-active-gate

The runtime probe diagnostic runner-callable recompile bridge slice is
workspace-only accepted first-pass. It adds a frozen internal envelope and
helper that compose diagnostic runner-request preparation, runner-callable
attempt collection, and the existing result-batch recompile helper. It accepts
a `SemanticDiagnosticResult` with an attached
`planned_runtime_probe_request_plan`, runtime probe preparation metadata, a
typed `RuntimeProbeRunnerCallable`, and the existing semantic recompile inputs.
It preserves diagnostic preparation, runner attempt collection, and
result-batch recompile application identity; preserves non-proof results as
non-proof; propagates runner exceptions; and leaves empty planned request
batches deterministic without runner invocation. It does not implement
subprocess execution, in-process repository probe execution,
family/form-specific probe logic, timeout enforcement, exception-to-result
synthesis, admission rule changes, recompile rule changes, facade/MCP/
package-root export, schema, eval, scoring, optimizer, compiler, benchmark, or
public claims.

Release state for the diagnostic runner-callable recompile bridge unit:

- proposed release unit is exactly:
  - `src/context_ir/runtime_observation_recompile.py`
  - `tests/test_runtime_observation_recompile.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- release-unit-audit-cleared
- full-regression-cleared with `895 passed`
- commit-gating-cleared
- staged: no
- locally committed at `74fb275 Compose runtime probe runner callable recompile`
- pushed with `origin/main` advanced through
  `f463df7 Sync runtime probe callable recompile release routing`
- release-gate status is no-active-gate

The runtime probe runner failure-normalization adapter slice is workspace-only
accepted first-pass. It adds an opt-in internal adapter in
`src/context_ir/runtime_probe_execution.py` that wraps a
`RuntimeProbeRunnerCallable` so `Exception` failures raised by the runner
become typed non-proof `RuntimeProbeExecutionAttempt` values for the matching
`RuntimeProbeRunnerRequest`, while successful typed attempts continue through
unchanged by object identity. The existing strict collector still propagates
runner exceptions when no adapter is used, untyped runner returns are rejected
rather than normalized, and `BaseException` subclasses still propagate. The
adapter preserves request, execution-input, replay-artifact, runner-request
identity, and runner-request batch order through existing gates, and keeps
crash, timeout, missing-environment, and setup-failure outcomes non-proof. It
does not implement subprocess execution, in-process repository probe
execution, timeout enforcement, family/form-specific probe logic, admission
rule changes, recompile rule changes, facade/MCP/package-root export, schema,
eval, scoring, optimizer, compiler, benchmark, or public claims.

Release state for the runtime probe runner failure-normalization adapter unit:

- proposed release unit is exactly:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- release-unit-audit-cleared
- full-regression-cleared with `903 passed`
- commit-gating-cleared
- staged: no
- locally committed at `93456b6 Normalize runtime probe runner failures`
- pushed with `origin/main` advanced through
  `4f13fac Sync runtime probe failure normalization routing`
- release-gate status is no-active-gate

The runtime probe runner dispatch table slice is accepted first-pass in
workspace-only state. Proposed release unit:

- `src/context_ir/runtime_probe_execution.py`
- `tests/test_runtime_probe_execution.py`
- `PLAN.md`
- `BUILDLOG.md`

The slice adds an internal frozen typed handler registry keyed by
`(RuntimeProbeFamily, form_label)` and a dispatching
`RuntimeProbeRunnerCallable` that validates `RuntimeProbeRunnerRequest`,
selects handlers by carried request family/form, and returns typed handler
attempts unchanged. Missing handlers return deterministic non-proof attempts,
defaulting to `RuntimeProbeResultOutcome.SETUP_FAILED`, while preserving
runner-request identity and replay artifact identity through existing gates.
Duplicate handler keys, blank form labels, observed missing-handler outcomes,
untyped handler returns, and handler identity drift reject or flow through
existing runner-request-gated assembly. Handler-raised exceptions propagate
unless the handler or dispatch runner is explicitly wrapped with the existing
failure-normalizing adapter. The slice does not add concrete family/form probe
behavior, subprocess execution, in-process repository probe execution, timeout
enforcement, admission rule changes, recompile rule changes,
facade/MCP/package-root export, schema, eval, scoring, optimizer, compiler,
benchmark, or public claims.

Release state for the runtime probe runner dispatch table unit:

- accepted in workspace: yes, first-pass
- release-unit-audit-cleared: yes, no findings
- focused validation: passed with `232 passed`
- full-regression-cleared: yes, full pytest `912 passed`
- commit-gating-cleared: yes
- staged: no
- locally committed at `3751df1 Add runtime probe runner dispatch table`
- pushed with `origin/main` advanced through
  `d7fe447 Sync runtime probe dispatch routing`
- release-gate status is no-active-gate
- next route: internal runtime probe runner environment context implementation
  slice

The runtime probe runner environment context slice is accepted first-pass in
workspace-only state. Proposed release unit:

- `src/context_ir/runtime_probe_execution.py`
- `tests/test_runtime_probe_execution.py`
- `PLAN.md`
- `BUILDLOG.md`

The slice adds a frozen typed `RuntimeProbeLocalPythonEnvironmentContext` and
`derive_runtime_probe_local_python_environment_context(...)` in
`src/context_ir/runtime_probe_execution.py`. It revalidates
`RuntimeProbeRunnerRequest` before deriving the context, parses
`runner_environment` into repository root, working directory, and ordered
Python path entries, preserves runner contract revision, timeout seconds,
runner environment, and runner assumptions for replay, and rejects missing
required singleton fields, duplicate singleton metadata, blank path metadata,
relative path metadata, and malformed path metadata. The context remains
module-local through `context_ir.runtime_probe_execution.__all__`, with no
package-root export.

Release state for the runtime probe runner environment context unit:

- accepted in workspace: yes, first-pass
- focused validation: passed with `163 passed`
- release-unit-audit-cleared: yes, no findings
- full-regression-cleared: yes, full pytest `925 passed`
- commit-gating-cleared: yes
- staged: no
- locally committed at `f75196e Add runtime probe runner environment context`
- pushed with `origin/main` advanced through
  `646298b Sync runtime probe environment context local routing`
- release-gate status is no-active-gate
- next route: select the next bounded control action after the pushed release

The slice does not inspect the filesystem, import modules, execute repository
code, spawn subprocesses, enforce timeouts, generate observed attempts, change
dispatch behavior, admission, recompile, facade/MCP/package-root export,
schema, eval, scoring, optimizer, compiler, benchmark, or public claims.

The runtime probe result-batch recompile tranche is pushed at
`591c09b Compose runtime probe result batch recompile` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

The runtime probe result admission bridge tranche is pushed at
`ccd417a Add runtime probe result admission bridge` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The runtime probe execution-result/replay-artifact contract tranche is pushed
at `eb6def0 Add runtime probe result contracts` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The typed facade runtime recompile tranche is pushed at
`8ac3b46 Add typed runtime recompile facade` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The runtime observation recompile composition tranche is pushed at
`b279b00 Compose runtime observation recompile flow` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

The diagnostic trace-refresh tranche is pushed at
`74aadd7 Refresh diagnostic runtime trace support` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The diagnostic runtime observation application tranche is pushed at
`95f7545 Apply diagnostic runtime observations` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The admitted runtime observation provenance bridge tranche is pushed at
`35c440d Attach admitted runtime observations` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The runtime observation admission compatibility validation tranche is pushed
at `f5c8df0 Validate runtime observation admission compatibility` and has
release-gate status no-active-gate. It should not be reopened absent new
findings.

The diagnostic runtime observation admission bridge tranche is pushed at
`8706f2e Add diagnostic runtime observation admission bridge` and has
release-gate status no-active-gate. It should not be reopened absent new
findings.

- `src/context_ir/runtime_observation_admission.py`
- `tests/test_runtime_observation_admission.py`
- `PLAN.md`
- `BUILDLOG.md`

The released slice adds
`admit_runtime_observations_for_diagnostic(diagnostic, observations)` as a
module-local helper in `src/context_ir/runtime_observation_admission.py`. It
uses the diagnostic's existing `planned_runtime_probe_request_plan`, rejects
diagnostics without an attached plan, and delegates to the released
`admit_runtime_observations_for_plan(...)` plan-level helper. It preserves
diagnostic/request/plan/observation object identity, deterministic plan order,
plan IDs, request IDs, empty-plan behavior, and the existing plan-level
unmatched/duplicate observation rejection.

The slice does not rederive runtime probe requests or plans from a program,
execute probes, define execution-result contracts, attach provenance, mutate
diagnostics/programs/requests/plans/observations, change analyzer or
tool-facade behavior, expose package-root or MCP APIs, or widen eval, schema,
scoring, optimizer, compiler, winner-selection, product, public benchmark, or
public-claim surfaces.

The internal runtime observation admission read-model tranche is pushed at
`b0a5ec5 Add runtime observation admission read model` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

- `src/context_ir/runtime_observation_admission.py`
- `tests/test_runtime_observation_admission.py`
- `PLAN.md`
- `BUILDLOG.md`

Ryan explicitly authorized opening this narrow observation-admission scope
after `fce09b0`. The authorized scope is limited to an internal read-model
contract: an already-collected typed runtime observation may be admitted only
when its source-site identity matches a request in a `RuntimeProbeRequestPlan`.
The slice must not execute probes, attach provenance, change analyzer or
tool-facade behavior, expose package-root or MCP APIs, or widen eval, schema,
scoring, optimizer, compiler, winner-selection, product, public benchmark, or
public-claim surfaces.

The post-`7c46f48` North Star planning/control spike is accepted. It selected
`index_runtime_probe_request_plan_by_source_site(plan)` in
`src/context_ir/runtime_probe_requests.py` as the next smallest meaningful
capability slice. This slice stays on the planned side: it indexes a
`RuntimeProbeRequestPlan` by the same source-site identity convention already
used by runtime request derivation and runtime acquisition matching, and it
rejects duplicate source-site ambiguity. The implementation slice is pushed at
`6d5fc47 Index runtime probe plans by source site` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The semantic diagnostic runtime probe request plan surfacing tranche is pushed
at `7c46f48 Surface semantic diagnostic probe plans` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

The diagnostic runtime probe request plan bridge tranche is pushed at
`97dc0f6 Add diagnostic runtime probe request plans` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

The planned runtime probe request plan tranche is pushed at
`744bf0e Add runtime probe request plans` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The planned runtime probe request ID indexing tranche is pushed at
`3df02c6 Index runtime probe requests by ID` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The stable planned runtime probe request identity tranche is pushed at
`49fa461 Add runtime probe request identities` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The completed diagnose/recompile bridge-consumption tranche is pushed at
`a819cf5 Surface diagnostic runtime probe requests` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The next control/planning lane must preserve the remaining holds: no probe
execution, execution-result contract, runtime observation collection,
analyzer/tool-facade behavior, package-root API, MCP, eval, schema, scoring,
optimizer, compiler, winner-selection, product, public benchmark, or
public-claim widening. Runtime provenance attachment is authorized only for
the already-pushed admitted-batch bridge at `35c440d`, through existing
additive runtime acquisition helpers.

Do not route `6d5fc47 Index runtime probe plans by source site` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `7c46f48 Surface semantic diagnostic probe plans` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `97dc0f6 Add diagnostic runtime probe request plans` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `744bf0e Add runtime probe request plans` back to docs review,
release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `3df02c6 Index runtime probe requests by ID` back to docs review,
release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `49fa461 Add runtime probe request identities` back to docs review,
release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `a819cf5 Surface diagnostic runtime probe requests` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `2e448ea Add diagnostic runtime probe request bridge` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `f6c66e4 Add runtime probe request planning contract` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `546a4da Add reflective builtin branch eval probes` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

`546a4da Add reflective builtin branch eval probes` is complete and pushed,
with release status no-active-gate. It is the current pushed code/eval release
authority.

`d73cde4 Expand original dynamic import budget coverage` is complete and
pushed, with release status no-active-gate. It is the prior pushed code/eval
release authority. Do not route `d73cde4` back to docs review, release-unit
audit, focused validation, full regression, commit-gating, staging, local
commit creation, or push absent new findings.

`e2f3dcf Expand dir-zero and metaclass budget coverage` is complete and pushed,
with release status no-active-gate. It is the prior pushed code/eval authority,
not the active route. Do not route `e2f3dcf` back to docs review,
release-unit audit, full regression, commit-gating, staging, local commit
creation, or push absent new findings.

`8aa38d5 Sync dir-zero metaclass release routing` is the prior pushed
continuity authority. `642b6f9 Sync exec eval release routing` is the earlier
pushed continuity authority. `21f2dc5 Expand exec and eval budget coverage` is
the earlier pushed code/eval authority and is no-active-gate.
`9fffc5e Sync dynamic import release routing`,
`c2c1898 Expand dynamic import sibling eval budget coverage`,
`98edc4a Codify release gate continuity controls`,
`b8e126e Expand runtime mutation eval budget coverage`, and
`ad9db8d Expand dir eval budget coverage` remain older pushed authorities and
are no-active-gate. Do not reopen `546a4da`, `d73cde4`, `e2f3dcf`, `8aa38d5`,
`642b6f9`, `21f2dc5`, `c2c1898`, `9fffc5e`, `98edc4a`, `b8e126e`, `ad9db8d`,
or earlier pushed releases absent new findings. Push remains Ryan-gated for any
future release. Do not widen
public/API/MCP/package-export/schema/scoring/optimizer/compiler/
winner-selection/product/public benchmark scope without a separately
authorized planning decision.

Completed post-5bd0616 planning decision:

- The next smallest evidence-building capability wedge is not a new runtime
  family. It was a budget-pressure expansion of the
  `oracle_signal_getattr_attribute_error_probe_matrix`, now released at
  `43d0439`.
- The implementation slice edited only:
  - `evals/run_specs/oracle_signal_getattr_attribute_error_probe_matrix.json`
  - `tests/test_eval_signal_getattr_attribute_error_probe.py`
- The slice adds budget `100` beside `220`, preserves the same fixture, task,
  query, providers, selector truth, and
  `lookup_outcome=raised_attribute_error` runtime payload, and asserts the
  same unsupported/opaque selected unit with additive runtime provenance at
  both budgets.
- Baseline providers remain empty at both budgets.
- Source, fixtures, task JSON, release-facing docs, public claims,
  package-root APIs, MCP behavior, analyzer/tool-facade/runtime behavior,
  schema, scoring, optimizer, compiler, winner-selection, product, and public
  benchmark changes remain out of scope for this released expansion.

Completed latest pushed release unit:

- Treat the internal eval-only `REFLECTIVE_BUILTIN` / `dir(obj)`
  budget-pressure expansion as completed and pushed at
  `ad9db8d Expand dir eval budget coverage`.
- Released budget-pressure expansion files:
  - `evals/run_specs/oracle_signal_dir_probe_matrix.json`
  - `tests/test_eval_signal_dir_probe.py`
- Docs/evidence/continuity reconciliation files:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- The matrix is `oracle_signal_dir_probe_matrix`: 1 task x 2 budgets x 3
  providers at budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`.
- Fixture, task, query, and runtime payload remain unchanged across both
  budget rows; runtime payload remains `listing_entry_count=74`.
- Selector and selected-unit truth remain `unsupported/opaque`; runtime
  provenance remains additive only; baseline providers remain empty at both
  budgets; public comparative claims remain bounded to the existing quad
  matrix.
- Excluded surfaces remain source beyond the released run-spec/test
  expansion, fixtures, task JSON, `AGENTS.md`,
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/
  winner-selection/product/public benchmark changes.
- Docs/evidence/continuity reconciliation is accepted first-pass;
  release-unit audit cleared first-pass; full regression cleared first-pass
  with `709 passed`.
- Commit-gating, local commit creation, and Ryan-authorized push completed at
  `ad9db8d`.
- No active release gate remains for
  `ad9db8d Expand dir eval budget coverage` absent new findings.
- Do not route back to docs review, release-unit audit, full regression,
  commit-gating, staging, local commit creation, or push for `ad9db8d` absent
  new findings.

Prior pushed release unit:

- Treat the internal eval-only `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` budget-pressure expansion as
  completed and pushed at
  `43d0439 Expand getattr AttributeError eval budget coverage`.
- Eval-only pilot files:
  - `evals/fixtures/oracle_signal_getattr_attribute_error_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_getattr_attribute_error_probe/main.py`
  - `evals/run_specs/oracle_signal_getattr_attribute_error_probe_matrix.json`
  - `evals/tasks/oracle_signal_getattr_attribute_error_probe.json`
  - `tests/test_eval_signal_getattr_attribute_error_probe.py`
- Docs/evidence/continuity reconciliation files:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- The matrix is `oracle_signal_getattr_attribute_error_probe_matrix`: 1
  task x 2 budgets x 3 providers at budgets 220 and 100, against providers
  `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- Fixture boundary is exactly `getattr(obj, name)`, with `AttributeError`
  caught so `render_probe_digest()` is deterministic
- Runtime payload is `lookup_outcome=raised_attribute_error`; primary selector
  and selected-unit truth remain `unsupported/opaque`; runtime provenance
  remains additive only; no dependency edge or selected symbol is created from
  the missing attribute
- Excluded forms remain generalized reflective-builtin support, dependency
  edges or selected symbols from missing attributes, product surface changes,
  schema changes, scoring changes, optimizer changes, compiler changes,
  winner-selection changes, and any
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening
- Implementation accepted first-pass.
- The original budget-220 pilot docs/evidence/continuity reconciliation was
  accepted after 2 corrections.
- The budget-pressure docs/evidence/continuity reconciliation was accepted
  first-pass.
- Release-unit audit cleared first-pass.
- Full regression cleared first-pass with `709 passed`.
- The first commit-gating review rejected with P1 stale-routing findings in
  `PLAN.md` and `BUILDLOG.md`.
- The routing correction was accepted first-pass.
- Corrected commit-gating cleared first-pass.
- Budget-pressure commit-gating, local commit creation, and Ryan-authorized push
  completed at `43d0439`.
- No active release gate remains for
  `43d0439 Expand getattr AttributeError eval budget coverage` absent new
  findings.
- Do not route back to docs review, release-unit audit, full regression,
  commit-gating, staging, local commit creation, or push for `43d0439` absent
  new findings.

Earlier pushed release unit:

- Treat the initial budget-220 internal eval-only `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot as completed and pushed at
  `5bd0616 Add getattr AttributeError eval probe`.
- The prior pushed matrix was
  `oracle_signal_getattr_attribute_error_probe_matrix`: 1 task x 1 budget x 3
  providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`.
- Fixture boundary, runtime payload, selector truth, and non-goals match the
  latest `43d0439` tranche except that the prior pushed matrix did not include
  budget 100.
- Local commit creation and Ryan-authorized push completed at `5bd0616`.
- Do not route back to docs review, release-unit audit, full regression,
  commit-gating, staging, local commit creation, or push for `5bd0616` absent
  new findings.

Earlier pushed release unit:

- Treat the builtins-alias pilot assets as completed and pushed at
  `6ac1e28 Add builtins-alias dynamic import eval probe`:
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/main.py`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/plugins/__init__.py`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/plugins/weather.py`
  - `evals/run_specs/oracle_signal_dynamic_import_builtins_alias_probe_matrix.json`
  - `evals/tasks/oracle_signal_dynamic_import_builtins_alias_probe.json`
  - `tests/test_eval_signal_dynamic_import_builtins_alias_probe.py`
- The matrix is `oracle_signal_dynamic_import_builtins_alias_probe_matrix`: 1
  task x 1 budget x 3 providers at budget 220, against providers
  `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- Fixture boundary is `import builtins as loader`,
  `name = "plugins.weather"`, and exactly `loader.__import__(name)`, with
  bounded `sys.modules[name]` retrieval only
- Runtime payload is `imported_module=plugins.weather`; primary selector and
  selected-unit truth remain `unsupported/opaque`; runtime provenance remains
  additive only; no dependency edge or selected symbol is created from
  `plugins.weather`
- Source/contract prerequisite and eval-only sibling were accepted first-pass.
- Docs/evidence/continuity reconciliation was accepted after one correction.
- Release-unit audit cleared first-pass.
- Full regression cleared first-pass with `702 passed`.
- Corrected commit-gating cleared first-pass after stale-routing corrections.
- Local commit creation and Ryan-authorized push completed at `6ac1e28`.
- Do not route back to release-unit audit, full regression, commit-gating,
  staging, local commit creation, or push for `6ac1e28` absent new findings.

Earlier pushed release unit:

- Treat the builtins-attribute pilot assets as completed and pushed at
  `3dfc355 Add builtins-attribute dynamic import eval probe`:
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_attr_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_attr_probe/main.py`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_attr_probe/plugins/__init__.py`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_attr_probe/plugins/weather.py`
  - `evals/run_specs/oracle_signal_dynamic_import_builtins_attr_probe_matrix.json`
  - `evals/tasks/oracle_signal_dynamic_import_builtins_attr_probe.json`
  - `tests/test_eval_signal_dynamic_import_builtins_attr_probe.py`
- The matrix is `oracle_signal_dynamic_import_builtins_attr_probe_matrix`: 1
  task x 1 budget x 3 providers at budget 220, against providers
  `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- Fixture boundary is `import builtins`, `name = "plugins.weather"`, and
  exactly `builtins.__import__(name)`, with bounded `sys.modules[name]`
  retrieval only
- Runtime payload is `imported_module=plugins.weather`; primary selector and
  selected-unit truth remain `unsupported/opaque`; runtime provenance remains
  additive only; no dependency edge or selected symbol is created from
  `plugins.weather`
- Treat the prior root-module alias pilot assets as completed and pushed at
  `b85f038 Add root-alias dynamic import eval probe`.
- The root-module alias matrix is `oracle_signal_dynamic_import_root_alias_probe_matrix`: 1 task
  x 1 budget x 3 providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`
- Fixture boundary is `import importlib as loader`,
  `name = "plugins.weather"`, and exactly `loader.import_module(name)`
- Runtime payload is `imported_module=plugins.weather`; primary selector and
  selected-unit truth remain `unsupported/opaque`; runtime provenance remains
  additive only; no dependency edge or selected symbol is created from
  `plugins.weather`
- Excluded forms remain root-module `importlib.import_module(name)` expansion,
  imported-name `import_module(name)` expansion, imported-alias
  `load_module(name)` expansion, literal dynamic import expansion,
  `__import__(name)`, `builtins.__import__`, globals/locals/fromlist forms,
  namespace mutation, generated-code dependency modeling, generalized dynamic
  import support, and any
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening
- Implementation/assets were accepted workspace-only before release; corrected
  docs/evidence/continuity reconciliation was accepted after one P1
  state-neutrality correction; release-unit audit cleared first-pass; full
  regression cleared first-pass with `688 passed`; commit-gating cleared
  first-pass; local commit creation completed at `b85f038`; Ryan-authorized
  push completed at `b85f038`
- There is no active release gate for `b85f038`

Prior pushed release unit:

- Treat the imported-alias pilot assets as completed and pushed at `4030845`:
  - `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/main.py`
  - `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/plugins/__init__.py`
  - `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/plugins/weather.py`
  - `evals/run_specs/oracle_signal_dynamic_import_imported_alias_probe_matrix.json`
  - `evals/tasks/oracle_signal_dynamic_import_imported_alias_probe.json`
  - `tests/test_eval_signal_dynamic_import_imported_alias_probe.py`
- Release-unit audit cleared first-pass
- Full regression cleared first-pass with `682 passed`
- First commit-gating rejected with P1 stale-routing findings in `PLAN.md` and
  `BUILDLOG.md`
- Continuity correction accepted first-pass
- Corrected commit-gating cleared first-pass
- Local commit creation completed at `4030845`
- Ryan-authorized push completed at `4030845`
- There is no active release gate for `4030845`
- The released matrix is
  `oracle_signal_dynamic_import_imported_alias_probe_matrix`: 1 task x 1
  budget x 3 providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`
- Fixture boundary is `from importlib import import_module as load_module`,
  `name = "plugins.weather"`, and exactly `load_module(name)`
- Runtime payload is `imported_module=plugins.weather`; primary selector and
  selected-unit truth remain `unsupported/opaque`; runtime provenance remains
  additive only; no dependency edge or selected symbol is created from
  `plugins.weather`
- Excluded forms remain root-module `importlib.import_module(name)` expansion,
  imported-name `import_module(name)` expansion, literal
  `load_module("plugins.weather")` expansion, `loader.import_module(name)`,
  `__import__(name)`, `builtins.__import__`, globals/locals/fromlist forms,
  namespace mutation, generated-code dependency modeling, generalized dynamic
  import support, and any
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening

Current pushed release authority:

- Treat pushed commit `3dfc355 Add builtins-attribute dynamic import eval
  probe` as the latest pushed release authority:
  - `oracle_signal_dynamic_import_builtins_attr_probe_matrix` is 1 task x 1
    budget x 3 providers at budget 220
  - providers remain `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `import builtins`, `name = "plugins.weather"`, and
    exactly `builtins.__import__(name)`, with bounded `sys.modules[name]`
    retrieval only
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or selected symbol is created from `plugins.weather`
  - no builtins alias form is included by this matrix; no bare
    `__import__(name)` expansion, shadowed/rebound/aliased forms, wrong-arity
    forms, literal `builtins.__import__("plugins.weather")` expansion,
    fromlist/globals/locals forms, namespace mutation, generated-code
    dependency modeling, or generalized dynamic import support is included
  - no public benchmark claim, API, MCP, package export, schema, scoring,
    optimizer, compiler, product, or winner-selection widening is authorized
  - implementation/assets were accepted workspace-only before release;
    docs/evidence/continuity reconciliation accepted first-pass; release-unit
    audit cleared first-pass; full regression passed with `696 passed`;
    commit-gating cleared first-pass; local commit creation and
    Ryan-authorized push completed at `3dfc355`
  - do not reopen `3dfc355` absent new findings
- Treat pushed commit `b9a493b Sync root-alias release routing` as a prior
  pushed continuity authority. It does not change eval/test release contents
  or authorize a new
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark boundary.
- Treat pushed commit `b85f038 Add root-alias dynamic import eval probe` as
  the prior root-module alias eval/test/docs release authority.
- Treat pushed commit `8a83a9b Sync imported-alias release routing` as a prior
  pushed continuity authority. It does not change eval/test release
  contents or authorize a new
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark boundary.
- Treat pushed commit `4030845 Add imported-alias dynamic import eval probe`
  as the prior dynamic-import imported-alias eval/test/docs release authority:
  - `oracle_signal_dynamic_import_imported_alias_probe_matrix` is 1 task x 1
    budget x 3 providers at budget 220
  - providers remain `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `from importlib import import_module as load_module`,
    `name = "plugins.weather"`, and exactly `load_module(name)`
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or selected symbol is created from `plugins.weather`
  - no imported-name `import_module(name)` expansion, root-module
    `importlib.import_module(name)` expansion, literal
    `load_module("plugins.weather")` expansion, `loader.import_module(name)`,
    `__import__(name)`, `builtins.__import__`, globals/locals/fromlist forms,
    namespace mutation, generated-code dependency modeling, or generalized
    dynamic import support is included
  - no public benchmark claim, API, MCP, package export, schema, scoring,
    optimizer, compiler, product, or winner-selection widening is authorized
  - release-unit audit cleared first-pass; full regression passed with
    `682 passed`; first commit-gating rejected with P1 stale-routing findings;
    continuity correction accepted first-pass; corrected commit-gating cleared
    first-pass; local commit creation and Ryan-authorized push completed at
    `4030845`
  - do not reopen `4030845` absent new findings
- Treat pushed commit `5d2d7e4 Sync imported-name dynamic import release routing`
  as the prior pushed continuity authority. It does not change eval/test
  release contents or authorize a new
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark boundary.
- Treat pushed commit `ee71a82 Add imported-name dynamic import eval probe` as
  the prior imported-name dynamic-import eval/test/docs release authority:
  - `oracle_signal_dynamic_import_imported_name_probe_matrix` is 1 task x 1
    budget x 3 providers at budget 220
  - providers remain `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `from importlib import import_module`,
    `name = "plugins.weather"`, and exactly `import_module(name)`
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or selected symbol is created from `plugins.weather`
  - no root-module `importlib.import_module(name)` expansion, literal
    `import_module("plugins.weather")` expansion, alias `load_module(name)`,
    `loader.import_module(name)`, `__import__(name)`, `builtins.__import__`,
    globals/locals/fromlist forms, or generalized dynamic import support is
    included
  - no public benchmark claim, API, MCP, package export, schema, scoring,
    optimizer, compiler, product, or winner-selection widening is authorized
  - release-unit audit cleared first-pass; full regression passed with
    `676 passed`; first commit-gating returned P1 continuity findings; the
    continuity correction was accepted; corrected commit-gating cleared; local
    commit and Ryan-authorized push completed at `ee71a82`
  - do not reopen `ee71a82` absent new findings
- Treat pushed commit `ca191c8 Sync builtin dynamic import release routing` as
  the prior builtin dynamic-import continuity authority. It does not change
  eval/test release contents or authorize a new
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark boundary.
- Treat pushed commit `397c7dd Add builtin dynamic import eval probe` as the
  prior builtin dynamic-import eval/test/docs release authority:
  - `oracle_signal_dynamic_import_builtin_probe_matrix` is 1 task x 1 budget x
    3 providers at budget 220
  - providers remain `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `name = "plugins.weather"` and exactly
    `__import__(name)`, with bounded `sys.modules[name]` retrieval only
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or symbol is created from `plugins.weather`
  - no `importlib.import_module(name)`, imported-name `import_module(name)`,
    alias or loader forms, `builtins.__import__`, globals/locals/fromlist
    forms, or generalized dynamic import support is included
  - no public benchmark claim, API, MCP, package export, schema, scoring,
    optimizer, compiler, product, or winner-selection widening is authorized
  - release-unit audit cleared first-pass; full regression passed with
    `670 passed`; commit-gating cleared first-pass; local commit and
    Ryan-authorized push completed at `397c7dd`
  - do not reopen `397c7dd` absent new findings
- Treat pushed commit `ad22ea6 Sync dynamic import root release routing` as an
  earlier pushed dynamic-import root release-routing continuity authority.
- Treat pushed commit `14b362e Add dynamic import root runtime eval pilot` as
  the prior root-module dynamic-import eval/test/docs release authority:
  - `oracle_signal_dynamic_import_root_probe_matrix` is 1 task x 1 budget x 3
    providers at budget 220
  - providers remain `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `import importlib`, `name = "plugins.weather"`, and
    exactly `importlib.import_module(name)`
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or symbol is created from the dynamically imported module
  - no `__import__(name)`, imported-name `import_module(name)`, alias or loader
    forms, or generalized dynamic import support is included
  - no public benchmark claim, API, MCP, package export, schema, scoring,
    optimizer, compiler, product, or winner-selection widening is authorized
  - release-unit audit cleared first-pass; full regression passed with
    `664 passed`; commit-gating cleared first-pass; local commit and
    Ryan-authorized push completed at `14b362e`
  - do not reopen `14b362e` absent new findings

Historical release anchors below remain guardrails and non-reopen constraints,
not pending release gates.

1. Treat pushed commit `bcd6d68 Add exec source runtime eval pilot` as the
   prior pushed exec(source) release authority:
   - `oracle_signal_exec_probe_matrix` is 1 task x 1 budget x 3 providers at
     budget 220
   - providers remain `context_ir`, `lexical_top_k_files`, and
     `import_neighborhood_files`
   - fixture/call boundary is `source = "pass"` and exactly `exec(source)`;
     executed source parses as exactly one `ast.Pass`
   - runtime proof requires `execution_outcome=completed`,
     `source_shape=literal_statement`, `source_sha256 == sha256(b"pass")`,
     and non-empty `durable_payload_reference`
   - optional `statement_kind=pass` is additive summary only
   - primary selector and selected-unit truth remain `unsupported/opaque`
   - runtime provenance remains additive only and attaches only to the
     preserved `EXEC_OR_EVAL` unsupported finding for `exec(source)`
   - no dependency edge or symbol is created from executed source
   - no namespace mutation modeling or generated-code dependency modeling is
     added
   - no generalized exec support is included
   - public comparative claims remain bounded to the existing quad matrix
   - no public benchmark claim, API, MCP, package export, schema, scoring,
     optimizer, compiler, product, or winner-selection widening is authorized
   - release-unit audit initially found one P1 digest-boundary issue; the
     correction pinned `source_sha256` to `sha256(b"pass")`; audit rerun
     cleared; full regression passed; commit-gating cleared; local commit
     creation completed; Ryan-authorized push completed
   - do not reopen `bcd6d68` exec(source) absent new findings
2. Treat pushed commit `96fc03a Add eval runtime eval pilot` as the prior
   pushed release authority:
   - `oracle_signal_eval_probe_matrix` is 1 task x 1 budget x 3 providers at
     budget 220
   - providers remain `context_ir`, `lexical_top_k_files`, and
     `import_neighborhood_files`
   - runtime proof requires `evaluation_outcome=returned_value`,
     `source_shape=literal_expression`, valid `source_sha256`, and non-empty
     `durable_payload_reference`
   - optional `result_type=builtins.str` is additive summary only
   - primary selector and selected-unit truth remain `unsupported/opaque`
   - runtime provenance remains additive only and attaches only to the
     preserved `EXEC_OR_EVAL` unsupported finding for `eval(source)`
   - public comparative claims remain bounded to the existing quad matrix
   - no public benchmark claim, API, MCP, package export, schema, scoring,
     optimizer, compiler, product, or winner-selection widening is authorized
   - do not reopen `96fc03a` eval(source) absent new findings
3. Treat pushed commit `41f6b57 Add delattr runtime eval pilot` as the prior
   pushed eval/test/docs release authority:
   - `oracle_signal_delattr_probe_matrix` is 1 task x 1 budget x 3 providers at budget `220`
   - providers remain `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
   - runtime payload is `mutation_outcome=deleted_attribute`
   - selector and selected-unit primary truth remain `unsupported/opaque`
   - runtime provenance remains additive only
   - public comparative claims remain bounded to the existing quad matrix
   - implementation is accepted first-pass
   - same-tranche docs/evidence reconciliation is accepted first-pass
   - release-unit audit is accepted first-pass with no findings
   - full regression is accepted first-pass with `612 passed, 1 deselected`
   - commit-gating is accepted first-pass
   - local commit creation and Ryan-authorized push are complete
4. Treat the accepted post-`41f6b57` planning decision as complete:
   - no concrete finding requires reopening `41f6b57`
   - `setattr(obj, name, value)` is the smallest uncovered `RUNTIME_MUTATION`
     sibling with an accepted lower-layer seam and no eval-only matrix
   - `delattr` budget `100` expansion is rejected for now because budget
     expansion is not automatic and no specific unanswered comparison requires
     it before `setattr`
   - `METACLASS_BEHAVIOR` is rejected as the immediate next move because it is
     a different, more claim-sensitive family
   - family-level consolidation is rejected for now because a small truthful
     evidence slice remains available
   - next implementation is one bounded eval-only
     `oracle_signal_setattr_probe_matrix`
   - implementation accepted first-pass in workspace-only state
   - same-tranche docs/evidence reconciliation accepted first-pass in
     workspace-only state
   - release-unit audit accepted first-pass with no findings
   - full regression accepted first-pass with `619 passed`
   - commit-gating accepted first-pass
   - exact accepted file set is approved for local commit with subject
     `Add setattr runtime eval pilot`
   - live local commit and push state must be verified from git
5. Treat pushed commit `c1a12d7 Add dir(obj) eval pilot` as the prior pushed
   eval/test/docs release authority, pushed commit `2dd8404 Expand locals eval
   budget matrix` as the prior `locals()` budget-expansion release authority,
   pushed commit `38e9d5f` as the prior initial `locals()` pilot release
   authority, pushed commit `5f74ede` as the prior `globals()` budget-expansion
   release authority, pushed commit `631a303` as the prior initial `globals()`
   release authority, pushed commit `9eec985` as the prior zero-argument
   `vars()` budget-expansion release authority, pushed commit `71db72e` as the
   prior initial zero-argument `vars()` pilot release authority, pushed commit
   `2c6b54a` as the prior `vars(obj)` budget-expansion release authority,
   pushed commit `ead239d` as the prior initial `vars(obj)` pilot release
   authority, and pushed commit `1b555ef` as the prior `getattr` family release
   authority:
   - `c1a12d7` adds `oracle_signal_dir_probe_matrix` as 1 task x 1 budget x 3 providers at budget 220 against `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
   - `c1a12d7` carries durable dir listing proof via `durable_payload_reference`; optional `listing_entry_count` is additive summary only
   - `c1a12d7` keeps selector and selected-unit primary truth `unsupported/opaque`, keeps runtime provenance as additive provenance only, and does not widen public comparative claims
   - `c1a12d7` passed implementation review, docs/evidence reconciliation after correction, process guardrail note acceptance, release-unit audit, full regression after one formatting correction with `607 passed`, corrected commit-gating, local commit creation, and Ryan-authorized push
   - `c1a12d7` does not authorize generalized dir support, zero-argument dir support, budget 100 expansion, public claim widening, API, MCP, runtime acquisition, analyzer, tool facade, schema, scoring, optimizer, or winner-selection widening
   - `2dd8404` expands `oracle_signal_locals_probe_matrix` to 1 task x 2 budgets x 3 providers at budgets `100` and `220`
   - `2dd8404` passed implementation review, same-tranche docs reconciliation, release-unit audit, full regression, corrected commit-gating, local commit creation, and Ryan-authorized push
   - the `locals()` matrix keeps selector and selected-unit primary truth `unsupported/opaque`, keeps runtime-backed provenance additive only with `lookup_outcome=returned_namespace`, and does not change runtime-acquisition, analyzer, tool-facade implementation, package-root API, MCP, schema, scoring, winner-selection, public benchmark, generalized `locals()` support, or public-claim boundaries
   - `38e9d5f` adds the initial internal eval-only `RUNTIME_MUTATION` / `locals()` pilot at `1 task x 1 budget x 3 providers` with budget `220`
   - `5f74ede` expands the existing internal eval-only `RUNTIME_MUTATION` / `globals()` matrix from budget `[220]` to budgets `[220, 100]`
   - `5f74ede` keeps selector and selected-unit primary truth `unsupported/opaque`, keeps runtime-backed provenance additive only with `lookup_outcome=returned_namespace`, and does not change runtime-acquisition, analyzer, tool-facade implementation, package-root API, MCP, schema, scoring, winner-selection, public benchmark, or public-claim boundaries
   - `631a303` adds the initial internal eval-only `RUNTIME_MUTATION` / `globals()` pilot at `1 task x 1 budget x 3 providers` with budget `220`
   - `631a303` preserves `unsupported/opaque` primary truth, additive runtime provenance, and the public-safe quad-matrix comparative boundary
   - `9eec985` expands the internal zero-argument `REFLECTIVE_BUILTIN` / `vars()` matrix to `1 task x 2 budgets x 3 providers` at budgets `100` and `220`
   - `71db72e` adds the initial internal zero-argument `REFLECTIVE_BUILTIN` / `vars()` eval pilot at `1 task x 1 budget x 3 providers` with budget `220`
   - `2c6b54a` expands the internal `REFLECTIVE_BUILTIN` / `vars(obj)` matrix to `1 task x 2 budgets x 3 providers` at budgets `100` and `220`
   - `ead239d` adds the initial internal `REFLECTIVE_BUILTIN` / `vars(obj)` eval pilot at `1 task x 1 budget x 3 providers` with budget `220`
   - `1b555ef` expands the existing `getattr` family matrices to budgets `220` and `100`
   - each `getattr` family matrix remains `1 task x 2 budgets x 3 providers`
3. Treat pushed commit `159e363` as the post-push continuity anchor for the `1b555ef` release state, and treat `8133e0a` as the prior docs-only process-correction anchor:
   - it corrects the self-referential continuity loop
   - it restores tranche-style release sequencing discipline
   - neither commit changes eval/test/docs release contents or widens product boundaries
4. Treat pushed commit `3291268` as the latest docs-only evidence/claim reconciliation authority:
   - it updates `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - it does not widen code/test authority, public claims, package-root exports, MCP behavior, source boundaries, schema, scoring, or winner selection
5. Treat pushed commit `d8ebdc3` as the prior runtime-outcome accounting release authority:
   - internal eval runtime-outcome accounting over normalized runtime provenance payload data
   - separate summary/report outcome counts for payload key/value pairs such as `lookup_outcome=returned_default_value` and `lookup_outcome=returned_value`
   - existing selector-tier, selected-unit-tier, provider, provider+tier, scoring, and winner-selection accounting remains unchanged
   - no runtime-acquisition, analyzer, tool-facade, package-root export, MCP, public-claim, fixture, task, run-spec, provider, budget, or public-doc surface changed
   - release-unit audit, full regression gate, commit-gating review, local commit creation, and remote push completed
6. Treat pushed commit `b014595` as the prior defaulted `getattr(obj, name, default)` value-return branch release authority:
   - narrow internal eval-only `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` value-return branch sibling pilot
   - `1 task x 1 budget x 3 providers` with budget `220`
   - additive runtime provenance remains separate from primary `unsupported/opaque` truth
   - same-tranche docs/evidence reconciliation in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - release-unit audit, full regression gate, commit-gating review, local commit creation, and remote push completed
7. Treat pushed commit `7d43302` as the prior defaulted `getattr(obj, name, default)` default-return branch release authority:
   - narrow internal eval-only `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` default-return branch pilot
   - `1 task x 1 budget x 3 providers` with budget `220`
   - additive runtime provenance remains separate from primary `unsupported/opaque` truth
   - same-tranche docs/evidence reconciliation in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - release-unit audit, full regression gate, commit-gating review, local commit creation, and remote push completed
8. Treat pushed commit `c592dca` as the prior `getattr(obj, name)` release authority:
   - narrow internal `REFLECTIVE_BUILTIN` / `getattr(obj, name)` eval pilot
   - `1 task x 1 budget x 3 providers` with budget `220`
   - additive runtime provenance remains separate from primary `unsupported/opaque` truth
   - same-tranche docs/evidence reconciliation in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - release-unit audit, full regression gate, commit-gating review, local commit creation, and remote push completed
9. Treat pushed commit `762dd51` as the prior `hasattr(obj, name)` provider/budget matrix release authority:
   - internal `REFLECTIVE_BUILTIN` / `hasattr(obj, name)` provider/budget matrix expansion
   - budgets `220` and `100`
   - additive runtime provenance remains separate from primary truth
   - full regression gate, commit-gating review, local commit creation, and remote push completed
10. Treat pushed commit `90dcc15` as the prior narrow `hasattr(obj, name)` pilot release authority.
11. Treat pushed commit `9a52b46` as the prior internal dynamic-import matrix release authority:
   - internal `DYNAMIC_IMPORT` provider/budget matrix expansion
   - release-unit audit over the dynamic-import provider/budget matrix release unit
   - full regression gate, local commit creation, and remote push
12. Treat pushed commit `215b6bb` as the prior provider-scoped accounting release authority:
   - provider-scoped selected-unit capability-tier accounting
   - full regression gate over the provider-scoped accounting slice
   - commit-gating and remote push of the provider-scoped accounting release unit
13. Treat pushed commit `a605b22` as the prior capability-tier eval/evidence code/test/pilot release authority:
   - tier-aware eval storage-contract slice
   - isolated internal `DYNAMIC_IMPORT` eval pilot
   - accepted post-pilot planning spike that authorizes the tier-aware internal-accounting rollout boundary
   - accepted tier-aware eval summary/report internal-accounting rollout
   - accepted full-regression gate over the enlarged workspace-only unit
   - accepted commit-gating review over the enlarged workspace-only unit
   - local commit creation for the coherent code/test/pilot release unit
   - remote push of the coherent code/test/pilot release unit
   - docs-only continuity sync in `PLAN.md` and `BUILDLOG.md`
14. Treat the accepted post-`762dd51` planning decision as complete:
   - the next smallest truthful move was to open a third internal runtime-backed eval family now
   - the chosen family was `REFLECTIVE_BUILTIN` / `getattr(obj, name)`
   - the resulting tranche is now implemented, docs/evidence-reconciled, audit-cleared, regression-cleared, commit-gating-cleared, committed locally, and pushed at `c592dca`
15. Treat the accepted post-`c592dca` planning decision as complete:
   - the next smallest truthful move is one eval-only pilot for defaulted `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)`
   - prefer the default-return branch first
   - do not broaden budgets or open a new runtime family first
16. Treat pushed commit `7d43302` as the completed defaulted `getattr(obj, name, default)` default-return branch release:
   - one narrow `EVAL.md` authority correction to the pushed `c592dca` release state
   - one narrow eval-only defaulted `getattr(obj, name, default)` pilot
   - one same-tranche docs/evidence reconciliation in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - no lower-layer runtime-acquisition, analyzer, tool-facade, package-root, MCP, schema, scoring, or winner-selection widening
17. Treat the release-unit audit, full regression gate, commit-gating review, local commit creation, and remote push for `7d43302` as accepted first-pass.
18. Treat the accepted post-`7d43302` planning decision as complete:
   - no concrete defect requires reopening `7d43302`
   - the current defaulted `getattr(obj, name, default)` evidence is explicitly limited to the default-return branch
   - runtime acquisition validation already admits `returned_value` for three-argument `getattr`
   - the next smallest truthful move is one additive internal eval-only sibling value-return branch pilot
19. Treat pushed commit `b014595` as the completed defaulted `getattr(obj, name, default)` value-return branch release:
   - add a sibling value-return fixture/task/run-spec/test set
   - keep the existing default-return probe unchanged
   - keep `1 task x 1 budget x 3 providers`, budget `220`, and the same provider set
   - keep primary truth `unsupported/opaque`
   - keep runtime-backed provenance additive only
   - do not widen package-root APIs, MCP exposure, analyzer/tool-facade behavior, runtime acquisition, schema, scoring, winner selection, public benchmark claims, or public product boundaries
20. Treat the accepted same-tranche docs/evidence reconciliation for `b014595` as pushed release state:
   - in-scope files were `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - it describes the value-return pilot as narrow internal eval-only evidence beside the existing default-return branch
   - it keeps primary truth `unsupported/opaque`
   - it keeps runtime-backed provenance additive only
   - it preserves public-safe quad-matrix comparative boundaries and does not widen public claims, package-root APIs, MCP behavior, runtime acquisition, schema, scoring, winner selection, or product positioning
21. Treat the dedicated read-only release-unit audit over the accumulated value-return branch tranche as accepted first-pass with no findings:
   - include the accepted value-return implementation slice
   - include the accepted same-tranche docs/evidence reconciliation
   - include the current continuity edits in `PLAN.md` and `BUILDLOG.md` as workspace-only continuity state, but do not let the audit edit them
   - no source/runtime-acquisition, analyzer, tool-facade, package-root, MCP, schema, scoring, winner-selection, public-claim, or product-positioning widening was found
22. Treat the full regression gate over the audit-cleared value-return branch tranche as accepted first-pass:
   - `.venv/bin/python -m ruff check src/ tests/` passed
   - `.venv/bin/python -m ruff format --check src/ tests/` passed
   - `.venv/bin/python -m mypy --strict src/` passed
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v` passed with `575 passed`
23. Treat commit-gating over the exact release-unit file set as accepted first-pass:
   - no findings
   - no source, default-return fixture, runtime-acquisition, analyzer, tool-facade, package-root, MCP, schema, scoring, winner-selection, public-claim, or product-positioning widening
   - release-unit files are approved for staging
   - `PLAN.md` and `BUILDLOG.md` remain excluded continuity state
24. Treat local commit creation as accepted first-pass:
   - `b014595 Add defaulted getattr value eval pilot`
   - local `HEAD` is `b014595`
   - `origin/main` is `b014595`
   - `PLAN.md` and `BUILDLOG.md` were kept excluded from the release-unit commit and handled in the post-push continuity sync
25. Treat remote push of `b014595` as accepted first-pass after explicit Ryan authorization.
26. Treat the accepted post-`b014595` runtime-outcome methodology/reporting planning spike as complete:
   - no concrete defect requires reopening `b014595`, `7d43302`, or earlier accepted release units
   - the defaulted `getattr(obj, name, default)` default-return and value-return branches are distinct at fixture/test level
   - current eval summary/report output still collapses both into attached-runtime-provenance counts instead of surfacing normalized runtime outcomes
   - the next smallest truthful implementation slice is internal eval outcome accounting for normalized runtime provenance payload data such as `lookup_outcome=returned_default_value` and `lookup_outcome=returned_value`
   - do not infer outcomes from task IDs or fixture names
   - do not add new fixtures, tasks, run specs, providers, budgets, runtime families, scoring, winner-selection, public APIs, MCP behavior, analyzer behavior, or public claims
27. Treat the accepted runtime-outcome methodology/reporting implementation slice as complete:
   - raw eval records now preserve attached runtime provenance `normalized_payload` fields in `runtime_provenance_records`
   - internal eval summary/report output now renders separate runtime outcome accounting rows for payload key/value counts such as `lookup_outcome=returned_default_value` and `lookup_outcome=returned_value`
   - existing selector-tier, selected-unit-tier, provider, provider+tier, scoring, and winner-selection accounting remains unchanged
   - no runtime-acquisition, analyzer, tool-facade, package-root export, MCP, public-claim, fixture, task, run-spec, provider, budget, or public docs surface changed in this implementation slice
   - targeted control-lane validation passed: ruff, format check, strict mypy over affected source files, focused pytest over affected eval tests, forbidden-surface diff check, and `git diff --check`
   - this acceptance is not commit readiness
28. Treat release-unit audit, full regression, commit-gating, local commit creation, and remote push for the runtime-outcome methodology/reporting hardening release unit as accepted first-pass:
   - dedicated read-only release-unit audit found no issues
   - full regression passed: `.venv/bin/python -m ruff check src/ tests/`, `.venv/bin/python -m ruff format --check src/ tests/`, `.venv/bin/python -m mypy --strict src/`, and `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v` with `578 passed`
   - commit-gating approved exactly eight implementation files and kept `PLAN.md` / `BUILDLOG.md` excluded as continuity state
   - pushed commit `d8ebdc3 Add runtime outcome eval accounting` contains only the approved implementation release-unit files
   - `origin/main` is `d8ebdc3`
29. Treat the post-`d8ebdc3` `getattr` family evidence-broadening planning spike as accepted after 1 control correction:
   - no concrete defect requires reopening `d8ebdc3`, `b014595`, `7d43302`, or earlier accepted release units
   - the control correction fixed `EVAL.md` release-anchor wording so `hasattr(obj, name)` evidence is attributed to `90dcc15` / `762dd51`, while `c592dca` remains only the `getattr(obj, name)` anchor
   - `d8ebdc3` closes the runtime-outcome reporting blocker, so broader existing `getattr` evidence can proceed without another reporting slice first
   - the next smallest truthful implementation slice is to add budget `100` to the three existing `getattr` family run specs, creating `1 task x 2 budgets x 3 providers` for each existing task
   - no new fixture, task, provider, baseline, runtime family, public claim, source runtime acquisition, analyzer/tool-facade behavior, schema, scoring, winner-selection, package-root API, or MCP change is authorized
30. Treat the `getattr` family provider/budget matrix expansion as accepted first-pass in workspace-only state:
   - `oracle_signal_getattr_probe_matrix`, `oracle_signal_getattr_default_probe_matrix`, and `oracle_signal_getattr_default_value_probe_matrix` now use budgets `220` and `100`
   - each existing task is now `1 task x 2 budgets x 3 providers`
   - focused tests double expected selector/runtime-outcome/selected-unit/provider accounting from `3` to `6` where the added budget doubles the matrix
   - JSON validation, focused pytest, ruff over changed Python tests, forbidden-surface diff checks, and `git diff --check` passed
   - no source, fixture, task, provider, baseline, public claim, runtime-acquisition, analyzer/tool-facade, schema, scoring, winner-selection, package-root API, or MCP behavior changed
   - this acceptance is not commit readiness
31. Treat the same-tranche docs/evidence reconciliation for the `getattr` family provider/budget matrix expansion as accepted first-pass in workspace-only state:
   - `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md` record the accepted internal evidence expansion without changing public claim boundaries
   - release-facing docs describe the three existing `getattr` family matrices as `1 task x 2 budgets x 3 providers` at budgets `100` and `220`
   - public-safe quad-matrix comparative wording remains unchanged
   - selector and selected-unit primary truth remain `unsupported/opaque`, and runtime-backed provenance remains additive only
   - no public benchmark, generalized `getattr`, generalized hybrid-runtime, public API, package-root API, MCP, scoring, winner-selection, analyzer/tool-facade, runtime-acquisition, fixture, task, run-spec, or provider widening is claimed
   - this acceptance is not commit readiness
32. Treat the release-unit audit for the accumulated `getattr` family provider/budget matrix expansion tranche as accepted first-pass:
   - the audit reviewed the governing docs, release-facing docs, three changed run specs, and five changed eval tests
   - the audit found no findings
   - the audit confirmed the expected 14-file dirty set, valid JSON run specs with budgets `[220, 100]`, unchanged forbidden surfaces, and focused validation passing with `42 passed`
   - the tranche is now audit-cleared
   - this is not full-regression clearance, commit-gating clearance, commit readiness, or push readiness
33. Treat the full regression gate for the accumulated `getattr` family provider/budget matrix expansion tranche as accepted first-pass:
   - ruff check over `src/` and `tests/` passed
   - ruff format check over `src/` and `tests/` passed with `77 files already formatted`
   - strict mypy over `src/` passed with no issues in 31 source files
   - full pytest passed with `578 passed`
   - the tranche is now audit-cleared and full-regression-cleared
   - this is not commit-gating clearance, commit readiness, local commit creation, or push readiness
34. Treat commit-gating over the exact `getattr` family provider/budget matrix expansion release file set as accepted first-pass:
   - no findings
   - dirty set exactly matches the expected 14-file release set
   - no staged changes were present during the commit-gating review
   - no source, runtime/API/MCP, schema, scoring, provider, fixture, or task files are included
   - the three changed run specs each have one case, budgets `[220, 100]`, and providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
   - release-facing docs preserve public-safe quad-matrix boundaries, narrow internal `getattr` wording, selector and selected-unit `unsupported/opaque` truth, and additive runtime provenance
   - the approved local commit subject is `Expand getattr-family eval matrices`
   - this is not local commit creation or push readiness
35. Treat local commit creation for the `getattr` family provider/budget matrix expansion as accepted first-pass:
   - local commit `1b555ef Expand getattr-family eval matrices` was created on `main`
   - the committed file set matches the approved 14-file release unit
   - the commit body records budgets `100` beside `220`, 1 task x 2 budgets x 3 providers, unsupported/opaque primary truth, additive runtime provenance, and no public/API/MCP/runtime/scoring widening
   - local `HEAD` is `1b555ef`
36. Treat remote push of `1b555ef` as accepted first-pass after explicit Ryan authorization:
   - remote push of `1b555ef` completed
   - `1b555ef` became the pushed `getattr` family eval/test/docs release authority at that release point and is now superseded by later pushed release `ead239d`
   - the prior pushed code/test release authority `d8ebdc3` remains the runtime-outcome accounting anchor
   - this post-push continuity sync in `PLAN.md` and `BUILDLOG.md` records the repo-backed `1b555ef` release state
37. Release sequencing going forward must follow the restored tranche cadence:
   - accumulate multiple accepted slices locally until they form one coherent release unit or are just shy of becoming too large
   - keep continuity synced in workspace during that accumulation
   - run one dedicated findings-first deep release-unit audit over the whole accumulated diff before commit
   - correct audit findings before final regression / commit-gating / commit / push
   - do not return to per-slice commit/push churn without explicit reason and explicit Ryan sign-off
38. The next lane must not reopen:
   - the accepted pushed `c592dca` `getattr(obj, name)` release unit
   - the accepted pushed `7d43302` defaulted `getattr(obj, name, default)` release unit
   - the accepted `EVAL.md` authority correction released in `7d43302`
   - the accepted defaulted `getattr(obj, name, default)` default-return eval pilot slice released in `7d43302`
   - the accepted same-tranche docs/evidence reconciliation slice released in `7d43302`
   - the accepted pushed `b014595` defaulted `getattr(obj, name, default)` value-return branch release unit
   - the accepted same-tranche docs/evidence reconciliation for the value-return branch in `b014595`
   - the accepted `hasattr` provider/budget matrix release unit at `762dd51`
   - the accepted docs-only continuity/process correction commit at `8133e0a`
   - the accepted docs-only runtime-backed evidence/claim reconciliation commit at `3291268`
   - the accepted internal `hasattr(obj, name)` runtime-backed eval pilot release unit at `90dcc15`
   - the accepted code/test/pilot release unit at `a605b22`
   - the accepted provider-scoped accounting release unit at `215b6bb`
   - the accepted internal dynamic-import provider/budget matrix release unit at `9a52b46`
   - public claim boundaries
   - package-root/public low-level runtime-observation exposure
   - MCP runtime-observation exposure
   - further inherited-call work
   - scoring, winner selection, tasks, fixtures, providers, docs, public surfaces, or runtime-acquisition breadth
   - any run spec unless a later control-reviewed eval pilot explicitly authorizes it
39. Keep `context_ir.tool_facade` as the highest exposed hybrid entry point, keep package-root/public low-level plus MCP runtime-observation widening on explicit hold, and keep public claim boundaries unchanged.
40. Maintain the accepted hold on further inherited-call reopening beyond the accepted first-exclusive-branch overlap boundary.

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

- The accepted pushed `d73cde4` `DYNAMIC_IMPORT` original budget-pressure
  release unit, or any docs review, release-unit audit, focused validation,
  full regression, commit-gating, staging, local commit creation, or push route
  for it, unless a later findings-based review proves a concrete defect
- The accepted pushed `e2f3dcf` zero-argument `dir()` plus
  `METACLASS_BEHAVIOR` budget-pressure release unit, or any docs review,
  release-unit audit, full regression, commit-gating, staging, local commit
  creation, or push route for it, unless a later findings-based review proves a
  concrete defect
- The accepted pushed `21f2dc5` `EXEC_OR_EVAL` eval/exec budget-pressure
  release unit, or any docs review, release-unit audit, full regression,
  commit-gating, staging, local commit creation, or push route for it, unless
  a later findings-based review proves a concrete defect
- The accepted pushed `c2c1898` `DYNAMIC_IMPORT` sibling budget-pressure
  release unit unless a later findings-based review proves a concrete defect
- The accepted pushed `b8e126e` `RUNTIME_MUTATION` / `delattr(obj, name)` and
  `setattr(obj, name, value)` budget-pressure expansion release unit unless a
  later findings-based review proves a concrete defect
- The accepted pushed `125f088` tranche batching / throughput discipline
  process-doc release unit unless a later findings-based review proves a
  concrete defect
- The accepted pushed `ad9db8d` `REFLECTIVE_BUILTIN` / `dir(obj)`
  budget-pressure expansion release unit unless a later findings-based review
  proves a concrete defect
- The accepted pushed `43d0439` `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` budget-pressure expansion
  release unit unless a later findings-based review proves a concrete defect
- The accepted pushed `ee71a82` `DYNAMIC_IMPORT` / imported-name
  `import_module(name)` runtime eval pilot release unit unless a later
  findings-based review proves a concrete defect
- The accepted pushed `397c7dd` `DYNAMIC_IMPORT` / builtin
  `__import__(name)` runtime eval pilot release unit unless a later
  findings-based review proves a concrete defect
- The accepted pushed `bcd6d68` `EXEC_OR_EVAL` / `exec(source)` release unit
  unless a later findings-based review proves a concrete defect
- The accepted pushed `96fc03a` `EXEC_OR_EVAL` / `eval(source)` release unit
  unless a later findings-based review proves a concrete defect
- The accepted pushed `19d9a32` `METACLASS_BEHAVIOR` / preserved
  `metaclass=...` keyword-site release unit unless a later findings-based
  review proves a concrete defect
- The accepted pushed `14b362e` `DYNAMIC_IMPORT` / root-module
  `importlib.import_module(name)` runtime eval pilot release unit unless a
  later findings-based review proves a concrete defect
- The accepted pushed `ad22ea6` dynamic-import root release-routing continuity
  sync unless a later findings-based review proves a concrete defect
- The accepted pushed `c592dca` `REFLECTIVE_BUILTIN` / `getattr(obj, name)` release unit unless a later findings-based review proves a concrete defect
- The accepted pushed `7d43302` defaulted `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` release unit unless a later findings-based review proves a concrete defect
- The accepted `EVAL.md` authority correction released in `7d43302` unless a later findings-based review proves a concrete defect
- The accepted defaulted `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` default-return eval pilot slice released in `7d43302` unless a later findings-based review proves a concrete defect
- The accepted same-tranche docs/evidence reconciliation for defaulted `getattr(obj, name, default)` released in `7d43302` unless a later findings-based review proves a concrete defect
- The accepted pushed `b014595` defaulted `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` value-return branch release unit unless a later findings-based review proves a concrete defect
- The accepted same-tranche docs/evidence reconciliation for the defaulted `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` value-return branch in `b014595` unless a later findings-based review proves a concrete defect
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
