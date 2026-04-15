# ARCHITECTURE.md -- Context IR

## Status

Semantic-first re-baselining. This document is the current architectural authority.

The April 13 frozen spec is retired and superseded. Existing runtime modules under `src/context_ir/` still largely reflect the retired symbol-graph-first build and must be treated as implementation history until they are replaced slice by slice.

## System Goal

Context IR is a semantically grounded Python context compiler for coding agents. The system should compile the smallest trustworthy working set for the next decision by:

1. analyzing a supported static Python subset into a `SemanticProgram`
2. deriving proved dependencies plus an explicit unknown frontier
3. applying ranking and budget optimization on top of that semantic substrate
4. compiling context artifacts that surface both evidence and uncertainty

## Public Low-Level Contract

`analyze_repository(repo_root) -> SemanticProgram`

This is the public low-level contract that higher layers build on. Ranking, optimization, compilation, and any future MCP surface must not claim stronger semantic knowledge than this API can actually prove.

`SemanticProgram` is the durable semantic product of repository analysis. At minimum it must carry:

- source inventory for the supported Python files under analysis
- syntax facts needed for semantic interpretation
- stable symbol identities and source spans
- scope and binding information
- resolved references and object-level facts within the supported subset
- semantic dependency edges with proof source or derivation reason
- explicit unknown or unsupported findings when proof is unavailable
- enough normalized structure for downstream rendering, ranking, optimization, and diagnostics

## Supported Static Subset

The first rebaseline targets a narrow, explicit Python subset. The analyzer is allowed to prove facts only inside this subset.

### In Scope First

- repository Python modules and files
- module imports that can be resolved statically inside the repository
- module-level bindings and constants
- function, async function, class, and method definitions
- lexical scopes at module, class, and function level
- name binding and reference resolution that can be proven from syntax plus supported imports
- class decorator support for `@dataclass` only, interpreted narrowly and explicitly

### `@dataclass` Scope

The first supported decorator set includes `@dataclass` only.

- Supported when the decorator resolves to `dataclasses.dataclass`
- Supported only as a class-level fact, not as a general decorator framework
- Intended initial semantic effect: record dataclass field facts derived from annotated class attributes and treat generated constructor-like behavior as supported only to the extent it is explicitly modeled
- Aliases, wrapper decorators, and mixed decorator stacks are unknown unless later slices add proof rules

### Unknown Without Proof

When a fact cannot be proven statically inside the supported subset, the system must mark it as unknown or unsupported instead of guessing. Examples include:

- dynamic imports and reflective module loading
- `exec`, `eval`, monkey patching, and runtime code generation
- decorators other than the explicitly supported set
- metaclass behavior, runtime attribute injection, and dynamic `__getattr__` patterns
- star imports or alias chains that cannot be resolved with proof
- semantic dependency claims inferred only from ranking heuristics

Unknown handling is part of the architecture, not a temporary omission.

## Mandatory Component Model

The architecture is built in this order. Higher layers depend on lower layers being truthful.

### 1. Syntax Extraction

Responsibility:
- read Python source files
- produce syntax facts and spans for supported constructs
- preserve enough structure for later semantic analysis without inventing meaning

Output:
- syntax-oriented repository facts that feed `SemanticProgram`

### 2. Semantic Analysis

Semantic analysis is mandatory. The retired symbol graph is not an acceptable substitute.

#### Binder and Scope Model

Responsibility:
- establish module, class, and function scopes
- assign bindings for definitions and imports
- represent visibility and shadowing rules that can be proven in the supported subset

Output:
- scope graph or equivalent binding model inside `SemanticProgram`

#### Resolver and Object Model

Responsibility:
- resolve references against the binder output
- attach object-level meaning to supported symbols
- track imports, aliases, dataclass facts, and other explicitly modeled constructs

Output:
- resolved references, symbol identities, and object facts inside `SemanticProgram`

### 3. Dependency and Frontier Derivation

Responsibility:
- derive semantic dependency edges from resolved program facts
- distinguish proved dependencies from unresolved frontier uncertainty
- expose where the analyzer ran out of proof

Policy:
- dependency claims must come from syntax plus semantic analysis
- ranking heuristics may prioritize selection but may not fabricate semantic dependency claims

Output:
- semantic dependency graph
- frontier or unknown set for unresolved but relevant areas

### 4. Rendering / Representation Policy

Responsibility:
- define how semantic units can be represented at different densities
- preserve provenance from `SemanticProgram`
- expose uncertainty clearly when representation depends on incomplete proof

Current authority:
- multi-tier representation remains in scope
- the exact tier count and semantics are not frozen during the rebaseline
- the prior 5-tier scheme is historical only and not current authority

### 5. Ranking

Responsibility:
- prioritize which proved units and frontier items matter most for a task
- combine task signals with semantic structure, not replace it

Policy:
- `p_edit` and `p_support` may remain as internal ranking policy
- they are not the public thesis of the project
- they can rank among proved candidates and frontier items, but they cannot create semantic facts

### 6. Optimization

Responsibility:
- choose a budget-feasible set of rendered units
- reason about tradeoffs, coverage, and downgrade decisions
- respect semantic dependency requirements and uncertainty surfacing

Output:
- optimized selection plan with traceable reasons

### 7. Compilation

Responsibility:
- assemble selected rendered units into a context artifact
- include trace, warnings, and uncertainty signals derived from the semantic layer
- avoid overclaiming completeness when frontier uncertainty remains

Policy:
- compile behavior is downstream of `SemanticProgram`
- no compile contract is authoritative unless it matches the semantic substrate beneath it

### 8. Diagnose / Recompile

Responsibility:
- interpret miss evidence against the compiled artifact and semantic trace
- identify which misses came from unsupported proof, missing frontier expansion, or ranking/optimization choices
- rebuild context without pretending the original semantic analysis knew more than it did

Current authority:
- diagnose and `recompile` are required architectural layers
- the public `recompile` contract is not frozen yet
- the old `recompile` hold is now part of the historical evidence trail, not the main control problem

## Planned Boundaries

Exact file names may change during the rebaseline, but the logical boundaries are:

- semantic contracts and shared dataclasses
- syntax extraction
- binder and scope model
- resolver and object model
- semantic dependency/frontier derivation
- rendering policy
- ranking policy
- optimization
- compilation
- diagnose/recompile

## Retired Non-Authoritative Descriptions

These ideas remain historical only and must not be treated as current authority:

- the old symbol-graph-first pipeline as the core architectural substrate
- the exact 5-tier renderer semantics as if already frozen
- heuristic graph propagation as a substitute for semantic dependency proof
- framing `p_edit` / `p_support` as the public thesis of the project
- treating the prior `recompile` contract dispute as the main gating issue ahead of semantic re-baselining
