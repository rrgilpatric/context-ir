# ARCHITECTURE.md -- Context IR

## Status

Semantic-first re-baselining with narrow internal runtime-backed evidence. This
document is the current architectural authority.

The accepted semantic-first / deterministic-evidence / reviewer-stack milestone
is the completed phase 0 foundation. It remains the public architectural
authority for current claims, regression anchors, and reviewer-facing surfaces.

Post-phase-0 internal slices have added capability-tier accounting and narrow
runtime-backed eval evidence, including the `DYNAMIC_IMPORT` provider/budget
matrix, the current root-module `importlib.import_module(name)`, root-module
literal `importlib.import_module("plugins.weather")`, builtin
`__import__(name)`, builtins-attribute `builtins.__import__(name)`,
and builtins-alias `loader.__import__(name)`,
imported-name `import_module(name)`, and imported-alias
`load_module(name)` sibling pilots, plus the current root-module alias
`loader.import_module(name)` sibling pilot, and
`REFLECTIVE_BUILTIN` pilots for `hasattr(obj, name)` and
`getattr(obj, name)`, plus narrow direct-literal
`getattr(obj, "bit_length")` and `hasattr(obj, "bit_length")` surfaces whose
matrices remain internal evidence and whose exact replay identities now have
default local runtime probe acquisition, plus a narrow direct-literal
`setattr(obj, "flag", value)` runtime-mutation surface whose matrix remains
internal evidence and whose exact replay identity now has default local
runtime probe acquisition, plus a narrow direct-literal `delattr(obj, "flag")`
surface whose matrix remains internal evidence and whose exact replay identity
now has default local runtime probe acquisition. Narrow internal eval-only
pilots for `getattr(obj, name, default)`
additionally record default-return branch evidence and value-return sibling
evidence. The three existing getattr-family
provider/budget matrices each remain one existing task only: 1 task x 2 budgets
x 3 providers at budgets `100` and `220`.

The completed direct-literal runtime-acquisition quartet is a closed internal
replay contract, not a generalized acquisition family. The quartet is exactly
`hasattr(obj, "bit_length")`, `getattr(obj, "bit_length")`,
`delattr(obj, "flag")`, and `setattr(obj, "flag", value)`. Each identity
keeps its exact subject, span, family/form, replay target, replay selector, and
form-specific replay inputs. `hasattr` and `getattr` keep
`object_type=builtins.int` and `attribute_name=bit_length`; `delattr` keeps
`object_type=main.ProbeTarget` and `attribute_name=flag`; `setattr` keeps
`object_type=main.ProbeTarget`, `attribute_name=flag`,
`assigned_value_type=builtins.str`, and `assigned_value_literal=ready`, with
the assigned-value durable reference shape
`artifact://runtime-probe/setattr-value/{request_id}.json`. Normalized runtime
payloads remain exactly `attribute_present=true`,
`lookup_outcome=returned_value`, `mutation_outcome=deleted_attribute`, and
`mutation_outcome=returned_none`, respectively. `observed_replay_inputs`
remains reserved for exact `exec(source)` / `eval(source)` source proof and
stays empty for the quartet. Unsupported selector and selected-unit primary
truth remain `unsupported/opaque`; runtime provenance remains additive only.

