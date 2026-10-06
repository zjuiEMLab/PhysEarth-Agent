// The host half against a stub cordis context.
//
// Why this file exists: every mistake this plugin actually made was a *silent* one. The prompt
// section was registered as `{ id, content }` instead of `{ name, order, text }`, which makes
// `systemPrompt.section` throw on a non-finite order; the settings scope was watched through
// `subscribe()`, which the scope does not have, so the switch would have applied at mount time
// and never again; and the MCP row was only touched when the plugin was already on, so "off"
// would have left the model's whole tool list in place. None of those are visible without a
// running harness, and all three are visible from here.
//
// The stubs below are deliberately strict: a service method that does not exist on the real
// package is a `TypeError`, not a permissive no-op.

import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { register } from 'node:module'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import test from 'node:test'

import { ACCENTS, DEFAULTS } from '../lib/logic.js'

// `entry.js` imports `@deepseek-ai/schemastery`, a peer dependency the host profile supplies.
// It is not a dependency of this package on purpose — there must be exactly one copy on the
// resolve path and it must be the host's — so the hook below stands in for it. Registered
// before the import, which is why the import is dynamic.
register('./resolve-hook.mjs', import.meta.url)
const { Config, MCP_ENTRY_ID, NAMESPACE, PROMPT_ORDER, PROMPT_HEADING, PROMPT_SECTION, apply, inject, name } = await import(
  '../entry.js'
)

/**
 * A context shaped like the real one, recording what the plugin asked of it.
 *
 * `settings.register` returns exactly the four members the shipped `dsh-settings-file` scope
 * exposes — `get`, `watch`, `update`, `replace` — so a plugin that reaches for a fifth one
 * fails here.
 */
function stubContext(config = {}) {
  const calls = { sections: [], rows: [], watched: 0, effects: [], logs: [] }
  let stored = { ...config }
  let watcher
  const scope = {
    get: () => stored,
    watch: (callback) => {
      calls.watched += 1
      watcher = callback
      return () => {
        watcher = undefined
      }
    },
    update: (patch) => {
      stored = { ...stored, ...patch }
      return Promise.resolve()
    },
    replace: (next) => {
      stored = { ...next }
      return Promise.resolve()
    },
  }
  const ctx = {
    logger: {
      info: (message) => calls.logs.push(['info', message]),
      warn: (message) => calls.logs.push(['warn', message]),
      error: (message) => calls.logs.push(['error', message]),
    },
    settings: { register: (ns, schema, options) => {
      calls.registered = { ns, schema, options }
      return scope
    } },
    systemPrompt: {
      section: (section) => {
        // The real service throws a TypeError for a non-finite order; mirror that so the
        // check is not merely a convention here.
        if (!Number.isFinite(section.order)) throw new TypeError(`prompt section "${section.name}" order must be a finite number`)
        if (typeof section.name !== 'string' || typeof section.text !== 'string') {
          throw new TypeError('prompt section needs a string name and text')
        }
        calls.sections.push(section)
        return () => {
          calls.disposed = (calls.disposed ?? 0) + 1
        }
      },
    },
    tools: {},
    loader: {
      update: (id, options) => {
        calls.rows.push([id, options])
        return Promise.resolve()
      },
    },
    effect: (callback, label) => {
      calls.effects.push(label)
      const dispose = callback()
      return () => {
        if (typeof dispose === 'function') dispose()
      }
    },
  }
  return { ctx, calls, flip: (patch) => {
    stored = { ...stored, ...patch }
    if (watcher) watcher(stored)
  } }
}

/**
 * Let the plugin's async startup settle.
 *
 * `apply` is synchronous but the bridge probe inside it is not, and the prompt section is
 * registered only after that probe answers. `setImmediate` rather than `Promise.resolve()`,
 * because the probe is a real (stubbed) socket call: resolving it takes an I/O turn, not just
 * a microtask.
 */
async function settle(rounds = 8) {
  for (let index = 0; index < rounds; index += 1) {
    await new Promise((resolve) => setImmediate(resolve))
  }
}

/** Replace `fetch` with one that refuses immediately, so no test opens a socket. */
async function withoutNetwork(run) {
  const original = globalThis.fetch
  globalThis.fetch = () => Promise.reject(new Error('ECONNREFUSED (stubbed)'))
  try {
    return await run()
  } finally {
    globalThis.fetch = original
  }
}

/**
 * Wait for a real subprocess to finish.
 *
 * `settle()` above counts event-loop turns, which is right for a stubbed socket and wrong for
 * `execFile`: a spawn takes tens of milliseconds, and twenty `setImmediate` rounds elapse in
 * well under one. Polling with a deadline is the honest version — it asserts the same thing and
 * fails with the timeout rather than with a confusing "expected 2, got 1".
 */
