"""
styles.py — Presentation Layer: Centralised Tkinter Styling

All colours, fonts, and widget factory functions live here.
The UI imports from this module — nothing is hard-coded in main_ui.py.
"""

import tkinter as tk
from tkinter import ttk

# ─── Colour Palette ────────────────────────────────────────────────────────────
PALETTE = {
    # Background hierarchy
    "bg_base":     "#0D1117",   # Deepest — window background
    "bg_surface":  "#161B22",   # Card / panel background
    "bg_elevated": "#21262D",   # Input, header rows
    "bg_hover":    "#30363D",

    # Accent
    "accent":      "#00FF88",   # Neon green — primary CTA, active indicator
    "accent_dim":  "#00CC6A",
    "accent_glow": "#00FF8833", # Semi-transparent for glow effects

    # Semantic
    "success":     "#3FB950",
    "warning":     "#D29922",
    "danger":      "#F85149",
    "info":        "#58A6FF",

    # Text
    "text_primary": "#E6EDF3",
    "text_secondary": "#8B949E",
    "text_muted":   "#484F58",

    # Borders
    "border":      "#30363D",
    "border_focus":"#58A6FF",
}

# ─── Font Map ──────────────────────────────────────────────────────────────────
FONTS = {
    "title":    ("Consolas", 20, "bold"),
    "subtitle": ("Consolas", 12),
    "body":     ("Segoe UI",  11),
    "body_bold":("Segoe UI",  11, "bold"),
    "small":    ("Segoe UI",   9),
    "mono":     ("Courier New",10),
    "tag":      ("Consolas",  10, "bold"),
}


# ─── Widget Factories ──────────────────────────────────────────────────────────

def styled_button(
    parent,
    text: str,
    command=None,
    variant: str = "primary",   # "primary" | "danger" | "ghost"
    **kwargs,
) -> tk.Button:
    """Return a styled flat button."""
    color_map = {
        "primary": (PALETTE["accent"],     PALETTE["bg_base"]),
        "danger":  (PALETTE["danger"],     PALETTE["text_primary"]),
        "ghost":   (PALETTE["bg_elevated"],PALETTE["text_primary"]),
        "warning": (PALETTE["warning"],    PALETTE["bg_base"]),
    }
    bg, fg = color_map.get(variant, color_map["primary"])

    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        font=FONTS["body_bold"],
        relief=tk.FLAT,
        cursor="hand2",
        padx=16,
        pady=8,
        activebackground=PALETTE["accent_dim"],
        activeforeground=PALETTE["bg_base"],
        bd=0,
        **kwargs,
    )
    return btn


def section_label(parent, text: str) -> tk.Label:
    """Small all-caps section header."""
    return tk.Label(
        parent,
        text=text.upper(),
        font=FONTS["tag"],
        fg=PALETTE["accent"],
        bg=PALETTE["bg_surface"],
    )


def info_label(parent, text: str = "") -> tk.Label:
    return tk.Label(
        parent,
        text=text,
        font=FONTS["body"],
        fg=PALETTE["text_secondary"],
        bg=PALETTE["bg_surface"],
    )


def status_badge(parent, text: str, color_key: str = "success") -> tk.Label:
    """Pill-shaped status indicator."""
    return tk.Label(
        parent,
        text=f"  {text}  ",
        font=FONTS["small"],
        fg=PALETTE["bg_base"],
        bg=PALETTE[color_key],
        padx=6,
        pady=2,
    )


def configure_treeview_style() -> None:
    """Apply dark-theme style to all ttk.Treeview widgets."""
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background=PALETTE["bg_elevated"],
        foreground=PALETTE["text_primary"],
        fieldbackground=PALETTE["bg_elevated"],
        rowheight=26,
        font=FONTS["mono"],
    )
    style.configure(
        "Treeview.Heading",
        background=PALETTE["bg_surface"],
        foreground=PALETTE["accent"],
        font=FONTS["body_bold"],
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", PALETTE["accent_glow"])],
        foreground=[("selected", PALETTE["accent"])],
    )
