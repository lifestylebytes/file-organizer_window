from pathlib import Path
import shutil
from organizer.platform import is_hidden_file
from organizer.undo import write_undo_log


def resolve_conflict(dest: Path, mode: str) -> Path:
    if not dest.exists():
        return dest

    if mode == "overwrite":
        dest.unlink()
        return dest

    base = dest.stem
    ext = dest.suffix
    i = 1
    while True:
        new = dest.with_name(f"{base}_{i}{ext}")
        if not new.exists():
            return new
        i += 1


def organize_desktop(
    target_dir: Path,
    rules: dict,
    exclude_extensions: list,
    mode: str,
    conflict_mode: str,
    archive_folder: str,
    exclude_hidden: bool,
):
    operations = []

    # 기준 디렉터리 결정
    if mode == "move":
        base_dir = target_dir / archive_folder
    else:
        base_dir = target_dir

    base_dir.mkdir(exist_ok=True)

    for item in target_dir.iterdir():

        if exclude_hidden and is_hidden_file(item):
            continue

        if not item.is_file():
            continue

        if item.suffix.lower() in exclude_extensions:
            continue

        ext = item.suffix.lower()
        category = rules.get(ext, "Others")

        dest_dir = base_dir / category
        dest_dir.mkdir(exist_ok=True)

        dest = dest_dir / item.name
        final_dest = resolve_conflict(dest, conflict_mode)

        operations.append({
            "from": str(item),
            "to": str(final_dest)
        })

        shutil.move(str(item), str(final_dest))

    if operations:
        write_undo_log(operations)
