# PLAN.md -- Context IR Build Plan

## Project

Context IR is a semantically grounded Python context compiler for coding agents. The system is being rebuilt to analyze a supported static subset of a repository, derive proved dependencies plus explicit uncertainty, and only then rank, optimize, and compile context under a budget.

## Current Authority

The April 13 frozen spec is retired and superseded. It remains part of the historical record in BUILDLOG.md, but it is no longer the governing contract for sequencing, acceptance, public positioning, or roadmap control.

### Semantic-First Baseline

- This accepted milestone is the phase 0 foundation for the next program
- Public low-level API: `analyze_repository(repo_root) -> SemanticProgram`
- Mandatory build order: syntax extraction -> semantic contracts and types -> binder and scope model -> resolver and object model -> semantic dependency/frontier derivation -> renderer -> ranking -> optimization -> compilation -> diagnose/recompile
- `p_edit` and `p_support` remain allowed as internal ranking policy after semantic analysis, but they are not the public thesis
- Multi-tier representation remains in scope, but the exact tier count and semantics are not frozen during the rebaseline
- `@dataclass` is in the first supported decorator set, scoped narrowly and explicitly
- If the analyzer cannot prove a semantic fact within the supported subset, it must emit uncertainty or unknown state rather than fabricate a dependency claim

### Capability-Tier North Star

- The new post-milestone program targets broad Python repo coverage through hybrid static + runtime analysis
- The phase 0 foundation remains closed and authoritative for current claims, regression anchors, and reviewer-facing artifacts
- Each capability tier must stay separate from representation tiers:
  - capability tier describes how a fact or unit is justified
  - representation tiers describe how densely a selected unit is rendered
- The future program must keep statically proved, runtime-backed, heuristic/frontier, and unsupported/opaque surfaces explicitly separate
- External benchmark leadership remains contingent on reproducible public methodology and raw results
- Production maturity remains contingent on packaging, compatibility, interoperability, error handling, CI/release evidence, and observability

### Superseded Baseline

- The prior symbol-graph-first frozen spec is retired
- The prior Slice 1 -> Slice 6 correction chain is retired
- Historical retrospective findings still stand as evidence for why the reset was required
- The old `recompile` contract issue is subsumed by the rebaseline and must not be treated as the main control problem anymore

## Current Phase

### Canonical Active Release-State Block

Current pushed source/contract release authority is
`0a3c4c6 Add local Python worker stdin transport`. Live git refs and
worktree state must still be verified from git during control intake; do not
infer them from committed prose.

Local Python worker request stdin transport contract release:

- `RuntimeProbeLocalPythonWorkerRequestStdinTransport` is a frozen
  module-local request handoff contract for the exact text future local-Python
  worker subprocesses receive over stdin
- transports materialize from typed
  `RuntimeProbeLocalPythonSubprocessInvocation` values after revalidating the
  invocation
- materialization internally derives
  `RuntimeProbeLocalPythonWorkerRequestPayload`, serializes it through the
  deterministic strict JSON helper, and parses it back through the strict
  parser as a drift check
- transports preserve invocation identity, the typed payload, deterministic
  stdin text, argv, working directory, ordered Python path entries, timeout
  seconds, request identity, family/form labels, replay seeds, and ordered
  replay payload fields
- direct construction rejects invocation/payload/stdin-text drift, malformed
  stdin text, blank or unsupported transport revision, extra trailing newline
  drift, and attempts to bypass strict payload validation
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not add `subprocess.run(input=...)`, executor behavior
  changes, handler adapter changes, worker modules, concrete family/form
  semantics, temp files, filesystem IO, stdout protocol changes,
  `RuntimeProbeObservedResult` synthesis, result assembly changes, admission,
  recompile, facade, MCP, package-root, schema, eval, scoring, optimizer,
  compiler, docs, or public claims
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1047 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `0a3c4c6 Add local Python worker stdin transport`
- Ryan-authorized push completed with release routing through
  `9a25fbf Sync local Python stdin transport release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `0a3c4c6`

Local Python worker request payload contract release:

- `RuntimeProbeLocalPythonWorkerRequestPayload` is a frozen module-local strict
  JSON request payload contract for future local-Python subprocess worker
  modules
- payloads materialize from typed
  `RuntimeProbeLocalPythonSubprocessInvocation` values after revalidating the
  invocation and carried `RuntimeProbeRunnerRequest`
- payloads preserve request identity, family/form, source-site identity,
  boundary text, reason code, replay target and selector seeds, request replay
  payload fields, runtime assumptions, runner environment, runner assumptions,
  runner contract revision, invocation contract revision, invocation identity,
  argv, working directory, ordered Python path entries, and timeout seconds
- request replay fields must contain exactly one required request identity key,
  including source-site identity, source span, `reason_code`, and
  `boundary_text`
- deterministic strict JSON serialization and parsing helpers reject malformed
  JSON, duplicate JSON keys, non-object payloads, missing or unknown top-level
  keys, invalid enum labels, invalid replay fields, missing required replay
  identity fields, and invocation/payload drift
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not add filesystem IO, stdin/stdout transport wiring,
  subprocess behavior changes, temp files, worker modules, concrete family/form
  semantics, global dispatch registration, `RuntimeProbeObservedResult`
  synthesis, result assembly changes, admission, recompile, facade, MCP,
  package-root, schema, eval, scoring, optimizer, compiler, docs, or public
  claims
- implementation review accepted the slice after two correction passes
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1033 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `4d155ec Add local Python worker payload contract`
- Ryan-authorized push completed with release routing through
  `20d8af3 Sync local Python worker payload release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `4d155ec`

Local Python runner handler adapter release:

- `RuntimeProbeLocalPythonSubprocessHandlerConfig` is a frozen module-local
  handler metadata contract for local-Python subprocess workers
- `make_runtime_probe_local_python_subprocess_handler_entry(...)` returns a
  dispatch-consumable `RuntimeProbeRunnerHandlerEntry`
- configured metadata includes family label, form label, Python executable,
  module name, invocation contract revision, completion contract revision, and
  optional module argv
- produced handlers revalidate runner requests and reject family/form drift
  before subprocess execution
- handlers materialize invocations through existing
  `materialize_runtime_probe_local_python_subprocess_invocation(...)`
- handlers execute and normalize attempts through existing
  `execute_runtime_probe_local_python_subprocess_invocation_attempt(...)`
- module argv order is preserved in the shell-free invocation argv
- success, nonzero, timeout, generic exception, and malformed stdout paths
  continue to flow through existing typed local-Python attempt materializers
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not add concrete family/form probe logic, worker modules,
  global dispatch registration, request payload transport, temp-file or stdin
  IO, `RuntimeProbeObservedResult` synthesis, result assembly changes,
  admission, recompile, facade, MCP, package-root, schema, eval, scoring,
  optimizer, compiler, docs, or public claims
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `1009 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `9b9b5cd Add local Python probe handler adapter`
- Ryan-authorized push completed with release routing through
  `2f63f7f Sync local Python handler adapter release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `9b9b5cd`

Local Python executor-to-attempt wrapper release:

- `execute_runtime_probe_local_python_subprocess_invocation_attempt(...)` is a
  module-local helper that consumes typed
  `RuntimeProbeLocalPythonSubprocessInvocation` values plus
  `completion_contract_revision`
- the helper revalidates invocation and completion revision before subprocess
  launch
- execution flows through existing
  `execute_runtime_probe_local_python_subprocess_invocation(...)`
- subprocess timeouts and generic subprocess exceptions map through
  `materialize_runtime_probe_local_python_subprocess_exception_attempt(...)`
- nonzero completions map through
  `materialize_runtime_probe_local_python_process_completion_attempt(...)`
- zero-returncode valid stdout protocol maps through
  `materialize_runtime_probe_local_python_stdout_protocol_result(...)` and
  `materialize_runtime_probe_local_python_stdout_protocol_attempt(...)`
- zero-returncode malformed stdout protocol maps through
  `materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(...)`
- observed success preserves runner request identity, request object,
  execution input, ordered normalized payload, and durable artifact reference
- failure attempts remain non-proof and sanitized without raw stdout, stderr,
  exception message, traceback text, temporary paths, PIDs, or process-local
  data
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not add concrete family/form handlers, dispatch
  registration, `RuntimeProbeObservedResult` synthesis, result assembly
  changes, admission, recompile, facade, MCP, package-root, schema, eval,
  scoring, optimizer, compiler, docs, or public claims
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `999 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `8625186 Execute local Python subprocess attempts`
- Ryan-authorized push completed with release routing through
  `cd103ae Sync local Python executor attempt release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `8625186`

Local Python stdout protocol failure-normalization release:

- `materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(...)`
  is a module-local helper that consumes typed
  `RuntimeProbeLocalPythonProcessCompletion` values plus a parsing or
  validation `Exception`
- the helper requires zero return code at this boundary; nonzero completion
  mapping remains owned by
  `materialize_runtime_probe_local_python_process_completion_attempt(...)`
- the helper revalidates completion, invocation, and runner request before
  materializing the attempt
- the helper returns non-proof `RuntimeProbeExecutionAttempt` values,
  defaulting to `RuntimeProbeResultOutcome.SETUP_FAILED`
- configured non-proof outcomes are supported and `OBSERVED` is rejected
- runner request identity, request object, and execution input are preserved
- failure summary/detail fields are deterministic and sanitized without raw
  stdout, stderr, exception message, traceback text, temporary paths, PIDs, or
  process-local data
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not change stdout protocol parsing, observed-attempt
  materialization, subprocess execution, nonzero completion mapping, executor
  wrapper orchestration, concrete family/form handlers, dispatch registration,
  `RuntimeProbeObservedResult` synthesis, result assembly, admission,
  recompile, facade, MCP, package-root, schema, eval, scoring, optimizer,
  compiler, docs, or public claims
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `993 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `d8cf97b Normalize local Python stdout protocol failures`
- Ryan-authorized push completed with release routing through
  `d5de659 Sync local Python stdout failure release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `d8cf97b`

Local Python stdout protocol observed-attempt materialization release:

- `materialize_runtime_probe_local_python_stdout_protocol_attempt(...)` is a
  module-local helper that consumes typed
  `RuntimeProbeLocalPythonStdoutProtocolResult` values
- the helper revalidates the stdout protocol result, carried completion,
  subprocess invocation, and runner request before materializing the attempt
- the helper returns `RuntimeProbeExecutionAttempt` with
  `RuntimeProbeResultOutcome.OBSERVED`
- runner request identity, request object, execution input, ordered normalized
  payload, and durable artifact reference are preserved
- observed attempts produced by this helper carry no failure summary or failure
  detail fields
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not change subprocess execution, stdout parsing, non-proof
  failure mapping, `RuntimeProbeObservedResult` synthesis, result-batch
  assembly, concrete family/form handlers, dispatch registration, executor
  wrapper orchestration, admission, recompile, facade, MCP, package-root,
  schema, eval, scoring, optimizer, compiler, docs, or public claims
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `985 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `81a3ce3 Materialize local Python observed attempts`
- Ryan-authorized push completed with release routing through
  `cc5ca86 Sync local Python observed attempt release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `81a3ce3`

Local Python stdout/result protocol contract release:

- `RuntimeProbeLocalPythonStdoutProtocolResult` is a frozen module-local
  contract for strict internal local-Python stdout success metadata
- `materialize_runtime_probe_local_python_stdout_protocol_result(...)`
  consumes typed `RuntimeProbeLocalPythonProcessCompletion` values only
- the materializer requires zero return code before parsing stdout success
  metadata
- stdout is parsed as a strict internal JSON object with explicit stdout
  protocol revision, ordered `normalized_payload`, and optional
  `durable_artifact_reference`
- at least one proof channel is required: normalized payload or durable
  artifact reference
- normalized payload order and the carried completion object are preserved
- completion, invocation, and runner-request contracts are revalidated before
  accepting protocol data
- malformed JSON, non-object JSON, missing/blank/unsupported protocol
  revision, unknown top-level keys, malformed payload entries, blank replay
  fields, malformed durable references, empty proof metadata, nonzero
  completions, and request/completion drift are rejected
- both parser and direct frozen-contract construction reject malformed durable
  references
- exports stay module-local through
  `context_ir.runtime_probe_execution.__all__`; package-root exports remain
  unchanged
- the release does not synthesize `RuntimeProbeExecutionAttempt` values,
  synthesize observed results, implement concrete family/form handlers,
  register dispatch handlers, add executor wrapper orchestration, or change
  admission, recompile, facade, MCP, package-root, schema, eval, scoring,
  optimizer, compiler, docs, or public claims
- implementation review accepted the slice after one durable-reference
  validation correction
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `982 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `0c4a654 Add local Python stdout protocol contract`
- Ryan-authorized push completed with release routing through
  `d0e9b89 Sync local Python stdout protocol release routing` and post-push
  state through `9277d2b Sync local Python stdout protocol post-push state`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `0c4a654`

Local Python subprocess non-proof attempt normalization release:

- module-local helpers convert local Python subprocess failure facts into typed
  non-proof `RuntimeProbeExecutionAttempt` values
- `subprocess.TimeoutExpired` maps to `TIMED_OUT`
- other local subprocess execution exceptions map to sanitized `CRASHED`
  attempts
- nonzero `RuntimeProbeLocalPythonProcessCompletion.returncode` maps to a
  non-proof attempt, defaulting to `CRASHED`
- configured non-proof outcomes for nonzero completions are supported
- `RuntimeProbeResultOutcome.OBSERVED` is rejected at this helper boundary
- zero-returncode completions reject as deferred
- invocation and completion contracts are revalidated before attempt
  materialization
- produced attempts preserve runner request, request object, and execution
  input identity, and intentionally do not carry invocation or completion
  object identity
- failure summary/detail fields are deterministic and do not leak raw stdout,
  stderr, traceback text, temporary paths, PIDs, or process-local data
- raw executor behavior remains unchanged and still returns raw completions
  while propagating subprocess exceptions
- the release does not parse stdout/stderr, synthesize observed results,
  implement family/form handlers, register handlers, or change admission,
  recompile, facade, MCP, package-root, schema, eval, scoring, optimizer,
  compiler, docs, or public claims
- implementation review accepted the slice after one implementation correction
  and one continuity/spec correction
- combined read-only release gate rerun passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `961 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `5b10728 Normalize local Python subprocess failures`
- Ryan-authorized push completed with `origin/main` advanced through
  `c471fd1 Sync local Python failure normalization release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `5b10728`

Local Python raw subprocess execution boundary release:

- `execute_runtime_probe_local_python_subprocess_invocation(...)` is a
  module-local executor that consumes a validated
  `RuntimeProbeLocalPythonSubprocessInvocation`
- the executor validates `completion_contract_revision` before subprocess
  execution and rejects invalid revision metadata before any child process can
  launch
- execution uses shell-free `subprocess.run(...)` with invocation argv, working
  directory, timeout seconds, text capture, `capture_output=True`,
  `check=False`, and `shell=False`
- the child environment is copied from ambient `os.environ` with deterministic
  `PYTHONPATH` override from ordered `invocation.python_path_entries`
- raw return code, stdout text, and stderr text are materialized through
  `materialize_runtime_probe_local_python_process_completion(...)`
- subprocess exceptions propagate for later mapping slices
- the release remains raw and non-interpreting: no stdout/stderr parsing, no
  return-code outcome normalization, no timeout-to-attempt/result mapping, no
  `RuntimeProbeExecutionAttempt` synthesis, no observed/non-proof result
  synthesis, no family/form handler implementation or dispatch registration,
  and no admission, recompile, facade, MCP, package-root, schema, eval,
  scoring, optimizer, compiler, benchmark, docs, or public-claim changes
- implementation review accepted the slice after one correction for pre-run
  completion revision validation
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `954 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `d0a009b Execute local Python subprocess invocations`
- Ryan-authorized push completed with `origin/main` advanced through
  `8ae13f6 Sync local Python subprocess execution release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `d0a009b`

Local Python process completion contract release:

- `RuntimeProbeLocalPythonProcessCompletion` is a frozen module-local raw
  completion contract for future local Python subprocess execution
- `materialize_runtime_probe_local_python_process_completion(...)` revalidates
  the carried invocation and materializes raw returncode/stdout/stderr fields
  without executing or interpreting anything
- the contract preserves invocation identity, argv, working directory, ordered
  Python path entries, timeout seconds, raw return code, raw stdout/stderr
  text, completion contract revision, and request replay payload fields
- empty stdout/stderr and nonzero return codes remain valid uninterpreted raw
  process facts
- the release remains non-executing and non-interpreting: no subprocess import
  or execution, no timeout enforcement, no stdout/stderr parsing, no
  `RuntimeProbeExecutionAttempt` synthesis, no observed/non-proof result
  synthesis, no family/form handler implementation or dispatch registration,
  and no admission, recompile, facade, MCP, package-root, schema, eval,
  scoring, optimizer, compiler, benchmark, or public-claim changes
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `949 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `e9f87fc Add local Python process completion contract`
- Ryan-authorized push completed with `origin/main` advanced through
  `928ea13 Sync local Python process completion routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `e9f87fc`

Local Python subprocess invocation contract release:

- `RuntimeProbeLocalPythonSubprocessInvocation` is a frozen module-local
  shell-free invocation contract for future local Python runtime probe handlers
- `materialize_runtime_probe_local_python_subprocess_invocation(...)`
  revalidates `RuntimeProbeRunnerRequest`, derives the existing local Python
  environment context, validates an absolute Python executable, validates
  dotted module names and argv tokens, and builds deterministic `python -m ...`
  argv without executing anything
- the contract preserves the original runner request, derived environment
  context, working directory, ordered Python path entries, timeout seconds,
  invocation contract revision, and replay payload fields
- blank or whitespace-only invocation contract revisions reject through tested
  validation
- the release remains non-executing: no subprocess import or execution, no
  in-process repository imports, no timeout enforcement, no stdout/stderr
  parsing, no observed-result synthesis, no family/form handler implementation
  or dispatch registration, and no admission, recompile, facade, MCP,
  package-root, schema, eval, scoring, optimizer, compiler, benchmark, or
  public-claim changes
- implementation review accepted the slice first-pass after one audit
  correction for the missing blank-revision negative test
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - Gate 2 full regression passed, including full pytest reporting
    `939 passed`
  - Gate 3 commit-gating passed for the exact four-file unit
- local commit creation completed at
  `ea6ff8e Add local Python subprocess invocation contract`
- Ryan-authorized push completed with `origin/main` advanced through
  `07cc3ce Sync local Python invocation release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-gate status is no-active-gate for `ea6ff8e`

Prior pushed runtime probe execution-input materialization release:

- `RuntimeProbeExecutionInput` is a frozen internal non-executing work item for
  one planned runtime probe request
- `RuntimeProbeExecutionInputBatch` is a frozen ordered internal batch for one
  runtime request plan
- `materialize_runtime_probe_execution_input_batch(...)` materializes
  replay-ready inputs from a `RuntimeProbeRequestPlan`,
  `RepositorySnapshotBasis`, probe contract revision, and explicit runtime
  assumptions
- materialization preserves plan ID, request IDs, request object identity,
  source-site identity, family/form labels, replay target and selector seeds,
  deterministic plan order, and the existing `RuntimeProbeReplayArtifact`
  replay metadata contract
- replay inputs carry plan/request identity, subject identity, source site/span,
  reason code, boundary text, family/form, replay target seed, and replay
  selector seed
- plan/request drift, duplicate request IDs, blank probe metadata, empty runtime
  assumptions, replay metadata drift, and batch/input plan mismatch reject
  through typed constructors or materialization gates
- empty request plans remain valid and deterministic when explicit runtime
  assumptions and probe metadata are supplied
- the helper remains internal to `context_ir.runtime_probe_execution`; no
  package-root, tool facade, MCP, JSON/schema, serialization, eval, scoring,
  optimizer, compiler, winner-selection, product, benchmark, or public-claim
  surface changed
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting
    `177 passed`
  - Gate 2 full regression passed, including full pytest reporting
    `857 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, no untracked drift, and clean `git diff --check`
- local commit creation completed at
  `cfed3c7 Add runtime probe execution input materialization`
- Ryan-authorized push completed with `origin/main` advanced through
  `d2e3e81 Sync runtime probe execution release routing`
- release files are `src/context_ir/runtime_probe_execution.py` and
  `tests/test_runtime_probe_execution.py`, plus control continuity in
  `PLAN.md` and `BUILDLOG.md`
- release-gate status is no-active-gate for `cfed3c7`

Runtime probe execution-attempt result assembly release:

- `RuntimeProbeExecutionAttempt` is a frozen internal normalized runner-output
  record for one materialized `RuntimeProbeExecutionInput`
- `assemble_runtime_probe_result_batch_from_execution_attempts(...)` converts
  a complete typed attempt set for a `RuntimeProbeExecutionInputBatch` into
  deterministic input-batch order `RuntimeProbeResultBatch`
- observed attempts become `RuntimeProbeObservedResult` only when they carry
  normalized payload or durable artifact reference
- crashed, timed-out, missing-environment, and setup-failed attempts become
  `RuntimeProbeNonProofResult` and remain non-proof
- assembly preserves plan ID, request IDs, request object identity, planned
  execution-input identity, replay artifact identity, input-batch order, and
  result-batch identity
- unplanned, duplicate, missing, plan-drifted, input-drifted, request-drifted,
  blank, malformed, and unsupported attempt metadata rejects through typed
  constructors or assembly gates
- exports remain module-local to `context_ir.runtime_probe_execution.__all__`;
  package-root, tool facade, MCP, JSON/schema, serialization, eval, scoring,
  optimizer, compiler, winner-selection, product, benchmark, and public-claim
  surfaces remain unchanged
- implementation review accepted the slice first-pass in workspace-only state
- focused validation passed, including targeted pytest reporting `189 passed`
- corrected combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting `189 passed`
  - Gate 2 full regression passed, including full pytest reporting
    `869 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, no untracked files, no ref drift, and clean
    `git diff --check`
- local commit creation completed at
  `86be8d7 Assemble runtime probe execution attempts`
- Ryan-authorized push completed with `origin/main` advanced through
  `44b05c8 Sync runtime probe attempt release routing`
- release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
- release-unit-audit, full-regression, commit-gating, staging, and local commit
  are complete for `86be8d7`
- release-gate status is no-active-gate for `86be8d7`

Runtime probe result-batch recompile bridge release:

- `RuntimeProbeResultBatchRecompileApplication` is a frozen internal envelope
  carrying result-batch admission, preserved non-proof results, runtime
  observation application, and semantic recompile result
- `apply_runtime_probe_result_batch_for_diagnostic_and_recompile(...)` requires
  the diagnostic's planned runtime probe request plan, admits the
  `RuntimeProbeResultBatch` through the existing result-batch admission bridge,
  attaches only observed proof-bearing results, preserves non-proof results
  separately, and recompiles with the updated program
- non-proof-only and partial mixed batches keep non-proof results out of
  runtime-backed proof while preserving deterministic plan-order admissions
- existing plan, request, source-site, family/form, duplicate result, negative
  budget, and missing compile-context gates propagate through the composed path
- the helper remains internal to `context_ir.runtime_observation_recompile`;
  package-root, tool facade, MCP, JSON/schema, serialization, eval, scoring,
  optimizer, compiler, winner-selection, docs, and public-claim surfaces remain
  unchanged
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting
    `232 passed`
  - Gate 2 full regression passed, including full pytest reporting
    `847 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, no untracked files, and clean `git diff --check`
- local commit creation completed at
  `591c09b Compose runtime probe result batch recompile`
- Ryan-authorized push completed with `origin/main` advanced through
  `5913bf0 Sync runtime probe batch recompile release routing`
- release files are
  `src/context_ir/runtime_observation_recompile.py` and
  `tests/test_runtime_observation_recompile.py`, plus control continuity in
  `PLAN.md` and `BUILDLOG.md`
- release-gate status is no-active-gate for `591c09b`

Prior pushed runtime probe result admission bridge release:

- `admit_runtime_probe_result_batch_for_plan(...)` bridges
  `RuntimeProbeResultBatch` into deterministic plan-ordered
  `RuntimeObservationAdmission` records
- only proof-bearing `RuntimeProbeObservedResult` values become typed
  `RuntimeObservation` values
- `RuntimeProbeNonProofResult` values are preserved separately as non-proof and
  are never admitted as runtime-backed proof
- plan ID, request ID, carried request identity, source-site identity, and
  family/form compatibility are revalidated
- probe identity, probe contract revision, repository snapshot basis, replay
  target/selector, replay inputs, runtime assumptions, normalized payload, and
  durable artifact reference are copied into the existing typed observation
  shape
- required `RuntimeAttachmentLink` values are derived deterministically from
  result identity or durable artifact reference
- the bridge remains internal to
  `context_ir.runtime_observation_admission`; package-root, facade, MCP, JSON
  schema, serialization, eval, scoring, optimizer, compiler, winner-selection,
  docs, and public-claim surfaces remain unchanged
- implementation review accepted the slice after 1 correction
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting
    `174 passed`
  - Gate 2 full regression passed, including full pytest reporting
    `842 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation completed at
  `ccd417a Add runtime probe result admission bridge`
- Ryan-authorized push completed with `origin/main` advanced through
  `6023220 Sync runtime probe admission release routing`

Released four-file unit:

- `src/context_ir/runtime_observation_admission.py`
- `tests/test_runtime_observation_admission.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `ccd417a`.

Prior pushed runtime probe execution-result/replay-artifact contract:

Released runtime probe execution-result/replay-artifact contract:

- `RuntimeProbeReplayField` provides typed replay and payload fields without
  `Any`
- `RuntimeProbeReplayArtifact` records stable probe identity, probe contract
  revision, repository snapshot basis, replay target/selector, replay inputs,
  and runtime assumptions
- `RuntimeProbeObservedResult` preserves `plan_id`, `request_id`, and carried
  `RuntimeProbeRequest` identity, validates request-ID drift, requires replay
  inputs/runtime assumptions, and requires normalized payload or durable
  artifact reference
- `RuntimeProbeNonProofResult` represents crash, timeout, missing-environment,
  and setup-failure outcomes without making them admissible runtime-backed
  proof
- `RuntimeProbeResultBatch` keeps ordered mixed proof and non-proof outcomes
  under one plan ID and rejects plan drift or duplicate request IDs
- the new contract is frozen and exported only from module-local
  `context_ir.runtime_probe_results.__all__`
- no probe execution, `RuntimeObservation` conversion, provenance attachment,
  `SemanticProgram` mutation, `tool_facade.py`, `mcp_server.py`,
  `context_ir/__init__.py`, eval, JSON schema, public claims, package-root,
  MCP, or public/API surface changed
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting
    `111 passed`
  - Gate 2 full regression passed, including full pytest reporting
    `833 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation and Ryan-authorized push completed at
  `eb6def0 Add runtime probe result contracts`

Released four-file unit:

- `src/context_ir/runtime_probe_results.py`
- `tests/test_runtime_probe_results.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `eb6def0`.

Prior released typed facade runtime recompile:


- `SemanticRuntimeObservationRecompileRequest` and
  `SemanticRuntimeObservationRecompileResponse` provide a frozen typed
  `context_ir.tool_facade` surface for applying typed runtime observations
  before semantic recompile
- `recompile_repository_context_with_runtime_observations(...)` delegates to
  `apply_runtime_observations_for_diagnostic_and_recompile(...)`
- delegation uses the previous `SemanticContextResponse` program and compile
  result
- optional `embed_fn` is forwarded
- response mirror fields are guarded against drift from the underlying runtime
  observation application and semantic recompile result
- existing admission, application, and recompile gates propagate through the
  facade
- empty observations preserve original-program application behavior while still
  recompiling
- successful runtime observation satisfaction does not re-plan the already
  satisfied diagnostic runtime request
- `context_ir.mcp_server`, `context_ir.__init__`, package-root exports, and
  JSON serialization remain unchanged
- no probe execution, runtime observation collection, execution-result
  contract, schema, scoring policy, compiler contract, optimizer,
  winner-selection, eval, product, benchmark, or public-claim surface changed
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting `58 passed`
  - Gate 2 full regression passed, including full pytest reporting `816 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation and Ryan-authorized push completed at
  `8ac3b46 Add typed runtime recompile facade`

Released four-file unit:

- `src/context_ir/tool_facade.py`
- `tests/test_tool_facade.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `8ac3b46`.

Released runtime observation recompile composition:

- `RuntimeObservationRecompileApplication` is a frozen internal result
  envelope in `src/context_ir/runtime_observation_recompile.py`
- `apply_runtime_observations_for_diagnostic_and_recompile(...)` composes
  `apply_runtime_observations_for_diagnostic(...)` with
  `recompile_semantic_context(...)`
- the helper applies observations through the existing diagnostic-gated
  admission/application path, then recompiles with
  `application.updated_program`
- optional `embed_fn` is forwarded to semantic recompile
- the returned envelope carries both the runtime observation application and
  the semantic recompile result
- successful runtime observation satisfaction does not re-plan the already
  satisfied diagnostic runtime request
- empty observations preserve existing empty-application behavior and
  recompile the original program
- missing diagnostic plans, unmatched observation sites, duplicate observation
  sites, family/form mismatches, negative budget deltas, and missing prior
  compile context reject through existing gates
- input `SemanticProgram`, previous compile result, diagnostic, plan, request,
  and observations are not mutated
- the new helper is exported only from module-local `__all__`; no package-root,
  analyzer, tool-facade, or MCP surface is widened
- no probe execution, execution-result contract, runtime observation
  collection, eval, schema, scoring policy, compiler contract, optimizer,
  winner-selection, product, public benchmark, or public-claim surface changed
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting `87 passed`
  - Gate 2 full regression passed, including full pytest reporting `811 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation and Ryan-authorized push completed at
  `b279b00 Compose runtime observation recompile flow`

Released four-file unit:

- `src/context_ir/runtime_observation_recompile.py`
- `tests/test_runtime_observation_recompile.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `b279b00`.

Prior released diagnostic trace refresh:

- `diagnose_semantic_miss(previous_result, evidence, current_program)` now
  classifies runtime support from the supplied current `SemanticProgram` using
  diagnose-visible provenance
- `previous_result` remains the source for prior selected detail, preserving
  prior depth/status semantics
- runtime-backed support remains additive: unsupported and frontier boundaries
  keep their primary non-proof tiers
- stale prior warning or selection trace summaries no longer make
  post-application diagnostics deny or fabricate current runtime support
- already satisfied diagnostic runtime requests are not planned again
- recompile with an updated program compiles that updated program and carries
  attached runtime support in selected trace summaries when selected
- no probe execution, execution-result contract, runtime observation
  collection, analyzer/tool-facade behavior, package-root API, MCP, eval,
  schema, scoring policy, compiler contract, winner-selection, product,
  public benchmark, or public-claim surface changed
- implementation review accepted the slice first-pass
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact five-file release unit
  - focused validation passed, including targeted pytest reporting `101 passed`
  - Gate 2 full regression passed, including full pytest reporting `806 passed`
  - Gate 3 commit-gating passed with the exact five-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation and Ryan-authorized push completed at
  `74aadd7 Refresh diagnostic runtime trace support`

Released five-file unit:

- `src/context_ir/semantic_diagnostics.py`
- `src/context_ir/semantic_optimizer.py`
- `tests/test_semantic_diagnostics.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `74aadd7`.

Prior released diagnostic runtime observation application:

- `RuntimeObservationApplication` is a frozen internal result envelope in
  `src/context_ir/runtime_observation_admission.py`
- `apply_runtime_observations_for_diagnostic(program, diagnostic, observations)`
  composes `admit_runtime_observations_for_diagnostic(...)` with
  `attach_admitted_runtime_observations(...)`
- application requires the diagnostic's planned runtime probe request plan
  through the existing diagnostic admission path
- admissions preserve diagnostic plan order, request IDs, request object
  identity, and observation object identity
- empty admitted batches return the original `SemanticProgram` object through
  the existing attachment behavior
- missing plans, unmatched observation source sites, duplicate observation
  source sites, and family/form mismatches reject through existing gates
- input `SemanticProgram`, `SemanticDiagnosticResult`, planned requests, and
  observations are not mutated
- no probe execution, execution-result contract, runtime observation
  collection, analyzer/tool-facade behavior, semantic recompile behavior,
  package-root API, MCP, eval, schema, scoring, optimizer, compiler,
  winner-selection, product, public benchmark, or public-claim surface changed
