"""CLI helpers. Usage: python -m app.cli hash <password>"""

import sys

from app.auth import hash_password


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 2 and argv[0] == "hash":
        print(hash_password(argv[1]))
        return 0
    print("usage: python -m app.cli hash <password>", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
