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
    ResolvedSymbolKind,
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


def _resolved_symbol_id_for(
    program: SemanticProgram,
    qualified_name: str,
    *,
    kind: ResolvedSymbolKind | None = None,
) -> str:
    """Return the unique resolved symbol ID for ``qualified_name``."""
    matching_symbol_ids = [
        symbol.symbol_id
        for symbol in program.resolved_symbols.values()
        if symbol.qualified_name == qualified_name
        and (kind is None or symbol.kind is kind)
    ]
    assert len(matching_symbol_ids) == 1
    return matching_symbol_ids[0]


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


def test_derive_dependency_frontier_surfaces_metaclass_keywords_as_unsupported(
    tmp_path: Path,
) -> None:
    """Class metaclass keywords stay explicit as unsupported behavior boundaries."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Base:
                pass

            class Example(Base, metaclass=Meta):
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unsupported_by_text = {
        construct.construct_text: (
            construct.reason_code,
            construct.enclosing_scope_id,
        )
        for construct in derived_program.unsupported_constructs
    }
    inheritance_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.INHERITANCE
    ]

    assert unsupported_by_text["metaclass=Meta"] == (
        UnresolvedReasonCode.METACLASS_BEHAVIOR,
        _definition_id_for(derived_program, "main"),
    )
    assert any(
        dependency.proof_kind is DependencyProofKind.BASE_CLASS_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Example")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.Base")
        for dependency in inheritance_dependencies
    )
    assert all(
        access.access_text != "metaclass=Meta"
        for access in derived_program.unresolved_frontier
    )


def test_derive_dependency_frontier_surfaces_named_dynamic_call_boundaries(
    tmp_path: Path,
) -> None:
    """Named dynamic loaders and code-execution builtins stay explicitly unsupported."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(name: str, source: str) -> None:
                importlib.import_module(name)
                __import__(name)
                exec(source)
                eval(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unresolved_by_text = {
        access.access_text: access.reason_code
        for access in derived_program.unresolved_frontier
    }
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert (
        unsupported_by_text["importlib.import_module(name)"]
        is UnresolvedReasonCode.DYNAMIC_IMPORT
    )
    assert (
        unsupported_by_text["__import__(name)"] is UnresolvedReasonCode.DYNAMIC_IMPORT
    )
    assert unsupported_by_text["exec(source)"] is UnresolvedReasonCode.EXEC_OR_EVAL
    assert unsupported_by_text["eval(source)"] is UnresolvedReasonCode.EXEC_OR_EVAL
    assert "importlib.import_module" not in unresolved_by_text
    assert "__import__" not in unresolved_by_text
    assert "exec" not in unresolved_by_text
    assert "eval" not in unresolved_by_text


def test_derive_dependency_frontier_surfaces_imported_import_module_boundaries(
    tmp_path: Path,
) -> None:
    """Direct imported ``import_module`` names stay explicit dynamic boundaries."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from importlib import import_module
            from importlib import import_module as load_module

            def run(name: str) -> None:
                import_module(name)
                load_module(name)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unresolved_by_text = {
        access.access_text: access.reason_code
        for access in derived_program.unresolved_frontier
    }
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert (
        unsupported_by_text["import_module(name)"]
        is UnresolvedReasonCode.DYNAMIC_IMPORT
    )
    assert (
        unsupported_by_text["load_module(name)"] is UnresolvedReasonCode.DYNAMIC_IMPORT
    )
    assert "import_module" not in unresolved_by_text
    assert "load_module" not in unresolved_by_text


def test_derive_dependency_frontier_surfaces_root_importlib_alias_boundaries(
    tmp_path: Path,
) -> None:
    """Aliased root-module ``importlib`` calls stay explicit dynamic boundaries."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib as loader

            def run(name: str) -> None:
                loader.import_module(name)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unresolved_by_text = {
        access.access_text: access.reason_code
        for access in derived_program.unresolved_frontier
    }
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert (
        unsupported_by_text["loader.import_module(name)"]
        is UnresolvedReasonCode.DYNAMIC_IMPORT
    )
    assert "loader.import_module" not in unresolved_by_text


def test_derive_dependency_frontier_surfaces_runtime_mutation_call_boundaries(
    tmp_path: Path,
) -> None:
    """Named runtime-mutation and reflection builtins stay explicitly unsupported."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object, name: str, value: object) -> None:
                setattr(obj, name, value)
                delattr(obj, name)
                globals()
                locals()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unresolved_by_text = {
        access.access_text: access.reason_code
        for access in derived_program.unresolved_frontier
    }
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert (
        unsupported_by_text["setattr(obj, name, value)"]
        is UnresolvedReasonCode.RUNTIME_MUTATION
    )
    assert (
        unsupported_by_text["delattr(obj, name)"]
        is UnresolvedReasonCode.RUNTIME_MUTATION
    )
    assert unsupported_by_text["globals()"] is UnresolvedReasonCode.RUNTIME_MUTATION
    assert unsupported_by_text["locals()"] is UnresolvedReasonCode.RUNTIME_MUTATION
    assert "setattr" not in unresolved_by_text
    assert "delattr" not in unresolved_by_text
    assert "globals" not in unresolved_by_text
    assert "locals" not in unresolved_by_text


def test_derive_dependency_frontier_surfaces_reflective_builtin_boundaries(
    tmp_path: Path,
) -> None:
    """Reflective builtin calls stay explicit unsupported reflection boundaries."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object, name: str) -> None:
                getattr(obj, name)
                hasattr(obj, name)
                vars(obj)
                vars()
                dir(obj)
                dir()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unresolved_by_text = {
        access.access_text: access.reason_code
        for access in derived_program.unresolved_frontier
    }
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert (
        unsupported_by_text["getattr(obj, name)"]
        is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    )
    assert (
        unsupported_by_text["hasattr(obj, name)"]
        is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    )
    assert unsupported_by_text["vars(obj)"] is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    assert unsupported_by_text["vars()"] is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    assert unsupported_by_text["dir(obj)"] is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    assert unsupported_by_text["dir()"] is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    assert "getattr" not in unresolved_by_text
    assert "hasattr" not in unresolved_by_text
    assert "vars" not in unresolved_by_text
    assert "dir" not in unresolved_by_text


def test_derive_dependency_frontier_treats_importlib_submodule_alias_as_generic_call(
    tmp_path: Path,
) -> None:
    """Aliased ``importlib`` submodules do not trigger the root-module dynamic rule."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib.metadata as importlib

            def run(name: str) -> None:
                importlib.import_module(name)
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
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert unresolved_by_text["importlib.import_module"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert "importlib.import_module(name)" not in unsupported_by_text


def test_derive_dependency_frontier_keeps_importlib_submodule_loader_alias_generic(
    tmp_path: Path,
) -> None:
    """Aliased ``importlib`` submodules stay on the generic path for loader names."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib.metadata as loader

            def run(name: str) -> None:
                loader.import_module(name)
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
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert unresolved_by_text["loader.import_module"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert "loader.import_module(name)" not in unsupported_by_text


def test_derive_dependency_frontier_preserves_shadowed_dynamic_call_names(
    tmp_path: Path,
) -> None:
    """Local rebinding keeps dynamic-looking names on the generic frontier path."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(loader: object) -> None:
                exec = loader
                eval = loader
                __import__ = loader
                importlib = loader
                exec()
                eval()
                __import__()
                importlib.import_module()
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
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert unresolved_by_text["exec"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["eval"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["__import__"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["importlib.import_module"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert "exec()" not in unsupported_by_text
    assert "eval()" not in unsupported_by_text
    assert "__import__()" not in unsupported_by_text
    assert "importlib.import_module()" not in unsupported_by_text


def test_derive_dependency_frontier_preserves_shadowed_importlib_root_alias_names(
    tmp_path: Path,
) -> None:
    """Local rebinding keeps aliased root-module names on the generic frontier path."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib as loader

            def run(value: object) -> None:
                loader = value
                loader.import_module()
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
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert unresolved_by_text["loader.import_module"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert "loader.import_module()" not in unsupported_by_text


def test_derive_dependency_frontier_preserves_shadowed_import_module_names(
    tmp_path: Path,
) -> None:
    """Local rebinding keeps imported ``import_module``-looking names generic."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from importlib import import_module
            from importlib import import_module as load_module

            def run(loader: object) -> None:
                import_module = loader
                load_module = loader
                import_module()
                load_module()
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
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert unresolved_by_text["import_module"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["load_module"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert "import_module()" not in unsupported_by_text
    assert "load_module()" not in unsupported_by_text


def test_derive_dependency_frontier_preserves_shadowed_runtime_mutation_names(
    tmp_path: Path,
) -> None:
    """Local rebinding keeps runtime-mutation builtin names on the generic path."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(loader: object) -> None:
                setattr = loader
                delattr = loader
                globals = loader
                locals = loader
                setattr()
                delattr()
                globals()
                locals()
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
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert unresolved_by_text["setattr"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["delattr"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["globals"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["locals"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert "setattr()" not in unsupported_by_text
    assert "delattr()" not in unsupported_by_text
    assert "globals()" not in unsupported_by_text
    assert "locals()" not in unsupported_by_text


def test_derive_dependency_frontier_preserves_shadowed_reflective_builtin_names(
    tmp_path: Path,
) -> None:
    """Local rebinding keeps reflective builtin names on the generic path."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(loader: object) -> None:
                getattr = loader
                hasattr = loader
                vars = loader
                dir = loader
                getattr()
                hasattr()
                vars()
                dir()
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
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert unresolved_by_text["getattr"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["hasattr"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["vars"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["dir"] == (
        UnresolvedReasonCode.UNRESOLVED_NAME,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert "getattr()" not in unsupported_by_text
    assert "hasattr()" not in unsupported_by_text
    assert "vars()" not in unsupported_by_text
    assert "dir()" not in unsupported_by_text


def test_derive_dependency_frontier_uses_same_class_self_call_proof_narrowly(
    tmp_path: Path,
) -> None:
    """Proven same-class ``self.foo()`` calls leave only non-proof frontier cases."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                def run(self) -> None:
                    self.build()
                    self.missing()

                def weird(cls) -> None:
                    cls.build()

                def other(self, helper: "Example") -> None:
                    helper.build()

                def build(self) -> None:
                    return None

            class Decorated:
                @staticmethod
                def helper() -> None:
                    return None

                def run(self) -> None:
                    self.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_text = {
        access.access_text: (
            access.reason_code,
            access.context,
            access.enclosing_scope_id,
        )
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Example.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.Example.build")
        for dependency in call_dependencies
    )
    assert "self.build" not in unresolved_by_text
    assert unresolved_by_text["self.missing"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.Example.run"),
    )
    assert unresolved_by_text["cls.build"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.Example.weird"),
    )
    assert unresolved_by_text["helper.build"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.Example.other"),
    )
    assert unresolved_by_text["self.helper"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.Decorated.run"),
    )


def test_derive_dependency_frontier_classifies_hooked_self_calls_as_unsupported(
    tmp_path: Path,
) -> None:
    """Hook-affected unresolved same-class ``self.foo()`` calls become unsupported."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Plain:
                def run(self) -> None:
                    self.build_plain()

                def build_plain(self) -> None:
                    return None

            class Hooked:
                def __getattribute__(self, name: str) -> object:
                    return object()

                def run(self) -> None:
                    self.build_hooked()
                    self.__getattribute__("build_hooked")

                def build_hooked(self) -> None:
                    return None

            class GetattrHooked:
                def __getattr__(self, name: str) -> object:
                    return object()

                def run(self) -> None:
                    self.missing_hooked()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_text = {
        access.access_text: (
            access.reason_code,
            access.context,
            access.enclosing_scope_id,
        )
        for access in derived_program.unresolved_frontier
    }
    unsupported_by_text = {
        construct.construct_text: (
            construct.reason_code,
            construct.enclosing_scope_id,
        )
        for construct in derived_program.unsupported_constructs
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Plain.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.Plain.build_plain")
        for dependency in call_dependencies
    )
    assert not any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Hooked.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.Hooked.build_hooked")
        for dependency in call_dependencies
    )
    assert unsupported_by_text["self.build_hooked"] == (
        UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET,
        _definition_id_for(derived_program, "main.Hooked.run"),
    )
    assert unsupported_by_text["self.missing_hooked"] == (
        UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET,
        _definition_id_for(derived_program, "main.GetattrHooked.run"),
    )
    assert unresolved_by_text["self.__getattribute__"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.Hooked.run"),
    )
    assert "self.build_hooked" not in unresolved_by_text
    assert "self.missing_hooked" not in unresolved_by_text
    assert "self.build_plain" not in unresolved_by_text


def test_derive_dependency_frontier_classifies_direct_base_self_calls_as_unsupported(
    tmp_path: Path,
) -> None:
    """Direct-base inherited self hooks make unresolved calls unsupported."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class PlainBase:
                pass

            class GetattrBase:
                def __getattr__(self, name: str) -> object:
                    return object()

            class GetattributeBase:
                def __getattribute__(self, name: str) -> object:
                    return object()

            class PlainChild(PlainBase):
                def run(self) -> None:
                    self.build_plain()

                def build_plain(self) -> None:
                    return None

            class GetattributeChild(PlainBase, GetattributeBase):
                def run(self) -> None:
                    self.build_from_getattribute_base()

                def build_from_getattribute_base(self) -> None:
                    return None

            class GetattrChild(GetattrBase):
                def run(self) -> None:
                    self.missing_from_getattr_base()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_text = {
        access.access_text: (
            access.reason_code,
            access.context,
            access.enclosing_scope_id,
        )
        for access in derived_program.unresolved_frontier
    }
    unsupported_by_text = {
        construct.construct_text: (
            construct.reason_code,
            construct.enclosing_scope_id,
        )
        for construct in derived_program.unsupported_constructs
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.PlainChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.PlainChild.build_plain")
        for dependency in call_dependencies
    )
    assert not any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.GetattributeChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(
            derived_program,
            "main.GetattributeChild.build_from_getattribute_base",
        )
        for dependency in call_dependencies
    )
    assert unsupported_by_text["self.build_from_getattribute_base"] == (
        UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET,
        _definition_id_for(derived_program, "main.GetattributeChild.run"),
    )
    assert unsupported_by_text["self.missing_from_getattr_base"] == (
        UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET,
        _definition_id_for(derived_program, "main.GetattrChild.run"),
    )
    assert "self.build_from_getattribute_base" not in unresolved_by_text
    assert "self.missing_from_getattr_base" not in unresolved_by_text
    assert "self.build_plain" not in unresolved_by_text


def test_dependency_frontier_classifies_transitive_self_calls_as_unsupported(
    tmp_path: Path,
) -> None:
    """Transitively hooked ancestors reroute unresolved self calls to unsupported."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class HookedGrandparent:
                def __getattribute__(self, name: str) -> object:
                    return object()

            class PlainIntermediate(HookedGrandparent):
                pass

            class LinearSameClassChild(PlainIntermediate):
                def run(self) -> None:
                    self.build_linear()

                def build_linear(self) -> None:
                    return None

            class LinearProvider(HookedGrandparent):
                def inherited_linear(self) -> None:
                    return None

            class LinearInheritedChild(LinearProvider):
                def run(self) -> None:
                    self.inherited_linear()

            class PlainDirectBase:
                pass

            class HookedBridge(HookedGrandparent):
                pass

            class MixedSameClassChild(PlainDirectBase, HookedBridge):
                def run(self) -> None:
                    self.build_mixed()

                def build_mixed(self) -> None:
                    return None

            class MixedProvider(HookedBridge):
                def inherited_mixed(self) -> None:
                    return None

            class MixedInheritedChild(PlainDirectBase, MixedProvider):
                def run(self) -> None:
                    self.inherited_mixed()

            class GetattrGrandparent:
                def __getattr__(self, name: str) -> object:
                    return object()

            class GetattrBridge(GetattrGrandparent):
                pass

            class GetattrMixedChild(PlainDirectBase, GetattrBridge):
                def run(self) -> None:
                    self.missing_getattr_mixed()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }
    unsupported_by_scope_and_text = {
        (construct.enclosing_scope_id, construct.construct_text): construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert not any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.LinearSameClassChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.LinearSameClassChild.build_linear")
        for dependency in call_dependencies
    )
    assert not any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.LinearInheritedChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.LinearProvider.inherited_linear")
        for dependency in call_dependencies
    )
    assert not any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.MixedSameClassChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.MixedSameClassChild.build_mixed")
        for dependency in call_dependencies
    )
    assert not any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.MixedInheritedChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.MixedProvider.inherited_mixed")
        for dependency in call_dependencies
    )
    assert not any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.GetattrMixedChild.run")
        for dependency in call_dependencies
    )
    assert (
        unsupported_by_scope_and_text[
            (
                _definition_id_for(derived_program, "main.LinearSameClassChild.run"),
                "self.build_linear",
            )
        ]
        == UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET
    )
    assert (
        unsupported_by_scope_and_text[
            (
                _definition_id_for(derived_program, "main.LinearInheritedChild.run"),
                "self.inherited_linear",
            )
        ]
        == UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET
    )
    assert (
        unsupported_by_scope_and_text[
            (
                _definition_id_for(derived_program, "main.MixedSameClassChild.run"),
                "self.build_mixed",
            )
        ]
        == UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET
    )
    assert (
        unsupported_by_scope_and_text[
            (
                _definition_id_for(derived_program, "main.MixedInheritedChild.run"),
                "self.inherited_mixed",
            )
        ]
        == UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET
    )
    assert (
        unsupported_by_scope_and_text[
            (
                _definition_id_for(derived_program, "main.GetattrMixedChild.run"),
                "self.missing_getattr_mixed",
            )
        ]
        == UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET
    )
    assert (
        _definition_id_for(derived_program, "main.LinearSameClassChild.run"),
        "self.build_linear",
    ) not in unresolved_by_scope_and_text
    assert (
        _definition_id_for(derived_program, "main.LinearInheritedChild.run"),
        "self.inherited_linear",
    ) not in unresolved_by_scope_and_text
    assert (
        _definition_id_for(derived_program, "main.MixedSameClassChild.run"),
        "self.build_mixed",
    ) not in unresolved_by_scope_and_text
    assert (
        _definition_id_for(derived_program, "main.MixedInheritedChild.run"),
        "self.inherited_mixed",
    ) not in unresolved_by_scope_and_text
    assert (
        _definition_id_for(derived_program, "main.GetattrMixedChild.run"),
        "self.missing_getattr_mixed",
    ) not in unresolved_by_scope_and_text


def test_derive_dependency_frontier_proves_narrow_direct_base_self_calls(
    tmp_path: Path,
) -> None:
    """Unique direct-base inherited ``self.foo()`` proof becomes a call dependency."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Base:
                def build(self) -> None:
                    return None

            class Child(Base):
                def run(self) -> None:
                    self.build()

            class OverrideChild(Base):
                def run(self) -> None:
                    self.build()

                def build(self) -> None:
                    return None

            class LeftBase:
                def shared(self) -> None:
                    return None

            class RightBase:
                def shared(self) -> None:
                    return None

            class AmbiguousChild(LeftBase, RightBase):
                def run(self) -> None:
                    self.shared()

            class DecoratedBase:
                @staticmethod
                def helper() -> None:
                    return None

            class DecoratedChild(DecoratedBase):
                def run(self) -> None:
                    self.helper()

            class ShadowBase:
                def helper(self) -> None:
                    return None

            class ShadowChild(ShadowBase):
                @staticmethod
                def helper() -> None:
                    return None

                def run(self) -> None:
                    self.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Child.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.Base.build")
        for dependency in call_dependencies
    )
    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.OverrideChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.OverrideChild.build")
        for dependency in call_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.Child.run"),
        "self.build",
    ) not in unresolved_by_scope_and_text
    assert (
        _definition_id_for(derived_program, "main.OverrideChild.run"),
        "self.build",
    ) not in unresolved_by_scope_and_text
    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.AmbiguousChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.LeftBase.shared")
        for dependency in call_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.AmbiguousChild.run"),
        "self.shared",
    ) not in unresolved_by_scope_and_text
    assert unresolved_by_scope_and_text[
        (_definition_id_for(derived_program, "main.DecoratedChild.run"), "self.helper")
    ] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
    )
    assert unresolved_by_scope_and_text[
        (_definition_id_for(derived_program, "main.ShadowChild.run"), "self.helper")
    ] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
    )


def test_derive_dependency_frontier_proves_transitive_sole_provider_self_calls(
    tmp_path: Path,
) -> None:
    """Transitive sole-provider inherited self calls become call dependencies."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class LinearGrandparent:
                def inherited_linear(self) -> None:
                    return None

            class LinearParent(LinearGrandparent):
                pass

            class LinearChild(LinearParent):
                def run(self) -> None:
                    self.inherited_linear()

            class BranchProvider:
                def inherited_branch(self) -> None:
                    return None

            class BranchBridge(BranchProvider):
                pass

            class OtherBranch:
                pass

            class BranchChild(BranchBridge, OtherBranch):
                def run(self) -> None:
                    self.inherited_branch()

            class LeftProvider:
                def ambiguous(self) -> None:
                    return None

            class LeftBridge(LeftProvider):
                pass

            class RightProvider:
                def ambiguous(self) -> None:
                    return None

            class RightBridge(RightProvider):
                pass

            class AmbiguousChild(LeftBridge, RightBridge):
                def run(self) -> None:
                    self.ambiguous()

            class FarProvider:
                def blocked(self) -> None:
                    return None

            class DecoratedBridge(FarProvider):
                @staticmethod
                def blocked() -> None:
                    return None

            class DecoratedChild(DecoratedBridge):
                def run(self) -> None:
                    self.blocked()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.LinearChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(
            derived_program,
            "main.LinearGrandparent.inherited_linear",
        )
        for dependency in call_dependencies
    )
    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.BranchChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.BranchProvider.inherited_branch")
        for dependency in call_dependencies
    )
    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.AmbiguousChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.LeftProvider.ambiguous")
        for dependency in call_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.AmbiguousChild.run"),
        "self.ambiguous",
    ) not in unresolved_by_scope_and_text
    assert unresolved_by_scope_and_text[
        (
            _definition_id_for(derived_program, "main.DecoratedChild.run"),
            "self.blocked",
        )
    ] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
    )


def test_derive_dependency_frontier_proves_linear_self_calls_to_nearest_owner(
    tmp_path: Path,
) -> None:
    """Linear single-chain inherited self calls become nearest-owner dependencies."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class FarProvider:
                def inherited_linear(self) -> None:
                    return None

            class NearProvider(FarProvider):
                def inherited_linear(self) -> None:
                    return None

            class LinearBridge(NearProvider):
                pass

            class LinearChild(LinearBridge):
                def run(self) -> None:
                    self.inherited_linear()

            class LeftFarProvider:
                def branched(self) -> None:
                    return None

            class LeftNearProvider(LeftFarProvider):
                def branched(self) -> None:
                    return None

            class LeftBridge(LeftNearProvider):
                pass

            class RightFarProvider:
                def branched(self) -> None:
                    return None

            class RightMiddle(RightFarProvider):
                pass

            class RightBridge(RightMiddle):
                pass

            class BranchedChild(LeftBridge, RightBridge):
                def run(self) -> None:
                    self.branched()

            class BlockedFarProvider:
                def blocked(self) -> None:
                    return None

            class BlockedNearProvider(BlockedFarProvider):
                @staticmethod
                def blocked() -> None:
                    return None

            class BlockedBridge(BlockedNearProvider):
                pass

            class BlockedChild(BlockedBridge):
                def run(self) -> None:
                    self.blocked()

            class ShadowedFarProvider:
                def shadowed(self) -> None:
                    return None

            class ShadowedNearProvider(ShadowedFarProvider):
                shadowed = 1

            class ShadowedBridge(ShadowedNearProvider):
                pass

            class ShadowedChild(ShadowedBridge):
                def run(self) -> None:
                    self.shadowed()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.LinearChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.NearProvider.inherited_linear")
        for dependency in call_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.LinearChild.run"),
        "self.inherited_linear",
    ) not in unresolved_by_scope_and_text
    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.BranchedChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.LeftNearProvider.branched")
        for dependency in call_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.BranchedChild.run"),
        "self.branched",
    ) not in unresolved_by_scope_and_text
    assert unresolved_by_scope_and_text[
        (_definition_id_for(derived_program, "main.BlockedChild.run"), "self.blocked")
    ] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
    )
    assert unresolved_by_scope_and_text[
        (_definition_id_for(derived_program, "main.ShadowedChild.run"), "self.shadowed")
    ] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
    )


