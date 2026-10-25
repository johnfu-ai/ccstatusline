# cctips

Practical [Claude Code](https://code.claude.com/) tips — small, self-contained, copy-paste ready. One folder per tip.

## Tips

### [ccstatusline](ccstatusline/) — a status line in one Python file

Model, reasoning effort, a color-coded context-window usage bar, token counts, the current directory, and the git branch, all on one line at the bottom of the terminal. Zero dependencies — standard library only.

```
Fable 5.1 │ ◉ high │ ▓▓▓▓░░░░░░░░░░░░░░░░ 18% │ ↑182k/1.0M ↓12k │ myproject  main
```

### [ccconfig](ccconfig/) — multiple models, two-letter launchers

One settings file per provider, layered on top of your defaults with `claude --settings`, so `cc` is your everyday Claude Code and `ccds` is the same session on DeepSeek — status line and everything else intact.

```bash
cc(){
  claude --permission-mode bypassPermissions "$@"
}
ccds(){
  claude --permission-mode bypassPermissions --settings ~/.claude/settings-deepseek.json "$@"
}
```

## License

[MIT](LICENSE)
