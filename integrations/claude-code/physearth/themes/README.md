# Theme

`physearth-night.json` overrides the alias layer of the built-in `dark` theme, using the same
palette the DeepSeek Harness plugin applies to that surface: the near-black OLED field, ice as the
accent, amber for permissions, blue for plan mode.

Loaded through `experimental.themes` in `plugin.json`, which is where Claude Code expects a plugin
theme: a top-level `themes` key also loads, but warns that it "will be removed in a future
release", so the experimental path is the one that will keep working.

**A plugin cannot activate a theme.** Claude Code reads a plugin's theme and shows it as
`custom:<plugin>:<slug>`, but the selection lives in the user's settings. Two ways to pick it:

```
/theme                                     # interactive
claude --settings ...                      # or set "theme" in settings.json
```

Or let the installer do it: `integrations/claude-code/install.sh --write-settings` writes
`"theme": "custom:physearth:physearth-night"` and the `statusLine` below, backing up first.

Token names and accepted value forms (`#rrggbb`, `#rgb`, `rgb(r,g,b)`, `ansi256(n)`, `ansi:<name>`)
come from the Claude Code theme documentation; a token this file does not name is left at its
built-in value, which is why the list is short — a guessed token name is silently ignored.