- implementation review accepted the slice first-pass
- control-lane focused validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_observation_admission.py tests/test_runtime_observation_admission.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_observation_admission.py tests/test_runtime_observation_admission.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_observation_admission.py tests/test_runtime_acquisition.py tests/test_runtime_probe_requests.py tests/test_semantic_diagnostics.py -v`
    reporting `165 passed`
  - `git diff --check`
- combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed for the exact four-file release unit
  - focused validation passed, including targeted pytest reporting `165 passed`
  - Gate 2 full regression passed, including full pytest reporting `805 passed`
  - Gate 3 commit-gating passed with the exact four-file unit, nothing staged,
    no extra drift, and clean `git diff --check`
- local commit creation and Ryan-authorized push completed at
  `95f7545 Apply diagnostic runtime observations`

Released four-file unit:

- `src/context_ir/runtime_observation_admission.py`
- `tests/test_runtime_observation_admission.py`
- `PLAN.md`
- `BUILDLOG.md`

Release-gate status is no-active-gate for `95f7545`.

Current route:

- Runtime probe result-batch recompile bridge is pushed at
  `591c09b Compose runtime probe result batch recompile` with no active gate.
- Runtime probe result admission bridge is pushed at
  `ccd417a Add runtime probe result admission bridge` with no active gate.
- Runtime probe execution-result/replay-artifact contract is pushed at
  `eb6def0` with no active gate.
- Typed facade runtime recompile is pushed at `8ac3b46` with no active gate.
- Runtime probe execution-input materialization is pushed at
  `cfed3c7 Add runtime probe execution input materialization` with no active
  gate.
- Runtime probe execution-attempt result assembly is pushed at
  `86be8d7 Assemble runtime probe execution attempts` with no active gate.
- Runtime probe runner-request materialization is pushed at
  `68a8e73 Materialize runtime probe runner requests` with no active gate.
  The release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- Combined read-only release gate passed with no findings for that exact
  four-file runner-request materialization unit, and Ryan-authorized push is
  complete.
- Runtime probe runner-request attempt/result assembly is pushed at
  `3363929 Assemble runtime probe runner request attempts` with no active
  gate. The release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- Combined read-only release gate passed with no findings for that exact
  four-file runner-request attempt/result assembly unit, and Ryan-authorized
  push is complete.
- Runtime probe diagnostic runner-request preparation is pushed at
  `fd0f6d8 Prepare runtime probe diagnostic runner requests` with no active
  gate. The release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- The combined read-only release gate passed with no findings for that exact
  four-file diagnostic runner-request preparation unit: Gate 1 release-unit
  audit passed, focused validation passed with `205 passed`, Gate 2 full
  regression passed with `885 passed`, and Gate 3 commit-gating passed.
- Ryan-authorized push is complete for the diagnostic runner-request
  preparation release, with `origin/main` advanced through
  `74d84fb Sync runtime probe diagnostic runner request release routing`.
- Runtime probe runner-callable attempt collection is pushed at
  `32f6220 Collect runtime probe runner attempts` with no active gate. The
  release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- The combined read-only release gate passed with no findings for that exact
  four-file runner-callable attempt collection unit: Gate 1 release-unit audit
  passed, focused validation passed with `211 passed`, Gate 2 full regression
  passed with `891 passed`, and Gate 3 commit-gating passed.
- Ryan-authorized push is complete for the runner-callable attempt collection
  release, with `origin/main` advanced through
  `e9b5b5a Sync runtime probe runner attempt collection release routing`.
- Runtime probe diagnostic runner-callable recompile bridge is pushed at
  `74fb275 Compose runtime probe runner callable recompile` with no active
  gate. The release unit is exactly
  `src/context_ir/runtime_observation_recompile.py`,
  `tests/test_runtime_observation_recompile.py`, `PLAN.md`, and
  `BUILDLOG.md`.
- Control-lane focused validation passed for that workspace-only unit:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_observation_recompile.py tests/test_runtime_observation_recompile.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_observation_recompile.py tests/test_runtime_observation_recompile.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_observation_recompile.py tests/test_runtime_observation_admission.py tests/test_runtime_probe_execution.py tests/test_runtime_probe_results.py tests/test_runtime_probe_requests.py tests/test_public_api.py tests/test_mcp_server.py tests/test_tool_facade.py -v`
    reporting `215 passed`
  - `git diff --check`
- The combined read-only release gate passed with no findings for that exact
  four-file diagnostic runner-callable recompile bridge unit: Gate 1
  release-unit audit passed, focused validation passed with `215 passed`,
  Gate 2 full regression passed with `895 passed`, and Gate 3 commit-gating
  passed.
- Local commit creation completed at
  `74fb275 Compose runtime probe runner callable recompile`.
- Ryan-authorized push completed with `origin/main` advanced through
  `f463df7 Sync runtime probe callable recompile release routing`.
- Release-gate status is no-active-gate for `74fb275`.
- Runtime probe runner failure-normalization adapter is pushed at
  `93456b6 Normalize runtime probe runner failures` with no active gate. The
  release unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- Control-lane focused validation passed for that workspace-only unit:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_execution.py tests/test_runtime_probe_execution.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_execution.py tests/test_runtime_probe_execution.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_execution.py tests/test_runtime_probe_results.py tests/test_runtime_probe_requests.py tests/test_runtime_observation_admission.py tests/test_runtime_observation_recompile.py tests/test_public_api.py tests/test_mcp_server.py tests/test_tool_facade.py -v`
    reporting `223 passed`
  - `git diff --check`
- The combined read-only release gate passed with no findings for that exact
  four-file runtime probe runner failure-normalization adapter unit: Gate 1
  release-unit audit passed, focused validation passed with `223 passed`,
  Gate 2 full regression passed with `903 passed`, and Gate 3 commit-gating
  passed.
- Local commit creation completed at
  `93456b6 Normalize runtime probe runner failures`.
- Ryan-authorized push completed with `origin/main` advanced through
  `4f13fac Sync runtime probe failure normalization routing`.
- Release-gate status is no-active-gate for `93456b6`.
- The accepted slice adds an internal
  runtime probe runner failure-normalization adapter in
  `src/context_ir/runtime_probe_execution.py` and
  `tests/test_runtime_probe_execution.py`. This route preserves the
  strict runner-callable path while adding an explicit opt-in wrapper that
  converts runner-raised exceptions into typed non-proof
  `RuntimeProbeExecutionAttempt` values. It does not implement subprocess
  execution, in-process repository probe execution, timeout enforcement,
  family/form-specific probe logic, admission or recompile rule changes,
  facade/MCP/package-root export, schema, eval, scoring, optimizer, compiler,
  benchmark, or public claims.
- Runtime probe runner dispatch table implementation slice is accepted
  first-pass in workspace-only state. It adds an internal frozen typed
  family/form handler registry and dispatching `RuntimeProbeRunnerCallable`.
  Missing handlers produce deterministic non-proof attempts rather than
  runtime-backed proof. Focused control-lane validation passed with
  `232 passed`.
- The combined read-only release gate passed with no findings for the exact
  four-file runtime probe runner dispatch table release unit:
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
  Focused validation passed with `232 passed`; full regression passed with
  `912 passed`; commit-gating passed.
- Local commit creation completed at
  `3751df1 Add runtime probe runner dispatch table`.
- Ryan-authorized push completed with `origin/main` advanced through
  `d7fe447 Sync runtime probe dispatch routing`.
- Release-gate status is no-active-gate for `3751df1`.
- Runtime probe runner environment context implementation slice is accepted
  first-pass in workspace-only state. It adds a frozen typed local Python
  environment context and derivation helper in
  `src/context_ir/runtime_probe_execution.py`, with focused tests in
  `tests/test_runtime_probe_execution.py`. Focused control-lane validation
  passed with `163 passed`.
- Proposed release unit is exactly:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release state for the environment context unit:
  - accepted in workspace: yes, first-pass
  - release-unit-audit-cleared: yes
  - full-regression-cleared: yes, full pytest `925 passed`
  - commit-gating-cleared: yes
  - staged: no
  - locally committed at `f75196e Add runtime probe runner environment context`
  - pushed with `origin/main` advanced through
    `646298b Sync runtime probe environment context local routing`
  - release-gate status is no-active-gate
  - next route: select the next bounded control action after the pushed release
- Do not route `591c09b`, `ccd417a`, `eb6def0`, `8ac3b46`, `b279b00`,
  `74aadd7`, `95f7545`,
  `35c440d`, `f5c8df0`, `8706f2e`, `b0a5ec5`, `6d5fc47`, `fce09b0`,
  `7c46f48`, `4ba06ad`, `97dc0f6`, `744bf0e`, `3df02c6`, `49fa461`,
  `a819cf5`, `2e448ea`, `f6c66e4`, or `546a4da` back to docs review,
  release-unit audit, focused validation, full regression, commit-gating,
  staging, local commit creation, or push absent new findings
- Push remains Ryan-gated for any future release

Released planned runtime probe request plan source-site indexing:

- `index_runtime_probe_request_plan_by_source_site(plan)` indexes a
  `RuntimeProbeRequestPlan` by the same source-site identity tuple used by
  runtime acquisition matching
- the helper preserves request object identity and plan insertion order
- full plans, diagnostic-filtered plans, and empty plans are supported
- duplicate source-site ambiguity raises `ValueError`
- request IDs, plan IDs, plan order, planned-only status, and empty-plan
  behavior are preserved
- tests cover full, diagnostic-filtered, and empty plans; duplicate sites;
  request/plan ID stability; planned-only status; object identity; insertion
  order; and non-mutation of the plan
- the helper is exported only from module-local
  `context_ir.runtime_probe_requests.__all__`; no package-root export is added
- no probe execution, execution-result contract, observation-admission
  contract, runtime provenance attachment, analyzer/tool-facade behavior, MCP,
  package-root API, eval, schema, scoring, optimizer, compiler,
  winner-selection, product, public benchmark, or public-claim surface changed
- implementation review accepted the slice first-pass in workspace-only state
- control-lane focused validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_requests.py tests/test_semantic_diagnostics.py -v`
    reporting `41 passed`
  - `git diff --check`
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `41 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `746 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Local commit creation and Ryan-authorized push completed at
  `6d5fc47 Index runtime probe plans by source site`

Release-gate status is no-active-gate for
`6d5fc47 Index runtime probe plans by source site`. Do not route `6d5fc47`
back to docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Released semantic diagnostic runtime probe request plan surfacing:

- `SemanticDiagnosticResult` now has optional
  `planned_runtime_probe_request_plan`
- the new field is typed through `TYPE_CHECKING` to avoid runtime import cycles
- `SemanticDiagnosticResult` rejects mismatches between
  `planned_runtime_probe_request_plan.requests` and
  `planned_runtime_probe_requests`
- `diagnose_semantic_miss(...)` derives the deterministic diagnostic request
  plan and sets `planned_runtime_probe_requests` from `plan.requests`
- ungrounded and requestless diagnostics expose the deterministic empty plan
- `recompile_semantic_context(...)` carries the diagnostic plan through
  `result.diagnostic`
- tests cover non-empty plans, empty plans, stable request IDs and plan IDs,
  mismatch rejection, and recompile carry-through
- no probe execution, execution-result contract, observation-admission
  contract, runtime provenance attachment, status widening,
  request-ID/plan-ID derivation change, `RuntimeProbeRequestPlan` contract
  change, `SemanticProgram` mutation, analyzer/tool facade, MCP,
  package-root export, eval, schema, scoring, optimizer, compiler,
  winner-selection, product, public benchmark, or public-claim surface changed
- Implementation review accepted the slice first-pass in workspace-only state
- Control-lane focused validation passed:
  - `.venv/bin/python -m ruff check src/context_ir/semantic_types.py src/context_ir/semantic_diagnostics.py tests/test_semantic_diagnostics.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/semantic_types.py src/context_ir/semantic_diagnostics.py tests/test_semantic_diagnostics.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_semantic_diagnostics.py tests/test_runtime_probe_requests.py -v`
    reporting `37 passed`
  - `git diff --check`
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `37 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `742 passed`
  - Gate 3 commit-gating passed and approved the exact five-file unit
- Local commit creation and Ryan-authorized push completed at
  `7c46f48 Surface semantic diagnostic probe plans`

Release-gate status is no-active-gate for
`7c46f48 Surface semantic diagnostic probe plans`. Do not route `7c46f48` back
to docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Prior pushed source/contract release authority is
`744bf0e Add runtime probe request plans`. It supersedes the workspace-only
planned runtime probe request plan release-gate route for active control
routing only. Live git refs and worktree state must still be verified from git
during control intake.

Repo-backed release truth verified during post-push continuity sync: branch
`main`, `HEAD` and `origin/main` at
`744bf0e Add runtime probe request plans`, clean worktree, and nothing staged.

Released planned runtime probe request plan contract:

- `RuntimeProbeRequestPlan` is a frozen internal planned-only request batch
  envelope
- Internal contract version is `runtime_probe_request_plan:v1`
- `build_runtime_probe_request_plan(requests)` preserves input request order
  as a tuple
- The plan exposes ordered `request_ids` from stable
  `RuntimeProbeRequest.request_id`
- `plan_id` is deterministic over the contract version and ordered request IDs
- Duplicate request IDs raise `ValueError` through the existing request ID
  indexer path
- Empty plans are valid and deterministic
- The helper and plan type are exported only from module-local
  `context_ir.runtime_probe_requests.__all__`; no package-root export is added
- Tests cover full plans, empty plans, duplicate-ID rejection,
  diagnostic-filtered plans, ID/order stability, and input purity
- The slice does not execute probes, add execution-result or
  observation-admission contracts, attach runtime provenance, add statuses,
  change request-ID derivation, mutate `SemanticProgram`, mutate diagnostics,
  mutate unsupported/frontier/provenance state, change compile/recompile
  behavior, or widen analyzer, tool facade, MCP, package-root exports, eval,
  schema, scoring, optimizer, compiler, winner-selection, product, public
  benchmark, or public-claim surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `33 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `738 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Control-lane focused validation before release gate passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_requests.py tests/test_semantic_diagnostics.py -v`
    reporting `33 passed`
  - `git diff --check`
- Local commit creation and Ryan-authorized push completed at
  `744bf0e Add runtime probe request plans`

Release-gate status is no-active-gate for
`744bf0e Add runtime probe request plans`. Do not route `744bf0e` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Prior pushed source/contract release authority is
`3df02c6 Index runtime probe requests by ID`. It supersedes the
workspace-only planned runtime probe request ID indexing release-gate route for
active control routing only. Live git refs and worktree state must still be
verified from git during control intake.

Repo-backed release truth verified during post-push continuity sync: branch
`main`, `HEAD` and `origin/main` at
`3df02c6 Index runtime probe requests by ID`, clean worktree, and nothing
staged.

Released planned runtime probe request ID indexing:

- `index_runtime_probe_requests_by_id(requests)` returns planned runtime probe
  requests keyed by stable `RuntimeProbeRequest.request_id`
- Input iteration order is preserved through normal dictionary insertion order
- Duplicate request IDs raise `ValueError`
- The helper is exported only from module-local
  `context_ir.runtime_probe_requests.__all__`; no package-root export is added
- Tests cover full-plan indexing, key order, duplicate rejection, no mutation,
  and diagnostic-filtered request indexing
- The slice does not execute probes, add execution-result or
  observation-admission contracts, attach runtime provenance, add statuses,
  change request-ID derivation, mutate `SemanticProgram`, mutate diagnostics,
  mutate unsupported/frontier/provenance state, change compile/recompile
  behavior, or widen analyzer, tool facade, MCP, package-root exports, eval,
  schema, scoring, optimizer, compiler, winner-selection, product, public
  benchmark, or public-claim surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `29 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `734 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Control-lane focused validation before release gate passed:
  - `.venv/bin/python -m ruff check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m ruff format --check src/context_ir/runtime_probe_requests.py tests/test_runtime_probe_requests.py`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_runtime_probe_requests.py tests/test_semantic_diagnostics.py -v`
    reporting `29 passed`
  - `git diff --check`
- Local commit creation and Ryan-authorized push completed at
  `3df02c6 Index runtime probe requests by ID`

Release-gate status is no-active-gate for
`3df02c6 Index runtime probe requests by ID`. Do not route `3df02c6` back to
docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Prior pushed source/contract release authority is
`49fa461 Add runtime probe request identities`. It supersedes the
workspace-only post-`bea0a1a` stable planned runtime probe request identity
release-gate route for active control routing only. Live git refs and worktree
state must still be verified from git during control intake.

Repo-backed release truth verified during post-push continuity sync: branch
`main`, `HEAD` and `origin/main` at
`49fa461 Add runtime probe request identities`, clean worktree, and nothing
staged.

Released stable planned runtime probe request identity:

- `RuntimeProbeRequest.request_id` is a computed stable internal identity for
  planned runtime probe requests
- Request IDs are SHA-256 based and derived from canonical planned-request
  identity fields only: subject identity, source site, reason code, boundary
  text, family/form labels, and replay target/selector seeds
- Constructor call sites are unchanged
- IDs are deterministic across repeated derivation from the same program and
  unique across a derived request set
- Diagnostic-filtered requests preserve the same IDs as their underlying
  planned requests
- Tests cover repeated-derivation stability, uniqueness, diagnostic filtering
  preservation, and ID presence across all currently supported runtime probe
  families
- The slice does not execute probes, add execution-result or
  observation-admission contracts, attach runtime provenance, add statuses,
  mutate `SemanticProgram`, mutate diagnostics, mutate unsupported/frontier/
  provenance state, change compile/recompile behavior, or widen analyzer,
  tool facade, MCP, package-root exports, eval, schema, scoring, optimizer,
  compiler, winner-selection, product, public benchmark, or public-claim
  surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `27 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `732 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Local commit creation and Ryan-authorized push completed at
  `49fa461 Add runtime probe request identities`

Release-gate status is no-active-gate for
`49fa461 Add runtime probe request identities`. Do not route `49fa461` back to
docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Prior pushed source/contract release authority is
`a819cf5 Surface diagnostic runtime probe requests`. It supersedes the
workspace-only post-`e94cd5d` diagnose/recompile planned runtime probe request
consumption release-gate route for active control routing only. Live git refs
and worktree state must still be verified from git during control intake.

Repo-backed release truth verified during post-push continuity sync: branch
`main`, `HEAD` and `origin/main` at
`a819cf5 Surface diagnostic runtime probe requests`, clean worktree, and
nothing staged.

Released diagnose/recompile planned runtime probe request consumption:

- `SemanticDiagnosticResult` now carries
  `planned_runtime_probe_requests` as a planned-only diagnostic result
  contract
- The result contract is typed without runtime import cycles and guarded so
  planned requests must target grounded diagnostic boundaries that still need
  runtime-backed support
- `diagnose_semantic_miss(...)` derives planned runtime probe requests through
  the existing `derive_diagnostic_runtime_probe_requests(program, diagnostic)`
  bridge after boundary classification
- `recompile_semantic_context(...)` carries the diagnostic result through
  unchanged via `result.diagnostic`
- Tests cover attachable omitted dynamic import, attached runtime support,
  non-attachable unsupported boundaries, heuristic frontier, statically proved
  units, ungrounded evidence, and mutation-free recompile carry-through
- The slice does not execute probes, attach runtime provenance, mutate
  `SemanticProgram`, mutate previous compile results, create dependency edges,
  add selected symbols or units, or widen analyzer, tool facade, package-root
  export, MCP, eval, schema, scoring, optimizer, compiler, winner-selection,
  product, public benchmark, or public-claim surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `27 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `732 passed`
  - Gate 3 commit-gating passed and approved the exact five-file unit
- Local commit creation and Ryan-authorized push completed at
  `a819cf5 Surface diagnostic runtime probe requests`

Release-gate status is no-active-gate for
`a819cf5 Surface diagnostic runtime probe requests`. Do not route `a819cf5`
back to docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Prior route superseded by the pushed `49fa461` request-ID release above:

- The bounded post-`a819cf5` North Star planning/control decision is complete;
  it selected stable planned runtime probe request identity as the next
  smallest meaningful capability slice; that slice is now released at
  `49fa461 Add runtime probe request identities`
- Do not route `49fa461`, `a819cf5`, `2e448ea`, `f6c66e4`, or `546a4da` back
  to docs review, release-unit audit, focused validation, full regression,
  commit-gating, staging, local commit creation, or push absent new findings
- Push remains Ryan-gated for any future release

Prior pushed source/contract release authority is
`2e448ea Add diagnostic runtime probe request bridge`. It supersedes the
workspace-only post-`38f3841` diagnostic runtime probe-request release-gate
route for active control routing only. Live git refs and worktree state must
still be verified from git during control intake.

Repo-backed release truth verified during post-push continuity sync: branch
`main`, `HEAD` and `origin/main` at
`2e448ea Add diagnostic runtime probe request bridge`, clean worktree, and
nothing staged.

Released internal diagnostic runtime probe-request bridge:

- `derive_diagnostic_runtime_probe_requests(program, diagnostic)` derives
  existing planned runtime probe requests and filters them to grounded
  diagnostic boundary units that still need runtime-backed support
- The bridge preserves `derive_runtime_probe_requests(program)` planned-only
  request semantics, deterministic ordering, attachable-only behavior, and
  `planned_not_executed` status
- It ignores statically proved diagnostic units, already runtime-supported
  boundaries, frontier items without attachable unsupported probe requests, and
  unsupported boundaries that are not attachable
- It does not execute probes, attach runtime provenance, mutate
  `SemanticProgram`, mutate `SemanticDiagnosticResult`, or widen analyzer,
  tool facade, package-root API, MCP, eval, schema, scoring, optimizer,
  compiler, winner-selection, product, public benchmark, or public-claim
  surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `6 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `729 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Local commit creation and Ryan-authorized push completed at
  `2e448ea Add diagnostic runtime probe request bridge`

Release-gate status is no-active-gate for
`2e448ea Add diagnostic runtime probe request bridge`. Do not route `2e448ea`
back to docs review, release-unit audit, focused validation, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

Prior pushed continuity authority is
`38f3841 Sync runtime probe request release routing`. Prior pushed
source/contract release authority is
`f6c66e4 Add runtime probe request planning contract`.

Prior pushed runtime probe-request planning contract:

- Repo-backed release truth verified during post-push continuity sync: branch
  `main`, `HEAD` and `origin/main` at
  `f6c66e4 Add runtime probe request planning contract`, clean worktree, and
  nothing staged.
- `derive_runtime_probe_requests(program)` emits deterministic planned-only
  requests for already-attachable unsupported runtime boundaries
- Request records include unsupported subject kind/id, source site, reason
  code, boundary text, runtime family/form labels, replay target/selector
  seeds, and explicit `planned_not_executed` status
- Covered families are current attachable `DYNAMIC_IMPORT`,
  `REFLECTIVE_BUILTIN`, `RUNTIME_MUTATION`, `EXEC_OR_EVAL`, and
  `METACLASS_BEHAVIOR` boundaries
- The function does not execute probes, attach runtime provenance, mutate
  unsupported/frontier/provenance state, or widen public/package-root/MCP
  surfaces
- Implementation review accepted the slice first-pass
- Combined read-only release gate passed with no findings:
  - Gate 1 release-unit audit passed
  - focused validation passed, including targeted pytest reporting `2 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `725 passed`
  - Gate 3 commit-gating passed and approved the exact four-file unit
- Local commit creation and Ryan-authorized push completed at
  `f6c66e4 Add runtime probe request planning contract`

Prior pushed code/eval release authority is
`546a4da Add reflective builtin branch eval probes`.

The completed and pushed release unit is the full 16-file internal eval-only
`REFLECTIVE_BUILTIN` tranche:

- Six docs:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- Five `hasattr_false` eval/test assets:
  - `evals/fixtures/oracle_signal_hasattr_false_probe/main.py`
  - `evals/fixtures/oracle_signal_hasattr_false_probe/eval_runtime_observations.json`
  - `evals/tasks/oracle_signal_hasattr_false_probe.json`
  - `evals/run_specs/oracle_signal_hasattr_false_probe_matrix.json`
  - `tests/test_eval_signal_hasattr_false_probe.py`
- Five `vars_type_error` eval/test assets:
  - `evals/fixtures/oracle_signal_vars_type_error_probe/main.py`
  - `evals/fixtures/oracle_signal_vars_type_error_probe/eval_runtime_observations.json`
  - `evals/tasks/oracle_signal_vars_type_error_probe.json`
  - `evals/run_specs/oracle_signal_vars_type_error_probe_matrix.json`
  - `tests/test_eval_signal_vars_type_error_probe.py`

`hasattr(obj, name)` false-branch implementation/evidence state:

- Matrix `oracle_signal_hasattr_false_probe_matrix` is exactly 1 task x 2
  budgets x 3 providers
- Budgets are `[220, 100]`
- Providers are `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`
- Fixture call boundary is exactly `hasattr(obj, name)`
- Runtime payload is exactly `attribute_present=false`
- Deterministic digest is `hasattr_false:missing`
- Selector and selected-unit primary truth remain `unsupported/opaque`
- Runtime provenance is additive runtime provenance only
- Empty baselines remain empty at both budgets
- Missing-attribute no-edge/no-symbol/no-unit boundary: no
  missing-attribute dependency edge, selected symbol, or selected unit is
  introduced
- No source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/
  winner-selection/product/public benchmark widening is authorized

`vars(obj)` raised-`TypeError` implementation/evidence state:

- Matrix `oracle_signal_vars_type_error_probe_matrix` is exactly 1 task x 2
  budgets x 3 providers
- Budgets are `[220, 100]`
- Providers are `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`
- Fixture boundary is exactly `vars(obj)`
- Runtime payload is exactly `lookup_outcome=raised_type_error`
- Deterministic digest is `vars_type_error:raised_type_error`
- Selector primary truth remains `unsupported/opaque`
- Runtime provenance is additive runtime provenance only
- Empty baselines remain empty at both budgets
- Failed-namespace no-edge/no-symbol/no-unit boundary: no namespace
  dependency edge, selected symbol, or selected unit is introduced from the
  failed `vars()` lookup
- Dependency guard uses `site:call:main.py:2:11`
- No source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/
  winner-selection/product/public benchmark widening is authorized

Release state for `546a4da`:

- Implementation review accepted the accumulated eval-only tranche in
  workspace
- Docs/evidence/continuity reconciliation was accepted after one correction
- Combined read-only release gate passed:
  - Gate 1 release-unit audit passed with no findings
  - focused validation passed with targeted pytest reporting `13 passed`
  - Gate 2 full regression passed with `pytest tests/ -v` reporting
    `723 passed`
  - Gate 3 commit-gating passed and approved the exact 16-file unit
- Local commit creation completed at
  `546a4da Add reflective builtin branch eval probes`
- Ryan-authorized push completed at
  `546a4da Add reflective builtin branch eval probes`
- Release-facing docs remain state-neutral
- Public comparative claims remain bounded to the existing public claim
  boundary
- No source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/
  winner-selection/product/public benchmark widening is authorized

Prior route superseded by the pushed `a819cf5` release state above:

- The bounded diagnose/recompile bridge-consumption implementation slice has
  completed, passed release gates, been locally committed, and been pushed at
  `a819cf5 Surface diagnostic runtime probe requests`
- Release-gate status is no-active-gate for
  `a819cf5 Surface diagnostic runtime probe requests`
- Do not route `a819cf5` back to docs review, release-unit audit, focused
  validation, full regression, commit-gating, staging, local commit creation,
  or push absent new findings
- Release-gate status is no-active-gate for
  `2e448ea Add diagnostic runtime probe request bridge`
- Do not route `2e448ea` back to docs review, release-unit audit, focused
  validation, full regression, commit-gating, staging, local commit creation,
  or push absent new findings
- Release-gate status is no-active-gate for
  `f6c66e4 Add runtime probe request planning contract`
- Do not route `f6c66e4` back to docs review, release-unit audit, focused
  validation, full regression, commit-gating, staging, local commit creation,
  or push absent new findings
- Release-gate status is no-active-gate for
  `546a4da Add reflective builtin branch eval probes`
- Do not route `546a4da` back to docs review, release-unit audit, focused
  validation, full regression, commit-gating, staging, local commit creation,
  or push absent new findings
- No active route remains to release-unit audit, focused validation, full
  regression, commit-gating, staging, local commit creation, or push for
  `49fa461`, `a819cf5`, `2e448ea`, `f6c66e4`, or `546a4da` absent new findings
- Push remains Ryan-gated for any future release

Latest pushed source/contract release authority is
`49fa461 Add runtime probe request identities`. Prior pushed continuity
authority is `bea0a1a Sync diagnostic probe request surface routing`. Prior
pushed source/contract release authority is
`a819cf5 Surface diagnostic runtime probe requests`; earlier pushed
source/contract release authorities are
`2e448ea Add diagnostic runtime probe request bridge` and
`f6c66e4 Add runtime probe request planning contract`. Prior pushed code/eval
release authority is `546a4da Add reflective builtin branch eval probes`.
Prior pushed continuity authority is
`5537a81 Sync original dynamic import release routing`. Prior code/eval
release authority is
`d73cde4 Expand original dynamic import budget coverage`; earlier pushed
code/eval release authority is
`e2f3dcf Expand dir-zero and metaclass budget coverage`; prior pushed
continuity authority is `8aa38d5 Sync dir-zero metaclass release routing`.
There is no active route back to release-unit audit, full regression,
commit-gating, staging, local commit creation, or push for `e2f3dcf` absent new
findings.

Prior pushed continuity authority is
`642b6f9 Sync exec eval release routing`. Prior pushed code/eval authority is
`21f2dc5 Expand exec and eval budget coverage`, which is no-active-gate. Do
not route `21f2dc5` back to docs review, release-unit audit, full regression,
commit-gating, staging, local commit creation, or push absent new findings.

`9fffc5e Sync dynamic import release routing` remains an older pushed
continuity authority. The completed and pushed internal eval-only
`DYNAMIC_IMPORT` sibling budget-pressure release at
`c2c1898 Expand dynamic import sibling eval budget coverage` remains an older
pushed code/eval authority and is no-active-gate. Latest pushed process-doc
authority remains `98edc4a Codify release gate continuity controls`.

The completed and pushed internal eval-only `RUNTIME_MUTATION` /
`delattr(obj, name)` and `setattr(obj, name, value)` budget-pressure expansion
release at `b8e126e Expand runtime mutation eval budget coverage` remains the
older pushed code/eval authority and is:

- Release unit:
  - `ARCHITECTURE.md`
  - `BUILDLOG.md`
  - `EVAL.md`
  - `PLAN.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `evals/run_specs/oracle_signal_delattr_probe_matrix.json`
  - `evals/run_specs/oracle_signal_setattr_probe_matrix.json`
  - `tests/test_eval_signal_delattr_probe.py`
  - `tests/test_eval_signal_setattr_probe.py`
- `oracle_signal_delattr_probe_matrix` expands from `[220]` to `[220, 100]`
- `oracle_signal_setattr_probe_matrix` expands from `[220]` to `[220, 100]`
- Each matrix remains 1 task x 2 budgets x 3 providers
- Providers remain `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`
- Fixtures, tasks, queries, and runtime payloads are unchanged
- `delattr` runtime payload remains `mutation_outcome=deleted_attribute`
- `setattr` runtime payload remains `mutation_outcome=returned_none`
- Selector and selected-unit truth remain `unsupported/opaque`
- Runtime provenance remains additive only
- Baseline providers remain empty at both budgets
- No source/API/MCP/package-export/schema/scoring/optimizer/compiler/
  winner-selection/product/public benchmark widening is authorized
- This release supersedes older historical routing notes that rejected
  `delattr` budget `100` expansion before a specific comparison need existed

Release state for `b8e126e`: docs/evidence/continuity reconciliation was
accepted after one correction; release-unit audit cleared first-pass; full
regression cleared first-pass with `ruff check src/ tests/`,
`ruff format --check src/ tests/`, `mypy --strict src/`, and
`pytest tests/ -v` reporting `709 passed`; commit-gating completed; local
commit creation completed at `b8e126e`; and Ryan-authorized push completed at
`b8e126e`.

Release-gate status is no-active-gate for `b8e126e`: do not route back to docs
review, release-unit audit, full regression, commit-gating, staging, local
commit creation, or push for this tranche absent new findings. No active route
remains to docs review, release-unit audit, full regression, commit-gating,
staging, local commit creation, or push for `b8e126e` absent new findings.
Do not reopen `c2c1898`, `b8e126e`, `98edc4a`, `ad9db8d`, or earlier pushed
releases absent new findings.

The completed and pushed process-doc release at
`98edc4a Codify release gate continuity controls` remains the pushed
process-doc authority. It preserves the tranche batching / throughput
discipline codified by `125f088` and adds release gate continuity controls
while preserving sequential implementation slices, findings-first gates, Ryan
authorization requirements, and push discipline. Release-gate status is
no-active-gate for `98edc4a`: do not route it back to release-unit audit, full
regression, commit-gating, staging, local commit creation, or push absent new
findings.

The completed and pushed internal eval-only `REFLECTIVE_BUILTIN` / `dir(obj)`
budget-pressure expansion release at
`ad9db8d Expand dir eval budget coverage` remains an older code/eval
authority:

- Matrix: `oracle_signal_dir_probe_matrix`
- Shape: `[220, 100]`: 1 task x 2 budgets x 3 providers
- Providers: `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`
- Fixture, task, query, and runtime payload remain unchanged
- Runtime payload remains `listing_entry_count=74`
- Selector and selected-unit truth remain `unsupported/opaque`
- Runtime provenance remains additive only
- Baseline providers remain empty at both budgets
- Released budget-pressure expansion files:
  - `evals/run_specs/oracle_signal_dir_probe_matrix.json`
  - `tests/test_eval_signal_dir_probe.py`

No source/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark claim widening is authorized. Release-facing docs remain
state-neutral for this eval-only expansion. Docs/evidence/continuity
reconciliation completed first-pass. Release-unit audit cleared first-pass.
Full regression cleared first-pass with `ruff check`, `ruff format --check`,
`mypy --strict`, and `pytest tests/ -v` reporting `709 passed`.
Commit-gating completed; local commit creation completed at `ad9db8d`; and
Ryan-authorized push completed at `ad9db8d`.

Release-gate status is no-active-gate for `ad9db8d`: do not route back to
docs review, release-unit audit, full regression, commit-gating, staging,
local commit creation, or push for this tranche absent new findings. No active
route remains to commit-gating, staging, local commit creation, or push for
`ad9db8d` absent new findings.

`43d0439 Expand getattr AttributeError eval budget coverage` is an older
pushed code/eval release authority for the internal eval-only
`REFLECTIVE_BUILTIN` / `getattr(obj, name)` raised-`AttributeError`
budget-pressure expansion at `[220, 100]`: 1 task x 2 budgets x 3 providers.
There is no active release gate for `43d0439` absent new findings.

