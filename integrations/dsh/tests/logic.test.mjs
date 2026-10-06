// What can be verified without a DeepSeek Harness runtime: the plugin's own logic, and the
// shape of the files a host loads (manifest, bundle patch, client bundle). Everything that
// needs the harness itself (the loader toggle, the theme cascade, visual acceptance) is a
// runtime step in the README, not faked here — but the *contracts* those steps exercise are
// pinned in `host.test.mjs` and `client.test.mjs`, because a wrong service method name fails
// silently rather than loudly and only a live browser would show it.

import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import {
  ACCENTS,
  DEFAULTS,
  PROMPT_DEPTHS,
  auditFields,
  bridgeCommand,
  normaliseSettings,
  portOf,
  resultHeadline,
  resultTone,
  toolCard,
} from '../lib/logic.js'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')

test('the plugin ships off, so mounting it changes nothing until a user asks', () => {
  assert.equal(DEFAULTS.enabled, false)
  assert.equal(DEFAULTS.approveRuns, false)
  assert.equal(DEFAULTS.restyleHost, true)
  assert.equal(DEFAULTS.autoStartBridge, false)
  assert.equal(DEFAULTS.colorScheme, 'dark')
  assert.deepEqual(ACCENTS, ['ice', 'amber', 'deep-blue'])
})

test('a non-loopback bridge address is refused instead of half-applied', () => {
  const { settings, warnings } = normaliseSettings({ bridgeUrl: 'http://10.0.0.5:8799' })

  assert.equal(settings.bridgeUrl, DEFAULTS.bridgeUrl)
  assert.equal(warnings.length, 1)
  assert.match(warnings[0], /not a loopback/)
})

test('a loopback address, including localhost and https, is kept', () => {
  assert.equal(normaliseSettings({ bridgeUrl: 'http://localhost:9000' }).settings.bridgeUrl, 'http://localhost:9000')
  assert.equal(normaliseSettings({ bridgeUrl: 'https://127.0.0.1:443' }).settings.bridgeUrl, 'https://127.0.0.1:443')
})

test('an unknown accent and an out-of-range timeout fall back with a reason', () => {
  const { settings, warnings } = normaliseSettings({ accent: 'neon', requestTimeoutMs: 5 })

  assert.equal(settings.accent, DEFAULTS.accent)
  assert.equal(settings.requestTimeoutMs, DEFAULTS.requestTimeoutMs)
  assert.equal(warnings.length, 2)
})

test('an unknown colour scheme falls back, but an absent one is not a warning', () => {
  assert.equal(normaliseSettings({ colorScheme: 'sepia' }).settings.colorScheme, 'dark')
  assert.equal(normaliseSettings({ colorScheme: 'sepia' }).warnings.length, 1)
  assert.equal(normaliseSettings({}).warnings.length, 0)
  assert.equal(normaliseSettings({ colorScheme: 'light' }).settings.colorScheme, 'light')
})

test('booleans and paths are coerced, so a settings document written by hand still loads', () => {
  const { settings } = normaliseSettings({ enabled: 1, approveRuns: 'yes', projectRoot: '  /tmp/x  ', pythonCmd: '  ' })

  assert.equal(settings.enabled, true)
  assert.equal(settings.approveRuns, true)
  assert.equal(settings.projectRoot, '/tmp/x')
  assert.equal(settings.pythonCmd, DEFAULTS.pythonCmd)
})

test('the bridge command matches the address the settings name', () => {
  const spec = bridgeCommand({ pythonCmd: 'python3', bridgeUrl: 'http://127.0.0.1:9123', projectRoot: '/repo' })

  assert.equal(spec.command, 'python3')
  assert.deepEqual(spec.args, ['-m', 'integrations.physearth', 'serve-http', '--host', '127.0.0.1', '--port', '9123', '--approval', 'ask'])
  assert.deepEqual(bridgeCommand({ pythonCmd: 'python3', approveRuns: true }).args.slice(-2), ['--approval', 'always'])
  assert.equal(spec.cwd, '/repo')
  assert.equal(portOf('not a url'), 8799)
})

test('the card shows the auditable fields before anything else', () => {
  const shown = auditFields({
    status: 'success',
    data: { handle: 'res_1', n_points: 20, units: 'K', qc: { passed: true } },
    citations: ['smrt-v1#08'],
  })

  assert.deepEqual(Object.keys(shown), ['handle', 'qc', 'citations', 'units', 'n_points'])
  assert.equal(shown.handle, 'res_1')
})

test('a refusal reads as a refusal, not as a result', () => {
  assert.equal(resultTone({ status: 'success' }), 'pass')
  assert.equal(resultTone({ status: 'needs_input' }), 'warn')
  assert.equal(resultTone({ status: 'terminal_error' }), 'block')
  assert.match(resultHeadline({ status: 'needs_input', error: 'density_kg_m3 = 2000.0 is outside 1.0 to 917.0' }), /^Refused:/)
  assert.match(resultHeadline({ status: 'terminal_error', error: 'no_credentials' }), /^Error:/)
})

test('tool cards exist for the tools a reviewer reads most', () => {
  for (const name of ['run_model', 'plot', 'research_plan', 'read_literature']) {
    const card = toolCard(name)
    assert.ok(card, name)
    assert.ok(card.title && card.icon && card.fields.length > 0, name)
  }
  assert.equal(toolCard('not_a_tool'), undefined)
})

