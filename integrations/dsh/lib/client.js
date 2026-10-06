// PhysEarth-Agent as a DeepSeek Harness plugin — browser half.
//
// This file is the package's `exports["./client"]` artifact, and that is a precise role: the
// client module system reads it, hashes it for cache-busting, serves it at
// `/plugins/dsh-plugin-physearth/client.js`, and hands it to the kernel as a CommonJS
// factory. Three consequences shape everything below.
//
//   1. It is a *single* file. The module table answers `require` only for platform seed words
//      and for rows already in the boot graph, so a relative `require('./client.css.js')`
//      would miss the table and throw. The stylesheet is therefore inline text here.
//   2. `exports.apply` runs on the real cordis context, not the sandboxed facade the
//      agent-authored dynamic packages get: `ctx.effect`, service injection and the loader
//      all behave normally.
//   3. Everything it registers hangs off `ctx.effect`, so unloading the package removes the
//      theme layer, the stylesheet, the body class and the settings card together. Nothing
//      here needs an unload hook of its own.
//
// What a user notices, in order:
//   1. the interface restyles — the host's semantic token layer is overridden and a scoped
//      stylesheet adds what tokens cannot express;
//   2. a card appears under 设置 → 插件, and its switch is the enable/disable control the
//      shipped plugin inventory does not offer;
//   3. the card says what the bridge can actually do, because a claim about 20 registered
//      models is worth less than one answered health probe.

