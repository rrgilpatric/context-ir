"""View renderers for the 5 ViewTier levels.

Each renderer transforms a SymbolNode into a UnitView at a chosen
representation density, from OMIT (reference ID only) through FULL
(complete source). The SLICE tier is the key deliverable -- it
produces a self-contained excerpt that includes same-file
dependencies needed to understand the target symbol.
"""

from __future__ import annotations

import io
import keyword
import token
import tokenize
from pathlib import Path

import tree_sitter as ts
import tree_sitter_python as tspython

from context_ir.types import (
    EdgeKind,
    SymbolGraph,
    SymbolKind,
    SymbolNode,
    UnitView,
    ViewTier,
)

# ---------------------------------------------------------------------------
# Module-level constants and parser setup
# ---------------------------------------------------------------------------

_LANGUAGE: ts.Language = ts.Language(tspython.language())
_PARSER: ts.Parser = ts.Parser(_LANGUAGE)


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------


def estimate_tokens(text: str) -> int:
    """Estimate token count for a text string.

    Uses a character-based approximation (1 token per ~4 characters).
    Replaceable with a proper tokenizer later.
    """
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Public render entry point
# ---------------------------------------------------------------------------


def render(
    node_id: str,
    tier: ViewTier,
    graph: SymbolGraph,
    repo_root: Path,
) -> UnitView:
    """Render a symbol at the given representation tier.

    Looks up the node in graph.nodes, reads source from disk as needed,
    and returns a UnitView with rendered content and estimated token cost.

    Raises KeyError if node_id is not in the graph.
    """
    node = graph.nodes[node_id]  # Raises KeyError if missing

    if tier == ViewTier.OMIT:
        content = _render_omit(node)
    elif tier == ViewTier.SUMMARY:
        content = _render_summary(node, graph, repo_root)
    elif tier == ViewTier.STUB:
        content = _render_stub(node, graph, repo_root)
    elif tier == ViewTier.SLICE:
        content = _render_slice(node, graph, repo_root)
    else:
        content = _render_full(node, graph, repo_root)

    return UnitView(
        unit_id=node_id,
        tier=tier,
        content=content,
        token_cost=estimate_tokens(content),
    )


# ---------------------------------------------------------------------------
# Source reading helpers
# ---------------------------------------------------------------------------


def _read_file_text(file_path: str, repo_root: Path) -> str | None:
    """Read the full text of a file, returning None on failure."""
    try:
        return (repo_root / file_path).read_text()
    except OSError:
        return None


def _read_node_source(node: SymbolNode, repo_root: Path) -> str | None:
    """Read the source lines for a node from disk.

    Returns the text between start_line and end_line (1-indexed,
    inclusive), or None if the file cannot be read.
    """
    text = _read_file_text(node.file_path, repo_root)
    if text is None:
        return None
    lines = text.splitlines(keepends=True)
    if node.start_line < 1 or node.start_line > len(lines):
        return None
    selected = lines[node.start_line - 1 : node.end_line]
    return "".join(selected)


def _fallback(node_id: str) -> str:
    """Return a fallback content string for unavailable source."""
    return f"[source unavailable: {node_id}]"


# ---------------------------------------------------------------------------
# Tree-sitter helpers
# ---------------------------------------------------------------------------


def _find_child(parent: ts.Node, type_name: str) -> ts.Node | None:
    """Find the first child of the given type."""
    for child in parent.children:
        if child.type == type_name:
            return child
    return None


def _find_first_def(root: ts.Node) -> ts.Node | None:
    """Find the first function_definition in the tree, unwrapping decorators."""
    for child in root.children:
        if child.type == "function_definition":
            return child
        if child.type == "decorated_definition":
            for sub in child.children:
                if sub.type == "function_definition":
                    return sub
    return None


def _find_first_class(root: ts.Node) -> ts.Node | None:
    """Find the first class_definition in the tree, unwrapping decorators."""
    for child in root.children:
        if child.type == "class_definition":
            return child
        if child.type == "decorated_definition":
            for sub in child.children:
                if sub.type == "class_definition":
                    return sub
    return None


def _ts_text(node: ts.Node) -> str:
    """Decode tree-sitter node text."""
    raw = node.text
    if raw is None:
        return ""
    result: str = raw.decode()
    return result


