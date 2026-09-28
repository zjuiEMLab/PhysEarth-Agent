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
 * Accent palettes as design-system values rather than inline literals in the host.
 *
 * The base is a dark, high-contrast surface for numbers people stare at, with one accent
 * that says which family you are looking at: ice for the microwave/cold half of the corpus,
 * amber for the hydrological half, deep blue for a neutral default. Every accent meets AA
 * on the shared surfaces below; contrast is not left to whatever theme is active.
 */
export const ACCENT_TOKENS = {
  ice: {
    '--geoai-accent': '#22d3ee',
    '--geoai-accent-strong': '#67e8f9',
    '--geoai-accent-soft': 'rgba(34, 211, 238, 0.14)',
    '--geoai-accent-line': 'rgba(34, 211, 238, 0.42)',
  },
  amber: {
    '--geoai-accent': '#f59e0b',
    '--geoai-accent-strong': '#fbbf24',
    '--geoai-accent-soft': 'rgba(245, 158, 11, 0.16)',
    '--geoai-accent-line': 'rgba(245, 158, 11, 0.45)',
  },
  'deep-blue': {
    '--geoai-accent': '#3b82f6',
    '--geoai-accent-strong': '#60a5fa',
    '--geoai-accent-soft': 'rgba(59, 130, 246, 0.16)',
    '--geoai-accent-line': 'rgba(59, 130, 246, 0.45)',
  },
}

/** Surface tokens shared by every accent. */
export const BASE_TOKENS = {
  '--geoai-bg': '#05070d',
  '--geoai-surface': '#0b1220',
  '--geoai-surface-2': '#111a2b',
  '--geoai-border': 'rgba(148, 163, 184, 0.18)',
  '--geoai-text': '#e6edf7',
  '--geoai-text-muted': '#93a4bf',
  '--geoai-pass': '#34d399',
  '--geoai-warn': '#fbbf24',
  '--geoai-block': '#f87171',
  '--geoai-font-sans': "'Fira Sans', 'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif",
  '--geoai-font-mono': "'Fira Code', ui-monospace, 'SFMono-Regular', 'JetBrains Mono', monospace",
  '--geoai-radius': '12px',
  '--geoai-radius-sm': '8px',
}

/**
 * Host theme tokens this plugin overrides.
 *
 * Only names the theme directory already declares are safe to override: the theme service
 * validates an override layer against that directory and rejects unknown names. These three
 * are the ones verified present in the shipped token sheets, and the rest of the visible
 * restyle travels in the plugin's own stylesheet, which is removed with the plugin.
 */
export const HOST_TOKEN_OVERRIDES = {
  '--dsw-alias-scrollbar-thumb': '#1f2b45',
  '--dsw-alias-scrollbar-thumb-hover': '#2c3b5c',
  '--dsw-elevation-stroke-color': 'rgba(148, 163, 184, 0.22)',
}

export function themeTokens(settings) {
  return { ...BASE_TOKENS, ...ACCENT_TOKENS[settings.accent] }
}

/** Theme id derived from the accent, so two accents can coexist in one deployment. */
export function themeId(settings) {
  return `geoai-${settings.accent}`
}

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