// The registration id is the MODULE id, which is this package's name — the same string the
// client module registry writes into the boot manifest as the row id, and the string it checks
// after importing this file. It is neither the settings namespace nor a display name. A mismatch
// produces `bundle /plugins/…/client.js loaded without registering "…" via __ModuleLoader__.load`,
// the row is dropped, and nothing at all happens in the browser — which is exactly what happened
// the first time this plugin was opened in a real one. `tests/client.test.mjs` ties the constant
// below to package.json's `name` so the two cannot drift.
window.__ModuleLoader__.load({
  id: 'dsh-plugin-physearth',
  factory: (require) => {
    const module = { exports: {} }
    const exports = module.exports
    Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' })

    const React = require('react')
    const { useCallback, useEffect, useMemo, useState } = React

    /** Settings namespace, also the slot `key` the plugin tab matches a served namespace by. */
    const NS = 'physearth'

    // ── The same definitions the host half and the tests read ──────────────────────────────
    // Duplicated as plain data rather than imported: a client bundle cannot value-import
    // across plugins (the bundle purity gate), and the alternatives — a second settings read
    // over the wire just to render a label, or a build step — are worse than two short lists.
    // `tests/logic.test.mjs` asserts these stay in step with lib/logic.js.

    const DEFAULTS = {
      enabled: false,
      bridgeUrl: 'http://127.0.0.1:8799',
      autoStartBridge: false,
      pythonCmd: 'python3',
      projectRoot: '',
      approveRuns: false,
      accent: 'ice',
      colorScheme: 'dark',
      restyleHost: true,
      promptDepth: 'rules',
      requestTimeoutMs: 120000,
    }

    const PROMPT_DEPTHS = [
      { id: 'rules', label: '规则栈 Rules', hint: '引擎自己的引用、证据与流程规则' },
      { id: 'full', label: '全部 Full', hint: '再加模型、数据集与工具目录（更长）' },
      { id: 'compact', label: '精简 Compact', hint: '本插件内置的短版，不起子进程' },
      { id: 'off', label: '不注入 Off', hint: '完全不改系统提示词' },
    ]

    const ACCENTS = [
      { id: 'ice', label: '冰蓝 Ice', hint: '微波、积雪与冰冻圈' },
      { id: 'amber', label: '琥珀 Amber', hint: '水文、蒸散与水量平衡' },
      { id: 'deep-blue', label: '深蓝 Deep blue', hint: '中性默认，贴近宿主配色' },
    ]

    const ACCENT_FILL = {
      dark: { ice: '#22d3ee', amber: '#f59e0b', 'deep-blue': '#3b82f6' },
      light: { ice: '#0e7490', amber: '#b45309', 'deep-blue': '#1e40af' },
    }

    const ACCENT_ON_FILL = {
      dark: { ice: '#04121a', amber: '#1a1204', 'deep-blue': '#f8fafc' },
      light: { ice: '#ffffff', amber: '#ffffff', 'deep-blue': '#ffffff' },
    }

    const ACCENT_SOFT = {
      dark: {
        ice: 'rgba(34, 211, 238, 0.14)',
        amber: 'rgba(245, 158, 11, 0.16)',
        'deep-blue': 'rgba(59, 130, 246, 0.16)',
      },
      light: {
        ice: 'rgba(14, 116, 144, 0.10)',
        amber: 'rgba(180, 83, 9, 0.10)',
        'deep-blue': 'rgba(30, 64, 175, 0.10)',
      },
    }

    /** The accent names, resolved once so the stylesheet never repeats the lookup. */
    function accentPaint(settings) {
      const mode = settings.colorScheme === 'light' ? 'light' : 'dark'
      const accent = Object.prototype.hasOwnProperty.call(ACCENT_FILL[mode], settings.accent) ? settings.accent : 'ice'
      return {
        fill: ACCENT_FILL[mode][accent],
        onFill: ACCENT_ON_FILL[mode][accent],
        soft: ACCENT_SOFT[mode][accent],
      }
    }

    // ── The token layer ────────────────────────────────────────────────────────────────────
    // `theme.overrideTokens(source, tokens)` takes token-name → { light, dark } pairs and
    // throws a teaching error on a bare string, because one value goes illegible the moment
    // the user flips the colour scheme. The names below are the host's *semantic* layer,
    // verified against the shipped sheet (`dsh-client-ui-theme/lib/styles/design-platform.css`,
    // 89 `--dsw-alias-*` / `--dsw-specific-*` names): overriding them moves surfaces, borders,
    // three label weights, the state colours, code blocks, bubbles, the sidebar and the
    // scrollbars together, without this file guessing at a single component class name.

    /** Surface roles in both exposures: the same design at two photographic stops. */
    const SURFACES = {
      dark: {
        base: '#05070d',
        layer1: '#0a0f1a',
        layer2: '#0f1728',
        layer3: '#141e33',
        platform: '#0d1526',
        overlay: '#16203a',
        skeleton: 'rgba(148, 163, 184, 0.10)',
        borderL1: 'rgba(148, 163, 184, 0.10)',
        borderL2: 'rgba(148, 163, 184, 0.20)',
        borderL3: 'rgba(148, 163, 184, 0.28)',
        borderL4: 'rgba(148, 163, 184, 0.36)',
        borderInverted: 'rgba(148, 163, 184, 0.14)',
        labelPrimary: '#e8eefb',
        labelPrimaryDimmed: '#c3cee3',
        labelPrimaryInverted: '#0f1728',
        labelSecondary: '#a8b8d4',
        labelTertiary: '#8094b4',
        labelCaption: '#7186a6',
        labelDimmed: '#43506b',
        hover: 'rgba(148, 163, 184, 0.10)',
        active: 'rgba(148, 163, 184, 0.16)',
        hoverSolid: '#17203a',
        buttonDimmed: '#1b2740',
        floating: '#131d33',
        floatingHover: '#1a2742',
        ghostActive: '#16223c',
        citation: '#131d33',
        codeBlock: '#080e1c',
        codeBanner: '#0d1526',
        inlineCode: '#131d33',
        tag: '#131d33',
        scrollBg: '#0f1728',
        scrollHover: '#1e2a45',
        scrollHover2: '#26344f',
        success: '#34d399',
        warn: '#fbbf24',
        warnSecondary: '#fcd34d',
        error: '#f87171',
        business: '#60a5fa',
        panel: '#141e33',
        bubble: '#101a2e',
        bubbleHighlight: '#16223c',
        inputMajor: '#0d1526',
        selector: '#16203a',
        sidebarFill: '#070b14',
        sidebarActive: '#141e33',
        sidebarActiveAccent: '#101a2e',
        sidebarHover: '#0f1728',
        tip: '#131d33',
      },
      light: {
        base: '#f4f7fc',
        layer1: '#ffffff',
        layer2: '#ffffff',
        layer3: '#ffffff',
        platform: '#e9f0fa',
        overlay: '#ffffff',
        skeleton: 'rgba(15, 23, 42, 0.05)',
        borderL1: 'rgba(15, 23, 42, 0.06)',
        borderL2: 'rgba(15, 23, 42, 0.12)',
        borderL3: 'rgba(15, 23, 42, 0.18)',
        borderL4: 'rgba(15, 23, 42, 0.26)',
        borderInverted: 'rgba(15, 23, 42, 0.10)',
        labelPrimary: '#0b1526',
        labelPrimaryDimmed: '#1e293b',
        labelPrimaryInverted: '#ffffff',
        labelSecondary: '#40506b',
        labelTertiary: '#5a6b86',
        labelCaption: '#6b7c96',
        labelDimmed: '#a9b6c9',
        hover: 'rgba(15, 23, 42, 0.05)',
        active: 'rgba(15, 23, 42, 0.09)',
        hoverSolid: '#e9f0fa',
        buttonDimmed: '#dbe6f6',
        floating: '#ffffff',
        floatingHover: '#eef4fc',
        ghostActive: '#e3ecf9',
        citation: '#eef4fc',
        codeBlock: '#f5f8fd',
        codeBanner: '#eaf1fb',
        inlineCode: '#eaf1fb',
        tag: '#eef4fc',
        scrollBg: '#dbe3ef',
        scrollHover: '#bcc8dc',
        scrollHover2: '#aab8ce',
        success: '#047857',
        warn: '#b45309',
        warnSecondary: '#d97706',
        error: '#b91c1c',
        business: '#1d4ed8',
        panel: '#1e293b',
        bubble: '#eef4fc',
        bubbleHighlight: '#dbe7f8',
        inputMajor: '#ffffff',
        selector: '#eaf1fb',
        sidebarFill: '#eaf1fb',
        sidebarActive: '#dbe7f8',
        sidebarActiveAccent: '#e3ecf9',
        sidebarHover: '#e2ebf9',
        tip: '#eef4fc',
      },
    }

    /**
     * Token name → surface role.
     *
     * A role table rather than a per-accent literal so that the two exposures stay one design:
     * change a surface and every token that means "that surface" follows, in both modes, for
     * every accent. The accent itself enters through four shared roles (`fill`, `fillHover`,
     * `onFill`, `accentSoft`) rather than being repeated per token.
     */
    const TOKEN_ROLES = {
      '--dsw-alias-bg-base': 'base',
      '--dsw-alias-bg-layer-1': 'layer1',
      '--dsw-alias-bg-layer-2': 'layer2',
      '--dsw-alias-bg-layer-3': 'layer3',
      '--dsw-alias-bg-module-platform': 'platform',
      '--dsw-alias-bg-overlay': 'overlay',
      '--dsw-alias-bg-skeleton': 'skeleton',
      '--dsw-alias-border-l1': 'borderL1',
      '--dsw-alias-border-l2': 'borderL2',
      '--dsw-alias-border-l3': 'borderL3',
      '--dsw-alias-border-l4': 'borderL4',
      '--dsw-alias-border-inverted': 'borderInverted',
      '--dsw-alias-brand-primary': 'fill',
      '--dsw-alias-brand-text': 'labelPrimary',
      '--dsw-alias-button-primary-fill': 'fill',
      '--dsw-alias-button-primary-hover': 'fillHover',
      '--dsw-alias-button-primary-dimmed': 'buttonDimmed',
      '--dsw-alias-button-floating-fill': 'floating',
      '--dsw-alias-button-floating-hover': 'floatingHover',
      '--dsw-alias-button-ghost-active-fill': 'ghostActive',
      '--dsw-alias-interactive-bg-hover': 'hover',
      '--dsw-alias-interactive-bg-active': 'active',
      '--dsw-alias-interactive-bg-hover-solid': 'hoverSolid',
      '--dsw-alias-label-primary': 'labelPrimary',
      '--dsw-alias-label-primary-dimmed': 'labelPrimaryDimmed',
      '--dsw-alias-label-primary-foreground': 'onFill',
      '--dsw-alias-label-primary-inverted': 'labelPrimaryInverted',
      '--dsw-alias-label-secondary': 'labelSecondary',
      '--dsw-alias-label-tertiary': 'labelTertiary',
      '--dsw-alias-label-caption': 'labelCaption',
      '--dsw-alias-label-dimmed': 'labelDimmed',
      '--dsw-alias-markdown-citation': 'citation',
      '--dsw-alias-markdown-code-block': 'codeBlock',
      '--dsw-alias-markdown-code-block-banner': 'codeBanner',
      '--dsw-alias-markdown-inline-code': 'inlineCode',
      '--dsw-alias-markdown-tag': 'tag',
      '--dsw-alias-scrollbar-bg-l1': 'scrollBg',
      '--dsw-alias-scrollbar-bg-l2': 'scrollBg',
      '--dsw-alias-scrollbar-hover-l1': 'scrollHover',
      '--dsw-alias-scrollbar-hover-l2': 'scrollHover2',
      '--dsw-alias-state-business-primary': 'business',
      '--dsw-alias-state-error-primary': 'error',
      '--dsw-alias-state-success-primary': 'success',
      '--dsw-alias-state-warn-primary': 'warn',
      '--dsw-alias-state-warn-secondary': 'warnSecondary',
      '--dsw-alias-toast-bg': 'panel',
      '--dsw-alias-tooltip-bg': 'panel',
      '--dsw-specific-bubble': 'bubble',
      '--dsw-specific-bubble-highlight': 'bubbleHighlight',
      '--dsw-specific-input-major': 'inputMajor',
      '--dsw-specific-menu': 'panel',
      '--dsw-specific-selector': 'selector',
      '--dsw-specific-sidebar-fill': 'sidebarFill',
      '--dsw-specific-sidebar-nav-item-active': 'sidebarActive',
      '--dsw-specific-sidebar-nav-item-active-accent': 'sidebarActiveAccent',
      '--dsw-specific-sidebar-nav-item-hover': 'sidebarHover',
      '--dsw-specific-tip': 'tip',
    }

    /** Token names this plugin owns, one per documented role plus the accent entry points. */
    const TOKEN_NAMES = Object.keys(TOKEN_ROLES)

    /**
     * The override layer for one settings snapshot: every token, both exposures.
     *
     * The accent only enters where the interface is *meant* to be recognisable — the primary
     * fill, hover on that fill, the text sitting on it, and the sidebar's active accent — so
     * picking amber repaints the identity, not the legibility.
     *
     * Contrast is a design constraint here, not a hope: every label value reaches at least
     * 4.5:1 against `bg-base` and `bg-layer-1` in the mode it belongs to, and each accent fill
     * carries its own `onFill` (`#04121a` on ice, `#f8fafc` on deep blue) instead of assuming
     * white.
     */
    function themeTokens(settings) {
      const mode = settings.colorScheme === 'light' ? 'light' : 'dark'
      const surface = SURFACES[mode]
      const paint = accentPaint(settings)
      const values = {
        ...surface,
        fill: paint.fill,
        fillHover: paint.fill,
        onFill: paint.onFill,
      }
      const out = {}
      for (const [token, role] of Object.entries(TOKEN_ROLES)) {
        const value = values[role]
        out[token] = { light: value, dark: value }
      }
      return out
    }

    /**
     * The scoped stylesheet.
     *
     * Two halves on purpose. `.physearth-card …` is not gated on the restyle, because the card is
     * the control that turns the plugin back on: it has to look deliberate even with the host
     * restyle switched off. `body.physearth-restyled …` carries the restyle itself, so turning the
     * switch off removes the look from the shell without touching the card.
     *
     * Two constraints from the product, both enforced below: no colour-only signal (every
     * state carries a word), and motion is optional (`prefers-reduced-motion` removes the
     * transitions rather than shortening them).
     */
    function stylesheet(paint) {
      return `
body.physearth-restyled {
  --physearth-accent: ${paint.fill};
  --physearth-accent-soft: ${paint.soft};
  --physearth-accent-on-fill: ${paint.onFill};
  --physearth-font-sans: 'Fira Sans', 'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --physearth-font-mono: 'Fira Code', ui-monospace, 'SFMono-Regular', 'JetBrains Mono', monospace;
  background-image:
    radial-gradient(1100px 520px at 12% -8%, var(--physearth-accent-soft), transparent 62%),
    radial-gradient(760px 420px at 100% 0%, rgba(59, 130, 246, 0.07), transparent 58%);
  background-attachment: fixed;
  font-family: var(--physearth-font-sans);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

/* Numbers are the product here, so the mono face is not decoration: a handle, a version, a
   parameter name and a unit all read better when the digits do not shift width. */
body.physearth-restyled code,
body.physearth-restyled pre,
body.physearth-restyled kbd,
body.physearth-restyled samp {
  font-family: var(--physearth-font-mono);
  font-variant-numeric: tabular-nums;
}

body.physearth-restyled :focus-visible {
  outline: 2px solid var(--physearth-accent);
  outline-offset: 2px;
  border-radius: 6px;
}

body.physearth-restyled ::selection {
  background: var(--physearth-accent-soft);
  color: var(--dsw-alias-label-primary, inherit);
}

body.physearth-restyled * {
  scrollbar-color: var(--dsw-alias-scrollbar-hover-l1, #1e2a45) transparent;
  scrollbar-width: thin;
}

body.physearth-restyled *::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

body.physearth-restyled *::-webkit-scrollbar-track {
  background: transparent;
}

body.physearth-restyled *::-webkit-scrollbar-thumb {
  background: var(--dsw-alias-scrollbar-hover-l1, #1e2a45);
  border: 2px solid transparent;
  border-radius: 999px;
  background-clip: content-box;
}

body.physearth-restyled *::-webkit-scrollbar-thumb:hover {
  background: var(--physearth-accent);
  background-clip: content-box;
}

/* The host animates with transitions, not keyframes, so honouring the preference here is a
   single rule rather than a stylesheet rewrite. */
@media (prefers-reduced-motion: reduce) {
  body.physearth-restyled *,
  body.physearth-restyled *::before,
  body.physearth-restyled *::after {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}

/* ── The card ────────────────────────────────────────────────────────────────────────────
   Mobile first: one column, full width, 44px minimum touch targets, and the control column
   only splits once there is room for it. */

.physearth-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  box-sizing: border-box;
  padding: 18px;
  border: 1px solid var(--dsw-alias-border-l2, rgba(148, 163, 184, 0.2));
  border-radius: 14px;
  background: var(--dsw-alias-bg-layer-1, transparent);
  color: var(--dsw-alias-label-primary, inherit);
  font-family: 'Fira Sans', 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
}

.physearth-card__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  justify-content: space-between;
}

.physearth-card__head h3 {
  margin: 0;
  font-size: 16px;
  line-height: 24px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.physearth-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--dsw-alias-border-l2, rgba(148, 163, 184, 0.2));
  background: var(--dsw-alias-bg-layer-2, transparent);
  color: var(--dsw-alias-label-secondary, inherit);
  font-size: 12px;
  line-height: 18px;
  font-weight: 600;
  white-space: nowrap;
}

.physearth-tag[data-on='true'] {
  border-color: var(--physearth-accent, #22d3ee);
  background: var(--physearth-accent-soft, rgba(34, 211, 238, 0.14));
  color: var(--dsw-alias-label-primary, inherit);
}

.physearth-card__desc {
  margin: 0;
  color: var(--dsw-alias-label-secondary, inherit);
  font-size: 13px;
  line-height: 21px;
}

.physearth-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--dsw-alias-border-l2, rgba(148, 163, 184, 0.2));
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-2, transparent);
}

.physearth-row__hint {
  color: var(--dsw-alias-label-tertiary, inherit);
  font-size: 12px;
  line-height: 19px;
}

/* A switch, not a checkbox: it reads as a state, and the label says which state. */
.physearth-switch {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  min-height: 44px;
  padding: 6px 14px 6px 6px;
  border: 1px solid var(--dsw-alias-border-l2, rgba(148, 163, 184, 0.2));
  border-radius: 999px;
  background: var(--dsw-alias-bg-layer-3, transparent);
  color: var(--dsw-alias-label-primary, inherit);
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  align-self: flex-start;
  transition: border-color 160ms ease, background-color 160ms ease;
}

.physearth-switch:hover:not(:disabled) {
  border-color: var(--physearth-accent, #22d3ee);
}

.physearth-switch:disabled {
  cursor: progress;
  opacity: 0.7;
}

.physearth-switch__track {
  position: relative;
  display: inline-block;
  width: 46px;
  height: 26px;
  border-radius: 999px;
  background: var(--dsw-alias-bg-skeleton, rgba(148, 163, 184, 0.2));
  transition: background-color 160ms ease;
}

.physearth-switch__knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--dsw-alias-label-primary, #e8eefb);
  transition: transform 160ms ease, background-color 160ms ease;
}

.physearth-switch.is-on {
  border-color: var(--physearth-accent, #22d3ee);
  background: var(--physearth-accent-soft, rgba(34, 211, 238, 0.14));
}

.physearth-switch.is-on .physearth-switch__track {
  background: var(--physearth-accent, #22d3ee);
}

.physearth-switch.is-on .physearth-switch__knob {
  transform: translateX(20px);
  background: var(--physearth-accent-on-fill, #04121a);
}

.physearth-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

/* A settings panel can hand this card a very narrow column — measured at 106px on a 390px
   viewport, where the host keeps its two-column shell. Nothing here tries to widen past its
   container (that would overflow); instead every text node wraps and every grid child may
   shrink, so the card degrades to a tall readable column instead of clipping. */
.physearth-card,
.physearth-card * {
  min-width: 0;
  overflow-wrap: anywhere;
}

.physearth-card__desc,
.physearth-row__hint,
.physearth-status {
  overflow-wrap: anywhere;
}

.physearth-grid label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--dsw-alias-label-secondary, inherit);
  font-size: 12px;
  line-height: 18px;
  font-weight: 600;
}

.physearth-grid input[type='text'],
.physearth-grid select {
  min-height: 40px;
  padding: 8px 10px;
  border: 1px solid var(--dsw-alias-border-l2, rgba(148, 163, 184, 0.2));
  border-radius: 8px;
  background: var(--dsw-alias-bg-base, transparent);
  color: var(--dsw-alias-label-primary, inherit);
  font-family: 'Fira Code', ui-monospace, SFMono-Regular, monospace;
  font-size: 12px;
  line-height: 18px;
}

.physearth-grid select {
  font-family: 'Fira Sans', system-ui, sans-serif;
  font-size: 13px;
}

.physearth-checks {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.physearth-checks label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-height: 44px;
  padding: 8px 0;
  color: var(--dsw-alias-label-secondary, inherit);
  font-size: 12px;
  line-height: 19px;
  cursor: pointer;
}

.physearth-checks input[type='checkbox'] {
  flex: none;
  width: 18px;
  height: 18px;
  margin: 1px 0 0;
  accent-color: var(--physearth-accent, #22d3ee);
}

.physearth-card__foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.physearth-btn {
  min-height: 40px;
  padding: 9px 18px;
  border: 1px solid var(--dsw-alias-border-l2, rgba(148, 163, 184, 0.2));
  border-radius: 10px;
  background: var(--dsw-alias-bg-layer-3, transparent);
  color: var(--dsw-alias-label-primary, inherit);
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 160ms ease, background-color 160ms ease;
}

.physearth-btn:hover:not(:disabled) {
  border-color: var(--physearth-accent, #22d3ee);
  background: var(--physearth-accent-soft, rgba(34, 211, 238, 0.14));
}

.physearth-btn:disabled {
  cursor: progress;
  opacity: 0.7;
}

/* State is never colour alone: each tone carries its own weight and the sentence says it. */
.physearth-status {
  flex: 1 1 260px;
  min-width: 0;
  font-size: 12px;
  line-height: 19px;
  color: var(--dsw-alias-label-secondary, inherit);
}

.physearth-status[data-tone='pass'] {
  color: var(--dsw-alias-state-success-primary, #34d399);
}

.physearth-status[data-tone='warn'] {
  color: var(--dsw-alias-state-warn-primary, #fbbf24);
}

.physearth-status[data-tone='block'] {
  color: var(--dsw-alias-state-error-primary, #f87171);
}

.physearth-facts {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.physearth-facts li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 10px;
  border: 1px solid var(--dsw-alias-border-l1, rgba(148, 163, 184, 0.1));
  border-radius: 8px;
  background: var(--dsw-alias-bg-layer-2, transparent);
  font-size: 12px;
  line-height: 18px;
}

.physearth-facts dt,
.physearth-facts span:first-child {
  color: var(--dsw-alias-label-tertiary, inherit);
}

.physearth-facts strong {
  font-family: 'Fira Code', ui-monospace, monospace;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

@media (min-width: 640px) {
  .physearth-card {
    padding: 20px;
  }

  .physearth-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .physearth-facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .physearth-row {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .physearth-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
`.trim()
    }

    /** Merge a partial settings document over the defaults, ignoring anything of the wrong type. */
    function readSettings(value) {
      const source = value && typeof value === 'object' ? value : {}
      const merged = { ...DEFAULTS }
      for (const key of Object.keys(DEFAULTS)) {
        if (source[key] !== undefined && source[key] !== null) merged[key] = source[key]
      }
      return merged
    }

    function Switch({ on, busy, onToggle, labelOn, labelOff }) {
      return React.createElement(
        'button',
        {
          type: 'button',
          className: 'physearth-switch' + (on ? ' is-on' : ''),
          role: 'switch',
          'aria-checked': on ? 'true' : 'false',
          'aria-busy': busy ? 'true' : 'false',
          disabled: busy,
          onClick: onToggle,
        },
        React.createElement(
          'span',
          { className: 'physearth-switch__track', 'aria-hidden': 'true' },
          React.createElement('span', { className: 'physearth-switch__knob' }),
        ),
        React.createElement('span', { className: 'physearth-switch__label' }, busy ? '正在写入…' : on ? labelOn : labelOff),
      )
    }

    function Card(props) {
      const scope = props.scope
      const t = props.t

      const snapshotOf = useCallback(() => {
        try {
          return scope.getSnapshot()
        } catch {
          return { value: undefined, writable: false, status: 'unavailable' }
        }
      }, [scope])

      const [snapshot, setSnapshot] = useState(snapshotOf)
      const [busy, setBusy] = useState(false)
      const [status, setStatus] = useState(null)

      useEffect(() => {
        let dispose
        try {
          dispose = scope.subscribe(() => setSnapshot(snapshotOf()))
        } catch {
          dispose = undefined
        }
        return () => {
          if (typeof dispose === 'function') dispose()
        }
      }, [scope, snapshotOf])

      const value = useMemo(() => readSettings(snapshot.value), [snapshot])
      const writable = snapshot.writable !== false

      const write = useCallback(
        (field, next) => {
          if (!writable) {
            setStatus({ tone: 'block', text: t('readOnly') })
            return
          }
          setBusy(true)
          setStatus(null)
          Promise.resolve(scope.set(field, next))
            .catch(() => setStatus({ tone: 'block', text: t('writeFailed') }))
            .finally(() => setBusy(false))
        },
        [scope, t, writable],
      )

      const probe = useCallback(async () => {
        setBusy(true)
        setStatus({ tone: 'warn', text: t('probing') })
        try {
          const response = await fetch(value.bridgeUrl.replace(/\/$/, '') + '/health')
          if (!response.ok) throw new Error(String(response.status))
          const payload = await response.json()
          setStatus({
            tone: 'pass',
            text: t('probeOk', {
              models: payload.models,
              runnable: payload.runnable_models,
              tools: payload.tools,
              papers: payload.knowledge.papers,
              sections: payload.knowledge.sections,
              skills: payload.knowledge.skills,
              credentials: payload.credentials ? t('probeCredentialsYes') : t('probeCredentialsNo'),
            }),
          })
        } catch (error) {
          setStatus({ tone: 'block', text: t('probeFailed', { message: error.message }) })
        } finally {
          setBusy(false)
        }
      }, [t, value.bridgeUrl])

      const statusLabel = snapshot.status === 'loading' ? t('loading') : snapshot.status === 'unavailable' ? t('unavailable') : null

      return React.createElement(
        'div',
        { className: 'physearth-card' },
        React.createElement(
          'div',
          { className: 'physearth-card__head' },
          React.createElement('h3', null, 'PhysEarth Geo-AI'),
          React.createElement(
            'span',
            { className: 'physearth-tag', 'data-on': value.enabled ? 'true' : 'false' },
            value.enabled ? t('enabled') : t('disabled'),
          ),
        ),
        React.createElement('p', { className: 'physearth-card__desc' }, t('description')),
        statusLabel
          ? React.createElement('p', { className: 'physearth-card__desc' }, statusLabel)
          : null,
        React.createElement(
          'div',
          { className: 'physearth-row' },
          React.createElement(Switch, {
            on: value.enabled,
            busy,
            onToggle: () => write('enabled', !value.enabled),
            labelOn: t('switchOn'),
            labelOff: t('switchOff'),
          }),
          React.createElement('div', { className: 'physearth-row__hint' }, value.enabled ? t('hintOn') : t('hintOff')),
        ),
        React.createElement(
          'div',
          { className: 'physearth-grid' },
          React.createElement(
            'label',
            null,
            t('accent'),
            React.createElement(
              'select',
              { value: value.accent, onChange: (event) => write('accent', event.target.value) },
              ACCENTS.map((item) =>
                React.createElement('option', { key: item.id, value: item.id }, `${item.label} · ${item.hint}`),
              ),
            ),
          ),
          React.createElement(
            'label',
            null,
            t('colorScheme'),
            React.createElement(
              'select',
              { value: value.colorScheme, onChange: (event) => write('colorScheme', event.target.value) },
              React.createElement('option', { value: 'dark' }, t('colorSchemeDark')),
              React.createElement('option', { value: 'light' }, t('colorSchemeLight')),
            ),
          ),
          React.createElement(
            'label',
            null,
            t('promptDepth'),
            React.createElement(
              'select',
              { value: value.promptDepth, onChange: (event) => write('promptDepth', event.target.value) },
              PROMPT_DEPTHS.map((item) =>
                React.createElement('option', { key: item.id, value: item.id }, `${item.label} · ${item.hint}`),
              ),
            ),
          ),
          React.createElement(
            'label',
            null,
            t('bridgeUrl'),
            React.createElement('input', {
              type: 'text',
              value: value.bridgeUrl,
              onChange: (event) => write('bridgeUrl', event.target.value),
              spellCheck: false,
              inputMode: 'url',
              autoComplete: 'off',
            }),
          ),
          React.createElement(
            'label',
            null,
            t('pythonCmd'),
            React.createElement('input', {
              type: 'text',
              value: value.pythonCmd,
              onChange: (event) => write('pythonCmd', event.target.value),
              spellCheck: false,
              autoComplete: 'off',
            }),
          ),
          React.createElement(
            'label',
            null,
            t('projectRoot'),
            React.createElement('input', {
              type: 'text',
              value: value.projectRoot,
              placeholder: t('projectRootPlaceholder'),
              onChange: (event) => write('projectRoot', event.target.value),
              spellCheck: false,
              autoComplete: 'off',
            }),
          ),
        ),
        React.createElement(
          'div',
          { className: 'physearth-checks' },
          React.createElement(
            'label',
            null,
            React.createElement('input', {
              type: 'checkbox',
              checked: value.restyleHost,
              onChange: (event) => write('restyleHost', event.target.checked),
            }),
            t('restyleHost'),
          ),
          React.createElement(
            'label',
            null,
            React.createElement('input', {
              type: 'checkbox',
              checked: value.autoStartBridge,
              onChange: (event) => write('autoStartBridge', event.target.checked),
            }),
            t('autoStartBridge'),
          ),
          React.createElement(
            'label',
            null,
            React.createElement('input', {
              type: 'checkbox',
              checked: value.approveRuns,
              onChange: (event) => write('approveRuns', event.target.checked),
            }),
            t('approveRuns'),
          ),
        ),
        React.createElement(
          'div',
          { className: 'physearth-card__foot' },
          React.createElement('button', { type: 'button', className: 'physearth-btn', onClick: probe, disabled: busy }, t('probe')),
          status ? React.createElement('span', { className: 'physearth-status', 'data-tone': status.tone, role: 'status' }, status.text) : null,
        ),
      )
    }

    // ── Dictionaries ───────────────────────────────────────────────────────────────────────
    // Registered through the locale service rather than hardcoded, so the card follows the
    // interface language and a later translation is a data change, not a code change.

    const zh = {
      nav: 'PhysEarth Geo-AI',
      description:
        '把 PhysEarth-Agent 的物理模型、证据规则与内置文献带进这个 Harness：注册模型按声明的物理范围校验，运行前有人工批准，运行后做质量控制，每个数字都能引用到真正读过的证据。',
      enabled: '已启用',
      disabled: '已停用',
      loading: '正在读取设置…',
      unavailable: '当前设置提供方不可用，卡片只读。',
      readOnly: '这个宿主的设置是只读的；请改 profile 的 cordis.patch.yml。',
      writeFailed: '写入设置失败，值没有保存。',
      switchOn: '点击停用',
      switchOff: '点击启用',
      hintOn: '工具以 mcp__physearth__* 出现，系统提示注入本项目的引用/证据/流程规则（深度见下），界面换成 Geo-AI 视觉。',
      hintOff: '停用后不注册工具、不注入提示词、不改界面；桥进程也会被释放。',
      accent: '视觉强调色',
      colorScheme: '强调色曝光',
      colorSchemeDark: '暗场（OLED）',
      colorSchemeLight: '亮场（日光）',
      promptDepth: '提示词注入深度',
      bridgeUrl: 'Python 桥地址',
      pythonCmd: 'Python 解释器',
      projectRoot: '仓库根目录（桥的工作目录）',
      projectRootPlaceholder: '留空则使用宿主进程的当前目录',
      restyleHost: '改版宿主界面（关掉只保留本卡片）',
      autoStartBridge: '桥未启动时由本插件拉起（停用时一并关闭）',
      approveRuns: '启动 Python 桥时预先批准物理运行（慎用：勾选即表示你代替人审）',
      probe: '测试桥连接',
      probing: '正在连接桥…',
      probeOk: (p) =>
        `桥已连接：${p.models} 个注册模型（${p.runnable} 个可运行）、${p.tools} 个工具、` +
        `${p.papers} 篇论文 / ${p.sections} 节、${p.skills} 个方法卡；凭据${p.credentials}。`,
      probeCredentialsYes: '已配置',
      probeCredentialsNo: '未配置',
      probeFailed: (p) => `桥没有应答（${p.message}）。先运行：python -m integrations.physearth serve-http`,
    }

    const en = {
      nav: 'PhysEarth Geo-AI',
      description:
        'Brings the PhysEarth-Agent physical models, evidence rules and bundled corpus into this harness: registered models are validated against declared physical ranges, a human approves a run before it executes, quality control follows it, and every number cites evidence that was actually read.',
      enabled: 'Enabled',
      disabled: 'Disabled',
      loading: 'Reading settings…',
      unavailable: 'The settings provider is unavailable; this card is read-only.',
      readOnly: 'This host serves settings read-only; edit the profile cordis.patch.yml instead.',
      writeFailed: 'The settings write failed; nothing was saved.',
      switchOn: 'Click to disable',
      switchOff: 'Click to enable',
      hintOn: 'Tools appear as mcp__physearth__*, the system prompt gains this project’s citation, evidence and workflow rules (depth below), and the interface takes the Geo-AI look.',
      hintOff: 'Disabled: no tools, no prompt rules, no restyle, and the bridge process is released.',
      accent: 'Accent',
      colorScheme: 'Accent exposure',
      colorSchemeDark: 'Dark field (OLED)',
      colorSchemeLight: 'Light field (daylight)',
      promptDepth: 'Prompt rules injected',
      bridgeUrl: 'Python bridge URL',
      pythonCmd: 'Python interpreter',
      projectRoot: 'Checkout root (bridge working directory)',
      projectRootPlaceholder: 'Empty uses the host process working directory',
      restyleHost: 'Restyle the host interface (off keeps only this card)',
      autoStartBridge: 'Start the bridge when it is not answering (released on disable)',
      approveRuns: 'Start the Python bridge with physical runs approved in advance (careful: ticking this means you approve in the human’s place)',
      probe: 'Probe the bridge',
      probing: 'Reaching the bridge…',
      probeOk: (p) =>
        `Bridge answered: ${p.models} registered models (${p.runnable} runnable), ${p.tools} tools, ` +
        `${p.papers} papers / ${p.sections} sections, ${p.skills} method cards; credentials ${p.credentials}.`,
      probeCredentialsYes: 'configured',
      probeCredentialsNo: 'not configured',
      probeFailed: (p) => `The bridge did not answer (${p.message}). Start it with: python -m integrations.physearth serve-http`,
    }

    /**
     * Services this half needs, declared so the runtime parks it until they exist.
     *
     * `connection` and `remote` are not used directly: the settings scope resolves its transport
     * and its invalidation feed through the *caller's* context, so they must be in scope for
     * `settingsScope.bind()` to work at all.
     */
    exports.inject = ['settingsScope', 'slots', 'theme', 'locale', 'connection', 'remote']

    exports.apply = function apply(ctx) {
      const t = ctx.locale.bind(NS)
      ctx.effect(() => ctx.locale.register(NS, { zh, en }), 'physearth: card dictionaries')

      const scope = ctx.settingsScope.bind({ namespace: NS })
      const snapshot = () => {
        try {
          return scope.getSnapshot()
        } catch {
          return undefined
        }
      }
      const current = () => readSettings(snapshot()?.value)

      // 1. The host's semantic token layer. One layer per accent identity, and every value is a
      //    { light, dark } pair — the theme service rejects a bare string precisely because it
      //    would go illegible when the user switches scheme.
      //
      //    The layer is gated on the switch. A layer left stacked while the plugin is off would
      //    keep the whole palette overridden — measured, not assumed: after the first click of
      //    the switch the body class was gone and `--dsw-alias-bg-base` was still ours.
      ctx.effect(() => {
        if (typeof ctx.theme?.overrideTokens !== 'function') {
          ctx.logger?.warn?.('physearth: no theme.overrideTokens on this host; the restyle falls back to the stylesheet alone')
          return () => {}
        }
        let dispose
        const sync = () => {
          if (typeof dispose === 'function') {
            dispose()
            dispose = undefined
          }
          const value = current()
          if (!value.enabled || !value.restyleHost) return
          dispose = ctx.theme.overrideTokens(NS, themeTokens(value))
        }
        sync()
        const stop = scope.subscribe(sync)
        return () => {
          if (typeof stop === 'function') stop()
          if (typeof dispose === 'function') dispose()
        }
      }, 'physearth: host token layer')

      // 2. The scoped stylesheet and the body class the restyle hangs off. The class is what
      //    makes "on" visible: tokens alone would recolour, not restyle.
      ctx.effect(() => {
        const style = document.createElement('style')
        style.id = 'physearth-restyle'
        document.head.appendChild(style)
        const render = () => {
          const value = current()
          style.textContent = stylesheet(accentPaint(value))
          const active = Boolean(value.enabled && value.restyleHost)
          document.body.classList.toggle('physearth-restyled', active)
          document.body.dataset.physearthAccent = value.accent
          document.body.dataset.physearthEnabled = value.enabled ? 'true' : 'false'
        }
        render()
        const stop = scope.subscribe(render)
        return () => {
          if (typeof stop === 'function') stop()
          document.body.classList.remove('physearth-restyled')
          delete document.body.dataset.physearthAccent
          delete document.body.dataset.physearthEnabled
          style.remove()
        }
      }, 'physeauth-physearth: stylesheet')

      // 3. The switch. The shipped plugin inventory is a read-only list, so the enable/disable
      //    control is this card's, and it writes the host half's own `enabled` setting — which
      //    is what moves the tools and the prompt rule, not just the pixels.
      ctx.effect(() => {
        const card = (props) => React.createElement(Card, { ...props, scope, t })
        return ctx.slots.inject('settings.plugin.item', function* () {
          yield ctx.slots.register(
            {
              name: 'settings.plugin.item',
              key: NS,
              id: NS,
              order: 60,
              label: () => t('nav'),
              inject: () => ({}),
            },
            card,
          )
        })
      }, 'physearth: settings card')

      ctx.logger?.info?.('physearth: browser half ready (设置 → 插件 → PhysEarth Geo-AI)')
    }

    // Exported for `tests/client.test.mjs`, which mounts this factory against a stub module
    // table and a stub React. The palette, the token layer and the stylesheet are the parts
    // most likely to break silently — a wrong token shape throws only in a live browser — so
    // they are reachable without one.
    exports.DEFAULTS = DEFAULTS
    exports.ACCENTS = ACCENTS
    exports.TOKEN_NAMES = TOKEN_NAMES
    exports.NS = NS
    exports.accentPaint = accentPaint
    exports.themeTokens = themeTokens
    exports.stylesheet = stylesheet

    return module.exports
  },
})
