// Pure plugin logic: settings, theme tokens, tool cards, bridge routes.
//
// Free of Cordis and of the DOM on purpose, so `node --test tests/` can run it on this
// checkout and so the host half, the browser half and the tests read one definition of
// what the plugin is. The halves are otherwise split by the platform boundary: the host
// registers capabilities, the browser renders and configures.

export const DEFAULTS = Object.freeze({
  /** The one switch: off means the plugin contributes nothing, tools included. */
  enabled: false,
  /** Loopback address of the Python bridge (`python -m integrations.geoai serve-http`). */
  bridgeUrl: 'http://127.0.0.1:8799',
  /** Start the bridge from this plugin when it is not answering yet. */
  autoStartBridge: true,
  /** Python executable used for that, relative or absolute. */
  pythonCmd: 'python',
  /** Repository root the bridge is started in; empty means "inherit the host cwd". */
  projectRoot: '',
  /** Whether this deployment owns the human approval step for physical model runs. */
  approveRuns: false,
  /** Visual accent of the Geo-AI surface. */
  accent: 'ice',
  /**
   * Which exposure the accent was tuned against.
   *
   * The token layer carries both modes, so the host picks per user preference; this only says
   * whether the *accent* was mixed for a dark or a light field, which decides the fill and
   * the text that sits on it.
   */
  colorScheme: 'dark',
  /** Restyle the host interface while enabled, or only add the Geo-AI cards. */
  restyleHost: true,
  /** Milliseconds before a bridge call is reported as unreachable. */
  requestTimeoutMs: 120000,
})

export const ACCENTS = ['ice', 'amber', 'deep-blue']

/** Engine tools this plugin surfaces, in the order a reviewer reads them. */
export const ENGINE_TOOLS = [
  'list_models',
  'run_model',
  'run_planned_model',
  'plot',
  'plot_planned_chart',
  'research_plan',
  'list_literature',
  'read_literature',
  'read_reference_dataset',
]

export const HOST_TOOLS = ['geoai_health', 'geoai_ask', 'geoai_evidence', 'geoai_plan_status', 'geoai_review']

/** Short labels and tones for the run-trace cards the browser half draws. */
export const TOOL_CARDS = {
  run_model: { title: 'Physical model run', icon: 'activity', fields: ['model', 'version', 'handle', 'n_points', 'units'] },
  run_planned_model: { title: 'Planned run', icon: 'route', fields: ['planned_run_id', 'model', 'handle'] },
  plot: { title: 'Figure', icon: 'chart', fields: ['figure_number', 'series'] },
  plot_planned_chart: { title: 'Figure', icon: 'chart', fields: ['planned_chart_id', 'figure_number'] },
  research_plan: { title: 'Research plan', icon: 'clipboard', fields: ['phase', 'plan_version'] },
  list_models: { title: 'Registered models', icon: 'database', fields: ['name', 'version', 'runnable_here'] },
  read_literature: { title: 'Evidence read', icon: 'book', fields: ['slug', 'section_id', 'title'] },
  read_reference_dataset: { title: 'Measurement read', icon: 'ruler', fields: ['dataset', 'rows'] },
  geoai_ask: { title: 'Geo-AI question', icon: 'sparkles', fields: ['session_id', 'counters'] },
  geoai_evidence: { title: 'Evidence gathered', icon: 'shield', fields: ['counts'] },
}

/** Result fields a reviewer must be able to audit without opening the raw payload. */
export const AUDITABLE_FIELDS = ['handle', 'qc', 'citations', 'units', 'n_points', 'planned_run_id']

export function isLoopback(url) {
  try {
    const parsed = new URL(url)
    return (
      (parsed.protocol === 'http:' || parsed.protocol === 'https:') &&
      ['127.0.0.1', 'localhost', '::1'].includes(parsed.hostname)
    )
  } catch {
    return false
  }
}

/**
 * Coerce whatever the settings document holds into something usable.
 *
 * A wrong bridge address is the one value that would make every tool fail silently, so it
 * falls back to the default and says why. The bridge is loopback-only by design, so a
 * public address is refused rather than "fixed" into shape.
 */
