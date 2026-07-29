#!/usr/bin/env bash

if [[ -z ${XDG_RUNTIME_DIR:-} ]]; then
    echo "niri-autostart: XDG_RUNTIME_DIR is not set for Waywallen" >&2
    exit 1
fi

socket_path="$XDG_RUNTIME_DIR/waywallen/display.sock"

# The user service owns the layer-shell process. Reuse an existing Flatpak
# daemon if one is already alive, otherwise launch exactly one instance.
if ! /usr/bin/flatpak ps --columns=application 2>/dev/null | \
    /usr/bin/grep -Fxq org.waywallen.waywallen; then
    /usr/bin/flatpak run org.waywallen.waywallen --no-ui &
fi

for ((attempt = 0; attempt < 300; attempt++)); do
    if [[ -S $socket_path ]]; then
        exec /usr/bin/waywallen-layer-shell --socket "$socket_path"
    fi
    sleep 0.1
done

echo "niri-autostart: Waywallen display socket was not ready after 30 seconds" >&2
exit 1
