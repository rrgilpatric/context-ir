"""Resolver and object-model layer for the semantic-first baseline."""

from __future__ import annotations

import ast
import keyword
from dataclasses import dataclass, replace

from context_ir.semantic_types import (
    AttributeSiteFact,
    BindingFact,
    BindingKind,
    CallSiteFact,
    DataclassField,
    DataclassModel,
    DecoratorFact,
    DefinitionKind,
    ImportFact,
    ImportKind,
    ImportTargetKind,
    ParameterFact,
    ParameterKind,
    RawDefinitionFact,
    ReferenceContext,
    ResolvedImport,
    ResolvedReference,
    ResolvedSymbol,
    ResolvedSymbolKind,
    SemanticProgram,
    SourceFileFact,
    SourceSite,
    SourceSpan,
    SupportedDecorator,
    SyntaxDiagnosticCode,
)

_FUNCTION_LIKE_KINDS = frozenset(
    {
        DefinitionKind.FUNCTION,
        DefinitionKind.ASYNC_FUNCTION,
        DefinitionKind.METHOD,
    }
)
_CALLABLE_SYMBOL_KINDS = frozenset(
    {
        ResolvedSymbolKind.FUNCTION,
        ResolvedSymbolKind.ASYNC_FUNCTION,
        ResolvedSymbolKind.CLASS,
        ResolvedSymbolKind.METHOD,
    }
)


@dataclass(frozen=True)
class _SimpleNameExpression:
    """Supported single-name reference surface."""

    name: str


@dataclass(frozen=True)
class _AttributeChainExpression:
    """Supported dotted reference surface with up to two attribute hops."""

    root_name: str
    attribute_names: tuple[str, ...]


_SupportedExpression = _SimpleNameExpression | _AttributeChainExpression
_OrderedClassDefinitionIds = tuple[str, ...]
_OrderedBranchClassDefinitionIds = tuple[_OrderedClassDefinitionIds, ...]
_DirectProvenBaseClassIdsByClassId = dict[str, _OrderedClassDefinitionIds]


@dataclass(frozen=True)
class _RepositoryIndex:
    """Indices derived from syntax and binder output for truthful resolution."""

    blocked_file_ids: frozenset[str]
    source_files_by_id: dict[str, SourceFileFact]
    definitions_by_id: dict[str, RawDefinitionFact]
    unique_definitions_by_qualified_name: dict[str, RawDefinitionFact]
    module_symbol_ids_by_name: dict[str, str]
    scope_parent_ids: dict[str, str | None]
    scope_kinds: dict[str, DefinitionKind]
    binding_by_symbol_id: dict[str, BindingFact]
    bindings_by_scope: dict[str, list[BindingFact]]
    parameters_by_owner_definition_id: dict[str, tuple[ParameterFact, ...]]
    methods_by_class_and_name: dict[tuple[str, str], tuple[RawDefinitionFact, ...]]
    unique_methods_by_class_and_name: dict[tuple[str, str], RawDefinitionFact]
    class_attributes_by_class_and_name: dict[tuple[str, str], tuple[BindingFact, ...]]
    unique_class_attributes_by_class_and_name: dict[tuple[str, str], BindingFact]
    class_ids_with_getattribute_method: frozenset[str]
    decorated_definition_ids: frozenset[str]


def resolve_semantics(program: SemanticProgram) -> SemanticProgram:
    """Resolve supported imports, references, and narrow dataclass facts."""
    index = _build_repository_index(program)
    resolved_imports = _resolve_imports(program, index)
    resolved_imports_by_binding_symbol_id = {
        resolved_import.binding_symbol_id: resolved_import
        for resolved_import in resolved_imports
    }
    resolved_references = _resolve_references(
        program,
        index,
        resolved_imports_by_binding_symbol_id,
    )
    dataclass_models, dataclass_fields = _resolve_dataclasses(
        program,
        index,
        resolved_imports_by_binding_symbol_id,
        resolved_references,
    )
    resolved_symbols = _with_proven_dataclass_support(
        program.resolved_symbols,
        dataclass_models,
    )

    return SemanticProgram(
        repo_root=program.repo_root,
        syntax=program.syntax,
        supported_subset=program.supported_subset,
        resolved_symbols=resolved_symbols,
        bindings=program.bindings,
        resolved_imports=resolved_imports,
        dataclass_models=dataclass_models,
        dataclass_fields=dataclass_fields,
        resolved_references=resolved_references,
        proven_dependencies=program.proven_dependencies,
        unresolved_frontier=program.unresolved_frontier,
        unsupported_constructs=program.unsupported_constructs,
        diagnostics=program.diagnostics,
    )


def _build_repository_index(program: SemanticProgram) -> _RepositoryIndex:
    """Build reusable repository indices from syntax and binder output."""
    blocked_file_ids = frozenset(
        diagnostic.file_id
        for diagnostic in program.syntax.diagnostics
        if diagnostic.code is SyntaxDiagnosticCode.PARSE_ERROR
    )
    definitions_by_id = {
        definition.definition_id: definition
        for definition in program.syntax.definitions
        if definition.file_id not in blocked_file_ids
    }
    definitions_by_qualified_name: dict[str, list[RawDefinitionFact]] = {}
    for definition in definitions_by_id.values():
        definitions_by_qualified_name.setdefault(definition.qualified_name, []).append(
            definition
        )
    unique_definitions_by_qualified_name = {
        qualified_name: definitions[0]
        for qualified_name, definitions in definitions_by_qualified_name.items()
        if len(definitions) == 1
    }
    module_symbol_ids_by_name = {
        definition.qualified_name: definition.definition_id
        for definition in definitions_by_id.values()
        if definition.kind is DefinitionKind.MODULE
        and definition.definition_id in program.resolved_symbols
    }
    binding_by_symbol_id = {binding.symbol_id: binding for binding in program.bindings}
    bindings_by_scope: dict[str, list[BindingFact]] = {}
    for binding in program.bindings:
        bindings_by_scope.setdefault(binding.scope_id, []).append(binding)
    parameters_by_owner_definition_id: dict[str, list[ParameterFact]] = {}
    for parameter in program.syntax.parameters:
        if parameter.owner_definition_id not in definitions_by_id:
            continue
        parameters_by_owner_definition_id.setdefault(
            parameter.owner_definition_id,
            [],
        ).append(parameter)
    methods_by_class_and_name: dict[tuple[str, str], list[RawDefinitionFact]] = {}
    class_attributes_by_class_and_name: dict[tuple[str, str], list[BindingFact]] = {}
    class_ids_with_getattribute_method: set[str] = set()
    for definition in definitions_by_id.values():
        if definition.kind is not DefinitionKind.METHOD:
            continue
        parent_definition_id = definition.parent_definition_id
        if parent_definition_id is None:
            continue
        if definition.name == "__getattribute__":
            class_ids_with_getattribute_method.add(parent_definition_id)
        methods_by_class_and_name.setdefault(
            (parent_definition_id, definition.name),
            [],
        ).append(definition)
    for binding in program.bindings:
        if binding.binding_kind is not BindingKind.CLASS_ATTRIBUTE:
            continue
        class_definition = definitions_by_id.get(binding.scope_id)
        if (
            class_definition is None
            or class_definition.kind is not DefinitionKind.CLASS
        ):
            continue
        class_attributes_by_class_and_name.setdefault(
            (binding.scope_id, binding.name),
            [],
        ).append(binding)

    return _RepositoryIndex(
        blocked_file_ids=blocked_file_ids,
        source_files_by_id=dict(program.syntax.source_files),
        definitions_by_id=definitions_by_id,
        unique_definitions_by_qualified_name=unique_definitions_by_qualified_name,
        module_symbol_ids_by_name=module_symbol_ids_by_name,
        scope_parent_ids={
            definition.definition_id: definition.parent_definition_id
            for definition in definitions_by_id.values()
        },
        scope_kinds={
            definition.definition_id: definition.kind
            for definition in definitions_by_id.values()
        },
        binding_by_symbol_id=binding_by_symbol_id,
        bindings_by_scope=bindings_by_scope,
        parameters_by_owner_definition_id={
            owner_definition_id: tuple(owner_parameters)
            for owner_definition_id, owner_parameters in (
                parameters_by_owner_definition_id.items()
            )
        },
        methods_by_class_and_name={
            method_key: tuple(method_definitions)
            for method_key, method_definitions in methods_by_class_and_name.items()
        },
        unique_methods_by_class_and_name={
            method_key: method_definitions[0]
            for method_key, method_definitions in methods_by_class_and_name.items()
            if len(method_definitions) == 1
        },
        class_attributes_by_class_and_name={
            attribute_key: tuple(attribute_bindings)
            for attribute_key, attribute_bindings in (
                class_attributes_by_class_and_name.items()
            )
        },
        unique_class_attributes_by_class_and_name={
            attribute_key: attribute_bindings[0]
            for attribute_key, attribute_bindings in (
                class_attributes_by_class_and_name.items()
            )
            if len(attribute_bindings) == 1
        },
        class_ids_with_getattribute_method=frozenset(
            class_ids_with_getattribute_method
        ),
        decorated_definition_ids=frozenset(
            decorator.owner_definition_id
            for decorator in program.syntax.decorators
            if decorator.owner_definition_id in definitions_by_id
        ),
    )


