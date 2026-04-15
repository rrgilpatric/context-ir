"""Parser surfaces for the semantic-first baseline and legacy graph compatibility.

`extract_syntax(...)` and `extract_syntax_file(...)` are the primary parser APIs
for the semantic-first baseline. They collect syntax facts only and preserve
source-backed evidence without fabricating semantic meaning.

`parse_file(...)` and `parse_repository(...)` are retained as legacy
SymbolGraph-compatible entry points for the retired architecture so the rest of
the repository can keep importing them during the rebaseline.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

import tree_sitter as ts
import tree_sitter_python as tspython

from context_ir.semantic_types import (
    AssignmentFact,
    AttributeSiteFact,
    BaseExpressionFact,
    CallSiteFact,
    DecoratorFact,
    DecoratorSupport,
    DefinitionKind,
    ImportFact,
    ImportKind,
    ParameterFact,
    ParameterKind,
    RawDefinitionFact,
    ReferenceContext,
    SourceFileFact,
    SourceSite,
    SourceSpan,
    SyntaxDiagnostic,
    SyntaxDiagnosticCode,
    SyntaxProgram,
)
from context_ir.types import Edge, EdgeKind, SymbolGraph, SymbolKind, SymbolNode

# ---------------------------------------------------------------------------
# Semantic-first syntax extraction
# ---------------------------------------------------------------------------

_UPPER_SNAKE_RE: re.Pattern[str] = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True)
class _DefinitionContext:
    """Current raw definition context while collecting syntax facts."""

    definition_id: str
    kind: DefinitionKind
    qualified_name: str


def extract_syntax(repo_root: Path | str) -> SyntaxProgram:
    """Extract syntax facts for every supported Python file under ``repo_root``."""
    root = Path(repo_root)
    program = SyntaxProgram(repo_root=root)

    for file_path in sorted(root.rglob("*.py")):
        _extract_syntax_into_program(
            file_path=file_path,
            repo_root=root,
            program=program,
        )

    return program


def extract_syntax_file(file_path: Path | str, repo_root: Path | str) -> SyntaxProgram:
    """Extract syntax facts for one file relative to ``repo_root``."""
    root = Path(repo_root)
    path = Path(file_path)
    program = SyntaxProgram(repo_root=root)
    _extract_syntax_into_program(file_path=path, repo_root=root, program=program)
    return program


def _extract_syntax_into_program(
    *, file_path: Path, repo_root: Path, program: SyntaxProgram
) -> None:
    """Populate ``program`` with syntax facts for one Python source file."""
    rel_path = str(file_path.relative_to(repo_root))
    file_id = f"file:{rel_path}"
    module_name = _module_name_from_rel_path(rel_path)

    program.source_files[file_id] = SourceFileFact(
        file_id=file_id,
        path=rel_path,
        module_name=module_name,
    )

    try:
        source_text = file_path.read_text(encoding="utf-8")
    except OSError:
        return

    module_name_for_ids = module_name or "__module__"
    module_definition_id = f"def:{rel_path}:{module_name_for_ids}"
    module_span = _file_span(source_text)
    module_site = SourceSite(
        site_id=f"site:{module_definition_id}",
        file_path=rel_path,
        span=module_span,
        snippet=_snippet_from_span(source_text, module_span),
    )
    program.definitions.append(
        RawDefinitionFact(
            definition_id=module_definition_id,
            kind=DefinitionKind.MODULE,
            name=_module_display_name(module_name, file_path),
            qualified_name=module_name or file_path.stem,
            file_id=file_id,
            site=module_site,
        )
    )

    try:
        tree = ast.parse(source_text, filename=rel_path)
    except SyntaxError as error:
        diagnostic = _syntax_error_diagnostic(
            source_text=source_text,
            rel_path=rel_path,
            file_id=file_id,
            error=error,
        )
        program.diagnostics.append(diagnostic)
        return

    collector = _SyntaxCollector(
        program=program,
        rel_path=rel_path,
        file_id=file_id,
        module_name=module_name or file_path.stem,
        module_definition_id=module_definition_id,
        source_text=source_text,
    )
    collector.collect(tree)


def _module_name_from_rel_path(rel_path: str) -> str:
    """Return the dotted module path represented by a repo-relative file path."""
    path = Path(rel_path)
    if path.name == "__init__.py":
        parts = path.parts[:-1]
        return ".".join(parts) if parts else "__init__"
    return ".".join(path.with_suffix("").parts)


def _module_display_name(module_name: str, file_path: Path) -> str:
    """Return the local display name for a module definition."""
    if module_name == "__init__":
        return "__init__"
    if module_name:
        return module_name.rsplit(".", maxsplit=1)[-1]
    return file_path.stem


def _file_span(source_text: str) -> SourceSpan:
    """Return a full-file span for source inventory and module facts."""
    lines = source_text.splitlines(keepends=True)
    if not lines:
        return SourceSpan(
            start_line=1,
            start_column=0,
            end_line=1,
            end_column=0,
        )
    return SourceSpan(
        start_line=1,
        start_column=0,
        end_line=len(lines),
        end_column=len(lines[-1]),
    )


def _snippet_from_span(source_text: str, span: SourceSpan) -> str | None:
    """Return the exact snippet for ``span`` or ``None`` if it is empty."""
    lines = source_text.splitlines(keepends=True)
    if not lines:
        return None

    if span.start_line == span.end_line:
        line = lines[span.start_line - 1]
        snippet = line[span.start_column : span.end_column]
        return snippet or None

    segment = lines[span.start_line - 1 : span.end_line]
    if not segment:
        return None

    segment[0] = segment[0][span.start_column :]
    segment[-1] = segment[-1][: span.end_column]
    snippet = "".join(segment)
    return snippet or None


def _syntax_error_diagnostic(
    *,
    source_text: str,
    rel_path: str,
    file_id: str,
    error: SyntaxError,
) -> SyntaxDiagnostic:
    """Return a syntax-layer diagnostic for a parse failure."""
    diagnostic_id = f"syntax:{rel_path}:parse_error"
    span = _syntax_error_span(source_text, error)
    return SyntaxDiagnostic(
        diagnostic_id=diagnostic_id,
        file_id=file_id,
        site=SourceSite(
            site_id=f"site:{diagnostic_id}",
            file_path=rel_path,
            span=span,
            snippet=_snippet_from_span(source_text, span),
        ),
        code=SyntaxDiagnosticCode.PARSE_ERROR,
        message=error.msg,
    )


def _syntax_error_span(source_text: str, error: SyntaxError) -> SourceSpan:
    """Return a source span that captures the physical line of a parse failure."""
    lines = source_text.splitlines(keepends=True)
    if not lines:
        return SourceSpan(
            start_line=1,
            start_column=0,
            end_line=1,
            end_column=0,
        )

    line_number = error.lineno if isinstance(error.lineno, int) else 1
    if line_number < 1 or line_number > len(lines):
        return _file_span(source_text)

    line_text = lines[line_number - 1]
    return SourceSpan(
        start_line=line_number,
        start_column=0,
        end_line=line_number,
        end_column=len(line_text),
    )


def _node_line(node: ast.AST) -> int:
    """Return a 1-indexed start line for an AST node."""
    lineno = getattr(node, "lineno", None)
    return lineno if isinstance(lineno, int) else 1


def _node_column(node: ast.AST) -> int:
    """Return a 0-indexed start column for an AST node."""
    column = getattr(node, "col_offset", None)
    return column if isinstance(column, int) else 0


def _node_end_line(node: ast.AST) -> int:
    """Return a 1-indexed end line for an AST node."""
    end_lineno = getattr(node, "end_lineno", None)
    if isinstance(end_lineno, int):
        return end_lineno
    return _node_line(node)


def _node_end_column(node: ast.AST) -> int:
    """Return a 0-indexed end column for an AST node."""
    end_column = getattr(node, "end_col_offset", None)
    if isinstance(end_column, int):
        return end_column
    return _node_column(node)


def _expression_text(node: ast.AST | None) -> str | None:
    """Return normalized source text for an expression node."""
    if node is None:
        return None
    return ast.unparse(node)


def _import_module_name(module: str | None, level: int) -> str:
    """Return the syntax-preserving module string for ``ImportFrom`` nodes."""
    prefix = "." * level
    if module is None:
        return prefix
    return f"{prefix}{module}"


def _attribute_context(node: ast.Attribute) -> ReferenceContext:
    """Return a syntax-level access context for an attribute node."""
    if isinstance(node.ctx, ast.Store):
        return ReferenceContext.STORE
    return ReferenceContext.ATTRIBUTE_ACCESS


class _SyntaxCollector(ast.NodeVisitor):
    """Collect syntax-only facts for one file without fabricating semantics."""

    def __init__(
        self,
        *,
        program: SyntaxProgram,
        rel_path: str,
        file_id: str,
        module_name: str,
        module_definition_id: str,
        source_text: str,
    ) -> None:
        self._program = program
        self._rel_path = rel_path
        self._file_id = file_id
        self._module_name = module_name
        self._source_text = source_text
        self._definition_stack: list[_DefinitionContext] = [
            _DefinitionContext(
                definition_id=module_definition_id,
                kind=DefinitionKind.MODULE,
                qualified_name=module_name,
            )
        ]
        self._definition_id_counts: dict[str, int] = {}

    def collect(self, tree: ast.Module) -> None:
        """Walk the parsed module and append facts to the owning program."""
        for statement in tree.body:
            self.visit(statement)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Record a raw class definition plus its syntax-backed children."""
        definition_id = self._make_definition_id(node.name)
        qualified_name = self._qualified_name(node.name)
        definition = RawDefinitionFact(
            definition_id=definition_id,
            kind=DefinitionKind.CLASS,
            name=node.name,
            qualified_name=qualified_name,
            file_id=self._file_id,
            site=self._definition_site(node, definition_id),
            parent_definition_id=self._current_scope_id(),
        )
        self._program.definitions.append(definition)
        self._record_decorators(definition_id, node.decorator_list)
        self._record_base_expressions(definition_id, node.bases)

        for decorator in node.decorator_list:
            self.visit(decorator)
        for base_expression in node.bases:
            self.visit(base_expression)
        for keyword in node.keywords:
            self.visit(keyword.value)

        self._definition_stack.append(
            _DefinitionContext(
                definition_id=definition_id,
                kind=DefinitionKind.CLASS,
                qualified_name=qualified_name,
            )
        )
        for statement in node.body:
            self.visit(statement)
        self._definition_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Record a raw function or method definition."""
        self._visit_function_like(node=node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Record a raw async function definition."""
        self._visit_function_like(node=node, is_async=True)

    def visit_Import(self, node: ast.Import) -> None:
        """Record one syntax fact per imported module."""
        for index, alias in enumerate(node.names, start=1):
            import_id = self._fact_id(
                prefix="import",
                node=node,
                suffix=f"{index}:{alias.name}:{alias.asname or '_'}",
            )
            self._program.imports.append(
                ImportFact(
                    import_id=import_id,
                    file_id=self._file_id,
                    scope_id=self._current_scope_id(),
                    site=self._site_for_node(node, import_id),
                    kind=ImportKind.IMPORT,
                    module_name=alias.name,
                    alias=alias.asname,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Record one syntax fact per imported name or star import."""
        module_name = _import_module_name(node.module, node.level)
        is_relative = node.level > 0
        for index, alias in enumerate(node.names, start=1):
            kind = (
                ImportKind.STAR_IMPORT if alias.name == "*" else ImportKind.FROM_IMPORT
            )
            import_id = self._fact_id(
                prefix="import",
                node=node,
                suffix=f"{index}:{alias.name}:{alias.asname or '_'}",
            )
            self._program.imports.append(
                ImportFact(
                    import_id=import_id,
                    file_id=self._file_id,
                    scope_id=self._current_scope_id(),
                    site=self._site_for_node(node, import_id),
                    kind=kind,
                    module_name=module_name,
                    imported_name=alias.name,
                    alias=alias.asname,
                    is_relative=is_relative,
                )
            )

    def visit_Assign(self, node: ast.Assign) -> None:
        """Record syntax-level assignment facts in the current lexical scope."""
        value_text = _expression_text(node.value)
        for index, target in enumerate(node.targets, start=1):
            assignment_id = self._fact_id(prefix="assign", node=node, suffix=str(index))
            self._program.assignments.append(
                AssignmentFact(
                    assignment_id=assignment_id,
                    scope_id=self._current_scope_id(),
                    site=self._site_for_node(node, assignment_id),
                    target_text=ast.unparse(target),
                    value_text=value_text,
                )
            )
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Record annotated assignments for later binder and resolver work."""
        assignment_id = self._fact_id(prefix="assign", node=node)
        self._program.assignments.append(
            AssignmentFact(
                assignment_id=assignment_id,
                scope_id=self._current_scope_id(),
                site=self._site_for_node(node, assignment_id),
                target_text=ast.unparse(node.target),
                value_text=_expression_text(node.value),
                annotation_text=ast.unparse(node.annotation),
            )
        )
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Record augmented assignments as raw syntax facts."""
        assignment_id = self._fact_id(prefix="assign", node=node)
        self._program.assignments.append(
            AssignmentFact(
                assignment_id=assignment_id,
                scope_id=self._current_scope_id(),
                site=self._site_for_node(node, assignment_id),
                target_text=ast.unparse(node.target),
                value_text=ast.unparse(node.value),
            )
        )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Record call sites without attempting semantic resolution."""
        call_site_id = self._fact_id(prefix="call", node=node)
        self._program.call_sites.append(
            CallSiteFact(
                call_site_id=call_site_id,
                enclosing_scope_id=self._current_scope_id(),
                site=self._site_for_node(node, call_site_id),
                callee_text=ast.unparse(node.func),
                argument_count=len(node.args) + len(node.keywords),
            )
        )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Record raw attribute access sites for later semantic interpretation."""
        attribute_site_id = self._fact_id(prefix="attribute", node=node)
        self._program.attribute_sites.append(
            AttributeSiteFact(
                attribute_site_id=attribute_site_id,
                enclosing_scope_id=self._current_scope_id(),
                site=self._site_for_node(node, attribute_site_id),
                base_text=ast.unparse(node.value),
                attribute_name=node.attr,
                context=_attribute_context(node),
            )
        )
        self.generic_visit(node)

    def _visit_function_like(
        self, *, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool
    ) -> None:
        """Record a function-like definition and recurse into its lexical body."""
        parent_kind = self._current_definition().kind
        kind = (
            DefinitionKind.METHOD
            if parent_kind is DefinitionKind.CLASS
            else DefinitionKind.ASYNC_FUNCTION
            if is_async
            else DefinitionKind.FUNCTION
        )
        definition_id = self._make_definition_id(node.name)
        qualified_name = self._qualified_name(node.name)
        definition = RawDefinitionFact(
            definition_id=definition_id,
            kind=kind,
            name=node.name,
            qualified_name=qualified_name,
            file_id=self._file_id,
            site=self._definition_site(node, definition_id),
            parent_definition_id=self._current_scope_id(),
        )
        self._program.definitions.append(definition)
        self._record_decorators(definition_id, node.decorator_list)
        self._record_parameters(definition_id, node.args)

        for decorator in node.decorator_list:
            self.visit(decorator)
        for positional_default in node.args.defaults:
            self.visit(positional_default)
        for keyword_default in node.args.kw_defaults:
            if keyword_default is not None:
                self.visit(keyword_default)

        self._definition_stack.append(
            _DefinitionContext(
                definition_id=definition_id,
                kind=kind,
                qualified_name=qualified_name,
            )
        )
        for statement in node.body:
            self.visit(statement)
        self._definition_stack.pop()

    def _record_decorators(
        self, owner_definition_id: str, decorators: list[ast.expr]
    ) -> None:
        """Append syntax facts for each decorator attached to a definition."""
        for index, decorator in enumerate(decorators, start=1):
            decorator_id = self._fact_id(
                prefix="decorator",
                node=decorator,
                suffix=f"{owner_definition_id}:{index}",
            )
            self._program.decorators.append(
                DecoratorFact(
                    decorator_id=decorator_id,
                    owner_definition_id=owner_definition_id,
                    site=self._site_for_node(decorator, decorator_id),
                    expression_text=ast.unparse(decorator),
                    support=DecoratorSupport.OPAQUE,
                )
            )

    def _record_parameters(
        self, owner_definition_id: str, arguments: ast.arguments
    ) -> None:
        """Append syntax facts for parameters in declaration order."""
        positional_parameters = [
            (ParameterKind.POSITIONAL_ONLY, parameter)
            for parameter in arguments.posonlyargs
        ] + [
            (ParameterKind.POSITIONAL_OR_KEYWORD, parameter)
            for parameter in arguments.args
        ]

        positional_defaults: dict[int, ast.expr] = {}
        positional_default_start = len(positional_parameters) - len(arguments.defaults)
        for index, default_value in enumerate(arguments.defaults):
            positional_defaults[positional_default_start + index] = default_value

        ordinal = 0
        for positional_index, (parameter_kind, parameter) in enumerate(
            positional_parameters
        ):
            self._append_parameter_fact(
                owner_definition_id=owner_definition_id,
                parameter=parameter,
                parameter_kind=parameter_kind,
                ordinal=ordinal,
                default_value=positional_defaults.get(positional_index),
            )
            ordinal += 1

        if arguments.vararg is not None:
            self._append_parameter_fact(
                owner_definition_id=owner_definition_id,
                parameter=arguments.vararg,
                parameter_kind=ParameterKind.VARARG,
                ordinal=ordinal,
                default_value=None,
            )
            ordinal += 1

        for parameter, keyword_default in zip(
            arguments.kwonlyargs,
            arguments.kw_defaults,
            strict=True,
        ):
            self._append_parameter_fact(
                owner_definition_id=owner_definition_id,
                parameter=parameter,
                parameter_kind=ParameterKind.KEYWORD_ONLY,
                ordinal=ordinal,
                default_value=keyword_default,
            )
            ordinal += 1

        if arguments.kwarg is not None:
            self._append_parameter_fact(
                owner_definition_id=owner_definition_id,
                parameter=arguments.kwarg,
                parameter_kind=ParameterKind.KWARGS,
                ordinal=ordinal,
                default_value=None,
            )

    def _append_parameter_fact(
        self,
        *,
        owner_definition_id: str,
        parameter: ast.arg,
        parameter_kind: ParameterKind,
        ordinal: int,
        default_value: ast.expr | None,
    ) -> None:
        """Append one parameter syntax fact with annotation/default metadata."""
        parameter_id = (
            f"parameter:{owner_definition_id}:{ordinal}:{parameter_kind.value}:"
            f"{parameter.arg}"
        )
        self._program.parameters.append(
            ParameterFact(
                parameter_id=parameter_id,
                owner_definition_id=owner_definition_id,
                name=parameter.arg,
                kind=parameter_kind,
                ordinal=ordinal,
                site=self._parameter_site(parameter, parameter_id),
                annotation_text=_expression_text(parameter.annotation),
                has_default=default_value is not None,
                default_value_text=_expression_text(default_value),
            )
        )

    def _record_base_expressions(
        self, owner_definition_id: str, base_expressions: list[ast.expr]
    ) -> None:
        """Append syntax facts for raw class base expressions."""
        for index, base_expression in enumerate(base_expressions, start=1):
            base_expression_id = self._fact_id(
                prefix="base",
                node=base_expression,
                suffix=f"{owner_definition_id}:{index}",
            )
            self._program.base_expressions.append(
                BaseExpressionFact(
                    base_expression_id=base_expression_id,
                    owner_definition_id=owner_definition_id,
                    site=self._site_for_node(base_expression, base_expression_id),
                    expression_text=ast.unparse(base_expression),
                )
            )

    def _make_definition_id(self, name: str) -> str:
        """Return a stable definition identifier with duplicate suffixing."""
        base_id = f"def:{self._rel_path}:{self._qualified_name(name)}"
        next_count = self._definition_id_counts.get(base_id, 0) + 1
        self._definition_id_counts[base_id] = next_count
        if next_count == 1:
            return base_id
        return f"{base_id}#{next_count}"

    def _qualified_name(self, name: str) -> str:
        """Return the fully qualified dotted name for a nested definition."""
        parent = self._current_definition()
        if parent.kind is DefinitionKind.MODULE:
            return f"{self._module_name}.{name}" if self._module_name else name
        return f"{parent.qualified_name}.{name}"

    def _definition_site(
        self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef, fact_id: str
    ) -> SourceSite:
        """Return a source site that includes leading decorator lines."""
        start_line = _node_line(node)
        start_column = _node_column(node)
        if node.decorator_list:
            first_decorator = min(
                node.decorator_list,
                key=lambda decorator: (_node_line(decorator), _node_column(decorator)),
            )
            start_line = _node_line(first_decorator)
            start_column = _node_column(first_decorator)
        return self._site_for_node(
            node,
            fact_id,
            start_line=start_line,
            start_column=start_column,
        )

    def _parameter_site(self, parameter: ast.arg, parameter_id: str) -> SourceSite:
        """Return a source site narrowed to the parameter name token."""
        start_line = _node_line(parameter)
        start_column = _node_column(parameter)
        end_column = start_column + len(parameter.arg)
        return self._site_for_node(
            parameter,
            parameter_id,
            start_line=start_line,
            start_column=start_column,
            end_line=start_line,
            end_column=end_column,
        )

    def _site_for_node(
        self,
        node: ast.AST,
        fact_id: str,
        *,
        start_line: int | None = None,
        start_column: int | None = None,
        end_line: int | None = None,
        end_column: int | None = None,
    ) -> SourceSite:
        """Build a source site for one raw syntax fact."""
        span = SourceSpan(
            start_line=start_line if start_line is not None else _node_line(node),
            start_column=(
                start_column if start_column is not None else _node_column(node)
            ),
            end_line=end_line if end_line is not None else _node_end_line(node),
            end_column=end_column if end_column is not None else _node_end_column(node),
        )
        return SourceSite(
            site_id=f"site:{fact_id}",
            file_path=self._rel_path,
            span=span,
            snippet=_snippet_from_span(self._source_text, span),
        )

    def _fact_id(self, *, prefix: str, node: ast.AST, suffix: str | None = None) -> str:
        """Return a source-stable identifier for a non-definition syntax fact."""
        base_id = f"{prefix}:{self._rel_path}:{_node_line(node)}:{_node_column(node)}"
        if suffix is None:
            return base_id
        return f"{base_id}:{suffix}"

    def _current_definition(self) -> _DefinitionContext:
        """Return the current enclosing raw definition context."""
        return self._definition_stack[-1]

    def _current_scope_id(self) -> str:
        """Return the current enclosing scope identifier."""
        return self._current_definition().definition_id


# ---------------------------------------------------------------------------
# Legacy SymbolGraph parser kept for compatibility with the retired baseline
# ---------------------------------------------------------------------------

_LANGUAGE: ts.Language = ts.Language(tspython.language())
_PARSER: ts.Parser = ts.Parser(_LANGUAGE)


def _text(node: ts.Node) -> str:
    """Safely decode the text of a tree-sitter node."""
    raw = node.text
    if raw is None:
        return ""
    return raw.decode()


def _node_name(node: ts.Node) -> str:
    """Extract the identifier name from a function_definition or class_definition."""
    for child in node.children:
        if child.type == "identifier":
            return _text(child)
    return "<anonymous>"


def _assignment_target_name(assignment: ts.Node) -> str | None:
    """Return the identifier name if the assignment target is a plain identifier."""
    for child in assignment.children:
        if child.type == "identifier":
            return _text(child)
        if child.type in ("=", ":", "type"):
            break
    return None


def _unwrap_definition(node: ts.Node) -> ts.Node | None:
    """Return the underlying function/class node, unwrapping decorators when present."""
    if node.type in ("function_definition", "class_definition"):
        return node
    if node.type == "decorated_definition":
        for child in node.children:
            if child.type in ("function_definition", "class_definition"):
                return child
    return None


def _node_span(node: ts.Node, span_node: ts.Node | None = None) -> tuple[int, int]:
    """Return a 1-indexed definition span, including decorators when requested."""
    effective_node = span_node or node
    return effective_node.start_point.row + 1, effective_node.end_point.row + 1


def _scoped_symbol_name(rel_path: str, parent_id: str, name: str) -> str:
    """Return the symbol name qualified by its enclosing class path when applicable."""
    prefix = f"{rel_path}::"
    if parent_id.startswith(prefix):
        return f"{parent_id[len(prefix) :]}.{name}"
    return name


def _make_unique_node_id(base_id: str, graph: SymbolGraph) -> str:
    """Return a deterministic node ID, suffixing duplicates only when needed."""
    if base_id not in graph.nodes:
        return base_id

    suffix = 2
    candidate = f"{base_id}#{suffix}"
    while candidate in graph.nodes:
        suffix += 1
        candidate = f"{base_id}#{suffix}"
    return candidate


def _module_path_from_file_path(file_path: str) -> str | None:
    """Convert a repo-relative Python file path to its dotted module path."""
    if file_path.endswith("/__init__.py"):
        return file_path[: -len("/__init__.py")].replace("/", ".")
    if file_path.endswith(".py"):
        return file_path[: -len(".py")].replace("/", ".")
    return None


def _append_import_edge(
    graph: SymbolGraph,
    source_id: str,
    target_id: str,
    resolved_targets: set[str],
) -> None:
    """Add one IMPORTS edge if this source/target pair has not been emitted yet."""
    if target_id in resolved_targets:
        return
    graph.edges.append(
        Edge(
            source_id=source_id,
            target_id=target_id,
            kind=EdgeKind.IMPORTS,
        )
    )
    resolved_targets.add(target_id)


# ---------------------------------------------------------------------------
# Single-file parsing
# ---------------------------------------------------------------------------


def _extract_call_names(block: ts.Node) -> list[str]:
    """Recursively collect supported call names from a subtree.

    Captures simple identifier calls (``helper()``) plus same-class
    attribute calls on ``self``/``cls`` (``self.helper()``). The latter
    stays within the accepted same-file/class resolution scope.
    """
    names: list[str] = []
    _collect_calls(block, names)
    return names


def _collect_calls(node: ts.Node, names: list[str]) -> None:
    """Walk descendants and collect supported call target names."""
    if node.type == "call":
        fn = node.child_by_field_name("function")
        if fn is not None:
            if fn.type == "identifier":
                names.append(_text(fn))
            elif fn.type == "attribute":
                object_node = fn.child_by_field_name("object")
                attribute_node = fn.child_by_field_name("attribute")
                if (
                    object_node is not None
                    and attribute_node is not None
                    and object_node.type == "identifier"
                    and attribute_node.type == "identifier"
                ):
                    receiver = _text(object_node)
                    if receiver in {"self", "cls"}:
                        names.append(f"{receiver}.{_text(attribute_node)}")
    for child in node.children:
        _collect_calls(child, names)


def _extract_import_module(node: ts.Node) -> str:
    """Extract the module name from an import or import-from statement.

    For ``import os`` returns "os".
    For ``from mypackage.models import User`` returns "mypackage.models".
    """
    if node.type == "import_statement":
        for child in node.children:
            if child.type == "dotted_name":
                return _text(child)
    elif node.type == "import_from_statement":
        # The first dotted_name after "from" is the module path.
        found_from = False
        for child in node.children:
            if child.type == "from":
                found_from = True
                continue
            if found_from and child.type == "dotted_name":
                return _text(child)
            if child.type == "import":
                break
    return "<unknown>"


def parse_file(file_path: Path, repo_root: Path) -> SymbolGraph:
    """Parse a single Python file into a symbol graph.

    Returns a SymbolGraph containing nodes and edges for this file only.
    repo_root is used to compute relative paths for node IDs and
    file_path fields.
    """
    rel_path = str(file_path.relative_to(repo_root))
    file_stem = file_path.stem

    graph = SymbolGraph()

    try:
        source = file_path.read_bytes()
    except OSError:
        return graph

    tree = _PARSER.parse(source)
    root = tree.root_node

    # Determine line count from source (1-indexed end_line).
    line_count = source.count(b"\n")
    if source and not source.endswith(b"\n"):
        line_count += 1
    if line_count == 0 and len(source) > 0:
        line_count = 1

    # FILE node
    file_node_id = f"file:{rel_path}"
    file_node = SymbolNode(
        id=file_node_id,
        name=file_stem,
        kind=SymbolKind.FILE,
        file_path=rel_path,
        start_line=1,
        end_line=max(line_count, 1),
    )
    graph.nodes[file_node_id] = file_node

    # Track symbols for intra-file edge resolution.
    # Maps simple name -> node id for top-level functions/classes/constants.
    symbol_index: dict[str, str] = {}

    # Walk top-level children of the module node.
    for child in root.children:
        _process_top_level(child, rel_path, file_node_id, graph, symbol_index)

    # Build CALLS edges from function/method bodies.
    _resolve_intra_file_calls(root, rel_path, file_node_id, graph, symbol_index)

    return graph


def _process_top_level(
    node: ts.Node,
    rel_path: str,
    file_node_id: str,
    graph: SymbolGraph,
    symbol_index: dict[str, str],
) -> None:
    """Process a single top-level AST child and populate the graph."""
    actual = _unwrap_definition(node)
    if actual is not None:
        if actual.type == "function_definition":
            _add_function(
                actual,
                rel_path,
                file_node_id,
                graph,
                symbol_index,
                span_node=node,
            )
        elif actual.type == "class_definition":
            _add_class(
                actual,
                rel_path,
                file_node_id,
                graph,
                symbol_index,
                span_node=node,
            )

    elif node.type in ("import_statement", "import_from_statement"):
        _add_import(node, rel_path, file_node_id, graph)

    elif node.type == "expression_statement":
        _try_add_constant(node, rel_path, file_node_id, graph, symbol_index)


def _add_function(
    node: ts.Node,
    rel_path: str,
    parent_id: str,
    graph: SymbolGraph,
    symbol_index: dict[str, str],
    span_node: ts.Node | None = None,
) -> None:
    """Add a FUNCTION node and its DEFINES edge."""
    name = _node_name(node)
    node_id = f"{rel_path}::{name}"
    start, end = _node_span(node, span_node)
    sym = SymbolNode(
        id=node_id,
        name=name,
        kind=SymbolKind.FUNCTION,
        file_path=rel_path,
        start_line=start,
        end_line=end,
        parent_id=parent_id,
    )
    graph.nodes[node_id] = sym
    graph.edges.append(
        Edge(source_id=parent_id, target_id=node_id, kind=EdgeKind.DEFINES)
    )
    symbol_index[name] = node_id


def _add_class(
    node: ts.Node,
    rel_path: str,
    parent_id: str,
    graph: SymbolGraph,
    symbol_index: dict[str, str],
    span_node: ts.Node | None = None,
) -> None:
    """Add a CLASS node, its methods, and DEFINES edges."""
    class_name = _node_name(node)
    scoped_class_name = _scoped_symbol_name(rel_path, parent_id, class_name)
    class_id = _make_unique_node_id(f"{rel_path}::{scoped_class_name}", graph)
    start, end = _node_span(node, span_node)
    cls = SymbolNode(
        id=class_id,
        name=class_name,
        kind=SymbolKind.CLASS,
        file_path=rel_path,
        start_line=start,
        end_line=end,
        parent_id=parent_id,
    )
    graph.nodes[class_id] = cls
    graph.edges.append(
        Edge(source_id=parent_id, target_id=class_id, kind=EdgeKind.DEFINES)
    )
    if not parent_id.startswith(f"{rel_path}::"):
        symbol_index[class_name] = class_id

    # Walk class body for methods and nested classes.
    body = _find_block(node)
    if body is None:
        return

    for child in body.children:
        actual = _unwrap_definition(child)
        if actual is None:
            continue

        if actual.type == "function_definition":
            method_name = _node_name(actual)
            scoped_method_name = _scoped_symbol_name(rel_path, class_id, method_name)
            method_id = _make_unique_node_id(
                f"{rel_path}::{scoped_method_name}",
                graph,
            )
            m_start, m_end = _node_span(actual, child)
            method = SymbolNode(
                id=method_id,
                name=method_name,
                kind=SymbolKind.METHOD,
                file_path=rel_path,
                start_line=m_start,
                end_line=m_end,
                parent_id=class_id,
            )
            graph.nodes[method_id] = method
            graph.edges.append(
                Edge(source_id=class_id, target_id=method_id, kind=EdgeKind.DEFINES)
            )

        elif actual.type == "class_definition":
            # Nested class -- recurse.
            _add_class(actual, rel_path, class_id, graph, symbol_index, span_node=child)


def _find_block(node: ts.Node) -> ts.Node | None:
    """Find the block child of a class or function definition."""
    for child in node.children:
        if child.type == "block":
            return child
    return None


def _add_import(
    node: ts.Node,
    rel_path: str,
    parent_id: str,
    graph: SymbolGraph,
) -> None:
    """Add an IMPORT node and its DEFINES edge."""
    line = node.start_point.row + 1
    node_id = f"{rel_path}::import:{line}"
    module_name = _extract_import_module(node)
    imp = SymbolNode(
        id=node_id,
        name=module_name,
        kind=SymbolKind.IMPORT,
        file_path=rel_path,
        start_line=line,
        end_line=node.end_point.row + 1,
        parent_id=parent_id,
    )
    graph.nodes[node_id] = imp
    graph.edges.append(
        Edge(source_id=parent_id, target_id=node_id, kind=EdgeKind.DEFINES)
    )


def _try_add_constant(
    node: ts.Node,
    rel_path: str,
    parent_id: str,
    graph: SymbolGraph,
    symbol_index: dict[str, str],
) -> None:
    """If the expression_statement is an UPPER_SNAKE assignment, add a CONSTANT node."""
    if not node.children:
        return
    expr = node.children[0]
    if expr.type != "assignment":
        return
    target_name = _assignment_target_name(expr)
    if target_name is None or not _UPPER_SNAKE_RE.match(target_name):
        return

    node_id = f"{rel_path}::{target_name}"
    start = node.start_point.row + 1
    end = node.end_point.row + 1
    const = SymbolNode(
        id=node_id,
        name=target_name,
        kind=SymbolKind.CONSTANT,
        file_path=rel_path,
        start_line=start,
        end_line=end,
        parent_id=parent_id,
    )
    graph.nodes[node_id] = const
    graph.edges.append(
        Edge(source_id=parent_id, target_id=node_id, kind=EdgeKind.DEFINES)
    )
    symbol_index[target_name] = node_id


def _resolve_intra_file_calls(
    root: ts.Node,
    rel_path: str,
    file_node_id: str,
    graph: SymbolGraph,
    symbol_index: dict[str, str],
) -> None:
    """Walk function/method bodies and add CALLS edges for known in-file symbols."""
    for node_id, sym in list(graph.nodes.items()):
        if sym.kind not in (SymbolKind.FUNCTION, SymbolKind.METHOD):
            continue
        # Find the AST node for this function/method by line range.
        ast_node = _find_definition_node(root, sym.start_line)
        if ast_node is None:
            continue
        body = _find_block(ast_node)
        if body is None:
            continue
        call_names = _extract_call_names(body)
        seen: set[str] = set()
        for name in call_names:
            target = _resolve_intra_file_call_target(name, sym, graph, symbol_index)
            if target is not None and target != node_id and target not in seen:
                graph.edges.append(
                    Edge(source_id=node_id, target_id=target, kind=EdgeKind.CALLS)
                )
                seen.add(target)


def _resolve_intra_file_call_target(
    call_name: str,
    caller: SymbolNode,
    graph: SymbolGraph,
    symbol_index: dict[str, str],
) -> str | None:
    """Resolve a supported call name to an in-file symbol ID."""
    if call_name in symbol_index:
        return symbol_index[call_name]

    if caller.kind != SymbolKind.METHOD or "." not in call_name:
        return None

    receiver, _, method_name = call_name.partition(".")
    if receiver not in {"self", "cls"} or caller.parent_id is None:
        return None

    target_id = f"{caller.parent_id}.{method_name}"
    target = graph.nodes.get(target_id)
    if target is None or target.kind != SymbolKind.METHOD:
        return None
    return target_id


def _find_definition_node(root: ts.Node, start_line: int) -> ts.Node | None:
    """Find a function_definition or class_definition starting at the given line."""
    for child in root.children:
        if child.start_point.row + 1 == start_line and child.type in (
            "function_definition",
            "class_definition",
            "decorated_definition",
        ):
            if child.type == "decorated_definition":
                for sub in child.children:
                    if sub.type in ("function_definition", "class_definition"):
                        return sub
            return child
        # Look inside class bodies.
        if child.type in ("class_definition", "decorated_definition"):
            inner = child
            if child.type == "decorated_definition":
                for sub in child.children:
                    if sub.type == "class_definition":
                        inner = sub
                        break
            block = _find_block(inner)
            if block is not None:
                result = _find_definition_node(block, start_line)
                if result is not None:
                    return result
    return None


# ---------------------------------------------------------------------------
# Repository-level parsing
# ---------------------------------------------------------------------------


def parse_repository(root: Path) -> SymbolGraph:
    """Parse all Python files under root into a symbol graph.

    Recursively finds .py files, extracts symbol nodes and relationship
    edges, and returns a complete SymbolGraph. File paths in nodes are
    relative to root.
    """
    graph = SymbolGraph()

    # Discover all .py files.
    py_files = sorted(root.rglob("*.py"))

    # Build MODULE nodes for packages (directories with __init__.py).
    package_dirs: set[Path] = set()
    for py_file in py_files:
        if py_file.name == "__init__.py":
            package_dirs.add(py_file.parent)

    # Create MODULE nodes with proper nesting.
    module_ids: dict[Path, str] = {}
    for pkg_dir in sorted(package_dirs):
        rel = str(pkg_dir.relative_to(root))
        mod_id = f"module:{rel}"
        mod_name = pkg_dir.name
        mod_node = SymbolNode(
            id=mod_id,
            name=mod_name,
            kind=SymbolKind.MODULE,
            file_path=rel,
            start_line=0,
            end_line=0,
        )
        # Check for parent module.
        if pkg_dir.parent in package_dirs:
            parent_mod_id = module_ids[pkg_dir.parent]
            mod_node.parent_id = parent_mod_id
            graph.edges.append(
                Edge(source_id=parent_mod_id, target_id=mod_id, kind=EdgeKind.DEFINES)
            )
        graph.nodes[mod_id] = mod_node
        module_ids[pkg_dir] = mod_id

    # Parse each file and merge into the graph.
    for py_file in py_files:
        file_graph = parse_file(py_file, root)
        # Merge nodes.
        graph.nodes.update(file_graph.nodes)
        # Merge edges.
        graph.edges.extend(file_graph.edges)
        # Set parent_id on FILE nodes to their containing MODULE.
        rel_path = str(py_file.relative_to(root))
        file_node_id = f"file:{rel_path}"
        if py_file.parent in module_ids:
            parent_mod_id = module_ids[py_file.parent]
            if file_node_id in graph.nodes:
                graph.nodes[file_node_id].parent_id = parent_mod_id
                graph.edges.append(
                    Edge(
                        source_id=parent_mod_id,
                        target_id=file_node_id,
                        kind=EdgeKind.DEFINES,
                    )
                )

    # Resolve cross-file imports.
    _resolve_cross_file_imports(graph, root)

    return graph


def _resolve_cross_file_imports(graph: SymbolGraph, root: Path) -> None:
    """Best-effort resolution of IMPORTS edges across files.

    Matches import statements to files and symbols in the graph by resolving
    Python import paths. External imports produce no IMPORTS edges.
    """
    # Build lookup from Python module path to file node id.
    # e.g., "mypackage.models" -> "file:mypackage/models.py"
    module_path_to_file: dict[str, str] = {}
    for node_id, node in graph.nodes.items():
        if node.kind == SymbolKind.FILE:
            dotted = _module_path_from_file_path(node.file_path)
            if dotted is not None:
                module_path_to_file[dotted] = node_id

    # Build lookup from Python symbol name to node id within each file.
    # e.g., ("mypackage.models", "User") -> "mypackage/models.py::User"
    file_symbol_index: dict[str, dict[str, str]] = {}
    for node_id, node in graph.nodes.items():
        if node.kind in (
            SymbolKind.FUNCTION,
            SymbolKind.CLASS,
            SymbolKind.CONSTANT,
        ):
            dotted = _module_path_from_file_path(node.file_path)
            if dotted is None:
                continue
            if dotted not in file_symbol_index:
                file_symbol_index[dotted] = {}
            file_symbol_index[dotted][node.name] = node_id

    # Walk all IMPORT nodes and try to resolve them.
    for node_id, node in graph.nodes.items():
        if node.kind != SymbolKind.IMPORT:
            continue

        module_name = node.name  # e.g., "mypackage.models"
        imported_names = _get_imported_names_from_source(
            node.file_path,
            node.start_line,
            root,
        )
        imported_modules = _get_imported_modules_from_source(
            node.file_path,
            node.start_line,
            root,
        )
        resolved_targets: set[str] = set()

        resolved_submodule = False
        for imported_name in imported_names:
            submodule_path = f"{module_name}.{imported_name}"
            if submodule_path in module_path_to_file:
                _append_import_edge(
                    graph,
                    node_id,
                    module_path_to_file[submodule_path],
                    resolved_targets,
                )
                resolved_submodule = True

        for imported_module in imported_modules:
            if imported_module in module_path_to_file:
                _append_import_edge(
                    graph,
                    node_id,
                    module_path_to_file[imported_module],
                    resolved_targets,
                )

        if module_name in module_path_to_file and not resolved_submodule:
            _append_import_edge(
                graph,
                node_id,
                module_path_to_file[module_name],
                resolved_targets,
            )

        if module_name in file_symbol_index:
            symbols_in_module = file_symbol_index[module_name]
            for imported_name in imported_names:
                if imported_name in symbols_in_module:
                    _append_import_edge(
                        graph,
                        node_id,
                        symbols_in_module[imported_name],
                        resolved_targets,
                    )


def _read_source_line(rel_file_path: str, line_number: int, root: Path) -> str | None:
    """Return the requested source line stripped of surrounding whitespace/comments."""
    file_path = root / rel_file_path
    try:
        lines = file_path.read_text().splitlines()
    except OSError:
        return None

    if line_number < 1 or line_number > len(lines):
        return None

    return lines[line_number - 1].split("#", 1)[0].strip()


def _split_import_clause(clause: str) -> list[str]:
    """Split a simple import clause into names, preserving existing limitations."""
    sanitized = clause.replace("(", "").replace(")", "")
    parts = [part.strip() for part in sanitized.split(",")]
    return [
        part
        for part in parts
        if part and " as " not in part and not part.startswith(".")
    ]


def _get_imported_names_from_source(
    rel_file_path: str, line_number: int, root: Path
) -> list[str]:
    """Read the source line at line_number and extract imported names.

    Returns the list of names after "import" in statements like:
    ``from mypackage.models import User, validate_name``
    """
    line = _read_source_line(rel_file_path, line_number, root)
    if line is None or not line.startswith("from "):
        return []

    _, separator, names_part = line.partition(" import ")
    if not separator:
        return []

    return _split_import_clause(names_part)


def _get_imported_modules_from_source(
    rel_file_path: str,
    line_number: int,
    root: Path,
) -> list[str]:
    """Read the source line at line_number and extract imported module paths."""
    line = _read_source_line(rel_file_path, line_number, root)
    if line is None or not line.startswith("import "):
        return []

    return _split_import_clause(line[len("import ") :])