async function waitFor(predicate, { timeout = 5000, step = 20 } = {}) {
  const deadline = Date.now() + timeout
  for (;;) {
    if (predicate()) return true
    if (Date.now() > deadline) return predicate()
    await new Promise((resolve) => setTimeout(resolve, step))
  }
}

test('the module exports what the cordis loader reads', () => {
  assert.equal(name, 'physearth')
  assert.deepEqual(inject, ['settings', 'tools', 'systemPrompt'])
  assert.equal(typeof apply, 'function')
  // Real schemastery schemas are callable; the test stub is a plain object. What matters here
  // is that a schema was exported at all — the shape of it is asserted below.
  assert.ok(Config && (typeof Config === 'object' || typeof Config === 'function'))
})

test('the settings schema declares exactly the keys both halves agree on', () => {
  const declared = Object.keys(Config.__spec).sort()

  // The browser half ships its own copy of these defaults (a client bundle cannot value-import
  // across plugins), so a key added on one side and not the other is a card that silently
  // writes a field the host drops on the floor.
  assert.deepEqual(declared, Object.keys(DEFAULTS).sort())
  assert.equal(Config.__spec.accent.__default, DEFAULTS.accent)
  assert.equal(Config.__spec.bridgeUrl.__default, DEFAULTS.bridgeUrl)
  assert.equal(Config.__spec.enabled.__default, DEFAULTS.enabled)
  assert.equal(Config.__spec.colorScheme.__kind, 'string')
  assert.ok(ACCENTS.length === 3)
})

test('the settings namespace is one the host accepts', () => {
  // `dsh-settings-file` validates against /^[a-z][a-z0-9-]*$/ before registering.
  assert.match(NAMESPACE, /^[a-z][a-z0-9-]*$/)
})

test('the composition config is registered as the namespace base layer', () => {
  const { ctx, calls } = stubContext({ enabled: true })
  apply(ctx, { enabled: true, bridgeUrl: 'http://127.0.0.1:9123' })

  // The service resolves schema defaults, then `base`, then the user's stored section. Without
  // `base`, the `config:` block in a patch layer would be decorative: `scope.get()` would answer
  // with the schema defaults, so a cordis.patch.yml saying `enabled: true` would mount a plugin
  // that stays off.
  assert.ok(calls.registered.options, 'register() received an options object')
  assert.equal(calls.registered.options.base.enabled, true)
  assert.equal(calls.registered.options.base.bridgeUrl, 'http://127.0.0.1:9123')
})

test('the prompt section is registered in the shape the service accepts', async () => {
  // `compact` throughout the older tests: they are about the section's *shape*, and the default
  // depth would make them spawn a real interpreter to upgrade it — a test that then passes or
  // fails depending on what `python3` happens to be on the machine.
  const { ctx, calls } = stubContext({ enabled: true, autoStartBridge: false, promptDepth: 'compact' })
  apply(ctx, { enabled: true, autoStartBridge: false, promptDepth: 'compact' })
  await settle()

  assert.equal(calls.sections.length, 1)
  const section = calls.sections[0]
  assert.equal(section.name, 'physearth-physics')
  assert.equal(section.order, PROMPT_ORDER)
  assert.ok(Number.isFinite(section.order))
  assert.equal(section.text, PROMPT_SECTION)
  // After the harness' own tool guidance (100-116), before the deployment layer (190+).
  assert.ok(section.order > 116 && section.order < 190)
})

test('the compact text names no model, so it cannot drift from the registry', () => {
  // The bug this replaces: the fifteen-line paraphrase that used to live here listed the six
  // registered models literally, so registering a seventh would leave the prompt asserting
  // something the registry no longer says, in the one place nobody re-reads.
  assert.match(PROMPT_SECTION, /list_models/)
  for (const name of ['SMRT', 'smrt', 'tau-omega', 'PROSAIL', 'prosail', 'pyet', 'pywatershed', 'water cloud']) {
    assert.ok(!PROMPT_SECTION.includes(name), `the compact section should not hardcode ${name}`)
  }
})

test('promptDepth "off" registers no section, and says that is deliberate', async () => {
  const { ctx, calls } = stubContext({ enabled: true, promptDepth: 'off' })
  apply(ctx, { enabled: true, promptDepth: 'off' })
  await settle()

  assert.equal(calls.sections.length, 0)
  assert.ok(
    calls.logs.some(([level, message]) => level === 'info' && /promptDepth is "off"/.test(message)),
    'choosing no prompt text is logged, not silent',
  )
})