def test_derive_dependency_frontier_proves_branched_self_calls_by_declared_base_order(
    tmp_path: Path,
) -> None:
    """Declared base order on linear branches becomes a call dependency."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class LeftProvider:
                def preferred(self) -> None:
                    return None

            class LeftBridge(LeftProvider):
                pass

            class RightProvider:
                def preferred(self) -> None:
                    return None

            class RightBridge(RightProvider):
                pass

            class PreferredChild(LeftBridge, RightBridge):
                def run(self) -> None:
                    self.preferred()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.PreferredChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.LeftProvider.preferred")
        for dependency in call_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.PreferredChild.run"),
        "self.preferred",
    ) not in unresolved_by_scope_and_text


def test_derive_dependency_frontier_prefers_earlier_transitive_over_later_direct_base(
    tmp_path: Path,
) -> None:
    """Earlier transitive branch owners produce the call dependency."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class LeftFarProvider:
                def helper(self) -> None:
                    return None

            class LeftBridge(LeftFarProvider):
                pass

            class RightNearProvider:
                def helper(self) -> None:
                    return None

            class Child(LeftBridge, RightNearProvider):
                def run(self) -> None:
                    self.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Child.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.LeftFarProvider.helper")
        for dependency in call_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.Child.run"),
        "self.helper",
    ) not in unresolved_by_scope_and_text


