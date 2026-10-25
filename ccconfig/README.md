# ccconfig — multiple models, one Claude Code

Two tips in one folder: run Claude Code against a **different model/provider** by keeping one settings file per model and a two-letter shell function to launch it — plus the `--permission-mode` helper that skips permission prompts.

## The shell functions

Add to `~/.bashrc` (or `~/.zshrc`):

```bash
# claude code
cc(){
  claude --permission-mode bypassPermissions "$@"
}
ccds(){
  claude --permission-mode bypassPermissions --settings ~/.claude/settings-deepseek.json "$@"
}
```

Then `source ~/.bashrc` and you have:

| Command | What it runs |
| --- | --- |
| `cc` | Claude Code with your default settings, permission prompts bypassed |
| `ccds` | The same, with `~/.claude/settings-deepseek.json` layered on top — DeepSeek endpoint and model |

`"$@"` forwards every argument, so `cc --resume`, `ccds -c "fix the failing test"`, or `ccds --model deepseek-reasoner` all work as usual.

## How `--settings` works

Claude Code merges settings from several sources. In increasing precedence:

1. user settings — `~/.claude/settings.json`
2. project settings — `.claude/settings.json`, `.claude/settings.local.json`
3. the file passed as `claude --settings <file>`

The file you pass **overrides matching keys and inherits everything else**. A per-model file therefore only needs the parts that differ — base URL, API key, model. Your status line, hooks, theme, and effort level from the regular settings still apply in every variant.

That's the whole trick: `settings-deepseek.json` is not a full second config, just the diff.

## The settings file

This folder ships a template, [`settings-deepseek.json`](settings-deepseek.json), using DeepSeek's Anthropic-compatible endpoint. Copy it into `~/.claude/` and put your real key in:

```bash
cp ccconfig/settings-deepseek.json ~/.claude/settings-deepseek.json
```

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "sk-your-deepseek-key",
    "ANTHROPIC_MODEL": "deepseek-flash",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-flash[1m]",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-flash[1m]",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-flash",
    "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek-flash",
    "CLAUDE_CODE_EFFORT_LEVEL": "max",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "786432"
  },
  "model": "deepseek-flash[1m]",
  "effortLevel": "max"
}
```

Details:

- **`ANTHROPIC_DEFAULT_*_MODEL`** — Claude Code also makes background calls with its haiku-class model. If your default settings already map these env vars to another provider (e.g. GLM), the overlay must remap them too, or those calls hit the DeepSeek endpoint with a foreign model id and fail.
- **`deepseek-flash[1m]`** — the `[1m]` suffix requests the 1M-token context variant of the model for the main conversation, while background/subagent calls stay on the plain `deepseek-flash`.
- **`CLAUDE_CODE_AUTO_COMPACT_WINDOW`: `786432`** — with a 1M context you also want auto-compact to trigger later; this raises the effective window (768K) it compacts against instead of the default ~200K.
- **Any Anthropic-compatible provider** works the same way — GLM/BigModel, Kimi, Qwen, a local gateway. One file plus one function each:

  ```bash
  cckimi(){
    claude --permission-mode bypassPermissions --settings ~/.claude/settings-kimi.json "$@"
  }
  ```

- **See which model you're on** — run `/status` in the session, or use the [ccstatusline](../ccstatusline/) status line, which shows the active model (and token usage) permanently. Handy once you have several variants lying around.

## About `bypassPermissions`

`--permission-mode bypassPermissions` skips every permission prompt — file writes, shell commands, everything. Convenient, but it means nothing checks the agent's actions. Use it in workspaces you trust; for anything else prefer the default mode, `acceptEdits`, or a scoped `permissions.allow` list.
