// The browser half, mounted against a stub module table and a stub React.
//
// Why this file exists: the browser half cannot be exercised by reading it. `theme.overrideTokens`
// throws a teaching error on a token value that is a bare string rather than a `{ light, dark }`
// pair — the mistake this file was written to prevent, and one that only ever surfaces in a live
// browser. Likewise a slot registration missing `key`, `id` or `label` still "works": the card
// simply never appears under 设置 → 插件, with no error anywhere.
//
// So the factory is evaluated for real, with the two things it can legitimately require supplied
// by hand: the module loader global and `react`. Everything else it touches is a stub that
// records what it was asked to do.

import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import { ACCENTS, DEFAULTS } from '../lib/logic.js'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const SOURCE = readFileSync(join(ROOT, 'lib', 'client.js'), 'utf8')

/**
 * A minimal React.
 *
 * Hooks are real enough to render once: `useState` returns its initial value and a recorder,
 * `useEffect` runs immediately (so a subscription the component makes is observable) and
 * `useMemo`/`useCallback` compute. The component is not re-rendered, because the assertion this
 * file cares about is "what does the switch do when clicked", which is settled on first render.
 */
function stubReact() {
  const effects = []
  const element = (type, props) => ({ __el: true, type, props: props ?? {} })
  return {
    __effects: effects,
    createElement: (type, props, ...children) => {
      const merged = { ...(props ?? {}) }
      if (children.length === 1) merged.children = children[0]
      else if (children.length > 1) merged.children = children
      return element(type, merged)
    },
    useState: (initial) => {
      const value = typeof initial === 'function' ? initial() : initial
      return [value, () => {}]
    },
    useEffect: (callback) => {
      effects.push(callback)
    },
    useMemo: (factory) => factory(),
    useCallback: (callback) => callback,
  }
}

/** Evaluate `lib/client.js` the way the module loader does, and hand back its exports. */
function mountClient() {
  let registration
  const React = stubReact()
  const globalScope = {
    __ModuleLoader__: {
      load: (row) => {
        registration = row
      },
    },
  }
  // The file is a script, not a module: it talks to `window` and expects a CJS factory.
  const factory = new Function('window', `${SOURCE}\nreturn window.__ModuleLoader__`)
  const loader = factory(globalScope)
  assert.ok(registration, 'the file registered itself with the module loader')
  assert.equal(typeof registration.factory, 'function')
  assert.equal(loader, globalScope.__ModuleLoader__)
  const exports = registration.factory((spec) => {
    if (spec === 'react') return React
    throw new Error(`require("${spec}") missed the module table`)
  })
  return { id: registration.id, exports, React }
}

/**
 * A context shaped like the client one, with the two guarded seats the kernel proxies.
 *
 * `overrideTokens` rejects a bare-string value exactly as the real theme service does, and
 * `slots.register` refuses an options object without a `name` — both copied from
 * `dsh-cordis-client-runner` / `dsh-client-ui-theme` so the assertions below mean something.
 */
