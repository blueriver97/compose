#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# run_ollama.sh
#
#   • Starts Ollama on a single RTX‑4090 (24 GB VRAM).
#   • Uses flash‑attention, sets a generous keep‑alive, and limits
#     the number of loaded models to avoid VRAM thrashing.
#   • Exposes the server on all interfaces (0.0.0.0) – change if you
#     want it bound only to localhost.
#   ──────────────────────────────────────────────────────────────────────
#  (c) 2025 by <your‑name> – MIT‑style license (see README if you plan
#  to distribute this script).  Happy LLM-ing! 🚀
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail   # safest Bash defaults

# ------------------------------------------------------------
#  1️⃣  Environment variables – tweak as needed
# ------------------------------------------------------------
export OLLAMA_DEBUG=0                             # 1 for verbose debugging, 0 for normal
export OLLAMA_HOST=0.0.0.0:11434                  # bind to all interfaces
export OLLAMA_KEEP_ALIVE=60m                      # keep a model loaded for 10 min after idle
export OLLAMA_MAX_LOADED_MODELS=1                 # 1–2 models is safe on 24 GB
export OLLAMA_MAX_QUEUE=32                        # max queued requests (higher = more back‑pressure)
export OLLAMA_NUM_PARALLEL=1                      # parallel requests that can run simultaneously
export OLLAMA_ORIGINS="*"                         # allow all CORS origins (replace if you want tighter control)
export OLLAMA_FLASH_ATTENTION=1                   # enable flash‑attention (requires CUDA 12+)
export OLLAMA_KV_CACHE_TYPE="f16"                 # memory‑efficient K/V cache
export OLLAMA_GPU_OVERHEAD=$((2*1024*1024*1024))  # reserve 2 GB for overhead (bytes)
export OLLAMA_MODELS="/home/kimyj/.ollama/models" # where Ollama stores its models
export OLLAMA_SCHED_SPREAD=0                      # not needed for a single GPU
export OLLAMA_LLM_LIBRARY="llama.cpp"             # you can also use "vllm" if you have it

# ------------------------------------------------------------
#  2️⃣  Make sure the model directory exists & has the right perms
# ------------------------------------------------------------
mkdir -p "$OLLAMA_MODELS"
chmod 700 "$OLLAMA_MODELS"

# ------------------------------------------------------------
#  3️⃣  Optionally pre‑load a model (e.g. 7B or 13B) – uncomment if you want a warm start
# ------------------------------------------------------------
# echo "Pre‑loading model 'gpt-oss:20b'..."
# ollama pull gpt-oss:20b
# echo "✅  Model loaded"

# ------------------------------------------------------------
#  4️⃣  Launch Ollama
# ------------------------------------------------------------
echo "🟢 Starting Ollama server on ${OLLAMA_HOST}"
echo "🟢 Keep‑alive: ${OLLAMA_KEEP_ALIVE}"
echo "🟢 Max loaded models: ${OLLAMA_MAX_LOADED_MODELS}"
echo "🟢 Flash attention: ${OLLAMA_FLASH_ATTENTION}"
echo "🟢 GPU overhead: ${OLLAMA_GPU_OVERHEAD} bytes"

# Run the server in the foreground; you can add '&' to background it
mkdir -p ~/.ollama/logs
ollama serve > ~/.ollama/logs/ollama.log 2>&1 &

# ------------------------------------------------------------
#  5️⃣  Graceful shutdown handling (Ctrl‑C)
# ------------------------------------------------------------
# When the script exits (via SIGINT or other), Ollama will terminate automatically.
# No explicit cleanup needed – the server will free VRAM on exit.