def test_derive_dependency_frontier_proves_overlapping_shared_ancestor_sole_providers(
    tmp_path: Path,
) -> None:
    """Shared non-direct sole providers become call dependencies across overlap."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class DiamondSharedProvider:
                def helper(self) -> None:
                    return None

            class LeftDiamondBridge(DiamondSharedProvider):
                pass

            class RightDiamondBridge(DiamondSharedProvider):
                pass

            class DiamondChild(LeftDiamondBridge, RightDiamondBridge):
                def run(self) -> None:
                    self.helper()

            class OverlapSharedProvider:
                def helper(self) -> None:
                    return None

            class LeftOverlapBridge(OverlapSharedProvider):
                pass

            class RightSharedBridge(OverlapSharedProvider):
                pass

            class RightOverlapBridge(RightSharedBridge):
                pass

            class OverlapChild(LeftOverlapBridge, RightOverlapBridge):
                def run(self) -> None:
                    self.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.DiamondChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.DiamondSharedProvider.helper")
        for dependency in call_dependencies
    )
    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.OverlapChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.OverlapSharedProvider.helper")
        for dependency in call_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.DiamondChild.run"),
        "self.helper",
    ) not in unresolved_by_scope_and_text
    assert (
        _definition_id_for(derived_program, "main.OverlapChild.run"),
        "self.helper",
    ) not in unresolved_by_scope_and_text


def test_derive_dependency_frontier_proves_later_owner_overlap_when_earlier_silent(
    tmp_path: Path,
) -> None:
    """A later overlap owner becomes the call dependency.

    Earlier overlap branches must stay silent.
    """
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class SharedProvider:
                def helper(self) -> None:
                    return None

            class LeftDiamondBridge(SharedProvider):
                pass

            class RightDiamondBridge(SharedProvider):
                def helper(self) -> None:
                    return None

            class Child(LeftDiamondBridge, RightDiamondBridge):
                def run(self) -> None:
                    self.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Child.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.RightDiamondBridge.helper")
        for dependency in call_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.Child.run"),
        "self.helper",
    ) not in unresolved_by_scope_and_text


def test_derive_dependency_frontier_proves_overlap_multi_owner_to_first_exclusive_owner(
    tmp_path: Path,
) -> None:
    """Declared-order exclusive overlap owners become the call dependency."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class SharedTop:
                pass

            class LeftOwner(SharedTop):
                def helper(self) -> None:
                    return None

            class LeftBridge(LeftOwner):
                pass

            class RightOwner(SharedTop):
                def helper(self) -> None:
                    return None

            class Child(LeftBridge, RightOwner):
                def run(self) -> None:
                    self.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Child.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.LeftOwner.helper")
        for dependency in call_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.Child.run"),
        "self.helper",
    ) not in unresolved_by_scope_and_text


