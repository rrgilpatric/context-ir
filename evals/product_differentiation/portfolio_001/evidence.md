# Portfolio 001 Evidence

## Classification

Task 0: `STRONG`

Task 1: `STRONG`

Task 2: `STRONG`

Task 3: `STRONG`

This is internal-only product-differentiation evidence. Public claims remain held.

Task 0 has been refreshed/superseded against current exact provider output. The refresh preserves the original `STRONG` internal-only classification under the original semantic rubric; it is not broad product proof and does not authorize public or demo claims.

## Task 0 Query And Budget

Query:

`Fix _selected_unit_metadata and eval report accounting so unsupported hasattr runtime provenance remains visible in selected unit metadata`

Budget: `220`

Providers:

- `context_ir`
- `lexical_top_k_files`
- `import_neighborhood_files`

## Task 0 Provider Comparison

| Provider | Tokens | Elapsed | Selected files | Selected units | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `context_ir` | `218` | `7.593s` | `0` | `7` | Passed required evidence path |
| `lexical_top_k_files` | `71` | `0.315s` | `0` | `0` | Failed under budget |
| `import_neighborhood_files` | `75` | `0.279s` | `0` | `0` | Failed under budget; `import_not_resolved` |

## Task 0 Selected Context_IR Units

`context_ir` selected the required evidence path:

- `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers._selected_unit_metadata`
- `def:src/context_ir/eval_results.py:src.context_ir.eval_results._runtime_provenance_record`
- `def:src/context_ir/eval_summary.py:src.context_ir.eval_summary._validate_selected_unit_runtime_provenance_links`
- `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers.EvalSelectedUnit`
- `assign:src/context_ir/eval_providers.py:166:4`
- `assign:src/context_ir/eval_providers.py:268:4`
- `eval_evidence:oracle_signal_hasattr_probe:hasattr:main.py:2:11`

The rendered context included:

`eval_evidence: oracle_signal_hasattr_probe; primary=unsupported/opaque; runtime=additive; payload=attribute_present=true`

This supersedes the stale exact selected-unit artifact while preserving the original semantic Task 0 rubric: `_selected_unit_metadata`, `EvalSelectedUnit`, eval-summary report accounting via `_validate_selected_unit_runtime_provenance_links`, compact `oracle_signal_hasattr_probe` evidence, `unsupported/opaque` primary truth, additive runtime evidence, and budget compliance.

## Task 0 Baseline Failure And Overinclude Analysis

Both baselines selected zero files at budget `220`, so neither surfaced `_selected_unit_metadata`, `EvalSelectedUnit`, eval-summary accounting, or the compact `oracle_signal_hasattr_probe` evidence.

The lexical baseline did identify related whole-file candidates, but the top candidates were far too large for the budget:

- `tests/test_eval_signal_hasattr_probe.py`: `6903` estimated tokens
- `tests/test_eval_signal_getattr_probe.py`: `2656` estimated tokens
- `tests/test_eval_signal_vars_probe.py`: `2726` estimated tokens
- `tests/test_semantic_optimizer.py`: `18572` estimated tokens

The import-neighborhood baseline seeded from `tests/test_eval_signal_hasattr_probe.py` and `tests/test_eval_signal_getattr_probe.py`, but selected neither file under budget and emitted `import_not_resolved`.

Under this budget, the baselines fail the evidence path. Reaching similar evidence through their candidates would require materially larger and less focused whole-file context.

## Task 1 Query And Budget

Query:

`Fix discover_semantic_eval_runtime_evidence so compact oracle_signal_hasattr_probe evidence renders additive runtime=additive attribute_present=true without becoming public API`

Primary budget: `260`

Ceiling budget: `360` not run because primary reached `STRONG`

Providers:

- `context_ir`
- `lexical_top_k_files`
- `import_neighborhood_files`

## Task 1 Provider Comparison

| Provider | Tokens | Elapsed | Selected files | Selected units | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `context_ir` | `247` | `118.783s` | `0` | `5` | Passed required evidence path |
| `lexical_top_k_files` | `80` | `0.267s` | `0` | `0` | Failed under budget |
| `import_neighborhood_files` | `85` | `0.265s` | `0` | `0` | Failed under budget; `import_not_resolved` |

## Task 1 Selected Context_IR Units

`context_ir` selected the required evidence path:

- `def:src/context_ir/eval_evidence.py:src.context_ir.eval_evidence.discover_semantic_eval_runtime_evidence`
- `def:src/context_ir/semantic_renderer.py:src.context_ir.semantic_renderer._render_eval_runtime_evidence`
- `def:src/context_ir/semantic_types.py:src.context_ir.semantic_types.SemanticEvalRuntimeEvidence`
- `def:src/context_ir/__init__.py:src.context_ir`
- `eval_evidence:oracle_signal_hasattr_probe:hasattr:main.py:2:11`