test('the bundle patch mounts the plugin and the MCP row that brings the tools', () => {
  const patch = readFileSync(join(ROOT, 'cordis.patch.yml'), 'utf8')

  assert.match(patch, /id: physearth\b/)
  assert.match(patch, /name: dsh-plugin-physearth/)
  assert.match(patch, /id: mcp-physearth/)
  assert.match(patch, /@deepseek-ai\/dsh-mcp-client/)
  assert.match(patch, /serverName: physearth/)
  assert.match(patch, /command: python3/)
  assert.match(patch, /args: \['-m', 'integrations\.physearth', 'serve'\]/)
  // Off by default.
  assert.match(patch, /enabled: false/)
  // And no placeholder: a patch layer cannot carry an absolute checkout path, and a later
  // layer's `config` REPLACES this row's config rather than merging into it (the harness
  // composes layers with a shallow per-entry assignment), so a placeholder would force every
  // installer to restate the whole object. The row is complete and path-free instead, and
  // install.sh writes a complete override for a real machine.
  assert.doesNotMatch(patch, /REPLACE_WITH_CHECKOUT/)
  assert.doesNotMatch(patch, /projectRoot:/)
})

test('the manifest points a host at the two halves it loads', () => {
  const manifest = JSON.parse(readFileSync(join(ROOT, 'package.json'), 'utf8'))

  assert.equal(manifest.main, 'entry.js')
  assert.equal(manifest.dsh.bundle.patch, './cordis.patch.yml')
  assert.equal(manifest.dsh.client.platform, 'web')
  assert.equal(manifest.exports['./client'], './lib/client.js')
  assert.ok(manifest.dsh.client.inject.includes('@deepseek-ai/dsh-client-ui-settings'))
  // The client bundle is read and served verbatim by the module registry, so `files` has to
  // carry the whole of `lib/` — a published package missing it fails at boot, not at install.
  assert.ok(manifest.files.includes('lib'))
  assert.ok(manifest.files.includes('cordis.patch.yml'))
})

test('the client half is a self-contained factory that can be unloaded', () => {
  const client = readFileSync(join(ROOT, 'lib', 'client.js'), 'utf8')

  assert.match(client, /window\.__ModuleLoader__\.load\(/)
  assert.match(client, /factory: \(require\) =>/)
  assert.match(client, /exports\.apply = function apply\(ctx\)/)
  assert.match(client, /exports\.inject =/)
  // The switch lives in this plugin's own card, because the shipped Plugins section is read-only.
  assert.match(client, /settings\.plugin\.item/)
  // Everything the restyle adds is an effect, so a disable removes it.
  assert.match(client, /overrideTokens/)
  assert.match(client, /classList\.remove\('physearth-restyled'\)/)
  assert.match(client, /style\.remove\(\)/)
})

test('the client half requires nothing but its declared rows', () => {
  const source = readFileSync(join(ROOT, 'lib', 'client.js'), 'utf8')
  // Comments are stripped first: this file documents *why* a relative require would fail, and
  // that prose must not read as a call.
  const code = source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/[^\n]*/g, '$1')
  const required = [...code.matchAll(/require\((['"])([^'"]+)\1\)/g)].map((match) => match[2])

  // The module table answers `require` only for platform seed words and for rows already in
  // the boot graph, so a relative path — the obvious way to split a stylesheet out — would
  // miss the table and throw at load.
  assert.deepEqual([...new Set(required)], ['react'])
})

test('the stylesheet is scoped to the enabled class and respects reduced motion', () => {
  const client = readFileSync(join(ROOT, 'lib', 'client.js'), 'utf8')

  assert.match(client, /body\.physearth-restyled/)
  assert.match(client, /prefers-reduced-motion: reduce/)
  assert.match(client, /focus-visible/)
  // Mobile first, then two relaxations as room appears.
  assert.match(client, /grid-template-columns: 1fr/)
  assert.match(client, /@media \(min-width: 640px\)/)
  assert.match(client, /@media \(min-width: 1024px\)/)
  // A switch needs a touch target; iOS asks for 44 CSS pixels.
  assert.match(client, /min-height: 44px/)
  assert.doesNotMatch(client, /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u, 'no emoji as icons')
})

test('an unknown prompt depth falls back loudly, because it changes a prompt', () => {
  const { settings, warnings } = normaliseSettings({ promptDepth: 'everything' })
  assert.equal(settings.promptDepth, DEFAULTS.promptDepth)
  assert.equal(DEFAULTS.promptDepth, 'rules')
  assert.ok(warnings.some((line) => /promptDepth/.test(line)), 'a prompt that silently changes is the worst kind')

  // A known depth is passed through, and an absent one is a default rather than a warning.
  assert.equal(normaliseSettings({ promptDepth: 'full' }).settings.promptDepth, 'full')
  assert.equal(normaliseSettings({ promptDepth: 'off' }).settings.promptDepth, 'off')
  assert.equal(normaliseSettings({}).warnings.length, 0)
  assert.deepEqual(PROMPT_DEPTHS, ['compact', 'rules', 'full', 'off'])
})

test('the card offers exactly the prompt depths the host half understands', () => {
  const client = readFileSync(join(ROOT, 'lib', 'client.js'), 'utf8')

  // The two halves cannot import each other, so the same list ships twice. A depth offered here
  // and unknown to the host is a select whose value is silently coerced back on every write —
  // the card would appear to work and change nothing.
  const offered = [...client.matchAll(/id: '([a-z-]+)', label: '[^']*', hint: '/g)].map((match) => match[1])
  for (const depth of PROMPT_DEPTHS) {
    assert.ok(offered.includes(depth), `the card offers ${depth}`)
  }
  // And the card's own defaults carry the key, or readSettings would drop the user's choice.
  assert.match(client, /promptDepth: 'rules'/)
  assert.match(client, /write\('promptDepth'/)
})
