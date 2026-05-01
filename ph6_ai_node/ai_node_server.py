from fastapi import FastAPI, UploadFile, File
from datetime import datetime
import hashlib
import os

app = FastAPI()

INBOX = "inbox"
os.makedirs(INBOX, exist_ok=True)

@app.get("/health")
def health():
    return {
        "node": "PH6_AI_NODE",
        "status": "OK",
        "role": "LANE2_ADVISORY_ONLY",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.post("/process")
async def process_frame(file: UploadFile = File(...)):
    data = await file.read()
    frame_hash = hashlib.blake2b(data, digest_size=32).hexdigest()

    path = os.path.join(INBOX, f"{frame_hash}.jpg")
    with open(path, "wb") as f:
        f.write(data)

    # Placeholder — wire Hailo inference here
    result = {
        "authority": "NONE",
        "lane": "LANE2",
        "frame_hash": frame_hash,
        "ai_status": "RECEIVED",
        "labels": [],
        "note": "Hailo inference not wired yet"
    }

    return result
