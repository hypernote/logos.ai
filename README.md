# Logos

**The Hypernote's coding assistant** — a local, model-agnostic coding stack for Apple Silicon, built on [Ollama](https://ollama.com) and [Open WebUI](https://github.com/open-webui/open-webui).

One command to start everything:

```bash
docker compose up -d
```

A terminal interface that feels like working with a senior engineer, running entirely on your machine. No cloud. No API keys. No data leaving your device.

---

## Features

- **Model-agnostic** — swap models at runtime, no rebuild required
- **Auto-pull** — missing models are downloaded automatically on first run
- **Model profiles** — per-model tuning (temperature, context window, top_p)
- **M2 memory protection** — 14b models automatically enforce single-load constraints
- **Terminal REPL** — streaming responses with live elapsed timer, thinking indicator, conversation history
- **Web UI** — Open WebUI on `http://localhost:3000`

---

## Supported Models

| Model | Tag | Notes |
|---|---|---|
| Gemma 3 | `gemma3:4b` | Default. Fast, great for general coding |
| Gemma 3 | `gemma3:12b` | Higher quality, needs ~10GB RAM |
| Qwen 2.5 Coder | `qwen2.5-coder:7b` | Strong code generation |
| Qwen 2.5 Coder | `qwen2.5-coder:14b` | Best output, 16GB RAM recommended |
| Phi-4 | `phi4` | Lightweight fallback |

---

## Requirements

- Docker Desktop (Apple Silicon)
- Python 3.9+
- ~4–15 GB free disk per model

---

## Getting Started

### 1. Clone

```bash
git clone https://github.com/your-username/logos.git
cd logos
```

### 2. Configure model

Edit `.env`:

```bash
MODEL=gemma3:4b
```

Or override at runtime:

```bash
MODEL=qwen2.5-coder:7b docker compose up -d
```

### 3. Start the stack

```bash
docker compose up -d
```

On first run, Ollama pulls the configured model automatically. Watch the progress:

```bash
docker logs -f logos-ollama
```

### 4. Open Web UI

```
http://localhost:3000
```

### 5. Install terminal CLI

```bash
./install.sh
```

This creates `~/.local/bin/logos` (no sudo required). If needed, add to your shell:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 6. Start the terminal interface

```bash
logos --dangerously-skip-permissions
```

---

## Switching Models

**One-time (current session):**

```bash
MODEL=gemma3:12b docker compose up -d
```

**Permanent:**

```bash
sed -i '' 's/MODEL=.*/MODEL=qwen2.5-coder:7b/' .env
docker compose down && docker compose up -d
```

---

## Terminal REPL Commands

| Command | Description |
|---|---|
| `/clear` | Reset conversation context |
| `/model` | Show active model |
| `/help` | Show commands |
| `/quit` | Exit |
| `Ctrl+C` | Exit |

---

## Project Structure

```
logos/
├── .env                    # Active model config
├── docker-compose.yml      # Ollama + Open WebUI services
├── install.sh              # CLI installer (no sudo)
├── requirements.txt        # Python dependencies
├── bin/
│   └── logos               # Shell entrypoint
├── logos_cli/
│   └── main.py             # Terminal REPL
├── ollama/
│   └── entrypoint.sh       # Model validation, auto-pull, memory protection
└── profiles/
    ├── gemma3.json          # Gemma generation params
    ├── qwen2.5-coder.json   # Qwen generation params
    └── phi4.json            # Phi-4 generation params
```

---

## Memory Protection (M2 16GB)

When a `14b` model is selected, the stack automatically sets:

```
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
```

If system memory is low, the container logs a fallback recommendation:

```
WARNING: Low memory detected.
Recommended fallback: MODEL=qwen2.5-coder:7b
```

---

## License

[Buy Me a Beer License](LICENSE) — free to use. If it helped you, consider sending some sats:

⚡ `slowcoke39@walletofsatoshi.com`
