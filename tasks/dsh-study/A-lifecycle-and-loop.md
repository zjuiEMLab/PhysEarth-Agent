# DSH 研究报告 A：Agent 生命周期、主循环、工具执行管线与失败处理

> 调研对象：`/Users/heihe/Desktop/Competitions/GeoAI_challenge/tmp/deepseek-harness`（TypeScript + pnpm monorepo，v0.1.5-rc.2）。全程只读，未修改仓库任何文件。
> 材料来源：`docs/agent-lifecycle.zh.md`、`docs/tool-execution-pipeline.zh.md`、`docs/architecture.zh.md#turn-flow`、`docs/defensive-patterns.md`、`docs/subsystems/{core,tools,llm-streaming}.zh.md`，以及 `packages/{core/agent-loop,core/agent,core/tools,core/session,llm/*,guard/*,compaction/*,jobs/*,api/gateway}` 的源码。
> 结论先行：**DSH 的"不卡死"主要不是靠"加超时"，而是靠三件事——(1) 一个"还欠不欠工作"的显式循环不变式；(2) 失败一律降级为"结构化数据"而不是异常上抛；(3) 每个可能永久挂起的 await 都有一个可归属的中止来源。** 且 **turn 级没有步数预算也没有墙钟 deadline**（第 4.9 节有 9 组关键词的全树复核）——这一点与直觉相反，也是迁移时必须自己补的洞。第 5 节（流式/UI）只保留与循环稳定性相关的部分；UI 重连、rebaseline、渲染节流等细节见同目录 `D-ui-streaming-and-tests.md`。

---

## 0. 机制速查表

| 机制名 | 作用 | 关键源码位置 | 解决的稳定性问题 |
|---|---|---|---|
| 三层嵌套 `kick → turn → step` | 会话级活动 / 轮次 / 单次模型调用+工具批次，各自有独立收敛条件 | `packages/core/agent-loop/src/agent.ts:225-238`、`:269-350`、`:352-498` | 全仓只有一处真 `while`，退出条件集中在 `turnEnds !== null && inbox.nextStep.length === 0`，不会出现多层循环各自判断该不该退 |
| `phase` 相位机 + `AgentStatus` | `idle`/`maintenance`/`running` 三态，迁移即同步广播 `agent/status` | `agent.ts:41-49`、`:114-126`、`:200-208` | 外部能观测"谁在跑"，避免把排队消息、steering、注入上下文误当同一次执行的产物 |
| **step 内重试循环** | 失败/重试在**已打开的 step 内**发生，不重复 pre-step、不重复组装提示词、不重复追加用户消息 | `agent.ts:361-497` | 重试不会让上下文留下 N 份用户消息/系统提示词这种不可逆污染 |
| `assistant/message` vs `assistant/attempt` | 成功 = 模型历史事件；失败/取消/中断 = **仅日志**事件，不进派生历史 | `agent.ts:399-440`、`:441-483`；`assistant-stream.ts:73-109` | 失败尝试不污染 transcript；崩溃在 settlement 前不留半截脏数据 |
| 工具批次：**barrier + 有界滚动池 + 启动前重分类** | 独占工具成栅栏；并行安全工具进滚动池；每个调用启动前重读一次 `executionMode` | `tool-calls.ts:85-101`、`:199-214`、`:122-247` | 防止"模型一次发 20 个写请求被并发执行互相踩"；也不会按过期的分类快照一路冲 |
| **结果按模型顺序提交** `commitReady` | 派发可乱序完成，`tool/result` 必须按模型调用顺序写入 | `tool-calls.ts:146-161` | transcript 与 provider 期望的 tool_call/tool_result 配对顺序一致 |
| 取消时**合成结果** `appendSkippedToolCall` | 取消后未启动的调用补写 `tool/call` + `isError` | `tool-calls.ts:96-99`、`:249-260` | 不留下"悬空 tool_call 无 result"，重放/续跑时 provider 不报协议错 |
| 工具管线**永不向上抛异常** | 每层 catch 都转 `isError` 结果，最外层两次 `materializeFinalResult` 兜底 | `packages/core/tools/src/index.ts:1453-1497`、`:1559-1588`、`:1621-1636` | 工具写崩不打断 turn：模型看到错误文本，可自行改参数重试 |
| 未知工具/折叠调用的**可路由拒绝** | 返回 `UNKNOWN_TOOL` 并附"该改调哪个入口" | `tools/index.ts:1363-1434` | 模型不会因"刚声明的工具说不知道"而判定系统坏了、陷入重复试错 |
| `tools/execute` 包裹式**协作式超时** | 工具自声明 `timeoutMs`，超时替换结果为 `TOOL_TIMEOUT` | `packages/guard/timeout-policy/src/index.ts:51-78` | 工具卡死不阻塞 turn；且**不放弃已启动 Promise**，不留幽灵副作用 |
| 流空闲看门狗 `idleWatchdog` | 只在"读挂起"期间计时；默认 300000ms | `packages/util/timeout/src/index.ts:126-173`；`packages/llm/llm-deepseek/src/adapter.ts:485-517` | 上游不发数据也不断开时 turn 不会永远挂着；且不把"消费者思考时间"算作 provider 空闲 |
| 重试决策单点 `agent/request-error` | 默认 `undefined` = 终止；只有声明能恢复的插件才延长循环 | `agent.ts:441-463`；`packages/llm/llm-retry/src/index.ts:194-241` | fail-closed：新增 provider/插件不会意外获得无限重试 |
| 退避公式（指数+对称抖动+夹上限） | `min(init*2^(n-1), max) * (1-r+2r*U)` 再夹 `max` | `llm-retry/src/index.ts:59-64`；默认值 `packages/llm/llm/src/retry-policy.ts:14-24` | 限流重试风暴；避免整机同相位重试 |
| `retry-after` 优先、越界则放弃 | ≤ 上限直接用（不抖动）；> 上限时 normal 模式不再重试 | `llm-retry/src/index.ts:226-238`；解析 `llm-deepseek/src/adapter.ts:318-326` | 服务端说"1 小时后再来"时不傻等，也不无视服务端指令 |
| 上下文溢出"压缩后重试一次" | 只在 `surface.replaceGeneration` **真前进**时才重试 | `packages/compaction/compaction-basic/src/index.ts:180-224` | 防"压缩没效果却一直重试"的活锁；也防把无效重试当作进展 |
| `max-tokens` 终态且丢弃 tool-call | 立即收尾；组装阶段丢掉被截断的 tool-call | `agent.ts:484`；`packages/llm/llm/src/assembler.ts:130-146` | 被截断的半截 JSON 参数不会被拿去执行（否则必然参数非法→无限重试） |
| 空响应 `EMPTY_RESPONSE` 提升为可重试错误 | 正常 stop 但零内容块 → error finish，而非空 assistant 消息 | `llm-deepseek/src/translate.ts:132-142`；`packages/llm/llm/src/error.ts:30-39` | 避免"空消息静默结束 turn、用户什么也看不到"的死状态 |
| 重复调用检测 `repeat-tool-reminder` | 同一 agent 同一(工具名+规范化参数) 连续命中 3/5/8 时注入提醒 | `packages/guard/repeat-tool-reminder/src/index.ts:28-50`、`:189-224` | 打断"同参数反复调用"的无效循环——**顾问式**，只提醒不停 |
| 崩溃恢复合成闭合事件 | 重启扫描未闭合 turn，补 `tool/result` + `step/end` + `turn/end{interrupted}` | `packages/core/session/src/repair.ts:29-135` | 进程被 kill 后日志仍对 provider 合法，可继续对话 |
| 运行时不变量（请求重建断言） | 每次 `llm/stream` 断言"发出的请求 == 日志派生结果" | `agent-loop/src/invariant.ts:21-56` | 从根上消灭"内存状态与日志漂移"这类最难查的卡死/串话 |
| 监听器异常隔离 | 逐回调 try/catch，一个坏订阅者不饿死后续订阅者 | `tools/index.ts:1646-1666`、`core/agent/src/dispatch.ts:113-136` | 回调抛错导致生命周期推进中断（极隐蔽的"卡在中间态"来源） |
| 后台 Job 与 turn 解耦 | 长任务注册为 job，进 turn 的只有句柄与结论 | `packages/jobs/README.md`（`ctx.jobs`/`jobs-local`/`tool-jobs`） | 长任务不占 turn 循环，不必把 turn 超时调得巨大 |
| Goal 轮次预算（唯二硬截断之一） | `roundsStarted >= maxGoalRounds` → block，理由 `round-limit` | `packages/goal/goal-round-driver/src/index.ts:166-172` | **跨 turn** 的长目标有硬上限，但该预算属于 goal 插件，不属于主循环 |

---

## 1. 一次 turn 的完整状态机

### 1.1 三层结构：谁循环、循环什么

