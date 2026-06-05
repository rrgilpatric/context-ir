# Private Reviewer Evidence Packet 001

Classification: internal-only.

Audience: private technical reviewer or control lane. This packet is not public
marketing, public copy, demo copy, or authorization to widen public claims.

## Purpose

This packet explains how to review the current internal evidence toward the
frontier-lab-relevant thesis: Context IR is an in-progress semantic-first
Python context compiler for coding agents that assembles budgeted context from
semantic evidence, explicit unresolved or unsupported boundaries, and additive
runtime provenance where the repo has exact evidence for it.

The reviewer goal is to inspect two complementary evidence bodies without
collapsing their boundaries:

- `portfolio_001`: exact-query product-differentiation evidence for Tasks 0-3.
- `default_local_probe_checkpoint_001`: exact runtime-provenance breadth
  evidence across the current individual non-smoke probe checkpoint.

## One-Page Reading Order

1. Project thesis and boundaries:
   - Start with [README.md](../../../README.md), [EVAL.md](../../../EVAL.md),
     and [PUBLIC_CLAIMS.md](../../../PUBLIC_CLAIMS.md).
   - Confirm the core project shape: semantic-first Python context assembly,
     supported static subset, explicit unresolved or unsupported frontier,
     internal eval evidence, and no public benchmark or production-readiness
     claim.
2. Product-differentiation evidence:
   - Read [portfolio_001_internal_readiness.md](portfolio_001_internal_readiness.md)
     first.
   - Then read [portfolio_001/README.md](../portfolio_001/README.md) and
     [portfolio_001/evidence.md](../portfolio_001/evidence.md).
   - Use [portfolio_001/manifest.json](../portfolio_001/manifest.json) and
     [portfolio_001/runs.jsonl](../portfolio_001/runs.jsonl) only after the
     human-readable summaries establish the exact task and budget boundaries.
3. Runtime-provenance breadth evidence:
   - Read
     [default_local_probe_checkpoint_001/reviewer_readiness.md](../../internal_runtime_evidence/default_local_probe_checkpoint_001/reviewer_readiness.md)
     and
     [default_local_probe_checkpoint_001/checkpoint.md](../../internal_runtime_evidence/default_local_probe_checkpoint_001/checkpoint.md).
   - Then inspect
     [manifest.json](../../internal_runtime_evidence/default_local_probe_checkpoint_001/manifest.json),
     [report.md](../../internal_runtime_evidence/default_local_probe_checkpoint_001/report.md),
     [ledger.jsonl](../../internal_runtime_evidence/default_local_probe_checkpoint_001/ledger.jsonl),
     and
     [run_spec.json](../../internal_runtime_evidence/default_local_probe_checkpoint_001/run_spec.json).
4. Claim boundaries:
   - Return to [EVAL.md](../../../EVAL.md) and
     [PUBLIC_CLAIMS.md](../../../PUBLIC_CLAIMS.md).
   - Check that every summary remains internal-only unless it is already
     permitted by the public-safe claim envelope.

## Evidence Map

### portfolio_001

- Location: `evals/product_differentiation/portfolio_001/`.
- Scope: internal exact-query evidence for Tasks 0-3.
- Classification: `STRONG` for Task 0 at budget `220`, Task 1 at budget
  `260`, Task 2 at budget `320`, and Task 3 at budget `280`.
- Evidence shape: `context_ir` selected the required semantic evidence paths
  for each exact query and budget, while file-level baselines failed under the
  same budgets or required materially larger whole-file context.
- What it proves: serious internal product-differentiation evidence for exact
  semantic context assembly tasks, including preservation of
  `unsupported/opaque` primary truth and additive runtime evidence where the
  task requires it.
- What it does not prove: broad product proof, production readiness, public
  benchmark quality, SWE-bench relevance, latency/token/cost wins, generalized
  runtime support, or public/demo readiness.
- Reviewer caveat: `context_ir` is materially slower than file-level baselines
  on the recorded full-repo portfolio runs, and selected support may be
  summary-level under budget pressure.

### default_local_probe_checkpoint_001

- Location:
  `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/`.
- Scope: internal exact runtime-provenance evidence for all `31/31`
  individual non-smoke `oracle_signal_*_probe` fixtures in the current queue.
