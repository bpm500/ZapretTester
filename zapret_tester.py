"""
ZapretTester — Zapret GUI для Discord/YouTube
License: MIT | github.com/Beesc9it/ZapretTester
"""

import sys
import os
import subprocess
import threading
import time
import json
import ctypes
import winreg
import psutil
import requests
import ping3
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QCheckBox, QTextEdit,
    QSystemTrayIcon, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QIcon, QPixmap, QColor, QPalette, QImage,
    QPainter, QBrush, QPen, QCursor, QAction
)

# ══════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════

def resource_path(rel: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(os.path.abspath("."), rel)

def get_app_dir() -> Path:
    if hasattr(sys, 'frozen'):
        return Path(sys.executable).parent
    return Path(__file__).parent

def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        return False

def apply_dark_titlebar(hwnd: int):
    try:
        val = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), 4)
    except:
        pass

# ── Run bat — unicode-safe, no VBS, no ShellExecute dialogs ──────

def _run_bat_admin(bat_path: Path):
    """
    Run a .bat file and then hide all windows belonging to winws.exe.
    """
    path_str = str(bat_path.resolve())
    work_dir = str(bat_path.parent.resolve())
    cmd = f'cmd.exe /c "{path_str}"'
    subprocess.Popen(
        cmd,
        cwd=work_dir,
        shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    # Give winws.exe time to start, then hide its window(s)
    def _hide_after_start():
        time.sleep(2)
        _hide_winws_windows()
    threading.Thread(target=_hide_after_start, daemon=True).start()


def _hide_winws_windows():
    """
    Hide all visible windows belonging to winws.exe processes.
    Uses EnumWindows + GetWindowThreadProcessId via ctypes.
    SW_HIDE = 0.
    """
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        # Collect PIDs of all winws.exe processes
        winws_pids: set[int] = set()
        for p in psutil.process_iter(["name", "pid"]):
            if p.info["name"] and "winws" in p.info["name"].lower():
                winws_pids.add(p.info["pid"])

        if not winws_pids:
            return

        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        )

        def _enum_cb(hwnd, _):
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value in winws_pids:
                # Hide window regardless of visibility state
                user32.ShowWindow(hwnd, 0)   # SW_HIDE
                # Also remove from taskbar / alt-tab
                ex_style = user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
                # WS_EX_TOOLWINDOW removes from alt-tab; clear WS_EX_APPWINDOW
                new_style = (ex_style | 0x00000080) & ~0x00040000
                user32.SetWindowLongW(hwnd, -20, new_style)
            return True

        user32.EnumWindows(EnumWindowsProc(_enum_cb), 0)
    except Exception:
        pass

def _kill_winws():
    try:
        for p in psutil.process_iter(["name", "pid"]):
            if p.info["name"] and "winws" in p.info["name"].lower():
                try:
                    psutil.Process(p.info["pid"]).terminate()
                    time.sleep(0.05)
                except:
                    try: psutil.Process(p.info["pid"]).kill()
                    except: pass
    except:
        pass

def _is_winws_running() -> bool:
    try:
        for p in psutil.process_iter(["name"]):
            if p.info["name"] and "winws" in p.info["name"].lower():
                return True
    except:
        pass
    return False

def _test_url(url: str) -> bool:
    try:
        r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code == 200
    except:
        return False

