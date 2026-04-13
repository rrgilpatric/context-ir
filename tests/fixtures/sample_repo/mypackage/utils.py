"""Utility functions for the sample package."""

from mypackage.models import User, validate_name

GREETING_PREFIX = "Hello"


def format_name(name: str) -> str:
    """Format a name for display."""
    if validate_name(name):
        return name.strip().title()
    return "Unknown"


def greet_user(user: User) -> str:
    """Build a greeting string for the given user."""
    display = user.display_name()
    return f"{GREETING_PREFIX}, {display}!"
