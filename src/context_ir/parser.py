"""Tree-sitter-based parser that builds a SymbolGraph from a Python codebase."""

from __future__ import annotations

import re
from pathlib import Path

import tree_sitter as ts
import tree_sitter_python as tspython

from context_ir.types import Edge, EdgeKind, SymbolGraph, SymbolKind, SymbolNode

# ---------------------------------------------------------------------------
# Module-level constants and parser setup
# ---------------------------------------------------------------------------

_UPPER_SNAKE_RE: re.Pattern[str] = re.compile(r"^[A-Z][A-Z0-9_]*$")

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


# ---------------------------------------------------------------------------
# Single-file parsing
# ---------------------------------------------------------------------------


def _extract_call_names(block: ts.Node) -> list[str]:
    """Recursively collect simple call names (identifiers only) from a subtree."""
    names: list[str] = []
    _collect_calls(block, names)
    return names


def _collect_calls(node: ts.Node, names: list[str]) -> None:
    """Walk all descendants looking for call expressions with identifier functions."""
    if node.type == "call":
        fn = node.child_by_field_name("function")
        if fn is not None and fn.type == "identifier":
            names.append(_text(fn))
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
    if node.type == "function_definition":
        _add_function(node, rel_path, file_node_id, graph, symbol_index)

    elif node.type == "class_definition":
        _add_class(node, rel_path, file_node_id, graph, symbol_index)

    elif node.type in ("import_statement", "import_from_statement"):
        _add_import(node, rel_path, file_node_id, graph)

    elif node.type == "expression_statement":
        _try_add_constant(node, rel_path, file_node_id, graph, symbol_index)

    elif node.type == "decorated_definition":
        # Unwrap decorator to find the actual definition.
        for child in node.children:
            if child.type in ("function_definition", "class_definition"):
                _process_top_level(child, rel_path, file_node_id, graph, symbol_index)
                break


def _add_function(
    node: ts.Node,
    rel_path: str,
    parent_id: str,
    graph: SymbolGraph,
    symbol_index: dict[str, str],
) -> None:
    """Add a FUNCTION node and its DEFINES edge."""
    name = _node_name(node)
    node_id = f"{rel_path}::{name}"
    start = node.start_point.row + 1
    end = node.end_point.row + 1
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
) -> None:
    """Add a CLASS node, its methods, and DEFINES edges."""
    class_name = _node_name(node)
    class_id = f"{rel_path}::{class_name}"
    start = node.start_point.row + 1
    end = node.end_point.row + 1
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
    symbol_index[class_name] = class_id

    # Walk class body for methods and nested classes.
    body = _find_block(node)
    if body is None:
        return

    for child in body.children:
        actual = child
        if child.type == "decorated_definition":
            for sub in child.children:
                if sub.type in ("function_definition", "class_definition"):
                    actual = sub
                    break
            else:
                continue

        if actual.type == "function_definition":
            method_name = _node_name(actual)
            method_id = f"{rel_path}::{class_name}.{method_name}"
            m_start = actual.start_point.row + 1
            m_end = actual.end_point.row + 1
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
            _add_class(actual, rel_path, class_id, graph, symbol_index)


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
            if name in symbol_index and name not in seen:
                target = symbol_index[name]
                if target != node_id:
                    graph.edges.append(
                        Edge(source_id=node_id, target_id=target, kind=EdgeKind.CALLS)
                    )
                    seen.add(name)


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
            # Convert file path to dotted module path.
            py_path = node.file_path
            if py_path.endswith("/__init__.py"):
                dotted = py_path[: -len("/__init__.py")].replace("/", ".")
            elif py_path.endswith(".py"):
                dotted = py_path[: -len(".py")].replace("/", ".")
            else:
                continue
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
            # Determine which module this belongs to.
            file_path = node.file_path
            if file_path.endswith("/__init__.py"):
                dotted = file_path[: -len("/__init__.py")].replace("/", ".")
            elif file_path.endswith(".py"):
                dotted = file_path[: -len(".py")].replace("/", ".")
            else:
                continue
            if dotted not in file_symbol_index:
                file_symbol_index[dotted] = {}
            file_symbol_index[dotted][node.name] = node_id

    # Walk all IMPORT nodes and try to resolve them.
    for node_id, node in graph.nodes.items():
        if node.kind != SymbolKind.IMPORT:
            continue

        module_name = node.name  # e.g., "mypackage.models"

        # Try to find the target file.
        if module_name in module_path_to_file:
            target_file_id = module_path_to_file[module_name]
            graph.edges.append(
                Edge(source_id=node_id, target_id=target_file_id, kind=EdgeKind.IMPORTS)
            )

        # Try to resolve individual imported names to symbols.
        # Read the original AST node text is not available, so we use the
        # module name to look up symbols.
        if module_name in file_symbol_index:
            symbols_in_module = file_symbol_index[module_name]
            # We need to know which names were imported. The IMPORT node
            # only stores the module name. We look at the node's file to
            # find the actual import statement by line number.
            imported_names = _get_imported_names_from_source(
                node.file_path, node.start_line, root
            )
            for iname in imported_names:
                if iname in symbols_in_module:
                    graph.edges.append(
                        Edge(
                            source_id=node_id,
                            target_id=symbols_in_module[iname],
                            kind=EdgeKind.IMPORTS,
                        )
                    )


def _get_imported_names_from_source(
    rel_file_path: str, line_number: int, root: Path
) -> list[str]:
    """Read the source line at line_number and extract imported names.

    Returns the list of names after "import" in statements like:
    ``from mypackage.models import User, validate_name``
    """
    file_path = root / rel_file_path
    try:
        lines = file_path.read_text().splitlines()
    except OSError:
        return []

    if line_number < 1 or line_number > len(lines):
        return []

    line = lines[line_number - 1]
    # Handle "from X import Y, Z" and "import X"
    if "import" in line:
        # For "from X import Y, Z" -- get everything after the last "import".
        parts = line.split("import")
        if len(parts) >= 2:
            names_part = parts[-1]
            # Strip parentheses, commas, whitespace.
            names_part = names_part.replace("(", "").replace(")", "")
            names = [n.strip() for n in names_part.split(",")]
            return [n for n in names if n and not n.startswith("#")]
    return []
