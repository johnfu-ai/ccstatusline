#!/usr/bin/env python3
"""Claude Code status line: model, effort, context-window bar + %, cost, dir, git branch.

Reads the session JSON payload from stdin (see
https://code.claude.com/docs/en/statusline for the schema). Fields can be
absent or null early in a session; every segment degrades gracefully.
"""
import json
import os
import subprocess
import sys
import time

GREEN, YELLOW, RED = "\033[32m", "\033[33m", "\033[31m"
CYAN, MAGENTA, DIM, RESET = "\033[36m", "\033[35m", "\033[2m", "\033[0m"
SEP = DIM + " │ " + RESET
BAR_WIDTH = 20


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def context_color(pct):
    if pct >= 90:
        return RED
    if pct >= 70:
        return YELLOW
    return GREEN


def fallback_usage(data):
    """(used_tokens, window) computed from the transcript, when the payload's
    context_window fields are missing/null (before the first API call, or an
    older payload shape). Returns (None, None) if nothing can be computed."""
    model_id = (data.get("model") or {}).get("id") or ""
    window = 1_000_000 if "[1m]" in model_id else int(
        os.environ.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW") or 200000)
    path = data.get("transcript_path")
    if not path:
        return None, window
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 262144))  # last 256KB is plenty
            lines = f.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return None, window
    for line in reversed(lines):
        try:
            usage = json.loads(line).get("message", {}).get("usage")
        except Exception:
            continue
        if usage and usage.get("input_tokens") is not None:
            used = (usage.get("input_tokens", 0)
                    + usage.get("cache_read_input_tokens", 0)
                    + usage.get("cache_creation_input_tokens", 0))
            return used, window
    return None, window


def default_effort(data):
    """effortLevel from settings, for when the payload omits effort (e.g. the
    active model doesn't support the effort parameter). Project settings
    override user settings, matching Claude Code's own precedence."""
    dirs = [(data.get("workspace") or {}).get("project_dir"),
            os.path.expanduser("~/.claude")]
    for d in dirs:
        if not d:
            continue
        try:
            with open(os.path.join(d, "settings.json")) as f:
                level = json.load(f).get("effortLevel")
        except (OSError, ValueError):
            continue
        if level:
            return level
    return None


def git_branch(cwd, session_id):
    """Current branch, cached 5s per session so frequent re-runs stay fast."""
    cache = f"/tmp/claude-statusline-git-{session_id}"
    try:
        if os.path.getmtime(cache) > time.time() - 5:
            with open(cache) as f:
                return f.read().strip() or None
    except OSError:
        pass
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "branch", "--show-current"],
            capture_output=True, text=True, timeout=2,
        ).stdout.strip()
    except Exception:
        out = ""
    try:
        with open(cache, "w") as f:
            f.write(out)
    except OSError:
        pass
    return out or None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print(f"{DIM}statusline: unreadable input{RESET}")
        return

    segments = []

    model = (data.get("model") or {}).get("display_name")
    if model:
        segments.append(f"{CYAN}{model}{RESET}")

    effort = (data.get("effort") or {}).get("level") or default_effort(data)
    if effort:
        segments.append(f"{DIM}◉ {effort}{RESET}")

    cw = data.get("context_window") or {}
    pct = cw.get("used_percentage")
    size = cw.get("context_window_size")
    used = cw.get("total_input_tokens")
    tout = cw.get("total_output_tokens")
    if pct is None:
        used, size = fallback_usage(data)
        if used is not None and size:
            pct = used / size * 100
    if pct is None:
        pct = 0.0  # fresh session: no API response yet
    pct = max(0.0, min(float(pct), 100.0))
    filled = round(pct / 100 * BAR_WIDTH)
    bar = "▓" * filled + "░" * (BAR_WIDTH - filled)
    pct_txt = f"{pct:.0f}%" if pct >= 10 else f"{pct:.1f}%"
    segments.append(f"{context_color(pct)}{bar} {pct_txt}{RESET}")

    if used is not None or tout:
        tok_parts = []
        if used is not None:
            tok_parts.append(f"↑{fmt_tokens(used)}" + (f"/{fmt_tokens(size)}" if size else ""))
        if tout:
            tok_parts.append(f"↓{fmt_tokens(tout)}")
        segments.append(DIM + " ".join(tok_parts) + RESET)

    cwd = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or os.getcwd()
    folder = os.path.basename(cwd.rstrip("/")) or cwd
    segments.append(f"{MAGENTA}{folder}{RESET}")
    branch = git_branch(cwd, data.get("session_id") or "default")
    if branch:
        segments[-1] += f" {YELLOW}{branch}{RESET}"

    print(SEP.join(segments))


if __name__ == "__main__":
    main()
