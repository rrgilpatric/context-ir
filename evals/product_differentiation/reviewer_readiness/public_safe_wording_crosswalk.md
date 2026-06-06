# Public-Safe Wording Crosswalk

Classification: internal-only / non-public.

Purpose: candidate public-safe wording crosswalk for reviewer and control-lane
use. This is not publication copy, not demo copy, not a public claim update,
and not authorization to change `PUBLIC_CLAIMS.md`, `README.md`, `EVAL.md`, or
any `portfolio_001` artifact.

## Ground Rules

- Treat every public-safe candidate as draft language only. A later control
  lane must still decide whether to use, edit, or discard it.
- Every public-safe candidate below maps only to `PUBLIC_CLAIMS.md`,
  `README.md`, or `EVAL.md`.
- `portfolio_001` is not public proof. It may appear only as internal-only or
  held context for reviewer readiness.
- Do not use `portfolio_001` to support public wording, benchmark claims,
  production-readiness claims, latency claims, token-savings claims,
  generalized runtime claims, broad product superiority claims, or
  demo-readiness claims.
- Keep replay/comparative matrix evidence separate from default-local
  subprocess checkpoint evidence. Do not combine them into public benchmark,
  public product, or generalized runtime-support wording.
- Some committed internal evidence artifacts record Python 3.14.3 as the
  generation environment while project support remains Python 3.11+. Do not
  use those artifacts for cross-version public wording without fresh
  target-version runs.
- Keep Task 4 held. Task 4 is only relevant if a later control decision targets
  eval-bundle, report, or pipeline reproducibility claims.

## Reviewer Risks To Preserve

- P3: raw `runs.jsonl` evidence is dense and non-uniform, so reviewers should
  start from the internal memo and `portfolio_001/evidence.md` rather than raw
  JSONL.
- P3: baseline comparisons must not be framed as broad benchmark or performance
  claims. If baseline language is used internally, keep it exact-query,
  fixed-budget, and caveated.

## Candidate Public-Safe Statements

| Candidate sentence | Classification | Allowed source mapping | Boundary note |
| --- | --- | --- | --- |
| Context IR is an in-progress semantic-first Python context compiler for coding agents. | public-safe candidate | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | Keep "in-progress" and "semantic-first"; do not imply production-readiness. |
| Context IR analyzes a supported static Python subset into a `SemanticProgram`, derives proven dependencies plus explicit unresolved or unsupported frontier, and compiles budgeted context. | public-safe candidate | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | Preserve "supported static Python subset"; do not collapse to broad Python support. |
| The current public surface is limited to `analyze_repository(...)`, `compile_repository_context(...)`, and a minimal stdio MCP wrapper around one tested compile tool. | public-safe candidate | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | Do not imply a complete MCP product integration or broader API surface. |
| The repo contains deterministic internal eval infrastructure with summary, report, pipeline, manifest, bundle, and JSONL ledger artifacts over fixed run specs. | public-safe candidate | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | This describes infrastructure, not external validation or product readiness. |
| Current evidence distinguishes proven semantic dependencies from unresolved frontier items, unsupported constructs, heuristic ranking candidates, and additive runtime-backed internal evidence. | public-safe candidate | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | Do not turn additive runtime evidence into generalized runtime support. |
| The public-safe comparative boundary remains the fixed internal quad matrix described in the repo evidence ledger. | public-safe candidate | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | If used, keep "internal" and "fixed"; do not describe it as an external benchmark. |

## Internal-Only Context

