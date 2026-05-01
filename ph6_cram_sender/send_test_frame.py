import requests
import sys
import json

AI_NODE_URL = "http://192.168.10.2:8000"

def check_health():
    r = requests.get(f"{AI_NODE_URL}/health", timeout=3)
    r.raise_for_status()
    return r.json()

def send_frame(path):
    with open(path, "rb") as f:
        r = requests.post(f"{AI_NODE_URL}/process", files={"file": f}, timeout=5)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Checking AI node health...")
        result = check_health()
        print(json.dumps(result, indent=2))
    else:
        frame_path = sys.argv[1]
        print(f"Sending: {frame_path}")
        result = send_frame(frame_path)
        print(json.dumps(result, indent=2))
