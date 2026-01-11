import json
from pathlib import Path
from datetime import datetime
from organizer.platform import get_config_dir

MAX_UNDO = 10


def get_undo_dir() -> Path:
    undo_dir = get_config_dir() / "undo"
    undo_dir.mkdir(parents=True, exist_ok=True)
    return undo_dir


def get_undo_files() -> list[Path]:
    undo_dir = get_undo_dir()
    return sorted(
        undo_dir.glob("undo_*.json"),
        key=lambda p: p.name
    )


def shift_undo_logs():
    files = get_undo_files()
    # 오래된 것부터 삭제
    if len(files) >= MAX_UNDO:
        files[-1].unlink()

    # 번호 밀기 (9 → 10, 8 → 9 ...)
    for f in reversed(files):
        idx = int(f.stem.split("_")[1])
        f.rename(f.with_name(f"undo_{idx + 1:03}.json"))


def write_undo_log(operations: list):
    shift_undo_logs()

    data = {
        "timestamp": datetime.now().isoformat(),
        "operations": operations
    }

    path = get_undo_dir() / "undo_000.json"
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def read_latest_undo() -> dict | None:
    files = get_undo_files()
    if not files:
        return None
    return json.loads(files[0].read_text(encoding="utf-8"))


def pop_latest_undo():
    files = get_undo_files()
    if files:
        files[0].unlink()


def undo_last_operation():
    log = read_latest_undo()
    if not log:
        raise RuntimeError("되돌릴 작업이 없습니다.")

    for op in reversed(log["operations"]):
        src = Path(op["to"])
        dst = Path(op["from"])

        if not src.exists():
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)

    pop_latest_undo()
