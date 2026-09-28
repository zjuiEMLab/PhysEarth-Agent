// What can be verified without a DeepSeek Harness runtime: the plugin's own logic, and the
// shape of the three files a host loads (manifest, bundle patch, client bundle). Everything
// that needs the harness (loader toggle, theme cascade, visual acceptance) is listed in the
// README as a runtime step, not faked here.

import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import {
  ACCENTS,
  BASE_TOKENS,
  DEFAULTS,
  HOST_TOKEN_OVERRIDES,
  auditFields,
  bridgeCommand,
  normaliseSettings,
  portOf,
  resultHeadline,
  resultTone,
  themeTokens,
  themeId,
  toolCard,
} from '../lib/logic.js'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')

test('the plugin ships off, so mounting it changes nothing until a user asks', () => {
  assert.equal(DEFAULTS.enabled, false)
  assert.equal(DEFAULTS.approveRuns, false)
  assert.equal(DEFAULTS.restyleHost, true)
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

test('booleans and paths are coerced, so a settings document written by hand still loads', () => {
  const { settings } = normaliseSettings({ enabled: 1, approveRuns: 'yes', projectRoot: '  /tmp/x  ', pythonCmd: '  ' })

  assert.equal(settings.enabled, true)
  assert.equal(settings.approveRuns, true)
  assert.equal(settings.projectRoot, '/tmp/x')
  assert.equal(settings.pythonCmd, DEFAULTS.pythonCmd)
})

test('theme tokens carry the base surfaces plus exactly one accent', () => {
  const ice = themeTokens({ accent: 'ice' })
  const amber = themeTokens({ accent: 'amber' })

  assert.equal(ice['--geoai-bg'], BASE_TOKENS['--geoai-bg'])
  assert.equal(ice['--geoai-accent'], '#22d3ee')
  assert.equal(amber['--geoai-accent'], '#f59e0b')
  assert.notEqual(ice['--geoai-accent'], amber['--geoai-accent'])
  assert.equal(themeId({ accent: 'amber' }), 'geoai-amber')
})

test('only token names the theme directory declares are overridden', () => {
  // Three names verified present in the shipped token sheets; a fourth would be rejected by
  // the theme service at runtime, so it must not appear here silently.
  assert.deepEqual(Object.keys(HOST_TOKEN_OVERRIDES).sort(), [
    '--dsw-alias-scrollbar-thumb',
    '--dsw-alias-scrollbar-thumb-hover',
    '--dsw-elevation-stroke-color',
  ])
})

test('the bridge command matches the address the settings name', () => {
  const spec = bridgeCommand({ pythonCmd: 'python3', bridgeUrl: 'http://127.0.0.1:9123', projectRoot: '/repo' })

  assert.equal(spec.command, 'python3')
  assert.deepEqual(spec.args, ['-m', 'integrations.geoai', 'serve-http', '--host', '127.0.0.1', '--port', '9123'])
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

  assert.match(patch, /id: geoai\b/)
  assert.match(patch, /name: dsh-plugin-physearth-geoai/)
  assert.match(patch, /id: mcp-geoai/)
  assert.match(patch, /@deepseek-ai\/dsh-mcp-client/)
  assert.match(patch, /serverName: geoai/)
  assert.match(patch, /command: python/)
  assert.match(patch, /args: \['-m', 'integrations\.geoai', 'serve'\]/)
  // Off by default, and the checkout path is a placeholder a human must resolve.
  assert.match(patch, /enabled: false/)
  assert.match(patch, /REPLACE_WITH_CHECKOUT/)
})

test('the manifest points a host at the two halves it loads', () => {
  const manifest = JSON.parse(readFileSync(join(ROOT, 'package.json'), 'utf8'))

  assert.equal(manifest.main, 'entry.js')
  assert.equal(manifest.dsh.bundle.patch, './cordis.patch.yml')
  assert.equal(manifest.dsh.client.platform, 'web')
  assert.equal(manifest.exports['./client'], './lib/client.js')
  assert.ok(manifest.dsh.client.inject.includes('@deepseek-ai/dsh-client-ui-settings'))
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
  assert.match(client, /classList\.remove\('geoai-restyled'\)/)
  assert.match(client, /style\.remove\(\)/)
})

test('the stylesheet is scoped to the enabled class and respects reduced motion', () => {
  const css = readFileSync(join(ROOT, 'lib', 'client.css.js'), 'utf8')

  assert.match(css, /body\.geoai-restyled/)
  assert.match(css, /prefers-reduced-motion: reduce/)
  assert.match(css, /focus-visible/)
  // Mobile first, then one relaxation at the tablet breakpoint.
  assert.match(css, /grid-template-columns: 1fr/)
  assert.match(css, /@media \(min-width: 768px\)/)
  assert.doesNotMatch(css, /\u{1F300}-\u{1FAFF}/u, 'no emoji as icons')
})
