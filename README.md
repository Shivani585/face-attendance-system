# 🎓 Face Recognition Attendance System

> **Final-Year Mini Project** — Real-time face recognition for automated attendance management.  
> Built with Python · OpenCV · face_recognition · Tkinter

---

## 📸 Screenshots

```
┌──────────────────────────────────────────────────────────────┐
│  ◉  FACE RECOGNITION ATTENDANCE SYSTEM    Monday, 03 May 2026│
├────────────────────────────────┬─────────────────────────────┤
│                                │  ┌──────┐ ┌──────┐ ┌──────┐│
│   [ LIVE WEBCAM FEED ]         │  │ 4    │ │ 3    │ │ACTIVE││
│                                │  │Users │ │Today │ │Status││
│   ┌─ Shivani [98%] ─┐          │  └──────┘ └──────┘ └──────┘│
│   │                 │          │  ┌──────────────────────────┤
│   │   (face box)    │          │  │ ATTENDANCE LOG           │
│   └─────────────────┘          │  ├──────────────────────────┤
│                                │  │ Shivani  2026-05-03 … ✔ │
│                                │  │ Arjun    2026-05-03 … ✔ │
├────────────────────────────────┴─────────────────────────────┤
│  ▶ Start  ■ Stop  ＋ Register  ↻ Refresh  ✕ Exit            │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1 — Prerequisites

| Requirement | Version |
|-------------|---------|
| Python      | 3.8 – 3.11 |
| pip         | latest  |
| Webcam      | any USB/built-in |
| OS          | Windows 10+ / Ubuntu 20.04+ / macOS 12+ |

> **Windows users**: Install `dlib` via pre-compiled wheel for speed:
> ```
> pip install https://github.com/jloh02/dlib/releases/download/v19.22/dlib-19.22.99-cp310-cp310-win_amd64.whl
> ```

### 2 — Clone & Install

```bash
git clone https://github.com/your-username/face_attendance_system.git
cd face_attendance_system

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

> ⚠️ `dlib` requires **CMake** and a C++ compiler.  
> macOS: `brew install cmake`  
> Ubuntu: `sudo apt install cmake build-essential`

### 3 — Register Known Faces

**Option A — GUI (recommended)**  
Launch the app and click **＋ Register User** — the webcam snaps your face live.

**Option B — Batch from images**  
```bash
# Place photos named "FirstName_Lastname.jpg" in data/dataset/
python scripts/register_faces.py

# Or specify any directory:
python scripts/register_faces.py --from-dir /path/to/photos
```

**Option C — Interactive CLI**  
```bash
python scripts/register_faces.py --interactive
```

### 4 — Run the Application

```bash
python main.py
```

---

## 🏗️ Architecture

```
face_attendance_system/
│
├── main.py                    ← Entry point
├── requirements.txt
├── README.md
│
├── app/
│   ├── ui/
│   │   ├── main_ui.py         ← Tkinter dashboard (Presentation Layer)
│   │   └── styles.py          ← Dark-theme colour/font constants
│   │
│   ├── core/
│   │   ├── face_detector.py   ← Face detection + bounding box drawing
│   │   ├── face_encoder.py    ← 128-d embedding generation & storage
│   │   └── recognizer.py      ← Euclidean-distance matching
│   │
│   ├── services/
│   │   ├── attendance_service.py ← Daily-once marking + cooldown
│   │   └── camera_service.py    ← Threaded webcam capture
│   │
│   └── utils/
│       ├── config.py          ← All tunable constants
│       └── file_handler.py    ← Pickle / CSV / JSON / logging I/O
│
├── data/
│   ├── dataset/               ← Source images for batch registration
│   ├── encodings/             ← face_encodings.pkl + user_metadata.json
│   └── attendance/            ← attendance.csv
│
├── scripts/
│   ├── register_faces.py      ← Batch / interactive registration CLI
│   └── view_attendance.py     ← CLI attendance report viewer
│
└── logs/
    └── system.log             ← Rotating application log
```

### Layer Responsibilities

| Layer | Module(s) | Responsibility |
|-------|-----------|---------------|
| **Presentation** | `ui/main_ui.py`, `ui/styles.py` | Dashboard, live feed, user interaction |
| **Application** | `services/attendance_service.py`, `services/camera_service.py` | Business rules, camera management |
| **Processing** | `core/face_detector.py`, `core/face_encoder.py`, `core/recognizer.py` | CV pipeline: detect → encode → match |
| **Data** | `utils/file_handler.py`, `utils/config.py` | Persistence, config, logging |

---

## ⚙️ Configuration (`app/utils/config.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CAMERA_INDEX` | `0` | Webcam index (`0` = built-in, `1` = external) |
| `TOLERANCE` | `0.50` | Match threshold (lower = stricter) |
| `MODEL` | `"hog"` | Detection model: `"hog"` (fast) or `"cnn"` (accurate, needs GPU) |
| `PROCESS_EVERY_N` | `2` | Skip frames for performance |
| `FRAME_SCALE` | `0.5` | Downscale factor before detection |

---

## 📊 CSV Attendance Format

```csv
Name,Date,Time,Status
Shivani,2026-05-03,10:32:11,Present
Arjun,2026-05-03,10:45:22,Present
```

View reports via CLI:
```bash
python scripts/view_attendance.py            # Today
python scripts/view_attendance.py --all      # All time
python scripts/view_attendance.py --summary  # Per-person count
python scripts/view_attendance.py --date 2026-05-01
```

---

## 🔬 Technical Concepts (Viva Preparation)

### Face Detection vs Face Recognition

| | Detection | Recognition |
|-|-----------|-------------|
| **What** | Finds WHERE faces are | Finds WHO the face belongs to |
| **Output** | Bounding box coordinates | Identity (name) + confidence |
| **Method** | HOG + SVM / CNN | 128-d embedding comparison |

### The 128-Dimensional Embedding

`face_recognition` uses a **deep ResNet** (trained on 3M+ faces) to project each face into a 128-dimensional vector. Points close in this space belong to the same person.

```
Raw image  →  ResNet  →  [0.31, -0.12, 0.87, ..., 0.05]  (128 floats)
                                         ↕  Euclidean distance
Database   →  ResNet  →  [0.29, -0.14, 0.84, ..., 0.07]
                                     distance ≈ 0.18  →  MATCH ✔
```

### Matching Logic

```python
distance = sqrt( Σ (e1_i - e2_i)² )   # for i in 0..127

if distance <= TOLERANCE (0.50):
    confidence = 1 - (distance / TOLERANCE)   # 0 → 1
    return name, confidence
else:
    return "Unknown", 0.0
```

### Why HOG over CNN by default?

- **HOG (Histogram of Oriented Gradients)** runs on CPU — no GPU needed, ~20 FPS on modern hardware.  
- **CNN** is more accurate in challenging lighting/angles but requires a CUDA GPU for real-time speed.  
- Switchable via `MODEL = "cnn"` in `config.py`.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `dlib` install fails | Use pre-compiled wheel (see Quick Start) |
| Camera not opening | Change `CAMERA_INDEX` in config |
| No face detected | Ensure good lighting; `UPSAMPLE_TIMES = 2` for small faces |
| False positives | Lower `TOLERANCE` to `0.40` |
| Slow performance | Increase `PROCESS_EVERY_N` to `4` |

---

## 📄 License

MIT — free for academic and personal use.

---

*Built as a Final-Year Mini Project demonstrating real-time computer vision, modular Python architecture, and GUI development.*
