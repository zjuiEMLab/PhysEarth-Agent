// Host-side environment resolution: where the checkout is, and which Python can run it.
//
// Both answers used to be written into the bundle patch as `REPLACE_WITH_CHECKOUT` and
// `python3`. A live boot showed why that is the wrong place for them:
//
//   - the harness composes patch layers with a *shallow* assignment per entry, so an id-targeted
//     `config:` override replaces a row's whole config rather than merging into it. A second
//     layer therefore cannot "just add the path" — it has to restate every key, and a bundle
//     patch shipped with a placeholder forces exactly that kind of duplicate.
//   - a bundle patch is repository content, so it cannot carry an absolute path at all.
//
// So the plugin resolves both itself, at mount, from facts it actually has:
//
//   - the checkout, by walking up from this file (which works when the package is symlinked out
//     of the checkout) and, failing that, from the process working directory (which works when
//     the package was copied into a profile);
//   - the interpreter, by proving candidates against the engine rather than trusting a name.
//     `python` is absent on macOS and on most Linux distributions, and `python3` is frequently a
//     bare system interpreter without PyYAML — which is how an MCP row comes up as an empty tool
//     list with nothing in the log.
//
// Both are pure functions over an injected `exists`/`probe`, so `tests/host-env.test.mjs` can
// exercise the interesting cases without a real filesystem or a real interpreter.

import { spawnSync } from 'node:child_process'
import { dirname, join, resolve } from 'node:path'

/**
 * Files that only exist in a checkout of this repository.
 *
 * Both are required: `backend/physearth` alone would match any sibling project that happens to
 * have the same layout, and `integrations/geoai` alone would match a directory holding only the
 * integrations tree.
 */
export const CHECKOUT_MARKERS = ['backend/physearth/__init__.py', 'integrations/geoai/service.py']

/**
 * Directories to consider, nearest first: every ancestor of the starting points, plus `cwd`.
 *
 * @param startDirs - directories to walk up from, nearest first.
 * @param cwd - the process working directory, tried last.
 * @returns candidate directories, de-duplicated, nearest first.
 */
export function checkoutCandidates(startDirs, cwd) {
  const seen = new Set()
  const out = []
  const push = (dir) => {
    if (!dir) return
    const key = resolve(dir)
    if (seen.has(key)) return
    seen.add(key)
    out.push(key)
  }
  for (const start of startDirs) {
    if (!start) continue
    let dir = resolve(start)
    for (;;) {
      push(dir)
      const parent = dirname(dir)
      if (parent === dir) break
      dir = parent
    }
  }
  push(cwd)
  return out
}

/**
 * The first candidate directory that holds all {@link CHECKOUT_MARKERS}.
 *
 * @param options.startDirs - directories to walk up from.
 * @param options.cwd - the process working directory, tried last.
 * @param options.exists - `(absolutePath) => boolean`.
 * @returns the checkout root, or `undefined`.
 */
export function findCheckout({ startDirs = [], cwd, exists }) {
  for (const dir of checkoutCandidates(startDirs, cwd)) {
    if (CHECKOUT_MARKERS.every((marker) => exists(join(dir, marker)))) return dir
  }
  return undefined
}

/**
 * Interpreter candidates in order of how specific they are.
 *
 * An explicit setting wins; then the environment variable an operator would reach for; then a
 * checkout virtualenv (what `uv sync` produces); then the portable system names.
 *
 * @param options.configured - the `pythonCmd` setting, which may be a bare name.
 * @param options.checkout - the resolved checkout, for the virtualenv candidate.
 * @param options.env - the process environment.
 * @returns candidate commands, de-duplicated, most specific first.
 */
export function interpreterCandidates({ configured, checkout, env = {} }) {
  const defaults = ['python3', 'python']
  const out = []
  const push = (value) => {
    const trimmed = String(value ?? '').trim()
    if (trimmed && !out.includes(trimmed)) out.push(trimmed)
  }
  // A configured value that is not one of the bare defaults is an explicit choice and is tried
  // first; a configured default is just the schema default and is retried in its natural place.
  if (configured && !defaults.includes(String(configured).trim())) push(configured)
  push(env.PHYSEARTH_PYTHON)
  if (checkout) push(join(checkout, '.venv', 'bin', 'python'))
  for (const name of defaults) push(name)
  return out
}

/**
 * The first candidate an engine import actually succeeds with.
 *
 * @param options.candidates - commands to try, in order.
 * @param options.probe - `(command) => boolean`, synchronous.
 * @returns the chosen command, or `undefined` when nothing worked.
 */
