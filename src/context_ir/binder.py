"""Binder and lexical scope model for the semantic-first baseline."""

from __future__ import annotations

import keyword
from dataclasses import dataclass

from context_ir.semantic_types import (
    BindingFact,
    BindingKind,
    DecoratorFact,
    DecoratorSupport,
    DefinitionKind,
    ImportFact,
    ImportKind,
    ParameterFact,
    RawDefinitionFact,
    ResolvedSymbol,
    ResolvedSymbolKind,
    SemanticProgram,
    SupportedDecorator,
    SyntaxDiagnosticCode,
    SyntaxProgram,
)


@dataclass(frozen=True)
class _BindingEmission:
    """Internal binding record with enough metadata for stable ordering."""

    binding: BindingFact
    symbol: ResolvedSymbol
    file_path: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    category_order: int
    sequence: int


def bind_syntax(syntax: SyntaxProgram) -> SemanticProgram:
    """Bind syntax facts into stable lexical symbols and binding history."""
    blocked_file_ids = {
        diagnostic.file_id
        for diagnostic in syntax.diagnostics
        if diagnostic.code is SyntaxDiagnosticCode.PARSE_ERROR
    }

    valid_definitions = [
        definition
        for definition in syntax.definitions
        if definition.file_id not in blocked_file_ids
    ]
    definition_by_id = {
        definition.definition_id: definition for definition in valid_definitions
    }
    supported_decorators = _supported_decorators_by_owner(
        syntax.decorators,
        definition_by_id,
    )

    resolved_symbols: dict[str, ResolvedSymbol] = {}
    for definition in valid_definitions:
        resolved_symbols[definition.definition_id] = ResolvedSymbol(
            symbol_id=definition.definition_id,
            kind=_definition_symbol_kind(definition.kind),
            qualified_name=definition.qualified_name,
            file_id=definition.file_id,
            definition_site=definition.site,
            defining_scope_id=(
                definition.parent_definition_id or definition.definition_id
            ),
            supported_decorators=supported_decorators.get(
                definition.definition_id,
                (),
            ),
        )

    emissions: list[_BindingEmission] = []
    sequence = 0

    for definition in valid_definitions:
        if definition.parent_definition_id is None:
            continue
        emissions.append(
            _definition_binding_emission(
                definition=definition,
                sequence=sequence,
            )
        )
        sequence += 1

    for parameter in syntax.parameters:
        owner = definition_by_id.get(parameter.owner_definition_id)
        if owner is None:
            continue
        parameter_emission = _parameter_binding_emission(
            parameter=parameter,
            owner=owner,
            sequence=sequence,
        )
        emissions.append(parameter_emission)
        resolved_symbols[parameter_emission.symbol.symbol_id] = (
            parameter_emission.symbol
        )
        sequence += 1

    for import_fact in syntax.imports:
        if import_fact.file_id in blocked_file_ids:
            continue
        scope_definition = definition_by_id.get(import_fact.scope_id)
        if scope_definition is None:
            continue
        import_emission = _import_binding_emission(
            import_fact=import_fact,
            scope_definition=scope_definition,
            sequence=sequence,
        )
        if import_emission is None:
            continue
        emissions.append(import_emission)
        resolved_symbols[import_emission.symbol.symbol_id] = import_emission.symbol
        sequence += 1

    for assignment in syntax.assignments:
        scope_definition = definition_by_id.get(assignment.scope_id)
        if scope_definition is None:
            continue
        bound_name = _bindable_identifier_name(assignment.target_text)
        if bound_name is None:
            continue
        if scope_definition.kind is DefinitionKind.CLASS:
            binding_kind = BindingKind.CLASS_ATTRIBUTE
            symbol_kind = ResolvedSymbolKind.ATTRIBUTE
        else:
            binding_kind = BindingKind.ASSIGNMENT
            symbol_kind = ResolvedSymbolKind.LOCAL
        symbol = ResolvedSymbol(
            symbol_id=assignment.assignment_id,
            kind=symbol_kind,
            qualified_name=_binding_qualified_name(
                scope_definition.qualified_name,
                bound_name,
            ),
            file_id=scope_definition.file_id,
            definition_site=assignment.site,
            defining_scope_id=assignment.scope_id,
        )
        emissions.append(
            _binding_emission(
                binding=BindingFact(
                    binding_id=f"binding:{assignment.assignment_id}",
                    scope_id=assignment.scope_id,
                    name=bound_name,
                    binding_kind=binding_kind,
                    symbol_id=assignment.assignment_id,
                    site=assignment.site,
                ),
                symbol=symbol,
                category_order=3,
                sequence=sequence,
            )
        )
        resolved_symbols[symbol.symbol_id] = symbol
        sequence += 1

    ordered_bindings = [
        emission.binding
        for emission in sorted(
            emissions,
            key=lambda emission: (
                emission.file_path,
                emission.start_line,
                emission.start_column,
                emission.end_line,
                emission.end_column,
                emission.category_order,
                emission.sequence,
            ),
        )
    ]

    return SemanticProgram(
        repo_root=syntax.repo_root,
        syntax=syntax,
        supported_subset=syntax.supported_subset,
        resolved_symbols=resolved_symbols,
        bindings=ordered_bindings,
    )


