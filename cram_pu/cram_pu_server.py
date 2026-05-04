from fastapi import FastAPI, UploadFile, File, Form
from pathlib import Path
from datetime import datetime
import shutil
import json
import hashlib
import uvicorn

BASE = Path.home() / "cram_pu"
INCOMING = BASE / "incoming"
RUNS = BASE / "runs"
REPORTS = BASE / "reports"
LOGS = BASE / "logs"

for p in [INCOMING, RUNS, REPORTS, LOGS]:
    p.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PH6 CRAM-PU Node", version="0.1")

MIN_VALID_FRAMES = 300

def blake2b256_file(path: Path) -> str:
    h = hashlib.blake2b(digest_size=32)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def now_id():
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

@app.get("/health")
def health():
    return {
        "node": "CRAM-PU",
        "status": "ALIVE",
        "authority": "LANE_1_DETERMINISTIC_ONLY",
        "soso_authority": "NONE",
        "min_valid_frames": MIN_VALID_FRAMES,
    }

@app.post("/upload_run")
async def upload_run(
    run_name: str = Form(default="unnamed_run"),
    frame_count: int = Form(default=0),
    pseudo_status: str = Form(default="UNKNOWN"),
    soso_status: str = Form(default="ADVISORY_ONLY"),
    file: UploadFile = File(...)
):
    run_id = f"{now_id()}_{run_name}".replace(" ", "_")
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    dest = run_dir / file.filename
    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_hash = blake2b256_file(dest)
    valid = frame_count >= MIN_VALID_FRAMES

    report = {
        "schema": "ph6.cram_pu.report.v0.1",
        "run_id": run_id,
        "run_name": run_name,
        "stored_file": str(dest),
        "file_hash_blake2b256": file_hash,
        "frame_count": frame_count,
        "minimum_required_frames": MIN_VALID_FRAMES,
        "valid_run": valid,
        "invalid_reason": None if valid else "UNDER_300_FRAMES",
        "pseudo_status": pseudo_status,
        "soso_status": soso_status,
        "authority_leakage_check": {
            "soso_authority": "NONE",
            "lane2_can_modify_pass_drop": False,
            "verdict": "PASS" if soso_status.upper() in ["ADVISORY_ONLY", "NONE"] else "HOLD"
        },
        "cram_pu_verdict": "ACCEPTED_FOR_REPLAY" if valid else "INVALID_RUN_REJECTED_FOR_CERT",
        "timestamp_utc": datetime.utcnow().isoformat() + "Z"
    }

    report_path = REPORTS / f"{run_id}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    with (LOGS / "cram_pu_events.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps(report) + "\n")

    return report

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765)
