"""Public analyzer tests for the semantic-first pipeline."""

from __future__ import annotations

import textwrap
from pathlib import Path

import context_ir
import context_ir.analyzer as analyzer_module
import context_ir.runtime_acquisition as runtime_acquisition
import context_ir.semantic_types as semantic_types
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_types import (
    ReferenceContext,
    SemanticDependencyKind,
    SemanticProgram,
    SyntaxDiagnosticCode,
    SyntaxProgram,
    UnresolvedReasonCode,
)


def _manual_pipeline(repo_root: Path) -> SemanticProgram:
    """Run the accepted lower-layer semantic pipeline manually."""
    syntax = extract_syntax(repo_root)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


def _definition_id_for(program: SemanticProgram, qualified_name: str) -> str:
    """Return the unique syntax definition ID for ``qualified_name``."""
    return next(
        definition.definition_id
        for definition in program.syntax.definitions
        if definition.qualified_name == qualified_name
    )


def _dynamic_import_runtime_observation(
    site,
) -> runtime_acquisition.DynamicImportRuntimeObservation:
    """Create one admissible dynamic-import runtime observation for analyzer tests."""
    return runtime_acquisition.DynamicImportRuntimeObservation(
        site=site,
        probe_identifier="probe:dynamic-import",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=semantic_types.RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
        ),
        attachment_links=(
            semantic_types.RuntimeAttachmentLink(
                attachment_id="attachment:dynamic-import:trace",
                attachment_role="trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="imported_module",
                value="pkg.dynamic",
            ),
        ),
    )


def _hasattr_runtime_observation(
    site,
) -> runtime_acquisition.HasattrRuntimeObservation:
    """Create one admissible ``hasattr`` runtime observation for analyzer tests."""
    return runtime_acquisition.HasattrRuntimeObservation(
        site=site,
        probe_identifier="probe:hasattr",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=semantic_types.RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
        ),
        attachment_links=(
            semantic_types.RuntimeAttachmentLink(
                attachment_id="attachment:hasattr:trace",
                attachment_role="trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="attribute_present",
                value="true",
            ),
        ),
    )


def _getattr_runtime_observation(
    site,
    *,
    lookup_outcome: str = "returned_value",
) -> runtime_acquisition.GetattrRuntimeObservation:
    """Create one admissible ``getattr`` runtime observation for analyzer tests."""
    return runtime_acquisition.GetattrRuntimeObservation(
        site=site,
        probe_identifier="probe:getattr",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=semantic_types.RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
        ),
        attachment_links=(
            semantic_types.RuntimeAttachmentLink(
                attachment_id="attachment:getattr:trace",
                attachment_role="trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="lookup_outcome",
                value=lookup_outcome,
            ),
        ),
    )


def _vars_runtime_observation(
    site,
    *,
    lookup_outcome: str = "returned_namespace",
) -> runtime_acquisition.VarsRuntimeObservation:
    """Create one admissible ``vars`` runtime observation for analyzer tests."""
    return runtime_acquisition.VarsRuntimeObservation(
        site=site,
        probe_identifier="probe:vars",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=semantic_types.RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
        ),
        attachment_links=(
            semantic_types.RuntimeAttachmentLink(
                attachment_id="attachment:vars:trace",
                attachment_role="trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="lookup_outcome",
                value=lookup_outcome,
            ),
        ),
    )


