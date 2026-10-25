# ccstatusline

A zero-dependency status line for [Claude Code](https://code.claude.com/docs/en/statusline), in a single Python script. It shows the active model, reasoning effort, a color-coded context-window usage bar, token counts, the current directory, and the git branch — all in one line at the bottom of the terminal.

```
Fable 5.1 │ ◉ high │ ▓▓▓▓░░░░░░░░░░░░░░░░ 18% │ ↑182k/1.0M ↓12k │ myproject  main
```

## What it shows

| Segment | Example | Color |
| --- | --- | --- |
| Model | `Fable 5.1` | cyan |
| Reasoning effort | `◉ high` | dim |
| Context bar + % | `▓▓▓▓░░░░░░░░░░░░░░░░ 18%` | green < 70%, yellow ≥ 70%, red ≥ 90% |
| Token counts | `↑182k/1.0M ↓12k` | dim |
| Directory | `myproject` | magenta |
| Git branch | ` main` | yellow |

Details:

- **Context bar** — 20 cells (`▓` filled, `░` empty). The percentage is the share of the model's context window already in use, so you can see auto-compact approaching at a glance.
- **Token counts** — `↑` input tokens used (with window size), `↓` output tokens, formatted compactly as `k`/`M`.
- **Graceful degradation** — Claude Code's payload fields can be absent or `null` early in a session. Every segment hides itself when its data is missing; you'll never see `None` or a crash.

## Requirements

- Python 3.7+ (standard library only — nothing to install)
- `git` (optional — the branch segment simply doesn't appear outside a repo)

## Install

```bash
git clone https://github.com/johnfu-ai/cctips.git
cp cctips/ccstatusline/statusline.py ~/.claude/statusline.py
```

(Or keep the clone anywhere and point the command at it — then `git pull` picks up updates.)

## Configure

Add a `statusLine` entry to your user settings (`~/.claude/settings.json`) or to a project's `.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/statusline.py"
  }
}
```

The `command` runs in a shell, so `~` expands. Claude Code reloads settings automatically and runs your script as soon as you save the file — no restart needed.

To remove the status line, delete the `statusLine` field from settings (or run `/statusline` in Claude Code and ask it to clear).

### Related settings

Two other settings feed the script's fallbacks:

- **`effortLevel`** — when the payload omits `effort.level` (the active model doesn't support the effort parameter), the script falls back to the `effortLevel` from `settings.json`. Project settings override user settings, matching Claude Code's own precedence:

  ```json
  {
    "effortLevel": "high"
  }
  ```

- **`CLAUDE_CODE_AUTO_COMPACT_WINDOW`** — environment variable with the context window size (in tokens) to assume when the payload doesn't report one. Defaults to `200000`; models whose id contains `[1m]` are assumed to have a 1M window regardless.

## How it works

Claude Code sends a JSON snapshot of the session to the script's stdin whenever meaningful state changes (model switch, new API response, directory change, …), debounced at 300 ms. The script prints one line; that line becomes your status bar. See the [status line docs](https://code.claude.com/docs/en/statusline) for the full payload schema.

Two implementation details worth knowing:

- **Transcript fallback** — before the first API response, the payload's `context_window` fields are `null`. The script then reads the last 256 KB of the session transcript (`transcript_path`) to find the most recent usage record and computes usage from it, so the bar is accurate even mid-warmup.
- **Git branch caching** — the status line re-runs frequently. To stay fast, the branch lookup is cached for 5 seconds per session in `/tmp/claude-statusline-git-<session_id>`.

## Testing it

Run the script by hand with a sample payload to see the output and debug changes:

```bash
echo '{"model":{"display_name":"Fable 5.1"},"workspace":{"current_dir":"'"$PWD"'"}}' \
  | python3 ccstatusline/statusline.py
```

## License

[MIT](LICENSE)
