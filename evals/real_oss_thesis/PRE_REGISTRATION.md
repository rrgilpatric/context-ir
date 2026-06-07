# Real OSS Thesis Experiment Pre-Registration

## Status

This document is a pre-registration artifact, not a results report. It freezes
the intended experiment design before provider outputs are generated, scored,
or interpreted.

This experiment is internal thesis evidence only. It is not a public benchmark
claim, leaderboard claim, or product claim. Public claims remain blocked until
results are run, independently audited, and claim-gated.

## Experiment Identity

- Experiment version: `real_oss_thesis_v1`
- Pre-registration date: 2026-06-07
- Selection seed: `20260607`
- Task manifest status: not yet generated
- Results status: not yet run

Any Context IR tuning, analyzer change, provider-implementation change, or
metric change after the task manifest is frozen creates a new experiment
version and must not be mixed with this version's results.

## Candidate Repositories

The candidate repository list is frozen for this experiment version:

- `pallets/flask`
- `encode/httpx`
- `psf/black`
- `scrapy/scrapy`
- `python-poetry/poetry`

Repository substitutions, additions, or removals require a new experiment
version or explicit control-lane approval before implementation.

## Task Plan

The task set is frozen as:

- 10 eligible merged PRs per repository
- 50 tasks total
- PRs selected before any provider runs
- Selection performed with fixed seed `20260607`
- Sampling without replacement within each repository

Selection procedure:

1. Enumerate eligible merged PRs for each frozen repository.
2. Sort the eligible candidate pool by PR number ascending.
3. Use the fixed seed to sample 10 PRs without replacement per repository.
4. Write the selected PR IDs and git-fact oracle fields to a task manifest
   before running any provider.
5. Do not replace tasks after provider outputs are known. If a task is later
   found invalid under the pre-registered skip rules, mark it invalid and
   report the remaining valid count.

## Eligibility Rules

A PR is eligible only if all of the following are true:

- The PR is merged into the default branch of one frozen repository.
- The PR has a resolvable PR number, base SHA, merge or head SHA, title, and
  body metadata.
- The base SHA and merge/head SHA can be checked out and diffed.
- The PR changes at least one tracked `.py` file.
- The PR has at least one base-side changed line range in an existing `.py`
  file. Added-only Python PRs are excluded because there is no base-side
  retrieval target.
- The PR is small enough for human oracle review to confirm changed paths and
  base-side ranges without ambiguous bulk rewrites.
- The PR is not already part of any Context IR fixture, task, run spec, or
  analyzer-derived oracle.

## Exclusion And Skip Rules

Exclude a PR before selection if any of the following are known during
candidate enumeration:

- It is unmerged, reverted before merge, closed without merge, or unavailable.
- It is primarily vendored code, generated code, lockfile-only work, formatting
  churn, repository-wide mechanical rewriting, or bulk renaming.
- It changes no `.py` files.
- It only adds new `.py` files and has no base-side changed line ranges.
- Its base or merge/head SHA cannot be resolved.
- Its metadata cannot be collected without using diffs, review comments,
  changed file lists, Context IR output, or analyzer-derived selectors.
- Its oracle would require semantic judgment beyond git facts and bounded
  human ambiguity review.

Skip a selected task after manifest freeze only if a pre-registered validity
condition fails during implementation or scoring:

- Repository checkout fails for reasons unrelated to a provider.
- Required git facts are missing or contradictory.
- The query text source is unavailable.
- Oracle ambiguity review marks the task ambiguous.
- The provider infrastructure fails in a way that prevents all providers from
  being compared fairly on that task.

Skipped tasks must be reported with the reason. They must not be replaced after
provider outputs are available.

## Query Construction

Queries must be constructed from PR and issue text only:

- PR title
- PR body
- Linked issue title and body when the issue is explicitly referenced by the PR
  metadata or PR body before provider runs

The query must exclude:

