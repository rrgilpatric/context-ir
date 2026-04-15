"""Resolver tests for the semantic-first baseline."""

from __future__ import annotations

import textwrap
from pathlib import Path

from context_ir.binder import bind_syntax
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_types import (
    DefinitionKind,
    ImportKind,
    ImportTargetKind,
    ReferenceContext,
    SemanticProgram,
    SupportedDecorator,
)


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


def test_resolve_semantics_preserves_binder_owned_data(tmp_path: Path) -> None:
    """Resolver output keeps the accepted binder substrate intact."""
    (tmp_path / "example.py").write_text(
        "def run(value: int) -> int:\n    return value\n",
        encoding="utf-8",
    )

    syntax = extract_syntax(tmp_path)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)

    assert isinstance(resolved_program, SemanticProgram)
    assert resolved_program.repo_root == tmp_path
    assert resolved_program.syntax is bound_program.syntax
    assert resolved_program.supported_subset == bound_program.supported_subset
    assert resolved_program.resolved_symbols is bound_program.resolved_symbols
    assert resolved_program.bindings is bound_program.bindings
    assert resolved_program.resolved_imports == []
    assert resolved_program.dataclass_models == []
    assert resolved_program.dataclass_fields == []
    assert resolved_program.proven_dependencies == []


def test_resolve_semantics_resolves_supported_import_targets(tmp_path: Path) -> None:
    """Supported import bindings resolve to truthful repository targets."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "base.py").write_text("class Base:\n    pass\n", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def helper() -> int:\n    return 1\n",
        encoding="utf-8",
    )
    (pkg / "mod.py").write_text(
        "def factory() -> int:\n    return 1\n",
        encoding="utf-8",
    )
    (pkg / "star.py").write_text("EXPORTED = 1\n", encoding="utf-8")
    (pkg / "example.py").write_text(
        textwrap.dedent(
            """
            from .helpers import helper as local_helper
            from pkg.base import Base as BaseAlias
            from pkg import mod as mod_alias
            from pkg.star import *
            import pkg.mod as mod
            import pkg.mod
            """
        ).lstrip(),
        encoding="utf-8",
    )

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    resolved_imports = {
        resolved_import.bound_name: resolved_import
        for resolved_import in resolved_program.resolved_imports
    }

    assert resolved_imports["local_helper"].target_kind is ImportTargetKind.DEFINITION
    assert (
        resolved_imports["local_helper"].target_qualified_name == "pkg.helpers.helper"
    )

    assert resolved_imports["BaseAlias"].target_kind is ImportTargetKind.DEFINITION
    assert resolved_imports["BaseAlias"].target_qualified_name == "pkg.base.Base"

    assert resolved_imports["mod_alias"].target_kind is ImportTargetKind.MODULE
    assert resolved_imports["mod_alias"].target_qualified_name == "pkg.mod"

    assert resolved_imports["mod"].target_kind is ImportTargetKind.MODULE
    assert resolved_imports["mod"].target_qualified_name == "pkg.mod"

    assert resolved_imports["pkg"].target_kind is ImportTargetKind.MODULE
    assert resolved_imports["pkg"].target_qualified_name == "pkg"

    star_import = next(
        import_fact
        for import_fact in resolved_program.syntax.imports
        if import_fact.kind is ImportKind.STAR_IMPORT
    )
    assert all(
        resolved_import.import_id != star_import.import_id
        for resolved_import in resolved_program.resolved_imports
    )


def test_resolve_semantics_requires_full_dotted_module_proof_for_plain_imports(
    tmp_path: Path,
) -> None:
    """Plain dotted imports resolve only when the full module path is proven."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "good.py").write_text("import pkg.mod\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text("import pkg.missing\n", encoding="utf-8")

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    resolved_imports_by_path = {
        resolved_import.site.file_path: resolved_import
        for resolved_import in resolved_program.resolved_imports
    }

    assert resolved_imports_by_path["good.py"].bound_name == "pkg"
    assert resolved_imports_by_path["good.py"].target_kind is ImportTargetKind.MODULE
    assert resolved_imports_by_path["good.py"].target_qualified_name == "pkg"
    assert "bad.py" not in resolved_imports_by_path


def test_resolve_semantics_honors_lexical_shadowing_for_simple_name_calls(
    tmp_path: Path,
) -> None:
    """Nearest provable binding wins for supported simple-name call resolution."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def helper() -> int:\n    return 1\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.helpers import helper

            def run() -> int:
                def helper() -> int:
                    return 2
                return helper()

            helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references = {
        resolved_reference.site.span.start_line: resolved_reference.resolved_symbol_id
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
        and resolved_reference.name == "helper"
    }

    assert call_references[6] == _definition_id_for(
        resolved_program,
        "main.run.helper",
    )
    assert call_references[8] == _definition_id_for(
        resolved_program,
        "pkg.helpers.helper",
    )


def test_resolve_semantics_resolves_supported_attribute_reference_surfaces(
    tmp_path: Path,
) -> None:
    """Decorator, base, and call surfaces resolve only when directly provable."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "decorators.py").write_text(
        "def register(value: object) -> object:\n    return value\n",
        encoding="utf-8",
    )
    (pkg / "base.py").write_text("class Base:\n    pass\n", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def build() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import pkg.decorators as decorators
            import pkg.base as base_mod
            import pkg.helpers as helpers

            @decorators.register
            class Child(base_mod.Base):
                def method(self) -> None:
                    helpers.build()
                    self.build()

            @decorators
            class BadDecorator:
                pass

            class BadBase(base_mod):
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    references_by_name = {
        resolved_reference.name: resolved_reference
        for resolved_reference in resolved_program.resolved_references
    }

    assert (
        references_by_name["decorators.register"].context is ReferenceContext.DECORATOR
    )
    assert references_by_name[
        "decorators.register"
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "pkg.decorators.register",
    )
    assert references_by_name["base_mod.Base"].context is ReferenceContext.BASE_CLASS
    assert references_by_name["base_mod.Base"].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "pkg.base.Base",
    )
    assert references_by_name["helpers.build"].context is ReferenceContext.CALL
    assert references_by_name["helpers.build"].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "pkg.helpers.build",
    )
    assert "decorators" not in references_by_name
    assert "base_mod" not in references_by_name
    assert "self.build" not in references_by_name


