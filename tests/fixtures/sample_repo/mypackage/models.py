"""Data models for the sample package."""

import os  # noqa: F401

MAX_NAME_LENGTH = 128
DEFAULT_ROLE = "member"


class User:
    """A user in the system."""

    def __init__(self, name: str, role: str = DEFAULT_ROLE) -> None:
        self.name = name
        self.role = role

    def display_name(self) -> str:
        """Return the formatted display name."""
        return f"{self.name} ({self.role})"


def check_length(name: str) -> bool:
    """Return True if the name is within the allowed length."""
    return len(name) <= MAX_NAME_LENGTH


def validate_name(name: str) -> bool:
    """Check whether a name is valid."""
    if not check_length(name):
        return False
    return len(name.strip()) > 0
