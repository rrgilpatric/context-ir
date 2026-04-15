"""Dependency/frontier derivation tests for the semantic-first baseline."""

from __future__ import annotations

import textwrap
from pathlib import Path

from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_types import (
    DependencyProofKind,
    ReferenceContext,
    SemanticDependencyKind,
    SemanticProgram,
    UnresolvedReasonCode,
)


def _derived_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted lower layers plus dependency/frontier derivation."""
    syntax = extract_syntax(tmp_path)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


def _resolved_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted lower layers up through resolver output."""
    return resolve_semantics(bind_syntax(extract_syntax(tmp_path)))


def _definition_id_for(
    program: SemanticProgram,
    qualified_name: str,
) -> str:
    """Return the unique definition ID for ``qualified_name``."""
    return next(
        definition.definition_id
        for definition in program.syntax.definitions
        if definition.qualified_name == qualified_name
    )


def test_derive_dependency_frontier_preserves_lower_layer_outputs(
    tmp_path: Path,
) -> None:
    """Dependency/frontier derivation augments rather than reopening prior layers."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def helper() -> None:
                return None

            helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    resolved_program = _resolved_program(tmp_path)
    derived_program = derive_dependency_frontier(resolved_program)

    assert isinstance(derived_program, SemanticProgram)
    assert derived_program.repo_root == resolved_program.repo_root
    assert derived_program.syntax is resolved_program.syntax
    assert derived_program.supported_subset == resolved_program.supported_subset
    assert derived_program.resolved_symbols is resolved_program.resolved_symbols
    assert derived_program.bindings is resolved_program.bindings
    assert derived_program.resolved_imports is resolved_program.resolved_imports
    assert derived_program.dataclass_models is resolved_program.dataclass_models
    assert derived_program.dataclass_fields is resolved_program.dataclass_fields
    assert derived_program.resolved_references is resolved_program.resolved_references
    assert derived_program.diagnostics is resolved_program.diagnostics
    assert {dependency.kind for dependency in derived_program.proven_dependencies} == {
        SemanticDependencyKind.CALL
    }


def test_derive_dependency_frontier_emits_import_dependencies_by_owning_scope(
    tmp_path: Path,
) -> None:
    """Repository-backed imports become dependencies from their owning scope."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "base.py").write_text("class Base:\n    pass\n", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import pkg.helpers as helpers_mod

            class Example:
                from pkg.base import Base as BaseAlias

                def method(self) -> None:
                    from pkg.helpers import helper as local_helper
                    local_helper()

            def run() -> None:
                from pkg.helpers import helper as runner_helper
                runner_helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    import_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.IMPORT
    ]
    dependencies_by_event = {
        dependency.dependency_id: (
            dependency.source_symbol_id,
            dependency.target_symbol_id,
            dependency.proof_kind,
        )
        for dependency in import_dependencies
    }

    assert dependencies_by_event == {
        next(
            dependency.dependency_id
            for dependency in import_dependencies
            if dependency.source_symbol_id
            == _definition_id_for(derived_program, "main")
        ): (
            _definition_id_for(derived_program, "main"),
            _definition_id_for(derived_program, "pkg.helpers"),
            DependencyProofKind.IMPORT_RESOLUTION,
        ),
        next(
            dependency.dependency_id
            for dependency in import_dependencies
            if dependency.source_symbol_id
            == _definition_id_for(derived_program, "main.Example")
        ): (
            _definition_id_for(derived_program, "main.Example"),
            _definition_id_for(derived_program, "pkg.base.Base"),
            DependencyProofKind.IMPORT_RESOLUTION,
        ),
        next(
            dependency.dependency_id
            for dependency in import_dependencies
            if dependency.source_symbol_id
            == _definition_id_for(derived_program, "main.Example.method")
        ): (
            _definition_id_for(derived_program, "main.Example.method"),
            _definition_id_for(derived_program, "pkg.helpers.helper"),
            DependencyProofKind.IMPORT_RESOLUTION,
        ),
        next(
            dependency.dependency_id
            for dependency in import_dependencies
            if dependency.source_symbol_id
            == _definition_id_for(derived_program, "main.run")
        ): (
            _definition_id_for(derived_program, "main.run"),
            _definition_id_for(derived_program, "pkg.helpers.helper"),
            DependencyProofKind.IMPORT_RESOLUTION,
        ),
    }


