# BUILDLOG.md -- Decision Log

Most recent supersession entries override older architectural decisions when they explicitly say so. Older entries remain intact below as history.

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
