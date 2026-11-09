"""Tk desktop UI. Serial traffic stays in one worker; Tk stays on the main thread."""
import math
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .capture import Capture, demo_capture
from .device import Device, list_ports
from .protocol import Config, RATES, Trigger

BG = "#101720"
PANEL = "#18232f"
GRID = "#293747"
TEXT = "#dbe7f3"
MUTED = "#8fa4b9"
COLORS = ("#54dbb5", "#75baff", "#f6c66d", "#c69bfa",
          "#f48e9c", "#7cdbec", "#d3e781", "#ffad73")


def time_label(seconds):
    if abs(seconds) < 0.001:
        return f"{seconds * 1e6:.2f} µs"
    if abs(seconds) < 1:
        return f"{seconds * 1e3:.2f} ms"
    return f"{seconds:.3f} s"


class Waveform(ttk.Frame):
    def __init__(self, parent, on_cursor):
        super().__init__(parent)
        self.capture = None
        self.start = 0.0
        self.span = 1.0
        self.cursor_a = self.cursor_b = None
        self.on_cursor = on_cursor
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, height=500)
        self.canvas.pack(fill="both", expand=True)
        self.scroll = ttk.Scrollbar(self, orient="horizontal", command=self.pan)
        self.scroll.pack(fill="x")
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Shift-Button-1>", lambda e: self.click(e, second=True))
        self.canvas.bind("<MouseWheel>", lambda e: self.zoom(0.5 if e.delta > 0 else 2, e.x))
        self.canvas.bind("<Button-4>", lambda e: self.zoom(0.5, e.x))
        self.canvas.bind("<Button-5>", lambda e: self.zoom(2, e.x))

    def set_capture(self, capture):
        self.capture = capture
        self.cursor_a = self.cursor_b = None
        self.fit()
        self.on_cursor("Click for cursor A · Shift-click for B · Scroll to zoom")

    def fit(self):
        self.start = 0
        self.span = len(self.capture.samples) if self.capture else 1
        self.draw()

    def zoom(self, factor, x=None):
        if not self.capture:
            return
        width = max(1, self.canvas.winfo_width() - 96)
        fraction = 0.5 if x is None else max(0, min(1, (x - 80) / width))
        anchor = self.start + fraction * self.span
        self.span = min(len(self.capture.samples), max(8, self.span * factor))
        self.start = max(0, min(len(self.capture.samples) - self.span, anchor - fraction * self.span))
        self.draw()

    def pan(self, action, value, units=None):
        if not self.capture:
            return
        count = len(self.capture.samples)
        if action == "moveto":
            self.start = float(value) * count
        else:
            self.start += int(value) * self.span * (0.9 if units == "pages" else 0.1)
        self.start = max(0, min(count - self.span, self.start))
        self.draw()

    def click(self, event, second=False):
        if not self.capture or event.x < 80:
            return
        width = max(1, self.canvas.winfo_width() - 96)
        sample = int(round(self.start + (event.x - 80) * self.span / width))
        sample = max(0, min(len(self.capture.samples) - 1, sample))
        if second:
            self.cursor_b = sample
        else:
            self.cursor_a = sample
        parts = []
        for label, index in (("A", self.cursor_a), ("B", self.cursor_b)):
            if index is not None:
                parts.append(f"{label}: {time_label(index / self.capture.rate)} · sample {index} · 0x{self.capture.samples[index]:02X}")
        if self.cursor_a is not None and self.cursor_b is not None:
            delta = abs(self.cursor_b - self.cursor_a) / self.capture.rate
            parts.append(f"Δt {time_label(delta)}" + (f" · 1/Δt {1 / delta:.1f} Hz" if delta else ""))
        self.on_cursor("    |    ".join(parts))
        self.draw()

    def draw(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        left, width = 80, max(1, w - 96)
        if not self.capture:
            c.create_text(w / 2, h / 2, text="Connect your analyser or choose Demo signals",
                          fill=MUTED, font=("TkDefaultFont", 14))
            self.scroll.set(0, 1)
            return
        cap = self.capture
        n = len(cap.samples)
        lane = max(24, (h - 52) / 8)
        for tick in range(11):
            x = left + width * tick / 10
            sample = self.start + self.span * tick / 10
            c.create_line(x, 36, x, h, fill=GRID)
            c.create_text(x, 17, text=time_label(sample / cap.rate), fill=MUTED,
                          font=("TkDefaultFont", 9))
        end = min(n, int(math.ceil(self.start + self.span)))
        begin = max(0, int(self.start))
        for ch, color in enumerate(COLORS):
            top = 45 + lane * ch
            high, low = top + lane * 0.12, top + lane * 0.70
            c.create_text(15, (high + low) / 2, anchor="w", text=f"CH{ch}", fill=color,
                          font=("TkDefaultFont", 11, "bold"))
            c.create_line(0, top + lane - 4, w, top + lane - 4, fill=PANEL)
            bit = 1 << ch
            if self.span <= width * 2:
                points = []
                previous_y = None
                for index in range(begin, end):
                    x = max(left, left + (index - self.start) * width / self.span)
                    y = high if cap.samples[index] & bit else low
                    if previous_y is not None:
                        points.extend((x, previous_y))
                    points.extend((x, y))
                    previous_y = y
                if points:
                    points.extend((min(w - 16, left + (end - self.start) * width / self.span), previous_y))
                    c.create_line(*points, fill=color, width=2)
            else:
                # Draw min/max occupancy per screen pixel. A narrow pulse must
                # remain visible when thousands of samples share one pixel.
                for pixel in range(int(width)):
                    a = max(0, int(self.start + pixel * self.span / width))
                    b = min(n, max(a + 1, int(self.start + (pixel + 1) * self.span / width)))
                    seen_high = seen_low = False
                    for index in range(a, b):
                        if cap.samples[index] & bit:
                            seen_high = True
                        else:
                            seen_low = True
                        if seen_high and seen_low:
                            break
                    y1 = high if seen_high else low
                    y2 = low if seen_low else high
                    c.create_line(left + pixel, y1, left + pixel + 1, y2, fill=color)
        if cap.trigger_index >= 0:
            self.marker(cap.trigger_index, "T", "#ffffff")
        for label, index in (("A", self.cursor_a), ("B", self.cursor_b)):
            if index is not None:
                self.marker(index, label, "#f9df87")
        self.scroll.set(self.start / n, min(1, (self.start + self.span) / n))

    def marker(self, index, label, color):
        c = self.canvas
        x = 80 + (index - self.start) * max(1, c.winfo_width() - 96) / self.span
        if 80 <= x <= c.winfo_width() - 16:
            c.create_line(x, 35, x, c.winfo_height(), fill=color, dash=(4, 3))
            c.create_text(x + 5, 32, text=label, anchor="w", fill=color)


class App:
    def __init__(self, root, demo=False, port=None, config=Config()):
        self.root = root
        self.device = None
        self.capture = None
        self.busy = False
        self.closing = False
        self.results = queue.Queue()
        root.title("LogicScope S3")
        root.geometry("1200x720")
        root.minsize(920, 600)
        root.configure(bg=BG)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", background=PANEL, foreground=TEXT, fieldbackground=BG)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, padding=2)
        style.configure("TButton", padding=(10, 7))
        style.configure("TCombobox", fieldbackground=PANEL, background=PANEL, foreground=TEXT,
                        arrowcolor=TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", TEXT)])
        style.map("TButton", background=[("active", GRID), ("disabled", PANEL)],
                  foreground=[("disabled", MUTED)])
        self.port = tk.StringVar(value=port or "")
        self.rate = tk.StringVar(value=str(config.rate))
        self.count = tk.StringVar(value=str(config.count))
        self.trigger = tk.StringVar(value=Trigger(config.trigger).name.lower())
        self.channel = tk.StringVar(value="CH0")
        self.mask = tk.StringVar(value="0xFF")
        self.pattern = tk.StringVar(value="0x00")
        self.status = tk.StringVar(value="Ready · hardware capture requires flashed LS-S3-A0")
        self.summary = tk.StringVar(value="No capture")
        self.cursor = tk.StringVar(value="Click for cursor A · Shift-click for B · Scroll to zoom")
        self.controls = []
        outer = ttk.Frame(root, padding=18)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 14))
        ttk.Label(header, text="LogicScope", font=("TkDefaultFont", 22, "bold")).pack(side="left")
        ttk.Label(header, text="S3  /  8-channel digital capture", foreground=MUTED).pack(side="left", padx=16)
        ttk.Label(header, text="PROTOTYPE · rates unmeasured", foreground="#f6c66d").pack(side="right")
        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        side_container = ttk.Frame(body)
        side_container.pack(side="left", fill="y", padx=(0, 18))
        side_canvas = tk.Canvas(side_container, width=240, bg=BG, highlightthickness=0)
        side_canvas.pack(side="left", fill="both", expand=True)
        side_scroll = ttk.Scrollbar(side_container, orient="vertical", command=side_canvas.yview)
        side_scroll.pack(side="right", fill="y")
        side_canvas.configure(yscrollcommand=side_scroll.set)
        side = ttk.Frame(side_canvas, padding=(0, 0, 8, 0))
        side_window = side_canvas.create_window(0, 0, window=side, anchor="nw")
        side.bind("<Configure>", lambda e: side_canvas.configure(scrollregion=side_canvas.bbox("all")))
        side_canvas.bind("<Configure>", lambda e: side_canvas.itemconfigure(side_window, width=e.width))
        self.label(side, "DEVICE")
        self.port_box = ttk.Combobox(side, textvariable=self.port, width=24)
        self.port_box.pack(fill="x", pady=(6, 8))
        self.controls.append((self.port_box, "normal"))
        row = ttk.Frame(side); row.pack(fill="x")
        self.button(row, "Refresh", self.refresh).pack(side="left")
        self.connect_button = self.button(row, "Connect", self.connect)
        self.connect_button.pack(side="left", padx=(8, 0))
        self.button(side, "Demo signals", self.demo).pack(fill="x", pady=(10, 20))
        self.label(side, "CAPTURE")
        self.capture_button = self.button(side, "Capture once", self.acquire)
        self.capture_button.pack(fill="x", pady=(8, 4))
        self.combo(side, "Sample rate (S/s)", self.rate, [str(x) for x in RATES])
        self.combo(side, "Samples", self.count, ["1024", "4096", "16384", "32768", "65536"], editable=True)
        self.label(side, "TRIGGER SEARCH", pady=(18, 3))
        self.combo(side, "Find within this capture", self.trigger, [x.name.lower() for x in Trigger])
        self.combo(side, "Edge / level channel", self.channel, [f"CH{i}" for i in range(8)])
        for label, variable in (("Pattern mask (hex)", self.mask), ("Pattern value (hex)", self.pattern)):
            ttk.Label(side, text=label, foreground=MUTED).pack(anchor="w", pady=(7, 2))
            entry = ttk.Entry(side, textvariable=variable, width=20)
            entry.pack(fill="x")
            self.controls.append((entry, "normal"))
        ttk.Label(side, text="Finite capture, then USB upload.\nSearch marks the first match.\nNo trigger wait or rolling history.",
                  foreground=MUTED, justify="left").pack(anchor="w", pady=(2, 10))
        main = ttk.Frame(body)
        main.pack(side="left", fill="both", expand=True)
        toolbar = ttk.Frame(main)
        toolbar.pack(fill="x", pady=(0, 10))
        for label, command in (("Open", self.open_capture), ("Save", self.save_capture),
                               ("Export CSV", lambda: self.export("csv")),
                               ("Export VCD", lambda: self.export("vcd"))):
            self.button(toolbar, label, command).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="Fit", command=lambda: self.wave.fit()).pack(side="right")
        ttk.Button(toolbar, text="−", command=lambda: self.wave.zoom(2)).pack(side="right", padx=4)
        ttk.Button(toolbar, text="+", command=lambda: self.wave.zoom(0.5)).pack(side="right")
        ttk.Label(main, textvariable=self.summary, foreground=MUTED).pack(anchor="w", pady=(0, 6))
        self.wave = Waveform(main, self.cursor.set)
        self.wave.pack(fill="both", expand=True)
        ttk.Label(main, textvariable=self.cursor, foreground=MUTED, wraplength=900).pack(fill="x", pady=10)
        ttk.Label(outer, textvariable=self.status, foreground=COLORS[0], wraplength=1100).pack(fill="x", pady=(10, 0))
        self.refresh()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(40, self.poll)
        if demo:
            root.after(100, self.demo)
        elif port:
            root.after(100, self.connect)

    def label(self, parent, text, pady=(0, 0)):
        ttk.Label(parent, text=text, font=("TkDefaultFont", 10, "bold"), foreground=MUTED).pack(anchor="w", pady=pady)

    def button(self, parent, text, command):
        button = ttk.Button(parent, text=text, command=command)
        self.controls.append((button, "normal"))
        return button

    def combo(self, parent, label, variable, values, editable=False):
        ttk.Label(parent, text=label, foreground=MUTED).pack(anchor="w", pady=(8, 2))
        state = "normal" if editable else "readonly"
        box = ttk.Combobox(parent, textvariable=variable, values=values, state=state, width=24)
        box.pack(fill="x")
        self.controls.append((box, state))

    def config(self):
        trigger = Trigger[self.trigger.get().upper()]
        mask = int(self.mask.get(), 0) if trigger == Trigger.PATTERN else 1 << int(self.channel.get()[2:])
        value = int(self.pattern.get(), 0) if trigger == Trigger.PATTERN else 0
        config = Config(int(self.rate.get()), int(self.count.get()), trigger, mask, value)
        config.validate()
        return config

    def refresh(self):
        try:
            ports = list_ports()
            self.port_box["values"] = [p.device for p in ports]
            if not self.port.get() and ports:
                preferred = next((p for p in ports if p.vid == 0x303A and p.pid == 0x1001), ports[0])
                self.port.set(preferred.device)
        except (ImportError, OSError) as exc:
            self.status.set(f"Port discovery: {exc}. Demo remains available.")

    def job(self, name, function, success):
        if self.busy:
            return
        self.busy = True
        self.status.set(name)
        for widget, _ in self.controls:
            widget.configure(state="disabled")

        def worker():
            result = None
            try:
                result = function()
                self.results.put((success, result, None))
            except Exception as exc:
                self.results.put((success, None, exc))
            finally:
                if self.closing:
                    if self.device:
                        self.device.close()
                    if isinstance(result, tuple) and result and isinstance(result[0], Device):
                        result[0].close()
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            success, result, error = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            for widget, state in self.controls:
                widget.configure(state=state)
            if error:
                self.status.set(f"Error: {error}")
                messagebox.showerror("LogicScope", str(error))
            else:
                success(result)
        if not self.closing:
            self.root.after(40, self.poll)

    def connect(self):
        if self.device:
            self.device.close()
            self.device = None
            self.connect_button.configure(text="Connect")
            self.status.set("Disconnected")
            return
        port = self.port.get().strip()
        if not port:
            messagebox.showinfo("LogicScope", "Select a serial port or use Demo signals.")
            return

        def work():
            device = Device(port)
            try:
                return device, device.info()
            except Exception:
                device.close()
                raise

        def connected(result):
            self.device, info = result
            self.connect_button.configure(text="Disconnect")
            self.status.set(f"Connected to {port} · firmware {info['firmware']} · hardware not yet qualified")
        self.job(f"Connecting to {port}…", work, connected)

    def acquire(self):
        if not self.device:
            messagebox.showinfo("LogicScope", "Connect the analyser first, or use Demo signals.")
            return
        try:
            config = self.config()
        except ValueError as exc:
            messagebox.showerror("Capture settings", str(exc))
            return
        self.job("Capturing to SRAM, then transferring over USB…",
                 lambda: self.device.capture(config), self.show_capture)

    def demo(self):
        try:
            self.show_capture(demo_capture(self.config()))
        except ValueError as exc:
            messagebox.showerror("Capture settings", str(exc))

    def show_capture(self, capture):
        self.capture = capture
        self.wave.set_capture(capture)
        origin = "DEMO · synthetic" if capture.source == "demo" else "HARDWARE · unqualified"
        trigger = f"match at sample {capture.trigger_index}" if capture.trigger_index >= 0 else "no trigger match / immediate"
        self.summary.set(f"{origin}    {capture.rate:,} S/s    {len(capture.samples):,} samples    {time_label(capture.duration)}    {trigger}")
        self.status.set("Capture ready · use the mouse wheel to inspect transitions, then save or export")

    def open_capture(self):
        path = filedialog.askopenfilename(filetypes=[("LogicScope capture", "*.lscope")])
        if path:
            try:
                self.show_capture(Capture.load(path))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                messagebox.showerror("Open capture", str(exc))

    def save_capture(self):
        self.export("lscope")

    def export(self, extension):
        if not self.capture:
            messagebox.showinfo("LogicScope", "Capture or open signals first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=f".{extension}",
                                          filetypes=[(extension.upper(), f"*.{extension}")])
        if path:
            capture = self.capture
            method = {"lscope": capture.save, "csv": capture.export_csv, "vcd": capture.export_vcd}[extension]
            self.job("Saving capture…", lambda: method(path), lambda _: self.status.set(f"Saved {path}"))

    def close(self):
        self.closing = True
        if self.device and not self.busy:
            self.device.close()
        self.root.destroy()


def run(demo=False, port=None, config=Config()):
    root = tk.Tk()
    App(root, demo=demo, port=port, config=config)
    root.mainloop()
