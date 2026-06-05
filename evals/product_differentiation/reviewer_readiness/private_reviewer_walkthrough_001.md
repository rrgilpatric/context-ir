# Private Reviewer Walkthrough 001

Classification: internal-only.

Audience: private technical reviewer.

Time box: 5-10 minutes.

## Boundaries First

This walkthrough is a fast guided path through existing committed internal
reviewer evidence. It does not widen public claims.

Do not infer:

- no public benchmark quality claim
- no production readiness claim
- no SWE-bench claim
- no broad product proof claim
- no generalized hybrid-runtime or dynamic-Python support claim
- no composite smoke support claim
- no Task 4 readiness claim
- no latency/token/cost win claim
- no public API/MCP/schema/scoring/compiler/optimizer/winner-selection/package-export/product launch/public demo widening

The intended takeaway is narrower: `portfolio_001` is exact-query internal
product-differentiation evidence for Tasks 0-3, and
`default_local_probe_checkpoint_001` is exact runtime-provenance breadth
evidence for `31/31` individual non-smoke probe fixtures under the committed
provider `context_ir_default_local_python_subprocess`.

## Reading Path

1. Read
   [private_reviewer_packet_001.md](private_reviewer_packet_001.md).
   Use it as the boundary map for the two evidence bodies.
2. Read
   [portfolio_001_internal_readiness.md](portfolio_001_internal_readiness.md).
   Use it to understand the exact Task 0-3 queries, budgets,
   classifications, and caveats.
3. Read
   [default_local_probe_checkpoint_001/reviewer_readiness.md](../../internal_runtime_evidence/default_local_probe_checkpoint_001/reviewer_readiness.md).
   Use it to confirm the runtime-provenance checkpoint scope and exclusions.
4. Run or inspect the read-only command transcript below. The commands read
   committed artifacts only; they do not execute eval tasks, regenerate
   evidence, start an MCP server, edit files, or change repo state.

## Read-Only CLI Transcript

Run from the repo root.

### 1. Portfolio Claim Boundary

```bash
jq -r '.classification.claim_boundary, (.classification.task_classifications[] | "\(.task_label): \(.value), budget=\(.budget)")' evals/product_differentiation/portfolio_001/manifest.json
```

Expected output:

```text
Internal-only refreshed/superseded evidence for Task 0 under budget 220, Task 1 under primary budget 260, Task 2 under primary budget 320, and Task 3 under primary budget 280; public claims remain held.
Task 0: STRONG, budget=220
Task 1: STRONG, budget=260
Task 2: STRONG, budget=320
Task 3: STRONG, budget=280
```

This proves the committed manifest classifies Tasks 0-3 as internal-only
STRONG evidence at fixed budgets.

It does not prove broad product proof, public benchmark quality, production
readiness, SWE-bench relevance, Task 4 readiness, or any public claim widening.

### 2. Portfolio Context IR Rows

```bash
jq -s '[.[] | select(.provider_name == "context_ir") | {task_id, budget, total_tokens, selected_units: ((.selected_unit_ids // []) | length), selected_files: ((.selected_files // []) | length), warnings}]' evals/product_differentiation/portfolio_001/runs.jsonl
```

Expected output summary:

```text
portfolio_001_task_0: budget 220, total_tokens 218, selected_units 7, selected_files 0
portfolio_001_task_1: budget 260, total_tokens 247, selected_units 5, selected_files 0
portfolio_001_task_2: budget 320, total_tokens 317, selected_units 7, selected_files 0
portfolio_001_task_3 full-repo row: budget 280, total_tokens 274, selected_units 4, selected_files 0
portfolio_001_task_3 fixture-root row: budget 280, total_tokens 223, selected_units 5, selected_files 0
```

Warnings are present on the full-repo rows. They are part of the evidence and
must not be hidden; they preserve budget-pressure and omitted-uncertainty
caveats.

This proves the committed raw portfolio records contain context-ir rows with
fixed budgets, token totals, selected semantic unit counts, and warnings.

