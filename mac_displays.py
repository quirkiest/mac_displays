#!/usr/bin/env python3
"""
mac_displays — restore monitor arrangement + per-position wallpapers on macOS.

Built for setups with IDENTICAL external monitors, where macOS:
  - regenerates "persistent" screen UUIDs after sleep/replug race conditions
  - reports the same serial for identical panels
  - shuffles contextual/NSScreen indexes on every reconnect

Strategy: store NO screen IDs in config. Capture a known-good layout as
position "slots". At restore time, re-read live IDs from `displayplacer list`,
match screens to slots (identical screens tie-break to whichever is currently
nearest its target position), apply layout, then map NSScreen frames to slots
and apply each slot's wallpaper by live index.

Dependencies (Homebrew):
  brew install displayplacer
  brew install wallpaper        # sindresorhus/macos-wallpaper

Usage:
  mac_displays.py save             Snapshot current (correct) layout + wallpapers
  mac_displays.py restore          Re-apply saved layout + wallpapers
  mac_displays.py status           Show saved vs current, report drift
  mac_displays.py watch-check      Restore only if drifted (used by launchd agent)
  mac_displays.py install-agent    Install launchd agent (auto-restore on change)
  mac_displays.py uninstall-agent  Remove launchd agent
  mac_displays.py pause | resume   Temporarily disable/enable auto-restore
  mac_displays.py version          Print version
"""

VERSION = "2.0.0"

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "mac_displays_config.json")
PAUSE_FILE = os.path.expanduser("~/.mac_displays_paused")
LOG_PATH = os.path.expanduser("~/Library/Logs/mac_displays.log")
AGENT_LABEL = "com.quirkiest.mac_displays"
AGENT_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{AGENT_LABEL}.plist")
ORIGIN_TOLERANCE = 16  # px slack when comparing origins


# ---------------------------------------------------------------- utilities

def log(msg, also_print=True):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass
    if also_print:
        print(msg)


