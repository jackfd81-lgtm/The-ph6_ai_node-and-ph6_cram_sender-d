import hashlib, json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path

def now_utc():
    return datetime.now(timezone.utc).isoformat()

def canonical_dumps(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def canonical_bytes(obj):
    return canonical_dumps(obj).encode("utf-8")

def blake2b256_bytes(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()

def canon_hash(obj) -> str:
    return blake2b256_bytes(canonical_bytes(obj))

def file_hash(path) -> str:
    h = hashlib.blake2b(digest_size=32)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))
        f.write("\n")

def append_jsonl(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(canonical_dumps(obj) + "\n")

def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

def atomic_write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    parent_fd = os.open(str(path.parent), os.O_DIRECTORY)
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(canonical_dumps(obj))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)
        if tmp_path and os.path.exists(tmp_path):
            try: os.unlink(tmp_path)
            except FileNotFoundError: pass
