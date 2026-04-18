# Context IR Case Study

## What This Case Is

This document is a derivative reviewer-facing case study built from the
accepted outward-facing doc stack in this repository. It is meant to give a
technical reviewer one concrete way to inspect the current semantic-first
thesis without turning one internal example into a broader claim surface.
[PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md) remains the sole claim source. This file
does not add claims, widen scope, or replace the evidence and qualifiers
already recorded elsewhere.

## Representative Case

The representative case is `oracle_signal_smoke_d`. Within the current docs, it
is the accepted illustrative case because it broadens the surface in the
method/class/dataclass direction rather than repeating a function-only shape.
For a reviewer, that matters because the case is not just about finding a
nearby top-level definition. It asks the current system to work across methods,
class structure, inherited relationships, and the repo's narrow accepted
`@dataclass` handling when it resolves to `dataclasses.dataclass`.

That makes `oracle_signal_smoke_d` a better walkthrough than a simpler example
for showing what the current supported static Python subset is actually trying
to prove. It remains one illustrative case inside the accepted internal quad
matrix, not a new proof surface on its own.

## Why This Case Matters

The technical thesis in this repo is semantic-first context compilation. In the
current implementation and evidence boundary, that means analyzing a supported
static Python subset into a `SemanticProgram`, deriving proven dependencies,
and keeping unresolved or unsupported frontier explicit instead of silently
flattening uncertainty into file proximity.

`oracle_signal_smoke_d` is useful because it makes that thesis inspectable on a
shape where class and method structure matters. A reviewer can look at this
case and ask a concrete question: does the system recover the units that are
semantically relevant to the requested change when the shape depends on method
ownership, class relationships, and narrow dataclass facts? That is a more
meaningful check of the repo's current direction than another example that can
be explained mostly by lexical closeness.

## What It Demonstrates

On this case, a reviewer should notice that the current system is trying to
select context from proven structure first. The important behavior is not that
every possible support unit is always recovered under every budget. The
important behavior is that the case is shaped so semantic signals around
methods, classes, and narrow dataclass structure are doing real work in the
selection process.

This is also the place where limited comparative wording can be useful, but
only in its accepted frame. `oracle_signal_smoke_d` sits inside the accepted
internal quad matrix, so it can be read as one row inside that matrix-only
comparison surface. The point is still subordinate to the main technical
reading of the case: this example helps show what semantic-first behavior looks
like when the edit surface is more structurally demanding than a simple
function-level task.

## Evidence Scope And Boundaries

The evidence behind this case is deterministic internal evidence only. It comes
from the repo's accepted docs, tests, quality gates, and internal eval harness.
This document should be read as one reviewer-facing walkthrough derived from
that accepted material, not as a general benchmark or product claim.

`oracle_signal_smoke_d` is one illustrative internal case. It is useful
because it broadens the accepted evidence surface in a method/class/dataclass
direction, but it does not by itself establish broader Python support, broader
product scope, or any external standing. Any comparison language remains
explicitly limited to the accepted internal quad matrix and should not be
generalized beyond that fixed internal surface.

## Current Limitation

This case study does not change the current accepted limitation. The evidence
surface is still not uniformly clean: `oracle_signal_smoke_b / 200` records
`budget_pressure`, and
`def:pkg/digest.py:pkg.digest.render_assignment_digest` can remain omitted
under that tight budget. That limitation matters here because the portfolio
material is meant to stay honest about the current state of the repo rather
than presenting only the strongest illustrative row.

In other words, `oracle_signal_smoke_d` is the representative case because it
shows the intended semantic surface clearly, but it should be read alongside
the accepted limitation rather than as a way to blur it.

## Repo Anchors

- [PUBLIC_CLAIMS.md](PUBLIC_CLAIMS.md) defines the claim boundary and remains
  the sole claim source.
- [PORTFOLIO_SOURCE_BRIEF.md](PORTFOLIO_SOURCE_BRIEF.md) captures the
  derivative portfolio-source rules for later outward-facing docs.
- [PORTFOLIO_TECHNICAL_BRIEF.md](PORTFOLIO_TECHNICAL_BRIEF.md) summarizes the
  current technical surface and evidence state.
- [PORTFOLIO_OVERVIEW.md](PORTFOLIO_OVERVIEW.md) gives the short reviewer
  orientation and reading path.
- [PORTFOLIO_CASE_STUDY_SOURCE.md](PORTFOLIO_CASE_STUDY_SOURCE.md) is the
  direct source layer for this case study.
- [EVAL.md](EVAL.md), [README.md](README.md), [PLAN.md](PLAN.md), and
  [BUILDLOG.md](BUILDLOG.md) anchor the accepted evidence surface, supported
  interface, current phase, and review history behind this derivative document.