def test_derive_dependency_frontier_proves_three_branch_overlap_first_exclusive_owner(
    tmp_path: Path,
) -> None:
    """The first declared exclusive owner becomes the three-branch dependency."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Shared:
                def helper(self) -> None:
                    return None

            class FirstSilent(Shared):
                pass

            class SecondOwner(Shared):
                def helper(self) -> None:
                    return None

            class ThirdOwner(Shared):
                def helper(self) -> None:
                    return None

            class Child(FirstSilent, SecondOwner, ThirdOwner):
                def run(self) -> None:
                    self.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Child.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.SecondOwner.helper")
        for dependency in call_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.Child.run"),
        "self.helper",
    ) not in unresolved_by_scope_and_text


def test_derive_dependency_frontier_leaves_earlier_ineligible_overlap_unresolved(
    tmp_path: Path,
) -> None:
    """An earlier ineligible overlap owner keeps the later branch unresolved."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class SharedTop:
                pass

            class LeftBlocked(SharedTop):
                @staticmethod
                def helper() -> None:
                    return None

            class LeftBridge(LeftBlocked):
                pass

            class RightOwner(SharedTop):
                def helper(self) -> None:
                    return None

            class Child(LeftBridge, RightOwner):
                def run(self) -> None:
                    self.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }

    blocked_scope_and_text = {
        (_definition_id_for(derived_program, "main.Child.run"), "self.helper")
    }
    blocked_scope_ids = {scope_id for scope_id, _ in blocked_scope_and_text}

    assert blocked_scope_and_text <= unresolved_by_scope_and_text.keys()
    assert all(
        unresolved_by_scope_and_text[scope_and_text]
        == (
            UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
            ReferenceContext.CALL,
        )
        for scope_and_text in blocked_scope_and_text
    )
    assert not any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id in blocked_scope_ids
        for dependency in call_dependencies
    )


