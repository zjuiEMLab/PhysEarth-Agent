// The bridge client: one HTTP JSON API in front of the Python engine.
//
// The engine keeps validation, the approval gate, quality control and the evidence rules;
// this client only transports a call and its result, and it never turns a refusal into a
// success. A `needs_input` (a run it refused to configure) or `terminal_error` result comes
// back as-is so the caller can surface it.

import { spawn } from 'node:child_process'

import { BRIDGE_ROUTES, bridgeCommand, portOf } from './logic.js'

export class BridgeClient {
  constructor(settings) {
    this.settings = settings
    this.child = undefined
  }

  url(path) {
    return `${this.settings.bridgeUrl.replace(/\/$/, '')}${path}`
  }

  async request(path, init = {}) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), this.settings.requestTimeoutMs)
    try {
      const response = await fetch(this.url(path), { ...init, signal: controller.signal })
      const text = await response.text()
      let payload
      try {
        payload = text ? JSON.parse(text) : {}
      } catch {
        payload = { status: 'terminal_error', error: 'bridge_protocol', summary: text.slice(0, 400) }
      }
      return { ok: response.ok, status: response.status, payload }
    } catch (error) {
      return {
        ok: false,
        status: 0,
        payload: {
          status: 'terminal_error',
          error: 'bridge_unreachable',
          summary: `${this.settings.bridgeUrl} did not answer: ${error.message}`,
        },
      }
    } finally {
      clearTimeout(timer)
    }
  }

  get(path) {
    return this.request(path)
  }

  post(path, body) {
    return this.request(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    })
  }

  health() {
    return this.get(BRIDGE_ROUTES.health)
  }

  tools() {
    return this.get(BRIDGE_ROUTES.tools)
  }

  models() {
    return this.get(BRIDGE_ROUTES.models)
  }

  knowledge() {
    return this.get(BRIDGE_ROUTES.knowledge)
  }

  prompt() {
    return this.get(BRIDGE_ROUTES.prompt)
  }

  newSession(model) {
    return this.post(BRIDGE_ROUTES.session, { model, approve_runs: this.settings.approveRuns })
  }

  call(name, args = {}, sessionId) {
    return this.post(BRIDGE_ROUTES.call, {
      name,
      arguments: args,
      session_id: sessionId,
      approve_runs: this.settings.approveRuns,
    })
  }

  ask(question, sessionId, model) {
    return this.post(BRIDGE_ROUTES.ask, {
      question,
      session_id: sessionId,
      model,
      approve_runs: this.settings.approveRuns,
    })
  }

  evidence(sessionId) {
    return this.post(BRIDGE_ROUTES.evidence, { session_id: sessionId })
  }

  plan(sessionId) {
    return this.post(BRIDGE_ROUTES.plan, { session_id: sessionId })
  }

  review(sessionId, choice) {
    return this.post(BRIDGE_ROUTES.review, { session_id: sessionId, choice })
  }

  /**
   * Start the bridge when it is not answering yet, and wait for it to come up.
   *
   * The plugin owns this process: it is spawned detached and killed on disable, so switching
   * the plugin off leaves nothing running behind it. A bridge the operator started already
   * is detected first and left alone.
   *
   * The child's stderr is captured while we wait, because the failure this used to hide was a
   * one-line `ModuleNotFoundError` in a process spawned with `stdio: 'ignore'`: the plugin
   * reported "did not answer within 10 s" and nothing said why. Once the bridge is up the pipes
   * are dropped and the child is unref'd, so the long run stays out of the host's event loop.
   */
  async ensureRunning() {
    const alive = await this.health()
    if (alive.ok) return { started: false, detail: 'bridge already answering' }
    if (!this.settings.autoStartBridge) {
      return { started: false, detail: 'autoStartBridge is off and no bridge is listening' }
    }
    const spec = bridgeCommand(this.settings)
    let child
    try {
      child = spawn(spec.command, spec.args, {
        cwd: spec.cwd || process.cwd(),
        env: { ...process.env, ...(spec.env || {}) },
        detached: true,
        stdio: ['ignore', 'pipe', 'pipe'],
      })
    } catch (error) {
      return { started: false, detail: `could not spawn ${spec.command}: ${error.message}` }
    }
    this.child = child
    let stderr = ''
    const capture = (chunk) => {
      stderr = (stderr + String(chunk)).slice(-2000)
    }
    child.stderr?.on('data', capture)
    child.stdout?.on('data', () => {})

    const release = () => {
      child.stdout?.destroy()
      child.stderr?.destroy()
      child.unref()
    }

    for (let attempt = 0; attempt < 40; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 250))
      if (child.exitCode !== null) {
        release()
        const tail = stderr.trim().split('\n').slice(-3).join(' | ')
        return {
          started: false,
          detail:
            `${spec.command} exited with code ${child.exitCode} before the bridge came up` +
            (tail ? `: ${tail}` : ` (no output; is ${spec.command} the right interpreter?)`),
        }
      }
      const ready = await this.health()
      if (ready.ok) {
        release()
        return { started: true, detail: `bridge started on port ${portOf(this.settings.bridgeUrl)}` }
      }
    }
    release()
    const tail = stderr.trim().split('\n').slice(-3).join(' | ')
    return {
      started: false,
      detail: `bridge did not answer within 10 s${tail ? `: ${tail}` : ''}`,
    }
  }

  /** Stop the bridge this client started, if it started one. */
  dispose() {
    if (this.child && this.child.pid) {
      try {
        process.kill(-this.child.pid, 'SIGTERM')
      } catch {
        // Already gone: failing to signal is not failing to have cleaned up.
      }
    }
    this.child = undefined
  }
}