The current `REFLECTIVE_BUILTIN` /
direct-literal `getattr(obj, "bit_length")` surface has two bounded parts:
the internal evidence matrix remains one task only through
`oracle_signal_getattr_literal_probe_matrix`: 1 task x 2 budgets x 3 providers
at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is exactly `getattr(obj, "bit_length")`; no name variable, default argument,
other reflective builtin, or generalized reflective-builtin behavior is
included. The runtime payload is `lookup_outcome=returned_value`; the exact
default acquisition path still does not carry returned value/type summary
fields. Primary selector and selected-unit truth remain `unsupported/opaque`;
runtime provenance remains additive only. The same exact replay identity is now
admitted by default local runtime probe acquisition. That acquisition is
limited to this single direct-literal replay identity; it does not generalize
literal `getattr`, all `getattr/2`, defaulted `getattr`, `getattr(obj, name)`,
or `hasattr` / `setattr` / `delattr`.
`context_ir` selects the edit symbol, digest support symbol, and unsupported
call boundary at both budgets. Baseline providers may select `main.py` at
budget `220`, but they select no semantic units and do not select the
unsupported/runtime evidence unit. No static attribute dependency edge,
selected `bit_length` symbol, selected `bit_length` unit, public API, MCP,
package export, schema, scoring, optimizer, compiler, winner-selection,
public/demo, benchmark, latency, production, or generalized reflective-builtin
widening is included. The current `REFLECTIVE_BUILTIN` /
direct-literal `hasattr(obj, "bit_length")` surface has two bounded parts:
the internal evidence matrix remains one task only through
`oracle_signal_hasattr_literal_probe_matrix`: 1 task x 2 budgets x 3 providers
at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is exactly `hasattr(obj, "bit_length")`; no name variable,
`hasattr(obj, name)`, other reflective builtin, or generalized
reflective-builtin behavior is included. The runtime payload is exactly
`attribute_present=true`. Unsupported selector and unsupported selected-unit
truth remain `unsupported/opaque`; runtime provenance remains additive only.
The same exact replay identity is now admitted by default local runtime probe
acquisition. That acquisition is limited to this single direct-literal replay
identity; it does not generalize literal `hasattr`, all `hasattr/2`,
`hasattr(obj, name)`, or `getattr` / `setattr` / `delattr`.
`context_ir` selects the edit symbol, digest support symbol, and unsupported
call boundary at both budgets. Baseline providers may select `main.py` at
budget `220`, but they select no semantic units and do not select the
unsupported/runtime evidence unit. No static attribute dependency edge,
selected `bit_length` symbol, selected `bit_length` unit, public API, MCP,
package export, schema, scoring, optimizer, compiler, winner-selection,
public/demo, benchmark, latency, production, or generalized
reflective-builtin widening is included. The current `RUNTIME_MUTATION` /
direct-literal `setattr(obj, "flag", value)` surface remains one task only through
`oracle_signal_setattr_literal_probe_matrix`: 1 task x 2 budgets x 3 providers
at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is exactly `setattr(obj, "flag", value)`; no name variable,
`setattr(obj, name, value)`, `delattr`, other runtime-mutation form, or
generalized runtime-mutation behavior is included. The runtime payload is
exactly `mutation_outcome=returned_none`. Unsupported selector and
selected-unit truth remain `unsupported/opaque`; runtime provenance remains
additive only. The same exact replay identity is now admitted by default local
runtime probe acquisition through `main.probe_set_literal_attribute` with
planned replay inputs `object_type=main.ProbeTarget`, `attribute_name=flag`,
`assigned_value_type=builtins.str`, and `assigned_value_literal=ready`; the
durable assigned-value reference keeps the
`artifact://runtime-probe/setattr-value/{request_id}.json` shape. `context_ir`
selects the unsupported call boundary at both budgets. Baseline providers may
select `main.py` at budget `220`, but they select no semantic units and do not
select the unsupported/runtime evidence unit. No static `flag` dependency
edge, selected `flag` symbol, selected attribute unit, runtime acquisition
widening beyond that exact replay identity, public API, MCP, package export,
schema, scoring, optimizer, compiler, winner-selection, or public benchmark
widening is included. The
narrow `RUNTIME_MUTATION` / direct-literal
`delattr(obj, "flag")` pilot remains one task only through
`oracle_signal_delattr_literal_probe_matrix`: 1 task x 2 budgets x 3 providers
at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`, and its exact replay
identity now also has default local runtime probe acquisition. The fixture
boundary is exactly `delattr(obj, "flag")`; no name variable,
`delattr(obj, name)`, `setattr`, other runtime-mutation form, or generalized
runtime-mutation behavior is included. The runtime payload is exactly
`mutation_outcome=deleted_attribute`, with replay input
`object_type=main.ProbeTarget` and `attribute_name=flag` only for the exact
`main.probe_delete_literal_attribute` identity. Unsupported selector and
selected-unit truth remain `unsupported/opaque`; runtime provenance remains
additive only.
`context_ir` selects the unsupported call boundary at both budgets. Baseline
providers may select `main.py` at budget `220`, but they select no semantic
units and do not select the unsupported/runtime evidence unit. No static
`flag` dependency edge, selected `flag` symbol, selected attribute unit,
runtime acquisition widening beyond that exact replay identity, public API,
MCP, package export, schema, scoring, optimizer, compiler, winner-selection,
or public benchmark widening is included. The current internal
eval-only `REFLECTIVE_BUILTIN` / `getattr(obj, name)` raised-`AttributeError`
branch pilot remains one task only through
`oracle_signal_getattr_attribute_error_probe_matrix`: 1 task x 2 budgets x 3
providers at budgets `220` and `100`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture, task,
query, and runtime payload remain unchanged across both budget rows. The
fixture boundary is exactly `getattr(obj, name)`, with `AttributeError` caught
so `render_probe_digest()` is deterministic. The runtime payload is
`lookup_outcome=raised_attribute_error`; primary selector and selected-unit
truth remain `unsupported/opaque`, runtime provenance remains additive only,
baseline providers remain empty at both budgets, no missing-attribute
dependency edge or selected symbol is created, and public comparative claims
remain bounded to the existing quad matrix. No
source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening is included.
The current internal eval-only `REFLECTIVE_BUILTIN` /
`hasattr(obj, name)` false-branch pilot remains one task only through
`oracle_signal_hasattr_false_probe_matrix`: 1 task x 2 budgets x 3 providers
at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture call
boundary is exactly `hasattr(obj, name)`, the runtime payload is exactly
`attribute_present=false`, and the deterministic fixture digest is
`hasattr_false:missing`. Selector and selected-unit primary truth remain
`unsupported/opaque`, runtime provenance is additive runtime provenance only, and
empty baselines remain empty at both budgets. This is a missing-attribute
no-edge/no-symbol/no-unit boundary: no missing-attribute dependency edge,
selected symbol, or selected unit is introduced. The no-widening boundary
preserves public comparative claims at the existing quad matrix and includes
no source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening.
The current internal
`REFLECTIVE_BUILTIN` / `vars(obj)` pilot remains one task only:
`oracle_signal_vars_probe`, 1 task x 2 budgets x 3 providers at budgets `100`
and `220`, against providers `context_ir`, `lexical_top_k_files`, and
`import_neighborhood_files`, with `lookup_outcome=returned_namespace`. The
current internal zero-argument `REFLECTIVE_BUILTIN` / `vars()` pilot remains one
task only through `oracle_signal_vars_zero_probe_matrix`: 1 task x 2 budgets x
3 providers at budgets `100` and `220`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`, with
`lookup_outcome=returned_namespace`; selector and selected-unit primary truth
remain `unsupported/opaque`, and runtime-backed provenance is additive only.
The current internal eval-only `REFLECTIVE_BUILTIN` / `vars(obj)`
raised-`TypeError` branch pilot remains one task only through
`oracle_signal_vars_type_error_probe_matrix`: 1 task x 2 budgets x 3 providers
at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is exactly `vars(obj)`, the runtime payload is exactly
`lookup_outcome=raised_type_error`, and the deterministic fixture digest is
`vars_type_error:raised_type_error`. Selector primary truth remains
`unsupported/opaque`, runtime provenance is additive runtime provenance only, and
empty baselines remain empty at both budgets. This is a failed-namespace
lookup no-edge/no-symbol/no-unit boundary: no namespace dependency edge,
selected symbol, or selected unit is introduced from the failed `vars()`
lookup, and the dependency guard uses `site:call:main.py:2:11`. The
no-widening boundary preserves public comparative claims at the existing quad
matrix and includes no
source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening.
The current internal eval-only `RUNTIME_MUTATION` / `globals()` pilot remains
one task only through `oracle_signal_globals_probe_matrix`: 1 task x 2 budgets x
3 providers at budgets `100` and `220`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`, with
`lookup_outcome=returned_namespace`; primary truth remains
`unsupported/opaque`, and runtime-backed provenance is additive only.
The current internal eval-only `RUNTIME_MUTATION` / `locals()` pilot remains
one task only through `oracle_signal_locals_probe_matrix`: 1 task x 2 budgets x
3 providers at budgets `100` and `220`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`, with
`lookup_outcome=returned_namespace`; selector and selected-unit primary truth
remain `unsupported/opaque`, and runtime-backed provenance is additive only.
The current internal eval-only `RUNTIME_MUTATION` / `delattr(obj, name)` pilot
remains one task only through `oracle_signal_delattr_probe_matrix`: 1 task x 2
budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
`mutation_outcome=deleted_attribute`; fixture, task, query, and runtime
payload remain unchanged across both budget rows; selector and selected-unit
primary truth remain `unsupported/opaque`; runtime provenance remains
additive only; baseline providers remain empty at both budgets; and public
comparative claims remain bounded to the existing quad matrix.
The current internal eval-only `RUNTIME_MUTATION` /
`setattr(obj, name, value)` evidence is narrow and remains one task only
through `oracle_signal_setattr_probe_matrix`: 1 task x 2 budgets x 3
providers at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
`mutation_outcome=returned_none`; fixture, task, query, and runtime payload
remain unchanged across both budget rows; selector/runtime-mutation surface
and selected-unit primary truth remain `unsupported/opaque`; runtime
provenance remains additive only; baseline providers remain empty at both
budgets; and public comparative claims remain bounded to the existing quad
matrix.
The current internal eval-only `REFLECTIVE_BUILTIN` / `dir(obj)` pilot remains
one task only through `oracle_signal_dir_probe_matrix`: 1 task x 2 budgets x 3
providers at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture, task,
query, and runtime payload remain unchanged across both budget rows; runtime
payload remains `listing_entry_count=74`. The runtime proof boundary is a
durable dir listing artifact via `durable_payload_reference`, and
`listing_entry_count` is additive summary only. Selector and selected-unit
primary truth remain `unsupported/opaque`, runtime-backed provenance is
additive only, baseline providers remain empty at both budgets, and public
comparative claims remain bounded to the existing quad matrix. No
source/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening is included.
The current internal eval-only `REFLECTIVE_BUILTIN` / zero-argument `dir()`
pilot remains one task only through `oracle_signal_dir_zero_probe_matrix`: 1
task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers
`context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`. Runtime
payload remains `listing_entry_count=0`; runtime proof remains via non-empty
`durable_payload_reference`; `listing_entry_count` is additive summary only.
Baseline providers remain empty at both budgets. At budgets `220` and `100`,
`context_ir` selects the same units:
`def:main.py:main.probe_directory`,
`def:main.py:main.render_probe_digest`, and
`unsupported:call:main.py:2:11`. Primary selector and selected-unit truth
remain `unsupported/opaque` where applicable, runtime provenance remains
additive only, no `dir()` output dependency edge or selected symbol is
introduced, and public comparative claims remain bounded to the existing quad
matrix. No
source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening is included.
The current internal eval-only `METACLASS_BEHAVIOR` pilot remains one task
only through `oracle_signal_metaclass_behavior_probe_matrix`: 1 task x 2
budgets x 3 providers at budgets `[220, 100]`, against providers
`context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`. Runtime
payload remains `class_creation_outcome=created_class`,
`created_class_qualified_name=main.Example`, and
`selected_metaclass_qualified_name=main.Meta`; `durable_payload_reference` is
required and non-empty, and the qualified-name fields are additive summary
only. Baseline providers remain empty at both budgets. At budget `220`,
`context_ir` selects `def:main.py:main.Example`, `def:main.py:main.Base`,
`unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1`, and
`frontier:base:main.py:5:11:def:main.py:main.Meta:1`. At budget `100`,
`context_ir` selects `def:main.py:main.Example`,
`unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1`, and
`frontier:base:main.py:5:11:def:main.py:main.Meta:1`, omitting
`def:main.py:main.Base`. Attachment is limited to the preserved full
`metaclass=...` keyword-site unsupported construct, selector and selected-unit
primary truth remain `unsupported/opaque` where applicable, runtime provenance
remains additive only, no selected `def:main.py:main.Meta` symbol, metaclass
dependency edge, or other selected symbol is introduced beyond the listed
units, and public comparative claims remain bounded to the existing quad
matrix. No
source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening is included.
The current internal eval-only `EXEC_OR_EVAL` / `eval(source)`
evidence is narrow and remains one task only through
`oracle_signal_eval_probe_matrix`: 1 task x 2 budgets x 3 providers at
budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The runtime
payload/proof boundary is
`evaluation_outcome=returned_value`, `source_shape=literal_expression`, valid
`source_sha256`, and non-empty `durable_payload_reference`; optional
`result_type=builtins.str` is additive summary only. Runtime provenance
attaches only to the preserved `EXEC_OR_EVAL` unsupported finding for
`eval(source)`. Primary selector and selected-unit truth remain
`unsupported/opaque`, additive runtime provenance remains separate from primary
truth, baseline providers remain empty at both budgets, and at both budgets
`context_ir` selects the same unsupported/opaque boundary unit with additive
runtime provenance. No generated-code dependency edge or selected symbol is
introduced, and public comparative claims remain bounded to the existing quad
matrix.
The current internal eval-only `EXEC_OR_EVAL` / `exec(source)`
evidence is narrow internal eval-only evidence and remains one task only
through `oracle_signal_exec_probe_matrix`: 1 task x 2 budgets x 3 providers at
budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture/call
boundary is `source = "pass"` and exactly `exec(source)`; the executed source
parses as exactly one `ast.Pass`. This evidence does not cover `exec("pass")`,
`exec(source + suffix)`, `exec(source=source)`, `exec(source, globals)`,
`exec(source, globals, locals)`, `builtins.exec`, or `eval`. The runtime
payload/proof boundary is `execution_outcome=completed`,
`source_shape=literal_statement`, valid `source_sha256` for exact `"pass"`,
and non-empty `durable_payload_reference`; optional `statement_kind=pass` is
additive summary only. Runtime provenance attaches only to the preserved
`EXEC_OR_EVAL` unsupported finding for `exec(source)`. Primary selector and
selected-unit truth remain `unsupported/opaque`, additive runtime provenance
remains separate from primary truth, baseline providers remain empty at both
budgets, and at both budgets `context_ir` selects the same
unsupported/opaque boundary unit with additive runtime provenance. No
generated-code dependency edge or selected symbol is introduced, no namespace
mutation modeling is added, and public comparative claims remain bounded to
the existing quad matrix.
The current internal eval-only `DYNAMIC_IMPORT` original provider/budget
evidence remains one task only through
`oracle_signal_dynamic_import_probe_matrix`: 1 task x 3 budgets x 3 providers
at budgets `[220, 180, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture, task,
query, and runtime payload remain unchanged; runtime payload remains
`imported_module=plugins.weather`. Baseline providers remain empty at all
budgets. Budget `100` non-selection is explicit: `context_ir` selects only
`def:main.py:main.load_weather_plugin`,
`def:main.py:main.render_probe_digest`, and
`frontier:call:main.py:6:11`; it does not select
`unsupported:call:main.py:5:13` or any `plugins/weather.py` unit.
Unsupported selector truth remains `unsupported/opaque` with
`unsupported_reason_code`, `opaque_boundary`, and attached runtime
provenance. Runtime provenance remains additive only. Winner behavior is
budget-specific: budget `100` winner is `context_ir`, while budgets `180` and
`220` winners remain `import_neighborhood_files`. No `plugins.weather`
dependency edge, selected symbol, or selected `plugins/weather.py` unit is
introduced, and public comparative claims remain bounded to the existing quad
matrix. No
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening is included.
The current internal eval-only `DYNAMIC_IMPORT` / root-module
`importlib.import_module(name)` sibling evidence is narrow and remains one task
only through `oracle_signal_dynamic_import_root_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is `import importlib`, `name = "plugins.weather"`, and exactly
`importlib.import_module(name)`. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, no
dependency edge or symbol is created from the dynamically imported module, and
public comparative claims remain bounded to the existing quad matrix. This
evidence does not cover `__import__(name)`, imported-name
`import_module(name)`, alias or loader forms, generalized dynamic import
support, or any
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening.
The current internal eval-only `DYNAMIC_IMPORT` / root-module literal
`importlib.import_module("plugins.weather")` sibling evidence is narrow and
remains one task only through
`oracle_signal_dynamic_import_root_literal_probe_matrix`: 1 task x 2 budgets x
3 providers at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is exactly `import importlib` plus
`module = importlib.import_module("plugins.weather")`; it does not include
`name = "plugins.weather"`, `importlib.import_module(name)`,
`from importlib import import_module`, `import_module("plugins.weather")`,
`__import__(...)`, `load_module(...)`, or `loader.import_module(...)`. The
runtime payload is `imported_module=plugins.weather`. File-level baselines
may select small fixture files, but their selected-unit layer remains empty
and they do not select the unsupported/runtime evidence unit.
At both budgets, `context_ir` selects
`def:main.py:main.load_weather_plugin`, `unsupported:call:main.py:5:13`, and
`frontier:call:main.py:6:11`, with the unsupported boundary retaining
`unsupported/opaque` primary truth and additive runtime provenance. No
`plugins.weather` dependency edge, selected symbol, or selected
`plugins/weather.py` unit is introduced. This evidence does not cover
name-variable, imported-name, alias, builtin, loader, generalized dynamic
import, public/API/MCP/package-export/schema/scoring/optimizer/compiler/
winner-selection/product/public benchmark, or product-surface widening.
The current internal eval-only `DYNAMIC_IMPORT` /
root-module alias `loader.import_module(name)` sibling evidence is narrow and
remains one task only through
`oracle_signal_dynamic_import_root_alias_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is `import importlib as loader`, `name = "plugins.weather"`, and exactly
`loader.import_module(name)`. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, no
dependency edge or selected symbol is created from `plugins.weather`, and
public comparative claims remain bounded to the existing quad matrix. This
evidence does not cover root-module `importlib.import_module(name)` expansion,
imported-name `import_module(name)` expansion, imported-alias
`load_module(name)` expansion, literal dynamic import expansion,
`__import__(name)`, `builtins.__import__`, globals/locals/fromlist forms,
namespace mutation, generated-code dependency modeling, generalized dynamic
import support, or any
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening.
The narrow internal eval-only `DYNAMIC_IMPORT` / builtin
`__import__(name)` sibling evidence is narrow and remains one task only through
`oracle_signal_dynamic_import_builtin_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary is
`name = "plugins.weather"` and exactly `__import__(name)`, with bounded
`sys.modules[name]` retrieval only. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, no
dependency edge or symbol is created from `plugins.weather`, and public
comparative claims remain bounded to the existing quad matrix. This evidence
does not cover `importlib.import_module(name)`, imported-name
`import_module(name)`, alias or loader forms, `builtins.__import__`,
globals/locals/fromlist forms, generalized dynamic import support, or any
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening.
The current internal eval-only `DYNAMIC_IMPORT` /
builtins-attribute `builtins.__import__(name)` sibling evidence is narrow and
remains one task only through
`oracle_signal_dynamic_import_builtins_attr_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is `import builtins`, `name = "plugins.weather"`, and exactly
`builtins.__import__(name)`, with bounded `sys.modules[name]` retrieval only.
The runtime payload is `imported_module=plugins.weather`. Primary selector and
selected-unit truth remain `unsupported/opaque`, runtime provenance remains
additive only, no dependency edge or selected symbol is created from
`plugins.weather`, and public comparative claims remain bounded to the
existing quad matrix. This evidence does not cover the separate builtins-alias
`loader.__import__(name)` form, bare `__import__(name)` expansion,
shadowed/rebound/aliased forms,
wrong-arity forms, literal `builtins.__import__("plugins.weather")`
expansion, fromlist/globals/locals forms, namespace mutation, generated-code
dependency modeling, generalized dynamic import support, or any
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening.
The current internal eval-only `DYNAMIC_IMPORT` /
builtins-alias `loader.__import__(name)` sibling evidence is narrow and
remains one task only through
`oracle_signal_dynamic_import_builtins_alias_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary
is `import builtins as loader`, `name = "plugins.weather"`, and exactly
`loader.__import__(name)`, with bounded `sys.modules[name]` retrieval only.
The runtime payload is `imported_module=plugins.weather`. Primary selector and
selected-unit truth remain `unsupported/opaque`, runtime provenance remains
additive only, no dependency edge or selected symbol is created from
`plugins.weather`, and public comparative claims remain bounded to the
existing quad matrix. This evidence does not cover other builtins alias names,
unaliased `builtins.__import__(name)` expansion in this matrix, bare
`__import__(name)` expansion, shadowed/rebound/non-builtins forms, wrong-arity
forms, literal `loader.__import__("plugins.weather")` expansion,
fromlist/globals/locals forms, namespace mutation, generated-code dependency
modeling, generalized dynamic import support, or any
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening.
The current internal eval-only `DYNAMIC_IMPORT` / imported-name
`import_module(name)` sibling evidence is narrow and remains one task only
through `oracle_signal_dynamic_import_imported_name_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary is
`from importlib import import_module`, `name = "plugins.weather"`, and exactly
`import_module(name)`. The runtime payload is
`imported_module=plugins.weather`. Primary selector and selected-unit truth
remain `unsupported/opaque`, runtime provenance remains additive only, no
dependency edge or selected symbol is created from `plugins.weather`, and
public comparative claims remain bounded to the existing quad matrix. This
evidence does not cover root-module `importlib.import_module(name)` expansion,
literal `import_module("plugins.weather")` expansion, alias
`load_module(name)`, `loader.import_module(name)`, `__import__(name)`,
`builtins.__import__`, globals/locals/fromlist forms, generalized dynamic
import support, or any
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening.
The current internal eval-only `DYNAMIC_IMPORT` / imported-alias
`load_module(name)` sibling evidence is narrow and remains one task only
through `oracle_signal_dynamic_import_imported_alias_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
`lexical_top_k_files`, and `import_neighborhood_files`. The fixture boundary is
`from importlib import import_module as load_module`,
`name = "plugins.weather"`, and exactly `load_module(name)`. The runtime
payload is `imported_module=plugins.weather`. Primary selector and selected-unit
truth remain `unsupported/opaque`, runtime provenance remains additive only, no
dependency edge or selected symbol is created from `plugins.weather`, and
public comparative claims remain bounded to the existing quad matrix. This
evidence does not cover root-module `importlib.import_module(name)` expansion,
imported-name `import_module(name)` expansion, literal
`load_module("plugins.weather")` expansion, `loader.import_module(name)`,
`__import__(name)`, `builtins.__import__`, globals/locals/fromlist forms,
namespace mutation, generated-code dependency modeling, generalized dynamic
import support, or any
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening.
Across the seven non-literal `DYNAMIC_IMPORT` sibling matrices
(`oracle_signal_dynamic_import_root_probe_matrix`,
`oracle_signal_dynamic_import_builtin_probe_matrix`,
`oracle_signal_dynamic_import_imported_name_probe_matrix`,
`oracle_signal_dynamic_import_imported_alias_probe_matrix`,
`oracle_signal_dynamic_import_root_alias_probe_matrix`,
`oracle_signal_dynamic_import_builtins_attr_probe_matrix`, and
`oracle_signal_dynamic_import_builtins_alias_probe_matrix`), each matrix is 1
task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers
`context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`. Fixture,
task, query, and runtime payload boundaries are unchanged across both budget
rows; runtime payload remains `imported_module=plugins.weather`. Baseline
providers remain empty at both budgets. At budget `220`, `context_ir` selects
the unsupported/opaque boundary unit with additive runtime provenance. At
budget `100`, `context_ir` preserves the resolved `unsupported/opaque`
selector and additive runtime provenance, but does not select the unsupported
boundary unit. No `plugins/weather.py` selected unit, dependency edge, or
selected symbol is introduced. No
source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening is included.
The eval(source) evidence intentionally adds a narrow lower-layer
eval(source) runtime provenance seam in runtime_acquisition, analyzer, and
tool_facade. It does not add generalized eval support, exec support,
`eval(source, globals)` support, `eval(source, globals, locals)` support,
generated-code dependency modeling, or namespace mutation modeling. Those
slices do not widen public claims, public APIs, MCP behavior,
package-export surfaces, scoring, winner-selection, optimizer, compiler,
product surfaces, schema, generalized reflective-builtin support, generalized
runtime-mutation support, generalized locals() support, or generalized
hybrid-runtime coverage, and they do not make metaclasses part of the public
supported subset. The no-widening boundary remains no
public/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
benchmark widening. The public-safe quad-matrix comparative boundary remains
unchanged.

