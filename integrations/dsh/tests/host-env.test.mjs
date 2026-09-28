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
  checkoutCandidates,
  findCheckout,
  interpreterCandidates,
  interpreterProvenance,
  pickInterpreter,
} from '../lib/host-env.js'
import { bridgeCommand, engineEnv } from '../lib/logic.js'

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
  const half = (path) => path === '/repo/backend/physearth/__init__.py' || path === '/repo/backend'
  assert.equal(findCheckout({ startDirs: ['/repo/backend'], cwd: '/repo', exists: half }), undefined)
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
  // `physearth` — the engine lives under backend/. Without this the child died with
  // ModuleNotFoundError inside a stdio:'ignore' spawn and the plugin only ever reported a
  // bridge that did not answer.
  assert.deepEqual(engineEnv('/repo'), { PYTHONPATH: '/repo/backend:/repo', PYTHONUNBUFFERED: '1' })
  assert.deepEqual(engineEnv(''), {})

  const spec = bridgeCommand({ pythonCmd: '/opt/py', bridgeUrl: 'http://127.0.0.1:8799', projectRoot: '/repo' })
  assert.equal(spec.command, '/opt/py')
  assert.deepEqual(spec.args, ['-m', 'integrations.geoai', 'serve-http', '--host', '127.0.0.1', '--port', '8799'])
  assert.equal(spec.cwd, '/repo')
  assert.equal(spec.env.PYTHONPATH, '/repo/backend:/repo')
})
