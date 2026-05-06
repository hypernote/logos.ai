#!/bin/bash

ALLOWED_MODELS=("gemma3:4b" "gemma3:12b" "qwen2.5-coder:7b" "qwen2.5-coder:14b" "phi4")
MODEL="${MODEL:-gemma3:4b}"

# Validate model against allowlist
valid=false
for m in "${ALLOWED_MODELS[@]}"; do
  if [[ "$m" == "$MODEL" ]]; then
    valid=true
    break
  fi
done

if [[ "$valid" != "true" ]]; then
  echo ""
  echo "ERROR: Unsupported model: '$MODEL'"
  echo ""
  echo "Allowed models:"
  for m in "${ALLOWED_MODELS[@]}"; do
    echo "  - $m"
  done
  echo ""
  exit 1
fi

# M2 memory protection for 14b models
if [[ "$MODEL" == *"14b"* ]]; then
  export OLLAMA_NUM_PARALLEL=1
  export OLLAMA_MAX_LOADED_MODELS=1
  echo "INFO: 14b model detected — memory protection enabled (NUM_PARALLEL=1, MAX_LOADED_MODELS=1)"
fi

echo "INFO: Starting Ollama with model: $MODEL"

# Start ollama server in background
ollama serve &
OLLAMA_PID=$!

# Wait for server to be ready
echo "INFO: Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
  if ollama list > /dev/null 2>&1; then
    echo "INFO: Ollama is ready."
    break
  fi
  sleep 2
done

# Check if model is already pulled
if ollama list 2>/dev/null | grep -qF "${MODEL}"; then
  echo "INFO: Model '$MODEL' already present."
else
  echo "INFO: Model '$MODEL' not found — pulling now..."
  if ollama pull "$MODEL"; then
    echo "INFO: Pull complete."
  else
    echo "ERROR: Failed to pull '$MODEL'. Check network connectivity."
    echo "INFO: Ollama will remain running; pull the model manually with:"
    echo "       docker exec logos-ollama ollama pull $MODEL"
  fi
fi

# Check memory pressure
if [[ -f /proc/meminfo ]]; then
  available_kb=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
  if [[ -n "$available_kb" && "$available_kb" -lt 4194304 ]]; then
    echo ""
    echo "WARNING: Low memory detected."
    echo "Recommended fallback: MODEL=qwen2.5-coder:7b"
    echo ""
  fi
fi

# Wait for ollama process
wait "$OLLAMA_PID"
