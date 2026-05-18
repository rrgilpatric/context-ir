# Portfolio 001 Product-Differentiation Evidence

## Scope

This bundle is internal-only evidence for two accepted checkpoints:

- Task 0: `Fix _selected_unit_metadata and eval report accounting so unsupported hasattr runtime provenance remains visible in selected unit metadata`
- Task 1: `Fix discover_semantic_eval_runtime_evidence so compact oracle_signal_hasattr_probe evidence renders additive runtime=additive attribute_present=true without becoming public API`

It preserves reproduced provider comparisons for:

- `context_ir`
- `lexical_top_k_files`
- `import_neighborhood_files`

Tasks 2-3 were not run or recorded in this bundle. Task 1's ceiling budget `360` was not run because the primary budget `260` reached `STRONG`.

## Claim Boundary

This bundle supports only narrow internal claims for the recorded Task 0 and Task 1 queries at their recorded budgets. It is internal portfolio evidence, not broad product-level proof, not production-readiness evidence, and not a polished public demo.

Public claims remain held pending separate approval and broader evidence.

## Rubric

`STRONG` means `context_ir` stays within the primary budget and selects every required evidence path while the baselines fail under the same budget or require materially larger, irrelevant whole-file context.

`PARTIAL` means `context_ir` finds the main edit target and most support, but misses concrete runtime evidence, loses uncertainty truth, or only weakly outperforms baselines.

`FAIL` means `context_ir` misses the main edit target, exceeds budget, exposes incorrect primary truth, or the baselines match or beat it under the same budget.

## Caveats

- `context_ir` remains materially slower than the baselines: Task 0 took `108.846s` versus about `0.25s`, and Task 1 took `118.783s` versus about `0.27s`.
- Selected support units include summaries under budget pressure, not always full source.
- The compact `oracle_signal_hasattr_probe` evidence is an internal eval evidence surface. It is not a selected unsupported runtime-attached source unit.
- The evidence keeps `unsupported/opaque` as primary truth and treats `attribute_present=true` as additive runtime evidence.
- Task 1 verifies that package-root `context_ir` does not export `discover_semantic_eval_runtime_evidence`; this is not a public API claim.
- Public claims remain held.

## Files

- `manifest.json`: run metadata, repo state, commands, artifact inventory, and classification.
- `runs.jsonl`: one reproduced provider result record per task, provider, and budget run.
- `evidence.md`: human-readable Task 0 and Task 1 comparisons and classifications.
