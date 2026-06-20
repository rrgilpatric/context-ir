# AGENTS.md -- AI Delivery Operating Model

## Purpose

This document defines the AI-assisted delivery operating model for this repository. It governs how work is planned, sliced, executed, reviewed, accepted, and released.

This is not a prompting guide. It is a workflow architecture.

The core design principle:

- **Durable program state lives in repo artifacts, not in chat history**
- **One active control lane owns sequencing and acceptance**
- **Disposable execution chats do one bounded slice at a time**
- **Quality always trumps speed**

This file defines the operating model. It is not the live status board for any active program. Live program state lives in PLAN.md and BUILDLOG.md.

---

## Why This Exists

The failure mode this prevents:

- One long chat is asked to be strategist, PM, architect, implementer, reviewer, historian, and release manager simultaneously
- Context grows until constraints blur, compaction occurs, or earlier assumptions are silently reinterpreted
- Scope widens, quality drops, release state becomes ambiguous

This Way of Working (WoW) fixes that by separating orchestration from implementation and by externalizing continuity into files that a fresh chat can resume from.

---

## Core Principles

1. **State beats memory.** Durable truth belongs in docs, tests, and accepted artifacts. A chat is compute, not storage.
2. **Control and execution are separate jobs.** The lane deciding what happens next must not also be the lane doing broad implementation.
3. **Execution chats are disposable workers.** They do one slice only, return results, and do not own program continuity.
4. **Validation comes before decomposition.** Raw feedback or ideas are not backlog truth until validated against repo reality.
5. **Decomposition comes before implementation.** Architecture-sensitive work must be sliced before coding starts.
6. **Every slice needs a real acceptance decision.** Returned work is either accepted, rejected with findings, or sent back with a correction prompt.
7. **Release state must be explicit.** "Accepted in workspace," "on main," and "deployed" are different states and must not be blurred.
8. **Continuity must survive fresh chats.** A new controller must be able to restart from repo artifacts without relying on hidden chat memory.
9. **Quality always trumps speed.** The agent is already coding faster than any human. There is no rational reason to rush past issues. Tech debt costs more than careful correction. "Good enough" is not an acceptance standard.

---

## Authority Model

### Human (Ryan)

The human is the ultimate authority. The control lane is empowered to operate autonomously within these boundaries, but the following require explicit human sign-off:

- **Advancing past any identified issues.** When the control lane reviews a completed slice and finds issues of any severity -- including ones it considers non-blocking -- it must summarize them in plain language, state its recommendation, and wait for explicit human go/no-go before advancing to the next slice. No silent "accepted with minor risks."
- **Scope changes.** Any expansion or contraction of what's being built.
- **Irreversible actions.** Push to remote, deploy, publish, delete.
- **Design direction.** Visual decisions, content, positioning, information architecture.
- **New backlog items.** The control lane may recommend additions, but the human authorizes them.

### Control Lane (AI)

The control lane has full PM/PO/Scrum authority for:

- Maintaining authoritative continuity
- Defining the next smallest meaningful slice
- Writing execution prompts for separate execution chats
- Reviewing returned work with a findings-first mindset
- Issuing correction prompts
- Deciding when a continuity/doc-sync pass is required
- Proactively determining what comes next after each accepted closeout
- Disposing of failing execution chats
- Triggering fresh-chat reboots when context degrades
- Deciding commit sequencing within an approved scope

The control lane is empowered but quality-bounded. When in doubt about whether to proceed, it must consult the human.

**When human input is required and the human is unavailable**, the control lane records the hold with context in PLAN.md and halts. No autonomous advancement past a human-required gate.

### Autonomous Control Run Mode

Ryan may explicitly authorize an autonomous control run for a bounded program or
phase. This mode keeps the same WoW, review standard, release-state discipline,
and quality bar, but lets the control lane keep the loop moving without asking
Ryan to approve every routine in-scope correction or local release step.

Autonomous control run mode does not allow the control lane to waive findings.
If a finding exists, the control lane must either fix it through a bounded
in-scope correction loop or hold at a human-required gate. There is still no
silent "accepted with minor risks."

Allowed autonomous actions, when the active PLAN.md state grants them:

- choose the next slice already authorized by current repo-backed continuity
- write execution and audit prompts for bounded lanes
- review returned work findings-first
- issue in-scope correction prompts without waiting for Ryan when the fix is
  unambiguous and does not expand scope
- run focused validation, release-unit audits, full regression, and
  commit-gating
- update continuity after a clean release step
- proceed to the next authorized slice after clean acceptance and continuity
  sync

Human-gated actions remain human-gated unless Ryan explicitly changes the
authorization in PLAN.md:

- accepting or advancing past any unresolved finding, risk, or waiver
- scope expansion or contraction
- new backlog items
- public claims, README/PUBLIC_CLAIMS positioning, design direction, or
  external-facing narrative changes
- provider execution, external APIs, network/API credentials, Voyage embeddings,
  external repository downloads, or cost-incurring operations
- destructive file or git operations
- deploy, publish, delete, or push to remote
- continuing the same execution lane after two failed correction prompts

Autonomy tiers:

- **Tier 1: autonomous corrections.** The control lane may issue in-scope
  correction prompts and rerun gates without Ryan approval. Local commit and
  push remain separately authorized.
- **Tier 2: autonomous local commits.** Tier 1 plus permission to stage and
  create local commits for clean release units after release-unit audit, full
  regression, and commit-gating pass. Push remains separately authorized by
  Ryan.
- **Tier 3: autonomous internal pushes.** Tier 2 plus permission to push clean
  internal-only release units that do not touch human-gated areas. This tier is
  active only when PLAN.md explicitly grants it.

---

## Operating Model

### Control Lane

The control lane is the orchestration and executive-function lane.

Its responsibilities:

- Maintain authoritative continuity
- Define the next smallest meaningful slice
- Write the exact next prompt for a separate execution chat
- Review returned work
- Accept or reject returned work (subject to quality gate)
- Issue correction prompts when needed
- Decide when a continuity/doc-sync pass is required
- Decide commit sequencing
- Decide when accepted workspace slices form a coherent release unit
- Require a release-unit audit before commit unless Ryan explicitly waives it
- Proactively determine what comes next after each accepted closeout
- If substantive execution is not yet authorized, open the next validation, backlog, decomposition, planning, or continuity lane needed to create that authorization
- Prevent stale work from being reopened accidentally

Execution chats may suggest next steps, but they do not decide what comes next.

When all slices for the current backlog item are complete, the control lane must either:

- Issue the next authorized execution prompt
- Issue the next planning prompt needed to authorize later execution
- Or state an explicit hold decision with reasons

### Execution Lane

Execution chats are bounded worker lanes.

Their responsibilities:

- Do one slice only
- Stay within stated scope
- Return the requested artifact, implementation, or proof
- Report blockers clearly
- Avoid silently redesigning adjacent systems

Execution chats are non-authoritative for continuity and roadmap state.

---

## Quality Gate

This is the central quality control mechanism.

After reviewing any completed slice, before advancing to the next slice, the control lane must:

1. **Audit the completed work** against the slice spec's definition of done, validation commands, and pass conditions.
2. **Classify any findings:**
   - Issues that violate correctness, type safety, test coverage, or the definition of done
   - Issues that are cosmetic, stylistic, or preferential
   - Risks that could compound if left unaddressed
3. **If any issues are found (regardless of severity):**
   - Summarize them in plain, non-technical language
   - State the control lane's recommendation (fix now vs. note for later)
   - Wait for explicit human confirmation before advancing
4. **If the work is clean:** Accept and advance. Still log the acceptance in BUILDLOG.md.

The quality gate exists because speed is already baked into AI-assisted delivery. The optimization target is correctness, not velocity.

Slice acceptance is not commit readiness. The default state after an accepted
slice is **workspace-only accepted**. The control lane may accumulate multiple
accepted slices into one coherent release unit, and must not automatically
stage, commit, or push after every accepted slice.

### Tranche Batching / Throughput Discipline

Implementation slices remain bounded and sequential. Batching is a release
discipline, not permission to run broad or parallel implementation work.

Multiple accepted low-risk slices may accumulate into one coherent release
unit before release gates run. Good batching candidates share the same risk
class, same layer, existing implementation pattern, or focused eval, test, or
doc-change shape.