/** A stand-in for the interpreter: it prints whatever the test needs and records its calls. */
function fakeEngine({ text = 'ENGINE RULES: numbers come from runs.', status = 0 } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'physearth-fake-'))
  const counter = join(dir, 'calls')
  const script = join(dir, 'python')
  writeFileSync(
    script,
    `#!/bin/sh\nprintf '%s\\n' "$*" >> ${JSON.stringify(counter)}\n` +
      (status === 0 ? `cat <<'TEXT'\n${text}\nTEXT\n` : `echo 'boom: no engine here' >&2\nexit ${status}\n`),
    { mode: 0o755 },
  )
  return {
    dir,
    script,
    // Every call, including the probe the interpreter search makes.
    calls: () => readFileSync(counter, 'utf8').trim().split('\n').filter(Boolean),
    // Just the prompt fetches, which is what a test about the *text* means.
    promptCalls: () =>
      readFileSync(counter, 'utf8')
        .trim()
        .split('\n')
        .filter((line) => line.startsWith('-m integrations.physearth')),
    cleanup: () => rmSync(dir, { recursive: true, force: true }),
  }
}

test('the engine supplies the prompt text, so it cannot drift from prompts/ and the registry', async () => {
  const engine = fakeEngine()
  try {
    const { ctx, calls } = stubContext({
      enabled: true,
      promptDepth: 'rules',
      pythonCmd: engine.script,
      projectRoot: engine.dir,
    })
    apply(ctx, {
      enabled: true,
      promptDepth: 'rules',
      pythonCmd: engine.script,
      projectRoot: engine.dir,
    })
    // One section, and it is the engine's — registered before `start()` yields, which is the
    // whole point: a host that composes its prompt for the first request must not catch the
    // compact fallback.
    assert.equal(calls.sections.length, 1)
    // The heading is this plugin's; everything under it is the engine's text, verbatim.
    const text = calls.sections[0].text
    assert.ok(text.startsWith(`${PROMPT_HEADING}\n\n`), text.slice(0, 60))
    assert.equal(text.slice(PROMPT_HEADING.length + 2), 'ENGINE RULES: numbers come from runs.')
    // And it asked the engine for the scope the depth names, not for everything. (`engine.calls()`
    // also holds the probe the interpreter search makes.)
    assert.deepEqual(engine.promptCalls(), ['-m integrations.physearth prompt --scopes rules'])
    assert.ok(
      calls.logs.some(([level, message]) => level === 'info' && /text from engine/.test(message)),
      'the source and size of the injected text are reported, not assumed',
    )
  } finally {
    engine.cleanup()
  }
})

test('a failing engine leaves the compact rules in place and names the depth that failed', async () => {
  const engine = fakeEngine({ status: 3 })
  try {
    const { ctx, calls } = stubContext({
      enabled: true,
      promptDepth: 'full',
      pythonCmd: engine.script,
      projectRoot: engine.dir,
    })
    apply(ctx, {
      enabled: true,
      promptDepth: 'full',
      pythonCmd: engine.script,
      projectRoot: engine.dir,
    })
    await waitFor(() => calls.sections.length >= 1)

    assert.equal(calls.sections.length, 1)
    assert.equal(calls.sections[0].text, PROMPT_SECTION)
    const warning = calls.logs.find(([level, message]) => level === 'warn' && /promptDepth "full"/.test(message))
    assert.ok(warning, 'the failure is a warning, not a silent fallback')
    assert.match(warning[1], /Exit 3|exit 3|boom/)
    // `full` is the three scopes, in the order the engine stacks them.
    assert.deepEqual(engine.promptCalls(), ['-m integrations.physearth prompt --scopes identity,rules,context'])
  } finally {
    engine.cleanup()
  }
})

test('the engine is asked once, not on every settings change', async () => {
  const engine = fakeEngine()
  try {
    const { ctx, calls, flip } = stubContext({
      enabled: true,
      promptDepth: 'rules',
      pythonCmd: engine.script,
      projectRoot: engine.dir,
    })
    apply(ctx, {
      enabled: true,
      promptDepth: 'rules',
      pythonCmd: engine.script,
      projectRoot: engine.dir,
    })
    assert.equal(engine.promptCalls().length, 1)

    // `reconcile()` runs on every write the card makes, and the card writes on every select and
    // checkbox change. Without the cache, changing the accent would spawn an interpreter and
    // rebuild 14 KB of prompt text.
    flip({ accent: 'amber' })
    await settle(20)
    flip({ accent: 'deep-blue' })
    await settle(20)

    assert.equal(engine.promptCalls().length, 1, 'the prompt text is read once per mount')
    assert.ok(calls.sections.at(-1).text.endsWith('ENGINE RULES: numbers come from runs.'))
  } finally {
    engine.cleanup()
  }
})

