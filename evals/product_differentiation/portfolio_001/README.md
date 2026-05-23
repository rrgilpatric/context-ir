# Portfolio 001 Product-Differentiation Evidence

## Scope

This bundle is internal-only evidence for four accepted checkpoints:

- Task 0: `Fix _selected_unit_metadata and eval report accounting so unsupported hasattr runtime provenance remains visible in selected unit metadata`
- Task 1: `Fix discover_semantic_eval_runtime_evidence so compact oracle_signal_hasattr_probe evidence renders additive runtime=additive attribute_present=true without becoming public API`
- Task 2: `Fix default local Python subprocess recompile so exec(source) runtime probe results attach additive provenance to unsupported EXEC_OR_EVAL units without promoting primary truth`
- Task 3: `Fix transitive sole-provider self-call resolution for MemberSignalCompiler.compile_member_digest while preserving alias_chain frontier on pkg_alias.labels.build_member_label`

It preserves reproduced provider comparisons for:

- `context_ir`
- `lexical_top_k_files`
- `import_neighborhood_files`

Task 1's ceiling budget `360`, Task 2's ceiling budget, and Task 3's ceiling budget were not run because their primary budgets reached `STRONG`.

Task 0 has been refreshed/superseded against current exact provider output. The refresh preserves the original `STRONG` internal-only classification under the original semantic rubric; it is not broad product proof and does not authorize public or demo claims.

## Claim Boundary

This bundle supports only narrow internal claims for the recorded Task 0, Task 1, Task 2, and Task 3 queries at their recorded budgets. It is internal portfolio evidence, not broad product-level proof, not production-readiness evidence, and not a polished public demo.

Public claims remain held pending separate approval and broader evidence.

## Rubric

`STRONG` means `context_ir` stays within the primary budget and selects every required evidence path while the baselines fail under the same budget or require materially larger, irrelevant whole-file context.

`PARTIAL` means `context_ir` finds the main edit target and most support, but misses concrete runtime evidence, loses uncertainty truth, or only weakly outperforms baselines.

`FAIL` means `context_ir` misses the main edit target, exceeds budget, exposes incorrect primary truth, or the baselines match or beat it under the same budget.

## Caveats

- `context_ir` remains materially slower than the baselines on full-repo runs: the refreshed Task 0 provider run took `7.593s` versus `0.315s` and `0.279s` for the baselines, Task 1 took `118.783s` versus about `0.27s`, Task 2 took about `129.702s` versus about `0.27s`, and Task 3 full-repo took `122.718s` versus about `0.27s`.
- Selected support units include summaries under budget pressure, not always full source.
- The compact `oracle_signal_hasattr_probe` evidence is an internal eval evidence surface. It is not a selected unsupported runtime-attached source unit.
- The evidence keeps `unsupported/opaque` as primary truth and treats `attribute_present=true` as additive runtime evidence.
- The compact `oracle_signal_exec_probe` evidence is internal-only evidence that keeps `unsupported/opaque` as primary truth and treats `execution_outcome=completed` and `statement_kind=pass` as additive runtime evidence.
- Task 3 verifies the exact alias-chain uncertainty waypoint as internal evidence; it does not authorize broader resolver, dependency-frontier, public API, or public demo claims.
- Task 1 verifies that package-root `context_ir` does not export `discover_semantic_eval_runtime_evidence`; this is not a public API claim.
- Public claims remain held.

## Files

- `manifest.json`: run metadata, repo state, commands, artifact inventory, and classification.
- `runs.jsonl`: one reproduced provider result record per task, provider, and budget run.
- `evidence.md`: human-readable Task 0, Task 1, Task 2, and Task 3 comparisons and classifications.