function stubClientContext(settings = {}) {
  const calls = { tokens: [], registrations: [], injected: [], effects: [], subscribed: 0, binds: [], logs: [] }
  let stored = { ...DEFAULTS, enabled: true, ...settings }
  const listeners = new Set()
  const scope = {
    getSnapshot: () => ({ value: stored, writable: true, status: 'ready' }),
    subscribe: (listener) => {
      calls.subscribed += 1
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    set: (field, value) => {
      calls.writes = calls.writes ?? []
      calls.writes.push([field, value])
      stored = { ...stored, [field]: value }
      return Promise.resolve()
    },
  }
  const ctx = {
    logger: {
      info: (message) => calls.logs.push(['info', message]),
      warn: (message) => calls.logs.push(['warn', message]),
    },
    effect: (callback, label) => {
      calls.effects.push(label)
      const dispose = callback()
      return () => {
        if (typeof dispose === 'function') dispose()
      }
    },
    settingsScope: {
      bind: (spec) => {
        calls.binds.push(spec)
        return scope
      },
    },
    theme: {
      overrideTokens: (source, tokens) => {
        for (const [token, value] of Object.entries(tokens)) {
          if (typeof value === 'string') {
            throw new TypeError(`theme override "${token}" from "${source}" is a bare string — pass { light, dark }`)
          }
          if (typeof value !== 'object' || value === null || typeof value.light !== 'string' || typeof value.dark !== 'string') {
            throw new TypeError(`theme override "${token}" from "${source}" must map to a { light, dark } pair of strings`)
          }
        }
        calls.tokens.push({ source, tokens })
        return () => {}
      },
    },
    locale: {
      bind: () => (key, params) => (typeof params === 'object' && params !== null ? `${key}` : String(key)),
      register: (ns, dictionaries) => {
        calls.locale = { ns, dictionaries }
        return () => {}
      },
    },
    slots: {
      inject: (key, generator) => {
        // The real `slots.inject` runs the generator once and hands each yielded disposer to
        // the fiber, so running it here is what makes a registration observable at all.
        calls.injected = calls.injected ?? []
        calls.injected.push(key)
        const disposers = [...generator()]
        return () => {
          for (const dispose of disposers) if (typeof dispose === 'function') dispose()
        }
      },
      register: (options, component) => {
        if (!options || typeof options.name !== 'string') throw new Error('slots.register(options, component) needs an options object with a `name`')
        calls.registrations.push({ options, component })
        return () => {}
      },
    },
    connection: {},
    remote: { $on: () => () => {} },
  }
  return { ctx, calls, scope }
}

/** Install the two DOM globals the half needs, and restore them afterwards. */
function withDom(run) {
  const head = { children: [], appendChild(child) { this.children.push(child) } }
  const classes = new Set()
  const body = {
    classList: {
      toggle: (name, on) => (on ? classes.add(name) : classes.delete(name)),
      contains: (name) => classes.has(name),
      remove: (name) => classes.delete(name),
    },
    dataset: {},
  }
  const created = []
  const previous = { document: globalThis.document }
  globalThis.document = {
    head,
    body,
    createElement: (tag) => {
      const node = { tag, id: '', textContent: '', remove: () => { created.push(tag) } }
      return node
    },
  }
  try {
    return run({ head, body, classes, created })
  } finally {
    globalThis.document = previous.document
  }
}

test('the browser half declares the services it reaches for', () => {
  const { id, exports } = mountClient()

  assert.equal(id, 'physearth-geoai')
  for (const service of ['settingsScope', 'slots', 'theme', 'locale']) {
    assert.ok(exports.inject.includes(service), service)
  }
  // The settings scope resolves its transport and invalidation feed through the *caller's*
  // context, so these two have to be in scope even though this file never reads them.
  assert.ok(exports.inject.includes('connection'))
  assert.ok(exports.inject.includes('remote'))
  assert.equal(typeof exports.apply, 'function')
})

test('the accent ids the card offers are the ones the host half validates', () => {
  const { exports } = mountClient()

  assert.deepEqual(exports.ACCENTS.map((item) => item.id), ACCENTS)
})

test('every token override is a { light, dark } pair, which is what the theme service demands', () => {
  const { exports } = mountClient()

  for (const accent of ACCENTS) {
    for (const colorScheme of ['dark', 'light']) {
      const tokens = exports.themeTokens({ accent, colorScheme })
      const names = Object.keys(tokens)
      assert.equal(names.length, exports.TOKEN_NAMES.length, `${accent}/${colorScheme}`)
      for (const [token, value] of Object.entries(tokens)) {
        assert.match(token, /^--/, token)
        assert.equal(typeof value.light, 'string', `${token} light`)
        assert.equal(typeof value.dark, 'string', `${token} dark`)
      }
      // The accent is a real choice: two accents must not produce the same primary fill.
      assert.ok(names.includes('--dsw-alias-brand-primary'))
    }
  }
  assert.notEqual(
    exports.themeTokens({ accent: 'ice' })['--dsw-alias-brand-primary'].dark,
    exports.themeTokens({ accent: 'amber' })['--dsw-alias-brand-primary'].dark,
  )
})

test('the accent decides the fill and the text that sits on it, per exposure', () => {
  const { exports } = mountClient()

  const ice = exports.accentPaint({ accent: 'ice', colorScheme: 'dark' })
  const amber = exports.accentPaint({ accent: 'amber', colorScheme: 'dark' })
  assert.equal(ice.fill, '#22d3ee')
  assert.equal(ice.onFill, '#04121a')
  assert.notEqual(amber.fill, ice.fill)
  // An unknown accent is not a crash: it is the default.
  assert.equal(exports.accentPaint({ accent: 'neon', colorScheme: 'dark' }).fill, ice.fill)
  // The light exposure is tuned separately rather than reusing the dark fill.
  assert.notEqual(exports.accentPaint({ accent: 'ice', colorScheme: 'light' }).fill, ice.fill)
})

test('the stylesheet carries the accent and stays scoped to the enabled class', () => {
  const { exports } = mountClient()

  const css = exports.stylesheet(exports.accentPaint({ accent: 'amber', colorScheme: 'dark' }))
  assert.match(css, /body\.geoai-restyled/)
  assert.match(css, /#f59e0b/)
  assert.match(css, /prefers-reduced-motion: reduce/)
  // The card must be readable with the restyle off, because it is the way back on.
  assert.match(css, /\.geoai-card \{/)
  assert.match(css, /\.geoai-switch \{/)
})

test('apply() binds the settings namespace and applies the token layer', () => {
  const { exports } = mountClient()
  const { ctx, calls } = stubClientContext()

  withDom(() => exports.apply(ctx))

  assert.deepEqual(calls.binds, [{ namespace: 'physearth-geoai' }])
  assert.equal(calls.tokens.length, 1)
  assert.equal(calls.tokens[0].source, 'physearth-geoai')
  assert.ok(Object.keys(calls.tokens[0].tokens).length >= 40)
})

test('the restyle is a body class, so the switch is visible and reversible', () => {
  const { exports } = mountClient()
  const { ctx, calls } = stubClientContext({ enabled: true, restyleHost: true })

  withDom((dom) => {
    exports.apply(ctx)
    assert.ok(dom.classes.has('geoai-restyled'), 'enabled turns the restyle on')
    assert.ok(calls.effects.some((label) => /stylesheet/.test(label)))
  })
})

test('the restyle stays off when the plugin is off, and the card stays styleable', () => {
  const { exports } = mountClient()
  const { ctx, calls } = stubClientContext({ enabled: false })

  withDom((dom) => {
    exports.apply(ctx)
    assert.equal(dom.classes.has('geoai-restyled'), false, 'disabled leaves the shell alone')
    assert.equal(dom.body.dataset.geoaiEnabled, 'false')
    assert.equal(calls.subscribed, 2, 'the token layer and the stylesheet both follow the settings')
  })
})

test('the card registers into settings.plugin.item with the fields the plugin tab reads', () => {
  const { exports } = mountClient()
  const { ctx, calls } = stubClientContext()

  withDom(() => exports.apply(ctx))

  const injected = calls.injected.includes('settings.plugin.item')
  assert.ok(injected, 'the slot was injected, not merely registered')
  const options = calls.registrations[0].options
  assert.equal(options.name, 'settings.plugin.item')
  // `key` is what the plugins tab matches a host-served namespace against, so a wrong key means
  // a card that never appears, with nothing logged.
  assert.equal(options.key, 'physearth-geoai')
  assert.equal(options.id, 'physearth-geoai')
  assert.ok(Number.isFinite(options.order))
  assert.equal(typeof options.label, 'function')
})

test('the switch writes the host half\u2019s enabled setting, which is what moves the tools', async () => {
  const { exports, React } = mountClient()
  const { ctx, calls, scope } = stubClientContext({ enabled: false })

  withDom(() => exports.apply(ctx))
  const { component } = calls.registrations[0]
  assert.ok(component, 'a component was registered')

  const tree = component({ scope })
  React.__effects.forEach((effect) => effect())

  // Find the switch by role rather than by position: it is the only role="switch" control.
  // The stub React has no renderer, so a function component stays an element until it is
  // expanded by hand — which is why this is a walk and not a shallow read of the tree.
  const buttons = []
  const walk = (node) => {
    if (!node || typeof node !== 'object') return
    if (node.__el && typeof node.type === 'function') {
      walk(node.type(node.props))
      return
    }
    if (node.__el && node.type === 'button') buttons.push(node)
    const children = node.props?.children
    for (const child of Array.isArray(children) ? children : [children]) if (child) walk(child)
  }
  walk(tree)

  const control = buttons.find((button) => button.props.role === 'switch')
  assert.ok(control, 'the card renders a switch')
  assert.equal(control.props['aria-checked'], 'false')
  assert.match(control.props.className, /geoai-switch/)

  control.props.onClick()
  await Promise.resolve()
  assert.deepEqual(calls.writes, [['enabled', true]])
})
