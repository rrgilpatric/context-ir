"""Context IR: a budgeted context compiler for long-horizon coding agents."""

__version__ = "0.1.0"

from context_ir.parser import parse_file, parse_repository
from context_ir.renderer import render
from context_ir.scorer import score_graph

__all__ = ["parse_file", "parse_repository", "render", "score_graph"]
