"""Entry point for the sample application."""

import sys

from mypackage.models import User
from mypackage.utils import format_name, greet_user

EXIT_SUCCESS = 0


def main() -> int:
    """Run the sample application."""
    name = format_name("alice")
    user = User(name=name)
    greeting = greet_user(user)
    print(greeting)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