def _resolve_imports(
    program: SemanticProgram,
    index: _RepositoryIndex,
) -> list[ResolvedImport]:
    """Resolve supported import bindings to repository or narrow external targets."""
    resolved_imports: list[ResolvedImport] = []
    for import_fact in program.syntax.imports:
        if (
            import_fact.file_id in index.blocked_file_ids
            or import_fact.kind is ImportKind.STAR_IMPORT
        ):
            continue
        binding = index.binding_by_symbol_id.get(import_fact.import_id)
        if binding is None:
            continue
        source_file = index.source_files_by_id.get(import_fact.file_id)
        if source_file is None:
            continue
        absolute_module_name = _absolute_import_module_name(
            import_fact=import_fact,
            source_file=source_file,
        )
        if absolute_module_name is None:
            continue
        resolved_import = _resolve_import_target(
            import_fact=import_fact,
            binding=binding,
            absolute_module_name=absolute_module_name,
            index=index,
        )
        if resolved_import is not None:
            resolved_imports.append(resolved_import)
    return resolved_imports


def _resolve_import_target(
    *,
    import_fact: ImportFact,
    binding: BindingFact,
    absolute_module_name: str,
    index: _RepositoryIndex,
) -> ResolvedImport | None:
    """Return the proven target for one import binding, if supported."""
    if import_fact.kind is ImportKind.IMPORT:
        if absolute_module_name == "dataclasses":
            return ResolvedImport(
                import_id=import_fact.import_id,
                binding_symbol_id=binding.symbol_id,
                bound_name=binding.name,
                scope_id=import_fact.scope_id,
                site=import_fact.site,
                target_kind=ImportTargetKind.EXTERNAL,
                target_qualified_name="dataclasses",
            )
        target_module_name = absolute_module_name
        if import_fact.alias is None and "." in absolute_module_name:
            if absolute_module_name not in index.module_symbol_ids_by_name:
                return None
            target_module_name = absolute_module_name.split(".", maxsplit=1)[0]
        target_symbol_id = index.module_symbol_ids_by_name.get(target_module_name)
        if target_symbol_id is None:
            return None
        return ResolvedImport(
            import_id=import_fact.import_id,
            binding_symbol_id=binding.symbol_id,
            bound_name=binding.name,
            scope_id=import_fact.scope_id,
            site=import_fact.site,
            target_kind=ImportTargetKind.MODULE,
            target_qualified_name=target_module_name,
            target_symbol_id=target_symbol_id,
        )

    imported_name = import_fact.imported_name
    if imported_name is None:
        return None
    if absolute_module_name == "dataclasses" and imported_name == "dataclass":
        return ResolvedImport(
            import_id=import_fact.import_id,
            binding_symbol_id=binding.symbol_id,
            bound_name=binding.name,
            scope_id=import_fact.scope_id,
            site=import_fact.site,
            target_kind=ImportTargetKind.EXTERNAL,
            target_qualified_name="dataclasses.dataclass",
        )

    target_qualified_name = f"{absolute_module_name}.{imported_name}"
    target_definition = index.unique_definitions_by_qualified_name.get(
        target_qualified_name
    )
    if target_definition is not None:
        if target_definition.kind is DefinitionKind.MODULE:
            return ResolvedImport(
                import_id=import_fact.import_id,
                binding_symbol_id=binding.symbol_id,
                bound_name=binding.name,
                scope_id=import_fact.scope_id,
                site=import_fact.site,
                target_kind=ImportTargetKind.MODULE,
                target_qualified_name=target_qualified_name,
                target_symbol_id=target_definition.definition_id,
            )
        return ResolvedImport(
            import_id=import_fact.import_id,
            binding_symbol_id=binding.symbol_id,
            bound_name=binding.name,
            scope_id=import_fact.scope_id,
            site=import_fact.site,
            target_kind=ImportTargetKind.DEFINITION,
            target_qualified_name=target_qualified_name,
            target_symbol_id=target_definition.definition_id,
        )

    target_symbol_id = index.module_symbol_ids_by_name.get(target_qualified_name)
    if target_symbol_id is None:
        return None
    return ResolvedImport(
        import_id=import_fact.import_id,
        binding_symbol_id=binding.symbol_id,
        bound_name=binding.name,
        scope_id=import_fact.scope_id,
        site=import_fact.site,
        target_kind=ImportTargetKind.MODULE,
        target_qualified_name=target_qualified_name,
        target_symbol_id=target_symbol_id,
    )


def _absolute_import_module_name(
    *,
    import_fact: ImportFact,
    source_file: SourceFileFact,
) -> str | None:
    """Return the absolute dotted module name represented by ``import_fact``."""
    if not import_fact.is_relative:
        return import_fact.module_name

    raw_module_name = import_fact.module_name
    level = len(raw_module_name) - len(raw_module_name.lstrip("."))
    suffix = raw_module_name[level:]
    if level == 0:
        return raw_module_name

    current_package_parts = _current_package_parts(source_file)
    parent_levels = level - 1
    if parent_levels > len(current_package_parts):
        return None
    base_parts = current_package_parts[: len(current_package_parts) - parent_levels]
    suffix_parts = [part for part in suffix.split(".") if part]
    absolute_parts = [*base_parts, *suffix_parts]
    return ".".join(absolute_parts)


def _current_package_parts(source_file: SourceFileFact) -> list[str]:
    """Return the package parts that relative imports resolve against."""
    module_parts = [part for part in source_file.module_name.split(".") if part]
    if source_file.path.endswith("__init__.py"):
        return module_parts
    if not module_parts:
        return []
    return module_parts[:-1]


def _resolve_references(
    program: SemanticProgram,
    index: _RepositoryIndex,
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport],
) -> list[ResolvedReference]:
    """Resolve supported decorator, base, call, and narrow attribute surfaces."""
    resolved_references: list[ResolvedReference] = []

    for decorator in program.syntax.decorators:
        if decorator.site.file_path not in _valid_file_paths(index):
            continue
        resolved_reference = _resolve_decorator_reference(
            decorator=decorator,
            index=index,
            program=program,
            resolved_imports_by_binding_symbol_id=resolved_imports_by_binding_symbol_id,
        )
        if resolved_reference is not None:
            resolved_references.append(resolved_reference)

    (
        base_class_references,
        direct_proven_base_class_ids_by_class_id,
    ) = _resolve_base_class_references(
        program=program,
        index=index,
        resolved_imports_by_binding_symbol_id=resolved_imports_by_binding_symbol_id,
    )
    resolved_references.extend(base_class_references)

    for call_site in program.syntax.call_sites:
        if call_site.site.file_path not in _valid_file_paths(index):
            continue
        resolved_reference = _resolve_call_reference(
            call_site=call_site,
            index=index,
            program=program,
            resolved_imports_by_binding_symbol_id=resolved_imports_by_binding_symbol_id,
            direct_proven_base_class_ids_by_class_id=direct_proven_base_class_ids_by_class_id,
        )
        if resolved_reference is not None:
            resolved_references.append(resolved_reference)

    for attribute_site in program.syntax.attribute_sites:
        if (
            attribute_site.context is not ReferenceContext.ATTRIBUTE_ACCESS
            or attribute_site.site.file_path not in _valid_file_paths(index)
        ):
            continue
        resolved_reference = _resolve_attribute_reference(
            attribute_site=attribute_site,
            index=index,
            direct_proven_base_class_ids_by_class_id=direct_proven_base_class_ids_by_class_id,
        )
        if resolved_reference is not None:
            resolved_references.append(resolved_reference)

    return resolved_references