def _supported_decorators_by_owner(
    decorators: list[DecoratorFact],
    definition_by_id: dict[str, RawDefinitionFact],
) -> dict[str, tuple[SupportedDecorator, ...]]:
    """Return syntax-declared supported decorators keyed by owning definition."""
    supported: dict[str, list[SupportedDecorator]] = {}
    for decorator in decorators:
        if decorator.owner_definition_id not in definition_by_id:
            continue
        if (
            decorator.support is DecoratorSupport.SUPPORTED
            and decorator.supported_decorator is not None
        ):
            supported.setdefault(decorator.owner_definition_id, []).append(
                decorator.supported_decorator
            )

    return {
        owner_definition_id: tuple(owner_supported_decorators)
        for owner_definition_id, owner_supported_decorators in supported.items()
    }


def _definition_symbol_kind(kind: DefinitionKind) -> ResolvedSymbolKind:
    """Map a raw definition kind into its semantic symbol kind."""
    if kind is DefinitionKind.MODULE:
        return ResolvedSymbolKind.MODULE
    if kind is DefinitionKind.CLASS:
        return ResolvedSymbolKind.CLASS
    if kind is DefinitionKind.ASYNC_FUNCTION:
        return ResolvedSymbolKind.ASYNC_FUNCTION
    if kind is DefinitionKind.METHOD:
        return ResolvedSymbolKind.METHOD
    return ResolvedSymbolKind.FUNCTION


def _definition_binding_emission(
    *,
    definition: RawDefinitionFact,
    sequence: int,
) -> _BindingEmission:
    """Return the enclosing-scope binding emission for one definition."""
    return _binding_emission(
        binding=BindingFact(
            binding_id=f"binding:{definition.definition_id}",
            scope_id=definition.parent_definition_id or definition.definition_id,
            name=definition.name,
            binding_kind=BindingKind.DEFINITION,
            symbol_id=definition.definition_id,
            site=definition.site,
        ),
        symbol=ResolvedSymbol(
            symbol_id=definition.definition_id,
            kind=_definition_symbol_kind(definition.kind),
            qualified_name=definition.qualified_name,
            file_id=definition.file_id,
            definition_site=definition.site,
            defining_scope_id=definition.parent_definition_id
            or definition.definition_id,
        ),
        category_order=0,
        sequence=sequence,
    )


def _parameter_binding_emission(
    *,
    parameter: ParameterFact,
    owner: RawDefinitionFact,
    sequence: int,
) -> _BindingEmission:
    """Return the binding emission for one declared parameter."""
    symbol = ResolvedSymbol(
        symbol_id=parameter.parameter_id,
        kind=ResolvedSymbolKind.PARAMETER,
        qualified_name=_binding_qualified_name(owner.qualified_name, parameter.name),
        file_id=owner.file_id,
        definition_site=parameter.site,
        defining_scope_id=owner.definition_id,
    )
    return _binding_emission(
        binding=BindingFact(
            binding_id=f"binding:{parameter.parameter_id}",
            scope_id=owner.definition_id,
            name=parameter.name,
            binding_kind=BindingKind.PARAMETER,
            symbol_id=parameter.parameter_id,
            site=parameter.site,
        ),
        symbol=symbol,
        category_order=1,
        sequence=sequence,
    )


def _import_binding_emission(
    *,
    import_fact: ImportFact,
    scope_definition: RawDefinitionFact,
    sequence: int,
) -> _BindingEmission | None:
    """Return the binding emission for one import that binds a visible name."""
    bound_name = _bound_name_for_import(import_fact)
    if bound_name is None:
        return None
    symbol = ResolvedSymbol(
        symbol_id=import_fact.import_id,
        kind=ResolvedSymbolKind.IMPORTED_NAME,
        qualified_name=_binding_qualified_name(
            scope_definition.qualified_name,
            bound_name,
        ),
        file_id=import_fact.file_id,
        definition_site=import_fact.site,
        defining_scope_id=import_fact.scope_id,
    )
    return _binding_emission(
        binding=BindingFact(
            binding_id=f"binding:{import_fact.import_id}",
            scope_id=import_fact.scope_id,
            name=bound_name,
            binding_kind=BindingKind.IMPORT,
            symbol_id=import_fact.import_id,
            site=import_fact.site,
        ),
        symbol=symbol,
        category_order=2,
        sequence=sequence,
    )


def _bound_name_for_import(import_fact: ImportFact) -> str | None:
    """Return the lexical name introduced by one import fact, if any."""
    if import_fact.kind is ImportKind.STAR_IMPORT:
        return None
    if import_fact.alias is not None:
        return import_fact.alias
    if import_fact.kind is ImportKind.FROM_IMPORT:
        return import_fact.imported_name
    return import_fact.module_name.split(".", maxsplit=1)[0]


def _bindable_identifier_name(target_text: str) -> str | None:
    """Return the target name when an assignment is a plain identifier binding."""
    if not target_text.isidentifier():
        return None
    if keyword.iskeyword(target_text):
        return None
    return target_text


def _binding_qualified_name(scope_qualified_name: str, name: str) -> str:
    """Return a stable lexical qualified name rooted in the owning scope."""
    if not scope_qualified_name:
        return name
    return f"{scope_qualified_name}.{name}"


def _binding_emission(
    *,
    binding: BindingFact,
    symbol: ResolvedSymbol,
    category_order: int,
    sequence: int,
) -> _BindingEmission:
    """Build an internal binding emission from one binding and symbol pair."""
    span = binding.site.span
    return _BindingEmission(
        binding=binding,
        symbol=symbol,
        file_path=binding.site.file_path,
        start_line=span.start_line,
        start_column=span.start_column,
        end_line=span.end_line,
        end_column=span.end_column,
        category_order=category_order,
        sequence=sequence,
    )


__all__ = ["bind_syntax"]