export function pickInterpreter({ candidates, probe }) {
  for (const command of candidates) {
    if (probe(command)) return command
  }
  return undefined
}

/**
 * How a resolved interpreter is described in the log, so "why is it using that Python?" has an
 * answer next to the line that chose it.
 *
 * @param command - the chosen command.
 * @param probed - how many candidates were tried before it worked.
 * @returns a one-line explanation.
 */
export function interpreterProvenance(command, probed) {
  if (!command) return 'no candidate could import the engine'
  return probed === 1 ? `${command} (first candidate)` : `${command} (candidate ${probed})`
}

/**
 * The scopes the engine publishes (`service.PROMPT_SCOPES`), which is what a depth may name.
 *
 * Duplicated from Python rather than imported, because the plugin cannot import Python. A scope
 * the engine drops shows up as a failed fetch with the engine's own error in the log, which is
 * the loud failure — not as a silently narrower prompt.
 */
export const PROMPT_SCOPES = Object.freeze(['identity', 'rules', 'context'])

/**
 * How deep a host takes the project's prompt stack, and what each answer costs.
 *
 * These are the card's choices. The sizes below are what this checkout reports, not guesses —
 * `python -m integrations.geoai prompt --list` prints them for any revision, and they are the
 * reason the default is not `full`: `context` is 24k characters of registered-model and corpus
 * text that the same session can also read through `mcp__geoai__*`, so paying for a copy in
 * every turn buys a snapshot that starts going stale immediately.
 *
 * `identity` is deliberately absent from the default for a different reason. It is 1.3k
 * characters that begin "You are PhysEarth, an Earth-science physical-modeling agent" — a
 * persona, and a host has one of its own. Injecting it would make the harness model claim to be
 * this agent while still being asked to do the host's work, which is the opposite of keeping
 * what the host is good at.
 */
export const PROMPT_SCOPE_ARGS = Object.freeze({
  compact: null,
  rules: 'rules',
  full: 'identity,rules,context',
})

/**
 * Read the project's prompt text out of the engine, so the section a host injects is the
 * engine's own words rather than a summary written next to them.
 *
 * The summary was the bug this replaces. `entry.js` carried a fifteen-line paraphrase that named
 * the six registered models literally — so registering a seventh model, or renaming one, would
 * leave the prompt asserting something the registry no longer says, in the one place nobody
 * re-reads. Text fetched here cannot drift: it is composed from `prompts/` and the registry at
 * the moment the plugin mounts.
 *
 * Synchronous, deliberately, and the measurement is the reason. On this checkout the fetch takes
 * 0.46 s, and a *live boot found the hard way* that asynchronous is wrong here: the harness
 * composes its prompt for the first request before an awaited child process can answer, so the
 * one-shot `dsh --profile headless "…"` run reported the compact text verbatim — the engine's
 * text would have arrived into a request that had already gone out. Half a second at mount is
 * the price of the first turn being right.
 *
 * @param options.pythonCmd - the interpreter to run.
 * @param options.checkout - repository root, used as the working directory and on PYTHONPATH.
 * @param options.scope - a key of {@link PROMPT_SCOPE_ARGS}.
 * @param options.env - the process environment.
 * @param options.run - `(command, args, options) => { status, stdout, stderr }`, defaults to
 *   `spawnSync`.
 * @returns the text and a one-line provenance note.
 * @throws when the interpreter fails, with the engine's own stderr in the message.
 */
export function readPromptStack({
  pythonCmd,
  checkout,
  scope,
  env = {},
  run = spawnSync,
  timeout = 30000,
}) {
  const scopes = PROMPT_SCOPE_ARGS[scope]
  if (!scopes) throw new Error(`prompt depth "${scope}" does not ask the engine for anything`)
  if (!pythonCmd || !checkout) throw new Error('no interpreter or checkout to ask')
  const args = ['-m', 'integrations.geoai', 'prompt', '--scopes', scopes]
  const result = run(pythonCmd, args, {
    cwd: checkout,
    timeout,
    env: { ...env, PYTHONPATH: `${checkout}/backend:${checkout}` },
    encoding: 'utf8',
  })
  if (!result || result.error) throw new Error(result?.error?.message || 'the run produced no result')
  if (result.status !== 0) {
    const stderr = String(result.stderr || '').trim().split('\n').slice(-3).join(' | ')
    throw new Error(`exit ${result.status}${stderr ? `: ${stderr}` : ''}`)
  }
  const text = String(result.stdout || '').trim()
  if (!text) throw new Error('the engine printed nothing')
  return { text, scope, detail: `${text.length} chars, scope=${scopes} from ${pythonCmd}` }
}
