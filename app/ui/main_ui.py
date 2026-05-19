"""
main_ui.py — Presentation Layer: Main Tkinter Dashboard

Architecture:
  ┌──────────────────────────────────────────────────────┐
  │  FaceAttendanceApp (root window)                     │
  │  ├── Header bar                                      │
  │  ├── Left panel  — live camera feed (Label canvas)  │
  │  └── Right panel                                     │
  │       ├── Stats row  (users / today's count)        │
  │       ├── Attendance log  (Treeview)                │
  │       └── Controls  (Start / Stop / Register / Exit)│
  └──────────────────────────────────────────────────────┘
"""

import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from typing import Optional

import cv2
from PIL import Image, ImageTk     # Pillow — needed for camera→Tkinter conversion

from app.core.face_detector import FaceDetector
from app.core.face_encoder  import FaceEncoder
from app.core.recognizer    import FaceRecognizer
from app.services.attendance_service import AttendanceService
from app.services.camera_service     import CameraService
from app.ui.styles import (
    PALETTE, FONTS,
    styled_button, section_label, info_label, configure_treeview_style,
)
from app.utils.config import (
    UI_TITLE, PROCESS_EVERY_N,
    COLOR_KNOWN, COLOR_UNKNOWN,
)
from app.utils.file_handler import setup_logger

logger = setup_logger()


# ─── Sound Helpers ─────────────────────────────────────────────────────────────

def _beep() -> None:
    """Non-blocking system beep (fallback if playsound not installed)."""
    import sys
    try:
        if sys.platform == "win32":
            import winsound
            threading.Thread(
                target=lambda: winsound.Beep(1000, 150), daemon=True
            ).start()
        else:
            print("\a", end="", flush=True)
    except Exception:
        pass


# ─── Main Application Class ────────────────────────────────────────────────────