```ts
// packages/core/agent-loop/src/agent.ts:225-238
private async kick(): Promise<void> {
  try { while (await this.turn()) {} }
  catch (_error) { /* Reported failures and cancellation are contained at the driver boundary. */ }
  finally {
    if (this.phase.kind === 'running') {
      const { turn, wakeRequested } = this.phase
      this.setPhase({ kind: 'idle', lastTurn: turn })
      if (wakeRequested && this.inbox.hasPending) this.wakeDriver()
    }
  }
}
```

这三条硬规则值得逐条记住：

1. **一个 driver 就是一次 `kick()`**，`while (await this.turn())` 是唯一的轮次循环，`turn()` 返回 `false` 即"没有下一轮"。
2. **`catch` 是空实现且有注释说明吞掉了什么**——错误已在 `turn()` 内通过 `throwError()` 广播为 `agent/error`，driver 边界只做 "contain"：绝不让异常逃逸到 `wakeDriver()` 的 promise（否则 unhandled rejection，且 status 永远停在 `running`）。
3. **`finally` 一定把相位落回 `idle` 并回放被 latch 的 wake**（`wakeRequested`）——这是"取消后新消息不丢"的关键。

`turn()` 的主干（`agent.ts:276-349` 精简）：

```ts
const turn = phase.turn + 1
this.session.append('turn/start', { turn })
let turnEnds: TurnEndReason | null = null
while (true) {
  signal.throwIfAborted()                        // ① 每个 await 前查取消
  const step = phase.step + 1
  const decision = await this.preStep(target, { turn, step })
  if (decision.kind === 'reject') { turnEnds = { kind: 'blocked' }; return false }
  if (phase.step === 0 && decision.messages.length === 0) { turnEnds = { kind: 'completed' }; return false }
  this.session.append('step/start', { turn, step })
  try { const stepEnd = await this.step(decision); if (turnEnds?.kind !== 'max-tokens') turnEnds = stepEnd }
  finally { this.session.append('step/end', { turn, step }) }
  if (turnEnds && this.inbox.nextStep.length === 0) await this.dispatch.serial('agent/turn-stopping', { turn, signal })
  if (turnEnds && this.inbox.nextStep.length === 0) break     // ② 唯一正常退出
  target = 'next-step'
}
```

- **`turnEnds` 就是"模型还欠不欠一次回答"的记账变量**：`step()` 返回 `null` 表示"这一步调了工具，欠下一次请求"，返回 `{kind:'completed'|'max-tokens'}` 表示不欠了（`agent.ts:51`、`:352`）。
- **`max-tokens` 是粘性的**（`agent.ts:310` 注释与实现）：某一步撞上限后，后续步骤即使正常完成也不会把 turn 结局"降级"成 `completed`，便于上游区分"真做完"与"被截断"。
- **`step/end` 一定写**（`finally`），`turn/end` 也一定写（1.4 的 `finally`），任何异常路径都不留未闭合 step。
- **退出前先跑 `agent/turn-stopping` 终检**：监听器若 `agent.steer(...)` 塞入新消息，`inbox.nextStep.length !== 0` 就继续；否则关闭。注意它是 **`serial` 事件（没有 `next()`）**，不像 waterfall 那样可被短路——语义是"所有监听器跑完，然后重读 inbox"。

### 1.2 相位机与状态广播

```ts
// agent.ts:41-49、:114-126
type Phase = { kind: 'idle'; lastTurn: number }
  | { kind: 'maintenance'; abort: AbortController; lastTurn: number; wakeRequested: boolean }
  | { kind: 'running'; abort: AbortController; turn: number; step: number; wakeRequested: boolean }
get status(): AgentStatus { return this.phase.kind === 'running' ? 'running' : 'idle' }
private setPhase(next: Phase) { const prev = this.status; this.phase = next; if (this.status !== prev) this.dispatch.emit('agent/status', { status: this.status }) }
```

- **对外只有两个状态** `idle`/`running`；`AgentStatus` 文档明确说 disposal 不是第三个可观测状态。
- `maintenance`（`agent.ts:157-177`）是"从真 idle 相位跑一个非 turn 任务"，对外仍是 `idle`，但 `whenIdle()` 会等它。
- **每个相位自带 `AbortController`**：`cancel()` 只 abort 当前相位（`agent.ts:149-155`），"取消"是相位局部的，不误伤下一轮。
- 新 turn 换新 controller 并清 `wakeRequested`（`agent.ts:345-347`），注释说明原因：latch 绑在旧 controller 上，换 controller 后 latch 已过期。

### 1.3 输入侧：inbox 与三种投递

输入是**双队列 + 持久 splice 事件**（`packages/core/agent-loop/src/inbox.ts`）：目标为 `next-turn`（自己的新轮次）与 `next-step`（下一个 step 边界）。三个入口（`agent.ts:128-147`）：`followup`（→`next-turn`，唤醒）、`steer`（→`next-step`，唤醒）、`inject`（→`next-step`，**不唤醒**）。

```ts
// agent.ts:128-135 —— 唤醒消息不能加入一个已 abort 的活动
const wakingAfterAbort = wakeup && this.phase.kind !== 'idle' && this.phase.abort.signal.aborted
const resolvedTarget = wakingAfterAbort ? 'next-turn' : target
this.inbox.splice(resolvedTarget, Infinity, 0, [message])
if (wakeup) this.wakeDriver(wakingAfterAbort)
```

这个分类在插入**之前**捕获，注释说明是为了防止"某个 splice 观察者重入 cancel 导致重新分类"——典型防御式写法。`claim()`（`inbox.ts:111-116`）取出整批 `next-step`，若目标含 turn 再加一条 `next-turn`；`preStep` 先删除再让 `agent/pre-step` 改写或拒绝，**被拒批次保持"已删除"状态**（`docs/agent-lifecycle.zh.md:33-34`），即被拒消息不会自己回到队列里造成死循环。

### 1.4 终止条件全表

`TurnEndReasonMap`（`packages/core/session/src/types.ts:200-224`）是**唯一权威的终止原因集合**，可被插件 merge 扩展：

| 终止原因 | 产生位置 | 语义 |
|---|---|---|
| `{kind:'completed'}` | `agent.ts:487`（无 tool_call）、`:492`（`concludesTurn`）、`:298`（首步空批次） | 模型不欠回答且 inbox 空 |
| `{kind:'max-tokens'}` | `agent.ts:484` | 至少一步撞输出上限（粘性） |
| `{kind:'blocked'}` | `agent.ts:291`（`pre-step` 返回 `reject`） | 插件权威否决；turn 被打开但不消耗 step |
| `{kind:'aborted', reason}` | `agent.ts:323-325` | 取消；`reason` 为 `AgentCancelCause`：`{'user'\|'parent'\|'hook'\|'disposed'}`（`types.ts:188-192`） |
| `{kind:'error', error: LlmFailure}` | `agent.ts:329-334` | `LlmError` 保留结构化 facts；其它错误压平成 `{message: errorChain(e), code:'UNKNOWN'}` |
| `{kind:'interrupted'}` | **仅恢复路径**：`repair.ts:133` | 崩溃孤儿 turn 的事后闭合标记；loop 从不 live 发出 |

`turn/end` 写在 `finally`（`agent.ts:336-343`），注释强调"每条退出路径都赋了值"。**"turn 一定会被关闭"是这个设计最重要的不变式**：监听器看到 `turn/start` 就必然等得到 `turn/end`（进程硬崩则由 `repair.ts` 补）。

### 1.5 一次 step 的时序（含重试）

```ts
// agent.ts:358-401 精简
const { assembly } = decision                 // 提示词组装结果：一轮只组装一次
let firstAttempt = true
while (true) {                                // ← step 内重试循环
  const { config, preparedCall } = await this.prepareRequest(turn, step, signal)
  const commits = this.systemPrompt.project(renderedPrompt, { ... })
  for (const { message, intent } of commits) this.session.append('system/message', { turn, step, message }, intent)
  if (firstAttempt) for (const m of decision.messages) this.session.append('user/message', m, { surfaceOp: 'append' })
  firstAttempt = false
  const request = this.buildRequest(config, preparedCall, assembly.tools, startsRequestSeries, signal)
  let started = false
  try {
    const stream = preparedCall?.stream(request) ?? this.loopCtx.llm.stream(request)
    signal.throwIfAborted(); live.start(); started = true   // ← 只有这里之后失败才算"已开始的 attempt"
    for await (const chunk of stream) { signal.throwIfAborted(); live.push(chunk) }
  } catch (error) { if (!started) throw error; /* 写 assistant/attempt 结算 */ }
}
```

`docs/architecture.zh.md:113` 把这条规则写成正式表述：**"重试不重复组装或 `agent/pre-step`"**。所以重试不会让上下文膨胀，也不会重复执行 pre-step 的副作用（压缩、注入）。另外"**流都没建立起来**"与"流建立了但中途失败"被区别对待：前者不写任何 attempt 事件（只是一次失败的准备），后者必须写 `assistant/attempt` 结算。

