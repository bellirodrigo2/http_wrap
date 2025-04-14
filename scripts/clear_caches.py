import os
import shutil
from pathlib import Path


def clear_python_caches(root_dir: Path = Path(".")) -> None:
    for path in root_dir.rglob("*"):
        if path.is_dir() and path.name == "__pycache__":
            print(f"Removing: {path}")
            shutil.rmtree(path, ignore_errors=True)
        elif path.suffix in {".pyc", ".pyo"}:
            print(f"Deleting: {path}")
            path.unlink(missing_ok=True)


def main():
    clear_python_caches()


if __name__ == "__main__":
    main()
