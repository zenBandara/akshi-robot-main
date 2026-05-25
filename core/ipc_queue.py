import json
import os
import time
import uuid


def append_ipc_command(command: dict, file_path: str) -> str:
    """Append a single IPC command as JSONL.

    We intentionally use JSON Lines (one JSON object per line) so multiple
    commands cannot overwrite each other (the previous implementation used
    json.dump(..., "w") which is last-write-wins).

    Returns the generated command id.
    """
    cmd = dict(command or {})
    cmd.setdefault("id", str(uuid.uuid4()))
    cmd.setdefault("ts", time.time())

    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

    # Append a single line. This is the simplest cross-process safe-ish primitive
    # we have without introducing a real IPC channel.
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(cmd, ensure_ascii=True) + "\n")

    return cmd["id"]
