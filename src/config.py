"""Configuration: load .env once and resolve paths from the project folder.

Every module reads settings through here, so `.env` is always loaded before
a variable is read, and relative paths (`./storage/...`, `data/...`) point
at the same place whichever directory the command is started from.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def path(value: str | os.PathLike) -> Path:
    """An absolute path; relative values are taken from the project folder."""
    p = Path(value).expanduser()
    return p if p.is_absolute() else ROOT / p


def setting_path(name: str, default: str) -> Path:
    return path(os.getenv(name, default))
