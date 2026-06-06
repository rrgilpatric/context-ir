# Portfolio 001 Internal Reviewer Readiness Memo

Classification: internal-only.

Audience: trusted internal reviewer or control lane.

Public claims remain held. This memo is a reviewer readiness aid for
portfolio_001 only. It is not public copy, not broad product proof, not a
portfolio/demo script, and not authorization to widen public claims.

## Bottom Line

portfolio_001 carries internal rubric classifications of STRONG for four exact
maintenance queries at fixed budgets. Read that as a bounded rubric label: for
those exact rows, `context_ir` selected the required semantic evidence paths
while the file-level baselines failed under the same budgets or needed
materially larger whole-file context.

The evidence does not prove generalized product quality, production readiness,
external benchmark performance, latency improvement, token savings, broad
dynamic-Python handling, or public/demo readiness. The primary truth for the
runtime-backed and uncertainty surfaces remains `unsupported/opaque`; runtime
provenance is additive only.

The committed portfolio manifest records Python 3.14.3 as the generation
environment. Project support remains Python 3.11+, so this memo must not be
used as cross-version proof without fresh target-version runs.

## What Portfolio 001 Supports

| Task | Exact query scope | Fixed budget | Internal classification | Evidence to cite |
| --- | --- | ---: | --- | --- |
| Task 0 | `_selected_unit_metadata` and eval report accounting so unsupported `hasattr` runtime provenance remains visible in selected unit metadata. | `220` | STRONG | [README](../portfolio_001/README.md), [evidence.md](../portfolio_001/evidence.md#task-0-query-and-budget), [manifest.json](../portfolio_001/manifest.json), [runs.jsonl](../portfolio_001/runs.jsonl) |
| Task 1 | `discover_semantic_eval_runtime_evidence` renders compact `oracle_signal_hasattr_probe` evidence as additive runtime evidence without becoming public API. | `260` | STRONG | [README](../portfolio_001/README.md), [evidence.md](../portfolio_001/evidence.md#task-1-query-and-budget), [manifest.json](../portfolio_001/manifest.json), [runs.jsonl](../portfolio_001/runs.jsonl) |
| Task 2 | Default local Python subprocess recompile attaches `exec(source)` runtime probe results as additive provenance to unsupported `EXEC_OR_EVAL` units without promoting primary truth. | `320` | STRONG | [README](../portfolio_001/README.md), [evidence.md](../portfolio_001/evidence.md#task-2-query-and-budget), [manifest.json](../portfolio_001/manifest.json), [runs.jsonl](../portfolio_001/runs.jsonl) |
| Task 3 | Transitive sole-provider self-call resolution for `MemberSignalCompiler.compile_member_digest` while preserving the alias-chain frontier on `pkg_alias.labels.build_member_label`. | `280` | STRONG | [README](../portfolio_001/README.md), [evidence.md](../portfolio_001/evidence.md#task-3-query-and-budget), [manifest.json](../portfolio_001/manifest.json), [runs.jsonl](../portfolio_001/runs.jsonl) |

Task 1's ceiling budget `360`, Task 2's ceiling budget, and Task 3's ceiling
budget were not run because their primary budgets already reached the internal
STRONG rubric label. Do not infer ceiling-budget robustness, broader baseline
coverage, or cross-budget product performance from those unrun ceiling rows.

Task 4 is not needed before this artifact, unless a later control decision
needs eval-bundle/pipeline/report reproducibility evidence.

## What Portfolio 001 Does Not Prove

portfolio_001 is exact-query internal evidence, not broad product proof. It
does not support claims that `context_ir` is production-ready, faster than
baselines, externally benchmarked, SWE-bench-relevant, multi-language, or
generally superior across arbitrary coding tasks.

It also does not widen source, runtime, public API, MCP, schema, package export,
scoring, optimizer, compiler, winner-selection, product, public benchmark, or
public demo surfaces. The repo-level public boundary remains the conservative
claim envelope in [PUBLIC_CLAIMS.md](../../../PUBLIC_CLAIMS.md), [README.md](../../../README.md),
and [EVAL.md](../../../EVAL.md).

## Caveats Reviewers Must Preserve

- `unsupported/opaque` remains primary truth.
- Runtime provenance is additive only; it does not turn unsupported or frontier
  behavior into static proof.
- Ceiling-budget rows for Task 1, Task 2, and Task 3 were not run; the primary
  budget rows are readable evidence, not proof of unused budget headroom.
- `context_ir` has a real latency caveat on full-repo portfolio runs: Task 0
  took `108.846s`, Task 1 took `118.783s`, Task 2 took about `129.702s`, and
  Task 3 full-repo took `122.718s`, while full-repo baselines took about
  `0.25s` to `0.28s`.
- Selected support may be summary-level under budget pressure, not always full
  source.
- portfolio_001 is exact-query internal evidence, not broad product proof.
- Public claims remain held pending separate approval and broader evidence.

## How To Cite The Evidence

Use the human-readable bundle files first:

- Cite [portfolio_001/README.md](../portfolio_001/README.md) for scope, claim
  boundary, rubric, caveats, and the held-public-claims statement.
- Cite [portfolio_001/evidence.md](../portfolio_001/evidence.md) for per-task
  provider comparisons, selected units, baseline failure analysis, and caveats.
- Cite [portfolio_001/manifest.json](../portfolio_001/manifest.json) for
  machine-readable classification, budgets, provider metadata, artifact
  inventory, and command provenance.
- Cite [portfolio_001/runs.jsonl](../portfolio_001/runs.jsonl) for raw
  provider records, rendered context, selected units/files, warnings, token
  counts, elapsed time, and omitted candidates.

Use repo-wide boundary files to avoid overclaiming:

- Cite [PUBLIC_CLAIMS.md](../../../PUBLIC_CLAIMS.md) for allowed public
  descriptors and disallowed/held language.
- Cite [README.md](../../../README.md) for current project status, public
  surface, and non-claims.
- Cite [EVAL.md](../../../EVAL.md) for the evidence ledger, methodology
  boundary, unsupported claims, and future eval plan.

## Statement Classification Table

| Proposed statement | Classification | Repo evidence | Reviewer note |
| --- | --- | --- | --- |
| Context IR is an in-progress semantic-first Python context compiler for coding agents over a supported static Python subset. | public-safe | [README.md](../../../README.md), [PUBLIC_CLAIMS.md](../../../PUBLIC_CLAIMS.md), [EVAL.md](../../../EVAL.md) | Safe as a descriptor when kept scoped to the current supported surface. |
| The current public surface is limited to `analyze_repository(...)`, `compile_repository_context(...)`, and a minimal tested MCP compile wrapper. | public-safe | [README.md](../../../README.md), [PUBLIC_CLAIMS.md](../../../PUBLIC_CLAIMS.md), [EVAL.md](../../../EVAL.md) | Do not turn this into a complete product integration claim. |
| The repo contains deterministic internal eval infrastructure and internal evidence artifacts over fixed run specs and ledgers. | public-safe | [README.md](../../../README.md), [PUBLIC_CLAIMS.md](../../../PUBLIC_CLAIMS.md), [EVAL.md](../../../EVAL.md) | Keep the public-safe comparative surface bounded to the existing claim envelope. |
| The portfolio_001 internal rubric records STRONG classifications for Task 0 at budget `220`, Task 1 at budget `260`, Task 2 at budget `320`, and Task 3 at budget `280`. | internal-only | [portfolio_001/README.md](../portfolio_001/README.md), [portfolio_001/evidence.md](../portfolio_001/evidence.md), [portfolio_001/manifest.json](../portfolio_001/manifest.json), [portfolio_001/runs.jsonl](../portfolio_001/runs.jsonl) | This is a bounded internal rubric summary, not product proof. |
| For the exact portfolio_001 queries and budgets, `context_ir` selected required semantic evidence paths while file-level baselines failed under the same budgets or required materially larger whole-file context. | internal-only | [portfolio_001/evidence.md](../portfolio_001/evidence.md), [portfolio_001/manifest.json](../portfolio_001/manifest.json), [portfolio_001/runs.jsonl](../portfolio_001/runs.jsonl) | Cite per-task selected units and baseline failure sections. |
| Task 0 preserved `unsupported/opaque` as primary truth while rendering `oracle_signal_hasattr_probe` runtime provenance as additive evidence. | internal-only | [portfolio_001/evidence.md](../portfolio_001/evidence.md#task-0-selected-context_ir-units), [portfolio_001/runs.jsonl](../portfolio_001/runs.jsonl) | Safe only as internal evidence for this exact query and budget. |
| Task 1 showed compact `oracle_signal_hasattr_probe` evidence rendering and package-root non-export evidence for `discover_semantic_eval_runtime_evidence`. | internal-only | [portfolio_001/evidence.md](../portfolio_001/evidence.md#task-1-selected-context_ir-units), [portfolio_001/manifest.json](../portfolio_001/manifest.json), [portfolio_001/runs.jsonl](../portfolio_001/runs.jsonl) | Not a public API claim. |
| Task 2 showed default local Python subprocess recompile evidence for exact `exec(source)` runtime provenance while keeping unsupported `EXEC_OR_EVAL` primary truth. | internal-only | [portfolio_001/evidence.md](../portfolio_001/evidence.md#task-2-selected-context_ir-units), [portfolio_001/manifest.json](../portfolio_001/manifest.json), [portfolio_001/runs.jsonl](../portfolio_001/runs.jsonl), [EVAL.md](../../../EVAL.md) | Does not imply generalized `exec` or generated-code dependency modeling. |
| Task 3 showed exact `compile_member_digest` support selection plus honest alias-chain frontier evidence at the fixed full-repo and fixture-root budgets. | internal-only | [portfolio_001/evidence.md](../portfolio_001/evidence.md#task-3-full-repo-selected-context_ir-units), [portfolio_001/manifest.json](../portfolio_001/manifest.json), [portfolio_001/runs.jsonl](../portfolio_001/runs.jsonl) | Does not authorize broader resolver, dependency-frontier, public API, or public demo claims. |
| `context_ir` is materially slower than baselines on full-repo portfolio_001 runs. | internal-only | [portfolio_001/README.md](../portfolio_001/README.md), [portfolio_001/evidence.md](../portfolio_001/evidence.md#caveats), [portfolio_001/manifest.json](../portfolio_001/manifest.json) | This latency caveat must travel with the evidence. |
| Selected support may be summary-level under budget pressure. | internal-only | [portfolio_001/README.md](../portfolio_001/README.md), [portfolio_001/evidence.md](../portfolio_001/evidence.md#caveats), [portfolio_001/runs.jsonl](../portfolio_001/runs.jsonl) | Do not imply every selected unit carried full source. |
| Task 4 is not needed before this artifact unless a later control decision needs eval-bundle/pipeline/report reproducibility evidence. | internal-only | [PLAN.md](../../../PLAN.md), [BUILDLOG.md](../../../BUILDLOG.md) | This is a current control-routing decision, not portfolio evidence. |
| Public claims remain held. | internal-only | [portfolio_001/README.md](../portfolio_001/README.md), [portfolio_001/evidence.md](../portfolio_001/evidence.md), [portfolio_001/manifest.json](../portfolio_001/manifest.json), [PUBLIC_CLAIMS.md](../../../PUBLIC_CLAIMS.md), [EVAL.md](../../../EVAL.md) | Required exact wording for reviewers. |
| portfolio_001 proves broad product superiority or broad product proof. | disallowed/held | [portfolio_001/README.md](../portfolio_001/README.md), [portfolio_001/evidence.md](../portfolio_001/evidence.md), [EVAL.md](../../../EVAL.md) | Disallowed. Use exact-query internal evidence language instead. |
| portfolio_001 proves production readiness, external benchmark wins, SWE-bench relevance, resolve-rate improvement, token savings, cost reduction, or latency reduction. | disallowed/held | [README.md](../../../README.md), [PUBLIC_CLAIMS.md](../../../PUBLIC_CLAIMS.md), [EVAL.md](../../../EVAL.md), [portfolio_001/evidence.md](../portfolio_001/evidence.md) | Disallowed. The portfolio evidence includes a latency caveat, not a latency win. |
| Runtime provenance proves generalized hybrid static plus runtime analysis or broad dynamic-Python support. | disallowed/held | [README.md](../../../README.md), [PUBLIC_CLAIMS.md](../../../PUBLIC_CLAIMS.md), [EVAL.md](../../../EVAL.md), [portfolio_001/README.md](../portfolio_001/README.md) | Disallowed. Runtime provenance is additive and scoped to narrow internal evidence. |
| Task 2 proves generalized `exec`, `eval`, generated-code dependency modeling, or namespace mutation handling. | disallowed/held | [EVAL.md](../../../EVAL.md), [portfolio_001/evidence.md](../portfolio_001/evidence.md#task-2-selected-context_ir-units), [portfolio_001/runs.jsonl](../portfolio_001/runs.jsonl) | Disallowed. Task 2 covers exact `exec(source)` portfolio evidence only. |
| Task 3 proves generalized resolver correctness, dependency-frontier correctness, public API readiness, or demo readiness. | disallowed/held | [portfolio_001/README.md](../portfolio_001/README.md), [portfolio_001/evidence.md](../portfolio_001/evidence.md#task-3-baseline-failure-and-overinclude-analysis), [portfolio_001/runs.jsonl](../portfolio_001/runs.jsonl) | Disallowed. Task 3 is exact-query evidence only. |
| portfolio_001 changes public/API/MCP/schema/package-export/scoring/optimizer/compiler/winner-selection/product/public benchmark surfaces. | disallowed/held | [README.md](../../../README.md), [PUBLIC_CLAIMS.md](../../../PUBLIC_CLAIMS.md), [EVAL.md](../../../EVAL.md), [portfolio_001/README.md](../portfolio_001/README.md) | Disallowed. No surface widening is authorized by this evidence. |

## Reviewer Use

Use this memo to check whether a draft internal review, control-lane summary, or
future portfolio note preserves the evidence boundary. The acceptable wording is
exact-query, fixed-budget, internal-only, and caveated. Any stronger wording
belongs in disallowed/held until the control lane approves new evidence and
claim gates.