def run(cmd, check=True):
    """Run a command (list form), return stdout. Logs failures."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        log(f"ERROR running {' '.join(cmd)}: {result.stderr.strip()}")
    return result.stdout


def which(binary):
    return subprocess.run(["/usr/bin/which", binary], capture_output=True,
                          text=True).stdout.strip()


def check_deps():
    missing = [b for b in ("displayplacer", "wallpaper") if not which(b)]
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Install with: brew install " + " ".join(missing))
        sys.exit(1)


# ------------------------------------------------------- displayplacer parse

def parse_displayplacer_list():
    """Parse `displayplacer list` into a list of screen dicts (live IDs)."""
    output = run(["displayplacer", "list"])
    screens = []
    for section in output.split("Persistent screen id: ")[1:]:
        body = section.split("Resolutions for rotation")[0]
        screen = {"persistent_id": body.splitlines()[0].strip()}
        for line in body.splitlines()[1:]:
            if ": " not in line:
                continue
            key, value = line.split(": ", 1)
            key = key.strip().lower().replace(" ", "_")
            screen[key] = value.strip()
        m = re.search(r"\((-?\d+),(-?\d+)\)", screen.get("origin", ""))
        screen["x"], screen["y"] = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        res = screen.get("resolution", "0x0")
        screen["w"], screen["h"] = (int(v) for v in res.split("x"))
        screens.append(screen)
    return screens


# ----------------------------------------------------------- NSScreen frames

def nsscreen_frames():
    """Return [{index, x, y, w, h}] in displayplacer (top-left, y-down) coords.

    Index order matches NSScreen.screens, which is what `wallpaper --screen N`
    uses. JXA via osascript — no extra dependencies.
    """
    jxa = (
        'ObjC.import("AppKit");'
        'const s=$.NSScreen.screens;const o=[];'
        'const mh=s.objectAtIndex(0).frame.size.height;'
        'for(let i=0;i<s.count;i++){const f=s.objectAtIndex(i).frame;'
        'o.push({i:i,x:f.origin.x,y:mh-(f.origin.y+f.size.height),'
        'w:f.size.width,h:f.size.height});}'
        'JSON.stringify(o)'
    )
    out = run(["osascript", "-l", "JavaScript", "-e", jxa]).strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        log(f"ERROR parsing NSScreen frames: {out!r}")
        return []


# ----------------------------------------------------------------- wallpaper

def get_wallpaper(screen_index):
    return run(["wallpaper", "get", "--screen", str(screen_index)],
               check=False).strip()


def set_wallpaper(path, screen_index):
    if not path:
        return
    if not os.path.exists(path):
        log(f"WARN wallpaper file missing, skipped: {path}")
        return
    run(["wallpaper", "set", path, "--screen", str(screen_index)])


# -------------------------------------------------------------------- config

def slot_name(screen, index):
    if "macbook" in screen.get("type", "").lower():
        return "builtin"
    return f"external_{index}"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"No config found at {CONFIG_PATH}")
        print("Arrange your displays correctly, then run: mac_displays.py save")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def cmd_save():
    """Snapshot current layout + wallpapers into config."""
    screens = parse_displayplacer_list()
    frames = nsscreen_frames()

    slots = []
    ext_count = 0
    for screen in sorted(screens, key=lambda s: s["x"]):
        if "macbook" in screen.get("type", "").lower():
            name = "builtin"
        else:
            ext_count += 1
            name = f"external_{ext_count}"
        # find NSScreen index for this screen by matching origin (for wallpaper)
        ns_index = None
        for f in frames:
            if (abs(f["x"] - screen["x"]) <= ORIGIN_TOLERANCE
                    and abs(f["y"] - screen["y"]) <= ORIGIN_TOLERANCE):
                ns_index = f["i"]
                break
        wp = get_wallpaper(ns_index) if ns_index is not None else ""
        slots.append({
            "slot": name,
            "type": screen.get("type", ""),
            "serial_id": screen.get("serial_screen_id", ""),
            "resolution": screen.get("resolution", ""),
            "hertz": screen.get("hertz", ""),
            "color_depth": screen.get("color_depth", ""),
            "scaling": screen.get("scaling", "off"),
            "origin": f"({screen['x']},{screen['y']})",
            "degree": screen.get("rotation", "0"),
            "wallpaper": wp,
        })

    config = {
        "config_version": VERSION,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "slots": slots,
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    log(f"Saved {len(slots)} screen slots to {CONFIG_PATH}")
    for s in slots:
        print(f"  {s['slot']:<12} {s['resolution']:<10} origin {s['origin']:<14} "
              f"wallpaper: {os.path.basename(s['wallpaper']) or '(none)'}")


# ------------------------------------------------------------------ matching

def match_screens_to_slots(screens, slots):
    """Assign each live screen to a config slot.

    Score on stable-ish attributes (type, serial, resolution). Identical
    monitors tie — resolved by assigning whichever screen is currently nearest
    the slot's target origin (wallpaper follows position, not physical unit).
    Returns list of (screen, slot) pairs.
    """
    def target_xy(slot):
        m = re.search(r"\((-?\d+),(-?\d+)\)", slot["origin"])
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

    pairs = []
    candidates = []
    for screen in screens:
        for slot in slots:
            score = 0
            if slot["type"] and slot["type"] == screen.get("type", ""):
                score += 4
            if slot["serial_id"] and slot["serial_id"] == screen.get("serial_screen_id", ""):
                score += 2
            if slot["resolution"] and slot["resolution"] == screen.get("resolution", ""):
                score += 1
            tx, ty = target_xy(slot)
            dist = abs(screen["x"] - tx) + abs(screen["y"] - ty)
            candidates.append((-score, dist, screen["persistent_id"], slot["slot"],
                               screen, slot))

    # Greedy: best score first, then smallest distance (position tie-break),
    # then persistent id for full determinism.
    used_screens, used_slots = set(), set()
    for neg_score, dist, pid, sname, screen, slot in sorted(
            candidates, key=lambda c: (c[0], c[1], c[2], c[3])):
        if pid in used_screens or sname in used_slots:
            continue
        used_screens.add(pid)
        used_slots.add(sname)
        pairs.append((screen, slot))
    return pairs


# ------------------------------------------------------------------- restore

def build_displayplacer_args(pairs):
    args = []
    for screen, slot in pairs:
        part = (f"id:{screen['persistent_id']} "
                f"res:{slot['resolution']} ")
        if slot.get("hertz"):
            part += f"hz:{slot['hertz']} "
        if slot.get("color_depth"):
            part += f"color_depth:{slot['color_depth']} "
        part += (f"enabled:true scaling:{slot['scaling']} "
                 f"origin:{slot['origin']} degree:{slot['degree']}")
        args.append(part)
    return args


def apply_wallpapers(slots):
    """Map current NSScreen indexes to slots by position, set wallpapers."""
    frames = nsscreen_frames()
    for slot in slots:
        if not slot.get("wallpaper"):
            continue
        m = re.search(r"\((-?\d+),(-?\d+)\)", slot["origin"])
        tx, ty = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        best = min(frames, key=lambda f: abs(f["x"] - tx) + abs(f["y"] - ty),
                   default=None)
        if best is None:
            continue
        set_wallpaper(slot["wallpaper"], best["i"])
        log(f"Wallpaper '{os.path.basename(slot['wallpaper'])}' -> "
            f"screen index {best['i']} ({slot['slot']})", also_print=False)


def detect_drift(screens, slots):
    """True if screen count differs in a fixable way or any origin is off."""
    if len(screens) != len(slots):
        return None  # different display set attached — do not touch
    pairs = match_screens_to_slots(screens, slots)
    for screen, slot in pairs:
        m = re.search(r"\((-?\d+),(-?\d+)\)", slot["origin"])
        tx, ty = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        if (abs(screen["x"] - tx) > ORIGIN_TOLERANCE
                or abs(screen["y"] - ty) > ORIGIN_TOLERANCE
                or screen.get("resolution") != slot["resolution"]):
            return True
    return False


def cmd_restore(force=True):
    config = load_config()
    slots = config["slots"]
    screens = parse_displayplacer_list()

    if len(screens) != len(slots):
        log(f"Screen count mismatch (live {len(screens)} vs saved {len(slots)}) "
            "— not restoring. Re-run 'save' if your setup changed.")
        return False

    pairs = match_screens_to_slots(screens, slots)
    args = build_displayplacer_args(pairs)
    log("Applying layout: displayplacer " + " ".join(f'"{a}"' for a in args),
        also_print=False)
    run(["displayplacer"] + args)
    time.sleep(2)  # let WindowServer settle before reading NSScreen
    apply_wallpapers(slots)
    log("Restore complete.")
    return True


def cmd_status():
    print(f"mac_displays v{VERSION}")
    config = load_config()
    slots = config["slots"]
    screens = parse_displayplacer_list()
    print(f"Config: {CONFIG_PATH} (saved {config.get('saved_at', '?')})")
    print(f"Saved slots: {len(slots)} | Live screens: {len(screens)}")
    drift = detect_drift(screens, slots)
    if drift is None:
        print("Different display set attached — auto-restore inactive.")
    elif drift:
        print("DRIFT DETECTED — layout differs from saved config.")
    else:
        print("Layout matches saved config.")
    if os.path.exists(PAUSE_FILE):
        print("Auto-restore is PAUSED (run 'resume' to re-enable).")


def cmd_watch_check():
    """Called by launchd. Restore only when drifted and not paused."""
    if os.path.exists(PAUSE_FILE):
        return
    config = load_config()
    screens = parse_displayplacer_list()
    drift = detect_drift(screens, config["slots"])
    if drift:
        log("Drift detected by watcher — restoring.", also_print=False)
        cmd_restore()
    # Wallpaper-only drift check (cheap): origins fine but wallpaper swapped
    elif drift is False:
        apply_wallpapers(config["slots"])


# ------------------------------------------------------------- launchd agent

AGENT_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>{script}</string>
        <string>watch-check</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StartInterval</key>
    <integer>30</integer>
    <key>WatchPaths</key>
    <array>
        <string>{byhost}</string>
    </array>
    <key>StandardOutPath</key>
    <string>{log}</string>
    <key>StandardErrorPath</key>
    <string>{log}</string>
</dict>
</plist>
"""


