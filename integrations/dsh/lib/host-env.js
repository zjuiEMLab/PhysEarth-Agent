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