def _resolve_base_class_references(
    *,
    program: SemanticProgram,
    index: _RepositoryIndex,
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport],
) -> tuple[list[ResolvedReference], _DirectProvenBaseClassIdsByClassId]:
    """Resolve base references and preserve proven direct-base declaration order."""
    resolved_references: list[ResolvedReference] = []
    mutable_direct_proven_base_class_ids_by_class_id: dict[str, list[str]] = {}

    for base_expression in program.syntax.base_expressions:
        owner_definition = index.definitions_by_id.get(
            base_expression.owner_definition_id
        )
        if owner_definition is None:
            continue
        evaluation_scope_id = owner_definition.parent_definition_id
        if evaluation_scope_id is None:
            continue
        resolved_reference = _resolve_expression_reference(
            reference_id=f"reference:{base_expression.base_expression_id}",
            expression_text=base_expression.expression_text,
            site=base_expression.site,
            context=ReferenceContext.BASE_CLASS,
            scope_id=evaluation_scope_id,
            program=program,
            index=index,
            resolved_imports_by_binding_symbol_id=resolved_imports_by_binding_symbol_id,
            direct_proven_base_class_ids_by_class_id={},
            require_repository_symbol=False,
            excluded_definition_symbol_id=owner_definition.definition_id,
        )
        if resolved_reference is None:
            continue
        resolved_references.append(resolved_reference)
        target_definition = index.definitions_by_id.get(
            resolved_reference.resolved_symbol_id
        )
        if (
            target_definition is None
            or target_definition.kind is not DefinitionKind.CLASS
        ):
            continue
        mutable_direct_proven_base_class_ids_by_class_id.setdefault(
            owner_definition.definition_id,
            [],
        ).append(resolved_reference.resolved_symbol_id)

    return (
        resolved_references,
        {
            class_definition_id: tuple(base_class_ids)
            for class_definition_id, base_class_ids in (
                mutable_direct_proven_base_class_ids_by_class_id.items()
            )
        },
    )


def _resolve_decorator_reference(
    *,
    decorator: DecoratorFact,
    index: _RepositoryIndex,
    program: SemanticProgram,
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport],
) -> ResolvedReference | None:
    """Resolve one supported decorator surface."""
    owner_definition = index.definitions_by_id.get(decorator.owner_definition_id)
    if owner_definition is None:
        return None
    evaluation_scope_id = owner_definition.parent_definition_id
    if evaluation_scope_id is None:
        return None
    return _resolve_expression_reference(
        reference_id=f"reference:{decorator.decorator_id}",
        expression_text=decorator.expression_text,
        site=decorator.site,
        context=ReferenceContext.DECORATOR,
        scope_id=evaluation_scope_id,
        program=program,
        index=index,
        resolved_imports_by_binding_symbol_id=resolved_imports_by_binding_symbol_id,
        direct_proven_base_class_ids_by_class_id={},
        require_repository_symbol=False,
        excluded_definition_symbol_id=owner_definition.definition_id,
    )


def _resolve_call_reference(
    *,
    call_site: CallSiteFact,
    index: _RepositoryIndex,
    program: SemanticProgram,
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport],
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> ResolvedReference | None:
    """Resolve one supported call-site callee when it targets a repository symbol."""
    return _resolve_expression_reference(
        reference_id=f"reference:{call_site.call_site_id}",
        expression_text=call_site.callee_text,
        site=call_site.site,
        context=ReferenceContext.CALL,
        scope_id=call_site.enclosing_scope_id,
        program=program,
        index=index,
        resolved_imports_by_binding_symbol_id=resolved_imports_by_binding_symbol_id,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
        require_repository_symbol=True,
        excluded_definition_symbol_id=None,
    )


