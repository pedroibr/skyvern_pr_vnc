#!/bin/bash
# Start VNC streaming services for Skyvern
#
# This script sets up the complete VNC streaming stack:
# - Xvfb (virtual X11 display)
# - x11vnc (VNC server for the display)
# - websockify (WebSocket-to-VNC proxy)

set -euo pipefail

readonly SCREEN_GEOMETRY="1920x1080x24"
readonly DISPLAY_BASE="${SKYVERN_STREAM_BASE_DISPLAY:-99}"
readonly MAX_SESSIONS="${SKYVERN_STREAM_MAX_SESSIONS:-10}"
readonly VNC_BASE_PORT="${SKYVERN_STREAM_BASE_VNC_PORT:-5900}"
readonly WS_BASE_PORT="${SKYVERN_STREAM_BASE_WS_PORT:-6080}"
readonly NOVNC_WEB_DIR="/usr/share/novnc"

log() {
    printf '%s\n' "$*"
}

is_running_exact() {
    local process_name="$1"
    pgrep -x "$process_name" > /dev/null 2>&1
}

is_running_match() {
    local pattern="$1"
    pgrep -f "$pattern" > /dev/null 2>&1
}

ensure_running() {
    local service_label="$1"
    local running_check_type="$2"  # "exact" | "match"
    local check_value="$3"
    local start_cmd="$4"

    if [[ "$running_check_type" == "exact" ]]; then
        if is_running_exact "$check_value"; then
            log "$service_label already running"
            return 0
        fi
    else
        if is_running_match "$check_value"; then
            log "$service_label already running"
            return 0
        fi
    fi

    log "Service $service_label not running. Starting..."
    eval "$start_cmd"
    log "$service_label started"
}

log "Starting VNC streaming services for Skyvern..."
log ""

for ((i=0; i<MAX_SESSIONS; i++)); do
  display=":$((DISPLAY_BASE + i))"
  vnc_port="$((VNC_BASE_PORT + i))"
  ws_port="$((WS_BASE_PORT + i))"

  ensure_running \
    "Xvfb ${display}" "match" "Xvfb ${display}" \
    "Xvfb ${display} -screen 0 ${SCREEN_GEOMETRY} > /dev/null 2>&1 &"

  ensure_running \
    "x11vnc ${display}" "match" "x11vnc.*${display}" \
    "x11vnc -display ${display} -bg -nopw -listen localhost -xkb -forever -shared -rfbport ${vnc_port} > /dev/null 2>&1"

  ensure_running \
    "websockify ${ws_port}" "match" "websockify.*${ws_port}" \
    "websockify ${ws_port} localhost:${vnc_port} --web ${NOVNC_WEB_DIR} --daemon > /dev/null 2>&1"
done

log ""
log "🎉 VNC streaming services are now running!"
log ""
log "Configuration:"
log "  - Displays: :${DISPLAY_BASE}..:$((DISPLAY_BASE + MAX_SESSIONS - 1))"
log "  - VNC ports: ${VNC_BASE_PORT}..$((VNC_BASE_PORT + MAX_SESSIONS - 1))"
log "  - WebSocket ports: ${WS_BASE_PORT}..$((WS_BASE_PORT + MAX_SESSIONS - 1))"
log ""
log "To stop services:"
log "  pkill x11vnc && pkill websockify"