---

## 2. 模型输出之后：校验与工具执行

### 2.1 参数解析：宽容但不猜测

```ts
// packages/core/agent-loop/src/tool-calls.ts:104-111
function parseArguments(raw: string): unknown {
  try { return raw ? JSON.parse(raw) : {} }
  catch { return raw }        // 非法 JSON 原样保留为字符串
}
```

**JSON 解析失败不抛错**，而是把原始字符串当参数值传下去。理由很实际：参数非法是"模型的错误"，应当作为一次可见的工具失败反馈给模型，而不是把整个 turn 炸掉。

### 2.2 类型化参数校验

执行点（`packages/core/tools/src/schema.ts:585-589`）：

```ts
async execute(args: unknown, exec: ToolRunContext): Promise<JsonValue> {
  const violations = validate(args)
  if (violations.length > 0) throw new ToolArgsError(violations)   // 消息 = 'invalid arguments: ' + violations.join('; ')
  return userExecute(args as InferArgs<S>, exec) as Promise<JsonValue>
}
```

1. **违规信息是"逐项 + 带路径"的字符串数组**（`validateArgs` → `validateJsonSchemaValue(..., '')`，第三参是路径前缀，`schema.ts:461-478`）：模型能直接知道哪个字段错了，比一句 "invalid arguments" 有用得多。
2. **校验只在 execute 里硬做一次；展示路径（`presentCall`/`presentResult`）用软校验**（`schema.ts:590-600` 注释：展示可能跑在**重放任意历史参数**上、可能来自旧 schema，所以必须永不抛错、降级为 `undefined`）。

### 2.3 工具调度：barrier + 有界滚动池 + 启动前重分类

```ts
// tool-calls.ts:85-101
let next = 0
while (next < planned.length) {
  const first = planned[next]!
  const mode = ctx.tools.executionMode(first.exec).kind
  const group = mode === 'parallel' ? planned.slice(next) : [first]   // 独占 → 单元素组（栅栏）
  const outcome = await runGroup(ctx, turn, step, group, mode, signal, acceptContext)
  next += outcome.consumed
  concluded ||= outcome.concluded
  if (outcome.aborted) { for (const c of planned.slice(next)) appendSkippedToolCall(session, turn, step, c.block); return { concluded } }
}
```

```ts
// tool-calls.ts:199-214 精简：启动前重读并发性，注册表变化即可就地造出新栅栏
while (!aborted && nextToStart < group.length && inFlight.size < maxParallelToolCalls) {
  const nextCall = group[nextToStart]!
  if (nextToStart > 0 && mode === 'parallel' && ctx.tools.executionMode(nextCall.exec).kind !== 'parallel') break
  await startCall(nextToStart); nextToStart++; await commitReady()
  if (signal.aborted) aborted = true
}
```

- **独占（非 parallel）工具的组退化为 1 个元素**，等价于一道栅栏：它之前的并行调用全部结算完才轮到它，它自己也不并发。
- 注释（`:201`）点明动机："**在有序提交之后再读一次后续工具的 mode**"——某个工具执行时注册/卸载了别的工具（DSH 支持 agent 自改插件），当前批次立即尊重新分类，不会按旧快照一路冲到底。
- **结果按模型顺序提交**（`tool-calls.ts:146-161`）：`committed` 只能在连续槽位上前进，`commitReady()` 是唯一写 `tool/result` 的地方——"第 3 个先完成"也必须等第 1、2 个结果提交。

### 2.4 取消时的排空与合成（防"卡死"的关键）

```ts
// tool-calls.ts:216-246 精简
try {
  await fillPool()
  while (inFlight.size > 0) {
    const settledIndex = await Promise.race(inFlight.values())
    inFlight.delete(settledIndex); throwSchedulerFailure(); await commitReady()
    if (signal.aborted) aborted = true
    await fillPool()
  }
} catch (error) {
  schedulerFailure ??= { error }
  await Promise.allSettled(inFlight.values())     // ← 排空，不放弃
  throw schedulerFailure.error
}
if (aborted) { for (const c of group.slice(started)) appendSkippedToolCall(session, turn, step, c.block); return { consumed: group.length, aborted: true, concluded } }
```

**取消不会 abandon 已启动的调用**：先 `Promise.race` 把在途排空并提交，再给"没来得及启动的"补合成错误结果。文件头注释（`tool-calls.ts:4-11`）划出一条重要分界：**用户取消 → 补合成结果（保证可重放）；调度器内部故障 → 不造假结果**（宁可留下悬空 call，也不撒谎说工具跑了）。合成结果（`tool-calls.ts:250-260`）是给模型看的可读文本 + 机器可路由的 code：`'Error: tool call aborted before dispatch'` + `{name:'AbortError', code:'TOOL_ABORTED_BEFORE_DISPATCH'}`。

### 2.5 工具执行流水线的六阶段与兜底

`tools/execute` 是**分阶段（staged）调度器**，不是一次函数调用（均在 `packages/core/tools/src/index.ts`）：

1. **`createExecution`**（`:1354-1441`）：分配 execution token；`snapshotJsonValue(exec.arguments)` 无损快照（失败 → 转 `final-result` 错误结果）；判定"模式折叠"（ptc 模式下只有 `run_code` 可直接调用）并**在策略流水线之前**拒绝（`:1413-1434`），注释解释为何必须在 guards/approval 之前：不能让审批者去批准一个注定失败的调用。
2. **`prepareExecution`**（`:1453-1497`）：`tools/pre-execute` waterfall → `ask` 走 `ctx.approval` 一次性批准 → 单调守卫 → 命中则返回 `{kind:'post-result', result: isError}`。
3. **`dispatchScheduledExecution`**（`:1559-1589`）：`tools/execute` waterfall（超时/指标/重试 wrapper 挂这里）；**`dispatchToolBody`**（`:1522-1550`）融合"调用方 signal + wrapper 替换后的 signal"再执行工具体，`catch` → `toolErrorResult(error)`。
4. **`finalizeScheduledExecution`**（`:1599-1611`）：`tools/post-execute` waterfall（可 accept/block/replace/add context）；**`finishScheduledExecution`**（`:1621-1636`）：两次 `materializeFinalResult` 兜底 + `applyFinalContent`（工具自有的 `finalizeContent`，内容级不变式）+ `notifyResult`。

最后一层的兜底写法值得原文照抄：

```ts
// tools/index.ts:1621-1636
let materializedResult: ToolExecutionResult
try { materializedResult = this.materializeFinalResult(result) }
catch (error) { materializedResult = this.materializeFinalResult(toolErrorResult(error)) }
let finalResult: ToolExecutionResult
try { finalResult = this.materializeFinalResult(this.applyFinalContent(exec, materializedResult)) }
catch (error) { finalResult = this.materializeFinalResult(toolErrorResult(error)) }
this.notifyResult(exec, finalResult); return finalResult
```

**"连错误结果本身的物化失败"都要兜住**——这是"绝不让工具层异常穿透到循环"的最终保证。唯一还能从 `runGroup` 抛出的只有调度器自身的不变式违例（如 `:245` 的 `uncommitted settled calls`）。`notifyResult`（`:1646-1666`）对每个观察者单独 try/catch 且 `Promise.resolve(returned).catch(...)`：**一个观察者抛错或返回 rejected promise，既不影响最终结果也不饿死后续观察者**；`packages/core/agent/src/dispatch.ts:113-136` 有同样的手写隔离。

### 2.6 重复调用与"无进展"检测（全仓唯一一处）

实现在 `packages/guard/repeat-tool-reminder`（配置 `:28-50`：`thresholds` 默认 `[3,5,8]`、`include`/`exclude` 为 `*` 通配工具名、`argumentsPreviewChars` 默认 500）：

```ts
// repeat-tool-reminder/src/index.ts:189-207
const canonical = canonicalize(exec.arguments)        // 深度 key 排序后 stringify
const key = JSON.stringify([exec.name, canonical])
const chain = chains.get(exec.agent)
const count = chain !== undefined && chain.key === key ? chain.count + 1 : 1
chains.set(exec.agent, { key, count })
if (!thresholdSet.has(count)) return undefined
const text = count === thresholds[0] ? GENTLE_REMINDER : detailedReminder(exec.name, count, previewArguments(canonical, argumentsPreviewChars))
```

可直接搬的设计要点：