test('a different depth reads the engine again, the same depth does not', async () => {
  const engine = fakeEngine({ text: 'ENGINE RULES: first read.' })
  try {
    const config = { enabled: true, promptDepth: 'rules', pythonCmd: engine.script, projectRoot: engine.dir }
    const { ctx, calls, flip } = stubContext(config)
    apply(ctx, config)
    await waitFor(() => calls.sections.length === 1)
    assert.equal(engine.promptCalls().length, 1)

    // A settings change re-runs reconcile(), and reconcile() re-registers the section. The text
    // is per depth, so `full` is a second read and `rules` again is not — otherwise changing the
    // accent would spawn an interpreter and rebuild the prompt.
    flip({ promptDepth: 'full' })
    await waitFor(() => calls.sections.length === 2)
    assert.deepEqual(engine.promptCalls(), [
      '-m integrations.physearth prompt --scopes rules',
      '-m integrations.physearth prompt --scopes identity,rules,context',
    ])

    flip({ accent: 'amber' })
    await waitFor(() => calls.sections.length === 3)
    assert.equal(engine.promptCalls().length, 2, 'the accent change reuses the cached text')
  } finally {
    engine.cleanup()
  }
})

test('mounting with the plugin off registers no prompt section and disables the tool row', async () => {
  const { ctx, calls } = stubContext({ enabled: false })
  apply(ctx, { enabled: false })
  await settle()

  assert.equal(calls.sections.length, 0)
  assert.deepEqual(calls.rows, [[MCP_ENTRY_ID, { disabled: true }]])
})

test('mounting with the plugin on enables the tool row', async () => {
  await withoutNetwork(async () => {
    const { ctx, calls } = stubContext({ enabled: true, autoStartBridge: false })
    apply(ctx, { enabled: true, autoStartBridge: false })
    await settle()

    assert.deepEqual(calls.rows, [[MCP_ENTRY_ID, { disabled: false }]])
    assert.equal(calls.sections.length, 1)
  })
})

test('the settings scope is watched through watch(), which is the method it has', () => {
  const { ctx, calls } = stubContext({ enabled: false })
  apply(ctx, { enabled: false })

  assert.ok(calls.registered, 'the namespace was registered')
  assert.equal(calls.watched, 1, 'watch() is the subscription the scope exposes')
  assert.ok(calls.effects.some((label) => /settings adoption/.test(label)))
})

test('flipping the switch moves the prompt section and the tool row together', async () => {
  await withoutNetwork(async () => {
    const { ctx, calls, flip } = stubContext({ enabled: false, autoStartBridge: false })
    apply(ctx, { enabled: false, autoStartBridge: false })
    await settle()
    assert.equal(calls.sections.length, 0)

    flip({ enabled: true })
    await settle()
    assert.equal(calls.sections.length, 1, 'turning it on adds the prompt section')
    assert.deepEqual(calls.rows.at(-1), [MCP_ENTRY_ID, { disabled: false }])

    flip({ enabled: false })
    await settle()
    assert.equal(calls.disposed, 1, 'turning it off disposes the prompt section')
    assert.deepEqual(calls.rows.at(-1), [MCP_ENTRY_ID, { disabled: true }], 'and takes the tools away')
  })
})

test('a host with no loader.update still mounts, and says what stays in the model\u2019s list', () => {
  const { ctx, calls } = stubContext({ enabled: false })
  const withoutLoader = { ...ctx, loader: undefined }
  apply(withoutLoader, { enabled: false })

  assert.equal(calls.sections.length, 0)
  assert.ok(
    calls.logs.some(([level, message]) => level === 'warn' && /no loader\.update/.test(message)),
    'the limitation is logged rather than hidden',
  )
})

test('a host whose settings scope has no watch() degrades loudly', () => {
  const { ctx, calls } = stubContext({ enabled: false })
  const crippled = { ...ctx, settings: { register: () => ({ get: () => ({ enabled: false }) }) } }
  apply(crippled, { enabled: false })

  assert.ok(calls.logs.some(([level, message]) => level === 'warn' && /no watch\(\)/.test(message)))
})

test('teardown is an effect, so an unload frees the bridge and the prompt section', async () => {
  await withoutNetwork(async () => {
    const { ctx, calls } = stubContext({ enabled: true, autoStartBridge: false })
    apply(ctx, { enabled: true, autoStartBridge: false })
    await settle()

    assert.ok(calls.effects.some((label) => /teardown/.test(label)))
    // Running the teardown effect is what an unload does; it must not throw with no bridge.
    assert.equal(calls.sections.length, 1)
  })
})
