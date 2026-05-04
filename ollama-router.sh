#!/usr/bin/env bash
# ollama-router.sh — use Jetson Nano GPU if reachable, else fall back to Pi CPU

JETSON_HOST="192.168.254.50"   # <-- update to your Jetson's IP
JETSON_PORT="11434"
LOCAL_HOST="127.0.0.1"
LOCAL_PORT="11434"

check_ollama() {
    local host=$1 port=$2
    curl -sf --max-time 2 "http://${host}:${port}/api/tags" > /dev/null 2>&1
}

if check_ollama "$JETSON_HOST" "$JETSON_PORT"; then
    echo "Using Jetson Nano GPU → http://${JETSON_HOST}:${JETSON_PORT}"
    export OLLAMA_HOST="http://${JETSON_HOST}:${JETSON_PORT}"
else
    echo "Jetson not reachable — using Pi CPU → http://${LOCAL_HOST}:${LOCAL_PORT}"
    export OLLAMA_HOST="http://${LOCAL_HOST}:${LOCAL_PORT}"
fi

# Default model based on backend
if [[ "$OLLAMA_HOST" == *"$JETSON_HOST"* ]]; then
    DEFAULT_MODEL="qwen2.5-coder:7b"
else
    DEFAULT_MODEL="llama3.2:3b"
fi

# If no args given, drop into chat with the appropriate default model
if [[ $# -eq 0 ]]; then
    exec ollama run "$DEFAULT_MODEL"
else
    exec ollama "$@"
fi