- **键 = (工具名, 规范化参数)**，`canonicalize` 深度 key 排序，"只有属性顺序不同"的参数视为同一调用（`:81-105`）。
- **连续语义**：参数一变 `chain.key !== key`，计数重置为 1。
- **挂在 `tools/post-execute` 而非 `pre-execute`**（`:181-188` 注释）：**被拒绝的调用也流经这条 waterfall**，而"模型对着一个一直被拒的调用猛敲"恰恰最该打断。
- **永不否决，只增补上下文**（`:209-223`）：先 `await next()` 委托，再把 reminder 前置到 `additionalContexts`；`block` 分支也照样带上 reminder。reminder 会作为 `user/message` 注入下一步，因此**模型可见**。
- **用户插话重置链**（`:229-232`）：`agent/pre-step` 批次含 `source.kind === 'user'` 就 `chains.delete(agent)`——"跨过一次用户插话的重复不算循环"。
- **提醒必须打标来源**（`:52-57` 注释）：`{kind:'plugin', plugin:'repeat-tool-reminder'}`，否则在派生历史里会渲染成用户提示词。
- **局限**：它只是提醒，**不中止 turn**；超过最高阈值后静默，对铁了心重复的模型零约束力。而且 reminder 只走 `additionalContexts`，`tool/result` 里看不到"被提醒过"（不污染审计链的代价）。

---

## 3. 上游错误分类、重试与退避

### 3.1 统一错误载体与规范码

```ts
// packages/llm/llm/src/error.ts:13-22
export class HarnessError extends Error {
  readonly code: string   // 稳定、可编程路由的失败类别（如 RATE_LIMIT）；用它路由，绝不解析 message
  constructor(message: string, code: string, options?: ErrorOptions) { super(message, options); this.code = code; this.name = new.target.name }
}
```

规范码（`error.ts:25-48`）：`CONTEXT_WINDOW_EXCEEDED`、`QUOTA`、`EMPTY_RESPONSE`、`INVALID_CREDENTIAL`。适配器层还产生 `AUTH`/`INVALID_REQUEST`/`RATE_LIMIT`/`SERVER`/`TIMEOUT`/`TRANSPORT`/`ABORTED`/`NO_ADAPTER`/`MALFORMED_RESPONSE`/`HTTP_<status>`/`UNKNOWN`。

**分类是"文本 + 结构化"双通道**（`error.ts:50-100`）：`isContextWindowExceededError` 用 5 条正则覆盖各家措辞（`context_length_exceeded`、`maximum context length`、`request too large for the model's context window`…）；`isQuotaExceededError` 区分"账号配额耗尽"（终态）与"限流"（可重试）。注释明确写了两条依据：`EMPTY_RESPONSE` "本次尝试没有产生任何持久内容，所以重试策略视其为安全可重复"；`INVALID_CREDENTIAL` "每次尝试都会以同样方式失败"，**故故意排除在默认可重试集合外**。

### 3.2 HTTP → code 映射（DeepSeek 适配器）

```ts
// packages/llm/llm-deepseek/src/adapter.ts:339-351
if (status === 401 || status === 403) return 'AUTH'
if (status === 413) return 'INVALID_REQUEST'
const detail = [error?.code, error?.type, error?.message].filter(Boolean).join(' ')
if (isQuotaExceededError(detail)) return QUOTA_EXCEEDED_CODE
if (status === 429) return 'RATE_LIMIT'
if (status === 400) { if (isContextWindowExceededError(detail)) return CONTEXT_WINDOW_EXCEEDED_CODE; return 'INVALID_REQUEST' }
if (status >= 500) return 'SERVER'
return `HTTP_${status}`
```

顺序有讲究：**先查配额文本再判 429**（有些 provider 用 429 表示余额不足），**先查溢出文本再判 400 泛化**。

### 3.3 适配器异常 → 终态 finish chunk 归一

```ts
// packages/llm/llm/src/index.ts:1124-1132
function adapterFailureChunk(error: unknown, signal?: AbortSignal): StreamChunk {
  const failure = normalizeLlmFailure(error)
  return { type: 'finish',
    reason: signal?.aborted || failure.code === 'ABORTED' ? { kind: 'aborted', failure } : { kind: 'error', failure } }
}
```

调用点（`llm/src/index.ts:1060-1078`）：适配器选择/首次迭代失败、迭代中途抛错，都 `yield adapterFailureChunk(...)` 后 `return`。契约是显式的（`docs/defensive-patterns.md:13`）：`LlmAdapter.stream()` 可以"抛"或"发 error finish"，但 `LlmRuntime.stream()` **统一暴露为终态 finish chunk**；middleware/consumer 自身缺陷仍然抛出。这样消费者永远不用猜"这个异常是 provider 的还是我自己的"。

`normalizeLlmFailure`（`packages/llm/llm/src/adapter-failure.ts`）用 `Object.getOwnPropertyDescriptor` 读 `code`/`failure`，**不触发 getter**（防 SDK accessor 抛错），并对 hostile coercion 兜底——"错误处理本身不能崩"。

### 3.4 重试策略：默认 fail-closed，决策单点

```ts
// agent.ts:441-463 精简
if (finish.kind === 'error' || finish.kind === 'aborted') {
  live.settle('assistant/attempt', () => this.session.append('assistant/attempt', { turn, step, stream: live.stream }).seq)
  const action = await this.dispatch.waterfall('agent/request-error', {
    turn, step, provider: request.provider, failure: finish.failure, retryPolicy: preparedCall?.retryPolicy, signal,
  }, () => Promise.resolve<RequestErrorAction>(undefined))     // ← 默认 undefined = 不重试
  signal.throwIfAborted()
  if (action?.kind !== 'retry') throw new LlmError(finish.failure.message, finish.failure.code, finish.failure)
  continue                                                     // ← 同一个 step 内重发
}
```

1. **`assistant/attempt` 在决策之前先落盘**：不管后面重不重试，这次尝试都有持久记录（`docs/agent-lifecycle.zh.md:85`）。
2. **默认 `undefined`** = "没有插件声明能恢复就终止 turn"（fail-closed）。
3. 重试是 `continue` → 重新 `prepareRequest` + 重新提交系统提示词 + **不重复用户消息**（`firstAttempt` 已置 false）。
4. `retryPolicy` 来自**提供方路由注册时捕获的不可变策略**（`llm/src/retry-policy.ts:78-79`）：谁提供模型谁决定重试语义。`dsh-llm-retry` 自身无配置并**显式拒绝 `retryPolicy` 键**（`llm-retry/src/index.ts:30-37`），防止配置放错层。

### 3.5 退避算法与 `retry-after`

```ts
// packages/llm/llm-retry/src/index.ts:59-64
function localDelay(config, retry, random): number {
  const exponent = Math.min(retry - 1, 1024)                                  // 防溢出
  const exponential = Math.min(config.initialDelayMs * 2 ** exponent, config.maxDelayMs)
  const jitter = 1 - config.jitterRatio + 2 * config.jitterRatio * random()    // 对称抖动 [1-r, 1+r]
  return Math.min(exponential * jitter, config.maxDelayMs)                     // 抖动后仍夹上限
}
```

默认值（`llm/src/retry-policy.ts:14-24`）：`maxRetries=5`、`initialDelayMs=500`、`maxDelayMs=10000`、`jitterRatio=0.1`、`retryableCodes=['EMPTY_RESPONSE','RATE_LIMIT','SERVER','TIMEOUT','TRANSPORT']`、`mode='normal'`（另一档 `'always'`：不设上限，直到成功/取消/卸载）。

```ts
// llm-retry/src/index.ts:226-238
if (failure.providerRetryAfterMs !== undefined && Number.isFinite(...) && failure.providerRetryAfterMs > 0) {
  if (failure.providerRetryAfterMs > policy.maxDelayMs) {
    if (policy.mode === 'normal') return next()          // ← 服务端要求等待太久：直接放弃重试
    delayMs = localDelay(policy, retry, random)          // always 模式：退回本地退避
  } else { delayMs = failure.providerRetryAfterMs }      // ← 服务端延迟优先，且不再抖动
} else { delayMs = localDelay(policy, retry, random) }
```

`providerRetryAfterMs` 支持秒数与 HTTP-date 两种格式（`llm-deepseek/src/adapter.ts:318-326`）；只有 DeepSeek 直连适配器解析 `retry-after`，pi-ai 走文本分类（无此字段）。

**计数是持久化的，按 `[provider, policyKey]` 归组，并在 `step/start`/`turn/end` 清零**（`llm-retry/src/index.ts:112-138`）：即"重试预算按 step 计，不跨 step 累积"。`policyKey` 含 mode/maxRetries/retryableCodes/backoff（`:66-77`），**改配置就等于开一条新重试序列**——运维调参后老计数不会莫名其妙继续生效。

**"先落盘、再等待"**（`:188-191`）：

```ts
agent.session.append('llm/retry', eventData)                                // 1. 记录"我将要重试"
if (!await cancellableDelay(delayMs, fusedSignal)) return                    // 2. 可取消的等待
agent.session.append('llm/retry-started', { retryId, turn, step, retry })     // 3. 记录"我真的重试了"
```

