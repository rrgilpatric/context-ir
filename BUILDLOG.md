# BUILDLOG.md -- Decision Log

Most recent supersession entries override older architectural decisions when they explicitly say so. Older entries remain intact below as history.

## 2026-04-23 -- Docs-Only Continuity Sync After Provider-Scoped Push

- Reviewed the docs-only continuity sync after the provider-scoped selected-unit capability-tier accounting release was pushed to `origin/main` at `215b6bb`
- Verified before local docs-only commit creation:
  - branch `main`
  - local `HEAD` `215b6bb`
  - `origin/main` `215b6bb`
  - modified files are limited to continuity docs:
    - `PLAN.md`
    - `BUILDLOG.md`
  - `git diff --check` reported no issues
- Continuity state captured:
  - `215b6bb` is now the latest pushed repo-backed code/test release unit
  - the provider-scoped selected-unit capability-tier accounting slice is released state, not workspace-only implementation state
  - no implementation, exposure, schema, scoring, public-claim, package-root, MCP, runtime-acquisition, or inherited-call boundary was widened by this docs-only sync
  - after this sync, further push or new planning/implementation work remains held for explicit Ryan authorization
- Acceptance decision:
  - accept the docs-only continuity sync first-pass
  - commit only `PLAN.md` and `BUILDLOG.md` locally
  - do not push the docs-only commit without later explicit authorization
- Acceptance status: first-pass

## 2026-04-23 -- Remote Push For Provider-Scoped Accounting

- Pushed the accepted provider-scoped selected-unit capability-tier accounting release unit to `origin/main`
- Verified before push:
  - branch `main`
  - local `HEAD` `215b6bb`
  - `origin/main` `d1265fe`
  - the remote advance included the accepted docs-only continuity correction `cb6c14f` plus the accepted code/test release candidate `215b6bb`
  - Ryan explicitly authorized pushing that two-commit sequence
- Push result:
  - `main` advanced from `d1265fe` to `215b6bb`
- Verified after push:
  - local `HEAD` `215b6bb`
  - `origin/main` `215b6bb`
  - remaining local changes are continuity-only:
    - `PLAN.md`
    - `BUILDLOG.md`
- Acceptance decision:
  - accept the remote push first-pass
  - `215b6bb` is now the latest pushed repo-backed code/test release unit
  - next control action is docs-only continuity sync commit review, then hold for explicit authorization before any further push or new lane
- Acceptance status: first-pass

## 2026-04-23 -- Commit-Gating And Local Commit For Provider-Scoped Accounting

- Reviewed the accepted provider-scoped selected-unit capability-tier accounting slice for commit gating after the full regression gate
- Verified before local commit:
  - dirty implementation files were limited to:
    - `src/context_ir/eval_summary.py`
    - `tests/test_eval_summary.py`
    - `tests/test_eval_report.py`
    - `tests/test_eval_signal_dynamic_import_probe.py`
  - dirty continuity files were separate:
    - `PLAN.md`
    - `BUILDLOG.md`
  - no untracked files were present
  - `git diff --check` reported no issues
  - staged release unit contained only the four implementation/test files above
  - `git diff --cached --check` reported no issues
- Created local commit:
  - `215b6bb` -- `Add provider-scoped eval tier accounting`
- Post-commit state:
  - local `HEAD` `215b6bb`
  - `origin/main` `d1265fe`
  - `PLAN.md` and `BUILDLOG.md` remain uncommitted continuity-only local changes
- Acceptance decision:
  - accept commit-gating review and local commit creation first-pass
  - `215b6bb` is the current unpushed local code/test release candidate for provider-scoped selected-unit capability-tier accounting
  - push remains a later human-gated action
- Acceptance status: first-pass

## 2026-04-23 -- Full Regression Gate For Provider-Scoped Capability-Tier Accounting

- Ran the full regression gate after accepting the provider-scoped selected-unit capability-tier accounting slice
- Validation passed:
  - `.venv/bin/python -m ruff check src/ tests/`
  - result: passed
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - result: `73 files already formatted`
  - `.venv/bin/python -m mypy --strict src/`
  - result: `Success: no issues found in 31 source files`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
  - result: `539 passed, 1 deselected`
- Acceptance decision:
  - accept the full regression gate first-pass
  - the accepted workspace-only provider-scoped accounting slice may advance to commit-gating review
  - no public claim, package-root, MCP, schema, scoring, winner-selection, task, run-spec, fixture, provider, oracle, runtime-acquisition, or inherited-call boundary is widened
- Acceptance status: first-pass

## 2026-04-23 -- Provider-Scoped Capability-Tier Accounting Implementation Review

- Reviewed the returned bounded implementation slice for provider-scoped selected-unit capability-tier accounting in the internal eval summary/report path
- Verified live state before review:
  - branch `main`
  - local `HEAD` `cb6c14f`
  - `origin/main` `d1265fe`
  - latest code/test/pilot release unit remains `a605b22`
  - pre-existing continuity changes were present in:
    - `PLAN.md`
    - `BUILDLOG.md`
  - implementation changes were present in:
    - `src/context_ir/eval_summary.py`
    - `tests/test_eval_summary.py`
    - `tests/test_eval_report.py`
    - `tests/test_eval_signal_dynamic_import_probe.py`
- Control review found no issues
- Accepted behavior:
  - provider-scoped selected-unit totals now include per-provider selected-unit count and attached-runtime-provenance count
  - provider plus actual-primary-tier totals now include selected-unit count and attached-runtime-provenance count
  - existing scalar provider aggregates, task-budget rows, and ledger-wide capability-tier tables remain intact
  - legacy/scalar-only ledgers still render deterministic zero or empty provider-tier accounting without loader failure
  - runtime-backed evidence remains additive and is not rendered as a primary selected-unit tier
  - no raw schema/spec-version, scoring, winner-selection, run-spec, task, fixture, provider, oracle, runtime-acquisition, analyzer, tool-facade, package-root, MCP, public-claim, or continuity-doc change was made by the execution slice
- Control-lane validation passed:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_summary.py tests/test_eval_report.py tests/test_eval_signal_dynamic_import_probe.py -q`
  - result: `30 passed`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_summary.py tests/test_eval_report.py tests/test_eval_pipeline.py tests/test_eval_bundle.py tests/test_eval_signal_dynamic_import_probe.py -q`
  - result: `39 passed`
  - `.venv/bin/python -m ruff check src/context_ir/eval_summary.py tests/test_eval_summary.py tests/test_eval_report.py tests/test_eval_signal_dynamic_import_probe.py`
  - result: passed
  - `.venv/bin/python -m ruff format --check src/context_ir/eval_summary.py tests/test_eval_summary.py tests/test_eval_report.py tests/test_eval_signal_dynamic_import_probe.py`
  - result: passed
  - `.venv/bin/python -m mypy --strict src/context_ir/eval_summary.py src/context_ir/eval_report.py`
  - result: passed
- Acceptance decision:
  - accept the provider-scoped selected-unit capability-tier accounting implementation first-pass
  - next control action is the full regression gate before commit sequencing
- Acceptance status: first-pass

## 2026-04-23 -- Provider-Scoped Capability-Tier Accounting Planning Spike Review

- Reviewed the returned bounded planning spike for the next capability-tier program slice after the released eval/evidence baseline
- Verified from live repo state:
  - branch `main`
  - local `HEAD` `cb6c14f`
  - `origin/main` `d1265fe`
  - worktree was clean before this continuity update
  - local commits ahead of origin were docs-only:
    - `PLAN.md`
    - `BUILDLOG.md`
  - latest code/test/pilot release unit remains `a605b22`
- Control review found no issues
- Acceptance decision:
  - accept the planning spike first-pass
  - authorize one bounded implementation slice for provider-scoped selected-unit capability-tier accounting in `src/context_ir/eval_summary.py` and targeted tests
  - do not broaden eval matrices, add another runtime-backed pilot, update public claims, widen package-root or MCP runtime-observation exposure, or reopen inherited-call work first
- Reasoning:
  - current internal accounting already consumes raw selector expectation and selected-unit capability-tier fields, but selected-unit tier/provenance accounting is ledger-wide rather than provider-scoped
  - provider-scoped accounting is the smallest truthful consumer hardening step before broader internal evidence comparisons across providers, budgets, or baselines
  - the proposed slice uses existing raw ledger fields and preserves schema, scoring, winner selection, public claims, and exposure holds
- Acceptance status: first-pass

## 2026-04-23 -- Docs-Only Continuity Push Completion Correction

- Corrected continuity wording after the docs-only continuity push completed
- Verified live state before this correction:
  - branch `main`
  - local `HEAD` `d1265fe`
  - `origin/main` `d1265fe`
  - worktree clean
  - commit `d1265fe` touched only:
    - `PLAN.md`
    - `BUILDLOG.md`
- Preserved release-state distinction:
  - `a605b22` remains the latest code/test/pilot release unit
  - docs-only continuity commits after `a605b22`, including `d1265fe`, are continuity state and not implementation release changes
  - public claims, exposure boundaries, schema, scoring, and eval implementation remain unchanged by this correction
- Acceptance decision:
  - accept this docs-only continuity correction
  - the next substantive move is one bounded planning spike to choose the next capability-tier program slice after the released eval/evidence baseline
- Acceptance status: first-pass

## 2026-04-23 -- Docs-Only Continuity Push Authorization

- Ryan authorized pushing the docs-only continuity commits after the capability-tier eval / evidence code/test/pilot release was already pushed at `a605b22`
- Pre-push verification before this entry:
  - branch `main`
  - local `HEAD` `8df45aa`
  - `origin/main` `a605b22`
  - worktree clean
  - commits ahead of `origin/main` touched only:
    - `PLAN.md`
    - `BUILDLOG.md`
- Corrected the live continuity wording before push so it remains true after the docs-only commits advance the branch tip:
  - the code/test/pilot release unit remains `a605b22`
  - commits after `a605b22` in this continuity chain are docs-only continuity commits
  - those docs-only commits do not widen implementation, exposure, schema, scoring, or public-claim boundaries
- Acceptance decision:
  - accept the docs-only continuity push authorization
  - push only docs-only commits whose diff is limited to `PLAN.md` and `BUILDLOG.md`
  - after that push, hold before any new implementation or planning lane until Ryan explicitly authorizes it
- Acceptance status: first-pass

## 2026-04-23 -- Docs-Only Continuity Local-Head Wording Correction

- Corrected `PLAN.md` after local docs-only commit creation so the current release-state section does not pin local `HEAD` to the code/test/pilot release hash `a605b22`
- Preserved the authoritative distinction:
  - `origin/main` at `a605b22` is the latest pushed repo-backed code/test/pilot release state
  - local `HEAD` may be ahead of `origin/main` by docs-only continuity commits
  - docs-only continuity commits do not widen implementation, exposure, schema, scoring, or public-claim boundaries
- Acceptance decision:
  - accept the docs-only continuity sync after this wording correction
  - do not push docs-only continuity commits without later explicit authorization
- Acceptance status: 1 correction

## 2026-04-23 -- Docs-Only Continuity Sync Review

- Reviewed the docs-only continuity sync after the accepted capability-tier eval / evidence unit was pushed to `origin/main` at `a605b22`
- Verified before local docs-only commit creation:
  - branch `main`
  - local `HEAD` `a605b22`
  - `origin/main` `a605b22`
  - modified files are limited to continuity docs:
    - `PLAN.md`
    - `BUILDLOG.md`
  - `git diff --check` reported no issues
- Continuity state captured:
  - `a605b22` is now the latest pushed repo-backed released unit
  - the prior runtime-backed tranche at `cb1dc65` remains historical released state
  - the docs-only sync is separate from the code/test/pilot release unit and does not widen implementation, exposure, schema, scoring, or public-claim boundaries
  - the next move after this sync remains held for Ryan's explicit authorization before any docs-only push or new implementation/planning lane
- Acceptance decision:
  - accept the docs-only continuity sync after the local-head wording correction
  - commit only `PLAN.md` and `BUILDLOG.md` locally
  - do not push the docs-only commit without later explicit authorization
- Acceptance status: 1 correction

## 2026-04-23 -- Remote Push For Capability-Tier Eval/Evidence Unit

- Performed bounded remote-state verification and pushed local commit `a605b22` to `origin/main`
- Verified before push:
  - branch `main`
  - local `HEAD` `a605b22`
  - `origin/main` `cb1dc65`
  - unstaged files were limited to continuity docs:
    - `PLAN.md`
    - `BUILDLOG.md`
- Push result:
  - `main` advanced from `cb1dc65` to `a605b22`
- Verified after push:
  - local `HEAD` `a605b22`
  - `origin/main` `a605b22`
  - `PLAN.md` and `BUILDLOG.md` remain uncommitted continuity-only local changes
- Acceptance decision:
  - accept remote push first-pass
  - `a605b22` is now the latest pushed repo-backed released unit
  - `cb1dc65` remains historical released state for the runtime-backed tranche
  - no further push is authorized for the local docs-only continuity changes
- Reasoning:
  - the pushed commit had already cleared the full regression gate and commit-gating review
  - the push preserved the separation between the code/test/pilot release unit and post-push continuity wording
- Acceptance status: first-pass

## 2026-04-23 -- Local Commit Creation For Capability-Tier Eval/Evidence Unit

- Created local commit `a605b22` on `main` for the accepted capability-tier eval / evidence release unit
- Verified before commit:
  - branch `main`
  - local `HEAD` `cb1dc65`
  - `origin/main` `cb1dc65`
  - staged file set matched the accepted commit-gating release unit exactly
  - unstaged files were limited to continuity docs:
    - `PLAN.md`
    - `BUILDLOG.md`
  - `git diff --cached --check` reported no issues
- Committed release-unit files:
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
- Post-commit release state:
  - local `HEAD` `a605b22`
  - `origin/main` `cb1dc65`
  - `PLAN.md` and `BUILDLOG.md` remain uncommitted continuity-only local changes
  - no push was performed
- Acceptance decision:
  - accept local commit creation first-pass
  - keep `cb1dc65` as the latest pushed repo-backed released unit until a later explicit push authorization
  - keep local commit `a605b22` as the current unpushed local release candidate
  - push remains a later human-gated action
- Reasoning:
  - the commit contains only the previously accepted code/test/pilot release unit, preserving the separation between release contents and continuity wording
  - remote release state remains explicit because local commit creation and pushing are separate gates
- Acceptance status: first-pass

## 2026-04-22 -- Commit-Gating Review For Workspace-Only Eval/Evidence Unit

- Reviewed the current workspace-only diff against repo-backed state `cb1dc65` for commit gating after the accepted full-regression gate
- Verified from fresh control-lane inspection:
  - repo-backed released state remains explicit and unchanged:
    - branch `main`
    - local `HEAD` `cb1dc65`
    - `origin/main` `cb1dc65`
  - the exact coherent local release unit is clean by file boundary:
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
  - `PLAN.md` and `BUILDLOG.md` remain separate continuity-sync-only local files and are not part of that release unit
  - diff hygiene is clean:
    - `git diff --check` reported no issues
  - the accepted full-regression gate remains the current validation basis for this exact local release unit:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
    - pytest result: `538 passed, 1 deselected`
- Control review found no issues
- Acceptance decision:
  - accept the commit-gating review
  - the code/test/pilot file set above is the exact coherent local release unit for the current workspace-only eval/evidence milestone
  - `PLAN.md` and `BUILDLOG.md` remain unstaged continuity-sync-only changes after any later local commit creation
  - repo-backed release state remains unchanged at `cb1dc65`
  - push remains a later human-gated action
- Reasoning:
  - the accepted storage-contract slice, isolated pilot, and internal-accounting rollout form one coherent local code/test/eval release unit
  - keeping `PLAN.md` and `BUILDLOG.md` separate preserves the same release-state discipline used for the earlier runtime-backed tranche by distinguishing code/test release contents from later continuity wording
- Acceptance status: first-pass

## 2026-04-22 -- Full Regression Gate For Workspace-Only Eval/Evidence Unit

- Reviewed the bounded full-regression gate for the enlarged workspace-only eval/evidence unit after the accepted tier-aware internal-accounting rollout and the narrow lint correction
- Verified from fresh control-lane inspection:
  - repo-backed released state remains explicit and unchanged:
    - branch `main`
    - local `HEAD` `cb1dc65`
    - `origin/main` `cb1dc65`
  - workspace-only accepted state under review remained the enlarged eval/evidence unit:
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
    - `evals/fixtures/oracle_signal_dynamic_import_probe/`
    - `evals/tasks/oracle_signal_dynamic_import_probe.json`
    - `evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json`
    - `tests/test_eval_signal_dynamic_import_probe.py`
    - `PLAN.md`
    - `BUILDLOG.md`
  - full validation passed on the current workspace:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
    - pytest result: `538 passed, 1 deselected`
- Control review found no issues
- Acceptance decision:
  - accept the bounded full-regression gate
  - the enlarged workspace-only eval/evidence unit is locally clean and may advance to commit-gating review
  - repo-backed release state remains unchanged at `cb1dc65`
  - commit and push remain later control actions only
- Reasoning:
  - the only earlier regression-gate finding was the narrow import-order lint issue in `src/context_ir/eval_summary.py`, and that defect is now closed
  - the clean full gate confirms the storage-contract slice, isolated pilot, and tier-aware internal-accounting rollout coexist without lint, format, type, or non-slow test regressions
- Acceptance status: first-pass

## 2026-04-22 -- Tier-Aware Internal-Accounting Rollout Review

- Reviewed the returned bounded implementation slice for tier-aware internal accounting in the eval summary/report path, plus one bounded correction slice for v1 summary-loader compatibility
- Verified from fresh control-lane inspection:
  - repo-backed released state remains explicit and unchanged:
    - branch `main`
    - local `HEAD` `cb1dc65`
    - `origin/main` `cb1dc65`
  - workspace-only accepted state before this review remained:
    - `src/context_ir/eval_oracles.py`
    - `src/context_ir/eval_providers.py`
    - `src/context_ir/eval_results.py`
    - `tests/test_eval_oracles.py`
    - `tests/test_eval_providers.py`
    - `tests/test_eval_results.py`
    - `tests/test_eval_runs.py`
    - `evals/fixtures/oracle_signal_dynamic_import_probe/`
    - `evals/tasks/oracle_signal_dynamic_import_probe.json`
    - `evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json`
    - `tests/test_eval_signal_dynamic_import_probe.py`
    - `PLAN.md`
    - `BUILDLOG.md`
  - the summary/report consumer path now adds separate internal accounting for:
    - declared selector primary-tier expectations and satisfaction counts
    - declared selector attached-runtime-provenance expectations and satisfaction counts
    - selected-unit primary-tier counts plus attached-runtime-provenance counts
  - legacy scalar summary/report behavior remains intact:
    - provider aggregates still consume the existing scalar metrics
    - task-budget results and winner selection still depend on the existing aggregate score path
    - no schema/spec-version bump, public-claim widening, package-root widening, or MCP widening occurred
  - the reviewed compatibility finding is closed:
    - `load_eval_ledger()` no longer requires `provider_metadata`, `resolved_selectors`, or `provider_metadata.selected_units` on every consumed row
    - legacy scalar-only ledger rows now load, summarize, and render deterministic empty capability-tier accounting sections
  - targeted and adjacent validation passed on the current corrected workspace:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_summary.py tests/test_eval_report.py tests/test_eval_signal_dynamic_import_probe.py -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_summary.py tests/test_eval_report.py tests/test_eval_pipeline.py tests/test_eval_bundle.py tests/test_eval_signal_dynamic_import_probe.py -q`
- Control review found no issues after the correction
- Acceptance decision:
  - accept the tier-aware internal-accounting rollout after 1 correction
  - the accepted workspace-only file set now additionally includes:
    - `src/context_ir/eval_summary.py`
    - `tests/test_eval_summary.py`
    - `tests/test_eval_report.py`
    - `tests/test_eval_signal_dynamic_import_probe.py`
  - commit-gating review, commit, and push remain later control actions only
- Reasoning:
  - the rollout now consumes already-accepted raw fields without mutating the durable v1 ledger contract
  - the accepted isolated `DYNAMIC_IMPORT` pilot is now visible in internal accounting while public claim boundaries and exposure holds remain unchanged
  - the compatibility correction keeps the accounting additive by treating absent tier-aware data as empty internal accounting rather than as a loader failure
- Acceptance status: 1 correction

## 2026-04-22 -- Post-Pilot Capability-Tier Eval Planning Spike Review

- Reviewed the returned bounded planning spike for the next capability-tier eval slice after the accepted isolated internal `DYNAMIC_IMPORT` eval pilot
- Verified from fresh control-lane inspection:
  - repo-backed released state remains explicit and unchanged:
    - branch `main`
    - local `HEAD` `cb1dc65`
    - `origin/main` `cb1dc65`
  - workspace-only accepted state remains explicit and unchanged before this continuity sync:
    - `src/context_ir/eval_oracles.py`
    - `src/context_ir/eval_providers.py`
    - `src/context_ir/eval_results.py`
    - `tests/test_eval_oracles.py`
    - `tests/test_eval_providers.py`
    - `tests/test_eval_results.py`
    - `tests/test_eval_runs.py`
    - `evals/fixtures/oracle_signal_dynamic_import_probe/`
    - `evals/tasks/oracle_signal_dynamic_import_probe.json`
    - `evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json`
    - `tests/test_eval_signal_dynamic_import_probe.py`
    - `PLAN.md`
    - `BUILDLOG.md`
  - the raw eval path already carries capability-tier and attached-runtime-provenance expectation/result fields end to end without widening public claims:
    - durable oracle selectors can declare `expected_primary_capability_tier` and `expect_attached_runtime_provenance`
    - resolved selectors and provider-selected units retain `primary_capability_tier`, `has_attached_runtime_provenance`, and `attached_runtime_provenance_record_ids`
    - raw eval records persist those fields through summary-input ledger rows
  - the current consumer gap is in the internal summary/report layer:
    - `src/context_ir/eval_summary.py` still loads and renders legacy scalar metrics only
    - `src/context_ir/eval_report.py` remains a thin composition wrapper around that legacy summary/render path
  - the accepted isolated internal pilot proves the intended additive-runtime shape:
    - the unsupported `DYNAMIC_IMPORT` selector carries expected primary tier `unsupported/opaque` with attached runtime provenance expectation
    - the isolated pilot test path verifies non-null attached runtime provenance survives oracle resolution and raw run execution
- Control review found no issues
- Acceptance decision:
  - accept the planning spike
  - the next authorized implementation boundary is one bounded tier-aware internal-accounting rollout in the eval summary/report path using the already-stored raw selector and selected-unit fields
  - keep legacy scalar scoring, winner selection, schema/spec version, public claims, and exposure boundaries unchanged in that slice
  - do not authorize another isolated runtime-backed pilot before the first consumer exists
  - commit-gating review, commit, and push remain later control actions only
- Reasoning:
  - `EVAL.md` already requires separate capability-tier accounting before stronger hybrid-analysis or public capability-tier claims are allowed
  - the accepted storage-contract slice and isolated pilot make the new fields durable, but the current summary/report path still leaves them unusable for internal accounting
  - consuming the existing raw fields is the smallest truthful next move because it makes the accepted pilot visible without broadening claims, changing scoring, or widening runtime-observation exposure
- Acceptance status: first-pass

## 2026-04-22 -- Capability-Tier Eval Continuity Sync

- Synced `PLAN.md` and `BUILDLOG.md` to the current accepted workspace authority beyond the repo-backed released state at `cb1dc65`
- Verified from current workspace inspection:
  - branch `main`, local `HEAD`, and `origin/main` all point to `cb1dc65`
  - the accepted runtime-backed tranche remains the latest repo-backed released state
  - the current workspace-only milestone is the capability-tier eval / evidence baseline
  - accepted control decisions are now durably recorded in order:
    1. tier-aware eval storage-contract slice in:
       - `src/context_ir/eval_oracles.py`
       - `src/context_ir/eval_providers.py`
       - `src/context_ir/eval_results.py`
       - `tests/test_eval_oracles.py`
       - `tests/test_eval_providers.py`
       - `tests/test_eval_results.py`
       - `tests/test_eval_runs.py`
       - resolved selectors, provider-selected units, and raw eval ledger/provider metadata now carry primary capability-tier and attached-runtime-provenance expectation/result fields without widening public claims
    2. isolated internal `DYNAMIC_IMPORT` eval pilot in:
       - `src/context_ir/eval_oracles.py`
       - `src/context_ir/eval_providers.py`
       - `evals/fixtures/oracle_signal_dynamic_import_probe/`
       - `evals/tasks/oracle_signal_dynamic_import_probe.json`
       - `evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json`
       - `tests/test_eval_oracles.py`
       - `tests/test_eval_providers.py`
       - `tests/test_eval_runs.py`
       - `tests/test_eval_signal_dynamic_import_probe.py`
       - one internal-only fixture/task/run-spec/test path now expects an unsupported primary tier with attached runtime provenance and verifies those fields survive oracle resolution and raw run execution
  - this docs-only continuity sync remains the local-only documentation state:
    - `PLAN.md`
    - `BUILDLOG.md`
- Continuity routing is now explicit:
  - repo-backed released state remains `cb1dc65` on `main` / `origin/main`
  - current workspace-only authority is the capability-tier eval / evidence baseline milestone
  - the next substantive move is one bounded planning spike for the next capability-tier eval slice after the isolated internal `DYNAMIC_IMPORT` eval pilot
  - commit-gating review, commit, and push remain later control actions only
  - `context_ir.tool_facade` remains the highest exposed hybrid entry point, package-root/public low-level plus MCP runtime-observation widening remain on hold, and public claim boundaries remain unchanged
- Acceptance status: first-pass

## 2026-04-21 -- Post-Push Continuity Sync

- Synced `PLAN.md` and `BUILDLOG.md` to the already-pushed repo state at `cb1dc65`
- Verified from current workspace inspection:
  - branch `main`, local `HEAD`, and `origin/main` all point to `cb1dc65`
  - the bounded runtime-backed code/test tranche is repo-backed released state
  - the only remaining local-only workspace state is this docs-only continuity-sync unit:
    - `PLAN.md`
    - `BUILDLOG.md`
- Continuity routing is now explicit:
  - `PLAN.md` routes the next substantive move to one bounded planning spike for the next milestone
  - completed runtime-backed tranche work is no longer described as workspace-only in the live routing sections
  - accepted package-root/public low-level, MCP, and further inherited-call holds remain explicit
- Acceptance status: first-pass

## 2026-04-21 -- Runtime-Backed Tranche Push Review

- Reviewed the post-push repo state after Ryan explicitly authorized pushing the accepted local release unit
- Verified from fresh control-lane inspection:
  - local `HEAD` remains `cb1dc65`
  - `origin/main` now also points to `cb1dc65`
  - the accepted code/test runtime-backed tranche is now repo-backed released state rather than a local-only commit
  - remaining local workspace changes are continuity-sync only:
    - `PLAN.md`
    - `BUILDLOG.md`
- Control review found no issues
- Acceptance decision:
  - accept the push step
  - `cb1dc65` is now the latest repo-backed released unit on `origin/main`
  - the next control action is continuity preservation only; do not reopen the completed runtime-backed tranche unless a later findings-based review proves a concrete defect
- Reasoning:
  - the previously accepted code/test release unit was already clean at commit-gating review and full validation, so Ryan's explicit authorization correctly advanced the remote release state from `cdbff24` to `cb1dc65`
  - keeping the follow-on continuity sync local-only for now preserves explicit release-state discipline by distinguishing the pushed code/test unit from later documentation-only state
- Acceptance status: first-pass

## 2026-04-21 -- Commit-Gating Review And Local Commit

- Reviewed the current workspace-only diff against `cdbff24` for commit gating after the accepted deep-audit pass and audit-fix correction slice
- Verified from fresh control-lane inspection:
  - exact workspace split was clean by file boundary:
    - seven source/test files formed the coherent release unit
    - `PLAN.md` and `BUILDLOG.md` remained separate continuity-sync-only files
  - `git diff --check cdbff24 --` found no diff hygiene issues
  - the accepted audit findings were closed before the commit decision
  - full validation remained green on the combined workspace:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
- Control review found no issues
- Acceptance decision:
  - accept the commit-gating review
  - the exact coherent local release unit is:
    - `src/context_ir/analyzer.py`
    - `src/context_ir/runtime_acquisition.py`
    - `src/context_ir/tool_facade.py`
    - `tests/test_analyzer.py`
    - `tests/test_dependency_frontier.py`
    - `tests/test_runtime_acquisition.py`
    - `tests/test_tool_facade.py`
  - created one coherent local commit on `main`:
    - `cb1dc65` — `Complete bounded runtime-backed provenance tranche`
  - `origin/main` remains at `cdbff24`
  - `PLAN.md` and `BUILDLOG.md` remain unstaged continuity-sync-only changes after the local commit
  - push remains explicitly pending Ryan's authorization
- Reasoning:
  - the source/test tranche is a coherent release unit on its own because the runtime-backed seam work and targeted coverage live entirely inside those seven files, while continuity docs should remain separate so repo-backed release-state wording does not get blurred into the code commit
  - no findings remained after commit-gating review, so local commit creation was the correct next control move while keeping the irreversible push step behind the human sign-off gate
- Acceptance status: first-pass

## 2026-04-21 -- Deep-Audit Correction Slice Review

- Reviewed the returned correction slice for the accepted deep-audit findings only
- Verified from fresh control-lane inspection:
  - repo-backed release state remains explicit and unchanged:
    - current branch is `main`
    - `HEAD` is `cdbff24`
    - `origin/main` is `cdbff24`
  - `PLAN.md` no longer contradicts current workspace reality:
    - current phase now states that repo-backed released state remains `cdbff24` while the larger accepted workspace-only diff is the active commit-gating subject
    - the stale claim that `METACLASS_BEHAVIOR` was still the highest-ranked remaining runtime-backed family is removed
    - plan routing now points forward to commit-gating review rather than backward to pre-implementation planning
  - `tests/test_runtime_acquisition.py` now covers the cited negative branches:
    - wrong-arity and shadowed same-name negatives for `globals()`, `locals()`, and `dir()`
    - missing discriminator-key rejection for `globals()` `lookup_outcome`
    - missing discriminator-key rejection for `locals()` `lookup_outcome`
    - missing discriminator-key rejection for `setattr(...)` `mutation_outcome`
    - missing discriminator-key rejection for `METACLASS_BEHAVIOR` `class_creation_outcome`
  - no source changes were required in `runtime_acquisition.py`; the new tests passed against the accepted existing implementation
- Control review found no issues
- Validation/discovery confirmed:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -q`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
- Acceptance decision:
  - accept the correction slice
  - the accepted deep-audit findings are now closed in workspace authority
  - the next control action is commit-gating review on the current workspace-only diff against `cdbff24`
- Reasoning:
  - the slice corrects the active continuity contradiction and adds the exact missing negative coverage without reopening broader contracts, widening exposure, or modifying accepted source seams
  - the full repo gate stays green after the correction, so the workspace is ready to move from audit-fix closure into commit-gating review
- Acceptance status: first-pass

## 2026-04-21 -- Metaclass Behavior Runtime-Backed Implementation Review

- Reviewed the returned implementation slice for bounded additive runtime-backed attachment on existing unsupported `METACLASS_BEHAVIOR` keyword-site findings only
- Verified from fresh control-lane inspection:
  - repo-backed release state remains explicit and unchanged:
    - current branch is `main`
    - `HEAD` is `cdbff24`
    - `origin/main` is `cdbff24`
  - `runtime_acquisition.py` now exposes one bounded family-level seam:
    - `MetaclassBehaviorRuntimeObservation`
    - `attach_metaclass_behavior_runtime_provenance(...)`
  - eligible attachment is limited to existing unsupported `METACLASS_BEHAVIOR` constructs matched to preserved `MetaclassKeywordFact` keyword sites rather than nested call or attribute subexpressions
  - the bounded payload contract requires `normalized_payload.class_creation_outcome == "created_class"` and a non-empty `durable_payload_reference`
  - optional additional normalized payload fields remain additive only
  - analyzer/tool-facade exposure stays bounded to:
    - `metaclass_behavior_runtime_observations` on `context_ir.analyzer.analyze_repository(...)`
    - `metaclass_behavior_runtime_observations` on `context_ir.tool_facade.SemanticContextRequest`
    - forwarding through `context_ir.tool_facade.compile_repository_context(...)`
  - package-root/public low-level and MCP surfaces remain unchanged
  - primary truth stays unsupported/opaque and runtime-backed provenance remains additive only
- Control review found no issues
- Validation/discovery confirmed:
  - targeted slice checks passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_parser.py -k "metaclass" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "metaclass" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "metaclass" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "metaclass" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "metaclass" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py tests/test_mcp_server.py -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py`
  - full repo gate also passed on control-lane revalidation of the combined workspace:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported `METACLASS_BEHAVIOR` keyword-site findings can now carry additive runtime-backed provenance through one bounded family-level seam
  - the currently accepted runtime-backed family queue is now complete in workspace authority for the bounded `DYNAMIC_IMPORT`, `REFLECTIVE_BUILTIN`, `RUNTIME_MUTATION`, and `METACLASS_BEHAVIOR` subjects accepted so far
  - the next control action is one bounded deep-audit lane over the full current workspace-only diff before any commit decision
- Reasoning:
  - the slice stays inside the accepted metaclass contract by attaching only to already-emitted keyword-site unsupported constructs, preserving nested call/attribute boundaries, and avoiding broader class-construction claims
  - review stays clean because package-root/public low-level surfaces, MCP inputs, frontier emission, parser surfaces, and the full combined-workspace regression gate all remain unchanged while the new runtime-backed support remains additive only
- Acceptance status: first-pass

## 2026-04-21 -- Metaclass Behavior Runtime-Backed Planning Review

- Reviewed the returned planning spike for the minimum truthful runtime-backed contract for already-emitted unsupported `METACLASS_BEHAVIOR` boundaries
- Verified from fresh control-lane inspection:
  - repo-backed release state remains explicit and unchanged:
    - current branch is `main`
    - `HEAD` is `cdbff24`
    - `origin/main` is `cdbff24`
  - workspace-only accepted state still contains the uncommitted `dir`, `globals`, `locals`, `delattr`, and `setattr` seams plus continuity updates; this spike itself made no repo edits
  - `parser.py` still preserves `MetaclassKeywordFact` for the full `metaclass=...` keyword surface
  - `dependency_frontier.py` still emits explicit unsupported `METACLASS_BEHAVIOR` constructs keyed to that preserved keyword site rather than silently dropping metaclass behavior
  - repo-local probing confirmed that simple-name, attribute, call, unresolved-call, and nested-scope metaclass forms each still emit one unsupported `METACLASS_BEHAVIOR` construct at the full keyword site, while nested unresolved call/attribute pieces remain on their already accepted non-proof paths
  - no `MetaclassBehaviorRuntimeObservation`, `attach_metaclass_behavior_runtime_provenance(...)`, or `metaclass_behavior_runtime_observations` seam exists yet in `runtime_acquisition.py`, `analyzer.py`, or `tool_facade.py`
  - the accepted analyzer/tool-facade hybrid seam remains the highest exposed entry point, and package-root/public low-level plus MCP surfaces remain unchanged
  - the minimum truthful bounded contract is one new family-level seam limited to existing unsupported `METACLASS_BEHAVIOR` keyword-site constructs, additive runtime-backed provenance only, standard replay metadata, `normalized_payload.class_creation_outcome == "created_class"`, and a non-empty `durable_payload_reference` for a normalized artifact that identifies the created class and the observed selected metaclass for that keyword site
  - the first slice remains success-only; failure/exception outcomes, `__prepare__`, `__new__`, `__init__`, namespace/MRO modeling, post-creation side effects, and broader class-construction claims remain explicitly out of scope
- Control review found no issues
- Acceptance decision:
  - accept the planning spike
  - `METACLASS_BEHAVIOR` is implementation-authorized now as one bounded family-level runtime-backed slice
  - the next control action is one bounded `METACLASS_BEHAVIOR` implementation prompt only
- Alternatives considered:
  - keep `METACLASS_BEHAVIOR` blocked behind another planning spike
  - reopen nested call/attribute handling inside metaclass values as part of the first metaclass slice
  - widen into broader class-construction or object-model replay claims in the first slice
  - widen package-root/public low-level or MCP runtime-observation exposure
- Reasoning:
  - the preserved metaclass keyword site is already a stable unsupported subject in repo reality, so one bounded family-level seam can attach additively without reopening parser/frontier honesty work or nested-subexpression handling
  - requiring both a success-only class-creation outcome marker and a durable artifact identifying the created class plus observed selected metaclass keeps the first slice truthful without implying post-creation object-model proof
- Acceptance status: first-pass

## 2026-04-21 -- Setattr Runtime-Backed Implementation Review

- Reviewed the returned implementation slice for bounded additive runtime-backed attachment on existing unsupported unshadowed simple-name three-argument `setattr(obj, name, value)` findings only
- Verified from fresh control-lane inspection:
  - repo-backed release state remains explicit and unchanged:
    - current branch is `main`
    - `HEAD` is `cdbff24`
    - `origin/main` is `cdbff24`
  - `runtime_acquisition.py` now exposes a bounded builtin-specific seam:
    - `SetattrRuntimeObservation`
    - `attach_setattr_runtime_provenance(...)`
  - eligible attachment is limited to existing unsupported `RUNTIME_MUTATION` constructs whose originating call site is a simple-name `setattr` with `argument_count == 3`
  - the bounded payload contract requires `normalized_payload.mutation_outcome == "returned_none"` and a non-empty `durable_payload_reference`
  - optional additional normalized payload fields remain additive only
  - the durable payload artifact is limited to the passed third-argument value proof; post-mutation object state and effective stored value remain out of scope
  - analyzer/tool-facade exposure stays bounded to:
    - `setattr_runtime_observations` on `context_ir.analyzer.analyze_repository(...)`
    - `setattr_runtime_observations` on `context_ir.tool_facade.SemanticContextRequest`
    - forwarding through `context_ir.tool_facade.compile_repository_context(...)`
  - package-root/public low-level and MCP surfaces remain unchanged
  - primary truth stays unsupported/opaque and runtime-backed provenance remains additive only
- Control review found no issues
- Validation/discovery confirmed:
  - targeted slice checks passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "setattr_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_setattr_runtime_provenance_post_frontier" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "setattr_runtime_observations or attaches_setattr_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_runtime_mutation_call_boundaries or preserves_shadowed_runtime_mutation_names" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py tests/test_mcp_server.py -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py`
  - full repo gate also passed on control-lane revalidation:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported unshadowed simple-name three-argument `setattr(obj, name, value)` findings can now carry additive runtime-backed provenance through a bounded builtin-specific `setattr` seam
  - the current bounded `RUNTIME_MUTATION` runtime-backed queue is now complete in workspace authority for the accepted builtin-specific subjects
  - the next control action is one bounded planning spike for `METACLASS_BEHAVIOR` only
- Reasoning:
  - the slice stays inside the accepted bounded mutation contract by introducing one builtin-specific sibling seam without widening public surfaces, claiming post-mutation object state, or reopening broader mutation-family taxonomy
  - review stays clean because wrong-arity `setattr(...)` forms, shadowed names, package-root/public low-level surfaces, MCP inputs, and broader mutation claims all remain unchanged while the full repo gate stays green
- Acceptance status: first-pass

## 2026-04-21 -- Setattr Assigned-Value Contract Planning Review

- Reviewed the returned planning spike for the minimum truthful contract for existing unsupported unshadowed simple-name `setattr(obj, name, value)` call sites after the accepted bounded `delattr(obj, name)` seam
- Verified from fresh control-lane inspection:
  - repo-backed release state remains explicit and unchanged:
    - current branch is `main`
    - `HEAD` is `cdbff24`
    - `origin/main` is `cdbff24`
  - workspace-only accepted state still contains the uncommitted `dir`, `globals`, `locals`, and `delattr` seams plus continuity updates; this spike itself made no repo edits
  - `dependency_frontier.py` still surfaces unshadowed simple-name `setattr(obj, name, value)` and wrong-arity `setattr(obj, name)` call sites as unsupported `RUNTIME_MUTATION` constructs
  - shadowed `setattr` names still route to unresolved frontier rather than builtin-specific unsupported constructs
  - no `SetattrRuntimeObservation`, `attach_setattr_runtime_provenance(...)`, or `setattr_runtime_observations` seam exists yet in `runtime_acquisition.py`, `analyzer.py`, or `tool_facade.py`
  - the generic runtime-observation carrier already supports both `normalized_payload` and `durable_payload_reference`, and the accepted `dir` seam already proves the repo pattern for requiring a durable artifact when outcome-only proof is insufficient
  - repo-local probing confirmed that builtin `setattr(...)` returns `None`, so the success-only branch can be frozen as `normalized_payload.mutation_outcome == "returned_none"` by control-lane inference from the accepted `delattr` mutation-outcome naming pattern plus the builtin return behavior
  - the minimum truthful bounded contract is one new builtin-specific sibling seam limited to existing unsupported unshadowed simple-name `setattr` call sites with `argument_count == 3`, additive runtime-backed provenance only, standard replay metadata, `normalized_payload.mutation_outcome == "returned_none"`, and a non-empty `durable_payload_reference` for the normalized assigned-value artifact representing the third argument as passed to the call
  - post-mutation object state and effective stored value remain explicitly out of scope for this bounded slice
- Control review found no issues
- Acceptance decision:
  - accept the planning spike
  - `setattr(obj, name, value)` is implementation-authorized now as one bounded builtin-specific `RUNTIME_MUTATION` slice
  - the next control action is one bounded `setattr(obj, name, value)` implementation prompt only
- Alternatives considered:
  - keep `setattr(obj, name, value)` blocked behind another planning spike
  - reuse the accepted `globals()` / `locals()` / `delattr()` seam or widen to a family-level `RUNTIME_MUTATION` seam
  - claim post-mutation object state or effective stored value in the first `setattr` slice
- Reasoning:
  - the accepted runtime-backed carrier and current analyzer/tool-facade pattern are already sufficient for one more builtin-specific sibling seam without widening public surfaces
  - requiring both a success-only mutation outcome and a durable assigned-value artifact keeps the slice truthful without reopening general object-state modeling
- Acceptance status: first-pass

## 2026-04-21 -- Delattr Runtime-Backed Implementation Review

- Reviewed the returned implementation slice for bounded additive runtime-backed attachment on existing unsupported unshadowed simple-name two-argument `delattr(obj, name)` findings only
- Verified from fresh control-lane inspection:
  - repo-backed release state remains explicit and unchanged:
    - current branch is `main`
    - `HEAD` is `cdbff24`
    - `origin/main` is `cdbff24`
  - `runtime_acquisition.py` now exposes a bounded builtin-specific seam:
    - `DelattrRuntimeObservation`
    - `attach_delattr_runtime_provenance(...)`
  - eligible attachment is limited to existing unsupported `RUNTIME_MUTATION` constructs whose originating call site is a simple-name `delattr` with `argument_count == 2`
  - the bounded payload contract requires `normalized_payload.mutation_outcome == "deleted_attribute"`
  - optional additional normalized payload fields remain additive only
  - analyzer/tool-facade exposure stays bounded to:
    - `delattr_runtime_observations` on `context_ir.analyzer.analyze_repository(...)`
    - `delattr_runtime_observations` on `context_ir.tool_facade.SemanticContextRequest`
    - forwarding through `context_ir.tool_facade.compile_repository_context(...)`
  - package-root/public low-level and MCP surfaces remain unchanged
  - primary truth stays unsupported/opaque and runtime-backed provenance remains additive only
- Control review found no issues
- Validation/discovery confirmed:
  - targeted slice checks passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "attach_delattr_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_delattr_runtime_provenance_post_frontier" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "delattr_runtime_observations or attaches_delattr_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_runtime_mutation_call_boundaries or preserves_shadowed_runtime_mutation_names" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py tests/test_mcp_server.py -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py`
  - full repo gate also passed on control-lane revalidation:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported unshadowed simple-name two-argument `delattr(obj, name)` findings can now carry additive runtime-backed provenance through a bounded builtin-specific `delattr` seam
  - the next control action is one bounded planning spike for `setattr(obj, name, value)` only
- Reasoning:
  - the slice stays inside the accepted bounded mutation contract by introducing one builtin-specific sibling seam without widening public surfaces, materializing post-delete object state, or reopening broader mutation-family taxonomy
  - review stays clean because wrong-arity `delattr(...)`, shadowed names, all `setattr(...)` forms, and public-surface holds remain unchanged while the full repo gate stays green
- Acceptance status: first-pass

## 2026-04-21 -- Delattr vs Setattr RUNTIME_MUTATION Planning Review

- Reviewed the returned planning spike for the smallest truthful remaining `RUNTIME_MUTATION` candidate after the accepted bounded `globals()` and `locals()` seams
- Verified from fresh control-lane inspection:
  - repo-backed release state remains explicit and unchanged:
    - current branch is `main`
    - `HEAD` is `cdbff24`
    - `origin/main` is `cdbff24`
  - workspace-only accepted state still contains the uncommitted `dir`, `globals`, and `locals` seams plus continuity updates; the spike itself made no repo edits
  - `dependency_frontier.py` still surfaces unshadowed simple-name `delattr(obj, name)` and `setattr(obj, name, value)` call sites as unsupported `RUNTIME_MUTATION` constructs
  - wrong-arity unshadowed `delattr(obj)` and `setattr(obj, name)` call sites also surface as unsupported `RUNTIME_MUTATION`, so any next slice must bound eligibility by arity
  - shadowed `delattr` and `setattr` names still route to unresolved frontier rather than builtin-specific unsupported constructs
  - no existing mutation-specific runtime-backed seam or analyzer/tool-facade field exists yet
  - `delattr(obj, name)` is the smallest truthful next candidate because it stays on an already-surfaced unsupported boundary while avoiding the unresolved assigned-value replay problem reopened by `setattr(obj, name, value)`
  - the minimum truthful bounded contract is one new builtin-specific sibling seam limited to existing unsupported unshadowed simple-name `delattr` call sites with `argument_count == 2`, additive runtime-backed provenance only, and standard replay metadata plus `normalized_payload.mutation_outcome == "deleted_attribute"`
  - optional additional normalized payload fields remain additive only, and no post-delete object-state materialization is required for this bounded slice
- Control review found no issues
- Acceptance decision:
  - accept the planning spike
  - `delattr(obj, name)` is implementation-authorized now as the smallest truthful remaining bounded `RUNTIME_MUTATION` slice
  - `setattr(obj, name, value)` remains explicitly held for a later planning spike
  - the next control action is one bounded `delattr(obj, name)` implementation prompt only
- Alternatives considered:
  - authorize `setattr(obj, name, value)` next
  - reuse the accepted `globals()` / `locals()` seam or widen to a family-level `RUNTIME_MUTATION` seam
  - require another planning spike before any mutation implementation
- Reasoning:
  - `delattr(obj, name)` preserves the accepted exposure holds and matches the current builtin-specific seam pattern without forcing a new value-representation contract
  - `setattr(obj, name, value)` still needs a separate contract decision for reproducible assigned-value handling before implementation can be truthful
- Acceptance status: first-pass

## 2026-04-21 -- Locals Runtime-Backed Implementation Review

- Reviewed the returned implementation slice for bounded additive runtime-backed attachment on existing unsupported unshadowed simple-name zero-argument `locals()` findings only
- Verified from fresh control-lane inspection:
  - `runtime_acquisition.py` now exposes a bounded builtin-specific seam:
    - `LocalsRuntimeObservation`
    - `attach_locals_runtime_provenance(...)`
  - eligible attachment is limited to existing unsupported `RUNTIME_MUTATION` constructs whose originating call site is a simple-name `locals` with `argument_count == 0`
  - the bounded payload contract requires `normalized_payload.lookup_outcome == "returned_namespace"`
  - optional additional normalized payload fields remain additive only
  - analyzer/tool-facade exposure stays bounded to:
    - `locals_runtime_observations` on `context_ir.analyzer.analyze_repository(...)`
    - `locals_runtime_observations` on `context_ir.tool_facade.SemanticContextRequest`
    - forwarding through `context_ir.tool_facade.compile_repository_context(...)`
  - package-root/public low-level and MCP surfaces remain unchanged
  - primary truth stays unsupported/opaque and runtime-backed provenance remains additive only
- Control review found no issues
- Validation/discovery confirmed:
  - targeted slice checks passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_runtime_mutation_call_boundaries or preserves_shadowed_runtime_mutation_names" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "attach_locals_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_locals_runtime_provenance_post_frontier" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "locals_runtime_observations or attaches_locals_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py tests/test_mcp_server.py -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py`
  - full repo gate also passed on control-lane revalidation:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported unshadowed simple-name zero-argument `locals()` findings can now carry additive runtime-backed provenance through a bounded builtin-specific `locals` seam
  - the next control action is one bounded continuity-sync pass, followed by one bounded planning spike to decide whether `delattr(obj, name)` or `setattr(obj, name, value)` is the smallest truthful remaining mutation slice
- Reasoning:
  - the slice stays inside the accepted bounded mutation contract by introducing a dedicated builtin-specific seam without widening public surfaces, materializing namespace contents, or claiming write-back semantics
  - review stays clean because `delattr(...)` and `setattr(...)` remain explicitly deferred and no new runtime-backed symbols, dependencies, or frontier items were introduced
- Acceptance status: first-pass

## 2026-04-20 -- Globals Runtime-Backed Implementation Review

- Reviewed the returned implementation slice for bounded additive runtime-backed attachment on existing unsupported unshadowed simple-name zero-argument `globals()` findings only
- Verified from fresh control-lane inspection:
  - `runtime_acquisition.py` now exposes a bounded builtin-specific seam:
    - `GlobalsRuntimeObservation`
    - `attach_globals_runtime_provenance(...)`
  - eligible attachment is limited to existing unsupported `RUNTIME_MUTATION` constructs whose originating call site is a simple-name `globals` with `argument_count == 0`
  - the bounded payload contract requires `normalized_payload.lookup_outcome == "returned_namespace"`
  - optional additional normalized payload fields remain additive only
  - analyzer/tool-facade exposure stays bounded to:
    - `globals_runtime_observations` on `context_ir.analyzer.analyze_repository(...)`
    - `globals_runtime_observations` on `context_ir.tool_facade.SemanticContextRequest`
    - forwarding through `context_ir.tool_facade.compile_repository_context(...)`
  - package-root/public low-level and MCP surfaces remain unchanged
  - primary truth stays unsupported/opaque and runtime-backed provenance remains additive only
- Control review found no issues
- Validation/discovery confirmed:
  - targeted slice checks passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_runtime_mutation_call_boundaries or preserves_shadowed_runtime_mutation_names" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "attach_globals_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_globals_runtime_provenance_post_frontier" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "globals_runtime_observations or attaches_globals_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py tests/test_mcp_server.py -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py tests/test_dependency_frontier.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py tests/test_dependency_frontier.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py`
  - full repo gate also passed on control-lane revalidation:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported unshadowed simple-name zero-argument `globals()` findings can now carry additive runtime-backed provenance through a bounded builtin-specific `globals` seam
  - the next control action is one bounded continuity-sync pass, followed by one bounded planning spike for `locals()` only
- Reasoning:
  - the slice stays inside the accepted bounded mutation contract by introducing a dedicated builtin-specific seam without widening public surfaces or materializing namespace contents
  - review stays clean because `locals()`, `delattr(...)`, and `setattr(...)` remain explicitly deferred and no new runtime-backed symbols, dependencies, or frontier items were introduced
- Acceptance status: first-pass

## 2026-04-20 -- Reflective-Queue Continuity Reconciliation

- Reviewed current continuity against live repo state and accepted workspace authority before any `RUNTIME_MUTATION` implementation authorization
- Verified from fresh control-lane inspection:
  - repo-backed release state is explicit and clean:
    - current branch is `main`
    - `HEAD` is `cdbff24`
    - `origin/main` is `cdbff24`
    - the broadened release unit is already pushed and on the remote
  - workspace-only accepted state has advanced beyond the stale continuity docs:
    - the accepted builtin-specific `dir` seam now exists in `src/context_ir/runtime_acquisition.py`, `src/context_ir/analyzer.py`, and `src/context_ir/tool_facade.py`
    - targeted `dir(obj)` and `dir()` tests exist in `tests/test_runtime_acquisition.py`, `tests/test_analyzer.py`, `tests/test_tool_facade.py`, and `tests/test_dependency_frontier.py`
    - `PLAN.md` and `BUILDLOG.md` still needed reconciliation so a fresh controller would not route backward
  - the next runtime-backed family sequencing is now truthful only after that reconciliation:
    - the current reflective-builtin queue is complete in workspace authority for the accepted bounded subjects
    - `RUNTIME_MUTATION` is now the highest-ranked remaining runtime-backed family
    - `globals()` is the smallest truthful next mutation candidate, but only after the continuity mismatch is repaired
- Acceptance decision:
  - accept the continuity reconciliation pass
  - continuity now records the pushed `cdbff24` release state, the accepted bounded `dir` queue, and the current hold structure truthfully
  - the next control action is one bounded `globals()` implementation slice through a new mutation-specific sibling seam only
- Alternatives considered:
  - authorize `RUNTIME_MUTATION` implementation directly from workspace/chat state without reconciling continuity
  - leave the stale release-state and reflective-queue notes in place until a later release unit is cut
  - reopen the accepted `dir` queue before mutation sequencing
- Reasoning:
  - a fresh control lane must be able to recover from repo artifacts without being misled about release state or next-sequencing truth
  - the stale continuity mismatch was now a real control problem, not a cosmetic doc lag
  - reconciling first preserves the repo rule that authoritative continuity, release state, and next-slice authorization stay explicit
- Acceptance status: first-pass

## 2026-04-20 -- Post-Reflective RUNTIME_MUTATION Planning Review

- Reviewed the returned planning spike for the next truthful runtime-backed move after the accepted bounded `dir` queue
- Verified from fresh control-lane inspection:
  - no `RUNTIME_MUTATION` subfamily was implementation-authorized while continuity was stale
  - the smallest truthful next candidate inside the current `RUNTIME_MUTATION` bucket is `globals()`
  - the minimum truthful `globals()` contract is one new mutation-specific sibling seam that:
    - matches only existing unsupported unshadowed simple-name `globals()` call sites with `argument_count == 0`
    - preserves primary unsupported/opaque truth and attaches runtime-backed provenance additively only
    - requires the standard replay metadata plus `normalized_payload.lookup_outcome == "returned_namespace"`
    - does not mint new runtime-backed symbols, dependencies, frontier items, package-root fields, or MCP inputs
  - `locals()` remains lower-ranked because it reopens current-scope / frame-local semantics earlier
  - `delattr(obj, name)` and `setattr(obj, name, value)` remain lower-ranked because they reopen broader object-state mutation semantics and replay complexity earlier
- Acceptance decision:
  - accept the planning spike
  - hold mutation implementation until continuity is reconciled
  - after reconciliation, authorize one bounded `globals()` implementation slice only
- Alternatives considered:
  - authorize `globals()` implementation immediately despite stale continuity
  - move next to `locals()`
  - move next to `delattr(...)` or `setattr(...)`
  - reopen the accepted reflective-builtin queue
- Reasoning:
  - the spike's sequencing conclusion is sound, but authoritative continuity needed to be repaired before mutation work could advance cleanly
  - `globals()` is the smallest truthful mutation candidate because it stays on existing unsupported call boundaries while avoiding the broader frame-local or object-state replay questions reopened by the other mutation forms
- Acceptance status: first-pass

## 2026-04-20 -- Zero-Argument Dir Runtime-Backed Implementation Review

- Reviewed the returned implementation slice for bounded additive runtime-backed attachment on existing unsupported unshadowed simple-name zero-argument `dir()` findings through the existing builtin-specific `dir` seam
- Verified from fresh control-lane inspection:
  - `runtime_acquisition.py` still reuses the accepted builtin-specific seam:
    - `DirRuntimeObservation`
    - `attach_dir_runtime_provenance(...)`
  - eligible `dir` attachment is now limited to existing unsupported `REFLECTIVE_BUILTIN` constructs whose originating call site is a simple-name `dir` with `argument_count` 0 or 1
  - `durable_payload_reference` remains required as the minimum truthful listing proof
  - optional normalized summary fields such as `listing_entry_count` remain additive summary only
  - analyzer/tool-facade field names, package-root `context_ir.analyze_repository(...)`, and MCP-visible tool registration/shape remain unchanged
  - primary truth stays unsupported/opaque and runtime-backed provenance remains additive only
- Control review found no issues
- Validation/discovery confirmed:
  - targeted slice checks passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_reflective_builtin_boundaries or preserves_shadowed_reflective_builtin_names" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "attach_dir_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_dir_runtime_provenance_post_frontier" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "dir_runtime_observations or attaches_dir_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py tests/test_mcp_server.py -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py tests/test_runtime_acquisition.py tests/test_dependency_frontier.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py tests/test_runtime_acquisition.py tests/test_dependency_frontier.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py`
  - full repo gate also passed on control-lane revalidation:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported unshadowed simple-name zero-argument `dir()` findings can now carry additive runtime-backed provenance through the existing builtin-specific `dir` seam
  - the next control action is one bounded planning spike for the smallest truthful post-reflective `RUNTIME_MUTATION` move
- Reasoning:
  - the slice stays inside the accepted bounded `dir` contract by reusing the existing seam, constraining new behavior by originating call-site arity, and keeping the durable reference as the truth-bearing payload proof
  - review stays clean because no new public surface, no MCP widening, and no runtime-backed symbol/dependency materialization was introduced
- Acceptance status: first-pass

## 2026-04-20 -- Zero-Argument Dir Runtime-Backed Planning Review

- Reviewed the returned planning spike for the smallest truthful contract for zero-argument `dir()` after the accepted bounded `dir(obj)` slice
- Verified from fresh control-lane inspection:
  - zero-argument `dir()` is implementation-authorized as one bounded slice through the existing `DirRuntimeObservation` seam; another planning/decomposition step is not required
  - current repo/workspace truth already exposes the `dir` seam at the analyzer/tool-facade boundary, so no new exposed field is required
  - the truthful minimum remains a durable listing artifact reference, not an outcome-only proof
  - optional normalized summary fields such as `listing_entry_count` remain summary-only rather than a new required contract
  - no new runtime-backed symbols, dependencies, frontier items, package-root fields, or MCP inputs are required
- Acceptance decision:
  - accept the planning spike
  - zero-argument `dir()` is implementation-authorized now as one bounded slice through the existing builtin-specific `dir` seam
  - the next control action is one bounded implementation slice extending the accepted `dir` seam to existing unsupported unshadowed zero-argument `dir()` findings only
- Alternatives considered:
  - require another planning/decomposition spike before any zero-argument `dir()` implementation
  - open a separate sibling seam for zero-argument `dir()`
  - pivot next to `RUNTIME_MUTATION`
- Reasoning:
  - current repo/workspace shape already proves the right exposed seam and payload boundary; the remaining gap is only the internal arity widening inside the accepted `dir` path
  - reusing the existing seam is more truthful than inventing a separate zero-argument contract when both arities share the same listing-artifact proof requirement
- Acceptance status: first-pass

## 2026-04-20 -- Dir(obj) Runtime-Backed Implementation Review

- Reviewed the returned implementation slice for bounded additive runtime-backed attachment on existing unsupported unshadowed simple-name one-argument `dir(obj)` findings
- Verified from fresh control-lane inspection:
  - `runtime_acquisition.py` now exposes a builtin-specific seam:
    - `DirRuntimeObservation`
    - `attach_dir_runtime_provenance(...)`
  - eligible attachment is limited to existing unsupported `REFLECTIVE_BUILTIN` constructs whose originating call site is a simple-name `dir` with `argument_count == 1`
  - the bounded payload contract requires standard replay metadata plus a non-empty `durable_payload_reference` for the listing artifact
  - analyzer/tool-facade exposure stays bounded to:
    - `dir_runtime_observations` on `context_ir.analyzer.analyze_repository(...)`
    - `dir_runtime_observations` on `context_ir.tool_facade.SemanticContextRequest`
    - forwarding through `context_ir.tool_facade.compile_repository_context(...)`
  - package-root/public low-level and MCP surfaces remain unchanged
  - primary truth stays unsupported/opaque and runtime-backed provenance remains additive only
- Control review found no issues
- Validation/discovery confirmed:
  - targeted slice checks passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_reflective_builtin_boundaries" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "attach_dir_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_dir_runtime_provenance_post_frontier" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "dir_runtime_observations or attaches_dir_runtime_provenance" -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py`
  - full repo gate also passed on control-lane revalidation:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported unshadowed simple-name `dir(obj)` findings can now carry additive runtime-backed provenance through a builtin-specific `dir` seam
  - the next control action is one bounded planning spike for zero-argument `dir()` only
- Reasoning:
  - the slice stays inside the accepted reflective-builtin narrowing by introducing a builtin-specific seam instead of widening existing `vars`/`getattr` paths or public surfaces
  - review stays clean because zero-argument `dir()` remains explicitly deferred and no runtime-backed symbol/dependency materialization was introduced
- Acceptance status: first-pass

## 2026-04-20 -- Dir(obj) Runtime-Backed Planning Review

- Reviewed the returned planning spike for the smallest truthful contract for existing unsupported unshadowed simple-name one-argument `dir(obj)` findings after the accepted bounded `vars()` queue
- Verified from fresh control-lane inspection:
  - `dir(obj)` was not implementation-authorized before this spike, but one bounded implementation slice is now authorized
  - the truthful boundary is a new builtin-specific `dir` seam rather than reuse of the existing `vars` / `getattr` seams or a broader reflective-family seam
  - the minimum truthful contract cannot stay outcome-only:
    - the returned name listing is the substantive observation for `dir(obj)`
    - a non-empty `durable_payload_reference` is required as the truth-bearing listing proof
    - optional normalized summary fields may accompany that durable reference but are not sufficient alone
  - zero-argument `dir()` remains explicitly out of scope for this slice and still needs its own bounded follow-on decision
  - package-root/public low-level and MCP surfaces remain held
- Acceptance decision:
  - accept the planning spike
  - one bounded `dir(obj)` implementation slice is now authorized
  - the next control action is one bounded implementation slice adding a builtin-specific `dir` seam for existing unsupported unshadowed simple-name one-argument `dir(obj)` findings only
- Alternatives considered:
  - reuse the existing `vars` or `getattr` seam
  - authorize a broader reflective-family seam
  - include zero-argument `dir()` in the same slice
  - pivot next to `RUNTIME_MUTATION`
- Reasoning:
  - `dir(obj)` is the top-ranked remaining reflective candidate, but truthful attachment requires proving the observed listing rather than merely proving that the call ran
  - a builtin-specific seam keeps the slice architecture-aligned with current repo shape and preserves the existing public-surface holds
- Acceptance status: first-pass

## 2026-04-20 -- Broadened Release Unit Remote-State Verification

- Reviewed live repo state after the accepted broadened local commit creation to verify actual remote release state
- Verified from fresh control-lane inspection:
  - current branch is `main`
  - `git rev-parse --short HEAD` reports `cdbff24`
  - `git rev-parse --short origin/main` also reports `cdbff24`
  - the broadened release unit committed as `cdbff24` is already pushed and present on `origin/main`
  - the broadened release unit is therefore accepted both in workspace history and on the remote
  - local continuity docs remained stale about that push and needed later reconciliation
- Acceptance decision:
  - accept the remote-state verification
  - the broadened release unit is already released to `origin/main`
  - do not treat `cdbff24` as a local-only hold anymore
  - the next control action is to resume the next bounded reflective planning step while leaving continuity sync as a separate workspace-only task
- Alternatives considered:
  - continue treating the commit as local-only based on stale continuity notes
  - reconcile continuity before verifying remote state
  - reopen the broadened release unit itself
- Reasoning:
  - repo-backed truth must override stale workspace notes about release state
  - making release state explicit first prevents later sequencing errors and prevents a fresh controller from holding the roadmap behind an already-completed remote action
- Acceptance status: first-pass

## 2026-04-20 -- Broadened Local Commit Creation Review

- Reviewed the returned commit-creation slice for the accepted broadened release candidate
- Verified from the returned results:
  - one local commit was created successfully on `main`
  - commit id: `cdbff24`
  - commit subject: `Broaden semantic coverage and runtime-backed provenance`
  - `git log -1 --stat --oneline` confirmed the committed contents match the accepted staged candidate:
    - 32 files changed
    - 12577 insertions
    - 180 deletions
  - `git status --short` confirmed the remaining worktree changes are only unstaged `PLAN.md` and `BUILDLOG.md`
  - no push occurred
- Acceptance decision:
  - accept the local commit-creation slice
  - the broadened release unit is now committed locally as one coherent commit
  - keep push on explicit hold pending Ryan's authorization
  - the next control action is a human go/no-go on push, followed later by the separate continuity-sync release step
- Alternatives considered:
  - hold without creating the local commit
  - split the broadened candidate into multiple commits before the first commit
  - push immediately after local commit creation
- Reasoning:
  - the staged boundary had already been accepted first-pass, so local commit creation was the next truthful release-sequencing step
  - keeping push separate preserves the repo rule that irreversible remote actions require explicit human sign-off
  - leaving `PLAN.md` and `BUILDLOG.md` unstaged preserves the later separate continuity-sync step
- Acceptance status: first-pass

## 2026-04-20 -- Broadened Staged Commit-Candidate Review

- Reviewed the returned staging pass for the broadened release candidate after the broadened release-gate acceptance
- Verified from fresh control-lane inspection:
  - the staged index contains the broadened release candidate only
  - staged paths cover the broadened tracked unit plus the in-scope untracked runtime-backed files and `oracle_signal_smoke_e` assets
  - `PLAN.md` and `BUILDLOG.md` remain intentionally unstaged for the later separate continuity-sync step
  - no unexpected dirty path remains outside those two continuity files
  - direct staged-diff inspection found no release-boundary, public-surface, MCP, or code-quality findings beyond the already-cleared broadened QA result
- Acceptance decision:
  - accept the broadened staged commit-candidate review
  - the broadened release unit is now commit-ready as one coherent commit
  - do not push yet; remote update still awaits Ryan's explicit authorization
  - the next control action is to create one coherent commit from the staged candidate
- Alternatives considered:
  - keep holding despite the clean staged candidate
  - split the staged candidate into multiple commits before the first commit is created
  - push immediately after staged review
- Reasoning:
  - the broadened candidate already passed full repo QA, and the staged boundary now matches that reviewed release unit exactly
  - keeping `PLAN.md` and `BUILDLOG.md` unstaged preserves the repo's separate continuity-sync release step
  - push remains a distinct human-controlled remote action even though commit sequencing is now clear
- Acceptance status: first-pass

## 2026-04-20 -- Broadened Release-Gate Review

- Reviewed the returned broadened deep-QA / release-gate spike after Ryan explicitly authorized release-scope broadening
- Verified from the returned audit:
  - no findings were reported
  - full repo validation passed again:
    - `ruff check src/ tests/`
    - `ruff format --check src/ tests/`
    - `mypy --strict src/`
    - `pytest tests/ -v`
  - the broadened tracked candidate is clean as one coherent release unit
  - the untracked `oracle_signal_smoke_e` fixture/run-spec/task/test set is now in-scope for this release candidate as accepted internal-only evidence
  - `EVAL.md` and `PUBLIC_CLAIMS.md` still keep the accepted quad matrix as the top public evidence surface, so including `oracle_signal_smoke_e` does not widen the public claim posture
- Acceptance decision:
  - accept the broadened release-gate spike
  - the broadened release candidate is now clean in workspace authority and can proceed to bounded staging/review
  - keep `PLAN.md` and `BUILDLOG.md` out of the release commit candidate so continuity sync still happens as a separate post-push step under repo release discipline
  - the next control action is one bounded staging pass to form the broadened commit candidate, followed by one final staged-diff review before any commit/push decision
- Alternatives considered:
  - keep holding despite the clean broadened gate
  - continue trying to isolate the narrow runtime-backed-only candidate
  - proceed directly to commit without a staged-diff review
- Reasoning:
  - once the release unit was broadened and re-audited, the earlier packaging blocker no longer applied
  - the broadened candidate now has full regression coverage and a truthful release boundary
  - a final staged-diff review remains worthwhile before commit, but another pre-staging QA cycle would be redundant
- Acceptance status: first-pass

## 2026-04-20 -- Release-Scope Broadening Decision

- Reviewed the returned staging/isolation slice after the accepted release-sequencing spike
- Verified from fresh control-lane inspection:
  - nothing was staged
  - the blocker is real:
    - `src/context_ir/dependency_frontier.py` and `tests/test_dependency_frontier.py` do not split cleanly at the runtime-backed boundary
    - accepted root-alias `loader.import_module(...)` / reflective-boundary work is entangled with broader attribute-chain/member-heavy changes
    - forcing an index-only cached patch would risk creating a fragile or misleading release snapshot
  - secondary mixed files remain, but they are not the primary blocker:
    - `src/context_ir/semantic_types.py`
    - `tests/test_semantic_types.py`
    - `PLAN.md`
    - `BUILDLOG.md`
- Human sign-off:
  - Ryan explicitly authorized broadening the release candidate rather than forcing hunk-level separation, because the underlying work quality now matters more than preserving the narrower runtime-backed-only release boundary
- Acceptance decision:
  - accept the release-scope broadening decision with human sign-off
  - abandon the narrow runtime-backed-only hunk-isolation path as the next release move
  - keep commit/push on hold until the broadened release candidate passes one more bounded deep-QA / release-gate review
  - the next control action is one bounded broadened QA/release spike that includes the entangled parser/resolver/member-heavy tranche and explicitly decides whether the untracked `oracle_signal_smoke_e` eval assets are in or out
- Alternatives considered:
  - force an index-only cached patch for the narrow runtime-backed tranche
  - keep holding until more separation work is done
  - broaden the release candidate and re-QA the larger coherent unit
- Reasoning:
  - the blocker is release packaging, not audited code quality inside the accepted runtime-backed tranche
  - the failed staging/isolation pass proved the narrow candidate is not a truthful clean release unit
  - after Ryan's explicit sign-off, the truthful next move is to QA the broader coherent unit rather than manufacture a synthetic staged snapshot
- Acceptance status: first-pass with human sign-off

## 2026-04-20 -- Deep-QA Release-Gate Review

- Reviewed the returned deep-QA / release-gate spike for the current accepted runtime-backed tranche
- Verified from fresh control-lane inspection:
  - the audited runtime-backed tranche is clean in workspace authority
  - full repo validation passed during deep QA:
    - `ruff check src/ tests/`
    - `ruff format --check src/ tests/`
    - `mypy --strict src/`
    - `pytest tests/ -v`
  - no additional correctness, type-safety, regression, public-surface, or MCP-widening findings were found inside the audited runtime-backed tranche
  - however, the overall dirty worktree is not one coherent release unit:
    - separately scoped parser/resolver/member-heavy work is still mixed into the worktree
    - untracked `oracle_signal_smoke_e` eval assets are still present
    - current evidence/claim docs still frame the top evidence surface around the accepted quad-matrix/triple-matrix anchors
- Control review found one release-sequencing finding:
  - hold commit/push for the full dirty worktree because it would blur the accepted runtime-backed tranche with unrelated scope
- Validation/discovery confirmed:
  - `git status --short`
  - `git diff --stat`
  - `git diff --name-only`
  - `git diff -- src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py src/context_ir/dependency_frontier.py src/context_ir/semantic_types.py src/context_ir/semantic_compiler.py src/context_ir/semantic_optimizer.py src/context_ir/semantic_diagnostics.py src/context_ir/__init__.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py tests/test_dependency_frontier.py tests/test_semantic_types.py tests/test_semantic_compiler.py tests/test_semantic_optimizer.py tests/test_semantic_diagnostics.py tests/test_public_api.py tests/test_mcp_server.py PLAN.md BUILDLOG.md ARCHITECTURE.md EVAL.md PUBLIC_CLAIMS.md README.md`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v`
- Acceptance decision:
  - accept the deep-QA spike
  - the accepted runtime-backed tranche is clean in workspace authority
  - hold commit/push for the full dirty worktree until release sequencing isolates the runtime-backed commit candidate cleanly
- Reasoning:
  - the QA result is strong enough to clear code quality for the audited tranche
  - the remaining blocker is release-boundary integrity, not code correctness
- Acceptance status: first-pass

## 2026-04-20 -- Runtime-Backed Release-Sequencing Review

- Reviewed the returned release-sequencing spike for isolating the commit candidate after deep QA
- Verified from fresh control-lane inspection:
  - the accepted runtime-backed tranche is not one path-based commit
  - the following paths are clean includes for the runtime-backed commit candidate:
    - `ARCHITECTURE.md`
    - `EVAL.md`
    - `src/context_ir/__init__.py`
    - `src/context_ir/analyzer.py`
    - `src/context_ir/runtime_acquisition.py`
    - `src/context_ir/semantic_compiler.py`
    - `src/context_ir/semantic_diagnostics.py`
    - `src/context_ir/semantic_optimizer.py`
    - `src/context_ir/tool_facade.py`
    - `tests/test_analyzer.py`
    - `tests/test_runtime_acquisition.py`
    - `tests/test_semantic_compiler.py`
    - `tests/test_semantic_diagnostics.py`
    - `tests/test_semantic_optimizer.py`
    - `tests/test_tool_facade.py`
  - the following paths are clearly outside the runtime-backed commit candidate:
    - `src/context_ir/parser.py`
    - `src/context_ir/resolver.py`
    - `tests/test_parser.py`
    - `tests/test_resolver.py`
    - `tests/test_scorer.py`
    - `tests/test_semantic_scorer.py`
    - `evals/fixtures/oracle_signal_smoke_e/`
    - `evals/run_specs/oracle_signal_smoke_e_matrix.json`
    - `evals/tasks/oracle_signal_smoke_e.json`
    - `tests/test_eval_signal_smoke_e.py`
  - six files remain mixed and require manual hunk separation:
    - `src/context_ir/dependency_frontier.py`
    - `src/context_ir/semantic_types.py`
    - `tests/test_dependency_frontier.py`
    - `tests/test_semantic_types.py`
    - `PLAN.md`
    - `BUILDLOG.md`
- Control review found no issues with the spike itself
- Acceptance decision:
  - accept the release-sequencing spike
  - the accepted runtime-backed tranche is commit-ready only with manual hunk-level separation
  - the next control action is one bounded staging pass to form the exact commit candidate, followed by review of the staged diff before any commit/push decision
- Reasoning:
  - a path-based commit would be wrong because mixed files carry both accepted runtime-backed work and separately scoped work
  - the clean include list is strong enough that a manual staging pass is now the smallest truthful next move
- Acceptance status: first-pass

## 2026-04-20 -- Zero-Argument Vars Runtime-Backed Implementation Review

- Reviewed the returned implementation slice for bounded additive runtime-backed attachment on existing unsupported unshadowed simple-name zero-argument `vars()` findings through the existing `vars` seam
- Verified from fresh control-lane inspection:
  - `runtime_acquisition.py` still reuses the accepted builtin-specific seam:
    - `VarsRuntimeObservation`
    - `attach_vars_runtime_provenance(...)`
  - eligible `vars` attachment is now limited to existing unsupported `REFLECTIVE_BUILTIN` constructs whose originating call site is a simple-name `vars` with `argument_count` 0 or 1
  - payload validation now branches by matched call-site arity rather than widening the exposed seam:
    - zero-argument `vars()` accepts only `returned_namespace`
    - one-argument `vars(obj)` still accepts only `returned_namespace` or `raised_type_error`
  - analyzer/tool-facade field names, package-root `context_ir.analyze_repository(...)`, and MCP-visible tool registration/shape remain unchanged
  - `dir(...)` remains unattached
  - shadowed `vars` names remain on the generic non-proof path
  - primary truth stays unsupported/opaque and runtime-backed provenance remains additive only
- Control review found no issues
- Validation/discovery confirmed:
  - `git diff -- src/context_ir/runtime_acquisition.py tests/test_runtime_acquisition.py tests/test_dependency_frontier.py tests/test_analyzer.py tests/test_tool_facade.py`
  - `git status --short`
  - `rg -n "VarsRuntimeObservation|attach_vars_runtime_provenance|_is_supported_vars_call_site|_validate_vars_lookup_outcome|returned_namespace|raised_type_error|argument_count == 0|argument_count == 1|vars\\(\\)" src/context_ir/runtime_acquisition.py tests/test_runtime_acquisition.py tests/test_dependency_frontier.py tests/test_analyzer.py tests/test_tool_facade.py`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '60,110p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '593,890p'`
  - `nl -ba tests/test_runtime_acquisition.py | sed -n '735,940p'`
  - `nl -ba tests/test_analyzer.py | sed -n '538,585p'`
  - `nl -ba tests/test_tool_facade.py | sed -n '786,872p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '572,612p'`
  - control-lane validation passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_reflective_builtin_boundaries or preserves_shadowed_reflective_builtin_names" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "attach_vars_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_vars_runtime_provenance_post_frontier" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "vars_runtime_observations or attaches_vars_runtime_provenance" -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py tests/test_runtime_acquisition.py tests/test_dependency_frontier.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py tests/test_runtime_acquisition.py tests/test_dependency_frontier.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py`
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported unshadowed simple-name zero-argument `vars()` findings can now carry additive runtime-backed provenance through the existing builtin-specific `vars` seam
  - the next control action is one bounded planning spike to decide the smallest truthful `dir(obj)` contract before any `dir` implementation is authorized
- Reasoning:
  - the slice stays inside the accepted reflective-builtin narrowing by reusing the existing `vars` seam, constraining new behavior by originating call-site arity, and keeping the payload branch-only
  - review stays clean because one-argument `vars(obj)`, held public surfaces, sibling seams, and new runtime-backed subjects remain unchanged
  - the next remaining reflective candidate, `dir(obj)`, still needs decomposition because no `dir`-specific runtime-backed seam exists in repo authority yet
- Acceptance status: first-pass

## 2026-04-20 -- Zero-Argument Vars Runtime-Backed Planning Review

- Reviewed the returned planning spike for the smallest truthful contract for zero-argument `vars()` after the accepted bounded `vars(obj)` slice
- Verified from fresh control-lane inspection:
  - zero-argument `vars()` is already implementation-authorized as one bounded slice; one more planning/decomposition step is not required
  - accepted continuity still keeps `REFLECTIVE_BUILTIN` above `RUNTIME_MUTATION`, and nothing in current repo reality changes that ordering
  - `dependency_frontier.py` plus a fresh control-lane repo-local probe confirm that unshadowed `vars()` already surfaces as unsupported `REFLECTIVE_BUILTIN`
  - `analyzer.py` and `tool_facade.py` already expose generic `vars_runtime_observations` pass-through, so no new analyzer/tool-facade field or broader exposed seam is required
  - `runtime_acquisition.py` still hard-codes the accepted attachable `vars` form to simple-name `vars` with `argument_count == 1`, which is the only remaining contract gap
  - the current `VarsRuntimeObservation` seam already uses an outcome-only payload shape and can stay unchanged at the public boundary
  - the truthful minimum is internal arity-specific branching inside the existing `vars` path:
    - zero-argument `vars()` may allow only `normalized_payload.lookup_outcome == "returned_namespace"`
    - one-argument `vars(obj)` keeps the accepted `returned_namespace` or `raised_type_error` outcomes
  - no new replay-target field, replay-selector field, subject kind, dependency kind, package-root field, or MCP input is required for this next slice
- Control review found no issues
- Validation/discovery confirmed:
  - `sed -n '175,206p' PLAN.md`
  - `sed -n '1,220p' BUILDLOG.md`
  - `sed -n '1,260p' ARCHITECTURE.md`
  - `sed -n '1,220p' EVAL.md`
  - `sed -n '1,220p' AGENTS.md`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '1,110p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '136,360p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '588,860p'`
  - `nl -ba src/context_ir/analyzer.py | sed -n '1,120p'`
  - `nl -ba src/context_ir/tool_facade.py | sed -n '1,140p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '70,110p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '680,760p'`
  - `nl -ba tests/test_runtime_acquisition.py | sed -n '150,210p'`
  - `nl -ba tests/test_runtime_acquisition.py | sed -n '735,890p'`
  - `nl -ba tests/test_analyzer.py | sed -n '120,155p'`
  - `nl -ba tests/test_analyzer.py | sed -n '520,590p'`
  - `nl -ba tests/test_tool_facade.py | sed -n '190,245p'`
  - `nl -ba tests/test_tool_facade.py | sed -n '715,840p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '572,615p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '900,970p'`
  - `rg -n "vars\\(|dir\\(|VarsRuntimeObservation|attach_vars_runtime_provenance|vars_runtime_observations|REFLECTIVE_BUILTIN|RUNTIME_MUTATION|runtime-backed" AGENTS.md PLAN.md BUILDLOG.md ARCHITECTURE.md EVAL.md src/context_ir tests`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_reflective_builtin_boundaries or surfaces_runtime_mutation_call_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "attach_vars_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_vars_runtime_provenance_post_frontier" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "vars_runtime_observations or attaches_vars_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -c 'import tempfile, textwrap; from pathlib import Path; from context_ir.parser import extract_syntax; from context_ir.binder import bind_syntax; from context_ir.resolver import resolve_semantics; from context_ir.dependency_frontier import derive_dependency_frontier; td=tempfile.TemporaryDirectory(); root=Path(td.name); (root/"main.py").write_text(textwrap.dedent("""\ndef run(obj: object) -> None:\n    vars()\n    vars(obj)\n    dir()\n    dir(obj)\n""").lstrip(), encoding="utf-8"); program=derive_dependency_frontier(resolve_semantics(bind_syntax(extract_syntax(root)))); print(sorted((c.construct_text, c.reason_code.value) for c in program.unsupported_constructs))'`
  - `git status --short`
- Acceptance decision:
  - accept the planning spike
  - zero-argument `vars()` is implementation-authorized now as one bounded slice through the existing `vars` seam
  - the next control action is one bounded implementation slice extending the existing `vars` seam to existing unsupported unshadowed zero-argument `vars()` findings only
- Alternatives considered:
  - require one more planning/decomposition spike before any zero-argument `vars()` implementation
  - move next to `dir(obj)`
  - move next to `dir()`
  - pivot next to `RUNTIME_MUTATION`
- Reasoning:
  - the existing `VarsRuntimeObservation` / `attach_vars_runtime_provenance(...)` / `vars_runtime_observations` seam is already truthful at the analyzer/tool-facade boundary, so the remaining work is an internal matcher/validator widening rather than a new exposed contract
  - zero-argument `vars()` is narrower and more ready than `dir(...)` because it can reuse the existing seam and needs only arity-specific outcome validation
  - `RUNTIME_MUTATION` remains lower-ranked because no mutation-specific runtime-backed seam exists yet and accepted continuity still places it behind the remaining reflective work
- Acceptance status: first-pass

## 2026-04-20 -- Post-Vars Runtime-Backed Planning Review

- Reviewed the returned planning spike for the next truthful runtime-backed move after the accepted bounded `vars(obj)` slice
- Verified from fresh control-lane inspection:
  - top-ranked next move is still inside `REFLECTIVE_BUILTIN`, not a pivot to `RUNTIME_MUTATION`
  - accepted continuity still keeps `REFLECTIVE_BUILTIN` above `RUNTIME_MUTATION`, and nothing in current repo reality changes that ordering
  - the current runtime-backed exposed seam remains limited to:
    - `DynamicImportRuntimeObservation`
    - `HasattrRuntimeObservation`
    - `GetattrRuntimeObservation`
    - `VarsRuntimeObservation`
  - `analyzer.py` and `tool_facade.py` already expose generic `vars_runtime_observations` pass-through, but `runtime_acquisition.py` still hard-codes the accepted attachable form to simple-name `vars` with `argument_count == 1`
  - the existing `VarsRuntimeObservation` docs and tests still describe the accepted attachable form as `vars(obj)`, and current tests explicitly assert `vars()` stays unattached
  - a fresh control-lane repo-local probe confirms that unshadowed `vars()`, `vars(obj)`, `dir()`, and `dir(obj)` all currently surface as unsupported `REFLECTIVE_BUILTIN`
  - no `DirRuntimeObservation` / `attach_dir...` / `dir_runtime...` seam exists anywhere in repo code or tests
  - no mutation-specific runtime-backed seam exists anywhere in repo code or tests
  - inference from current repo shape supports the ranking:
    - `vars()` first
    - `dir(obj)` second
    - `dir()` third
    - `RUNTIME_MUTATION` fourth
- Control review found no issues
- Validation/discovery confirmed:
  - `sed -n '175,206p' PLAN.md`
  - `sed -n '1,140p' BUILDLOG.md`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '136,360p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '588,860p'`
  - `nl -ba src/context_ir/analyzer.py | sed -n '1,120p'`
  - `nl -ba src/context_ir/tool_facade.py | sed -n '1,140p'`
  - `rg -n "RUNTIME_MUTATION|REFLECTIVE_BUILTIN|vars\\(|dir\\(|setattr\\(|delattr\\(|globals\\(|locals\\(|VarsRuntimeObservation|vars_runtime_observations|runtime-backed" AGENTS.md PLAN.md BUILDLOG.md ARCHITECTURE.md EVAL.md src/context_ir tests`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_reflective_builtin_boundaries or surfaces_runtime_mutation_call_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -c 'import tempfile, textwrap; from pathlib import Path; from context_ir.parser import extract_syntax; from context_ir.binder import bind_syntax; from context_ir.resolver import resolve_semantics; from context_ir.dependency_frontier import derive_dependency_frontier; td=tempfile.TemporaryDirectory(); root=Path(td.name); (root/"main.py").write_text(textwrap.dedent("""\ndef run(obj: object, name: str, value: object) -> None:\n    vars()\n    vars(obj)\n    dir()\n    dir(obj)\n    setattr(obj, name, value)\n    delattr(obj, name)\n    globals()\n    locals()\n""").lstrip(), encoding="utf-8"); program=derive_dependency_frontier(resolve_semantics(bind_syntax(extract_syntax(root)))); print(sorted((c.construct_text, c.reason_code.value) for c in program.unsupported_constructs))'`
  - `rg -n "DirRuntimeObservation|attach_dir|dir_runtime|RuntimeMutationObservation|attach_runtime_mutation|setattr_runtime|delattr_runtime|globals_runtime|locals_runtime" src/context_ir tests`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "attach_vars_runtime_provenance" -q`
- Acceptance decision:
  - accept the planning spike
  - zero-argument `vars()` is the top-ranked next move after the accepted `vars(obj)` slice
  - direct implementation is not yet authorized
  - the next control action is one bounded planning/decomposition spike for zero-argument `vars()` only
- Alternatives considered:
  - move next to `dir(obj)`
  - move next to `dir()`
  - pivot next to `RUNTIME_MUTATION`
  - skip decomposition and implement zero-argument `vars()` immediately
- Reasoning:
  - the existing `vars` seam is generic enough to make zero-argument `vars()` plausible, but runtime acquisition still encodes only the one-argument accepted contract, so one more explicit contract decision is more truthful than jumping straight to implementation
  - `dir(obj)` and `dir()` are less ready because no `dir`-specific seam exists at all
  - `RUNTIME_MUTATION` remains last because accepted continuity still ranks it lower and there is still no mutation-specific runtime-backed seam
- Acceptance status: first-pass

## 2026-04-20 -- Vars Runtime-Backed Implementation Review

- Reviewed the returned implementation slice for bounded builtin-specific runtime-backed attachment on existing unsupported unshadowed simple-name `vars(obj)` findings
- Verified from fresh control-lane inspection:
  - `runtime_acquisition.py` now exposes a builtin-specific seam:
    - `VarsRuntimeObservation`
    - `attach_vars_runtime_provenance(...)`
  - eligible attachment is limited to existing unsupported `REFLECTIVE_BUILTIN` constructs whose originating call site is a simple-name `vars` with `argument_count == 1`
  - the bounded payload contract is enforced through `normalized_payload.lookup_outcome`, with allowed values only `returned_namespace` or `raised_type_error`
  - unshadowed zero-argument `vars()`, all `dir(...)` forms, and the already accepted `hasattr`, `getattr`, and `DYNAMIC_IMPORT` seams remain unchanged
  - `analyzer.py` and `tool_facade.py` now accept optional `vars_runtime_observations` while preserving the exact static-only path when runtime observations are omitted
  - package-root `context_ir.analyze_repository(...)` remains the static-only regression anchor, and MCP-visible tool registration/shape remain unchanged
  - primary truth stays unsupported/opaque and runtime-backed provenance remains additive only
- Control review found no issues
- Validation/discovery confirmed:
  - `git diff -- src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
  - `rg -n "VarsRuntimeObservation|attach_vars_runtime_provenance|vars_runtime_observations|returned_namespace|raised_type_error|argument_count == 1|argument_count != 1|vars\\(" src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
  - `git status --short`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '136,340p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '588,820p'`
  - `nl -ba tests/test_runtime_acquisition.py | sed -n '735,890p'`
  - `nl -ba tests/test_analyzer.py | sed -n '541,582p'`
  - `nl -ba tests/test_tool_facade.py | sed -n '715,823p'`
  - control-lane validation passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py -k "exports_analyze_repository or semantic_module_level_apis_are_not_root_exports" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_mcp_server.py -k "mcp_server_registers_exactly_one_compile_tool or mcp_server_does_not_change_package_root_exports or tool_delegates_to_tool_facade" -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py`
    - `git diff --check -- src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
  - worker-reported validation also passed with the same requested suite
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported unshadowed simple-name `vars(obj)` findings can now carry additive runtime-backed provenance through a bounded builtin-specific seam
  - the next control action is one bounded planning spike to choose the next truthful post-`vars(obj)` runtime-backed move
- Reasoning:
  - the slice stays inside the accepted reflective-builtin narrowing by matching only already-emitted unsupported findings plus originating call-site facts and a bounded outcome-only payload contract
  - review stays clean because zero-argument `vars()`, all `dir(...)` forms, public-surface holds, sibling seams, and new runtime-backed subjects remain unchanged
  - the remaining truthful sequencing question is now whether to continue inside the remaining reflective-builtin space or pivot later to `RUNTIME_MUTATION`
- Acceptance status: first-pass

## 2026-04-20 -- Post-Getattr Runtime-Backed Planning Review

- Reviewed the returned planning spike for the next truthful runtime-backed move after the accepted bounded `getattr` path
- Verified from fresh control-lane inspection:
  - accepted continuity still ranks `REFLECTIVE_BUILTIN` above `RUNTIME_MUTATION`, and nothing in current repo reality changes that ordering
  - the current runtime-backed exposed seam remains limited to:
    - `DynamicImportRuntimeObservation`
    - `HasattrRuntimeObservation`
    - `GetattrRuntimeObservation`
  - `analyzer.py` and `tool_facade.py` still expose optional pass-through only for those accepted seams
  - `dependency_frontier.py` still surfaces repo-backed remaining candidates today:
    - `vars(...)` and `dir(...)` as `REFLECTIVE_BUILTIN`
    - `setattr(...)`, `delattr(...)`, `globals()`, and `locals()` as `RUNTIME_MUTATION`
  - a fresh control-lane repo-local probe confirms that unshadowed `vars()`, `vars(obj)`, `dir()`, and `dir(obj)` all currently surface as unsupported `REFLECTIVE_BUILTIN`, so any remaining reflective slice must narrow by originating call-site form rather than by family label alone
  - inference from current repo evidence supports `vars(obj)` ahead of `dir(obj)`: the `vars(obj)` unit can be bounded to simple-name one-argument form with a minimal outcome-only payload, while `dir(...)` still reopens broader namespace-enumeration and object-model contract choices
  - `RUNTIME_MUTATION` remains lower-ranked because it reopens state/namespace replay semantics and still has no accepted mutation-specific seam
- Control review found no issues
- Validation/discovery confirmed:
  - `sed -n '172,196p' PLAN.md`
  - `sed -n '1,120p' BUILDLOG.md`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '80,90p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '1,220p'`
  - `nl -ba src/context_ir/analyzer.py | sed -n '1,120p'`
  - `nl -ba src/context_ir/tool_facade.py | sed -n '1,120p'`
  - `rg -n "RUNTIME_MUTATION|REFLECTIVE_BUILTIN|vars\\(|dir\\(|setattr\\(|delattr\\(|globals\\(|locals\\(|runtime-backed" PLAN.md BUILDLOG.md ARCHITECTURE.md EVAL.md src/context_ir tests`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_reflective_builtin_boundaries or surfaces_runtime_mutation_call_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -c 'import tempfile, textwrap; from pathlib import Path; from context_ir.parser import extract_syntax; from context_ir.binder import bind_syntax; from context_ir.resolver import resolve_semantics; from context_ir.dependency_frontier import derive_dependency_frontier; td=tempfile.TemporaryDirectory(); root=Path(td.name); (root/"main.py").write_text(textwrap.dedent("""\ndef run(obj: object, name: str, value: object) -> None:\n    vars()\n    vars(obj)\n    dir()\n    dir(obj)\n    setattr(obj, name, value)\n    delattr(obj, name)\n    globals()\n    locals()\n""").lstrip(), encoding="utf-8"); program=derive_dependency_frontier(resolve_semantics(bind_syntax(extract_syntax(root)))); print(sorted((c.construct_text, c.reason_code.value) for c in program.unsupported_constructs))'`
- Acceptance decision:
  - accept the planning spike
  - `vars(obj)` is now the next smallest truthful runtime-backed move
  - direct implementation is authorized for one bounded builtin-specific `vars(obj)` slice only
  - the next control action is one bounded implementation slice adding additive runtime-backed provenance for existing unsupported unshadowed simple-name `vars(obj)` findings only
- Alternatives considered:
  - move next to `dir(obj)` / `dir()`
  - pivot next to `RUNTIME_MUTATION`
  - require another planning pass before any `vars(...)` implementation
- Reasoning:
  - repo-local truth now confirms that both zero-argument and one-argument reflective builtin forms surface, so the smallest safe next slice is the one-argument `vars(obj)` form with explicit arity narrowing
  - `dir(...)` is still broader because it pushes object-model and enumeration semantics further than the already accepted builtin-specific seam pattern
  - `RUNTIME_MUTATION` still requires another decomposition step before implementation because no accepted mutation-specific observation seam or payload contract exists yet
- Acceptance status: first-pass

## 2026-04-20 -- Getattr Default-Form Implementation Review

- Reviewed the returned implementation slice for bounded builtin-specific runtime-backed attachment on existing unsupported unshadowed `getattr(obj, name, default)` findings
- Verified from fresh control-lane inspection:
  - `runtime_acquisition.py` still reuses the accepted builtin-specific seam:
    - `GetattrRuntimeObservation`
    - `attach_getattr_runtime_provenance(...)`
  - eligible `getattr` attachment is now limited to existing unsupported `REFLECTIVE_BUILTIN` constructs whose originating call site is a simple-name `getattr` with `argument_count` 2 or 3
  - payload validation now branches by matched call-site form rather than widening the exposed seam:
    - two-argument `getattr(obj, name)` still accepts only `returned_value` or `raised_attribute_error`
    - defaulted `getattr(obj, name, default)` now accepts only `returned_value` or `returned_default_value`
  - invalid-arity `getattr()`, sibling reflective builtins, analyzer/tool-facade field names, package-root `context_ir.analyze_repository(...)`, and MCP-visible tool registration/shape remain unchanged
  - primary truth stays unsupported/opaque and runtime-backed provenance remains additive only
- Control review found no issues
- Validation/discovery confirmed:
  - `git diff -- src/context_ir/runtime_acquisition.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
  - `rg -n "GetattrRuntimeObservation|attach_getattr_runtime_provenance|lookup_outcome|returned_default_value|argument_count == 3|argument_count != 2|argument_count != 3" src/context_ir/runtime_acquisition.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
  - `git status --short`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '56,90p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '500,715p'`
  - `nl -ba tests/test_runtime_acquisition.py | sed -n '616,780p'`
  - `nl -ba tests/test_analyzer.py | sed -n '455,515p'`
  - `nl -ba tests/test_tool_facade.py | sed -n '616,662p'`
  - control-lane validation passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "attach_getattr_runtime_provenance or attach_hasattr_runtime_provenance_targets_supported_hasattr_boundaries or dynamic_import_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_getattr_runtime_provenance_post_frontier or attaches_hasattr_runtime_provenance_post_frontier or dynamic_import_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "getattr_runtime_observations or attaches_getattr_runtime_provenance or forwards_hasattr_runtime_observations or attaches_hasattr_runtime_provenance or dynamic_import_runtime_observations" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py -k "exports_analyze_repository or semantic_module_level_apis_are_not_root_exports" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_mcp_server.py -k "mcp_server_registers_exactly_one_compile_tool or mcp_server_does_not_change_package_root_exports or tool_delegates_to_tool_facade" -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py`
  - worker-reported validation also passed with the same targeted suite
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported unshadowed `getattr(obj, name, default)` findings can now carry additive runtime-backed provenance through the existing builtin-specific `getattr` seam
  - the next control action is one bounded planning spike to decide the next truthful post-`getattr` runtime-backed move
- Reasoning:
  - the slice stays inside the accepted reflective-builtin narrowing by reusing the existing seam and constraining new behavior by originating call-site form plus branch-only payload semantics
  - review stays clean because invalid-arity `getattr`, held public surfaces, sibling seams, and new runtime-backed subjects remain unchanged
  - the remaining truthful sequencing question is now whether to keep going inside the remaining reflective-builtin space (`vars(...)` / `dir(...)`) or pivot to the next broader family such as `RUNTIME_MUTATION`
- Acceptance status: first-pass

## 2026-04-20 -- Getattr Default-Form Planning Review

- Reviewed the returned planning spike for the next truthful runtime-backed reflective-builtin move after the accepted bounded `getattr(obj, name)` implementation
- Verified from fresh control-lane inspection:
  - `dependency_frontier.py` already surfaces `getattr(obj, name, default)` as an explicit unsupported `REFLECTIVE_BUILTIN` boundary inside the same builtin-name bucket as the accepted two-argument form
  - `runtime_acquisition.py` already exposes the accepted builtin-specific seam:
    - `GetattrRuntimeObservation`
    - `attach_getattr_runtime_provenance(...)`
  - `analyzer.py` and `tool_facade.py` already accept optional `getattr_runtime_observations` while preserving the exact static-only path when runtime observations are omitted
  - the current `getattr` matcher remains bounded to simple-name `getattr` with `argument_count == 2`, so extending the seam to the defaulted form is now a narrow matcher/payload widening rather than a new exposed contract family
  - the current bounded payload validator requires `normalized_payload.lookup_outcome` and currently allows only `returned_value` or `raised_attribute_error`
  - the minimum truthful contract addition for the defaulted form is branch outcome only: keep `returned_value` for attribute-return branches and add `returned_default_value` for default-return branches without attempting concrete value/default serialization
  - package-root `context_ir.analyze_repository(...)` remains the static-only regression anchor, MCP-visible tool registration/shape remain unchanged, and no new runtime-backed symbols, dependencies, subject kinds, or facade fields are required for this next slice
- Control review found no issues
- Validation/discovery confirmed:
  - `sed -n '149,195p' PLAN.md`
  - `sed -n '654,706p' PLAN.md`
  - `sed -n '1,140p' BUILDLOG.md`
  - `rg -n "getattr\\(|GetattrRuntimeObservation|attach_getattr_runtime_provenance|getattr_runtime_observations|lookup_outcome|REFLECTIVE_BUILTIN|runtime-backed" AGENTS.md PLAN.md BUILDLOG.md ARCHITECTURE.md EVAL.md src/context_ir tests`
  - `sed -n '89,110p' ARCHITECTURE.md`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '110,320p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '480,710p'`
  - `nl -ba src/context_ir/analyzer.py | sed -n '1,120p'`
  - `nl -ba src/context_ir/tool_facade.py | sed -n '1,160p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '70,110p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '680,740p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '560,625p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '900,970p'`
  - `nl -ba tests/test_runtime_acquisition.py | sed -n '616,740p'`
  - `nl -ba tests/test_analyzer.py | sed -n '440,520p'`
  - `nl -ba tests/test_tool_facade.py | sed -n '530,670p'`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_reflective_builtin_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "attach_getattr_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_getattr_runtime_provenance_post_frontier" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "getattr_runtime_observations or attaches_getattr_runtime_provenance" -q`
- Acceptance decision:
  - accept the planning spike
  - defaulted `getattr(obj, name, default)` is now the next smallest truthful runtime-backed reflective-builtin slice
  - direct implementation is authorized for one bounded extension of the existing builtin-specific `getattr` seam only
  - the next control action is one bounded implementation slice extending that seam to already-emitted unsupported simple-name `getattr(obj, name, default)` call sites with `argument_count == 3`
- Alternatives considered:
  - require another planning pass before any defaulted `getattr` implementation
  - introduce a sibling observation type or new facade field for the defaulted form
  - materialize concrete returned/default values in the first defaulted-form slice
- Reasoning:
  - the existing builtin-specific `getattr` seam already carries the needed analyzer/tool-facade/runtime contract, so another planning pass would mostly restate the current exposed shape
  - the smallest truthful widening is branch outcome only, because returned objects alone are ambiguous when an attribute value equals the supplied default
  - reusing the existing seam keeps review narrow and preserves the explicit holds on package-root/public low-level widening, MCP widening, broader reflective-family generalization, and new runtime-backed subjects
- Acceptance status: first-pass

## 2026-04-20 -- Getattr Runtime-Backed Implementation Review

- Reviewed the returned implementation slice for bounded builtin-specific runtime-backed attachment on existing unsupported unshadowed `getattr(obj, name)` findings
- Verified from fresh control-lane inspection:
  - `runtime_acquisition.py` now exposes a builtin-specific seam:
    - `GetattrRuntimeObservation`
    - `attach_getattr_runtime_provenance(...)`
  - eligible attachment is limited to existing unsupported `REFLECTIVE_BUILTIN` constructs whose originating call site is a simple-name `getattr` with `argument_count == 2`
  - the bounded payload contract is enforced through `normalized_payload.lookup_outcome`, with allowed values only `returned_value` or `raised_attribute_error`
  - invalid-arity `getattr()` and defaulted `getattr(obj, name, default)` remain unchanged
  - `analyzer.py` and `tool_facade.py` now accept optional `getattr_runtime_observations` while preserving the exact static-only path when runtime observations are omitted
  - the already accepted `hasattr` and `DYNAMIC_IMPORT` runtime-backed seams still work unchanged
  - package-root `context_ir.analyze_repository(...)` remains the static-only regression anchor, and MCP-visible tool registration/shape remain unchanged
- Control review found no issues
- Validation/discovery confirmed:
  - `git diff -- src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
  - `git status --short`
  - `rg -n "GetattrRuntimeObservation|attach_getattr_runtime_provenance|getattr_runtime_observations|lookup_outcome|HasattrRuntimeObservation|attach_hasattr_runtime_provenance|DynamicImportRuntimeObservation|attach_dynamic_import_runtime_provenance" src/context_ir tests`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "getattr_runtime_provenance or attach_hasattr_runtime_provenance_targets_supported_hasattr_boundaries or dynamic_import_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "getattr_runtime_provenance or attaches_hasattr_runtime_provenance_post_frontier or dynamic_import_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "getattr_runtime_observations or getattr_runtime_provenance or forwards_hasattr_runtime_observations or attaches_hasattr_runtime_provenance or dynamic_import_runtime_observations" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py -k "exports_analyze_repository or semantic_module_level_apis_are_not_root_exports" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_mcp_server.py -k "mcp_server_registers_exactly_one_compile_tool or mcp_server_does_not_change_package_root_exports or tool_delegates_to_tool_facade" -q`
  - `PYTHONPATH=src .venv/bin/python -c "import inspect, context_ir, context_ir.analyzer as a; print('pkg', inspect.signature(context_ir.analyze_repository)); print('analyzer', inspect.signature(a.analyze_repository))"`
  - worker-reported validation also passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "getattr_runtime_provenance or attach_hasattr_runtime_provenance_targets_supported_hasattr_boundaries or dynamic_import_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "getattr_runtime_provenance or attaches_hasattr_runtime_provenance_post_frontier or dynamic_import_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "getattr_runtime_observations or getattr_runtime_provenance or forwards_hasattr_runtime_observations or attaches_hasattr_runtime_provenance or dynamic_import_runtime_observations" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py -k "exports_analyze_repository or semantic_module_level_apis_are_not_root_exports" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_mcp_server.py -k "mcp_server_registers_exactly_one_compile_tool or mcp_server_does_not_change_package_root_exports or tool_delegates_to_tool_facade" -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py`
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported unshadowed `getattr(obj, name)` findings can now carry additive runtime-backed provenance through a bounded builtin-specific seam
  - the next control action is one bounded planning spike for `getattr(obj, name, default)` branch semantics and replay/payload decisions
- Reasoning:
  - the slice stays inside the accepted reflective-builtin narrowing by matching only already-emitted unsupported findings plus originating call-site facts and a bounded payload contract
  - review stays clean because invalid-arity/defaulted `getattr`, sibling seams, new runtime-backed symbols/dependencies, and held public surfaces remain unchanged
  - `getattr(obj, name, default)` is still not implementation-authorized because truthful replay must distinguish returned-attribute vs returned-default behavior
- Acceptance status: first-pass

## 2026-04-20 -- Getattr Runtime-Backed Planning Review

- Reviewed the returned planning spike for the next truthful `getattr(...)` runtime-backed reflective-builtin slice after the accepted `hasattr(obj, name)` implementation
- Verified from fresh control-lane inspection:
  - no accepted `GetattrRuntimeObservation`, `attach_getattr_runtime_provenance(...)`, or `getattr_runtime_observations` seam exists yet; the only reflective-builtin runtime-backed seam today is the accepted builtin-specific `hasattr(obj, name)` path
  - the current frontier emits `getattr()`, `getattr(obj, name)`, and `getattr(obj, name, default)` under the same unsupported `REFLECTIVE_BUILTIN` bucket, so the next runtime-backed slice must narrow eligibility by originating call-site form rather than by family label alone
  - the current runtime-backed sibling-seam pattern in `runtime_acquisition.py`, `analyzer.py`, and `tool_facade.py` is already sufficient for another bounded builtin-specific reflective slice
  - two-argument `getattr(obj, name)` is the smallest truthful next unit because it stays on the already-emitted unsupported call boundary while avoiding default-branch semantics and arbitrary returned-value materialization
  - a minimal boundary-only payload such as one normalized `lookup_outcome` field with `returned_value` or `raised_attribute_error` stays within the accepted additive runtime-backed admissibility boundary without claiming concrete returned-value serialization
- Control review found no issues
- Validation/discovery confirmed:
  - `sed -n '149,190p' PLAN.md`
  - `sed -n '648,690p' PLAN.md`
  - `sed -n '1,120p' BUILDLOG.md`
  - `rg -n "getattr\\(|REFLECTIVE_BUILTIN|HasattrRuntimeObservation|attach_hasattr_runtime_provenance|hasattr_runtime_observations|GetattrRuntimeObservation|attach_getattr_runtime_provenance|getattr_runtime_observations|runtime-backed" AGENTS.md PLAN.md BUILDLOG.md ARCHITECTURE.md EVAL.md src/context_ir tests`
  - `sed -n '89,110p' ARCHITECTURE.md`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '1,260p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '420,620p'`
  - `nl -ba src/context_ir/analyzer.py | sed -n '1,120p'`
  - `nl -ba src/context_ir/tool_facade.py | sed -n '1,160p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '70,110p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '680,740p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '560,625p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '900,970p'`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_reflective_builtin_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "attach_hasattr_runtime_provenance_targets_supported_hasattr_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_hasattr_runtime_provenance_post_frontier" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "forwards_hasattr_runtime_observations or attaches_hasattr_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -c 'import tempfile, textwrap; from pathlib import Path; from context_ir.parser import extract_syntax; from context_ir.binder import bind_syntax; from context_ir.resolver import resolve_semantics; from context_ir.dependency_frontier import derive_dependency_frontier; td=tempfile.TemporaryDirectory(); root=Path(td.name); (root/"main.py").write_text(textwrap.dedent("""\ndef run(obj: object, name: str, default: object) -> None:\n    getattr()\n    getattr(obj, name)\n    getattr(obj, name, default)\n""").lstrip(), encoding="utf-8"); program=derive_dependency_frontier(resolve_semantics(bind_syntax(extract_syntax(root)))); print(sorted((c.construct_text, c.reason_code.value) for c in program.unsupported_constructs if c.reason_code.value=="reflective_builtin"))'`
- Acceptance decision:
  - accept the planning spike
  - two-argument `getattr(obj, name)` is now the next smallest truthful runtime-backed reflective-builtin slice
  - direct implementation is authorized for one bounded builtin-specific slice only
  - the next control action is one bounded implementation slice adding additive runtime-backed provenance for existing unsupported unshadowed `getattr(obj, name)` findings only
- Alternatives considered:
  - start with `getattr(obj, name, default)`
  - require another planning pass before any `getattr(...)` implementation
  - skip form-splitting and treat all `getattr(...)` forms as one runtime-backed slice
- Reasoning:
  - two-argument `getattr(obj, name)` reuses the accepted builtin-specific seam shape without forcing default-branch semantics into the first slice
  - `getattr(obj, name, default)` is materially broader because truthful replay must distinguish returned-attribute vs returned-default behavior
  - the repo already has the necessary hybrid seam pattern, so another planning pass would not add truth beyond the now-explicit form and payload narrowing
- Acceptance status: first-pass

## 2026-04-20 -- Hasattr Runtime-Backed Implementation Review

- Reviewed the returned implementation slice for bounded builtin-specific runtime-backed attachment on existing unsupported unshadowed `hasattr(obj, name)` findings
- Verified from fresh control-lane inspection:
  - `runtime_acquisition.py` now exposes a builtin-specific seam:
    - `HasattrRuntimeObservation`
    - `attach_hasattr_runtime_provenance(...)`
  - eligible attachment is limited to existing unsupported `REFLECTIVE_BUILTIN` constructs whose originating call site is a simple-name `hasattr` with `argument_count == 2`
  - invalid-arity `hasattr()` and other reflective builtins remain unchanged
  - `analyzer.py` and `tool_facade.py` now accept optional `hasattr_runtime_observations` while preserving the exact static-only path when runtime observations are omitted
  - the already accepted `DYNAMIC_IMPORT` runtime-backed seam still works unchanged
  - package-root `context_ir.analyze_repository(...)` remains the static-only regression anchor, and MCP-visible tool registration/shape remain unchanged
- Control review found no issues
- Validation/discovery confirmed:
  - `git diff -- src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
  - `rg -n "HasattrRuntimeObservation|attach_hasattr_runtime_provenance|hasattr_runtime_observations|dynamic_import_runtime_observations|attach_dynamic_import_runtime_provenance|DynamicImportRuntimeObservation" src/context_ir tests`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "hasattr_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "hasattr_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "hasattr_runtime_observations or hasattr_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "dynamic_import_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py -k "exports_analyze_repository or semantic_module_level_apis_are_not_root_exports" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_mcp_server.py -k "mcp_server_registers_exactly_one_compile_tool or mcp_server_does_not_change_package_root_exports or tool_delegates_to_tool_facade" -q`
  - `PYTHONPATH=src .venv/bin/python -c "import inspect, context_ir, context_ir.analyzer as a; print('pkg', inspect.signature(context_ir.analyze_repository)); print('analyzer', inspect.signature(a.analyze_repository))"`
  - worker-reported validation also passed:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "hasattr_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "hasattr_runtime_provenance" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "hasattr_runtime_observations or hasattr_runtime_provenance" -q`
    - `.venv/bin/python -m ruff check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py`
- Acceptance decision:
  - accept the implementation slice
  - existing unsupported unshadowed `hasattr(obj, name)` findings can now carry additive runtime-backed provenance through a bounded builtin-specific seam
  - the next control action is one bounded planning spike for `getattr(...)` form-splitting and runtime payload decisions
- Reasoning:
  - the slice stays inside the accepted reflective-builtin narrowing by matching only already-emitted unsupported findings plus originating call-site facts
  - review stays clean because invalid-arity `hasattr()`, other reflective builtins, new runtime-backed symbols/dependencies, and held public surfaces remain unchanged
  - `getattr(...)` is still not implementation-authorized because its already-emitted unsupported family includes multiple forms with different value/default semantics
- Acceptance status: first-pass

## 2026-04-20 -- Reflective-Builtin Subfamily Planning Review

- Reviewed the returned planning spike for the next truthful runtime-backed `REFLECTIVE_BUILTIN` subfamily beyond the now-complete bounded `DYNAMIC_IMPORT` family
- Verified from fresh control-lane inspection:
  - the repo still has no accepted reflective-builtin runtime-backed observation type, analyzer keyword, or tool-facade field; the current exposed hybrid seam remains `DYNAMIC_IMPORT`-only
  - `dependency_frontier.py` currently surfaces unshadowed `getattr(...)`, `hasattr(...)`, `vars(...)`, and `dir(...)` call sites as explicit unsupported `REFLECTIVE_BUILTIN` records by builtin name rather than by arity
  - a direct repo-local control-lane probe confirms that broader reflective forms such as `getattr()`, `getattr(obj, name, None)`, `hasattr()`, `vars()`, and `dir()` already surface inside the same unsupported family, so the first runtime-backed reflective slice must constrain eligibility explicitly rather than relying on the frontier bucket alone
  - `hasattr(obj, name)` is the smallest truthful first runtime-backed subfamily because it stays on existing unsupported call boundaries, has one bounded accepted arity, and carries a minimal boolean payload, while `getattr(...)`, `vars(...)`, and `dir(...)` reopen value materialization, default-form splitting, or namespace-enumeration semantics earlier
- Control review found no issues
- Validation/discovery confirmed:
  - `sed -n '149,179p' PLAN.md`
  - `sed -n '592,710p' PLAN.md`
  - `sed -n '1,140p' BUILDLOG.md`
  - `rg -n "REFLECTIVE_BUILTIN|getattr\\(|hasattr\\(|vars\\(|dir\\(|HasattrRuntimeObservation|GetattrRuntimeObservation|attach_hasattr|attach_getattr|hasattr_runtime_observations|getattr_runtime_observations|runtime-backed" AGENTS.md PLAN.md BUILDLOG.md ARCHITECTURE.md EVAL.md src/context_ir tests`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '70,120p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '682,735p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '1,260p'`
  - `nl -ba src/context_ir/analyzer.py | sed -n '1,140p'`
  - `nl -ba src/context_ir/tool_facade.py | sed -n '1,140p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '570,620p'`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_reflective_builtin_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "dynamic_import_runtime_provenance_targets_dynamic_import_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_dynamic_import_runtime_provenance_post_frontier" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "forwards_dynamic_import_runtime_observations or attaches_builtin_dynamic_import_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -c 'import tempfile, textwrap; from pathlib import Path; from context_ir.parser import extract_syntax; from context_ir.binder import bind_syntax; from context_ir.resolver import resolve_semantics; from context_ir.dependency_frontier import derive_dependency_frontier; td=tempfile.TemporaryDirectory(); root=Path(td.name); (root/"main.py").write_text(textwrap.dedent("""\ndef run(obj: object, name: str) -> None:\n    getattr()\n    hasattr()\n    getattr(obj, name, None)\n    hasattr(obj, name)\n    vars()\n    dir()\n    vars(obj)\n    dir(obj)\n""").lstrip(), encoding="utf-8"); program=derive_dependency_frontier(resolve_semantics(bind_syntax(extract_syntax(root)))); print(sorted((c.construct_text, c.reason_code.value) for c in program.unsupported_constructs if c.reason_code.value=="reflective_builtin"))'`
- Acceptance decision:
  - accept the planning spike
  - existing unsupported unshadowed `hasattr(obj, name)` call sites are now the next smallest truthful runtime-backed `REFLECTIVE_BUILTIN` subfamily
  - direct implementation is authorized for one bounded builtin-specific slice only
  - the next control action is one bounded implementation slice adding additive runtime-backed provenance for existing unsupported unshadowed `hasattr(obj, name)` findings only
- Alternatives considered:
  - start with `getattr(...)`
  - start with `vars(...)`
  - start with `dir(...)`
  - require another planning pass before any reflective-builtin implementation
- Reasoning:
  - the repo-local probe shows the current unsupported reflective bucket is broader than any truthful first runtime-backed slice, so implementation must choose one explicit attachable unit and constrain eligibility at the matcher level
  - `hasattr(obj, name)` is the narrowest first unit because it avoids value-materialization and namespace-enumeration semantics while staying on an already emitted unsupported call boundary
  - direct implementation no longer requires another planning pass because the bounded first unit and its necessary eligibility guard are now explicit
- Acceptance status: first-pass

## 2026-04-20 -- Post-Dynamic-Import Runtime-Family Ranking Review

- Reviewed the returned planning spike for the next runtime-backed capability family beyond the now-complete bounded `DYNAMIC_IMPORT` family
- Verified from fresh control-lane inspection:
  - the remaining repo-backed candidate families are still surfaced today only as explicit unsupported boundaries:
    - `REFLECTIVE_BUILTIN`
    - `RUNTIME_MUTATION`
    - `METACLASS_BEHAVIOR`
  - the currently accepted runtime-backed seam remains specific to completed `DYNAMIC_IMPORT` work; no accepted runtime-backed observation type, analyzer keyword, or tool-facade field exists yet for the remaining families
  - `REFLECTIVE_BUILTIN` stays on already-surfaced unsupported call boundaries and is read/query-oriented, while `RUNTIME_MUTATION` reopens state/namespace replay semantics and `METACLASS_BEHAVIOR` reopens broader non-call class-creation semantics
  - the current `REFLECTIVE_BUILTIN` bucket still groups heterogeneous builtins (`getattr`, `hasattr`, `vars`, `dir`) under one unsupported family with no accepted runtime-backed subfamily contract yet
- Control review found no issues
- Validation/discovery confirmed:
  - `sed -n '149,179p' PLAN.md`
  - `sed -n '592,610p' PLAN.md`
  - `sed -n '1,120p' BUILDLOG.md`
  - `rg -n "RUNTIME_MUTATION|REFLECTIVE_BUILTIN|METACLASS_BEHAVIOR|ReflectiveBuiltinRuntimeObservation|RuntimeMutationRuntimeObservation|Metaclass.*RuntimeObservation|attach_reflective|attach_runtime_mutation|attach_metaclass|reflective_builtin_runtime|runtime_mutation_runtime|metaclass_behavior_runtime|dynamic_import_runtime_observations|attach_dynamic_import_runtime_provenance" AGENTS.md PLAN.md BUILDLOG.md ARCHITECTURE.md EVAL.md src/context_ir tests`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_runtime_mutation_call_boundaries or surfaces_reflective_builtin_boundaries or surfaces_metaclass_keywords_as_unsupported" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "dynamic_import_runtime_provenance_targets_dynamic_import_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_dynamic_import_runtime_provenance_post_frontier" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "forwards_dynamic_import_runtime_observations or attaches_builtin_dynamic_import_runtime_provenance" -q`
- Acceptance decision:
  - accept the planning spike
  - `REFLECTIVE_BUILTIN` is now the highest-ranked remaining runtime-backed capability family
  - direct implementation is not yet authorized because the current family bucket is still too coarse for a truthful first runtime-backed seam
  - the next control action is one bounded planning spike to choose the next truthful `REFLECTIVE_BUILTIN` subfamily
- Alternatives considered:
  - move next to `RUNTIME_MUTATION`
  - move next to `METACLASS_BEHAVIOR`
  - skip planning and implement the whole `REFLECTIVE_BUILTIN` family directly
- Reasoning:
  - `REFLECTIVE_BUILTIN` is the least aggressive remaining family, but the repo does not yet encode which builtin subset is the smallest truthful first runtime-backed unit inside that family
  - direct implementation would force an unaccepted contract decision about whether the first unit is `getattr(...)` alone, a narrower read-only pair, or the whole family bucket
- Acceptance status: first-pass

## 2026-04-20 -- Dynamic-Import Builtin Attachment Review

- Reviewed the returned implementation slice for extending the generalized `DYNAMIC_IMPORT` seam to existing unsupported `__import__(...)` subjects
- Verified from fresh control-lane inspection:
  - `runtime_acquisition.py` now treats `__import__(...)` as an attachable dynamic-import boundary through the same family-level matcher that already handles the accepted importlib-backed cases
  - the already accepted importlib-backed attachment path remains unchanged
  - primary subject truth still remains unsupported/opaque, with runtime-backed provenance attached additively rather than relabeling the construct
  - analyzer/tool-facade seam usage remains unchanged
  - package-root/public low-level `context_ir.analyze_repository(...)` remains the static-only regression anchor, and MCP-visible tool registration/shape remain unchanged
- Control review found no issues
- Validation/discovery confirmed:
  - `git diff -- src/context_ir/runtime_acquisition.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py`
  - `rg -n "__import__|dynamic_import_runtime_observations|attach_dynamic_import_runtime_provenance|DynamicImportRuntimeObservation" src/context_ir tests`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "dynamic_import_runtime_provenance" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "dynamic_import_runtime_provenance_post_frontier" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "forwards_dynamic_import_runtime_observations" -q`
  - `PYTHONPATH=src .venv/bin/python -c "import inspect, context_ir, context_ir.analyzer as a; print('pkg', inspect.signature(context_ir.analyze_repository)); print('analyzer', inspect.signature(a.analyze_repository))"`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py -k "exports_analyze_repository or semantic_module_level_apis_are_not_root_exports" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_mcp_server.py -k "mcp_server_registers_exactly_one_compile_tool or mcp_server_does_not_change_package_root_exports or tool_delegates_to_tool_facade" -q`
  - worker-reported validation also passed:
    - `ruff check`
    - `ruff format --check`
    - `mypy --strict`
    - targeted dependency-frontier and seam-test pytest commands
- Acceptance decision:
  - accept the implementation slice
  - the bounded `DYNAMIC_IMPORT` runtime-backed family is now complete for the currently accepted existing unsupported subjects
  - the next control action is one bounded planning spike to choose the next truthful runtime-backed capability family
- Reasoning:
  - the slice closes the last already-authorized same-family gap without widening beyond existing unsupported `DYNAMIC_IMPORT` subjects
  - review stays clean because no new runtime-backed dependency/symbol subjects or public-surface changes were introduced
  - with the current bounded `DYNAMIC_IMPORT` family complete, the truthful next move returns to planning rather than silently rolling into another dynamic family
- Acceptance status: first-pass

## 2026-04-20 -- Dynamic-Import Seam-Generalization Implementation Review

- Reviewed the returned implementation slice for family-level `DYNAMIC_IMPORT` seam generalization with importlib-only behavior preserved
- Verified from fresh control-lane inspection:
  - the exposed seam now uses truthful family-level naming across the accepted analyzer/tool-facade/runtime boundary:
    - `DynamicImportRuntimeObservation`
    - `attach_dynamic_import_runtime_provenance(...)`
    - `dynamic_import_runtime_observations`
  - current runtime-backed attachment behavior remains unchanged:
    - eligible runtime-backed attachment still lands only on the already accepted direct/imported/aliased/root-alias `importlib.import_module` family
    - `__import__(...)` still does not receive runtime-backed attachment in this slice
  - primary unsupported/opaque truth remains unchanged and additive runtime-backed provenance still stays separate from primary subject capability tier
  - package-root/public low-level `context_ir.analyze_repository(...)` remains the static-only regression anchor, while only the module-level analyzer seam widened its naming
  - MCP-visible tool registration and package-root export expectations remain unchanged
  - no remaining uses of the retired importlib-specific exposed seam identifiers were found in `src/` or `tests/`
- Control review found no issues
- Validation/discovery confirmed:
  - `git diff -- src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py src/context_ir/tool_facade.py tests/test_runtime_acquisition.py tests/test_analyzer.py tests/test_tool_facade.py tests/test_semantic_optimizer.py tests/test_semantic_diagnostics.py`
  - `rg -n "ImportlibImportModuleRuntimeObservation|attach_importlib_import_module_runtime_provenance|importlib_runtime_observations" src tests`
  - `rg -n "DynamicImportRuntimeObservation|attach_dynamic_import_runtime_provenance|dynamic_import_runtime_observations" src tests`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "targets_only_import_module_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "runtime_provenance_post_frontier" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "runtime_observations" -q`
  - `PYTHONPATH=src .venv/bin/python -c "import inspect, context_ir, context_ir.analyzer as a; print('pkg', inspect.signature(context_ir.analyze_repository)); print('analyzer', inspect.signature(a.analyze_repository))"`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py -k "exports_analyze_repository or semantic_module_level_apis_are_not_root_exports" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_mcp_server.py -k "mcp_server_registers_exactly_one_compile_tool or mcp_server_does_not_change_package_root_exports or tool_delegates_to_tool_facade" -q`
  - worker-reported validation also passed:
    - `ruff check`
    - `ruff format --check`
    - `mypy --strict`
    - targeted dependency-frontier and seam-test pytest commands
- Acceptance decision:
  - accept the implementation slice
  - the next control action is one bounded implementation slice to extend the generalized `DYNAMIC_IMPORT` seam to existing unsupported `__import__(...)` subjects only
- Reasoning:
  - the slice achieved the now-authorized seam generalization without smuggling in new runtime-backed behavior
  - review stays clean because the rename/generalization and the later `__import__(...)` behavior widening remain separated into two bounded slices
  - public low-level and MCP holds remain intact
- Acceptance status: first-pass

## 2026-04-20 -- Dynamic-Import Seam-Generalization Planning Review

- Reviewed the returned planning spike for the minimum truthful seam shape needed before extending runtime-backed attachment to existing unsupported `__import__(...)` subjects
- Verified from fresh control-lane inspection:
  - `runtime_acquisition.py` already has a generic `attach_runtime_observations(...)` primitive, but the exported observation type, exported helper, analyzer keyword, and tool-facade field are still importlib-specific
  - `dependency_frontier.py` already classifies both `__import__(...)` and the accepted `importlib.import_module` forms as the same unsupported `DYNAMIC_IMPORT` family
  - the current runtime-backed matcher intentionally targets only `importlib.import_module`-family call sites and explicitly excludes `__import__(...)`
  - directly impacted seam references also exist in `tests/test_semantic_optimizer.py` and `tests/test_semantic_diagnostics.py`, so the bounded rename blast radius is wider than the first three seam tests alone but remains repo-local and targeted
- Control review found no issues
- Validation/discovery confirmed:
  - `rg -n "importlib_runtime_observations|ImportlibImportModuleRuntimeObservation|attach_importlib_import_module_runtime_provenance|attach_runtime_observations|DYNAMIC_IMPORT|__import__" AGENTS.md PLAN.md BUILDLOG.md ARCHITECTURE.md EVAL.md src/context_ir tests`
  - `nl -ba PLAN.md | sed -n '629,642p'`
  - `nl -ba BUILDLOG.md | sed -n '1,230p'`
  - `nl -ba ARCHITECTURE.md | sed -n '1,220p'`
  - `nl -ba EVAL.md | sed -n '1,220p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '1,74p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '74,180p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '354,445p'`
  - `nl -ba src/context_ir/analyzer.py | sed -n '1,120p'`
  - `nl -ba src/context_ir/tool_facade.py | sed -n '1,120p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '70,95p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '700,745p'`
  - `rg -n "ImportlibImportModuleRuntimeObservation|attach_importlib_import_module_runtime_provenance|importlib_runtime_observations" src/context_ir tests/test_semantic_optimizer.py tests/test_semantic_diagnostics.py tests/test_analyzer.py tests/test_tool_facade.py tests/test_runtime_acquisition.py`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "targets_only_import_module_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_named_dynamic_call_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_importlib_runtime_provenance_post_frontier" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "forwards_importlib_runtime_observations" -q`
- Acceptance decision:
  - accept the planning spike
  - generalize the current importlib-specific exposed seam to one family-level `DYNAMIC_IMPORT` seam rather than introducing a sibling `__import__(...)` seam
  - split the work into two sequential slices:
    - first, seam generalization only with no behavior widening
    - later, extend the generalized seam to existing unsupported `__import__(...)` subjects only
  - the next control action is one bounded implementation slice for seam generalization only
- Alternatives considered:
  - add `__import__(...)` immediately through the current importlib-specific seam
  - create a separate sibling seam just for `__import__(...)`
  - combine seam generalization and `__import__(...)` behavior widening into one implementation slice
- Reasoning:
  - one family-level seam is more truthful because frontier semantics already place `__import__(...)` and `importlib.import_module` forms in the same `DYNAMIC_IMPORT` family
  - a sibling seam would duplicate exposed contracts for one semantic family without a payload or provenance distinction
  - combining rename/generalization with new attachment behavior would blur review because the exposed analyzer/tool-facade contract is already live in workspace authority
- Acceptance status: first-pass

## 2026-04-20 -- Post-Exposure Runtime-Backed Capability-Family Planning Review

- Reviewed the returned planning spike for the next runtime-backed capability-family move after the accepted tool-facade exposure hold
- Verified from fresh control-lane inspection:
  - existing unsupported `__import__(...)` call sites already surface as explicit `DYNAMIC_IMPORT` boundaries
  - the current runtime-backed attachment seam remains intentionally `importlib.import_module`-specific across `runtime_acquisition.py`, `analyzer.py`, and `tool_facade.py`
  - broader candidate families such as `RUNTIME_MUTATION`, `REFLECTIVE_BUILTIN`, and `METACLASS_BEHAVIOR` would reopen value/state/class-creation semantics earlier than necessary
  - no inspected non-test in-repo consumer currently depends on the importlib-specific seam outside the analyzer/tool-facade/runtime path
- Control review found one issue:
  - the returned proposed next prompt incorrectly labeled the next worker as a control lane rather than an execution lane, which conflicts with `AGENTS.md` lane authority
- Validation/discovery confirmed:
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '70,95p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '700,745p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '413,455p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '74,180p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '354,445p'`
  - `nl -ba tests/test_runtime_acquisition.py | sed -n '421,494p'`
  - `nl -ba src/context_ir/analyzer.py | sed -n '1,80p'`
  - `nl -ba src/context_ir/tool_facade.py | sed -n '1,110p'`
  - `rg -n "importlib_runtime_observations|ImportlibImportModuleRuntimeObservation|attach_importlib_import_module_runtime_provenance" src tests`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "targets_only_import_module_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_named_dynamic_call_boundaries or surfaces_runtime_mutation_call_boundaries or surfaces_reflective_builtin_boundaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "attaches_importlib_runtime_provenance_post_frontier" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "forwards_importlib_runtime_observations" -q`
- Ryan explicitly approved advancing past the role-boundary issue with a control-lane rewrite of the next prompt rather than sending the spike back for correction
- Acceptance decision:
  - accept the planning result content with human sign-off
  - `__import__(...)` is now the smallest truthful next runtime-backed capability-family target
  - the next control action is one bounded planning spike to decide the minimum family-level `DYNAMIC_IMPORT` seam generalization needed before implementation
- Alternatives considered:
  - move next to `RUNTIME_MUTATION`, `REFLECTIVE_BUILTIN`, or `METACLASS_BEHAVIOR`
  - implement `__import__(...)` immediately through the current importlib-specific seam
  - treat `__import__(...)` as a separate sibling seam without first clarifying the family-level boundary
- Reasoning:
  - `__import__(...)` stays inside the already accepted `DYNAMIC_IMPORT` family and additive attachment-to-existing-unsupported-subject pattern
  - current importlib-specific naming makes immediate implementation a contract decision rather than a trivial extension
  - the spike's substantive ranking is sound, but the worker-role wording had to be corrected in the control lane before reuse
- Acceptance status: accepted with human sign-off

## 2026-04-20 -- Post-Tool-Facade Hybrid Exposure Review

- Reviewed the returned planning spike for the next exposure decision after the accepted tool-facade pass-through slice
- Verified from fresh control-lane inspection:
  - the current highest exposed hybrid-entry surface is now `context_ir.tool_facade`:
    - `SemanticContextRequest` accepts optional `importlib_runtime_observations`
    - `compile_repository_context(...)` forwards them into `context_ir.analyzer.analyze_repository(...)`
  - package-root/public low-level `analyze_repository(repo_root) -> SemanticProgram` remains the accepted static-only regression anchor:
    - `ARCHITECTURE.md` still anchors that low-level public contract
    - `semantic_types.py` and `__init__.py` still expose only the static-only wrapper signature
    - public-API regression tests still freeze that boundary
  - MCP widening is not a trivial forwarding move:
    - the live MCP tool schema is still primitive-only (`repo_root`, `query`, `budget`, `include_document`)
    - widening it would require a JSON-safe runtime-observation contract and conversion layer, not just exposing the existing Python dataclass tree
  - no inspected in-repo consumer currently needs broader exposure:
    - `eval_providers.py` already consumes the Python-level tool facade directly
    - no inspected caller requires package-root or MCP access to `importlib_runtime_observations`
- Control review found no issues
- Validation/discovery confirmed:
  - `rg -n "importlib_runtime_observations|compile_repository_context|analyze_repository|runtime-backed|DYNAMIC_IMPORT|provenance_records" src tests PLAN.md BUILDLOG.md ARCHITECTURE.md`
  - `sed -n '1,180p' src/context_ir/tool_facade.py`
  - `sed -n '1,120p' src/context_ir/analyzer.py`
  - `sed -n '1315,1345p' src/context_ir/semantic_types.py`
  - `sed -n '60,150p' src/context_ir/__init__.py`
  - `sed -n '1,180p' src/context_ir/mcp_server.py`
  - `sed -n '200,330p' src/context_ir/eval_providers.py`
  - `PYTHONPATH=src .venv/bin/python -c "import inspect, context_ir, context_ir.analyzer as a, context_ir.semantic_types as st; print('pkg', inspect.signature(context_ir.analyze_repository)); print('semantic_types', inspect.signature(st.analyze_repository)); print('analyzer', inspect.signature(a.analyze_repository))"`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... MCP_SERVER.list_tools() ... PY`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k forwards_importlib_runtime_observations -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py -k "exports_analyze_repository or semantic_module_level_apis_are_not_root_exports" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_mcp_server.py -k "tool_delegates_to_tool_facade or output_is_json_safe_and_complete or mcp_server_registers_exactly_one_compile_tool" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_providers.py -k context_ir_provider_delegates_to_facade_with_no_embed_fn -q`
- Acceptance decision:
  - accept the planning spike
  - keep `context_ir.tool_facade` as the highest exposed hybrid entry point for this seam for now
  - do not authorize package-root/public low-level or MCP widening on this seam yet
- Alternatives considered:
  - widen package-root/public low-level `analyze_repository(...)`
  - widen MCP input schema and tool contract
  - continue exposing the seam upward immediately because it is technically possible
- Reasoning:
  - package-root widening would reopen the most stable public low-level contract without a present in-repo consumer need
  - MCP widening would require a new JSON-safe observation contract and conversion layer, which is materially larger than a forwarding change
  - the accepted tool-facade surface already satisfies the only inspected in-repo hybrid-entry consumer path
- Acceptance status: first-pass

## 2026-04-20 -- Runtime-Backed Tool-Facade Pass-Through Review

- Reviewed the returned implementation slice for narrow tool-facade input pass-through on the accepted `importlib_runtime_observations` seam
- Verified from fresh control-lane inspection:
  - `context_ir.tool_facade.SemanticContextRequest` now accepts optional `importlib_runtime_observations` typed to the accepted `ImportlibImportModuleRuntimeObservation` contract
  - `compile_repository_context(...)` forwards that field into `context_ir.analyzer.analyze_repository(...)` only when explicitly supplied
  - omitting the field preserves the exact accepted pre-slice tool-facade analyzer call path
  - package-root/public low-level `context_ir.analyze_repository(...)` and `context_ir.semantic_types.analyze_repository(...)` signatures remain unchanged
  - MCP-visible inputs and JSON response shape remain unchanged
- Control review found no issues
- Validation confirmed:
  - `git diff -- src/context_ir/tool_facade.py tests/test_tool_facade.py`
  - `sed -n '1,180p' src/context_ir/tool_facade.py`
  - `sed -n '1,280p' tests/test_tool_facade.py`
  - `sed -n '1,220p' tests/test_public_api.py`
  - `sed -n '1,220p' tests/test_mcp_server.py`
  - `.venv/bin/python -m ruff check src/context_ir/tool_facade.py tests/test_tool_facade.py tests/test_public_api.py tests/test_mcp_server.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/tool_facade.py tests/test_tool_facade.py tests/test_public_api.py tests/test_mcp_server.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/tool_facade.py`
  - `.venv/bin/python -m pytest tests/test_tool_facade.py tests/test_public_api.py tests/test_mcp_server.py -v`
  - `git diff --check -- src/context_ir/tool_facade.py tests/test_tool_facade.py tests/test_public_api.py tests/test_mcp_server.py`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... signature guard ... PY`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v`
- Acceptance decision:
  - accept the implementation slice
  - the next control action is one bounded planning spike to decide the next truthful hybrid-entry exposure boundary beyond explicit module-level tool-facade callers
- Reasoning:
  - this slice exposes the already-accepted analyzer seam one layer upward without widening package-root/public low-level or MCP-visible contracts
  - the next smallest truthful question is which surface, if any, should widen next, not immediate further contract expansion
- Acceptance status: first-pass

## 2026-04-20 -- Runtime-Backed Exposure-Boundary Planning Review

- Reviewed the returned planning spike for the next move after the accepted first runtime-backed hybrid implementation slice
- Verified from fresh control-lane inspection:
  - the accepted analyzer seam is still narrow and phase-0-safe:
    - `context_ir.analyzer.analyze_repository(...)` exposes optional `importlib_runtime_observations`
    - the default path still returns the exact accepted static-only semantic program when no runtime observations are supplied
  - a narrow tool-facade pass-through is possible without widening response shape:
    - `SemanticContextRequest` is the only tool-facing input contract that needs an optional field
    - `compile_repository_context(...)` is the only forwarding seam needed to pass observations into `analyze_repository(...)`
    - the returned `SemanticContextResponse` already carries the full `SemanticProgram`, so no response-shape change is required
  - widening package-root/public low-level contracts would reopen an accepted boundary:
    - `context_ir.analyze_repository(...)` and `context_ir.semantic_types.analyze_repository(...)` still expose the phase-0 low-level `analyze_repository(repo_root) -> SemanticProgram` signature
    - `ARCHITECTURE.md` still anchors that low-level public contract
  - MCP does not need to widen for the next step:
    - `mcp_server.py` still accepts only `repo_root`, `query`, `budget`, and `include_document`
    - MCP JSON output shape remains fixed and current tests freeze that surface
- Control review found no issues
- Validation/discovery confirmed:
  - `rg -n "importlib_runtime_observations|compile_repository_context|analyze_repository|runtime-backed|DYNAMIC_IMPORT|provenance_records" src tests PLAN.md BUILDLOG.md ARCHITECTURE.md`
  - `sed -n '1,140p' src/context_ir/analyzer.py`
  - `sed -n '1,140p' src/context_ir/tool_facade.py`
  - `sed -n '1,140p' src/context_ir/__init__.py`
  - `sed -n '1,160p' src/context_ir/mcp_server.py`
  - `sed -n '1310,1355p' src/context_ir/semantic_types.py`
  - `PYTHONPATH=src .venv/bin/python -c "import inspect, context_ir, context_ir.analyzer as a, context_ir.semantic_types as st; print('pkg', inspect.signature(context_ir.analyze_repository)); print('semantic_types', inspect.signature(st.analyze_repository)); print('analyzer', inspect.signature(a.analyze_repository))"`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "matches_manual_pipeline or import_paths_accept_path_and_str or attaches_importlib_runtime_provenance_post_frontier" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_facade.py -k "returns_typed_response_for_simple_repo or uses_analyzer_and_semantic_compiler or tool_facade_does_not_change_package_root_exports" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_public_api.py -k "exports_analyze_repository or semantic_module_level_apis_are_not_root_exports" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_mcp_server.py -k "mcp_tool_delegates_to_tool_facade or mcp_server_registers_exactly_one_compile_tool or mcp_server_does_not_change_package_root_exports" -q`
- Acceptance decision:
  - accept the planning spike
  - the next control action is one bounded implementation slice for narrow tool-facade input pass-through only
- Alternatives considered:
  - widen package-root/public low-level `analyze_repository(...)` contracts now
  - widen MCP input/output contracts now
  - keep the accepted analyzer seam internal for longer
- Reasoning:
  - tool-facade pass-through is the smallest truthful exposure step because it reuses the accepted analyzer seam, preserves additive provenance behavior, and avoids widening public low-level or MCP-visible contracts prematurely
  - package-root and MCP expansion would reopen more stable surfaces than necessary for the next hybrid step
- Acceptance status: first-pass

## 2026-04-20 -- First Runtime-Backed Hybrid Implementation Review

- Reviewed the returned implementation slice for additive runtime-backed provenance on existing unsupported `DYNAMIC_IMPORT` findings backed by `importlib.import_module` forms only
- Verified from fresh control-lane inspection:
  - `analyze_repository(...)` now accepts narrow optional `importlib_runtime_observations` input and still preserves the exact accepted static-only pipeline when no runtime observations are supplied
  - `runtime_acquisition.py` now attaches admissible runtime-backed provenance only to existing unsupported `DYNAMIC_IMPORT` subjects for:
    - direct `importlib.import_module(...)`
    - imported `import_module(...)` and imported alias forms
    - root-module alias forms such as `loader.import_module(...)`
  - `__import__(...)` and non-`DYNAMIC_IMPORT` unsupported families remain untouched by the new attachment path
  - optimizer trace summaries and diagnostic wording still treat the affected units as primary unsupported/opaque with additive runtime-backed provenance rather than relabeling static truth
  - `tool_facade.py` remains unchanged, so the accepted seam is analyzer-level only for now
- Control review found no issues
- Validation confirmed:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "matches_manual_pipeline or import_paths_accept_path_and_str" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "accepts_frontier_and_unsupported_subjects" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_semantic_optimizer.py -k "emits_tier_aware_trace_summaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_semantic_diagnostics.py -k "warning_trace_summary_for_omitted_unsupported" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_named_dynamic_call_boundaries or surfaces_imported_import_module_boundaries or surfaces_root_importlib_alias_boundaries or surfaces_runtime_mutation_call_boundaries or surfaces_reflective_builtin_boundaries or surfaces_metaclass_keywords_as_unsupported" -q`
  - direct control-lane repro: existing unsupported `importlib.import_module`-family subjects receive attached runtime-backed provenance, while `__import__(...)` does not
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v`
- Acceptance decision:
  - accept the implementation slice
  - the next control action is one bounded planning spike to decide whether the accepted analyzer-level `importlib_runtime_observations` seam should be exposed through a narrow tool/package-root pass-through or intentionally kept internal for now
- Reasoning:
  - this slice lands the first real hybrid static+runtime step without widening primary subject truth, user-facing response shapes, or public claims
  - the next smallest truthful question is exposure boundary, not another runtime-backed subject family or broader probe surface
- Acceptance status: first-pass

## 2026-04-20 -- First Runtime-Backed Hybrid Slice Planning Review

- Reviewed the returned planning spike for the first true runtime-backed phase-2 hybrid-coverage slice
- Verified from fresh control-lane inspection:
  - the current analyzer/tool path is still static-only:
    - `analyze_repository(...)` remains extract -> bind -> resolve -> dependency/frontier derivation with no runtime-backed attachment step
    - `compile_repository_context(...)` still consumes that static-only analyzer output directly
  - the runtime-backed plumbing needed for a first additive slice already exists:
    - `runtime_acquisition.py` attaches admissible runtime-backed provenance to existing frontier and unsupported subjects without mutating primary subject truth
    - optimizer trace summaries and diagnostic surfaces already carry attached runtime-backed provenance additively on existing unsupported/frontier units
  - the cleanest first target family is existing unsupported `DYNAMIC_IMPORT`, narrowed further to `importlib.import_module` forms only:
    - `dependency_frontier.py` already emits stable unsupported `DYNAMIC_IMPORT` subjects for direct `importlib.import_module(...)`
    - imported `import_module(...)` and imported alias forms already emit the same stable unsupported family
    - root-module alias forms such as `loader.import_module(...)` already emit the same stable unsupported family
  - starting with new runtime-backed dependency or symbol subjects would widen the current renderable/trace contract more than necessary because the accepted trace-summary path currently keys off existing symbols, frontier items, and unsupported findings
  - the remaining candidate families are larger first moves:
    - `__import__(...)` remains later within `DYNAMIC_IMPORT`
    - `REFLECTIVE_BUILTIN` and `RUNTIME_MUTATION` pull value/state semantics earlier
    - `METACLASS_BEHAVIOR` pulls broader class-creation semantics earlier
- Control review found no issues
- Validation/discovery confirmed:
  - `rg -n "runtime_acquisition|attach_runtime_observations|provenance_records|runtime-backed|DYNAMIC_IMPORT|RUNTIME_MUTATION|REFLECTIVE_BUILTIN|METACLASS_BEHAVIOR" src tests PLAN.md BUILDLOG.md ARCHITECTURE.md`
  - `nl -ba src/context_ir/analyzer.py | sed -n '1,80p'`
  - `nl -ba src/context_ir/tool_facade.py | sed -n '70,100p'`
  - `nl -ba src/context_ir/runtime_acquisition.py | sed -n '70,140p'`
  - `nl -ba src/context_ir/semantic_optimizer.py | sed -n '340,430p'`
  - `nl -ba src/context_ir/semantic_diagnostics.py | sed -n '603,695p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '620,740p'`
  - `nl -ba tests/test_runtime_acquisition.py | sed -n '330,390p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '400,520p'`
  - `nl -ba tests/test_analyzer.py | sed -n '1,90p'`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_analyzer.py -k "matches_manual_pipeline or import_paths_accept_path_and_str" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_acquisition.py -k "accepts_frontier_and_unsupported_subjects" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_semantic_optimizer.py -k "emits_tier_aware_trace_summaries" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_semantic_diagnostics.py -k "warning_trace_summary_for_omitted_unsupported" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "surfaces_named_dynamic_call_boundaries or surfaces_imported_import_module_boundaries or surfaces_root_importlib_alias_boundaries or surfaces_runtime_mutation_call_boundaries or surfaces_reflective_builtin_boundaries or surfaces_metaclass_keywords_as_unsupported" -q`
- Acceptance decision:
  - accept the planning spike
  - the next control action is one bounded implementation slice for additive runtime-backed provenance on existing unsupported `DYNAMIC_IMPORT` findings backed by `importlib.import_module` forms only
- Alternatives considered:
  - continue inherited-call widening despite the accepted hold
  - start with `__import__(...)` as part of the first runtime-backed slice
  - start with `REFLECTIVE_BUILTIN`, `RUNTIME_MUTATION`, or `METACLASS_BEHAVIOR`
  - introduce new runtime-backed dependency or symbol subjects in the first slice
- Reasoning:
  - this is the smallest truthful first hybrid step that actually advances the north star instead of further squeezing a parked static edge-case lane
  - existing unsupported `DYNAMIC_IMPORT` subjects plus additive runtime-backed attachment keep the first slice reviewable and contract-bounded
  - broader dynamic families and new runtime-backed subject creation remain later because they widen semantics and downstream contracts more aggressively
- Acceptance status: first-pass

## 2026-04-20 -- Next North-Star Move Sequencing Decision

- Reviewed current repo reality to decide the next move after the accepted inherited-call hold
- Verified from fresh control-lane inspection:
  - the post-milestone north star remains broad Python repo coverage through hybrid static + runtime analysis with explicit capability tiers
  - the inherited-call branch is intentionally parked:
    - first-exclusive-branch overlap is accepted in workspace authority
    - further inherited-call widening is already on explicit hold because the remaining deltas require broader blocked-owner eligibility or non-linear ancestry/MRO semantics
  - the runtime-backed contract and plumbing now exist:
    - phase-1 capability-tier contract work is complete
    - `runtime_acquisition.py` provides admissible runtime-backed provenance attachment against existing semantic subjects
    - compile, optimization, and diagnose layers already preserve additive runtime-backed provenance distinctly from static proof
  - the repo is still not actually on a hybrid analysis path yet:
    - `analyze_repository(...)` remains parse -> bind -> resolve -> frontier with no runtime-backed acquisition step
    - `compile_repository_context(...)` still consumes the static-only analyzer output directly
    - no concrete runtime probe family is yet selected or wired into the accepted analyzer/tool path
  - stable unsupported boundary families already exist for a first runtime-backed planning pass, including `DYNAMIC_IMPORT`, `RUNTIME_MUTATION`, `REFLECTIVE_BUILTIN`, and `METACLASS_BEHAVIOR`
- Control decision:
  - keep inherited-call implementation on the accepted explicit hold
  - make the next north-star move one bounded planning spike for the first true runtime-backed phase-2 hybrid-coverage slice
- Reasoning:
  - continuing to squeeze static inherited-call edge cases is now lower leverage than starting the first real hybrid-analysis path the north star actually names
  - the infrastructure needed to carry runtime-backed provenance is already in place, but no probe family or integration boundary has been decomposed yet
  - a planning spike is the smallest truthful next move because the first runtime-backed target still needs an explicit subject family, replay contract, and analyzer/tool-facade boundary before implementation is authorized
- Acceptance status: first-pass

## 2026-04-20 -- Post-First-Exclusive-Overlap Inherited-Call Planning Spike Review

- Reviewed the returned bounded planning spike for the next truthful inherited-call follow-on beyond the accepted first-exclusive-branch overlap reopening
- Verified from fresh control-lane inspection:
  - the current resolver-owned proof ladder is still same-class -> direct-base -> linear single-chain transitive -> declared-order branched disjoint -> first-owner overlap -> transitive sole-provider overlap fallback
  - the current accepted positives already exhaust the repo-backed proof shapes inside the existing overlap contract:
    - shared-tail sole-provider overlap resolves
    - later-owner overlap resolves when earlier overlap branches are silent
    - first-exclusive-branch overlap now resolves the tested two-branch and three-branch overlap-specific multi-owner shapes
  - earlier-ineligible overlap is not a smaller remaining precedence gap:
    - runtime lands on the earlier blocked binding
    - the resolver and wider inherited-call surface already reject decorated or otherwise ineligible blockers rather than skipping them
    - reopening only overlap here would implicitly widen blocked-owner eligibility semantics beyond this seam
  - non-linear overlap is structurally larger than the accepted contract:
    - current branch helpers still require each direct-base branch to remain individually linear before any shared-tail reasoning applies
    - runtime determinism in the tested non-linear repro would require new ancestry/MRO handling rather than a narrower overlap tweak
  - no narrower repo-backed missed proof was found between the accepted first-exclusive-branch overlap boundary and broader overlapping/shared-ancestor or C3-style behavior
- Control review found no issues
- Validation/discovery confirmed:
  - `rg -n "earlier|blocked|non-linear|overlap|shared|diamond|precedence|branched|transitive|ancestor|C3|exclusive" src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py PLAN.md BUILDLOG.md ARCHITECTURE.md`
  - `nl -ba src/context_ir/resolver.py | sed -n '680,1185p'`
  - `nl -ba src/context_ir/resolver.py | sed -n '1200,1609p'`
  - `nl -ba tests/test_resolver.py | sed -n '1038,1388p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '1940,2295p'`
  - `nl -ba PLAN.md | sed -n '136,150p'`
  - `nl -ba PLAN.md | sed -n '271,281p'`
  - `nl -ba BUILDLOG.md | sed -n '1,24p'`
  - `nl -ba ARCHITECTURE.md | sed -n '1,120p'`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -k "later_owner_overlap_when_earlier_silent or overlap_multi_owner_to_first_exclusive_owner or three_branch_overlap_to_first_exclusive_owner or earlier_ineligible_overlap_unresolved or non_linear_overlap_unresolved or overlapping_shared_ancestor_sole_providers" -q`
  - `python3 - <<'PY' ... earlier_ineligible_mro -> Child, LeftBridge, LeftBlocked, RightOwner, SharedTop, object; earlier_ineligible_target -> LeftBlocked.helper; earlier_ineligible_value -> blocked; nonlinear_mro -> NonLinearChild, NonLinearBranch, ForkLeft, ForkRight, Left, Shared, object; nonlinear_target -> Shared.helper; nonlinear_value -> shared ... PY`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... earlier_ineligible_overlap -> UNRESOLVED; non_linear_overlap -> UNRESOLVED ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
  - `rg -n "blocks_self_call_proof_for_earlier_shadowed_branch_owners|staticmethod|decorated_definition_ids|_resolve_unique_owned_undecorated_method_definition" src/context_ir/resolver.py tests/test_resolver.py`
- Acceptance decision:
  - accept the planning spike
  - maintain an explicit hold on further inherited-call implementation beyond the accepted first-exclusive-branch overlap boundary
- Alternatives considered:
  - reopen earlier-ineligible overlap next
  - reopen non-linear overlap next
  - jump to broader overlapping/shared-ancestor or fuller C3-style inherited-call handling
- Reasoning:
  - the remaining runtime deltas no longer fit a reviewable one-helper widening
  - earlier-ineligible overlap would require a broader eligibility-policy decision, not just another precedence tweak
  - non-linear overlap would require broader ancestry/MRO semantics beyond the current individually-linear shared-tail contract
- Acceptance status: first-pass

## 2026-04-20 -- First-Exclusive-Branch Overlap Review

- Reviewed the returned `resolver.py` slice for first exclusive-branch owner precedence on individually linear overlapping/shared-ancestor inherited `self.foo()` branches
- Verified from fresh control-lane inspection:
  - the accepted resolver proof ladder now truthfully covers the intended overlap-specific precedence reopening:
    - when direct-base branches are individually linear, a real shared tail exists, and the first declared-order exclusive-branch binding is a unique owned undecorated method, canonical inherited `self.foo()` now resolves to that first exclusive-branch owner
  - accepted earlier overlap reopenings remain intact:
    - the later-owner overlap positive still resolves when earlier overlap branches are silent
    - the shared-tail sole-provider overlap fallback still resolves the accepted diamond/shared-provider shape
  - accepted conservative overlap boundaries remain intact:
    - earlier-ineligible overlap remains unresolved
    - non-linear overlap remains unresolved
  - the widened overlap precedence now closes the concrete repo-backed missed-proof cases:
    - the tested two-branch overlap-specific multi-owner shape now resolves to `LeftOwner.helper`
    - the tested three-branch individually linear overlap shape now resolves to `SecondOwner.helper`
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... later_owner -> RightDiamondBridge.helper; multi_owner_overlap -> LeftOwner.helper; three_branch_multi_owner_overlap -> SecondOwner.helper; earlier_ineligible -> UNRESOLVED; nonlinear -> UNRESOLVED; diamond_shared_provider -> Shared.helper; first_branch_owner -> FirstOwner.helper ... PY`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v`
- Acceptance decision:
  - accept the first-exclusive-branch overlap slice
  - the next control action is one bounded inherited-call planning spike for the smallest truthful follow-on beyond the accepted first-exclusive-branch overlap reopening, with explicit focus on earlier-ineligible overlap, non-linear overlap, and fuller overlapping/shared-ancestor boundaries
- Alternatives considered:
  - keep treating overlap-specific multi-owner shapes as unresolved
  - reopen earlier-ineligible overlap next
  - jump to broader overlapping/shared-ancestor or fuller C3-style inherited-call handling
- Reasoning:
  - this closes concrete repo-backed missed proofs without reopening blocked-earlier-owner or non-linear overlap semantics
  - the accepted widening reuses existing ordered-branch and shared-tail machinery rather than requiring new ancestry contracts
  - earlier-ineligible overlap and non-linear overlap still require a separate truth-finding pass before any broader reopening is authorized
- Acceptance status: first-pass

## 2026-04-20 -- Post-Later-Owner-Overlap Inherited-Call Planning Spike Review

- Reviewed the returned bounded planning spike for the next truthful inherited-call follow-on beyond the accepted later-owner overlap reopening
- Verified from fresh control-lane inspection:
  - the current resolver-owned proof ladder is still same-class -> direct-base -> linear single-chain transitive -> declared-order branched disjoint -> later-owner overlap -> transitive sole-provider overlap fallback
  - the repo and runtime now show one smaller remaining missed proof on individually linear overlap:
    - in overlap-specific multi-owner shapes, Python MRO deterministically picks the first exclusive-branch owner in declared-order layout
    - the repo resolver still leaves those same shapes unresolved today
  - the current overlap seam already has the necessary ancestry contract:
    - it uses ordered individually linear branches plus shared-tail detection
    - it scans exclusive branch segments before the shared tail
    - it currently bails out on a second eligible owner or any ineligible earlier binding
  - broader overlap is still not yet truthful to reopen generally:
    - earlier-ineligible overlap resolves at runtime to the earlier blocked binding, so the resolver must not skip blocked earlier owners
    - non-linear overlap still exceeds the current ordered-linear shared-tail contract
  - docs-only or boundary-hardening follow-on work is not the smallest move because the current unresolved overlap boundaries are already pinned in both resolver and dependency-frontier tests
- Control review found no issues
- Validation/discovery confirmed:
  - `rg -n "later-owner|multi-owner|earlier|blocked|overlap|shared|diamond|precedence|branched|transitive|ancestor|C3|linear|direct-base|sole-provider" src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py PLAN.md BUILDLOG.md ARCHITECTURE.md`
  - `nl -ba src/context_ir/resolver.py | sed -n '690,820p'`
  - `nl -ba src/context_ir/resolver.py | sed -n '1130,1628p'`
  - `nl -ba tests/test_resolver.py | sed -n '1040,1388p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '1900,2348p'`
  - `nl -ba PLAN.md | sed -n '141,145p'`
  - `nl -ba BUILDLOG.md | sed -n '1,40p'`
  - `nl -ba ARCHITECTURE.md | sed -n '300,326p'`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_resolver.py -k "overlapping_shared_ancestor_sole_providers or later_owner_overlap_when_earlier_silent or overlap_multi_owner_ambiguity_unresolved or earlier_ineligible_overlap_unresolved or non_linear_overlap_unresolved or blocks_self_call_proof_for_earlier_shadowed_branch_owners" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "overlapping_shared_ancestor_sole_providers or later_owner_overlap_when_earlier_silent or overlap_multi_owner_ambiguity_unresolved or earlier_ineligible_overlap_unresolved or non_linear_overlap_unresolved or blocks_earlier_shadowed_self_calls" -q`
  - `python3 - <<'PY' ... multi_owner_runtime -> left via LeftOwner.helper; earlier_ineligible_runtime -> blocked via LeftBlocked.helper; three_branch_multi_owner_runtime -> second via SecondOwner.helper ... PY`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... later_owner_overlap -> RightDiamondBridge.helper; multi_owner_overlap -> UNRESOLVED; earlier_ineligible_overlap -> UNRESOLVED; three_branch_multi_owner_overlap -> UNRESOLVED ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
- Acceptance decision:
  - accept the planning spike
  - the next control action is one bounded resolver-only implementation slice for first exclusive-branch owner precedence on individually linear overlapping/shared-ancestor inherited `self.foo()` branches, while preserving earlier-ineligible overlap and non-linear overlap as unresolved
- Alternatives considered:
  - hold on docs-only or hardening-only follow-up work
  - reopen earlier-ineligible overlap next
  - jump to broader overlapping/shared-ancestor or fuller C3-style inherited-call handling
- Reasoning:
  - the overlap-specific multi-owner shapes tested here are not actual Python ambiguity; they are concrete repo-backed missed proofs with a stable first-exclusive-branch winner
  - earlier-ineligible overlap must remain unresolved because runtime selects the earlier blocked binding, so widening that shape next would require broader eligibility semantics than the smaller precedence reopening
  - non-linear overlap remains larger than the current resolver-owned contract because the existing helpers only justify individually linear branches with a real shared tail
- Acceptance status: first-pass

## 2026-04-19 -- Later-Owner Overlap Review and Quality-Gate Correction

- Reviewed the returned `resolver.py` slice for later-owner precedence on individually linear overlapping/shared-ancestor inherited `self.foo()` branches, plus the bounded correction required to clear the full regression gate
- Verified from fresh control-lane inspection:
  - the accepted resolver proof ladder now truthfully covers the intended later-owner overlap shape:
    - when direct-base branches are individually linear, a shared tail exists, all earlier declared-order overlap branches are silent for the target name, and exactly one later branch owner appears before the shared tail, canonical inherited `self.foo()` now resolves to that later branch owner
  - accepted conservative overlap boundaries remain intact:
    - overlap-specific multi-owner ambiguity remains unresolved
    - earlier ineligible overlap remains unresolved
    - non-linear overlap remains unresolved
  - the quality-gate correction is bounded and does not reopen resolver semantics:
    - the slow default-embedding integration test now checks for a locally cached `all-MiniLM-L6-v2` model and skips with a clear reason when the model is unavailable offline
    - the stale semantic-scorer uncertainty test now uses `pkg.helpers.helper.extra()` as the unsupported surface, while accepted import-rooted `pkg.helpers.helper()` behavior remains resolved and repository-backed
- Control review found no issues
- Validation confirmed:
  - `git diff -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `nl -ba src/context_ir/resolver.py | sed -n '1128,1665p'`
  - `nl -ba tests/test_resolver.py | sed -n '1030,1295p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '1890,2188p'`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... later_owner -> RightDiamondBridge.helper; multi_owner_overlap -> UNRESOLVED; earlier_ineligible -> UNRESOLVED; nonlinear -> UNRESOLVED ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
  - `python3 - <<'PY' ... later_owner_runtime -> right; multi_owner_runtime -> left; earlier_ineligible_runtime -> blocked ... PY`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... three_branch_late_owner -> Third.helper; first_branch_owner_should_stay_blocked -> UNRESOLVED; shared_tail_only_should_not_reopen -> Shared.helper ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
  - `python3 - <<'PY' ... three_branch_late_owner_runtime -> third; first_branch_owner_runtime -> first ... PY`
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `git diff -- tests/test_scorer.py tests/test_semantic_scorer.py`
  - `.venv/bin/python -m ruff check tests/test_scorer.py tests/test_semantic_scorer.py src/context_ir/scorer.py`
  - `.venv/bin/python -m ruff format --check tests/test_scorer.py tests/test_semantic_scorer.py src/context_ir/scorer.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/scorer.py`
  - `.venv/bin/python -m pytest tests/test_scorer.py -k default_embed_integration -v`
  - `.venv/bin/python -m pytest tests/test_semantic_scorer.py -k relevant_scope_support_for_uncertainty_items -v`
  - `git diff --check -- tests/test_scorer.py tests/test_semantic_scorer.py src/context_ir/scorer.py`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v`
- Acceptance decision:
  - accept the later-owner overlap reopening slice
  - accept the bounded quality-gate correction that cleared the full regression blockers
  - the next control action is one bounded planning spike for the next truthful inherited-call follow-on beyond the accepted later-owner overlap reopening, focused on overlap-specific multi-owner ambiguity, earlier-ineligible overlap, and fuller overlapping/shared-ancestor boundaries
- Alternatives considered:
  - accept the later-owner slice despite the red full-suite gate
  - reopen broader overlap implementation immediately
  - treat the stale semantic-scorer expectation as a resolver regression and reopen accepted lower-layer semantics
- Reasoning:
  - the later-owner gap was a concrete repo-backed missed proof and is now closed without widening into overlap-specific multi-owner, blocked-earlier-owner, or non-linear overlap semantics
  - the quality gate required a green full regression suite before continuity could advance, so the unrelated red tests had to be corrected rather than waived
  - the next truthful move is planning rather than another implementation slice because the remaining overlap cases are order-sensitive or ambiguity-sensitive in ways that exceed the now-accepted narrower reopening
- Acceptance status: after 1 correction

## 2026-04-19 -- Post-Shared-Ancestor-Overlap Inherited-Call Planning Spike Review

- Reviewed the returned bounded planning spike for the next truthful inherited-call follow-on beyond the accepted shared-ancestor sole-provider overlap reopening
- Verified from fresh control-lane inspection:
  - the current resolver-owned proof ladder is still same-class -> direct-base -> linear single-chain transitive -> declared-order branched -> transitive sole-provider overlap fallback
  - the repo and runtime now show one narrower order-sensitive missed proof:
    - a later-owner overlap case resolves at runtime to the later branch owner when earlier declared-order overlap branches are silent
    - the repo resolver still leaves that later-owner overlap case unresolved today
  - broader overlap still remains larger than the smallest truthful next slice:
    - an overlap-specific multi-owner case resolves at runtime but would require broader target-selection semantics than a one-owner later-branch reopening
    - an earlier-ineligible overlap case resolves at runtime to the earlier blocked owner, so the next slice must not skip blocked earlier branches
    - non-linear overlap remains structurally larger and still belongs on the unresolved path for now
  - overlap-specific multi-owner negatives are documented in continuity but are not yet pinned as their own dedicated overlap regression pair
- Control review found no issues
- Validation/discovery confirmed:
  - `rg -n "later-owner|multi-owner|overlap|shared|diamond|precedence|branched|transitive|ancestor|C3" src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py PLAN.md BUILDLOG.md ARCHITECTURE.md`
  - `nl -ba src/context_ir/resolver.py | sed -n '736,1165p'`
  - `nl -ba src/context_ir/resolver.py | sed -n '1361,1455p'`
  - `nl -ba tests/test_resolver.py | sed -n '722,1235p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '1539,2065p'`
  - `nl -ba PLAN.md | sed -n '130,145p'`
  - `nl -ba PLAN.md | sed -n '256,262p'`
  - `nl -ba BUILDLOG.md | sed -n '1,34p'`
  - `nl -ba ARCHITECTURE.md | sed -n '210,225p'`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_resolver.py -k "resolves_linear_transitive_self_calls_to_nearest_owner or resolves_branched_self_calls_by_declared_base_order or prefers_earlier_transitive_over_later_direct_base or resolves_overlapping_shared_ancestor_sole_providers or leaves_blocked_later_owner_or_non_linear_overlap_unresolved or resolves_transitive_self_calls_only_for_sole_providers" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "proves_linear_self_calls_to_nearest_owner or proves_branched_self_calls_by_declared_base_order or prefers_earlier_transitive_over_later_direct_base or proves_overlapping_shared_ancestor_sole_providers or leaves_overlap_edge_cases_unresolved or proves_transitive_sole_provider_self_calls" -q`
  - `python3 - <<'PY' ... later-owner overlap runtime repro ... MRO ... runtime target RightDiamondBridge.helper ... PY`
  - `python3 - <<'PY' ... overlap-specific multi-owner runtime repro ... MRO ... runtime target LeftOwner.helper ... PY`
  - `python3 - <<'PY' ... earlier-ineligible overlap runtime repro ... MRO ... runtime target LeftBlocked.helper ... PY`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... later_owner_overlap UNRESOLVED; multi_owner_overlap UNRESOLVED; earlier_ineligible_overlap UNRESOLVED ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
- Acceptance decision:
  - accept the planning spike
  - the next control action is one bounded resolver-only implementation slice for later-owner precedence on individually linear overlapping/shared-ancestor inherited `self.foo()` branches, while preserving overlap-specific multi-owner ambiguity, earlier ineligible owners, and non-linear overlap as unresolved
- Alternatives considered:
  - keep all order-sensitive overlap unresolved for now
  - reopen overlap-specific multi-owner handling next
  - jump to broader overlapping/shared-ancestor or fuller C3-style inherited-call handling
- Reasoning:
  - keeping all order-sensitive overlap unresolved would leave a concrete repo-backed missed proof unaddressed even though the repo already preserves the declared-order ancestry facts needed for the narrower later-owner reopening
  - multi-owner overlap and broader overlapping/shared-ancestor handling are larger because they require wider target-selection semantics and tighter ambiguity rules than the one-owner later-branch case
  - earlier ineligible-owner behavior proves the next slice must preserve the existing “do not skip blocked earlier branches” rule, which keeps the later-owner-only reopening reviewable and bounded
- Acceptance status: first-pass

## 2026-04-19 -- Overlapping Shared-Ancestor Sole-Provider Review

- Reviewed the returned `resolver.py` slice plus targeted resolver and dependency-frontier regressions for overlapping linear shared-ancestor sole-provider inherited `self.foo()` widening
- Verified from fresh control-lane inspection:
  - the transitive sole-provider seam now permits overlap only when each direct-base branch is individually linear, while the accepted declared-order linear-disjoint branch seam remains unchanged
  - the repo now truthfully proves the intended narrow shared-ancestor cases:
    - pure diamond/shared-provider `self.helper()` now resolves to the shared non-direct owner
    - overlapping non-diamond shared-provider `self.helper()` now resolves to the same shared non-direct owner
  - accepted conservative boundaries remain intact:
    - later-owner overlap still remains unresolved
    - multi-owner overlap still remains unresolved through the unique-owner guard
    - earlier ineligible owners still block proof
    - non-linear overlap still remains unresolved
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... diamond/shared-provider -> Shared.helper; overlapping shared-provider -> Shared.helper; later-owner -> UNRESOLVED; nonlinear -> UNRESOLVED ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
  - `python3 - <<'PY' ... class Shared ... class Left(Shared) ... class RightBridge(Shared) ... class Right(RightBridge) ... class Child(Left, Right) ... print(Child.__mro__, Child().helper()) ... PY`
- Acceptance decision:
  - accept the overlapping shared-ancestor sole-provider widening slice
  - the next control action is one bounded planning spike for the next inherited-call follow-on beyond the accepted shared-ancestor sole-provider overlap reopening, focused on later-owner precedence, multi-owner overlap, and fuller overlapping/shared-ancestor boundaries
- Reasoning:
  - the slice closes a truthful missed-proof seam without reopening order-sensitive overlap or generic C3 handling
  - broader overlapping/shared-ancestor behavior still needs bounded planning because branch order can change the answer once a later owner or multiple owners appear
- Acceptance status: first-pass

## 2026-04-19 -- Post-Linear-Branch-Precedence Inherited-Call Planning Spike Review

- Reviewed the returned bounded planning spike for the next truthful inherited-call follow-on beyond the accepted linear disjoint branch-precedence rule
- Verified from fresh control-lane inspection:
  - the current resolver-owned proof ladder is still same-class -> direct-base -> linear single-chain transitive -> declared-order branched -> transitive sole-provider
  - the repo now already preserves the key ancestry state this follow-on needs:
    - direct proven bases retain declared order
    - transitive ancestor closure is deduped and stable enough to inspect shared non-direct owners
  - the current unresolved pure diamond/shared-provider case is a truthful missed proof today:
    - Python runtime resolves `Child(Left, Right).helper()` to `Shared.helper`
    - the repo resolver still leaves that case unresolved under the current conservative overlap guard
  - broader overlap is still not yet truthful to reopen generally:
    - a later-owner overlapping/shared-ancestor case still resolves at runtime to the later branch owner
    - the repo resolver also leaves that case unresolved today
    - therefore order-sensitive overlap, multi-owner overlap, and non-linear overlap remain larger than the smallest truthful next slice
- Control review found no issues
- Validation/discovery confirmed:
  - `rg -n "direct_base|linear|branched|transitive|ancestor|diamond|shared|branch|base order|precedence" src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py PLAN.md BUILDLOG.md ARCHITECTURE.md`
  - `nl -ba src/context_ir/resolver.py | sed -n '700,1165p'`
  - `nl -ba src/context_ir/resolver.py | sed -n '1340,1455p'`
  - `nl -ba tests/test_resolver.py | sed -n '940,1095p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '1785,1925p'`
  - `python3 - <<'PY' ... class Shared ... class Left(Shared) ... class Right(Shared) ... class Child(Left, Right) ... print(Child.__mro__, Child().helper()) ... PY`
  - `python3 - <<'PY' ... class Root ... class Left(Root) ... class Right(Root): def helper ... class Child(Left, Right) ... print(Child.__mro__, Child().helper()) ... PY`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... diamond -> UNRESOLVED; later_owner -> UNRESOLVED ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_resolver.py -k "declared_base_order or earlier_transitive_over_later_direct_base or blocked_or_non_linear_branched_self_calls_unresolved" -q`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dependency_frontier.py -k "declared_base_order or earlier_transitive_over_later_direct_base or blocked_branched_self_calls_unresolved" -q`
- Acceptance decision:
  - accept the planning spike
  - the next control action is one bounded resolver-only implementation slice for overlapping linear shared-ancestor sole-provider inherited `self.foo()` widening, including the pure diamond case
- Alternatives considered:
  - keep all overlapping/shared-ancestor shapes unresolved for now
  - reopen broader overlap including later-owner precedence cases
  - jump to generic or fuller C3-style inherited-call handling
- Reasoning:
  - keeping all overlap unresolved would leave a now-demonstrated truthful missed proof on the table even though the repo already has enough ancestry state to support it conservatively
  - reopening broader overlap would overclaim because later-owner precedence still depends on branch order and exceeds the smallest truthful boundary
  - fuller C3-style handling is materially larger than the current resolver-owned gap and is not needed to justify the narrow shared-ancestor sole-provider reopening
- Acceptance status: first-pass

## 2026-04-19 -- Declared-Order Branched Inherited `self.foo()` Correction Review

- Reviewed the returned `resolver.py` correction slice plus targeted resolver and dependency-frontier regressions for declared-base-order / branch-precedence inherited-call selection on linear branch subtrees
- Verified from fresh control-lane inspection:
  - the direct-base `self.foo()` fast path now applies only to true single-base inheritance, so multi-base cases no longer bypass the declared-order branched resolver seam
  - the previously failing concrete case now resolves truthfully:
    - `Child(LeftBridge, RightNearProvider)` now resolves `self.helper()` to `LeftFarProvider.helper`
    - the matching dependency-frontier call dependency now points to `LeftFarProvider.helper` and no longer stays incorrect or unresolved
  - accepted conservative boundaries remain intact:
    - overlapping/shared-ancestor branches still remain unresolved
    - non-linear branch subtrees still remain unresolved
    - earlier ineligible owners still block proof rather than skipping to a later winner
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_parser.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_parser.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_parser.py tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... Child(LeftBridge, RightNearProvider) ... resolve_semantics(bind_syntax(extract_syntax(...))) ... assert self.helper() == LeftFarProvider.helper ... PY`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... Child(LeftBridge, RightNearProvider) ... derive_dependency_frontier(analyze_repository(...)) ... assert CALL_RESOLUTION target == LeftFarProvider.helper ... PY`
- Acceptance decision:
  - accept the declared-base-order / branch-precedence inherited `self.foo()` linear-branch slice
  - acceptance status for this slice is after 1 correction
  - the next control action is one bounded planning spike for the next inherited-call follow-on beyond the accepted linear disjoint branch-precedence rule, focused on overlapping/shared-ancestor and diamond boundaries
- Reasoning:
  - the correction closes the concrete precedence defect without widening into generic C3 or broader overlapping-ancestor semantics
  - the accepted branched reopening is now truthful for the authorized linear disjoint branch contract, and broader branch shapes still need bounded planning before any further implementation reopening
- Acceptance status: 1 correction

## 2026-04-19 -- Ordered Direct-Base Ancestry Contract Review

- Reviewed the returned `resolver.py` contract slice plus targeted parser and resolver tests for declaration-ordered direct-base ancestry
- Verified from fresh control-lane inspection:
  - resolver-owned proven direct bases now preserve declaration order as tuples instead of collapsing to set/frozenset state
  - resolver-owned ancestor closure now preserves declaration-backed left-to-right order instead of sorting ancestor IDs
  - accepted `self.foo()` behavior remains unchanged:
    - truthful branched sole-provider cases still resolve through the preserved fallback
    - branched ambiguous cases still remain unresolved
    - linear nearest-provider cases still resolve to the nearer owner
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_parser.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_parser.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_parser.py tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_parser.py tests/test_resolver.py`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... branched_sole_provider_preserved; branched_ambiguous_stays_unresolved; linear_nearest_still_resolves ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
- Acceptance decision:
  - accept the ordered direct-base ancestry contract slice
  - the next control action is one bounded resolver-only implementation slice for declared-base-order / branch-precedence inherited `self.foo()` selection on linear branch subtrees
- Reasoning:
  - the slice clears the order-preservation blocker without widening proof prematurely
  - ordered ancestry is now available for the next truthful branched reopening, while broader non-linear / diamond / fuller C3-style work remains later
- Acceptance status: first-pass

## 2026-04-19 -- Ordering-Aware Contract Prerequisite Spike Review

- Reviewed the returned bounded planning spike for the smallest truthful ordering-aware blocker before broader branched inherited-call target selection
- Verified from fresh control-lane inspection:
  - parser-owned base facts already preserve declared direct-base order through list position and base-expression IDs
  - base-class resolved references also still appear in declared order before ancestry state is collapsed
  - resolver-owned ancestry currently loses that order by collapsing proven direct bases into set/frozenset state and later walking sorted ancestor IDs
  - broader branched inherited-call widening is still not truthful under the current model because Python branch precedence can pick a farther left-branch provider over a nearer right-branch provider
  - dependency/frontier production changes are not required for the first contract slice because proven call dependencies already follow resolver-backed `ResolvedReference` output
- Control review found no issues
- Validation/discovery confirmed:
  - `nl -ba src/context_ir/parser.py | sed -n '657,672p'`
  - `nl -ba src/context_ir/semantic_types.py | sed -n '519,590p'`
  - `nl -ba src/context_ir/resolver.py | sed -n '423,490p'`
  - `nl -ba src/context_ir/resolver.py | sed -n '1235,1285p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '227,240p'`
  - `nl -ba tests/test_parser.py | sed -n '136,185p'`
  - `nl -ba tests/test_parser.py | sed -n '260,292p'`
  - `nl -ba PLAN.md | sed -n '247,253p'`
  - `nl -ba BUILDLOG.md | sed -n '21,26p'`
  - `nl -ba EVAL.md | sed -n '1,20p'`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... class Child(Left, Right) ... extract_syntax(...) ... [('Left', '1'), ('Right', '2')] ... PY`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... class Child(Left, Right) ... resolve_semantics(...) ... [('Left', 'def:main.py:main.Left'), ('Right', 'def:main.py:main.Right')] ... PY`
  - `python3 - <<'PY' ... class Child(LeftBridge, RightBridge) ... print(Child.__mro__, Child().helper()) ... PY`
  - `git status --short`
- Acceptance decision:
  - accept the planning spike
  - the next control action is one bounded resolver-only implementation slice to preserve declared direct-base order in resolver-owned ancestry state without widening branched inherited `self.foo()` behavior yet
- Reasoning:
  - the ordered ancestry contract is the smallest truthful blocker-clearer because ordered base information already exists upstream and is only lost in resolver/frontier-owned ancestry state
  - a semantic schema change would be hardening, but it is not yet required to clear the current blocker honestly
- Acceptance status: first-pass

## 2026-04-19 -- Linear Single-Chain Inherited `self.foo()` Widening Review

- Reviewed the returned `resolver.py` slice and targeted tests for linear single-chain nearest-provider inherited-call proof
- Verified from fresh control-lane inspection:
  - the resolver-owned call-proof ladder is now same-class -> direct-base -> linear single-chain transitive -> order-free transitive sole-provider
  - the new helper only proves when every hop outward remains unbranched until the first transitive class-scope owner is found
  - that first owner must still own the name as one unique undecorated method; nearer decorated or attribute-backed owners remain on the non-proof path
  - existing truthful branched sole-provider cases still resolve through the preserved fallback, while branched different-distance cases still remain unresolved
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... linear_nearest_owner; branched_sole_provider_preserved; branched_different_distance_stays_unresolved ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
- Acceptance decision:
  - accept the linear single-chain nearest-provider widening slice
  - the next control action is one bounded planning spike for the ordering-aware contract work that broader branched inherited-call target selection would require
- Reasoning:
  - the slice closes the truthful linear-chain gap without inventing branch precedence the repo still cannot represent
  - broader branched inherited-call selection remains blocked on an ordering-aware contract, not on more resolver heuristics
- Acceptance status: first-pass

## 2026-04-19 -- Post-Order-Free-Transitive Inherited-Call Planning Spike Review

- Reviewed the returned bounded planning spike for the next inherited-call follow-on beyond the accepted order-free transitive sole-provider `self.foo()` boundary
- Verified from fresh control-lane inspection:
  - the current resolver-owned proof ladder is still same-class -> direct-base -> transitive sole-provider
  - the current transitive helper still rejects linear multi-provider chains because it returns no proof on a second transitive owner anywhere in closure
  - the repo still stores direct proven bases as set/frozenset state and walks sorted ancestor IDs, so branched nearest-hop widening would still overclaim without preserved base-order semantics
  - dependency/frontier derivation does not need new proof logic for the next slice; resolver-owned call proof still flows automatically into `CALL_RESOLUTION` dependencies
- Control review found no issues
- Validation/discovery confirmed:
  - `nl -ba src/context_ir/resolver.py | sed -n '420,500p'`
  - `nl -ba src/context_ir/resolver.py | sed -n '660,970p'`
  - `nl -ba src/context_ir/resolver.py | sed -n '1138,1165p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '220,245p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '390,415p'`
  - `nl -ba src/context_ir/parser.py | sed -n '650,670p'`
  - `nl -ba src/context_ir/semantic_types.py | sed -n '510,530p'`
  - `nl -ba tests/test_resolver.py | sed -n '650,790p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '1525,1685p'`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... FarProvider -> NearProvider -> Bridge -> Child.run -> self.helper() ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
  - `python3 - <<'PY' ... class D(B, C) ... print(D.__mro__, D().helper()) ... PY`
  - `git status --short`
- Acceptance decision:
  - accept the planning spike
  - the next control action is one bounded resolver-only implementation slice for linear single-chain nearest-provider inherited `self.foo()` proof widening
- Reasoning:
  - the linear single-chain case is the smallest truthful missed proof under the repo's current order-free ancestor model
  - broader branched inherited-call widening still needs an ordering-aware contract before it can be reopened honestly
- Acceptance status: first-pass

## 2026-04-19 -- Order-Free Transitive Inherited `self.foo()` Widening Correction Review

- Reviewed the returned `resolver.py` correction slice and targeted tests for final class-namespace ownership across current `self.foo()` proof seams
- Verified from fresh control-lane inspection:
  - same-class `self.foo()` proof now requires the final same-class binding for that name to remain the same unique undecorated method
  - direct-base inherited `self.foo()` proof now contracts when same-class or competing direct-base class-scope bindings take ownership of the name
  - the accidental transitive sole-provider inherited `self.foo()` widening now contracts when same-class, direct-base, or transitive class-scope bindings shadow or compete for that name
  - previously accepted positive same-class, direct-base, and transitive sole-provider cases still resolve, while blocked cases now stay on the existing unresolved non-proof path
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... same_class_rebound; direct_base_same_class_shadow; direct_other_base_attr_conflict; transitive_intermediate_attr_shadow; transitive_other_branch_attr_conflict; transitive_provider_rebound; positive_transitive_unique_provider ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
- Acceptance decision:
  - accept the correction slice
  - resolve the prior hold on accidental transitive sole-provider widening
  - the corrected order-free transitive sole-provider inherited `self.foo()` widening is now accepted in workspace authority
  - the next control action is one bounded planning spike for the next inherited-call target-selection follow-on beyond the accepted order-free sole-provider boundary
- Reasoning:
  - the correction closes the correctness defect that affected same-class, direct-base, and accidental transitive `self.foo()` proof
  - with final class-namespace ownership now enforced, the transitive sole-provider rule matches the repo's current order-free honesty boundary without inventing full MRO semantics
- Acceptance status: 1 correction

## 2026-04-19 -- Accidental Transitive Inherited `self.foo()` Widening Review

- Reviewed two external-lane artifacts:
  - a bounded inherited-call planning spike recommending order-free transitive sole-provider `self.foo()` proof widening
  - an accidental workspace-only implementation of that widening in `resolver.py` plus targeted tests
- Verified from fresh control-lane inspection:
  - the new resolver seam adds a third `self.foo()` proof pass after same-class and direct-base proof, resolving when exactly one transitively proven ancestor declares the method name and that sole ancestor is beyond the direct-base layer
  - the targeted test additions cover linear transitive proof, unique multi-branch proof, multi-provider ambiguity fallback, and decorated transitive fallback
- Control review found issues:
  - fresh repros showed the accidental widening falsely resolves inherited `self.foo()` calls when a class-scope binding like `helper = 1` shadows the inherited method name
  - the same repro session also showed the existing accepted same-class and direct-base `self.foo()` proof seams share the same final class-namespace ownership defect
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... Grandparent.helper + Parent.helper = 1 + Child.run -> self.helper(); Example.helper + helper = 1 + self.helper() ... resolve_semantics(bind_syntax(extract_syntax(...))) ... PY`
- Human sign-off:
  - Ryan reviewed the findings and explicitly authorized a fix-now correction slice
- Acceptance decision:
  - hold the accidental workspace-only transitive widening implementation
  - do not accept the widening into repo authority yet
  - the next control action is one bounded correction slice to contract current `self.foo()` proof seams around final class-namespace ownership before any broader inherited-call widening is reconsidered
- Reasoning:
  - the newly discovered defect is correctness-affecting, not stylistic
  - because the same bug also exists on already-accepted `self.foo()` proof seams, the truthful next move is a narrow correction pass on current proof contracts rather than accepting or extending the widening
- Acceptance status: held

## 2026-04-19 -- Ancestor-Closure Hook-Aware Unsupported-Boundary Review

- Reviewed the returned `dependency_frontier.py` and targeted tests slice for transitive inherited-hook unsupported classification
- Verified from fresh control-lane inspection:
  - the new helper now walks the transitively proven repository-class ancestor graph for attribute-hook detection, covering both `__getattr__` and `__getattribute__`
  - the change stays inside the accepted dependency/frontier seams only:
    - unresolved canonical `self.foo()` call surfaces
    - unresolved canonical `self.<name>` attribute-read surfaces
    - unresolved canonical `self.<name>` store surfaces
  - affected transitive-hook cases now reroute to the existing unsupported reason codes instead of staying on the generic unresolved path
  - already-proven resolver-backed call and attribute dependencies remain untouched, and same-class/direct-base hook-aware unsupported behavior still holds
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/dependency_frontier.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python - <<'PY' ... HookedGrandparent -> PlainIntermediate -> LinearSameClassChild and PlainDirectBase + GetattrBridge -> GetattrMixedChild ... derive_dependency_frontier(resolve_semantics(bind_syntax(extract_syntax(...)))) ... PY`
- Acceptance decision:
  - accept the ancestor-closure hook-aware unsupported-boundary slice
  - the next control action is one bounded inherited/MRO-aware `self.foo()` proof-widening decomposition spike
- Reasoning:
  - the slice completes the accepted honesty-first inherited-hook sequence: proof contraction first, unsupported surfacing second
  - the next remaining inherited/object-model follow-on is no longer honesty routing; it is broader inherited target selection, which needs bounded planning before code changes reopen it
- Acceptance status: first-pass

## 2026-04-19 -- Ancestor-Closure `__getattribute__` Proof-Contraction Review

- Reviewed the returned `resolver.py` and targeted tests slice for transitive inherited-hook proof contraction
- Verified from fresh control-lane inspection:
  - the new guard now walks the transitively proven repository-class ancestor graph instead of checking only direct bases
  - the change stays inside the accepted resolver-owned proof seams only:
    - same-class `self.foo()` call proof
    - direct-base inherited `self.foo()` call proof
    - same-class canonical `self.<name>` attribute-read proof
  - affected indirect-hook cases now fall back to the existing generic unresolved path rather than resolving and rather than surfacing as unsupported in this slice
  - same-class and direct-base positive/negative cases remain intact under the existing target-selection rules
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python - <<'PY' ... HookedGrandparent -> PlainIntermediate -> LinearSameClassChild and PlainDirectBase + MixedProvider -> MixedInheritedChild ... derive_dependency_frontier(resolve_semantics(bind_syntax(extract_syntax(...)))) ... PY`
- Acceptance decision:
  - accept the ancestor-closure `__getattribute__` proof-contraction slice
  - the next control action is one bounded dependency-frontier ancestor-hook unsupported surfacing slice
- Reasoning:
  - the slice closes the concrete beyond-direct-base false-proof gap without reopening unsupported/frontier policy or broader inherited target selection
  - preserving generic unresolved as the interim fallback matches the accepted sequence: proof contraction first, unsupported surfacing second, proof widening later
- Acceptance status: first-pass

## 2026-04-19 -- Post-Same-Class-Attribute-Proof Inherited-Hook Priority And Decomposition Spike Review

- Reviewed the returned planning spike for the next smallest truthful inherited-hook target after the accepted same-class canonical-self attribute-read proof slice
- Verified from fresh control-lane inspection:
  - resolver still builds only `direct_proven_base_class_ids_by_class_id`, so the current beyond-direct-base hook gap is real and still invisible to existing proof guards
  - the same direct-base-only `__getattribute__` guard currently gates all live resolver-owned object-model proof seams:
    - same-class `self.foo()` call proof
    - direct-base inherited `self.foo()` call proof
    - same-class canonical `self.<name>` attribute-read proof
  - dependency/frontier hook-aware unsupported classification is also still same-class/direct-base only, so unsupported surfacing remains the right follow-on after proof contraction rather than the first next slice
  - a fresh control-lane repro confirmed the concrete false-proof gap: a hooked grandparent behind a plain direct base still allows `self.build()` to resolve to the direct base method and `self.field` to resolve to the same-class class attribute, with no frontier or unsupported record emitted
- Control review found no issues
- Validation confirmed:
  - `rg -n "__getattribute__|__getattr__|direct base|ancestor|MRO|unsupported|self\\." src/context_ir tests PLAN.md BUILDLOG.md EVAL.md`
  - `sed -n '423,520p' src/context_ir/resolver.py`
  - `sed -n '560,620p' src/context_ir/resolver.py`
  - `sed -n '845,1018p' src/context_ir/resolver.py`
  - `sed -n '223,240p' src/context_ir/dependency_frontier.py`
  - `sed -n '727,905p' src/context_ir/dependency_frontier.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -k "getattribute or direct_base or self_attribute_proof" -q`
  - `.venv/bin/python - <<'PY' ... HookedGrandparent -> PlainBase -> CallChild ... derive_dependency_frontier(resolve_semantics(bind_syntax(extract_syntax(...)))) ... PY`
- Acceptance decision:
  - accept the post-same-class-attribute-proof inherited-hook priority and decomposition spike
  - the next control action is one bounded resolver-only ancestor-closure `__getattribute__` proof-contraction slice
- Alternatives considered:
  - ancestor-closure hook-aware unsupported surfacing as the first next slice
  - broader inherited/MRO-aware `self.foo()` proof widening as the first next slice
- Reasoning:
  - the smallest truthful inherited-only follow-on is still proof contraction on already accepted resolver-owned seams, not a frontier redesign and not a broader target-selection reopening
  - the repo's established sequence for hook-sensitive work remains contraction first, unsupported surfacing second, proof widening later
- Acceptance status: first-pass

## 2026-04-19 -- Same-Class Canonical-Self Attribute-Read Proof Correction Review

- Reviewed the returned `resolver.py` and targeted tests correction slice for same-class canonical-self attribute-read proof
- Verified from fresh control-lane inspection:
  - the accepted positive case still holds: narrow same-class canonical `self.field` reads resolve to the same unique same-class class-attribute symbol and dependency derivation still emits `ATTRIBUTE_RESOLUTION`
  - the reviewed shadowed-method defect is now closed: when a same-class method later rebinds the same name, `self.<name>` no longer resolves as an attribute target and stays on the existing non-proof path
  - same-class and direct-base `__getattribute__` guards still block the narrow attribute-read proof path
  - the correction stayed inside the bounded fix: `dependency_frontier.py` behavior did not widen; the corrected resolver output now feeds the already accepted dependency/frontier behavior honestly
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py src/context_ir/dependency_frontier.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python - <<'PY' ... Plain.field stays proved; Shadowed.field stays unresolved ... derive_dependency_frontier(resolve_semantics(bind_syntax(extract_syntax(...)))) ... PY`
- Acceptance decision:
  - accept the same-class canonical-self attribute-read proof slice after 1 correction
  - the next control action is one bounded post-same-class-attribute-proof inherited-hook priority and decomposition spike
- Reasoning:
  - the correction now matches the accepted boundary of unique same-class class-attribute symbols only
  - class-scope shadowing by a later same-class method no longer masquerades as attribute proof
- Acceptance status: 1 correction

## 2026-04-19 -- Same-Class Canonical-Self Attribute-Read Proof Review

- Reviewed the returned `resolver.py`, `dependency_frontier.py`, and targeted tests slice for same-class canonical-self attribute-read proof
- Verified from fresh control-lane inspection:
  - the new resolver path correctly stays read-only on `ReferenceContext.ATTRIBUTE_ACCESS`
  - same-class and direct-base `__getattribute__` guards still block the narrow attribute-read proof path
  - targeted validation reported by the execution lane reproduced cleanly:
    - `.venv/bin/python -m ruff check src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py src/context_ir/dependency_frontier.py`
    - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
    - `git diff --check -- src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
- Control review found one issue:
  - class-scope shadowing is still over-proved: when a class defines a class attribute and then a same-class method of the same name, the new resolver path still resolves `self.<name>` to the class-attribute binding and dependency derivation emits an `ATTRIBUTE` dependency, even though the class namespace no longer has a uniquely attribute-only target
- Repo-backed repro used in control review:
  - `.venv/bin/python - <<'PY' ... class Example: field = 1; def field(self): ...; def run(self): seen = self.field ... derive_dependency_frontier(resolve_semantics(bind_syntax(extract_syntax(...)))) ... PY`
- Human sign-off:
  - Ryan approved fixing the defect now before advancing
- Acceptance decision:
  - hold the same-class canonical-self attribute-read proof slice for one narrow correction
  - the next control action is one bounded correction slice that blocks attribute proof when same-class namespace shadowing makes `self.<name>` ambiguous or method-backed
- Reasoning:
  - the accepted slice boundary was unique same-class class-attribute symbols only
  - class-scope shadowing by a same-class method violates that uniqueness boundary and cannot be accepted as a truthful attribute proof
- Acceptance status: held

## 2026-04-19 -- Post-Direct-Base-Inherited Phase-2 Priority And Decomposition Spike Review

- Reviewed the returned planning spike for the next smallest truthful phase-2 target after the now-complete direct-base inherited follow-on queue
- Verified from fresh control-lane inspection:
  - parser still retains raw attribute-site surfaces and contexts, binder still emits same-class class-attribute bindings and symbols, and the semantic contract still reserves `ATTRIBUTE_RESOLUTION` plus `SemanticDependencyKind.ATTRIBUTE`
  - resolver-owned proof still stops at decorator, base-expression, and call-site surfaces, with narrow `self.foo()` as the only live object-model proof seam; it does not yet resolve attribute-site reads
  - dependency/frontier derivation already carries plain same-class `self.field` reads as unresolved or hook-aware unsupported output, so the smallest truthful next widening is a narrow proof slice on that already-retained surface
  - broader inherited/MRO-aware lookup, `cls.*`, and decorator/property/descriptor semantics remain larger follow-ons outside the smallest next slice
- Control review found no issues
- Validation confirmed:
  - `rg -n "AttributeSiteFact|ATTRIBUTE_RESOLUTION|SemanticDependencyKind\\.ATTRIBUTE|ReferenceContext\\.ATTRIBUTE_ACCESS|self\\.|cls\\.|__getattribute__|__getattr__|SupportedDecorator|DecoratorSupport|DATACLASS" src/context_ir tests PLAN.md BUILDLOG.md EVAL.md`
  - `rg --files src/context_ir tests | rg "binder|parser|resolver|dependency_frontier|semantic_types|test_resolver|test_dependency_frontier|test_parser"`
  - `nl -ba src/context_ir/parser.py | sed -n '280,320p'`
  - `nl -ba src/context_ir/parser.py | sed -n '470,505p'`
  - `nl -ba src/context_ir/semantic_types.py | sed -n '40,140p'`
  - `nl -ba src/context_ir/binder.py | sed -n '110,180p'`
  - `nl -ba src/context_ir/resolver.py | sed -n '360,860p'`
  - `nl -ba src/context_ir/dependency_frontier.py | sed -n '336,930p'`
  - `nl -ba tests/test_resolver.py | sed -n '300,620p'`
  - `nl -ba tests/test_dependency_frontier.py | sed -n '1660,1875p'`
- Acceptance decision:
  - accept the post-direct-base-inherited phase-2 priority and decomposition spike
  - the next control action is one bounded same-class canonical-self attribute-read proof implementation slice for unique same-class class-attribute symbols, read-only on `ReferenceContext.ATTRIBUTE_ACCESS`
- Alternatives considered:
  - inherited hook handling beyond direct bases as the first inherited-only follow-on
  - broader inherited/MRO-aware `self.foo()` proof widening
  - `cls.*` plus decorator/property/descriptor semantics as the next member/object-model reopening
- Reasoning:
  - the recommended slice widens proof on an already-retained attribute surface without reopening accepted direct-base call contracts or classmethod/descriptor semantics
  - the repo already has the necessary parser, binder, and semantic-type seams, while resolver and dependency/frontier behavior still leave the narrow same-class `self.field` read case unproved
  - the alternatives all require broader ancestor ordering, new hook-closure logic, or unsupported decorator/property/descriptor semantics and are therefore larger than the smallest truthful next slice
- Acceptance status: first-pass

## 2026-04-19 -- Direct-Base Inherited `self.foo()` Proof-Widening Review

- Reviewed the returned `resolver.py` and tests slice for narrow direct-base inherited `self.foo()` proof widening
- Verified from fresh control-lane inspection:
  - the existing narrow resolver-owned `self.foo()` path can now resolve to a uniquely defined undecorated method on exactly one directly proven base class after same-class proof fails
  - same-class precedence is preserved, so same-class methods still win before any inherited proof is considered
  - same-class shadowing, ambiguous multi-base matches, decorated base methods, and direct dunder-call cases such as `self.__getattr__()` / `self.__getattribute__()` remain on the existing non-proof path
  - the direct-base and same-class `__getattribute__` proof guards still hold, so the slice widens proof only inside the accepted narrow boundary
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the direct-base inherited `self.foo()` proof-widening slice
  - the accepted direct-base inherited follow-on queue is now complete
  - the next control action is one bounded post-direct-base-inherited phase-2 priority and decomposition spike
- Acceptance status: first-pass

## 2026-04-19 -- Direct-Base Inherited Hook-Aware Unsupported-Boundary Review

- Reviewed the returned `dependency_frontier.py` and tests slice for direct-base inherited hook-aware unsupported classification
- Verified from fresh control-lane inspection:
  - unresolved direct `self.*` call surfaces now become explicit unsupported `UNSUPPORTED_CALL_TARGET` output when a directly proven base defines `__getattr__` or `__getattribute__`
  - unresolved direct non-call `self.*` reads and stores now become explicit unsupported `UNSUPPORTED_ATTRIBUTE_ACCESS` output under the same narrow direct-base rule
  - plain direct-base cases remain on the existing generic unresolved path, and direct dunder hook calls such as `self.__getattribute__(...)` remain excluded from the hook-boundary classification
  - the slice stays honesty-only: no resolver change, no proof widening, and no new reason codes landed here
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/dependency_frontier.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the direct-base inherited hook-aware unsupported-boundary slice
  - the next control action is one bounded narrow direct-base inherited `self.foo()` proof-widening slice
- Acceptance status: first-pass

## 2026-04-19 -- Direct-Base Inherited `__getattribute__` Proof-Guard Review

- Reviewed the returned `resolver.py` and tests slice for direct-base inherited `__getattribute__` proof contraction
- Verified from fresh control-lane inspection:
  - narrow `self.foo()` proof now contracts back to the existing non-proof path when any directly proven base class of the enclosing class defines `__getattribute__`
  - plain direct-base cases still preserve the accepted narrow proof path
  - the affected inherited-hook call now stays on the existing generic unresolved frontier path rather than resolving and rather than surfacing through the accepted same-class hook-aware unsupported path
  - the slice stays honesty-only: no inherited proof widening, no new reason codes, and no dependency-frontier redesign landed here
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the direct-base inherited `__getattribute__` proof-guard slice
  - the next control action is one bounded direct-base inherited hook-aware unsupported-boundary slice for unresolved `self.*` call and non-call attribute surfaces
- Acceptance status: first-pass

## 2026-04-19 -- Post-Hook Phase-2 Priority And Decomposition Spike Review

- Reviewed the returned planning spike for the next smallest truthful post-hook phase-2 target after the now-complete reflection-hook follow-on queue
- Verified from fresh control-lane inspection:
  - the repo's only live object-model proof path remains narrow `self.foo()` resolution, and it still does not inspect directly proven base classes for inherited `__getattribute__`
  - directly proven base-expression resolution and inheritance dependency surfacing already exist, so the smallest truthful next slice is proof contraction on an existing path rather than a new proof family
  - inherited hook misses still remain on generic non-proof paths today, so direct-base inherited hook-aware unsupported surfacing is the next bounded follow-on after the proof guard
  - broader inherited proof widening, non-self receiver reasoning, and decorator/property/descriptor semantics remain later work under the accepted public-claim boundary
- Control review found two issues in the initially proposed next execution prompt:
  - the validation contract was underpowered because it used targeted `pytest -k ...` subsets and omitted `git diff --check`
  - the prompt omitted the required `AGENTS.md` execution-lane return shape beyond completion state
- Human sign-off:
  - Ryan agreed with the recommendation to correct the prompt before advancing
- Validation confirmed:
  - `rg -n "__getattr__|__getattribute__|property|cached_property|classmethod|staticmethod|super\\(|__mro__|descriptor|__get__|__set__|__delete__" src/context_ir tests`
  - `rg -n "self\\.|cls\\.|helper\\.|owner\\.|receiver|attribute|member|decorator" src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `rg -n "DATACLASS|SupportedDecorator|DecoratorSupport|OPAQUE_DECORATOR|UNSUPPORTED_DECORATOR" src/context_ir tests`
  - `rg -n "dynamic-boundary|reflection-hook|decorator/object-model|member-access|What Is Next|Phase-2 Decomposition" PLAN.md BUILDLOG.md EVAL.md`
  - `.venv/bin/python - <<'PY' ... analyze_repository(...) ...`
- Acceptance decision:
  - accept the post-hook phase-2 priority and decomposition spike after 1 control correction with human sign-off
  - the next control action is one bounded direct-base inherited `__getattribute__` proof-guard implementation slice with full repo-standard targeted validation and the complete `AGENTS.md` execution-lane return shape
- Acceptance status: 1 control correction with human sign-off

## 2026-04-19 -- Import-Rooted Module Hook-Boundary Review

- Reviewed the returned `dependency_frontier.py` and tests slice for direct import-rooted module hook classification
- Verified from fresh control-lane inspection:
  - unresolved direct one-hop import-rooted `mod.attr` and `mod.attr()` surfaces now become explicit unsupported output when the root binding resolves to a directly imported repo module that defines module-level `__getattr__`
  - direct imported repo modules without module-level `__getattr__` remain on the existing generic unresolved path
  - package-root multi-hop chains such as `pkg.sub.attr` remain on the existing generic unresolved path, preserving the accepted narrow scope
  - the slice stays honesty-only: no resolver change, no schema/type widening, and no new reason codes landed here
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/dependency_frontier.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the import-rooted module hook-boundary slice
  - the accepted object-model reflection-hook follow-on queue is now complete
  - the next control action is one bounded post-hook phase-2 priority and decomposition spike
- Acceptance status: first-pass

## 2026-04-19 -- Same-Class Hook-Aware Unsupported-Boundary Review

- Reviewed the returned `dependency_frontier.py` and tests slice for same-class hook-aware unsupported classification
- Verified from fresh control-lane inspection:
  - unresolved same-class `self.*` call surfaces now become explicit unsupported `UNSUPPORTED_CALL_TARGET` output when the enclosing class defines a same-class `__getattr__` or `__getattribute__`
  - unresolved same-class non-call `self.*` reads and stores now become explicit unsupported `UNSUPPORTED_ATTRIBUTE_ACCESS` output under the same narrow hook rule
  - plain-class behavior remains unchanged, and direct `self.__getattribute__(...)` stays on the generic non-proof path as intentionally out of scope
  - the slice stays honesty-only: no resolver change, no schema/type widening, and no new reason codes landed here
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/dependency_frontier.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the same-class hook-aware unsupported-boundary slice
  - the next control action is one bounded import-rooted module hook-boundary slice for directly proven repo-module imports with module-level `__getattr__`
- Acceptance status: first-pass

## 2026-04-19 -- Same-Class `__getattribute__` Proof-Guard Review

- Reviewed the returned `resolver.py` and tests slice for same-class `__getattribute__` proof contraction
- Verified from fresh control-lane inspection:
  - narrow same-class `self.foo()` proof now contracts back to the existing non-proof path when the enclosing class defines a same-class `__getattribute__`
  - accepted same-class `self.foo()` proof still holds for classes without that hook
  - when the guard triggers, downstream dependency/frontier derivation now sees the call on the existing non-proof path and surfaces `UNRESOLVED_ATTRIBUTE` rather than a proven dependency
  - the slice stays honesty-only: no schema/type widening, no new reason codes, and no dependency-frontier redesign landed here
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py`
  - `.venv/bin/python -m pytest tests/test_resolver.py tests/test_dependency_frontier.py -v`
  - `git diff --check -- src/context_ir/resolver.py tests/test_resolver.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the same-class `__getattribute__` proof-guard slice
  - the next control action is one bounded same-class hook-aware unsupported-boundary slice for unresolved `self.*` call and non-call attribute surfaces
- Acceptance status: first-pass

## 2026-04-19 -- Object-Model Reflection-Hook Priority And Decomposition Spike Review

- Reviewed the returned planning spike for the next post-reflective-builtin object-model reflection-hook follow-on
- Verified from fresh control-lane inspection:
  - parser definition retention is already sufficient for hook planning because raw class and function/method definitions keep dunder names without a dedicated filter
  - attribute sites are already retained downstream, while call-site surfaces already suppress duplicate attribute-site handling, so hook-aware call honesty cannot be solved by attribute-site plumbing alone
  - the live same-class `self.foo()` proof path is currently the smallest hook-blind overclaim because resolver-owned same-class self-call proof does not inspect same-class `__getattribute__`
  - same-class hook-aware unsupported surfacing for unresolved `self.*` call and non-call attribute sites remains the next bounded follow-on after the proof guard lands
  - import-rooted module hook boundaries remain later, lower-leverage work
- Control review found two issues:
  - the proposed next execution prompt used underpowered validation (`ruff check` plus `pytest`) instead of the repo's normal targeted implementation-slice validation bar
  - the proposed next execution prompt omitted the `AGENTS.md` execution-lane return-shape requirements beyond completion state
- Human sign-off:
  - Ryan agreed with the recommendation to correct the prompt before advancing
- Validation confirmed:
  - `rg -n "__getattr__|__getattribute__|getattr\(|hasattr\(|vars\(|dir\(|AttributeSiteFact|UNSUPPORTED_ATTRIBUTE_ACCESS|REFLECTIVE_BUILTIN" src/context_ir tests`
  - `rg -n "class .*__getattr__|class .*__getattribute__|def __getattr__|def __getattribute__" src/context_ir tests`
  - `rg -n "__getattr__|__getattribute__" .`
  - `git status --short`
  - `git diff --stat`
- Acceptance decision:
  - accept the object-model reflection-hook priority and decomposition spike after 1 control correction with human sign-off
  - the next control action is one bounded same-class `__getattribute__` proof-guard implementation slice with full repo-standard targeted validation and the complete `AGENTS.md` execution-lane return shape
- Acceptance status: 1 control correction with human sign-off

## 2026-04-19 -- Reflective Builtin Call-Surface Honesty Review

- Reviewed the returned `semantic_types.py`, `dependency_frontier.py`, and tests slice for reflective builtin call-surface honesty
- Verified from fresh control-lane inspection:
  - unshadowed `getattr(...)`, `hasattr(...)`, `vars(...)`, and `dir(...)` now surface as explicit unsupported `REFLECTIVE_BUILTIN` boundaries instead of generic unresolved frontier
  - the new reason code is included in the supported-subset unknown-without-proof boundary
  - locally rebound reflective builtin names still stay on the generic frontier path, preserving the accepted shadowing rule
  - accepted importlib-family, runtime-mutation, and metaclass behaviors remain unchanged
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_dependency_frontier.py -v`
  - `.venv/bin/python -m pytest tests/test_semantic_types.py -q`
  - `.venv/bin/python -m ruff check src/context_ir/semantic_types.py src/context_ir/dependency_frontier.py tests/test_semantic_types.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/semantic_types.py src/context_ir/dependency_frontier.py tests/test_semantic_types.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/semantic_types.py src/context_ir/dependency_frontier.py`
  - `git diff --check -- src/context_ir/semantic_types.py src/context_ir/dependency_frontier.py tests/test_semantic_types.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the reflective builtin call-surface honesty slice
  - the next control action is one bounded object-model reflection-hook priority and decomposition spike
- Acceptance status: first-pass

## 2026-04-19 -- Aliased Root-Module `importlib as ...` Dynamic-Boundary Review

- Reviewed the returned `dependency_frontier.py` and tests slice for aliased root-module `importlib` dynamic-boundary surfacing
- Verified from fresh control-lane inspection:
  - `import importlib as loader; loader.import_module(...)` now surfaces as an explicit unsupported `DYNAMIC_IMPORT` boundary instead of generic unresolved frontier
  - the accepted exact-root and imported simple-name `import_module(...)` behaviors remain unchanged
  - submodule-alias negatives such as `import importlib.metadata as loader` remain on the generic frontier path
  - locally rebound alias names still stay on the generic frontier path, preserving the accepted shadowing rule
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_dependency_frontier.py -v`
  - `.venv/bin/python -m ruff check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/dependency_frontier.py`
  - `git diff --check -- src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the aliased root-module `importlib as ...` dynamic-boundary slice
  - the next control action is one bounded reflective builtin call-surface honesty slice
- Acceptance status: first-pass

## 2026-04-19 -- Imported `importlib.import_module` Dynamic-Boundary Review

- Reviewed the returned `dependency_frontier.py` and tests slice for imported `import_module(...)` dynamic-boundary surfacing
- Verified from fresh control-lane inspection:
  - `from importlib import import_module` and `from importlib import import_module as ...` call sites now surface as explicit unsupported `DYNAMIC_IMPORT` boundaries instead of generic unresolved frontier
  - the accepted exact-root `importlib.import_module(...)` behavior remains unchanged
  - the accepted submodule-alias negative case remains unchanged
  - locally rebound `import_module` and `load_module` names still stay on the generic frontier path, preserving the accepted shadowing rule
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_dependency_frontier.py -v`
  - `.venv/bin/python -m ruff check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/dependency_frontier.py`
  - `git diff --check -- src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the imported `importlib.import_module` dynamic-boundary slice
  - the next control action is one bounded aliased root-module `importlib as ...` dynamic-boundary slice
- Acceptance status: first-pass

## 2026-04-19 -- Broader Reflective-Boundary Decomposition Spike Review

- Reviewed the returned planning spike for the next post-metaclass reflective/dynamic-boundary follow-on
- Verified from fresh control-lane inspection:
  - the ranking is grounded in current repo reality: imported `from importlib import import_module` simple-name call surfaces remain the smallest gap in the accepted `DYNAMIC_IMPORT` contract
  - exact-root `importlib.import_module(...)`, runtime-mutation builtins, and metaclass keyword surfacing are already accepted and covered
  - aliased root-module forms such as `import importlib as loader; loader.import_module(...)` are a plausible same-family next slice after the imported-name gap closes
  - reflective builtins such as `getattr(...)`, `hasattr(...)`, `vars(...)`, and `dir(...)` remain later candidates, while `__getattr__`, `__getattribute__`, and monkeypatch/runtime-introspection surfaces are not yet tightly decomposed enough for immediate implementation
- Control review found one issue:
  - the initially proposed next execution prompt used underpowered validation (`pytest -k ...` plus `git diff --stat`) instead of the repo's normal implementation-slice validation bar
- Human sign-off:
  - Ryan agreed with the recommendation to fix the prompt before advancing
- Validation confirmed:
  - `rg -n "getattr\(|hasattr\(|vars\(|dir\(|__getattr__|__getattribute__|import_module|importlib|monkeypatch|patch\(" src/context_ir tests`
  - `rg -n "DYNAMIC_IMPORT|EXEC_OR_EVAL|METACLASS_BEHAVIOR|RUNTIME_MUTATION|ALIAS_CHAIN|UNRESOLVED_ATTRIBUTE|UNSUPPORTED_CALL_TARGET" src/context_ir tests`
  - `git diff --stat`
- Acceptance decision:
  - accept the broader reflective-boundary decomposition spike after 1 control correction
  - the next control action is one bounded imported `importlib.import_module` dynamic-boundary slice with full repo-standard validation
- Acceptance status: 1 correction

## 2026-04-19 -- Metaclass Keyword Surfacing Review

- Reviewed the returned parser/frontier/types/tests slice for explicit metaclass boundary surfacing
- Verified from fresh control-lane inspection:
  - the parser now retains a narrow `metaclass=...` syntax fact instead of dropping that keyword surface
  - frontier derivation now emits explicit unsupported `METACLASS_BEHAVIOR` records with source-backed keyword text instead of leaving metaclass behavior silent
  - existing base-expression handling remains unchanged
  - nested call or attribute surfaces inside a metaclass value still follow their already accepted paths, so this slice adds honesty without widening proof
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_parser.py -v`
  - `.venv/bin/python -m pytest tests/test_dependency_frontier.py -v`
  - `.venv/bin/python -m pytest tests/test_semantic_types.py -q`
  - `.venv/bin/python -m ruff check src/context_ir/parser.py src/context_ir/dependency_frontier.py src/context_ir/semantic_types.py tests/test_parser.py tests/test_dependency_frontier.py tests/test_semantic_types.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/parser.py src/context_ir/dependency_frontier.py src/context_ir/semantic_types.py tests/test_parser.py tests/test_dependency_frontier.py tests/test_semantic_types.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/parser.py src/context_ir/dependency_frontier.py src/context_ir/semantic_types.py`
  - `git diff --check -- src/context_ir/parser.py src/context_ir/dependency_frontier.py src/context_ir/semantic_types.py tests/test_parser.py tests/test_dependency_frontier.py tests/test_semantic_types.py`
- Acceptance decision:
  - accept the metaclass keyword surfacing slice
  - the next control action is one bounded broader reflective-boundary priority and decomposition spike
- Acceptance status: first-pass

## 2026-04-19 -- Runtime-Mutation Call-Site Honesty Review

- Reviewed the returned `dependency_frontier.py` and tests slice for named runtime-mutation and reflection call boundaries
- Verified from fresh control-lane inspection:
  - unresolved `setattr(...)`, `delattr(...)`, `globals(...)`, and `locals(...)` call sites now surface as explicit unsupported `RUNTIME_MUTATION` boundaries instead of generic unresolved frontier
  - exact call snippets are preserved as construct text when source-backed snippets are available
  - lexically shadowed or rebound names still stay on the generic frontier path, preserving the accepted narrow scope
  - the accepted dynamic-import / `exec` / `eval` handling remains unchanged
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_dependency_frontier.py -v`
  - `.venv/bin/python -m ruff check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/dependency_frontier.py`
  - `git diff --check -- src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the runtime-mutation call-site honesty slice
  - the next control action is one bounded metaclass keyword surfacing slice
- Acceptance status: first-pass

## 2026-04-19 -- Dynamic-Boundary Call-Site Honesty Review

- Reviewed the returned `dependency_frontier.py` and tests slice for named dynamic-call boundary surfacing
- Verified from fresh control-lane inspection:
  - unresolved `importlib.import_module(...)` and `__import__(...)` call sites now surface as explicit unsupported `DYNAMIC_IMPORT` boundaries instead of generic unresolved frontier
  - unresolved `exec(...)` and `eval(...)` call sites now surface as explicit unsupported `EXEC_OR_EVAL` boundaries instead of generic unresolved frontier
  - shadowed or rebound names still stay on the generic frontier path, preserving the accepted narrow scope
  - the first review found one issue: the initial importlib guard treated aliased submodule imports such as `import importlib.metadata as importlib` as the root `importlib` module
  - the correction tightens the guard so only a true `import importlib` binding triggers `DYNAMIC_IMPORT`
  - targeted tests now cover both the dynamic-boundary happy path and the importlib-submodule-alias no-regression case
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_dependency_frontier.py -v`
  - `.venv/bin/python -m ruff check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/dependency_frontier.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the dynamic-boundary call-site honesty slice after 1 correction
  - the next control action is one bounded runtime-mutation call-site honesty slice
- Acceptance status: 1 correction

## 2026-04-19 -- Dynamic-Boundary Decomposition Spike Review

- Reviewed the returned planning spike for the next post-member-access boundary-honesty target
- Verified from fresh control-lane inspection:
  - the repo already declares `DYNAMIC_IMPORT`, `EXEC_OR_EVAL`, `METACLASS_BEHAVIOR`, and `RUNTIME_MUTATION` in the semantic contract and supported-subset boundary
  - parser tests already prove syntax extraction captures `importlib.import_module(...)`, `__import__(...)`, and `exec(...)` as call surfaces
  - current analyzer reality still misclassifies named dynamic call surfaces generically through the existing call-site frontier path
  - metaclass keyword behavior remains a silent downstream gap, but it is not the smallest next slice because the parser does not yet persist a metaclass-specific syntax fact
  - the smallest next implementation slice is the dynamic-boundary call-site honesty slice for `importlib.import_module(...)`, `__import__(...)`, `exec(...)`, and `eval(...)`
- Control review found no issues
- Validation confirmed:
  - `rg -n "DYNAMIC_IMPORT|EXEC_OR_EVAL|METACLASS_BEHAVIOR|RUNTIME_MUTATION|importlib\.import_module|__import__|exec\(|eval\(" src/context_ir tests`
  - `rg -n "metaclass|__setattr__|setattr\(|delattr\(|globals\(|locals\(" src/context_ir tests`
  - `git diff --stat`
- Acceptance decision:
  - accept the dynamic-boundary decomposition spike
  - the next control action is one bounded dynamic-boundary call-site honesty slice
- Acceptance status: first-pass

## 2026-04-19 -- Member-Heavy Internal Eval Rebaseline Review

- Reviewed the returned internal-evidence slice for the new `oracle_signal_smoke_e` asset
- Verified from fresh control-lane inspection:
  - the slice adds one new internal-only eval fixture/task/run-spec/test bundle without touching analyzer code, existing accepted smoke assets, or the accepted quad-matrix run spec
  - the new asset anchors the accepted member-access expansion work with:
    - narrow same-class `self.foo()` proof via `resolve_owner_alias`
    - shallow import-rooted member-chain proof via `pkg.labels.build_member_label`
    - honest alias-boundary surfacing via `pkg_alias.labels.build_member_label`
  - the targeted test covers deterministic selector resolution, run-spec loading, deterministic bundle execution, tight-budget baseline behavior, internal-only packaging, and selected-unit behavior at budgets `200` and `240`
  - at `200`, the asset records an honest uncertainty omission for the alias-boundary call selector; at `240`, the full intended surface is selected
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_signal_smoke_e.py -v`
  - `.venv/bin/python -m ruff check tests/test_eval_signal_smoke_e.py`
  - `.venv/bin/python -m ruff format --check tests/test_eval_signal_smoke_e.py`
  - `git diff --check -- evals/fixtures/oracle_signal_smoke_e evals/tasks/oracle_signal_smoke_e.json evals/run_specs/oracle_signal_smoke_e_matrix.json tests/test_eval_signal_smoke_e.py`
- Acceptance decision:
  - accept the member-heavy internal regression/eval rebaseline slice
  - the next control action is one bounded dynamic-boundary decomposition spike
- Acceptance status: first-pass

## 2026-04-19 -- Module/Member-Chain And Alias-Boundary Review

- Reviewed the returned resolver/frontier/tests slice for narrow shallow chain proof and honest alias boundaries
- Verified from fresh control-lane inspection:
  - `resolver.py` now proves shallow import-rooted chains only under the accepted narrow rule: visible import root, repository-module intermediate hops, and unique repository-definition final hop
  - the accepted same-class `self.foo()` proof boundary remains unchanged and still applies only to one-hop canonical `self` calls
  - `dependency_frontier.py` now emits `ALIAS_CHAIN` for shallow local assignment aliases rooted in import-backed references instead of collapsing those cases into generic unresolved or unsupported output
  - broader alias/dataflow reasoning and chains deeper than two attribute hops remain non-proof
  - targeted tests now cover proven shallow chains, preserved broader-chain non-proof, and shallow alias boundaries
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_resolver.py -q`
  - `.venv/bin/python -m pytest tests/test_dependency_frontier.py -q`
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py src/context_ir/dependency_frontier.py`
  - `git diff --check -- src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the module/member-chain and alias-boundary slice
  - the next control action is one bounded member-heavy internal regression/eval rebaseline slice
- Acceptance status: first-pass

## 2026-04-18 -- Attribute-Site Uncertainty Surfacing Review

- Reviewed the returned frontier/tests slice for explicit non-call attribute-surface honesty
- Verified from fresh control-lane inspection:
  - `dependency_frontier.py` now consumes `SemanticProgram.syntax.attribute_sites` so ordinary non-call member reads and stores stop being silently dropped
  - supported direct attribute reads/stores now surface as explicit unresolved frontier with preserved `ATTRIBUTE_ACCESS` or `STORE` context
  - unsupported attribute shapes now surface as explicit unsupported output with the honest `UNSUPPORTED_ATTRIBUTE_ACCESS` reason code
  - attribute surfaces already represented by decorator, base-expression, or call-site handling are skipped so call-callee member expressions are not double-counted
  - resolver proof boundaries remain unchanged; no `cls.foo()` support, inheritance-aware inference, or broader member proof was added
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_dependency_frontier.py -q`
  - `.venv/bin/python -m pytest tests/test_semantic_types.py -q`
  - `.venv/bin/python -m ruff check src/context_ir/dependency_frontier.py src/context_ir/semantic_types.py tests/test_dependency_frontier.py tests/test_semantic_types.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/dependency_frontier.py src/context_ir/semantic_types.py tests/test_dependency_frontier.py tests/test_semantic_types.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/dependency_frontier.py src/context_ir/semantic_types.py`
  - `git diff --check -- src/context_ir/dependency_frontier.py src/context_ir/semantic_types.py tests/test_dependency_frontier.py tests/test_semantic_types.py`
- Acceptance decision:
  - accept the attribute-site uncertainty surfacing slice
  - the next control action is one bounded module/member-chain and alias-chain handling slice
- Acceptance status: first-pass

## 2026-04-18 -- Same-Class `self.foo()` Receiver Call-Resolution Review

- Reviewed the returned resolver/tests slice for narrow same-class instance-receiver call proof
- Verified from fresh control-lane inspection:
  - `resolver.py` now adds a narrow proof path for `self.foo()` calls only when the call occurs in an undecorated method, `self` is the canonical first parameter, and the target is a uniquely defined undecorated method on the same enclosing class
  - broader receiver/member cases remain non-proof surfaces, including missing `self.foo()`, `cls.foo()`, non-self receivers such as `helper.build()`, decorated target methods, and other out-of-scope member patterns
  - no code change was required in `dependency_frontier.py`; frontier behavior updates automatically from the new resolver proof
  - targeted resolver and dependency-frontier tests now cover both the supported same-class proof path and preserved unresolved frontier cases
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_resolver.py -q`
  - `.venv/bin/python -m pytest tests/test_dependency_frontier.py -q`
  - `.venv/bin/python -m ruff check src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/resolver.py src/context_ir/dependency_frontier.py`
  - `git diff --check -- src/context_ir/resolver.py src/context_ir/dependency_frontier.py tests/test_resolver.py tests/test_dependency_frontier.py`
- Acceptance decision:
  - accept the same-class `self.foo()` receiver call-resolution slice
  - the next control action is one bounded attribute-site uncertainty surfacing slice
- Acceptance status: first-pass

## 2026-04-18 -- Phase-2 Hybrid-Coverage Priority Spike Review

- Reviewed the returned planning spike ranking post-phase-1 broad-Python coverage priorities
- Verified from fresh control-lane inspection:
  - the spike correctly identifies shallow member-access coverage as the highest-leverage next target because parser facts already capture calls and attribute sites while resolver proof still stops at simple names and import-backed direct attributes
  - the spike correctly identifies dynamic-boundary surfacing and decorator/object-model broadening beyond `@dataclass` as later phase-2 targets rather than immediate first slices
  - the spike correctly treats the next move as a bounded decomposition step rather than a broad implementation jump
- Control review found two issues before advancement:
  - the proposed first execution slice bundled `self.foo()` and `cls.foo()` together even though current repo reality does not yet justify classmethod/`cls` semantics
  - the proposed prompt omitted the required execution-lane completion-state and return-shape fields required by `AGENTS.md`
- Human sign-off was given to hold the spike and rewrite the prompt before advancement
- Acceptance decision after control correction:
  - accept the phase-2 hybrid-coverage priority and decomposition spike after one control correction with human sign-off
  - narrow the first implementation slice to same-class `self.foo()` receiver call resolution only
  - the next control action is one bounded same-class `self.foo()` receiver call-resolution implementation slice
- Acceptance status: 1 control correction with human sign-off

## 2026-04-18 -- Tier-Aware Diagnose/Recompile And Internal Evidence Gate Review

- Reviewed the returned code-and-tests slice adding typed boundary-aware diagnose/recompile behavior
- Verified from fresh control-lane inspection:
  - `semantic_types.py` now defines typed diagnostic boundary contracts for unit status, tier-aware boundary kind, and per-unit diagnostic boundary classification
  - `semantic_diagnostics.py` now consumes selection and warning trace summaries when present, with category fallback only when no trace summary exists
  - diagnose now treats frontier and unsupported units without attached runtime-backed provenance as surfaced non-proof boundary work once identity is present, instead of classifying them as generic static too-shallow misses
  - recompile boosts now preserve proof/runtime/frontier/unsupported distinctions by using strong proof-like boosts only for statically proved misses and conservative boosts for non-proof boundary work
  - targeted tests now cover proof-backed misses, warning-trace fallback for omitted unsupported units, no-runtime frontier boundary handling, and additive runtime-backed frontier upgrades
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/semantic_types.py src/context_ir/semantic_diagnostics.py src/context_ir/__init__.py tests/test_semantic_types.py tests/test_semantic_diagnostics.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/semantic_types.py src/context_ir/semantic_diagnostics.py src/context_ir/__init__.py tests/test_semantic_types.py tests/test_semantic_diagnostics.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/semantic_types.py src/context_ir/semantic_diagnostics.py src/context_ir/semantic_optimizer.py src/context_ir/semantic_compiler.py`
  - `.venv/bin/python -m pytest tests/test_semantic_types.py tests/test_semantic_diagnostics.py -v`
  - `git diff --check -- src/context_ir/semantic_types.py src/context_ir/semantic_diagnostics.py src/context_ir/__init__.py tests/test_semantic_types.py tests/test_semantic_diagnostics.py`
- Acceptance decision:
  - accept the tier-aware diagnose/recompile and internal evidence gate slice
  - the next control action is one bounded phase-2 hybrid-coverage priority and decomposition spike
- Acceptance status: first-pass

## 2026-04-18 -- Tier-Aware Optimization And Compile Trace Propagation Correction Review

- Reviewed the returned correction slice for the held tier-aware optimization and compile trace propagation work
- Verified from fresh control-lane inspection:
  - `semantic_types.py` now defines shared typed validators so provenance records and trace summaries enforce the same capability-tier origin/replay invariants and subject-kind tier admissibility rules
  - `SemanticUnitTraceSummary` now rejects impossible primary tier/origin/replay combinations and rejects `RUNTIME_BACKED` as primary truth, keeping runtime record IDs additive only
  - targeted semantic-type tests now cover misaligned primary trace contracts, invalid subject-kind and primary-tier combinations, and the additive-only runtime provenance rule
  - the previously returned optimizer and compiler propagation behavior remains intact and now sits on a hardened typed trace contract
- Control review found no issues after the correction
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/semantic_types.py tests/test_semantic_types.py tests/test_semantic_optimizer.py tests/test_semantic_compiler.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/semantic_types.py tests/test_semantic_types.py tests/test_semantic_optimizer.py tests/test_semantic_compiler.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/semantic_types.py src/context_ir/semantic_optimizer.py src/context_ir/semantic_compiler.py`
  - `.venv/bin/python -m pytest tests/test_semantic_types.py tests/test_semantic_optimizer.py tests/test_semantic_compiler.py -v`
  - `git diff --check -- src/context_ir/semantic_types.py tests/test_semantic_types.py tests/test_semantic_optimizer.py tests/test_semantic_compiler.py`
- Acceptance decision:
  - accept the tier-aware ranking, optimization, and compile propagation slice after correction
  - the held trace-summary contract-rigor gap is now closed
  - the next control action is one bounded tier-aware diagnose/recompile and internal evidence gate slice
- Acceptance status: 1 correction

## 2026-04-18 -- Runtime-Backed Acquisition Infrastructure Correction Review

- Reviewed the returned correction slice for the held runtime-backed acquisition implementation
- Verified from fresh control-lane inspection:
  - `semantic_types.py` now permits `CapabilityTier.RUNTIME_BACKED` on existing `FRONTIER_ITEM` and `UNSUPPORTED_FINDING` subjects while preserving the existing non-runtime tier mappings and runtime-only metadata requirements
  - `runtime_acquisition.py` now resolves known frontier and unsupported subject IDs to their existing subject sites instead of hard-rejecting them
  - targeted tests now cover successful runtime-backed attachment for frontier and unsupported subjects rather than locking in rejection behavior
  - analyzer defaults remain phase-0-safe because `analyze_repository(...)` still returns `provenance_records == []`
- Control review found no issues after the correction
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/semantic_types.py src/context_ir/runtime_acquisition.py tests/test_semantic_types.py tests/test_runtime_acquisition.py tests/test_analyzer.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/semantic_types.py src/context_ir/runtime_acquisition.py tests/test_semantic_types.py tests/test_runtime_acquisition.py tests/test_analyzer.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/semantic_types.py src/context_ir/runtime_acquisition.py src/context_ir/analyzer.py`
  - `.venv/bin/python -m pytest tests/test_runtime_acquisition.py tests/test_semantic_types.py tests/test_analyzer.py -v`
  - `git diff --check -- src/context_ir/semantic_types.py src/context_ir/runtime_acquisition.py tests/test_semantic_types.py tests/test_runtime_acquisition.py`
- Acceptance decision:
  - accept the runtime-backed acquisition infrastructure slice after correction
  - the held frontier/unsupported admissibility mismatch is now closed
  - the next control action is one bounded tier-aware ranking, optimization, and compile propagation slice
- Acceptance status: 1 correction

## 2026-04-18 -- Runtime-Backed Provenance Metadata Schema Alignment Review

- Reviewed the returned code-and-tests slice aligning the provenance schema with the accepted runtime-backed admissibility boundary
- Verified from fresh control-lane inspection:
  - `semantic_types.py` now defines public dataclass metadata types for repository snapshot basis and runtime attachment linkage
  - `SemanticProvenanceRecord` now carries runtime-backed repository snapshot basis and attachment linkage fields
  - runtime-only invariants now require those metadata fields for `RUNTIME_BACKED` records and reject them on non-runtime tiers
  - analyzer behavior remains phase-0-default because `provenance_records` still defaults to `[]` and no population behavior was added
  - targeted semantic-type tests now cover valid runtime-backed construction plus rejection of missing or misplaced runtime-backed metadata
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/semantic_types.py src/context_ir/__init__.py tests/test_semantic_types.py tests/test_analyzer.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/semantic_types.py src/context_ir/__init__.py tests/test_semantic_types.py tests/test_analyzer.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/semantic_types.py src/context_ir/__init__.py src/context_ir/analyzer.py`
  - `.venv/bin/python -m pytest tests/test_semantic_types.py tests/test_analyzer.py -v`
  - `git diff --check -- src/context_ir/semantic_types.py src/context_ir/__init__.py tests/test_semantic_types.py tests/test_analyzer.py`
- Acceptance decision:
  - accept the runtime-backed provenance metadata schema alignment slice
  - the next control action is one bounded runtime-backed acquisition infrastructure slice against the accepted admissibility boundary and aligned schema
- Acceptance status: first-pass

## 2026-04-18 -- Runtime-Backed Evidence Admissibility Boundary Review

- Reviewed the returned docs slice defining the admissibility boundary for runtime-backed evidence
- Verified from fresh control-lane inspection:
  - `ARCHITECTURE.md` now states explicit admission conditions for runtime-backed evidence: repository linkage, stable probe identity, replay contract, reproducible outcome, and additive provenance attachment
  - the architecture now states the minimum attachable runtime-backed record, including repository snapshot basis and attachment linkage, without claiming any implementation
  - explicit non-admissible cases now prevent manual notes, unreplayable runs, crashes/timeouts, heuristic co-occurrence, and untracked instrumentation from being treated as runtime-backed proof
  - `PLAN.md` now places admissibility ahead of later runtime-backed work in the phase-1 queue
- Control review found no issues
- Validation confirmed:
  - targeted `rg` checks for runtime-backed admissibility language, phase-0 boundary preservation, and forbidden overclaim wording passed
  - `git diff --check -- ARCHITECTURE.md PLAN.md` returned clean
- Acceptance decision:
  - accept the runtime-backed evidence admissibility boundary slice
  - the next control action is one bounded runtime-backed provenance metadata schema alignment slice so the code-facing contract can carry repository snapshot basis and attachment linkage before acquisition infrastructure begins
- Acceptance status: first-pass

## 2026-04-18 -- SemanticProgram Provenance Schema/Types Review

- Reviewed the returned code-and-tests slice widening the semantic contract for provenance-bearing records
- Verified from fresh control-lane inspection:
  - `semantic_types.py` now defines explicit provenance contract types for capability tier, evidence origin, replay status, downstream visibility, subject kind, and per-record provenance
  - `SemanticProgram` now carries `provenance_records` with a default-empty phase-0-safe surface
  - provenance invariants now reject inconsistent tier/origin/replay combinations and keep frontier and unsupported subject kinds aligned to their non-proof tiers
  - package-root exports now include the new public provenance contract types
  - targeted tests now cover backward-compatible empty defaults, explicit provenance record construction across all four tiers, invariant rejection, and analyzer outputs remaining phase-0-default
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/context_ir/semantic_types.py src/context_ir/__init__.py tests/test_semantic_types.py tests/test_analyzer.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/semantic_types.py src/context_ir/__init__.py tests/test_semantic_types.py tests/test_analyzer.py`
  - `.venv/bin/python -m mypy --strict src/context_ir/semantic_types.py src/context_ir/__init__.py src/context_ir/analyzer.py`
  - `.venv/bin/python -m pytest tests/test_semantic_types.py tests/test_analyzer.py -v`
  - `git diff --check -- src/context_ir/semantic_types.py src/context_ir/__init__.py tests/test_semantic_types.py tests/test_analyzer.py`
- Acceptance decision:
  - accept the `SemanticProgram` provenance schema/types slice as the first bounded code reopening under the post-milestone program
  - the next control action is one bounded runtime-backed evidence admissibility boundary slice before any acquisition or propagation work
- Acceptance status: first-pass

## 2026-04-18 -- Phase-1 Capability-Tier Contract And Decomposition Review

- Reviewed the returned phase-1 docs slice covering capability-tier semantics, widened `SemanticProgram` provenance boundaries, and downstream compile/diagnose preservation rules
- Verified from fresh control-lane inspection:
  - `ARCHITECTURE.md` now defines the four capability tiers and keeps them explicitly separate from representation tiers
  - the contract now states that runtime-backed evidence is additive provenance rather than a substitute for static proof
  - the future widened `SemanticProgram` boundary is specified at the contract level with required provenance-bearing record categories and invariants, without claiming implementation
  - compile, diagnose, and recompile preservation rules now state how mixed-tier artifacts must remain traceable rather than collapsing into one unlabeled proof bucket
  - `PLAN.md` now decomposes phase 1 into five bounded follow-on slices, with `SemanticProgram` provenance schema/types as the first code-facing reopening
- Control review found no issues
- Validation confirmed:
  - targeted `rg` checks for capability-tier taxonomy, decomposition, and forbidden overclaim language passed
  - `git diff --check -- ARCHITECTURE.md PLAN.md` returned clean
- Acceptance decision:
  - accept the phase-1 capability-tier contract/decomposition slice
  - the next control action is one bounded `SemanticProgram` provenance schema/types slice as the first code reopening under the post-milestone program
- Acceptance status: first-pass

## 2026-04-18 -- Capability-Tier Rebaseline Control-State Sync

- Updated `PLAN.md`, `BUILDLOG.md`, `ARCHITECTURE.md`, and `EVAL.md` so the accepted post-milestone roadmap is now encoded as durable control-state
- Preserved as closed current truths:
  - the semantic-first / deterministic-evidence / reviewer-stack milestone remains the completed phase 0 foundation
  - the accepted quad matrix remains the current top internal evidence surface and regression anchor
  - the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation remains explicit current and historical truth
  - the current README / public-claim / portfolio stack remains unchanged and closed unless later evidence gates justify reopening it
- Recorded the governing roadmap for the new program:
  - broad Python repo coverage is now the target, pursued through hybrid static + runtime analysis
  - capability tier framing is distinct from representation tiers
  - future contracts and eval methodology must keep statically proved, runtime-backed, heuristic/frontier, and unsupported/opaque surfaces explicitly separate
  - external benchmark leadership remains gated on reproducible public methodology plus raw published results
  - production maturity remains gated on packaging, compatibility, interoperability, error handling, CI/release evidence, and observability
- Acceptance decision:
  - accept this control-state rebaseline as the governing roadmap for post-phase-0 work
  - the next control action is one bounded phase-1 contract/decomposition slice for capability-tier and hybrid-analysis boundary design before code changes
- Acceptance status: first-pass

## 2026-04-18 -- North-Star Rebaseline Planning Spike Review

- Reviewed the returned spike on how to turn the newly authorized post-milestone north star into a sequenced roadmap
- Verified from fresh control-lane inspection:
  - the proposed framing keeps the current semantic-first / deterministic-evidence / reviewer-stack milestone intact as the accepted phase-0 foundation rather than erasing it
  - the recommendation correctly reopens only the boundaries needed for the new program:
    - `analyze_repository(...)` / `SemanticProgram` contract shape
    - supported-subset policy toward explicit capability tiers
    - dependency/frontier and uncertainty model
    - renderer / compiler / diagnose contracts
    - ranking / optimization policy for mixed-evidence selection
    - eval and claim-gating model
    - MCP / product boundary
    - the distinction between capability tiers and representation tiers
  - the recommendation correctly keeps the accepted quad matrix as the completed current program's top internal evidence surface and regression anchor, not as external benchmark proof
  - the recommendation correctly preserves the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation as historical truth rather than a defect to silently optimize away
  - the recommendation correctly keeps external benchmark leadership and production maturity contingent on later evidence gates rather than planning-time wording
- Control review found one issue in the initial proposed next prompt:
  - it was under-specified relative to `AGENTS.md` implementation-slice requirements and omitted explicit blind spots, what must not be reopened, docs/tests/schema scope, and expected pass condition
- Ryan explicitly approved holding the spike at the quality gate, rewriting the prompt, and then advancing
- Acceptance decision:
  - accept the planning-spike recommendation after 1 control correction with human sign-off
  - the next control action is one bounded docs-only slice to update `PLAN.md`, `BUILDLOG.md`, `ARCHITECTURE.md`, and `EVAL.md` so the new capability-tier / hybrid-program roadmap is encoded before implementation
  - keep `README.md`, `PUBLIC_CLAIMS.md`, and all portfolio-facing artifacts out of scope for that slice
- Acceptance status: 1 correction

## 2026-04-18 -- North-Star Rebaseline Authorization

- Ryan explicitly authorized a new post-milestone north star after the accepted current program closeout
- Authorized target framing:
  - best-in-class agent context system for broad Python repos
  - explicit capability tiers
  - strong external benchmark performance
  - production-grade reliability
- Control interpretation:
  - the current semantic-first / deterministic-evidence / reviewer-stack milestone remains accepted and complete as a separate finished program state
  - the newly authorized work is a new program that may reopen analyzer architecture, uncertainty modeling, eval methodology, public-claim boundaries, MCP/product scope, and operational packaging, but only through an explicit rebaseline plan
- Acceptance decision:
  - do not jump directly into implementation
  - the next control action is one bounded north-star rebaseline planning spike to define phases, reopened boundaries, risks, and acceptance criteria
  - keep the existing accepted portfolio-facing stack stable unless the new roadmap later proves a concrete reason to revise it
- Acceptance status: first-pass

## 2026-04-18 -- Post-Polished-Case-Study Portfolio-Readiness Planning Review

- Reviewed the returned spike on the single highest-signal next move after the polished case-study layer
- Verified from fresh control-lane inspection:
  - the current outward-facing repo-native stack is coherent, reviewer-usable, and now includes:
    - `README.md`
    - `EVAL.md`
    - `PUBLIC_CLAIMS.md`
    - `PORTFOLIO_SOURCE_BRIEF.md`
    - `PORTFOLIO_TECHNICAL_BRIEF.md`
    - `PORTFOLIO_OVERVIEW.md`
    - `PORTFOLIO_CASE_STUDY_SOURCE.md`
    - `PORTFOLIO_CASE_STUDY.md`
  - the recommendation correctly distinguishes packaging convenience from substantive portfolio-readiness gain
  - a presentation-packaging source layer would add format-translation convenience, but no new evidence, no new claim authority, and no missing reviewer-facing substance inside the repo
  - an explicit stop is therefore the highest-signal move under the current evidence and claim boundary
- Control review found no issues
- Acceptance decision:
  - accept the planning-spike recommendation
  - do not issue a new execution slice now
  - treat the current outward-facing repo-native stack as sufficient for frontier-lab technical review until a concrete downstream presentation channel or new evidence/claim authorization appears
- Acceptance status: first-pass

## 2026-04-18 -- Portfolio Case Study Review

- Reviewed the returned `PORTFOLIO_CASE_STUDY.md` against the accepted public-claim envelope, derivative-artifact rules, and polished case-study slice contract
- Verified from fresh control-lane inspection:
  - `PORTFOLIO_CASE_STUDY.md` exists and follows the required section structure
  - the document stays derivative of `PUBLIC_CLAIMS.md` and the accepted outward-facing doc stack rather than becoming a second claim authority
  - `oracle_signal_smoke_d` is used as one illustrative internal case and not generalized beyond the accepted internal quad matrix
  - comparative wording remains subordinate and explicitly scoped to the accepted internal quad matrix
  - the accepted global limitation remains explicit: `oracle_signal_smoke_b / 200` still records `budget_pressure`, and `def:pkg/digest.py:pkg.digest.render_assignment_digest` can remain omitted
  - the document reads as a restrained reviewer-facing case study rather than source notes or marketing copy
- Control review found no issues
- Validation confirmed:
  - file existence check passed
  - section checks passed
  - targeted grep checks confirmed required scoping and limitation markers
  - disallowed-phrasing grep returned no matches
  - word-count check stayed inside the intended target range
- Acceptance decision:
  - accept `PORTFOLIO_CASE_STUDY.md` as the polished reviewer-facing case-study layer
  - keep `PUBLIC_CLAIMS.md` as the sole claim source and keep the case study derivative and claim-bounded
  - the next control action is one bounded planning spike to decide whether the next move should be a presentation-packaging source layer or an explicit stop
- Acceptance status: first-pass

## 2026-04-18 -- Post-Case-Study Portfolio-Readiness Planning Review

- Reviewed the returned spike on the single highest-signal next move after the current outward-facing doc stack plus case-study source
- Verified from fresh control-lane inspection:
  - the current outward-facing stack is coherent, reviewer-usable, and now includes:
    - `README.md`
    - `EVAL.md`
    - `PUBLIC_CLAIMS.md`
    - `PORTFOLIO_SOURCE_BRIEF.md`
    - `PORTFOLIO_TECHNICAL_BRIEF.md`
    - `PORTFOLIO_OVERVIEW.md`
    - `PORTFOLIO_CASE_STUDY_SOURCE.md`
  - the recommendation is directionally correct: the highest-signal next move is a polished but still conservative case-study layer derived from the accepted stack
  - the first returned execution prompt had one control-lane issue:
    - it referred to "required sections" but did not define an explicit required section structure for `PORTFOLIO_CASE_STUDY.md`
    - that left the slice under-specified for review and acceptance
- Control review held the prompt at the quality gate and recommended a prompt rewrite rather than advancing as-is
- Ryan explicitly approved the rewrite and authorized proceeding with a corrected execution-ready prompt
- Acceptance decision:
  - accept the planning-spike recommendation after one control correction
  - the next control action is one bounded docs slice to author `PORTFOLIO_CASE_STUDY.md`
  - keep the case-study polished but restrained, derivative, evidence-linked, and inside the accepted claim envelope
  - keep presentation packaging, slide/site work, and broader portfolio framing out of scope for that slice
- Acceptance status: 1 correction

## 2026-04-18 -- Portfolio Case-Study Source Review

- Reviewed the returned `PORTFOLIO_CASE_STUDY_SOURCE.md` against the accepted public-claim envelope, derivative-artifact rules, and representative-case slice contract
- Verified from fresh control-lane inspection:
  - `PORTFOLIO_CASE_STUDY_SOURCE.md` exists and follows the required section structure
  - the document stays derivative of `PUBLIC_CLAIMS.md` and the accepted outward-facing doc stack rather than becoming a second claim authority
  - `oracle_signal_smoke_d` is used as an illustrative internal case because it broadens the accepted surface in the method/class/dataclass direction
  - comparative wording remains explicitly scoped to the accepted internal quad matrix
  - the accepted global limitation remains explicit: `oracle_signal_smoke_b / 200` still records `budget_pressure`, and `def:pkg/digest.py:pkg.digest.render_assignment_digest` can remain omitted
- Control review found no issues
- Validation confirmed:
  - file existence check passed
  - section checks passed
  - targeted grep checks confirmed derivative/scoping/limitation markers
  - disallowed-phrasing grep returned no matches
- Acceptance decision:
  - accept `PORTFOLIO_CASE_STUDY_SOURCE.md` as the representative-case source layer in the outward-facing doc stack
  - keep `PUBLIC_CLAIMS.md` as the sole claim source and keep the case-study source derivative and illustrative rather than generalizing
  - the next control action is one bounded planning spike to identify the single highest-signal move after the current doc stack plus case-study source
- Acceptance status: first-pass

## 2026-04-18 -- Post-Overview Portfolio-Readiness Planning Review

- Reviewed the returned spike on the single highest-signal next portfolio-facing move after the current reviewer-facing doc stack
- Verified from fresh control-lane inspection:
  - the current outward-facing repo-native stack is now coherent and reviewer-usable:
    - `README.md`
    - `EVAL.md`
    - `PUBLIC_CLAIMS.md`
    - `PORTFOLIO_SOURCE_BRIEF.md`
    - `PORTFOLIO_TECHNICAL_BRIEF.md`
    - `PORTFOLIO_OVERVIEW.md`
  - the recommendation identifies the real remaining gap correctly: the stack still lacks one concrete representative walkthrough tying the semantic-first thesis to the current accepted evidence surface
  - `PORTFOLIO_CASE_STUDY_SOURCE.md` is a tighter next step than another general repo-native doc, a presentation-packaging layer, or an immediate stop
  - the proposed slice keeps `PUBLIC_CLAIMS.md` as the sole claim source, keeps comparative language scoped to the accepted internal quad matrix, and preserves the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation
- Control review found no issues
- Acceptance decision:
  - accept the planning-spike recommendation
  - the next control action is one bounded docs slice to author `PORTFOLIO_CASE_STUDY_SOURCE.md`
  - keep the case-study source derivative, evidence-linked, non-promotional, and illustrative rather than generalizing
  - keep polished case-study copy, presentation packaging, and broader portfolio/site rewrite out of scope for that slice
- Acceptance status: first-pass

## 2026-04-18 -- Portfolio Reviewer Overview Review

- Reviewed the returned `PORTFOLIO_OVERVIEW.md` against the accepted public-claim envelope, derivative-artifact rules, and reviewer-orientation slice contract
- Verified from fresh control-lane inspection:
  - `PORTFOLIO_OVERVIEW.md` exists and follows the required section structure
  - the document stays derivative of `PUBLIC_CLAIMS.md` and consistent with `PORTFOLIO_TECHNICAL_BRIEF.md`
  - the overview remains short, reviewer-oriented, and technical rather than drifting into benchmark language or polished marketing prose
  - the accepted internal quad-matrix comparison remains subordinate and explicitly scoped
  - the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation and omitted-support caveat remain explicit
- Control review found no issues
- Validation confirmed:
  - file existence check passed
  - section checks passed
  - targeted grep checks confirmed supported-subset wording, quad-matrix wording, claim-source wording, and limitation language
  - disallowed-phrasing grep returned no matches
  - word-count check confirmed the document remains inside the intended short-form range
- Acceptance decision:
  - accept `PORTFOLIO_OVERVIEW.md` as the short reviewer-orientation layer in the outward-facing repo-native stack
  - keep `PUBLIC_CLAIMS.md` as the sole claim source and keep the overview derivative
  - the next control action is one bounded planning spike to identify the single highest-signal next portfolio-facing move after the current doc stack
- Acceptance status: first-pass

## 2026-04-18 -- Portfolio-Readiness Gap Assessment Review

- Reviewed the returned spike on the single highest-signal remaining outward-facing gap against the accepted claim envelope and current repo-native outward-facing stack
- Verified from fresh control-lane inspection:
  - the current stack is correctly described as:
    - `README.md`
    - `EVAL.md`
    - `PUBLIC_CLAIMS.md`
    - `PORTFOLIO_SOURCE_BRIEF.md`
    - `PORTFOLIO_TECHNICAL_BRIEF.md`
  - the recommendation identifies a real remaining gap: there is still no short reviewer-orientation layer that a new external reader can use before dropping into the deeper technical and evidence docs
  - `PORTFOLIO_OVERVIEW.md` is a tighter next step than a case-study, comparison appendix, or broader packaging/demo slice
  - the proposed slice keeps `PUBLIC_CLAIMS.md` as the sole claim source and keeps the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation explicit
- Control review found no issues
- Acceptance decision:
  - accept the planning-spike recommendation
  - the next control action is one bounded docs slice to author `PORTFOLIO_OVERVIEW.md`
  - keep the overview short, reviewer-oriented, derivative, conservative, and non-promotional
  - keep broader case-study work, comparison-led presentation, packaging, and demo work out of scope for that slice
- Acceptance status: first-pass

## 2026-04-18 -- Portfolio Technical Brief Review

- Reviewed the returned `PORTFOLIO_TECHNICAL_BRIEF.md` against the accepted public-claim envelope, derivative-source rules, and outward-facing brief slice contract
- Verified from fresh control-lane inspection:
  - `PORTFOLIO_TECHNICAL_BRIEF.md` exists and follows the required section structure
  - the brief stays within `PUBLIC_CLAIMS.md` and does not become a second claim authority
  - `PORTFOLIO_SOURCE_BRIEF.md` remains derivative source material only
  - the outward-facing surface stays technical, concise, and pre-marketing rather than drifting into polished portfolio prose
  - comparative language remains subordinate inside the evidence section and explicitly scoped to the accepted internal quad matrix
  - the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation and omitted-support caveat remain explicit
- Control review found no issues
- Validation confirmed:
  - file existence check passed
  - section checks passed
  - targeted grep checks confirmed supported-subset wording, interface wording, quad-matrix phrasing, and limitation language
  - disallowed-phrasing grep returned no matches
- Acceptance decision:
  - accept `PORTFOLIO_TECHNICAL_BRIEF.md` as the first outward-facing repo-native technical brief
  - keep `PUBLIC_CLAIMS.md` as the sole claim source and `PORTFOLIO_SOURCE_BRIEF.md` as derivative source material
  - the next control action is one bounded planning spike to identify the single highest-signal remaining gap to frontier-lab portfolio readiness and define the next exact slice
- Acceptance status: first-pass

## 2026-04-18 -- Outward-Facing Artifact Planning Spike Review

- Reviewed the returned planning spike for the first outward-facing repo-native copy artifact against the accepted claim envelope and derivative-source scaffold
- Verified from fresh control-lane inspection:
  - the candidate-artifact analysis stays within the accepted public-claim boundary in `PUBLIC_CLAIMS.md`
  - `PORTFOLIO_TECHNICAL_BRIEF.md` is the strongest first outward-facing artifact because it is smaller and less drift-prone than a general overview or case-study document
  - the recommended structure keeps the doc readable for an external reviewer while keeping comparison language subordinate to the evidence section
  - the recommendation preserves `PUBLIC_CLAIMS.md` as the sole claim source and `PORTFOLIO_SOURCE_BRIEF.md` as derivative source material only
  - the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation remains part of the required framing rather than being softened or omitted
- Control review found no issues
- Acceptance decision:
  - accept the planning-spike recommendation
  - the next control action is one bounded docs slice to author `PORTFOLIO_TECHNICAL_BRIEF.md`
  - keep the brief technical, concise, evidence-linked, and pre-marketing
  - keep broader portfolio/site copy, narrative case-study work, and comparison-led presentation out of scope for that slice
- Acceptance status: first-pass

## 2026-04-18 -- Portfolio Source Brief Review

- Reviewed the returned `PORTFOLIO_SOURCE_BRIEF.md` against the accepted claim boundary and the derivative-brief slice contract
- Verified from fresh control-lane inspection:
  - `PORTFOLIO_SOURCE_BRIEF.md` exists and follows the required section structure
  - the brief remains derivative of `PUBLIC_CLAIMS.md` rather than becoming a second source of truth
  - the document stays technical and source-oriented instead of drifting into polished portfolio copy
  - the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation is preserved
  - comparative wording remains explicitly scoped to the accepted internal quad matrix
- Control review found no issues
- Validation confirmed:
  - file existence check passed
  - section checks passed
  - targeted grep checks confirmed AC1-AC4, limitation language, quad-matrix scoping, supported-subset wording, and `Evidence:` anchors
- Acceptance decision:
  - accept `PORTFOLIO_SOURCE_BRIEF.md` as the derivative portfolio-source scaffold
  - keep `PUBLIC_CLAIMS.md` as the sole claim source
  - the next control action is one bounded planning spike to define the exact first outward-facing repo-native copy artifact and its structure before authoring polished copy
- Acceptance status: first-pass

## 2026-04-18 -- Portfolio-Artifact Planning Spike Review

- Reviewed the returned planning spike for the next portfolio-facing repo artifact against the accepted evidence boundary and claim-gating state
- Verified from fresh control-lane inspection:
  - the candidate-artifact analysis stays within the accepted claim envelope in `PUBLIC_CLAIMS.md`
  - `PORTFOLIO_SOURCE_BRIEF.md` is the smallest useful next artifact because it organizes allowed claims, required qualifiers, and limitations without widening into polished portfolio copy
  - the recommended artifact keeps `PUBLIC_CLAIMS.md` as the sole claim source rather than creating a second authority
- Control review found no issues
- Acceptance decision:
  - accept the planning-spike recommendation
  - the next control action is one bounded docs slice to create `PORTFOLIO_SOURCE_BRIEF.md` as a derivative portfolio-source brief
  - keep later portfolio/site copy, narrative case-study work, and broader positioning out of scope for that slice
- Acceptance status: first-pass

## 2026-04-18 -- Public-Claims Crosswalk Review

- Reviewed the returned `PUBLIC_CLAIMS.md` crosswalk against the accepted evidence boundary and current claim-gating docs
- Verified from fresh control-lane inspection:
  - `PUBLIC_CLAIMS.md` exists and contains the required sections:
    - `Allowed Claims`
    - `Required Qualifiers`
    - `Disallowed Phrasings`
    - `Evidence Map`
  - the allowed claims stay scoped to accepted repo-local evidence only
  - comparative wording stays explicitly scoped to the fixed internal quad matrix
  - the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` blemish is preserved as a current limitation
  - the triple matrix remains prior internal evidence and the quad matrix remains the current top surface
- Control review found no issues
- Validation confirmed:
  - `test -f PUBLIC_CLAIMS.md`
  - section checks via `rg`
  - evidence-anchor checks via `rg`
- Acceptance decision:
  - accept `PUBLIC_CLAIMS.md` as the durable public-claim crosswalk
  - use it as the sole claim source for later portfolio-facing copy
  - the next control action is one bounded planning spike to define the exact portfolio-facing repo artifact and structure before drafting outward-facing copy
- Acceptance status: first-pass

## 2026-04-18 -- Evidence-Ledger / Claim-Gating Sync Review

- Reviewed the returned `EVAL.md` / `README.md` evidence-ledger sync against repo reality and accepted evidence boundaries
- Verified from fresh control-lane inspection:
  - `EVAL.md` now reflects the accepted deterministic internal eval harness through summary, report, pipeline, manifest, and bundle artifacts
  - `EVAL.md` and `README.md` now reflect the accepted four-asset signal surface:
    - `oracle_signal_smoke`
    - `oracle_signal_smoke_b`
    - `oracle_signal_smoke_c`
    - `oracle_signal_smoke_d`
  - both docs now reflect the accepted quad matrix as the current broader evidence surface:
    - `4` tasks x `2` budgets x `3` providers
    - `context_ir` wins all `8/8` task-budget rows
    - provider-average aggregate scores are recorded conservatively and correctly
  - both docs preserve the accepted `oracle_signal_smoke_b` / `200` `budget_pressure` blemish as an explicit tight-budget limitation
  - the earlier triple matrix is retained as prior internal evidence, not the current top surface
- Control review found no issues
- Validation confirmed:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_signal_smoke.py tests/test_eval_signal_smoke_b.py tests/test_eval_signal_smoke_c.py tests/test_eval_signal_smoke_d.py -q` with 28 passed
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_bundle.py tests/test_eval_manifest.py tests/test_eval_pipeline.py tests/test_eval_report.py tests/test_eval_summary.py -q` with 36 passed
  - targeted grep checks confirmed the stale "not implemented yet" / "Current evidence is limited to" wording is removed while the current quad-matrix and `budget_pressure` wording remains
- Acceptance decision:
  - accept the evidence-ledger / claim-gating sync
  - keep public claims conservative and strictly bounded by the synced `EVAL.md`
  - the next control action is one bounded planning spike to define the frontier-lab-facing public-claim envelope that current evidence supports
- Acceptance status: first-pass

## 2026-04-18 -- Smoke D Shaping Correction Review

- Reviewed the returned `oracle_signal_smoke_d` shaping correction against repo reality and the held fourth-asset / quad-matrix contract
- Verified from fresh control-lane reruns and artifact inspection:
  - the corrected `oracle_signal_smoke_d` asset remains materially different in semantic shape from the accepted trio:
    - method-oriented edit target
    - inherited base-class support surface
    - narrow accepted `@dataclass` support surface
  - the held weakness is now closed:
    - at `200`, `context_ir` now reaches support coverage `0.5`, uncertainty honesty `1.0`, warnings `[]`, and aggregate `0.8435567010309278`
    - at `240`, `context_ir` now reaches support coverage `1.0`, uncertainty honesty `1.0`, warnings `[]`, and aggregate `0.9639484978540772`
  - the accepted `oracle_signal_smoke_b` / `200` blemish remains unchanged:
    - support coverage `0.6666666666666666`
    - uncertainty honesty `1.0`
    - warnings `['budget_pressure']`
  - the broader-evidence expansion now holds cleanly:
    - quad-matrix provider-average aggregate remains led by `context_ir` at `0.9599139230003012`
    - file baselines remain behind at `0.6065653086866415` and `0.6228480543023547`
    - `context_ir` remains winner on all `8/8` task-budget rows
  - determinism holds across two independent corrected single-asset and quad-matrix runs:
    - `ledger.jsonl` matched exactly
    - `report.md` matched exactly
    - `manifest.json` matched after normalizing caller-chosen artifact paths and generation timestamp
- Control review found no issues
- Acceptance decision:
  - accept the corrected fourth asset and quad-matrix expansion
  - keep the accepted triple matrix as the prior anchor and the quad matrix as the current broader-evidence surface
  - keep the accepted `oracle_signal_smoke_b` / `200` blemish as an explicit documented tight-budget limit
- Acceptance status: first-pass

## 2026-04-18 -- Fourth-Asset / Quad-Matrix Expansion Review

- Reviewed the returned fourth-asset / quad-matrix expansion against repo reality and the accepted slice contract
- Verified from fresh control-lane inspection:
  - the new `oracle_signal_smoke_d` asset is materially different in semantic shape from the accepted trio:
    - method-oriented edit target
    - imported-base support surface
    - narrow accepted `@dataclass` support surface
  - the reported validation and determinism claims are consistent with the workspace and emitted bundle artifacts
  - the quad-matrix provider-average lead survives and `context_ir` still wins all `8/8` task-budget rows
- Review found one issue before acceptance:
  - the new fourth asset is too weak to accept as a high-quality broader-evidence expansion in its current form
  - `oracle_signal_smoke_d` recovers only `1/3` support coverage at both budgets and still carries `budget_pressure` at `240`
  - the task asks for two source-level support methods, but the current `context_ir` row does not recover either source-level method as required support
  - the new test contract locks that weakness in as acceptable instead of treating it as the problem to solve
- Reasoning:
  - broadening the surface is directionally correct, but accepting a broadened-yet-weak fourth asset would dilute the evidence upgrade this slice was supposed to create
  - the issue is narrow enough to address through `oracle_signal_smoke_d` fixture/task/test shaping without reopening accepted methodology, providers, budgets, or prior assets
- Human sign-off:
  - Ryan explicitly approved one narrow correction prompt rather than accepting the quad matrix as mixed evidence
- Decision:
  - hold the fourth-asset / quad-matrix expansion
  - issue one bounded correction slice limited to `oracle_signal_smoke_d` shaping and tests
  - keep the accepted triple matrix and the accepted `oracle_signal_smoke_b` / `200` blemish unchanged
- Acceptance status: held

## 2026-04-18 -- Broader-Evidence Planning Spike Review

- Reviewed the returned broader-evidence planning spike against repo reality, accepted control state, and current evidence boundaries
- Findings:
  - the strategic recommendation is sound:
    - the strongest remaining evidence gap is breadth across semantic shapes rather than more cleanup on the accepted `oracle_signal_smoke_b` / `200` blemish
    - the current accepted trio remains function-centric enough that one additional materially different asset would add genuinely new falsifiable evidence
  - the proposed execution prompt needed control-lane tightening before issue:
    - it did not require explicit comparisons for `ledger.jsonl`, `report.md`, and normalized `manifest.json`
    - it omitted repo-quality validation commands such as `ruff check`, `ruff format --check`, `mypy --strict`, and a broader regression pass
- Human sign-off:
  - Ryan explicitly approved advancing with a rewritten execution-ready prompt rather than issuing the worker's proposed prompt as-is
- Decision:
  - accept the planning-spike direction
  - issue one bounded fourth-asset / quad-matrix execution prompt with explicit determinism comparisons and repo-quality validation
  - keep the accepted triple matrix as the anchor and preserve the accepted `oracle_signal_smoke_b` / `200` blemish as documented current state
- Acceptance status: first-pass

## 2026-04-17 -- Ryan Accepts Bounded Smoke B `/200` Blemish For Broader Evidence Work

- Ryan explicitly accepted the single bounded `oracle_signal_smoke_b` / `200` `budget_pressure` blemish as sufficient for broader evidence work
- Accepted risk:
  - the current strongest accepted triple-matrix surface keeps one honest tight-budget limitation:
    - `oracle_signal_smoke_b` / `200` omits `def:pkg/digest.py:pkg.digest.render_assignment_digest`
    - support coverage remains `0.6666666666666666`
    - uncertainty honesty remains `1.0`
    - warnings remain `['budget_pressure']`
- Alternatives considered:
  - reopen one accepted boundary to chase a fully clean `6/6` surface
  - keep broader evidence work paused pending another cleanup attempt
- Reasoning:
  - control review verified that the exact oracle-clean 5-selector surface does not fit the current accepted `200` budget under the current accepted renderer/compiler contracts
  - accepting the bounded blemish preserves methodological discipline and avoids moving the goalposts just to eliminate one honest red cell
  - the next highest-signal move is to broaden evidence under the fixed accepted contracts rather than spending more cycles on optimizer-only cleanup that cannot succeed
- Decision:
  - broader evidence work is now authorized
  - public-claim and portfolio-claim work remain gated by `EVAL.md` and are not yet authorized by this decision alone
  - the next control action is to issue one bounded broader-evidence planning slice that keeps the accepted triple matrix and the accepted `smoke_b` `/200` blemish as documented current state
- Acceptance status: first-pass

## 2026-04-17 -- Smoke B `/200` Clean-Surface Feasibility Review

- An accidental extra execution lane returned a bounded `oracle_signal_smoke_b` / `200` feasibility write-up and also wrote non-authoritative continuity edits into `PLAN.md` and `BUILDLOG.md`
- Control lane discarded those continuity edits as non-authoritative, then independently verified the substantive feasibility claim against the current provider, optimizer, renderer, and compiler path:
  - the current selected row remains:
    - `def:main.py:main.run_signal_smoke_b` at `source`
    - `def:pkg/collector.py:pkg.collector.collect_signal_rows` at `source`
    - `def:pkg/labels.py:pkg.labels.build_priority_labels` at `summary`
    - `frontier:call:main.py:10:4` at `identity`
  - the only omitted required selector remains `def:pkg/digest.py:pkg.digest.render_assignment_digest`
  - a cheaper optimizer swap such as downgrading `pkg.collector.collect_signal_rows` to `summary` can fit `pkg.digest.render_assignment_digest`, but it does **not** clean the row because the oracle also requires `pkg.collector.collect_signal_rows` at `source`
  - the exact oracle-clean 5-selector surface under the current accepted render details compiles to `239` tokens
  - even a hypothetical zero-framing join of just the rendered unit contents is still `221` tokens
- Alternatives considered:
  - one more optimizer-only change in support ordering or source-promotion heuristics
  - summary/identity compaction without reopening source-render contracts
  - reopening accepted renderer, compiler-envelope, token-budget, or signal-asset boundaries
- Reasoning:
  - the first option cannot work because the required clean surface already exceeds the budget before any truthful optimizer-only packing choice can save it
  - the second option also cannot work within current accepted contracts because even removing compile framing entirely leaves the exact required rendered contents above budget
  - the only remaining paths to a fully clean row would reopen an accepted contract boundary, which requires Ryan's explicit scope authorization
- Control review accepts the feasibility finding as accurate
- Human decision required before any further execution:
  - recommendation is to accept the single bounded `oracle_signal_smoke_b` / `200` blemish and advance broader evidence work
  - if Ryan still requires a fully clean surface, he must explicitly authorize which accepted boundary may reopen: renderer/source-summary contract, compiler document envelope, token-budget methodology, or signal-asset/task budget
  - broader evidence expansion and public-claim work remain paused pending Ryan's explicit go/no-go
- Acceptance status: held

## 2026-04-17 -- Post-Noise-Tightening Triple-Matrix Evidence Review

- Ran the accepted `oracle_signal_triple_matrix.json` bundle path twice as a fresh control-lane spike over the accepted noise-tightened workspace state:
  - `/tmp/context_ir_post_noise_review_a`
  - `/tmp/context_ir_post_noise_review_b`
- Verified from the emitted artifacts and fresh control-lane inspection:
  - `ledger.jsonl` matched exactly across the two reruns
  - `report.md` matched exactly across the two reruns
  - raw `manifest.json` differed only in the caller-chosen `ledger_path` and `report_path`
  - `manifest.json` matched after normalizing only those caller-chosen artifact paths
  - all `18/18` rows remained budget-compliant and `budget_violation_run_ids` stayed empty
  - `context_ir` still wins all `6/6` task-budget rows
  - provider-average aggregate across the reviewed triple matrix remains led by:
    - `context_ir` `0.9786343641862341`
    - `lexical_top_k_files` `0.6269136127513334`
    - `import_neighborhood_files` `0.6262610465072885`
  - lexical baseline ordering remains unchanged overall and on each task-budget slot:
    - `lexical_top_k_files` still narrowly leads `import_neighborhood_files`
- The strengthened three-asset surface is now deterministic and mostly clean:
  - five `context_ir` rows are clean exact 5-unit winning surfaces with support coverage `1.0`, uncertainty honesty `1.0`, and warnings `[]`
  - `oracle_signal_smoke_b` / `200` remains the only residual blemish:
    - aggregate score `0.9096774193548387`
    - selected surface remains the accepted 4-unit floor
    - support coverage remains `0.6666666666666666`
    - uncertainty honesty remains `1.0`
    - warnings remain `['budget_pressure']`
    - omitted repository-backed support remains `def:pkg/digest.py:pkg.digest.render_assignment_digest`
- Alternatives considered:
  - accept the current reviewed surface and move directly into broader evidence work
  - authorize one more tightly scoped follow-up only for the residual `oracle_signal_smoke_b` / `200` row
  - pause at the quality gate and require Ryan to decide whether the single remaining blemish is acceptable
- Reasoning:
  - the evidence surface is now strong on determinism, row wins, aggregate lead, support coverage, and uncertainty honesty
  - but the remaining `oracle_signal_smoke_b` / `200` `budget_pressure` row is still a real blemish under the repo quality gate, even if it is bounded and honest
  - moving into broader evidence or public-claim work without Ryan's explicit decision would blur the difference between "mostly clean" and "clean enough for the next claim boundary"
- Control review accepts the spike as accurate
- Human decision required before any further execution:
  - recommendation is a narrow go/no-go: either explicitly accept the single bounded `oracle_signal_smoke_b` / `200` blemish for broader evidence work, or authorize one more tightly scoped follow-up only if a fully clean `6/6` reviewed surface is required
  - broader evidence expansion and public-claim work remain paused pending Ryan's explicit go/no-go
- Acceptance status: held

## 2026-04-17 -- Noise-Tightening Correction

- Reviewed the returned noise-tightening correction against repo reality and fresh control-lane inspection of the emitted `.tmp_exec_noise_tighten_a` and `.tmp_exec_noise_tighten_b` artifacts
- Updated:
  - `src/context_ir/semantic_optimizer.py`
  - `tests/test_eval_signal_smoke.py`
  - `tests/test_eval_signal_smoke_b.py`
  - `tests/test_eval_signal_smoke_c.py`
  - `tests/test_semantic_optimizer.py`
- Verified from fresh artifacts and targeted control-lane reruns:
  - `context_ir` still wins all `6/6` task-budget rows
  - provider-average aggregate across the corrected triple matrix is now:
    - `context_ir` `0.9786343641862341`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
  - the targeted surplus uncertainty is now removed from the reviewed winning rows:
    - `oracle_signal_smoke` / `200` and `/240` now both keep the exact required 5-unit surface with warnings `[]`
    - `oracle_signal_smoke_b` / `200` keeps the accepted 4-unit floor, no longer selects `frontier:call:pkg/collector.py:2:20`, and still honestly retains `budget_pressure`
    - `oracle_signal_smoke_b` / `240` keeps the clean 5-unit surface with warnings `[]`
    - `oracle_signal_smoke_c` / `200` and `/240` now both keep the exact required 5-unit surface with warnings `[]`
  - the accepted core-fix and helper-support-complete floors remain intact:
    - `oracle_signal_smoke` still includes `unsupported:import:main.py:2:0:1:*:_` at both budgets with uncertainty honesty `1.0`
    - `oracle_signal_smoke_b` still keeps support coverage `0.667` / `1.0` with uncertainty honesty `1.0`
    - `oracle_signal_smoke_c` still keeps support coverage `1.0` / `1.0` with uncertainty honesty `1.0`
  - across two independent noise-tightening triple-matrix runs:
    - `ledger.jsonl` matched exactly
    - `report.md` matched exactly
    - `manifest.json` matched after normalizing caller-chosen artifact paths and generation timestamp
- Control review found no issues
- Validation confirmed:
  - execution lane reported:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_signal_smoke.py tests/test_eval_signal_smoke_b.py tests/test_eval_signal_smoke_c.py tests/test_semantic_optimizer.py -v` with 33 passed
    - `PYTHONPATH=src .venv/bin/python -m ruff check src/ tests/`
    - `PYTHONPATH=src .venv/bin/python -m ruff format --check src/ tests/`
    - `PYTHONPATH=src .venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"` with 344 passed and 1 deselected
  - control reran `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_signal_smoke.py tests/test_eval_signal_smoke_b.py tests/test_eval_signal_smoke_c.py tests/test_semantic_optimizer.py -q` with 33 passed
- A fresh post-noise-tightening triple-matrix evidence review is next; broader evidence expansion and public-claim work remain deferred until that review is accepted
- Acceptance status: first-pass

## 2026-04-17 -- Post-Core-Correction Triple-Matrix Evidence Review

- Ran the accepted `oracle_signal_triple_matrix.json` bundle path twice first-pass as a post-core-correction spike over the accepted core-uncertainty-corrected workspace state
- Verified from emitted artifacts and fresh control-lane inspection:
  - `ledger.jsonl` matched exactly across the two reruns
  - `report.md` matched exactly across the two reruns
  - `manifest.json` matched after normalizing the caller-chosen `ledger_path` and `report_path`
  - all 18 records remained budget-compliant and `budget_violation_run_ids` stayed empty
  - `context_ir` still wins all `6/6` task-budget rows
  - provider-average aggregate across the accepted triple matrix is now led by:
    - `context_ir` `0.972`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
- The corrected three-asset surface is stronger but still not clean enough to treat as broader-evidence-ready:
  - the accepted core uncertainty miss is closed:
    - `oracle_signal_smoke` now reaches uncertainty honesty `1.0` at both budgets
    - `unsupported:import:main.py:2:0:1:*:_` is now selected at both budgets
  - the accepted helper-support-complete smoke_b and smoke_c rows remain intact
  - the remaining weakness is now surplus non-required uncertainty rather than correctness or determinism:
    - `oracle_signal_smoke` / `240` still adds `frontier:call:pkg/planner.py:2:20` and `unsupported:call:pkg/presenter.py:2:31`
    - `oracle_signal_smoke_b` / `200` still carries `budget_pressure`, omits `def:pkg/digest.py:pkg.digest.render_assignment_digest`, and adds `frontier:call:pkg/collector.py:2:20`
    - `oracle_signal_smoke_c` / `200` still adds `frontier:call:main.py:6:20`
    - `oracle_signal_smoke_c` / `240` still adds `frontier:call:main.py:6:20` and `frontier:call:pkg/registry.py:2:23`
- Reasoning:
  - the evidence surface is now strong on wins, aggregate, support coverage, and uncertainty honesty
  - but broader evidence expansion from this surface would overstate cleanliness because multiple winning rows still include surplus uncertainty material and one row still carries explicit budget pressure
- Control review accepts the spike as accurate
- Human decision required before any further execution:
  - recommendation is one narrower follow-up only, focused on noise-tightening surplus non-required uncertainty without reopening the accepted corrected evidence floors
  - broader evidence expansion and public-claim work remain paused pending Ryan's explicit go/no-go
- Human sign-off:
  - Ryan approved one narrower noise-tightening follow-up
  - the next control action is to issue one bounded correction slice focused on removing surplus non-required uncertainty from the reviewed winning rows without reopening accepted evidence floors or broadening scope
- Acceptance status: first-pass

## 2026-04-17 -- Core Uncertainty-Surfacing Correction

- Reviewed the returned core uncertainty-surfacing correction against repo reality and fresh control-lane inspection of the emitted `.tmp_exec_core_uncertainty_a` and `.tmp_exec_core_uncertainty_b` artifacts
- Updated:
  - `src/context_ir/semantic_optimizer.py`
  - `tests/test_eval_signal_smoke.py`
  - `tests/test_eval_signal_smoke_b.py`
  - `tests/test_eval_signal_smoke_c.py`
  - `tests/test_semantic_optimizer.py`
- Verified from fresh artifacts and targeted control-lane reruns:
  - `context_ir` still wins all `6/6` task-budget rows
  - provider-average aggregate across the corrected triple matrix is now:
    - `context_ir` `0.972`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
  - the persistent core uncertainty miss is now closed on `oracle_signal_smoke`:
    - at `200`, selected units now include `unsupported:import:main.py:2:0:1:*:_`
    - at `240`, selected units now include `unsupported:import:main.py:2:0:1:*:_`
    - both rows now keep support coverage `1.0`, uncertainty honesty `1.0`, and warnings `[]`
  - the accepted smoke_b and smoke_c helper-support surfaces remain intact:
    - `oracle_signal_smoke_b` / `200` stays at support coverage `0.667` with uncertainty honesty `1.0`
    - `oracle_signal_smoke_b` / `240` stays at support coverage `1.0` with uncertainty honesty `1.0`
    - `oracle_signal_smoke_c` / `200` stays at support coverage `1.0` with uncertainty honesty `1.0`
    - `oracle_signal_smoke_c` / `240` stays at support coverage `1.0` with uncertainty honesty `1.0`
  - across two independent core-uncertainty triple-matrix runs:
    - `ledger.jsonl` matched exactly
    - `report.md` matched exactly
    - `manifest.json` matched after normalizing caller-chosen artifact paths and generation timestamp
- Control review found no issues
- Validation confirmed:
  - execution lane reported:
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_signal_smoke.py tests/test_eval_signal_smoke_b.py tests/test_eval_signal_smoke_c.py tests/test_semantic_optimizer.py tests/test_semantic_compiler.py tests/test_semantic_renderer.py tests/test_semantic_diagnostics.py tests/test_tool_facade.py -v` with 68 passed
    - `PYTHONPATH=src .venv/bin/python -m ruff check src/ tests/`
    - `PYTHONPATH=src .venv/bin/python -m ruff format --check src/ tests/`
    - `PYTHONPATH=src .venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"` with 343 passed and 1 deselected
  - control reran `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_signal_smoke.py tests/test_eval_signal_smoke_b.py tests/test_eval_signal_smoke_c.py tests/test_semantic_optimizer.py -q` with 32 passed
- A fresh post-core-correction triple-matrix evidence review is next; broader evidence expansion and public-claim work remain deferred until that review is accepted
- Acceptance status: first-pass

## 2026-04-17 -- Post-Helper-Correction Triple-Matrix Evidence Review

- Ran the accepted `oracle_signal_triple_matrix.json` bundle path twice first-pass as a post-helper spike over the accepted helper-support-complete workspace state
- Verified from emitted artifacts and fresh control-lane reruns:
  - `ledger.jsonl` matched exactly across the two reruns
  - `report.md` matched exactly across the two reruns
  - `manifest.json` matched after normalizing the caller-chosen `ledger_path` and `report_path`
  - all 18 records remained budget-compliant and `budget_violation_run_ids` stayed empty
  - `context_ir` still wins all `6/6` task-budget rows
  - provider-average aggregate across the accepted triple matrix remains led by:
    - `context_ir` `0.948`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
- The three-asset surface is materially stronger but still mixed rather than uniformly strong:
  - the accepted helper-support correction closes the previously concrete helper-support misses on the reviewed surface
  - the strongest remaining weakness is now on `signal_core_baselines`:
    - at both budgets, support coverage remains `1.0`
    - but uncertainty honesty remains `0.625`
    - `omitted_expected_uncertainty_ids` still contains `unsupported:import:main.py:2:0:1:*:_`
  - a secondary tighter-budget weakness remains on `signal_digest_baselines` / `200`:
    - support coverage remains `0.667`
    - `budget_pressure` still reports omitted support `def:pkg/digest.py:pkg.digest.render_assignment_digest`
    - that row recovers at `240`
- Reasoning:
  - the main remaining blocker is now persistent uncertainty surfacing on the core asset
  - the digest miss looks secondary because it is confined to the tighter-budget row
- Control review accepts the spike as accurate
- Human sign-off:
  - Ryan approved one more bounded correction slice focused on the persistent omission of `unsupported:import:main.py:2:0:1:*:_` on `signal_core_baselines`, without reopening the accepted helper-support work
  - broader evidence expansion remains paused pending the result of that correction and a fresh evidence review
- Acceptance status: first-pass

## 2026-04-17 -- Remaining Helper-Support Budget-Pressure Correction

- Added one more bounded correction pass to close the last repository-backed helper-support gaps on the accepted triple matrix first-pass
- Updated:
  - `src/context_ir/semantic_optimizer.py`
  - `src/context_ir/semantic_compiler.py`
  - `src/context_ir/semantic_renderer.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_semantic_compiler.py`
  - `tests/test_semantic_renderer.py`
  - `tests/test_semantic_diagnostics.py`
  - `tests/test_tool_facade.py`
- Verified from the emitted `.tmp_exec_helper_fix_a` artifacts and fresh control-lane inspection:
  - `context_ir` still wins all `6/6` task-budget rows
  - provider-average aggregate across the corrected triple matrix is now:
    - `context_ir` `0.948`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
  - the remaining helper-support gaps are now closed:
    - `oracle_signal_smoke_b` / `200` includes `def:pkg/collector.py:pkg.collector.collect_signal_rows` and reaches support coverage `0.667` with uncertainty honesty `1.0`
    - `oracle_signal_smoke_b` / `240` includes `def:pkg/collector.py:pkg.collector.collect_signal_rows` and reaches support coverage `1.0` with uncertainty honesty `1.0`
    - `oracle_signal_smoke_c` / `200` includes `def:pkg/registry.py:pkg.registry.resolve_owner_alias` and reaches support coverage `1.0` with uncertainty honesty `1.0`
    - `oracle_signal_smoke_c` / `240` includes `def:pkg/registry.py:pkg.registry.resolve_owner_alias` and reaches support coverage `1.0` with uncertainty honesty `1.0`
  - the accepted original smoke surface remains intact:
    - `oracle_signal_smoke` / `200` and `/240` both keep support coverage `1.0`
    - uncertainty honesty remains `0.625`
    - no warnings were introduced on those rows
  - across two independent helper-fix triple-matrix runs:
    - `ledger.jsonl` matched exactly
    - `report.md` matched exactly
    - `manifest.json` matched after caller-path normalization
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_signal_smoke.py tests/test_eval_signal_smoke_b.py tests/test_eval_signal_smoke_c.py tests/test_semantic_optimizer.py tests/test_semantic_scorer.py tests/test_semantic_compiler.py tests/test_semantic_renderer.py tests/test_semantic_diagnostics.py tests/test_tool_facade.py -v` with 78 passed
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 342 passed and 1 deselected
- A fresh post-helper-correction triple-matrix evidence review is next; broader evidence expansion and public-claim work remain deferred until that review is accepted
- Acceptance status: first-pass

## 2026-04-17 -- Post-Support-Correction Triple-Matrix Evidence Review

- Ran the accepted `oracle_signal_triple_matrix.json` bundle path twice first-pass as a post-support spike over the accepted smoke_b support-improved workspace state
- Verified from emitted artifacts and fresh control-lane reruns:
  - `ledger.jsonl` matched exactly across the two reruns
  - `report.md` matched exactly across the two reruns
  - `manifest.json` matched after normalizing the caller-chosen `ledger_path` and `report_path`
  - all 18 records remained budget-compliant and `budget_violation_run_ids` stayed empty
  - `context_ir` still wins all `6/6` task-budget rows
  - provider-average aggregate across the accepted triple matrix is now led by:
    - `context_ir` `0.882`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
- The strengthened three-asset surface is stronger than materially weak but still mixed rather than uniformly strong:
  - `oracle_signal_smoke` now looks strong on support at both budgets, with support coverage `1.0` and no warnings
  - `oracle_signal_smoke_b` is still not clean:
    - at `200`, support coverage remains `0.333`
    - at `240`, support coverage reaches `0.667`, but `budget_pressure` still reports missing repository-backed support for `def:pkg/collector.py:pkg.collector.collect_signal_rows`
  - `oracle_signal_smoke_c` is also still not clean:
    - support coverage remains `0.667` at both budgets
    - `budget_pressure` still reports missing repository-backed support for `def:pkg/registry.py:pkg.registry.resolve_owner_alias`
- Reasoning:
  - the remaining bounded weakness is primarily support selection under budget pressure
  - it is not primarily uncertainty handling, because the two tightened assets now retain uncertainty honesty `1.0`
- Control review accepts the spike as accurate
- Human sign-off:
  - Ryan approved one more bounded correction slice focused on the remaining helper-support gap under budget pressure without reopening eval semantics or accepted signal assets
  - broader evidence expansion remains paused pending the result of that correction and a fresh evidence review
- Acceptance status: first-pass

## 2026-04-17 -- Smoke B Support-Selection Budget-Pressure Correction Review

- Reviewed the returned smoke_b support-selection correction against repo reality and fresh control-lane inspection of the emitted `.tmp_exec_support_fix_a` artifacts
- Verified from fresh artifacts and reported validations:
  - `context_ir` still wins all `6/6` task-budget rows
  - provider-average aggregate rises to:
    - `context_ir` `0.882`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
  - the targeted smoke_b weakness is materially improved:
    - at `oracle_signal_smoke_b` / `200`, support coverage rises from `0.0` to `0.333` with uncertainty honesty `1.0`
    - at `oracle_signal_smoke_b` / `240`, support coverage rises from `0.333` to `0.667` with uncertainty honesty `1.0`
  - the accepted widened smoke_c floors remain satisfied:
    - `oracle_signal_smoke_c` / `200` now reaches support coverage `0.667` with uncertainty honesty `1.0`
    - `oracle_signal_smoke_c` / `240` remains at support coverage `0.667` with uncertainty honesty `1.0`
- Review found one issue before human gate:
  - it also reopens the already accepted original `oracle_signal_smoke` / `200` surface without a findings-based reason
  - the fresh report now moves that row from the previously accepted support coverage `0.5` to support coverage `1.0`
  - the test contract was relaxed to allow this drift by changing the original smoke `/200` expectation from exact equality to a minimum floor in:
    - `tests/test_eval_signal_smoke.py`
    - `tests/test_eval_signal_smoke_b.py`
    - `tests/test_eval_signal_smoke_c.py`
- Reasoning:
  - the slice was authorized to correct the remaining smoke_b support-selection weakness while preserving accepted smoke_c gains
  - it was not backed by a findings-based authorization to reopen the accepted original smoke competitive-recovery surface or its tight-budget tradeoff
  - under repo workflow, that required a human quality-gate decision rather than silent acceptance, even though the reopened row improved numerically
- Control review found no separate correctness, type-safety, determinism, or validation risk in the returned code; the only issue was scope reopening
- Human sign-off:
  - Ryan approved accepting this broader improvement as a one-off, provided there was no actual code risk
  - control review confirms the issue was scope creep rather than a concrete code-risk finding
- Next control action:
  - accept the slice in workspace
  - resync continuity
  - run a fresh triple-matrix evidence review before authorizing broader evidence work
- Acceptance status: accepted with human sign-off

## 2026-04-17 -- Post-Correction Triple-Matrix Evidence Review

- Ran the accepted `oracle_signal_triple_matrix.json` bundle path twice first-pass as a post-correction spike over the widened-correction workspace state
- Verified from emitted artifacts and fresh control-lane reruns:
  - `ledger.jsonl` matched exactly across the two reruns
  - `report.md` matched exactly across the two reruns
  - `manifest.json` matched after normalizing the caller-chosen `ledger_path` and `report_path`
  - all 18 records remained budget-compliant and `budget_violation_run_ids` stayed empty
  - `context_ir` still wins all `6/6` task-budget rows
  - provider-average aggregate across the accepted triple matrix remains led by:
    - `context_ir` `0.809`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
- The corrected three-asset surface is materially stronger but still mixed rather than uniformly strong:
  - the weakest remaining area is now `oracle_signal_smoke_b` support selection under budget pressure
  - at `oracle_signal_smoke_b` / `200`, `context_ir` still selects no repository-backed support units and remains at support coverage `0.0`
  - at `oracle_signal_smoke_b` / `240`, `context_ir` reaches only support coverage `0.333`
  - `oracle_signal_smoke_c` is now materially improved, but still retains bounded support gaps:
    - at `200`, it still omits `def:pkg/registry.py:pkg.registry.resolve_owner_alias` and `def:pkg/summary.py:pkg.summary.render_route_summary`
    - at `240`, it still omits `def:pkg/registry.py:pkg.registry.resolve_owner_alias`
    - both smoke_c rows still carry `budget_pressure`, and both still carry an `omitted_uncertainty` warning for `frontier:call:main.py:6:20`
- Reasoning:
  - the remaining bounded weakness is primarily support selection under budget pressure
  - it is not primarily uncertainty handling, because `oracle_signal_smoke_b` and `oracle_signal_smoke_c` now retain uncertainty honesty `1.0` on the corrected rows
- Control review accepts the spike as accurate
- Human sign-off:
  - Ryan approved one bounded correction slice focused on remaining support-selection-under-budget-pressure weakness without reopening eval semantics or accepted signal assets
  - broader evidence expansion remains paused pending the result of that correction and a fresh evidence review
- Acceptance status: first-pass

## 2026-04-17 -- Smoke C 240 Budget-Envelope Widened Correction

- Added a widened correction pass to resolve the documented smoke_c `/240` budget-envelope blocker first-pass
- Updated:
  - `src/context_ir/semantic_optimizer.py`
  - `src/context_ir/semantic_renderer.py`
  - `tests/test_eval_signal_smoke_b.py`
  - `tests/test_eval_signal_smoke_c.py`
  - `tests/test_semantic_compiler.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_semantic_renderer.py`
- The widened correction preserved eval semantics and signal assets while reducing identity-frontier render cost and refining focus packing so one honest uncertainty surface is selected before support widens further
- Verified through the accepted `oracle_signal_triple_matrix.json` bundle path and fresh control-lane reruns:
  - `context_ir` still wins all `6/6` task-budget rows
  - provider-average aggregate across the corrected triple matrix is now:
    - `context_ir` `0.809`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
  - `oracle_signal_smoke_b` / `200` is restored to the previously accepted evidence surface:
    - selected units include `def:main.py:main.run_signal_smoke_b`
    - selected units include `frontier:call:main.py:10:4`
    - support coverage `0.0`
    - uncertainty honesty `1.0`
  - `oracle_signal_smoke_c` / `200` now reaches:
    - selected units include `def:main.py:main.run_signal_smoke_c`
    - selected units include `frontier:call:pkg/router.py:7:4`
    - support coverage `0.333`
    - uncertainty honesty `1.0`
    - budget-compliant at `196/200`
  - `oracle_signal_smoke_c` / `240` now reaches:
    - selected units include `def:main.py:main.run_signal_smoke_c`
    - selected units include `frontier:call:pkg/router.py:7:4`
    - selected units include `def:pkg/summary.py:pkg.summary.render_route_summary`
    - support coverage `0.667`
    - uncertainty honesty `1.0`
    - budget-compliant at `237/240`
  - smoke_c still omits `def:pkg/registry.py:pkg.registry.resolve_owner_alias` under the tightened envelope, but the row now satisfies the accepted widened slice contract without changing eval semantics
  - across two independent widened triple-matrix runs:
    - `ledger.jsonl` matched exactly
    - `report.md` matched exactly
    - `manifest.json` matched after caller-path normalization
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_signal_smoke_c.py tests/test_eval_signal_smoke_b.py tests/test_semantic_optimizer.py tests/test_semantic_compiler.py tests/test_semantic_diagnostics.py tests/test_tool_facade.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 341 passed and 1 deselected
- A fresh post-correction triple-matrix evidence review is next; broader evidence expansion and public-claim work remain deferred
- Acceptance status: first-pass

## 2026-04-17 -- Smoke C Uncertainty-Restoration Correction Escalation

- Reviewed the returned `ESCALATE` result against repo reality and reproduced the feasibility boundary in the current workspace
- No repo files changed in the execution lane; the returned result was a constraint analysis, not an implementation
- Verified blocker:
  - under the current compile envelope and unchanged eval semantics, `oracle_signal_smoke_c` / `240` cannot satisfy both:
    - support coverage above `0.333` (that is, two adequate support selectors)
    - uncertainty honesty `1.0` for the expected frontier surface
  - fresh control-lane probes over adequate smoke_c selector combinations produced compile sizes above the `240` budget:
    - `run_signal_smoke_c` + frontier + `build_handoff_route` + `resolve_owner_alias` -> `283`
    - `run_signal_smoke_c` + frontier + `build_handoff_route` + `render_route_summary` -> `257`
    - `run_signal_smoke_c` + frontier + `resolve_owner_alias` + `render_route_summary` -> `257`
- Verified feasible restoration surfaces:
  - `oracle_signal_smoke_b` / `200` accepted surface remains feasible:
    - `run_signal_smoke_b` + frontier compiles at `156`
  - `oracle_signal_smoke_c` / `200` target surface remains feasible:
    - `run_signal_smoke_c` + `render_route_summary` + frontier compiles at `190`
- Reasoning:
  - the remaining blocker is not ranking alone
  - it is a scope/constraint conflict between the current `240` budget, the current compile/document envelope, and the unchanged eval requirement for full uncertainty credit on smoke_c
- Control review accepts the escalation as accurate
- Human decision required before any further execution:
  - widen scope to allow compile-envelope reduction or another broader change
  - revise the smoke_c `/240` requirement
  - or narrow the correction target to the feasible smoke_b `/200` and smoke_c `/200` restorations only
- Human sign-off:
  - Ryan chose the widened-scope path
  - next control action is to issue one widened correction slice that may reduce compile/document overhead or otherwise change what fits at `240`, while keeping eval semantics unchanged
- Broader evidence expansion remains paused
- Acceptance status: held

## 2026-04-17 -- Smoke C Budget-Envelope Correction Review

- Reviewed the returned bounded `oracle_signal_smoke_c` correction against repo reality and fresh control-lane reruns
- Verified from fresh corrected triple-matrix artifacts:
  - `context_ir` still wins all `6/6` task-budget rows
  - provider-average aggregate rises to `0.791`
  - `oracle_signal_smoke_c` now materially improves on the targeted retrieval weakness:
    - at `200`, `context_ir` now selects `def:main.py:main.run_signal_smoke_c` with edit coverage `1.0`
    - at `240`, `context_ir` reaches support coverage `0.667`
- Review found two issues, so the slice is not accepted:
  - the new packing path restores smoke_c edit/support by dropping the selected uncertainty surface to omitted-warning credit, reducing smoke_c uncertainty honesty from the previously accepted `1.0` to `0.5`
  - the generic optimizer change also reopens the already accepted `oracle_signal_smoke_b` / `200` row, changing it from support `0.0` with uncertainty honesty `1.0` to support `0.333` with uncertainty honesty `0.5`
- Reasoning:
  - the smoke_c retrieval improvement is real
  - but the fix currently pays for that gain by weakening an accepted frontier-honesty surface and by changing an unrelated accepted evidence row
  - under the repo workflow, that requires a correction pass rather than silent acceptance
- Human sign-off:
  - Ryan gave explicit go to draft a narrow correction prompt
  - the next control action is a bounded correction that preserves the smoke_c edit/support gains, restores smoke_c uncertainty honesty to the prior `1.0` surface, and avoids the smoke_b reopening
- Acceptance status: held

## 2026-04-17 -- Post-Recovery Triple-Matrix Evidence Review

- Ran the accepted `oracle_signal_triple_matrix.json` through the accepted bundle path first-pass as a post-recovery spike
- Verified from deterministic bundle artifacts and fresh control-lane reruns:
  - `context_ir` still wins all `6/6` task-budget rows
  - provider aggregates across the corrected triple matrix are:
    - `context_ir` `0.757`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
- The corrected three-asset surface is stronger but not yet clean:
  - at `oracle_signal_smoke_c` / `200`, `context_ir` still omits `main.run_signal_smoke_c`
  - that row still carries edit coverage `0.0`, support coverage `0.667`, representation adequacy `1.0`, and uncertainty honesty `1.0`
  - selected units there are:
    - `def:pkg/router.py:pkg.router.build_handoff_route`
    - `frontier:call:pkg/router.py:7:4`
    - `def:pkg/summary.py:pkg.summary.render_route_summary`
  - at `oracle_signal_smoke_c` / `240`, `context_ir` recovers `main.run_signal_smoke_c` and wins the row with aggregate score `0.801`
  - that row still carries support coverage `0.333`
  - it still omits:
    - `def:pkg/registry.py:pkg.registry.resolve_owner_alias`
    - `def:pkg/summary.py:pkg.summary.render_route_summary`
  - two `budget_pressure` warnings remain at `oracle_signal_smoke_c` / `240`
- Determinism held across independent corrected triple-matrix runs:
  - `ledger.jsonl` matched exactly
  - `report.md` matched exactly
  - `manifest.json` matched after caller-path normalization
- Alternatives considered:
  - broaden evidence immediately from the corrected triple-matrix lead
  - run one more bounded correction on `oracle_signal_smoke_c`
- Reasoning:
  - the corrected matrix lead is real, but the accepted artifacts still show one zero-edit row and one support-thin row on the newest asset
  - broadening evidence now would compound a known weakness instead of clarifying it
- Control review accepted the spike output as accurate
- Remaining product issue for human review:
  - `oracle_signal_smoke_c` remains mixed after recovery and is still the limiting evidence surface
  - the remaining weakness now looks like tight-budget selection quality, with an edit miss at `200` and thin support at `240`, not a determinism or frontier-honesty problem
- Control decision pending human go/no-go:
  - broader evidence expansion remains paused
  - recommendation is one more bounded `oracle_signal_smoke_c` correction before any broader evidence-building or public-claim work
- Human sign-off:
  - Ryan gave explicit go to proceed with one more bounded `oracle_signal_smoke_c` correction
  - next control action is to issue that bounded execution prompt; broader evidence expansion remains paused
- Acceptance status: first-pass

## 2026-04-17 -- Signal Smoke C Edit-Target Recovery

- Added a narrow semantic recovery pass for the real `oracle_signal_smoke_c` / `240` miss first-pass
- Updated:
  - `src/context_ir/semantic_optimizer.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_eval_signal_smoke_c.py`
- The correction stayed within the semantic optimizer and did not reopen eval metrics, providers, oracle assets, run specs, or reporting contracts
- The optimizer now keeps a direct caller with material edit signal in the post-anchor pack before widening into helper-only support
- Verified through the accepted `oracle_signal_triple_matrix.json` bundle path:
  - `context_ir` now wins all `6/6` task-budget rows
  - at `oracle_signal_smoke_c` / `240`, `context_ir` reaches:
    - aggregate score `0.801`
    - edit coverage `1.0`
    - support coverage `0.333`
    - representation adequacy `1.0`
    - uncertainty honesty `1.0`
  - selected units at `oracle_signal_smoke_c` / `240` now include:
    - `def:pkg/router.py:pkg.router.build_handoff_route`
    - `def:main.py:main.run_signal_smoke_c`
    - `frontier:call:pkg/router.py:7:4`
  - `oracle_signal_smoke_c` / `200` remains budget-compliant and honest with non-zero support and uncertainty coverage
  - provider-average aggregate across the corrected triple matrix is now:
    - `context_ir` `0.757`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
  - across two independent triple-matrix runs:
    - `ledger.jsonl` matched exactly
    - `report.md` matched exactly
    - `manifest.json` matched after caller-path normalization
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_signal_smoke*.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 340 passed and 1 deselected
- A fresh corrected triple-matrix evidence review is next; broader evidence expansion and public-claim work remain deferred
- Acceptance status: first-pass

## 2026-04-17 -- Three-Asset Signal Evidence Review

- Ran the accepted `oracle_signal_triple_matrix.json` through the accepted bundle path first-pass as a spike
- Verified from deterministic bundle artifacts:
  - `context_ir` wins `5/6` task-budget rows
  - provider aggregates across the triple matrix are:
    - `context_ir` `0.713`
    - `lexical_top_k_files` `0.627`
    - `import_neighborhood_files` `0.626`
- The strongest remaining issue is `oracle_signal_smoke_c` at budget `240`:
  - `context_ir` omits `main.run_signal_smoke_c`
  - `context_ir` still carries support coverage `0.667`, representation adequacy `1.0`, and uncertainty honesty `1.0`
  - both file baselines recover the explicit edit target under the same budget
- The observed `oracle_signal_smoke_c` failure pattern looks most like an edit-target ranking/selection miss, not a representation collapse or uncertainty-only issue
- Determinism held across independent triple-matrix runs:
  - `ledger.jsonl` matched exactly
  - `report.md` matched exactly
  - `manifest.json` matched after caller-path normalization
- Control decision after human go:
  - broader evidence expansion is paused
  - the next slice should be a targeted semantic correction for `oracle_signal_smoke_c`
- Acceptance status: first-pass

## 2026-04-17 -- Third Methodology-Tightened Signal Asset And Three-Asset Matrix

- Added a third methodology-tightened signal asset and a deterministic three-asset matrix first-pass
- Added:
  - `evals/fixtures/oracle_signal_smoke_c/main.py`
  - `evals/fixtures/oracle_signal_smoke_c/pkg/__init__.py`
  - `evals/fixtures/oracle_signal_smoke_c/pkg/router.py`
  - `evals/fixtures/oracle_signal_smoke_c/pkg/registry.py`
  - `evals/fixtures/oracle_signal_smoke_c/pkg/summary.py`
  - `evals/tasks/oracle_signal_smoke_c.json`
  - `evals/run_specs/oracle_signal_smoke_c_matrix.json`
  - `evals/run_specs/oracle_signal_triple_matrix.json`
  - `tests/test_eval_signal_smoke_c.py`
- The new asset stays on the accepted selector-based oracle, run-spec, and bundle path while probing a different semantic retrieval pattern than both existing signal assets
- The new asset uses:
  - an edit locus in `main.py`
  - an upstream alias-resolution support path in `pkg/registry.py`
  - a downstream route-summary support path in `pkg/summary.py`
  - an unresolved routing-note uncertainty surface in `pkg/router.py`
- The new triple matrix runs:
  - `oracle_signal_smoke`
  - `oracle_signal_smoke_b`
  - `oracle_signal_smoke_c`
- Focused tests cover:
  - selector determinism
  - single-asset and triple-matrix run-spec loading
  - single-asset and triple-matrix bundle execution
  - cross-run determinism
  - tight-budget anti-saturation for the new asset
  - internal-only surfaces
  - explicit 18-record triple-matrix production
- No production semantic, provider, metric, or reporting code changed in this slice
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_signal_smoke*.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 338 passed and 1 deselected
- The accepted bundle path also produced a live 18-record triple-matrix bundle with 6 records per task
- Three-asset evidence review is next; public-claim work remains deferred
- Acceptance status: first-pass

## 2026-04-17 -- Signal Smoke B Semantic Recovery

- Added a narrow semantic recovery pass for `oracle_signal_smoke_b` first-pass
- Updated:
  - `src/context_ir/semantic_scorer.py`
  - `src/context_ir/semantic_optimizer.py`
  - `src/context_ir/semantic_compiler.py`
  - `tests/test_eval_signal_smoke_b.py`
  - `tests/test_semantic_scorer.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_semantic_compiler.py`
  - `tests/test_semantic_diagnostics.py`
  - `tests/test_tool_facade.py`
- The recovery stayed within the semantic layer and did not reopen eval metrics, providers, oracle assets, run specs, or reporting contracts
- The scorer now boosts orchestrating edit loci when multiple relevant downstream units align with the query
- The optimizer now repacks after securing the edit anchor, preserves scoped uncertainty, and promotes richer detail when it is no more expensive than the leaner alternative
- The compiler keeps the larger fitting pack under the final budget and trims document-body bookkeeping overhead while preserving structured omitted IDs, warning metadata, and budget totals
- Verified through the accepted `oracle_signal_pair_matrix.json` bundle path:
  - `context_ir` still wins both `oracle_signal_smoke` rows with support coverage `0.5` at budget `200` and `1.0` at budget `240`
  - `context_ir` now materially recovers on `oracle_signal_smoke_b`
  - at budget `200`, `context_ir` reaches aggregate score `0.715`, edit coverage `1.0`, representation adequacy `1.0`, and uncertainty honesty `1.0`
  - at budget `240`, `context_ir` reaches aggregate score `0.801`, edit coverage `1.0`, support coverage `0.333`, representation adequacy `1.0`, and uncertainty honesty `1.0`
  - provider-average aggregate across the pair matrix is now:
    - `context_ir` `0.803`
    - `lexical_top_k_files` `0.666`
    - `import_neighborhood_files` `0.665`
  - across two independent pair-matrix runs:
    - `ledger.jsonl` matched exactly
    - `report.md` matched exactly
    - `manifest.json` matched after caller-path normalization
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_signal_smoke*.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 332 passed and 1 deselected
- Broader evidence-building beyond the accepted two-asset pair is next; public-claim work remains deferred
- Acceptance status: first-pass

## 2026-04-17 -- Two-Asset Signal Evidence Review

- Ran the accepted `oracle_signal_pair_matrix.json` through the accepted bundle path first-pass as a spike
- Verified from deterministic bundle artifacts:
  - `context_ir` wins both `oracle_signal_smoke` rows
  - `context_ir` fails both `oracle_signal_smoke_b` rows
  - provider aggregates across the pair matrix are:
    - `lexical_top_k_files` `0.666`
    - `import_neighborhood_files` `0.665`
    - `context_ir` `0.442`
- For `oracle_signal_smoke_b`, the observed failure pattern is:
  - selected edit-path and collector units remain too shallow
  - support units are omitted at both budgets
  - uncertainty visibility improves at `240`, but edit/support/representation remain at `0.0`
- Determinism held across independent pair-matrix runs:
  - `ledger.jsonl` matched exactly
  - `report.md` matched exactly
  - `manifest.json` matched after caller-path normalization
- Control decision after human go:
  - broader evidence expansion is paused
  - the next slice should be a targeted semantic correction for `oracle_signal_smoke_b`
- Acceptance status: first-pass

## 2026-04-17 -- Second Methodology-Tightened Signal Asset And Two-Asset Matrix

- Added a second methodology-tightened signal asset and a deterministic two-asset matrix first-pass
- Added:
  - `evals/fixtures/oracle_signal_smoke_b/main.py`
  - `evals/fixtures/oracle_signal_smoke_b/pkg/__init__.py`
  - `evals/fixtures/oracle_signal_smoke_b/pkg/collector.py`
  - `evals/fixtures/oracle_signal_smoke_b/pkg/digest.py`
  - `evals/fixtures/oracle_signal_smoke_b/pkg/labels.py`
  - `evals/tasks/oracle_signal_smoke_b.json`
  - `evals/run_specs/oracle_signal_smoke_b_matrix.json`
  - `evals/run_specs/oracle_signal_pair_matrix.json`
  - `tests/test_eval_signal_smoke_b.py`
- The new asset stays on the accepted selector-based oracle, run-spec, and bundle path while probing a different semantic retrieval pattern than `oracle_signal_smoke`
- The new asset uses a four-file edit/support layout and an unresolved-attribute frontier, rather than the earlier star-import shape
- The new pair matrix runs:
  - `oracle_signal_smoke`
  - `oracle_signal_smoke_b`
- Focused tests cover:
  - selector determinism
  - single-asset and pair-matrix run-spec loading
  - single-asset and pair-matrix bundle execution
  - cross-run determinism
  - tight-budget anti-saturation for the new asset
  - internal-only surfaces
  - explicit 12-record pair-matrix production
- No production code changed in this slice
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_signal_smoke*.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 329 passed and 1 deselected
- Multi-asset evidence review remains next; public-claim work remains deferred
- Acceptance status: first-pass

## 2026-04-17 -- Signal Smoke Competitive Recovery

- Added a competitive recovery pass for `context_ir` on the accepted signal smoke first-pass
- Updated:
  - `src/context_ir/semantic_optimizer.py`
  - `src/context_ir/semantic_compiler.py`
  - `tests/test_eval_signal_smoke.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_semantic_compiler.py`
  - `tests/test_semantic_diagnostics.py`
- The optimizer now promotes richer detail when it is actually cheaper than a leaner render and the signal is material, which improves support-unit packing without dishonest task-specific branching
- Selection reasons were updated so such promotions are described as cost-aware promotions instead of budget downgrades
- The compiled semantic document no longer emits omitted-unit preview IDs in the text body; omitted counts remain in the document and full omitted IDs remain in structured outputs
- Verified through the accepted `oracle_signal_smoke` bundle path:
  - at budget `200`, `context_ir` now reaches aggregate score `0.718`, support coverage `0.5`, and a non-empty compiled pack
  - at budget `240`, `context_ir` now reaches aggregate score `0.844` and support coverage `1.0`
  - at both budgets, `context_ir` no longer materially trails the baselines and is the winning provider on aggregate score
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_signal_smoke.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 323 passed and 1 deselected
- Single-asset success is not yet sufficient for public claims; broader evidence generation remains next
- Acceptance status: first-pass

## 2026-04-17 -- Signal Smoke Context IR Recovery

- Added a first semantic recovery pass for the real `context_ir` miss on the accepted signal smoke first-pass
- Updated:
  - `src/context_ir/semantic_scorer.py`
  - `src/context_ir/semantic_optimizer.py`
  - `src/context_ir/semantic_compiler.py`
  - `tests/test_eval_signal_smoke.py`
  - `tests/test_semantic_scorer.py`
  - `tests/test_semantic_optimizer.py`
  - `tests/test_semantic_compiler.py`
  - `tests/test_semantic_diagnostics.py`
- The recovery stayed on the semantic path only and did not reopen eval metrics, providers, oracle assets, or reporting contracts
- The scorer now adds body-local query signal for scope-defining symbols so behavioral edit queries can lift the owning function without task-specific branching
- The optimizer now ranks by strongest relevance and can promote near-cost source detail for directly relevant symbols while staying conservative for support-only units
- The compiler now searches for the largest fitting semantic pack under the final document budget instead of collapsing to an empty pack after an over-tight envelope adjustment
- Verified through the accepted `oracle_signal_smoke` bundle path:
  - at budget `200`, `context_ir` now selects `def:main.py:main.run_signal_smoke`
  - at budget `200`, edit coverage is non-zero and the compiled semantic pack is not empty
  - at budget `240`, `context_ir` selects `def:main.py:main.run_signal_smoke` and `def:pkg/planner.py:pkg.planner.build_execution_plan`
  - at budget `240`, support coverage is non-zero
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_signal_smoke.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 321 passed and 1 deselected
- Broader evidence generation and public-claim work remain deferred; any further implementation should stay narrow and ranking-quality focused
- Acceptance status: first-pass

## 2026-04-17 -- Methodology-Tightened Signal Smoke Eval Assets

- Added methodology-tightened signal smoke assets first-pass
- Added:
  - `evals/fixtures/oracle_signal_smoke/main.py`
  - `evals/fixtures/oracle_signal_smoke/pkg/__init__.py`
  - `evals/fixtures/oracle_signal_smoke/pkg/planner.py`
  - `evals/fixtures/oracle_signal_smoke/pkg/presenter.py`
  - `evals/tasks/oracle_signal_smoke.json`
  - `evals/run_specs/oracle_signal_smoke_matrix.json`
  - `tests/test_eval_signal_smoke.py`
- The new signal smoke stays on the accepted selector-based oracle, run-spec, and bundle path while creating a real tight-budget tradeoff for whole-file baselines
- At budget `200`, both whole-file baselines select `main.py` and `pkg/planner.py` but omit `pkg/presenter.py`, so full relevant-file coverage is no longer available by construction
- The accepted `oracle_smoke` assets remain available as plumbing smoke; the new signal smoke is the stronger near-term diagnostic asset
- No production compiler, provider, or metric code changed in this slice
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_signal_smoke.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 317 passed and 1 deselected
- Narrow scorer / optimizer / compile correction work remains next; broader evidence generation and public-claim work remain deferred
- Acceptance status: first-pass

## 2026-04-16 -- Deterministic Internal Eval Bundle Directory

- Added deterministic internal eval bundle-directory orchestration first-pass
- Added `src/context_ir/eval_bundle.py` with:
  - frozen `EvalBundlePaths`
  - frozen `EvalBundleArtifact`
  - `execute_eval_bundle(...) -> EvalBundleArtifact`
- The bundle layer derives deterministic internal filenames:
  - `ledger.jsonl`
  - `report.md`
  - `manifest.json`
- The bundle layer composes accepted pipeline and manifest behavior so one execution's ledger, report, and manifest can be persisted and routed as one internal bundle without reopening lower-layer contracts
- Added `tests/test_eval_bundle.py` covering:
  - nested caller-provided bundle directories
  - deterministic internal filenames
  - path alignment across bundle paths, pipeline artifact, and manifest
  - manifest JSON round-tripping from disk
  - independent smoke-bundle equivalence apart from caller-specific absolute paths
  - internal-only surface boundaries
  - non-mutation of returned pipeline and manifest artifacts after follow-up reads
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_bundle.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 311 passed and 1 deselected
- Bundle indexing, public-claim gating, CLI, docs updates, and release work remain deferred
- Acceptance status: first-pass

## 2026-04-16 -- Deterministic Internal Eval Run Manifest

- Added deterministic internal eval run manifest composition first-pass
- Added `src/context_ir/eval_manifest.py` with:
  - frozen `EvalManifestCaseCount`
  - frozen `EvalRunManifest`
  - `build_eval_run_manifest(spec_path, pipeline_artifact) -> EvalRunManifest`
  - `eval_run_manifest_to_json(manifest) -> dict[str, object]`
  - `write_eval_run_manifest_json(manifest, output_path) -> Path`
- The manifest layer composes accepted pipeline outputs into a narrow JSON-safe artifact without re-running lower layers and without embedding raw ledger contents or full report Markdown
- Added `tests/test_eval_manifest.py` covering:
  - typed manifest creation from a smoke pipeline artifact
  - truthful mirroring of nested execution and summary fields
  - nested manifest writing and JSON round-trip
  - equivalence across independent smoke pipelines apart from caller-specific artifact paths
  - internal-only scope boundaries and non-mutation of the provided pipeline artifact
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_manifest.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 306 passed and 1 deselected
- Bundle-directory conventions, public-claim gating, CLI, docs updates, and release work remain deferred
- Acceptance status: first-pass

## 2026-04-16 -- Deterministic Internal Eval Pipeline Composition

- Added deterministic internal eval pipeline composition after 1 correction
- Added `src/context_ir/eval_pipeline.py` with:
  - frozen `EvalPipelineArtifact`
  - `execute_eval_pipeline(...) -> EvalPipelineArtifact`
- The pipeline composes the accepted run-spec execution flow and accepted report-artifact flow without changing lower-layer oracle, provider, metric, raw-record, summary, or report-artifact contracts
- Added `tests/test_eval_pipeline.py` covering:
  - end-to-end smoke execution into caller-provided ledger and report paths
  - honest nested path alignment across execution result, report artifact, and written report path
  - exact UTF-8 Markdown bytes on disk
  - deterministic independent runs
  - post-read immutability and internal-only scope boundaries
- Control review initially found one correctness defect:
  - nested report output paths failed with `FileNotFoundError` because report-parent directories were not prepared before writing
- Correction pass updated the internal report writer to create parent directories before writing exact Markdown bytes and tightened pipeline regression coverage to use distinct nested caller paths
- Validation confirmed after correction:
  - `.venv/bin/python -m pytest tests/test_eval_pipeline.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 301 passed and 1 deselected
- Durable run manifests, public-claim gating, CLI, docs updates, and release work remain deferred
- Acceptance status: 1 correction

## 2026-04-16 -- Deterministic Internal Eval Report Artifact

- Added deterministic internal eval report composition first-pass
- Added `src/context_ir/eval_report.py` with:
  - frozen `EvalReportArtifact`
  - `build_eval_report(ledger_path) -> EvalReportArtifact`
  - `write_eval_report_markdown(report, output_path) -> Path`
- The report artifact composes the accepted raw-ledger loader, accepted summary builder, and accepted Markdown renderer without changing lower-layer semantics
- Added `tests/test_eval_report.py` covering:
  - smoke-ledger artifact creation through the accepted runner
  - exact Markdown writing to a caller-provided output path
  - deterministic independent report builds
  - non-mutation of the typed report artifact during write
  - internal-only scope boundaries with no package-root or public-claim creep
- Validation confirmed:
  - `.venv/bin/python -m pytest tests/test_eval_report.py -v`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 297 passed and 1 deselected
- Multi-run pipeline composition, public-claim gating, CLI, docs updates, and release work remain deferred
- Acceptance status: first-pass

## 2026-04-16 -- Deterministic Ledger Summary Rendering

- Added deterministic internal eval ledger summary rendering after 1 correction
- Added `src/context_ir/eval_summary.py` with:
  - strict raw JSONL ledger loading into typed immutable records
  - deterministic provider aggregate rollups
  - deterministic per-`task_id` plus `budget` provider comparison rows
  - deterministic Markdown rendering for overview, provider aggregates, task-budget results, and optional budget violations
- Added `tests/test_eval_summary.py` covering:
  - valid smoke-ledger loading through the accepted runner
  - malformed JSON, blank-line, duplicate-`run_id`, and missing-field rejection
  - deterministic provider aggregate ordering and nullable-metric averaging
  - deterministic task-budget ordering and exact tie handling
  - deterministic Markdown rendering and optional budget-violation sections
  - internal-only scope boundaries and non-mutation
- Control review initially found one rigor defect:
  - strict ledger parsing still accepted `NaN` and `Infinity` because Python's default JSON loader is permissive for non-finite numeric tokens
- Correction pass updated strict parsing to reject non-finite JSON numeric tokens at decode time, added finite-value guards for required and nullable numeric metric fields, and added regression coverage for `NaN`, `Infinity`, and `-Infinity`
- Validation confirmed after correction:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 292 passed and 1 deselected
- Higher-level report pipelines, public-claim gating, CLI, docs updates, and release work remain deferred
- Acceptance status: 1 correction

## 2026-04-16 -- Deterministic Multi-Run Ledger Production

- Added deterministic multi-run eval ledger orchestration first-pass
- Added `src/context_ir/eval_runs.py` with:
  - strict run-spec loading for deterministic task x provider x budget execution
  - repo-relative task-path resolution
  - deterministic provider dispatch over accepted internal provider names
  - one oracle setup resolution per case
  - deterministic run-id construction
  - orchestration that executes providers, scores runs, builds raw records, and appends compact JSONL ledger rows
- Added durable run-spec asset:
  - `evals/run_specs/oracle_smoke_matrix.json`
- Added `tests/test_eval_runs.py` covering:
  - typed run-spec loading
  - unknown top-level and case-field rejection
  - unknown provider-name rejection
  - empty case-list and non-positive-budget rejection
  - provider-dispatch coverage for accepted internal names
  - one raw record per task x provider x budget combination
  - deterministic case/provider/budget execution order
  - oracle setup reuse once per case
  - non-mutation of loaded specs and resolved setups
  - internal-only scope boundaries with no report/public-surface creep
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 275 passed and 1 deselected
- Markdown reports, category rollups, public-claim gating, CLI, and docs updates remain deferred
- Acceptance status: first-pass

## 2026-04-16 -- Deterministic Raw Result Record Core

- Added deterministic per-run raw eval result records after 1 correction
- Added `src/context_ir/eval_results.py` with:
  - typed JSON-safe dataclasses for fixture hashes, provider config and metadata, resolved selector evidence, metric outputs, and full raw run records
  - `build_eval_run_record(setup, result, metrics, ...) -> EvalRunRecord`
  - `eval_run_record_to_json(record) -> dict[str, object]`
  - `append_eval_run_record_jsonl(path, record) -> None`
- The raw-record contract now preserves:
  - fixture file hashes keyed by sorted repo-relative paths
  - provider config, selected files, selected unit IDs, omitted unit IDs, and warnings
  - structured provider metadata needed by later ledger and report slices
  - resolved oracle selector evidence with original selectors, resolved unit IDs, file paths, and spans
  - full deterministic metric outputs from the accepted scoring layer
- Added `tests/test_eval_results.py` covering deterministic JSON-safe record creation, resolved selector preservation, structured provider metadata preservation, deterministic fixture hashing, compact one-object-per-line JSONL appends, repeated append preservation, non-mutation, and internal-only scope boundaries
- Control review initially found one reproducibility issue:
  - fixture hashes were computed from decoded text and re-encoded bytes rather than raw on-disk bytes
- Correction pass updated fixture hashing to use raw file bytes and added a CRLF regression test proving the recorded hash matches on-disk bytes rather than normalized text
- Validation confirmed after correction:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 263 passed and 1 deselected
- Multi-run orchestration, Markdown summaries, category rollups, public-claim gating, and docs updates remain deferred
- Acceptance status: 1 correction

## 2026-04-16 -- Deterministic Metric Scoring Core

- Added deterministic per-run eval scoring first-pass
- Added `src/context_ir/eval_metrics.py` with `score_eval_run(setup, result) -> EvalRunMetrics`
- The scorer now computes deterministic per-run outputs over accepted oracle and provider inputs:
  - budget compliance
  - edit coverage
  - support coverage
  - representation adequacy
  - uncertainty honesty
  - credited relevant tokens
  - noise tokens, noise ratio, and noise efficiency
  - aggregate score with weight renormalization when support or uncertainty components are absent
- The scorer uses the accepted deterministic rules for:
  - detail-rank adequacy across `identity`, `summary`, and `source`
  - Context IR structured trace matching
  - whole-file baseline source adequacy
  - selected and omitted uncertainty honesty credit
  - exact source-span token credit
  - overlap merging for source-span credits
- Added `tests/test_eval_metrics.py` covering detail-rank behavior, source-level baseline adequacy, `None` handling for support and uncertainty components, selected and omitted uncertainty credit, exact-span token credit, overlapping-span merge behavior, non-mutation, and internal-only scope boundaries
- Control review found no issues
- Validation confirmed:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 254 passed and 1 deselected
- Raw ledgers, reports, run-matrix execution, and public-claim updates remain deferred
- Acceptance status: first-pass

## 2026-04-16 -- Deterministic Provider/Baseline Infrastructure

- Added deterministic internal eval provider infrastructure after 1 correction
- Added `src/context_ir/eval_providers.py` with:
  - typed provider request, config, metadata, and result dataclasses
  - shared token estimator `max(1, (len(text) + 3) // 4)`
  - deterministic lexical tokenization and lexical file scoring
  - whole-file budget-aware packing for baseline providers
  - Context IR provider delegation through `compile_repository_context(...)` with `embed_fn=None`
  - deterministic `lexical_top_k_files`, `import_neighborhood_files`, and diagnostic `file_order_floor` providers
- Added `tests/test_eval_providers.py` covering token estimation, lexical tokenization, lexical ordering, zero-match behavior, header-aware budget packing, import-neighborhood seed/import behavior, star-import warning behavior, missing/external import handling, diagnostic baseline marking, Context IR facade delegation, no-oracle provider inputs, and internal-only scope boundaries
- Control review initially found one metadata-contract issue:
  - Context IR provider output collapsed selection trace and warnings too aggressively for the later scoring slice
- Correction pass added structured Context IR metadata:
  - `EvalSelectedUnit`
  - `EvalProviderWarning`
  - `EvalProviderMetadata.selected_units`
  - `EvalProviderMetadata.warning_details`
- Context IR provider output now preserves:
  - selected unit `unit_id`, `detail`, `token_count`, `basis`
  - selected unit `reason`, `edit_score`, and `support_score`
  - warning `code`, `unit_id`, and `message`
- `EvalProviderResult` now rejects lossy mismatches between convenience tuples and the structured Context IR metadata
- Validation confirmed after correction:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 243 passed and 1 deselected
- Metric scoring, raw result ledgers, reports, and public-claim updates remain deferred
- Acceptance status: 1 correction

## 2026-04-15 -- Eval Oracle Foundation

- Added the deterministic eval oracle foundation after 1 correction
- Added `src/context_ir/eval_oracles.py` as an internal module with:
  - typed dataclasses for eval tasks, selectors, resolved selector records, and setup results
  - JSON task loading
  - generated runtime-ID field rejection
  - strict unknown-field rejection for task records and selector records
  - selector resolution through `analyze_repository(...)`
  - loud unresolved and ambiguous selector setup failures
- Added durable smoke eval assets under `evals/`:
  - `evals/fixtures/oracle_smoke/main.py`
  - `evals/fixtures/oracle_smoke/pkg/__init__.py`
  - `evals/fixtures/oracle_smoke/pkg/helpers.py`
  - `evals/tasks/oracle_smoke.json`
- Added `tests/test_eval_oracles.py` covering typed loading, generated-ID rejection, unknown-field rejection, deterministic symbol/frontier/unsupported selector resolution, analyzer usage, unresolved and ambiguous failure paths, no mutation, and no public/package/provider/baseline/scoring/report expansion
- Control review initially found one schema-strictness issue: unknown task and selector fields were silently accepted
- Correction pass added allowed-field validation and tests for unknown top-level, symbol, frontier, and unsupported selector fields
- Validation confirmed after correction:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `.venv/bin/python -m pytest tests/ -v -m "not slow"` with 229 passed and 1 deselected
- Provider adapters, baseline providers, metric scoring, raw result output, reports, and public-claim updates remain deferred
- Acceptance status: 1 correction

## 2026-04-15 -- Deterministic Fixture-Level Eval Design

- Accepted the read-only deterministic fixture-level eval design slice after 2 corrections
- The accepted design answers the evidence-building question: whether Context IR produces higher-quality context packs than simple deterministic retrieval baselines under fixed budgets on repo-controlled coding-agent fixtures
- Correction 1 froze:
  - deterministic `lexical_top_k_files` and `import_neighborhood_files` baseline algorithms
  - shared token estimator and whole-document budget accounting
  - credited-relevant-token, noise, coverage, representation, and uncertainty metric rules
  - success, failure, negative-evidence, and no-public-claim gates
  - uncertainty scoring policy requiring selected document, selected trace, omitted surface, or optimization-warning evidence rather than dormant facade metadata
- Correction 2 replaced generated unit-ID oracles with stable selector-based task records resolved at run time through `analyze_repository(...)`
- The accepted next implementation slice is narrowed to the eval oracle foundation:
  - eval asset layout
  - task schema or strict loader
  - selector resolver
  - tiny fixtures/task records
  - tests proving symbol, frontier, and unsupported selectors resolve deterministically
  - tests proving unresolved or ambiguous selectors fail setup loudly
- Provider adapters, baseline providers, metric scoring, raw JSONL output, reports, and public-claim updates remain deferred until the oracle foundation is accepted
- No files were changed by the execution research lane; control-lane continuity was updated after acceptance
- Acceptance status: 2 corrections

## 2026-04-15 -- Release Sequencing

- Released the accepted semantic-first baseline to `origin/main`
- Current released commit verified locally: `9abc57c Rebaseline Context IR around semantic analysis`
- Local `main` has no ahead/behind marker relative to `origin/main`
- Release state now distinguishes the accepted/pushed semantic baseline from the next evidence-building phase
- Acceptance status: first-pass

## 2026-04-15 -- README / Public-Claim Sync

- Updated `README.md` to match the accepted semantic-first public surface and `EVAL.md` claim boundaries
- README now describes:
  - Context IR as an in-progress semantic-first Python context compiler
  - supported static Python subset and explicit unsupported limits
  - public analyzer usage through `context_ir.analyze_repository(...)`
  - tool-facing compile usage through `context_ir.tool_facade.compile_repository_context(...)`
  - minimal MCP stdio usage through `python -m context_ir.mcp_server`
  - local development and validation commands
  - evidence limits and unsupported SWE-bench, benchmark, production, performance, and multi-language claims
  - legacy graph-first modules as direct-module compatibility only, not package-root public API
- Removed stale README framing that renderer, ranking, optimizer, compiler, recompile, MCP, and eval work were still all pending
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- Eval Methodology and Evidence Baseline

- Added `EVAL.md` as the repo evidence and methodology baseline
- The evidence ledger distinguishes:
  - behavior proven by current unit/integration tests
  - local quality-gate validation
  - protocol smoke-test evidence
  - architecturally intended but unevaluated work
  - unsupported benchmark, performance, production, multi-language, and portfolio claims
- `EVAL.md` records allowed claims for the accepted semantic-first core, analyzer, package-root quarantine, tool-facing facade, and minimal MCP wrapper
- `EVAL.md` explicitly disallows SWE-bench, benchmark improvement, resolve-rate, production-readiness, multi-language, broad dynamic-Python, performance, and complete-product MCP claims without further evidence
- Future eval slices are scoped as deterministic fixture-level behavioral eval, budget-curve harness design, baseline comparison design, raw result ledger, and only later SWE-bench-style methodology
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- Minimal MCP Wrapper

- Accepted the minimal MCP wrapper after explicit human authorization for the dependency/protocol path
- Added the official Python MCP SDK dependency: `mcp>=1.27.0`
- Verified local SDK metadata: installed `mcp` version `1.27.0`, `Requires-Python >=3.10`
- Added `src/context_ir/mcp_server.py` using `mcp.server.fastmcp.FastMCP` from the official SDK
- Registered exactly one MCP tool: `compile_repository_context`
- The tool:
  - validates inputs
  - rejects non-positive budgets with JSON-safe errors
  - delegates to `context_ir.tool_facade.compile_repository_context(...)`
  - serializes document, token totals, budget, confidence, selection trace, omitted units, unresolved frontier, unsupported constructs, syntax diagnostics, semantic diagnostics, and optimization warnings
  - supports `include_document=false` while preserving trace and uncertainty output
  - preserves package-root export quarantine
- Added `tests/test_mcp_server.py` covering delegation, JSON-safe serialization, document omission, uncertainty surfacing, parse diagnostics, invalid budget errors, retired API avoidance, package-root non-exposure, and SDK registration/local invocation
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- MCP Wrapper Dependency/Protocol Hold

- MCP wrapper implementation lane returned `NEEDS-CONTROL` with no files changed
- Reason: the repo has no MCP dependency, no existing MCP/server/protocol surface, and neither `mcp` nor `fastmcp` is installed in the local environment
- Control assessment: the execution lane correctly stopped rather than guessing an SDK API or writing a speculative protocol shim
- Human authorization is required before adding a new MCP dependency or declaring a protocol/transport choice
- Recommended next authorized action, if approved:
  - add and verify the official Python MCP SDK dependency
  - use stdio transport for the first server
  - implement one minimal compile tool over `context_ir.tool_facade.compile_repository_context(...)`
  - test JSON-safe output, uncertainty surfacing, invalid-budget errors, and SDK registration/local invocation
- Acceptance status: held

## 2026-04-15 -- Tool-Facing Facade Contract

- Added `src/context_ir/tool_facade.py` with:
  - `SemanticContextRequest`
  - `SemanticContextResponse`
  - `compile_repository_context(...)`
- The facade delegates directly to the accepted public analyzer and semantic compiler:
  - `analyze_repository(...)`
  - `compile_semantic_context(...)`
- The facade response transparently exposes:
  - returned `SemanticProgram`
  - returned `SemanticCompileResult`
  - unresolved frontier
  - unsupported constructs
  - syntax and semantic diagnostics
  - optimization warnings
  - selection trace
  - omitted unit IDs
  - compile budget and total tokens
- Package-root exports were intentionally left unchanged; the facade remains available through `context_ir.tool_facade`
- Added `tests/test_tool_facade.py` to lock delegation, uncertainty surfacing, parse-error truthfulness, budget honesty, retired graph-first API avoidance, optional embedding pass-through, and package-root non-exposure
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- Package-Root Public API and Legacy Quarantine

- Updated `src/context_ir/__init__.py` so package-root exports are semantic-first
- Kept `context_ir.analyze_repository` as the promoted public low-level API
- Root exports now mirror the public semantic contract types from `semantic_types.py`
- Removed retired graph-first root bindings and `__all__` entries for:
  - `compile`
  - `optimize`
  - `parse_file`
  - `parse_repository`
  - `render`
  - `score_graph`
- Preserved direct old-module import compatibility for the retired graph-first modules
- Added `tests/test_public_api.py` to lock:
  - root `__all__` policy
  - root analyzer availability
  - retired graph-first root quarantine
  - direct old-module import compatibility
  - semantic module-level API availability through explicit modules
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- Semantic Analyzer Public Contract

- Added `analyze_repository(repo_root: Path | str) -> SemanticProgram` as the real public low-level semantic analysis API
- Added `src/context_ir/analyzer.py` to orchestrate the accepted semantic-first pipeline:
  - `extract_syntax(repo_root)`
  - `bind_syntax(syntax)`
  - `resolve_semantics(bound_program)`
  - `derive_dependency_frontier(resolved_program)`
- Replaced the `semantic_types.py` placeholder with a lazy wrapper that preserves `from context_ir.semantic_types import analyze_repository`
- Package-root `context_ir.analyze_repository` remains available through the existing export path
- Added analyzer tests for:
  - parity with the accepted manual pipeline
  - `Path` and `str` repo roots
  - package-root and semantic-types import paths
  - parse-error truthfulness
  - presence of derived binder/resolver/dependency/frontier outputs
  - narrow orchestration boundaries
- Control review found no issues
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-15 -- Final-Phase Planning

- Accepted final-phase decomposition planning for MCP / eval / portfolio-facing work
- Planning confirmed current repo reality:
  - `analyze_repository(repo_root) -> SemanticProgram` remains the approved public low-level API but is still a loud placeholder
  - semantic-first core APIs exist as module-level surfaces, while package-root exports still include retired graph-first APIs
  - no MCP server, CLI, tool-facing adapter, eval harness, benchmark suite, or console entry point exists yet
  - README remains stale relative to the accepted semantic-first core
  - accepted semantic-first work is present in the workspace but not yet committed or pushed
- Control decision: the next implementation slice is the semantic analyzer public contract
- Planned later slices remain separate:
  - package-root API and legacy quarantine
  - tool-facing facade contract
  - MCP wrapper decision and implementation
  - eval methodology and evidence baseline
  - README / portfolio-facing claim sync
  - final release and continuity sequencing
- Public claims, benchmark framing, and MCP protocol work remain paused until their dedicated evidence-backed slices
- Acceptance status: first-pass

## 2026-04-14 -- Diagnose and Recompile Reset

- Added semantic-first diagnose/recompile contracts in `src/context_ir/semantic_types.py`:
  - `SemanticMissKind`
  - `SemanticMissEvidence`
  - `SemanticDiagnosticResult`
  - `SemanticRecompileResult`
  - narrow `SemanticCompileContext`
- Updated `compile_semantic_context(...)` to persist the prior query in `SemanticCompileResult.compile_context`
- Added `diagnose_semantic_miss(...)` and `recompile_semantic_context(...)` in `src/context_ir/semantic_diagnostics.py`
- Diagnose now grounds supported miss evidence only to accepted semantic unit IDs and distinguishes:
  - omitted units
  - selected-but-too-shallow units
  - already sufficient units
  - ungrounded evidence
- Recompile now re-scores from the prior query, applies conservative miss-driven boosts, and recompiles under `previous_result.budget + delta_budget` without mutating inputs
- Correction pass fixed two reviewed P1 grounding defects:
  - inconsistent stack traces with mismatched file/function clues no longer ground to unrelated units
  - path grounding now rejects arbitrary substrings and only accepts conservative path-shaped matches
- Validation confirmed after correction: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: 1 correction

## 2026-04-14 -- Optimizer and Compile Reset

- Added semantic-first optimization and compile contracts in `src/context_ir/semantic_types.py` for:
  - `SemanticSelectionRecord`
  - `SemanticOptimizationWarning`
  - `SemanticOptimizationResult`
  - `SemanticCompileResult`
- Added `optimize_semantic_units(program, scoring, budget) -> SemanticOptimizationResult` in `src/context_ir/semantic_optimizer.py`
- Added `compile_semantic_context(program, query, budget, *, scoring=None, embed_fn=None) -> SemanticCompileResult` in `src/context_ir/semantic_compiler.py`
- The new optimizer/compiler stack now operates only on accepted semantic unit IDs and accepted semantic render details (`identity`, `summary`, `source`)
- Correction pass fixed a reviewed P1 contract-honesty defect:
  - compile token accounting now reflects the emitted document, not only selected unit render cost
  - compilation re-optimizes against reserved document-assembly overhead until the emitted artifact fits the requested budget
  - impossibly small budgets now fail loudly rather than returning an over-budget artifact with misleading totals
- `SemanticOptimizationResult.total_tokens` continues to represent selected-unit render cost, while `SemanticCompileResult.total_tokens` now represents the assembled artifact cost
- Validation confirmed after correction: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: 1 correction

## 2026-04-14 -- Scorer Reset

- Added `score_semantic_units(program: SemanticProgram, query: str, *, embed_fn: Callable[[list[str]], list[list[float]]] | None = None) -> SemanticScoringResult` in `src/context_ir/semantic_scorer.py` as the semantic-first scorer entry point on top of the accepted renderer baseline
- Established a minimal separate scorer-result contract with:
  - `SemanticUnitScore` carrying `unit_id`, `p_edit`, and `p_support`
  - `SemanticScoringResult` carrying the query plus the score map
- The scorer now ranks every renderable semantic unit ID:
  - proven symbols
  - unresolved frontier items
  - unsupported constructs
- Direct relevance drives `p_edit`, one-hop propagation over accepted `proven_dependencies` raises only `p_support`, and uncertainty items may gain support from a directly relevant enclosing scope
- Scores remain bounded in `[0.0, 1.0]`, the scorer does not mutate `SemanticProgram`, and embedding-based similarity remains optional through injected `embed_fn`
- Boundary note: package-root exposure for the new semantic scorer remains deferred; the retired `score_graph(...)` surface was intentionally left untouched in this slice
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-14 -- Renderer Reset

- Added `render_semantic_unit(program: SemanticProgram, unit_id: str, detail: RenderDetail) -> RenderedUnit` in `src/context_ir/semantic_renderer.py` as the semantic-first renderer entry point on top of the accepted dependency/frontier substrate
- Established a minimal semantic-first representation baseline with three detail levels:
  - `IDENTITY` for concise identity plus provenance
  - `SUMMARY` for semantic summary plus provenance
  - `SOURCE` for exact source-backed rendering or truthful source-unavailable fallback
- The renderer now supports one unified API across:
  - proven repository-backed symbols
  - unresolved frontier items
  - unsupported constructs
- Proven dataclass support and dataclass field facts are surfaced in rendered symbol summaries when present in accepted lower-layer facts
- Each rendered unit now carries positive token accounting for later optimizer work
- Boundary note: unsupported constructs do not currently carry a lower-layer reference context, so renderer output surfaces `context: unavailable` instead of inventing missing context
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-14 -- Semantic Dependency Graph and Frontier

- Added `derive_dependency_frontier(program: SemanticProgram) -> SemanticProgram` as the dependency/frontier derivation entry point on top of the accepted resolver substrate
- The slice now derives repository-backed semantic dependencies for:
  - imports from the owning module/class/function/method scope
  - calls from the owning module/function/method scope
  - proven base-class references
  - proven decorator references
- The slice now surfaces explicit frontier/unsupported records for:
  - supported-but-unresolved simple-name and direct-attribute decorator/base/call surfaces
  - star imports
  - unsupported decorator/base/call target shapes outside the accepted direct grammar
- Parse-error files remain excluded from dependency/frontier facts
- Boundary note: ordinary unresolved non-star imports still do not have a dedicated honest frontier surface in the current contracts; this slice stayed conservative and did not force those cases into misleading records
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-14 -- Resolver and Object Model

- Added `resolve_semantics(program: SemanticProgram) -> SemanticProgram` as the resolver / object-model entry point on top of the accepted binder substrate
- Resolver now records proven import targets, proven decorator/base/call references for supported direct forms, and narrow dataclass object facts using only binder output plus `SemanticProgram.syntax`
- Narrow dataclass support is now mirrored onto the owning class `ResolvedSymbol` when the resolver can actually prove `dataclasses.dataclass`
- Correction pass fixed three reviewed P1 defects:
  - proven dataclass support now reaches the class symbol
  - bare module imports no longer become proven decorator/base references
  - non-aliased dotted imports require proof of the full dotted module path before a `ResolvedImport` is recorded
- `proven_dependencies` remains empty by design in this slice; semantic dependency/frontier derivation remains the next layer
- Validation confirmed after correction: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: 1 correction

## 2026-04-14 -- Binder and Scope Model

- Added `bind_syntax(syntax: SyntaxProgram) -> SemanticProgram` as the binder / scope-model entry point
- Binder reuses syntax-backed definition IDs as stable semantic symbol IDs and carries `SemanticProgram.syntax` through unchanged
- Binder emits definition, parameter, import, simple identifier assignment, and provable class-attribute binding facts with ordered binding history preserved for later shadowing resolution
- Files with `SyntaxDiagnosticCode.PARSE_ERROR` do not contribute binder-owned semantic facts
- Narrow prerequisite contract correction landed with this slice: `ImportFact` now carries `scope_id`, and parser population of that field keeps nested import bindings in the correct lexical scope
- Validation confirmed: `ruff check`, `ruff format --check`, `mypy --strict`, and `pytest -v -m "not slow"` all passed
- Acceptance status: first-pass

## 2026-04-14 -- Parameter-Facts Prerequisite Correction

- Accepted follow-up parser correction to preserve parameter declaration order, parameter kinds, default metadata, and source sites needed by binder and resolver work
- Validation remained clean after the correction
- Acceptance status: first-pass

## 2026-04-14 -- Syntax Parse-Failure Correction

- Accepted follow-up parser correction to emit explicit `SyntaxDiagnosticCode.PARSE_ERROR` diagnostics for syntax-invalid files
- Parse-error files remain in source inventory but are excluded from trustworthy semantic fact production beyond the syntax-level scaffold
- Validation remained clean after the correction
- Acceptance status: first-pass

## 2026-04-14 -- Syntax Parser Reset

- Accepted the semantic-first parser reset after 1 correction
- `extract_syntax(...)` and `extract_syntax_file(...)` now produce `SyntaxProgram` facts for supported Python files instead of feeding the retired heuristic symbol-graph contract
- Syntax extraction now preserves source inventory, raw definitions, imports, decorators, base expressions, assignments, call sites, attribute sites, and other source-backed facts needed for later semantic analysis
- Legacy `parse_file(...)` and `parse_repository(...)` compatibility entry points remain compiling during the rebaseline so the old stack can stay importable while it is being replaced slice by slice
- Acceptance status: 1 correction

## 2026-04-14 -- Semantic Contracts and Types

- Accepted the semantic contracts / types slice after 1 correction
- Introduced the `SyntaxProgram` and `SemanticProgram` contract surfaces plus the shared dataclasses and enums needed for later parser, binder, resolver, dependency, renderer, ranking, optimization, compiler, and diagnostics work
- Established explicit supported-subset, proof-status, unresolved-frontier, and unsupported-construct surfaces so later slices can report uncertainty without fabricating semantic claims
- Recorded `@dataclass` as the first explicitly supported decorator set in the semantic-first baseline
- Acceptance status: 1 correction

## 2026-04-13 -- Semantic-First Baseline Supersedes Frozen Spec

- Prior April 13 frozen spec retired and superseded as the current authority for planning, architecture, and acceptance
- Human-approved control decisions recorded:
  - Replace the old frozen baseline with the new semantic-first baseline
  - Keep `p_edit` / `p_support`, but only as internal ranking policy rather than the public thesis
  - Keep the multi-tier representation idea, but do not keep the exact 5-tier semantics frozen yet
  - Make `analyze_repository(...) -> SemanticProgram` a public low-level API
  - Include `@dataclass` in the first supported decorator set, scoped narrowly and explicitly
- Control decision: future execution follows the new slice plan:
  1. Docs freeze / continuity reset
  2. Semantic contracts and types
  3. Syntax parser reset
  4. Binder and scope model
  5. Resolver and object model
  6. Semantic dependency graph and frontier
  7. Renderer reset
  8. Scorer reset
  9. Optimizer and compile reset
  10. Diagnose / recompile reset
  11. Only then MCP / eval / portfolio-facing work
- Prior retrospective findings still stand as evidence for why the reset was required
- Earlier slice entries, including any accepted corrections or historical parser/renderer improvements, remain historical record only and do not override the new control state
- Alternatives considered:
  - Continue the old Slice 1 -> Slice 6 correction chain on top of the retired frozen spec
  - Patch only the public `recompile` contract while keeping the prior architecture
  - Rebaseline the system around semantic analysis before resuming higher layers
- Reasoning:
  - Retrospective evidence showed the failure was architectural, not a single top-layer contract issue
  - Semantic contracts, binder behavior, and resolver behavior must exist before ranking, optimization, compilation, or `recompile` can make truthful claims
  - Public positioning must shift from heuristic budget packing to semantically grounded compilation with explicit uncertainty handling
- Acceptance status: first-pass

## 2026-04-13 -- Project Genesis: Context IR

- Concept developed through 3 rounds of research and adversarial review
- Round 1 (ChatGPT): Initial concept development. Identified reference-first context compilation as the thesis. Proposed six-component architecture.
- Round 2 (Claude control lane + execution spike): Competitive landscape validation. Mapped Aider, Codebase-Memory, SWE-agent, Moatless, Agentless. Confirmed gap: no existing tool does budget-aware format selection. Scoped to Option B (MCP server + SWE-bench Mini eval, 4-6 weeks).
- Round 3 (ChatGPT devil's advocate): Sharpened algorithm (symbol-level units, 5-tier hierarchy, dual scoring, dependency-preserving source slices), eval methodology (frozen-input regime, budget curves, ablations), systems engineering signal (recompile loop, compile traces, diagnostics). Confirmed competitive claims (RepoRepair March 2026, SWE-bench Pro preference, Verified submission restrictions).
- Frozen spec locked.
- Build order: compiler core first, MCP wrapper later.
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

## 2026-04-13 -- Slice 1: Symbol Graph Parser

- Created tree-sitter-based parser (src/context_ir/parser.py)
- Added FILE and MODULE to SymbolKind enum (resolved container node question)
- Decision: container nodes as additional enum values, not a separate type. Keeps graph homogeneous -- all nodes are SymbolNode.
- Parser extracts FUNCTION, CLASS, METHOD, CONSTANT, IMPORT nodes with DEFINES, CALLS, IMPORTS edges
- Cross-file import resolution via best-effort Python path matching
- Node ID convention established: file:<path>, module:<path>, <path>::<name>
- Added tree-sitter and tree-sitter-python as runtime dependencies
- Test fixtures: 4-file sample Python package in tests/fixtures/sample_repo/
- 14 new parser tests (23 total), all passing
- Review finding: dead code (_extract_imported_names never called) removed in correction pass
- Accepted gap: REFERENCES edges not implemented (deferred to Slice 3 evaluation, Ryan sign-off given)
- Accepted gap: relative imports, aliased imports, multi-line imports have limited resolution (best-effort scope)
- Acceptance status: 1 correction

## 2026-04-13 -- Slice 2: View Renderers

- Created 5-tier view renderer (src/context_ir/renderer.py)
- OMIT: reference ID. SUMMARY: signature + docstring + structural counts. STUB: signature with ... body. SLICE: source + same-file imports, constants, called function stubs. FULL: exact source from disk.
- SLICE tier (key deliverable) uses graph edges (CALLS, DEFINES) and text-matching heuristic for import relevance
- Token estimation: max(1, len(text) // 4). Isolated in estimate_tokens() for later replacement.
- tree-sitter reused for robust signature extraction (multiline, decorated definitions)
- 18 new tests (41 total), all passing
- Execution chat reported mypy errors but verification showed clean pass in project venv (reporting discrepancy, not a code issue)
- Acceptance status: first-pass

## 2026-04-13 -- Slice 3: Scoring Engine

- Created scoring engine (src/context_ir/scorer.py) with score_graph() public API
- 9-step pipeline: query term extraction, symbol text profiles, lexical scoring, structural priors, semantic similarity, weighted combination, graph propagation, container node scoring, normalization
- Lexical features: name match (exact/substring), path match (with dotted-path normalization), content match (query terms in source)
- Structural priors: test file p_support boost + p_edit penalty, config file boost, entry point boost, kind-based base probabilities
- Semantic similarity: sentence-transformers (all-MiniLM-L6-v2), lazy loaded, injectable embed_fn for testing
- Graph propagation: 2 iterations, 0.3 decay. CALLS/IMPORTS -> p_support on target. DEFINES -> p_edit upward to parent.
- Container scoring: FILE/MODULE get max of children's scores
- Feature weights: lexical 40%/30%, structural 10%/20%, semantic 50%/50% (edit/support). Weights sum to 1.0.
- Design decision: REFERENCES edges evaluated and determined not needed. CALLS + IMPORTS + DEFINES provide sufficient propagation signal.
- sentence-transformers 5.x ships type stubs, so no type: ignore[import-untyped] needed
- 14 new tests (55 total), all passing. Real model integration test runs in ~3.6s.
- Acceptance status: first-pass

## 2026-04-13 -- Slice 4: Budget Optimizer

- Created budget optimizer (src/context_ir/optimizer.py) with optimize() public API
- Added OptimizationResult dataclass to types.py
- Greedy algorithm: marginal utility per token, sorted by efficiency, multi-pass to handle prerequisite ordering of upgrade steps
- Tier value tables: OMIT(0.0/0.1), SUMMARY(0.1/0.5), STUB(0.3/0.8), SLICE(0.9/0.25), FULL(1.0/0.3) for edit/support
- Dependency closure: one-hop CALLS edges, ensures targets at minimum STUB. Can exceed budget.
- Warning generation: HIGH_RISK_OMISSION (p_edit > 0.5, excluded), BUDGET_FORCED_DOWNGRADE (p_edit > 0.3, at STUB or below), UNRESOLVED_SYMBOL_FRONTIER (non-packable targets of edges from packed symbols)
- Trace: one CompileTraceEntry per packable symbol with downgrade reasons (DEPENDENCY_ONLY, LOW_RELEVANCE, BUDGET_PRESSURE)
- Confidence: achieved utility / max possible utility across all tiers (not always FULL, since STUB is optimal for support-heavy symbols)
- Packs FUNCTION, CLASS, METHOD, CONSTANT only. FILE, MODULE, IMPORT excluded from packing.
- Execution chat fixed: prerequisite ordering bug (multi-pass), confidence formula (actual max tier, not always FULL)
- 14 new tests + 1 smoke test (70 total), all passing
- Acceptance status: first-pass

## 2026-04-13 -- Slice 5: Compile Contract

- Created compiler module (src/context_ir/compiler.py) with compile() public API
- Orchestrates full pipeline: parse -> score -> optimize -> render -> assemble
- Document format: metadata header, file-grouped sections (alphabetical), symbols ordered by start_line, tier labels ([FULL], [SLICE], [STUB], [SUMMARY], [OMIT]), omitted section at end
- Optional pre-parsed graph parameter (skips re-parsing)
- Optional embed_fn pass-through to scorer
- First of three frozen-spec contracts (compile, diagnose, recompile)
- 12 new integration tests (82 total), all passing
- Execution chat reported mypy errors but verification showed clean pass in project venv (same pattern as Slice 2)
- Acceptance status: first-pass

## 2026-04-13 -- Retrospective Audit: Slice 1 Rejected

- Prior acceptance withdrawn after retrospective audit.
- Proven issue classes: parser-layer correctness gaps, contract/documentation overclaim, and insufficient acceptance evidence for the symbol/edge extraction baseline that later slices depended on.
- Downstream consequence: Slice 2 onward cannot remain accepted on top of this unresolved lower layer.
- Acceptance status: rejected

## 2026-04-13 -- Retrospective Audit: Slice 2 Rejected

- Prior acceptance withdrawn after retrospective audit.
- Proven issue classes: renderer tier-behavior and source-slice contract gaps, acceptance notes that outran verified repo reality, and dependency on a rejected parser baseline.
- Downstream consequence: Slice 3 onward cannot remain accepted on top of this unresolved layer.
- Acceptance status: rejected

## 2026-04-13 -- Retrospective Audit: Slice 3 Rejected

- Prior acceptance withdrawn after retrospective audit.
- Proven issue classes: scoring-behavior and feature-contract overclaim, insufficient acceptance basis for claimed propagation/feature behavior, and reliance on rejected lower layers.
- Downstream consequence: Slice 4 onward cannot remain accepted on top of this unresolved layer.
- Acceptance status: rejected

## 2026-04-13 -- Retrospective Audit: Slice 4 Rejected

- Prior acceptance withdrawn after retrospective audit.
- Proven issue classes: optimizer trace/warning/confidence contract gaps, architecture claims that outran verified behavior, and reliance on rejected upstream layers.
- Downstream consequence: Slice 5 onward cannot remain accepted on top of this unresolved layer.
- Acceptance status: rejected

## 2026-04-13 -- Retrospective Audit: Slice 5 Rejected

- Prior acceptance withdrawn after retrospective audit.
- Proven issue classes: compile-contract and output-guarantee overclaim, acceptance based on an invalid lower-layer foundation, and architecture/docs that presented the slice as settled when it is not.
- Downstream consequence: Slice 6 cannot advance as a clean top-layer continuation.
- Acceptance status: rejected

## 2026-04-13 -- Retrospective Audit: Slice 6 Held

- Prior forward-progress framing withdrawn after retrospective audit.
- Proven issue classes: public `recompile` contract remains unresolved, lower-layer corrections must land first, and architecture/docs had already overclaimed Slice 6 behavior as if accepted.
- Control decision at that time: hold Slice 6 until Slices 1-5 are corrected in order and the control lane makes an explicit public-contract decision.
- Historical note: this hold remains part of the evidence trail, but future execution now follows the semantic-first rebaseline recorded above rather than the retired correction chain.
- Acceptance status: held
