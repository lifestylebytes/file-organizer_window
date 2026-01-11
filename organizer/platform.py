import os
import sys
import stat
from pathlib import Path


def is_windows():
    return os.name == "nt"


def is_macos():
    return sys.platform == "darwin"


def get_desktop_path() -> Path:
    if is_windows():
        return Path(os.environ["USERPROFILE"]) / "Desktop"
    return Path.home() / "Desktop"


def is_hidden_file(path: Path) -> bool:
    try:
        if is_windows():
            return bool(
                os.stat(path).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN
            )
        return path.name.startswith(".")
    except Exception:
        return False


def get_config_dir() -> Path:
    if is_windows():
        return Path(os.getenv("APPDATA")) / "FileOrganizer"
    return Path.home() / ".fileorganizer"
