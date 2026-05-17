# Task 0 Evidence

## Classification

`STRONG`

This is internal-only product-differentiation evidence. Public claims remain held.

## Query And Budget

Query:

`Fix _selected_unit_metadata and eval report accounting so unsupported hasattr runtime provenance remains visible in selected unit metadata`

Budget: `220`

Providers:

- `context_ir`
- `lexical_top_k_files`
- `import_neighborhood_files`

Tasks 1-3 were not run.

## Provider Comparison

| Provider | Tokens | Elapsed | Selected files | Selected units | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `context_ir` | `219` | `108.846s` | `0` | `6` | Passed required evidence path |
| `lexical_top_k_files` | `71` | `0.252s` | `0` | `0` | Failed under budget |
| `import_neighborhood_files` | `75` | `0.256s` | `0` | `0` | Failed under budget; `import_not_resolved` |

## Selected Context_IR Units

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

## Baseline Failure And Overinclude Analysis

Both baselines selected zero files at budget `220`, so neither surfaced `_selected_unit_metadata`, `EvalSelectedUnit`, eval-summary accounting, or the compact `oracle_signal_hasattr_probe` evidence.

The lexical baseline did identify related whole-file candidates, but the top candidates were far too large for the budget:

- `tests/test_eval_signal_hasattr_probe.py`: `6903` estimated tokens
- `tests/test_eval_signal_getattr_probe.py`: `2656` estimated tokens
- `tests/test_eval_signal_vars_probe.py`: `2726` estimated tokens
- `tests/test_semantic_optimizer.py`: `12031` estimated tokens

The import-neighborhood baseline seeded from `tests/test_eval_signal_hasattr_probe.py` and `tests/test_eval_signal_getattr_probe.py`, but selected neither file under budget and emitted `import_not_resolved`.

Under this budget, the baselines fail the evidence path. Reaching similar evidence through their candidates would require materially larger and less focused whole-file context.

## Caveats

- Latency is a real caveat: `context_ir` took `108.846s`, while the baselines took about `0.25s`.
- The selected repository code units were rendered as summaries under budget pressure, not full source.
- The compact eval evidence unit is an internal evidence surface, not a selected unsupported runtime-attached source unit.
- `context_ir` emitted `budget_pressure` and `omitted_uncertainty` warnings.
- This supports only Task 0 at budget `220`; it is not evidence for Tasks 1-3 or broad product claims.
- Public claims remain held.

## Evidence Location

The raw reproduced provider records are in `evals/product_differentiation/portfolio_001/runs.jsonl`. Each JSONL row embeds the rendered context in the `document` field and records the selected units/files, token count, elapsed time, warnings, candidate files, omitted candidate files, and lexical score evidence.