def _extract_signature(source: str) -> str:
    """Extract the function/method signature from source.

    Returns the def line through the return annotation, without the
    trailing colon. Collapses multiline signatures into a single line.
    """
    tree = _PARSER.parse(source.encode())
    func = _find_first_def(tree.root_node)
    if func is None:
        lines = source.splitlines()
        return lines[0].rstrip().rstrip(":") if lines else ""

    block = _find_child(func, "block")
    if block is None:
        lines = source.splitlines()
        return lines[0].rstrip().rstrip(":") if lines else ""

    sig_bytes = source.encode()[func.start_byte : block.start_byte]
    sig = sig_bytes.decode().rstrip().rstrip(":")
    return " ".join(sig.split())


def _extract_docstring_first_line(source: str) -> str | None:
    """Extract the first line of a function or class docstring.

    Looks for a string literal as the first statement in the body block.
    """
    tree = _PARSER.parse(source.encode())
    def_node = _find_first_def(tree.root_node) or _find_first_class(tree.root_node)
    if def_node is None:
        return None

    block = _find_child(def_node, "block")
    if block is None:
        return None

    for child in block.children:
        if child.type == "expression_statement":
            for sub in child.children:
                if sub.type == "string":
                    return _strip_docstring_text(_ts_text(sub))
            break
    return None


def _strip_docstring_text(text: str) -> str | None:
    """Strip quotes from a docstring and return its first content line."""
    for quote in ('"""', "'''", '"', "'"):
        if (
            text.startswith(quote)
            and text.endswith(quote)
            and len(text) >= 2 * len(quote)
        ):
            text = text[len(quote) : -len(quote)]
            break
    stripped = text.strip()
    if not stripped:
        return None
    return stripped.splitlines()[0].strip()


def _extract_class_header(source: str) -> str:
    """Extract the class definition line (e.g., 'class User(Base)')."""
    tree = _PARSER.parse(source.encode())
    cls = _find_first_class(tree.root_node)
    if cls is None:
        lines = source.splitlines()
        return lines[0].rstrip().rstrip(":") if lines else ""

    block = _find_child(cls, "block")
    if block is None:
        lines = source.splitlines()
        return lines[0].rstrip().rstrip(":") if lines else ""

    header_bytes = source.encode()[cls.start_byte : block.start_byte]
    header = header_bytes.decode().rstrip().rstrip(":")
    return " ".join(header.split())


# ---------------------------------------------------------------------------
# Graph helpers
# ---------------------------------------------------------------------------


def _get_children(parent_id: str, graph: SymbolGraph) -> list[SymbolNode]:
    """Get direct children of a node via DEFINES edges."""
    child_ids = {
        e.target_id
        for e in graph.edges
        if e.source_id == parent_id and e.kind == EdgeKind.DEFINES
    }
    return [graph.nodes[cid] for cid in child_ids if cid in graph.nodes]


def _pluralize(count: int, singular: str) -> str:
    """Pluralize a count + noun pair."""
    if count == 1:
        return f"1 {singular}"
    if singular.endswith("s"):
        return f"{count} {singular}es"
    return f"{count} {singular}s"


# ---------------------------------------------------------------------------
# OMIT tier
# ---------------------------------------------------------------------------


def _render_omit(node: SymbolNode) -> str:
    """Render OMIT tier: just the reference ID."""
    return f"[ref: {node.id}]"


# ---------------------------------------------------------------------------
# SUMMARY tier
# ---------------------------------------------------------------------------


def _render_summary(node: SymbolNode, graph: SymbolGraph, repo_root: Path) -> str:
    """Render SUMMARY tier: one-line structural summary."""
    kind = node.kind
    if kind in (SymbolKind.FUNCTION, SymbolKind.METHOD):
        return _summary_callable(node, repo_root)
    if kind == SymbolKind.CLASS:
        return _summary_class(node, graph, repo_root)
    if kind in (SymbolKind.CONSTANT, SymbolKind.IMPORT):
        return _summary_source_line(node, repo_root)
    if kind == SymbolKind.FILE:
        return _summary_file(node, graph)
    if kind == SymbolKind.MODULE:
        return _summary_module(node, graph)
    return _fallback(node.id)


