import os
import sys


def _ensure_repo_root_on_path() -> None:
    """Ensure project root (containing the `src` package) is importable.

    Pytest runs from the repo root by default, but in some environments
    `PYTHONPATH` may not include it. The tests import modules using the
    `src` package (src-layout). This adds the repository root to `sys.path`.
    """

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


_ensure_repo_root_on_path()