The rendered context included:

`eval_evidence: oracle_signal_hasattr_probe; primary=unsupported/opaque; runtime=additive; payload=attribute_present=true`

The package-root `context_ir` unit was included to verify that `discover_semantic_eval_runtime_evidence` did not become a package-root export. This remains internal portfolio evidence, not a public API or demo claim.

## Task 1 Baseline Failure And Overinclude Analysis

Both baselines selected zero files at budget `260`, so neither surfaced `discover_semantic_eval_runtime_evidence`, renderer support, the semantic evidence type, the package-root export boundary, or the compact `oracle_signal_hasattr_probe` evidence.

The lexical baseline identified related whole-file candidates, but the top candidates were too large for the budget:

- `tests/test_semantic_compiler.py`: `7991` estimated tokens
- `tests/test_semantic_scorer.py`: `7802` estimated tokens
- `tests/test_semantic_optimizer.py`: `13651` estimated tokens
- `tests/test_eval_signal_hasattr_probe.py`: `6903` estimated tokens
- `tests/test_eval_evidence.py`: `2852` estimated tokens

The import-neighborhood baseline considered:

- `tests/test_semantic_compiler.py`: `7991` estimated tokens
- `tests/test_semantic_scorer.py`: `7802` estimated tokens

It selected neither file under budget and emitted `import_not_resolved`.

Under this budget, the baselines fail the evidence path. Reaching similar evidence through their candidates would require materially larger and less focused whole-file context.

## Task 2 Query And Budget

Query:

`Fix default local Python subprocess recompile so exec(source) runtime probe results attach additive provenance to unsupported EXEC_OR_EVAL units without promoting primary truth`

Primary budget: `320`

Ceiling budget: not run because primary reached `STRONG`

Repo HEAD: `de9e382`

Providers:

- `context_ir`
- `lexical_top_k_files`
- `import_neighborhood_files`

## Task 2 Provider Comparison

| Provider | Tokens | Elapsed | Selected files | Selected units | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `context_ir` | `317` | `129.702s` | `0` | `7` | Passed required evidence path |
| `lexical_top_k_files` | `80` | `0.272s` | `0` | `0` | Failed under budget |
| `import_neighborhood_files` | `85` | `0.278s` | `0` | `0` | Failed under budget; `import_not_resolved` |

## Task 2 Selected Context_IR Units

`context_ir` selected the required evidence path:

- `def:src/context_ir/tool_facade.py:src.context_ir.tool_facade.recompile_repository_context_with_default_local_python_subprocess`
- `def:src/context_ir/tool_facade.py:src.context_ir.tool_facade.recompile_repository_context_with_dynamic_import_local_python_subprocess`
- `def:src/context_ir/runtime_observation_admission.py:src.context_ir.runtime_observation_admission.admit_runtime_probe_result_batch_for_plan`
- `def:src/context_ir/runtime_observation_recompile.py:src.context_ir.runtime_observation_recompile.apply_default_local_python_subprocess_for_diagnostic_and_recompile`
- `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers.build_context_ir_default_local_python_subprocess_pack`
- `assign:src/context_ir/tool_facade.py:364:4`
- `eval_evidence:oracle_signal_exec_probe:exec:main.py:3:4`

The rendered context included:

`eval_evidence: oracle_signal_exec_probe; primary=unsupported/opaque; runtime=additive; execution_outcome=completed; statement_kind=pass`

This preserves the main truth boundary: `unsupported/opaque` remains primary, and the exec-probe runtime result remains additive evidence.

## Task 2 Baseline Failure And Overinclude Analysis

Both baselines selected zero files at budget `320`, so neither surfaced the default local Python subprocess recompile path, the runtime observation admission and recompile support path, the eval-provider pack, or the compact `oracle_signal_exec_probe` evidence.

The lexical baseline omitted oversized candidates, including:

- `tests/test_semantic_scorer.py`: about `9911` estimated tokens
- `tests/test_semantic_compiler.py`: about `8548` estimated tokens
- `tests/test_eval_signal_exec_probe.py`: about `6127` estimated tokens
- `src/context_ir/eval_providers.py`: about `13190` estimated tokens

The import-neighborhood baseline considered and omitted:

- `tests/test_semantic_scorer.py`: about `9911` estimated tokens
- `tests/test_semantic_compiler.py`: about `8548` estimated tokens

It selected neither file under budget and emitted `import_not_resolved`.

Under this budget, the baselines fail the evidence path. The omitted-uncertainty warnings on the selected `context_ir` path do not contradict the selected runtime evidence path.