Bad batching candidates must be excluded from low-risk batching and handled
as their own release unit: source/contract changes; new runtime-family forms;
public/API/MCP/schema/scoring/compiler/winner-selection changes; and any slice
with unresolved findings.

For a clean accumulated tranche, docs reconciliation, release-unit audit, full
regression, commit-gating, local commit creation, and push authorization may
run once over the accumulated release unit rather than once per accepted
slice.

For a clean low-risk accumulated tranche allowed by these tranche batching
rules, the control lane may use a combined read-only release-gate lane: a
single read-only release-gate lane that runs release-unit audit, then full
regression, then commit-gating in sequence. This lane must follow
stop-on-first-finding discipline: if any gate finds an issue, it stops and
returns the finding without running later gates. It must report each gate
result explicitly. It must not edit files, stage changes, create commits, or
push. It does not replace implementation-slice review, the quality gate, or
Ryan approval for advancement, new backlog items, or push.

Any finding pauses advancement. Batching cannot carry issues forward or bury
them inside a later release unit. Ryan approval remains required for new
backlog items and for push.

---

## Control State Bundle

The source of truth for any active program is the control state bundle. For this project, it consists of fixed-name artifacts at the repo root:

| Artifact | Purpose |
|----------|---------|
| **AGENTS.md** | Stable operating rules (this file). Not a live status board. |
| **PLAN.md** | Living build plan. Milestones, acceptance criteria, current phase, what's next. |
| **BUILDLOG.md** | Living decision log. Records decisions, alternatives considered, reasoning, and per-slice acceptance metrics. |
| **ARCHITECTURE.md** | Component structure, data flow, key technical decisions and rationale. |
| **README.md** | Project overview, setup instructions, tech stack. The public-facing repo interface. |

If the control lane becomes heavy, restart it from the current control state bundle. Do not confuse "one authoritative chat" with "one authoritative state."

---

## Bootstrapping Protocol

The Standard Flow assumes a working project with tests to run and artifacts to reference. The first slice of a new project is special -- there is no existing codebase, no test suite, no control state bundle.

**Slice zero** creates the foundation:

1. Initialize the project (framework, dependencies, configuration)
2. Create the control state bundle: AGENTS.md, PLAN.md, BUILDLOG.md, README.md
3. Set up CI pipeline (even if minimal: lint + type-check + build)
4. Establish the first BUILDLOG.md entry documenting the bootstrap decisions
5. ARCHITECTURE.md may be deferred until there is enough structure to document

Slice zero follows a lighter validation standard -- there may be no tests to run yet, and the "regression suite" is the build itself. Once the scaffold exists, all subsequent slices follow the full Standard Flow.

---

## Standard Flow

1. **Signal intake** -- External feedback, bugs, internal concerns, audits, or strategic ideas are gathered.
2. **Validation** -- Check what is true, partially true, false, missing proof, or still open against repo reality.
3. **Backlog shaping** -- Turn validated reality into backlog items or explicit deferrals.
4. **Slice decomposition** -- Break one backlog item into a compact set of delivery slices.
5. **Single-slice execution** -- One execution chat handles one slice only. Tests for new behavior are part of the slice deliverable, not a separate step.
6. **Review and correction** -- Returned work is reviewed in the control lane. If it is wrong or incomplete, issue a narrow correction pass.
7. **Quality gate** -- All findings surfaced to human. Explicit go/no-go before advancing.
8. **Workspace acceptance / accumulation** -- Accepted slices remain workspace-only until the control lane declares a coherent release unit. Do not assume one accepted slice equals one commit.
9. **Release-unit audit** -- Before local commit creation, run or request a dedicated read-only deep quality audit over the complete proposed release unit unless Ryan explicitly waives it. The audit is separate from the implementation lane and must be findings-first.
10. **Full regression check** -- Run the complete validation suite (`ruff check`, `ruff format --check`, `mypy --strict`, `pytest`) to catch regressions across the codebase. This is not where tests are written -- they were written in step 5. This is where the full suite is run to confirm nothing else broke.
11. **Release sequencing** -- Distinguish:
   - Accepted in workspace
   - Audit-cleared
   - Commit-ready
   - Committed locally
   - Pushed to remote