def cmd_install_agent():
    python = sys.executable or "/usr/bin/python3"
    plist = AGENT_TEMPLATE.format(
        label=AGENT_LABEL,
        python=python,
        script=os.path.abspath(__file__),
        byhost=os.path.expanduser("~/Library/Preferences/ByHost"),
        log=LOG_PATH,
    )
    os.makedirs(os.path.dirname(AGENT_PATH), exist_ok=True)
    with open(AGENT_PATH, "w") as f:
        f.write(plist)
    subprocess.run(["launchctl", "unload", AGENT_PATH], capture_output=True)
    subprocess.run(["launchctl", "load", AGENT_PATH], capture_output=True)
    log(f"Agent installed and loaded: {AGENT_PATH}")
    print("Auto-restore active: checks every 30s + on display-config changes.")
    print("Use 'pause'/'resume' to toggle, 'uninstall-agent' to remove.")


def cmd_uninstall_agent():
    subprocess.run(["launchctl", "unload", AGENT_PATH], capture_output=True)
    if os.path.exists(AGENT_PATH):
        os.remove(AGENT_PATH)
    log("Agent uninstalled.")


# ---------------------------------------------------------------------- main

def main():
    print(f"mac_displays v{VERSION}", file=sys.stderr)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "restore"
    if cmd in ("version", "--version", "-v"):
        print(VERSION)
        return
    check_deps()
    if cmd == "save":
        cmd_save()
    elif cmd == "restore":
        cmd_restore()
    elif cmd == "status":
        cmd_status()
    elif cmd == "watch-check":
        cmd_watch_check()
    elif cmd == "install-agent":
        cmd_install_agent()
    elif cmd == "uninstall-agent":
        cmd_uninstall_agent()
    elif cmd == "pause":
        open(PAUSE_FILE, "w").close()
        print("Auto-restore paused.")
    elif cmd == "resume":
        if os.path.exists(PAUSE_FILE):
            os.remove(PAUSE_FILE)
        print("Auto-restore resumed.")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