def test_derive_dependency_frontier_leaves_non_linear_overlap_unresolved(
    tmp_path: Path,
) -> None:
    """Non-linear overlap branches stay on the unresolved path."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Shared:
                def helper(self) -> None:
                    return None

            class ForkLeft:
                pass

            class ForkRight:
                pass

            class NonLinearBranch(ForkLeft, ForkRight):
                pass

            class Left(Shared):
                pass

            class Child(NonLinearBranch, Left):
                def run(self) -> None:
                    self.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }

    blocked_scope_and_text = {
        (_definition_id_for(derived_program, "main.Child.run"), "self.helper")
    }
    blocked_scope_ids = {scope_id for scope_id, _ in blocked_scope_and_text}

    assert blocked_scope_and_text <= unresolved_by_scope_and_text.keys()
    assert all(
        unresolved_by_scope_and_text[scope_and_text]
        == (
            UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
            ReferenceContext.CALL,
        )
        for scope_and_text in blocked_scope_and_text
    )
    assert not any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id in blocked_scope_ids
        for dependency in call_dependencies
    )


def test_derive_dependency_frontier_blocks_earlier_shadowed_self_calls(
    tmp_path: Path,
) -> None:
    """Earlier class-scope shadowing keeps blocked ``self.foo()`` calls unresolved."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class SameClassRebound:
                def helper(self) -> None:
                    return None

                helper = 1

                def run(self) -> None:
                    self.helper()

            class DirectBaseProvider:
                def helper(self) -> None:
                    return None

            class DirectBaseShadowChild(DirectBaseProvider):
                helper = 1

                def run(self) -> None:
                    self.helper()

            class CompetingDirectBaseProvider:
                def helper(self) -> None:
                    return None

            class CompetingDirectBaseShadow:
                helper = 1

            class CompetingDirectBaseChild(
                CompetingDirectBaseProvider,
                CompetingDirectBaseShadow,
            ):
                def run(self) -> None:
                    self.helper()

            class TransitiveProvider:
                def helper(self) -> None:
                    return None

            class IntermediateShadow(TransitiveProvider):
                helper = 1

            class IntermediateShadowChild(IntermediateShadow):
                def run(self) -> None:
                    self.helper()

            class BranchProvider:
                def helper(self) -> None:
                    return None

            class BranchBridge(BranchProvider):
                pass

            class OtherBranchShadowGrandparent:
                helper = 1

            class OtherBranch(OtherBranchShadowGrandparent):
                pass

            class BranchShadowChild(BranchBridge, OtherBranch):
                def run(self) -> None:
                    self.helper()

            class ProviderRebound:
                def helper(self) -> None:
                    return None

                helper = 1

            class ProviderBridge(ProviderRebound):
                pass

            class ProviderReboundChild(ProviderBridge):
                def run(self) -> None:
                    self.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_by_scope_and_text = {
        (access.enclosing_scope_id, access.access_text): (
            access.reason_code,
            access.context,
        )
        for access in derived_program.unresolved_frontier
    }
    unsupported_by_scope_and_text = {
        (construct.enclosing_scope_id, construct.construct_text): construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.CompetingDirectBaseChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(
            derived_program,
            "main.CompetingDirectBaseProvider.helper",
        )
        for dependency in call_dependencies
    )
    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.BranchShadowChild.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "main.BranchProvider.helper")
        for dependency in call_dependencies
    )

    blocked_scope_and_text = {
        (
            _definition_id_for(derived_program, "main.SameClassRebound.run"),
            "self.helper",
        ),
        (
            _definition_id_for(derived_program, "main.DirectBaseShadowChild.run"),
            "self.helper",
        ),
        (
            _definition_id_for(derived_program, "main.IntermediateShadowChild.run"),
            "self.helper",
        ),
        (
            _definition_id_for(derived_program, "main.ProviderReboundChild.run"),
            "self.helper",
        ),
    }

    blocked_scope_ids = {scope_id for scope_id, _ in blocked_scope_and_text}

    assert not any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id in blocked_scope_ids
        for dependency in call_dependencies
    )
    assert all(
        unresolved_by_scope_and_text[scope_and_text]
        == (
            UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
            ReferenceContext.CALL,
        )
        for scope_and_text in blocked_scope_and_text
    )
    assert blocked_scope_and_text.isdisjoint(unsupported_by_scope_and_text)