区分"计划"与"执行"让"等待期间被取消"在日志里可见——崩溃/取消后能分辨"没重试"和"重试了但不知结果"。`cancellableDelay`（`:83-96`）= `setTimeout` + `abort` 监听 + `clearTimeout`，返回 `false` 表示被取消（Python 里对应 `asyncio.wait_for(asyncio.sleep(d), ...)` 或 cancel scope）。

### 3.6 上下文超限：压缩后重试一次（活锁防护）

```ts
// packages/compaction/compaction-basic/src/index.ts:180-224 精简
ctx.on('agent/request-error', async ({ agent, failure, signal }, next) => {
  if (failure.code !== CONTEXT_WINDOW_EXCEEDED_CODE || signal.aborted) return next()
  const retries = this.overflowRetries.get(agent) ?? 0
  if (retries >= policy.maxOverflowRetries) return next()          // ← 默认 maxOverflowRetries = 1
  const generation = agent.session.surface.replaceGeneration
  try { result = await this.compactIfNeeded(agent, 'context-overflow', signal) }
  catch (recoveryError) {
    // 即使可选摘要阶段失败，只要"无模型的剪枝"已推进 surface，就仍算恢复成功
    if (!signal.aborted && agent.session.surface.replaceGeneration > generation) { this.overflowRetries.set(agent, retries + 1); return { kind: 'retry' } }
    return next()                                                   // 保留原始请求错误
  }
  if (signal.aborted || agent.session.surface.replaceGeneration <= generation) return next()
  this.overflowRetries.set(agent, retries + 1); return { kind: 'retry' }
})
```

核心不变式：**只有 `surface.replaceGeneration` 真前进才允许重试**——防活锁的通用判据是"重试必须由一个可观测的状态推进来授权"。恢复顺序是"**先剪枝（无模型、便宜、必成功）再摘要（有模型、可能失败）**"（`:284-289`），且摘要失败不抛弃已落地的剪枝成果。命中上限后，累计计数在成功响应后清零（`:170-179`：`agent/status==='idle'` 或收到 `assistant/message` 时 delete）。**压力压缩（`trigger:'pressure'`）挂在 `agent/pre-step`**（`:150-169`），失败只 `logger.warn` 继续 turn——"压缩是尽力而为，不是硬门禁"。

### 3.7 哪些错误会终止整个 turn

| 情形 | 是否终止 | 依据 |
|---|---|---|
| 可重试码 + 有 `retryPolicy` + 未超预算 | 否，同 step 重发 | `agent.ts:460-463` |
| 其它任何 `finish.kind === 'error'` | **是**（`turn/end{error}`） | `agent.ts:461` |
| `CONTEXT_WINDOW_EXCEEDED` + compaction 能推进 surface | 否，重试（默认仅 1 次） | `compaction-basic/src/index.ts:180-224` |
| `max-tokens` | 否（正常结束），但丢 tool-call 且结局标记 `max-tokens` | `agent.ts:484`、`assembler.ts:137-140` |
| 用户取消 / disposed / hook 要求停 | **是**（`aborted`） | `agent.ts:322-325` |
| `pre-step` 返回 `reject` | **是**（`blocked`），且不消耗 step | `agent.ts:290-293` |
| 工具失败 / 参数非法 / 未知工具 / 工具超时 | **从不终止**：变成 `isError` 结果回到模型 | `tools/index.ts:1621-1636`、`:1429-1432`、`guard/timeout-policy/src/index.ts:73-75` |
| `QUOTA` / `AUTH` / `INVALID_REQUEST` | **是**（不在默认可重试集合） | `llm/src/retry-policy.ts:18-24` |
| 内容策略拒绝（`content_filter` 等未知 finish_reason） | **是**：映射成 `code = reason.toUpperCase()` 的 error finish | `llm-deepseek/src/translate.ts:34-43` |

`'always'` 模式会连 `QUOTA`/`AUTH` 这类"重试必然同样失败"的错误一起无上限重试——这是给无人值守场景的显式逃生门，必须用户主动开启。

---

## 4. 循环如何防止无限迭代

### 4.1 主循环的退出条件（以及一个反直觉的结论）

`packages/core/agent-loop` 里**没有步数上限、没有迭代预算、没有 wall-clock 截止时间**。真正的退出条件只有三条语义条件：

1. **`step()` 返回非 `null`**（模型不再调用工具 / 撞 max-tokens / 某工具结果带 `concludesTurn`）；
2. **`inbox.nextStep` 为空**（无 steering、无 `additionalContexts`、`turn-stopping` 里也没新塞引导）；
3. 或者 `blocked` / `aborted` / `error`。

```ts
// agent.ts:315-321
if (turnEnds && this.inbox.nextStep.length === 0) {
  await this.dispatch.serial('agent/turn-stopping', { turn, signal })
  signal.throwIfAborted()
}
if (turnEnds && this.inbox.nextStep.length === 0) break
target = 'next-step'
```

注意 **`turn-stopping` 之后要再判一次**——终检监听器可能刚刚 steer 了新内容。这是"数据决定"而非"监听器顺序决定"（`docs/subsystems/core.zh.md:1209`）：`turnEnds` 只表示"模型不欠回答"，是否真停由 inbox 是否为空决定。

**为什么敢不设预算？** 无限循环的成本由三处外部机制截断：每次迭代都要过 provider 的请求级重试/限流（真实世界的硬墙）；工具重复调用有 `repeat-tool-reminder` 的顾问式提醒；长目标的**轮次预算是 goal 插件的责任**（`goal-round-driver/src/index.ts:166-172`），不是循环的责任。迁移启示：加"步数上限"前先想清楚"上限到了之后谁能接手"——DSH 的替代方案是让停止变成一个**有产品语义的可扩展决策**（`turn-stopping` + 工具 `concludesTurn`），而不是一个魔法数字。

### 4.2 显式的"提前停止"通道

**通道一：`pre-step` 的 `reject`**（插件权威否决）

```ts
// packages/core/agent/src/runtime-types.ts:112-120
export type PreStepDecision = { kind: 'reject' } | { kind: 'enter'; messages: UserMessage[]; startsRequestSeries?: true }
```
`reject` → `turnEnds = {kind:'blocked'}` 且 `return false`（`agent.ts:290-293`），**不写 `step/start`、不消耗 step**——"还没开始模型调用就叫停"的干净出口。

**通道二：工具结果的 `concludesTurn`**（数据驱动收尾）

```ts
// packages/core/tools/src/index.ts:405-410（契约）、:554-559（类型）
/** Mark a successful final result as terminal for the current agent turn. */
concludeTurn(): void
readonly concludesTurn?: true      // ToolExecutionSuccess 上；失败类型定义为 concludesTurn?: never
```
消费点（`agent.ts:486-492`）：`if (toolCalls.length === 0) return {kind:'completed'}`；`executeToolCalls` 返回 `concluded` 则同样返回 `completed`。物化点 `tools/index.ts:1805`：`const concludesTurn = this.concludingExecutions.has(exec)`——**标记只能出现在成功结果上**。现有用户：`run_code` 的 PTC 子调用（`tools/src/ptc.ts:575`）与 in-process subagent 的结构化输出（`subagent-in-process-driver/src/structured.ts:94`）。

**通道三：`agent/turn-stopping`**（终检点，可放行也可续跑）
定义为 `serial` 事件（无 `next()`），`core.zh.md:1209` 给了明确语义：监听器若 `agent.steer(...)`，机器重读 inbox 再跑一步；不 steer 就关闭。反向控制（提前停）同样是数据：带 `concludesTurn` 的工具结果在该 step 结束 turn。

**这条机制的已知缺口**（`packages/hooks/hooks-claude-code/src/index.ts:268-277`）：

```ts
// TODO(stop-loop-guard): cap consecutive forced continuations; hooks must self-limit meanwhile.
ctx.on('agent/turn-stopping', async ({ agent, turn, signal }): Promise<void> => {
  const merged = await runPoint('Stop', '', stopPayload(agent), { agent, turn, signal })
  if (merged.decision === 'deny') { agent.steer(createUserMessage({ content: [{ type: 'text', text: merged.reason ?? 'continue: blocked by Stop hook' }], source: PLUGIN_SOURCE })) }
})
```

即**"连续强制续跑的次数上限"被明确承认尚未实现**，使用该类 hook 时必须靠 hook 自身设限。迁移时要特别小心这个坑。

### 4.3 在途工具数限制与并发策略

- 上限 `maxParallelToolCalls` 默认 **10**（`packages/core/agent-loop/src/constants.ts`），可在 `cordis.yml` 或 settings 的 `agent-loop` 命名空间改（`agent-loop/src/index.ts:300-315`、`:363-375`）。
- 它是 **getter**（`agent-loop/src/index.ts:396-399`），`tool-calls.ts` 在每个组开始时解构 → **一次设置变更只限制下一个组，不打断在途的组**。
- 校验 `resolveMaxParallelToolCalls`（`:190-196`）要求正整数否则抛错（fail loud）；settings 提交只校验不写运行值，注释说明"拒绝非法值让调度器保持在最后一个好值上"（`:400-411`）。
- **并发分类按参数动态判定，且默认独占**（`tools/index.ts:1266-1276`）：