export function normaliseSettings(raw, fallback = DEFAULTS) {
  const warnings = []
  const merged = { ...fallback, ...(raw || {}) }

  if (!isLoopback(merged.bridgeUrl)) {
    warnings.push(`bridgeUrl ${JSON.stringify(merged.bridgeUrl)} is not a loopback http(s) address; using ${fallback.bridgeUrl}`)
    merged.bridgeUrl = fallback.bridgeUrl
  }
  if (!ACCENTS.includes(merged.accent)) {
    warnings.push(`accent ${JSON.stringify(merged.accent)} is unknown; using ${fallback.accent}`)
    merged.accent = fallback.accent
  }
  if (merged.colorScheme !== 'dark' && merged.colorScheme !== 'light') {
    if (merged.colorScheme !== undefined && merged.colorScheme !== '') {
      warnings.push(`colorScheme ${JSON.stringify(merged.colorScheme)} is neither dark nor light; using ${fallback.colorScheme}`)
    }
    merged.colorScheme = fallback.colorScheme
  }
  const timeout = Number(merged.requestTimeoutMs)
  if (!Number.isFinite(timeout) || timeout < 1000 || timeout > 600000) {
    warnings.push(`requestTimeoutMs ${JSON.stringify(merged.requestTimeoutMs)} is outside 1000-600000; using ${fallback.requestTimeoutMs}`)
    merged.requestTimeoutMs = fallback.requestTimeoutMs
  } else {
    merged.requestTimeoutMs = Math.round(timeout)
  }
  merged.pythonCmd = String(merged.pythonCmd || fallback.pythonCmd).trim() || fallback.pythonCmd
  merged.projectRoot = String(merged.projectRoot || '').trim()
  merged.enabled = Boolean(merged.enabled)
  merged.restyleHost = Boolean(merged.restyleHost)
  merged.approveRuns = Boolean(merged.approveRuns)
  merged.autoStartBridge = Boolean(merged.autoStartBridge)
  return { settings: merged, warnings }
}

/**
 * Accent palettes, in the shape the host theme service actually accepts.
 *
 * `theme.overrideTokens(source, tokens)` takes token-name → `{ light, dark }` value pairs and
 * throws a teaching error on a bare string, because a single value goes illegible the moment
 * the user flips the colour scheme. So every accent below carries both modes.
 *
 * The two modes are not the same design in different greys. The dark mode is the one this
 * plugin is designed for: an OLED-grade near-black field for numbers people stare at, one
 * accent that says which half of the corpus you are looking at. The light mode is a daylight
 * version of the same identity rather than a fallback, because a user who reads in light mode
 * should still be able to tell the plugin is on.
 *
 * The accent names follow the subject matter: ice for the microwave/cold-region half of the
 * corpus, amber for the hydrological half, deep blue for a neutral default.
 */
/**
 * Palette, stylesheet and token layer deliberately live in `lib/client.js`, not here.
 *
 * Every one of them is presentational, only the browser half can apply them, and a client
 * bundle cannot value-import a sibling file — so keeping them here would mean shipping the
 * same data twice and having one copy silently drift. What stays here is what the two halves
 * genuinely share: the settings shape and its coercion, the tool surface, and the bridge
 * routes. `tests/logic.test.mjs` pins the accent ids and the settings keys on both sides.
 */

export function toolCard(name) {
  return TOOL_CARDS[name] || undefined
}

/** Fields worth showing before the raw payload, in reading order. */
export function auditFields(result) {
  if (!result || typeof result !== 'object') return {}
  const data = result.data && typeof result.data === 'object' ? result.data : {}
  const shown = {}
  for (const field of AUDITABLE_FIELDS) {
    if (result[field] !== undefined) shown[field] = result[field]
    else if (data[field] !== undefined) shown[field] = data[field]
  }
  return shown
}

/**
 * What the browser shows for one bridge result.
 *
 * A refusal is not decoration: the card has to say "nothing was computed" and keep the
 * engine's own wording, because a run that never happened must not look like a run.
 */
export function resultTone(result) {
  if (!result || typeof result !== 'object') return 'neutral'
  if (result.status === 'success') return 'pass'
  if (result.status === 'needs_input') return 'warn'
  if (result.status === 'terminal_error') return 'block'
  return 'neutral'
}

export function resultHeadline(result) {
  if (!result || typeof result !== 'object') return 'No result'
  if (result.status === 'success') return result.summary || 'Completed'
  if (result.status === 'needs_input') return `Refused: ${result.error || result.summary || 'input required'}`
  if (result.status === 'terminal_error') return `Error: ${result.error || result.summary || 'failed'}`
  return result.summary || String(result.status || 'unknown')
}

export const BRIDGE_ROUTES = Object.freeze({
  health: '/health',
  tools: '/tools',
  models: '/models',
  knowledge: '/knowledge',
  prompt: '/prompt',
  session: '/session',
  call: '/call',
  ask: '/ask',
  evidence: '/evidence',
  plan: '/plan',
  review: '/review',
})

export function portOf(bridgeUrl) {
  try {
    const parsed = new URL(bridgeUrl)
    if (parsed.port) return Number(parsed.port)
    return parsed.protocol === 'https:' ? 443 : 80
  } catch {
    return 8799
  }
}

/** The bridge command this plugin starts when nothing is listening yet. */
export function bridgeCommand(settings) {
  return {
    command: settings.pythonCmd,
    args: ['-m', 'integrations.geoai', 'serve-http', '--host', '127.0.0.1', '--port', String(portOf(settings.bridgeUrl))],
    cwd: settings.projectRoot || undefined,
  }
}