def test_derive_dependency_frontier_emits_call_base_and_decorator_dependencies(
    tmp_path: Path,
) -> None:
    """Repository-backed resolver proof becomes traced semantic dependencies."""
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
            from dataclasses import dataclass as dc
            from pkg.base import Base
            from pkg.decorators import decorate
            from pkg.helpers import helper

            @dc
            @decorate
            class Child(Base):
                pass

            def run() -> None:
                helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    dependencies = derived_program.proven_dependencies
    dependency_ids = {dependency.dependency_id for dependency in dependencies}
    decorator_dependencies = [
        dependency
        for dependency in dependencies
        if dependency.kind is SemanticDependencyKind.DECORATOR
    ]

    assert len(dependency_ids) == len(dependencies)
    assert any(
        dependency.kind is SemanticDependencyKind.INHERITANCE
        and dependency.proof_kind is DependencyProofKind.BASE_CLASS_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Child")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "pkg.base.Base")
        and dependency.evidence_reference_id is not None
        for dependency in dependencies
    )
    assert any(
        dependency.kind is SemanticDependencyKind.CALL
        and dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "pkg.helpers.helper")
        and dependency.evidence_reference_id is not None
        for dependency in dependencies
    )
    assert len(decorator_dependencies) == 1
    assert decorator_dependencies[0].source_symbol_id == _definition_id_for(
        derived_program,
        "main.Child",
    )
    assert decorator_dependencies[0].target_symbol_id == _definition_id_for(
        derived_program,
        "pkg.decorators.decorate",
    )
    assert all(
        not dependency.target_symbol_id.startswith("import:")
        for dependency in decorator_dependencies
    )


def test_derive_dependency_frontier_surfaces_supported_unresolved_reference_forms(
    tmp_path: Path,
) -> None:
    """Supported simple-name and direct-attribute misses become unresolved frontier."""
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
            import pkg.base as base_mod
            import pkg.decorators as decorators
            import pkg.helpers as helpers

            @missing_decorator
            class MissingDecorator:
                pass

            @decorators.missing
            class MissingDecoratorAttr:
                pass

            class MissingBase(MissingBaseAlias):
                pass

            class MissingBaseAttr(base_mod.MissingBase):
                pass

            def run(self) -> None:
                missing_call()
                helpers.missing()
                self.build()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unresolved_by_text = {
        access.access_text: (
            access.reason_code,
            access.context,
            access.enclosing_scope_id,
        )
        for access in derived_program.unresolved_frontier
    }

    assert unresolved_by_text["missing_decorator"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.DECORATOR,
        _definition_id_for(derived_program, "main"),
    )
    assert unresolved_by_text["decorators.missing"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.DECORATOR,
        _definition_id_for(derived_program, "main"),
    )
    assert unresolved_by_text["MissingBaseAlias"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.BASE_CLASS,
        _definition_id_for(derived_program, "main"),
    )
    assert unresolved_by_text["base_mod.MissingBase"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.BASE_CLASS,
        _definition_id_for(derived_program, "main"),
    )
    assert unresolved_by_text["missing_call"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["helpers.missing"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["self.build"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )


def test_derive_dependency_frontier_surfaces_star_imports_and_unsupported_shapes(
    tmp_path: Path,
) -> None:
    """Out-of-subset star imports and opaque expressions stay explicit."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.helpers import *
            import pkg.helpers

            def wrap(value: object) -> object:
                return value

            def factory() -> type[object]:
                return object

            @wrap(helper)
            class Wrapped:
                pass

            class DynamicBase(factory()):
                pass

            def run() -> None:
                pkg.helpers.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert (
        unsupported_by_text["from pkg.helpers import *"]
        is UnresolvedReasonCode.STAR_IMPORT
    )
    assert unsupported_by_text["wrap(helper)"] is UnresolvedReasonCode.OPAQUE_DECORATOR
    assert (
        unsupported_by_text["factory()"]
        is UnresolvedReasonCode.UNSUPPORTED_BASE_EXPRESSION
    )
    assert (
        unsupported_by_text["pkg.helpers.helper"]
        is UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET
    )


def test_derive_dependency_frontier_skips_parse_error_files(
    tmp_path: Path,
) -> None:
    """Parse-error files do not contribute dependency or frontier facts."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "good.py").write_text(
        "from pkg.helpers import *\n",
        encoding="utf-8",
    )
    (tmp_path / "bad.py").write_text(
        "from pkg.helpers import *\nclass Broken(\n",
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    all_paths = {
        dependency.evidence_site_id
        for dependency in derived_program.proven_dependencies
        if dependency.evidence_site_id is not None
    }
    frontier_paths = {
        access.site.file_path for access in derived_program.unresolved_frontier
    }
    unsupported_paths = {
        construct.site.file_path for construct in derived_program.unsupported_constructs
    }

    assert all("bad.py" not in site_id for site_id in all_paths)
    assert "bad.py" not in frontier_paths
    assert "bad.py" not in unsupported_paths
    assert unsupported_paths == {"good.py"}