`5bd0616 Add getattr AttributeError eval probe` is an older pushed code/eval
release authority for the initial internal eval-only `REFLECTIVE_BUILTIN` /
`getattr(obj, name)` raised-`AttributeError` pilot at budget 220. `6ac1e28 Add
builtins-alias dynamic import eval probe` remains the earlier pushed release
authority for the internal eval-only `DYNAMIC_IMPORT` /
builtins-alias `loader.__import__(name)` probe. `3dfc355 Add
builtins-attribute dynamic import eval probe` remains an older pushed
builtins-attribute release authority. `b85f038 Add root-alias dynamic import
eval probe` remains an older root-module alias dynamic-import release
authority. `4030845 Add imported-alias dynamic import eval probe`,
`ee71a82 Add imported-name dynamic import eval probe`, `397c7dd Add builtin
dynamic import eval probe`, and `14b362e Add dynamic import root runtime eval
pilot` remain earlier released dynamic-import authorities and must not be
reopened absent new findings.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` /
builtins-alias `loader.__import__(name)` release at `6ac1e28` is:

- Source/contract prerequisite accepted first-pass:
  - exact unshadowed `import builtins as loader` plus exactly
    `loader.__import__(name)` is classified as unsupported `DYNAMIC_IMPORT`
  - runtime provenance can attach to that exact unsupported boundary
  - existing `import builtins` plus `builtins.__import__(name)` behavior is
    preserved
  - shadowed/rebound/non-builtins/wrong-arity/literal forms remain generic or
    deferred
  - changed files are `src/context_ir/dependency_frontier.py`,
    `src/context_ir/runtime_acquisition.py`,
    `tests/test_dependency_frontier.py`, and
    `tests/test_runtime_acquisition.py`
- Eval-only sibling accepted first-pass:
  - matrix is `oracle_signal_dynamic_import_builtins_alias_probe_matrix`
  - shape is 1 task x 1 budget x 3 providers at budget 220
  - providers are `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `import builtins as loader`,
    `name = "plugins.weather"`, and exactly `loader.__import__(name)`, with
    bounded `sys.modules[name]`
    retrieval only
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or selected symbol is created from `plugins.weather`
  - asset/test files are:
    - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/eval_runtime_observations.json`
    - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/main.py`
    - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/plugins/__init__.py`
    - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/plugins/weather.py`
    - `evals/run_specs/oracle_signal_dynamic_import_builtins_alias_probe_matrix.json`
    - `evals/tasks/oracle_signal_dynamic_import_builtins_alias_probe.json`
    - `tests/test_eval_signal_dynamic_import_builtins_alias_probe.py`

The docs/evidence/continuity reconciliation was accepted after one
correction. The release-unit audit cleared first-pass. Full regression cleared
first-pass with `702 passed`. The first commit-gating review rejected with P1
stale-routing findings in `PLAN.md` and `BUILDLOG.md`; a later PLAN-only
stale-route correction was accepted first-pass; corrected commit-gating cleared
first-pass; local commit creation completed at `6ac1e28`; and Ryan-authorized
push completed at `6ac1e28`.

There is no active release gate for `6ac1e28`: do not route back to
release-unit audit, full regression, commit-gating, staging, local commit
creation, or push for this tranche absent new findings. The post-`6ac1e28`
route is superseded by the completed and pushed `5bd0616` getattr
AttributeError release.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` / root-module
alias `loader.import_module(name)` sibling pilot was released at
`b85f038 Add root-alias dynamic import eval probe`. Its pilot assets are:

- `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/eval_runtime_observations.json`
- `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/main.py`
- `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/plugins/__init__.py`
- `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/plugins/weather.py`
- `evals/run_specs/oracle_signal_dynamic_import_root_alias_probe_matrix.json`
- `evals/tasks/oracle_signal_dynamic_import_root_alias_probe.json`
- `tests/test_eval_signal_dynamic_import_root_alias_probe.py`

The released matrix is
`oracle_signal_dynamic_import_root_alias_probe_matrix`: 1 task x 1 budget x 3
providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary is
`import importlib as loader`, `name = "plugins.weather"`, and exactly
`loader.import_module(name)`. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, and no
dependency edge or selected symbol is created from `plugins.weather`. No
root-module `importlib.import_module(name)` expansion, imported-name
`import_module(name)` expansion, imported-alias `load_module(name)` expansion,
literal dynamic import expansion, `__import__(name)`, `builtins.__import__`,
globals/locals/fromlist forms, namespace mutation, generated-code dependency
modeling, generalized dynamic import support,
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening, product surface, schema, scoring, optimizer, compiler, or
winner-selection widening is authorized.

The first docs/evidence/continuity reconciliation for the root-module alias
pilot was rejected with a P1 state-neutrality finding because release-facing
docs described the evidence with live workspace-state wording. The corrected
docs/evidence/continuity reconciliation is accepted; release-facing docs remain
state-neutral. The root-module alias implementation/assets were accepted
workspace-only before release; the corrected docs reconciliation was accepted
after one P1 state-neutrality correction; the release-unit audit cleared
first-pass; full regression cleared first-pass with `688 passed`;
commit-gating cleared first-pass; local commit creation completed at
`b85f038`; and Ryan-authorized push completed at `b85f038`.

There is no active release gate for `b85f038`: do not route back to
release-unit audit, full regression, commit-gating, staging, local commit
creation, or push for this tranche absent new findings.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` / imported-alias
`load_module(name)` sibling pilot was released at
`4030845 Add imported-alias dynamic import eval probe`. Its pilot assets are:

- `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/eval_runtime_observations.json`
- `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/main.py`
- `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/plugins/__init__.py`
- `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/plugins/weather.py`
- `evals/run_specs/oracle_signal_dynamic_import_imported_alias_probe_matrix.json`
- `evals/tasks/oracle_signal_dynamic_import_imported_alias_probe.json`
- `tests/test_eval_signal_dynamic_import_imported_alias_probe.py`

The released matrix is
`oracle_signal_dynamic_import_imported_alias_probe_matrix`: 1 task x 1 budget
x 3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is `from importlib import import_module as load_module`,
`name = "plugins.weather"`, and exactly `load_module(name)`. The runtime
payload is `imported_module=plugins.weather`. Primary selector and
selected-unit truth remain `unsupported/opaque`, runtime provenance remains
additive only, and no dependency edge or selected symbol is created from
`plugins.weather`. No root-module `importlib.import_module(name)` expansion,
imported-name `import_module(name)` expansion, literal
`load_module("plugins.weather")` expansion, `loader.import_module(name)`,
`__import__(name)`, `builtins.__import__`, globals/locals/fromlist forms,
namespace mutation, generated-code dependency modeling, generalized dynamic
import support,
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening, product surface, schema, scoring, optimizer, compiler, or
winner-selection widening is authorized.

The release-unit audit for `4030845` cleared first-pass. Full regression
cleared first-pass with `682 passed`. The first commit-gating review rejected
with P1 stale-routing findings in `PLAN.md` and `BUILDLOG.md`; the continuity
correction was accepted first-pass; corrected commit-gating cleared
first-pass; local commit creation completed at `4030845`; Ryan-authorized push
completed at `4030845`.

There is no active release gate for `4030845`: do not route back to
release-unit audit, full regression, commit-gating, staging, local commit
creation, or push for this tranche absent new findings. The prior fresh
post-imported-alias next-move route is superseded by the completed
root-module alias release at `b85f038` and the post-root-alias
planning/control route above.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` / imported-name
`import_module(name)` sibling pilot was released at
`ee71a82 Add imported-name dynamic import eval probe`. Its pilot assets are:

- `evals/fixtures/oracle_signal_dynamic_import_imported_name_probe/`
- `evals/tasks/oracle_signal_dynamic_import_imported_name_probe.json`
- `evals/run_specs/oracle_signal_dynamic_import_imported_name_probe_matrix.json`
- `tests/test_eval_signal_dynamic_import_imported_name_probe.py`

The released matrix is
`oracle_signal_dynamic_import_imported_name_probe_matrix`: 1 task x 1 budget x
3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary is
`from importlib import import_module`, `name = "plugins.weather"`, and exactly
`import_module(name)`. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, and no
dependency edge or selected symbol is created from `plugins.weather`. No
root-module `importlib.import_module(name)` expansion, literal
`import_module("plugins.weather")` expansion, alias `load_module(name)`,
`loader.import_module(name)`, `__import__(name)`, `builtins.__import__`,
globals/locals/fromlist forms, generalized dynamic import support,
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening, product surface, schema, scoring, optimizer, compiler, or
winner-selection widening is authorized.

The release-unit audit for `ee71a82` cleared first-pass. Full regression
passed: `ruff check`, `ruff format --check`, `mypy --strict`, and
`pytest tests/ -v` with `676 passed`. The first commit-gating review returned
P1 continuity findings; the continuity correction was accepted; corrected
commit-gating cleared; local commit creation completed; Ryan-authorized push
completed at `ee71a82`.

There is no active release gate for `ee71a82` or `4030845`: do not route back
to release-unit audit, full regression, commit-gating, staging, local commit
creation, or push for those tranches absent new findings. The
post-imported-alias route should move to a fresh bounded next-move
planning/control decision, not implementation and not release handling. Do
not reopen `4030845`, `ee71a82`, `397c7dd`, `14b362e`, `bcd6d68`, or
`96fc03a` absent new findings.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` / root-module
`importlib.import_module(name)` sibling pilot was released at
`14b362e Add dynamic import root runtime eval pilot`. Its pilot assets are:

- `evals/fixtures/oracle_signal_dynamic_import_root_probe/`
- `evals/tasks/oracle_signal_dynamic_import_root_probe.json`
- `evals/run_specs/oracle_signal_dynamic_import_root_probe_matrix.json`
- `tests/test_eval_signal_dynamic_import_root_probe.py`

The pushed matrix is `oracle_signal_dynamic_import_root_probe_matrix`: 1 task x
1 budget x 3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is `import importlib`, `name = "plugins.weather"`, and exactly
`importlib.import_module(name)`. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, and no
dependency edge or symbol is created from the dynamically imported module. No
`__import__(name)`, imported-name `import_module(name)`, alias or loader forms,
generalized dynamic import support, public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening, product surface, schema, scoring, optimizer, compiler, or
winner-selection widening is authorized.

The release-unit audit for `14b362e` cleared first-pass. Full regression passed:
`ruff check`, `ruff format --check`, `mypy --strict`, and
`pytest tests/ -v` with `664 passed`. Commit-gating cleared first-pass. Local
commit creation and Ryan-authorized push completed at `14b362e`.

The completed and pushed internal eval-only `DYNAMIC_IMPORT` / builtin
`__import__(name)` sibling pilot was released at
`397c7dd Add builtin dynamic import eval probe`. Its pilot assets are:

- `evals/fixtures/oracle_signal_dynamic_import_builtin_probe/`
- `evals/tasks/oracle_signal_dynamic_import_builtin_probe.json`
- `evals/run_specs/oracle_signal_dynamic_import_builtin_probe_matrix.json`
- `tests/test_eval_signal_dynamic_import_builtin_probe.py`

The released matrix is `oracle_signal_dynamic_import_builtin_probe_matrix`: 1
task x 1 budget x 3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is `name = "plugins.weather"` and exactly `__import__(name)`, with bounded
`sys.modules[name]` retrieval only. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, and no
dependency edge or symbol is created from `plugins.weather`. No
`importlib.import_module(name)`, imported-name `import_module(name)`, alias or
loader forms, `builtins.__import__`, globals/locals/fromlist forms,
generalized dynamic import support, public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening, product surface, schema, scoring, optimizer, compiler, or
winner-selection widening is authorized.

The release-unit audit for `397c7dd` cleared first-pass. Full regression
passed: `ruff check`, `ruff format --check`, `mypy --strict`, and
`pytest tests/ -v` with `670 passed`. Commit-gating cleared first-pass. Local
commit creation and Ryan-authorized push completed at `397c7dd`.

`bcd6d68 Add exec source runtime eval pilot` remains the prior pushed
exec(source) release. It adds the narrow internal eval-only `EXEC_OR_EVAL` /
`exec(source)` evidence through `oracle_signal_exec_probe_matrix`: 1 task x 1
budget x 3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture/call
boundary is `source = "pass"` and exactly `exec(source)`; the executed source
parses as exactly one `ast.Pass`. The runtime proof boundary is
`execution_outcome=completed`, `source_shape=literal_statement`,
`source_sha256 == sha256(b"pass")`, and non-empty
`durable_payload_reference`; optional `statement_kind=pass` is additive
summary only. Runtime provenance attaches only to the preserved `EXEC_OR_EVAL`
unsupported finding for `exec(source)`. Primary selector and selected-unit
truth remain `unsupported/opaque`, additive runtime provenance remains
separate from primary truth, no dependency edge or symbol is created from
executed source, no namespace mutation modeling is added, no generated-code
dependency modeling is added, and public comparative claims remain bounded to
the existing quad matrix. The release-unit audit initially found one P1
digest-boundary issue; the correction pinned `source_sha256` to
`sha256(b"pass")`; the audit rerun cleared; full regression passed;
commit-gating cleared; local commit creation completed; Ryan-authorized push
completed. Do not reopen `bcd6d68` exec(source) absent new findings.

`96fc03a Add eval runtime eval pilot` remains the prior eval(source) release
authority. It adds the narrow internal eval-only `EXEC_OR_EVAL` /
`eval(source)` evidence through `oracle_signal_eval_probe_matrix`: 1 task x 1
budget x 3 providers at budget 220, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The runtime
payload/proof boundary is `evaluation_outcome=returned_value`,
`source_shape=literal_expression`, valid `source_sha256`, and non-empty
`durable_payload_reference`; optional `result_type=builtins.str` is additive
summary only. Runtime provenance attaches only to the preserved
`EXEC_OR_EVAL` unsupported finding for `eval(source)`. Primary selector and
selected-unit truth remain `unsupported/opaque`, additive runtime provenance
remains separate from primary truth, and public comparative claims remain
bounded to the existing quad matrix. Do not reopen `96fc03a` eval(source)
absent new findings.

There is no active release gate for `bcd6d68` or `96fc03a`.

Prior pushed release anchors remain: `f0efbef` for the internal eval-only
`REFLECTIVE_BUILTIN` / zero-argument `dir()` provider matrix; `19d9a32` for
the internal eval-only
`METACLASS_BEHAVIOR` / preserved `metaclass=...` keyword-site provider matrix;
`38e9d5f` for the initial internal
eval-only `RUNTIME_MUTATION` / `locals()` pilot; `5f74ede` for the internal
eval-only `RUNTIME_MUTATION` / `globals()` budget expansion; `631a303` for the
initial `globals()` pilot; `9eec985` for the zero-argument `vars()` budget
expansion; `71db72e` for the initial zero-argument `vars()` pilot; `2c6b54a`
for the `vars(obj)` budget expansion; `ead239d` for the initial `vars(obj)`
pilot; `1b555ef` for the `getattr` family budget expansion; `d8ebdc3` for
runtime-outcome accounting; `b014595`, `7d43302`, and `c592dca` for the
accepted `getattr` runtime-backed family releases; `762dd51` and `90dcc15` for
`hasattr(obj, name)`; `9a52b46` for `DYNAMIC_IMPORT`; `215b6bb` for
provider-scoped selected-unit capability-tier accounting; and `a605b22` for
the capability-tier eval / evidence baseline.

The active release model is tranche-based, not slice-by-slice. Accepted slices may accumulate locally with continuity synced in workspace until they form one coherent release unit. For a future release unit that has not already cleared gates, the control lane should request one dedicated findings-first deep release-unit audit over the whole accumulated diff, then run the full regression gate, then do commit-gating, commit, and push. The `c1a12d7` dir(obj) release has already completed those gates and must not reopen audit, regression, commit-gating, staging, local commit, or push handling absent new findings.

## Evidence-Building Cadence Guardrails

These streamlining guardrails standardize repeatable mechanics without
weakening findings-first review, release-unit audit, full regression,
commit-gating, human push authorization, or claim-boundary discipline.

During the current internal evidence-building mode, future control lanes may
reuse a standard eval-pilot packet for repeated internal evidence slices: one
bounded task/fixture/run-spec packet, explicit provider and budget shape,
runtime proof boundary, selector/selected-unit truth boundary, docs
reconciliation checklist, and the exact validation commands needed for that
pilot. The packet is a prompt scaffold only; it does not open the next lane or
widen scope by itself.

Docs reconciliation for these pilots should use stable wording: name the
matrix, state task x budget x provider shape, list providers and budgets, state
runtime proof as additive, preserve `unsupported/opaque` primary truth when
applicable, and restate the public claim boundary. Avoid recording every
transient handoff; after several related pilots, consolidate at the family
level when the durable evidence story is clearer.

Before commit-gating any accumulated evidence release unit, the control lane
must run an explicit release-state checklist: branch/HEAD/origin state,
staged/unstaged file set, included/excluded files, active holds,
release-unit audit status, full-regression status, and whether human push
sign-off exists. Common guard checks should also look for dirty-file surprises,
forbidden diffs outside the slice/doc set, stale routing language, run-spec
shape drift, and claim widening.

Budget expansion remains a control question, not an automatic next step.
Consider it only when a first-budget pilot leaves a specific unanswered
comparison or coverage question, the run-spec shape can stay bounded, and
claim boundaries remain unchanged.

This section is a standing process note only. It does not change `AGENTS.md`,
alter any pushed dir(obj) release authority, claim new evidence or capability,
or route to commit or push. It does not require a follow-on continuity pass.

The `2dd8404` locals budget-expansion release passed implementation review,
same-tranche docs reconciliation, release-unit audit, full regression,
corrected commit-gating, local commit creation, and Ryan-authorized push. It is
no longer pending any release gate. The next lane should make a fresh control
decision on the next north-star move rather than reopen release sequencing for
`2dd8404` absent new findings.

The `c1a12d7 Add dir(obj) eval pilot` release passed implementation review,
docs/evidence reconciliation after correction, process guardrail note
acceptance, release-unit audit, full regression after one formatting correction
with `607 passed`, corrected commit-gating, local commit creation, and
Ryan-authorized push. It is no longer pending any release gate. The next lane
should make a fresh control-lane north-star decision rather than reopen release
sequencing for `c1a12d7` absent new findings.

## What Is Complete

