"""Package bridge for the repository's flat ``src`` module layout."""

from pathlib import Path


__path__.append(str(Path(__file__).resolve().parent.parent))
