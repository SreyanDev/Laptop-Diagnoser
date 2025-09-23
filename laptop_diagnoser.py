import os
import sys
import platform
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime
import threading
import time

# External deps
import psutil
import PySimpleGUI as sg

IS_WINDOWS = platform.system() == "Windows"

# Optional: Windows event log
if IS_WINDOWS:
    try:
        import win32evtlog
    except ImportError:
        win32evtlog = None


# ------------------ Helpers ------------------
def human_bytes(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def gather_basic_info():
    mem = psutil.virtual_memory()
    du = shutil.disk_usage(os.getenv("SystemDrive", "C:\\"))
    battery = psutil.sensors_battery()
    info = {
        "Platform": platform.platform(),
        "Python": platform.python_version(),
        "CPU cores": psutil.cpu_count(logical=True),
        "CPU usage": f"{psutil.cpu_percent(interval=0.6)}%",
        "Memory": f"{human_bytes(mem.used)} / {human_bytes(mem.total)} ({mem.percent}%)",
        "Disk (C:)": f"{human_bytes(du.used)} / {human_bytes(du.total)} ({(du.used/du.total)*100:.1f}%)",
    }
    if battery:
        info["Battery"] = f"{battery.percent}% {'Charging' if battery.power_plugged else 'On Battery'}"
    return info


def top_processes(limit=10):
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            procs.append(p.info)
        except Exception:
            pass
    procs.sort(
        key=lambda x: (x.get("cpu_percent", 0) or 0)
        + (x.get("memory_percent", 0) or 0),
        reverse=True,
    )
    return procs[:limit]


def check_network_basic():
    res = {}

    def ping(host):
        try:
            rc = subprocess.run(
                ["ping", "-n", "2", host],
                capture_output=True,
                text=True,
                timeout=6,
            )
            return rc.returncode == 0
        except Exception:
            return False

    res["ping 1.1.1.1"] = ping("1.1.1.1")
    try:
        import socket

        res["DNS google.com"] = bool(socket.gethostbyname("www.google.com"))
    except Exception:
        res["DNS google.com"] = False
    return res


def clear_temp_files():
    paths = [os.environ.get("TEMP"), os.environ.get("TMP")]
    removed = 0
    for p in set(filter(None, paths)):
        for root, _, files in os.walk(p):
            for fn in files:
                try:
                    os.remove(os.path.join(root, fn))
                    removed += 1
                except Exception:
                    pass
    return removed


def get_recent_events(limit=15, hours=48):
    if not IS_WINDOWS or not win32evtlog:
        return ["Event Log not available"]
    from datetime import timedelta

    entries = []
    cutoff = datetime.now() - timedelta(hours=hours)
    for log in ["System", "Application"]:
        try:
            hand = win32evtlog.OpenEventLog("localhost", log)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            for ev in events:
                if ev.EventType not in (
                    win32evtlog.EVENTLOG_ERROR_TYPE,
                    win32evtlog.EVENTLOG_WARNING_TYPE,
                ):
                    continue
                etime = ev.TimeGenerated.Format()
                entries.append(f"[{log}] {etime} {ev.SourceName}: {ev.EventType}")
                if len(entries) >= limit:
                    break
        except Exception:
            pass
    return entries or ["No recent warnings/errors"]


def list_startup_apps():
    """List startup items from registry (Windows only)"""
    if not IS_WINDOWS:
        return ["Not supported"]
    try:
        import winreg

        result = []
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        )
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                result.append(f"{name}: {value}")
                i += 1
            except OSError:
                break
        return result or ["No startup apps"]
    except Exception:
        return ["Could not fetch startup apps"]


def generate_report(info, procs, net, events, startup):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"Laptop Diagnoser Report - {ts}", "=" * 60, ""]
    lines.extend([f"{k}: {v}" for k, v in info.items()])
    lines.append("\nTop processes:")
    for p in procs:
        lines.append(
            f" PID {p['pid']:>5} {p['name'][:25]:25} CPU {p['cpu_percent']:>5}% MEM {p['memory_percent']:.1f}%"
        )
    lines.append("\nNetwork checks:")
    lines.extend([f" {k}: {'OK' if v else 'FAILED'}" for k, v in net.items()])
    lines.append("\nStartup Apps:")
    lines.extend(startup)
    lines.append("\nEvent Log:")
    lines.extend(events)
    return "\n".join(lines)


# ------------------ GUI ------------------
sg.theme("DarkBlue3")

