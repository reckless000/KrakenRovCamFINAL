from flask import Flask, Response, send_file
import cv2
import time
import threading
from ultralytics import YOLO  # ← NEW: load YOLO

app = Flask(__name__)

# ─────────────────────────────────────────────
# LOAD YOUR TRAINED MODEL
# Make sure best.pt is in the same folder as this script
# ─────────────────────────────────────────────
model = YOLO("best.pt")  # ← NEW
print("✅ Green crab model loaded!")

# ─────────────────────────────────────────────
# CAMERAS
# Update indexes if needed (0, 1, 2)
# ─────────────────────────────────────────────
cam_front   = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cam_gripper = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # ← fixed index to 1

def setup_cam(cam):
    cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cam.set(cv2.CAP_PROP_FPS, 30)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

setup_cam(cam_front)
setup_cam(cam_gripper)

# ─────────────────────────────────────────────
# SHARED FRAME STORAGE
# Only front and gripper now (removed rear)
# ─────────────────────────────────────────────
latest_frames = {"front": None, "gripper": None}
frame_locks   = {"front": threading.Lock(), "gripper": threading.Lock()}
rotations     = {"front": cv2.ROTATE_180, "gripper": None}

# ─────────────────────────────────────────────
# BACKGROUND READER THREADS
# Constantly drain frames so buffer never fills up
# ─────────────────────────────────────────────
def reader(cam, name):
    while True:
        success, frame = cam.read()
        if not success:
            time.sleep(0.01)
            continue
        with frame_locks[name]:
            latest_frames[name] = frame

threading.Thread(target=reader, args=(cam_front,   "front"),   daemon=True).start()
threading.Thread(target=reader, args=(cam_gripper, "gripper"), daemon=True).start()

# ─────────────────────────────────────────────
# DETECTION THREAD FOR GRIPPER CAM
# Runs YOLO on the latest gripper frame in the
# background so it doesn't slow down streaming
# ─────────────────────────────────────────────
latest_annotated_gripper = None                  # stores the YOLO-annotated frame
annotated_lock = threading.Lock()                # protects it from race conditions

def detection_thread():
    global latest_annotated_gripper
    while True:
        # Grab latest gripper frame
        with frame_locks["gripper"]:
            frame = latest_frames["gripper"]

        if frame is None:
            time.sleep(0.01)
            continue

        # Run YOLO detection
        results = model(frame, conf=0.4, verbose=False)
        annotated = results[0].plot()  # draws boxes on the frame

        # Store annotated frame
        with annotated_lock:
            latest_annotated_gripper = annotated

# Start detection in background thread
threading.Thread(target=detection_thread, daemon=True).start()
print("✅ Detection thread started!")

# ─────────────────────────────────────────────
# HTML PAGE
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return send_file('index.html')

# ─────────────────────────────────────────────
# FRAME GENERATOR
# Encodes frames as JPEG and streams them
# For gripper it uses the YOLO annotated frame
# For front it uses the raw frame
# ─────────────────────────────────────────────
def gen(name):
    prev_time = time.time()
    fps = 0
    alpha = 0.1

    while True:
        # ── Pick the right frame source ──
        if name == "gripper_detection":
            # YOLO annotated gripper frame
            with annotated_lock:
                frame = latest_annotated_gripper
        else:
            # Raw frame for front and gripper
            with frame_locks[name]:
                frame = latest_frames[name]

        if frame is None:
            time.sleep(0.01)
            continue

        # ── Rotate if needed ──
        if rotations.get(name) is not None:
            frame = cv2.rotate(frame, rotations[name])

        # ── Resize ──
        frame = cv2.resize(frame, (680, 420))

        # ── Encode and stream ──
        _, buffer = cv2.imencode('.jpg', frame,
                                 [int(cv2.IMWRITE_JPEG_QUALITY), 40])

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() +
               b'\r\n')

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.route('/front')
def front_feed():
    return Response(gen("front"),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/gripper')
def gripper_feed():
    return Response(gen("gripper"),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/gripper_detection')
def gripper_detection_feed():
    return Response(gen("gripper_detection"),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, threaded=True)