def _summary_callable(node: SymbolNode, repo_root: Path) -> str:
    """SUMMARY for a function or method: signature + docstring first line."""
    source = _read_node_source(node, repo_root)
    if source is None:
        return _fallback(node.id)
    sig = _extract_signature(source)
    doc = _extract_docstring_first_line(source)
    if doc:
        return f"{sig} -- {doc}"
    return sig


def _summary_class(node: SymbolNode, graph: SymbolGraph, repo_root: Path) -> str:
    """SUMMARY for a class: header + method count + docstring first line."""
    source = _read_node_source(node, repo_root)
    if source is None:
        return _fallback(node.id)
    header = _extract_class_header(source)
    method_count = sum(
        1
        for n in graph.nodes.values()
        if n.kind == SymbolKind.METHOD and n.parent_id == node.id
    )
    parts: list[str] = [header]
    if method_count > 0:
        parts.append(f"({_pluralize(method_count, 'method')})")
    doc = _extract_docstring_first_line(source)
    result = " ".join(parts)
    if doc:
        result += f" -- {doc}"
    return result


def _summary_source_line(node: SymbolNode, repo_root: Path) -> str:
    """SUMMARY for a constant or import: the full source line."""
    source = _read_node_source(node, repo_root)
    if source is None:
        return _fallback(node.id)
    return source.strip()


def _summary_file(node: SymbolNode, graph: SymbolGraph) -> str:
    """SUMMARY for a file: filename + symbol count."""
    children = _get_children(node.id, graph)
    counts: dict[str, int] = {}
    for child in children:
        if child.kind == SymbolKind.CLASS:
            counts["class"] = counts.get("class", 0) + 1
        elif child.kind == SymbolKind.FUNCTION:
            counts["function"] = counts.get("function", 0) + 1
        elif child.kind == SymbolKind.CONSTANT:
            counts["constant"] = counts.get("constant", 0) + 1
    parts: list[str] = []
    for kind_name in ("class", "function", "constant"):
        count = counts.get(kind_name, 0)
        if count > 0:
            parts.append(_pluralize(count, kind_name))
    filename = Path(node.file_path).name
    summary = ", ".join(parts)
    if summary:
        return f"{filename} ({summary})"
    return filename


def _summary_module(node: SymbolNode, graph: SymbolGraph) -> str:
    """SUMMARY for a module: package name + file count."""
    file_count = sum(
        1
        for n in graph.nodes.values()
        if n.kind == SymbolKind.FILE and n.parent_id == node.id
    )
    return f"{node.name}/ ({_pluralize(file_count, 'file')})"


# ---------------------------------------------------------------------------
# STUB tier
# ---------------------------------------------------------------------------


def _render_stub(node: SymbolNode, graph: SymbolGraph, repo_root: Path) -> str:
    """Render STUB tier: interface-level view."""
    kind = node.kind
    if kind in (SymbolKind.FUNCTION, SymbolKind.METHOD):
        return _stub_callable(node, repo_root)
    if kind == SymbolKind.CLASS:
        return _stub_class(node, graph, repo_root)
    if kind in (SymbolKind.CONSTANT, SymbolKind.IMPORT):
        return _summary_source_line(node, repo_root)
    if kind == SymbolKind.FILE:
        return _stub_file(node, graph, repo_root)
    if kind == SymbolKind.MODULE:
        return _stub_module(node, graph)
    return _fallback(node.id)


def _stub_callable(node: SymbolNode, repo_root: Path) -> str:
    """STUB for a function or method: signature with ... body."""
    source = _read_node_source(node, repo_root)
    if source is None:
        return _fallback(node.id)
    sig = _extract_signature(source)
    return f"{sig}: ..."


def _stub_class(node: SymbolNode, graph: SymbolGraph, repo_root: Path) -> str:
    """STUB for a class: header + docstring + method stubs."""
    source = _read_node_source(node, repo_root)
    if source is None:
        return _fallback(node.id)

    header = _extract_class_header(source)
    lines: list[str] = [f"{header}:"]

    doc = _extract_docstring_first_line(source)
    if doc:
        lines.append(f'    """{doc}"""')

    methods = sorted(
        [
            n
            for n in graph.nodes.values()
            if n.kind == SymbolKind.METHOD and n.parent_id == node.id
        ],
        key=lambda n: n.start_line,
    )
    for method in methods:
        method_source = _read_node_source(method, repo_root)
        if method_source is not None:
            sig = _extract_signature(method_source)
            lines.append(f"    {sig}: ...")

    return "\n".join(lines)