tab1 = [
    [sg.Multiline(size=(90, 20), key="-OUT-", disabled=True, font=("Consolas", 10))],
    [sg.Button("Run Diagnostics"), sg.Button("Clear Temp Files"),
     sg.Button("Show Repair Commands"), sg.Button("Save Report")]
]

tab2 = [
    [sg.Text("Real-time Monitoring (updates every 2s)", font=("Segoe UI", 12))],
    [sg.Text("", key="-MONITOR-", size=(90, 10), font=("Consolas", 10))]
]

tab3 = [
    [sg.Text("Security & Startup Checks", font=("Segoe UI", 12))],
    [sg.Multiline(size=(90, 15), key="-SEC-", disabled=True, font=("Consolas", 10))],
    [sg.Button("Run Security Check")]
]

layout = [
    [sg.TabGroup([
        [sg.Tab("Diagnostics", tab1), sg.Tab("Monitor", tab2), sg.Tab("Security", tab3)]
    ])],
    [sg.Button("Exit")]
]

window = sg.Window("Laptop Diagnoser", layout, finalize=True)

diagnostics = {}

def run_diagnostics():
    info = gather_basic_info()
    procs = top_processes(10)
    net = check_network_basic()
    events = get_recent_events()
    startup = list_startup_apps()
    diagnostics.update(
        {"info": info, "procs": procs, "net": net, "events": events, "startup": startup}
    )

    report = generate_report(info, procs, net, events, startup)
    window["-OUT-"].update(report)


def run_security_check():
    txt = []
    if IS_WINDOWS:
        # Firewall check
        try:
            fw = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            txt.append("Firewall Status:\n" + fw.stdout.splitlines()[0:10].__str__())
        except Exception:
            txt.append("Could not check firewall")
        # Defender check
        try:
            av = subprocess.run(
                ["powershell", "Get-MpComputerStatus | Select-Object -Property AMServiceEnabled,AntispywareEnabled,AntivirusEnabled"],
                capture_output=True,
                text=True,
            )
            txt.append("Antivirus Status:\n" + av.stdout.strip())
        except Exception:
            txt.append("Could not check antivirus")
    else:
        txt.append("Security check is Windows-only")
    txt.extend(["\nStartup Apps:"] + list_startup_apps())
    window["-SEC-"].update("\n".join(txt))


# ------------------ Main Loop ------------------
last_monitor = 0

while True:
    event, _ = window.read(timeout=1000)
    if event in (sg.WIN_CLOSED, "Exit"):
        break

    if event == "Run Diagnostics":
        threading.Thread(target=run_diagnostics, daemon=True).start()

    if event == "Clear Temp Files":
        if sg.popup_yes_no("Delete temporary files?") == "Yes":
            removed = clear_temp_files()
            sg.popup(f"Removed {removed} temp files.")

    if event == "Show Repair Commands":
        sg.popup_scrolled(
            "Suggested Windows Repair Commands (run as Administrator):\n\n"
            " - sfc /scannow   (System File Checker)\n"
            " - DISM /Online /Cleanup-Image /RestoreHealth\n"
            " - chkdsk C: /f   (Check disk on next reboot)\n"
            " - cleanmgr       (Disk Cleanup)\n"
            " - start ms-settings:windowsupdate   (Windows Update)\n"
        )

    if event == "Save Report":
        if not diagnostics:
            sg.popup("Run diagnostics first.")
            continue
        fname = sg.popup_get_file(
            "Save Report As",
            save_as=True,
            default_extension=".txt",
            file_types=(("Text Files", "*.txt"), ("JSON", "*.json")),
        )
        if fname:
            if fname.endswith(".json"):
                Path(fname).write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
            else:
                Path(fname).write_text(generate_report(**diagnostics), encoding="utf-8")
            sg.popup(f"Report saved to {fname}")

    if event == "Run Security Check":
        threading.Thread(target=run_security_check, daemon=True).start()

    # Update monitor every 2s
    if time.time() - last_monitor > 2:
        last_monitor = time.time()
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=None)
        disk = psutil.disk_usage(os.getenv("SystemDrive", "C:\\"))
        net = psutil.net_io_counters()
        monitor_txt = (
            f"CPU: {cpu}%   "
            f"Memory: {mem.percent}% ({human_bytes(mem.used)}/{human_bytes(mem.total)})   "
            f"Disk: {disk.percent}%   "
            f"Net Sent: {human_bytes(net.bytes_sent)} / Recv: {human_bytes(net.bytes_recv)}"
        )
        window["-MONITOR-"].update(monitor_txt)

window.close()
