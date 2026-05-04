"""Tests for planned runtime probe request derivation."""

from __future__ import annotations

import hashlib
import json
import textwrap
from pathlib import Path

import pytest

import context_ir.runtime_probe_requests as runtime_probe_requests
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_types import (
    CapabilityTier,
    SemanticDiagnosticBoundary,
    SemanticDiagnosticBoundaryKind,
    SemanticDiagnosticResult,
    SemanticDiagnosticUnitStatus,
    SemanticProgram,
    SemanticSubjectKind,
    UnresolvedReasonCode,
)


def _derived_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted semantic pipeline through frontier derivation."""
    syntax = extract_syntax(tmp_path)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


def _unsupported_id_for(program: SemanticProgram, construct_text: str) -> str:
    """Return the unsupported-construct ID for one preserved surface."""
    matching_ids = [
        construct.construct_id
        for construct in program.unsupported_constructs
        if construct.construct_text == construct_text
    ]
    assert len(matching_ids) == 1
    return matching_ids[0]


def _frontier_id_for(program: SemanticProgram, access_text: str) -> str:
    """Return the unresolved-frontier ID for one preserved surface."""
    matching_ids = [
        access.access_id
        for access in program.unresolved_frontier
        if access.access_text == access_text
    ]
    assert len(matching_ids) == 1
    return matching_ids[0]


def _symbol_id_for(program: SemanticProgram, qualified_name: str) -> str:
    """Return the resolved-symbol ID for one qualified name."""
    matching_ids = [
        symbol_id
        for symbol_id, symbol in program.resolved_symbols.items()
        if symbol.qualified_name == qualified_name
    ]
    assert len(matching_ids) == 1
    return matching_ids[0]


def _diagnostic_boundary(
    unit_id: str,
    *,
    boundary_kind: SemanticDiagnosticBoundaryKind,
    primary_capability_tier: CapabilityTier,
    status: SemanticDiagnosticUnitStatus = SemanticDiagnosticUnitStatus.OMITTED,
    has_attached_runtime_provenance: bool = False,
) -> SemanticDiagnosticBoundary:
    """Build one typed diagnostic boundary for runtime-request tests."""
    return SemanticDiagnosticBoundary(
        unit_id=unit_id,
        status=status,
        boundary_kind=boundary_kind,
        primary_capability_tier=primary_capability_tier,
        has_attached_runtime_provenance=has_attached_runtime_provenance,
    )


def _diagnostic_result(
    boundaries: tuple[SemanticDiagnosticBoundary, ...],
) -> SemanticDiagnosticResult:
    """Build a diagnostic result aligned with the supplied boundaries."""
    return SemanticDiagnosticResult(
        grounded_unit_ids=tuple(boundary.unit_id for boundary in boundaries),
        omitted_unit_ids=tuple(
            boundary.unit_id
            for boundary in boundaries
            if boundary.status is SemanticDiagnosticUnitStatus.OMITTED
        ),
        too_shallow_unit_ids=tuple(
            boundary.unit_id
            for boundary in boundaries
            if boundary.status is SemanticDiagnosticUnitStatus.TOO_SHALLOW
        ),
        sufficiently_represented_unit_ids=tuple(
            boundary.unit_id
            for boundary in boundaries
            if (
                boundary.status is SemanticDiagnosticUnitStatus.SUFFICIENTLY_REPRESENTED
            )
        ),
        recommended_expansions=(),
        reason="Test diagnostic result.",
        boundary_classifications=boundaries,
    )


def _expected_plan_id(
    plan: runtime_probe_requests.RuntimeProbeRequestPlan,
) -> str:
    """Return the expected stable request-plan ID for test assertions."""
    serialized_identity = json.dumps(
        (
            ("contract_version", plan.contract_version),
            ("request_ids", plan.request_ids),
        ),
        separators=(",", ":"),
    )
    digest = hashlib.sha256(serialized_identity.encode("utf-8")).hexdigest()
    return f"runtime_probe_request_plan:{digest}"


def test_derive_runtime_probe_requests_plans_attachable_runtime_boundaries(
    tmp_path: Path,
) -> None:
    """Runtime probe requests cover supported attachable boundary families."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import builtins
            import importlib
            from importlib import import_module as load_module

            class Meta(type):
                pass

            class Example(metaclass=Meta):
                pass

            def run(
                obj: object,
                name: str,
                value: object,
                source: str,
                default: object,
            ) -> None:
                importlib.import_module(name)
                load_module(name)
                builtins.__import__(name)
                __import__(name)
                getattr(obj, name)
                getattr(obj, name, default)
                hasattr(obj, name)
                vars(obj)
                vars()
                dir(obj)
                dir()
                setattr(obj, name, value)
                delattr(obj, name)
                globals()
                locals()
                exec(source)
                eval(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)
    original_unsupported = list(program.unsupported_constructs)
    original_frontier = list(program.unresolved_frontier)
    original_provenance_records = list(program.provenance_records)

    first_requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    second_requests = runtime_probe_requests.derive_runtime_probe_requests(program)

    requests_by_text = {request.boundary_text: request for request in first_requests}
    first_request_ids = [request.request_id for request in first_requests]
    second_request_ids = [request.request_id for request in second_requests]
    source_site_fragments = [
        (
            request.source_site.file_path,
            request.source_site.span.start_line,
            request.source_site.span.start_column,
            request.source_site.span.end_line,
            request.source_site.span.end_column,
        )
        for request in first_requests
    ]

    assert first_requests == second_requests
    assert first_request_ids == second_request_ids
    assert len(first_request_ids) == len(set(first_request_ids))
    assert all(
        request_id.startswith("runtime_probe:") for request_id in first_request_ids
    )
    assert {
        request.family_label for request in first_requests if request.request_id
    } == set(runtime_probe_requests.RuntimeProbeFamily)
    assert source_site_fragments == sorted(source_site_fragments)
    assert len(source_site_fragments) == len(set(source_site_fragments))
    assert program.unsupported_constructs == original_unsupported
    assert program.unresolved_frontier == original_frontier
    assert program.provenance_records == original_provenance_records
    assert set(requests_by_text) == {
        "metaclass=Meta",
        "importlib.import_module(name)",
        "load_module(name)",
        "builtins.__import__(name)",
        "__import__(name)",
        "getattr(obj, name)",
        "getattr(obj, name, default)",
        "hasattr(obj, name)",
        "vars(obj)",
        "vars()",
        "dir(obj)",
        "dir()",
        "setattr(obj, name, value)",
        "delattr(obj, name)",
        "globals()",
        "locals()",
        "exec(source)",
        "eval(source)",
    }

    dynamic_import = requests_by_text["importlib.import_module(name)"]
    assert dynamic_import.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert dynamic_import.reason_code is UnresolvedReasonCode.DYNAMIC_IMPORT
    assert (
        dynamic_import.family_label
        is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT
    )
    assert dynamic_import.form_label == "dynamic_import:importlib.import_module/1"
    assert dynamic_import.replay_target_seed == "main.run"
    assert dynamic_import.replay_selector_seed.startswith(
        "call:main.run:dynamic_import:importlib.import_module/1@main.py:"
    )
    assert (
        dynamic_import.status
        is runtime_probe_requests.RuntimeProbeRequestStatus.PLANNED_NOT_EXECUTED
    )

    reflective_builtin = requests_by_text["getattr(obj, name, default)"]
    assert reflective_builtin.reason_code is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    assert (
        reflective_builtin.family_label
        is runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN
    )
    assert reflective_builtin.form_label == "reflective_builtin:getattr/3"
    assert reflective_builtin.replay_target_seed == "main.run"
    assert (
        reflective_builtin.status
        is runtime_probe_requests.RuntimeProbeRequestStatus.PLANNED_NOT_EXECUTED
    )

    runtime_mutation = requests_by_text["setattr(obj, name, value)"]
    assert runtime_mutation.reason_code is UnresolvedReasonCode.RUNTIME_MUTATION
    assert (
        runtime_mutation.family_label
        is runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION
    )
    assert runtime_mutation.form_label == "runtime_mutation:setattr/3"
    assert runtime_mutation.replay_target_seed == "main.run"

    exec_request = requests_by_text["exec(source)"]
    assert exec_request.reason_code is UnresolvedReasonCode.EXEC_OR_EVAL
    assert (
        exec_request.family_label
        is runtime_probe_requests.RuntimeProbeFamily.EXEC_OR_EVAL
    )
    assert exec_request.form_label == "exec_or_eval:exec/1"
    assert exec_request.replay_target_seed == "main.run"

    metaclass_request = requests_by_text["metaclass=Meta"]
    assert metaclass_request.reason_code is UnresolvedReasonCode.METACLASS_BEHAVIOR
    assert (
        metaclass_request.family_label
        is runtime_probe_requests.RuntimeProbeFamily.METACLASS_BEHAVIOR
    )
    assert metaclass_request.form_label == "metaclass_behavior:keyword"
    assert metaclass_request.replay_target_seed == "main.Example"
    assert metaclass_request.replay_selector_seed.startswith(
        "class:main.Example:metaclass@main.py:"
    )


