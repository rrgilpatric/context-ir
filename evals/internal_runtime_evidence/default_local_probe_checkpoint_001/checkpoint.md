# Runtime Evidence Checkpoint

This is an internal checkpoint for tangible runtime-evidence verification. It is not a public benchmark, benchmark result, or product claim.

## Artifacts

| Artifact | Path |
| --- | --- |
| Generated run spec | `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/run_spec.json` |
| Raw ledger | `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/ledger.jsonl` |
| Eval report | `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/report.md` |
| Manifest | `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/manifest.json` |
| Checkpoint | `evals/internal_runtime_evidence/default_local_probe_checkpoint_001/checkpoint.md` |

## Evidence

| Probe | Provider | Budget | Normalized Payload |
| --- | --- | ---: | --- |
| oracle_signal_locals_probe | context_ir_default_local_python_subprocess | 100 | `{"lookup_outcome":"returned_namespace"}` |
| oracle_signal_globals_probe | context_ir_default_local_python_subprocess | 100 | `{"lookup_outcome":"returned_namespace"}` |
| oracle_signal_vars_probe | context_ir_default_local_python_subprocess | 100 | `{"lookup_outcome":"returned_namespace"}` |
| oracle_signal_vars_type_error_probe | context_ir_default_local_python_subprocess | 100 | `{"lookup_outcome":"raised_type_error"}` |
| oracle_signal_vars_zero_probe | context_ir_default_local_python_subprocess | 100 | `{"lookup_outcome":"returned_namespace"}` |
| oracle_signal_dir_probe | context_ir_default_local_python_subprocess | 100 | `{"listing_entry_count":"74"}` |
| oracle_signal_dir_zero_probe | context_ir_default_local_python_subprocess | 100 | `{"listing_entry_count":"0"}` |
| oracle_signal_hasattr_probe | context_ir_default_local_python_subprocess | 100 | `{"attribute_present":"true"}` |
| oracle_signal_hasattr_false_probe | context_ir_default_local_python_subprocess | 100 | `{"attribute_present":"false"}` |
| oracle_signal_hasattr_literal_probe | context_ir_default_local_python_subprocess | 100 | `{"attribute_present":"true"}` |
| oracle_signal_getattr_probe | context_ir_default_local_python_subprocess | 100 | `{"lookup_outcome":"returned_value"}` |
| oracle_signal_getattr_attribute_error_probe | context_ir_default_local_python_subprocess | 100 | `{"lookup_outcome":"raised_attribute_error"}` |
| oracle_signal_getattr_default_probe | context_ir_default_local_python_subprocess | 100 | `{"lookup_outcome":"returned_default_value"}` |
| oracle_signal_getattr_default_value_probe | context_ir_default_local_python_subprocess | 100 | `{"lookup_outcome":"returned_value"}` |
| oracle_signal_getattr_literal_probe | context_ir_default_local_python_subprocess | 100 | `{"lookup_outcome":"returned_value"}` |
| oracle_signal_dynamic_import_root_literal_probe | context_ir_default_local_python_subprocess | 100 | `{"imported_module":"plugins.weather"}` |
| oracle_signal_dynamic_import_root_probe | context_ir_default_local_python_subprocess | 220 | `{"imported_module":"plugins.weather"}` |
| oracle_signal_dynamic_import_root_alias_probe | context_ir_default_local_python_subprocess | 220 | `{"imported_module":"plugins.weather"}` |
| oracle_signal_dynamic_import_builtin_probe | context_ir_default_local_python_subprocess | 220 | `{"imported_module":"plugins.weather"}` |
| oracle_signal_dynamic_import_builtins_attr_probe | context_ir_default_local_python_subprocess | 220 | `{"imported_module":"plugins.weather"}` |
| oracle_signal_dynamic_import_builtins_alias_probe | context_ir_default_local_python_subprocess | 220 | `{"imported_module":"plugins.weather"}` |
| oracle_signal_dynamic_import_imported_name_probe | context_ir_default_local_python_subprocess | 220 | `{"imported_module":"plugins.weather"}` |
| oracle_signal_dynamic_import_imported_alias_probe | context_ir_default_local_python_subprocess | 220 | `{"imported_module":"plugins.weather"}` |
| oracle_signal_dynamic_import_probe | context_ir_default_local_python_subprocess | 180 | `{"imported_module":"plugins.weather"}` |
| oracle_signal_setattr_probe | context_ir_default_local_python_subprocess | 100 | `{"mutation_outcome":"returned_none"}` |
| oracle_signal_setattr_literal_probe | context_ir_default_local_python_subprocess | 100 | `{"mutation_outcome":"returned_none"}` |
| oracle_signal_delattr_probe | context_ir_default_local_python_subprocess | 100 | `{"mutation_outcome":"deleted_attribute"}` |
| oracle_signal_delattr_literal_probe | context_ir_default_local_python_subprocess | 100 | `{"mutation_outcome":"deleted_attribute"}` |
| oracle_signal_exec_probe | context_ir_default_local_python_subprocess | 100 | `{"execution_outcome":"completed","statement_kind":"pass"}` |
| oracle_signal_eval_probe | context_ir_default_local_python_subprocess | 100 | `{"evaluation_outcome":"returned_value","result_type":"builtins.str"}` |
| oracle_signal_metaclass_behavior_probe | context_ir_default_local_python_subprocess | 100 | `{"class_creation_outcome":"created_class","created_class_qualified_name":"main.Example","selected_metaclass_qualified_name":"main.Meta"}` |

## Unsupported / Remaining Gap

This checkpoint only exercises the exact `context_ir_default_local_python_subprocess` fixtures listed above at their provider-valid budgets. It does not widen support for generalized runtime/provider behavior, additional runtime-probe forms, compiler semantics, scoring, MCP contracts, schema/config contracts, composite smoke tasks, legacy smoke tasks, or any public benchmark/product claim beyond these exact supported probes.
