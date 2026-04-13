"""Context IR: a budgeted context compiler for long-horizon coding agents."""

__version__ = "0.1.0"

from context_ir.parser import parse_file, parse_repository

__all__ = ["parse_file", "parse_repository"]