- PR diffs
- Review comments
- Inline code review threads
- Changed file lists
- Commit file lists
- Patch hunks
- Base-side or head-side line ranges
- Context IR output
- Context IR analyzer IDs
- Analyzer-resolved symbol names or selectors
- Any oracle fields

Query normalization must be deterministic and frozen before provider outputs:

- Preserve natural-language text and inline code already present in the
  allowed PR or issue text.
- Remove Markdown boilerplate only if the rule is applied uniformly to all
  tasks.
- Do not append repository path hints, changed symbols, or manually curated
  retrieval hints.
- Record query leakage flags before scoring.

Leakage flags must be logged before scoring, including at minimum:

- Explicit file path in allowed PR/issue text
- Explicit function, class, method, or module name in allowed PR/issue text
- Stack trace in allowed PR/issue text
- Direct line number in allowed PR/issue text
- Patch-like code block in allowed PR/issue text

Severe query leakage is a methodology reevaluation trigger, not a reason to
silently edit or replace selected tasks after provider outputs are known.

## Git-Fact Oracle

The oracle must be constructed from git facts only. The required oracle fields
for each task are:

- Repository URL
- PR number
- Base SHA
- Merge/head SHA
- Changed `.py` paths
- Base-side changed line ranges for changed `.py` paths

Base-side changed line ranges are derived from git diff metadata between the
base SHA and merge/head SHA, using zero-context diff hunks for `.py` files.
For modified or deleted existing Python files, record the base-side old-file
line ranges. For renamed Python files, record the base-side path and line
ranges when git can resolve the rename unambiguously; otherwise mark the task
ambiguous.

Context IR analyzer IDs are explicitly forbidden in oracle construction.
Analyzer-resolved oracle selectors, symbol IDs, node IDs, relationship IDs,
view IDs, or Context IR-derived path/range selectors must not be used to build,
filter, repair, or validate the oracle.

Human oracle review is allowed only to classify ambiguity against the frozen
git facts. It must not add semantic targets, expected symbols, analyzer IDs, or
provider-aware judgments.

## Providers

The providers for this experiment version are frozen as:

- `context_ir_static`
- `bm25_chunks`
- `embedding_chunks`

All providers must run against the same selected tasks, same query text, same
repository base state, and same token budgets.

### context_ir_static

`context_ir_static` is the Context IR static retrieval provider evaluated for
this experiment. It may use Context IR's normal static analysis and scoring
pipeline to select context, but it must not influence task selection, query
construction, oracle construction, baseline chunking, skip rules, or metric
formulas.

### bm25_chunks

`bm25_chunks` is a lexical baseline over analyzer-independent repository
chunks. Frozen BM25 parameters for v1:

- Tokenization: lowercase Unicode word tokens matched by `\w+`
- Stopword removal: none
- Stemming: none
- `k1`: 1.2
- `b`: 0.75
- Ranking unit: independent text chunk

### embedding_chunks

`embedding_chunks` is an embedding baseline over the same
analyzer-independent repository chunks used by `bm25_chunks`.

The embedding model must be frozen before provider outputs are generated.
Embedding model choice may require separate Ryan approval if it adds
network/API cost. If that approval is required and not granted, implementation
must hold rather than substitute a model after seeing outputs.

## Baseline Chunking

Baseline chunks must be independent of Context IR analyzer output.

Baseline chunking rules for `bm25_chunks` and `embedding_chunks`:

- Input files: tracked `.py` files at the task base SHA.
- Exclusions: generated, vendored, build, virtualenv, and cache directories
  according to frozen path rules.
- Chunking source: raw file text only.
- Chunk size target: 160 non-overlap content lines.
- Chunk overlap: 40 lines.
- Chunk identity: repository path plus start and end line numbers.
- Chunk ordering tie-breaker: score descending, then path ascending, then
  start line ascending.
- No tree-sitter nodes, Context IR symbols, Context IR views, analyzer
  relationship edges, or analyzer-selected boundaries may be used.

The same baseline chunks must be used for BM25 and embedding retrieval.

## Token Budgets

The frozen token budgets are:

- 2000 tokens
- 4000 tokens
- 8000 tokens

Token accounting tokenizer for v1 is frozen as `cl100k_base`. The exact
implementation package and version must be recorded in the later run manifest
before provider outputs are generated.

Providers may return less than the budget when no more candidate context is
available. Providers must not exceed the budget.

## Metrics

Primary metrics are computed per task, provider, and budget:

- `edit_relevant_recall@budget`
- `wasted_tokens@budget`
- `waste_rate@budget`
- `recall AUC across budgets`

Definitions:

- `edit_relevant_recall@budget` is the fraction of oracle base-side changed
  line units covered by selected context within the token budget.
- `wasted_tokens@budget` is the number of selected context tokens that do not
  overlap oracle base-side changed line units.
- `waste_rate@budget` is `wasted_tokens@budget / selected_tokens@budget`.
  If `selected_tokens@budget` is zero, waste rate is undefined and the task is
  invalid for that provider/budget comparison.
- `recall AUC across budgets` is the normalized trapezoidal area under recall
  over log2 token budgets 2000, 4000, and 8000. Because the budgets are evenly
  spaced in log2 space, per-task recall AUC is:
  `(recall@2000 + 2 * recall@4000 + recall@8000) / 4`.

Secondary diagnostics may be reported, but they must not replace or redefine
the primary metrics after results are known.

## Aggregation

Aggregation is paired per task. For each valid task, compare
`context_ir_static` against the best baseline result among `bm25_chunks` and
`embedding_chunks` for the same task and metric.

Report at minimum:

- Mean per-provider metric values
- Median per-provider metric values
- Mean paired deltas
- Median paired deltas
- Bootstrap confidence intervals over paired per-task deltas

Bootstrap confidence intervals:

- Resampling unit: task
- Pairing: preserved within each resampled task
- Resamples: 10,000
- Confidence interval: percentile 95%
- Bootstrap seed: `20260607`

For the kill criterion, "statistically tied" means the 95% bootstrap confidence
interval for the paired recall-AUC delta between `context_ir_static` and the
best baseline includes 0.

## Kill And Reevaluate Criteria

The kill/material reevaluation criteria are frozen exactly as follows:

- kill/materially reevaluate if Context IR does not beat the best of BM25/embedding by at least +0.05 median recall-AUC, or if recall is statistically tied while waste rate is worse by >= 0.10
- reevaluate methodology if fewer than 35 valid tasks remain, oracle ambiguity exceeds 15%, query leakage is severe, or Context IR infrastructure failures exceed 20%

These criteria must be interpreted before any public claim language is drafted.

## Anti-Circularity Rules

This experiment must not use any of the following to select tasks, construct
queries, construct oracles, define baselines, or score results:

- `evals/fixtures`
- `evals/tasks`
- `evals/run_specs`
- `eval_oracles`
- `EvalRunMetrics.aggregate_score`
- analyzer-resolved oracle selectors

Additional anti-circularity requirements:

- Do not use self-authored synthetic fixtures as decisive thesis evidence.
- Do not use Context IR analyzer IDs in oracle construction.
- Freeze repos, PR IDs, budgets, tokenizer, chunking, BM25 params, embedding
  model, metric formulas, and skip rules before provider outputs.
- Log query leakage flags before scoring.
- Context IR tuning after manifest freeze creates a new experiment version.
- Do not inspect provider outputs to decide whether a task remains in the
  scored set, except under the frozen skip rules.
- Do not use Context IR output to repair baseline chunks, query text, oracle
  fields, or ambiguity decisions.

## Explicit Holds

Implementation is blocked on these holds:

- Ryan must accept repo list and kill criterion before implementation.
- Embedding model choice may require separate approval if it adds
  network/API cost.
- Public claims remain blocked until results are run, audited, and
  claim-gated.

## Definition Of Done For This Artifact

This pre-registration artifact is complete when it clearly records an
anti-circular, pre-result experiment design suitable for later control review.
It does not authorize implementation, provider runs, public claims, staging,
commit, or push.