```ts
executionMode(exec: ToolExecutionInput): ToolExecutionMode {
  const tool = this.resolveExecution(exec.name, exec.agent, exec.parent !== undefined)
  if (!tool?.isConcurrencySafe) return { kind: 'exclusive' }          // 未声明 → 独占
  try { return tool.isConcurrencySafe(exec.arguments) === true ? { kind: 'parallel' } : { kind: 'exclusive' } }
  catch { return { kind: 'exclusive' } }                              // 谓词抛错 → 独占（fail-safe）
}
```
  工具定义侧是可选方法 `isConcurrencySafe?(args): boolean`（`tools/index.ts:261`），即**同一工具不同参数可有不同并发性**（如 `read` 不同文件并行、同文件串行）。它**不进模型 schema**，所以工具目录文档查不到；谓词抛错时降级为独占而非崩溃或误判并行。

### 4.4 单工具超时（协作式）

```ts
// packages/guard/timeout-policy/src/index.ts:56-73
const timeoutMs = ctx.tools.get(exec.name, exec.agent)?.timeoutMs
if (timeoutMs === undefined) return next()               // 没声明就不限时（不猜默认）
using d = deadline(exec.signal, timeoutMs, TOOL_TIMEOUT)
const upstream = exec.signal; exec.signal = d.signal
try {
  const result = await next()
  if (timeoutOf(d.signal, TOOL_TIMEOUT) !== undefined) return toolTimeoutResult(timeoutMs)
  return result
} finally { exec.signal = upstream }                      // ← 恢复调用方 signal，后置监听器看不到超时信号
```

- **协作式**：不是 `Promise.race` 后放弃，而是把超时信号换进 `exec.signal` 让工具自己收尾，等它返回后再替换结果为 `TOOL_TIMEOUT`。文件头注释（`:2-4`）："without racing or abandoning the tool promise"。
- **`timeoutOf(signal, TOOL_TIMEOUT)` 用 code 作用域**（`util/timeout/src/index.ts:184-190`）：嵌套的外层 deadline 先触发时不会被误判成本插件超时，而走普通取消路径。
- 超时结果是给模型看的文本 + 机器可路由 code（`:41-49`）。底层 `deadline`（`util/timeout/src/index.ts:91-113`）用 `AbortSignal.any([upstream, timer.signal])`——**谁先 abort，reason 就是谁的**，所以 `timeoutOf` 只在超时赢时才读到 `TimeoutReason`。

### 4.5 流空闲看门狗

```ts
// packages/util/timeout/src/index.ts:126-160 精简
export function idleWatchdog(upstream, timeoutMs, code): IdleWatchdog {
  const timeout = new AbortController()
  return {
    signal: upstream === undefined ? timeout.signal : AbortSignal.any([upstream, timeout.signal]),
    async next<T>(iterator: AsyncIterator<T>) {
      if (outstanding) throw new Error('idleWatchdog next is already outstanding')
      outstanding = true; arm()                     // ← 只在"有一次读挂起"时计时
      try { return await iterator.next() } finally { clearTimeout(timer); timer = undefined; outstanding = false }
    },
    pulse() { if (!disposed && outstanding) arm() },  // 传输层有活动但没产出迭代值时重武装
    [Symbol.dispose]() { ... },
  }
}
```

计时器**只在一次 `next()` 挂起期间存在**；注释（`:117-119`）："消费者思考时间不算 provider 空闲时间"——这正是"超时该量谁的时间"的正确答案。DeepSeek 默认 300000ms（5 分钟），超时错误带实际值与 `TIMEOUT` code（`llm-deepseek/src/adapter.ts:505-510`、默认值 `:144-145`）。**注意看门狗由各适配器自己实现，`LlmRuntime` 不提供跨适配器兜底**——迁移时最容易漏的一处。

**注意**：窥探器由**各适配器自己实现**，`LlmRuntime` 不提供跨适配器兜底——迁移时这是最容易漏的一处。

### 4.6 崩溃恢复：把"卡死"变成"可恢复"

`packages/core/session/src/repair.ts:29-135` 的 `interruptedTurnClosers()` 在 resume 时扫描持久日志、构造确定性合成闭合事件：

- 未配对的 tool_call → 合成 `tool/result`，并**区分两种语义**（`:94-108`）：已记录开始但结果未知 → "The tool call was interrupted after it was recorded, but no result was durably recorded. Its outcome is unknown. … retry only if the operation is read-only or idempotent; if it may have side effects, first verify external state or ask the user. **Do not retry blindly.**"；根本没开始 → "Retry it if it is still needed."。对应错误码 `TOOL_OUTCOME_UNKNOWN` / `TOOL_NOT_STARTED`（`:14-18`）。
- 顺序讲究（`:128-133`）：先关 call，再关 `step/end`，最后 `turn/end{kind:'interrupted'}`——"一个开着 step 的 turn/end 是不变式违例，必须先合成 step 边界"。
- 时间戳复用最后一条真实事件的时间（`:84-88`），注释："保持确定性，且从不发明一个未来的时间"。日志已平衡时返回空数组（幂等）。

### 4.7 运行时不变量：把"漂移"变成"立刻失败"

`packages/core/agent-loop/src/invariant.ts:21-56` 每次 `llm/stream` 都断言（`prepend: true` 确保不被短路监听器吞掉）：

```ts
if (!Object.isFrozen(options)) fail('a loop-built request must be frozen')
if (!Object.isFrozen(options.messages)) fail('a loop-built request must carry a frozen messages array')
if (!events.some(e => e.type === 'step/start')) return fail('a loop-built request with no step/start in its session log')
if (foldRequestHeader(events) === undefined) return fail('...no request/header event...')
const expected = session.deriveMessages()
if (JSON.stringify(options.messages) !== JSON.stringify(expected)) {
  fail(`llm request for session "${id}" diverges from the dispatch-time durable derivation (log-reconstruction desync)`)
}
```

**"发出去的请求必须等于从日志重新派生出来的请求"**——这一条断言直接消灭"内存状态与持久事实漂移"这一整类 bug（长会话里最典型的隐性卡死/串话来源）。`packages/runtime-diagnostics/invariants/README.md` 说明这是可选运行时诊断层；`dsh-sdk-minimal` 挂载 session/agent/scope/agent-loop 四个伴生检查（对应关系："Session log enclosure and call/result trace"、"agent-status transitions"、"loop-built request reconstruction"）。

### 4.8 后台 Job：长任务不占 turn

`packages/jobs/README.md`：`jobs`（契约 `ctx.jobs`）/ `jobs-local`（进程内存储与执行，按 owner 隔离）/ `tool-jobs`（模型可见的读取、等待、列出、取消工具 + 完成通知）。**job 属于发起它的 agent session，一个 agent 看不到另一个 agent 的 job；完成是"推送到会话"而不是轮询**。于是长任务既不阻塞 turn，也不需要把 turn 超时调得很大——"用架构解决超时"而不是"用更大的超时解决"。

这里存在全仓**唯二的硬截断之一**：`tool-jobs` 的 `maxConsecutiveWakes`（默认 **3**，必须为正整数否则启动失败；`packages/jobs/tool-jobs/src/index.ts`，测试断言 `packages/jobs/tool-jobs/tests/tool-jobs.spec.ts:133-156`），限制"完成通知连续唤醒同一 agent 的次数"，防止一批 job 连续完成把 turn 吵成无限续跑。

### 4.9 关于"没有 turn 预算"的复核

用 9 组关键词全树 grep 复核（`maxSteps` / `maxIterations` / `stepBudget` / `maxTurns` / `iterationLimit` / `wallClock` / `deadline` / `turnTimeout` / `budget`）：`packages/core` 与 `packages/guard` 下除 `guard/timeout-policy` 的单工具超时外**全部 0 命中**；`docs/` 里也没有任何 turn 级步数/迭代/墙钟上限的记载；`docs/defensive-patterns.md` 的 6 条硬规则里**没有一条**关于 turn 超时。易误读点：`config-catalog.md` 里那个 `default 300000` 是**持久 bash 单条命令**的墙钟上限，**不是 turn 的**。

**结论（本报告最重要的负面发现）：turn 本身既无步数上限也无墙钟 deadline。一个持续产出工具调用的模型可以无限步进，系统只会礼貌地提醒它（`repeat-tool-reminder`）而永远不会停下它。** 迁移时必须自己补上这一段。

---

## 5. 流式输出与前后端状态契约（只保留与循环相关的部分）

