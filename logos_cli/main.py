#!/usr/bin/env python3
"""Logos — local coding assistant terminal REPL backed by Ollama."""

import argparse
import itertools
import json
import os
import sys
import threading
import time
from pathlib import Path

import requests
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich.theme import Theme

ALLOWED_MODELS = ["gemma3:4b", "gemma3:12b", "qwen2.5-coder:7b", "qwen2.5-coder:14b", "phi4"]

SYSTEM_PROMPT = (
    "You are Logos, a senior software engineer assistant running locally. "
    "You help with code, debugging, architecture, and technical explanations. "
    "Be concise and precise. Prefer code over prose. "
    "When showing code, always use fenced markdown code blocks with the language tag."
)

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

THINKING_PHRASES = itertools.cycle([
    "thinking",
    "reasoning",
    "processing",
    "analyzing",
    "working on it",
    "crafting response",
    "thinking",
    "computing",
])

theme = Theme({
    "logos.brand":  "bold cyan",
    "logos.dim":    "color(240)",
    "logos.model":  "cyan",
    "logos.border": "cyan",
    "logos.prompt": "bold cyan",
    "logos.time":   "color(67)",
    "logos.think":  "color(67) italic",
    "logos.ok":     "bold green",
    "logos.warn":   "bold yellow",
    "logos.err":    "bold red",
    "logos.rule":   "color(24)",
})

console = Console(theme=theme)


def load_profile(profiles_dir: str, model: str) -> dict:
    base = model.split(":")[0]
    path = Path(profiles_dir) / f"{base}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"temperature": 0.2}


def stream_response(ollama_url: str, model: str, messages: list, params: dict) -> tuple[str, float]:
    """Stream chat completion with a live-updating display throughout. Returns (text, elapsed)."""
    url = f"{ollama_url}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {k: params[k] for k in ("temperature", "top_p") if k in params},
    }
    if "context_window" in params:
        payload["options"]["num_ctx"] = params["context_window"]
    elif "num_ctx" in params:
        payload["options"]["num_ctx"] = params["num_ctx"]

    t_start = time.monotonic()
    chunks: list[str] = []
    thinking = True

    # Spinner frame is advanced by a background thread so it ticks independently
    # of how often Live refreshes.
    frame_ref = [0]
    phrase_ref = [next(THINKING_PHRASES)]
    phrase_tick = [0]
    stop_frame = threading.Event()

    def _advance():
        while not stop_frame.is_set():
            frame_ref[0] = (frame_ref[0] + 1) % len(SPINNER_FRAMES)
            phrase_tick[0] += 1
            if phrase_tick[0] % 30 == 0:  # change phrase every ~3 s
                phrase_ref[0] = next(THINKING_PHRASES)
            time.sleep(0.1)

    frame_thread = threading.Thread(target=_advance, daemon=True)
    frame_thread.start()

    def make_display() -> object:
        elapsed = time.monotonic() - t_start
        time_tag = f"[color(67)]{elapsed:.1f}s[/color(67)]"

        if thinking:
            frame = SPINNER_FRAMES[frame_ref[0]]
            return Text.from_markup(
                f"\n  [cyan]{frame}[/cyan] [logos.think]{phrase_ref[0]}...[/logos.think]"
                f"  {time_tag}\n"
            )

        content = "".join(chunks)
        try:
            body = Markdown(content)
        except Exception:
            body = Text(content)

        return Group(
            body,
            Text.from_markup(f"\n  [logos.dim]⏱[/logos.dim]  {time_tag}\n"),
        )

    error_msg: list[str] = []
    stop_refresh = threading.Event()

    def _refresh_loop(live: Live):
        while not stop_refresh.is_set():
            live.update(make_display())
            time.sleep(0.1)

    try:
        with Live(
            make_display(),
            console=console,
            refresh_per_second=10,
            vertical_overflow="visible",
            transient=False,
        ) as live:
            refresh_thread = threading.Thread(target=_refresh_loop, args=(live,), daemon=True)
            refresh_thread.start()

            with requests.post(url, json=payload, stream=True, timeout=300) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        if thinking:
                            thinking = False
                        chunks.append(chunk)
                    if data.get("done"):
                        break

            stop_refresh.set()
            refresh_thread.join()
            live.update(make_display())

    except requests.exceptions.ConnectionError:
        error_msg.append(
            "[logos.err]✗ Cannot connect to Ollama[/logos.err] "
            f"at [logos.dim]{ollama_url}[/logos.dim]\n"
            "  Run: [logos.model]docker compose up -d[/logos.model]"
        )
    except requests.exceptions.HTTPError as e:
        error_msg.append(f"[logos.err]✗ Ollama API error:[/logos.err] {e}")
    finally:
        stop_refresh.set()
        stop_frame.set()
        frame_thread.join()

    if error_msg:
        console.print(f"\n{error_msg[0]}")
        return "", 0.0

    elapsed = time.monotonic() - t_start
    return "".join(chunks), elapsed