- [x] Slice 0: project bootstrap
- [x] Docs freeze / continuity reset: repo authority now points to the semantic-first baseline instead of the retired frozen spec
- [x] Retrospective findings preserved as historical evidence in BUILDLOG.md
- [x] Semantic contracts and types accepted after 1 correction
- [x] Syntax parser reset accepted after 1 correction
- [x] Syntax parse-failure correction accepted
- [x] Parameter-facts prerequisite correction accepted
- [x] Binder and scope model accepted first-pass
- [x] Resolver and object model accepted after 1 correction
- [x] Semantic dependency graph and frontier accepted first-pass
- [x] Renderer reset accepted first-pass
- [x] Scorer reset accepted first-pass
- [x] Optimizer / compile reset accepted after 1 correction
- [x] Diagnose / recompile reset accepted after 1 correction
- [x] Final-phase MCP / eval / portfolio-facing planning accepted first-pass
- [x] Semantic analyzer public contract accepted first-pass
- [x] Package-root public API and legacy quarantine accepted first-pass
- [x] Tool-facing facade contract accepted first-pass
- [x] Minimal MCP wrapper accepted first-pass after dependency/protocol authorization
- [x] Eval methodology and evidence baseline accepted first-pass
- [x] Capability-tier eval / evidence baseline milestone released to repo-backed authority at `a605b22`
- [x] Tier-aware eval storage-contract slice released at `a605b22`
- [x] Isolated internal `DYNAMIC_IMPORT` eval pilot released at `a605b22`
- [x] Post-pilot capability-tier eval internal-accounting planning spike accepted first-pass
- [x] Tier-aware eval summary/report internal-accounting rollout accepted after 1 correction
- [x] Full regression gate for the enlarged workspace-only eval/evidence unit accepted first-pass
- [x] Commit-gating review for the enlarged workspace-only eval/evidence unit accepted first-pass
- [x] Local commit creation for the coherent capability-tier eval/evidence release unit accepted first-pass at `a605b22`
- [x] Remote push for the coherent capability-tier eval/evidence release unit accepted first-pass at `a605b22`
- [x] Docs-only continuity sync and push authorization accepted after 1 correction
- [x] Docs-only continuity push completed through `d1265fe`
- [x] Post-release provider-scoped capability-tier accounting planning spike accepted first-pass
- [x] Provider-scoped selected-unit capability-tier accounting implementation accepted first-pass
- [x] Full regression gate for provider-scoped selected-unit capability-tier accounting accepted first-pass
- [x] Commit-gating review and local commit creation for provider-scoped selected-unit capability-tier accounting accepted first-pass at `215b6bb`
- [x] Remote push for provider-scoped selected-unit capability-tier accounting completed at `215b6bb`
- [x] README / public-claim sync accepted first-pass
- [x] Release sequencing completed to `origin/main` at `9abc57c`
- [x] Post-provider-scoped `DYNAMIC_IMPORT` evidence-broadening planning spike accepted first-pass
- [x] Internal `DYNAMIC_IMPORT` provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review for internal `DYNAMIC_IMPORT` provider/budget matrix expansion accepted first-pass
- [x] Release-unit audit workflow correction accepted with human sign-off
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` provider/budget matrix expansion accepted first-pass
- [x] Local commit creation for internal `DYNAMIC_IMPORT` provider/budget matrix expansion accepted first-pass at `9a52b46`
- [x] Remote push for internal `DYNAMIC_IMPORT` provider/budget matrix expansion completed at `9a52b46`
- [x] Execution-lane overreach continuity correction accepted first-pass
- [x] Control review of `hasattr(obj, name)` runtime-backed eval pilot recommendation accepted first-pass
- [x] Internal `hasattr(obj, name)` runtime-backed eval pilot implementation accepted first-pass as workspace-only state
- [x] Payload-shape correction for internal `hasattr(obj, name)` runtime-backed eval pilot accepted first-pass
- [x] Corrected release-unit audit for internal `hasattr(obj, name)` runtime-backed eval pilot accepted first-pass
- [x] Full regression gate for internal `hasattr(obj, name)` runtime-backed eval pilot accepted first-pass
- [x] Commit-gating review and local commit creation for internal `hasattr(obj, name)` runtime-backed eval pilot accepted first-pass at `90dcc15`
- [x] Remote push for internal `hasattr(obj, name)` runtime-backed eval pilot completed at `90dcc15`
- [x] Runtime-backed evidence/claim docs reconciliation accepted first-pass
- [x] Commit-gating review and local commit creation for runtime-backed evidence/claim docs reconciliation accepted first-pass at `3291268`
- [x] Remote push for runtime-backed evidence/claim docs reconciliation completed at `3291268`
- [x] Continuity-loop correction and tranche-cadence reset accepted first-pass at `8133e0a`
- [x] Post-`hasattr`-pilot matrix-broadening planning spike accepted first-pass
- [x] Internal `hasattr(obj, name)` provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for internal `hasattr(obj, name)` provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review and local commit creation for internal `hasattr(obj, name)` provider/budget matrix expansion accepted first-pass at `762dd51`
- [x] Remote push for internal `hasattr(obj, name)` provider/budget matrix expansion completed at `762dd51`
- [x] Post-`762dd51` runtime-family planning spike accepted first-pass
- [x] Internal `getattr(obj, name)` runtime-backed eval pilot implementation accepted after 1 correction as workspace-only tranche state
- [x] Post-`getattr(obj, name)` same-tranche docs/evidence reconciliation decision accepted first-pass
- [x] Same-tranche docs/evidence reconciliation for internal `getattr(obj, name)` tranche accepted first-pass
- [x] Release-unit audit for internal `getattr(obj, name)` tranche accepted first-pass
- [x] Full regression gate for internal `getattr(obj, name)` tranche accepted first-pass
- [x] Commit-gating review and local commit creation for internal `getattr(obj, name)` tranche accepted first-pass at `c592dca`
- [x] Remote push for internal `getattr(obj, name)` tranche completed at `c592dca`
- [x] Post-`c592dca` defaulted `getattr(obj, name, default)` eval planning spike accepted first-pass
- [x] `EVAL.md` authority correction accepted first-pass as workspace-only tranche state
- [x] Internal defaulted `getattr(obj, name, default)` eval pilot implementation accepted first-pass as workspace-only tranche state
- [x] Same-tranche docs/evidence reconciliation for defaulted `getattr(obj, name, default)` accepted first-pass as workspace-only tranche state
- [x] Release-unit audit for defaulted `getattr(obj, name, default)` tranche accepted first-pass
- [x] Full regression gate for defaulted `getattr(obj, name, default)` tranche accepted first-pass
- [x] Release-doc wording correction for defaulted `getattr(obj, name, default)` accepted first-pass after human sign-off
- [x] Commit-gating review for defaulted `getattr(obj, name, default)` tranche accepted first-pass
- [x] Local commit creation for defaulted `getattr(obj, name, default)` tranche accepted first-pass at `7d43302`
- [x] Remote push for defaulted `getattr(obj, name, default)` tranche completed at `7d43302`
- [x] Post-`7d43302` defaulted `getattr(obj, name, default)` value-return branch planning spike accepted first-pass
- [x] Internal defaulted `getattr(obj, name, default)` value-return branch eval pilot implementation accepted first-pass as workspace-only tranche state
- [x] Same-tranche docs/evidence reconciliation for defaulted `getattr(obj, name, default)` value-return branch accepted first-pass as workspace-only tranche state
- [x] Release-unit audit for defaulted `getattr(obj, name, default)` value-return branch tranche accepted first-pass
- [x] Full regression gate for defaulted `getattr(obj, name, default)` value-return branch tranche accepted first-pass
- [x] Commit-gating review for defaulted `getattr(obj, name, default)` value-return branch tranche accepted first-pass
- [x] Local commit creation for defaulted `getattr(obj, name, default)` value-return branch tranche accepted first-pass at `b014595`
- [x] Remote push for defaulted `getattr(obj, name, default)` value-return branch tranche completed at `b014595`
- [x] Post-`b014595` runtime-outcome methodology/reporting planning spike accepted first-pass
- [x] Runtime-outcome methodology/reporting hardening implementation accepted first-pass as workspace-only state
- [x] Release-unit audit for runtime-outcome methodology/reporting hardening accepted first-pass
- [x] Full regression gate for runtime-outcome methodology/reporting hardening accepted first-pass
- [x] Commit-gating review for runtime-outcome methodology/reporting hardening accepted first-pass
- [x] Local commit creation for runtime-outcome methodology/reporting hardening accepted first-pass at `d8ebdc3`
- [x] Remote push for runtime-outcome methodology/reporting hardening completed at `d8ebdc3`
- [x] Post-`d8ebdc3` `getattr` family evidence-broadening planning spike accepted after 1 control correction
- [x] `EVAL.md` release-anchor attribution correction accepted first-pass as workspace-only state
- [x] `getattr` family provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for the `getattr` family provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Release-unit audit for the `getattr` family provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for the `getattr` family provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review for the `getattr` family provider/budget matrix expansion accepted first-pass
- [x] Local commit creation for the `getattr` family provider/budget matrix expansion accepted first-pass at `1b555ef`
- [x] Remote push for the `getattr` family provider/budget matrix expansion completed at `1b555ef`
- [x] Post-`d9be4d5` `vars(obj)` internal eval evidence planning spike accepted first-pass
- [x] Internal `vars(obj)` runtime-backed eval pilot implementation accepted first-pass
- [x] Same-tranche docs/evidence reconciliation for internal `vars(obj)` pilot accepted after 1 correction
- [x] Release-unit audit for internal `vars(obj)` tranche accepted first-pass
- [x] Full regression gate for internal `vars(obj)` tranche accepted first-pass
- [x] Commit-gating review for internal `vars(obj)` tranche accepted first-pass
- [x] Post-`ead239d` `vars(obj)` budget-expansion planning spike accepted first-pass
- [x] Internal `vars(obj)` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `vars(obj)` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Corrected release-unit audit for internal `vars(obj)` provider/budget matrix expansion accepted after 1 correction
- [x] Full regression gate for internal `vars(obj)` provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review for internal `vars(obj)` provider/budget matrix expansion accepted first-pass
- [x] Internal zero-argument `vars()` eval pilot implementation accepted first-pass for the accumulated release candidate
- [x] Same-tranche docs/evidence reconciliation for internal zero-argument `vars()` pilot accepted first-pass for the accumulated release candidate
- [x] Release-unit audit for internal zero-argument `vars()` release candidate accepted first-pass
- [x] Full regression gate for internal zero-argument `vars()` release candidate accepted first-pass
- [x] Commit-gating review for internal zero-argument `vars()` release candidate accepted first-pass
- [x] Post-`71db72e` zero-argument `vars()` budget-expansion planning spike accepted first-pass
- [x] Internal zero-argument `vars()` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal zero-argument `vars()` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Release-unit audit for internal zero-argument `vars()` provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for internal zero-argument `vars()` provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review for internal zero-argument `vars()` provider/budget matrix expansion accepted first-pass
- [x] Post-`9eec985` globals-family planning spike accepted first-pass
- [x] Internal `globals()` eval pilot implementation accepted first-pass
- [x] Same-tranche docs/evidence reconciliation for internal `globals()` eval pilot accepted first-pass
- [x] Release-unit audit for internal `globals()` eval pilot accepted first-pass
- [x] Full regression gate for internal `globals()` eval pilot accepted first-pass
- [x] Commit-gating review for internal `globals()` eval pilot accepted first-pass
- [x] Post-`631a303` globals budget-expansion planning spike accepted first-pass
- [x] Internal `globals()` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `globals()` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Release-unit audit for internal `globals()` provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for internal `globals()` provider/budget matrix expansion accepted first-pass
- [x] Commit-gating review for internal `globals()` provider/budget matrix expansion accepted first-pass
- [x] Deterministic fixture-level eval design accepted after 2 corrections
- [x] Eval oracle foundation accepted after 1 correction
- [x] Deterministic provider/baseline infrastructure accepted after 1 correction
- [x] Deterministic metric scoring core accepted first-pass
- [x] Deterministic raw result record core accepted after 1 correction
- [x] Deterministic multi-run ledger production accepted first-pass
- [x] Deterministic ledger summary rendering accepted after 1 correction
- [x] Deterministic internal eval report artifact accepted first-pass
- [x] Deterministic internal eval pipeline composition accepted after 1 correction
- [x] Deterministic internal eval run manifest accepted first-pass
- [x] Deterministic internal eval bundle directory accepted first-pass
- [x] Methodology-tightened signal smoke eval assets accepted first-pass
- [x] Signal smoke Context IR recovery accepted first-pass
- [x] Signal smoke competitive recovery accepted first-pass
- [x] Second methodology-tightened signal asset and two-asset matrix accepted first-pass
- [x] Two-asset signal evidence review accepted first-pass
- [x] Signal smoke B semantic recovery accepted first-pass
- [x] Third methodology-tightened signal asset and three-asset matrix accepted first-pass
- [x] Three-asset signal evidence review accepted first-pass
- [x] Signal smoke C edit-target recovery accepted first-pass
- [x] Post-recovery triple-matrix evidence review accepted first-pass
- [x] Smoke C 240 budget-envelope widened correction accepted first-pass
- [x] Post-correction triple-matrix evidence review accepted first-pass
- [x] Smoke B support-selection budget-pressure correction accepted with human sign-off
- [x] Post-support-correction triple-matrix evidence review accepted first-pass
- [x] Remaining helper-support budget-pressure correction accepted first-pass
- [x] Post-helper-correction triple-matrix evidence review accepted first-pass
- [x] Core uncertainty-surfacing correction accepted first-pass
- [x] Post-core-correction triple-matrix evidence review accepted first-pass
- [x] Noise-tightening correction accepted first-pass
- [x] Outward-facing artifact planning spike accepted first-pass
- [x] Portfolio technical brief accepted first-pass
- [x] Portfolio-readiness gap assessment spike accepted first-pass
- [x] Portfolio reviewer overview accepted first-pass
- [x] Post-overview portfolio-readiness planning spike accepted first-pass
- [x] Portfolio case-study source accepted first-pass
- [x] Post-case-study portfolio-readiness planning spike accepted after 1 control correction with human sign-off
- [x] Portfolio case study accepted first-pass
- [x] Post-polished-case-study portfolio-readiness planning spike accepted first-pass
- [x] North-star rebaseline planning spike accepted after 1 control correction with human sign-off
- [x] Capability-tier rebaseline control-state sync accepted first-pass
- [x] Phase-1 capability-tier contract/decomposition slice accepted first-pass
- [x] `SemanticProgram` provenance schema/types slice accepted first-pass
- [x] Runtime-backed evidence admissibility boundary slice accepted first-pass
- [x] Runtime-backed provenance metadata schema alignment slice accepted first-pass
- [x] Runtime-backed acquisition infrastructure slice accepted after 1 correction
- [x] Tier-aware ranking, optimization, and compile propagation slice accepted after 1 correction
- [x] Tier-aware diagnose/recompile and internal evidence gate slice accepted first-pass
- [x] Phase-2 hybrid-coverage priority and decomposition spike accepted after 1 control correction with human sign-off
- [x] Same-class `self.foo()` receiver call-resolution slice accepted first-pass
- [x] Object-model reflection-hook priority and decomposition spike accepted after 1 control correction with human sign-off
- [x] Same-class `__getattribute__` proof-guard slice accepted first-pass
- [x] Same-class hook-aware unsupported-boundary slice accepted first-pass
- [x] Import-rooted module hook-boundary slice accepted first-pass
- [x] Post-hook phase-2 priority and decomposition spike accepted after 1 control correction with human sign-off
- [x] Direct-base inherited `__getattribute__` proof-guard slice accepted first-pass
- [x] Direct-base inherited hook-aware unsupported-boundary slice accepted first-pass
- [x] Direct-base inherited `self.foo()` proof-widening slice accepted first-pass
- [x] Post-direct-base-inherited phase-2 priority and decomposition spike accepted first-pass
- [x] Same-class canonical-self attribute-read proof slice accepted after 1 correction
- [x] Post-same-class-attribute-proof inherited-hook priority and decomposition spike accepted first-pass
- [x] Ancestor-closure `__getattribute__` proof-contraction slice accepted first-pass
- [x] Ancestor-closure hook-aware unsupported-boundary slice accepted first-pass
- [x] Order-free transitive sole-provider inherited `self.foo()` proof-widening slice accepted after 1 correction
- [x] Post-order-free-transitive inherited-call priority and decomposition spike accepted first-pass
- [x] Linear single-chain nearest-provider inherited `self.foo()` proof-widening slice accepted first-pass
- [x] Ordering-aware contract prerequisite spike accepted first-pass
- [x] Ordered direct-base ancestry contract slice accepted first-pass
- [x] Declared-base-order / branch-precedence inherited `self.foo()` selection on linear branch subtrees accepted after 1 correction
- [x] Post-linear-branch-precedence inherited-call priority and decomposition spike accepted first-pass
- [x] Overlapping linear shared-ancestor sole-provider inherited `self.foo()` widening accepted first-pass
- [x] Post-shared-ancestor-overlap inherited-call priority and decomposition spike accepted first-pass
- [x] Later-owner precedence on individually linear overlapping/shared-ancestor inherited `self.foo()` branches accepted after 1 correction
- [x] Post-later-owner-overlap inherited-call priority and decomposition spike accepted first-pass
- [x] First exclusive-branch owner precedence on individually linear overlapping/shared-ancestor inherited `self.foo()` branches accepted first-pass
- [x] Post-first-exclusive-overlap inherited-call priority and decomposition spike accepted first-pass
- [x] First true runtime-backed phase-2 hybrid-coverage priority spike accepted first-pass
- [x] First runtime-backed hybrid implementation slice for existing unsupported `importlib.import_module`-family `DYNAMIC_IMPORT` findings accepted first-pass
- [x] Post-first-runtime-backed-implementation exposure-boundary spike accepted first-pass
- [x] Tool-facade pass-through for accepted `importlib_runtime_observations` seam accepted first-pass
- [x] Post-tool-facade hybrid-entry exposure-boundary spike accepted first-pass
- [x] Reflective-builtin runtime-backed subfamily ranking spike accepted first-pass
- [x] Bounded `hasattr(obj, name)` runtime-backed implementation slice accepted first-pass
- [x] `getattr(...)` runtime-backed form-splitting spike accepted first-pass
- [x] Bounded `getattr(obj, name)` runtime-backed implementation slice accepted first-pass
- [x] `getattr(obj, name, default)` runtime-backed branch-semantics spike accepted first-pass
- [x] Bounded `getattr(obj, name, default)` runtime-backed implementation slice accepted first-pass
- [x] Post-`getattr` runtime-backed next-move spike accepted first-pass
- [x] Bounded `vars(obj)` runtime-backed implementation slice accepted first-pass
- [x] Post-`vars(obj)` runtime-backed next-move spike accepted first-pass
- [x] Zero-argument `vars()` runtime-backed contract spike accepted first-pass
- [x] Bounded zero-argument `vars()` runtime-backed implementation slice accepted first-pass
- [x] Deep-QA / release-gate spike accepted first-pass
- [x] Runtime-backed tranche release-sequencing spike accepted first-pass
- [x] Release-scope broadening decision accepted with human sign-off after hunk-isolation blocker
- [x] Broadened release-gate spike accepted first-pass
- [x] Broadened staged commit-candidate review accepted first-pass
- [x] Broadened local commit creation accepted first-pass
- [x] Broadened release unit remote-state verification accepted first-pass
- [x] `dir(obj)` runtime-backed contract spike accepted first-pass
- [x] Bounded `dir(obj)` runtime-backed implementation slice accepted first-pass
- [x] Zero-argument `dir()` runtime-backed contract spike accepted first-pass
- [x] Bounded zero-argument `dir()` runtime-backed implementation slice accepted first-pass
- [x] Post-reflective `RUNTIME_MUTATION` planning spike accepted first-pass
- [x] Reflective-queue continuity reconciliation accepted first-pass
- [x] Bounded `globals()` runtime-backed implementation slice accepted first-pass
- [x] Bounded `locals()` runtime-backed implementation slice accepted first-pass
- [x] Internal `locals()` provider/budget matrix expansion accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `locals()` provider/budget matrix expansion completed first-pass as workspace-only state
- [x] Release-unit audit for internal `locals()` provider/budget matrix expansion accepted first-pass
- [x] Full regression gate for internal `locals()` provider/budget matrix expansion accepted first-pass
- [x] Corrected commit-gating review for internal `locals()` provider/budget matrix expansion accepted after 1 correction
- [x] Local commit creation for internal `locals()` provider/budget matrix expansion accepted at `2dd8404`
- [x] Ryan-authorized remote push for internal `locals()` provider/budget matrix expansion completed at `2dd8404`
- [x] Post-`2dd8404` release-authority sync completed first-pass
- [x] `delattr(obj, name)` vs `setattr(obj, name, value)` mutation-planning spike accepted first-pass
- [x] Bounded `delattr(obj, name)` runtime-backed implementation slice accepted first-pass
- [x] `setattr(obj, name, value)` assigned-value contract spike accepted first-pass
- [x] Bounded `setattr(obj, name, value)` runtime-backed implementation slice accepted first-pass
- [x] `METACLASS_BEHAVIOR` runtime-backed contract spike accepted first-pass
- [x] Bounded `METACLASS_BEHAVIOR` runtime-backed implementation slice accepted first-pass
- [x] Deep-audit correction slice for `PLAN.md` truthfulness and runtime-acquisition negative coverage accepted first-pass
- [x] Runtime-backed tranche release sequencing completed to `origin/main` at `cb1dc65`
- [x] Internal `dir(obj)` eval-only provider matrix implementation accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `dir(obj)` eval-only provider matrix accepted after 1 correction as workspace-only state
- [x] Evidence-building process guardrail note accepted first-pass as workspace-only continuity state
- [x] Release-unit audit for internal `dir(obj)` eval-only provider matrix accepted first-pass with no findings
- [x] Full regression gate for internal `dir(obj)` eval-only provider matrix accepted first-pass after one formatting correction with `607 passed`
- [x] Corrected commit-gating review for internal `dir(obj)` eval-only provider matrix accepted first-pass
- [x] Local commit creation for internal `dir(obj)` eval-only provider matrix accepted at `c1a12d7`
- [x] Ryan-authorized remote push for internal `dir(obj)` eval-only provider matrix completed at `c1a12d7`
- [x] Internal `delattr(obj, name)` eval-only provider matrix implementation accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `delattr(obj, name)` eval-only provider matrix completed first-pass as workspace-only state
- [x] Release-unit audit for internal `delattr(obj, name)` eval-only provider matrix accepted first-pass with no findings
- [x] Full regression gate for internal `delattr(obj, name)` eval-only provider matrix accepted first-pass with `612 passed, 1 deselected`
- [x] Commit-gating review for internal `delattr(obj, name)` eval-only provider matrix accepted first-pass
- [x] Local commit creation and Ryan-authorized push for internal `delattr(obj, name)` eval-only provider matrix completed at `41f6b57`
- [x] Post-`41f6b57` runtime-mutation next-move planning spike accepted first-pass
- [x] Internal `setattr(obj, name, value)` eval-only provider matrix implementation accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `setattr(obj, name, value)` eval-only provider matrix accepted first-pass as workspace-only state
- [x] Release-unit audit for internal `setattr(obj, name, value)` eval-only provider matrix accepted first-pass with no findings
- [x] Full regression gate for internal `setattr(obj, name, value)` eval-only provider matrix accepted first-pass with `619 passed`
- [x] Commit-gating review for internal `setattr(obj, name, value)` eval-only provider matrix accepted first-pass
- [x] Local commit creation and Ryan-authorized push for internal `setattr(obj, name, value)` eval-only provider matrix completed at `f67bab7`
- [x] Post-`f67bab7` metaclass eval-matrix next-move planning spike accepted first-pass
- [x] Internal `METACLASS_BEHAVIOR` eval-only provider matrix implementation accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence reconciliation for internal `METACLASS_BEHAVIOR` eval-only provider matrix accepted first-pass as workspace-only state
- [x] Release-unit audit for internal `METACLASS_BEHAVIOR` eval-only provider matrix accepted first-pass with no findings
- [x] Full regression gate for internal `METACLASS_BEHAVIOR` eval-only provider matrix accepted first-pass with `624 passed`
- [x] Commit-gating review for internal `METACLASS_BEHAVIOR` eval-only provider matrix accepted first-pass
- [x] Local commit creation and Ryan-authorized push for internal `METACLASS_BEHAVIOR` eval-only provider matrix completed at `19d9a32`
- [x] Internal zero-argument `dir()` eval-only provider matrix implementation accepted first-pass as workspace-only state
- [x] Same-tranche docs/evidence/continuity reconciliation for internal zero-argument `dir()` eval-only provider matrix accepted after 1 correction
- [x] Release-unit audit for internal zero-argument `dir()` eval-only provider matrix cleared with no findings
- [x] Full regression gate for internal zero-argument `dir()` eval-only provider matrix cleared with `629 passed`
- [x] Corrected commit-gating review for internal zero-argument `dir()` eval-only provider matrix accepted first-pass
- [x] Local commit creation and Ryan-authorized push for internal zero-argument `dir()` eval-only provider matrix completed at `f0efbef`
- [x] `EXEC_OR_EVAL` / `eval(source)` contract spike accepted first-pass
- [x] Lower-layer `EXEC_OR_EVAL` / `eval(source)` runtime provenance seam accepted workspace-only after 1 correction
- [x] `oracle_signal_eval_probe_matrix` implementation/assets accepted workspace-only first-pass
- [x] Docs/evidence/continuity reconciliation for accumulated internal eval-only `EXEC_OR_EVAL` / `eval(source)` release unit accepted first-pass as workspace-only state
- [x] Local commit creation and Ryan-authorized push for internal `EXEC_OR_EVAL` / `eval(source)` runtime eval pilot completed at `96fc03a`
- [x] Lower-layer `EXEC_OR_EVAL` / `exec(source)` runtime provenance seam accepted first-pass and released at `bcd6d68`
- [x] `oracle_signal_exec_probe_matrix` implementation/assets accepted first-pass and released at `bcd6d68`
- [x] Docs/evidence/continuity reconciliation for accumulated internal eval-only `EXEC_OR_EVAL` / `exec(source)` release unit accepted first-pass
- [x] Release-unit audit for internal `EXEC_OR_EVAL` / `exec(source)` runtime eval pilot initially found one P1 digest-boundary issue; correction pinned `source_sha256` to `sha256(b"pass")`
- [x] Corrected release-unit audit for internal `EXEC_OR_EVAL` / `exec(source)` runtime eval pilot cleared
- [x] Full regression gate for internal `EXEC_OR_EVAL` / `exec(source)` runtime eval pilot passed
- [x] Commit-gating review for internal `EXEC_OR_EVAL` / `exec(source)` runtime eval pilot cleared
- [x] Local commit creation and Ryan-authorized push for internal `EXEC_OR_EVAL` / `exec(source)` runtime eval pilot completed at `bcd6d68`
- [x] Accepted workspace-only `EXEC_OR_EVAL` budget-pressure implementation
  first-pass: `oracle_signal_eval_probe_matrix` and
  `oracle_signal_exec_probe_matrix` expanded from `[220]` to `[220, 100]`
- [x] Internal eval-only `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)` sibling implementation accepted first-pass and released at `14b362e`
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)` runtime eval pilot cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)` runtime eval pilot passed with `664 passed`
- [x] Commit-gating review for internal `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)` runtime eval pilot cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / root-module `importlib.import_module(name)` runtime eval pilot completed at `14b362e`
- [x] Post-`14b362e` / `ad22ea6` builtin `__import__(name)` sibling planning and implementation slice accepted first-pass and released at `397c7dd`
- [x] Internal eval-only `DYNAMIC_IMPORT` / builtin `__import__(name)` sibling pilot released at `397c7dd` for `oracle_signal_dynamic_import_builtin_probe_matrix`
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / builtin `__import__(name)` runtime eval pilot cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / builtin `__import__(name)` runtime eval pilot passed with `670 passed`
- [x] Commit-gating review for internal `DYNAMIC_IMPORT` / builtin `__import__(name)` runtime eval pilot cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / builtin `__import__(name)` runtime eval pilot completed at `397c7dd`
- [x] Internal eval-only `DYNAMIC_IMPORT` / imported-name `import_module(name)` sibling implementation/assets accepted as workspace-only state for `oracle_signal_dynamic_import_imported_name_probe_matrix`
- [x] Docs/evidence/continuity reconciliation for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` accepted as workspace-only state
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot passed with `676 passed`
- [x] First commit-gating review for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot returned P1 continuity findings
- [x] Continuity correction for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot accepted
- [x] Corrected commit-gating review for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot cleared
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / imported-name `import_module(name)` runtime eval pilot completed at `ee71a82`
- [x] Post-`ee71a82` release routing sync completed at `5d2d7e4`
- [x] Internal eval-only `DYNAMIC_IMPORT` / imported-alias `load_module(name)` sibling implementation/assets accepted as workspace-only state for `oracle_signal_dynamic_import_imported_alias_probe_matrix`
- [x] Docs/evidence/continuity reconciliation for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` accepted as workspace-only state
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit cleared first-pass with `682 passed`
- [x] First commit-gating review for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit rejected with P1 stale-routing findings in `PLAN.md` and `BUILDLOG.md`
- [x] Continuity correction for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit accepted first-pass
- [x] Corrected commit-gating review for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / imported-alias `load_module(name)` release unit completed at `4030845`
- [x] Internal eval-only `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` sibling implementation/assets accepted as workspace-only state for `oracle_signal_dynamic_import_root_alias_probe_matrix`
- [x] Corrected docs/evidence/continuity reconciliation for internal `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` accepted after 1 correction
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` release unit cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` release unit cleared first-pass with `688 passed`
- [x] Commit-gating review for internal `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` release unit cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / root-module alias `loader.import_module(name)` release unit completed at `b85f038`
- [x] Source/contract prerequisite for exact unshadowed `import builtins` plus `builtins.__import__(name)` accepted first-pass as workspace-only state
- [x] Eval-only sibling `oracle_signal_dynamic_import_builtins_attr_probe_matrix` accepted first-pass as workspace-only state
- [x] Docs/evidence/continuity reconciliation for internal `DYNAMIC_IMPORT` / builtins-attribute `builtins.__import__(name)` accepted first-pass
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / builtins-attribute `builtins.__import__(name)` release candidate cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / builtins-attribute `builtins.__import__(name)` release candidate cleared first-pass with `696 passed`
- [x] Commit-gating review for internal `DYNAMIC_IMPORT` / builtins-attribute `builtins.__import__(name)` release unit cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / builtins-attribute `builtins.__import__(name)` release unit completed at `3dfc355`
- [x] Source/contract prerequisite for exact unshadowed `import builtins as loader` plus `loader.__import__(name)` accepted first-pass as workspace-only state
- [x] Eval-only sibling `oracle_signal_dynamic_import_builtins_alias_probe_matrix` accepted first-pass as workspace-only state
- [x] Corrected docs/evidence/continuity reconciliation for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` accepted after 1 correction
- [x] Release-unit audit for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate cleared first-pass
- [x] Full regression gate for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate cleared first-pass with `702 passed`
- [x] First commit-gating review for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate rejected with P1 stale-routing findings in `PLAN.md` and `BUILDLOG.md`
- [x] Continuity routing correction for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate accepted first-pass
- [x] Corrected commit-gating review for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate rejected with one P1 stale-route finding in `PLAN.md`
- [x] PLAN-only stale-route correction for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release candidate accepted first-pass
- [x] Corrected commit-gating review for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release unit cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal `DYNAMIC_IMPORT` / builtins-alias `loader.__import__(name)` release unit completed at `6ac1e28`
- [x] Internal eval-only `REFLECTIVE_BUILTIN` / `getattr(obj, name)`
  raised-`AttributeError` pilot implementation accepted first-pass as
  workspace-only state for `oracle_signal_getattr_attribute_error_probe_matrix`
- [x] Docs/evidence/continuity reconciliation for internal
  `REFLECTIVE_BUILTIN` / `getattr(obj, name)` raised-`AttributeError` pilot
  accepted after 2 corrections
- [x] Release-unit audit for internal `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot cleared first-pass
- [x] Full regression gate for internal `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot cleared first-pass with
  `709 passed`
- [x] First commit-gating review for internal `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot rejected with P1
  stale-routing findings in `PLAN.md` and `BUILDLOG.md`
- [x] Routing correction for internal `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot accepted first-pass
- [x] Corrected commit-gating review for internal `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot cleared first-pass
- [x] Local commit creation and Ryan-authorized push for internal
  `REFLECTIVE_BUILTIN` / `getattr(obj, name)` raised-`AttributeError`
  release unit completed at `5bd0616`
- [x] Post-5bd0616 North Star planning/control decision selected the
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion as the next smallest evidence-building capability wedge
- [x] Bounded `oracle_signal_getattr_attribute_error_probe_matrix`
  budget-pressure expansion from `[220]` to `[220, 100]` accepted first-pass
  as workspace-only state
- [x] Docs/evidence/continuity reconciliation for the workspace-only accepted
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion accepted first-pass
- [x] Release-unit audit for the workspace-only accepted
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion cleared first-pass
- [x] Full regression gate for the workspace-only accepted
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion cleared first-pass with `709 passed`
- [x] Commit-gating review for the
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion release unit completed
- [x] Local commit creation and Ryan-authorized push for the
  `oracle_signal_getattr_attribute_error_probe_matrix` budget-pressure
  expansion release unit completed at `43d0439`
- [x] Post-43d0439 North Star planning/control selected the
  `oracle_signal_dir_probe_matrix` budget-pressure expansion as the next
  smallest evidence-building capability wedge
- [x] Bounded `oracle_signal_dir_probe_matrix` budget-pressure expansion from
  `[220]` to `[220, 100]` accepted first-pass as workspace-only state
- [x] Docs/evidence/continuity reconciliation for the workspace-only accepted
  `oracle_signal_dir_probe_matrix` budget-pressure expansion accepted
  first-pass
- [x] Release-unit audit for the workspace-only accepted
  `oracle_signal_dir_probe_matrix` budget-pressure expansion cleared
  first-pass
- [x] Full regression gate for the workspace-only accepted
  `oracle_signal_dir_probe_matrix` budget-pressure expansion cleared
  first-pass with `709 passed`
- [x] Commit-gating review for the `oracle_signal_dir_probe_matrix`
  budget-pressure expansion release unit completed
- [x] Local commit creation and Ryan-authorized push for the
  `oracle_signal_dir_probe_matrix` budget-pressure expansion release unit
  completed at `ad9db8d`
- [x] Tranche batching / throughput discipline process-doc slice accepted
  first-pass by control review as workspace-only state
- [x] Corrected tranche batching / throughput discipline process-doc release
  unit passed the dedicated read-only release-unit audit rerun first-pass after
  one correction
- [x] Full regression over the current workspace for the corrected
  tranche-batching / throughput discipline process-doc release unit cleared
  first-pass with `ruff check`, `ruff format --check`, `mypy --strict`, and
  `pytest tests/ -v` reporting `709 passed`
- [x] First commit-gating review for the tranche-batching / throughput
  discipline process-doc release unit rejected with stale routing findings in
  `PLAN.md` and `BUILDLOG.md`
- [x] Corrected commit-gating review over `AGENTS.md`, `PLAN.md`, and
  `BUILDLOG.md` completed
- [x] Local commit creation and Ryan-authorized push for the tranche-batching /
  throughput discipline process-doc release unit completed at `125f088`
- [x] Internal eval-only `RUNTIME_MUTATION` / `delattr(obj, name)` budget
  expansion from `[220]` to `[220, 100]` accepted as workspace-only state
- [x] Internal eval-only `RUNTIME_MUTATION` / `setattr(obj, name, value)`
  budget expansion from `[220]` to `[220, 100]` accepted as workspace-only
  state
- [x] Findings-first control review for the docs/evidence/continuity
  reconciliation over the accepted workspace-only `delattr` and `setattr`
  budget expansion tranche accepted
- [x] Release-unit audit for the `RUNTIME_MUTATION` delattr/setattr
  budget-pressure tranche passed first-pass
- [x] Full regression gate for the audit-cleared `RUNTIME_MUTATION`
  delattr/setattr budget-pressure tranche cleared first-pass with
  `ruff check`, `ruff format --check`, `mypy --strict`, and
  `pytest tests/ -v` reporting `709 passed`
- [x] Commit-gating review for the `RUNTIME_MUTATION` delattr/setattr
  budget-pressure tranche completed
- [x] Local commit creation and Ryan-authorized push for the
  `RUNTIME_MUTATION` delattr/setattr budget-pressure release unit completed at
  `b8e126e`
- [x] Internal eval-only `DYNAMIC_IMPORT` sibling budget-pressure expansion
  across seven run specs and seven tests accepted after 1 correction as
  workspace-only state
- [x] Docs/evidence/continuity review for the `DYNAMIC_IMPORT` sibling
  budget-pressure release unit completed after 1 correction
- [x] Combined read-only release gate for the `DYNAMIC_IMPORT` sibling
  budget-pressure release unit completed
- [x] Full regression gate for the `DYNAMIC_IMPORT` sibling budget-pressure
  release unit cleared with `pytest tests/ -v` reporting `709 passed`
- [x] Commit-gating review for the `DYNAMIC_IMPORT` sibling budget-pressure
  release unit completed
- [x] Local commit creation and Ryan-authorized push for
  `c2c1898 Expand dynamic import sibling eval budget coverage` completed
- [x] Docs reconciliation for the internal `EXEC_OR_EVAL` eval/exec
  budget-pressure tranche accepted
- [x] Combined release-unit audit for the internal `EXEC_OR_EVAL` eval/exec
  budget-pressure release unit completed
- [x] Full regression gate for the internal `EXEC_OR_EVAL` eval/exec
  budget-pressure release unit cleared with `pytest tests/ -v` reporting
  `709 passed`
- [x] Commit-gating review for the internal `EXEC_OR_EVAL` eval/exec
  budget-pressure release unit completed
- [x] Local commit creation and Ryan-authorized push for
  `21f2dc5 Expand exec and eval budget coverage` completed
- [x] Internal eval-only zero-argument `dir()` and `METACLASS_BEHAVIOR`
  budget-pressure tranche implementation accepted first-pass
- [x] Docs/evidence/continuity reconciliation for the zero-argument `dir()` and
  `METACLASS_BEHAVIOR` budget-pressure tranche accepted after 1 correction
- [x] Combined release-unit audit for
  `e2f3dcf Expand dir-zero and metaclass budget coverage` passed
- [x] Full regression gate for
  `e2f3dcf Expand dir-zero and metaclass budget coverage` passed with
  `pytest tests/ -v` reporting `709 passed`
- [x] Commit-gating review for
  `e2f3dcf Expand dir-zero and metaclass budget coverage` passed
- [x] Local commit creation and Ryan-authorized push for
  `e2f3dcf Expand dir-zero and metaclass budget coverage` completed
- [x] Release-unit audit for
  `d73cde4 Expand original dynamic import budget coverage` completed
- [x] Focused validation for
  `d73cde4 Expand original dynamic import budget coverage` completed
- [x] Full regression gate for
  `d73cde4 Expand original dynamic import budget coverage` passed with
  `pytest tests/ -v` reporting `710 passed`
- [x] Commit-gating review for
  `d73cde4 Expand original dynamic import budget coverage` completed
- [x] Local commit creation and Ryan-authorized push for
  `d73cde4 Expand original dynamic import budget coverage` completed
- [x] Internal eval-only `REFLECTIVE_BUILTIN` `hasattr(obj, name)` false-branch
  and `vars(obj)` raised-`TypeError` tranche released at
  `546a4da Add reflective builtin branch eval probes`
- [x] Combined release gate for
  `546a4da Add reflective builtin branch eval probes` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `546a4da Add reflective builtin branch eval probes` completed
- [x] Runtime probe-request planning implementation accepted first-pass in
  workspace-only state
- [x] Combined release gate for
  `f6c66e4 Add runtime probe request planning contract` passed with no
  findings
- [x] Local commit creation and Ryan-authorized push for
  `f6c66e4 Add runtime probe request planning contract` completed
- [x] Diagnostic runtime probe-request bridge implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for
  `2e448ea Add diagnostic runtime probe request bridge` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `2e448ea Add diagnostic runtime probe request bridge` completed
- [x] Diagnose/recompile planned runtime probe request consumption
  implementation accepted first-pass in workspace-only state
- [x] Combined release gate for
  `a819cf5 Surface diagnostic runtime probe requests` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `a819cf5 Surface diagnostic runtime probe requests` completed
- [x] Stable planned runtime probe request identity implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for
  `49fa461 Add runtime probe request identities` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `49fa461 Add runtime probe request identities` completed
- [x] Planned runtime probe request ID indexing implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for
  `3df02c6 Index runtime probe requests by ID` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `3df02c6 Index runtime probe requests by ID` completed
- [x] Planned runtime probe request plan implementation accepted first-pass in
  workspace-only state
- [x] Combined release gate for
  `744bf0e Add runtime probe request plans` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `744bf0e Add runtime probe request plans` completed
- [x] Diagnostic runtime probe request plan bridge implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for
  `97dc0f6 Add diagnostic runtime probe request plans` passed with no findings
- [x] Local commit creation and Ryan-authorized push for
  `97dc0f6 Add diagnostic runtime probe request plans` completed
- [x] Semantic diagnostic runtime probe request plan surfacing implementation
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact five-file
  `SemanticDiagnosticResult.planned_runtime_probe_request_plan` tranche
- [x] Local commit creation and Ryan-authorized push for the
  `SemanticDiagnosticResult.planned_runtime_probe_request_plan` tranche
- [x] Post-`7c46f48` North Star planning/control selected planned-side source-site
  indexing for runtime probe request plans
- [x] Planned runtime probe request plan source-site indexing implementation
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file planned runtime probe
  request plan source-site indexing tranche
- [x] Local commit creation and Ryan-authorized push for the planned runtime
  probe request plan source-site indexing tranche
- [x] Ryan authorized bounded internal observation-admission contract scope
- [x] Runtime observation admission read-model implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file internal runtime
  observation admission read-model tranche
- [x] Local commit creation and Ryan-authorized push for the internal runtime
  observation admission read-model tranche
- [x] Post-`b0a5ec5` North Star planning/control selected the diagnostic
  runtime observation admission bridge
- [x] Diagnostic runtime observation admission bridge implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file diagnostic runtime
  observation admission bridge tranche
- [x] Local commit creation and Ryan-authorized push for the diagnostic runtime
  observation admission bridge tranche
- [x] Post-`8706f2e` North Star planning/control selected runtime observation
  admission compatibility validation
- [x] Runtime observation admission compatibility validation implementation
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime observation
  admission compatibility validation tranche
- [x] Local commit creation and Ryan-authorized push for the runtime observation
  admission compatibility validation tranche
- [x] Post-`f5c8df0` North Star planning/control selected the internal
  admitted-runtime-observation provenance attachment bridge
- [x] Admitted runtime observation provenance attachment bridge implementation
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file admitted runtime
  observation provenance bridge tranche
- [x] Local commit creation and Ryan-authorized push for the admitted runtime
  observation provenance bridge tranche
- [x] Post-`35c440d` North Star planning/control selected the diagnostic runtime
  observation application helper
- [x] Diagnostic runtime observation application helper implementation accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file diagnostic runtime
  observation application tranche
- [x] Local commit creation and Ryan-authorized push for the diagnostic runtime
  observation application tranche
- [x] Post-`95f7545` runtime-applied recompile consumption spike accepted
  first-pass
- [x] Diagnostic trace-refresh implementation slice accepted first-pass in
  workspace-only state
- [x] Combined release gate for the exact five-file diagnostic trace-refresh
  release unit
- [x] Local commit creation and Ryan-authorized push for the diagnostic
  trace-refresh release unit
- [x] Post-`74aadd7` North Star planning/control selected the internal runtime
  observation recompile composition helper
- [x] Runtime observation recompile composition helper implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime observation
  recompile composition release unit
- [x] Local commit creation and Ryan-authorized push for the runtime
  observation recompile composition release unit
- [x] Post-`b279b00` North Star planning/control selected a read-only
  exposed-consumption boundary spike
- [x] Exposed-consumption boundary spike accepted first-pass
- [x] Typed facade runtime observation recompile request/response slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file typed facade runtime
  recompile release unit
- [x] Local commit creation and Ryan-authorized push for the typed facade
  runtime recompile release unit
- [x] Post-`8ac3b46` execution-boundary spike accepted first-pass
- [x] Runtime probe execution-result/replay-artifact contract slice accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe result
  contract release unit
- [x] Local commit creation and Ryan-authorized push for the runtime probe
  result contract release unit
- [x] Post-`eb6def0` planning/control selected the internal execution-result
  to typed-observation admission boundary
- [x] Runtime probe result admission bridge implementation slice accepted after
  1 correction in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe result
  admission bridge release unit
- [x] Local commit creation and Ryan-authorized push for the runtime probe
  result admission bridge release unit
- [x] Post-`ccd417a` planning/control selected the internal result-batch to
  runtime recompile bridge
- [x] Runtime probe result-batch recompile bridge implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe result-batch
  recompile bridge release unit
- [x] Local commit creation and Ryan-authorized push for the runtime probe
  result-batch recompile bridge release unit
- [x] Post-`591c09b` planning/control selected the internal non-executing
  runtime probe execution-input materialization boundary
- [x] Runtime probe execution-input materialization implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe
  execution-input materialization release unit
- [x] Local commit creation for the runtime probe execution-input
  materialization release unit
- [x] Ryan-authorized push for the runtime probe
  execution-input materialization release unit
- [x] Post-`cfed3c7` planning/control selected the internal non-executing
  runtime probe execution-attempt to result-batch assembly boundary
- [x] Runtime probe execution-attempt result assembly implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe
  execution-attempt result assembly release unit
- [x] Local commit creation for the runtime probe execution-attempt result
  assembly release unit
- [x] Ryan-authorized push for the runtime probe execution-attempt result
  assembly release unit
- [x] Post-`86be8d7` planning/control selected the internal non-executing
  runtime probe runner-request materialization boundary
- [x] Runtime probe runner-request materialization implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe
  runner-request materialization release unit
- [x] Local commit creation for the runtime probe runner-request
  materialization release unit
- [x] Ryan-authorized push for the runtime probe runner-request
  materialization release unit
- [x] Post-`68a8e73` planning/control selected the internal non-executing
  runner-request attempt/result assembly gate
- [x] Runtime probe runner-request attempt/result assembly implementation
  slice accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe
  runner-request attempt/result assembly release unit
- [x] Local commit creation for the runtime probe runner-request attempt/result
  assembly release unit
- [x] Ryan-authorized push for the runtime probe runner-request attempt/result
  assembly release unit
- [x] Post-`3363929` planning/control selected the internal non-executing
  diagnostic runner-request preparation boundary
- [x] Runtime probe diagnostic runner-request preparation implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe diagnostic
  runner-request preparation release unit
- [x] Local commit creation for the runtime probe diagnostic runner-request
  preparation release unit
- [x] Ryan-authorized push for the runtime probe diagnostic runner-request
  preparation release unit
- [x] Post-`fd0f6d8` planning/control selected the internal runner-callable
  attempt collection boundary
- [x] Runtime probe runner-callable attempt collection implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe
  runner-callable attempt collection release unit
- [x] Local commit creation for the runtime probe runner-callable attempt
  collection release unit
- [x] Ryan-authorized push for the runtime probe runner-callable attempt
  collection release unit
- [x] Post-`32f6220` planning/control selected the internal diagnostic
  runner-callable recompile bridge
- [x] Runtime probe diagnostic runner-callable recompile bridge implementation
  slice accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe diagnostic
  runner-callable recompile bridge release unit
- [x] Local commit creation for the runtime probe diagnostic runner-callable
  recompile bridge release unit
- [x] Ryan-authorized push for the runtime probe diagnostic runner-callable
  recompile bridge release unit
- [x] Post-`74fb275` planning/control selected the internal runtime probe
  runner failure-normalization adapter
- [x] Runtime probe runner failure-normalization adapter implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe runner
  failure-normalization adapter release unit
- [x] Local commit creation for the runtime probe runner failure-normalization
  adapter release unit
- [x] Ryan-authorized push for the runtime probe runner failure-normalization
  adapter release unit
- [x] Post-`93456b6` planning/control selected the internal runtime probe
  runner dispatch table
- [x] Runtime probe runner dispatch table implementation slice accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe runner
  dispatch table release unit
- [x] Local commit creation for the runtime probe runner dispatch table
  release unit
- [x] Ryan-authorized push for the runtime probe runner dispatch table release
  unit
- [x] Post-`3751df1` planning/control selected the internal runtime probe
  runner environment context
- [x] Runtime probe runner environment context implementation slice accepted
  first-pass in workspace-only state
- [x] Combined release gate for the exact four-file runtime probe runner
  environment context release unit
- [x] Local commit creation for the runtime probe runner environment context
  release unit
- [x] Ryan-authorized push for the runtime probe runner environment context
  release unit
- [x] Post-`f75196e` planning/control selected the local Python runner
  execution-boundary spike
- [x] Local Python runner execution-boundary spike accepted first-pass
- [x] Local Python subprocess invocation contract implementation slice accepted
  first-pass in workspace-only state
- [x] Blank invocation revision negative-test correction for the local Python
  subprocess invocation contract
- [x] Combined release gate for the exact four-file local Python subprocess
  invocation contract release unit
- [x] Local commit creation for the local Python subprocess invocation
  contract release unit
- [x] Ryan-authorized push for the local Python subprocess invocation
  contract release unit
- [x] Post-`ea6ff8e` planning/control selected the local Python subprocess
  execution-boundary spike
- [x] Local Python subprocess execution-boundary spike accepted first-pass
- [x] Local Python process completion/result contract implementation slice
  accepted first-pass in workspace-only state
- [x] Combined release gate for the exact four-file local Python process
  completion contract release unit
- [x] Local commit creation for the local Python process completion contract
  release unit
- [x] Ryan-authorized push for the local Python process completion contract
  release unit
- [x] Post-`e9f87fc` planning/control selected the raw local Python subprocess
  execution boundary
- [x] Raw local Python subprocess execution boundary implementation slice
  accepted in workspace after one correction
- [x] Completion revision pre-run validation correction for the raw local
  Python subprocess execution boundary
- [x] Combined release gate for the exact four-file raw local Python
  subprocess execution boundary release unit
- [x] Local commit creation for the raw local Python subprocess execution
  boundary release unit
- [x] Ryan-authorized push for the raw local Python subprocess execution
  boundary release unit
- [x] Post-`d0a009b` planning/control selected the post-subprocess execution
  boundary next-move spike
- [x] Post-subprocess execution boundary next-move spike accepted first-pass
- [x] Local Python subprocess non-proof attempt normalization implementation
  slice accepted in workspace after one correction
- [x] Ryan decision on nonzero completion outcome-parameter test coverage
  finding
- [x] Nonzero completion outcome-parameter test coverage correction
- [x] Ryan decision on the local Python subprocess non-proof attempt
  normalization release-gate identity overclaim finding
- [x] Continuity/spec correction for the local Python subprocess non-proof
  attempt normalization identity claim
- [x] Combined release gate rerun for the exact four-file local Python
  subprocess non-proof attempt normalization release unit
- [x] Local commit creation for the local Python subprocess non-proof attempt
  normalization release unit
- [x] Ryan-authorized push for the local Python subprocess non-proof attempt
  normalization release unit
- [x] Post-`5b10728` planning/control selected a local Python success-boundary
  next-move spike
- [x] Local Python success-boundary next-move spike accepted first-pass
- [x] Local Python stdout/result protocol contract implementation slice accepted
  in workspace after one correction
- [x] Ryan decision on local Python stdout protocol durable-reference contract
  validation finding
- [x] Local Python stdout protocol durable-reference contract correction
- [x] Combined release gate for the exact four-file local Python stdout/result
  protocol contract release unit
- [x] Local commit creation for the local Python stdout/result protocol
  contract release unit
- [x] Ryan-authorized push for the local Python stdout/result protocol
  contract release unit
- [x] Post-`0c4a654` control selected local Python stdout protocol observed
  attempt materialization
- [x] Local Python stdout protocol observed-attempt materialization
  implementation slice
- [x] Combined release gate for the exact four-file local Python stdout
  protocol observed-attempt materialization release unit
- [x] Local commit creation for the local Python stdout protocol
  observed-attempt materialization release unit
- [x] Ryan-authorized push for the local Python stdout protocol
  observed-attempt materialization release unit
- [x] Post-`81a3ce3` control selected local Python stdout protocol failure
  normalization
- [x] Local Python stdout protocol failure-normalization implementation slice
- [x] Combined release gate for the exact four-file local Python stdout
  protocol failure-normalization release unit
- [x] Local commit creation for the local Python stdout protocol
  failure-normalization release unit
- [x] Ryan-authorized push for the local Python stdout protocol
  failure-normalization release unit
- [x] Post-`d8cf97b` control selected local Python executor-to-attempt wrapper
- [x] Local Python executor-to-attempt wrapper implementation slice accepted
  first-pass as workspace-only state
- [x] Combined release gate for the exact four-file local Python
  executor-to-attempt wrapper release unit
- [x] Local commit creation for the local Python executor-to-attempt wrapper
  release unit
- [x] Ryan-authorized push for the local Python executor-to-attempt wrapper
  release unit
- [x] Post-`8625186` control selected local Python runner handler adapter
- [x] Local Python runner handler adapter implementation slice accepted
  first-pass as workspace-only state
- [x] Combined release gate for the exact four-file local Python runner handler
  adapter release unit
- [x] Local commit creation for the local Python runner handler adapter release
  unit
- [x] Ryan-authorized push for the local Python runner handler adapter release
  unit
- [x] Post-`9b9b5cd` control selected local Python worker request payload
  contract
- [x] First local Python worker request payload implementation lane returned
  `NEEDS-CONTROL` on prompt wording
- [x] Clarified local Python worker request payload contract implementation
  slice accepted after two corrections as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  worker request payload contract release unit
- [x] Local commit creation for the local Python worker request payload
  contract release unit
- [x] Ryan-authorized push for the local Python worker request payload contract
  release unit
- [x] Post-`4d155ec` control selected local Python worker request stdin
  transport contract
- [x] Local Python worker request stdin transport contract implementation slice
  accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  worker request stdin transport contract release unit
- [x] Local commit creation for the local Python worker request stdin transport
  contract release unit
- [x] Ryan-authorized push for the local Python worker request stdin transport
  contract release unit
- [x] Post-`0a3c4c6` control selected local Python subprocess stdin execution
  wiring
- [x] Local Python subprocess stdin execution wiring implementation slice
  accepted first-pass as workspace-only state
- [x] Combined read-only release gate for the exact four-file local Python
  subprocess stdin execution wiring release unit
- [ ] Local commit creation for the local Python subprocess stdin execution
  wiring release unit

## What Is In Progress

- Runtime probe execution-attempt result assembly is completed and pushed at
  `86be8d7 Assemble runtime probe execution attempts`.
- The released unit is exactly
  `src/context_ir/runtime_probe_execution.py`,
  `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`.
- Release-gate status is no-active-gate for `86be8d7`.
- Runtime probe execution-input materialization is completed and pushed at
  `cfed3c7 Add runtime probe execution input materialization`.
- Released unit:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `cfed3c7`.
- No release gate, staging, local commit, or push is active for `86be8d7`.
- Runtime probe runner-request materialization is accepted first-pass in
  workspace-only state, release-gate-cleared, locally committed, and pushed:
  - release unit is exactly `src/context_ir/runtime_probe_execution.py`,
    `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
  - release-unit audit passed with no findings
  - full regression passed with `876 passed`
  - commit-gating passed with the exact four-file unit
  - local commit is `68a8e73 Materialize runtime probe runner requests`
  - Ryan-authorized push completed with `origin/main` advanced through
    `7eb5304 Sync runtime probe runner request release routing`
  - release-gate status is no-active-gate for `68a8e73`