| Statement | Classification | Internal source context | Boundary note |
| --- | --- | --- | --- |
| `portfolio_001` is internal-only exact-query evidence for Tasks 0-3 at their recorded budgets. | internal-only context | `evals/product_differentiation/portfolio_001/README.md`; `evals/product_differentiation/portfolio_001/evidence.md`; `evals/product_differentiation/reviewer_readiness/portfolio_001_internal_readiness.md` | Not public proof and not a public claim source. |
| The reviewer readiness memo is suitable as the starting point for trusted internal reviewers before raw `runs.jsonl`. | internal-only context | `evals/product_differentiation/reviewer_readiness/portfolio_001_internal_readiness.md`; `evals/product_differentiation/portfolio_001/evidence.md` | Preserves the P3 raw-ledger readability risk. |
| The portfolio baseline comparisons are useful only as exact-query, fixed-budget internal evidence with latency caveats. | internal-only context | `evals/product_differentiation/portfolio_001/README.md`; `evals/product_differentiation/portfolio_001/evidence.md`; reviewer readiness memo | Must not become broad benchmark, latency, or performance wording. |
| `default_local_probe_checkpoint_001` is internal default-local subprocess runtime-provenance checkpoint evidence for individual non-smoke probes. | internal-only context | `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/reviewer_readiness.md`; `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/checkpoint.md`; `EVAL.md` | Separate from replay/comparative matrices; not public benchmark or cross-version proof. |
| Task 4 remains held for now. | internal-only context | `PLAN.md`; `BUILDLOG.md` | Only relevant if eval-bundle/report/pipeline reproducibility claims become the target. |

## Disallowed Or Held Wording

| Wording pattern | Classification | Source boundary | Why held |
| --- | --- | --- | --- |
| Context IR is a benchmark winner, state of the art, or externally benchmarked. | disallowed/held | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | The source boundary rejects external benchmark and benchmark-leadership framing. |
| Context IR is production ready, deployment ready, or enterprise ready. | disallowed/held | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | The source boundary does not make production-readiness claims. |
| Context IR reduces latency, improves latency, or is faster than baselines. | disallowed/held | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md`; internal-only `portfolio_001` context | `portfolio_001` records a latency caveat, not a latency win, and public latency claims are not authorized. |
| Context IR provides token-savings, cost savings, or generalized efficiency gains. | disallowed/held | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | Token-savings and cost-reduction wording is outside the current public claim envelope. |
| Context IR has generalized runtime, hybrid-runtime, dynamic-import, reflection, `exec`, `eval`, monkey-patching, metaclass, or runtime-mutation support. | disallowed/held | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | Runtime-backed evidence is narrow, internal, and additive; it does not widen the public supported subset. |
| Python 3.14.3-generated committed evidence proves Python-version-general behavior. | disallowed/held | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md`; internal-only evidence artifacts | Project support remains Python 3.11+, but cross-version evidence needs fresh target-version runs. |
| `portfolio_001` proves broad product superiority or broad product proof. | disallowed/held | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md`; internal-only `portfolio_001` context | `portfolio_001` is exact-query internal evidence and not public proof. |
| `portfolio_001` is a public demo, polished demo script, or demo-readiness proof. | disallowed/held | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md`; internal-only `portfolio_001` context | Public/demo claims remain held. |
| Task 4 must run before this crosswalk can exist. | disallowed/held | `PLAN.md`; `BUILDLOG.md` | Current control routing keeps Task 4 held unless eval-bundle/report/pipeline reproducibility claims become the target. |

## Needs More Evidence

| Possible future statement | Classification | Current source boundary | Evidence needed |
| --- | --- | --- | --- |
| Context IR improves outcomes on public coding-agent benchmarks. | needs-more-evidence | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | Public benchmark methodology, reproducible raw results, and approved public reporting. |
| Context IR is ready for production use. | needs-more-evidence | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | Packaging, compatibility, interoperability, error handling, CI/release, observability, and user-facing maturity evidence. |
| Context IR saves tokens, lowers cost, or improves latency for real workflows. | needs-more-evidence | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | Measured timing, token, output-size, and cost data under approved methodology. |
| Context IR supports broad Python runtime behavior. | needs-more-evidence | `PUBLIC_CLAIMS.md`; `README.md`; `EVAL.md` | Broader runtime-family coverage with claim gates that preserve primary truth and public API boundaries. |

## Use Guidance

Use only the public-safe candidate rows as inputs to later public wording
planning, and keep their source mapping intact. Use internal-only rows to brief
trusted reviewers about why `portfolio_001` is held context and not public
proof. Treat disallowed/held and needs-more-evidence rows as stop signs until
the control lane authorizes a new evidence target.
