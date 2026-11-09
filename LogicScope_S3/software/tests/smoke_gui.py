"""Exercise actual Tk widgets on a desktop or xvfb-run display."""
import tkinter as tk
from types import SimpleNamespace
from unittest.mock import patch

from logicscope.capture import demo_capture
from logicscope.gui import App
from logicscope.protocol import Config, Trigger


def main():
    root = tk.Tk()
    with patch("logicscope.gui.list_ports", return_value=[]):
        app = App(root)
    root.update()
    assert app.capture_button.winfo_ismapped()
    assert app.capture_button.winfo_rooty() + app.capture_button.winfo_height() < root.winfo_rooty() + root.winfo_height()
    cap = demo_capture(Config(count=65536, trigger=Trigger.RISING))
    app.show_capture(cap)
    root.update()
    assert app.capture is cap
    assert len(app.wave.canvas.find_all()) > 100
    app.wave.zoom(0.001)
    root.update()
    assert app.wave.span < 100
    app.wave.pan("moveto", "0.25")
    assert app.wave.start > 0
    app.wave.click(SimpleNamespace(x=150))
    app.wave.click(SimpleNamespace(x=300), second=True)
    assert "Δt" in app.cursor.get()
    app.wave.fit()
    assert app.wave.start == 0 and app.wave.span == 65536
    app.close()
    print("GUI smoke test passed: 8 lanes, max capture, zoom, pan, cursors, fit")


if __name__ == "__main__":
    main()