12. **Continuity sync** -- Update PLAN.md and BUILDLOG.md so future chats route correctly.
13. **Advance to next lane** -- Only after acceptance, quality gate, and continuity sync. The control lane proactively chooses the next authorized move rather than waiting to be asked.

---

## Slice Specifications

Slices are executed sequentially -- one at a time. Parallel execution slices are not permitted. This ensures clean review, predictable state, and simple continuity.

Every execution prompt must include a slice spec. There are two types.

### Implementation Slice Spec

For slices that produce code, configuration, or content artifacts:

- **Objective** -- What this slice delivers
- **Why now** -- Why this slice is sequenced here
- **In-scope files or areas** -- Exactly what can be touched
- **Explicit non-goals** -- What this slice must NOT do
- **Explicit blind spots** -- Systems, files, or context intentionally withheld to protect worker focus. Example: "This slice builds the scoring engine. The execution chat does not need to know about the MCP server, the eval harness, or the deployment pipeline. Do not reference or modify those areas."
- **Architectural or policy constraints** -- Rules the execution must follow
- **What must not be reopened** -- Previously accepted work that is off-limits
- **What later slices will handle** -- Work intentionally reserved for future slices
- **Whether schema / types / tests / docs are in or out of scope**
- **Exact validation commands** -- What to run to verify the work
- **Expected pass condition** -- What the output of validation should look like
- **Definition of done** -- The exact condition under which this slice is complete

### Spike / Research Slice Spec

For slices that produce a decision, finding, or recommendation (not working code):

- **Question to answer** -- What this spike is trying to determine
- **Why now** -- Why this question needs answering before proceeding
- **Scope of investigation** -- What to look at, where to search
- **Explicit non-goals** -- What NOT to investigate or decide
- **Time/effort bound** -- How much effort is justified before escalating
- **Definition of done** -- A clear finding, recommendation, or decision. Not working code.
- **Expected output format** -- Summary of findings, recommendation, evidence supporting the recommendation

The key distinction: a spike's definition of done is a **decision or finding**. An implementation slice's definition of done is **working, tested code**.

---

## Architecture Awareness

For any non-trivial change, the responsible lane must explicitly consider impact across this project's layers:

- **Symbol graph** -- tree-sitter parsing, node types, relationship edges
- **View renderers** -- 5-tier representation hierarchy
- **Scoring engine** -- p_edit, p_support, feature extraction
- **Budget optimizer** -- greedy with dependency closure
- **Compiler contracts** -- compile, diagnose, recompile
- **MCP server** -- tool definitions, protocol compliance
- **Eval harness** -- external eval methodology, baselines, metrics, and
  evidence boundaries
- **Observability** -- compile traces, warnings, diagnostics

This does not mean every slice changes every layer. It means every slice checks whether those layers are affected before claiming completeness.

---

## Evidence Discipline

Bounded execution slices remain the default repair discipline. They keep
implementation reviewable and reduce accidental regressions. They are not the
company scoreboard: company-level progress is judged by real-repo capability
and externally credible evidence, not by micro-slice throughput.

Decisive north-star or company evidence must not reuse self-authored synthetic
fixtures, oracle probe matrices, or Context IR analyzer-derived oracles as the
deciding proof. Those artifacts are useful for engineering regression, fixture
coverage, and internal debugging, but they do not establish external market or
thesis credibility by themselves.

Real-OSS thesis experiments must be pre-registered before execution. They must
use independent repo/PR-derived oracle facts, fair lexical/BM25 and embedding
baselines at equal token budgets, wasted-token and edit-relevant recall metrics,
and a written kill/reevaluate criterion before results are known.

---

## Execution Chat Protocol

Execution chats operate with explicit completion states:

- **DONE** -- Slice completed per spec
- **BLOCKED** -- Cannot proceed without information or access the execution chat doesn't have
- **ESCALATE** -- Issue found that exceeds slice scope; requires control lane decision
- **NEEDS-CONTROL** -- Ambiguity in the spec that needs clarification before proceeding

Every execution lane returns a consistent result shape:

- Completion state
- Summary of what changed
- Files changed
- Validation commands run and results
- Known risks or gaps
- Recommended next control action

Execution chats must not:

- Broaden into adjacent backlog items
- Decide release sequencing
- Write their own follow-on roadmap as if it were authoritative
- Silently reinterpret accepted policy
- Dump full rewritten files for minor edits when targeted changes would make review clearer

If a blocker would force scope expansion, the execution chat must stop and report it.

---

## Review Standard

Returned work is reviewed with a findings-first mindset: actively look for problems before confirming success. The default assumption is that issues exist until proven otherwise.

Review priorities for this project:

1. **Correctness** -- Does the code do what the spec says?
2. **Type safety** -- mypy strict compliance, zero `Any` types
3. **Test coverage** -- Are new behaviors covered by tests? Do existing tests still pass?
4. **Compile trace fidelity** -- Are diagnostics accurate? Do warnings fire when they should?
5. **Eval methodology rigor** -- Are measurements fair, reproducible, and correctly attributed?
6. **Performance** -- Compilation speed matters for developer experience
7. **Documentation** -- Docstrings on public functions/classes, ARCHITECTURE.md kept current

An acceptance decision is always explicit:

- **Accepted** -- Work meets all criteria
- **Rejected with findings** -- Specific issues listed, correction prompt issued
- **Held for human review** -- Issues found, summarized for Ryan, awaiting go/no-go

---

## Release-Unit Audit

A release-unit audit is the default pre-commit quality gate for non-trivial
code, test, eval, architecture, claim, or workflow changes.

Purpose:

- prevent the control lane from turning every accepted slice into an automatic
  commit
- preserve a deeper independent review pass over the full accumulated release
  unit
- verify that accepted slices still compose correctly when reviewed together
- catch scope creep, stale continuity, release-state ambiguity, claim drift,
  and boundary violations before commit

Rules:

- The audit is read-only. It must not edit files, stage changes, commit, push,
  or rewrite continuity.
- The audit must be findings-first and review the complete proposed release
  unit, not just the last slice.
- The audit prompt must state the repo-backed release truth, workspace-only
  accepted state, files included in the proposed release unit, files excluded
  from it, active holds, validation already run, and governing artifacts.
- The audit must check the proposed release unit against `AGENTS.md`,
  `PLAN.md`, `BUILDLOG.md`, `ARCHITECTURE.md`, `EVAL.md`,
  `PUBLIC_CLAIMS.md`, and `README.md` when those artifacts are relevant to the
  slice.
- If the audit finds any issue, the control lane must issue a correction prompt
  or hold for Ryan according to the normal quality gate. Do not silently accept
  "minor" audit findings.
- The audit may be skipped only with explicit Ryan waiver recorded in
  `BUILDLOG.md`, and the waiver must state why skipping the audit is acceptable
  for that release unit.

Release-unit audit clearance means the unit may proceed to full regression and
commit-gating review. It still does not imply push authorization.

---

## Release Discipline

**Branch strategy**: This is a solo project. All work happens on `main`. Push only after the full quality gate clears. There is no feature-branch overhead. Note: no auto-deploy; GitHub is the distribution surface.

For this project, the release pipeline is:

1. Complete one or more slices in the workspace
2. Review and correct each slice as needed under the quality gate
3. Declare the coherent release unit and explicitly separate included files
   from excluded continuity or unrelated workspace changes
4. Run or request the release-unit audit, unless Ryan explicitly waives it
5. Run full validation suite as a final gate-check: `ruff check src/ tests/`,
   `ruff format --check src/ tests/`, `mypy --strict src/`,
   `pytest tests/ -v`. Execution chats run validation during their slice and
   report results; the control lane may re-run at its discretion. This step is
   the final confirmation before commit/push, not a substitute for the
   release-unit audit.
6. Perform commit-gating review over the exact file set to be staged
7. Stage and commit with a meaningful commit message only after the release
   unit is audit-cleared, regression-cleared, and commit-gating-cleared
8. Push to remote only after explicit Ryan authorization
9. Update PLAN.md and BUILDLOG.md as a separate continuity sync step

**Post-push revert protocol**: If a pushed slice is discovered to be broken after push, immediately revert the commit and push the revert. Log the incident in BUILDLOG.md with root cause. The broken slice re-enters the workflow as a correction pass with a refined slice spec.

Do not collapse all release steps into one fuzzy "done" state.

---

## Code Quality Conventions

These are the project-specific code standards layered on top of the WoW process:

- **Python**: 3.11+, strict mypy, zero `Any` types, explicit return type annotations on all public functions
- **Data structures**: dataclasses for all data structures
- **Naming**: snake_case for functions/variables/modules, PascalCase for classes, UPPER_SNAKE for constants
- **Layout**: `src/context_ir/` package, one module per concern
- **Linting**: ruff for lint and format
- **Testing**: Every new behavior gets a test. pytest for all tests.
- **Commits**: Imperative mood, concise subject line, body explains why (not what). Example: `Add symbol graph parser with tree-sitter backend`
- **Docstrings**: All public functions and classes must have docstrings
- **No dead code**: Remove unused imports, variables, and functions before committing

---

## Continuity Rules

Continuity docs are not optional polish. They are the memory system.

**PLAN.md** must explicitly state:

- What is complete
- What is in progress
- What is next
- What is deferred
- What should not be reopened

**BUILDLOG.md** entries must include:

- Date
- What was decided or completed
- Acceptance status: `first-pass` | `N corrections` | `held` | `rejected`

For decision entries, also include:
- Alternatives considered
- Reasoning

For routine implementation entries (e.g., "add view renderer module"), the lighter format is sufficient -- date, what was completed, acceptance status. Do not manufacture reasoning for straightforward slices.

For any entry where risks were accepted, note the risk and that human sign-off was given.

If a continuity artifact is stale relative to repo reality, do not proceed blindly. Update from current repo state first.

### Non-Recursive Continuity

Committed continuity docs should record durable release anchors, accepted decisions, holds, and routing boundaries. They should not try to keep mutable live git facts perpetually current when those facts become stale immediately after the next continuity commit.

Live `HEAD`, `origin/main`, branch, and worktree state are verified from git by each control lane during intake, review, and release sequencing. They are not kept as always-current fields in `PLAN.md`, `BUILDLOG.md`, or other committed continuity docs.

Standalone docs-only continuity commits are allowed only for materially wrong routing, safety, or process defects, or with explicit Ryan authorization. They are not allowed merely to record that the previous docs-only continuity commit was pushed.

Prefer one canonical active release-state block for current routing. Historical
BUILDLOG entries may remain as history when a newer supersession entry clearly
overrides them. Do not rewrite every stale historical mention unless it can
actively misroute current work. This historical supersession guidance keeps
continuity updates from turning into write-amplification while preserving a
clear current route for fresh controllers.

Post-push continuity notes may be folded into the next process, continuity, or
substantive tranche unless stale committed routing would mislead a fresh
controller.

---

## Disposal Rule

If an execution chat fails to deliver the slice correctly after two correction prompts, terminate that chat.

Return to the control lane, refine the prompt or slice boundary, and start a fresh execution worker.

Do not sink cost into a failing chat.

---

## Fresh-Chat Reboot Rule

Restart the control lane when:

- A major phase or milestone closes
- The control chat becomes heavy or hard to reason about
- Continuity has materially changed
- You want to avoid degraded orchestration quality

The reboot input is the current control state bundle (AGENTS.md + PLAN.md + BUILDLOG.md + ARCHITECTURE.md), not a chat transcript.

---

## Slice Size Guidance

Execution slices should be small enough that:

- One chat can complete them without carrying major ambiguity
- Review can be performed against a short, concrete contract
- Correction passes are narrow rather than architectural

If a slice feels like "build the whole subsystem," it is too large.
If a slice is so small that coordination overhead dominates, it is too small.

Heuristics:

- Spikes should stay tightly bounded -- answer one question, return one finding
- Implementation slices should usually be a focused unit of architecture, behavior, or proof
- Architecture-sensitive work should start with schema/contract/boundary slices before implementation work

---

## What Good Looks Like

- Smaller but sharper prompts
- Explicit scope boundaries
- Fewer accidental regressions
- Less context-window fragility
- Better review quality
- Cleaner release sequencing
- Durable continuity that survives new chats
- First-pass acceptance rate trending upward
- Correction loops per slice trending downward
- Zero "good enough" acceptances

The process may feel slower at the front, but it reduces rework. That is intentional.

---

## Default Rule

Unless there is a strong reason not to, this is the default way of doing all AI-assisted work in this repository.