def test_derive_runtime_probe_requests_excludes_non_attachable_boundaries(
    tmp_path: Path,
) -> None:
    """Unsupported but non-attachable forms do not become runtime probe requests."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib.metadata as importlib

            def wrapper(func):
                return func

            @wrapper(factory())
            def decorated() -> None:
                pass

            def run(
                obj: object,
                name: str,
                source: str,
                globals_ns: dict[str, object],
                default: object,
            ) -> None:
                importlib.import_module(name)
                getattr()
                hasattr(obj)
                globals(obj)
                locals(obj)
                setattr(obj, name)
                delattr(obj)
                dir(obj, default)
                eval(source, globals_ns)
                eval(source=source)
                exec(source, globals_ns)
                exec(source=source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)

    requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    requested_texts = {request.boundary_text for request in requests}
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in program.unsupported_constructs
    }

    assert requests == ()
    assert unsupported_by_text["getattr()"] is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    assert unsupported_by_text["hasattr(obj)"] is (
        UnresolvedReasonCode.REFLECTIVE_BUILTIN
    )
    assert unsupported_by_text["globals(obj)"] is (
        UnresolvedReasonCode.RUNTIME_MUTATION
    )
    assert unsupported_by_text["locals(obj)"] is UnresolvedReasonCode.RUNTIME_MUTATION
    assert unsupported_by_text["setattr(obj, name)"] is (
        UnresolvedReasonCode.RUNTIME_MUTATION
    )
    assert unsupported_by_text["delattr(obj)"] is UnresolvedReasonCode.RUNTIME_MUTATION
    assert unsupported_by_text["dir(obj, default)"] is (
        UnresolvedReasonCode.REFLECTIVE_BUILTIN
    )
    assert unsupported_by_text["eval(source, globals_ns)"] is (
        UnresolvedReasonCode.EXEC_OR_EVAL
    )
    assert unsupported_by_text["eval(source=source)"] is (
        UnresolvedReasonCode.EXEC_OR_EVAL
    )
    assert unsupported_by_text["exec(source, globals_ns)"] is (
        UnresolvedReasonCode.EXEC_OR_EVAL
    )
    assert unsupported_by_text["exec(source=source)"] is (
        UnresolvedReasonCode.EXEC_OR_EVAL
    )
    assert unsupported_by_text["wrapper(factory())"] is (
        UnresolvedReasonCode.OPAQUE_DECORATOR
    )
    assert "importlib.import_module(name)" not in unsupported_by_text
    assert requested_texts.isdisjoint(unsupported_by_text)


def test_index_runtime_probe_requests_by_id_returns_ordered_full_plan(
    tmp_path: Path,
) -> None:
    """Runtime probe request indexing preserves full-plan request identity order."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(obj: object, name: str, source: str) -> None:
                importlib.import_module(name)
                getattr(obj, name)
                exec(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)

    requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    original_requests = tuple(requests)
    original_unsupported = list(program.unsupported_constructs)
    original_frontier = list(program.unresolved_frontier)
    original_provenance_records = list(program.provenance_records)
    requests_by_id = runtime_probe_requests.index_runtime_probe_requests_by_id(requests)

    assert requests_by_id == {request.request_id: request for request in requests}
    assert list(requests_by_id) == [request.request_id for request in requests]
    assert list(requests_by_id.values()) == list(requests)
    assert requests == original_requests
    assert program.unsupported_constructs == original_unsupported
    assert program.unresolved_frontier == original_frontier
    assert program.provenance_records == original_provenance_records


