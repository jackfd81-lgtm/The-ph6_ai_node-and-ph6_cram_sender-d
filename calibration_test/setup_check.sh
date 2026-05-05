#!/bin/bash
# Pre-flight check and mount helper for the calibration test.
# Run once before calibrate.py

set -e

PARTITION=/dev/sdb2
MOUNT=/mnt/calibration_drive

echo "=== Pre-flight Check ==="

# Block device
if [ ! -b "$PARTITION" ]; then
    echo "ERROR: $PARTITION not found. Check lsblk."
    lsblk -f /dev/sdb 2>/dev/null || echo "  /dev/sdb not visible either"
    exit 1
fi
echo "OK: $PARTITION exists"

# Mount point
sudo mkdir -p "$MOUNT"

# Already mounted?
if mountpoint -q "$MOUNT"; then
    echo "OK: $MOUNT already mounted"
    mount | grep "$MOUNT"
else
    echo "Mounting $PARTITION read-only at $MOUNT ..."
    sudo mount -o ro "$PARTITION" "$MOUNT"
    echo "OK: mounted"
fi

# Verify read-only
if mount | grep "$MOUNT" | grep -q '\bro\b'; then
    echo "OK: mounted read-only"
else
    echo "WARNING: not mounted read-only — remounting..."
    sudo mount -o remount,ro "$MOUNT"
fi

# Filesystem type
FS=$(lsblk -no FSTYPE "$PARTITION" 2>/dev/null)
echo "Filesystem: ${FS:-unknown}"
if [[ "$FS" == "ntfs" || "$FS" == "exfat" ]]; then
    echo "  Installing NTFS/exFAT support..."
    sudo apt-get install -y exfatprogs ntfs-3g
fi

# Python deps
echo ""
echo "=== Python Dependencies ==="
python3 -c "import cv2; print('cv2:', cv2.__version__)" 2>/dev/null || \
    { echo "Installing opencv..."; pip3 install opencv-python-headless; }
python3 -c "import numpy; print('numpy:', numpy.__version__)" 2>/dev/null || \
    { echo "Installing numpy..."; pip3 install numpy; }
which ffmpeg > /dev/null 2>&1 && echo "ffmpeg: $(ffmpeg -version 2>&1 | head -1)" || \
    { echo "Installing ffmpeg..."; sudo apt-get install -y ffmpeg; }

echo ""
echo "=== Contents of $MOUNT ==="
ls -lah "$MOUNT/"

echo ""
echo "Ready. Run: python3 /home/jack/calibration_test/calibrate.py"
