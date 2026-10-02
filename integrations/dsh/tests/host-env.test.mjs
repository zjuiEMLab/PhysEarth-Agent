// Where the checkout is, and which Python can import it.
//
// Both answers used to be written into the patch layer as `REPLACE_WITH_CHECKOUT`, and a live
// boot showed why that cannot work: the harness replaces a row's whole `config` when a later
// layer targets it by id, so a placeholder forces every installer to restate the row. The two
// resolvers below are therefore real code, and these are their cases.

import assert from 'node:assert/strict'
import { join } from 'node:path'
import test from 'node:test'

import {
  CHECKOUT_MARKERS,
  PROMPT_SCOPES,
  PROMPT_SCOPE_ARGS,
  checkoutCandidates,
  findCheckout,
  interpreterCandidates,
  interpreterProvenance,
  pickInterpreter,
  readPromptStack,
} from '../lib/host-env.js'
import { DEFAULTS, PROMPT_DEPTHS, bridgeCommand, engineEnv } from '../lib/logic.js'

test('the checkout markers are files a checkout cannot lack', () => {
  assert.ok(CHECKOUT_MARKERS.length >= 2)
  for (const marker of CHECKOUT_MARKERS) {
    assert.match(marker, /\//)
    assert.doesNotMatch(marker, /^\//)
  }
})

test('candidates walk up from every starting point and end with the working directory', () => {
  const candidates = checkoutCandidates(['/a/b/c'], '/w')

  assert.equal(candidates[0], '/a/b/c')
  assert.ok(candidates.includes('/a/b'))
  assert.ok(candidates.includes('/a'))
  assert.equal(candidates.at(-1), '/w')
  // De-duplicated, so an ancestor shared by two starting points appears once.
  assert.equal(new Set(candidates).size, candidates.length)
})

test('a symlinked package finds the checkout it was installed from', () => {
  // The package lives at <checkout>/integrations/dsh, so two levels up is the checkout.
  const checkout = '/repo'
  const exists = (path) => CHECKOUT_MARKERS.some((marker) => path === join(checkout, marker))

  assert.equal(findCheckout({ startDirs: ['/repo/integrations/dsh'], cwd: '/elsewhere', exists }), checkout)
})

test('a copied package falls back to the working directory', () => {
  const checkout = '/repo'
  const exists = (path) => CHECKOUT_MARKERS.some((marker) => path === join(checkout, marker))

  assert.equal(
    findCheckout({ startDirs: ['/home/me/.dsh/profiles/web/node_modules/pkg'], cwd: checkout, exists }),
    checkout,
  )
})

test('a directory that is not a checkout is not reported as one', () => {
  assert.equal(findCheckout({ startDirs: ['/tmp/x'], cwd: '/tmp', exists: () => false }), undefined)
  // Two markers are required, so a directory holding only one of them does not qualify.
  const half = (path) => path === '/repo/src/physearth/__init__.py' || path === '/repo/src'
  assert.equal(findCheckout({ startDirs: ['/repo/src'], cwd: '/repo', exists: half }), undefined)
})

test('an explicit interpreter is tried before the environment and the defaults', () => {
  const candidates = interpreterCandidates({ configured: '/opt/py', checkout: '/repo', env: { PHYSEARTH_PYTHON: '/env/py' } })

  assert.equal(candidates[0], '/opt/py')
  assert.equal(candidates[1], '/env/py')
  assert.equal(candidates[2], join('/repo', '.venv', 'bin', 'python'))
  assert.deepEqual(candidates.slice(-2), ['python3', 'python'])
})

test('the schema default is not mistaken for an explicit choice', () => {
  // `python3` is what the Config schema defaults to; treating it as an explicit choice would
  // park it above PHYSEARTH_PYTHON and a checkout virtualenv.
  const candidates = interpreterCandidates({ configured: 'python3', checkout: '/repo', env: { PHYSEARTH_PYTHON: '/env/py' } })

  assert.equal(candidates[0], '/env/py')
  assert.equal(candidates.at(-1), 'python')
})

test('an interpreter is chosen only after it proves it can import the engine', () => {
  const tried = []
  const chosen = pickInterpreter({
    candidates: ['python3', 'python', '/opt/py'],
    probe: (command) => {
      tried.push(command)
      return command === '/opt/py'
    },
  })

  assert.equal(chosen, '/opt/py')
  assert.deepEqual(tried, ['python3', 'python', '/opt/py'])
  assert.equal(pickInterpreter({ candidates: ['python3'], probe: () => false }), undefined)
  assert.match(interpreterProvenance('/opt/py', 3), /\/opt\/py/)
  assert.match(interpreterProvenance(undefined, 3), /no candidate/)
})

test('the bridge child inherits a PYTHONPATH that can reach the engine', () => {
  // `-m integrations.geoai` puts the cwd on sys.path, which finds `integrations` but not
  // `physearth` — the engine lives under src/. Without this the child died with
  // ModuleNotFoundError inside a stdio:'ignore' spawn and the plugin only ever reported a
  // bridge that did not answer.
  assert.deepEqual(engineEnv('/repo'), { PYTHONPATH: '/repo/src:/repo', PYTHONUNBUFFERED: '1' })
  assert.deepEqual(engineEnv(''), {})

  const spec = bridgeCommand({ pythonCmd: '/opt/py', bridgeUrl: 'http://127.0.0.1:8799', projectRoot: '/repo' })
  assert.equal(spec.command, '/opt/py')
  assert.deepEqual(spec.args, ['-m', 'integrations.geoai', 'serve-http', '--host', '127.0.0.1', '--port', '8799', '--approval', 'ask'])
  assert.equal(spec.cwd, '/repo')
  assert.equal(spec.env.PYTHONPATH, '/repo/src:/repo')
})

test('each prompt depth asks the engine for a scope, and the cheap one asks for nothing', () => {
  // The map is the card's contract with the engine: `compact` is text this plugin writes
  // itself, so it must *not* look like a fetch, and every other depth must name a scope the
  // engine publishes. `python -m integrations.geoai prompt --list` is where those come from.
  assert.equal(PROMPT_SCOPE_ARGS.compact, null)
  assert.equal(PROMPT_SCOPE_ARGS.rules, 'rules')
  assert.equal(PROMPT_SCOPE_ARGS.full, 'identity,rules,context')
  for (const [depth, scopes] of Object.entries(PROMPT_SCOPE_ARGS)) {
    assert.ok(PROMPT_DEPTHS.includes(depth), `${depth} is offered by the card`)
    if (scopes === null) continue
    for (const scope of scopes.split(',')) {
      assert.ok(PROMPT_SCOPES.includes(scope), `${scope} is a scope the engine publishes`)
    }
  }
  // The default is not `full`: that scope is 24k characters of model and corpus context that the
  // same session can also read through the tools, and `identity` would replace the host's own.
  assert.equal(DEFAULTS.promptDepth, 'rules')
  assert.ok(!PROMPT_SCOPE_ARGS[DEFAULTS.promptDepth].includes('identity'))
})

test('the prompt fetch asks the engine with the scopes and the PYTHONPATH it needs', () => {
  const seen = []
  const run = (command, args, options) => {
    seen.push({ command, args, options })
    return { status: 0, stdout: 'RULES\n', stderr: '' }
  }
  const result = readPromptStack({
    pythonCmd: '/opt/py',
    checkout: '/repo',
    scope: 'rules',
    env: { HOME: '/home/x' },
    run,
  })

  assert.equal(result.text, 'RULES')
  assert.match(result.detail, /\/opt\/py/)
  assert.equal(seen.length, 1)
  assert.equal(seen[0].command, '/opt/py')
  assert.deepEqual(seen[0].args, ['-m', 'integrations.geoai', 'prompt', '--scopes', 'rules'])
  assert.equal(seen[0].options.cwd, '/repo')
  // Same reason as the bridge: `-m integrations.geoai` finds `integrations` through the cwd,
  // and the engine itself lives under src/.
  assert.equal(seen[0].options.env.PYTHONPATH, '/repo/src:/repo')
  assert.equal(seen[0].options.env.HOME, '/home/x', 'the rest of the environment is inherited')
})

test('a prompt fetch that fails says why, and never invents text', () => {
  const failing = () => ({ status: 3, stdout: '', stderr: 'line one\nboom: no engine\n' })
  assert.throws(
    () => readPromptStack({ pythonCmd: '/opt/py', checkout: '/repo', scope: 'rules', run: failing }),
    /exit 3.*boom: no engine/,
  )
  const silent = () => ({ status: 0, stdout: '   \n', stderr: '' })
  assert.throws(
    () => readPromptStack({ pythonCmd: '/opt/py', checkout: '/repo', scope: 'rules', run: silent }),
    /printed nothing/,
  )
  const missing = () => ({ status: 1, stdout: '', stderr: '', error: new Error('spawn ENOENT') })
  assert.throws(
    () => readPromptStack({ pythonCmd: '/opt/py', checkout: '/repo', scope: 'rules', run: missing }),
    /ENOENT/,
  )
  // And the two ways of asking for nothing are refused rather than silently answered with ''.
  assert.throws(
    () => readPromptStack({ pythonCmd: '/opt/py', checkout: '/repo', scope: 'compact', run: failing }),
    /does not ask the engine/,
  )
  assert.throws(
    () => readPromptStack({ pythonCmd: '', checkout: '/repo', scope: 'rules', run: failing }),
    /no interpreter or checkout/,
  )
})