- The active next action may choose the next bounded runtime-probe
  execution-loop planning or implementation lane. Do not reopen `68a8e73`
  release gates absent new findings.
- Runtime probe runner-request attempt/result assembly is accepted first-pass
  in workspace-only state, release-gate-cleared, locally committed, and pushed:
  - release unit is exactly `src/context_ir/runtime_probe_execution.py`,
    `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
  - release-unit audit passed with no findings
  - full regression passed with `882 passed`
  - commit-gating passed with the exact four-file unit
  - local commit is
    `3363929 Assemble runtime probe runner request attempts`
  - Ryan-authorized push completed with `origin/main` advanced through
    `0d37074 Sync runtime probe runner attempt release routing`
  - release-gate status is no-active-gate for `3363929`
- The active next action may choose the next bounded runtime-probe
  execution-loop planning or implementation lane. Do not reopen `3363929`
  release gates absent new findings.
- Runtime probe diagnostic runner-request preparation is accepted first-pass,
  release-gate-cleared, locally committed, and pushed:
  - release unit is exactly `src/context_ir/runtime_probe_execution.py`,
    `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
  - release-unit audit passed with no findings
  - focused validation passed with `205 passed`
  - full regression passed with `885 passed`
  - commit-gating passed with the exact four-file unit
  - local commit is `fd0f6d8 Prepare runtime probe diagnostic runner requests`
  - Ryan-authorized push completed with `origin/main` advanced through
    `74d84fb Sync runtime probe diagnostic runner request release routing`
  - release-gate status is no-active-gate for `fd0f6d8`
- Runtime probe runner-callable attempt collection is accepted first-pass,
  release-gate-cleared, locally committed, and pushed:
  - release unit is exactly `src/context_ir/runtime_probe_execution.py`,
    `tests/test_runtime_probe_execution.py`, `PLAN.md`, and `BUILDLOG.md`
  - release-unit audit passed with no findings
  - focused validation passed with `211 passed`
  - full regression passed with `891 passed`
  - commit-gating passed with the exact four-file unit
  - local commit is `32f6220 Collect runtime probe runner attempts`
  - Ryan-authorized push completed with `origin/main` advanced through
    `e9b5b5a Sync runtime probe runner attempt collection release routing`
  - release-gate status is no-active-gate for `32f6220`
- The next implementation slice is an internal diagnostic runner-callable
  recompile bridge in `src/context_ir/runtime_observation_recompile.py` and
  `tests/test_runtime_observation_recompile.py`.
- `PLAN.md` and `BUILDLOG.md` are dirty control-lane continuity state for this
  route. They should not be edited by the implementation lane.
- Runtime probe result-batch recompile bridge is completed and pushed at
  `591c09b Compose runtime probe result batch recompile`.
- Release-gate status is no-active-gate for `591c09b`.
- Runtime probe execution-result/replay-artifact contract is completed and
  pushed at `eb6def0`.
- Runtime probe result admission bridge is completed and pushed at `ccd417a`.
- Typed facade runtime observation recompile is completed and pushed at
  `8ac3b46`:
  - `src/context_ir/tool_facade.py`
  - `tests/test_tool_facade.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `8ac3b46`.
- No release gate is active for the pushed runtime observation recompile
  composition tranche.
- The runtime observation recompile composition tranche is completed and
  pushed at `b279b00`:
  - `src/context_ir/runtime_observation_recompile.py`
  - `tests/test_runtime_observation_recompile.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `b279b00`.
- No release gate is active for the pushed diagnostic trace-refresh tranche.
- The diagnostic trace-refresh tranche is completed and pushed at `74aadd7`:
  - `src/context_ir/semantic_diagnostics.py`
  - `src/context_ir/semantic_optimizer.py`
  - `tests/test_semantic_diagnostics.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `74aadd7`.
- No release gate is active for the pushed diagnostic runtime observation
  application tranche.
- The diagnostic runtime observation application tranche is completed and
  pushed at `95f7545`:
  - `src/context_ir/runtime_observation_admission.py`
  - `tests/test_runtime_observation_admission.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `95f7545`.
- No release gate is active for the pushed admitted runtime observation
  provenance bridge tranche.
- The admitted runtime observation provenance bridge tranche is completed and
  pushed at `35c440d`:
  - `src/context_ir/runtime_observation_admission.py`
  - `tests/test_runtime_observation_admission.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `35c440d`.
- No release gate is active for the pushed runtime observation admission
  read-model tranche.
- No release gate is active for the pushed diagnostic runtime observation
  admission bridge tranche.
- No release gate is active for the pushed runtime observation admission
  compatibility validation tranche.
- The runtime observation admission compatibility validation tranche is
  completed and pushed at `f5c8df0`:
  - `src/context_ir/runtime_observation_admission.py`
  - `tests/test_runtime_observation_admission.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `f5c8df0`.
- The diagnostic runtime observation admission bridge tranche is completed and
  pushed at `8706f2e`:
  - `src/context_ir/runtime_observation_admission.py`
  - `tests/test_runtime_observation_admission.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `8706f2e`.
- Active next route is bounded post-`95f7545` North Star planning/control to
  choose the next smallest meaningful capability slice.
- The pushed admitted-runtime-observation bridge only attaches already-admitted
  observations through existing additive provenance helpers. It still does not
  authorize probe execution, execution-result contracts, runtime observation
  collection, analyzer or tool-facade behavior, package-root API, MCP, eval,
  schema, scoring, optimizer, compiler, winner-selection, product, public
  benchmark, or public-claim changes.
- The internal runtime observation admission read-model tranche is completed
  and pushed at `b0a5ec5`:
  - `src/context_ir/runtime_observation_admission.py`
  - `tests/test_runtime_observation_admission.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `b0a5ec5`.
- Push remains Ryan-gated for any future release.
- The planned runtime probe request plan source-site indexing tranche is
  completed and pushed at `6d5fc47`:
  - `src/context_ir/runtime_probe_requests.py`
  - `tests/test_runtime_probe_requests.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `6d5fc47`.
- The `SemanticDiagnosticResult.planned_runtime_probe_request_plan` tranche is
  completed and pushed at `7c46f48`:
  - `src/context_ir/semantic_types.py`
  - `src/context_ir/semantic_diagnostics.py`
  - `tests/test_semantic_diagnostics.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `7c46f48`.
- The diagnostic runtime probe request plan bridge tranche is completed and
  pushed at `97dc0f6` with release-gate status no-active-gate.
- The planned runtime probe request plan tranche is completed and pushed at
  `744bf0e` with release-gate status no-active-gate.
- The planned runtime probe request ID indexing tranche is completed and
  pushed at `3df02c6` with release-gate status no-active-gate.
- The stable planned runtime probe request identity tranche is completed and
  pushed at `49fa461` with release-gate status no-active-gate.
- The diagnose/recompile planned runtime probe request consumption tranche is
  completed and pushed at `a819cf5`:
  - `src/context_ir/semantic_diagnostics.py`
  - `src/context_ir/semantic_types.py`
  - `tests/test_semantic_diagnostics.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `a819cf5`.
- The internal diagnostic runtime probe-request bridge tranche is completed and
  pushed at `2e448ea`:
  - `src/context_ir/runtime_probe_requests.py`
  - `tests/test_runtime_probe_requests.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `2e448ea`.
- No implementation slice, staging, local commit creation, or push is currently
  in progress.
- The internal runtime probe-request planning tranche is completed and pushed
  at `f6c66e4`:
  - `src/context_ir/runtime_probe_requests.py`
  - `tests/test_runtime_probe_requests.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- Release-gate status is no-active-gate for `f6c66e4`.
- No implementation slice, staging, local commit creation, or push is currently
  in progress.
- The 16-file internal eval-only `REFLECTIVE_BUILTIN` tranche is completed and
  pushed at `546a4da`; release-gate status is no-active-gate.
- The current nine-file `DYNAMIC_IMPORT` original budget-pressure tranche is
  completed and pushed at `d73cde4`; release-gate status is no-active-gate.
- The zero-argument `dir()` plus `METACLASS_BEHAVIOR` budget-pressure release
  is pushed at `e2f3dcf` and has release-gate status no-active-gate. It is
  historical pushed authority, not the active route. Do not route `e2f3dcf`
  back to docs review, release-unit audit, full regression, commit-gating,
  staging, local commit creation, or push absent new findings.
- Fresh control lanes should use the canonical active release-state block above
  for current routing, and should treat older conflicting routing notes as
  historical when superseded by that block or by newer BUILDLOG entries.

## Historical Superseded Routing Notes

The following older routing notes remain as historical context only. They do not
override the canonical active release-state block above or newer BUILDLOG
supersession entries.

- Prior code/eval release state is complete and pushed for the internal
  eval-only
  `REFLECTIVE_BUILTIN` / `dir(obj)` budget-pressure expansion at
  `ad9db8d Expand dir eval budget coverage`.
- Release-gate status is no-active-gate for `ad9db8d`. Do not route
  `ad9db8d` back to docs review, release-unit audit, full regression,
  commit-gating, staging, local commit creation, or push absent new findings.
- No active route remains to commit-gating, staging, local commit creation, or
  push for `ad9db8d` absent new findings.
- The bounded post-43d0439 North Star planning/control decision is complete
  and released. It selected a budget-pressure expansion of
  `oracle_signal_dir_probe_matrix` to `[220, 100]`: 1 task x 2 budgets x 3
  providers, preserving providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`.
- Fixture, task, query, and runtime payload remain unchanged; runtime payload
  remains `listing_entry_count=74`.
- Selector and selected-unit truth remain `unsupported/opaque`; runtime
  provenance remains additive only; baseline providers remain empty at both
  budgets.
- No source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is authorized.
- Docs/evidence/continuity reconciliation for this expansion was accepted
  first-pass.
- Release-unit audit for this expansion cleared first-pass.
- Full regression for this expansion cleared first-pass with `709 passed`.
- Commit-gating, local commit creation, and Ryan-authorized push for this
  expansion are complete at `ad9db8d`.
- Completed getattr AttributeError release state:
  - implementation accepted first-pass
  - docs/evidence/continuity reconciliation accepted after 2 corrections
  - release-unit audit cleared first-pass
  - full regression cleared first-pass with `709 passed`
  - first commit-gating review rejected with P1 stale-routing findings
  - routing correction accepted first-pass
  - corrected commit-gating cleared first-pass
  - local commit creation and Ryan-authorized push completed at `5bd0616`
- Prior completed builtins-alias release state:
  - source/contract prerequisite and eval-only sibling accepted first-pass
  - docs/evidence/continuity reconciliation accepted after one correction
  - release-unit audit cleared first-pass
  - full regression cleared first-pass with `702 passed`
  - first commit-gating review rejected with P1 stale-routing findings
  - first continuity routing correction accepted first-pass
  - corrected commit-gating review rejected with one P1 stale-route finding
  - PLAN-only stale-route correction accepted first-pass
  - corrected commit-gating review cleared first-pass
  - local commit creation and Ryan-authorized push completed at `6ac1e28`
- Prior completed builtins-attribute release state:
  - implementation/assets were accepted workspace-only before release
  - docs/evidence/continuity reconciliation was accepted first-pass
  - release-unit audit cleared first-pass
  - full regression cleared first-pass
  - commit-gating cleared first-pass
  - local commit creation and Ryan-authorized push completed at `3dfc355`
  - no docs-only post-push sync is required merely to record that live git refs
    already show the pushed release commit
- Prior completed root-module alias release state:
  - implementation/assets were accepted workspace-only before release
  - corrected docs/evidence/continuity reconciliation was accepted after one
    P1 state-neutrality correction
  - release-unit audit cleared first-pass
  - full regression cleared first-pass
  - commit-gating cleared first-pass
  - local commit creation completed at `b85f038`
  - Ryan-authorized push completed at `b85f038`
- Full regression evidence:
  - `ruff check` passed
  - `ruff format --check` passed
  - `mypy --strict src/` passed
  - `pytest tests/ -v` passed with `688 passed`
- The released root-module alias implementation/assets are:
  - `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/main.py`
  - `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/plugins/__init__.py`
  - `evals/fixtures/oracle_signal_dynamic_import_root_alias_probe/plugins/weather.py`
  - `evals/run_specs/oracle_signal_dynamic_import_root_alias_probe_matrix.json`
  - `evals/tasks/oracle_signal_dynamic_import_root_alias_probe.json`
  - `tests/test_eval_signal_dynamic_import_root_alias_probe.py`
- The released matrix is
  `oracle_signal_dynamic_import_root_alias_probe_matrix`: 1 task x 1 budget x
  3 providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`
- The fixture boundary is `import importlib as loader`,
  `name = "plugins.weather"`, and exactly `loader.import_module(name)`
- Runtime payload is `imported_module=plugins.weather`; primary selector and
  selected-unit truth remain `unsupported/opaque`; runtime provenance remains
  additive only; no dependency edge or selected symbol is created from
  `plugins.weather`
- Non-goals remain no root-module `importlib.import_module(name)` expansion,
  no imported-name `import_module(name)` expansion, no imported-alias
  `load_module(name)` expansion, no literal dynamic import expansion, no
  `__import__(name)`, no `builtins.__import__`, no globals/locals/fromlist
  forms, no namespace mutation, no generated-code dependency modeling, no
  generalized dynamic import support, and no
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening
- No active release gate remains for `b85f038 Add root-alias dynamic import
  eval probe` absent new findings.
- Do not reopen `b85f038`, `4030845`, `ee71a82`, `397c7dd`, `14b362e`,
  `bcd6d68`, or `96fc03a` absent new findings
- `5d2d7e4 Sync imported-name dynamic import release routing` remains the prior
  pushed continuity authority
- `ca191c8 Sync builtin dynamic import release routing` remains the prior
  builtin dynamic-import continuity authority
- `397c7dd Add builtin dynamic import eval probe` is the prior builtin
  dynamic-import eval/test/docs release authority and must not be reopened
  absent new findings
- `14b362e Add dynamic import root runtime eval pilot` is the prior root-module
  dynamic-import eval/test/docs release authority and must not be reopened
  absent new findings
- `bcd6d68 Add exec source runtime eval pilot` is the prior exec(source) release
  and must not be reopened absent new findings
- `96fc03a Add eval runtime eval pilot` remains the prior eval(source)
  release authority and must not be reopened absent new findings
- The internal eval-only `EXEC_OR_EVAL` / `exec(source)` release unit is
  completed and pushed at `bcd6d68`
- The exec matrix is `oracle_signal_exec_probe_matrix`, 1 task x 1 budget x 3
  providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`
- The fixture/call boundary is `source = "pass"` and exactly `exec(source)`;
  executed source parses as exactly one `ast.Pass`; no `exec("pass")`,
  `exec(source + suffix)`, `exec(source=source)`, `exec(source, globals)`,
  `exec(source, globals, locals)`, `builtins.exec`, or `eval` is included
- Runtime proof is `execution_outcome=completed`,
  `source_shape=literal_statement`, `source_sha256 == sha256(b"pass")`, and
  non-empty `durable_payload_reference`; optional `statement_kind=pass` is
  additive summary only
- Provenance attaches only to the preserved `EXEC_OR_EVAL` unsupported finding
  for `exec(source)`
- Primary selector and selected-unit truth remain `unsupported/opaque`;
  additive runtime provenance remains separate from primary truth
- No dependency edge or symbol is created from executed source, no namespace
  mutation modeling is added, and no generated-code dependency modeling is
  added
- Scope remains exactly simple-name builtin `exec(source)` with one positional
  argument; no broader `exec` forms are included, no generalized exec support
  is included, and public comparative claims remain bounded to the existing
  quad matrix
- No
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is authorized
- Release-unit audit initially found one P1 digest-boundary issue; the
  correction pinned `source_sha256` to `sha256(b"pass")`; audit rerun cleared;
  full regression passed; commit-gating cleared; local commit creation
  completed; Ryan-authorized push completed
- The prior post-imported-alias next-move route is superseded by the completed
  root-module alias release at `b85f038` and the post-root-alias
  planning/control route above
- The runtime-outcome methodology/reporting hardening release unit is pushed to `origin/main` at `d8ebdc3`
- Live git refs and worktree state are intentionally verified from git rather than kept as mutable committed continuity fields
- The `getattr` family matrix expansion release unit is pushed at `1b555ef`
- The same-tranche docs/evidence reconciliation released in `1b555ef` includes:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The `getattr` family matrix expansion released in `1b555ef` includes:
  - `evals/run_specs/oracle_signal_getattr_probe_matrix.json`
  - `evals/run_specs/oracle_signal_getattr_default_probe_matrix.json`
  - `evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json`
  - `tests/test_eval_signal_getattr_probe.py`
  - `tests/test_eval_signal_getattr_default_probe.py`
  - `tests/test_eval_signal_getattr_default_value_probe.py`
  - `tests/test_eval_runs.py`
  - `tests/test_eval_report.py`
- The release-unit audit over the accumulated `getattr` family matrix expansion tranche is accepted first-pass
- The accepted `getattr` family matrix expansion:
  - add budget `100` to `evals/run_specs/oracle_signal_getattr_probe_matrix.json`
  - add budget `100` to `evals/run_specs/oracle_signal_getattr_default_probe_matrix.json`
  - add budget `100` to `evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json`
  - update focused tests only as needed
- The full regression gate over the accumulated `getattr` family matrix expansion tranche is accepted first-pass
- Commit-gating over the exact intended release file set is accepted first-pass
- Local commit creation over the exact intended release file set is accepted first-pass at `1b555ef`
- Remote push of `1b555ef` is accepted first-pass after explicit Ryan authorization
- The post-push continuity anchor for the `1b555ef` release state is `159e363`
- The post-`1b555ef` / `d9be4d5` bounded planning boundary is complete
- The post-`d9be4d5` `vars(obj)` planning decision is accepted first-pass
- The accepted `vars(obj)` eval pilot includes:
  - `src/context_ir/eval_oracles.py`
  - `src/context_ir/eval_providers.py`
  - `evals/fixtures/oracle_signal_vars_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_vars_probe/main.py`
  - `evals/tasks/oracle_signal_vars_probe.json`
  - `evals/run_specs/oracle_signal_vars_probe_matrix.json`
  - `tests/test_eval_signal_vars_probe.py`
- The accepted same-tranche docs/evidence reconciliation for the `vars(obj)` pilot includes:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The accepted `vars(obj)` pilot is one internal eval-only task at budget `220` across `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- The accepted `vars(obj)` pilot keeps selector and selected-unit primary truth `unsupported/opaque` with additive runtime-backed provenance only
- The accepted `vars(obj)` tranche does not widen package-root APIs, MCP behavior, analyzer/runtime-acquisition/tool-facade behavior, schema, scoring, winner selection, public claims, public comparison boundaries, or zero-argument `vars()` / sibling reflective families
- The release-unit audit over the accumulated `vars(obj)` tranche is accepted first-pass
- The full regression gate over the accumulated `vars(obj)` tranche is accepted first-pass
- Commit-gating over the exact intended `vars(obj)` release file set is accepted first-pass
- The accumulated `vars(obj)` tranche has passed planning, implementation review, docs reconciliation, release-unit audit, full regression, and commit-gating
- Local commit and remote push state for the tranche are verified from git, not maintained as mutable continuity prose
- If git shows the release commit is local-only, push remains explicitly Ryan-gated
- If git shows the release commit is already pushed, route to the next bounded planning/evidence move
- Do not create a docs-only post-push commit merely to record the push
- The post-`ead239d` `vars(obj)` budget-expansion planning decision is accepted first-pass
- The accepted workspace-only `vars(obj)` budget expansion currently includes:
  - `evals/run_specs/oracle_signal_vars_probe_matrix.json`
  - `tests/test_eval_signal_vars_probe.py`
- The accepted workspace-only budget expansion changes only the existing `oracle_signal_vars_probe_matrix` from budget `[220]` to `[220, 100]`
- The budget `100` row preserves the expected `unsupported/opaque` selected unit with additive runtime provenance
- The accepted same-tranche docs/evidence reconciliation for the `vars(obj)` budget expansion currently includes:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The accepted docs/evidence reconciliation describes the `vars(obj)` pilot as 1 task x 2 budgets x 3 providers at budgets `100` and `220`
- The accepted budget expansion does not widen fixtures, tasks, providers, source, package-root APIs, MCP behavior, runtime-acquisition/analyzer/tool-facade behavior, schema, scoring, winner selection, public claims, zero-argument `vars()`, or sibling runtime families
- The corrected release-unit audit over this budget expansion tranche is accepted after 1 correction
- The full regression gate over this budget expansion tranche is accepted first-pass
- Commit-gating over the exact 8-file release-unit candidate is accepted first-pass
- Local commit creation and remote push for that budget-expansion tranche completed at `2c6b54a`
- The accepted zero-argument `vars()` eval pilot implementation includes:
  - `src/context_ir/eval_oracles.py`
  - `evals/fixtures/oracle_signal_vars_zero_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_vars_zero_probe/main.py`
  - `evals/tasks/oracle_signal_vars_zero_probe.json`
  - `evals/run_specs/oracle_signal_vars_zero_probe_matrix.json`
  - `tests/test_eval_signal_vars_zero_probe.py`
- The accepted zero-argument `vars()` pilot is one internal eval-only task at budget `220` across `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- The accepted zero-argument `vars()` pilot keeps selector and selected-unit primary truth `unsupported/opaque` with additive runtime-backed provenance only
- The accepted zero-argument `vars()` pilot does not widen runtime acquisition, analyzer, tool facade behavior, MCP, package-root APIs, schema, scoring, winner selection, public claims, or sibling runtime families
- The accepted same-tranche docs/evidence reconciliation for the zero-argument `vars()` pilot includes:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The accepted docs/evidence reconciliation describes the zero-argument `vars()` pilot as `oracle_signal_vars_zero_probe_matrix`: 1 task x 1 budget x 3 providers at budget `220`
- The accepted docs/evidence reconciliation keeps release-facing wording neutral: no live workspace, local commit, or push-state claim belongs in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, or `ARCHITECTURE.md`
- The release-unit audit over the accumulated zero-argument `vars()` release candidate is accepted first-pass
- The full regression gate over the accumulated zero-argument `vars()` release candidate is accepted first-pass with `590 passed`
- Commit-gating over the exact accumulated zero-argument `vars()` release-candidate file set is accepted first-pass
- The accepted staging set is:
  - `src/context_ir/eval_oracles.py`
  - `evals/fixtures/oracle_signal_vars_zero_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_vars_zero_probe/main.py`
  - `evals/tasks/oracle_signal_vars_zero_probe.json`
  - `evals/run_specs/oracle_signal_vars_zero_probe_matrix.json`
  - `tests/test_eval_signal_vars_zero_probe.py`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- The accepted commit message is `Add zero-argument vars eval pilot`
- The accumulated zero-argument `vars()` release candidate has implementation, docs/evidence, release-unit audit, full-regression, and commit-gating acceptance, but local commit and remote push state must be verified from git rather than inferred from continuity prose
- Local commit and remote push state for this tranche must be verified from git; do not create a docs-only post-push continuity commit merely to record the push
- Local commit creation and remote push for the initial zero-argument `vars()` pilot completed at `71db72e`
- The accepted workspace-only zero-argument `vars()` budget expansion currently includes:
  - `evals/run_specs/oracle_signal_vars_zero_probe_matrix.json`
  - `tests/test_eval_signal_vars_zero_probe.py`
- The accepted workspace-only budget expansion changes only the existing `oracle_signal_vars_zero_probe_matrix` from budget `[220]` to budgets `[220, 100]`
- The budget `100` row preserves the expected `unsupported/opaque` selected unit with additive `lookup_outcome=returned_namespace` runtime provenance
- Baseline providers remain empty at both budgets
- The accepted budget expansion does not widen fixtures, tasks, providers, source, package-root APIs, MCP behavior, runtime-acquisition/analyzer/tool-facade behavior, schema, scoring, winner selection, public claims, or sibling runtime families
- The accepted same-tranche docs/evidence reconciliation for the zero-argument `vars()` budget expansion includes:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The accepted docs/evidence reconciliation describes the zero-argument `vars()` pilot as 1 task x 2 budgets x 3 providers at budgets `100` and `220`
- The accepted docs/evidence reconciliation keeps release-facing wording neutral: no live workspace, local commit, or push-state claim belongs in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, or `ARCHITECTURE.md`
- The release-unit audit over the accumulated zero-argument `vars()` budget-expansion release candidate is accepted first-pass
- The full regression gate over the accumulated zero-argument `vars()` budget-expansion release candidate is accepted first-pass with `590 passed`
- Commit-gating over the exact accumulated zero-argument `vars()` budget-expansion release-candidate file set is accepted first-pass
- The accepted staging set is:
  - `evals/run_specs/oracle_signal_vars_zero_probe_matrix.json`
  - `tests/test_eval_signal_vars_zero_probe.py`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- The accepted commit message is `Expand zero-argument vars budget matrix`
- The accumulated zero-argument `vars()` budget-expansion release candidate has implementation, docs/evidence, release-unit audit, full-regression, and commit-gating acceptance, but local commit and remote push state must be verified from git rather than inferred from continuity prose
- Local commit creation and remote push for the zero-argument `vars()` budget expansion completed at `9eec985`
- The accepted `globals()` eval pilot includes:
  - `src/context_ir/eval_oracles.py`
  - `src/context_ir/eval_providers.py`
  - `evals/fixtures/oracle_signal_globals_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_globals_probe/main.py`
  - `evals/tasks/oracle_signal_globals_probe.json`
  - `evals/run_specs/oracle_signal_globals_probe_matrix.json`
  - `tests/test_eval_signal_globals_probe.py`