def test_index_runtime_probe_requests_by_id_rejects_duplicate_ids(
    tmp_path: Path,
) -> None:
    """Runtime probe request indexing rejects ambiguous duplicate request IDs."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(name: str) -> None:
                importlib.import_module(name)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)
    requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    duplicate_requests = (requests[0], requests[0])

    with pytest.raises(ValueError, match="duplicate runtime probe request_id"):
        runtime_probe_requests.index_runtime_probe_requests_by_id(duplicate_requests)


def test_build_runtime_probe_request_plan_wraps_full_plan_deterministically(
    tmp_path: Path,
) -> None:
    """Runtime probe request plans preserve full planned batches deterministically."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(obj: object, name: str, source: str) -> None:
                importlib.import_module(name)
                getattr(obj, name)
                exec(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)
    first_requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    second_requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    original_requests = tuple(first_requests)
    original_request_ids = tuple(request.request_id for request in first_requests)
    original_unsupported = list(program.unsupported_constructs)
    original_frontier = list(program.unresolved_frontier)
    original_provenance_records = list(program.provenance_records)

    first_plan = runtime_probe_requests.build_runtime_probe_request_plan(first_requests)
    second_plan = runtime_probe_requests.build_runtime_probe_request_plan(
        second_requests
    )

    assert first_plan.contract_version == "runtime_probe_request_plan:v1"
    assert first_plan.requests == first_requests
    assert first_plan.request_ids == original_request_ids
    assert first_plan.plan_id == _expected_plan_id(first_plan)
    assert first_plan.plan_id == second_plan.plan_id
    assert first_plan.requests == second_plan.requests
    assert [request.boundary_text for request in first_plan.requests] == [
        "importlib.import_module(name)",
        "getattr(obj, name)",
        "exec(source)",
    ]
    assert all(
        plan_request is request
        for plan_request, request in zip(
            first_plan.requests, first_requests, strict=True
        )
    )
    assert first_requests == original_requests
    assert (
        tuple(request.request_id for request in first_requests) == original_request_ids
    )
    assert program.unsupported_constructs == original_unsupported
    assert program.unresolved_frontier == original_frontier
    assert program.provenance_records == original_provenance_records