The April 13 frozen spec is retired and superseded. Existing runtime modules under `src/context_ir/` still largely reflect the retired symbol-graph-first build and must be treated as implementation history until they are replaced slice by slice.

## System Goal

Context IR is a semantically grounded Python context compiler for coding agents. The system should compile the smallest trustworthy working set for the next decision by:

1. analyzing a supported static Python subset into a `SemanticProgram`
2. deriving proved dependencies plus an explicit unknown frontier
3. applying ranking and budget optimization on top of that semantic substrate
4. compiling context artifacts that surface both evidence and uncertainty

## Phase 0 Authority and Reopened Boundaries

Closed current authority:

- `analyze_repository(repo_root) -> SemanticProgram` remains the phase 0 low-level contract and current regression anchor
- the accepted quad matrix remains the top internal evidence surface for the completed milestone
- the accepted `oracle_signal_smoke_b / 200` `budget_pressure` limitation remains an explicit tight-budget truth
- current README, claim, and portfolio artifacts stay derivative of this phase 0 authority
- narrow post-phase-0 runtime-backed eval pilots are internal evidence only and
  do not change the public supported-subset boundary

Reopened for the post-milestone program:

- the exact shape of `SemanticProgram` as hybrid static + runtime evidence
  expands beyond narrow additive internal attachments
