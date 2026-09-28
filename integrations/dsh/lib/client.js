// PhysEarth-Agent as a DeepSeek Harness plugin — browser half.
//
// Self-contained by hand: the client module system wraps this file in a CJS factory and the
// kernel adopts { apply, inject } as a client plugin, so no bundler from the harness repo is
// involved (out-of-tree client plugins load exactly this way).
//
// What it does, in order of what a user notices:
//   1. restyles the shell with the Geo-AI palette while the plugin is on, and removes both the
//      token override and its own stylesheet when it is off — nothing survives a disable;
//   2. adds the 设置 → 插件 → PhysEarth Geo-AI card, whose one-click switch is the enable/disable
//      control the shipped Plugins section does not provide;
//   3. points the reviewer at the evidence: the card shows what the bridge can do, not a promise.

window.__ModuleLoader__.load({
  id: 'physearth-geoai',
  factory: (require) => {
    const module = { exports: {} }
    const exports = module.exports
    Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' })

    const React = require('react')
    const { useEffect, useMemo, useState } = React

    const NS = 'physearth-geoai'
    const CSS = require('./client.css.js')

    const ACCENTS = [
      { id: 'ice', label: '冰蓝 Ice', hint: '微波/积雪与冰冻圈' },
      { id: 'amber', label: '琥珀 Amber', hint: '水文与水量平衡' },
      { id: 'deep-blue', label: '深蓝 Deep blue', hint: '中性默认' },
    ]

    const BASE_TOKENS = {
      '--geoai-bg': '#05070d',
      '--geoai-surface': '#0b1220',
      '--geoai-surface-2': '#111a2b',
      '--geoai-border': 'rgba(148, 163, 184, 0.18)',
      '--geoai-text': '#e6edf7',
      '--geoai-text-muted': '#93a4bf',
      '--geoai-pass': '#34d399',
      '--geoai-warn': '#fbbf24',
      '--geoai-block': '#f87171',
      '--geoai-accent': '#22d3ee',
      '--geoai-accent-strong': '#67e8f9',
      '--geoai-accent-soft': 'rgba(34, 211, 238, 0.14)',
      '--geoai-accent-line': 'rgba(34, 211, 238, 0.42)',
    }

    const ACCENT_TOKENS = {
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

    /** Host tokens this plugin overrides; names must exist in the theme directory. */
    const HOST_TOKEN_OVERRIDES = {
      '--dsw-alias-scrollbar-thumb': '#1f2b45',
      '--dsw-alias-scrollbar-thumb-hover': '#2c3b5c',
      '--dsw-elevation-stroke-color': 'rgba(148, 163, 184, 0.22)',
    }

    function tokensFor(accent) {
      return { ...BASE_TOKENS, ...(ACCENT_TOKENS[accent] || ACCENT_TOKENS.ice) }
    }

    function Switch({ on, busy, onToggle, labelOn, labelOff }) {
      return React.createElement(
        'button',
        {
          type: 'button',
          className: 'geoai-switch' + (on ? ' is-on' : ''),
          role: 'switch',
          'aria-checked': on ? 'true' : 'false',
          disabled: busy,
          onClick: onToggle,
        },
        React.createElement('span', { className: 'geoai-switch__track' }, React.createElement('span', { className: 'geoai-switch__knob' })),
        React.createElement('span', { className: 'geoai-switch__label' }, busy ? '…' : on ? labelOn : labelOff),
      )
    }

    function Card(props) {
      const scope = props.scope
      const read = () => ({ ...BASE_DEFAULTS, ...(scope.get ? scope.get() : {}) })
      const [value, setValue] = useState(read)
      const [busy, setBusy] = useState(false)
      const [status, setStatus] = useState(null)

      useEffect(() => {
        if (typeof scope.subscribe !== 'function') return undefined
        return scope.subscribe(() => setValue(read()))
      }, [scope])

      const write = (patch) => {
        if (typeof scope.set !== 'function') {
          setStatus({ tone: 'block', text: '这个宿主的 settings scope 不支持写入；请在 profile 的 cordis.patch.yml 里改。' })
          return
        }
        const next = { ...value, ...patch }
        setValue(next)
        scope.set(patch)
      }

      const probe = async () => {
        setBusy(true)
        setStatus({ tone: 'warn', text: '正在连接桥…' })
        try {
          const response = await fetch(value.bridgeUrl.replace(/\/$/, '') + '/health')
          const payload = await response.json()
          setStatus({
            tone: 'pass',
            text:
              `桥已连接：${payload.models} 个注册模型（${payload.runnable_models} 个可运行）、` +
              `${payload.tools} 个工具、${payload.knowledge.papers} 篇论文 / ${payload.knowledge.sections} 节、` +
              `${payload.knowledge.skills} 个方法卡；凭据${payload.credentials ? '已配置' : '未配置'}。`,
          })
        } catch (error) {
          setStatus({ tone: 'block', text: `桥没有应答（${error.message}）。先运行：python -m integrations.geoai serve-http` })
        } finally {
          setBusy(false)
        }
      }

      return React.createElement(
        'div',
        { className: 'geoai-card' },
        React.createElement(
          'div',
          { className: 'geoai-card__head' },
          React.createElement('h3', null, 'PhysEarth Geo-AI'),
          React.createElement('span', { className: 'geoai-tag', 'data-on': value.enabled ? 'true' : 'false' }, value.enabled ? '已启用' : '已停用'),
        ),
        React.createElement(
          'p',
          { className: 'geoai-card__desc' },
          '把 PhysEarth-Agent 的物理模型、证据规则与内置文献带进这个 Harness：注册模型按声明的物理范围校验，运行前有人工批准，运行后做质量控制，每个数字都能引用到真正读过的证据。',
        ),
        React.createElement(
          'div',
          { className: 'geoai-row' },
          React.createElement(Switch, {
            on: value.enabled,
            busy,
            onToggle: () => write({ enabled: !value.enabled }),
            labelOn: '点击停用',
            labelOff: '点击启用',
          }),
          React.createElement(
            'div',
            { className: 'geoai-row__hint' },
            value.enabled
              ? '工具以 mcp__geoai__* 出现，系统提示里加入引用与单位规则，界面换成 Geo-AI 视觉。'
              : '停用后不注册工具、不注入提示词、不改界面；桥进程也会被释放。',
          ),
        ),
        React.createElement(
          'div',
          { className: 'geoai-grid' },
          React.createElement(
            'label',
            null,
            '视觉强调色',
            React.createElement(
              'select',
              { value: value.accent, onChange: (event) => write({ accent: event.target.value }) },
              ACCENTS.map((item) => React.createElement('option', { key: item.id, value: item.id }, `${item.label} · ${item.hint}`)),
            ),
          ),
          React.createElement(
            'label',
            null,
            'Python 桥地址',
            React.createElement('input', {
              type: 'text',
              value: value.bridgeUrl,
              onChange: (event) => setValue({ ...value, bridgeUrl: event.target.value }),
              onBlur: () => write({ bridgeUrl: value.bridgeUrl }),
              spellCheck: false,
            }),
          ),
          React.createElement(
            'label',
            null,
            'Python 解释器',
            React.createElement('input', {
              type: 'text',
              value: value.pythonCmd,
              onChange: (event) => setValue({ ...value, pythonCmd: event.target.value }),
              onBlur: () => write({ pythonCmd: value.pythonCmd }),
              spellCheck: false,
            }),
          ),
          React.createElement(
            'label',
            null,
            '仓库根目录（桥的工作目录）',
            React.createElement('input', {
              type: 'text',
              value: value.projectRoot,
              placeholder: '留空则使用宿主进程的当前目录',
              onChange: (event) => setValue({ ...value, projectRoot: event.target.value }),
              onBlur: () => write({ projectRoot: value.projectRoot }),
              spellCheck: false,
            }),
          ),
        ),
        React.createElement(
          'div',
          { className: 'geoai-checks' },
          React.createElement(
            'label',
            null,
            React.createElement('input', {
              type: 'checkbox',
              checked: value.restyleHost,
              onChange: (event) => write({ restyleHost: event.target.checked }),
            }),
            '改版宿主界面（关掉只保留本卡片）',
          ),
          React.createElement(
            'label',
            null,
            React.createElement('input', {
              type: 'checkbox',
              checked: value.autoStartBridge,
              onChange: (event) => write({ autoStartBridge: event.target.checked }),
            }),
            '桥未启动时由本插件拉起（停用时一并关闭）',
          ),
          React.createElement(
            'label',
            null,
            React.createElement('input', {
              type: 'checkbox',
              checked: value.approveRuns,
              onChange: (event) => write({ approveRuns: event.target.checked }),
            }),
            '由本部署承担物理运行的人工批准（慎用：勾选即表示你代替人审）',
          ),
        ),
        React.createElement(
          'div',
          { className: 'geoai-card__foot' },
          React.createElement('button', { type: 'button', className: 'geoai-btn', onClick: probe, disabled: busy }, '测试桥连接'),
          status ? React.createElement('span', { className: 'geoai-status', 'data-tone': status.tone }, status.text) : null,
        ),
      )
    }

    const BASE_DEFAULTS = {
      enabled: false,
      bridgeUrl: 'http://127.0.0.1:8799',
      autoStartBridge: true,
      pythonCmd: 'python',
      projectRoot: '',
      approveRuns: false,
      accent: 'ice',
      restyleHost: true,
      requestTimeoutMs: 120000,
    }

    exports.inject = ['settingsScope', 'slots', 'theme']

    exports.apply = function apply(ctx) {
      const scope = ctx.settingsScope.bind(NS)
      const read = () => ({ ...BASE_DEFAULTS, ...(scope.get ? scope.get() : {}) })

      // 1. The visible restyle: token overrides for the host theme, our own stylesheet for
      //    component-level treatment, and a body class both key off. Each is an effect, so a
      //    disable removes all three rather than leaving a half-styled shell behind.
      ctx.effect(() => {
        if (typeof ctx.theme.overrideTokens !== 'function') return () => {}
        return ctx.theme.overrideTokens('geoai', { ...HOST_TOKEN_OVERRIDES, ...tokensFor(read().accent) })
      }, 'physearth-geoai: theme tokens')

      ctx.effect(() => {
        const style = document.createElement('style')
        style.id = 'geoai-restyle'
        style.textContent = CSS
        document.head.appendChild(style)
        const applyClass = (value) => {
          document.body.classList.toggle('geoai-restyled', Boolean(value.enabled && value.restyleHost))
          document.body.dataset.geoaiAccent = value.accent || 'ice'
        }
        applyClass(read())
        const unsubscribe = typeof scope.subscribe === 'function' ? scope.subscribe(() => applyClass(read())) : undefined
        return () => {
          if (unsubscribe) unsubscribe()
          document.body.classList.remove('geoai-restyled')
          delete document.body.dataset.geoaiAccent
          style.remove()
        }
      }, 'physearth-geoai: stylesheet')

      // 2. The switch a user actually clicks. The shipped Plugins section is read-only, so the
      //    control lives in this plugin's own card under settings.plugin.item.
      ctx.effect(
        () =>
          ctx.slots.inject('settings.plugin.item', () =>
            ctx.slots.register({ key: NS, order: 60 }, (props) => React.createElement(Card, { ...props, scope })),
          ),
        'physearth-geoai: settings card',
      )

      ctx.logger?.info?.('physearth-geoai: browser half ready (设置 → 插件 → PhysEarth Geo-AI)')
    }

    return module.exports
  },
})