def test_build_runtime_probe_request_plan_rejects_duplicate_request_ids(
    tmp_path: Path,
) -> None:
    """Runtime probe request plans reject duplicate stable request IDs."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(name: str) -> None:
                importlib.import_module(name)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)
    requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    duplicate_requests = (requests[0], requests[0])

    with pytest.raises(ValueError, match="duplicate runtime probe request_id"):
        runtime_probe_requests.build_runtime_probe_request_plan(duplicate_requests)


def test_build_runtime_probe_request_plan_allows_empty_plan() -> None:
    """Empty runtime probe request plans are valid and deterministic."""
    first_plan = runtime_probe_requests.build_runtime_probe_request_plan(())
    second_plan = runtime_probe_requests.build_runtime_probe_request_plan([])

    assert first_plan.contract_version == "runtime_probe_request_plan:v1"
    assert first_plan.requests == ()
    assert first_plan.request_ids == ()
    assert first_plan.plan_id.startswith("runtime_probe_request_plan:")
    assert first_plan.plan_id == _expected_plan_id(first_plan)
    assert first_plan == second_plan


def test_derive_diagnostic_runtime_probe_requests_returns_attachable_omitted_boundary(
    tmp_path: Path,
) -> None:
    """Omitted unsupported attachable boundaries become planned probe requests."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(name: str) -> None:
                importlib.import_module(name)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)
    unsupported_id = _unsupported_id_for(program, "importlib.import_module(name)")
    planned_requests_by_subject_id = {
        request.subject_id: request
        for request in runtime_probe_requests.derive_runtime_probe_requests(program)
    }
    diagnostic = _diagnostic_result(
        (
            _diagnostic_boundary(
                unsupported_id,
                boundary_kind=(
                    SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
                ),
                primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
            ),
        )
    )

    requests = runtime_probe_requests.derive_diagnostic_runtime_probe_requests(
        program,
        diagnostic,
    )

    assert len(requests) == 1
    assert requests[0].subject_id == unsupported_id
    assert requests[0].boundary_text == "importlib.import_module(name)"
    assert (
        requests[0].request_id
        == planned_requests_by_subject_id[unsupported_id].request_id
    )
    assert (
        requests[0].status
        is runtime_probe_requests.RuntimeProbeRequestStatus.PLANNED_NOT_EXECUTED
    )