def check_ollama(ollama_url: str, model: str) -> bool:
    try:
        resp = requests.get(f"{ollama_url}/api/tags", timeout=5)
        resp.raise_for_status()
        tags = [m["name"] for m in resp.json().get("models", [])]
        if model not in tags:
            console.print(
                f"[logos.warn]⚠  Model [logos.model]{model}[/logos.model] not cached yet[/logos.warn]"
                " — responses will start once the pull completes."
            )
        return True
    except Exception:
        return False


def build_key_bindings() -> KeyBindings:
    kb = KeyBindings()

    @kb.add("c-c")
    def _(event):
        event.app.exit(result=None)

    return kb


def print_header(model: str, ollama_url: str):
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                f"  [logos.brand]LOGOS[/logos.brand]   "
                f"[logos.dim]The hypernote's coding assistant[/logos.dim]\n\n"
                f"  [logos.dim]model[/logos.dim]    [logos.model]{model}[/logos.model]\n"
                f"  [logos.dim]backend[/logos.dim]  [logos.dim]{ollama_url}[/logos.dim]\n\n"
                f"  [logos.dim]/clear  /model  /help  /quit  ·  Ctrl+C to exit[/logos.dim]"
            ),
            border_style="logos.border",
            padding=(0, 1),
        )
    )
    console.print()


def run_repl(model: str, ollama_url: str, profiles_dir: str, skip_permissions: bool):
    params = load_profile(profiles_dir, model)

    history_path = Path.home() / ".logos_history"
    session = PromptSession(
        history=FileHistory(str(history_path)),
        key_bindings=build_key_bindings(),
        style=Style.from_dict({"prompt": "bold cyan"}),
        multiline=False,
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print_header(model, ollama_url)

    if not check_ollama(ollama_url, model):
        console.print(
            "[logos.err]✗ Ollama not reachable[/logos.err] "
            f"at [logos.dim]{ollama_url}[/logos.dim]\n"
            "  Start the stack: [logos.model]docker compose up -d[/logos.model]"
        )
        if not skip_permissions:
            sys.exit(1)

    turn = 0
    while True:
        try:
            console.print(Rule(style="logos.rule"))
            user_input = session.prompt("  ❯ ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[logos.dim]  bye.[/logos.dim]\n")
            break

        if user_input is None or user_input.strip() == "":
            continue

        text = user_input.strip()

        if text in ("/quit", "/exit", "exit", "quit"):
            console.print("[logos.dim]  bye.[/logos.dim]\n")
            break

        if text == "/clear":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            turn = 0
            console.clear()
            print_header(model, ollama_url)
            console.print("[logos.dim]  context cleared[/logos.dim]")
            continue

        if text == "/model":
            console.print(f"  [logos.dim]active model[/logos.dim]  [logos.model]{model}[/logos.model]")
            continue

        if text == "/help":
            console.print(
                Panel(
                    Text.from_markup(
                        "  [logos.dim]/clear[/logos.dim]   reset conversation context\n"
                        "  [logos.dim]/model[/logos.dim]   show active model\n"
                        "  [logos.dim]/quit[/logos.dim]    exit\n"
                        "  [logos.dim]Ctrl+C[/logos.dim]  exit"
                    ),
                    border_style="logos.border",
                    title="[logos.dim]help[/logos.dim]",
                    title_align="left",
                    padding=(0, 1),
                )
            )
            continue

        turn += 1
        messages.append({"role": "user", "content": text})
        response, elapsed = stream_response(ollama_url, model, messages, params)

        if response:
            messages.append({"role": "assistant", "content": response})
            console.print(
                f"  [logos.time]⏱  {elapsed:.1f}s[/logos.time]  "
                f"[logos.dim]·  turn {turn}  ·  {len(response)} chars[/logos.dim]"
            )


def main():
    parser = argparse.ArgumentParser(
        prog="logos",
        description="Logos — local AI coding assistant",
    )
    parser.add_argument("--model", default=os.environ.get("MODEL", "gemma3:4b"))
    parser.add_argument(
        "--ollama-url", default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    parser.add_argument("--profiles-dir", default="profiles")
    parser.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Skip permission/connectivity checks (mirrors Claude Code flag)",
    )
    args = parser.parse_args()

    model = args.model.strip()

    if model not in ALLOWED_MODELS:
        console.print(f"\n[logos.err]✗ Unsupported model:[/logos.err] [bold]{model}[/bold]\n")
        console.print("  Allowed models:")
        for m in ALLOWED_MODELS:
            console.print(f"  [logos.dim]·[/logos.dim] [logos.model]{m}[/logos.model]")
        sys.exit(1)

    run_repl(
        model=model,
        ollama_url=args.ollama_url,
        profiles_dir=args.profiles_dir,
        skip_permissions=args.dangerously_skip_permissions,
    )


if __name__ == "__main__":
    main()