- The accepted `globals()` pilot is one internal eval-only task at budget `220` across `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- The accepted `globals()` pilot keeps selector and selected-unit primary truth `unsupported/opaque` with additive `lookup_outcome=returned_namespace` runtime provenance only
- The accepted `globals()` pilot does not widen runtime acquisition, analyzer, tool facade implementation, MCP, package-root APIs, schema, scoring, winner selection, public claims, or sibling runtime families
- Same-tranche docs/evidence reconciliation for the accepted `globals()` pilot is complete in:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The release-unit audit over the accumulated `globals()` release candidate is accepted first-pass
- The full regression gate over the accumulated `globals()` release candidate is accepted first-pass with `595 passed`
- The commit-gating review over the accumulated `globals()` release candidate is accepted first-pass
- The accepted commit message is `Add globals runtime eval pilot`
- Local commit creation and remote push for the initial `globals()` pilot completed at `631a303`
- The pushed `globals()` budget expansion at `5f74ede` includes:
  - `evals/run_specs/oracle_signal_globals_probe_matrix.json`
  - `tests/test_eval_signal_globals_probe.py`
- The pushed `globals()` budget expansion changes only the existing `oracle_signal_globals_probe_matrix` from budget `[220]` to budgets `[220, 100]`
- The pushed `globals()` budget expansion keeps the existing task, fixture, query, provider set, selector, and runtime provenance shape unchanged
- The pushed `globals()` budget expansion preserves `unsupported/opaque` selected-unit primary truth, additive `lookup_outcome=returned_namespace` runtime provenance, empty baseline selected units, and summary/report accounting over the expanded two-budget matrix
- The pushed `globals()` budget expansion does not widen runtime acquisition, analyzer, tool facade implementation, MCP, package-root APIs, schema, scoring, winner selection, public claims, or sibling runtime families
- Same-tranche docs/evidence reconciliation for the accepted `globals()` budget expansion is complete in:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
- The release-unit audit over the accepted `globals()` budget expansion is accepted first-pass
- The full regression gate over the accepted `globals()` budget expansion is accepted first-pass with `596 passed`
- The commit-gating review over the accepted `globals()` budget expansion is accepted first-pass
- The accepted commit message is `Expand globals eval budget matrix`
- Local commit creation and remote push for the `globals()` budget expansion completed at `5f74ede`
- The latest pushed `locals()` eval/test/docs release authority is `2dd8404
  Expand locals eval budget matrix`; `38e9d5f` remains the initial one-budget
  `locals()` pilot anchor
- The pushed `2dd8404` `locals()` budget expansion includes:
  - `evals/run_specs/oracle_signal_locals_probe_matrix.json`
  - `tests/test_eval_signal_locals_probe.py`
- The pushed budget expansion changes only the existing
  `oracle_signal_locals_probe_matrix` from budget `[220]` to budgets
  `[220, 100]`
- The pushed budget expansion describes `oracle_signal_locals_probe_matrix` as
  1 task x 2 budgets x 3 providers at budgets `100` and `220`
- The budget `100` row preserves the expected `unsupported/opaque` selected
  unit with additive `lookup_outcome=returned_namespace` runtime provenance;
  baseline providers remain empty at the selected-unit layer
- The pushed budget expansion does not widen fixtures, tasks, providers,
  source, runtime acquisition, analyzer, tool facade implementation, MCP,
  package-root APIs, schema, scoring, winner selection, public claims,
  generalized locals() support, or sibling runtime families
- Same-tranche docs/evidence reconciliation for the pushed `locals()` budget
  expansion is complete in:
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `ARCHITECTURE.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- The pushed docs/evidence reconciliation keeps selector, runtime-mutation
  surface, and selected-unit primary truth `unsupported/opaque`; keeps
  runtime-backed provenance additive only; preserves
  `lookup_outcome=returned_namespace`; and leaves the public-safe quad-matrix
  comparative boundary unchanged
- The `2dd8404` locals budget-expansion release passed implementation review,
  same-tranche docs reconciliation, release-unit audit, full regression,
  corrected commit-gating, local commit creation, and Ryan-authorized push
- Do not route future control work to release gates for `2dd8404` unless a
  later findings-based review identifies a concrete defect
- Pushed implementation release `d8ebdc3` contains the runtime-outcome methodology/reporting hardening implementation release unit:
  - `src/context_ir/eval_results.py`
  - `src/context_ir/eval_summary.py`
  - `tests/test_eval_report.py`
  - `tests/test_eval_results.py`
  - `tests/test_eval_runs.py`
  - `tests/test_eval_signal_getattr_default_probe.py`
  - `tests/test_eval_signal_getattr_default_value_probe.py`
  - `tests/test_eval_summary.py`
- Pushed implementation release `b014595` contains the accepted value-return branch tranche after pushed `7d43302`:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `evals/fixtures/oracle_signal_getattr_default_value_probe/`
  - `evals/tasks/oracle_signal_getattr_default_value_probe.json`
  - `evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json`
  - `tests/test_eval_providers.py`
  - `tests/test_eval_runs.py`
  - `tests/test_eval_signal_getattr_default_value_probe.py`
  - the accepted post-`7d43302` planning decision was implemented as one bounded internal eval-only sibling pilot for the value-return branch of `getattr(obj, name, default)`
  - add a new sibling `oracle_signal_getattr_default_value_probe` fixture/task/run-spec/test set
  - keep the existing `oracle_signal_getattr_default_probe` default-return fixture unchanged
  - keep the pilot at `1 task x 1 budget x 3 providers` with budget `220`
  - keep providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
  - assert selector and selected-unit primary truth remains `unsupported/opaque`
  - keep runtime-backed provenance additive only
  - do not widen package-root APIs, MCP exposure, analyzer/tool-facade behavior, runtime acquisition, schema, scoring, winner selection, public benchmark claims, or public product boundaries
  - the value-return pilot covers `lookup_outcome=returned_value`
  - selector and selected-unit primary truth remains `unsupported/opaque`
  - runtime-backed provenance remains additive only
  - no package-root API, MCP, analyzer/tool-facade behavior, runtime-acquisition, schema, scoring, winner-selection, public benchmark claim, or public product-boundary surface changed
  - execution-lane validation passed:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_signal_getattr_default_value_probe.py -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v`
    - pytest result: `575 passed`
  - control-lane validation passed:
    - `git diff --check`
    - JSON validation for the new runtime observation, task, and run-spec files
    - forbidden-surface diff check over source, public docs, package-root, MCP, runtime-acquisition, analyzer/tool-facade, schema, scoring, and winner-selection surfaces
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_signal_getattr_default_value_probe.py -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_runs.py tests/test_eval_providers.py -k getattr_default_value_probe -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_providers.py -k "defaulted_getattr_value_probe or getattr_value_probe" -q`
  - the accepted value-return implementation slice is audit-cleared, full-regression-cleared, commit-gating-cleared, committed locally, and pushed
  - same-tranche docs/evidence reconciliation is included:
  - after post-push release-doc correction, names `b014595` as pushed code/test evidence authority and keeps `7d43302` as the prior default-return branch anchor
  - adds release-neutral wording for the narrow internal eval-only `getattr(obj, name, default)` value-return branch pilot beside the default-return branch
  - keeps public-safe quad-matrix comparative boundaries unchanged
  - keeps selector and selected-unit primary truth `unsupported/opaque`
  - keeps runtime-backed provenance additive only
  - does not widen public claims, public APIs, MCP behavior, runtime acquisition, analyzer/tool-facade behavior, schema, scoring, winner selection, or product positioning
  - docs/evidence validation passed:
    - `git diff --check -- EVAL.md PUBLIC_CLAIMS.md README.md ARCHITECTURE.md`
    - no `workspace-only`, `workspace tranche`, or `accepted workspace` wording remains in release docs
    - targeted boundary grep checks confirmed default-return, value-return, `unsupported/opaque`, additive provenance, public-safe quad-matrix, public API, MCP, and winner-selection boundary wording
  - release-unit audit passed with no findings
  - full regression passed:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v`
    - pytest result: `575 passed`
  - commit-gating passed with no findings
  - exact release-unit files approved for staging:
    - `ARCHITECTURE.md`
    - `EVAL.md`
    - `PUBLIC_CLAIMS.md`
    - `README.md`
    - `tests/test_eval_providers.py`
    - `tests/test_eval_runs.py`
    - `tests/test_eval_signal_getattr_default_value_probe.py`
    - `evals/fixtures/oracle_signal_getattr_default_value_probe/eval_runtime_observations.json`
    - `evals/fixtures/oracle_signal_getattr_default_value_probe/main.py`
    - `evals/tasks/oracle_signal_getattr_default_value_probe.json`
    - `evals/run_specs/oracle_signal_getattr_default_value_probe_matrix.json`
  - continuity files `PLAN.md` and `BUILDLOG.md` are excluded from the release-unit commit candidate
  - local commit creation passed at `b014595`
  - remote push completed at `b014595`
  - the accumulated accepted tranche is audit-cleared, full-regression-cleared, commit-gating-cleared, committed locally, and pushed
- Pushed implementation release `7d43302` contains the accepted defaulted `getattr(obj, name, default)` tranche after pushed `c592dca`:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `src/context_ir/eval_oracles.py`
  - `evals/fixtures/oracle_signal_getattr_default_probe/`
  - `evals/tasks/oracle_signal_getattr_default_probe.json`
  - `evals/run_specs/oracle_signal_getattr_default_probe_matrix.json`
  - `tests/test_eval_oracles.py`
  - `tests/test_eval_providers.py`
  - `tests/test_eval_runs.py`
  - `tests/test_eval_signal_getattr_default_probe.py`
  - the accepted planning decision behind this tranche is to extend the eval layer, not the lower runtime layer, with one narrow defaulted `getattr(obj, name, default)` pilot
  - the `EVAL.md` correction updates the evidence ledger so `c592dca` is the latest pushed code/test authority and the pushed `getattr(obj, name)` pilot is no longer described as workspace-only
  - eval eligibility is widened only from simple-name `getattr` with `argument_count == 2` to include the simple-name defaulted form with `argument_count == 3`
  - the new pilot remains exactly `1 task x 1 budget x 3 providers` with budget `220`
  - providers remain `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
  - this eval pilot covers only the default-return branch via `lookup_outcome=returned_default_value`
  - the defaulted `getattr(obj, name, default)` selector and selected unit remain primary `unsupported/opaque`, with runtime-backed provenance attached additively only
  - the docs/evidence reconciliation keeps the public-safe quad-matrix comparative surface unchanged and describes the defaulted `getattr(obj, name, default)` work only as narrow internal eval-only evidence
  - targeted validation passed:
    - `.venv/bin/python -m ruff check src/context_ir/eval_oracles.py src/context_ir/eval_providers.py tests/test_eval_oracles.py tests/test_eval_providers.py tests/test_eval_runs.py tests/test_eval_signal_getattr_default_probe.py`
    - `.venv/bin/python -m ruff format --check src/context_ir/eval_oracles.py src/context_ir/eval_providers.py tests/test_eval_oracles.py tests/test_eval_providers.py tests/test_eval_runs.py tests/test_eval_signal_getattr_default_probe.py`
    - `.venv/bin/python -m mypy --strict src/context_ir/eval_oracles.py src/context_ir/eval_providers.py`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_oracles.py -k "getattr or dynamic_import or hasattr" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_providers.py -k "getattr or dynamic_import or hasattr" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_runs.py -k "getattr_default_probe or getattr_probe or dynamic_import_probe or hasattr_probe" -q`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_signal_getattr_default_probe.py -q`
  - docs/evidence validation passed:
    - `git diff --check -- EVAL.md PUBLIC_CLAIMS.md README.md ARCHITECTURE.md`
  - release-unit audit passed with no findings
  - full regression passed:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v`
    - pytest result: `567 passed`
  - release-doc wording correction passed:
    - `git diff --check -- EVAL.md PUBLIC_CLAIMS.md README.md ARCHITECTURE.md`
    - no `workspace-only`, `workspace tranche`, or `accepted workspace` wording remains in the release docs
  - commit-gating passed with no findings
  - local commit creation passed at `7d43302`
  - remote push completed at `7d43302`
- Prior pushed implementation release `c592dca` remains the `getattr(obj, name)` release anchor:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `evals/fixtures/oracle_signal_getattr_probe/`
  - `evals/tasks/oracle_signal_getattr_probe.json`
  - `evals/run_specs/oracle_signal_getattr_probe_matrix.json`
  - `src/context_ir/eval_oracles.py`
  - `src/context_ir/eval_providers.py`
  - `tests/test_eval_oracles.py`
  - `tests/test_eval_providers.py`
  - `tests/test_eval_runs.py`
  - `tests/test_eval_signal_getattr_probe.py`
  - it adds a narrow internal `REFLECTIVE_BUILTIN` / `getattr(obj, name)` eval pilot at `1 task x 1 budget x 3 providers`
  - the budget is `220`
  - providers are `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
  - eligibility is constrained to simple-name `getattr` with `argument_count == 2`
  - the `getattr(obj, name)` unsupported selector and selected unit remain primary `unsupported/opaque`, with runtime-backed provenance attached additively only
  - the same-tranche docs/evidence reconciliation updates `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md` to cover the accepted internal `getattr(obj, name)` pilot without widening public claims, package-root exports, MCP behavior, schema, scoring, or winner selection
  - release-unit audit found no issues
  - full regression passed:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v`
  - pytest result: `558 passed`
  - commit-gating review passed
  - local commit creation passed at `c592dca`
  - remote push completed at `c592dca`
- The only current local workspace modifications should be:
  - `PLAN.md`
  - `BUILDLOG.md`
- Prior pushed implementation release `762dd51` remains the `hasattr(obj, name)` provider/budget matrix authority:
  - `evals/run_specs/oracle_signal_hasattr_probe_matrix.json`
  - `tests/test_eval_signal_hasattr_probe.py`
  - `tests/test_eval_runs.py`
  - the `hasattr(obj, name)` internal pilot now runs `1 task x 2 budgets x 3 providers`
  - the budgets are `220` and `100`
  - `context_ir` still carries the intended `unsupported/opaque` selected unit with additive runtime provenance at both budgets
  - both baselines remain structurally empty for this pilot, including the tighter `100` budget row
  - summary/report-facing assertions still prove additive-only runtime provenance and no primary `runtime_backed` selected-unit tier
  - the slice passed targeted validation, full regression, commit-gating review, local commit creation, and remote push
  - it does not widen source boundaries, public claims, package-root exports, MCP behavior, schema, scoring, winner selection, tasks, or fixtures
- Prior pushed implementation release `90dcc15` has passed corrected release-unit audit, full regression, commit-gating review, local commit creation, and remote push:
  - `src/context_ir/eval_oracles.py`
  - `src/context_ir/eval_providers.py`
  - `evals/fixtures/oracle_signal_hasattr_probe/`
  - `evals/tasks/oracle_signal_hasattr_probe.json`
  - `evals/run_specs/oracle_signal_hasattr_probe_matrix.json`
  - `tests/test_eval_signal_hasattr_probe.py`
  - `tests/test_eval_oracles.py`
  - `tests/test_eval_providers.py`
  - `tests/test_eval_runs.py`
  - this release adds fixture-local `hasattr_runtime_observations` loading and Context IR provider pass-through via the existing tool facade seam
  - the pilot is one task x one budget (`220`) x three providers (`context_ir`, `lexical_top_k_files`, `import_neighborhood_files`)
  - the `hasattr(obj, name)` unsupported selector remains primary `unsupported/opaque`, with runtime-backed provenance only as additive attached evidence
  - baselines expose no structured selected units or attached runtime provenance for this pilot
  - package-root exports, public claims, MCP, analyzer, tool-facade, source runtime-acquisition semantics, scoring, winner selection, existing dynamic-import matrix boundaries, and schema version remain unchanged
  - corrected release-unit audit, full regression, commit-gating review, and local commit creation have passed
  - remote push has passed
- The first read-only release-unit audit for the `hasattr` pilot found one P2 issue:
  - `evals/fixtures/oracle_signal_hasattr_probe/eval_runtime_observations.json` uses `normalized_payload` fields `lookup_outcome=attribute_present` and `result=true`
  - accepted `hasattr(obj, name)` runtime evidence uses the minimal boolean shape `attribute_present=true|false`
  - narrow correction is accepted: the fixture now uses `attribute_present=true`, and `tests/test_eval_signal_hasattr_probe.py` asserts the exact loaded fixture payload
  - corrected audit accepted the release unit with no findings
  - full regression passed:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v`
    - pytest result: `549 passed`
  - commit-gating review passed and pushed commit `90dcc15` contains only the implementation release unit
- Pushed implementation release `9a52b46` has passed release-unit audit, full regression, commit-gating review, local commit creation, and remote push:
  - `evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json`
  - `tests/test_eval_signal_dynamic_import_probe.py`
  - `tests/test_eval_runs.py`
  - the dynamic-import pilot now runs 1 task x 2 budgets (`220`, `180`) x 3 providers (`context_ir`, `lexical_top_k_files`, `import_neighborhood_files`)
  - provider-scoped accounting assertions preserve the distinction between scalar winner selection and additive runtime-provenance accounting
  - the implementation remains internal-only and does not alter source code, public claims, schema, scoring, winner selection, package-root exports, MCP, or runtime-acquisition breadth
  - release-unit audit found no issues and recommended acceptance
  - full regression passed:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
  - commit-gating review found the implementation release unit is limited to the three authorized files and separable from continuity docs
  - pushed commit `9a52b46` contains only the three implementation files
- Docs-only continuity sync records:
  - the execution-lane overreach correction
  - the control-reviewed `hasattr` pilot planning decision
  - the `hasattr` implementation acceptance, correction, audit, regression, commit, and push
  - the pushed `90dcc15` release state
  - the pushed docs-only runtime-backed evidence/claim reconciliation commit `3291268`
  - the pushed continuity/process correction commit `8133e0a`
  - the pushed `762dd51` `hasattr` matrix expansion release state
- Pushed workflow authority exists in:
  - `AGENTS.md`
  - `AGENTS.md` codifies that slice acceptance is workspace-only by default, commits happen at coherent release-unit boundaries, and a release-unit audit is the default pre-commit quality gate
- Repo-backed and local release state is now explicit and complete:
  - historical pushed runtime-outcome accounting release authority is `d8ebdc3`
  - prior pushed defaulted `getattr(obj, name, default)` default-return branch release authority is `7d43302`
  - latest pushed docs-only continuity/process correction commit in the current release chain is `8133e0a`
  - latest pushed docs-only evidence/claim reconciliation commit remains `3291268`
  - prior pushed `getattr(obj, name)` release authority remains `c592dca`
  - prior pushed `hasattr` pilot release authority remains `90dcc15`
  - the accepted internal `DYNAMIC_IMPORT` provider/budget matrix expansion release unit remains `9a52b46`
  - the accepted provider-scoped selected-unit capability-tier accounting release unit is `215b6bb`
  - the accepted capability-tier eval / evidence code/test/pilot release unit is `a605b22`
  - docs-only continuity commits after `a605b22`, including pushed continuity through `6435434`, pushed evidence-doc reconciliation `3291268`, and pushed process correction `8133e0a`, are not implementation release changes
  - the previously accepted runtime-backed tranche at `cb1dc65` remains historical released state and must not be routed as workspace-only work
- The prior capability-tier eval / evidence baseline remains repo-backed at `a605b22`:
  - accepted tier-aware eval storage-contract slice is released in:
    - `src/context_ir/eval_oracles.py`
    - `src/context_ir/eval_providers.py`
    - `src/context_ir/eval_results.py`
    - `tests/test_eval_oracles.py`
    - `tests/test_eval_providers.py`
    - `tests/test_eval_results.py`
    - `tests/test_eval_runs.py`
  - accepted isolated internal `DYNAMIC_IMPORT` eval pilot is released in:
    - `src/context_ir/eval_oracles.py`
    - `src/context_ir/eval_providers.py`
    - `evals/fixtures/oracle_signal_dynamic_import_probe/`
    - `evals/tasks/oracle_signal_dynamic_import_probe.json`
    - `evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json`
    - `tests/test_eval_oracles.py`
    - `tests/test_eval_providers.py`
    - `tests/test_eval_runs.py`
    - `tests/test_eval_signal_dynamic_import_probe.py`
  - accepted tier-aware internal-accounting rollout is released in:
    - `src/context_ir/eval_summary.py`
    - `tests/test_eval_summary.py`
    - `tests/test_eval_report.py`
    - `tests/test_eval_signal_dynamic_import_probe.py`
    - the internal summary/report path now consumes existing raw selector expectation and selected-unit capability-tier fields
    - separate internal accounting now exists for declared selector tier/provenance expectations and actual selected-unit tier/provenance
    - legacy scalar scoring, winner selection, schema version, public claims, and exposure boundaries remain unchanged
  - accepted full-regression gate confirmed the enlarged eval/evidence unit was locally clean before commit and push:
    - `.venv/bin/python -m ruff check src/ tests/`
    - `.venv/bin/python -m ruff format --check src/ tests/`
    - `.venv/bin/python -m mypy --strict src/`
    - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
  - accepted commit-gating review defined the exact coherent release unit now pushed at `a605b22`:
    - `src/context_ir/eval_oracles.py`
    - `src/context_ir/eval_providers.py`
    - `src/context_ir/eval_results.py`
    - `src/context_ir/eval_summary.py`
    - `tests/test_eval_oracles.py`
    - `tests/test_eval_providers.py`
    - `tests/test_eval_report.py`
    - `tests/test_eval_results.py`
    - `tests/test_eval_runs.py`
    - `tests/test_eval_summary.py`
    - `tests/test_eval_signal_dynamic_import_probe.py`
    - `evals/fixtures/oracle_signal_dynamic_import_probe/`
    - `evals/tasks/oracle_signal_dynamic_import_probe.json`
    - `evals/run_specs/oracle_signal_dynamic_import_probe_matrix.json`
  - `PLAN.md` and `BUILDLOG.md` are separate docs-only continuity-sync files outside that pushed release unit
  - the docs-only continuity sync is limited to:
    - `PLAN.md`
    - `BUILDLOG.md`
- Release-boundary holds remain unchanged:
  - keep `context_ir.tool_facade` as the highest exposed hybrid entry point
  - do not widen package-root/public low-level runtime-observation exposure
  - do not widen MCP runtime-observation exposure
  - keep public claim boundaries unchanged from the accepted internal-eval state
- Further inherited-call reopening remains on explicit hold: no next implementation slice is authorized beyond the accepted first-exclusive-branch overlap reopening
- Push for `a605b22` is complete; docs-only continuity pushes through `6435434`, evidence-doc reconciliation `3291268`, and process correction `8133e0a` are complete; implementation pushes for `9a52b46`, `90dcc15`, and `762dd51` are complete
- The accepted post-release planning spike found no concrete defect requiring `a605b22` to be reopened
- Provider-scoped selected-unit capability-tier accounting is released in:
  - `src/context_ir/eval_summary.py`
  - `tests/test_eval_summary.py`
  - `tests/test_eval_report.py`
  - `tests/test_eval_signal_dynamic_import_probe.py`
- The accepted provider-scoped accounting slice:
  - adds provider selected-unit totals and attached-runtime-provenance totals
  - adds provider plus actual-primary-tier selected-unit totals and attached-runtime-provenance totals
  - preserves legacy scalar provider aggregates, task-budget rows, ledger-wide tier tables, schema version, scoring, winner selection, public claims, and exposure holds
- Full regression passed on the workspace containing the accepted provider-scoped accounting slice:
  - `.venv/bin/python -m ruff check src/ tests/`
  - `.venv/bin/python -m ruff format --check src/ tests/`
  - `.venv/bin/python -m mypy --strict src/`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v -m "not slow"`
  - pytest result: `539 passed, 1 deselected`
- Commit-gating review accepted the exact local code/test release unit now committed at `215b6bb`:
  - `src/context_ir/eval_summary.py`
  - `tests/test_eval_summary.py`
  - `tests/test_eval_report.py`
  - `tests/test_eval_signal_dynamic_import_probe.py`
- Remote push for `215b6bb` is complete

## What Is Next

Immediate next route: create a local commit for the exact four-file local
Python subprocess stdin execution wiring release unit. Current pushed
source/contract authority is
`0a3c4c6 Add local Python worker stdin transport`, with release-routing
continuity through
`9a25fbf Sync local Python stdin transport release routing`. Release-gate
status is no-active-gate for `0a3c4c6`. Do not reopen pushed stdin transport,
worker payload, handler adapter, executor attempt wrapper, stdout failure
normalization, observed attempt, stdout protocol, nonzero failure
normalization, subprocess execution, completion, invocation, environment
context, dispatch table, or prior releases absent new findings.

Accepted workspace-only local Python subprocess stdin execution wiring slice:

- wires the existing raw local-Python subprocess executor to materialize
  `RuntimeProbeLocalPythonWorkerRequestStdinTransport` before launch and pass
  its deterministic `stdin_text` to `subprocess.run(...)` as text-mode stdin
- preserves the existing invocation, cwd, child environment, timeout,
  `shell=False`, captured stdout/stderr, completion materialization, exception
  propagation from the raw executor, and attempt-normalization wrapper behavior
- validates the invocation, completion contract revision, worker request payload,
  and stdin transport before subprocess launch
- rejects invocation/stdin/payload drift before `subprocess.run(...)`
- keeps success, nonzero, timeout, generic exception, malformed stdout, and
  dispatch paths flowing through the existing materializers
- no worker module, concrete family/form semantics, global registration, temp
  files, filesystem IO, stdout protocol changes, observed-result synthesis,
  result assembly changes, admission, recompile, facade, MCP, package-root,
  schema, eval, scoring, optimizer, compiler, docs, or public claims

Current release state for the selected stdin execution wiring slice:

- selected by control: yes
- implementation lane launched: yes
- implementation returned: yes
- accepted in workspace: yes, first-pass
- implementation validation reported by execution lane: passed, including
  requested subset reporting `287 passed`
- focused control validation: passed with `50 passed, 148 deselected`
- focused control ruff check: passed
- release-unit-audit-cleared: yes
- full-regression-cleared: yes, full pytest `1049 passed`
- commit-gating-cleared: yes
- staged: no
- locally committed: no
- pushed: no
- expected implementation files:
  `src/context_ir/runtime_probe_execution.py` and
  `tests/test_runtime_probe_execution.py`
- control-route continuity files:
  `PLAN.md` and `BUILDLOG.md`
- proposed release unit is exactly:
  `BUILDLOG.md`, `PLAN.md`,
  `src/context_ir/runtime_probe_execution.py`, and
  `tests/test_runtime_probe_execution.py`
- next route: local commit creation for the exact four-file unit

The local Python subprocess non-proof attempt normalization slice is accepted
in workspace after one correction. It adds pure module-local helpers that
convert local Python subprocess failure facts into non-proof
`RuntimeProbeExecutionAttempt` values:

- `subprocess.TimeoutExpired` maps to `TIMED_OUT`
- other local subprocess execution exceptions map to non-proof attempts,
  defaulting to `CRASHED`
- nonzero `RuntimeProbeLocalPythonProcessCompletion.returncode` maps to a
  non-proof attempt, defaulting to `CRASHED`
- configured non-proof outcomes for nonzero completions are supported
- `RuntimeProbeResultOutcome.OBSERVED` is rejected at the helper boundary
- zero-returncode completions reject or remain deferred

Release-gate finding and correction:

- Gate 1 found that the accepted release-unit wording overclaims identity
  preservation
- the produced `RuntimeProbeExecutionAttempt` preserves runner request,
  request object, and execution input identity, but it has no fields for
  invocation or completion object identity
- the materializers revalidate invocation/completion contracts before attempt
  materialization, but they do not preserve those objects in the resulting
  attempt
- Ryan authorized the recommended narrow continuity/spec correction
- active wording now states that invocation/completion contracts are revalidated
  while runner request, request object, and execution input identity are
  preserved in the produced attempt

Corrected boundary:

- do not widen `RuntimeProbeExecutionAttempt` to carry invocation or completion
  identity in this slice; that would expand the source contract beyond the
  intended non-proof failure-normalization boundary
- rerun the combined read-only release gate over the exact four-file unit

Current release state for the proposed local Python subprocess non-proof
attempt normalization unit:

- selected by control: yes
- implementation lane launched: yes
- implementation returned: yes
- review finding: missing configured-outcome and observed-outcome rejection
  coverage
- correction authorized by Ryan: yes
- correction returned: yes
- release-gate finding: identity preservation overclaim in continuity/spec
  wording, corrected after Ryan authorization
- accepted in workspace: yes, after one implementation correction and one
  continuity/spec correction
- focused validation: passed with `199 passed`
- release-unit-audit-cleared: yes
- full-regression-cleared: yes, full pytest `961 passed`
- commit-gating-cleared: yes
- staged: yes, then committed
- locally committed: yes, `5b10728`
- pushed: yes, with `origin/main` advanced through `c471fd1`
- next route: bounded read-only local Python success-boundary next-move spike

The runtime probe runner-request attempt/result assembly release is pushed at
`3363929 Assemble runtime probe runner request attempts` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

Released unit:

- `src/context_ir/runtime_probe_execution.py`
- `tests/test_runtime_probe_execution.py`
- `PLAN.md`
- `BUILDLOG.md`

The runtime probe runner-request materialization release is pushed at
`68a8e73 Materialize runtime probe runner requests` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

Released unit:

- `src/context_ir/runtime_probe_execution.py`
- `tests/test_runtime_probe_execution.py`
- `PLAN.md`
- `BUILDLOG.md`

The runtime probe execution-attempt result assembly release is pushed at
`86be8d7 Assemble runtime probe execution attempts` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

Released unit:

- `src/context_ir/runtime_probe_execution.py`
- `tests/test_runtime_probe_execution.py`
- `PLAN.md`
- `BUILDLOG.md`

The corrected combined read-only release gate passed with no findings, full
regression passed with `869 passed`, local commit creation is complete, and
Ryan-authorized push is complete.

The runtime probe execution-input materialization release is pushed at
`cfed3c7 Add runtime probe execution input materialization` and has
release-gate status no-active-gate. It should not be reopened absent new
findings.

The released slice adds internal non-executing typed execution-attempt records
tied to `RuntimeProbeExecutionInput` and a deterministic helper that
converts a complete attempt set for a `RuntimeProbeExecutionInputBatch` into
`RuntimeProbeResultBatch`. It does not execute probes, collect runtime
observations, admit observations, attach provenance, recompile, serialize
JSON/schema, widen `tool_facade.py`, `mcp_server.py`, `context_ir/__init__.py`,
or touch eval, scoring, optimizer, compiler, package-root, product, benchmark,
or public-claim surfaces.

The runner-request materialization slice is workspace-only accepted first-pass
and release-gate-cleared, local commit creation is complete at
`68a8e73 Materialize runtime probe runner requests`. It adds frozen internal
runner-request records tied to `RuntimeProbeExecutionInput` and a deterministic
helper that turns a complete `RuntimeProbeExecutionInputBatch` into an ordered
runner-request batch. It does not execute probes. The runner-request contract
preserves plan ID, request IDs, request object identity, execution-input object
identity, replay artifact identity, batch order, explicit runner contract
revision, timeout, and explicit runner environment/assumption fields. It
rejects drift, duplicates, blank metadata, invalid timeout, empty runner
environment, and empty runner assumptions. The combined read-only release gate
passed with no findings: Gate 1 release-unit audit passed, Gate 2 full
regression passed with `876 passed`, Gate 3 commit-gating passed, and
Ryan-authorized push is complete.

The runner-request attempt/result assembly slice is workspace-only accepted
first-pass and release-gate-cleared, local commit creation is complete at
`3363929 Assemble runtime probe runner request attempts`, and Ryan-authorized
push is complete. It adds an internal helper that accepts a
`RuntimeProbeRunnerRequestBatch` plus typed `RuntimeProbeExecutionAttempt`
values, validates attempts against the runner requests, and returns a
deterministic `RuntimeProbeResultBatch` in runner-request plan order. It does
not execute probes. It preserves runner request order, plan ID, request IDs,
request object identity, execution-input object identity, replay artifact
identity, and existing observed/non-proof result behavior. It rejects
unplanned, duplicate, missing, plan-drifted, request-drifted,
execution-input-drifted, runner-request-drifted, blank, and malformed attempt
metadata.

The combined read-only release gate passed with no findings: Gate 1
release-unit audit passed, Gate 2 full regression passed with `882 passed`,
and Gate 3 commit-gating passed.

Ryan-authorized push is complete.

The runtime probe diagnostic runner-request preparation slice is
workspace-only accepted first-pass, release-gate-cleared, locally committed at
`fd0f6d8 Prepare runtime probe diagnostic runner requests`, and pushed. It
adds a frozen internal preparation envelope and helper that take a
`SemanticDiagnosticResult` with an attached `planned_runtime_probe_request_plan`,
materialize the corresponding `RuntimeProbeExecutionInputBatch`, and then
materialize the corresponding `RuntimeProbeRunnerRequestBatch`. It does not
execute probes. It preserves diagnostic object identity, request plan object
identity, request object identities, plan IDs, request IDs,
execution-input identity, replay artifact identity, runner metadata, and
deterministic plan order. It rejects missing diagnostic plans,
diagnostic/request-plan drift, blank probe or runner metadata, empty runtime
assumptions, invalid timeout, and drift already rejected by the pushed
input/runner-request materialization contracts.

Release state for the diagnostic runner-request preparation unit:

- proposed release unit is exactly:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- workspace-only accepted
- release-unit-audit-cleared
- full-regression-cleared with `885 passed`
- commit-gating-cleared
- locally committed at `fd0f6d8`
- Ryan-authorized push completed with `origin/main` advanced through
  `74d84fb Sync runtime probe diagnostic runner request release routing`
- release-gate status is no-active-gate

The runtime probe runner-callable attempt collection slice is workspace-only
accepted first-pass, release-gate-cleared, locally committed at
`32f6220 Collect runtime probe runner attempts`, and pushed. It adds an
internal strict runner-callable attempt collection boundary. It accepts a
`RuntimeProbeRunnerRequestBatch` and a typed runner callable, validates the
batch before invocation, calls the runner exactly once per
`RuntimeProbeRunnerRequest` in runner-request order, collects only typed
`RuntimeProbeExecutionAttempt` values, validates and assembles them through the
existing runner-request-gated result-batch helper, and returns a frozen
internal envelope preserving the runner request batch, ordered attempts, and
result batch. It supports empty runner-request batches without invoking the
callable. It does not implement subprocess execution, in-process probe
execution, family/form-specific probe logic, timeout enforcement,
exception-to-result synthesis, admission, recompile, facade/MCP/package-root
export, schema, eval, scoring, optimizer, compiler, benchmark, or public
claims. Runner exceptions propagate; failure outcomes remain the
responsibility of a runner callable that returns typed non-proof attempts.

Release state for the runner-callable attempt collection unit:

- proposed release unit is exactly:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- workspace-only accepted
- release-unit-audit-cleared
- full-regression-cleared with `891 passed`
- commit-gating-cleared
- locally committed at `32f6220`
- Ryan-authorized push completed with `origin/main` advanced through
  `e9b5b5a Sync runtime probe runner attempt collection release routing`
- release-gate status is no-active-gate

The runtime probe diagnostic runner-callable recompile bridge slice is
workspace-only accepted first-pass. It adds a frozen internal envelope and
helper that compose diagnostic runner-request preparation, runner-callable
attempt collection, and the existing result-batch recompile helper. It accepts
a `SemanticDiagnosticResult` with an attached
`planned_runtime_probe_request_plan`, runtime probe preparation metadata, a
typed `RuntimeProbeRunnerCallable`, and the existing semantic recompile inputs.
It preserves diagnostic preparation, runner attempt collection, and
result-batch recompile application identity; preserves non-proof results as
non-proof; propagates runner exceptions; and leaves empty planned request
batches deterministic without runner invocation. It does not implement
subprocess execution, in-process repository probe execution,
family/form-specific probe logic, timeout enforcement, exception-to-result
synthesis, admission rule changes, recompile rule changes, facade/MCP/
package-root export, schema, eval, scoring, optimizer, compiler, benchmark, or
public claims.

Release state for the diagnostic runner-callable recompile bridge unit:

- proposed release unit is exactly:
  - `src/context_ir/runtime_observation_recompile.py`
  - `tests/test_runtime_observation_recompile.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- release-unit-audit-cleared
