# Logos

**The Hypernote's coding assistant** — a local, model-agnostic coding stack for Apple Silicon, built on [Ollama](https://ollama.com) and [Open WebUI](https://github.com/open-webui/open-webui).

One command to start everything:

```bash
docker compose up -d
```

A terminal interface that feels like working with a senior engineer, running entirely on your machine. No cloud. No API keys. No data leaving your device. No monthly subscription to cancel and forget about.

---

## Features

- **Model-agnostic** — swap models at runtime, no rebuild required
- **Auto-pull** — missing models are downloaded automatically on first run (yes, it does the boring part for you)
- **Model profiles** — per-model tuning (temperature, context window, top_p)
- **M2 memory protection** — 14b models automatically enforce single-load constraints, because your laptop is not a data center
- **Terminal REPL** — streaming responses with live elapsed timer, thinking indicator, conversation history
- **Web UI** — Open WebUI on `http://localhost:3000`, for when the terminal feels too intimidating

---

## Supported Models

| Model | Tag | Notes |
|---|---|---|
| Gemma 3 | `gemma3:4b` | Default. Fast, great for general coding |
| Gemma 3 | `gemma3:12b` | Higher quality, needs ~10GB RAM |
| Qwen 2.5 Coder | `qwen2.5-coder:7b` | Strong code generation |
| Qwen 2.5 Coder | `qwen2.5-coder:14b` | Best output, 16GB RAM recommended (you were warned) |
| Phi-4 | `phi4` | Lightweight fallback for when you pushed your luck with the 14b |

---

## Requirements

- Docker Desktop (Apple Silicon)
- Python 3.9+
- ~4–15 GB free disk per model (clean up those node_modules first)

---

## Getting Started

### 1. Clone

```bash
git clone https://github.com/hypernote/logos.ai.git
cd logos.ai
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

Go make a coffee. It's a big file.

### 4. Open Web UI

```
http://localhost:3000
```

### 5. Install terminal CLI

```bash
./install.sh
```

Supports macOS and Linux. Works without `sudo` because we're not animals.

If needed, add to your shell:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 6. Start the terminal interface

```bash
logos --dangerously-skip-permissions
```

The flag name is borrowed from Claude Code. We kept it because it sounds cool.

---

## Switching Models

**One-time:**

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
| `/clear` | Reset conversation context (fresh start, no judgment) |
| `/model` | Show active model |
| `/help` | Show commands |
| `/quit` | Exit |
| `Ctrl+C` | Exit, slightly more dramatically |

---

## Project Structure

```
logos/
├── .env                    # Active model config (not committed, you're welcome)
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

Because loading two 14b models simultaneously on 16GB of RAM is the kind of optimism that ends in a spinning beachball and regret.

If memory is critically low, the container logs a suggestion:

```
WARNING: Low memory detected.
Recommended fallback: MODEL=qwen2.5-coder:7b
```

---

## License

[Buy Me a Beer License](LICENSE) — free to use, forever. If it saved you an hour of Stack Overflow, consider sending some sats:

⚡ `slowcoke39@walletofsatoshi.com`
