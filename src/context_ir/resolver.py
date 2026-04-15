"""Resolver and object-model layer for the semantic-first baseline."""

from __future__ import annotations

import ast
import keyword
from dataclasses import dataclass, replace

from context_ir.semantic_types import (
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
class _DirectAttributeExpression:
    """Supported direct ``name.attribute`` reference surface."""

    base_name: str
    attribute_name: str


_SupportedExpression = _SimpleNameExpression | _DirectAttributeExpression


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
    """Resolve supported decorator, base, and call reference surfaces."""
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
            require_repository_symbol=False,
            excluded_definition_symbol_id=owner_definition.definition_id,
        )
        if resolved_reference is not None:
            resolved_references.append(resolved_reference)

    for call_site in program.syntax.call_sites:
        if call_site.site.file_path not in _valid_file_paths(index):
            continue
        resolved_reference = _resolve_call_reference(
            call_site=call_site,
            index=index,
            program=program,
            resolved_imports_by_binding_symbol_id=resolved_imports_by_binding_symbol_id,
        )
        if resolved_reference is not None:
            resolved_references.append(resolved_reference)

    return resolved_references


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
        require_repository_symbol=False,
        excluded_definition_symbol_id=owner_definition.definition_id,
    )


def _resolve_call_reference(
    *,
    call_site: CallSiteFact,
    index: _RepositoryIndex,
    program: SemanticProgram,
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport],
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
        require_repository_symbol=True,
        excluded_definition_symbol_id=None,
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
        name=expression.base_name,
        scope_id=scope_id,
        site=site,
        index=index,
        excluded_definition_symbol_id=excluded_definition_symbol_id,
    )
    if binding is None or binding.binding_kind is not BindingKind.IMPORT:
        return None
    resolved_symbol_id = _resolve_direct_attribute_symbol_id(
        base_binding=binding,
        attribute_name=expression.attribute_name,
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


def _resolve_direct_attribute_symbol_id(
    *,
    base_binding: BindingFact,
    attribute_name: str,
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport],
    index: _RepositoryIndex,
    require_repository_symbol: bool,
) -> str | None:
    """Return the symbol targeted by a direct module-alias attribute reference."""
    resolved_import = resolved_imports_by_binding_symbol_id.get(base_binding.symbol_id)
    if resolved_import is None:
        return None

    if resolved_import.target_kind is ImportTargetKind.MODULE:
        candidate_qualified_name = (
            f"{resolved_import.target_qualified_name}.{attribute_name}"
        )
        target_definition = index.unique_definitions_by_qualified_name.get(
            candidate_qualified_name
        )
        if (
            target_definition is not None
            and target_definition.kind is not DefinitionKind.MODULE
        ):
            return target_definition.definition_id

    if (
        not require_repository_symbol
        and resolved_import.target_kind is ImportTargetKind.EXTERNAL
        and resolved_import.target_qualified_name == "dataclasses"
        and attribute_name == "dataclass"
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
        name=expression.base_name,
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
        and expression.attribute_name == "dataclass"
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
    """Parse one supported simple-name or direct-attribute expression."""
    try:
        expression = ast.parse(expression_text, mode="eval").body
    except SyntaxError:
        return None

    if isinstance(expression, ast.Name) and _is_simple_identifier(expression.id):
        return _SimpleNameExpression(name=expression.id)
    if (
        isinstance(expression, ast.Attribute)
        and isinstance(expression.value, ast.Name)
        and _is_simple_identifier(expression.value.id)
        and _is_simple_identifier(expression.attr)
    ):
        return _DirectAttributeExpression(
            base_name=expression.value.id,
            attribute_name=expression.attr,
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
