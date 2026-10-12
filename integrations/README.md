# integrations — this project inside a coding agent

Everything in this directory exists to put the engine behind a *host*. None of it is the research
product: the engine, the interface, the corpus, the prompt stack and the registered models all live
at the repository root, and nothing here duplicates them. Every host reaches the engine through
`integrations/geoai/`, the one Python surface.

## Layout on this branch

```
integrations/
  geoai/      the shared surface — host-neutral, and the only way in
  dsh/        DeepSeek Harness: the plugin package (host half + browser half + bundle patch)
  scripts/    the host's installers, in one place
  README.md   this file
```

| Directory | What it is |
|---|---|
| `geoai/` | `service.py` (capabilities, knowledge, prompt stack, one call, one turn), `mcp_server.py` (28 tools over stdio), `bridge.py` (loopback JSON API), `__main__.py` (CLI) |
| `dsh/` | `entry.js` (host half: settings, prompt section, lifecycle), `lib/` (bridge client, settings logic, browser bundle, host-environment resolution), `cordis.patch.yml`, `tests/` (59 node tests) |
| `scripts/` | `install-dsh.sh`, `verify-dsh-profile.sh`, and `merge-patch-block.py` |

The other two hosts are on their own branches, each with the same shape: `plugin/codex-geoai` carries
`integrations/codex/`, and `plugin/claude-geoai` carries `integrations/claude/`. A branch ships one
host's plugin plus the shared surface, so nothing here has to explain a second host's conventions.

`scripts/find-python.sh` lives at the repository root rather than here: it is shared by the project's
own `scripts/studio.sh` and by every host's installer, so it belongs with the project's scripts and
the installers reach up to it.

## How DeepSeek Harness gets in

```bash
integrations/scripts/install-dsh.sh
integrations/scripts/verify-dsh-profile.sh geoai-verify 3199   # or into a throwaway profile
dsh web
```

`install-dsh.sh` resolves this checkout and an interpreter that can import the engine, copies the
package into the profile, adds it to `dsh.profile.bundles`, and writes the two complete rows the
harness needs — a plugin row and an MCP row — into the profile's own patch layer, inside sentinel
comments. `merge-patch-block.py` is that last step; it is separate because it is the part with the
edge cases (a row's `config` is *replaced*, not merged, and a patch list is one YAML document).

## Verified

`tests/test_dsh_integration.py` plus 59 node tests, and a real boot: the plugin mounts in an
isolated profile, the switch moves the palette, the tool list and the prompt section together, and a
one-shot headless run reports the engine's own rules in its system prompt.

`integrations/geoai/README.md` documents the shared surface; `integrations/dsh/README.md` is the
plugin's own guide.

## 在别的分支上你会看到什么

本分支只带自己的宿主目录 `integrations/dsh/`。另外两个宿主不在这个 checkout 里：plugin/codex-geoai 带 integrations/codex/，plugin/claude-geoai 带 integrations/claude/
所以在这里 `ls integrations/` 只有 `geoai/`、`dsh/`、`scripts/` 和这份 README。

**切换分支后可能留下空壳目录。** `git checkout` 会删掉不再跟踪的*文件*，但**不会删目录**——git
根本不跟踪目录。所以从 Codex 分支切回来时，工作树里可能还留着空的 `integrations/codex/plugin/`，
看起来像"文件丢了"。它们不在版本库里，清掉即可：

```bash
git clean -nd integrations     # 先看一遍会删什么（现在是空的目录和缓存）
git clean -fd integrations     # 真删
```