### 5.1 增量块类型

```ts
// packages/llm/llm/src/types.ts:390-404
export type StreamChunk =
  | { type: 'block-start'; index: number; blockType: ContentBlockType }
  | { type: 'text-delta'; index: number; text: string }
  | { type: 'reasoning-delta'; index: number; text: string }
  | { type: 'tool-call-delta'; index: number; id: ToolCallId; name?: string; argumentsDelta: string }
  | { type: 'block-end'; index: number; block: ContentBlock }
  | { type: 'usage'; usage: TokenUsage }
  | { type: 'finish'; reason: FinishReason; replayState?: ReplayEnvelope }   // 终态：reason 见 FinishReasonMap
```
契约写在类型的 JSDoc 上：**`index` 关联交错的 delta；适配器在终态 finish 之前发 usage、之后什么都不发；工具参数保持原始 JSON 字符串**（不在适配器层解析）。`FinishReasonMap`（`types.ts:126-139`）：`stop`/`tool-calls`/`max-tokens`/`aborted{failure}`/`error{failure}`，merge-extensible。

### 5.2 一次"尝试"的帧机与瞬态/持久双轨

```ts
// packages/core/agent-loop/src/assistant-stream.ts:60-97
push(chunk) {
  const timed = this.accumulator.push({ time: Date.now(), chunk })   // 带时间戳落紧凑累积器
  this.assembler.push(timed.chunk)                                   // 组装 ContentBlock
  this.emit({ type:'chunk', attemptId, revision: this.nextRevision(), index: this.index++, time: timed.time, chunk: timed.chunk })
}
settle(eventType, append) {
  try { seq = append() } catch (error) { this.abandon(); throw error }   // ← 落盘失败就发 abandoned，不假装已提交
  this.emit({ type:'end', attemptId, revision, index, outcome: { kind:'committed', eventType, seq } })
}
```

- **终态帧只在持久事件提交成功后发**（`settle` 注释：`Publish terminal settlement after the matching durable event commits`）。
- `revision` 单调递增且是**进程本地**的（`agent.ts:89-90`），`index` 是 attempt 内稠密零基位置；帧类型在 `packages/core/agent/src/types.ts` 的 `AssistantStreamFrame`。

| | 实时轨 | 持久轨 |
|---|---|---|
| 事件 | `agent/assistant-stream`（`start`/`chunk`/`end`） | `assistant/message` / `assistant/attempt` |
| 载体 | 进程内 emit，不入日志 | Session 追加日志，`seq` 单调 |
| 内容 | 每个 StreamChunk 的原始帧 | **内嵌完整紧凑 stream**：`AssistantStreamRecord[]`（`time0` + `dt[]`，保留逐 delta 精确时间戳，不合并 token 边界） |
| 用途 | UI 增量渲染 | 回放、fork、恢复、转写、遥测 |
| 崩溃时 | 无痕迹（这正是设计目标） | 最后一条已提交事件完好 |

`docs/architecture.zh.md:121`：**"如果进程在 settlement 前硬中断，则不会留下持久 attempt stream"**。而 `assistant/message` "会记录每次成功的提供方调用，包括返回空内容或以 `max-tokens` 结束的调用"（`docs/agent-lifecycle.zh.md:85`）；**空内容不进入派生历史**——`EMPTY_RESPONSE` 被提升为错误而非空消息，正是为了让"空"这条路径有明确且可重试的语义。

### 5.3 一次 turn 写进日志的全部事件

`SessionEventMap`（`packages/core/session/src/types.ts`）在一次 turn 中写入：`turn/start`、`step/start`、`system/message`、`user/message`、`request/header`、`request/context`、`assistant/message`、`assistant/attempt`、`tool/call`、`tool/result`、`step/end`、`turn/end`，外加 `agent/inbox/spliced`（inbox 每次变更都持久化）以及由 `llm-retry` 插件 merge 扩展进来的 `llm/retry` / `llm/retry-started`。

`tool/result` 通过 `sourceEventSeqs: [callSeq]` 显式指向对应 `tool/call`（`tool-calls.ts:289`）；`assistant/message` 与 `tool/result` 都带 `{surfaceOp:'append'}`——派生历史由这些 append 事件折叠，替换类事件（压缩）用另一种 surfaceOp，两者共用一个 `replaceGeneration` 计数器。

**这一个计数器同时服务三处正确性**：压缩重试授权（3.6）、请求序列边界（`agent.ts:561-582` 的 `startsSeries`）、前端 rebaseline。一个计数器撑起三处，很值得抄。

### 5.4 后端与 UI 的状态契约

**对外状态只有 `agent/status` 的 `idle ⇄ running`**（`core.zh.md:1186`）："A waking delivery enters `running` synchronously after reserving cancellation; `idle` means no driver remains scheduled or active." **`whenIdle()` 的语义被刻意收窄**（`core.zh.md:88-94`）："Resolve after the current whole-agent activity reaches quiescence. …**but does not identify the settlement of any particular message**."

`docs/defensive-patterns.md:15-17` 把它升格为通用规则（"Async state is not synchronous state"）：`agent.followup()` 没有 per-message 完成回调；一个 `running` 区间可能同时含多条排队消息、steering、注入工作；取消或 disposal 可能丢弃未开始的项目。**正确做法是自动化调用方显式定义自己的观测区间**（例如"从我的消息的持久 inbox 回执，到下一次全 agent idle"），并把输出描述为"区间级"而非"因果归属于某条消息"。同一条规则还给了反向警告：**若被等待的转换永远不会发生，等待就会挂死，所以必须显式处理"没什么可等"的分支**。

UI 侧用 `attemptId + revision + index` 做幂等应用：revision 跳号 / index 跳号 / pending 配不上，任一处不连续就**整体丢弃并重开 follow**（保守 rebaseline），配合 `seq > startedAfterSeq` + turn/step + `surfaceOp === 'append'` 三重守卫，避免把上一轮或压缩替换写入的消息错配给当前 attempt。注意 `packages/api/gateway/src/stream-protocol.ts` 是 Cordis Remote Event 转发协议（`$events`/waterfall 远程化），**不是** turn 流协议；Web 侧真正的会话流在 `packages/api/session-controller` 与 Session-follow adapter。

---

## 6. 可直接迁移到 Python 单体 Agent 的做法

> 前提：单进程 Python agent（asyncio + 一个会话状态对象），无插件框架、无分布式。

1. **把三层循环显式化，只保留一处真 `while`。** `run_session()`（多轮）→ `run_turn()`（一次用户输入）→ `run_step()`（一次模型调用 + 它请求的工具批次）。`run_turn` 返回 `bool`（还有没有下一轮），`run_step` 返回"欠不欠下一次请求"（`None` = 欠，终止原因 = 不欠）。把所有"该不该继续"的判断收在这两个返回值上，不要在工具实现、异常处理器、UI 回调里各自决定停不停——DSH 里对应的就是 `turnEnds && inbox.nextStep.length === 0` 这一个判据（`agent.ts:319`）。
2. **建立终止原因枚举，并保证 turn 一定会被关闭。** 照搬 `completed`/`max-tokens`/`blocked`/`aborted{reason}`/`error{failure}`/`interrupted`。用 `try/finally` 保证 `turn_end` 一定写；用结构化 failure `{message, code}` 而非裸异常。好处：日志可回放、UI 能区分"做完了/被截断"、崩溃恢复有判据（见第 9 条）。
3. **失败一律降级为数据，绝不穿透主循环。** 三层兜底照抄（`tools/index.ts:1621-1636`）：工具错误 → `is_error` 结果；**连"构造错误结果本身失败"也再兜一层**。工具超时用**协作式**（传超时信号、等它返回、再替换结果为 `TOOL_TIMEOUT`），不要 `asyncio.wait_for` 直接取消——那会留下"不知是否完成的副作用"。最外层 `run_driver` 用空 `except` 兜住并广播状态，**绝不让异常逃逸到事件循环**（那是 status 永远停在 running 的直接原因）。
4. **把"重试"变成单点决策函数，默认不重试。** `on_request_error(failure, policy) -> 'retry' | None`，无策略返回 `None`。可重试码只放 `{EMPTY_RESPONSE, RATE_LIMIT, SERVER, TIMEOUT, TRANSPORT}`。退避 `min(init*2**(n-1), max) * (1-r+2*r*random())` 再夹上限，默认 500ms/10s/0.1/5 次。**服务端 `retry-after` ≤ 上限直接用（不抖动）；> 上限就放弃重试**。重试计数按 `(provider, policy)` 归组、step 开始时清零——不要用全局计数器跨 step 累积。
5. **重试必须在"已打开的 step 内"进行，绝不重复提交输入。** 把 `prompt 组装`、`pre_step` 钩子、`用户消息追加` 都放进 step 的**第一次尝试**（一个 `first_attempt` 布尔），重试只重新发起请求。否则重试 N 次就在上下文留下 N 份用户消息/系统提示词，token 迅速膨胀且模型开始重复回答——这是长会话里最常见、也最容易被忽略的稳定性杀手。
6. **给"恢复"设一个可观测的推进判据，而不是设次数。** 上下文溢出照抄：`g = surface.replace_generation; 压缩(); if replace_generation <= g: 保留原始错误（不重试）; else 重试一次`。把这个模式也用到"校验失败重试""gate 不通过重试"（对应该项目的 P-2 问题）：**重试必须由一个可观测的状态指纹前进（generation / 内容哈希 / 覆盖关系集合）来授权**。同时"先做无模型的廉价剪枝，再做有模型的摘要"，摘要失败不抛弃已落地的剪枝。
7. **工具批次：barrier + 有界并发 + 按请求顺序提交结果。** 独占型（写文件、改全局状态）串行成栅栏，只读型进 `max_parallel=10` 的滚动池；**每个任务启动前重读一次"是否可并行"**（工具集在批次中途可能变化）。派发可乱序完成，但结果必须按模型给出的调用顺序写入历史。取消时"先排空已启动的，再给未启动的补合成错误结果"，让重放永远合法（assistant 的 tool_call 一定有对应 tool_result）。
8. **无进展检测用"状态指纹 + 分级提醒"，而不是"次数上限"。** 维护 `(工具名, 规范化参数)` 的连续计数，命中 3/5/8 注入用户可见提醒（先温和后详细，带参数预览并截断到 500 字符），用户插话时重置。**提醒要打标来源**（`source.kind='plugin'`），否则会渲染成用户提示词。计数器要挂在 **post-execute**（被拒的调用也要计数），并**升到会话级**——不要用 agent 局部变量，因为每轮重建 agent 会让它归零（正对该项目 P-3 问题）。注意它的局限：只是提醒，**不停止**；turn 级硬上限要另外自己做（DSH 在这里是留白的）。
9. **崩溃恢复写一个幂等的 `close_interrupted_turn(events)`。** 扫描日志，对未配对的 tool_call 补 `is_error` 结果并区分"已记录开始但结果未知"（提示：只在只读/幂等时重试，否则先核对外部状态或问用户）与"根本没开始"（可直接重试）；再补 `step_end`、`turn_end{reason:'interrupted'}`。时间戳复用最后一条真实事件的时间以保证确定性；日志平衡时返回空（幂等）。这样"进程被 kill"就从"卡死"变成"可恢复"。

