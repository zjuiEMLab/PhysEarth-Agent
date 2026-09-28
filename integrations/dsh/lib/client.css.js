// The plugin's stylesheet, as a string module so the hand-written client bundle needs no CSS
// loader. It is scoped to `body.geoai-restyled`, a class the browser half adds only while the
// plugin is enabled and the user kept the restyle on — disabling removes the class and the
// whole style element, so nothing of this file survives a switch-off.
//
// Design intent: a dark, high-contrast surface for numbers people stare at, one accent that
// names the corpus family (ice / amber / deep blue), and zero decoration that would fight the
// host's own layout. Mobile first: every rule is sized for a 375px viewport, then relaxed.

module.exports = `
body.geoai-restyled {
  --geoai-rule: 1px solid var(--geoai-border);
  background:
    radial-gradient(1200px 600px at 12% -10%, var(--geoai-accent-soft), transparent 60%),
    linear-gradient(180deg, var(--geoai-bg), #04060b 70%);
  color: var(--geoai-text);
  font-family: var(--geoai-font-sans, system-ui, sans-serif);
}

/* ---- shell chrome: a quiet accent rail instead of a re-layout ------------------------- */
body.geoai-restyled [data-dsh-sidebar],
body.geoai-restyled aside {
  border-right: var(--geoai-rule);
}
body.geoai-restyled ::selection {
  background: var(--geoai-accent-soft);
}
body.geoai-restyled :focus-visible {
  outline: 2px solid var(--geoai-accent);
  outline-offset: 2px;
  border-radius: var(--geoai-radius-sm, 8px);
}

/* ---- conversation: monospace for anything that is a number --------------------------- */
body.geoai-restyled code,
body.geoai-restyled pre,
body.geoai-restyled [data-dsh-message-content] code {
  font-family: var(--geoai-font-mono, ui-monospace, monospace);
  font-variant-numeric: tabular-nums;
}

/* ---- the Geo-AI card in 设置 → 插件 --------------------------------------------------- */
.geoai-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  border: var(--geoai-rule);
  border-radius: var(--geoai-radius, 12px);
  background: linear-gradient(180deg, var(--geoai-surface), var(--geoai-surface-2));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 12px 32px rgba(2, 6, 16, 0.5);
  color: var(--geoai-text);
}
.geoai-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.geoai-card__head h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.01em;
}
.geoai-tag {
  padding: 2px 8px;
  border: 1px solid var(--geoai-accent-line);
  border-radius: 999px;
  font-family: var(--geoai-font-mono, monospace);
  font-size: 11px;
  color: var(--geoai-text-muted);
  background: var(--geoai-accent-soft);
}
.geoai-tag[data-on='true'] {
  color: var(--geoai-accent-strong);
  border-color: var(--geoai-accent);
}
.geoai-card__desc {
  margin: 0;
  color: var(--geoai-text-muted);
  font-size: 13px;
  line-height: 1.6;
}

/* ---- the one-click switch ------------------------------------------------------------ */
.geoai-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.geoai-switch {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border: 1px solid var(--geoai-accent-line);
  border-radius: 999px;
  background: var(--geoai-surface-2);
  color: var(--geoai-text);
  font-size: 13px;
  cursor: pointer;
  transition: background-color 200ms ease, border-color 200ms ease, color 200ms ease;
}
.geoai-switch:hover:not(:disabled) {
  background: var(--geoai-accent-soft);
  border-color: var(--geoai-accent);
}
.geoai-switch:disabled {
  cursor: progress;
  opacity: 0.7;
}
.geoai-switch__track {
  position: relative;
  width: 34px;
  height: 18px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.35);
  transition: background-color 200ms ease;
}
.geoai-switch__knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #e6edf7;
  transition: transform 200ms ease;
}
.geoai-switch.is-on .geoai-switch__track {
  background: var(--geoai-accent);
}
.geoai-switch.is-on .geoai-switch__knob {
  transform: translateX(16px);
}
.geoai-switch__label {
  font-family: var(--geoai-font-mono, monospace);
  font-size: 12px;
}
.geoai-row__hint {
  flex: 1 1 220px;
  color: var(--geoai-text-muted);
  font-size: 12px;
  line-height: 1.5;
}

/* ---- settings grid: one column on a phone, two on a tablet --------------------------- */
.geoai-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}
@media (min-width: 768px) {
  .geoai-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
.geoai-grid label {
  display: grid;
  gap: 6px;
  font-size: 12px;
  color: var(--geoai-text-muted);
}
.geoai-grid input[type='text'],
.geoai-grid select {
  width: 100%;
  padding: 8px 10px;
  border: var(--geoai-rule);
  border-radius: var(--geoai-radius-sm, 8px);
  background: var(--geoai-bg);
  color: var(--geoai-text);
  font-family: var(--geoai-font-mono, monospace);
  font-size: 12px;
}
.geoai-grid input[type='text']:hover,
.geoai-grid select:hover {
  border-color: var(--geoai-accent-line);
}

/* ---- checkboxes and the probe button ------------------------------------------------- */
.geoai-checks {
  display: grid;
  gap: 8px;
  font-size: 12px;
  color: var(--geoai-text-muted);
}
.geoai-checks label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
}
.geoai-card__foot {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.geoai-btn {
  padding: 8px 14px;
  border: 1px solid var(--geoai-accent-line);
  border-radius: var(--geoai-radius-sm, 8px);
  background: var(--geoai-accent-soft);
  color: var(--geoai-accent-strong);
  font-size: 12px;
  cursor: pointer;
  transition: background-color 200ms ease, border-color 200ms ease;
}
.geoai-btn:hover:not(:disabled) {
  border-color: var(--geoai-accent);
  background: var(--geoai-surface-2);
}
.geoai-status {
  flex: 1 1 240px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--geoai-text-muted);
}
.geoai-status[data-tone='pass'] {
  color: var(--geoai-pass);
}
.geoai-status[data-tone='warn'] {
  color: var(--geoai-warn);
}
.geoai-status[data-tone='block'] {
  color: var(--geoai-block);
}

/* Motion is decoration here; a reviewer reading a calibration curve does not need it. */
@media (prefers-reduced-motion: reduce) {
  body.geoai-restyled *,
  .geoai-card * {
    transition: none !important;
    animation: none !important;
  }
}
`