def test_analyze_repository_matches_manual_pipeline(tmp_path: Path) -> None:
    """The analyzer is exactly the accepted semantic-first pipeline."""
    (tmp_path / "helpers.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from helpers import helper

            def run() -> None:
                helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    analyzed_program = analyzer_module.analyze_repository(tmp_path)
    manual_program = _manual_pipeline(tmp_path)

    assert isinstance(analyzed_program, SemanticProgram)
    assert analyzed_program == manual_program
    assert isinstance(analyzed_program.syntax, SyntaxProgram)
    assert analyzed_program.syntax.repo_root == tmp_path
    assert analyzed_program.provenance_records == []


def test_analyze_repository_import_paths_accept_path_and_str(
    tmp_path: Path,
) -> None:
    """Package-root and semantic-types imports both expose the analyzer."""
    (tmp_path / "example.py").write_text(
        "def run() -> None:\n    return None\n",
        encoding="utf-8",
    )

    package_program = context_ir.analyze_repository(tmp_path)
    semantic_types_program = semantic_types.analyze_repository(str(tmp_path))

    assert isinstance(package_program, SemanticProgram)
    assert isinstance(semantic_types_program, SemanticProgram)
    assert package_program == semantic_types_program
    assert package_program.provenance_records == []
    assert semantic_types_program.provenance_records == []


def test_analyze_repository_preserves_parse_error_truthfulness(
    tmp_path: Path,
) -> None:
    """Parse-error files stay in syntax inventory but gain no semantic facts."""
    (tmp_path / "good.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text(
        "from good import VALUE\nclass Broken(\n",
        encoding="utf-8",
    )

    program = analyzer_module.analyze_repository(tmp_path)

    assert {"file:good.py", "file:bad.py"}.issubset(program.syntax.source_files)
    assert any(
        diagnostic.code is SyntaxDiagnosticCode.PARSE_ERROR
        and diagnostic.file_id == "file:bad.py"
        for diagnostic in program.syntax.diagnostics
    )
    assert any(
        definition.file_id == "file:bad.py" for definition in program.syntax.definitions
    )
    assert all(
        symbol.file_id != "file:bad.py" for symbol in program.resolved_symbols.values()
    )
    assert all(binding.site.file_path != "bad.py" for binding in program.bindings)
    assert all(
        resolved_import.site.file_path != "bad.py"
        for resolved_import in program.resolved_imports
    )
    assert all(
        resolved_reference.site.file_path != "bad.py"
        for resolved_reference in program.resolved_references
    )
    assert all(
        dependency.evidence_site_id is None
        or "bad.py" not in dependency.evidence_site_id
        for dependency in program.proven_dependencies
    )
    assert all(
        access.site.file_path != "bad.py" for access in program.unresolved_frontier
    )
    assert all(
        construct.site.file_path != "bad.py"
        for construct in program.unsupported_constructs
    )


def test_analyze_repository_returns_derived_semantic_outputs(
    tmp_path: Path,
) -> None:
    """Analyzer output includes binder, resolver, dependency, and frontier facts."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "base.py").write_text("class Base:\n    pass\n", encoding="utf-8")
    (pkg / "decorators.py").write_text(
        "def decorate(value: object) -> object:\n    return value\n",
        encoding="utf-8",
    )
    (pkg / "helpers.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from dataclasses import dataclass
            from pkg.base import Base
            from pkg.decorators import decorate
            from pkg.helpers import helper

            @dataclass
            class User:
                name: str
                count: int = 0

            @decorate
            class Child(Base):
                pass

            def run() -> None:
                helper()
                missing_call()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = analyzer_module.analyze_repository(tmp_path)
    user_id = _definition_id_for(program, "main.User")
    child_id = _definition_id_for(program, "main.Child")
    helper_id = _definition_id_for(program, "pkg.helpers.helper")

    assert user_id in program.resolved_symbols
    assert child_id in program.resolved_symbols
    assert any(binding.name == "helper" for binding in program.bindings)
    assert any(
        resolved_import.bound_name == "Base"
        and resolved_import.target_symbol_id
        == _definition_id_for(program, "pkg.base.Base")
        for resolved_import in program.resolved_imports
    )
    assert {model.class_symbol_id for model in program.dataclass_models} == {user_id}
    assert {
        field.name
        for field in program.dataclass_fields
        if field.class_symbol_id == user_id
    } == {"name", "count"}
    assert any(
        reference.context is ReferenceContext.CALL
        and reference.resolved_symbol_id == helper_id
        for reference in program.resolved_references
    )
    assert {dependency.kind for dependency in program.proven_dependencies}.issuperset(
        {
            SemanticDependencyKind.IMPORT,
            SemanticDependencyKind.CALL,
            SemanticDependencyKind.INHERITANCE,
            SemanticDependencyKind.DECORATOR,
        }
    )
    assert any(
        access.access_text == "missing_call"
        and access.reason_code is UnresolvedReasonCode.UNRESOLVED_NAME
        and access.context is ReferenceContext.CALL
        for access in program.unresolved_frontier
    )
    assert program.provenance_records == []


def test_analyze_repository_only_orchestrates_lower_layers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Analyzer calls each lower layer once and returns the derived program."""
    calls: list[str] = []
    syntax = SyntaxProgram(repo_root=tmp_path)
    bound_program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    resolved_program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    derived_program = SemanticProgram(repo_root=tmp_path, syntax=syntax)

    def fake_extract(repo_root: Path | str) -> SyntaxProgram:
        calls.append(f"extract:{repo_root}")
        return syntax

    def fake_bind(received_syntax: SyntaxProgram) -> SemanticProgram:
        calls.append("bind")
        assert received_syntax is syntax
        return bound_program

    def fake_resolve(received_program: SemanticProgram) -> SemanticProgram:
        calls.append("resolve")
        assert received_program is bound_program
        return resolved_program

    def fake_derive(received_program: SemanticProgram) -> SemanticProgram:
        calls.append("derive")
        assert received_program is resolved_program
        return derived_program

    monkeypatch.setattr(analyzer_module, "extract_syntax", fake_extract)
    monkeypatch.setattr(analyzer_module, "bind_syntax", fake_bind)
    monkeypatch.setattr(analyzer_module, "resolve_semantics", fake_resolve)
    monkeypatch.setattr(
        analyzer_module,
        "derive_dependency_frontier",
        fake_derive,
    )

    result = analyzer_module.analyze_repository(str(tmp_path))

    assert result is derived_program
    assert calls == [f"extract:{tmp_path}", "bind", "resolve", "derive"]
    assert bound_program.proven_dependencies == []
    assert resolved_program.proven_dependencies == []
    assert result.provenance_records == []


def test_analyze_repository_attaches_dynamic_import_runtime_provenance_post_frontier(
    tmp_path: Path,
) -> None:
    """Analyzer adds dynamic-import runtime provenance only after static derivation."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(name: str) -> None:
                importlib.import_module(name)
                __import__(name)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    manual_program = _manual_pipeline(tmp_path)
    observations = [
        _dynamic_import_runtime_observation(construct.site)
        for construct in manual_program.unsupported_constructs
        if construct.construct_text
        in {
            "importlib.import_module(name)",
            "__import__(name)",
        }
    ]

    analyzed_program = analyzer_module.analyze_repository(
        tmp_path,
        dynamic_import_runtime_observations=observations,
    )
    expected_program = runtime_acquisition.attach_dynamic_import_runtime_provenance(
        manual_program,
        observations,
    )

    assert analyzed_program == expected_program
    assert (
        analyzed_program.unsupported_constructs == manual_program.unsupported_constructs
    )
    assert {record.subject_id for record in analyzed_program.provenance_records} == {
        construct.construct_id
        for construct in manual_program.unsupported_constructs
        if construct.construct_text
        in {
            "importlib.import_module(name)",
            "__import__(name)",
        }
    }
    assert len(analyzed_program.provenance_records) == 2


def test_analyze_repository_attaches_hasattr_runtime_provenance_post_frontier(
    tmp_path: Path,
) -> None:
    """Analyzer adds bounded ``hasattr`` runtime provenance after static derivation."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object, name: str) -> None:
                hasattr(obj, name)
                hasattr(obj)
                getattr(obj, name)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    manual_program = _manual_pipeline(tmp_path)
    observations = [
        _hasattr_runtime_observation(construct.site)
        for construct in manual_program.unsupported_constructs
    ]

    analyzed_program = analyzer_module.analyze_repository(
        tmp_path,
        hasattr_runtime_observations=observations,
    )
    expected_program = runtime_acquisition.attach_hasattr_runtime_provenance(
        manual_program,
        observations,
    )

    assert analyzed_program == expected_program
    assert (
        analyzed_program.unsupported_constructs == manual_program.unsupported_constructs
    )
    assert {record.subject_id for record in analyzed_program.provenance_records} == {
        next(
            construct.construct_id
            for construct in manual_program.unsupported_constructs
            if construct.construct_text == "hasattr(obj, name)"
        )
    }
    assert len(analyzed_program.provenance_records) == 1


def test_analyze_repository_attaches_getattr_runtime_provenance_post_frontier(
    tmp_path: Path,
) -> None:
    """Analyzer adds bounded ``getattr`` runtime provenance after static derivation."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object, name: str, default: object) -> None:
                getattr(obj, name)
                getattr(obj, name, default)
                getattr()
                hasattr(obj, name)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    manual_program = _manual_pipeline(tmp_path)
    observations = [
        _getattr_runtime_observation(
            construct.site,
            lookup_outcome=(
                "returned_value"
                if construct.construct_text == "getattr(obj, name)"
                else "returned_default_value"
            ),
        )
        for construct in manual_program.unsupported_constructs
    ]

    analyzed_program = analyzer_module.analyze_repository(
        tmp_path,
        getattr_runtime_observations=observations,
    )
    expected_program = runtime_acquisition.attach_getattr_runtime_provenance(
        manual_program,
        observations,
    )

    assert analyzed_program == expected_program
    assert (
        analyzed_program.unsupported_constructs == manual_program.unsupported_constructs
    )
    assert {record.subject_id for record in analyzed_program.provenance_records} == {
        construct.construct_id
        for construct in manual_program.unsupported_constructs
        if construct.construct_text
        in {"getattr(obj, name)", "getattr(obj, name, default)"}
    }
    assert len(analyzed_program.provenance_records) == 2


def test_analyze_repository_attaches_vars_runtime_provenance_post_frontier(
    tmp_path: Path,
) -> None:
    """Analyzer adds bounded ``vars`` runtime provenance post-frontier."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object) -> None:
                vars(obj)
                vars()
                dir(obj)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    manual_program = _manual_pipeline(tmp_path)
    observations = [
        _vars_runtime_observation(construct.site)
        for construct in manual_program.unsupported_constructs
    ]

    analyzed_program = analyzer_module.analyze_repository(
        tmp_path,
        vars_runtime_observations=observations,
    )
    expected_program = runtime_acquisition.attach_vars_runtime_provenance(
        manual_program,
        observations,
    )

    assert analyzed_program == expected_program
    assert (
        analyzed_program.unsupported_constructs == manual_program.unsupported_constructs
    )
    assert {record.subject_id for record in analyzed_program.provenance_records} == {
        construct.construct_id
        for construct in manual_program.unsupported_constructs
        if construct.construct_text in {"vars(obj)", "vars()"}
    }
    assert len(analyzed_program.provenance_records) == 2
