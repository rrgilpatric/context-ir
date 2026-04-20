"""Resolver tests for the semantic-first baseline."""

from __future__ import annotations

import textwrap
from pathlib import Path

from context_ir.binder import bind_syntax
from context_ir.parser import extract_syntax
from context_ir.resolver import (
    _build_repository_index,
    _resolve_base_class_references,
    _resolve_imports,
    _transitively_proven_ancestor_class_ids,
    resolve_semantics,
)
from context_ir.semantic_types import (
    DefinitionKind,
    ImportKind,
    ImportTargetKind,
    ReferenceContext,
    ResolvedSymbolKind,
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


def test_resolve_semantics_resolves_shallow_import_rooted_member_chains(
    tmp_path: Path,
) -> None:
    """Import-rooted two-hop chains resolve only for proven repo module/member paths."""
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
            import pkg

            @pkg.decorators.register
            class Child(pkg.base.Base):
                def method(self) -> None:
                    pkg.helpers.build()
                    pkg.helpers.build.extra()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    references_by_name = {
        resolved_reference.name: resolved_reference
        for resolved_reference in resolved_program.resolved_references
    }

    assert references_by_name[
        "pkg.decorators.register"
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "pkg.decorators.register",
    )
    assert references_by_name["pkg.base.Base"].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "pkg.base.Base",
    )
    assert references_by_name[
        "pkg.helpers.build"
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "pkg.helpers.build",
    )
    assert "pkg.helpers.build.extra" not in references_by_name


def test_resolve_semantics_resolves_same_class_self_calls_only_under_narrow_rules(
    tmp_path: Path,
) -> None:
    """Same-class ``self.foo()`` calls resolve only for canonical methods."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                def run(self) -> None:
                    self.build()
                    self.run()
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_name = {
        resolved_reference.name: resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_name[
        "self.build"
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.Example.build",
    )
    assert call_references_by_name["self.run"].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.Example.run",
    )
    assert "self.missing" not in call_references_by_name
    assert "cls.build" not in call_references_by_name
    assert "helper.build" not in call_references_by_name
    assert "self.helper" not in call_references_by_name


def test_resolve_semantics_skips_same_class_self_call_proof_when_getattribute_exists(
    tmp_path: Path,
) -> None:
    """A same-class ``__getattribute__`` disables narrow ``self.foo()`` call proof."""
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

                def build_hooked(self) -> None:
                    return None
            """
        ).lstrip(),
        encoding="utf-8",
    )

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_name = {
        resolved_reference.name: resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_name[
        "self.build_plain"
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.Plain.build_plain",
    )
    assert "self.build_hooked" not in call_references_by_name


def test_resolve_semantics_skips_self_call_proof_for_direct_base_getattribute(
    tmp_path: Path,
) -> None:
    """A directly proven base ``__getattribute__`` disables same-class proof."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class PlainBase:
                pass

            class HookedBase:
                def __getattribute__(self, name: str) -> object:
                    return object()

            class PlainChild(PlainBase):
                def run(self) -> None:
                    self.build_plain()

                def build_plain(self) -> None:
                    return None

            class MixedChild(PlainBase, HookedBase):
                def run(self) -> None:
                    self.build_mixed()

                def build_mixed(self) -> None:
                    return None
            """
        ).lstrip(),
        encoding="utf-8",
    )

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_name = {
        resolved_reference.name: resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_name[
        "self.build_plain"
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.PlainChild.build_plain",
    )
    assert "self.build_mixed" not in call_references_by_name


def test_resolve_semantics_skips_self_call_proof_for_transitive_getattribute_ancestors(
    tmp_path: Path,
) -> None:
    """Transitively proven hooked ancestors disable the narrow self-call seams."""
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
            """
        ).lstrip(),
        encoding="utf-8",
    )

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert (
        _definition_id_for(resolved_program, "main.LinearSameClassChild.run"),
        "self.build_linear",
    ) not in call_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.LinearInheritedChild.run"),
        "self.inherited_linear",
    ) not in call_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.MixedSameClassChild.run"),
        "self.build_mixed",
    ) not in call_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.MixedInheritedChild.run"),
        "self.inherited_mixed",
    ) not in call_references_by_scope_and_name


def test_resolve_semantics_resolves_direct_base_self_calls_under_narrow_rules(
    tmp_path: Path,
) -> None:
    """Direct-base inherited ``self.foo()`` proof stays narrow and unambiguous."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.Child.run"), "self.build")
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.Base.build",
    )
    assert call_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.OverrideChild.run"), "self.build")
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.OverrideChild.build",
    )
    assert call_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.AmbiguousChild.run"), "self.shared")
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.LeftBase.shared",
    )
    assert (
        _definition_id_for(resolved_program, "main.DecoratedChild.run"),
        "self.helper",
    ) not in call_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.ShadowChild.run"),
        "self.helper",
    ) not in call_references_by_scope_and_name