def _stub_file(node: SymbolNode, graph: SymbolGraph, repo_root: Path) -> str:
    """STUB for a file: concatenation of STUB views for top-level symbols."""
    children = _get_children(node.id, graph)
    children.sort(key=lambda n: n.start_line)
    parts: list[str] = []
    for child in children:
        stub = _render_stub(child, graph, repo_root)
        parts.append(stub)
    return "\n".join(parts)


def _stub_module(node: SymbolNode, graph: SymbolGraph) -> str:
    """STUB for a module: list of file names."""
    file_children = sorted(
        [
            n
            for n in graph.nodes.values()
            if n.kind == SymbolKind.FILE and n.parent_id == node.id
        ],
        key=lambda n: n.file_path,
    )
    return "\n".join(Path(f.file_path).name for f in file_children)


# ---------------------------------------------------------------------------
# SLICE tier
# ---------------------------------------------------------------------------


def _render_slice(node: SymbolNode, graph: SymbolGraph, repo_root: Path) -> str:
    """Render SLICE tier: dependency-preserving source slice.

    For functions, methods, and classes, includes same-file imports,
    constants, and called function stubs that the symbol references.
    For other kinds, falls through to FULL.
    """
    if node.kind in (SymbolKind.FUNCTION, SymbolKind.METHOD):
        return _slice_callable(node, graph, repo_root)
    if node.kind == SymbolKind.CLASS:
        return _slice_class(node, graph, repo_root)
    return _render_full(node, graph, repo_root)


def _slice_callable(node: SymbolNode, graph: SymbolGraph, repo_root: Path) -> str:
    """SLICE for a function or method: source + same-file dependencies."""
    source = _read_node_source(node, repo_root)
    if source is None:
        return _fallback(node.id)

    file_node_id = f"file:{node.file_path}"
    same_file_nodes = _get_children(file_node_id, graph)

    import_lines = _find_relevant_imports(source, same_file_nodes, repo_root)
    constant_lines = _find_relevant_constants(source, same_file_nodes, repo_root)
    called_stubs = _find_called_stubs(node, graph, repo_root)

    return _assemble_slice(import_lines, constant_lines, called_stubs, source)


def _slice_class(node: SymbolNode, graph: SymbolGraph, repo_root: Path) -> str:
    """SLICE for a class: full source + same-file dependencies."""
    source = _read_node_source(node, repo_root)
    if source is None:
        return _fallback(node.id)

    file_node_id = f"file:{node.file_path}"
    same_file_nodes = _get_children(file_node_id, graph)

    import_lines = _find_relevant_imports(source, same_file_nodes, repo_root)
    constant_lines = _find_relevant_constants(source, same_file_nodes, repo_root)
    called_stubs = _find_class_called_stubs(node, graph, repo_root)

    return _assemble_slice(import_lines, constant_lines, called_stubs, source)


def _assemble_slice(
    import_lines: list[str],
    constant_lines: list[str],
    called_stubs: list[str],
    source: str,
) -> str:
    """Assemble sections of a SLICE into a formatted string."""
    sections: list[str] = []
    if import_lines:
        sections.append("# Imports\n" + "\n".join(import_lines))
    if constant_lines:
        sections.append("# Constants\n" + "\n".join(constant_lines))
    if called_stubs:
        sections.append("# Referenced signatures\n" + "\n".join(called_stubs))
    sections.append("# Source\n" + source.rstrip())
    return "\n\n".join(sections)


def _find_relevant_imports(
    source: str,
    same_file_nodes: list[SymbolNode],
    repo_root: Path,
) -> list[str]:
    """Find import statements from the same file that the source references."""
    referenced_names = _extract_executable_names(source)
    results: list[str] = []
    for node in same_file_nodes:
        if node.kind != SymbolKind.IMPORT:
            continue
        imp_source = _read_node_source(node, repo_root)
        if imp_source is None:
            continue
        names = _extract_import_names(imp_source.strip())
        for name in names:
            if name in referenced_names:
                results.append(imp_source.strip())
                break
    return results