def test_derive_dependency_frontier_proves_narrow_same_class_self_attributes(
    tmp_path: Path,
) -> None:
    """Unique same-class ``self.attr`` reads become attribute dependencies."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                field: int = 1

                def run(self) -> None:
                    seen = self.field
                    self.field = seen
                    missing = self.missing

                def weird(cls) -> None:
                    seen = cls.field

                def other(self, helper: "Example") -> None:
                    seen = helper.field

                def method(self) -> None:
                    return None

                def method_reader(self) -> None:
                    seen = self.method

            class Duplicate:
                field = 1
                field = 2

                def run(self) -> None:
                    seen = self.field

            class Base:
                inherited = 1

            class Child(Base):
                def run(self) -> None:
                    seen = self.inherited
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    attribute_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.ATTRIBUTE
    ]
    unresolved_by_scope_text_and_context = {
        (
            access.enclosing_scope_id,
            access.access_text,
            access.context,
        ): access.reason_code
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.ATTRIBUTE_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Example.run")
        and dependency.target_symbol_id
        == _resolved_symbol_id_for(
            derived_program,
            "main.Example.field",
            kind=ResolvedSymbolKind.ATTRIBUTE,
        )
        for dependency in attribute_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.Example.run"),
        "self.field",
        ReferenceContext.ATTRIBUTE_ACCESS,
    ) not in unresolved_by_scope_text_and_context
    assert (
        unresolved_by_scope_text_and_context[
            (
                _definition_id_for(derived_program, "main.Example.run"),
                "self.field",
                ReferenceContext.STORE,
            )
        ]
        == UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert (
        unresolved_by_scope_text_and_context[
            (
                _definition_id_for(derived_program, "main.Example.run"),
                "self.missing",
                ReferenceContext.ATTRIBUTE_ACCESS,
            )
        ]
        == UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert (
        unresolved_by_scope_text_and_context[
            (
                _definition_id_for(derived_program, "main.Example.weird"),
                "cls.field",
                ReferenceContext.ATTRIBUTE_ACCESS,
            )
        ]
        == UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert (
        unresolved_by_scope_text_and_context[
            (
                _definition_id_for(derived_program, "main.Example.other"),
                "helper.field",
                ReferenceContext.ATTRIBUTE_ACCESS,
            )
        ]
        == UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert (
        unresolved_by_scope_text_and_context[
            (
                _definition_id_for(derived_program, "main.Example.method_reader"),
                "self.method",
                ReferenceContext.ATTRIBUTE_ACCESS,
            )
        ]
        == UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert (
        unresolved_by_scope_text_and_context[
            (
                _definition_id_for(derived_program, "main.Duplicate.run"),
                "self.field",
                ReferenceContext.ATTRIBUTE_ACCESS,
            )
        ]
        == UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert (
        unresolved_by_scope_text_and_context[
            (
                _definition_id_for(derived_program, "main.Child.run"),
                "self.inherited",
                ReferenceContext.ATTRIBUTE_ACCESS,
            )
        ]
        == UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )


def test_derive_dependency_frontier_skips_shadowed_same_class_self_attributes(
    tmp_path: Path,
) -> None:
    """Method-backed same-class shadowing preserves the non-proof attribute path."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Plain:
                field = 1

                def run(self) -> None:
                    seen = self.field

            class Shadowed:
                field = 1

                def field(self) -> None:
                    return None

                def run(self) -> None:
                    seen = self.field
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    attribute_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.ATTRIBUTE
    ]
    unresolved_by_scope_text_and_context = {
        (
            access.enclosing_scope_id,
            access.access_text,
            access.context,
        ): access.reason_code
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.ATTRIBUTE_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Plain.run")
        and dependency.target_symbol_id
        == _resolved_symbol_id_for(
            derived_program,
            "main.Plain.field",
            kind=ResolvedSymbolKind.ATTRIBUTE,
        )
        for dependency in attribute_dependencies
    )
    assert not any(
        dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Shadowed.run")
        and dependency.kind is SemanticDependencyKind.ATTRIBUTE
        for dependency in attribute_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.Plain.run"),
        "self.field",
        ReferenceContext.ATTRIBUTE_ACCESS,
    ) not in unresolved_by_scope_text_and_context
    assert (
        unresolved_by_scope_text_and_context[
            (
                _definition_id_for(derived_program, "main.Shadowed.run"),
                "self.field",
                ReferenceContext.ATTRIBUTE_ACCESS,
            )
        ]
        == UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )


def test_derive_dependency_frontier_proves_shallow_import_rooted_member_chains(
    tmp_path: Path,
) -> None:
    """Proven two-hop import-rooted chains become dependencies without prefix noise."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "decorators.py").write_text(
        "def decorate(value: object) -> object:\n    return value\n",
        encoding="utf-8",
    )
    (pkg / "base.py").write_text("class Base:\n    pass\n", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import pkg

            @pkg.decorators.decorate
            class Child(pkg.base.Base):
                def run(self) -> None:
                    pkg.helpers.helper()
                    pkg.helpers.helper.extra()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]
    unresolved_entries = {
        (access.access_text, access.site.span.start_line): access.reason_code
        for access in derived_program.unresolved_frontier
    }
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.DECORATOR_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Child")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "pkg.decorators.decorate")
        for dependency in derived_program.proven_dependencies
    )
    assert any(
        dependency.proof_kind is DependencyProofKind.BASE_CLASS_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Child")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "pkg.base.Base")
        for dependency in derived_program.proven_dependencies
    )
    assert any(
        dependency.proof_kind is DependencyProofKind.CALL_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Child.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "pkg.helpers.helper")
        for dependency in call_dependencies
    )
    assert ("pkg.decorators.decorate", 3) not in unresolved_entries
    assert ("pkg.decorators", 3) not in unresolved_entries
    assert ("pkg.base.Base", 4) not in unresolved_entries
    assert ("pkg.base", 4) not in unresolved_entries
    assert ("pkg.helpers.helper", 6) not in unresolved_entries
    assert ("pkg.helpers", 6) not in unresolved_entries
    assert (
        unsupported_by_text["pkg.helpers.helper.extra"]
        is UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET
    )


def test_derive_dependency_frontier_classifies_module_getattr_calls_as_unsupported(
    tmp_path: Path,
) -> None:
    """Direct unresolved ``mod.attr()`` calls honor imported module ``__getattr__``."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(
        textwrap.dedent(
            """
            def __getattr__(name: str) -> object:
                return object()
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "hooked.py").write_text(
        textwrap.dedent(
            """
            def __getattr__(name: str) -> object:
                return object()
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "plain.py").write_text("", encoding="utf-8")
    (pkg / "sub.py").write_text("", encoding="utf-8")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import pkg
            import pkg.hooked as hooked_mod
            import pkg.plain as plain_mod

            def run() -> None:
                pkg.dynamic()
                pkg.sub.missing()
                hooked_mod.missing()
                plain_mod.missing()
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
    unsupported_by_text = {
        construct.construct_text: (
            construct.reason_code,
            construct.enclosing_scope_id,
        )
        for construct in derived_program.unsupported_constructs
    }

    assert unsupported_by_text["pkg.dynamic"] == (
        UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unsupported_by_text["hooked_mod.missing"] == (
        UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET,
        _definition_id_for(derived_program, "main.run"),
    )
    assert "pkg.dynamic" not in unresolved_by_text
    assert "hooked_mod.missing" not in unresolved_by_text
    assert unresolved_by_text["pkg.sub.missing"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["plain_mod.missing"] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert "pkg.sub.missing" not in unsupported_by_text
    assert "plain_mod.missing" not in unsupported_by_text


def test_derive_dependency_frontier_classifies_module_getattr_attributes_as_unsupported(
    tmp_path: Path,
) -> None:
    """Direct unresolved ``mod.attr`` reads/stores honor module ``__getattr__``."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(
        textwrap.dedent(
            """
            def __getattr__(name: str) -> object:
                return object()
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "hooked.py").write_text(
        textwrap.dedent(
            """
            def __getattr__(name: str) -> object:
                return object()
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "plain.py").write_text("", encoding="utf-8")
    (pkg / "sub.py").write_text("", encoding="utf-8")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import pkg
            import pkg.hooked as hooked_mod
            import pkg.plain as plain_mod

            def run() -> None:
                root_seen = pkg.dynamic
                hooked_seen = hooked_mod.value
                hooked_mod.value = hooked_seen
                plain_seen = plain_mod.value
                plain_mod.value = plain_seen
                package_chain_seen = pkg.sub.value
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unresolved_pairs = {
        (access.access_text, access.context): access.reason_code
        for access in derived_program.unresolved_frontier
    }
    unsupported_reasons_by_text: dict[str, list[UnresolvedReasonCode]] = {}
    for construct in derived_program.unsupported_constructs:
        unsupported_reasons_by_text.setdefault(construct.construct_text, []).append(
            construct.reason_code
        )

    assert unsupported_reasons_by_text["pkg.dynamic"] == [
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS
    ]
    assert unsupported_reasons_by_text["hooked_mod.value"] == [
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
    ]
    assert ("pkg.dynamic", ReferenceContext.ATTRIBUTE_ACCESS) not in unresolved_pairs
    assert ("hooked_mod.value", ReferenceContext.ATTRIBUTE_ACCESS) not in (
        unresolved_pairs
    )
    assert ("hooked_mod.value", ReferenceContext.STORE) not in unresolved_pairs
    assert unresolved_pairs[("plain_mod.value", ReferenceContext.ATTRIBUTE_ACCESS)] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert unresolved_pairs[("plain_mod.value", ReferenceContext.STORE)] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert unresolved_pairs[("pkg.sub.value", ReferenceContext.ATTRIBUTE_ACCESS)] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )


def test_derive_dependency_frontier_surfaces_shallow_alias_boundaries_as_alias_chain(
    tmp_path: Path,
) -> None:
    """Assignment-rooted shallow alias calls stay unresolved as honest alias chains."""
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
            import pkg

            def run() -> None:
                pkg_alias = pkg
                helpers_alias = pkg.helpers
                helper_alias = pkg.helpers.helper
                pkg_alias.helpers.helper()
                helpers_alias.helper()
                helper_alias()
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
    call_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.CALL
    ]

    assert unresolved_by_text["pkg_alias.helpers.helper"] == (
        UnresolvedReasonCode.ALIAS_CHAIN,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["helpers_alias.helper"] == (
        UnresolvedReasonCode.ALIAS_CHAIN,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert unresolved_by_text["helper_alias"] == (
        UnresolvedReasonCode.ALIAS_CHAIN,
        ReferenceContext.CALL,
        _definition_id_for(derived_program, "main.run"),
    )
    assert not any(
        dependency.source_symbol_id == _definition_id_for(derived_program, "main.run")
        and dependency.target_symbol_id
        == _definition_id_for(derived_program, "pkg.helpers.helper")
        for dependency in call_dependencies
    )


def test_derive_dependency_frontier_surfaces_non_call_attribute_reads_and_stores(
    tmp_path: Path,
) -> None:
    """Non-call attribute reads/stores become frontier or honest unsupported output."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def factory() -> object:
                return object()

            def run(obj: object) -> None:
                seen = obj.value
                obj.value = seen
                alias = pkg.helpers.helper
                dynamic = factory().value
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unresolved_pairs = {
        (access.access_text, access.context): access.reason_code
        for access in derived_program.unresolved_frontier
    }
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in derived_program.unsupported_constructs
    }

    assert unresolved_pairs[("obj.value", ReferenceContext.ATTRIBUTE_ACCESS)] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert unresolved_pairs[("obj.value", ReferenceContext.STORE)] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert (
        unsupported_by_text["pkg.helpers.helper"]
        is UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS
    )
    assert (
        unsupported_by_text["factory().value"]
        is UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS
    )


def test_derive_dependency_frontier_classifies_hooked_self_attributes_as_unsupported(
    tmp_path: Path,
) -> None:
    """Hook-affected same-class ``self.field`` reads and stores become unsupported."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Plain:
                def run(self) -> None:
                    seen = self.field_plain
                    self.field_plain = seen

            class GetattrHooked:
                def __getattr__(self, name: str) -> object:
                    return object()

                def run(self) -> None:
                    seen = self.field_from_getattr
                    self.field_from_getattr = seen

            class GetattributeHooked:
                def __getattribute__(self, name: str) -> object:
                    return object()

                def run(self) -> None:
                    seen = self.field_from_getattribute
                    self.field_from_getattribute = seen
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unresolved_pairs = {
        (access.access_text, access.context): access.reason_code
        for access in derived_program.unresolved_frontier
    }
    unsupported_reasons_by_text: dict[str, list[UnresolvedReasonCode]] = {}
    for construct in derived_program.unsupported_constructs:
        unsupported_reasons_by_text.setdefault(construct.construct_text, []).append(
            construct.reason_code
        )

    assert (
        unresolved_pairs[("self.field_plain", ReferenceContext.ATTRIBUTE_ACCESS)]
        == UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert unresolved_pairs[("self.field_plain", ReferenceContext.STORE)] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert ("self.field_from_getattr", ReferenceContext.ATTRIBUTE_ACCESS) not in (
        unresolved_pairs
    )
    assert ("self.field_from_getattr", ReferenceContext.STORE) not in unresolved_pairs
    assert unsupported_reasons_by_text["self.field_from_getattr"] == [
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
    ]
    assert unsupported_reasons_by_text["self.field_from_getattribute"] == [
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
    ]


def test_derive_dependency_frontier_blocks_getattribute_affected_self_attributes(
    tmp_path: Path,
) -> None:
    """``__getattribute__`` interference still blocks same-class attribute proof."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Plain:
                field_plain = 1

                def run(self) -> None:
                    seen = self.field_plain

            class Hooked:
                field_hooked = 1

                def __getattribute__(self, name: str) -> object:
                    return object()

                def run(self) -> None:
                    seen = self.field_hooked

            class HookedBase:
                def __getattribute__(self, name: str) -> object:
                    return object()

            class MixedChild(HookedBase):
                field_mixed = 1

                def run(self) -> None:
                    seen = self.field_mixed
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    attribute_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.ATTRIBUTE
    ]
    unsupported_by_text = {
        construct.construct_text: (
            construct.reason_code,
            construct.enclosing_scope_id,
        )
        for construct in derived_program.unsupported_constructs
    }
    unresolved_by_scope_text_and_context = {
        (
            access.enclosing_scope_id,
            access.access_text,
            access.context,
        ): access.reason_code
        for access in derived_program.unresolved_frontier
    }

    assert any(
        dependency.proof_kind is DependencyProofKind.ATTRIBUTE_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Plain.run")
        and dependency.target_symbol_id
        == _resolved_symbol_id_for(
            derived_program,
            "main.Plain.field_plain",
            kind=ResolvedSymbolKind.ATTRIBUTE,
        )
        for dependency in attribute_dependencies
    )
    assert not any(
        dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.Hooked.run")
        and dependency.target_symbol_id
        == _resolved_symbol_id_for(
            derived_program,
            "main.Hooked.field_hooked",
            kind=ResolvedSymbolKind.ATTRIBUTE,
        )
        for dependency in attribute_dependencies
    )
    assert not any(
        dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.MixedChild.run")
        and dependency.target_symbol_id
        == _resolved_symbol_id_for(
            derived_program,
            "main.MixedChild.field_mixed",
            kind=ResolvedSymbolKind.ATTRIBUTE,
        )
        for dependency in attribute_dependencies
    )
    assert unsupported_by_text["self.field_hooked"] == (
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
        _definition_id_for(derived_program, "main.Hooked.run"),
    )
    assert unsupported_by_text["self.field_mixed"] == (
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
        _definition_id_for(derived_program, "main.MixedChild.run"),
    )
    assert (
        _definition_id_for(derived_program, "main.Hooked.run"),
        "self.field_hooked",
        ReferenceContext.ATTRIBUTE_ACCESS,
    ) not in unresolved_by_scope_text_and_context
    assert (
        _definition_id_for(derived_program, "main.MixedChild.run"),
        "self.field_mixed",
        ReferenceContext.ATTRIBUTE_ACCESS,
    ) not in unresolved_by_scope_text_and_context


def test_derive_dependency_frontier_classifies_direct_base_self_attrs_as_unsupported(
    tmp_path: Path,
) -> None:
    """Direct-base inherited self hooks make unresolved attributes unsupported."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class PlainBase:
                pass

            class GetattrBase:
                def __getattr__(self, name: str) -> object:
                    return object()

            class GetattributeBase:
                def __getattribute__(self, name: str) -> object:
                    return object()

            class PlainChild(PlainBase):
                def run(self) -> None:
                    seen = self.field_plain
                    self.field_plain = seen

            class GetattrChild(GetattrBase):
                def run(self) -> None:
                    seen = self.field_from_getattr_base
                    self.field_from_getattr_base = seen

            class GetattributeChild(PlainBase, GetattributeBase):
                def run(self) -> None:
                    seen = self.field_from_getattribute_base
                    self.field_from_getattribute_base = seen
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unresolved_pairs = {
        (access.access_text, access.context): access.reason_code
        for access in derived_program.unresolved_frontier
    }
    unsupported_reasons_by_text: dict[str, list[UnresolvedReasonCode]] = {}
    for construct in derived_program.unsupported_constructs:
        unsupported_reasons_by_text.setdefault(construct.construct_text, []).append(
            construct.reason_code
        )

    assert (
        unresolved_pairs[("self.field_plain", ReferenceContext.ATTRIBUTE_ACCESS)]
        == UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert unresolved_pairs[("self.field_plain", ReferenceContext.STORE)] == (
        UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    assert ("self.field_from_getattr_base", ReferenceContext.ATTRIBUTE_ACCESS) not in (
        unresolved_pairs
    )
    assert (
        "self.field_from_getattr_base",
        ReferenceContext.STORE,
    ) not in unresolved_pairs
    assert unsupported_reasons_by_text["self.field_from_getattr_base"] == [
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
    ]
    assert unsupported_reasons_by_text["self.field_from_getattribute_base"] == [
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
    ]


def test_dependency_frontier_classifies_transitive_self_attrs_as_unsupported(
    tmp_path: Path,
) -> None:
    """Transitively hooked ancestors reroute unresolved self attrs to unsupported."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class HookedGrandparent:
                def __getattribute__(self, name: str) -> object:
                    return object()

            class PlainIntermediate(HookedGrandparent):
                pass

            class LinearChild(PlainIntermediate):
                field_linear = 1

                def run(self) -> None:
                    seen = self.field_linear
                    self.field_linear = seen

            class PlainDirectBase:
                pass

            class HookedBridge(HookedGrandparent):
                pass

            class MixedChild(PlainDirectBase, HookedBridge):
                field_mixed = 1

                def run(self) -> None:
                    seen = self.field_mixed
                    self.field_mixed = seen

            class GetattrGrandparent:
                def __getattr__(self, name: str) -> object:
                    return object()

            class GetattrBridge(GetattrGrandparent):
                pass

            class GetattrMixedChild(PlainDirectBase, GetattrBridge):
                def run(self) -> None:
                    seen = self.field_getattr_mixed
                    self.field_getattr_mixed = seen
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    attribute_dependencies = [
        dependency
        for dependency in derived_program.proven_dependencies
        if dependency.kind is SemanticDependencyKind.ATTRIBUTE
    ]
    unresolved_by_scope_text_and_context = {
        (
            access.enclosing_scope_id,
            access.access_text,
            access.context,
        ): access.reason_code
        for access in derived_program.unresolved_frontier
    }
    unsupported_reasons_by_scope_and_text: dict[
        tuple[str, str], list[UnresolvedReasonCode]
    ] = {}
    for construct in derived_program.unsupported_constructs:
        unsupported_reasons_by_scope_and_text.setdefault(
            (construct.enclosing_scope_id, construct.construct_text),
            [],
        ).append(construct.reason_code)

    assert not any(
        dependency.proof_kind is DependencyProofKind.ATTRIBUTE_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.LinearChild.run")
        and dependency.target_symbol_id
        == _resolved_symbol_id_for(
            derived_program,
            "main.LinearChild.field_linear",
            kind=ResolvedSymbolKind.ATTRIBUTE,
        )
        for dependency in attribute_dependencies
    )
    assert not any(
        dependency.proof_kind is DependencyProofKind.ATTRIBUTE_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.MixedChild.run")
        and dependency.target_symbol_id
        == _resolved_symbol_id_for(
            derived_program,
            "main.MixedChild.field_mixed",
            kind=ResolvedSymbolKind.ATTRIBUTE,
        )
        for dependency in attribute_dependencies
    )
    assert not any(
        dependency.proof_kind is DependencyProofKind.ATTRIBUTE_RESOLUTION
        and dependency.source_symbol_id
        == _definition_id_for(derived_program, "main.GetattrMixedChild.run")
        for dependency in attribute_dependencies
    )
    assert (
        _definition_id_for(derived_program, "main.LinearChild.run"),
        "self.field_linear",
        ReferenceContext.ATTRIBUTE_ACCESS,
    ) not in unresolved_by_scope_text_and_context
    assert (
        _definition_id_for(derived_program, "main.LinearChild.run"),
        "self.field_linear",
        ReferenceContext.STORE,
    ) not in unresolved_by_scope_text_and_context
    assert (
        _definition_id_for(derived_program, "main.MixedChild.run"),
        "self.field_mixed",
        ReferenceContext.ATTRIBUTE_ACCESS,
    ) not in unresolved_by_scope_text_and_context
    assert (
        _definition_id_for(derived_program, "main.MixedChild.run"),
        "self.field_mixed",
        ReferenceContext.STORE,
    ) not in unresolved_by_scope_text_and_context
    assert (
        _definition_id_for(derived_program, "main.GetattrMixedChild.run"),
        "self.field_getattr_mixed",
        ReferenceContext.ATTRIBUTE_ACCESS,
    ) not in unresolved_by_scope_text_and_context
    assert (
        _definition_id_for(derived_program, "main.GetattrMixedChild.run"),
        "self.field_getattr_mixed",
        ReferenceContext.STORE,
    ) not in unresolved_by_scope_text_and_context
    assert unsupported_reasons_by_scope_and_text[
        (
            _definition_id_for(derived_program, "main.LinearChild.run"),
            "self.field_linear",
        )
    ] == [
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
    ]
    assert unsupported_reasons_by_scope_and_text[
        (
            _definition_id_for(derived_program, "main.MixedChild.run"),
            "self.field_mixed",
        )
    ] == [
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
    ]
    assert unsupported_reasons_by_scope_and_text[
        (
            _definition_id_for(derived_program, "main.GetattrMixedChild.run"),
            "self.field_getattr_mixed",
        )
    ] == [
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
    ]


def test_derive_dependency_frontier_skips_attribute_sites_covered_elsewhere(
    tmp_path: Path,
) -> None:
    """Attribute sites already modeled as decorator/base/call surfaces are skipped."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            @decorators.missing
            class Example(base_mod.Missing):
                def run(self) -> None:
                    helpers.missing()
                    pkg.helpers.helper()
                    value = self.field
            """
        ).lstrip(),
        encoding="utf-8",
    )

    derived_program = _derived_program(tmp_path)
    unresolved_contexts_by_text: dict[str, set[ReferenceContext]] = {}
    for access in derived_program.unresolved_frontier:
        unresolved_contexts_by_text.setdefault(access.access_text, set()).add(
            access.context
        )
    unsupported_reasons_by_text: dict[str, list[UnresolvedReasonCode]] = {}
    for construct in derived_program.unsupported_constructs:
        unsupported_reasons_by_text.setdefault(construct.construct_text, []).append(
            construct.reason_code
        )

    assert unresolved_contexts_by_text["decorators.missing"] == {
        ReferenceContext.DECORATOR
    }
    assert unresolved_contexts_by_text["base_mod.Missing"] == {
        ReferenceContext.BASE_CLASS
    }
    assert unresolved_contexts_by_text["helpers.missing"] == {ReferenceContext.CALL}
    assert unresolved_contexts_by_text["self.field"] == {
        ReferenceContext.ATTRIBUTE_ACCESS
    }
    assert unsupported_reasons_by_text["pkg.helpers.helper"] == [
        UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET
    ]


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
                pkg.helpers.helper.extra()
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
        unsupported_by_text["pkg.helpers.helper.extra"]
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
