# 🦀 ROV Dual Camera + AI Crab Detection

A Raspberry Pi-based ROV vision system with two independent camera feeds and real-time crab detection using YOLOv8.

---

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Hardware Setup](#hardware-setup)
- [OS & System Dependencies](#os--system-dependencies)
- [Camera Setup & udev Rules](#camera-setup--udev-rules)
- [Python Environment](#python-environment)
- [YOLOv8 Installation](#yolov8-installation)
- [Project Installation](#project-installation)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

| Component | Recommended |
|-----------|-------------|
| Hardware | Raspberry Pi 4 (4GB+ RAM) or Pi 5 |
| OS | Raspberry Pi OS (64-bit, Bookworm) |
| Python | 3.9 – 3.11 |
| Cameras | 2x USB cameras (e.g. Logitech C270 or similar) |
| Storage | 16GB+ microSD (Class 10 / A1) |

---

## Hardware Setup

Connect both USB cameras to the Raspberry Pi. To verify they are detected:

```bash
ls /dev/video*
# Expected output: /dev/video0  /dev/video2 (or similar)
```

You can also inspect camera details with:

```bash
v4l2-ctl --list-devices
```

---

## OS & System Dependencies

Update the system first:

```bash
sudo apt update && sudo apt upgrade -y
```

Install required system packages:

```bash
sudo apt install -y \
  python3-pip \
  python3-venv \
  python3-dev \
  libopencv-dev \
  v4l-utils \
  libv4l-dev \
  libatlas-base-dev \
  libhdf5-dev \
  libjpeg-dev \
  libpng-dev \
  libtiff-dev \
  ffmpeg \
  git \
  cmake
```

---

## Camera Setup & udev Rules

By default, camera device names (`/dev/video0`, `/dev/video2`, etc.) can change on reboot. udev rules lock each physical camera to a stable name.

### Create the udev rules file

```bash
sudo nano /etc/udev/rules.d/99-rov-cams.rules
```

### Example rules (replace with your camera serial numbers)

```udev
# Camera 1 — Forward feed
SUBSYSTEM=="video4linux", ATTRS{idVendor}=="046d", ATTRS{idProduct}=="0825", ATTRS{serial}=="YOUR_SERIAL_1", SYMLINK+="rov_cam_forward"

# Camera 2 — Downward feed
SUBSYSTEM=="video4linux", ATTRS{idVendor}=="046d", ATTRS{idProduct}=="0825", ATTRS{serial}=="YOUR_SERIAL_2", SYMLINK+="rov_cam_down"
```

> **Tip:** To find your camera's vendor ID, product ID, and serial, run:
> ```bash
> udevadm info --name=/dev/video0 --attribute-walk | grep -E "idVendor|idProduct|serial"
> ```

### Reload udev rules

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

After this, your cameras will always be available at `/dev/rov_cam_forward` and `/dev/rov_cam_down`.

---

## Python Environment

It is strongly recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Upgrade pip:

```bash
pip install --upgrade pip
```

---

## YOLOv8 Installation

Install the Ultralytics YOLOv8 package:

```bash
pip install ultralytics
```

Install OpenCV (headless version is lighter and better suited for Pi):

```bash
pip install opencv-python-headless
```

Install other dependencies:

```bash
pip install numpy torch torchvision
```

> ⚠️ **Note on PyTorch for Raspberry Pi:** The standard `torch` pip install may not work directly on ARM. If it fails, install the ARM-compatible wheel:
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
> ```
> Or follow the [official PyTorch ARM install guide](https://pytorch.org/get-started/locally/).

### Verify YOLOv8 is working

```bash
python3 -c "from ultralytics import YOLO; print('YOLOv8 OK')"
```

---

## Project Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Place your trained YOLOv8 model weights in the `models/` directory:

```
models/
└── crab_detect.pt
```

---

## Usage

### Run both camera feeds with crab detection

```bash
python3 main.py
```

### Run a single camera

```bash
python3 main.py --cam forward
python3 main.py --cam down
```

### Test cameras independently

```bash
# Test forward camera
python3 -c "import cv2; cap = cv2.VideoCapture('/dev/rov_cam_forward'); print('OK' if cap.isOpened() else 'FAIL')"

# Test downward camera
python3 -c "import cv2; cap = cv2.VideoCapture('/dev/rov_cam_down'); print('OK' if cap.isOpened() else 'FAIL')"
```

### Run a quick YOLOv8 inference test

```bash
python3 -c "
from ultralytics import YOLO
model = YOLO('models/crab_detect.pt')
results = model('/dev/rov_cam_down', stream=True)
for r in results:
    print(r.boxes)
"
```

---

## Troubleshooting

### Camera not detected
- Run `ls /dev/video*` to check if the device exists
- Try unplugging and replugging the camera
- Check USB power — use a powered USB hub if needed on Pi 4

### `/dev/rov_cam_forward` doesn't exist after reboot
- Confirm the udev rule serial numbers match your actual hardware
- Re-run `sudo udevadm trigger` and check `ls -la /dev/rov_cam*`

### YOLOv8 runs too slow on Pi
- Reduce input resolution in your script (e.g. 320x240 instead of 640x640)
- Use `model.export(format='ncnn')` to convert to a Pi-optimized format
- Consider running detection only every N frames

### `libGL.so.1` or OpenCV import error
```bash
sudo apt install -y libgl1 libglib2.0-0
```

### Permission denied on `/dev/video*`
```bash
sudo usermod -aG video $USER
# Then log out and back in
```

---

## Dependencies Summary

| Package | Install Command |
|---------|----------------|
| ultralytics (YOLOv8) | `pip install ultralytics` |
| OpenCV | `pip install opencv-python-headless` |
| NumPy | `pip install numpy` |
| PyTorch | `pip install torch torchvision` |
| v4l-utils | `sudo apt install v4l-utils` |
| ffmpeg | `sudo apt install ffmpeg` |

---

## License

MIT License — see `LICENSE` for details.
