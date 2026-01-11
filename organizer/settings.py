import json
from pathlib import Path
from organizer.platform import get_config_dir, get_desktop_path


DEFAULT_SETTINGS = {
    "target_dir": None,
    "rules": {
        "Images": [".jpg", ".png", ".webp"],
        "Videos": [".mp4", ".mov"],
    },
    "exclude_extensions": [".psd", ".blend", ".aep"],
    "on_conflict": None,        # rename | overwrite (필수 선택)
    "mode": None,               # move | inplace (필수 선택)
    "archive_folder": "Archive",
    "exclude_hidden": True,
}


def get_settings_path() -> Path:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "settings.json"


def load_settings() -> dict:
    path = get_settings_path()

    if not path.exists():
        settings = DEFAULT_SETTINGS.copy()
        settings["target_dir"] = str(get_desktop_path())
        save_settings(settings)
        return settings

    settings = json.loads(path.read_text(encoding="utf-8"))

    for key, value in DEFAULT_SETTINGS.items():
        if key not in settings:
            settings[key] = value

    if not settings.get("target_dir"):
        settings["target_dir"] = str(get_desktop_path())

    return settings


def save_settings(settings: dict):
    path = get_settings_path()
    path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def reset_settings() -> dict:
    settings = DEFAULT_SETTINGS.copy()
    settings["target_dir"] = str(get_desktop_path())
    save_settings(settings)
    return settings