def test_resolve_semantics_skips_star_imports_and_parse_error_files(
    tmp_path: Path,
) -> None:
    """Resolver-owned facts stay silent for star imports and syntax-invalid files."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "good.py").write_text(
        "from pkg.helpers import *\nhelper()\n",
        encoding="utf-8",
    )
    (tmp_path / "bad.py").write_text(
        "from pkg.helpers import helper\nclass Broken(\n",
        encoding="utf-8",
    )

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))

    assert resolved_program.resolved_imports == []
    assert resolved_program.resolved_references == []
    assert resolved_program.dataclass_models == []
    assert resolved_program.dataclass_fields == []
    assert all(
        resolved_import.site.file_path != "bad.py"
        for resolved_import in resolved_program.resolved_imports
    )
    assert all(
        resolved_reference.site.file_path != "bad.py"
        for resolved_reference in resolved_program.resolved_references
    )


def test_resolve_semantics_records_narrow_dataclass_models_and_fields(
    tmp_path: Path,
) -> None:
    """Only proven narrow dataclass forms produce dataclass object facts."""
    (tmp_path / "models.py").write_text(
        textwrap.dedent(
            """
            from dataclasses import dataclass as dc
            import dataclasses as dataclasses_mod

            @dc
            class Direct:
                name: str
                count: int = 1
                other.attr: int = 2
                label = "x"

            @dataclasses_mod.dataclass
            class ViaModule:
                value: str

            def wrap(value: object) -> object:
                return value

            @dc
            @wrap
            class Mixed:
                bad: int

            @wrap(dc)
            class Wrapped:
                also_bad: int
            """
        ).lstrip(),
        encoding="utf-8",
    )

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    model_symbol_ids = {
        model.class_symbol_id for model in resolved_program.dataclass_models
    }
    dataclass_field_names = {
        (field.class_symbol_id, field.name)
        for field in resolved_program.dataclass_fields
    }
    references_by_name = {
        resolved_reference.name: resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.DECORATOR
    }

    assert references_by_name["dc"].resolved_symbol_id.startswith("import:")
    assert references_by_name[
        "dataclasses_mod.dataclass"
    ].resolved_symbol_id.startswith("import:")

    assert model_symbol_ids == {
        _definition_id_for(resolved_program, "models.Direct"),
        _definition_id_for(resolved_program, "models.ViaModule"),
    }
    assert resolved_program.resolved_symbols[
        _definition_id_for(resolved_program, "models.Direct")
    ].supported_decorators == (SupportedDecorator.DATACLASS,)
    assert resolved_program.resolved_symbols[
        _definition_id_for(resolved_program, "models.ViaModule")
    ].supported_decorators == (SupportedDecorator.DATACLASS,)
    assert dataclass_field_names == {
        (_definition_id_for(resolved_program, "models.Direct"), "name"),
        (_definition_id_for(resolved_program, "models.Direct"), "count"),
        (_definition_id_for(resolved_program, "models.ViaModule"), "value"),
    }
    assert _definition_id_for(resolved_program, "models.Mixed") not in model_symbol_ids
    assert (
        _definition_id_for(resolved_program, "models.Wrapped") not in model_symbol_ids
    )
    assert (
        resolved_program.resolved_symbols[
            _definition_id_for(resolved_program, "models.Mixed")
        ].supported_decorators
        == ()
    )
    assert (
        resolved_program.resolved_symbols[
            _definition_id_for(resolved_program, "models.Wrapped")
        ].supported_decorators
        == ()
    )
    assert resolved_program.proven_dependencies == []


def test_resolve_semantics_resolves_imported_base_references_to_repo_symbols(
    tmp_path: Path,
) -> None:
    """Simple-name bases imported from the repository resolve to the target class."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "base.py").write_text("class Base:\n    pass\n", encoding="utf-8")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.base import Base as BaseAlias

            class Child(BaseAlias):
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    base_reference = next(
        resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.BASE_CLASS
    )

    assert base_reference.name == "BaseAlias"
    assert base_reference.resolved_symbol_id == _definition_id_for(
        resolved_program,
        "pkg.base.Base",
    )
    assert (
        next(
            definition.kind
            for definition in resolved_program.syntax.definitions
            if definition.definition_id == base_reference.resolved_symbol_id
        )
        is DefinitionKind.CLASS
    )