- full-regression-cleared with `895 passed`
- commit-gating-cleared
- staged: no
- locally committed at `74fb275 Compose runtime probe runner callable recompile`
- pushed with `origin/main` advanced through
  `f463df7 Sync runtime probe callable recompile release routing`
- release-gate status is no-active-gate

The runtime probe runner failure-normalization adapter slice is workspace-only
accepted first-pass. It adds an opt-in internal adapter in
`src/context_ir/runtime_probe_execution.py` that wraps a
`RuntimeProbeRunnerCallable` so `Exception` failures raised by the runner
become typed non-proof `RuntimeProbeExecutionAttempt` values for the matching
`RuntimeProbeRunnerRequest`, while successful typed attempts continue through
unchanged by object identity. The existing strict collector still propagates
runner exceptions when no adapter is used, untyped runner returns are rejected
rather than normalized, and `BaseException` subclasses still propagate. The
adapter preserves request, execution-input, replay-artifact, runner-request
identity, and runner-request batch order through existing gates, and keeps
crash, timeout, missing-environment, and setup-failure outcomes non-proof. It
does not implement subprocess execution, in-process repository probe
execution, timeout enforcement, family/form-specific probe logic, admission
rule changes, recompile rule changes, facade/MCP/package-root export, schema,
eval, scoring, optimizer, compiler, benchmark, or public claims.

Release state for the runtime probe runner failure-normalization adapter unit:

- proposed release unit is exactly:
  - `src/context_ir/runtime_probe_execution.py`
  - `tests/test_runtime_probe_execution.py`
  - `PLAN.md`
  - `BUILDLOG.md`
- release-unit-audit-cleared
- full-regression-cleared with `903 passed`
- commit-gating-cleared
- staged: no
- locally committed at `93456b6 Normalize runtime probe runner failures`
- pushed with `origin/main` advanced through
  `4f13fac Sync runtime probe failure normalization routing`
- release-gate status is no-active-gate

The runtime probe runner dispatch table slice is accepted first-pass in
workspace-only state. Proposed release unit:

- `src/context_ir/runtime_probe_execution.py`
- `tests/test_runtime_probe_execution.py`
- `PLAN.md`
- `BUILDLOG.md`

The slice adds an internal frozen typed handler registry keyed by
`(RuntimeProbeFamily, form_label)` and a dispatching
`RuntimeProbeRunnerCallable` that validates `RuntimeProbeRunnerRequest`,
selects handlers by carried request family/form, and returns typed handler
attempts unchanged. Missing handlers return deterministic non-proof attempts,
defaulting to `RuntimeProbeResultOutcome.SETUP_FAILED`, while preserving
runner-request identity and replay artifact identity through existing gates.
Duplicate handler keys, blank form labels, observed missing-handler outcomes,
untyped handler returns, and handler identity drift reject or flow through
existing runner-request-gated assembly. Handler-raised exceptions propagate
unless the handler or dispatch runner is explicitly wrapped with the existing
failure-normalizing adapter. The slice does not add concrete family/form probe
behavior, subprocess execution, in-process repository probe execution, timeout
enforcement, admission rule changes, recompile rule changes,
facade/MCP/package-root export, schema, eval, scoring, optimizer, compiler,
benchmark, or public claims.

Release state for the runtime probe runner dispatch table unit:

- accepted in workspace: yes, first-pass
- release-unit-audit-cleared: yes, no findings
- focused validation: passed with `232 passed`
- full-regression-cleared: yes, full pytest `912 passed`
- commit-gating-cleared: yes
- staged: no
- locally committed at `3751df1 Add runtime probe runner dispatch table`
- pushed with `origin/main` advanced through
  `d7fe447 Sync runtime probe dispatch routing`
- release-gate status is no-active-gate
- next route: internal runtime probe runner environment context implementation
  slice

The runtime probe runner environment context slice is accepted first-pass in
workspace-only state. Proposed release unit:

- `src/context_ir/runtime_probe_execution.py`
- `tests/test_runtime_probe_execution.py`
- `PLAN.md`
- `BUILDLOG.md`

The slice adds a frozen typed `RuntimeProbeLocalPythonEnvironmentContext` and
`derive_runtime_probe_local_python_environment_context(...)` in
`src/context_ir/runtime_probe_execution.py`. It revalidates
`RuntimeProbeRunnerRequest` before deriving the context, parses
`runner_environment` into repository root, working directory, and ordered
Python path entries, preserves runner contract revision, timeout seconds,
runner environment, and runner assumptions for replay, and rejects missing
required singleton fields, duplicate singleton metadata, blank path metadata,
relative path metadata, and malformed path metadata. The context remains
module-local through `context_ir.runtime_probe_execution.__all__`, with no
package-root export.

Release state for the runtime probe runner environment context unit:

- accepted in workspace: yes, first-pass
- focused validation: passed with `163 passed`
- release-unit-audit-cleared: yes, no findings
- full-regression-cleared: yes, full pytest `925 passed`
- commit-gating-cleared: yes
- staged: no
- locally committed at `f75196e Add runtime probe runner environment context`
- pushed with `origin/main` advanced through
  `646298b Sync runtime probe environment context local routing`
- release-gate status is no-active-gate
- next route: select the next bounded control action after the pushed release

The slice does not inspect the filesystem, import modules, execute repository
code, spawn subprocesses, enforce timeouts, generate observed attempts, change
dispatch behavior, admission, recompile, facade/MCP/package-root export,
schema, eval, scoring, optimizer, compiler, benchmark, or public claims.

The runtime probe result-batch recompile tranche is pushed at
`591c09b Compose runtime probe result batch recompile` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

The runtime probe result admission bridge tranche is pushed at
`ccd417a Add runtime probe result admission bridge` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The runtime probe execution-result/replay-artifact contract tranche is pushed
at `eb6def0 Add runtime probe result contracts` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The typed facade runtime recompile tranche is pushed at
`8ac3b46 Add typed runtime recompile facade` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The runtime observation recompile composition tranche is pushed at
`b279b00 Compose runtime observation recompile flow` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

The diagnostic trace-refresh tranche is pushed at
`74aadd7 Refresh diagnostic runtime trace support` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The diagnostic runtime observation application tranche is pushed at
`95f7545 Apply diagnostic runtime observations` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The admitted runtime observation provenance bridge tranche is pushed at
`35c440d Attach admitted runtime observations` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The runtime observation admission compatibility validation tranche is pushed
at `f5c8df0 Validate runtime observation admission compatibility` and has
release-gate status no-active-gate. It should not be reopened absent new
findings.

The diagnostic runtime observation admission bridge tranche is pushed at
`8706f2e Add diagnostic runtime observation admission bridge` and has
release-gate status no-active-gate. It should not be reopened absent new
findings.

- `src/context_ir/runtime_observation_admission.py`
- `tests/test_runtime_observation_admission.py`
- `PLAN.md`
- `BUILDLOG.md`

The released slice adds
`admit_runtime_observations_for_diagnostic(diagnostic, observations)` as a
module-local helper in `src/context_ir/runtime_observation_admission.py`. It
uses the diagnostic's existing `planned_runtime_probe_request_plan`, rejects
diagnostics without an attached plan, and delegates to the released
`admit_runtime_observations_for_plan(...)` plan-level helper. It preserves
diagnostic/request/plan/observation object identity, deterministic plan order,
plan IDs, request IDs, empty-plan behavior, and the existing plan-level
unmatched/duplicate observation rejection.

The slice does not rederive runtime probe requests or plans from a program,
execute probes, define execution-result contracts, attach provenance, mutate
diagnostics/programs/requests/plans/observations, change analyzer or
tool-facade behavior, expose package-root or MCP APIs, or widen eval, schema,
scoring, optimizer, compiler, winner-selection, product, public benchmark, or
public-claim surfaces.

The internal runtime observation admission read-model tranche is pushed at
`b0a5ec5 Add runtime observation admission read model` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

- `src/context_ir/runtime_observation_admission.py`
- `tests/test_runtime_observation_admission.py`
- `PLAN.md`
- `BUILDLOG.md`

Ryan explicitly authorized opening this narrow observation-admission scope
after `fce09b0`. The authorized scope is limited to an internal read-model
contract: an already-collected typed runtime observation may be admitted only
when its source-site identity matches a request in a `RuntimeProbeRequestPlan`.
The slice must not execute probes, attach provenance, change analyzer or
tool-facade behavior, expose package-root or MCP APIs, or widen eval, schema,
scoring, optimizer, compiler, winner-selection, product, public benchmark, or
public-claim surfaces.

The post-`7c46f48` North Star planning/control spike is accepted. It selected
`index_runtime_probe_request_plan_by_source_site(plan)` in
`src/context_ir/runtime_probe_requests.py` as the next smallest meaningful
capability slice. This slice stays on the planned side: it indexes a
`RuntimeProbeRequestPlan` by the same source-site identity convention already
used by runtime request derivation and runtime acquisition matching, and it
rejects duplicate source-site ambiguity. The implementation slice is pushed at
`6d5fc47 Index runtime probe plans by source site` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The semantic diagnostic runtime probe request plan surfacing tranche is pushed
at `7c46f48 Surface semantic diagnostic probe plans` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

The diagnostic runtime probe request plan bridge tranche is pushed at
`97dc0f6 Add diagnostic runtime probe request plans` and has release-gate
status no-active-gate. It should not be reopened absent new findings.

The planned runtime probe request plan tranche is pushed at
`744bf0e Add runtime probe request plans` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The planned runtime probe request ID indexing tranche is pushed at
`3df02c6 Index runtime probe requests by ID` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The stable planned runtime probe request identity tranche is pushed at
`49fa461 Add runtime probe request identities` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The completed diagnose/recompile bridge-consumption tranche is pushed at
`a819cf5 Surface diagnostic runtime probe requests` and has release-gate status
no-active-gate. It should not be reopened absent new findings.

The next control/planning lane must preserve the remaining holds: no probe
execution, execution-result contract, runtime observation collection,
analyzer/tool-facade behavior, package-root API, MCP, eval, schema, scoring,
optimizer, compiler, winner-selection, product, public benchmark, or
public-claim widening. Runtime provenance attachment is authorized only for
the already-pushed admitted-batch bridge at `35c440d`, through existing
additive runtime acquisition helpers.

Do not route `6d5fc47 Index runtime probe plans by source site` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `7c46f48 Surface semantic diagnostic probe plans` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `97dc0f6 Add diagnostic runtime probe request plans` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `744bf0e Add runtime probe request plans` back to docs review,
release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `3df02c6 Index runtime probe requests by ID` back to docs review,
release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `49fa461 Add runtime probe request identities` back to docs review,
release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `a819cf5 Surface diagnostic runtime probe requests` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `2e448ea Add diagnostic runtime probe request bridge` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `f6c66e4 Add runtime probe request planning contract` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

Do not route `546a4da Add reflective builtin branch eval probes` back to docs
review, release-unit audit, focused validation, full regression, commit-gating,
staging, local commit creation, or push absent new findings.

`546a4da Add reflective builtin branch eval probes` is complete and pushed,
with release status no-active-gate. It is the current pushed code/eval release
authority.

`d73cde4 Expand original dynamic import budget coverage` is complete and
pushed, with release status no-active-gate. It is the prior pushed code/eval
release authority. Do not route `d73cde4` back to docs review, release-unit
audit, focused validation, full regression, commit-gating, staging, local
commit creation, or push absent new findings.

`e2f3dcf Expand dir-zero and metaclass budget coverage` is complete and pushed,
with release status no-active-gate. It is the prior pushed code/eval authority,
not the active route. Do not route `e2f3dcf` back to docs review,
release-unit audit, full regression, commit-gating, staging, local commit
creation, or push absent new findings.

`8aa38d5 Sync dir-zero metaclass release routing` is the prior pushed
continuity authority. `642b6f9 Sync exec eval release routing` is the earlier
pushed continuity authority. `21f2dc5 Expand exec and eval budget coverage` is
the earlier pushed code/eval authority and is no-active-gate.
`9fffc5e Sync dynamic import release routing`,
`c2c1898 Expand dynamic import sibling eval budget coverage`,
`98edc4a Codify release gate continuity controls`,
`b8e126e Expand runtime mutation eval budget coverage`, and
`ad9db8d Expand dir eval budget coverage` remain older pushed authorities and
are no-active-gate. Do not reopen `546a4da`, `d73cde4`, `e2f3dcf`, `8aa38d5`,
`642b6f9`, `21f2dc5`, `c2c1898`, `9fffc5e`, `98edc4a`, `b8e126e`, `ad9db8d`,
or earlier pushed releases absent new findings. Push remains Ryan-gated for any
future release. Do not widen
public/API/MCP/package-export/schema/scoring/optimizer/compiler/
winner-selection/product/public benchmark scope without a separately
authorized planning decision.

Completed post-5bd0616 planning decision:

- The next smallest evidence-building capability wedge is not a new runtime
  family. It was a budget-pressure expansion of the
  `oracle_signal_getattr_attribute_error_probe_matrix`, now released at
  `43d0439`.
- The implementation slice edited only:
  - `evals/run_specs/oracle_signal_getattr_attribute_error_probe_matrix.json`
  - `tests/test_eval_signal_getattr_attribute_error_probe.py`
- The slice adds budget `100` beside `220`, preserves the same fixture, task,
  query, providers, selector truth, and
  `lookup_outcome=raised_attribute_error` runtime payload, and asserts the
  same unsupported/opaque selected unit with additive runtime provenance at
  both budgets.
- Baseline providers remain empty at both budgets.
- Source, fixtures, task JSON, release-facing docs, public claims,
  package-root APIs, MCP behavior, analyzer/tool-facade/runtime behavior,
  schema, scoring, optimizer, compiler, winner-selection, product, and public
  benchmark changes remain out of scope for this released expansion.

Completed latest pushed release unit:

- Treat the internal eval-only `REFLECTIVE_BUILTIN` / `dir(obj)`
  budget-pressure expansion as completed and pushed at
  `ad9db8d Expand dir eval budget coverage`.
- Released budget-pressure expansion files:
  - `evals/run_specs/oracle_signal_dir_probe_matrix.json`
  - `tests/test_eval_signal_dir_probe.py`
- Docs/evidence/continuity reconciliation files:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- The matrix is `oracle_signal_dir_probe_matrix`: 1 task x 2 budgets x 3
  providers at budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`.
- Fixture, task, query, and runtime payload remain unchanged across both
  budget rows; runtime payload remains `listing_entry_count=74`.
- Selector and selected-unit truth remain `unsupported/opaque`; runtime
  provenance remains additive only; baseline providers remain empty at both
  budgets; public comparative claims remain bounded to the existing quad
  matrix.
- Excluded surfaces remain source beyond the released run-spec/test
  expansion, fixtures, task JSON, `AGENTS.md`,
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/
  winner-selection/product/public benchmark changes.
- Docs/evidence/continuity reconciliation is accepted first-pass;
  release-unit audit cleared first-pass; full regression cleared first-pass
  with `709 passed`.
- Commit-gating, local commit creation, and Ryan-authorized push completed at
  `ad9db8d`.
- No active release gate remains for
  `ad9db8d Expand dir eval budget coverage` absent new findings.
- Do not route back to docs review, release-unit audit, full regression,
  commit-gating, staging, local commit creation, or push for `ad9db8d` absent
  new findings.

Prior pushed release unit:

- Treat the internal eval-only `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` budget-pressure expansion as
  completed and pushed at
  `43d0439 Expand getattr AttributeError eval budget coverage`.
- Eval-only pilot files:
  - `evals/fixtures/oracle_signal_getattr_attribute_error_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_getattr_attribute_error_probe/main.py`
  - `evals/run_specs/oracle_signal_getattr_attribute_error_probe_matrix.json`
  - `evals/tasks/oracle_signal_getattr_attribute_error_probe.json`
  - `tests/test_eval_signal_getattr_attribute_error_probe.py`
- Docs/evidence/continuity reconciliation files:
  - `ARCHITECTURE.md`
  - `EVAL.md`
  - `PUBLIC_CLAIMS.md`
  - `README.md`
  - `PLAN.md`
  - `BUILDLOG.md`
- The matrix is `oracle_signal_getattr_attribute_error_probe_matrix`: 1
  task x 2 budgets x 3 providers at budgets 220 and 100, against providers
  `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- Fixture boundary is exactly `getattr(obj, name)`, with `AttributeError`
  caught so `render_probe_digest()` is deterministic
- Runtime payload is `lookup_outcome=raised_attribute_error`; primary selector
  and selected-unit truth remain `unsupported/opaque`; runtime provenance
  remains additive only; no dependency edge or selected symbol is created from
  the missing attribute
- Excluded forms remain generalized reflective-builtin support, dependency
  edges or selected symbols from missing attributes, product surface changes,
  schema changes, scoring changes, optimizer changes, compiler changes,
  winner-selection changes, and any
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening
- Implementation accepted first-pass.
- The original budget-220 pilot docs/evidence/continuity reconciliation was
  accepted after 2 corrections.
- The budget-pressure docs/evidence/continuity reconciliation was accepted
  first-pass.
- Release-unit audit cleared first-pass.
- Full regression cleared first-pass with `709 passed`.
- The first commit-gating review rejected with P1 stale-routing findings in
  `PLAN.md` and `BUILDLOG.md`.
- The routing correction was accepted first-pass.
- Corrected commit-gating cleared first-pass.
- Budget-pressure commit-gating, local commit creation, and Ryan-authorized push
  completed at `43d0439`.
- No active release gate remains for
  `43d0439 Expand getattr AttributeError eval budget coverage` absent new
  findings.
- Do not route back to docs review, release-unit audit, full regression,
  commit-gating, staging, local commit creation, or push for `43d0439` absent
  new findings.

Earlier pushed release unit:

- Treat the initial budget-220 internal eval-only `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` pilot as completed and pushed at
  `5bd0616 Add getattr AttributeError eval probe`.
- The prior pushed matrix was
  `oracle_signal_getattr_attribute_error_probe_matrix`: 1 task x 1 budget x 3
  providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`.
- Fixture boundary, runtime payload, selector truth, and non-goals match the
  latest `43d0439` tranche except that the prior pushed matrix did not include
  budget 100.
- Local commit creation and Ryan-authorized push completed at `5bd0616`.
- Do not route back to docs review, release-unit audit, full regression,
  commit-gating, staging, local commit creation, or push for `5bd0616` absent
  new findings.

Earlier pushed release unit:

- Treat the builtins-alias pilot assets as completed and pushed at
  `6ac1e28 Add builtins-alias dynamic import eval probe`:
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/main.py`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/plugins/__init__.py`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_alias_probe/plugins/weather.py`
  - `evals/run_specs/oracle_signal_dynamic_import_builtins_alias_probe_matrix.json`
  - `evals/tasks/oracle_signal_dynamic_import_builtins_alias_probe.json`
  - `tests/test_eval_signal_dynamic_import_builtins_alias_probe.py`
- The matrix is `oracle_signal_dynamic_import_builtins_alias_probe_matrix`: 1
  task x 1 budget x 3 providers at budget 220, against providers
  `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- Fixture boundary is `import builtins as loader`,
  `name = "plugins.weather"`, and exactly `loader.__import__(name)`, with
  bounded `sys.modules[name]` retrieval only
- Runtime payload is `imported_module=plugins.weather`; primary selector and
  selected-unit truth remain `unsupported/opaque`; runtime provenance remains
  additive only; no dependency edge or selected symbol is created from
  `plugins.weather`
- Source/contract prerequisite and eval-only sibling were accepted first-pass.
- Docs/evidence/continuity reconciliation was accepted after one correction.
- Release-unit audit cleared first-pass.
- Full regression cleared first-pass with `702 passed`.
- Corrected commit-gating cleared first-pass after stale-routing corrections.
- Local commit creation and Ryan-authorized push completed at `6ac1e28`.
- Do not route back to release-unit audit, full regression, commit-gating,
  staging, local commit creation, or push for `6ac1e28` absent new findings.

Earlier pushed release unit:

- Treat the builtins-attribute pilot assets as completed and pushed at
  `3dfc355 Add builtins-attribute dynamic import eval probe`:
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_attr_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_attr_probe/main.py`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_attr_probe/plugins/__init__.py`
  - `evals/fixtures/oracle_signal_dynamic_import_builtins_attr_probe/plugins/weather.py`
  - `evals/run_specs/oracle_signal_dynamic_import_builtins_attr_probe_matrix.json`
  - `evals/tasks/oracle_signal_dynamic_import_builtins_attr_probe.json`
  - `tests/test_eval_signal_dynamic_import_builtins_attr_probe.py`
- The matrix is `oracle_signal_dynamic_import_builtins_attr_probe_matrix`: 1
  task x 1 budget x 3 providers at budget 220, against providers
  `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
- Fixture boundary is `import builtins`, `name = "plugins.weather"`, and
  exactly `builtins.__import__(name)`, with bounded `sys.modules[name]`
  retrieval only
- Runtime payload is `imported_module=plugins.weather`; primary selector and
  selected-unit truth remain `unsupported/opaque`; runtime provenance remains
  additive only; no dependency edge or selected symbol is created from
  `plugins.weather`
- Treat the prior root-module alias pilot assets as completed and pushed at
  `b85f038 Add root-alias dynamic import eval probe`.
- The root-module alias matrix is `oracle_signal_dynamic_import_root_alias_probe_matrix`: 1 task
  x 1 budget x 3 providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`
- Fixture boundary is `import importlib as loader`,
  `name = "plugins.weather"`, and exactly `loader.import_module(name)`
- Runtime payload is `imported_module=plugins.weather`; primary selector and
  selected-unit truth remain `unsupported/opaque`; runtime provenance remains
  additive only; no dependency edge or selected symbol is created from
  `plugins.weather`
- Excluded forms remain root-module `importlib.import_module(name)` expansion,
  imported-name `import_module(name)` expansion, imported-alias
  `load_module(name)` expansion, literal dynamic import expansion,
  `__import__(name)`, `builtins.__import__`, globals/locals/fromlist forms,
  namespace mutation, generated-code dependency modeling, generalized dynamic
  import support, and any
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening
- Implementation/assets were accepted workspace-only before release; corrected
  docs/evidence/continuity reconciliation was accepted after one P1
  state-neutrality correction; release-unit audit cleared first-pass; full
  regression cleared first-pass with `688 passed`; commit-gating cleared
  first-pass; local commit creation completed at `b85f038`; Ryan-authorized
  push completed at `b85f038`
- There is no active release gate for `b85f038`

Prior pushed release unit:

- Treat the imported-alias pilot assets as completed and pushed at `4030845`:
  - `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/eval_runtime_observations.json`
  - `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/main.py`
  - `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/plugins/__init__.py`
  - `evals/fixtures/oracle_signal_dynamic_import_imported_alias_probe/plugins/weather.py`
  - `evals/run_specs/oracle_signal_dynamic_import_imported_alias_probe_matrix.json`
  - `evals/tasks/oracle_signal_dynamic_import_imported_alias_probe.json`
  - `tests/test_eval_signal_dynamic_import_imported_alias_probe.py`
- Release-unit audit cleared first-pass
- Full regression cleared first-pass with `682 passed`
- First commit-gating rejected with P1 stale-routing findings in `PLAN.md` and
  `BUILDLOG.md`
- Continuity correction accepted first-pass
- Corrected commit-gating cleared first-pass
- Local commit creation completed at `4030845`
- Ryan-authorized push completed at `4030845`
- There is no active release gate for `4030845`
- The released matrix is
  `oracle_signal_dynamic_import_imported_alias_probe_matrix`: 1 task x 1
  budget x 3 providers at budget 220, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`
- Fixture boundary is `from importlib import import_module as load_module`,
  `name = "plugins.weather"`, and exactly `load_module(name)`
- Runtime payload is `imported_module=plugins.weather`; primary selector and
  selected-unit truth remain `unsupported/opaque`; runtime provenance remains
  additive only; no dependency edge or selected symbol is created from
  `plugins.weather`
- Excluded forms remain root-module `importlib.import_module(name)` expansion,
  imported-name `import_module(name)` expansion, literal
  `load_module("plugins.weather")` expansion, `loader.import_module(name)`,
  `__import__(name)`, `builtins.__import__`, globals/locals/fromlist forms,
  namespace mutation, generated-code dependency modeling, generalized dynamic
  import support, and any
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening

Current pushed release authority:

- Treat pushed commit `3dfc355 Add builtins-attribute dynamic import eval
  probe` as the latest pushed release authority:
  - `oracle_signal_dynamic_import_builtins_attr_probe_matrix` is 1 task x 1
    budget x 3 providers at budget 220
  - providers remain `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `import builtins`, `name = "plugins.weather"`, and
    exactly `builtins.__import__(name)`, with bounded `sys.modules[name]`
    retrieval only
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or selected symbol is created from `plugins.weather`
  - no builtins alias form is included by this matrix; no bare
    `__import__(name)` expansion, shadowed/rebound/aliased forms, wrong-arity
    forms, literal `builtins.__import__("plugins.weather")` expansion,
    fromlist/globals/locals forms, namespace mutation, generated-code
    dependency modeling, or generalized dynamic import support is included
  - no public benchmark claim, API, MCP, package export, schema, scoring,
    optimizer, compiler, product, or winner-selection widening is authorized
  - implementation/assets were accepted workspace-only before release;
    docs/evidence/continuity reconciliation accepted first-pass; release-unit
    audit cleared first-pass; full regression passed with `696 passed`;
    commit-gating cleared first-pass; local commit creation and
    Ryan-authorized push completed at `3dfc355`
  - do not reopen `3dfc355` absent new findings
- Treat pushed commit `b9a493b Sync root-alias release routing` as a prior
  pushed continuity authority. It does not change eval/test release contents
  or authorize a new
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark boundary.
- Treat pushed commit `b85f038 Add root-alias dynamic import eval probe` as
  the prior root-module alias eval/test/docs release authority.
- Treat pushed commit `8a83a9b Sync imported-alias release routing` as a prior
  pushed continuity authority. It does not change eval/test release
  contents or authorize a new
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark boundary.
- Treat pushed commit `4030845 Add imported-alias dynamic import eval probe`
  as the prior dynamic-import imported-alias eval/test/docs release authority:
  - `oracle_signal_dynamic_import_imported_alias_probe_matrix` is 1 task x 1
    budget x 3 providers at budget 220
  - providers remain `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `from importlib import import_module as load_module`,
    `name = "plugins.weather"`, and exactly `load_module(name)`
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or selected symbol is created from `plugins.weather`
  - no imported-name `import_module(name)` expansion, root-module
    `importlib.import_module(name)` expansion, literal
    `load_module("plugins.weather")` expansion, `loader.import_module(name)`,
    `__import__(name)`, `builtins.__import__`, globals/locals/fromlist forms,
    namespace mutation, generated-code dependency modeling, or generalized
    dynamic import support is included
  - no public benchmark claim, API, MCP, package export, schema, scoring,
    optimizer, compiler, product, or winner-selection widening is authorized
  - release-unit audit cleared first-pass; full regression passed with
    `682 passed`; first commit-gating rejected with P1 stale-routing findings;
    continuity correction accepted first-pass; corrected commit-gating cleared
    first-pass; local commit creation and Ryan-authorized push completed at
    `4030845`
  - do not reopen `4030845` absent new findings
- Treat pushed commit `5d2d7e4 Sync imported-name dynamic import release routing`
  as the prior pushed continuity authority. It does not change eval/test
  release contents or authorize a new
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark boundary.
- Treat pushed commit `ee71a82 Add imported-name dynamic import eval probe` as
  the prior imported-name dynamic-import eval/test/docs release authority:
  - `oracle_signal_dynamic_import_imported_name_probe_matrix` is 1 task x 1
    budget x 3 providers at budget 220
  - providers remain `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `from importlib import import_module`,
    `name = "plugins.weather"`, and exactly `import_module(name)`
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or selected symbol is created from `plugins.weather`
  - no root-module `importlib.import_module(name)` expansion, literal
    `import_module("plugins.weather")` expansion, alias `load_module(name)`,
    `loader.import_module(name)`, `__import__(name)`, `builtins.__import__`,
    globals/locals/fromlist forms, or generalized dynamic import support is
    included
  - no public benchmark claim, API, MCP, package export, schema, scoring,
    optimizer, compiler, product, or winner-selection widening is authorized
  - release-unit audit cleared first-pass; full regression passed with
    `676 passed`; first commit-gating returned P1 continuity findings; the
    continuity correction was accepted; corrected commit-gating cleared; local
    commit and Ryan-authorized push completed at `ee71a82`
  - do not reopen `ee71a82` absent new findings
- Treat pushed commit `ca191c8 Sync builtin dynamic import release routing` as
  the prior builtin dynamic-import continuity authority. It does not change
  eval/test release contents or authorize a new
  public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark boundary.
- Treat pushed commit `397c7dd Add builtin dynamic import eval probe` as the
  prior builtin dynamic-import eval/test/docs release authority:
  - `oracle_signal_dynamic_import_builtin_probe_matrix` is 1 task x 1 budget x
    3 providers at budget 220
  - providers remain `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `name = "plugins.weather"` and exactly
    `__import__(name)`, with bounded `sys.modules[name]` retrieval only
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or symbol is created from `plugins.weather`
  - no `importlib.import_module(name)`, imported-name `import_module(name)`,
    alias or loader forms, `builtins.__import__`, globals/locals/fromlist
    forms, or generalized dynamic import support is included
  - no public benchmark claim, API, MCP, package export, schema, scoring,
    optimizer, compiler, product, or winner-selection widening is authorized
  - release-unit audit cleared first-pass; full regression passed with
    `670 passed`; commit-gating cleared first-pass; local commit and
    Ryan-authorized push completed at `397c7dd`
  - do not reopen `397c7dd` absent new findings
- Treat pushed commit `ad22ea6 Sync dynamic import root release routing` as an
  earlier pushed dynamic-import root release-routing continuity authority.
- Treat pushed commit `14b362e Add dynamic import root runtime eval pilot` as
  the prior root-module dynamic-import eval/test/docs release authority:
  - `oracle_signal_dynamic_import_root_probe_matrix` is 1 task x 1 budget x 3
    providers at budget 220
  - providers remain `context_ir`, `lexical_top_k_files`, and
    `import_neighborhood_files`
  - fixture boundary is `import importlib`, `name = "plugins.weather"`, and
    exactly `importlib.import_module(name)`
  - runtime payload is `imported_module=plugins.weather`
  - primary selector and selected-unit truth remain `unsupported/opaque`
  - runtime provenance remains additive only
  - no dependency edge or symbol is created from the dynamically imported module
  - no `__import__(name)`, imported-name `import_module(name)`, alias or loader
    forms, or generalized dynamic import support is included
  - no public benchmark claim, API, MCP, package export, schema, scoring,
    optimizer, compiler, product, or winner-selection widening is authorized
  - release-unit audit cleared first-pass; full regression passed with
    `664 passed`; commit-gating cleared first-pass; local commit and
    Ryan-authorized push completed at `14b362e`
  - do not reopen `14b362e` absent new findings

Historical release anchors below remain guardrails and non-reopen constraints,
not pending release gates.

1. Treat pushed commit `bcd6d68 Add exec source runtime eval pilot` as the
   prior pushed exec(source) release authority:
   - `oracle_signal_exec_probe_matrix` is 1 task x 1 budget x 3 providers at
     budget 220
   - providers remain `context_ir`, `lexical_top_k_files`, and
     `import_neighborhood_files`
   - fixture/call boundary is `source = "pass"` and exactly `exec(source)`;
     executed source parses as exactly one `ast.Pass`
   - runtime proof requires `execution_outcome=completed`,
     `source_shape=literal_statement`, `source_sha256 == sha256(b"pass")`,
     and non-empty `durable_payload_reference`
   - optional `statement_kind=pass` is additive summary only
   - primary selector and selected-unit truth remain `unsupported/opaque`
   - runtime provenance remains additive only and attaches only to the
     preserved `EXEC_OR_EVAL` unsupported finding for `exec(source)`
   - no dependency edge or symbol is created from executed source
   - no namespace mutation modeling or generated-code dependency modeling is
     added
   - no generalized exec support is included
   - public comparative claims remain bounded to the existing quad matrix
   - no public benchmark claim, API, MCP, package export, schema, scoring,
     optimizer, compiler, product, or winner-selection widening is authorized
   - release-unit audit initially found one P1 digest-boundary issue; the
     correction pinned `source_sha256` to `sha256(b"pass")`; audit rerun
     cleared; full regression passed; commit-gating cleared; local commit
     creation completed; Ryan-authorized push completed
   - do not reopen `bcd6d68` exec(source) absent new findings
