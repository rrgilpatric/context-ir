# Portfolio 001 Product-Differentiation Evidence

## Scope

This bundle is internal-only evidence for Task 0:

`Fix _selected_unit_metadata and eval report accounting so unsupported hasattr runtime provenance remains visible in selected unit metadata`

It preserves one reproduced provider comparison at budget `220` for:

- `context_ir`
- `lexical_top_k_files`
- `import_neighborhood_files`

Tasks 1-3 were not run or recorded in this bundle.

## Claim Boundary

This bundle supports only a narrow internal claim: for this specific real-repo Task 0 query and budget, `context_ir` produced materially better task context than the two file-level baselines while preserving truthful uncertainty about unsupported `hasattr` runtime provenance.

This bundle does not prove general product superiority, does not establish production readiness, and is not a polished public demo. Public claims remain held pending separate approval and broader evidence.

## Rubric

`STRONG` means `context_ir` stays within the primary budget and selects every required evidence path while the baselines fail under the same budget or require materially larger, irrelevant whole-file context.

`PARTIAL` means `context_ir` finds the main edit target and most support, but misses concrete runtime evidence, loses uncertainty truth, or only weakly outperforms baselines.

`FAIL` means `context_ir` misses the main edit target, exceeds budget, exposes incorrect primary truth, or the baselines match or beat it under the same budget.

## Caveats

- The `context_ir` run was much slower than the baselines: `108.846s` versus about `0.25s`.
- The selected repository units are rendered as summaries under budget pressure, not full source.
- The compact `oracle_signal_hasattr_probe` evidence is an internal eval evidence surface. It is not a selected unsupported runtime-attached source unit.
- The evidence keeps `unsupported/opaque` as primary truth and treats `attribute_present=true` as additive runtime evidence.
- Public claims remain held.

## Files

- `manifest.json`: run metadata, repo state, commands, artifact inventory, and classification.
- `runs.jsonl`: one reproduced provider result record per provider.
- `evidence.md`: human-readable Task 0 comparison and classification.