def test_resolve_semantics_preserves_declared_base_order_in_resolver_ancestry(
    tmp_path: Path,
) -> None:
    """Resolver ancestry keeps direct bases and closure in declaration order."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class ZLeaf:
                pass

            class MLeaf:
                pass

            class ZBase(ZLeaf):
                pass

            class ABase(MLeaf):
                pass

            class Example(ZBase, ABase):
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )

    bound_program = bind_syntax(extract_syntax(tmp_path))
    index = _build_repository_index(bound_program)
    resolved_imports = _resolve_imports(bound_program, index)
    resolved_imports_by_binding_symbol_id = {
        resolved_import.binding_symbol_id: resolved_import
        for resolved_import in resolved_imports
    }
    _, direct_proven_base_class_ids_by_class_id = _resolve_base_class_references(
        program=bound_program,
        index=index,
        resolved_imports_by_binding_symbol_id=resolved_imports_by_binding_symbol_id,
    )

    example_definition_id = _definition_id_for(bound_program, "main.Example")
    assert direct_proven_base_class_ids_by_class_id[example_definition_id] == (
        _definition_id_for(bound_program, "main.ZBase"),
        _definition_id_for(bound_program, "main.ABase"),
    )
    assert _transitively_proven_ancestor_class_ids(
        class_definition_id=example_definition_id,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    ) == (
        _definition_id_for(bound_program, "main.ZBase"),
        _definition_id_for(bound_program, "main.ZLeaf"),
        _definition_id_for(bound_program, "main.ABase"),
        _definition_id_for(bound_program, "main.MLeaf"),
    )


def test_resolve_semantics_resolves_transitive_self_calls_only_for_sole_providers(
    tmp_path: Path,
) -> None:
    """Transitive inherited ``self.foo()`` proof stays unique and conservative."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_scope_and_name[
        (
            _definition_id_for(resolved_program, "main.LinearChild.run"),
            "self.inherited_linear",
        )
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.LinearGrandparent.inherited_linear",
    )
    assert call_references_by_scope_and_name[
        (
            _definition_id_for(resolved_program, "main.BranchChild.run"),
            "self.inherited_branch",
        )
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.BranchProvider.inherited_branch",
    )
    assert call_references_by_scope_and_name[
        (
            _definition_id_for(resolved_program, "main.AmbiguousChild.run"),
            "self.ambiguous",
        )
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.LeftProvider.ambiguous",
    )
    assert (
        _definition_id_for(resolved_program, "main.DecoratedChild.run"),
        "self.blocked",
    ) not in call_references_by_scope_and_name