def _resolve_attribute_reference(
    *,
    attribute_site: AttributeSiteFact,
    index: _RepositoryIndex,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> ResolvedReference | None:
    """Resolve one narrow same-class ``self.<name>`` attribute-read site."""
    if attribute_site.base_text != "self":
        return None
    binding = _lookup_visible_binding(
        name="self",
        scope_id=attribute_site.enclosing_scope_id,
        site=attribute_site.site,
        index=index,
        excluded_definition_symbol_id=None,
    )
    if binding is None:
        return None
    resolved_symbol_id = _resolve_same_class_self_attribute_symbol_id(
        base_binding=binding,
        attribute_name=attribute_site.attribute_name,
        scope_id=attribute_site.enclosing_scope_id,
        context=attribute_site.context,
        index=index,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    )
    if resolved_symbol_id is None:
        return None
    return ResolvedReference(
        reference_id=f"reference:{attribute_site.attribute_site_id}",
        site=attribute_site.site,
        name=f"{attribute_site.base_text}.{attribute_site.attribute_name}",
        context=attribute_site.context,
        resolved_symbol_id=resolved_symbol_id,
        enclosing_scope_id=attribute_site.enclosing_scope_id,
    )


def _resolve_expression_reference(
    *,
    reference_id: str,
    expression_text: str,
    site: SourceSite,
    context: ReferenceContext,
    scope_id: str,
    program: SemanticProgram,
    index: _RepositoryIndex,
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport],
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
    require_repository_symbol: bool,
    excluded_definition_symbol_id: str | None,
) -> ResolvedReference | None:
    """Resolve one supported expression surface into a concrete reference."""
    expression = _parse_supported_expression(expression_text)
    if expression is None:
        return None

    if isinstance(expression, _SimpleNameExpression):
        binding = _lookup_visible_binding(
            name=expression.name,
            scope_id=scope_id,
            site=site,
            index=index,
            excluded_definition_symbol_id=excluded_definition_symbol_id,
        )
        if binding is None:
            return None
        resolved_symbol_id = _resolve_simple_binding_symbol_id(
            binding=binding,
            program=program,
            resolved_imports_by_binding_symbol_id=resolved_imports_by_binding_symbol_id,
            require_repository_symbol=require_repository_symbol,
        )
        if resolved_symbol_id is None:
            return None
        return ResolvedReference(
            reference_id=reference_id,
            site=site,
            name=expression_text,
            context=context,
            resolved_symbol_id=resolved_symbol_id,
            enclosing_scope_id=scope_id,
        )

    binding = _lookup_visible_binding(
        name=expression.root_name,
        scope_id=scope_id,
        site=site,
        index=index,
        excluded_definition_symbol_id=excluded_definition_symbol_id,
    )
    if binding is None:
        return None
    same_class_self_target_symbol_id = None
    if len(expression.attribute_names) == 1:
        same_class_self_target_symbol_id = _resolve_same_class_self_call_symbol_id(
            base_binding=binding,
            attribute_name=expression.attribute_names[0],
            scope_id=scope_id,
            context=context,
            index=index,
            direct_proven_base_class_ids_by_class_id=(
                direct_proven_base_class_ids_by_class_id
            ),
        )
    if same_class_self_target_symbol_id is not None:
        return ResolvedReference(
            reference_id=reference_id,
            site=site,
            name=expression_text,
            context=context,
            resolved_symbol_id=same_class_self_target_symbol_id,
            enclosing_scope_id=scope_id,
        )
    direct_base_self_target_symbol_id = None
    if len(expression.attribute_names) == 1:
        direct_base_self_target_symbol_id = _resolve_direct_base_self_call_symbol_id(
            base_binding=binding,
            attribute_name=expression.attribute_names[0],
            scope_id=scope_id,
            context=context,
            index=index,
            direct_proven_base_class_ids_by_class_id=(
                direct_proven_base_class_ids_by_class_id
            ),
        )
    if direct_base_self_target_symbol_id is not None:
        return ResolvedReference(
            reference_id=reference_id,
            site=site,
            name=expression_text,
            context=context,
            resolved_symbol_id=direct_base_self_target_symbol_id,
            enclosing_scope_id=scope_id,
        )
    linear_transitive_self_target_symbol_id = None
    if len(expression.attribute_names) == 1:
        linear_transitive_self_target_symbol_id = (
            _resolve_linear_transitive_self_call_symbol_id(
                base_binding=binding,
                attribute_name=expression.attribute_names[0],
                scope_id=scope_id,
                context=context,
                index=index,
                direct_proven_base_class_ids_by_class_id=(
                    direct_proven_base_class_ids_by_class_id
                ),
            )
        )
    if linear_transitive_self_target_symbol_id is not None:
        return ResolvedReference(
            reference_id=reference_id,
            site=site,
            name=expression_text,
            context=context,
            resolved_symbol_id=linear_transitive_self_target_symbol_id,
            enclosing_scope_id=scope_id,
        )
    branched_self_target_symbol_id = None
    if len(expression.attribute_names) == 1:
        branched_self_target_symbol_id = (
            _resolve_declared_order_branched_self_call_symbol_id(
                base_binding=binding,
                attribute_name=expression.attribute_names[0],
                scope_id=scope_id,
                context=context,
                index=index,
                direct_proven_base_class_ids_by_class_id=(
                    direct_proven_base_class_ids_by_class_id
                ),
            )
        )
    if branched_self_target_symbol_id is not None:
        return ResolvedReference(
            reference_id=reference_id,
            site=site,
            name=expression_text,
            context=context,
            resolved_symbol_id=branched_self_target_symbol_id,
            enclosing_scope_id=scope_id,
        )
    overlapping_self_target_symbol_id = None
    if len(expression.attribute_names) == 1:
        overlapping_self_target_symbol_id = (
            _resolve_first_owner_overlapping_self_call_symbol_id(
                base_binding=binding,
                attribute_name=expression.attribute_names[0],
                scope_id=scope_id,
                context=context,
                index=index,
                direct_proven_base_class_ids_by_class_id=(
                    direct_proven_base_class_ids_by_class_id
                ),
            )
        )
    if overlapping_self_target_symbol_id is not None:
        return ResolvedReference(
            reference_id=reference_id,
            site=site,
            name=expression_text,
            context=context,
            resolved_symbol_id=overlapping_self_target_symbol_id,
            enclosing_scope_id=scope_id,
        )
    transitive_self_target_symbol_id = None
    if len(expression.attribute_names) == 1:
        transitive_self_target_symbol_id = (
            _resolve_transitive_sole_provider_self_call_symbol_id(
                base_binding=binding,
                attribute_name=expression.attribute_names[0],
                scope_id=scope_id,
                context=context,
                index=index,
                direct_proven_base_class_ids_by_class_id=(
                    direct_proven_base_class_ids_by_class_id
                ),
            )
        )
    if transitive_self_target_symbol_id is not None:
        return ResolvedReference(
            reference_id=reference_id,
            site=site,
            name=expression_text,
            context=context,
            resolved_symbol_id=transitive_self_target_symbol_id,
            enclosing_scope_id=scope_id,
        )
    if binding.binding_kind is not BindingKind.IMPORT:
        return None
    resolved_symbol_id = _resolve_import_rooted_attribute_chain_symbol_id(
        base_binding=binding,
        attribute_names=expression.attribute_names,
        program=program,
        resolved_imports_by_binding_symbol_id=resolved_imports_by_binding_symbol_id,
        index=index,
        require_repository_symbol=require_repository_symbol,
    )
    if resolved_symbol_id is None:
        return None
    return ResolvedReference(
        reference_id=reference_id,
        site=site,
        name=expression_text,
        context=context,
        resolved_symbol_id=resolved_symbol_id,
        enclosing_scope_id=scope_id,
    )


