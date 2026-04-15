"""Package-root public API policy tests."""

from pathlib import Path

import context_ir
import context_ir.semantic_types as semantic_types
from context_ir.semantic_types import SemanticProgram

RETIRED_GRAPH_FIRST_ROOT_NAMES = {
    "compile",
    "optimize",
    "parse_file",
    "parse_repository",
    "render",
    "score_graph",
}

ANALYZER_CONTRACT_NAMES = {
    "AssignmentFact",
    "AttributeSiteFact",
    "BaseExpressionFact",
    "BindingFact",
    "BindingKind",
    "CallSiteFact",
    "DataclassField",
    "DataclassModel",
    "DecoratorFact",
    "DecoratorSupport",
    "DefinitionKind",
    "DependencyProofKind",
    "DiagnosticSeverity",
    "ImportFact",
    "ImportKind",
    "ImportTargetKind",
    "ParameterFact",
    "ParameterKind",
    "ProofStatus",
    "RawDefinitionFact",
    "ReferenceContext",
    "ResolvedImport",
    "ResolvedReference",
    "ResolvedSymbol",
    "ResolvedSymbolKind",
    "ResolverDiagnostic",
    "SemanticDependency",
    "SemanticDependencyKind",
    "SemanticProgram",
    "SourceFileFact",
    "SourceSite",
    "SourceSpan",
    "SupportedDecorator",
    "SupportedSubsetBoundary",
    "SyntaxDiagnostic",
    "SyntaxDiagnosticCode",
    "SyntaxProgram",
    "UnresolvedAccess",
    "UnresolvedReasonCode",
    "UnsupportedConstruct",
}

SEMANTIC_MODULE_LEVEL_FUNCTIONS = {
    "bind_syntax",
    "compile_semantic_context",
    "derive_dependency_frontier",
    "diagnose_semantic_miss",
    "extract_syntax",
    "recompile_semantic_context",
    "render_semantic_unit",
    "resolve_semantics",
    "score_semantic_units",
    "optimize_semantic_units",
}


def test_package_root_all_matches_semantic_contract_surface() -> None:
    """The root public surface mirrors the semantic contract module."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert len(context_ir.__all__) == len(set(context_ir.__all__))


def test_package_root_exports_analyze_repository(tmp_path: Path) -> None:
    """The accepted low-level public analysis API remains callable at root."""
    (tmp_path / "example.py").write_text("VALUE = 1\n", encoding="utf-8")

    program = context_ir.analyze_repository(tmp_path)

    assert isinstance(program, SemanticProgram)
    assert program.repo_root == tmp_path


def test_package_root_exports_analyzer_contract_types() -> None:
    """Analyzer users can inspect returned programs from root-exported contracts."""
    public_names = set(context_ir.__all__)

    assert ANALYZER_CONTRACT_NAMES.issubset(public_names)

    for public_name in ANALYZER_CONTRACT_NAMES:
        assert hasattr(context_ir, public_name)


def test_retired_graph_first_apis_are_quarantined_from_root() -> None:
    """Retired graph-first APIs are not normalized as package-root exports."""
    public_names = set(context_ir.__all__)

    assert RETIRED_GRAPH_FIRST_ROOT_NAMES.isdisjoint(public_names)

    for retired_name in RETIRED_GRAPH_FIRST_ROOT_NAMES:
        assert not hasattr(context_ir, retired_name)


def test_old_graph_first_modules_remain_directly_importable() -> None:
    """Legacy graph-first modules still compile behind explicit module paths."""
    from context_ir.compiler import compile
    from context_ir.optimizer import optimize
    from context_ir.parser import parse_file, parse_repository
    from context_ir.renderer import render
    from context_ir.scorer import score_graph

    assert callable(compile)
    assert callable(optimize)
    assert callable(parse_file)
    assert callable(parse_repository)
    assert callable(render)
    assert callable(score_graph)


def test_semantic_module_level_apis_remain_directly_importable() -> None:
    """Semantic-first module APIs stay available at their explicit modules."""
    from context_ir.binder import bind_syntax
    from context_ir.dependency_frontier import derive_dependency_frontier
    from context_ir.parser import extract_syntax
    from context_ir.resolver import resolve_semantics
    from context_ir.semantic_compiler import compile_semantic_context
    from context_ir.semantic_diagnostics import (
        diagnose_semantic_miss,
        recompile_semantic_context,
    )
    from context_ir.semantic_optimizer import optimize_semantic_units
    from context_ir.semantic_renderer import render_semantic_unit
    from context_ir.semantic_scorer import score_semantic_units

    module_functions = {
        bind_syntax.__name__,
        compile_semantic_context.__name__,
        derive_dependency_frontier.__name__,
        diagnose_semantic_miss.__name__,
        extract_syntax.__name__,
        optimize_semantic_units.__name__,
        recompile_semantic_context.__name__,
        render_semantic_unit.__name__,
        resolve_semantics.__name__,
        score_semantic_units.__name__,
    }

    assert module_functions == SEMANTIC_MODULE_LEVEL_FUNCTIONS


def test_semantic_module_level_apis_are_not_root_exports() -> None:
    """Only ``analyze_repository`` is promoted to the package root for now."""
    public_names = set(context_ir.__all__)

    assert SEMANTIC_MODULE_LEVEL_FUNCTIONS.isdisjoint(public_names)

    for function_name in SEMANTIC_MODULE_LEVEL_FUNCTIONS:
        assert not hasattr(context_ir, function_name)