- supported-subset policy as it evolves into explicit capability tier handling
- dependency, frontier, and uncertainty modeling for mixed static/runtime evidence
- renderer, compiler, diagnose, and recompile contracts for tier-aware output
- ranking and optimization policy for mixed-evidence selection
- MCP and product boundaries for later production-facing work

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

This remains the authoritative phase 0 contract. Later slices may widen it, but only if the widened contract preserves provenance and keeps new evidence classes separate from static proof.

## Capability-Tier Target Model

The post-milestone program is organized around capability tier boundaries, not
around rendering density.

- statically proved: facts established from the accepted static semantic pipeline inside the supported subset
- runtime-backed: repository-backed facts supported by reproducible runtime
  evidence or probes; current internal evidence is limited to narrow additive
  `DYNAMIC_IMPORT` evidence, including the original
  `oracle_signal_dynamic_import_probe_matrix` provider/budget evidence at 1
  task x 3 budgets x 3 providers for budgets `[220, 180, 100]`, plus the
  current root-module
  `importlib.import_module(name)` sibling pilot, the current root-module
  literal `importlib.import_module("plugins.weather")` sibling pilot, and the
  narrow builtin
  `__import__(name)` sibling pilot, plus the current imported-name
  `import_module(name)` sibling pilot, plus the current imported-alias
  `load_module(name)` sibling pilot, plus the current root-module alias `loader.import_module(name)` sibling pilot, plus
  the current builtins-alias `loader.__import__(name)` sibling pilot, plus
  `REFLECTIVE_BUILTIN` /
  `hasattr(obj, name)` and
  `getattr(obj, name)` pilot attachments, including the current internal
  eval-only `hasattr(obj, name)` false-branch
  `oracle_signal_hasattr_false_probe_matrix` at 1 task x 2 budgets x 3
  providers for budgets `[220, 100]` with exact runtime payload
  `attribute_present=false`, deterministic digest `hasattr_false:missing`,
  `unsupported/opaque` selector and selected-unit primary truth, additive
  runtime provenance only, empty baselines, a missing-attribute
  no-edge/no-symbol/no-unit boundary, and no
  source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening, plus eval-only default-return and
  value-return branch pilots for `getattr(obj, name, default)`, plus the
  current internal eval-only raised-`AttributeError` branch pilot for exactly
  `getattr(obj, name)`, plus the current internal one-argument `vars(obj)` and
  zero-argument `vars()` pilots, plus the current internal eval-only
  raised-`TypeError` branch pilot for `vars(obj)`,
  plus the current internal one-argument `dir(obj)` pilot, plus the current
  internal zero-argument `dir()` pilot, plus the current internal eval-only
  `RUNTIME_MUTATION` / `globals()`, `locals()`, and
  `delattr(obj, name)` pilots, plus the current narrow internal eval-only
  `RUNTIME_MUTATION` / `setattr(obj, name, value)` evidence, plus the current
  internal eval-only `METACLASS_BEHAVIOR` / preserved `metaclass=...`
  keyword-site pilot.
  The three existing
  getattr-family provider/budget matrices cover budgets `100` and `220`; each
  remains 1 task x 2 budgets x 3 providers. The current internal `vars(obj)`
  pilot covers only 1 task x 2 budgets x 3 providers at budgets `100` and
  `220`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`. The current internal zero-argument `vars()`
  pilot covers only `oracle_signal_vars_zero_probe_matrix`: 1 task x 2 budgets x
  3 providers at budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`. In each case, selector and selected-unit
  primary truth still `unsupported/opaque` and runtime-backed provenance remains
  additive only. The current internal eval-only raised-`AttributeError`
  branch pilot for `getattr(obj, name)` covers only
  `oracle_signal_getattr_attribute_error_probe_matrix`: 1 task x 2 budgets x
  3 providers at budgets `220` and `100`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; the fixture, task,
  query, and runtime payload remain unchanged across both budget rows; the
  fixture boundary is exactly `getattr(obj, name)`, with `AttributeError`
  caught so `render_probe_digest()` is deterministic; runtime payload is
  `lookup_outcome=raised_attribute_error`; primary selector and selected-unit
  truth remain `unsupported/opaque`, runtime provenance remains additive only,
  baseline providers remain empty at both budgets, no missing-attribute
  dependency edge or selected symbol is created, and public comparative claims
  remain bounded to the existing quad matrix. No
  source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is included.
  The current internal eval-only raised-`TypeError` branch pilot for
  `vars(obj)` covers only `oracle_signal_vars_type_error_probe_matrix`: 1 task
  x 2 budgets x 3 providers at budgets `[220, 100]`, against providers
  `context_ir`, `lexical_top_k_files`, and `import_neighborhood_files`; the
  fixture boundary is exactly `vars(obj)`; runtime payload is exactly
  `lookup_outcome=raised_type_error`; deterministic digest is
  `vars_type_error:raised_type_error`; selector primary truth remains
  `unsupported/opaque`; runtime provenance is additive runtime provenance only;
  empty baselines remain empty at both budgets; no namespace dependency edge,
  selected symbol, or selected unit is introduced from the failed `vars()`
  lookup; the dependency guard uses `site:call:main.py:2:11`; and public
  comparative claims remain bounded to the existing quad matrix. No
  source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is included.
  The current internal `globals()` pilot covers only
  `oracle_signal_globals_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`; primary truth remains
  `unsupported/opaque`, and runtime-backed provenance is additive only.
  The current internal `locals()` pilot covers only
  `oracle_signal_locals_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `100` and `220`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with
  `lookup_outcome=returned_namespace`;
  selector and selected-unit primary truth remain `unsupported/opaque`, and
  runtime-backed provenance is additive only.
  The current internal eval-only `RUNTIME_MUTATION` / `delattr(obj, name)`
  pilot covers only `oracle_signal_delattr_probe_matrix`: 1 task x 2 budgets x
  3 providers at budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
  `mutation_outcome=deleted_attribute`; fixture, task, query, and runtime
  payload remain unchanged across both budget rows; selector and selected-unit
  primary truth remain `unsupported/opaque`; runtime provenance remains
  additive only; baseline providers remain empty at both budgets; and public
  comparative claims remain bounded to the existing quad matrix.
  The current internal eval-only `RUNTIME_MUTATION` /
  `setattr(obj, name, value)` evidence is narrow and covers only
  `oracle_signal_setattr_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`, with runtime payload
  `mutation_outcome=returned_none`; fixture, task, query, and runtime payload
  remain unchanged across both budget rows; selector/runtime-mutation surface
  and selected-unit primary truth remain `unsupported/opaque`; runtime
  provenance remains additive only; baseline providers remain empty at both
  budgets; and public comparative claims remain bounded to the existing quad
  matrix.
  The current internal `dir(obj)` pilot covers only
  `oracle_signal_dir_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; fixture, task,
  query, and runtime payload remain unchanged across both budget rows; runtime
  payload remains `listing_entry_count=74`; durable listing proof is carried
  by `durable_payload_reference`; `listing_entry_count` is additive summary
  only; selector and selected-unit primary truth remain `unsupported/opaque`;
  runtime-backed provenance is additive only; baseline providers remain empty
  at both budgets; and public comparative claims remain bounded to the
  existing quad matrix.
  The current internal zero-argument `dir()` pilot covers only
  `oracle_signal_dir_zero_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; runtime payload
  remains `listing_entry_count=0`; runtime proof remains via non-empty
  `durable_payload_reference`; `listing_entry_count` is additive summary only;
  baseline providers remain empty at both budgets; at budgets `220` and `100`,
  `context_ir` selects the same units:
  `def:main.py:main.probe_directory`,
  `def:main.py:main.render_probe_digest`, and
  `unsupported:call:main.py:2:11`; primary selector and selected-unit truth
  remain `unsupported/opaque` where applicable, runtime provenance remains
  additive only, no `dir()` output dependency edge or selected symbol is
  introduced, and public comparative claims remain bounded to the existing
  quad matrix. No
  source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is included.
  The current internal `METACLASS_BEHAVIOR` pilot covers only
  `oracle_signal_metaclass_behavior_probe_matrix`: 1 task x 2 budgets x 3
  providers at budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; runtime payload
  remains `class_creation_outcome=created_class`,
  `created_class_qualified_name=main.Example`, and
  `selected_metaclass_qualified_name=main.Meta`; `durable_payload_reference`
  is required and non-empty, and the qualified-name fields are additive
  summary only; baseline providers remain empty at both budgets; at budget
  `220`, `context_ir` selects `def:main.py:main.Example`,
  `def:main.py:main.Base`,
  `unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1`, and
  `frontier:base:main.py:5:11:def:main.py:main.Meta:1`; at budget `100`,
  `context_ir` selects `def:main.py:main.Example`,
  `unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1`, and
  `frontier:base:main.py:5:11:def:main.py:main.Meta:1`, omitting
  `def:main.py:main.Base`; attachment is limited to the preserved full
  `metaclass=...` keyword-site unsupported construct, selector and
  selected-unit primary truth remain `unsupported/opaque` where applicable,
  runtime provenance remains additive only, no selected
  `def:main.py:main.Meta` symbol, metaclass dependency edge, or other selected
  symbol is introduced beyond the listed units, and public comparative claims
  remain bounded to the existing quad matrix. No
  source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is included.
  The current internal `EXEC_OR_EVAL` / `eval(source)` evidence covers only
  `oracle_signal_eval_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; runtime proof
  requires
  `evaluation_outcome=returned_value`, `source_shape=literal_expression`,
  valid `source_sha256`, and non-empty `durable_payload_reference`. Baseline
  providers remain empty at both budgets. At both budgets, `context_ir`
  selects the same unsupported/opaque boundary unit with additive runtime
  provenance, and no generated-code dependency edge or selected symbol is
  introduced.
  The current internal `EXEC_OR_EVAL` / `exec(source)` evidence covers only
  `oracle_signal_exec_probe_matrix`: 1 task x 2 budgets x 3 providers at
  budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; fixture input is
  `source = "pass"`, the call is exactly `exec(source)`, executed source
  parses as exactly one `ast.Pass`, and runtime proof requires
  `execution_outcome=completed`,
  `source_shape=literal_statement`, valid `source_sha256` for exact `"pass"`,
  and non-empty `durable_payload_reference`. Optional `statement_kind=pass` is
  additive summary only. Primary selector and selected-unit truth remain
  `unsupported/opaque`, additive runtime provenance remains separate from
  primary truth, baseline providers remain empty at both budgets, and at both
  budgets `context_ir` selects the same unsupported/opaque boundary unit with
  additive runtime provenance. No generated-code dependency edge or selected
  symbol is introduced, no namespace mutation modeling is added, and public
  comparative claims remain bounded to the existing quad matrix.
  The current internal `DYNAMIC_IMPORT` / root-module
  `importlib.import_module(name)` sibling evidence covers only
  `oracle_signal_dynamic_import_root_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; fixture input is
  `import importlib`, `name = "plugins.weather"`, and exactly
  `importlib.import_module(name)`; runtime payload is
  `imported_module=plugins.weather`. Primary selector and selected-unit truth
  remain `unsupported/opaque`, runtime provenance remains additive only, no
  dependency edge or symbol is created from the dynamically imported module,
  no `__import__(name)`, imported-name `import_module(name)`, alias or loader
  forms, generalized dynamic import support, or public comparative claim
  widening is included.
  The current internal `DYNAMIC_IMPORT` / root-module literal
  `importlib.import_module("plugins.weather")` sibling evidence covers only
  `oracle_signal_dynamic_import_root_literal_probe_matrix`: 1 task x 2 budgets
  x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; fixture input is
  exactly `import importlib` plus
  `module = importlib.import_module("plugins.weather")`; runtime payload is
  `imported_module=plugins.weather`. File-level baselines may select small
  fixture files, but their selected-unit layer remains empty and they do not
  select the unsupported/runtime evidence unit. At both budgets,
  `context_ir` selects
  `def:main.py:main.load_weather_plugin`, `unsupported:call:main.py:5:13`,
  and `frontier:call:main.py:6:11`; the selected unsupported unit remains
  `unsupported/opaque` with additive runtime provenance. No
  `plugins/weather.py` selected unit, `plugins.weather` dependency edge, or
  selected symbol is introduced, and no name-variable, imported-name, alias,
  builtin, loader, generalized dynamic import support, or public comparative
  claim widening is included.
  The current internal `DYNAMIC_IMPORT` / root-module alias
  `loader.import_module(name)` sibling evidence covers only
  `oracle_signal_dynamic_import_root_alias_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; fixture input is
  `import importlib as loader`, `name = "plugins.weather"`, and exactly
  `loader.import_module(name)`; runtime payload is
  `imported_module=plugins.weather`. Primary selector and selected-unit truth
  remain `unsupported/opaque`, runtime provenance remains additive only, no
  dependency edge or selected symbol is created from `plugins.weather`, and no
  root-module `importlib.import_module(name)` expansion, imported-name
  `import_module(name)` expansion, imported-alias `load_module(name)`
  expansion, literal dynamic import expansion, `__import__(name)`,
  `builtins.__import__`, globals/locals/fromlist forms, namespace mutation,
  generated-code dependency modeling, generalized dynamic import support, or
  public comparative claim widening is included.
  The narrow internal `DYNAMIC_IMPORT` / builtin
  `__import__(name)` sibling evidence covers only
  `oracle_signal_dynamic_import_builtin_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; fixture input is
  `name = "plugins.weather"` and exactly `__import__(name)`, with bounded
  `sys.modules[name]` retrieval only; runtime payload is
  `imported_module=plugins.weather`. Primary selector and selected-unit truth
  remain `unsupported/opaque`, runtime provenance remains additive only, no
  dependency edge or symbol is created from `plugins.weather`, and no
  `importlib.import_module(name)`, imported-name `import_module(name)`, alias
  or loader forms, `builtins.__import__`, globals/locals/fromlist forms,
  generalized dynamic import support, or public comparative claim widening is
  included.
  The current internal `DYNAMIC_IMPORT` /
  builtins-attribute `builtins.__import__(name)` sibling evidence covers only
  `oracle_signal_dynamic_import_builtins_attr_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; fixture input is
  `import builtins`, `name = "plugins.weather"`, and exactly
  `builtins.__import__(name)`, with bounded `sys.modules[name]` retrieval
  only; runtime payload is `imported_module=plugins.weather`. Primary selector
  and selected-unit truth remain `unsupported/opaque`, runtime provenance
  remains additive only, no dependency edge or selected symbol is created from
  `plugins.weather`, and no separate builtins-alias
  `loader.__import__(name)` form, bare `__import__(name)` expansion,
  shadowed/rebound/aliased forms, wrong-arity forms, literal
  `builtins.__import__("plugins.weather")` expansion, fromlist/globals/locals
  forms, namespace mutation, generated-code dependency modeling, generalized
  dynamic import support, or public comparative claim widening is included.
  The current internal `DYNAMIC_IMPORT` /
  builtins-alias `loader.__import__(name)` sibling evidence covers only
  `oracle_signal_dynamic_import_builtins_alias_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; fixture input is
  `import builtins as loader`, `name = "plugins.weather"`, and exactly
  `loader.__import__(name)`, with bounded `sys.modules[name]` retrieval only;
  runtime payload is `imported_module=plugins.weather`. Primary selector and
  selected-unit truth remain `unsupported/opaque`, runtime provenance remains
  additive only, no dependency edge or selected symbol is created from
  `plugins.weather`, and no other builtins alias names, unaliased
  `builtins.__import__(name)` expansion in this matrix, bare
  `__import__(name)` expansion, shadowed/rebound/non-builtins forms,
  wrong-arity forms, literal `loader.__import__("plugins.weather")`
  expansion, fromlist/globals/locals forms, namespace mutation,
  generated-code dependency modeling, generalized dynamic import support, or
  public comparative claim widening is included.
  The current internal `DYNAMIC_IMPORT` / imported-name `import_module(name)`
  sibling evidence covers only
  `oracle_signal_dynamic_import_imported_name_probe_matrix`: 1 task x 2 budgets x 3 providers at budgets `[220, 100]`, against providers `context_ir`,
  `lexical_top_k_files`, and `import_neighborhood_files`; fixture input is
  `from importlib import import_module`, `name = "plugins.weather"`, and
  exactly `import_module(name)`; runtime payload is
  `imported_module=plugins.weather`. Primary selector and selected-unit truth
  remain `unsupported/opaque`, runtime provenance remains additive only, no
  dependency edge or selected symbol is created from `plugins.weather`, and no
  root-module `importlib.import_module(name)` expansion, literal
  `import_module("plugins.weather")` expansion, alias `load_module(name)`,
  `loader.import_module(name)`, `__import__(name)`, `builtins.__import__`,
  globals/locals/fromlist forms, generalized dynamic import support, or public
  comparative claim widening is included.
  The seven current non-literal `DYNAMIC_IMPORT` sibling budget-pressure matrices,
  including `oracle_signal_dynamic_import_imported_alias_probe_matrix`, share
  the same bounded evidence shape: 1 task x 2 budgets x 3 providers at budgets
  `[220, 100]`, against providers `context_ir`, `lexical_top_k_files`, and
  `import_neighborhood_files`. Fixture, task, query, and runtime payload
  boundaries are unchanged; runtime payload remains
  `imported_module=plugins.weather`; baseline providers remain empty at both
  budgets. At budget `220`, `context_ir` selects the unsupported/opaque
  boundary unit with additive runtime provenance. At budget `100`, `context_ir`
  preserves the resolved `unsupported/opaque` selector and additive runtime
  provenance, but does not select the unsupported boundary unit. No
  `plugins/weather.py` selected unit, dependency edge, selected symbol, or
  source/runtime/API/MCP/package-export/schema/scoring/optimizer/compiler/winner-selection/product/public
  benchmark widening is introduced.
- heuristic/frontier: relevant candidates or unresolved areas that may guide selection or follow-up work without being promoted to proof
- unsupported/opaque: dynamic or externalized surfaces that cannot yet be justified with durable evidence

Representation tiers remain a separate concern:

- a capability tier describes proof strength and provenance
- representation tiers describe how a selected unit is rendered for consumption
- a richer representation tier must not upgrade a unit from heuristic/frontier to runtime-backed or from runtime-backed to statically proved

## Phase-1 Capability-Tier Contract

Phase 1 began as a contract-definition step. The current repo now contains
narrow internal implementation/evidence slices that must continue to preserve
the same capability-tier meanings and provenance invariants.

### Tier Semantics and Admissible Evidence

- statically proved units may be emitted only when the accepted static semantic pipeline can trace the fact to supported syntax, binding, resolution, and dependency derivation inside the repository
- runtime-backed units may be emitted only when a reproducible repository-backed probe or observation produces evidence linked to a concrete repository subject, stable probe identity, and replay contract
- heuristic/frontier units may surface candidates, ranking hints, or incomplete dependency leads, but they cannot satisfy proof obligations, erase unknowns, or be counted as runtime-backed
- unsupported/opaque units mark boundaries the system cannot presently justify; they must remain explicit in artifacts and diagnostics instead of being dropped

Runtime-backed evidence is additive provenance, not a substitute for static proof. It may justify observed behavior that phase 0 could not prove statically, but it must never relabel an unresolved static surface as statically proved.

### Runtime-Backed Admissibility Boundary

A runtime-backed record is admissible only when all of the following hold:

- repository linkage: the observation attaches to a concrete repository subject such as a symbol, source span, dependency edge, frontier item, or unsupported finding; a free-floating claim that "the program did X" is insufficient
- stable probe identity: the record names the specific probe or observation contract that produced it, including a stable probe identifier and probe-contract revision
- replay contract: the record carries enough information to rerun the same observation against the same repository state, including the repository snapshot basis, target selector or entry surface, material probe inputs, and material runtime assumptions
- reproducible outcome: rerunning the same replay contract against the same repository state is expected to reproduce the same normalized observation; one-off manual success is not admissible proof
- provenance attachment: the observation can attach to the widened provenance schema without mutating phase 0 static facts in place; runtime-backed evidence is recorded as separate tiered support, not as a silent upgrade of static proof

Minimum attachable runtime-backed record, even if field names differ:

- subject locator: stable identity for the repository-backed subject plus source path/span or equivalent repository locator
- claim kind: what the observation is asserting, such as a dependency, resolution, behavior, or boundary fact
- probe identity: stable probe identifier plus probe-contract revision
- repository snapshot basis: the repository state the observation was taken from, such as a commit SHA or equivalent workspace snapshot identifier
- replay inputs: the target selector, probe parameters, and normalization rules required to reproduce the observation
- runtime assumptions: only the interpreter, dependency, or environment constraints that materially affect replay or interpretation
- observation payload: the normalized evidence payload or durable artifact reference that downstream layers can cite without reconstructing the probe
- attachment target: whether the record introduces a runtime-backed fact, corroborates an existing subject with separate runtime-backed provenance, or records a runtime-backed boundary condition

Explicitly non-admissible for runtime-backed admission:

- manual notes, screenshots, console snippets, or copied logs that are not tied to a stable probe identity and replay contract
- observations that cannot be linked back to a concrete repository subject and repository snapshot basis
- one-off runs whose outcome depends on unrecorded machine state, hidden setup, mutable external services, or other unreplayable conditions
- probe crashes, timeouts, setup failures, or missing-environment results treated as if they were positive runtime-backed proof; those may justify unsupported/opaque or acquisition-gap reporting, but not runtime-backed admission
- heuristic inferences drawn from repeated co-occurrence, frequency, or ranking usefulness without a replayed observation
- observations gathered from modified code, monkey patches, or ad hoc instrumentation that are not themselves represented in the recorded repository snapshot basis

Attachment rules for the widened provenance boundary:

- static and runtime evidence may point at the same subject, but they remain separate provenance entries with distinct capability tiers and evidence origins
- a runtime-backed record may justify a new dependency edge or subject record only if that edge or subject is itself marked runtime-backed and carries its own replay metadata
- lack of admissible runtime evidence does not erase frontier or unsupported status; it leaves the subject in its prior non-proof state
- compile, ranking, and diagnose layers may consume admissible runtime-backed records later, but they must not infer missing replay metadata or probe identity after the fact

### `SemanticProgram` Provenance Boundary

Current and later widened `SemanticProgram` contracts must preserve the phase 0
static layer as-is and add provenance-bearing records rather than replacing
existing proof classes.

Minimum widened contract shape, even if field names differ:

- subject identity for each symbol, dependency edge, frontier item, or unsupported finding
- source spans or repository locations for the subject and its supporting evidence
- repository snapshot basis for any runtime-backed supporting evidence
- capability tier for every downstream-visible record: statically proved, runtime-backed, heuristic/frontier, or unsupported/opaque
- evidence origin for every downstream-visible record: static derivation rule, runtime probe identity, heuristic rule, or unsupported-reason code
- replay status for every downstream-visible record: deterministic static, reproducible runtime, non-proof heuristic, or opaque boundary
- attachment target or equivalent linkage showing which semantic record the evidence supports
- downstream visibility signals needed by rendering, compile, and diagnose so later stages preserve provenance instead of reconstructing it heuristically

Policy constraints on the widened boundary:

- phase 0 static facts remain authoritative and must not be downgraded or silently remapped
- runtime-backed records may add new justified observations, but they must remain distinguishable from statically proved facts in the same `SemanticProgram`
- heuristic/frontier material may guide acquisition or selection, but it remains non-proof even when repeatedly useful
- unsupported/opaque records remain first-class because absence of proof is itself part of the contract

### Compile and Diagnose Preservation Rules

- compile may assemble mixed-tier artifacts, but every selected unit and every warning path must retain capability tier and evidence origin in traceable form
- compile must not merge statically proved and runtime-backed units into one unlabeled proof bucket
- ranking and optimization may compare units across tiers for budget decisions, but traces must show whether a loss came from budget pressure, lack of proof, or lack of runtime evidence
- diagnose must classify misses and gaps by tier boundary: missing static proof, missing runtime-backed evidence, heuristic/frontier under-selection, or unsupported/opaque boundary
- recompile may request more frontier expansion or runtime evidence acquisition, but it must not rewrite prior results as if proof already existed

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

Future reopening:
- the hybrid static + runtime analysis program may continue to add
  runtime-backed dependency evidence
- any such widening must preserve a visible separation between statically proved, runtime-backed, heuristic/frontier, and unsupported/opaque surfaces

### 4. Rendering / Representation Policy

Responsibility:
- define how semantic units can be represented at different densities
- preserve provenance from `SemanticProgram`
- expose uncertainty clearly when representation depends on incomplete proof

Current authority:
- multi-tier representation remains in scope
- the exact tier count and semantics are not frozen during the rebaseline
- the prior 5-tier scheme is historical only and not current authority
- representation tiers are not the same as capability tiers and must not be used as a proxy for proof strength

### 5. Ranking

Responsibility:
- prioritize which proved units and frontier items matter most for a task
- combine task signals with semantic structure, not replace it

Policy:
- `p_edit` and `p_support` may remain as internal ranking policy
- they are not the public thesis of the project
- they can rank among proved candidates and frontier items, but they cannot create semantic facts
- future user-facing mixed-evidence ranking may compare statically proved,
  runtime-backed, and heuristic/frontier units, but it must preserve those
  boundaries in traces and outputs

### 6. Optimization

Responsibility:
- choose a budget-feasible set of rendered units
- reason about tradeoffs, coverage, and downgrade decisions
- respect semantic dependency requirements and uncertainty surfacing

Output:
- optimized selection plan with traceable reasons

Future reopening:
- optimization may later become tier-aware across statically proved, runtime-backed, heuristic/frontier, and unsupported/opaque surfaces
- budget tradeoffs must not collapse those tiers into one undifferentiated score

### 7. Compilation

Responsibility:
- assemble selected rendered units into a context artifact
- include trace, warnings, and uncertainty signals derived from the semantic layer
- avoid overclaiming completeness when frontier uncertainty remains

Policy:
- compile behavior is downstream of `SemanticProgram`
- no compile contract is authoritative unless it matches the semantic substrate beneath it
- compiled artifacts that mix statically proved and runtime-backed material
  must keep capability tier provenance explicit

### 8. Diagnose / Recompile

Responsibility:
- interpret miss evidence against the compiled artifact and semantic trace
- identify which misses came from unsupported proof, missing frontier expansion, or ranking/optimization choices
- rebuild context without pretending the original semantic analysis knew more than it did

Current authority:
- diagnose and `recompile` are required architectural layers
- the public `recompile` contract is not frozen yet
- the old `recompile` hold is now part of the historical evidence trail, not the main control problem
- diagnose behavior may distinguish static-proof misses, runtime-backed misses,
  heuristic/frontier misses, and unsupported/opaque misses for tested internal
  surfaces, but public claims remain bounded by the current claim envelope

## Planned Boundaries

Exact file names may change during the rebaseline, but the logical boundaries are:

- semantic contracts and shared dataclasses
- syntax extraction
- binder and scope model
- resolver and object model
- semantic dependency/frontier derivation
- runtime-backed evidence acquisition boundary
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
