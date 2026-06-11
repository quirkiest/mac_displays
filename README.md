# mac_displays v2.0.2

Restores monitor arrangement and per-position wallpapers on macOS. Built specifically for setups with **identical external monitors**, where macOS (tested on Tahoe 26.x, M1):

- regenerates "persistent" screen UUIDs after sleep/replug race conditions
- reports the **same serial number** for identical panels (so serial-based matching fails)
- shuffles contextual/NSScreen indexes on every reconnect (so `wallpaper --screen N` binds to the wrong monitor)

## How v2 solves it

v1 stored screen IDs in config and matched against them — every ID type macOS offers is unstable for identical monitors. v2 stores **no IDs at all**:

1. `save` snapshots your current correct layout as position *slots* (builtin, external_1, external_2) with resolution, origin, scaling, and the wallpaper currently on each position.
2. `restore` re-reads live IDs from `displayplacer list`, matches screens to slots by type/serial/resolution, and breaks ties between identical monitors by whichever screen is currently nearest its target position. Since the monitors are physically identical, the wallpaper follows the *position* — which is what you actually perceive.
3. Wallpapers are applied by mapping live NSScreen frames (via JXA, no extra deps) to slot positions, so the index is always correct at the moment of application.

## Dependencies

```sh
brew install displayplacer
brew install wallpaper
```

## Usage

```sh
# One-time: arrange displays + wallpapers correctly, then
./mac_displays.py save

# When macOS shuffles things
./mac_displays.py restore

# Set and forget: auto-restore on display-config changes (checks every 30s
# + watches ~/Library/Preferences/ByHost for WindowServer rewrites)
./mac_displays.py install-agent

# Other commands
./mac_displays.py status            # saved vs live, drift report
./mac_displays.py pause | resume    # toggle auto-restore (e.g. when presenting)
./mac_displays.py uninstall-agent
./mac_displays.py version
```

## Notes

- Config lives in `mac_displays_config.json` next to the script (written by `save` — no hand-editing needed). The v1 `mac_displays_params.json` is no longer used.
- If a different set of displays is attached (count mismatch), restore and the watcher do nothing — they never fight a setup you haven't saved.
- Logs: `~/Library/Logs/mac_displays.log`
- Agent: `~/Library/LaunchAgents/com.quirkiest.mac_displays.plist`

## Version history

- **2.0.2** — Silence version banner for `watch-check` so the launchd log isn't flooded every 30s.
- **2.0.1** — Fix: launchd agent couldn't find Homebrew binaries (bare launchd PATH) — binaries now resolved to absolute paths + PATH set in agent plist. Fix: `Rotation:`/help-text suffixes from `displayplacer list` corrupted saved degree value. Watcher now only re-sets wallpapers that differ (no churn).
- **2.0.0** — Full rewrite: ID-free slot matching for identical monitors, `save` snapshot command, NSScreen-frame wallpaper mapping, launchd auto-restore agent, drift detection, pause/resume, logging.
- **1.x** — Serial-ID based matching (broken for identical monitors).