def test_resolve_semantics_resolves_linear_transitive_self_calls_to_nearest_owner(
    tmp_path: Path,
) -> None:
    """Linear single-chain inherited calls stop at the first eligible owner."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_scope_and_name[
        (
            _definition_id_for(resolved_program, "main.LinearChild.run"),
            "self.inherited_linear",
        )
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.NearProvider.inherited_linear",
    )
    assert call_references_by_scope_and_name[
        (
            _definition_id_for(resolved_program, "main.BranchedChild.run"),
            "self.branched",
        )
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.LeftNearProvider.branched",
    )
    assert (
        _definition_id_for(resolved_program, "main.BlockedChild.run"),
        "self.blocked",
    ) not in call_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.ShadowedChild.run"),
        "self.shadowed",
    ) not in call_references_by_scope_and_name


def test_resolve_semantics_resolves_branched_self_calls_by_declared_base_order(
    tmp_path: Path,
) -> None:
    """Declared base order wins across linear disjoint inherited-call branches."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_scope_and_name[
        (
            _definition_id_for(resolved_program, "main.PreferredChild.run"),
            "self.preferred",
        )
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.LeftProvider.preferred",
    )


def test_resolve_semantics_prefers_earlier_transitive_over_later_direct_base(
    tmp_path: Path,
) -> None:
    """Earlier transitive branch owners beat later direct-base owners."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.Child.run"), "self.helper")
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.LeftFarProvider.helper",
    )


def test_resolve_semantics_resolves_overlapping_shared_ancestor_sole_providers(
    tmp_path: Path,
) -> None:
    """Shared non-direct sole providers resolve across individually linear overlap."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.DiamondChild.run"), "self.helper")
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.DiamondSharedProvider.helper",
    )
    assert call_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.OverlapChild.run"), "self.helper")
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.OverlapSharedProvider.helper",
    )


def test_resolve_semantics_resolves_later_owner_overlap_when_earlier_silent(
    tmp_path: Path,
) -> None:
    """A later overlap owner resolves when earlier overlap branches stay silent."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.Child.run"), "self.helper")
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.RightDiamondBridge.helper",
    )


def test_resolve_semantics_resolves_overlap_multi_owner_to_first_exclusive_owner(
    tmp_path: Path,
) -> None:
    """Declared-order exclusive overlap owners resolve to the first owner."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.Child.run"), "self.helper")
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.LeftOwner.helper",
    )


def test_resolve_semantics_resolves_three_branch_overlap_to_first_exclusive_owner(
    tmp_path: Path,
) -> None:
    """The first declared exclusive owner wins across three linear overlap branches."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.Child.run"), "self.helper")
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.SecondOwner.helper",
    )


def test_resolve_semantics_leaves_earlier_ineligible_overlap_unresolved(
    tmp_path: Path,
) -> None:
    """An earlier ineligible overlap owner keeps the later branch blocked."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert (
        _definition_id_for(resolved_program, "main.Child.run"),
        "self.helper",
    ) not in call_references_by_scope_and_name


def test_resolve_semantics_leaves_non_linear_overlap_unresolved(
    tmp_path: Path,
) -> None:
    """Non-linear overlap branches stay outside the reopened proof shape."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert (
        _definition_id_for(resolved_program, "main.Child.run"),
        "self.helper",
    ) not in call_references_by_scope_and_name


def test_resolve_semantics_blocks_self_call_proof_for_earlier_shadowed_branch_owners(
    tmp_path: Path,
) -> None:
    """Earlier class-scope shadowing keeps ``self.foo()`` on the non-proof path."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    call_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.CALL
    }

    assert call_references_by_scope_and_name[
        (
            _definition_id_for(resolved_program, "main.CompetingDirectBaseChild.run"),
            "self.helper",
        )
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.CompetingDirectBaseProvider.helper",
    )
    assert call_references_by_scope_and_name[
        (
            _definition_id_for(resolved_program, "main.BranchShadowChild.run"),
            "self.helper",
        )
    ].resolved_symbol_id == _definition_id_for(
        resolved_program,
        "main.BranchProvider.helper",
    )

    blocked_scope_and_name = {
        (
            _definition_id_for(resolved_program, "main.SameClassRebound.run"),
            "self.helper",
        ),
        (
            _definition_id_for(resolved_program, "main.DirectBaseShadowChild.run"),
            "self.helper",
        ),
        (
            _definition_id_for(resolved_program, "main.IntermediateShadowChild.run"),
            "self.helper",
        ),
        (
            _definition_id_for(resolved_program, "main.ProviderReboundChild.run"),
            "self.helper",
        ),
    }

    assert blocked_scope_and_name.isdisjoint(call_references_by_scope_and_name)


