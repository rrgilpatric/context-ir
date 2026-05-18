# Portfolio 001 Evidence

## Classification

Task 0: `STRONG`

Task 1: `STRONG`

This is internal-only product-differentiation evidence. Public claims remain held.

Tasks 2-3 were not run.

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
| `context_ir` | `219` | `108.846s` | `0` | `6` | Passed required evidence path |
| `lexical_top_k_files` | `71` | `0.252s` | `0` | `0` | Failed under budget |
| `import_neighborhood_files` | `75` | `0.256s` | `0` | `0` | Failed under budget; `import_not_resolved` |

## Task 0 Selected Context_IR Units

`context_ir` selected the required evidence path:

- `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers._selected_unit_metadata`
- `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers.EvalSelectedUnit`
- `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers.EvalProviderMetadata`
- `def:src/context_ir/eval_providers.py:src.context_ir.eval_providers.EvalProviderResult`
- `def:src/context_ir/eval_summary.py:src.context_ir.eval_summary._build_runtime_provenance_record_lookup`
- `eval_evidence:oracle_signal_hasattr_probe:hasattr:main.py:2:11`

The rendered context included:

`eval_evidence: oracle_signal_hasattr_probe; primary=unsupported/opaque; runtime=additive; payload=attribute_present=true`

This preserves the main truth boundary: `unsupported/opaque` remains primary, and runtime evidence remains additive.

## Task 0 Baseline Failure And Overinclude Analysis

Both baselines selected zero files at budget `220`, so neither surfaced `_selected_unit_metadata`, `EvalSelectedUnit`, eval-summary accounting, or the compact `oracle_signal_hasattr_probe` evidence.

The lexical baseline did identify related whole-file candidates, but the top candidates were far too large for the budget:

- `tests/test_eval_signal_hasattr_probe.py`: `6903` estimated tokens
- `tests/test_eval_signal_getattr_probe.py`: `2656` estimated tokens
- `tests/test_eval_signal_vars_probe.py`: `2726` estimated tokens
- `tests/test_semantic_optimizer.py`: `12031` estimated tokens

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

## Caveats

- Latency is a real caveat: `context_ir` took `108.846s` for Task 0 and `118.783s` for Task 1, while the baselines took about `0.25s` to `0.27s`.
- Selected support units include summaries under budget pressure, not always full source.
- The compact eval evidence unit is an internal evidence surface, not a selected unsupported runtime-attached source unit.
- `context_ir` emitted `budget_pressure` and `omitted_uncertainty` warnings.
- This supports only Task 0 at budget `220` and Task 1 at primary budget `260`; it is not evidence for Tasks 2-3 or broad product claims.
- Public claims remain held.

## Evidence Location

The raw reproduced provider records are in `evals/product_differentiation/portfolio_001/runs.jsonl`. Each JSONL row embeds the rendered context in the `document` field and records the selected units/files, token count, elapsed time, warnings, candidate files, omitted candidate files, and lexical score evidence.
