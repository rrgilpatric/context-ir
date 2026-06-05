# Eval Summary

- Record count: 31
- Tasks: oracle_signal_delattr_literal_probe, oracle_signal_delattr_probe, oracle_signal_dir_probe, oracle_signal_dir_zero_probe, oracle_signal_dynamic_import_builtin_probe, oracle_signal_dynamic_import_builtins_alias_probe, oracle_signal_dynamic_import_builtins_attr_probe, oracle_signal_dynamic_import_imported_alias_probe, oracle_signal_dynamic_import_imported_name_probe, oracle_signal_dynamic_import_probe, oracle_signal_dynamic_import_root_alias_probe, oracle_signal_dynamic_import_root_literal_probe, oracle_signal_dynamic_import_root_probe, oracle_signal_eval_probe, oracle_signal_exec_probe, oracle_signal_getattr_attribute_error_probe, oracle_signal_getattr_default_probe, oracle_signal_getattr_default_value_probe, oracle_signal_getattr_literal_probe, oracle_signal_getattr_probe, oracle_signal_globals_probe, oracle_signal_hasattr_false_probe, oracle_signal_hasattr_literal_probe, oracle_signal_hasattr_probe, oracle_signal_locals_probe, oracle_signal_metaclass_behavior_probe, oracle_signal_setattr_literal_probe, oracle_signal_setattr_probe, oracle_signal_vars_probe, oracle_signal_vars_type_error_probe, oracle_signal_vars_zero_probe
- Providers: context_ir_default_local_python_subprocess
- Budgets: 100, 180, 220

## Provider Aggregates

| Provider | Records | Budget Compliance | Aggregate Score | Edit Coverage | Support Coverage | Representation Adequacy | Uncertainty Honesty | Noise Efficiency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| context_ir_default_local_python_subprocess | 31 | 1.000 | 0.707 | 0.645 | 0.633 | 0.661 | 0.976 | 0.747 |

## Capability-Tier Accounting


### Selector Expectations by Declared Primary Tier

| Declared Primary Tier | Selectors | Satisfied |
| --- | ---: | ---: |
| unsupported/opaque | 31 | 31 |

### Selector Runtime Provenance Expectations

| Expected Attached Runtime Provenance | Selectors | Satisfied |
| --- | ---: | ---: |
| yes | 31 | 31 |

### Selected Units by Actual Primary Tier

| Actual Primary Tier | Selected Units | Attached Runtime Provenance |
| --- | ---: | ---: |
| statically_proved | 60 | 0 |
| heuristic/frontier | 10 | 0 |
| unsupported/opaque | 30 | 30 |

### Selected Units by Provider

| Provider | Selected Units | Attached Runtime Provenance |
| --- | ---: | ---: |
| context_ir_default_local_python_subprocess | 100 | 30 |

### Selected Units by Provider and Actual Primary Tier

| Provider | Actual Primary Tier | Selected Units | Attached Runtime Provenance |
| --- | --- | ---: | ---: |
| context_ir_default_local_python_subprocess | statically_proved | 60 | 0 |
| context_ir_default_local_python_subprocess | heuristic/frontier | 10 | 0 |
| context_ir_default_local_python_subprocess | unsupported/opaque | 30 | 30 |

## Runtime Outcome Accounting


### Selected-Unit Runtime Outcomes

| Selected Unit | Payload Key | Payload Value | Runtime Provenance Records |
| --- | --- | --- | ---: |
| unsupported:call:main.py:2:11 | attribute_present | false | 1 |
| unsupported:call:main.py:2:11 | attribute_present | true | 2 |
| unsupported:call:main.py:2:11 | listing_entry_count | 0 | 1 |
| unsupported:call:main.py:2:11 | listing_entry_count | 74 | 1 |
| unsupported:call:main.py:2:11 | lookup_outcome | raised_attribute_error | 1 |
| unsupported:call:main.py:2:11 | lookup_outcome | returned_default_value | 1 |
| unsupported:call:main.py:2:11 | lookup_outcome | returned_namespace | 2 |
| unsupported:call:main.py:2:11 | lookup_outcome | returned_value | 3 |
| unsupported:call:main.py:3:11 | evaluation_outcome | returned_value | 1 |
| unsupported:call:main.py:3:11 | lookup_outcome | returned_namespace | 1 |
| unsupported:call:main.py:3:11 | result_type | builtins.str | 1 |
| unsupported:call:main.py:3:4 | execution_outcome | completed | 1 |
| unsupported:call:main.py:3:4 | statement_kind | pass | 1 |
| unsupported:call:main.py:5:13 | imported_module | plugins.weather | 2 |
| unsupported:call:main.py:6:13 | imported_module | plugins.weather | 4 |
| unsupported:call:main.py:6:4 | imported_module | plugins.weather | 1 |
| unsupported:call:main.py:7:11 | lookup_outcome | returned_namespace | 1 |
| unsupported:call:main.py:7:4 | imported_module | plugins.weather | 2 |
| unsupported:call:main.py:7:4 | mutation_outcome | deleted_attribute | 2 |
| unsupported:call:main.py:7:4 | mutation_outcome | returned_none | 2 |
| unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1 | class_creation_outcome | created_class | 1 |
| unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1 | created_class_qualified_name | main.Example | 1 |
| unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1 | selected_metaclass_qualified_name | main.Meta | 1 |

