#!/usr/bin/env bash

# Waywallen 0.2.5 exposes a StatusNotifierItem but does not register it with
# Noctalia's watcher. Wait for both peers, then register the stable bus name.
for attempt in {1..100}; do
    if busctl --user --quiet call \
        org.freedesktop.DBus \
        /org/freedesktop/DBus \
        org.freedesktop.DBus \
        GetNameOwner \
        s org.waywallen.waywallen.Daemon 2>/dev/null && \
       busctl --user --quiet call \
        org.freedesktop.DBus \
        /org/freedesktop/DBus \
        org.freedesktop.DBus \
        GetNameOwner \
        s org.kde.StatusNotifierWatcher 2>/dev/null; then
        if busctl --user --quiet call \
            org.kde.StatusNotifierWatcher \
            /StatusNotifierWatcher \
            org.kde.StatusNotifierWatcher \
            RegisterStatusNotifierItem \
            s org.waywallen.waywallen.Daemon 2>/dev/null; then
            exit 0
        fi
    fi
    sleep 0.1
done

echo "niri-autostart: could not register the Waywallen tray icon" >&2
exit 0
