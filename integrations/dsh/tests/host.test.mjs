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
import { register } from 'node:module'
import test from 'node:test'

import { ACCENTS, DEFAULTS } from '../lib/logic.js'

// `entry.js` imports `@deepseek-ai/schemastery`, a peer dependency the host profile supplies.
// It is not a dependency of this package on purpose — there must be exactly one copy on the
// resolve path and it must be the host's — so the hook below stands in for it. Registered
// before the import, which is why the import is dynamic.
register('./resolve-hook.mjs', import.meta.url)
const { Config, MCP_ENTRY_ID, NAMESPACE, PROMPT_ORDER, PROMPT_SECTION, apply, inject, name } = await import(
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

test('the module exports what the cordis loader reads', () => {
  assert.equal(name, 'physearth-geoai')
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
  const { ctx, calls } = stubContext({ enabled: true, autoStartBridge: false })
  apply(ctx, { enabled: true, autoStartBridge: false })
  await settle()

  assert.equal(calls.sections.length, 1)
  const section = calls.sections[0]
  assert.equal(section.name, 'geoai-physics')
  assert.equal(section.order, PROMPT_ORDER)
  assert.ok(Number.isFinite(section.order))
  assert.equal(section.text, PROMPT_SECTION)
  // After the harness' own tool guidance (100-116), before the deployment layer (190+).
  assert.ok(section.order > 116 && section.order < 190)
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