def test_resolve_semantics_resolves_same_class_self_attribute_reads_narrowly(
    tmp_path: Path,
) -> None:
    """Same-class ``self.attr`` reads resolve only to unique class attributes."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    attribute_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.ATTRIBUTE_ACCESS
    }

    assert attribute_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.Example.run"), "self.field")
    ].resolved_symbol_id == _resolved_symbol_id_for(
        resolved_program,
        "main.Example.field",
        kind=ResolvedSymbolKind.ATTRIBUTE,
    )
    assert (
        _definition_id_for(resolved_program, "main.Example.run"),
        "self.missing",
    ) not in attribute_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.Example.weird"),
        "cls.field",
    ) not in attribute_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.Example.other"),
        "helper.field",
    ) not in attribute_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.Example.method_reader"),
        "self.method",
    ) not in attribute_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.Duplicate.run"),
        "self.field",
    ) not in attribute_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.Child.run"),
        "self.inherited",
    ) not in attribute_references_by_scope_and_name


def test_resolve_semantics_skips_self_attribute_proof_for_getattribute_interference(
    tmp_path: Path,
) -> None:
    """Same-class and direct-base ``__getattribute__`` disable ``self.attr`` proof."""
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    attribute_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.ATTRIBUTE_ACCESS
    }

    assert attribute_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.Plain.run"), "self.field_plain")
    ].resolved_symbol_id == _resolved_symbol_id_for(
        resolved_program,
        "main.Plain.field_plain",
        kind=ResolvedSymbolKind.ATTRIBUTE,
    )
    assert (
        _definition_id_for(resolved_program, "main.Hooked.run"),
        "self.field_hooked",
    ) not in attribute_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.MixedChild.run"),
        "self.field_mixed",
    ) not in attribute_references_by_scope_and_name


def test_resolve_semantics_blocks_self_attr_proof_for_transitive_getattribute(
    tmp_path: Path,
) -> None:
    """Transitively proven hooked ancestors disable narrow ``self.attr`` proof."""
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

            class PlainDirectBase:
                pass

            class HookedBridge(HookedGrandparent):
                pass

            class MixedChild(PlainDirectBase, HookedBridge):
                field_mixed = 1

                def run(self) -> None:
                    seen = self.field_mixed
            """
        ).lstrip(),
        encoding="utf-8",
    )

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    attribute_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.ATTRIBUTE_ACCESS
    }

    assert (
        _definition_id_for(resolved_program, "main.LinearChild.run"),
        "self.field_linear",
    ) not in attribute_references_by_scope_and_name
    assert (
        _definition_id_for(resolved_program, "main.MixedChild.run"),
        "self.field_mixed",
    ) not in attribute_references_by_scope_and_name


def test_resolve_semantics_skips_self_attribute_proof_for_same_class_shadowing(
    tmp_path: Path,
) -> None:
    """Same-class shadowing blocks ``self.attr`` proof.

    The accepted positive case remains the unique same-class class attribute.
    """
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

    resolved_program = resolve_semantics(bind_syntax(extract_syntax(tmp_path)))
    attribute_references_by_scope_and_name = {
        (
            resolved_reference.enclosing_scope_id,
            resolved_reference.name,
        ): resolved_reference
        for resolved_reference in resolved_program.resolved_references
        if resolved_reference.context is ReferenceContext.ATTRIBUTE_ACCESS
    }

    assert attribute_references_by_scope_and_name[
        (_definition_id_for(resolved_program, "main.Plain.run"), "self.field")
    ].resolved_symbol_id == _resolved_symbol_id_for(
        resolved_program,
        "main.Plain.field",
        kind=ResolvedSymbolKind.ATTRIBUTE,
    )
    assert (
        _definition_id_for(resolved_program, "main.Shadowed.run"),
        "self.field",
    ) not in attribute_references_by_scope_and_name


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