---

## 7. 看起来有用、但深度依赖 DSH 插件框架、难以迁移的部分

| DSH 机制 | 为什么难迁移 | 迁移建议 |
|---|---|---|
| **Cordis waterfall + `next()` 委托语义**（`agent/{pre-step,request,request-error}`、`llm/stream`、`tools/{pre-execute,execute,post-execute}`） | "必须调 `next()` 才委托、否则短路"是有序中间件协议；`agent/turn-stopping` 又刻意是**无 `next()` 的 serial**。Python 普通回调列表没有这两级语义，中间件顺序与短路只能靠约定维护 | 只留 3–4 个真正需要的钩子，用**固定顺序的显式列表 + 每个钩子返回 decision 对象**（`allow/ask/deny/replace`）表达短路，别去仿真 waterfall |
| **`ctx.effect()` 注册即副作用 + 自动反向 dispose** | 插件/服务/监听器生命周期由 Cordis fiber 树管理（加载、卸载、HMR、父卸载级联）；`agent-loop/src/index.ts:419-420`、`llm-retry/src/index.ts:254-258` 靠它保证"卸载时 abort 并 drain 在途操作" | 换成"一个 context manager 持资源 + 显式 `shutdown()`"；关键是**卸载时必须 abort 且把在途操作 drain 到静止**（`Promise.allSettled` ↔ `asyncio.gather(..., return_exceptions=True)`） |
| **Session projection 持久折叠状态**（`inbox`、`turnBoundary`、`llmRetry` 都用） | `ctx.sessionProjections.register({key, stateVersion, stateSchema, apply})` 把"事件→类型化状态"做成可注册、可版本化、可 wire 投影的机制，还带 zod 校验 | 只需要"**事件日志 + 若干纯函数 fold**"：`reduce_state(events)`，每次从日志重算或按 `seq` 增量 fold。不要引入注册表 |
| **durable-before-wait 的顺序保证 + 配套 invariant** | "先写 `llm/retry` 再等、等完写 `llm/retry-started`"之所以可信，是因为有 `dsh-invariants` 在运行时断言"loop-built request == 日志派生结果" | 逻辑可照抄（两条事件区分"计划/执行"），但**断言要自己写成测试**：`assert build_request(state) == derive_from_log(log)`。这也是把 P-1（plan/run/chart 三重状态漂移）真正钉死的方式 |
| **`ctx.tools[TOOL_RUNTIME_SCHEDULER]` 的 staged 调度器**（`prepare/dispatch/finalize/finish` + `MutableToolRunContext` + WeakMap 侧表 `contentFinalizers`/`cancellationStates`/`deferredContexts`） | 为让**并发调度**与**策略流水线**解耦：`tool-calls.ts` 只做编排，注册表持策略。代价是状态放 WeakMap、只对"注册表铸造的 execution"有效（多处 `throw ... invariant violated`） | 合并成一个类 `ToolRuntime.prepare()/dispatch()/finalize()`，用 dataclass 带状态而非侧表。**要保留的是"四阶段划分"本身**，它是"策略可插拔而不改循环"的关键 |
| **`AbortSignal.any` + `using` + `TimeoutReason` code 作用域** | 用"融合多 signal、按 code 认领超时原因、`Symbol.dispose` 自动清理"表达取消来源；Python 无同构设施 | 自建 `class Cancellation(reason, code, event)`；融合 = 监听多个来源，谁先到就写入自己的 reason；超时按 `code` 区分归属——**语义照抄、机制自建**，否则嵌套超时会互相误判 |
| **注册期捕获的不可变 retry 策略 + settings 热重载** | 策略在适配器注册时冻结，settings 变更走 Schemastery 校验换 source；`llm-retry` 自身显式拒绝 `retryPolicy` 键以防配置放错层 | 单体里"启动时读一次 → 冻结进 dataclass"，并在加载阶段**对放错位置的配置键直接报错**（fail loud 这个习惯比机制更值得抄） |
| **`repeat-tool-reminder` 依赖"被拒调用也流经 post-execute"这一保证** | 它能捕获"模型反复敲一个被拒的调用"，是因为注册表**把 deny 也路由过同一条 waterfall**（`:181-188` 注释） | 迁移时必须自己保证**"被策略拒绝"与"工具抛错"走同一条后置处理路径**，否则重复检测会漏掉最该打断的那类循环 |
| **hooks-claude-code / hooks-codex 的 Stop→`turn-stopping` 续跑** | 依赖 serial 事件 + `agent.steer()`；且**连续强制续跑上限是已知 TODO**（`hooks/hooks-claude-code/src/index.ts:268`） | 可保留"终检钩子能抢在收尾前续一步"，但**必须自己加连续续跑上限**——DSH 自己都还没做 |
| **`packages/api/gateway/src/stream-protocol.ts`** | 名字像 turn 流协议，实际是 Cordis Remote Event 转发协议，与 UI 的 turn 状态无关 | 不要照它设计前端协议；该抄的是 5.2 的 `attemptId+revision+index` 帧与"瞬态/持久双轨" |
| **运行时不变量注册表（`ctx.invariants.register(pkg, install)`）** | 可插拔、可 allowlist/blocklist、按包归属报告失败 | 退化成"一组 `assert` 函数 + 一个 `DEBUG_INVARIANTS` 开关"；重点是断言本身（如"发出的 request == 日志派生的 request"），不是注册表 |
---

## 附：一句话总结

DSH 让 Agent 不卡死的核心不是"加超时"，而是四句能直接搬到 Python 的硬规则：

1. **只有一处循环**，退出条件是"模型不欠回答 **且** 队列为空"，且该条件在终检钩子之后**再读一次**。
2. **失败降级为数据**：工具层永不向上抛（连"构造错误结果失败"都有兜底）；上游错误归一成带 `code` 的结构化 failure。
3. **重试由显式决策点授权、默认不重试**；上下文恢复的授权判据是"可观测状态真的推进了"（`replaceGeneration`），不是"再试一次看看"。
4. **每个可能永久挂起的 await 都有可归属的中止来源**：工具超时带自己的 code、流空闲看门狗只在"读挂起"时计时、取消时先排空已启动的再补合成结果、崩溃后还有幂等的日志闭合。

**唯一的致命留白**：turn 本身没有步数上限也没有墙钟 deadline（第 4.9 节）。一个持续产出工具调用的模型可以无限步进——迁移时必须自己补这一块。