def _extract_import_names(import_text: str) -> list[str]:
    """Extract the names introduced by an import statement."""
    if import_text.startswith("from ") and "import " in import_text:
        parts = import_text.split("import", 1)
        if len(parts) >= 2:
            names_part = parts[1].replace("(", "").replace(")", "")
            names: list[str] = []
            for segment in names_part.split(","):
                segment = segment.strip()
                if " as " in segment:
                    segment = segment.split(" as ")[-1].strip()
                if segment and not segment.startswith("#"):
                    names.append(segment)
            return names
    elif import_text.startswith("import "):
        name_part = import_text.split("import", 1)[1].strip()
        if " as " in name_part:
            name = name_part.split(" as ")[-1].strip()
        else:
            name = name_part.split(".")[0].strip()
        if name:
            return [name]
    return []


def _find_relevant_constants(
    source: str,
    same_file_nodes: list[SymbolNode],
    repo_root: Path,
) -> list[str]:
    """Find constants from the same file that the source references."""
    referenced_names = _extract_executable_names(source)
    results: list[str] = []
    for node in same_file_nodes:
        if node.kind != SymbolKind.CONSTANT:
            continue
        if node.name in referenced_names:
            const_source = _read_node_source(node, repo_root)
            if const_source is not None:
                results.append(const_source.strip())
    return results


def _extract_executable_names(source: str) -> set[str]:
    """Extract identifier tokens while ignoring comments and string literals."""
    names: set[str] = set()
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    except (IndentationError, tokenize.TokenError):
        return names

    for tok in tokens:
        if tok.type == token.NAME and not keyword.iskeyword(tok.string):
            names.add(tok.string)
    return names


def _find_called_stubs(
    node: SymbolNode,
    graph: SymbolGraph,
    repo_root: Path,
) -> list[str]:
    """Find stubs for same-file functions/methods called by this node."""
    called_ids = {
        e.target_id
        for e in graph.edges
        if e.source_id == node.id and e.kind == EdgeKind.CALLS
    }
    stubs: list[str] = []
    for target_id in sorted(called_ids):
        target = graph.nodes.get(target_id)
        if target is None or target.file_path != node.file_path:
            continue
        if target.kind in (SymbolKind.FUNCTION, SymbolKind.METHOD):
            stubs.append(_stub_callable(target, repo_root))
    return stubs


def _find_class_called_stubs(
    node: SymbolNode,
    graph: SymbolGraph,
    repo_root: Path,
) -> list[str]:
    """Find stubs for same-file functions called by any method of this class."""
    method_ids = {
        n.id
        for n in graph.nodes.values()
        if n.kind == SymbolKind.METHOD and n.parent_id == node.id
    }
    all_sources = method_ids | {node.id}

    called_ids: set[str] = set()
    for edge in graph.edges:
        if edge.source_id in all_sources and edge.kind == EdgeKind.CALLS:
            called_ids.add(edge.target_id)

    stubs: list[str] = []
    for target_id in sorted(called_ids):
        target = graph.nodes.get(target_id)
        if target is None or target.file_path != node.file_path:
            continue
        if target.kind in (SymbolKind.FUNCTION, SymbolKind.METHOD):
            if target.parent_id == node.id:
                continue
            stubs.append(_stub_callable(target, repo_root))
    return stubs


# ---------------------------------------------------------------------------
# FULL tier
# ---------------------------------------------------------------------------


def _render_full(node: SymbolNode, graph: SymbolGraph, repo_root: Path) -> str:
    """Render FULL tier: exact source code from disk."""
    if node.kind == SymbolKind.FILE:
        text = _read_file_text(node.file_path, repo_root)
        if text is None:
            return _fallback(node.id)
        return text
    if node.kind == SymbolKind.MODULE:
        return _full_module(node, graph, repo_root)
    source = _read_node_source(node, repo_root)
    if source is None:
        return _fallback(node.id)
    return source


def _full_module(node: SymbolNode, graph: SymbolGraph, repo_root: Path) -> str:
    """Render FULL for a MODULE: __init__.py content or file listing."""
    init_path = repo_root / node.file_path / "__init__.py"
    try:
        return init_path.read_text()
    except OSError:
        pass
    file_children = sorted(
        [
            n
            for n in graph.nodes.values()
            if n.kind == SymbolKind.FILE and n.parent_id == node.id
        ],
        key=lambda n: n.file_path,
    )
    return "\n".join(Path(f.file_path).name for f in file_children)