class FaceAttendanceApp:
    """Root Tkinter application — orchestrates all layers."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(UI_TITLE)
        self.root.configure(bg=PALETTE["bg_base"])
        self.root.resizable(True, True)
        self.root.geometry("1200x720")
        self.root.minsize(900, 600)

        configure_treeview_style()

        # ── Layer instances ────────────────────────────────────────────────────
        self.camera_svc    = CameraService()
        self.detector      = FaceDetector()
        self.encoder       = FaceEncoder()
        self.recognizer    = FaceRecognizer()
        self.attendance    = AttendanceService()

        # ── State ──────────────────────────────────────────────────────────────
        self._running       = False
        self._frame_count   = 0
        self._process_thread: Optional[threading.Thread] = None
        self._last_results  = []   # list of (name, conf) from latest recognition
        self._photo_ref     = None # keep Tkinter image reference alive

        # ── Build UI ──────────────────────────────────────────────────────────
        self._build_ui()
        self._refresh_log()

        # ── Window close handler ───────────────────────────────────────────────
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)

        logger.info("FaceAttendanceApp initialised.")

    # ══════════════════════════════════════════════════════════════════════════
    # UI Construction
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        self._build_header()
        content = tk.Frame(self.root, bg=PALETTE["bg_base"])
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        self._build_camera_panel(content)
        self._build_right_panel(content)
        self._build_statusbar()

    def _build_header(self) -> None:
        hdr = tk.Frame(self.root, bg=PALETTE["bg_surface"], height=56)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        # Logo + title
        tk.Label(
            hdr,
            text="◉  FACE RECOGNITION ATTENDANCE SYSTEM",
            font=FONTS["title"],
            fg=PALETTE["accent"],
            bg=PALETTE["bg_surface"],
        ).pack(side=tk.LEFT, padx=20, pady=12)

        # Live clock
        self._clock_var = tk.StringVar()
        tk.Label(
            hdr,
            textvariable=self._clock_var,
            font=FONTS["subtitle"],
            fg=PALETTE["text_secondary"],
            bg=PALETTE["bg_surface"],
        ).pack(side=tk.RIGHT, padx=20)
        self._tick_clock()

        # Thin accent line below header
        tk.Frame(self.root, bg=PALETTE["accent"], height=2).pack(fill=tk.X)

    def _build_camera_panel(self, parent) -> None:
        cam_frame = tk.Frame(parent, bg=PALETTE["bg_surface"], bd=0)
        cam_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=6)

        section_label(cam_frame, "Live Feed").pack(anchor="w", padx=12, pady=(10, 4))

        # Camera canvas
        self._cam_label = tk.Label(
            cam_frame,
            bg="#000000",
            text="[ Camera Offline ]",
            font=FONTS["mono"],
            fg=PALETTE["text_muted"],
        )
        self._cam_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def _build_right_panel(self, parent) -> None:
        right = tk.Frame(parent, bg=PALETTE["bg_base"])
        right.grid(row=0, column=1, sticky="nsew", pady=6)
        right.rowconfigure(1, weight=1)

        # ── Stats row ──────────────────────────────────────────────────────────
        stats = tk.Frame(right, bg=PALETTE["bg_surface"])
        stats.pack(fill=tk.X, pady=(0, 6))

        self._stat_users  = self._stat_card(stats, "Registered Users", str(self.encoder.user_count))
        self._stat_today  = self._stat_card(stats, "Present Today",    str(len(self.attendance.get_todays_records())))
        self._stat_status = self._stat_card(stats, "System Status",    "IDLE", PALETTE["text_muted"])

        # ── Attendance log ─────────────────────────────────────────────────────
        log_frame = tk.Frame(right, bg=PALETTE["bg_surface"])
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        section_label(log_frame, "Attendance Log").pack(anchor="w", padx=12, pady=(10, 4))

        cols = ("Name", "Date", "Time", "Status")
        self._tree = ttk.Treeview(log_frame, columns=cols, show="headings", selectmode="browse")
        widths = {"Name": 140, "Date": 100, "Time": 90, "Status": 80}
        for col in cols:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=widths[col], anchor="center")

        sb = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0), pady=(0, 10))
        sb.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10), padx=(0, 8))

        # ── Control buttons ────────────────────────────────────────────────────
        ctrl = tk.Frame(right, bg=PALETTE["bg_base"])
        ctrl.pack(fill=tk.X)

        self._btn_start = styled_button(ctrl, "▶  Start Camera",  self._start_camera,  "primary")
        self._btn_stop  = styled_button(ctrl, "■  Stop Camera",   self._stop_camera,   "danger")
        btn_register    = styled_button(ctrl, "＋  Register User", self._open_register, "ghost")
        btn_refresh     = styled_button(ctrl, "↻  Refresh Log",   self._refresh_log,   "ghost")
        btn_exit        = styled_button(ctrl, "✕  Exit",          self._on_exit,        "warning")

        for w in (self._btn_start, self._btn_stop, btn_register, btn_refresh, btn_exit):
            w.pack(side=tk.LEFT, padx=4, pady=4)

        self._btn_stop.config(state=tk.DISABLED)

    def _build_statusbar(self) -> None:
        bar = tk.Frame(self.root, bg=PALETTE["bg_elevated"], height=28)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        self._status_var = tk.StringVar(value="System ready.")
        tk.Label(
            bar,
            textvariable=self._status_var,
            font=FONTS["small"],
            fg=PALETTE["text_secondary"],
            bg=PALETTE["bg_elevated"],
        ).pack(side=tk.LEFT, padx=12, pady=4)

        self._fps_var = tk.StringVar(value="")
        tk.Label(
            bar,
            textvariable=self._fps_var,
            font=FONTS["small"],
            fg=PALETTE["text_muted"],
            bg=PALETTE["bg_elevated"],
        ).pack(side=tk.RIGHT, padx=12)

    # ── Stat Card Helper ───────────────────────────────────────────────────────

    def _stat_card(self, parent, title: str, value: str, val_color=None) -> tk.StringVar:
        card = tk.Frame(parent, bg=PALETTE["bg_elevated"], padx=14, pady=10)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=8)

        tk.Label(card, text=title, font=FONTS["small"], fg=PALETTE["text_secondary"], bg=PALETTE["bg_elevated"]).pack(anchor="w")
        var = tk.StringVar(value=value)
        tk.Label(card, textvariable=var, font=FONTS["title"], fg=val_color or PALETTE["accent"], bg=PALETTE["bg_elevated"]).pack(anchor="w")
        return var

    # ══════════════════════════════════════════════════════════════════════════
    # Camera & Recognition Loop
    # ══════════════════════════════════════════════════════════════════════════

    def _start_camera(self) -> None:
        if self._running:
            return
        if not self.camera_svc.start():
            messagebox.showerror("Camera Error", "Could not open webcam.\nCheck camera index in config.py.")
            return
        self._running = True
        self._frame_count = 0
        self._btn_start.config(state=tk.DISABLED)
        self._btn_stop.config(state=tk.NORMAL)
        self._set_status("Camera active — recognising faces…", PALETTE["success"])
        self._stat_status.set("ACTIVE")

        # Start background recognition thread
        self._process_thread = threading.Thread(target=self._recognition_loop, daemon=True)
        self._process_thread.start()

        # Start UI update loop
        self._update_camera_ui()

    def _stop_camera(self) -> None:
        self._running = False
        self.camera_svc.stop()
        self._btn_start.config(state=tk.NORMAL)
        self._btn_stop.config(state=tk.DISABLED)
        self._set_status("Camera stopped.", PALETTE["text_muted"])
        self._stat_status.set("IDLE")
        self._cam_label.config(image="", text="[ Camera Offline ]")

    def _recognition_loop(self) -> None:
        """
        Background thread:
          - Grabs latest frame from CameraService
          - Runs detection + encoding + recognition every N frames
          - Calls attendance marking
          - Stores results for the UI thread to consume
        """
        frame_idx  = 0
        fps_start  = time.time()
        fps_frames = 0

        while self._running:
            frame = self.camera_svc.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            frame_idx  += 1
            fps_frames += 1

            # FPS calculation
            elapsed = time.time() - fps_start
            if elapsed >= 1.0:
                fps = fps_frames / elapsed
                self.root.after(0, self._fps_var.set, f"FPS: {fps:.1f}")
                fps_start  = time.time()
                fps_frames = 0

            # Only run heavy recognition every N frames
            if frame_idx % PROCESS_EVERY_N != 0:
                continue

            # Detection
            small_rgb, orig_locs, small_locs = self.detector.detect(frame)

            if not small_locs:
                self._last_results = []
                continue

            # Encoding
            live_encs = self.encoder.encode_faces(small_rgb, small_locs)

            # Recognition
            results = self.recognizer.identify(
                live_encs,
                self.encoder.known_encodings,
                self.encoder.known_names,
            )

            self._last_results = list(zip(orig_locs, results))

            # Attendance + notifications
            for _, (name, conf) in self._last_results:
                status = self.attendance.try_mark(name)
                if status == "marked":
                    _beep()
                    self.root.after(0, self._on_attendance_marked, name)

    def _update_camera_ui(self) -> None:
        """UI-thread loop: overlays results on frame → displays in Label."""
        if not self._running:
            return

        frame = self.camera_svc.get_frame()
        if frame is not None:
            locs   = [r[0] for r in self._last_results]
            names  = [r[1][0] for r in self._last_results]
            confs  = [r[1][1] for r in self._last_results]

            annotated = FaceDetector.draw_boxes(frame, locs, names, confs,
                                                COLOR_KNOWN, COLOR_UNKNOWN)

            # Resize to fit the label widget's current size
            w = self._cam_label.winfo_width()  or 640
            h = self._cam_label.winfo_height() or 480
            display = cv2.resize(annotated, (w, h))
            rgb_img  = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            pil_img  = Image.fromarray(rgb_img)
            tk_img   = ImageTk.PhotoImage(pil_img)

            self._cam_label.config(image=tk_img, text="")
            self._photo_ref = tk_img  # prevent GC

        self.root.after(30, self._update_camera_ui)  # ~33 fps UI refresh

    # ══════════════════════════════════════════════════════════════════════════
    # Attendance Events
    # ══════════════════════════════════════════════════════════════════════════

    def _on_attendance_marked(self, name: str) -> None:
        """Called on the UI thread when a new attendance is recorded."""
        self._refresh_log()
        self._stat_today.set(str(len(self.attendance.get_todays_records())))
        self._set_status(f"✔  Attendance marked for {name}", PALETTE["success"])
        # Flash the status green briefly
        self.root.after(3000, lambda: self._set_status("Camera active — recognising faces…", PALETTE["success"]))

    def _refresh_log(self) -> None:
        """Reload today's attendance into the Treeview."""
        for row in self._tree.get_children():
            self._tree.delete(row)
        records = self.attendance.get_todays_records()
        for i, r in enumerate(reversed(records)):
            tag = "even" if i % 2 == 0 else "odd"
            self._tree.insert("", tk.END, values=(r["Name"], r["Date"], r["Time"], r["Status"]), tags=(tag,))
        self._tree.tag_configure("even", background=PALETTE["bg_elevated"])
        self._tree.tag_configure("odd",  background=PALETTE["bg_surface"])

    # ══════════════════════════════════════════════════════════════════════════
    # User Registration
    # ══════════════════════════════════════════════════════════════════════════

    def _open_register(self) -> None:
        """Open the in-app face registration dialog."""
        RegisterDialog(self.root, self.encoder, self.camera_svc, self._on_register_done)

    def _on_register_done(self) -> None:
        self._stat_users.set(str(self.encoder.user_count))
        self._set_status("New user registered successfully.", PALETTE["info"])

    # ══════════════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _set_status(self, msg: str, color: str = None) -> None:
        self._status_var.set(f"  {msg}")

    def _tick_clock(self) -> None:
        self._clock_var.set(datetime.now().strftime("%A, %d %b %Y  —  %H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    def _on_exit(self) -> None:
        if self._running:
            self._stop_camera()
        self.root.destroy()


# ─── Registration Dialog ───────────────────────────────────────────────────────

class RegisterDialog(tk.Toplevel):
    """
    Modal window that captures a webcam snapshot and registers a new user.
    """

    def __init__(self, parent, encoder: FaceEncoder, camera_svc: CameraService, on_done):
        super().__init__(parent)
        self.title("Register New User")
        self.configure(bg=PALETTE["bg_base"])
        self.geometry("560x500")
        self.resizable(False, False)
        self.grab_set()           # modal

        self._encoder    = encoder
        self._camera_svc = camera_svc
        self._on_done    = on_done
        self._snapshot   = None
        self._own_camera = not camera_svc.is_running
        self._photo_ref  = None

        self._build()

        if self._own_camera:
            self._camera_svc.start()

        self._update_preview()

    def _build(self) -> None:
        tk.Label(self, text="REGISTER NEW USER", font=FONTS["title"],
                 fg=PALETTE["accent"], bg=PALETTE["bg_base"]).pack(pady=(16, 4))

        # Preview
        self._preview = tk.Label(self, bg="#000", width=320, height=240,
                                 text="Loading camera…", font=FONTS["mono"],
                                 fg=PALETTE["text_muted"])
        self._preview.pack(padx=20, pady=8)

        # Name entry
        row = tk.Frame(self, bg=PALETTE["bg_base"])
        row.pack(pady=4)
        tk.Label(row, text="Full Name:", font=FONTS["body"],
                 fg=PALETTE["text_primary"], bg=PALETTE["bg_base"]).pack(side=tk.LEFT, padx=8)
        self._name_var = tk.StringVar()
        entry = tk.Entry(row, textvariable=self._name_var, font=FONTS["body"],
                         bg=PALETTE["bg_elevated"], fg=PALETTE["text_primary"],
                         insertbackground=PALETTE["accent"], relief=tk.FLAT,
                         width=24, bd=4)
        entry.pack(side=tk.LEFT)
        entry.focus_set()

        # Buttons
        btn_row = tk.Frame(self, bg=PALETTE["bg_base"])
        btn_row.pack(pady=12)
        styled_button(btn_row, "📷  Capture & Register", self._capture_register, "primary").pack(side=tk.LEFT, padx=6)
        styled_button(btn_row, "Cancel", self._close, "ghost").pack(side=tk.LEFT, padx=6)

        self._msg_var = tk.StringVar()
        tk.Label(self, textvariable=self._msg_var, font=FONTS["body"],
                 fg=PALETTE["success"], bg=PALETTE["bg_base"]).pack(pady=4)

    def _update_preview(self) -> None:
        if not self.winfo_exists():
            return
        frame = self._camera_svc.get_frame()
        if frame is not None:
            rgb = cv2.cvtColor(cv2.resize(frame, (320, 240)), cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(rgb))
            self._preview.config(image=img, text="")
            self._photo_ref = img
        self.after(40, self._update_preview)

    def _capture_register(self) -> None:
        name = self._name_var.get().strip()
        if not name:
            self._msg_var.set("⚠  Please enter a name.")
            return
        frame = self._camera_svc.get_frame()
        if frame is None:
            self._msg_var.set("⚠  No camera frame available.")
            return
        ok = self._encoder.register_from_webcam(name, frame)
        if ok:
            self._msg_var.set(f"✔  {name} registered successfully!")
            self._on_done()
            self.after(1500, self._close)
        else:
            self._msg_var.set("✘  No face detected. Try again.")

    def _close(self) -> None:
        if self._own_camera:
            self._camera_svc.stop()
        self.grab_release()
        self.destroy()