It does not prove that every selected unit is full source, that warnings are
irrelevant, that baselines were exhaustively evaluated beyond this portfolio,
or that there is a latency/token/cost win.

### 3. Runtime Checkpoint Manifest

```bash
jq '{record_count, provider_names, budgets, budget_violation_run_ids, case_count: (.case_record_counts | length)}' evals/internal_runtime_evidence/default_local_probe_checkpoint_001/manifest.json
```

Expected output:

```json
{
  "record_count": 31,
  "provider_names": [
    "context_ir_default_local_python_subprocess"
  ],
  "budgets": [
    100,
    180,
    220
  ],
  "budget_violation_run_ids": [],
  "case_count": 31
}
```

This proves the checkpoint manifest records 31 cases, one provider, three
provider-valid budgets, and no budget violations.

It does not prove composite smoke support, generalized hybrid-runtime support,
dynamic-Python support, Task 4 readiness, production readiness, or public
benchmark quality.

### 4. Runtime Checkpoint Ledger Count

```bash
jq -s '{rows: length, providers: ([.[].provider_name] | unique), runtime_rows: ([.[] | select((.runtime_provenance_records | length) > 0)] | length)}' evals/internal_runtime_evidence/default_local_probe_checkpoint_001/ledger.jsonl
```

Expected output:

```json
{
  "rows": 31,
  "providers": [
    "context_ir_default_local_python_subprocess"
  ],
  "runtime_rows": 31
}
```

This proves every committed checkpoint ledger row has at least one runtime
provenance record and that the provider set is exactly the default-local
subprocess provider.

It does not prove the checkpoint includes composite smoke tasks, legacy
`oracle_smoke`, broad product proof, or public demo readiness.

### 5. Runtime Payload Spot Check

```bash
jq -s '[.[] | select(.task_id | IN("oracle_signal_hasattr_probe", "oracle_signal_hasattr_false_probe", "oracle_signal_dynamic_import_root_probe", "oracle_signal_exec_probe")) | {task_id, budget, provider_name, runtime_records: (.runtime_provenance_records | length), payloads: [.runtime_provenance_records[].normalized_payload]}]' evals/internal_runtime_evidence/default_local_probe_checkpoint_001/ledger.jsonl
```

Expected output summary:

```text
The four matching rows include:
- oracle_signal_hasattr_probe at budget 100 with attribute_present=true payloads
- oracle_signal_hasattr_false_probe at budget 100 with attribute_present=false payloads
- oracle_signal_dynamic_import_root_probe at budget 220 with imported_module=plugins.weather payloads
- oracle_signal_exec_probe at budget 100 with execution_outcome=completed and statement_kind=pass payloads
Each shown row uses provider context_ir_default_local_python_subprocess and has runtime_records=2.
```

This proves representative committed ledger rows expose normalized runtime
payloads for reflective builtins, dynamic import, and exec from committed
artifacts.

It does not prove generalized dynamic-Python support, generalized dynamic
import support, broad hybrid runtime support, or support for unsupported
program shapes outside these fixtures.

## Optional Tool Facade Feel

If the reviewer asks what the evidence would feel like from a tool-facing
surface, keep the answer high level and artifact-backed:

- `portfolio_001` Task 2 selected existing tool-facade and runtime-observation
  recompile path units while preserving `exec(source)` primary truth as
  `unsupported/opaque` and runtime evidence as additive.
- Repo boundary docs already describe an accepted
  `compile_repository_context(...)` facade and a minimal tested MCP compile
  wrapper, but this walkthrough does not center MCP and does not require
  running an MCP server.

Use this only as an orientation aid. It is not an MCP implementation
walkthrough, public API widening, product launch proof, or public demo.

## Next Possible Reviewer Questions

- What Task 4 reproducibility evidence would be needed before claiming
  eval-bundle, pipeline, or report reproducibility?
- What is the right default-local strategy for composite smoke tasks, given
  that individual probe coverage must not be treated as composite smoke
  support?
- Should this private demo/readme walkthrough evolve into a small runnable
  demo, and what claim gates would keep that demo internal and bounded?