def _make_tray_icon(connected: bool) -> QIcon:
    img = QImage(64, 64, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    color = QColor("#28a745") if connected else QColor("#555")
    p.setBrush(QBrush(color))
    p.setPen(QPen(QColor("#fff"), 2))
    p.drawEllipse(4, 4, 56, 56)
    p.setBrush(QBrush(QColor("#fff")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(22, 22, 20, 20)
    p.end()
    return QIcon(QPixmap.fromImage(img))

# ══════════════════════════════════════════════════════════════════
#  STYLESHEET
# ══════════════════════════════════════════════════════════════════

STYLE = """
* { font-family: 'Segoe UI', Arial, sans-serif; }
QMainWindow, QWidget { background: #0d0d0d; }

/* Tab bar */
QWidget#tabBar { background: #111; border-bottom: 1px solid #1e1e1e; }
QPushButton#tab {
    background: #111; color: #555;
    border: none; border-bottom: 2px solid transparent;
    padding: 11px 0; font-size: 13px; font-weight: 600;
}
QPushButton#tab:hover { color: #999; background: #141414; }
QPushButton#tab[active="true"] {
    color: #e8e8e8; border-bottom: 2px solid #4f9ef8; background: #0d0d0d;
}

/* Buttons */
QPushButton#actionBtn {
    background: #1a1a1a; color: #bbb;
    border: 1px solid #252525; border-radius: 5px;
    padding: 7px 14px; font-size: 12px;
}
QPushButton#actionBtn:hover { background: #222; border-color: #3a3a3a; color: #eee; }
QPushButton#actionBtn:pressed { background: #141414; }
QPushButton#actionBtn:disabled { color: #3a3a3a; border-color: #191919; }
QPushButton#testBtn {
    background: #162a1a; color: #4caf6e;
    border: 1px solid #1e3a22; border-radius: 5px;
    padding: 7px 14px; font-size: 12px; font-weight: 600;
}
QPushButton#testBtn:hover { background: #1a3520; border-color: #4caf6e; }
QPushButton#testBtn[testing="true"] {
    background: #2a1616; color: #e05555; border-color: #3a2020;
}
QPushButton#testBtn[testing="true"]:hover { border-color: #e05555; }

/* ComboBox */
QComboBox {
    background: #141414; color: #bbb;
    border: 1px solid #222; border-radius: 5px;
    padding: 5px 10px; font-size: 12px; min-height: 26px;
}
QComboBox:hover { border-color: #333; color: #ddd; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #141414; color: #bbb;
    border: 1px solid #2a2a2a;
    selection-background-color: #1e1e1e;
    outline: none;
}

/* CheckBox */
QCheckBox { color: #666; font-size: 12px; spacing: 7px; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1px solid #2a2a2a; border-radius: 3px; background: #141414;
}
QCheckBox::indicator:checked { background: #4f9ef8; border-color: #4f9ef8; }
QCheckBox:hover { color: #999; }

/* Console */
QTextEdit#console {
    background: #080808; color: #bbb;
    border: 1px solid #181818; border-radius: 5px;
    font-family: 'Consolas', monospace; font-size: 11px;
    padding: 6px;
}

/* ScrollBar */
QScrollBar:vertical { background: #0d0d0d; width: 4px; border-radius: 2px; }
QScrollBar::handle:vertical { background: #2a2a2a; border-radius: 2px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* Status bar */
QLabel#statusBar {
    background: #080808; color: #333; font-size: 11px;
    border-top: 1px solid #151515; padding: 0 12px;
}

/* Section labels */
QLabel#sectionLbl {
    color: #333; font-size: 10px; font-weight: 700;
    letter-spacing: 1.5px; background: transparent;
}

/* Tray menu */
QMenu { background: #111; color: #bbb; border: 1px solid #222; font-size: 12px; }
QMenu::item { padding: 6px 20px; }
QMenu::item:selected { background: #1a1a1a; color: #eee; }
QMenu::separator { background: #1e1e1e; height: 1px; margin: 3px 0; }
"""

# ══════════════════════════════════════════════════════════════════
#  POWER BUTTON
# ══════════════════════════════════════════════════════════════════

class PowerButton(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False
        self.setFixedSize(210, 210)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pix_on = self._pix_off = None
        self._load_images()
        self._refresh()

    def _load_images(self):
        for attr, fname in (("_pix_on", "on.png"), ("_pix_off", "off.png")):
            p = resource_path(fname)
            if os.path.exists(p):
                px = QPixmap(p).scaled(
                    210, 210,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                setattr(self, attr, px)

    def _refresh(self):
        px = self._pix_on if self._connected else self._pix_off
        if px:
            self.setPixmap(px)
            return
        # Fallback drawing
        img = QImage(130, 130, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor("#28a745") if self._connected else QColor("#e8e8e8")
        p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(3, 3, 124, 124)
        p.setBrush(QBrush(QColor("#0d0d0d")))
        p.drawEllipse(35, 35, 60, 60)
        pw = QPen(QColor("#0d0d0d"), 7, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap)
        p.setPen(pw)
        p.drawLine(65, 35, 65, 68)
        p.end()
        self.setPixmap(QPixmap.fromImage(img))

    def set_connected(self, v: bool):
        if self._connected != v:
            self._connected = v
            self._refresh()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

# ══════════════════════════════════════════════════════════════════
#  TEST WORKER
# ══════════════════════════════════════════════════════════════════

class TestWorker(QThread):
    log      = pyqtSignal(str, str)
    result   = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, bat_files: list, zapret_dir: Path):
        super().__init__()
        self.bat_files  = bat_files
        self.zapret_dir = zapret_dir
        self._stop      = False

    def stop(self):
        self._stop = True

    def run(self):
        results = []
        ping_targets = {
            "Yandex": "yandex.com", "Discord": "discord.com",
            "YouTube": "youtube.com", "Roblox": "roblox.com",
        }

        self.log.emit("═" * 50, "yellow")
        self.log.emit(f"Starting tests: {len(self.bat_files)} configs", "yellow")

        for bat_file in self.bat_files:
            if self._stop:
                break

            bat_path = self.zapret_dir / bat_file
            self.log.emit(f"\n▶ Testing: {bat_file}", "white")

            try:
                self.log.emit("  Stopping old processes...", "yellow")
                _kill_winws()
                time.sleep(1)
                if self._stop: break

                self.log.emit("  Starting config...", "yellow")
                _run_bat_admin(bat_path)
                time.sleep(3)
                if self._stop: _kill_winws(); break

                res = {"name": bat_file, "services": {}, "pings": {}, "avg": 0}

                # Service checks
                for svc, url in [("YouTube","https://www.youtube.com"),
                                  ("Discord","https://discord.com"),
                                  ("Roblox", "https://www.roblox.com")]:
                    if self._stop: break
                    ok = _test_url(url)
                    res["services"][svc] = ok
                    self.log.emit(
                        f"    {svc}: {'✓' if ok else '✗'}",
                        "green" if ok else "red"
                    )

                if self._stop: _kill_winws(); break

                # Ping checks
                ping_vals = []
                for svc, host in ping_targets.items():
                    if self._stop: break
                    try:
                        d  = ping3.ping(host, timeout=2)
                        ms = int(d * 1000) if d else 999
                    except:
                        ms = 999
                    res["pings"][svc] = ms
                    ping_vals.append(ms)
                    lbl = "Ping" if svc == "Yandex" else f"{svc} ping"
                    self.log.emit(f"    {lbl}: {ms} ms",
                                  "cyan" if ms < 999 else "red")

                valid = [p for p in ping_vals if p < 999]
                res["avg"] = sum(valid) / len(valid) if valid else 999
                results.append(res)

                _kill_winws()
                time.sleep(1)

            except Exception as e:
                self.log.emit(f"  Error: {e}", "red")
                _kill_winws()

        # FIX #3: always log stop/done
        if self._stop:
            _kill_winws()
            self.log.emit("", "white")
            self.log.emit("⛔  Тесты остановлены пользователем.", "red")
        else:
            if results:
                self._show_top(results)
            self.log.emit("", "white")
            self.log.emit("✅  Все тесты завершены!", "green")

        self.finished.emit()

    def _show_top(self, results):
        srt = sorted(results,
                     key=lambda x: (x["avg"], -sum(x["services"].values())))[:3]
        lines = ["\n" + "═" * 50, "  TOP 3 RESULTS", "═" * 50]
        for i, r in enumerate(srt, 1):
            av = sum(r["services"].values())
            lines.append(f"\n{i}. {r['name']}")
            lines.append(f"   Available: {av}/3  |  Avg ping: {r['avg']:.0f} ms")
            for k, v in r["pings"].items():
                lbl = "Ping" if k == "Yandex" else f"{k} ping"
                lines.append(f"   {lbl}: {v} ms")
        self.result.emit("\n".join(lines))

# ══════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZapretTester")
        self.setMinimumSize(420, 560)
        self.resize(440, 600)
        self.setStyleSheet(STYLE)

        ico = resource_path("1.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        # State
        self._connected    = False
        self._process      = None
        self._bat_files    : list[str]    = []
        self._current_bat  : str | None   = None
        self._test_worker  : TestWorker | None = None
        self._dark_applied = False

        # Paths
        self._app_dir    = get_app_dir()
        self._zapret_dir = self._find_zapret_dir()
        self._cfg_file   = self._app_dir / "zapret_settings.json"

        self._auto_connect = False
        self._auto_start   = False
        self._load_settings()

        self._build_ui()
        self._load_bat_files()
        self._setup_tray()

        if _is_winws_running():
            self._connected = True
            self._sync_ui()
            self._log("Detected active winws process.", "yellow")

        if self._auto_connect and self._current_bat:
            QTimer.singleShot(1000, self._connect)

    # ── Paths ─────────────────────────────────────────────────────

    def _find_zapret_dir(self) -> Path:
        """
        FIX #3: zapret folder sits directly next to the exe.
        We look for .bat files in <app_dir>/zapret/ first,
        then fall back to a single subdirectory inside it.
        """
        base = self._app_dir / "zapret"
        base.mkdir(exist_ok=True)

        # Direct .bat files inside zapret/
        if list(base.glob("*.bat")):
            return base

        # Single subdirectory (e.g. zapret-discord-youtube-1.9.3/)
        subdirs = [d for d in base.iterdir() if d.is_dir()]
        if len(subdirs) == 1:
            return subdirs[0]

        return base

    # ── Settings ──────────────────────────────────────────────────

    def _load_settings(self):
        if self._cfg_file.exists():
            try:
                d = json.loads(self._cfg_file.read_text(encoding="utf-8"))
                self._current_bat  = d.get("last_bat")
                self._auto_connect = d.get("auto_connect", False)
                self._auto_start   = d.get("auto_start", False)
                self._apply_auto_start()
            except:
                pass

    def _save_settings(self):
        try:
            self._cfg_file.write_text(
                json.dumps({
                    "last_bat":     self._current_bat,
                    "auto_connect": self._auto_connect,
                    "auto_start":   self._auto_start,
                }, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except:
            pass

    def _apply_auto_start(self):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        name     = "ZapretTester"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path,
                                 0, winreg.KEY_SET_VALUE)
            if self._auto_start:
                exe = sys.executable if hasattr(sys, "frozen") else sys.argv[0]
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, f'"{exe}"')
            else:
                try:
                    winreg.DeleteValue(key, name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self._log(f"Auto-start error: {e}", "red")

    # ── UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        vlay = QVBoxLayout(root)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        # Tab bar
        tab_bar = QWidget(); tab_bar.setObjectName("tabBar")
        tab_bar.setFixedHeight(44)
        tb = QHBoxLayout(tab_bar)
        tb.setContentsMargins(0, 0, 0, 0); tb.setSpacing(0)

        self._tab_connect  = self._mk_tab("Connect")
        self._tab_settings = self._mk_tab("Settings")
        self._tab_connect.clicked.connect(lambda: self._switch(0))
        self._tab_settings.clicked.connect(lambda: self._switch(1))
        tb.addWidget(self._tab_connect)
        tb.addWidget(self._tab_settings)
        vlay.addWidget(tab_bar)

        # Pages
        self._pg_connect  = self._build_connect_page()
        self._pg_settings = self._build_settings_page()
        vlay.addWidget(self._pg_connect,  1)
        vlay.addWidget(self._pg_settings, 1)

        # Status bar
        self._status_bar = QLabel()
        self._status_bar.setObjectName("statusBar")
        self._status_bar.setFixedHeight(22)
        vlay.addWidget(self._status_bar)

        self._switch(0)
        self._refresh_statusbar()

    def _mk_tab(self, text: str) -> QPushButton:
        b = QPushButton(text)
        b.setObjectName("tab")
        b.setProperty("active", "false")
        b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        return b

    def _switch(self, idx: int):
        self._pg_connect.setVisible(idx == 0)
        self._pg_settings.setVisible(idx == 1)
        for i, b in enumerate([self._tab_connect, self._tab_settings]):
            b.setProperty("active", "true" if i == idx else "false")
            b.style().unpolish(b); b.style().polish(b)

    # ── Connect page ──────────────────────────────────────────────

    def _build_connect_page(self) -> QWidget:
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(32, 20, 32, 20)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # ── Power button ──────────────────────────────────────────
        self._power_btn = PowerButton()
        self._power_btn.clicked.connect(self._toggle_connection)
        lay.addWidget(self._power_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(14)

        # ── Status ────────────────────────────────────────────────
        self._status_lbl = QLabel("Disconnected")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet(
            "color:#e8e8e8; font-size:17px; font-weight:700; background:transparent;")
        lay.addWidget(self._status_lbl)
        lay.addSpacing(28)

        # ── Config selector ───────────────────────────────────────
        sel_lbl = QLabel("КОНФИГУРАЦИЯ")
        sel_lbl.setObjectName("sectionLbl")
        lay.addWidget(sel_lbl)
        lay.addSpacing(6)

        self._combo = QComboBox()
        self._combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._combo.currentTextChanged.connect(self._on_combo_changed)
        lay.addWidget(self._combo)
        lay.addSpacing(24)

        # ── Options ───────────────────────────────────────────────
        opt_lbl = QLabel("ПАРАМЕТРЫ")
        opt_lbl.setObjectName("sectionLbl")
        lay.addWidget(opt_lbl)
        lay.addSpacing(8)

        chk_row = QHBoxLayout(); chk_row.setSpacing(20)
        self._chk_autostart = QCheckBox("Автозапуск")
        self._chk_autostart.setChecked(self._auto_start)
        self._chk_autostart.toggled.connect(self._on_autostart_changed)

        self._chk_autoconnect = QCheckBox("Автоподключение")
        self._chk_autoconnect.setChecked(self._auto_connect)
        self._chk_autoconnect.toggled.connect(self._on_autoconnect_changed)

        chk_row.addWidget(self._chk_autostart)
        chk_row.addWidget(self._chk_autoconnect)
        chk_row.addStretch()
        lay.addLayout(chk_row)

        return w

    # ── Settings page ─────────────────────────────────────────────

    def _build_settings_page(self) -> QWidget:
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        # Console label + clear
        row1 = QHBoxLayout()
        con_lbl = QLabel("КОНСОЛЬ"); con_lbl.setObjectName("sectionLbl")
        self._btn_clear = QPushButton("Очистить")
        self._btn_clear.setObjectName("actionBtn")
        self._btn_clear.setFixedHeight(26)
        self._btn_clear.clicked.connect(self._console_clear)
        row1.addWidget(con_lbl); row1.addStretch(); row1.addWidget(self._btn_clear)
        lay.addLayout(row1)

        self._console = QTextEdit()
        self._console.setObjectName("console")
        self._console.setReadOnly(True)
        self._console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        lay.addWidget(self._console, 3)

        # Action buttons
        btn_row = QHBoxLayout(); btn_row.setSpacing(6)
        self._btn_service = QPushButton("▶  Run service.bat")
        self._btn_service.setObjectName("actionBtn")
        self._btn_service.clicked.connect(self._run_service)

        self._btn_test = QPushButton("⚡  Test All Configs")
        self._btn_test.setObjectName("testBtn")
        self._btn_test.setProperty("testing", "false")
        self._btn_test.clicked.connect(self._toggle_testing)

        btn_row.addWidget(self._btn_service)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_test)
        lay.addLayout(btn_row)

        # Results
        res_lbl = QLabel("РЕЗУЛЬТАТЫ"); res_lbl.setObjectName("sectionLbl")
        lay.addWidget(res_lbl)

        self._results = QTextEdit()
        self._results.setObjectName("console")
        self._results.setReadOnly(True)
        lay.addWidget(self._results, 2)

        return w

    # ── Tray ──────────────────────────────────────────────────────

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(_make_tray_icon(False))
        self._tray.setToolTip("ZapretTester")
        self._tray.activated.connect(self._on_tray_activated)

        m = QMenu()
        m.setStyleSheet(STYLE)
        self._act_open  = QAction("Открыть",      self)
        self._act_conn  = QAction("Подключить",   self)
        self._act_disc  = QAction("Отключить",    self)
        self._act_exit  = QAction("Выход",        self)
        self._act_open.triggered.connect(self._restore)
        self._act_conn.triggered.connect(self._connect)
        self._act_disc.triggered.connect(self._disconnect)
        self._act_exit.triggered.connect(self._exit_app)
        m.addAction(self._act_open)
        m.addSeparator()
        m.addAction(self._act_conn)
        m.addAction(self._act_disc)
        m.addSeparator()
        m.addAction(self._act_exit)
        self._tray.setContextMenu(m)
        self._tray.show()
        self._refresh_tray()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self._restore()

    def _restore(self):
        self.showNormal(); self.activateWindow(); self.raise_()

    def _exit_app(self):
        self._disconnect()
        self._tray.hide()
        QApplication.quit()

    def _refresh_tray(self):
        self._act_conn.setVisible(not self._connected)
        self._act_disc.setVisible(self._connected)
        self._tray.setIcon(_make_tray_icon(self._connected))

    # ── Window events ─────────────────────────────────────────────

    def showEvent(self, e):
        super().showEvent(e)
        if not self._dark_applied:
            self._dark_applied = True
            try:
                apply_dark_titlebar(int(self.winId()))
            except:
                pass

    def closeEvent(self, e):
        e.ignore()
        self.hide()
        self._tray.showMessage("ZapretTester",
            "Свёрнуто в трей. Нажмите на иконку для открытия.",
            QSystemTrayIcon.MessageIcon.Information, 2000)

    # ── BAT files ─────────────────────────────────────────────────

    def _load_bat_files(self):
        self._bat_files = []
        if self._zapret_dir.exists():
            for f in sorted(self._zapret_dir.glob("*.bat")):
                if f.name.lower() != "service.bat":
                    self._bat_files.append(f.name)

        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItems(self._bat_files)
        if self._current_bat and self._current_bat in self._bat_files:
            self._combo.setCurrentText(self._current_bat)
        elif self._bat_files:
            self._current_bat = self._bat_files[0]
            self._combo.setCurrentIndex(0)
        self._combo.blockSignals(False)

    def _on_combo_changed(self, text: str):
        if text:
            self._current_bat = text
            self._save_settings()
            self._log(f"Selected: {text}", "white")

    # ── Connection ────────────────────────────────────────────────

    def _toggle_connection(self):
        if self._connected:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        if not self._current_bat:
            self._set_status("No config selected", "#e05555"); return
        bat = self._zapret_dir / self._current_bat
        if not bat.exists():
            self._set_status("File not found", "#e05555")
            self._log(f"Not found: {bat}", "red"); return

        self._set_status("Connecting...", "#ffc107")
        QApplication.processEvents()
        try:
            _run_bat_admin(bat)
            time.sleep(1.5)
            self._connected = True
            self._sync_ui()
            self._log(f"Connected: {self._current_bat}", "green")
        except Exception as ex:
            self._set_status("Error", "#e05555")
            self._log(f"Error: {ex}", "red")

    def _disconnect(self):
        _kill_winws()
        if self._process:
            try: self._process.terminate()
            except: pass
            self._process = None
        self._connected = False
        self._sync_ui()
        self._log("Disconnected.", "yellow")

    def _sync_ui(self):
        self._power_btn.set_connected(self._connected)
        self._set_status(
            "Connected"    if self._connected else "Disconnected",
            "#28a745"      if self._connected else "#e8e8e8"
        )
        self._refresh_tray()
        self._refresh_statusbar()

    def _set_status(self, text: str, color: str):
        self._status_lbl.setText(text)
        self._status_lbl.setStyleSheet(
            f"color:{color}; font-size:17px; font-weight:700; background:transparent;")

    def _refresh_statusbar(self):
        dot   = "●" if self._connected else "○"
        state = "Connected" if self._connected else "Disconnected"
        col   = "#28a745"   if self._connected else "#333"
        admin = "Admin ✓" if is_admin() else "No admin"
        self._status_bar.setText(f"  {dot} {state}   ·   {admin}")
        self._status_bar.setStyleSheet(
            f"background:#080808; color:{col}; font-size:11px; "
            f"border-top:1px solid #151515; padding:0 12px;")

    # ── Settings actions ──────────────────────────────────────────

    def _on_autostart_changed(self, v: bool):
        self._auto_start = v
        self._apply_auto_start()
        self._save_settings()
        self._log(f"Auto-start {'enabled' if v else 'disabled'}", "yellow")

    def _on_autoconnect_changed(self, v: bool):
        self._auto_connect = v
        self._save_settings()
        self._log(f"Auto-connect {'enabled' if v else 'disabled'}", "yellow")

    def _console_clear(self):
        self._console.clear()

    def _run_service(self):
        svc = self._zapret_dir / "service.bat"
        if not svc.exists():
            self._log("ERROR: service.bat not found!", "red"); return
        self._log("Starting service.bat...", "yellow")

        def _run():
            try:
                p = subprocess.Popen(
                    ["cmd.exe", "/c", str(svc.resolve())],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="ignore",
                    cwd=str(svc.parent.resolve()),
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in p.stdout:
                    if line.strip():
                        self._log(line.strip(), "cyan")
                p.wait()
                self._log("service.bat completed.", "green")
            except Exception as e:
                self._log(f"Error: {e}", "red")

        threading.Thread(target=_run, daemon=True).start()

    # ── Testing ───────────────────────────────────────────────────

    def _toggle_testing(self):
        if self._test_worker and self._test_worker.isRunning():
            self._test_worker.stop()
            self._btn_test.setEnabled(False)
            self._btn_test.setText("Stopping...")
        else:
            self._start_testing()

    def _start_testing(self):
        if not self._bat_files:
            self._log("No .bat files found.", "red"); return

        self._results.clear()
        self._btn_test.setText("⛔  Stop Testing")
        self._btn_test.setProperty("testing", "true")
        self._btn_test.style().unpolish(self._btn_test)
        self._btn_test.style().polish(self._btn_test)

        self._test_worker = TestWorker(self._bat_files, self._zapret_dir)
        self._test_worker.log.connect(self._log)
        self._test_worker.result.connect(self._results.setPlainText)
        self._test_worker.finished.connect(self._on_test_done)
        self._test_worker.start()

    def _on_test_done(self):
        self._btn_test.setText("⚡  Test All Configs")
        self._btn_test.setEnabled(True)
        self._btn_test.setProperty("testing", "false")
        self._btn_test.style().unpolish(self._btn_test)
        self._btn_test.style().polish(self._btn_test)

    # ── Logging ───────────────────────────────────────────────────

    def _log(self, text: str, color: str = "white"):
        COLORS = {
            "white":  "#bbb",   "green":  "#4caf6e",
            "red":    "#e05555","yellow": "#f0b429",
            "cyan":   "#38bdf8","blue":   "#4f9ef8",
        }
        hx = COLORS.get(color, "#bbb")
        ts = time.strftime("%H:%M:%S")
        self._console.append(
            f'<span style="color:#2a2a2a;">[{ts}]</span> '
            f'<span style="color:{hx};">{text}</span>'
        )
        sb = self._console.verticalScrollBar()
        sb.setValue(sb.maximum())


# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ZapretTester")
    app.setQuitOnLastWindowClosed(False)

    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,     QColor(13, 13, 13))
    p.setColor(QPalette.ColorRole.WindowText, QColor(187, 187, 187))
    p.setColor(QPalette.ColorRole.Base,       QColor(8, 8, 8))
    p.setColor(QPalette.ColorRole.Text,       QColor(187, 187, 187))
    app.setPalette(p)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
