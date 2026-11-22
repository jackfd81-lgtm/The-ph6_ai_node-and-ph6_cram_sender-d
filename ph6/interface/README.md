# PH6 Local Desktop Interface v1

Lightweight FastAPI web dashboard for PH6 system control.

## Start

```bash
cd /home/jack/ph6/interface
python3 -m uvicorn app:app --host 127.0.0.1 --port 8765
```

Access from local terminal: `curl http://127.0.0.1:8765/api/status`

Access from Chromebook via SSH tunnel:
```bash
ssh -L 8765:127.0.0.1:8765 jack@192.168.254.188
# then open: http://127.0.0.1:8765
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard — system health, git, safety locks |
| `/tests` | Run CRAM test, governance scan, preflight, compileall |
| `/reports` | Browse PH6_SOURCE/DEPLOYMENT/*.md reports |
| `/fleet` | Pi 5 + Zero 2W sentinel status |
| `/settings` | Edit settings.json |
| `/api/status` | JSON system status |
| `/api/settings` | JSON settings |

## Safety

- Camera tests: DISABLED by default
- USB tests: DISABLED by default
- CAN HAT: DEFERRED by default
- Destructive actions: BLOCKED by default
- All subprocess commands are whitelisted in Python — no user free-text execution
- Settings saved atomically (write-tmp → fsync → replace → fsync-dir)
- Report path traversal blocked

## Install dependencies (if needed)

```bash
pip3 install -r requirements.txt
```