def _resolve_same_class_self_attribute_symbol_id(
    *,
    base_binding: BindingFact,
    attribute_name: str,
    scope_id: str,
    context: ReferenceContext,
    index: _RepositoryIndex,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> str | None:
    """Return a same-class class-attribute target for narrow ``self.attr`` proof."""
    class_definition_id = _narrow_self_attribute_owner_class_id(
        base_binding=base_binding,
        scope_id=scope_id,
        context=context,
        index=index,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    )
    if class_definition_id is None:
        return None
    target_attribute_binding = _resolve_unique_class_attribute_binding(
        class_definition_id=class_definition_id,
        attribute_name=attribute_name,
        index=index,
    )
    if target_attribute_binding is None:
        return None
    return target_attribute_binding.symbol_id


def _resolve_same_class_self_call_symbol_id(
    *,
    base_binding: BindingFact,
    attribute_name: str,
    scope_id: str,
    context: ReferenceContext,
    index: _RepositoryIndex,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> str | None:
    """Return a same-class method target for narrow ``self.foo()`` call proof."""
    class_definition_id = _narrow_self_call_owner_class_id(
        base_binding=base_binding,
        scope_id=scope_id,
        context=context,
        index=index,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    )
    if class_definition_id is None:
        return None
    target_method = _resolve_unique_owned_undecorated_method_definition(
        class_definition_id=class_definition_id,
        attribute_name=attribute_name,
        index=index,
    )
    if target_method is None:
        return None
    return target_method.definition_id


def _resolve_direct_base_self_call_symbol_id(
    *,
    base_binding: BindingFact,
    attribute_name: str,
    scope_id: str,
    context: ReferenceContext,
    index: _RepositoryIndex,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> str | None:
    """Return a direct-base method target for narrow inherited ``self.foo()`` proof."""
    if attribute_name in {"__getattr__", "__getattribute__"}:
        return None
    class_definition_id = _narrow_self_call_owner_class_id(
        base_binding=base_binding,
        scope_id=scope_id,
        context=context,
        index=index,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    )
    if class_definition_id is None:
        return None
    if (
        _latest_class_namespace_binding(
            class_definition_id=class_definition_id,
            attribute_name=attribute_name,
            index=index,
        )
        is not None
    ):
        return None

    direct_base_class_definition_ids = direct_proven_base_class_ids_by_class_id.get(
        class_definition_id,
        (),
    )
    if len(direct_base_class_definition_ids) != 1:
        return None
    direct_base_class_definition_id = direct_base_class_definition_ids[0]
    latest_base_namespace_binding = _latest_class_namespace_binding(
        class_definition_id=direct_base_class_definition_id,
        attribute_name=attribute_name,
        index=index,
    )
    if latest_base_namespace_binding is None:
        return None
    base_target_method = _resolve_unique_owned_undecorated_method_definition(
        class_definition_id=direct_base_class_definition_id,
        attribute_name=attribute_name,
        index=index,
    )
    if base_target_method is None:
        return None
    return base_target_method.definition_id


def _resolve_transitive_sole_provider_self_call_symbol_id(
    *,
    base_binding: BindingFact,
    attribute_name: str,
    scope_id: str,
    context: ReferenceContext,
    index: _RepositoryIndex,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> str | None:
    """Return one transitive sole-provider target for narrow inherited calls."""
    if attribute_name in {"__getattr__", "__getattribute__"}:
        return None
    class_definition_id = _narrow_self_call_owner_class_id(
        base_binding=base_binding,
        scope_id=scope_id,
        context=context,
        index=index,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    )
    if class_definition_id is None:
        return None
    if (
        _latest_class_namespace_binding(
            class_definition_id=class_definition_id,
            attribute_name=attribute_name,
            index=index,
        )
        is not None
    ):
        return None

    direct_base_class_definition_ids = direct_proven_base_class_ids_by_class_id.get(
        class_definition_id,
        (),
    )
    if len(direct_base_class_definition_ids) > 1 and (
        not _direct_base_branches_are_individually_linear(
            direct_base_class_definition_ids=direct_base_class_definition_ids,
            direct_proven_base_class_ids_by_class_id=(
                direct_proven_base_class_ids_by_class_id
            ),
        )
    ):
        return None
    for base_class_definition_id in direct_base_class_definition_ids:
        if (
            _latest_class_namespace_binding(
                class_definition_id=base_class_definition_id,
                attribute_name=attribute_name,
                index=index,
            )
            is not None
        ):
            return None

    matching_target_method: RawDefinitionFact | None = None
    for ancestor_class_definition_id in _transitively_proven_ancestor_class_ids(
        class_definition_id=class_definition_id,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    ):
        if ancestor_class_definition_id in direct_base_class_definition_ids:
            continue
        latest_ancestor_namespace_binding = _latest_class_namespace_binding(
            class_definition_id=ancestor_class_definition_id,
            attribute_name=attribute_name,
            index=index,
        )
        if latest_ancestor_namespace_binding is None:
            continue
        ancestor_target_method = _resolve_unique_owned_undecorated_method_definition(
            class_definition_id=ancestor_class_definition_id,
            attribute_name=attribute_name,
            index=index,
        )
        if ancestor_target_method is None:
            return None
        if matching_target_method is not None:
            return None
        matching_target_method = ancestor_target_method
    if matching_target_method is None:
        return None
    return matching_target_method.definition_id


def _resolve_linear_transitive_self_call_symbol_id(
    *,
    base_binding: BindingFact,
    attribute_name: str,
    scope_id: str,
    context: ReferenceContext,
    index: _RepositoryIndex,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> str | None:
    """Return the first eligible transitive owner on one unique proven chain."""
    if attribute_name in {"__getattr__", "__getattribute__"}:
        return None
    class_definition_id = _narrow_self_call_owner_class_id(
        base_binding=base_binding,
        scope_id=scope_id,
        context=context,
        index=index,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    )
    if class_definition_id is None:
        return None
    if (
        _latest_class_namespace_binding(
            class_definition_id=class_definition_id,
            attribute_name=attribute_name,
            index=index,
        )
        is not None
    ):
        return None

    current_class_definition_id = _resolve_unique_proven_base_class_id(
        class_definition_id=class_definition_id,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    )
    if current_class_definition_id is None:
        return None
    direct_base_class_definition_id = current_class_definition_id

    while True:
        latest_namespace_binding = _latest_class_namespace_binding(
            class_definition_id=current_class_definition_id,
            attribute_name=attribute_name,
            index=index,
        )
        if latest_namespace_binding is not None:
            if current_class_definition_id == direct_base_class_definition_id:
                return None
            target_method = _resolve_unique_owned_undecorated_method_definition(
                class_definition_id=current_class_definition_id,
                attribute_name=attribute_name,
                index=index,
            )
            if target_method is None:
                return None
            return target_method.definition_id

        next_class_definition_id = _resolve_unique_proven_base_class_id(
            class_definition_id=current_class_definition_id,
            direct_proven_base_class_ids_by_class_id=(
                direct_proven_base_class_ids_by_class_id
            ),
        )
        if next_class_definition_id is None:
            return None
        current_class_definition_id = next_class_definition_id


def _resolve_declared_order_branched_self_call_symbol_id(
    *,
    base_binding: BindingFact,
    attribute_name: str,
    scope_id: str,
    context: ReferenceContext,
    index: _RepositoryIndex,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> str | None:
    """Return the earliest eligible owner across linear declared-order branches."""
    if attribute_name in {"__getattr__", "__getattribute__"}:
        return None
    class_definition_id = _narrow_self_call_owner_class_id(
        base_binding=base_binding,
        scope_id=scope_id,
        context=context,
        index=index,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    )
    if class_definition_id is None:
        return None
    if (
        _latest_class_namespace_binding(
            class_definition_id=class_definition_id,
            attribute_name=attribute_name,
            index=index,
        )
        is not None
    ):
        return None

    direct_base_class_definition_ids = direct_proven_base_class_ids_by_class_id.get(
        class_definition_id,
        (),
    )
    if len(direct_base_class_definition_ids) < 2:
        return None
    ordered_branch_class_definition_ids = (
        _ordered_linear_disjoint_branch_class_definition_ids(
            direct_base_class_definition_ids=direct_base_class_definition_ids,
            direct_proven_base_class_ids_by_class_id=(
                direct_proven_base_class_ids_by_class_id
            ),
        )
    )
    if ordered_branch_class_definition_ids is None:
        return None

    for branch_class_definition_ids in ordered_branch_class_definition_ids:
        for branch_class_definition_id in branch_class_definition_ids:
            latest_namespace_binding = _latest_class_namespace_binding(
                class_definition_id=branch_class_definition_id,
                attribute_name=attribute_name,
                index=index,
            )
            if latest_namespace_binding is None:
                continue
            target_method = _resolve_unique_owned_undecorated_method_definition(
                class_definition_id=branch_class_definition_id,
                attribute_name=attribute_name,
                index=index,
            )
            if target_method is None:
                return None
            return target_method.definition_id
    return None


def _resolve_first_owner_overlapping_self_call_symbol_id(
    *,
    base_binding: BindingFact,
    attribute_name: str,
    scope_id: str,
    context: ReferenceContext,
    index: _RepositoryIndex,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> str | None:
    """Return the first eligible exclusive-branch owner before a shared tail."""
    if attribute_name in {"__getattr__", "__getattribute__"}:
        return None
    class_definition_id = _narrow_self_call_owner_class_id(
        base_binding=base_binding,
        scope_id=scope_id,
        context=context,
        index=index,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    )
    if class_definition_id is None:
        return None
    if (
        _latest_class_namespace_binding(
            class_definition_id=class_definition_id,
            attribute_name=attribute_name,
            index=index,
        )
        is not None
    ):
        return None

    direct_base_class_definition_ids = direct_proven_base_class_ids_by_class_id.get(
        class_definition_id,
        (),
    )
    if len(direct_base_class_definition_ids) < 2:
        return None
    ordered_branch_class_definition_ids = _ordered_linear_branch_class_definition_ids(
        direct_base_class_definition_ids=direct_base_class_definition_ids,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    )
    if ordered_branch_class_definition_ids is None:
        return None
    shared_tail_class_definition_ids = _shared_branch_tail_class_definition_ids(
        ordered_branch_class_definition_ids=ordered_branch_class_definition_ids
    )
    if not shared_tail_class_definition_ids:
        return None

    shared_tail_length = len(shared_tail_class_definition_ids)
    for branch_class_definition_ids in ordered_branch_class_definition_ids:
        exclusive_branch_class_definition_ids = branch_class_definition_ids[
            :-shared_tail_length
        ]
        for branch_class_definition_id in exclusive_branch_class_definition_ids:
            latest_namespace_binding = _latest_class_namespace_binding(
                class_definition_id=branch_class_definition_id,
                attribute_name=attribute_name,
                index=index,
            )
            if latest_namespace_binding is None:
                continue
            target_method = _resolve_unique_owned_undecorated_method_definition(
                class_definition_id=branch_class_definition_id,
                attribute_name=attribute_name,
                index=index,
            )
            if target_method is None:
                return None
            return target_method.definition_id

    return None


def _narrow_self_attribute_owner_class_id(
    *,
    base_binding: BindingFact,
    scope_id: str,
    context: ReferenceContext,
    index: _RepositoryIndex,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> str | None:
    """Return the owning class for one eligible narrow ``self.attr`` read."""
    if context is not ReferenceContext.ATTRIBUTE_ACCESS:
        return None
    if base_binding.binding_kind is not BindingKind.PARAMETER:
        return None
    method_definition = index.definitions_by_id.get(scope_id)
    if method_definition is None or method_definition.kind is not DefinitionKind.METHOD:
        return None
    if scope_id in index.decorated_definition_ids:
        return None
    if not _is_canonical_self_parameter(
        parameter_symbol_id=base_binding.symbol_id,
        method_definition_id=method_definition.definition_id,
        index=index,
    ):
        return None
    class_definition_id = method_definition.parent_definition_id
    if class_definition_id is None:
        return None
    if class_definition_id in index.class_ids_with_getattribute_method:
        return None
    if _has_transitively_proven_ancestor_with_getattribute(
        class_definition_id=class_definition_id,
        index=index,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    ):
        return None
    return class_definition_id


def _narrow_self_call_owner_class_id(
    *,
    base_binding: BindingFact,
    scope_id: str,
    context: ReferenceContext,
    index: _RepositoryIndex,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> str | None:
    """Return the owning class for one eligible narrow ``self.foo()`` call."""
    if context is not ReferenceContext.CALL:
        return None
    if base_binding.binding_kind is not BindingKind.PARAMETER:
        return None
    method_definition = index.definitions_by_id.get(scope_id)
    if method_definition is None or method_definition.kind is not DefinitionKind.METHOD:
        return None
    if scope_id in index.decorated_definition_ids:
        return None
    if not _is_canonical_self_parameter(
        parameter_symbol_id=base_binding.symbol_id,
        method_definition_id=method_definition.definition_id,
        index=index,
    ):
        return None
    class_definition_id = method_definition.parent_definition_id
    if class_definition_id is None:
        return None
    if class_definition_id in index.class_ids_with_getattribute_method:
        return None
    if _has_transitively_proven_ancestor_with_getattribute(
        class_definition_id=class_definition_id,
        index=index,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    ):
        return None
    return class_definition_id


def _resolve_unique_class_attribute_binding(
    *,
    class_definition_id: str,
    attribute_name: str,
    index: _RepositoryIndex,
) -> BindingFact | None:
    """Return the unique same-class class attribute if it still owns the name."""
    target_attribute_binding = index.unique_class_attributes_by_class_and_name.get(
        (class_definition_id, attribute_name)
    )
    if target_attribute_binding is None:
        return None
    latest_class_namespace_binding = _latest_class_namespace_binding(
        class_definition_id=class_definition_id,
        attribute_name=attribute_name,
        index=index,
    )
    if (
        latest_class_namespace_binding is None
        or latest_class_namespace_binding.binding_kind
        is not BindingKind.CLASS_ATTRIBUTE
        or latest_class_namespace_binding.symbol_id
        != target_attribute_binding.symbol_id
    ):
        return None
    return target_attribute_binding


def _resolve_unique_owned_undecorated_method_definition(
    *,
    class_definition_id: str,
    attribute_name: str,
    index: _RepositoryIndex,
) -> RawDefinitionFact | None:
    """Return the unique undecorated method if it still owns the class name."""
    target_method = _resolve_unique_undecorated_method_definition(
        class_definition_id=class_definition_id,
        attribute_name=attribute_name,
        index=index,
    )
    if target_method is None:
        return None
    latest_class_namespace_binding = _latest_class_namespace_binding(
        class_definition_id=class_definition_id,
        attribute_name=attribute_name,
        index=index,
    )
    if (
        latest_class_namespace_binding is None
        or latest_class_namespace_binding.binding_kind is not BindingKind.DEFINITION
        or latest_class_namespace_binding.symbol_id != target_method.definition_id
    ):
        return None
    return target_method


def _latest_class_namespace_binding(
    *,
    class_definition_id: str,
    attribute_name: str,
    index: _RepositoryIndex,
) -> BindingFact | None:
    """Return the final class-scope binding for one name after class-body execution."""
    for binding in reversed(index.bindings_by_scope.get(class_definition_id, [])):
        if binding.name == attribute_name:
            return binding
    return None


def _resolve_unique_undecorated_method_definition(
    *,
    class_definition_id: str,
    attribute_name: str,
    index: _RepositoryIndex,
) -> RawDefinitionFact | None:
    """Return the unique undecorated method with ``attribute_name``, if any."""
    target_method = index.unique_methods_by_class_and_name.get(
        (class_definition_id, attribute_name)
    )
    if (
        target_method is None
        or target_method.definition_id in index.decorated_definition_ids
    ):
        return None
    return target_method


def _has_transitively_proven_ancestor_with_getattribute(
    *,
    class_definition_id: str,
    index: _RepositoryIndex,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> bool:
    """Return whether any proven ancestor defines ``__getattribute__``."""
    return any(
        ancestor_class_definition_id in index.class_ids_with_getattribute_method
        for ancestor_class_definition_id in _transitively_proven_ancestor_class_ids(
            class_definition_id=class_definition_id,
            direct_proven_base_class_ids_by_class_id=(
                direct_proven_base_class_ids_by_class_id
            ),
        )
    )


def _transitively_proven_ancestor_class_ids(
    *,
    class_definition_id: str,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> tuple[str, ...]:
    """Return the repository-class ancestor closure for one proven class."""
    pending_class_definition_ids = list(
        reversed(
            direct_proven_base_class_ids_by_class_id.get(
                class_definition_id,
                (),
            )
        )
    )
    seen_class_definition_ids: set[str] = set()
    ordered_ancestor_class_definition_ids: list[str] = []
    while pending_class_definition_ids:
        candidate_class_definition_id = pending_class_definition_ids.pop()
        if candidate_class_definition_id in seen_class_definition_ids:
            continue
        seen_class_definition_ids.add(candidate_class_definition_id)
        ordered_ancestor_class_definition_ids.append(candidate_class_definition_id)
        pending_class_definition_ids.extend(
            reversed(
                direct_proven_base_class_ids_by_class_id.get(
                    candidate_class_definition_id,
                    (),
                )
            )
        )
    return tuple(ordered_ancestor_class_definition_ids)


def _resolve_unique_proven_base_class_id(
    *,
    class_definition_id: str,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> str | None:
    """Return one proven base only when the next hop is unbranched."""
    direct_base_class_definition_ids = direct_proven_base_class_ids_by_class_id.get(
        class_definition_id,
        (),
    )
    if len(direct_base_class_definition_ids) != 1:
        return None
    return direct_base_class_definition_ids[0]


def _direct_base_branches_are_individually_linear(
    *,
    direct_base_class_definition_ids: _OrderedClassDefinitionIds,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> bool:
    """Return whether each direct-base branch stays on one proven class chain."""
    for direct_base_class_definition_id in direct_base_class_definition_ids:
        seen_branch_class_definition_ids: set[str] = set()
        current_class_definition_id = direct_base_class_definition_id
        while True:
            if current_class_definition_id in seen_branch_class_definition_ids:
                return False
            seen_branch_class_definition_ids.add(current_class_definition_id)
            next_class_definition_ids = direct_proven_base_class_ids_by_class_id.get(
                current_class_definition_id,
                (),
            )
            if not next_class_definition_ids:
                break
            if len(next_class_definition_ids) != 1:
                return False
            current_class_definition_id = next_class_definition_ids[0]
    return True


def _ordered_linear_disjoint_branch_class_definition_ids(
    *,
    direct_base_class_definition_ids: _OrderedClassDefinitionIds,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> tuple[_OrderedClassDefinitionIds, ...] | None:
    """Return direct-base branch chains only when they stay linear and disjoint."""
    ordered_branch_class_definition_ids = _ordered_linear_branch_class_definition_ids(
        direct_base_class_definition_ids=direct_base_class_definition_ids,
        direct_proven_base_class_ids_by_class_id=(
            direct_proven_base_class_ids_by_class_id
        ),
    )
    if ordered_branch_class_definition_ids is None:
        return None
    seen_branch_class_definition_ids: set[str] = set()
    for branch_class_definition_ids in ordered_branch_class_definition_ids:
        for current_class_definition_id in branch_class_definition_ids:
            if current_class_definition_id in seen_branch_class_definition_ids:
                return None
            seen_branch_class_definition_ids.add(current_class_definition_id)
    return ordered_branch_class_definition_ids


def _ordered_linear_branch_class_definition_ids(
    *,
    direct_base_class_definition_ids: _OrderedClassDefinitionIds,
    direct_proven_base_class_ids_by_class_id: _DirectProvenBaseClassIdsByClassId,
) -> _OrderedBranchClassDefinitionIds | None:
    """Return direct-base branch chains only when each branch stays linear."""
    ordered_branch_class_definition_ids: list[_OrderedClassDefinitionIds] = []
    for direct_base_class_definition_id in direct_base_class_definition_ids:
        branch_class_definition_ids: list[str] = []
        current_class_definition_id = direct_base_class_definition_id
        seen_branch_class_definition_ids: set[str] = set()
        while True:
            if current_class_definition_id in seen_branch_class_definition_ids:
                return None
            seen_branch_class_definition_ids.add(current_class_definition_id)
            branch_class_definition_ids.append(current_class_definition_id)
            next_class_definition_ids = direct_proven_base_class_ids_by_class_id.get(
                current_class_definition_id,
                (),
            )
            if not next_class_definition_ids:
                break
            if len(next_class_definition_ids) != 1:
                return None
            current_class_definition_id = next_class_definition_ids[0]
        ordered_branch_class_definition_ids.append(tuple(branch_class_definition_ids))
    return tuple(ordered_branch_class_definition_ids)


def _shared_branch_tail_class_definition_ids(
    *,
    ordered_branch_class_definition_ids: _OrderedBranchClassDefinitionIds,
) -> _OrderedClassDefinitionIds:
    """Return the shared tail across linear branches in declared-order layout."""
    shared_tail_reversed: list[str] = []
    reversed_branch_class_definition_ids = [
        tuple(reversed(branch_class_definition_ids))
        for branch_class_definition_ids in ordered_branch_class_definition_ids
    ]
    for candidate_tail_class_definition_ids in zip(
        *reversed_branch_class_definition_ids,
        strict=False,
    ):
        shared_class_definition_id = candidate_tail_class_definition_ids[0]
        if any(
            candidate_class_definition_id != shared_class_definition_id
            for candidate_class_definition_id in candidate_tail_class_definition_ids[1:]
        ):
            break
        shared_tail_reversed.append(shared_class_definition_id)
    return tuple(reversed(shared_tail_reversed))


def _is_canonical_self_parameter(
    *,
    parameter_symbol_id: str,
    method_definition_id: str,
    index: _RepositoryIndex,
) -> bool:
    """Return whether ``parameter_symbol_id`` is the canonical first ``self``."""
    parameters = index.parameters_by_owner_definition_id.get(method_definition_id)
    if not parameters:
        return False
    first_parameter = min(parameters, key=lambda parameter: parameter.ordinal)
    return (
        first_parameter.parameter_id == parameter_symbol_id
        and first_parameter.name == "self"
        and first_parameter.kind
        in {
            ParameterKind.POSITIONAL_ONLY,
            ParameterKind.POSITIONAL_OR_KEYWORD,
        }
    )


def _lookup_visible_binding(
    *,
    name: str,
    scope_id: str,
    site: SourceSite,
    index: _RepositoryIndex,
    excluded_definition_symbol_id: str | None,
) -> BindingFact | None:
    """Return the nearest visible binding for ``name`` in lexical scope order."""
    current_scope_id: str | None = scope_id
    while current_scope_id is not None:
        for binding in reversed(index.bindings_by_scope.get(current_scope_id, [])):
            if binding.name != name:
                continue
            if not _binding_is_visible(
                binding=binding,
                site=site,
                excluded_definition_symbol_id=excluded_definition_symbol_id,
            ):
                continue
            return binding
        current_scope_id = _next_scope_id_for_lookup(current_scope_id, index)
    return None


def _binding_is_visible(
    *,
    binding: BindingFact,
    site: SourceSite,
    excluded_definition_symbol_id: str | None,
) -> bool:
    """Return whether ``binding`` is available at ``site`` conservatively."""
    if binding.site.file_path != site.file_path:
        return False
    if binding.binding_kind is BindingKind.PARAMETER:
        return True
    if binding.binding_kind is BindingKind.DEFINITION:
        if (
            excluded_definition_symbol_id is not None
            and binding.symbol_id == excluded_definition_symbol_id
        ):
            return False
        return _span_starts_before(binding.site.span, site.span)
    return _span_ends_before_or_at(binding.site.span, site.span)


def _next_scope_id_for_lookup(
    scope_id: str,
    index: _RepositoryIndex,
) -> str | None:
    """Return the next lexical scope to search, skipping class scopes for closures."""
    parent_scope_id = index.scope_parent_ids.get(scope_id)
    if parent_scope_id is None:
        return None
    current_kind = index.scope_kinds.get(scope_id)
    parent_kind = index.scope_kinds.get(parent_scope_id)
    if current_kind in _FUNCTION_LIKE_KINDS and parent_kind is DefinitionKind.CLASS:
        return index.scope_parent_ids.get(parent_scope_id)
    return parent_scope_id


def _resolve_simple_binding_symbol_id(
    *,
    binding: BindingFact,
    program: SemanticProgram,
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport],
    require_repository_symbol: bool,
) -> str | None:
    """Return the symbol targeted by a simple-name reference, if supported."""
    if binding.binding_kind is BindingKind.IMPORT:
        resolved_import = resolved_imports_by_binding_symbol_id.get(binding.symbol_id)
        if resolved_import is None:
            return None
        if (
            resolved_import.target_kind is ImportTargetKind.DEFINITION
            and resolved_import.target_symbol_id is not None
        ):
            if require_repository_symbol:
                target_symbol = program.resolved_symbols.get(
                    resolved_import.target_symbol_id
                )
                if (
                    target_symbol is None
                    or target_symbol.kind not in _CALLABLE_SYMBOL_KINDS
                ):
                    return None
            return resolved_import.target_symbol_id
        if require_repository_symbol:
            return None
        if (
            resolved_import.target_kind is ImportTargetKind.EXTERNAL
            and resolved_import.target_qualified_name == "dataclasses.dataclass"
        ):
            return binding.symbol_id
        return None

    symbol = program.resolved_symbols.get(binding.symbol_id)
    if symbol is None:
        return None
    if require_repository_symbol and symbol.kind not in _CALLABLE_SYMBOL_KINDS:
        return None
    return binding.symbol_id


def _resolve_import_rooted_attribute_chain_symbol_id(
    *,
    base_binding: BindingFact,
    attribute_names: tuple[str, ...],
    program: SemanticProgram,
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport],
    index: _RepositoryIndex,
    require_repository_symbol: bool,
) -> str | None:
    """Return the target for a narrow import-rooted attribute chain, if proven."""
    resolved_import = resolved_imports_by_binding_symbol_id.get(base_binding.symbol_id)
    if resolved_import is None:
        return None

    if not attribute_names:
        return None

    if resolved_import.target_kind is ImportTargetKind.MODULE:
        module_qualified_name = resolved_import.target_qualified_name
        for attribute_name in attribute_names[:-1]:
            candidate_module_qualified_name = (
                f"{module_qualified_name}.{attribute_name}"
            )
            if candidate_module_qualified_name not in index.module_symbol_ids_by_name:
                return None
            module_qualified_name = candidate_module_qualified_name
        candidate_qualified_name = f"{module_qualified_name}.{attribute_names[-1]}"
        target_definition = index.unique_definitions_by_qualified_name.get(
            candidate_qualified_name
        )
        if (
            target_definition is not None
            and target_definition.kind is not DefinitionKind.MODULE
        ):
            if require_repository_symbol:
                target_symbol = program.resolved_symbols.get(
                    target_definition.definition_id
                )
                if (
                    target_symbol is None
                    or target_symbol.kind not in _CALLABLE_SYMBOL_KINDS
                ):
                    return None
            return target_definition.definition_id

    if (
        not require_repository_symbol
        and resolved_import.target_kind is ImportTargetKind.EXTERNAL
        and resolved_import.target_qualified_name == "dataclasses"
        and attribute_names == ("dataclass",)
    ):
        return base_binding.symbol_id
    return None


def _resolve_dataclasses(
    program: SemanticProgram,
    index: _RepositoryIndex,
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport],
    resolved_references: list[ResolvedReference],
) -> tuple[list[DataclassModel], list[DataclassField]]:
    """Resolve proven narrow ``@dataclass`` models and their field facts."""
    decorator_reference_ids = {
        resolved_reference.reference_id
        for resolved_reference in resolved_references
        if resolved_reference.context is ReferenceContext.DECORATOR
    }
    decorators_by_owner: dict[str, list[DecoratorFact]] = {}
    for decorator in program.syntax.decorators:
        if decorator.owner_definition_id not in index.definitions_by_id:
            continue
        decorators_by_owner.setdefault(decorator.owner_definition_id, []).append(
            decorator
        )

    dataclass_models: list[DataclassModel] = []
    dataclass_fields: list[DataclassField] = []
    for definition in index.definitions_by_id.values():
        if definition.kind is not DefinitionKind.CLASS:
            continue
        owner_decorators = decorators_by_owner.get(definition.definition_id, [])
        if len(owner_decorators) != 1:
            continue
        decorator = owner_decorators[0]
        decorator_reference_id = f"reference:{decorator.decorator_id}"
        if decorator_reference_id not in decorator_reference_ids:
            continue
        if not _decorator_proves_dataclass(
            decorator=decorator,
            owner_definition=definition,
            index=index,
            resolved_imports_by_binding_symbol_id=resolved_imports_by_binding_symbol_id,
        ):
            continue
        dataclass_models.append(
            DataclassModel(
                model_id=f"dataclass:{definition.definition_id}",
                class_symbol_id=definition.definition_id,
                decorator_reference_id=decorator_reference_id,
                decorator_site=decorator.site,
            )
        )
        dataclass_fields.extend(
            _collect_dataclass_fields(
                class_definition=definition,
                program=program,
            )
        )
    return dataclass_models, dataclass_fields


def _with_proven_dataclass_support(
    resolved_symbols: dict[str, ResolvedSymbol],
    dataclass_models: list[DataclassModel],
) -> dict[str, ResolvedSymbol]:
    """Mirror proven dataclass support onto the owning class symbols."""
    updated_symbols: dict[str, ResolvedSymbol] | None = None
    for model in dataclass_models:
        symbol = resolved_symbols.get(model.class_symbol_id)
        if symbol is None:
            continue
        if SupportedDecorator.DATACLASS in symbol.supported_decorators:
            continue
        if updated_symbols is None:
            updated_symbols = dict(resolved_symbols)
        updated_symbols[model.class_symbol_id] = replace(
            symbol,
            supported_decorators=(
                *symbol.supported_decorators,
                SupportedDecorator.DATACLASS,
            ),
        )
    if updated_symbols is None:
        return resolved_symbols
    return updated_symbols


def _decorator_proves_dataclass(
    *,
    decorator: DecoratorFact,
    owner_definition: RawDefinitionFact,
    index: _RepositoryIndex,
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport],
) -> bool:
    """Return whether ``decorator`` proves narrow ``dataclasses.dataclass`` support."""
    evaluation_scope_id = owner_definition.parent_definition_id
    if evaluation_scope_id is None:
        return False
    expression = _parse_supported_expression(decorator.expression_text)
    if expression is None:
        return False

    if isinstance(expression, _SimpleNameExpression):
        binding = _lookup_visible_binding(
            name=expression.name,
            scope_id=evaluation_scope_id,
            site=decorator.site,
            index=index,
            excluded_definition_symbol_id=owner_definition.definition_id,
        )
        if binding is None or binding.binding_kind is not BindingKind.IMPORT:
            return False
        resolved_import = resolved_imports_by_binding_symbol_id.get(binding.symbol_id)
        return bool(
            resolved_import is not None
            and resolved_import.target_kind is ImportTargetKind.EXTERNAL
            and resolved_import.target_qualified_name == "dataclasses.dataclass"
        )

    binding = _lookup_visible_binding(
        name=expression.root_name,
        scope_id=evaluation_scope_id,
        site=decorator.site,
        index=index,
        excluded_definition_symbol_id=owner_definition.definition_id,
    )
    if binding is None or binding.binding_kind is not BindingKind.IMPORT:
        return False
    resolved_import = resolved_imports_by_binding_symbol_id.get(binding.symbol_id)
    return bool(
        resolved_import is not None
        and resolved_import.target_kind is ImportTargetKind.EXTERNAL
        and resolved_import.target_qualified_name == "dataclasses"
        and expression.attribute_names == ("dataclass",)
    )


def _collect_dataclass_fields(
    *,
    class_definition: RawDefinitionFact,
    program: SemanticProgram,
) -> list[DataclassField]:
    """Return proven dataclass field facts for one supported dataclass class."""
    dataclass_fields: list[DataclassField] = []
    for assignment in program.syntax.assignments:
        if assignment.scope_id != class_definition.definition_id:
            continue
        if assignment.annotation_text is None or not _is_simple_identifier(
            assignment.target_text
        ):
            continue
        field_symbol = program.resolved_symbols.get(assignment.assignment_id)
        if field_symbol is None:
            continue
        dataclass_fields.append(
            DataclassField(
                field_id=f"dataclass_field:{assignment.assignment_id}",
                class_symbol_id=class_definition.definition_id,
                field_symbol_id=field_symbol.symbol_id,
                name=assignment.target_text,
                site=assignment.site,
                annotation_text=assignment.annotation_text,
                has_default=assignment.value_text is not None,
                default_value_text=assignment.value_text,
            )
        )
    return dataclass_fields


def _parse_supported_expression(expression_text: str) -> _SupportedExpression | None:
    """Parse one supported simple-name or narrow dotted-chain expression."""
    try:
        expression = ast.parse(expression_text, mode="eval").body
    except SyntaxError:
        return None

    if isinstance(expression, ast.Name) and _is_simple_identifier(expression.id):
        return _SimpleNameExpression(name=expression.id)
    attribute_names: list[str] = []
    current_expression: ast.expr = expression
    while isinstance(current_expression, ast.Attribute):
        if not _is_simple_identifier(current_expression.attr):
            return None
        attribute_names.append(current_expression.attr)
        if len(attribute_names) > 2:
            return None
        current_expression = current_expression.value
    if (
        attribute_names
        and isinstance(current_expression, ast.Name)
        and _is_simple_identifier(current_expression.id)
    ):
        return _AttributeChainExpression(
            root_name=current_expression.id,
            attribute_names=tuple(reversed(attribute_names)),
        )
    return None


def _is_simple_identifier(name: str) -> bool:
    """Return whether ``name`` is a plain identifier that can bind lexically."""
    return name.isidentifier() and not keyword.iskeyword(name)


def _span_starts_before(left: SourceSpan, right: SourceSpan) -> bool:
    """Return whether ``left`` starts strictly before ``right``."""
    return (left.start_line, left.start_column) < (
        right.start_line,
        right.start_column,
    )


def _span_ends_before_or_at(left: SourceSpan, right: SourceSpan) -> bool:
    """Return whether ``left`` ends before or at the start of ``right``."""
    return (left.end_line, left.end_column) <= (
        right.start_line,
        right.start_column,
    )


def _valid_file_paths(index: _RepositoryIndex) -> frozenset[str]:
    """Return the resolver-eligible repo-relative file paths."""
    return frozenset(
        source_file.path
        for file_id, source_file in index.source_files_by_id.items()
        if file_id not in index.blocked_file_ids
    )