## Task 3 Query And Budget

Query:

`Fix transitive sole-provider self-call resolution for MemberSignalCompiler.compile_member_digest while preserving alias_chain frontier on pkg_alias.labels.build_member_label`

Primary budget: `280`

Ceiling budget: not run because primary reached `STRONG`

Repo HEAD: `a201568`

Providers:

- `context_ir`
- `lexical_top_k_files`
- `import_neighborhood_files`

## Task 3 Full-Repo Provider Comparison

| Provider | Tokens | Elapsed | Selected files | Selected units | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `context_ir` | `274` | `122.718s` | `0` | `4` | Passed required evidence path |
| `lexical_top_k_files` | `82` | `0.274s` | `0` | `0` | Failed under budget |
| `import_neighborhood_files` | `86` | `0.275s` | `0` | `0` | Failed under budget; `import_not_resolved` |

## Task 3 Full-Repo Selected Context_IR Units

`context_ir` selected the required full-repo evidence path:

- `def:evals/fixtures/oracle_signal_smoke_e/pkg/service.py:evals.fixtures.oracle_signal_smoke_e.pkg.service.MemberSignalCompiler.compile_member_digest`
- `def:evals/fixtures/oracle_signal_smoke_e/pkg/labels.py:evals.fixtures.oracle_signal_smoke_e.pkg.labels.build_member_label`
- `def:evals/fixtures/oracle_signal_smoke_e/pkg/service.py:evals.fixtures.oracle_signal_smoke_e.pkg.service.MemberSignalCompiler.resolve_owner_alias`
- `unsupported:call:evals/fixtures/oracle_signal_smoke_e/pkg/service.py:10:8`

The selected path kept the alias-chain waypoint honest as `unsupported/opaque` with `unsupported_reason_code` and `opaque_boundary`. The full-repo run emitted `omitted_uncertainty` three times; this is non-blocking for this checkpoint because the required alias-chain uncertainty waypoint was selected honestly.

## Task 3 Fixture-Root Provider Comparison

| Provider | Tokens | Elapsed | Selected files | Selected units | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `context_ir` | `223` | `0.012s` | `0` | `5` | Passed required method/support/frontier waypoints |
| `lexical_top_k_files` | `241` | `0.000s` | `2` | `0` | Missed `pkg/labels.py`; uncertainty honesty `0.0` |
| `import_neighborhood_files` | `243` | `0.001s` | `2` | `0` | Missed `pkg/labels.py`; uncertainty honesty `0.0` |

## Task 3 Fixture-Root Selected Context_IR Units

`context_ir` selected the required fixture-root waypoints with edit, support, and uncertainty metrics all at `1.0`:

- `def:pkg/service.py:pkg.service.MemberSignalCompiler.compile_member_digest`
- `def:pkg/labels.py:pkg.labels.build_member_label`
- `frontier:call:pkg/service.py:10:8`
- `def:pkg/service.py:pkg.service.MemberSignalCompiler.resolve_owner_alias`
- `frontier:attribute:pkg/service.py:10:8:10:24`

The fixture-root baselines selected `pkg/service.py` and `pkg/__init__.py`, omitted `pkg/labels.py`, and recorded `uncertainty_honesty=0.0`.

## Task 3 Baseline Failure And Overinclude Analysis

Full-repo baselines selected no files under budget `280`, so neither surfaced the exact `compile_member_digest` source, `pkg.labels.build_member_label` source, `resolve_owner_alias` support, or the alias-chain uncertainty waypoint.

Fixture-root baselines fit two files under budget, but both omitted the required `pkg/labels.py` support file and did not honestly preserve the semantic uncertainty waypoint. Under this budget, the baselines fail the complete Task 3 evidence path.

## Caveats

- Latency is a real caveat: the refreshed `context_ir` Task 0 provider run took `7.593s`, Task 1 took `118.783s`, Task 2 took about `129.702s`, and the Task 3 full-repo run took `122.718s`, while the full-repo baselines are much faster.
- Selected support units include summaries under budget pressure, not always full source.
- The compact eval evidence unit is an internal evidence surface, not a selected unsupported runtime-attached source unit.
- `context_ir` emitted `budget_pressure` and `omitted_uncertainty` warnings.
- This supports only Task 0 at budget `220`, Task 1 at primary budget `260`, Task 2 at primary budget `320`, and Task 3 at primary budget `280`; it is not evidence for broad product claims.
- Public claims remain held.

## Evidence Location

The raw reproduced provider records are in `evals/product_differentiation/portfolio_001/runs.jsonl`. Each JSONL row embeds the rendered context in the `document` field and records the selected units/files, token count, elapsed time, warnings, candidate files, omitted candidate files, and lexical score evidence.