- Provider: exactly `context_ir_default_local_python_subprocess`.
- Budget distribution: `100` x `23`, `180` x `1`, `220` x `7`.
- Budget violations: none.
- Explicit exclusions: composite smoke tasks
  `oracle_signal_smoke`, `oracle_signal_smoke_b`, `oracle_signal_smoke_c`,
  `oracle_signal_smoke_d`, and `oracle_signal_smoke_e`; legacy
  `oracle_smoke`.
- What it proves: exact internal runtime-provenance and normalized payload
  evidence exists for every individual non-smoke probe fixture at its
  provider-valid budget.
- What it does not prove: generalized hybrid-runtime support, composite smoke
  support, broad dynamic-Python support, production readiness, public benchmark
  quality, Task 4 readiness, or latency/token/cost wins.

## Reviewer Checklist

- Verify the artifact files exist:
  - `evals/product_differentiation/portfolio_001/README.md`
  - `evals/product_differentiation/portfolio_001/evidence.md`
  - `evals/product_differentiation/portfolio_001/manifest.json`
  - `evals/product_differentiation/portfolio_001/runs.jsonl`
  - `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/reviewer_readiness.md`
  - `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/checkpoint.md`
  - `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/manifest.json`
  - `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/report.md`
  - `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/ledger.jsonl`
  - `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/run_spec.json`
- Inspect `portfolio_001/manifest.json` for task classifications, budgets,
  provider names under `provider_results[].provider_name`, and artifact
  inventory.
- Inspect `portfolio_001/evidence.md` before raw JSONL to confirm the exact
  query, selected units, baseline failures, and caveats for each task.
- Inspect `portfolio_001/runs.jsonl` only to verify raw provider records,
  rendered context, selected units/files, warnings, token counts, and elapsed
  time behind the summaries.
- Inspect the checkpoint `manifest.json` for `record_count: 31`, provider names,
  budgets, written run IDs, and an empty budget violation list.
- Inspect the checkpoint `run_spec.json` to confirm each case uses only
  `context_ir_default_local_python_subprocess` at the recorded provider-valid
  budget.
- Inspect the checkpoint `report.md` for provider aggregate accounting,
  selector runtime-provenance satisfaction, task budget rows, and budget
  compliance.
- Inspect the checkpoint `ledger.jsonl` to spot-check runtime provenance
  records, normalized payloads, selected unsupported units, and preservation of
  `unsupported/opaque` primary truth.
- Check preservation and boundary claims:
  - Runtime provenance is additive only.
  - Unsupported or frontier surfaces remain unsupported, opaque, or heuristic
    where applicable.
  - Public-safe comparative claims remain bounded to the existing quad matrix.
  - README.md and PUBLIC_CLAIMS.md are not changed by this packet.

## Disallowed Inferences

- No public benchmark quality claim.
- No production readiness claim.
- No SWE-bench claim.
- No broad product proof claim.
- No generalized hybrid-runtime support claim.
- No composite smoke support claim.
- No Task 4 readiness claim.
- No latency/token/cost win claim.
- No public API, MCP, schema, scoring, compiler, optimizer, winner-selection,
  package-export, product launch, or public demo widening.
- No claim that `portfolio_001` and `default_local_probe_checkpoint_001`
  combine into external validation or public evidence.

## Recommended Reviewer Takeaway

The combined evidence is serious internal evidence of semantic context assembly
plus exact runtime-provenance acquisition. It shows that Context IR can assemble
reviewable semantic evidence for exact product-differentiation tasks and can
acquire exact runtime-provenance evidence across the current individual
non-smoke probe checkpoint.

It is not yet a public benchmark, packaged product launch claim, production
readiness claim, SWE-bench claim, generalized hybrid-runtime support claim, or
latency/token/cost win claim.

## Next Possible Reviewer Questions

- Should Task 4 run to add eval-bundle, pipeline, or report reproducibility
  evidence?
- Should composite smoke default-local support be designed as a separate
  strategy rather than inferred from individual probe coverage?
- Should a small private demo or README-style walkthrough be built for trusted
  reviewers, with PUBLIC_CLAIMS.md kept as the controlling public boundary?