def test_derive_diagnostic_runtime_probe_requests_ignores_runtime_supported_boundary(
    tmp_path: Path,
) -> None:
    """Unsupported boundaries with attached runtime support need no new request."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(name: str) -> None:
                importlib.import_module(name)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)
    unsupported_id = _unsupported_id_for(program, "importlib.import_module(name)")
    diagnostic = _diagnostic_result(
        (
            _diagnostic_boundary(
                unsupported_id,
                boundary_kind=(
                    SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
                ),
                primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
                has_attached_runtime_provenance=True,
            ),
        )
    )

    assert runtime_probe_requests.derive_runtime_probe_requests(program)
    assert (
        runtime_probe_requests.derive_diagnostic_runtime_probe_requests(
            program,
            diagnostic,
        )
        == ()
    )


def test_derive_diagnostic_runtime_probe_requests_ignores_non_attachable_boundary(
    tmp_path: Path,
) -> None:
    """Unsupported diagnostic boundaries without attachable probes are skipped."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> None:
                getattr()
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)
    unsupported_id = _unsupported_id_for(program, "getattr()")
    diagnostic = _diagnostic_result(
        (
            _diagnostic_boundary(
                unsupported_id,
                boundary_kind=(
                    SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
                ),
                primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
            ),
        )
    )

    assert runtime_probe_requests.derive_runtime_probe_requests(program) == ()
    assert (
        runtime_probe_requests.derive_diagnostic_runtime_probe_requests(
            program,
            diagnostic,
        )
        == ()
    )