### Runtime Provenance Outcomes

| Payload Key | Payload Value | Runtime Provenance Records |
| --- | --- | ---: |
| attribute_present | false | 2 |
| attribute_present | true | 4 |
| class_creation_outcome | created_class | 2 |
| created_class_qualified_name | main.Example | 2 |
| evaluation_outcome | returned_value | 2 |
| execution_outcome | completed | 2 |
| imported_module | plugins.weather | 18 |
| listing_entry_count | 0 | 2 |
| listing_entry_count | 74 | 2 |
| lookup_outcome | raised_attribute_error | 2 |
| lookup_outcome | raised_type_error | 1 |
| lookup_outcome | returned_default_value | 2 |
| lookup_outcome | returned_namespace | 8 |
| lookup_outcome | returned_value | 6 |
| mutation_outcome | deleted_attribute | 4 |
| mutation_outcome | returned_none | 4 |
| result_type | builtins.str | 2 |
| selected_metaclass_qualified_name | main.Meta | 2 |
| statement_kind | pass | 2 |

## Task Budget Results

| Task | Budget | Winner | Provider Results |
| --- | ---: | --- | --- |
| oracle_signal_delattr_literal_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.995, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.948, budget=yes) |
| oracle_signal_delattr_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.995, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.949, budget=yes) |
| oracle_signal_dir_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.995, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.949, budget=yes) |
| oracle_signal_dir_zero_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.993, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.933, budget=yes) |
| oracle_signal_dynamic_import_builtin_probe | 220 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.152, edit=0.000, support=0.000, repr=0.000, honest=1.000, noise=0.020, budget=yes) |
| oracle_signal_dynamic_import_builtins_alias_probe | 220 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.186, edit=0.000, support=0.000, repr=0.000, honest=1.000, noise=0.364, budget=yes) |
| oracle_signal_dynamic_import_builtins_attr_probe | 220 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.186, edit=0.000, support=0.000, repr=0.000, honest=1.000, noise=0.362, budget=yes) |
| oracle_signal_dynamic_import_imported_alias_probe | 220 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.153, edit=0.000, support=0.000, repr=0.000, honest=1.000, noise=0.029, budget=yes) |
| oracle_signal_dynamic_import_imported_name_probe | 220 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.180, edit=0.000, support=0.000, repr=0.000, honest=1.000, noise=0.304, budget=yes) |
| oracle_signal_dynamic_import_probe | 180 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.190, edit=0.000, support=0.000, repr=0.000, honest=1.000, noise=0.398, budget=yes) |
| oracle_signal_dynamic_import_root_alias_probe | 220 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.189, edit=0.000, support=0.000, repr=0.000, honest=1.000, noise=0.390, budget=yes) |
| oracle_signal_dynamic_import_root_literal_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.226, edit=0.000, support=0.000, repr=0.000, honest=1.000, noise=0.756, budget=yes) |
| oracle_signal_dynamic_import_root_probe | 220 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.189, edit=0.000, support=0.000, repr=0.000, honest=1.000, noise=0.394, budget=yes) |
| oracle_signal_eval_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.995, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.953, budget=yes) |
| oracle_signal_exec_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.994, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.941, budget=yes) |
| oracle_signal_getattr_attribute_error_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.994, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.938, budget=yes) |
| oracle_signal_getattr_default_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.994, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.944, budget=yes) |
| oracle_signal_getattr_default_value_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.546, edit=0.000, support=1.000, repr=0.500, honest=1.000, noise=0.714, budget=yes) |
| oracle_signal_getattr_literal_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.994, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.940, budget=yes) |
| oracle_signal_getattr_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.992, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.925, budget=yes) |
| oracle_signal_globals_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.960, edit=1.000, support=-, repr=1.000, honest=1.000, noise=0.703, budget=yes) |
| oracle_signal_hasattr_false_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.243, edit=0.000, support=0.000, repr=0.000, honest=1.000, noise=0.925, budget=yes) |
| oracle_signal_hasattr_literal_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.994, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.939, budget=yes) |
| oracle_signal_hasattr_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.994, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.937, budget=yes) |
| oracle_signal_locals_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.994, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.937, budget=yes) |
| oracle_signal_metaclass_behavior_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.736, edit=1.000, support=0.000, repr=1.000, honest=1.000, noise=0.856, budget=yes) |
| oracle_signal_setattr_literal_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.994, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.942, budget=yes) |
| oracle_signal_setattr_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.994, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.942, budget=yes) |
| oracle_signal_vars_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.993, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.934, budget=yes) |
| oracle_signal_vars_type_error_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.881, edit=1.000, support=1.000, repr=1.000, honest=0.250, noise=0.936, budget=yes) |
| oracle_signal_vars_zero_probe | 100 | context_ir_default_local_python_subprocess | context_ir_default_local_python_subprocess (agg=0.995, edit=1.000, support=1.000, repr=1.000, honest=1.000, noise=0.950, budget=yes) |