2. Treat pushed commit `96fc03a Add eval runtime eval pilot` as the prior
   pushed release authority:
   - `oracle_signal_eval_probe_matrix` is 1 task x 1 budget x 3 providers at
     budget 220
   - providers remain `context_ir`, `lexical_top_k_files`, and
     `import_neighborhood_files`
   - runtime proof requires `evaluation_outcome=returned_value`,
     `source_shape=literal_expression`, valid `source_sha256`, and non-empty
     `durable_payload_reference`
   - optional `result_type=builtins.str` is additive summary only
   - primary selector and selected-unit truth remain `unsupported/opaque`
   - runtime provenance remains additive only and attaches only to the
     preserved `EXEC_OR_EVAL` unsupported finding for `eval(source)`
   - public comparative claims remain bounded to the existing quad matrix
   - no public benchmark claim, API, MCP, package export, schema, scoring,
     optimizer, compiler, product, or winner-selection widening is authorized
   - do not reopen `96fc03a` eval(source) absent new findings
3. Treat pushed commit `41f6b57 Add delattr runtime eval pilot` as the prior
   pushed eval/test/docs release authority:
   - `oracle_signal_delattr_probe_matrix` is 1 task x 1 budget x 3 providers at budget `220`
   - providers remain `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
   - runtime payload is `mutation_outcome=deleted_attribute`
   - selector and selected-unit primary truth remain `unsupported/opaque`
   - runtime provenance remains additive only
   - public comparative claims remain bounded to the existing quad matrix
   - implementation is accepted first-pass
   - same-tranche docs/evidence reconciliation is accepted first-pass
   - release-unit audit is accepted first-pass with no findings
   - full regression is accepted first-pass with `612 passed, 1 deselected`
   - commit-gating is accepted first-pass
   - local commit creation and Ryan-authorized push are complete
4. Treat the accepted post-`41f6b57` planning decision as complete:
   - no concrete finding requires reopening `41f6b57`
   - `setattr(obj, name, value)` is the smallest uncovered `RUNTIME_MUTATION`
     sibling with an accepted lower-layer seam and no eval-only matrix
   - `delattr` budget `100` expansion is rejected for now because budget
     expansion is not automatic and no specific unanswered comparison requires
     it before `setattr`
   - `METACLASS_BEHAVIOR` is rejected as the immediate next move because it is
     a different, more claim-sensitive family
   - family-level consolidation is rejected for now because a small truthful
     evidence slice remains available
   - next implementation is one bounded eval-only
     `oracle_signal_setattr_probe_matrix`
   - implementation accepted first-pass in workspace-only state
   - same-tranche docs/evidence reconciliation accepted first-pass in
     workspace-only state
   - release-unit audit accepted first-pass with no findings
   - full regression accepted first-pass with `619 passed`
   - commit-gating accepted first-pass
   - exact accepted file set is approved for local commit with subject
     `Add setattr runtime eval pilot`
   - live local commit and push state must be verified from git
5. Treat pushed commit `c1a12d7 Add dir(obj) eval pilot` as the prior pushed
   eval/test/docs release authority, pushed commit `2dd8404 Expand locals eval
   budget matrix` as the prior `locals()` budget-expansion release authority,
   pushed commit `38e9d5f` as the prior initial `locals()` pilot release
   authority, pushed commit `5f74ede` as the prior `globals()` budget-expansion
   release authority, pushed commit `631a303` as the prior initial `globals()`
   release authority, pushed commit `9eec985` as the prior zero-argument
   `vars()` budget-expansion release authority, pushed commit `71db72e` as the
   prior initial zero-argument `vars()` pilot release authority, pushed commit
   `2c6b54a` as the prior `vars(obj)` budget-expansion release authority,
   pushed commit `ead239d` as the prior initial `vars(obj)` pilot release
   authority, and pushed commit `1b555ef` as the prior `getattr` family release
   authority:
   - `c1a12d7` adds `oracle_signal_dir_probe_matrix` as 1 task x 1 budget x 3 providers at budget 220 against `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
   - `c1a12d7` carries durable dir listing proof via `durable_payload_reference`; optional `listing_entry_count` is additive summary only
   - `c1a12d7` keeps selector and selected-unit primary truth `unsupported/opaque`, keeps runtime provenance as additive provenance only, and does not widen public comparative claims
   - `c1a12d7` passed implementation review, docs/evidence reconciliation after correction, process guardrail note acceptance, release-unit audit, full regression after one formatting correction with `607 passed`, corrected commit-gating, local commit creation, and Ryan-authorized push
   - `c1a12d7` does not authorize generalized dir support, zero-argument dir support, budget 100 expansion, public claim widening, API, MCP, runtime acquisition, analyzer, tool facade, schema, scoring, optimizer, or winner-selection widening
   - `2dd8404` expands `oracle_signal_locals_probe_matrix` to 1 task x 2 budgets x 3 providers at budgets `100` and `220`
   - `2dd8404` passed implementation review, same-tranche docs reconciliation, release-unit audit, full regression, corrected commit-gating, local commit creation, and Ryan-authorized push
   - the `locals()` matrix keeps selector and selected-unit primary truth `unsupported/opaque`, keeps runtime-backed provenance additive only with `lookup_outcome=returned_namespace`, and does not change runtime-acquisition, analyzer, tool-facade implementation, package-root API, MCP, schema, scoring, winner-selection, public benchmark, generalized `locals()` support, or public-claim boundaries
   - `38e9d5f` adds the initial internal eval-only `RUNTIME_MUTATION` / `locals()` pilot at `1 task x 1 budget x 3 providers` with budget `220`
   - `5f74ede` expands the existing internal eval-only `RUNTIME_MUTATION` / `globals()` matrix from budget `[220]` to budgets `[220, 100]`
   - `5f74ede` keeps selector and selected-unit primary truth `unsupported/opaque`, keeps runtime-backed provenance additive only with `lookup_outcome=returned_namespace`, and does not change runtime-acquisition, analyzer, tool-facade implementation, package-root API, MCP, schema, scoring, winner-selection, public benchmark, or public-claim boundaries
   - `631a303` adds the initial internal eval-only `RUNTIME_MUTATION` / `globals()` pilot at `1 task x 1 budget x 3 providers` with budget `220`
   - `631a303` preserves `unsupported/opaque` primary truth, additive runtime provenance, and the public-safe quad-matrix comparative boundary
   - `9eec985` expands the internal zero-argument `REFLECTIVE_BUILTIN` / `vars()` matrix to `1 task x 2 budgets x 3 providers` at budgets `100` and `220`
   - `71db72e` adds the initial internal zero-argument `REFLECTIVE_BUILTIN` / `vars()` eval pilot at `1 task x 1 budget x 3 providers` with budget `220`
   - `2c6b54a` expands the internal `REFLECTIVE_BUILTIN` / `vars(obj)` matrix to `1 task x 2 budgets x 3 providers` at budgets `100` and `220`
   - `ead239d` adds the initial internal `REFLECTIVE_BUILTIN` / `vars(obj)` eval pilot at `1 task x 1 budget x 3 providers` with budget `220`
   - `1b555ef` expands the existing `getattr` family matrices to budgets `220` and `100`
   - each `getattr` family matrix remains `1 task x 2 budgets x 3 providers`
3. Treat pushed commit `159e363` as the post-push continuity anchor for the `1b555ef` release state, and treat `8133e0a` as the prior docs-only process-correction anchor:
   - it corrects the self-referential continuity loop
   - it restores tranche-style release sequencing discipline
   - neither commit changes eval/test/docs release contents or widens product boundaries
4. Treat pushed commit `3291268` as the latest docs-only evidence/claim reconciliation authority:
   - it updates `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - it does not widen code/test authority, public claims, package-root exports, MCP behavior, source boundaries, schema, scoring, or winner selection
5. Treat pushed commit `d8ebdc3` as the prior runtime-outcome accounting release authority:
   - internal eval runtime-outcome accounting over normalized runtime provenance payload data
   - separate summary/report outcome counts for payload key/value pairs such as `lookup_outcome=returned_default_value` and `lookup_outcome=returned_value`
   - existing selector-tier, selected-unit-tier, provider, provider+tier, scoring, and winner-selection accounting remains unchanged
   - no runtime-acquisition, analyzer, tool-facade, package-root export, MCP, public-claim, fixture, task, run-spec, provider, budget, or public-doc surface changed
   - release-unit audit, full regression gate, commit-gating review, local commit creation, and remote push completed
6. Treat pushed commit `b014595` as the prior defaulted `getattr(obj, name, default)` value-return branch release authority:
   - narrow internal eval-only `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` value-return branch sibling pilot
   - `1 task x 1 budget x 3 providers` with budget `220`
   - additive runtime provenance remains separate from primary `unsupported/opaque` truth
   - same-tranche docs/evidence reconciliation in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - release-unit audit, full regression gate, commit-gating review, local commit creation, and remote push completed
7. Treat pushed commit `7d43302` as the prior defaulted `getattr(obj, name, default)` default-return branch release authority:
   - narrow internal eval-only `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` default-return branch pilot
   - `1 task x 1 budget x 3 providers` with budget `220`
   - additive runtime provenance remains separate from primary `unsupported/opaque` truth
   - same-tranche docs/evidence reconciliation in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - release-unit audit, full regression gate, commit-gating review, local commit creation, and remote push completed
8. Treat pushed commit `c592dca` as the prior `getattr(obj, name)` release authority:
   - narrow internal `REFLECTIVE_BUILTIN` / `getattr(obj, name)` eval pilot
   - `1 task x 1 budget x 3 providers` with budget `220`
   - additive runtime provenance remains separate from primary `unsupported/opaque` truth
   - same-tranche docs/evidence reconciliation in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - release-unit audit, full regression gate, commit-gating review, local commit creation, and remote push completed
9. Treat pushed commit `762dd51` as the prior `hasattr(obj, name)` provider/budget matrix release authority:
   - internal `REFLECTIVE_BUILTIN` / `hasattr(obj, name)` provider/budget matrix expansion
   - budgets `220` and `100`
   - additive runtime provenance remains separate from primary truth
   - full regression gate, commit-gating review, local commit creation, and remote push completed
10. Treat pushed commit `90dcc15` as the prior narrow `hasattr(obj, name)` pilot release authority.
11. Treat pushed commit `9a52b46` as the prior internal dynamic-import matrix release authority:
   - internal `DYNAMIC_IMPORT` provider/budget matrix expansion
   - release-unit audit over the dynamic-import provider/budget matrix release unit
   - full regression gate, local commit creation, and remote push
12. Treat pushed commit `215b6bb` as the prior provider-scoped accounting release authority:
   - provider-scoped selected-unit capability-tier accounting
   - full regression gate over the provider-scoped accounting slice
   - commit-gating and remote push of the provider-scoped accounting release unit
13. Treat pushed commit `a605b22` as the prior capability-tier eval/evidence code/test/pilot release authority:
   - tier-aware eval storage-contract slice
   - isolated internal `DYNAMIC_IMPORT` eval pilot
   - accepted post-pilot planning spike that authorizes the tier-aware internal-accounting rollout boundary
   - accepted tier-aware eval summary/report internal-accounting rollout
   - accepted full-regression gate over the enlarged workspace-only unit
   - accepted commit-gating review over the enlarged workspace-only unit
   - local commit creation for the coherent code/test/pilot release unit
   - remote push of the coherent code/test/pilot release unit
   - docs-only continuity sync in `PLAN.md` and `BUILDLOG.md`
14. Treat the accepted post-`762dd51` planning decision as complete:
   - the next smallest truthful move was to open a third internal runtime-backed eval family now
   - the chosen family was `REFLECTIVE_BUILTIN` / `getattr(obj, name)`
   - the resulting tranche is now implemented, docs/evidence-reconciled, audit-cleared, regression-cleared, commit-gating-cleared, committed locally, and pushed at `c592dca`
15. Treat the accepted post-`c592dca` planning decision as complete:
   - the next smallest truthful move is one eval-only pilot for defaulted `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)`
   - prefer the default-return branch first
   - do not broaden budgets or open a new runtime family first
16. Treat pushed commit `7d43302` as the completed defaulted `getattr(obj, name, default)` default-return branch release:
   - one narrow `EVAL.md` authority correction to the pushed `c592dca` release state
   - one narrow eval-only defaulted `getattr(obj, name, default)` pilot
   - one same-tranche docs/evidence reconciliation in `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - no lower-layer runtime-acquisition, analyzer, tool-facade, package-root, MCP, schema, scoring, or winner-selection widening
17. Treat the release-unit audit, full regression gate, commit-gating review, local commit creation, and remote push for `7d43302` as accepted first-pass.
18. Treat the accepted post-`7d43302` planning decision as complete:
   - no concrete defect requires reopening `7d43302`
   - the current defaulted `getattr(obj, name, default)` evidence is explicitly limited to the default-return branch
   - runtime acquisition validation already admits `returned_value` for three-argument `getattr`
   - the next smallest truthful move is one additive internal eval-only sibling value-return branch pilot
19. Treat pushed commit `b014595` as the completed defaulted `getattr(obj, name, default)` value-return branch release:
   - add a sibling value-return fixture/task/run-spec/test set
   - keep the existing default-return probe unchanged
   - keep `1 task x 1 budget x 3 providers`, budget `220`, and the same provider set
   - keep primary truth `unsupported/opaque`
   - keep runtime-backed provenance additive only
   - do not widen package-root APIs, MCP exposure, analyzer/tool-facade behavior, runtime acquisition, schema, scoring, winner selection, public benchmark claims, or public product boundaries
20. Treat the accepted same-tranche docs/evidence reconciliation for `b014595` as pushed release state:
   - in-scope files were `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md`
   - it describes the value-return pilot as narrow internal eval-only evidence beside the existing default-return branch
   - it keeps primary truth `unsupported/opaque`
   - it keeps runtime-backed provenance additive only
   - it preserves public-safe quad-matrix comparative boundaries and does not widen public claims, package-root APIs, MCP behavior, runtime acquisition, schema, scoring, winner selection, or product positioning
21. Treat the dedicated read-only release-unit audit over the accumulated value-return branch tranche as accepted first-pass with no findings:
   - include the accepted value-return implementation slice
   - include the accepted same-tranche docs/evidence reconciliation
   - include the current continuity edits in `PLAN.md` and `BUILDLOG.md` as workspace-only continuity state, but do not let the audit edit them
   - no source/runtime-acquisition, analyzer, tool-facade, package-root, MCP, schema, scoring, winner-selection, public-claim, or product-positioning widening was found
22. Treat the full regression gate over the audit-cleared value-return branch tranche as accepted first-pass:
   - `.venv/bin/python -m ruff check src/ tests/` passed
   - `.venv/bin/python -m ruff format --check src/ tests/` passed
   - `.venv/bin/python -m mypy --strict src/` passed
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v` passed with `575 passed`
23. Treat commit-gating over the exact release-unit file set as accepted first-pass:
   - no findings
   - no source, default-return fixture, runtime-acquisition, analyzer, tool-facade, package-root, MCP, schema, scoring, winner-selection, public-claim, or product-positioning widening
   - release-unit files are approved for staging
   - `PLAN.md` and `BUILDLOG.md` remain excluded continuity state
24. Treat local commit creation as accepted first-pass:
   - `b014595 Add defaulted getattr value eval pilot`
   - local `HEAD` is `b014595`
   - `origin/main` is `b014595`
   - `PLAN.md` and `BUILDLOG.md` were kept excluded from the release-unit commit and handled in the post-push continuity sync
25. Treat remote push of `b014595` as accepted first-pass after explicit Ryan authorization.
26. Treat the accepted post-`b014595` runtime-outcome methodology/reporting planning spike as complete:
   - no concrete defect requires reopening `b014595`, `7d43302`, or earlier accepted release units
   - the defaulted `getattr(obj, name, default)` default-return and value-return branches are distinct at fixture/test level
   - current eval summary/report output still collapses both into attached-runtime-provenance counts instead of surfacing normalized runtime outcomes
   - the next smallest truthful implementation slice is internal eval outcome accounting for normalized runtime provenance payload data such as `lookup_outcome=returned_default_value` and `lookup_outcome=returned_value`
   - do not infer outcomes from task IDs or fixture names
   - do not add new fixtures, tasks, run specs, providers, budgets, runtime families, scoring, winner-selection, public APIs, MCP behavior, analyzer behavior, or public claims
27. Treat the accepted runtime-outcome methodology/reporting implementation slice as complete:
   - raw eval records now preserve attached runtime provenance `normalized_payload` fields in `runtime_provenance_records`
   - internal eval summary/report output now renders separate runtime outcome accounting rows for payload key/value counts such as `lookup_outcome=returned_default_value` and `lookup_outcome=returned_value`
   - existing selector-tier, selected-unit-tier, provider, provider+tier, scoring, and winner-selection accounting remains unchanged
   - no runtime-acquisition, analyzer, tool-facade, package-root export, MCP, public-claim, fixture, task, run-spec, provider, budget, or public docs surface changed in this implementation slice
   - targeted control-lane validation passed: ruff, format check, strict mypy over affected source files, focused pytest over affected eval tests, forbidden-surface diff check, and `git diff --check`
   - this acceptance is not commit readiness
28. Treat release-unit audit, full regression, commit-gating, local commit creation, and remote push for the runtime-outcome methodology/reporting hardening release unit as accepted first-pass:
   - dedicated read-only release-unit audit found no issues
   - full regression passed: `.venv/bin/python -m ruff check src/ tests/`, `.venv/bin/python -m ruff format --check src/ tests/`, `.venv/bin/python -m mypy --strict src/`, and `PYTHONPATH=src .venv/bin/python -m pytest tests/ -v` with `578 passed`
   - commit-gating approved exactly eight implementation files and kept `PLAN.md` / `BUILDLOG.md` excluded as continuity state
   - pushed commit `d8ebdc3 Add runtime outcome eval accounting` contains only the approved implementation release-unit files
   - `origin/main` is `d8ebdc3`
29. Treat the post-`d8ebdc3` `getattr` family evidence-broadening planning spike as accepted after 1 control correction:
   - no concrete defect requires reopening `d8ebdc3`, `b014595`, `7d43302`, or earlier accepted release units
   - the control correction fixed `EVAL.md` release-anchor wording so `hasattr(obj, name)` evidence is attributed to `90dcc15` / `762dd51`, while `c592dca` remains only the `getattr(obj, name)` anchor
   - `d8ebdc3` closes the runtime-outcome reporting blocker, so broader existing `getattr` evidence can proceed without another reporting slice first
   - the next smallest truthful implementation slice is to add budget `100` to the three existing `getattr` family run specs, creating `1 task x 2 budgets x 3 providers` for each existing task
   - no new fixture, task, provider, baseline, runtime family, public claim, source runtime acquisition, analyzer/tool-facade behavior, schema, scoring, winner-selection, package-root API, or MCP change is authorized
30. Treat the `getattr` family provider/budget matrix expansion as accepted first-pass in workspace-only state:
   - `oracle_signal_getattr_probe_matrix`, `oracle_signal_getattr_default_probe_matrix`, and `oracle_signal_getattr_default_value_probe_matrix` now use budgets `220` and `100`
   - each existing task is now `1 task x 2 budgets x 3 providers`
   - focused tests double expected selector/runtime-outcome/selected-unit/provider accounting from `3` to `6` where the added budget doubles the matrix
   - JSON validation, focused pytest, ruff over changed Python tests, forbidden-surface diff checks, and `git diff --check` passed
   - no source, fixture, task, provider, baseline, public claim, runtime-acquisition, analyzer/tool-facade, schema, scoring, winner-selection, package-root API, or MCP behavior changed
   - this acceptance is not commit readiness
31. Treat the same-tranche docs/evidence reconciliation for the `getattr` family provider/budget matrix expansion as accepted first-pass in workspace-only state:
   - `EVAL.md`, `PUBLIC_CLAIMS.md`, `README.md`, and `ARCHITECTURE.md` record the accepted internal evidence expansion without changing public claim boundaries
   - release-facing docs describe the three existing `getattr` family matrices as `1 task x 2 budgets x 3 providers` at budgets `100` and `220`
   - public-safe quad-matrix comparative wording remains unchanged
   - selector and selected-unit primary truth remain `unsupported/opaque`, and runtime-backed provenance remains additive only
   - no public benchmark, generalized `getattr`, generalized hybrid-runtime, public API, package-root API, MCP, scoring, winner-selection, analyzer/tool-facade, runtime-acquisition, fixture, task, run-spec, or provider widening is claimed
   - this acceptance is not commit readiness
32. Treat the release-unit audit for the accumulated `getattr` family provider/budget matrix expansion tranche as accepted first-pass:
   - the audit reviewed the governing docs, release-facing docs, three changed run specs, and five changed eval tests
   - the audit found no findings
   - the audit confirmed the expected 14-file dirty set, valid JSON run specs with budgets `[220, 100]`, unchanged forbidden surfaces, and focused validation passing with `42 passed`
   - the tranche is now audit-cleared
   - this is not full-regression clearance, commit-gating clearance, commit readiness, or push readiness
33. Treat the full regression gate for the accumulated `getattr` family provider/budget matrix expansion tranche as accepted first-pass:
   - ruff check over `src/` and `tests/` passed
   - ruff format check over `src/` and `tests/` passed with `77 files already formatted`
   - strict mypy over `src/` passed with no issues in 31 source files
   - full pytest passed with `578 passed`
   - the tranche is now audit-cleared and full-regression-cleared
   - this is not commit-gating clearance, commit readiness, local commit creation, or push readiness
34. Treat commit-gating over the exact `getattr` family provider/budget matrix expansion release file set as accepted first-pass:
   - no findings
   - dirty set exactly matches the expected 14-file release set
   - no staged changes were present during the commit-gating review
   - no source, runtime/API/MCP, schema, scoring, provider, fixture, or task files are included
   - the three changed run specs each have one case, budgets `[220, 100]`, and providers `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`
   - release-facing docs preserve public-safe quad-matrix boundaries, narrow internal `getattr` wording, selector and selected-unit `unsupported/opaque` truth, and additive runtime provenance
   - the approved local commit subject is `Expand getattr-family eval matrices`
   - this is not local commit creation or push readiness
35. Treat local commit creation for the `getattr` family provider/budget matrix expansion as accepted first-pass:
   - local commit `1b555ef Expand getattr-family eval matrices` was created on `main`
   - the committed file set matches the approved 14-file release unit
   - the commit body records budgets `100` beside `220`, 1 task x 2 budgets x 3 providers, unsupported/opaque primary truth, additive runtime provenance, and no public/API/MCP/runtime/scoring widening
   - local `HEAD` is `1b555ef`
36. Treat remote push of `1b555ef` as accepted first-pass after explicit Ryan authorization:
   - remote push of `1b555ef` completed
   - `1b555ef` became the pushed `getattr` family eval/test/docs release authority at that release point and is now superseded by later pushed release `ead239d`
   - the prior pushed code/test release authority `d8ebdc3` remains the runtime-outcome accounting anchor
   - this post-push continuity sync in `PLAN.md` and `BUILDLOG.md` records the repo-backed `1b555ef` release state
37. Release sequencing going forward must follow the restored tranche cadence:
   - accumulate multiple accepted slices locally until they form one coherent release unit or are just shy of becoming too large
   - keep continuity synced in workspace during that accumulation
   - run one dedicated findings-first deep release-unit audit over the whole accumulated diff before commit
   - correct audit findings before final regression / commit-gating / commit / push
   - do not return to per-slice commit/push churn without explicit reason and explicit Ryan sign-off
38. The next lane must not reopen:
   - the accepted pushed `c592dca` `getattr(obj, name)` release unit
   - the accepted pushed `7d43302` defaulted `getattr(obj, name, default)` release unit
   - the accepted `EVAL.md` authority correction released in `7d43302`
   - the accepted defaulted `getattr(obj, name, default)` default-return eval pilot slice released in `7d43302`
   - the accepted same-tranche docs/evidence reconciliation slice released in `7d43302`
   - the accepted pushed `b014595` defaulted `getattr(obj, name, default)` value-return branch release unit
   - the accepted same-tranche docs/evidence reconciliation for the value-return branch in `b014595`
   - the accepted `hasattr` provider/budget matrix release unit at `762dd51`
   - the accepted docs-only continuity/process correction commit at `8133e0a`
   - the accepted docs-only runtime-backed evidence/claim reconciliation commit at `3291268`
   - the accepted internal `hasattr(obj, name)` runtime-backed eval pilot release unit at `90dcc15`
   - the accepted code/test/pilot release unit at `a605b22`
   - the accepted provider-scoped accounting release unit at `215b6bb`
   - the accepted internal dynamic-import provider/budget matrix release unit at `9a52b46`
   - public claim boundaries
   - package-root/public low-level runtime-observation exposure
   - MCP runtime-observation exposure
   - further inherited-call work
   - scoring, winner selection, tasks, fixtures, providers, docs, public surfaces, or runtime-acquisition breadth
   - any run spec unless a later control-reviewed eval pilot explicitly authorizes it
39. Keep `context_ir.tool_facade` as the highest exposed hybrid entry point, keep package-root/public low-level plus MCP runtime-observation widening on explicit hold, and keep public claim boundaries unchanged.
40. Maintain the accepted hold on further inherited-call reopening beyond the accepted first-exclusive-branch overlap boundary.

## What Is Deferred

- Multi-language analysis beyond Python
- Broader decorator and metaprogramming support beyond the initial explicit subset
- Production packaging and distribution polish under the completed current milestone; broader production-grade delivery scope now awaits the new north-star rebaseline plan
- Portfolio or benchmark claims beyond what the rebaseline can prove
- Public claim updates until evidence-generating and claim-gating slices are accepted
- Any claim of benchmark leadership or production maturity until the corresponding post-milestone phases land with durable proof

## Historical Notes

- Any earlier Slice 1 or Slice 2 accepted corrections are historical improvements only. They may inform implementation details, but they do not govern the current roadmap.
- Existing workspace modules that reflect the retired baseline are implementation history, not current architectural authority.
- BUILDLOG retrospective findings remain operative evidence for why the reset occurred.

## What Should Not Be Reopened

- The accepted pushed `d73cde4` `DYNAMIC_IMPORT` original budget-pressure
  release unit, or any docs review, release-unit audit, focused validation,
  full regression, commit-gating, staging, local commit creation, or push route
  for it, unless a later findings-based review proves a concrete defect
- The accepted pushed `e2f3dcf` zero-argument `dir()` plus
  `METACLASS_BEHAVIOR` budget-pressure release unit, or any docs review,
  release-unit audit, full regression, commit-gating, staging, local commit
  creation, or push route for it, unless a later findings-based review proves a
  concrete defect
- The accepted pushed `21f2dc5` `EXEC_OR_EVAL` eval/exec budget-pressure
  release unit, or any docs review, release-unit audit, full regression,
  commit-gating, staging, local commit creation, or push route for it, unless
  a later findings-based review proves a concrete defect
- The accepted pushed `c2c1898` `DYNAMIC_IMPORT` sibling budget-pressure
  release unit unless a later findings-based review proves a concrete defect
- The accepted pushed `b8e126e` `RUNTIME_MUTATION` / `delattr(obj, name)` and
  `setattr(obj, name, value)` budget-pressure expansion release unit unless a
  later findings-based review proves a concrete defect
- The accepted pushed `125f088` tranche batching / throughput discipline
  process-doc release unit unless a later findings-based review proves a
  concrete defect
- The accepted pushed `ad9db8d` `REFLECTIVE_BUILTIN` / `dir(obj)`
  budget-pressure expansion release unit unless a later findings-based review
  proves a concrete defect
- The accepted pushed `43d0439` `REFLECTIVE_BUILTIN` /
  `getattr(obj, name)` raised-`AttributeError` budget-pressure expansion
  release unit unless a later findings-based review proves a concrete defect
- The accepted pushed `ee71a82` `DYNAMIC_IMPORT` / imported-name
  `import_module(name)` runtime eval pilot release unit unless a later
  findings-based review proves a concrete defect
- The accepted pushed `397c7dd` `DYNAMIC_IMPORT` / builtin
  `__import__(name)` runtime eval pilot release unit unless a later
  findings-based review proves a concrete defect
- The accepted pushed `bcd6d68` `EXEC_OR_EVAL` / `exec(source)` release unit
  unless a later findings-based review proves a concrete defect
- The accepted pushed `96fc03a` `EXEC_OR_EVAL` / `eval(source)` release unit
  unless a later findings-based review proves a concrete defect
- The accepted pushed `19d9a32` `METACLASS_BEHAVIOR` / preserved
  `metaclass=...` keyword-site release unit unless a later findings-based
  review proves a concrete defect
- The accepted pushed `14b362e` `DYNAMIC_IMPORT` / root-module
  `importlib.import_module(name)` runtime eval pilot release unit unless a
  later findings-based review proves a concrete defect
- The accepted pushed `ad22ea6` dynamic-import root release-routing continuity
  sync unless a later findings-based review proves a concrete defect
- The accepted pushed `c592dca` `REFLECTIVE_BUILTIN` / `getattr(obj, name)` release unit unless a later findings-based review proves a concrete defect
- The accepted pushed `7d43302` defaulted `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` release unit unless a later findings-based review proves a concrete defect
- The accepted `EVAL.md` authority correction released in `7d43302` unless a later findings-based review proves a concrete defect
- The accepted defaulted `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` default-return eval pilot slice released in `7d43302` unless a later findings-based review proves a concrete defect
- The accepted same-tranche docs/evidence reconciliation for defaulted `getattr(obj, name, default)` released in `7d43302` unless a later findings-based review proves a concrete defect
- The accepted pushed `b014595` defaulted `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` value-return branch release unit unless a later findings-based review proves a concrete defect
- The accepted same-tranche docs/evidence reconciliation for the defaulted `REFLECTIVE_BUILTIN` / `getattr(obj, name, default)` value-return branch in `b014595` unless a later findings-based review proves a concrete defect
- The accepted bounded runtime-backed tranche work for `DYNAMIC_IMPORT`, `REFLECTIVE_BUILTIN`, `RUNTIME_MUTATION`, and `METACLASS_BEHAVIOR` unless a later findings-based review proves a concrete defect
- The accepted tier-aware eval storage-contract slice unless a later findings-based review proves a concrete defect
- The accepted isolated internal `DYNAMIC_IMPORT` eval pilot unless a later findings-based review proves a concrete defect
- The accepted package-root/public low-level runtime-observation hold unless a later bounded planning spike explicitly authorizes widening
- The accepted MCP runtime-observation hold unless a later bounded planning spike explicitly authorizes widening
- The completed push decision for `cb1dc65`
- The completed phase 0 foundation as if it were incomplete or invalid
- The accepted quad matrix as anything other than the current top internal evidence surface
- The accepted `oracle_signal_smoke_b` / `200` `budget_pressure` limitation as if it were undocumented or silently fixed
- The current README / `PUBLIC_CLAIMS.md` / portfolio stack unless later evidence gates explicitly justify changes
- The April 13 frozen spec as if it were current authority
- The old Slice 1 -> Slice 6 correction chain
- The claim that exact 5-tier renderer semantics are already frozen
- The framing of `p_edit` / `p_support` as the public thesis instead of internal ranking policy
- The idea that the unresolved `recompile` contract is the primary control issue
- Any heuristic dependency claim that is not backed by the supported semantic layer
- The accepted bounded builtin-specific `dir` seam, the accepted bounded builtin-specific `globals` seam, the accepted bounded builtin-specific `locals` seam, the accepted bounded builtin-specific `delattr` seam, the accepted bounded builtin-specific `setattr` seam, and the completed current reflective-builtin/runtime-mutation runtime-backed queues unless a later findings-based review proves a concrete defect
- Accepted semantic-contract, syntax, binder, resolver/object-model, dependency/frontier, renderer, scorer, optimizer/compile, and diagnose/recompile contracts unless a later findings-based review proves a concrete defect
- Accepted raw-ledger, metric, and deterministic internal summary-rendering contracts unless a later findings-based review proves a concrete defect
- Accepted internal eval-report artifact and exact Markdown-write contracts unless a later findings-based review proves a concrete defect
- Accepted internal eval-pipeline composition and caller-path handling contracts unless a later findings-based review proves a concrete defect
- Accepted internal eval-run manifest and JSON-write contracts unless a later findings-based review proves a concrete defect
- Accepted internal eval bundle-directory filenames and path-alignment contracts unless a later findings-based review proves a concrete defect
- Accepted methodology-tightened signal smoke assets and their tight-budget baseline tradeoff unless a later findings-based review proves a concrete defect
- Accepted first recovery pass for `context_ir` on the signal smoke unless a later findings-based review proves a concrete defect
- Accepted competitive recovery for `context_ir` on the signal smoke unless a later findings-based review proves a concrete defect
- Accepted second methodology-tightened signal asset and pair-matrix orchestration unless a later findings-based review proves a concrete defect
- Accepted two-asset signal evidence review unless a later findings-based review proves a concrete defect
- Accepted semantic recovery for `context_ir` on `oracle_signal_smoke_b` unless a later findings-based review proves a concrete defect
- Accepted third methodology-tightened signal asset and triple-matrix orchestration unless a later findings-based review proves a concrete defect
- Accepted three-asset signal evidence review unless a later findings-based review proves a concrete defect
- Accepted `oracle_signal_smoke_c` edit-target recovery unless a later findings-based review proves a concrete defect
- Accepted post-recovery triple-matrix evidence review unless a later findings-based review proves a concrete defect
- Accepted smoke_c `240` budget-envelope widened correction unless a later findings-based review proves a concrete defect
- Accepted post-correction triple-matrix evidence review unless a later findings-based review proves a concrete defect
- Accepted smoke_b support-selection budget-pressure correction unless a later findings-based review proves a concrete defect
- Accepted post-support-correction triple-matrix evidence review unless a later findings-based review proves a concrete defect
- Accepted remaining helper-support budget-pressure correction unless a later findings-based review proves a concrete defect
- Accepted post-helper-correction triple-matrix evidence review unless a later findings-based review proves a concrete defect