def test_derive_diagnostic_runtime_probe_requests_is_deterministic_and_pure(
    tmp_path: Path,
) -> None:
    """Diagnostic request derivation keeps planner ordering and mutates nothing."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(obj: object, name: str, source: str) -> None:
                importlib.import_module(name)
                missing_name()
                getattr(obj, name)
                exec(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)
    import_id = _unsupported_id_for(program, "importlib.import_module(name)")
    getattr_id = _unsupported_id_for(program, "getattr(obj, name)")
    exec_id = _unsupported_id_for(program, "exec(source)")
    frontier_id = _frontier_id_for(program, "missing_name")
    symbol_id = _symbol_id_for(program, "main.run")
    diagnostic = _diagnostic_result(
        (
            _diagnostic_boundary(
                frontier_id,
                boundary_kind=(
                    SemanticDiagnosticBoundaryKind.HEURISTIC_FRONTIER_MISSING_RUNTIME_SUPPORT
                ),
                primary_capability_tier=CapabilityTier.HEURISTIC_FRONTIER,
            ),
            _diagnostic_boundary(
                exec_id,
                boundary_kind=(
                    SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
                ),
                primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
            ),
            _diagnostic_boundary(
                symbol_id,
                boundary_kind=SemanticDiagnosticBoundaryKind.STATICALLY_PROVED,
                primary_capability_tier=CapabilityTier.STATICALLY_PROVED,
            ),
            _diagnostic_boundary(
                getattr_id,
                boundary_kind=(
                    SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
                ),
                primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
            ),
            _diagnostic_boundary(
                import_id,
                boundary_kind=(
                    SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
                ),
                primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
            ),
        )
    )
    expected_subject_ids = {import_id, getattr_id, exec_id}
    original_planned_requests = runtime_probe_requests.derive_runtime_probe_requests(
        program
    )
    original_request_ids_by_subject_id = {
        request.subject_id: request.request_id for request in original_planned_requests
    }
    original_unsupported = list(program.unsupported_constructs)
    original_frontier = list(program.unresolved_frontier)
    original_provenance_records = list(program.provenance_records)
    original_diagnostics = list(program.diagnostics)
    original_boundary_classifications = diagnostic.boundary_classifications
    original_grounded_unit_ids = diagnostic.grounded_unit_ids

    first_requests = runtime_probe_requests.derive_diagnostic_runtime_probe_requests(
        program,
        diagnostic,
    )
    second_requests = runtime_probe_requests.derive_diagnostic_runtime_probe_requests(
        program,
        diagnostic,
    )

    assert first_requests == second_requests
    assert [request.request_id for request in first_requests] == [
        original_request_ids_by_subject_id[request.subject_id]
        for request in first_requests
    ]
    assert first_requests == tuple(
        request
        for request in original_planned_requests
        if request.subject_id in expected_subject_ids
    )
    assert [request.boundary_text for request in first_requests] == [
        "importlib.import_module(name)",
        "getattr(obj, name)",
        "exec(source)",
    ]
    assert (
        runtime_probe_requests.derive_runtime_probe_requests(program)
        == original_planned_requests
    )
    assert program.unsupported_constructs == original_unsupported
    assert program.unresolved_frontier == original_frontier
    assert program.provenance_records == original_provenance_records
    assert program.diagnostics == original_diagnostics
    assert diagnostic.boundary_classifications == original_boundary_classifications
    assert diagnostic.grounded_unit_ids == original_grounded_unit_ids

    diagnostic_requests_by_id = (
        runtime_probe_requests.index_runtime_probe_requests_by_id(first_requests)
    )
    assert diagnostic_requests_by_id == {
        request.request_id: request for request in first_requests
    }
    assert list(diagnostic_requests_by_id) == [
        request.request_id for request in first_requests
    ]
    assert set(diagnostic_requests_by_id) == {
        original_request_ids_by_subject_id[request.subject_id]
        for request in first_requests
    }


def test_build_runtime_probe_request_plan_wraps_diagnostic_filtered_requests_purely(
    tmp_path: Path,
) -> None:
    """Diagnostic-filtered request plans keep request IDs, ordering, and inputs."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(obj: object, name: str, source: str) -> None:
                importlib.import_module(name)
                getattr(obj, name)
                exec(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)
    import_id = _unsupported_id_for(program, "importlib.import_module(name)")
    exec_id = _unsupported_id_for(program, "exec(source)")
    diagnostic = _diagnostic_result(
        (
            _diagnostic_boundary(
                exec_id,
                boundary_kind=(
                    SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
                ),
                primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
            ),
            _diagnostic_boundary(
                import_id,
                boundary_kind=(
                    SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
                ),
                primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
            ),
        )
    )
    original_unsupported = list(program.unsupported_constructs)
    original_frontier = list(program.unresolved_frontier)
    original_provenance_records = list(program.provenance_records)
    original_diagnostics = list(program.diagnostics)
    original_boundary_classifications = diagnostic.boundary_classifications
    original_grounded_unit_ids = diagnostic.grounded_unit_ids

    requests = runtime_probe_requests.derive_diagnostic_runtime_probe_requests(
        program,
        diagnostic,
    )
    original_request_ids = tuple(request.request_id for request in requests)
    plan = runtime_probe_requests.build_runtime_probe_request_plan(requests)

    assert plan.requests == requests
    assert plan.request_ids == original_request_ids
    assert plan.plan_id == _expected_plan_id(plan)
    assert [request.boundary_text for request in plan.requests] == [
        "importlib.import_module(name)",
        "exec(source)",
    ]
    assert all(
        plan_request is request
        for plan_request, request in zip(plan.requests, requests, strict=True)
    )
    assert tuple(request.request_id for request in requests) == original_request_ids
    assert program.unsupported_constructs == original_unsupported
    assert program.unresolved_frontier == original_frontier
    assert program.provenance_records == original_provenance_records
    assert program.diagnostics == original_diagnostics
    assert diagnostic.boundary_classifications == original_boundary_classifications
    assert diagnostic.grounded_unit_ids == original_grounded_unit_ids
