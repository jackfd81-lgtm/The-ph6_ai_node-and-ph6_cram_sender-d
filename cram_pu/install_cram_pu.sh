#!/bin/bash
set -e

echo "[1/5] Creating dirs..."
mkdir -p ~/cram_pu/{incoming,runs,reports,logs,tools}

echo "[2/5] Installing pip + deps via apt..."
sudo apt-get install -y python3-pip python3-venv 2>&1 | tail -3
python3 -m venv ~/cram_pu/.venv
~/cram_pu/.venv/bin/pip install --quiet fastapi uvicorn python-multipart
echo "      deps OK"

echo "[3/5] Fetching server..."
curl -s http://192.168.254.188:9090/cram_pu_server.py -o ~/cram_pu/cram_pu_server.py
echo "      server OK"

echo "[4/5] Installing systemd service..."
sudo tee /etc/systemd/system/cram_pu.service > /dev/null <<UNIT
[Unit]
Description=PH6 CRAM-PU Receiver Node
After=network.target

[Service]
Type=simple
User=jack
WorkingDirectory=/home/jack/cram_pu
ExecStart=/home/jack/cram_pu/.venv/bin/python3 /home/jack/cram_pu/cram_pu_server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable cram_pu
sudo systemctl start cram_pu

echo "[5/5] Health check..."
sleep 3
curl -s http://localhost:8765/health
echo ""
echo "DONE."
