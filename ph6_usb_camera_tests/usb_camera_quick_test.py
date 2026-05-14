import cv2
import time
import sys

CAM_INDEX = int(sys.argv[1]) if len(sys.argv) > 1 else 0

cap = cv2.VideoCapture(CAM_INDEX)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print(f"FAIL: Could not open camera index {CAM_INDEX}")
    sys.exit(1)

print(f"PASS: Camera index {CAM_INDEX} opened")

# warmup — discard first few frames
for _ in range(5):
    cap.read()

for i in range(10):
    ok, frame = cap.read()
    if not ok or frame is None:
        print(f"FAIL: Frame {i} not captured")
        cap.release()
        sys.exit(1)

    print(f"Frame {i}: shape={frame.shape}")

cap.release()
print("PASS: Quick camera frame test complete")
