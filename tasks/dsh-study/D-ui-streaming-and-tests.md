# D — 流式 UI 状态一致性 + 可靠性测试网（DeepSeek Harness v0.1.5 源码研读）

研读对象：`/Users/heihe/Desktop/Competitions/GeoAI_challenge/tmp/deepseek-harness`（只读，未修改任何文件）。
版本锚点：`package.json:3` → `"version": "0.1.5-rc.2"`；`git log -1` → `c291e7961a515f6d7af9304e7fd1d257929aef26`（2026-09-10）。下文 `path:line` 相对仓库根；代码保持英文原文。

---

## 0. 机制速查表

| # | 机制 | 作用 | 关键源码位置 | 解决什么问题 |
|---|---|---|---|---|
| 1 | **Generation（连接代次）** | 每次成功建立的连接是一个单调递增 `id`，丢失即作废 | `packages/client/connection/src/client/connection.ts:77-101`；`client/index.ts:272-286` | 判定"消息属于哪一代"，杜绝跨代脏状态 |
| 2 | **Ready 握手（先挂监听后报就绪）** | 载体必须先接好增量监听再调 `ready(host)` | `connection.ts:58-70`；`packages/api/gateway/src/client/remote-events.ts:140-145` | 消除"连上了但事件窗口未就绪"的丢事件缝隙 |
| 3 | **Warn + Hard deadline 双阈值** | 慢握手先告警，再硬性取消并重连 | `connection.ts:288-323`；`recovery-config.ts:12-31` | 卡死连接不挂死 UI，也不误杀"慢但正常" |
| 4 | **退避抖动 + 离线暂停** | `cap/2 + rand*cap/2`，上限 10s；离线完全不重试 | `connection.ts:139-147`、`:127-137`；`client/index.ts:169-182` | 避免重连风暴与离线噪音 |
| 5 | **状态去重 + sink 异常隔离** | 相同状态不重复通知；业务回调抛错不影响重连 | `connection.ts:270-275`、`:277-284` | 消除无意义渲染；业务 bug 不放大为连接故障 |
| 6 | **逻辑流跨代重开** | 物理代次变化时同一逻辑流自动重开，丢弃旧代次迟到值 | `packages/api/gateway/src/client/remote-stream.ts:95-157`、`:241-256` | 逻辑订阅与物理连接解耦 |
| 7 | **单次容忍重试** | Host 仍可用时只允许 1 次隔离重试 | `remote-stream.ts:160-197` | 区分瞬时抖动与真断线 |
| 8 | **Carrier vs Terminal 分类** | carrier 错误可重试；业务/协议错误立即终结该流 | `stream-client.ts:16-25`；`remote-stream.ts:132`、`:206-213` | 重试不把"协议被破坏"当网络抖动重放 |
| 9 | **Journal 游标代数 + 缺口修复** | 条目游标区间须严格相接；断开后按游标重读一页补齐 | `packages/api/gateway/src/client/journal-stream.ts:305-336`、`:338-395`、`:473-493` | 丢事件必被发现并补齐，不留历史断裂 |
| 10 | **游标幂等应用** | `compare(cursor,last) <= 0` 直接丢弃；部分重叠报违规 | `journal-stream.ts:310-315` | 重连重放的重复事件不二次渲染 |
| 11 | **恢复游标单调校验** | 重开后开游标落后于已应用尾游标 → 协议违规 | `journal-stream.ts:277-282` | 防止恢复旧快照造成内容回退/闪烁 |
| 12 | **页完整性断言** | 页尾游标须等于请求游标；页内条目须连续 | `journal-stream.ts:551-563`、`:574-579` | 半截页/乱序页被拒绝而非静默应用 |
| 13 | **快照流（Baseline+Delta）** | 每代次恰好一个开快照，之后才是增量 | `packages/api/gateway/src/client/snapshot-stream.ts:67-93` | 断线保留旧值、重连原子替换，不闪白 |
| 14 | **物理复用 + 逻辑多路复用** | 一条 WebSocket 承载多条独立可取消逻辑流 | `stream-client.ts:34-120`、`:275-302` | N 个订阅不产生 N 条连接 |
| 15 | **Assistant 流 revision 校验** | 增量帧 `revision` 必须 `= expected` | `packages/api/session-controller/src/client/transport.ts:206-216` | 丢一帧即可检测，不必等结尾 |
| 16 | **Transient/Durable 双轨 + 分数 seq** | 实时增量是临时行（分数 seq），持久事件到达后原子替换 | `.../sessions/assistant-stream.ts:120-183`；`contract/events.ts:5-35` | 流式显示与持久真相解耦，同段文本不渲染两遍 |
| 17 | **Rebaseline 兜底** | 任何对不齐 → 请求整窗重读 | `assistant-stream.ts:108/123/139/166/176`；`sessions/session.ts:677-684` | 无法增量修复时宁可整体重取，绝不显示错乱 |
| 18 | **渲染节流三通道** | 结构走 microtask、可见流式走 rAF、受控输入走同步 | `.../sessions/notifier.ts:31-55`、`:87-96` | 大量 chunk 不炸主线程；caret 不跳尾 |
| 19 | **懒重建** | 无订阅者不重建，只置 dirty | `notifier.ts:57-65`、`:89` | 后台会话零快照构建开销 |
| 20 | **乐观 Echo + rpcId 去重** | 用户消息本地回显，持久事件按 `source.rpcId` 退场 | `sessions/session.ts:725-761`；`ui-chat/src/client/chat/ChatView.tsx:288-297` | 输入即时反馈且不出现重复气泡 |
| 21 | **装配层 revision 连续性** | 重复 revision 丢弃；跳号降级为整窗替换 | `ui-conversation/src/client/conversation/assembly.ts:101-107` | 中间层二次兜底，防 delta 被重放 |
| 22 | **顺序保留式基线合并** | 权威基线到达时保留已显示行相对顺序 | `.../client/ordered-baseline.ts:11-43` | 基线刷新不引起列表跳动 |
| 23 | **引用稳定** | 值相等的行复用同一对象；快照未变则同一引用 | `manager.ts:139-143`；`chat-snapshot-builder.ts:59-64` | React memo 不失效，避免全列表重渲 |
| 24 | **`connection/reset` 广播** | 新代次建立后，线派生缓存统一重取 | `client/index.ts:17-26`、`:272-277` | 一个明确失效点，替代散落缓存逻辑 |
| 25 | **线边界强校验** | 入站事件只允许白名单字段；拒绝自定义原型对象 | `session-wire-event.ts:14-46`；`remote-events.ts:313-320` | 坏数据/原型投毒在边界即失败 |
| 26 | **快照一致性不变量（文档化）** | "历史+实时追加"必须等价于"整窗重放" | `docs/subsystems/conversation.md:245-256`（尤其 `:251`） | 可重放性成为验收条件 |
| 27 | **分层测试网 + per-file 100%** | unit/coverage/e2e/expected/snapshot/web/bench 七层 | `docs/testing.md:9-17`；`vitest.config.ts:352-368` | 每层只证明自己那层 |
| 28 | **录制会话快照三态** | transcript 与 UI 输出落盘为夹具；CI 只读重放 | `docs/testing.md:12-17`；`snapshots/AGENTS.md`；`vitest.snapshot.config.ts` | 无 key 也回归"完整组装后的行为" |
| 29 | **性能预算门禁 + 显式校准** | `CI_TIME_SCALE=2`、`HEADROOM=1.25`；重连替换 63ms 上限 | `benchmarks/support/calibration.ts:4-15`；`benchmarks/active-stream-reconnect/reconnect.bench.client.ts:9-56` | 稳定性回归有数值红线 |
| 30 | **PR 汇总裁决 job** | 任一必需 job 失败/取消/跳过 → 裁决 job 直接红 | `.github/workflows/ci.yml:707-714` | "跳过"不能伪装成通过 |
| 31 | **防御性模式清单** | 正交结果独立上报、dispose 必须静默、回调异常隔离 | `docs/defensive-patterns.md:7-33` | 把已发生缺陷类别固化为规则 |
| 32 | **超时策略 + 专项测试** | 工具声明 `timeoutMs`，超时映射为 `TOOL_TIMEOUT` | `packages/guard/timeout-policy/src/index.ts:56-74`；`tests/timeout-policy.spec.ts:97-232` | 循环内挂死工具可确定性收口 |
| 33 | **浏览器级重连 e2e（注入时钟）** | 断网、拒绝连接、逐次 kill socket，断言重试次数与文案 | `apps/web/tests/lifecycle-chrome.e2e.ts:401-524` | 重连在真实浏览器中被验证，含"不许多重试" |

---

## 1. (A) 流式事件协议长什么样

### 1.1 三条并行路径，共用载体、协议互不伪装

`docs/api-gateway.md:160` 划界：

> Remote handles only unary method calls with one request and one result. Session event streams, pagination, incremental reduce, projection, and entity substreams require a separate data protocol and registration model; even when they reuse the Connection, they must not masquerade as Remote methods.

| 路径 | 形态 | 语义 | 位置 |
|---|---|---|---|
| 一元 RPC（Typert Remote） | `POST /api/<ns>/<method>`，`{args}` → `{result}` | 请求/响应，可取消，`rpcId` 关联 | `packages/client/connection/src/client/rpc.ts:31-71` |
| 事件转发流（`$events`） | 长流：`ready` → `emit` / `waterfall` / `cancel` | Cordis 事件跨进程转发（含 waterfall 回执） | `packages/api/gateway/src/client/remote-events.ts:122-183` |
| 数据流（streams） | WebSocket mux：`open`/`item`/`end`/`error`/`cancel` | 快照流 / Journal 流 | `packages/api/gateway/src/stream-protocol.ts:243-310`；`stream-client.ts:80-120` |

三条共用同一 Connection 与同一 WebSocket mux（`stream-client.ts:304-310`），但消息类型彼此独立。层级顺序为 `remotes → gateway → connection → webserver`（`docs/api-gateway.md:162`）。

### 1.2 帧格式与"精确键 + 原型白名单"校验

服务端消息是闭合联合（`stream-protocol.ts:260` 起），解析器对每种帧做精确键校验（`stream-protocol.ts:293-297`：`exactKeys(value, ['type','streamId'])` 或带 `value` 的两种键集合，二者之外一律拒绝）。事件转发流同款严格，并额外拒绝自定义原型（廉价防原型投毒）：

```ts
// packages/api/gateway/src/client/remote-events.ts:311-320（节选）
function isRemoteEventRecord(value: unknown): value is Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return false
  const prototype: unknown = Object.getPrototypeOf(value)
  return prototype === Object.prototype || prototype === null
}
function hasExactRemoteEventKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const ownKeys = Reflect.ownKeys(value)
  return ownKeys.length === keys.length && keys.every(key => Object.hasOwn(value, key))
}
```

### 1.3 事件类型：emit / waterfall / serial

全仓矩阵见 `docs/event-producer-consumer.md:8-77`（由 `scripts/gen-doc-graphs.ts` 生成）。三类语义不同：`emit` 广播无返回值（`packages/core/session/src/index.ts:72`）；`waterfall` 必须 `next()` 委派否则短路（`packages/core/tools/src/index.ts:155`）；`serial` 无 `next()`（`packages/core/agent/src/runtime-types.ts:391`）。

跨进程转发只对**被选中**事件生效，waterfall 需回执（客户端派发后回传 `{clientId, eventId, outcome}`，`remote-events.ts:185-221`）。取消按 `eventId` 精确取消，代次结束时才统一 abort：

```ts
// packages/api/gateway/src/client/remote-events.ts:147-150
if (frame.type === 'cancel') {
  active.get(frame.eventId)?.abort(new Error('client api: Remote event was cancelled by the Host'))
  continue
}
```

### 1.4 增量 vs 快照：按数据语义分层强制

**快照流**（控制面 / Workspace）的三条不变量（`snapshot-stream.ts:70-89`）：① 每代次恰好一个开快照，否则 `emitted more than one opening snapshot`；② 快照前不得有 update，否则 `emitted an update before its opening snapshot`；③ **旧值保留到新快照被成功应用**（`docs/subsystems/web-client.md:79`：retain the last published value while disconnected, then atomically replace it from a fresh opening baseline）。第 ③ 条是"不闪白"的直接原因。

**Journal 流**（会话事件窗）：开快照 + 之后按 seq 追加，用游标代数做连续性校验（§2.3）。

**助手增量流**：独立密集帧通道，带 `revision`（§2.4）。

### 1.5 序号体系：六种编号各司其职

| 编号 | 作用域 | 单调性来源 | 位置 |
|---|---|---|---|
| `generation` | 每条逻辑流内部 | 客户端 `++this.generation` | `remote-stream.ts:109` |
| `seq` | 会话事件日志（持久） | Host 日志追加序，校验为非负安全整数 | `session-wire-event.ts:34-40` |
| `cursor` | Journal 窗口 `[first,last]` | 由条目导出，区间须严格相接 | `journal-stream.ts:565-572` |
| `revision` | Assistant 流代次 | 重开 +1，客户端强制 `expected = prev + 1` | `transport.ts:206-216` |
| `rpcId` | 一次一元调用 | 发起方铸号，响应方回显并校验 | `client/rpc.ts:36-59` |
| `eventId` | 一次跨进程事件派发 | Host 铸号 | `remote-events.ts:155-166` |

`rpcId` 双向纪律被写成硬性规则（`packages/client/AGENTS.md`：`rpcId is strictly bidirectional: the initiator mints, the responder echoes, and minting stays in Connection`），且**会被校验**：

```ts
// packages/client/connection/src/client/rpc.ts:55-59
const full = parseConnectionResponse(await response.json())
if (full.rpcId !== rpcId) {
  throw new Error(`rpcId mismatch for ${endpoint}: sent ${rpcId}, got ${full.rpcId}`)
}
return full.result
```

反向兼容细节：`docs/api-gateway.md:127` 说明只有"无法归类"的抛错才折叠为 `gateway/internal`，业务错误码（`session/not-found`、`session/agent-busy`）**原样上线**，客户端可据语义分流而不必解析字符串。

### 1.6 ACP 侧：chunk 型增量协议

ACP 服务器复用外部 `@agentclientprotocol/sdk` 的 `SessionUpdate` 联合，**只发 6 个变体**且全部从**已提交的** DSH 会话事件派生（`packages/acp/acp/src/updates.ts:16-45`）：reasoning → `agent_thought_chunk`，其余块 → `agent_message_chunk`，工具 → `tool_call` / `tool_call_update`，另有 `usage_update` 与 `config_option_update`（`src/session.ts:221`）；没有 `plan`、没有 `available_commands_update`。

三点值得注意：① 名字虽叫 `*_chunk`，但它是"**按块的提交快照**"而非 token 级 delta——一次 `assistant/message` 拆成若干块更新；② 协议本身**无 seq、无 revision**（`grep seq|revision` 在 `packages/acp/acp/src` 零命中），顺序只靠**每会话一条 `outputTail` promise 链**串行化（`src/session.ts:102`、`:345-352`）；③ ACP 层**没有任何超时**，悬挂的 in-flight prompt 只能靠客户端 cancel 解除。因此序号与幂等责任全部留在 DSH 自己的客户端。

取消是协作式且区分进度（`session.ts:474-480`：置 `cancelRequested`、abort admission、仅在消息已入队时调 `agent.cancel({kind:'user'})`），最终让本次 prompt 以 `stopReason: 'cancelled'` 收口（`session.ts:311-313`）而非抛错。一个反直觉映射在 `packages/acp/acp/src/codec.ts:13-32`：harness 的 `aborted`（被 hook 或他人中止）映射为 **`end_turn`**，只有 `interrupted` 才映射 `cancelled`——注释说明 `cancelled` 专门保留给"显式客户端取消与 disposal"。

---

## 2. (A) 客户端如何避免闪烁 / 重复渲染 / 丢事件

### 2.1 物理层：ConnectionController

**代次 + 一次性 ready。** 三重守卫把"迟到的 ready"当一等公民：

```ts
// packages/client/connection/src/client/connection.ts:216-220
const reportReady = (host: ConnectionHostInfo): void => {
  if (sourceReady || gen !== this.generation || !this.isGenerationActive(ac)) return
  sourceReady = true
  resolveReady(host)
}
```

契约写在类型注释（`connection.ts:58-70`）：*The source must attach its incremental listeners before calling `ready` … On abort it must stop delivery, release its resources, and settle before a replacement can start.* 代次建立时**先撤回旧代次再宣布 connecting**，保证 UI 不在中间态读到上一代 host 事实（`client/index.ts:278-285`；测试 `packages/client/connection/tests/client-apply.client.spec.ts:346-377`）。

**双阈值就绪超时**（`connection.ts:295-302`）：先 `generationReadyWarnMs` 告警、再 `generationReadyTimeoutMs` 硬杀。默认值集中在 schema 并用 `z.natural().min(1).max(MAX_TIMER_MS)` 钉在浏览器 32 位定时器上限内（`recovery-config.ts:21-31`）：`backoffBaseMs=500`、`backoffFactor=2`、`backoffMaxMs=10000`、`warn=3000`、`timeout=15000`。

**退避抖动 + 状态去重 + sink 隔离**：

```ts
// packages/client/connection/src/client/connection.ts:144-147
private backoffDelay(attempt: number): number {
  const cap = this.backoffCap(attempt)
  return cap / 2 + Math.random() * (cap / 2)
}
```

```ts
// packages/client/connection/src/client/connection.ts:271-284（节选）
private emitState(state: ConnectionState): void {
  if (this.lastState === state) return          // 相同状态不重复通知
  this.lastState = state
  this.callSink(() => this.sinks.onStateChange?.(state))
}
private callSink(fn: () => void): void {
  try { fn() } catch (error) { console.error('[connection] connection sink threw:', error) }
}
```

离线时走 `waitForAbort` 原地等待、完全不重试（`:167-176`）；网络恢复重置 attempt 并立刻重连（`:127-137`）。**连接状态永不进 store**（`:72-79`：`State (generation/attempt) is instance-private, never in the store.`）。

### 2.2 逻辑层：RemoteStream 的"重开而不丢语义"

`accept()` 是**写回调度器**的握手：只有领域消费者确认"这一代次的开快照/游标有效"后才调 `accept()`，调度器据此重置重试计数。

```ts
// packages/api/gateway/src/client/remote-stream.ts:119-123
accept: () => {
  if (this.generationAbort !== generationAbort || revision !== this.revision) return
  accepted = true
  attempt = 0
},
```

这解决"**收到了帧 ≠ 这一代次可用**"：开快照校验失败时重试计数不重置。重试节奏区分两种处境（`:166-170`）：Host 代次还在 → 只允许 1 次隔离重试；已消失 → 订阅 generation 发布后重开（`:171-196`）。错误分类决定生死，且注释本身是一条设计原则（`:199-205`）：*Mark a terminal escape before it crosses the stream boundary: consumers discriminate failures by code, so an unmarked throw reads as a local bug … The carrier class never escapes as a terminal outcome.*

### 2.3 会话事件窗：游标代数 + 缺口修复 + 幂等（最值得抄的一段）

每个条目抽象成 `[first, last]` 游标区间（`journal-stream.ts:565-572`），应用入口做三种分流：

```ts
// packages/api/gateway/src/client/journal-stream.ts:310-322（节选）
const { first, last: cursor } = this.entryRange(entry)
const last = this.lastCursor as Cursor
if (this.options.compare(cursor, last) <= 0) return                 // 完全重复/更旧 → 幂等丢弃
if (this.options.compare(first, last) <= 0) {
  throw protocolViolation(`${this.options.name} emitted a partially overlapping entry`)
}
if (!this.options.follows(last, first)) {                           // 缺口 → 读一页补齐
  const request = this.repairPageRequest()
  const superseded = await this.replaceThrough(request, cursor, item.generation, item.signal, iterator, [entry], [])
  ...
}
```

- **完全重复/更旧** → 丢弃（不渲染）
- **部分重叠** → 协议违规（不应发生；发生了就是 bug，宁可 loud fail）
- **不连续** → 触发修复：读权威页补齐后发布一个 `replace`

恢复不能倒退（`:277-282`）：`if (resumed && compare(cursor, this.lastCursor) < 0) throw protocolViolation('… resumed at a cursor behind the last applied entry')`——直接对应"重连后内容回退/闪烁"。页必须自洽且读到位（`:574-579`）：页尾游标必须等于请求游标，否则 `page did not end at its requested cursor`；页内条目必须连续（`:551-563`）。

修复还要处理"读页期间新条目仍在到"：`readPageWhileFollowing`（`:397-445`）用 `Promise.race` 同时等页返回与下一个流条目，把流条目暂存 `queued`，再用 `mergeReplacement`（`:473-493`）按游标严格拼接；拼不上返回 `undefined` 触发二次读页（`:361-379`），仍不行则报违规。

`packages/api/gateway/tests/journal-stream.client.spec.ts`（1118 行）的测试名几乎就是这台状态机的不变量清单：

```
:227  defers notifications behind a durable gap until replacement commits
:412  deduplicates complete ranged entries and rejects partial live overlap
:523  repairs a live gap before publishing another change
:680  merges contiguous entries that arrive while a replacement page is loading
:791  reports a resumed generation that emits an entry before its cursor
:927  discards old-generation entries while waiting for the replacement opening
:1056 reports duplicate and regressed generation cursors as terminal failures
```

辅助规格 `control-retry.client.spec.ts`（373 行）专测逻辑流重开：`:100` `permits one isolated retry while the Host remains available`、`:146` `waits for a replacement Host generation after observing unavailability`、`:241` `drops values and cancellation failures from a replaced generation`。

### 2.4 助手流式文本：Transient/Durable 双轨 + Rebaseline

窗口条目分两类，临时行的 `seq` 是**分数**，插在持久游标与它 +1 之间：

```ts
// packages/api/session-controller/src/client/contract/events.ts:19-22
export type SessionEventLikeEntry =
  | { readonly type: 'event'; readonly event: SessionEvent }
  | { readonly type: 'transient'; readonly event: AssistantLiveChunkEvent }
```

```ts
// packages/api/session-controller/src/client/sessions/assistant-stream.ts:147-149
type: 'assistant/live-chunk',
seq: this.durableCursor + 1 - 1 / (this.transientInGap + 1),
```

分数 seq 的价值：临时行有**严格可排序的位置**，渲染层按 unified `seq` 排序即可，无需额外分类逻辑也不会插错位置。关键纪律：**增量帧只能是 update，不能是 start**（`docs/subsystems/conversation.md:45`）。正式结算到达时**原子替换 + 按 seq 去重**：

```ts
// packages/api/session-controller/src/client/sessions/assistant-stream.ts:172-179（节选）
if (this.publishedSeqs.has(frame.outcome.seq)) return undefined
const entry = this.pending.get(frame.outcome.seq)
if (entry === undefined || entry.event.type !== frame.outcome.eventType) {
  return { type: 'rebaseline' }
}
```

**Rebaseline 是最后兜底**：出现重复结算、序号跳变、未知 attempt、chunk index 不连续等任何一种对不齐，就返回 `rebaseline` 由上层整窗重读，且带双重守卫（在微任务里重开，期间流已被替换则放弃）：

```ts
// packages/api/session-controller/src/client/sessions/session.ts:677-684（节选）
if (result?.type === 'rebaseline') {
  const events = this.events
  queueMicrotask(() => {
    if (events !== undefined && this.events === events) events.restart()
  })
  return
}
```

对应测试 `tests/assistant-stream.client.spec.ts:149` `rebaselines duplicate durable settlements or starts`、`:173` `rebaselines known attempts on chunk or terminal index mismatch`。

装配层还有对称的**revision 连续性**兜底（`assembly.ts:102-107`）：重复 revision 丢弃；`revision !== prev + 1` 或 `change.kind === 'replace'` 则降级为整窗替换（不是丢弃、也不是重放 delta）。乱序则有硬约束（`assembler.ts:522-528`）：`previous.event.seq >= input.event.seq` → `received non-appended Match`；同 seq 重复在归并时直接抛错（`assembler.ts:113` `received duplicate Match`），append 入口另有幂等短路（`assembler.ts:221-223`）。

### 2.5 渲染节流：三通道 + 三帧 rAF + 懒重建

`Notifier` 三个通道（`notifier.ts:30-55`）：结构变化走 microtask（`markDirty`）；可见流式走 `requestAnimationFrame`（`markFrameDirty`，注释：*publish cumulative state at most once per frame*）；受控输入走同步 `notifyNow`，注释解释理由——*controlled-input writes must notify in the same tick as onChange, or React rolls the DOM back to the stale value and the caret jumps to the end*。

纪律条款（`packages/client/AGENTS.md`）：

> **Notifier publication discipline**: `notifyNow` is only the direct echo of a user gesture; structural updates use microtask-batched `markDirty`, while visible streaming chunks use cumulative `markFrameDirty`.

"cumulative" 是关键：每帧发布**累积快照**而非本帧增量，因此掉帧不丢内容、只少一次刷新。装配层再叠一层"三帧后发布"（`assembly.ts:130-147`，注释：*Cross three paint opportunities before publishing high-frequency stream updates*），节奏由 Definition 自声明（`ui-conversation/src/client/contract/conversation.ts:178-179`）；chat assistant 规则是"usage/finish 不发布，其余 delta 走 animation-frame"（`ui-chat/.../conversation-nodes/assistant.ts:321-326`）。

懒重建（`notifier.ts:87-96`）：`if (this.listeners.size === 0) return // lazy: dirty (if still set) rebuilds on next getSnapshot`——后台会话在流式期间零快照构建成本。`client/store` 侧有同款 `rafBatch` 合并，且默认 `flush:'sync'`、`'raf'` 需显式选择（`packages/client/store/src/index.ts:71-104`）。

### 2.6 乐观回显、引用稳定与"承认窗口并掩盖它"

```ts
// packages/api/session-controller/src/client/sessions/session.ts:747-752（注释原文）
/**
 * Latch one observed settlement and remove the echo an animation frame
 * later. The delay keeps the echo in the snapshot until the frame in which
 * the durable node (whose assembly frame was registered first) is
 * renderable; the render-time rpcId dedupe hides the one-frame overlap.
 */
```

即**承认会有一帧重叠**，并用渲染期 `rpcId` 去重掩盖（`ui-chat/src/client/chat/ChatView.tsx:288-297`）。这是成熟取舍：与其把分布式时序做成不可能失败，不如承认窗口存在并让窗口不可见。

引用稳定被当硬要求：列表行 `entryCache` 做值相等复用，注释解释"wire refresh 每次铸全新 summary 对象，若不做值级身份恢复，每次刷新都会让所有 memo 失配"（`manager.ts:139-143`）；chat 快照发布带同引用短路（`chat-snapshot-builder.ts:59-64`：`if (this.published === next) return`）。顺序保留式基线合并（`ordered-baseline.ts:1-9` 注释：*identity-preserving merge … inserted relative to the nearest following known identity*）则避免基线刷新引起列表跳动。

### 2.7 线边界校验：拒绝未知字段

`session-wire-event.ts:20-40` 对入站事件逐键白名单（`type/seq/time/data/ignorable/surfaceOp/sourceEventSeqs`），其余一律 `throw new Error('… has unexpected field …')`；`seq` 必须为非负安全整数且 `!Object.is(seq, -0)`，`ignorable` 只允许字面 `true`。三个可迁移点：**未知字段直接报错**（而非忽略）、显式拒绝 `-0`、布尔白名单只认字面 `true`。

---

## 3. (A) 断线重连与会话恢复

### 3.1 物理恢复与逻辑恢复分离

`docs/subsystems/web-client.md:74`：

> Physical and logical recovery are separate. Gateway mux restores the physical WebSocket; each `RemoteStream` reopens its own logical source when the Connection publishes a usable generation. A carrier failure is retryable, while a business error, malformed opening item, or protocol violation is terminal for the owning logical stream.

### 3.2 三类数据三种恢复语义

`docs/subsystems/web-client.md:78-80`：durable 会话日志按游标校验并在每代次由开快照替换窗口，`page()` 供历史与缺口修复；控制面与 Workspace 流断线期间保留最后值、重连后原子替换；**普通转发通知不重放**——*Stateful domains need a baseline, cursor, or explicit query.* 这条约束很重要：不是所有东西都值得恢复，防止制造无意义的补发逻辑。

### 3.3 连接代次广播：`connection/reset`

```ts
// packages/client/connection/src/client/index.ts:18-25
interface Events {
  /**
   * A connection generation was established. Wire-derived caches must
   * repull; long-lived streams own their own resume and baseline lifecycle.
   * @mode emit
   */
  'connection/reset'(): void
}
```

发布点在 `client/index.ts:272-277`，首个连接也发。仓内约 15 个客户端包订阅它重取线派生缓存（`api/session-controller/src/client/index.ts:119`、`ui-settings/src/client/index.ts:63`、`ui-skill/src/client/index.ts:212` 等）。价值：**"哪些缓存该失效"的决策留给缓存所有者**，连接层只广播"现在该重取了"。

### 3.4 会话冷启动与恢复：`openGeneration` 守卫

`Session.openState` 走 `cold → loading → open | error`（`sessions/session.ts:605-633`），用"世代计数器 + 引用相等"丢弃迟到结果：

```ts
// packages/api/session-controller/src/client/sessions/session.ts:611-614
publish: (change) => {
  if (generation !== this.openGeneration || this.events !== events) return
  this.acceptEventChange(change)
},
```

`openGeneration` 在 `dispose()` 时 `++`（`:597`）。对应测试（`packages/api/session-controller/tests/session.client.spec.ts`）：

```
:66  is idempotent: concurrent opens share one follow, reopening when open is a no-op
:83  lands exhausted carrier retries in openState=error as gateway/internal
:104 stitches live frames landing right behind the opening snapshot, dropping the page overlap
:131 drops replayed frames at or below the window tail
:148 repairs a seq gap by repulling the tail page instead of appending a hole
:725 doOpen transport throw of a stale generation is swallowed (generation guard in catch)
:737 drops a stale doOpen whose history resolved successfully after resync superseded it
```

`:148` 几乎就是这套机制的一句话总结：**"补一页，而不是留一个洞"**。

### 3.5 拉取/推送竞态：higher-seq-wins

推送帧与拉取响应到达顺序不定，规则是**高 seq 者赢**，并在飞行中的 list 响应之上重放 mutation（`manager.ts:627-634`：*Apply immediately and retain for replay when a list response is in flight*）：

```ts
// packages/api/session-controller/src/client/sessions/projection-store.ts:137-138
const row = this.rows.get(key)
if (row !== undefined && seq <= row.seq) return // higher seq wins; replays and stale frames drop
```

对应测试：`manager.client.spec.ts:67` `replays incremental frames over hydration and never batch-reorders established ids`、`:177` `drops a projection row beyond the subscription baseline before accepting its durable replay`、`:439` `replays status frames over an older in-flight catalog response`、`:560` `keeps removal invalidation across a stale success and failed trailing pull`；`session.client.spec.ts:566` `settles the title projection cell from the unary response (higher-seq-wins vs the push frame)`。

### 3.6 浏览器级重连验证（注入时钟）

`apps/web/tests/lifecycle-chrome.e2e.ts:401-524` 用 `routeWebSocket` 逐个接管 socket，配合 `clock.install()` 精确推进时间。离线时断言"绝不重试"：

```ts
// apps/web/tests/lifecycle-chrome.e2e.ts:419-426
await recoveryPage.context().setOffline(true)
const offline = recoveryPage.getByRole('button', { name: 'Disconnected, reconnect now', exact: true })
await offline.waitFor({ timeout: 2_000 })
await recoveryPage.clock.fastForward(60_000)
expect(sockets).toHaveLength(1)
```

上线后逐次推进 10s 并 kill socket，断言 socket 数与退避窗口严格匹配（`:450-457`，含 `if (count === 2) { fastForward(1_000); expect(sockets).toHaveLength(count) }` 即"退避生效：1s 内不应有新连接"）。最终断言告警条数**精确为 11**：

```ts
// apps/web/tests/lifecycle-chrome.e2e.ts:520-522
expect(recoveryTripwire.pageErrors).toEqual([])
expect(recoveryTripwire.warnings.filter(warning => /connection lost, retry #/i.test(warning)))
  .toHaveLength(11)
```

"既不许多也不许少"正是防重连抖动（reconnect churn）的关键。同类"无多余重连"断言还有 `apps/web/tests/replay-round-trip.e2e.ts:228`、`cordis-tool-round.e2e.ts:214`、`ptc-round.e2e.ts:154`。

---

## 4. (A) UI 状态是否单一数据源？

**不是"一个 store"，而是"权威在 Host、客户端各有身份稳定的镜像、并用明确规则解决竞态"。** 这是显式声明的：

`docs/subsystems/web-client.md:11`（Host 层）：*Own authoritative state, persistence, mutation ordering, access policy, and stream production.*

`docs/subsystems/web-client.md:52`（客户端不是第二真相）：

> This pairing is not a second source of business truth. Host controllers decide durable state and mutation outcomes; Client models maintain the latest usable local projection, preserve object identity where useful to rendering, and encode how delayed responses and replacement baselines merge.

`docs/subsystems/web-client.md:82` 明确**否认**常见架构模式：

> There is no monolithic Client `Runtime`, `HostFrame`, `events.mux`, `events.host`, or universal `resync()` API. The Connection exposes generation state, Gateway owns logical stream supervision, and each Client model defines replacement or resume semantics appropriate to its data.

代码层三条硬约束：① **列表数据不进 store**（`manager.ts:1-3`：`List data never enters zustand`）；② **连接代次/重试不进 store**（`connection.ts:72-79`）；③ **store 只装视图/交互态**（`packages/client/AGENTS.md`：*Business data lives in the object layer, never a store. Entry-declared stores carry shared viewing/interaction state (selection, drafts, panel widths); sessions, frames, and connections stay in the object layer.*）。

组件侧只有一个**读**通道：全部经框架 hook → `useSyncExternalStoreWithSelector`（`packages/client/ui-renderer/src/client/bind.ts:21-27`），业务组件禁止自建订阅（`packages/client/AGENTS.md`：*Business components contain no subscription machinery*）；store 对组件只暴露 `useStore` + `actions`，没有 instance/set/update（`packages/client/store/src/contract.ts:130-137`）。

同时存在**并行的多个真相宿主**：`SessionEventWindow`（`contract/events.ts:108-117`）、`ProjectionValueStore` 的 per-key 行、`SessionQueueMirror` 的瞬态队列、以及被明确定义为 *admitted outside durable cursor algebra* 的 transient assistant 行（`contract/events.ts:34-35`）。

结论：**DSH 的一致性不是靠"唯一 store"，而是靠"唯一权威 + 显式竞态规则 + 显式重放/修复路径"**。可迁移的不是某个类，而是"每类数据声明自己的恢复速度与修复方式"这条纪律。

---

## 5. (B) 可靠性测试与工程约束

### 5.1 七层测试网

`docs/testing.md:9-17` 是权威描述：

| 层 | 命令 | 覆盖 | 关键约束 |
|---|---|---|---|
| Unit | `pnpm run test` | `tests/**` + `scripts/**/*.spec.ts` | **每个 registry 必须有一个 HMR 安全测试**（dispose 贡献 fiber 并断言清理） |
| Coverage gate | `pnpm run test:coverage` | `packages/*/*/src` | **per-file 100%**；"An uncovered line is often dead code the gate flags for deletion" |
| Real-API e2e | `pnpm run test:e2e` | 真 provider API | 无 key 自跳过；覆盖文件写入 prompt、多轮、工具调用、**mid-stream cancellation** |
| Expected | `pnpm run test:expected` | 组装后 CLI/进程期望 | 无 key；驱动为 `*.expected.e2e.ts` |
| Snapshot | `pnpm run test:snapshot` | 录制会话回放 | 见 §5.3 |
| Web browser | `pnpm run test:web` | Chromium + `snapshots/web/` | CI 强制 `DSH_SNAPSHOT=replay`（只读），绝不写期望输出 |
| Bench | `pnpm run test:bench` | `benchmarks/` | Linux PR 必过门禁 `node 24 / benchmarks`；"timed code runs under plain Node, never TSX" |

`docs/testing.md:10` 值得单独引用：*Line coverage is necessary, never sufficient — it proves lines ran, not that the feature works as shipped.*

### 5.2 vitest 分层配置的具体差异

所有配置共享 `vitest.shared.ts`：`standardDecoratorPlugin()`（在 Vite 默认解析器前转译标准装饰器，并把编译器合成的装饰器访问器标成 `/* v8 ignore next */`）与 `vitestExecArgv`（`--no-webstorage`，避免进程级 Web Storage 遮蔽 jsdom storage）。全部指向 `tsconfig.base.json` 的 paths facade，保证测试解析到 `src` 而非构建产物（`docs/testing.md:45`：*stale artifacts there load a second copy of module singletons*）。

**覆盖率阈值**（`vitest.config.ts:352-368`）——注释即政策：

```
// 100% or it doesn't merge (docs/testing.md: excessive tests are welcome).
// Per-file so a well-covered big file can't subsidize a bare one.
thresholds: coveragePartitionMode ? undefined : {
  perFile: true, statements: 100, branches: 100, functions: 100, lines: 100,
},
reporter: coveragePartitionMode ? [] : process.env.CI
  ? ['text', uncoveredLocationsReporter]
  : ['text', 'html', uncoveredLocationsReporter],
```

分区模式下阈值被显式关掉（分区在 `scripts/coverage-partitions.ts`），并自建 `scripts/coverage-uncovered-locations.cjs` reporter 打印未覆盖位置（`vitest.config.ts:14`）。两个 Vitest project 都强制 `pool: 'forks'`，注释给了原因：*Node 24 has aborted in its CJS lexer … from worker threads on macOS, Linux, and Windows. Forked workers avoid that shared thread path.*（`vitest.config.ts:176`、`:191`）。

| 配置 | include | 并发/超时/重试 | 备注 |
|---|---|---|---|
| `vitest.config.ts` | 包内 `tests/**` + `scripts/**` | 双 fork project（`thread-safe` / `process-bound`） | per-file 100%（见上） |
| `vitest.e2e.config.ts` | `packages/*/*/tests/**/*.e2e.ts`、`apps/cli/tests/**/*.e2e.ts` | `testTimeout 120_000`、`hookTimeout 30_000`、`retry: 2`、`DSH_E2E_MAX_WORKERS`（默认 4） | 排除 `*.expected.e2e.ts`；只有此配置 `process.loadEnvFile('.env')`；注释说明 retry 因共享内部 key 撞并发配额 |
| `vitest.snapshot.config.ts` | `snapshots/**/*.snapshot.ts` + corpus | replay 并行、record/refresh 串行；`DSH_SNAPSHOT_MAX_CONCURRENCY`（默认 `min(5, availableParallelism())`） | `replay`/`refresh` **不读 `.env`**，只有 `record` 读；非 ENOENT 的 loadEnv 失败会抛出而非静默 |
| `vitest.web.config.ts` | `apps/web/tests/**` | — | 需先构建前端 dist（`test:web` 先构建以支持插件 CSS） |

`vitest.e2e.config.ts:58` 注释解释了为什么 `apps/web/tests/*.e2e.ts` 被排除：它们需要构建后的 dist，归 `test:web`。

### 5.3 快照与夹具：怎么防"稳定性回归"

`docs/testing.md:14` 定义命名与选代：父文件名 `session[.vN].jsonl`、子角色 `session.<ordinal>[.vN].jsonl`、v0 省略 `.v0`、正版本小写 `.vN`，且**文件名必须与 header 一致**。关键机制：

1. **版本化世代 + 永不改写**（`docs/architecture.md:119`）：`committed generation paths are never renamed, replaced, or deleted`。旧夹具永远可回放，回归测试不因格式演进集体失效。
2. **夹具只保留语义、不保留时序包装**（`docs/testing.md:17`）：*Session fixtures retain headers and payloads but omit body sequence/time envelopes; replay synthesizes them.* 时间/序号不污染 diff——**只在语义变化时红**（根 `AGENTS.md`：*fix fixtures, not normalizers*）。
3. **record / replay / refresh 三态**（`apps/web/tests/scaffold.ts:113`）：`export type WebSnapshotMode = 'replay' | 'record' | 'refresh'`。默认 `replay` 无 key；`record` 打真 API 并更新夹具与期望；`refresh` 重放已提交脚本只更新当前期望（`vitest.snapshot.config.ts:20-23`）。
4. **改写型场景额外比对工作区**（`docs/testing.md:14`）：*A mutating scenario independently compares the complete workspace.expected/ tree, which record and refresh never rewrite.* 例：`snapshots/acp/cancel-tool-calls/workspace.expected/started.txt`。
5. **CI 只读重放 + 每处 diff 都人看**（`docs/testing.md:15`）：*CI forces read-only DSH_SNAPSHOT=replay, never writing expected outputs; record/refresh stay local and every diff is reviewed.*
6. **文件名/清单本身有门禁**：`.github/workflows/expected-filenames.yml`；夹具清单断言 `apps/web/tests/scaffold.ts:1539` `assertFixtureInventory(dir, expected)`。
7. **golden 比较与失败取证**：`apps/web/tests/scaffold.ts:1521` `compareOrRefreshGolden(goldenPath, actual, mode)`；失败时 `saveFailureShot` 落截图（`apps/web/tests/support.ts:177`）。

### 5.4 "验证世界，不验证自述"

`docs/testing.md:35` 是最值得整段抄给任何 agent 项目的一句：

> An e2e assertion re-runs the command or re-reads the file externally; a keyword probe on the agent's own output lets a cheating agent pass. Assert untouched files are byte-identical. e2e tests own their resources: create it in the test, dispose in `afterEach` (even on failure/retry/timeout); shared fixtures live in a plain `tests/harness.ts`, never another `*.e2e.ts`.

配套三条（`docs/testing.md:37-41`）：产品可见插件必须有**非单测的真组装测试**（boot test-only `cordis.yml` 走 Loader 与 app/process，只 mock 外部服务，断言模型可见请求/日志、持久状态或用户可见输出）；"A guard only guards if the regression fails it"——须**引入回归→看红→还原**证明守卫有效；"real entry path" 指**已发布产物**（`bin` 跑构建后 `lib/bin.js`，暴露 tsx 会掩盖的 settle 竞态、模块解析、被吞掉的加载失败）。

### 5.5 并发执行模型与"孤岛通过"判定

`docs/testing.md:21`：

> Only the process is isolated: ports, predictable paths, external namespaces, and inherited children are not. Own each acquired resource through its teardown, and **read a spec that passes only when it runs alone as a defect in the spec rather than an unstable runner.**

`packages/AGENTS.md` 同款条款。立场很硬：**"单独跑才绿"是 spec 的缺陷，不是 runner 的锅**。

### 5.6 CI 门禁（`.github/workflows/ci.yml`）

顶层 `concurrency` + `cancel-in-progress: true`（`:17-19`）。主要 job：

| job | 行 | 内容 |
|---|---|---|
| `node 24 / static` | `:50` | 静态门禁（lint / typecheck / doc-sync 等） |
| `node 24 / coverage` | `:117` | 穷尽覆盖率（per-file 100%） |
| `node 24 / benchmarks` | `:196` | 性能基准，`timeout-minutes: 15`，必过 |
| `node 24 / snapshots and artifacts` | `:247` | 兼容性 + 快照 + 产物门禁；装 Playwright Chromium（`:328`）；注释说明 failover 会把快照并发减半（`:258`） |
| 兼容矩阵 | `:355` | node 22.19 / 24.9 / 26，各自 `DSH_GATE_CONCURRENCY: '1'` |
| `python 3.10 / keyless SDK` | `:434` | 完整无 key Python 套件 |
| `python runtime / release-shaped matrix` | `:454` | release 形态矩阵 |
| `windows node 24 / build`、`coverage`(120min)、`native tests`(60min) | `:477`、`:521`、`:598` | Windows 平台门禁 |

最有辨识度的是**汇总裁决 job**（`:709-714`）——`needs` 列出全部 9 个必需 job，然后：

```yaml
- name: Fail if any needed job did not succeed
  if: contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled') || contains(needs.*.result, 'skipped')
  run: |
    echo "::error::Needed job results: ${{ join(needs.*.result, ', ') }}"
    exit 1
```

即 **`skipped` 与 `cancelled` 同样判红**——"静默跳过"不能伪装成通过。这对"自跳过套件"（无 key 的 e2e 自跳过）是关键补丁。

另有 17 个 workflow 覆盖 e2e、`docs-pages`（VitePress 构建兼死链检查）、`expected-filenames`、E2B、provider e2e、发行发布等；`.gitlab-ci.yml`（8883 B）是第二套 CI 定义。一条策略性规定（根 `AGENTS.md`）：*Never default to the full suite or repeat a passing check for commit or push. CI owns exhaustive coverage and the platform matrix.*

### 5.7 本地门禁与静态约束

**`lefthook.yml`（55 行）** 定位写在文件头：*Keep these local checkpoints fast; CI owns the full repository-wide gate matrix.*

- `pre-commit`：i18n 配对校验（`*.i18n.yaml`）、归档 Agent Note 完整性、`run-oxlint.ts --config .oxlintrc.staged.json --fix`（staged 文件，`stage_fixed: true`）、**第三方声明重新生成而非拒绝**（`:24-32`，注释说明"忘了更新 notices 会在很久之后的 test lane 才失败"）、`git diff --cached --check` 空白检查、vendor manifest 守卫。
- `pre-push`：只有 `pnpm run typecheck`。

**`.oxlintrc.json`** 采用"逐条显式声明、不用预设档位"的风格——`categories.correctness: "off"`（`:4-5`）。安全相关条目：

```
:83   "typescript/no-explicit-any": "error",        // 每个刻意的 any 都需要带理由的窄豁免
:87   "typescript/no-floating-promises": "error",
:176  "typescript/switch-exhaustiveness-check": [ ... ]
```

（`:329` 对 fixture 目录有 `no-explicit-any: "off"` 窄豁免——与根 `AGENTS.md` 的 *Use narrow, justified exceptions instead of disabling a rule globally* 一致。）

**`.jscpd.json`**：跨文件克隆检测，`minTokens: 60`、`minLines: 6`、`mode: "mild"`、`exitCode: 1`，忽略 `**/tests/**` 与 `tsdown.config.ts`，支持 `/* jscpd:ignore-start */…end */` 显式豁免。**`scripts/change-scope.ts`** 只报告提交/暂存/未暂存/未跟踪的路径清单（`ChangeScopeReport`），**不裁剪门禁**——即变更范围信息用于选择检查，而非自动少跑。覆盖率豁免写法：不可达的防御分支必须 `/* v8 ignore -- <reason> */` 并给真实理由（`packages/client/AGENTS.md`：*never a bare ignore*）。

### 5.8 Agent 循环 / 超时 / 失败的专项测试

**（1）循环契约回归。** `docs/testing.md:9` 点名 `packages/core/agent-loop/tests/contract-regressions.spec.ts` 为"契约回归的永久测试"范例，要求优先覆盖边界、错误路径、**事件顺序**、**并发竞态**。

**（2）工具超时做成 waterfall 包装器。** 工具自声明预算，插件统一收口：

```ts
// packages/guard/timeout-policy/src/index.ts:57-61（节选）
ctx.on('tools/execute', async (exec, next): Promise<ToolExecutionResult> => {
  const timeoutMs = ctx.tools.get(exec.name, exec.agent)?.timeoutMs
  if (timeoutMs === undefined) return next()
  using d = deadline(exec.signal, timeoutMs, TOOL_TIMEOUT)
```

README 对**能力边界**很诚实：插件只能"请求停止"，不尊重取消的工具仍会拖住调用方。专项测试覆盖真正的难点——**两个取消源竞争**（`packages/guard/timeout-policy/tests/timeout-policy.spec.ts`）：

```
:49  delegates a tool with NO declared budget unchanged and does not touch exec.signal
:72  a budgeted tool receives the DERIVED deadline signal (not the caller signal) during dispatch
:84  restores the caller signal for post-execute after wrapping
:117 replaces a provider-owned abort ERROR result with TOOL_TIMEOUT when the signal was ours
:131 preserves registry ABORTED when the caller aborts first (upstream cancel, not our timeout)
:159 preserves TOOL_TIMEOUT when the deadline wins before a later caller abort
:203 removes its tools/execute listener when the plugin fiber disposes   ← HMR 安全
:221 has no default export and keeps name/inject through unwrapExports  ← 真实加载路径守卫
```

`:131` 与 `:159` 成对出现，专门测"两个取消源"的两种胜负顺序——超时实现里最容易错的地方。

**（3）恢复测试分离 pre/post-chunk 失败。** `docs/testing.md:31`：*Recovery tests separate pre/post-chunk failures by step and prove failed chunks derive no message or tool side effect. Cover exhaustion, cancellation, policy composition, persistence, status, wire counts, transport-closing idle timeouts, and shipping Loader composition.* 即"失败分片不得产生任何消息或工具副作用"，并覆盖**传输关闭的空闲超时**。

**（4）mock 边界纪律。** `docs/testing.md:29`：*Mock only the expensive or non-deterministic boundary (LLM adapter, network, clock); keep everything downstream real.* 范本是 ACP 的 `makeBridgeHarness()`（`packages/acp/acp/tests/harness.ts`）：`MockAdapter` 是唯一 mock，loop、session store、tool registry、JSONL 持久化全部真实；其脚本原语 `textResponse/maxTokensResponse/errorResponse`（`harness.ts:153-174`）让失败与截断可被确定性构造。

### 5.9 防御性模式清单（`docs/defensive-patterns.md`，全文 33 行）

定位（`:5`）：*each pattern below is a class of defect that actually shipped or nearly shipped here*。摘录：

| 行 | 规则 | 典型后果 |
|---|---|---|
| `:7-9` | 正交结果独立上报（`timedOut`/`signal`/`exitCode` 各自成字段） | "a caller reads a cut-short run as a clean success" |
| `:15-17` | 异步状态不是同步状态：`agent.followup()` 无逐条完成语义，`agent/status`/`whenIdle()` **不能**当作某条消息的结果 | 多条排队/steering 共享同一 `running` 区间 |
| `:19-21` | Dispose 必须达到静止而非只发请求（kill → await `done`；先关监听注册表再 kill） | 留孤儿进程 |
| `:23-25` | dispatcher 内包裹回调异常 | 一个坏订阅者饿死后续订阅者 |
| `:27-29` | 不把环境或可预测路径交给不可信输出（清理 `*KEY*`/`*SECRET*`/`*TOKEN*`/`*PASSWORD*`） | 凭证泄漏 |
| `:31-33` | 先 `lstatSync().isSymbolicLink()` 再 `unlinkSync` | 符号链接 / Windows junction 竞态 |

`docs/testing.md:5` 明确它与测试层互补：*Test-tier counterparts (real entry path, world-verification, resource ownership) are in testing.md.*

### 5.10 性能门禁：把"稳定性"变成数值红线

`benchmarks/` 五组用户路径门禁：`active-stream-reconnect`、`agent-continuation`、`conversation-fold`、`long-session-browser`、`session-open`。校准集中且显式（`benchmarks/support/calibration.ts:4-15`）：

```ts
/** Measured wall-time ratio between the x64 CI runner and the arm64 reference machine. */
export const CI_TIME_SCALE = 2
/** Allowed variance above the calibrated expectation. */
export const PERFORMANCE_BUDGET_HEADROOM = 1.25
export function ciTimeBudget(expectedMs: number): number {
  return Math.ceil(expectedMs * CI_TIME_SCALE * PERFORMANCE_BUDGET_HEADROOM)
}
```

与本次主题直接对应的是 `active-stream-reconnect`（`README.md`）：测量"重连携带未完成的 100,000-delta reasoning 前缀"时生产代码 fold 的替换耗时与强制 GC 后保留堆，各自独立中位数预算；*Standard hosted CI uses a 50 ms replacement expectation with the shared 1.25× headroom (63 ms ceiling); the retained-heap budget remains 30 MiB*。最聪明的写法是**把门禁函数本身也测了**：

```ts
// benchmarks/active-stream-reconnect/reconnect.bench.client.ts:15-22（节选）
const recordedMedian = [46.574411, 46.067910, 44.193704].toSorted((a, b) => a - b)[1]!
expect(() => expectReplacementWithinBudget(recordedMedian, ciTimeBudget(16))).toThrow()
expectReplacementWithinBudget(recordedMedian, REPLACE_BUDGET_MS)
expect(REPLACE_BUDGET_MS).toBe(63)
expect(() => expectReplacementWithinBudget(75, REPLACE_BUDGET_MS)).toThrow()
```

用已录制样本证明"预算能通过"，再用伪造大值证明"预算真会失败"（与 `docs/testing.md:40` 的 *introduce the regression, watch red, revert* 同一思路）。真实测量在独立 worker 中进行、取 3 次中位数，并断言"重连后下一帧仍能被接受"（`:41-43` `expect(run.report.nextFrame).toBe('transient')`）。

浏览器侧压力测试 `apps/web/stress-tests/reasoning-chunks.stress.ts` 向真实页面注入 **100,000 个 chunk**（每 16ms 128 个），主线程延迟预算 250ms（`:10-14`），验证的正是 §2.5 那套节流在极端负载下是否成立。这类 `*.stress.ts` 与包内 `*.perf.ts` 属诊断用途，不进 PR CI 门禁。

---

## 6. 迁移到一个 Python + Gradio 单体 Agent 的做法（8 条）

前提：单体 Python 进程（FastAPI/Flask 内核 + Gradio Blocks 前端），单机部署，会话持久化到 JSONL/SQLite，模型流式输出经 generator 产出。

### ① 把"事件序号 + 游标区间"做成第一等公民（可行，最优先）

核心可迁移结论：**每条可增量应用的数据都要自带 `[first, last]` 语义的游标**（`journal-stream.ts:305-336`、`:565-572`）。在 Python 里就是给每个会话事件一个单调 `seq`，并让"已应用到哪个 seq"成为服务端与前端都持有的显式状态。应用新事件时三条判断：

- `seq <= applied` → 丢弃（幂等，消灭重复渲染）
- `seq` 跨越已应用边界 → 报协议错误（不该发生，宁可 loud fail）
- `seq > applied + 1` → 触发缺口修复（重读权威页，而不是留洞）

三条判断共十几行代码，能消灭绝大多数"重复渲染/少一条/顺序错乱"缺陷。**Gradio 落地**：`gr.Chatbot` 拿的是消息列表、无游标概念，游标必须维护在服务端会话状态（`gr.State` 或自建 store）里，前端只拿投影后的列表。游标层必须自建，但完全可行。

### ② 连接代次 + "先挂监听后报就绪"的握手（可行）

`connection.ts:58-70`、`:216-220`。每个 WebSocket/SSE 连接分配单调 `generation_id`；服务端**先把订阅注册进广播列表，再返回 `ready` 帧**；任何来自旧 generation 的迟到回调直接丢弃（`if gen != self.generation: return`）。配合 ①，能消除"重连后内容回退一屏"。另照搬一条纪律：**代次建立时先撤回旧代次再宣布 connecting**，保证 UI 不在中间态读到上一代的 host 事实。

### ③ 两类流分开，各自声明恢复语义（可行）

`snapshot-stream.ts:67-93` 与 `journal-stream.ts` 是两种不同答案，DSH 没有统一。单体里同样应分开：

- **控制面/状态面**（会话列表、运行状态、模型选择）→ 快照流：每代次发完整 baseline，之后发 delta；**断线期间保留旧值，重连后原子替换**（`web-client.md:79`）
- **对话正文** → 日志流：baseline + seq 追加 + 缺口重读
- **纯通知（toast 类）** → 明确不做恢复（`web-client.md:80`）

把这三种语义写成三个基类或三个 generator 约定，比追求"一套通用 resync"省事得多——DSH 明确否认存在通用 `resync()`（`web-client.md:82`）。

### ④ 重连退避 / 离线暂停 / 状态去重 / 回调隔离（可行，与框架无关）

四条可直接照搬：`cap/2 + rand*cap/2` 退避（`connection.ts:144-147`）、离线时不重试并等 `online` 事件（`connection.ts:167-176`、`client/index.ts:169-182`）、相同状态不重复通知（`connection.ts:271-275`）、业务回调抛错只记日志绝不影响重连循环（`connection.ts:278-284`）。后两条尤其重要：前者防 UI 反复重绘，后者防业务 bug 放大成连接故障。

### ⑤ 流式渲染：累积快照 + 时间窗合并（部分可行，机制需替换）

DSH 用"三通道（microtask / rAF / 同步）+ 累积快照 + 三帧 rAF"。Gradio 每次 `yield` 都触发组件更新、**没有 `requestAnimationFrame` 的对应物**，故"每帧一次"必须替换为**时间窗合并**：在服务端 generator 里收集 30-60ms（或每 N 字节）后 yield 一次**累积快照**，而不是每 token 一次。要保留的关键不变式是**发布累积值而非增量**，这样掉帧只少一次刷新、不丢内容（`notifier.ts:38-43` 的 *publish cumulative state*）。用户输入回显必须与提交同一轮返回，避免被旧值覆盖（对应 `notifyNow`，`notifier.ts:46-49` 解释了同步 flush 的理由）。

### ⑥ 数据去重与渲染去重的责任重新分配（需替换实现）

DSH 把"乐观 echo 的一帧重叠"用渲染期 `rpcId` 去重掩盖（`session.ts:747-752`）。Gradio 的 `Chatbot` 不接受渲染期钩子，无法在渲染时过滤重复行。**替代方案**：把去重提前到数据结构——**服务端保证同一时刻只有一个权威消息列表**，乐观回显由服务端立即写入（pending 状态），持久化到达后就地更新同一条记录，前端永远不合并两个列表。同理"引用稳定"纪律（`manager.ts:139-143`、`chat-snapshot-builder.ts:59-64`）在 Gradio 中无从表达（组件更新是全量 diff），改为**产物级缓存 + 内容哈希变更检测**：只在渲染结构真正变化时返回新对象。

### ⑦ 客户端那份 580 行游标状态机整体不要移植（不可行，用服务端幂等接口替代）

`RemoteJournalStream` 的复杂度几乎全部来自**浏览器端的重连不确定性**：页读取与流帧竞态、代次被超越、部分重叠拼接（`journal-stream.ts:397-445`）。Gradio 是"一次事件调用 → 一次返回"，没有客户端可编程流控，无法在浏览器侧实现"读页期间暂存流条目再拼接"。**替代方案**：把一致性责任整体搬到服务端——前端只持有 `(session_id, applied_seq)`，用一条**幂等的 `GET /messages?after_seq=N`** 拉取，所有竞态在服务端用单线程/锁消解。这实际上是简化：**别在客户端做一致性，让服务端只发可幂等重取的东西**。相应地，整条 WebSocket mux 多路复用层（`stream-client.ts:34-120`）也不需要——单会话一条 SSE/WebSocket 即可，省下的复杂度应投入到 ①。

### ⑧ 不要搬数值，要搬方法与验收清单（需自行标定）

`active-stream-reconnect` 的 50ms/63ms 是"Node 单线程 fold 10 万 delta"的实测标定；Python 解释器开销与 Gradio 组件 diff 成本量级不同，直接套用只会得到无意义的红绿。**保留方法论**：独立进程/worker 取样、取中位数、显式校准系数（`CI_TIME_SCALE` 与 `HEADROOM`，`calibration.ts:4-15`）、像 `reconnect.bench.client.ts:15-22` 那样**用伪造值证明门禁会失败**——但数值必须自己跑 10 次取中位数后重新标定。

更值得整段带走的还有**非代码资产**：`docs/subsystems/conversation.md:245-256` 那份验收条件清单（尤其 `:251` *Initial history followed by live append produces the same result as replaying the combined window*），以及把测试名写成不变量句子的习惯（`journal-stream.client.spec.ts:412` *deduplicates complete ranged entries and rejects partial live overlap*）。在 Python 项目里为每个流式场景写 5-8 条这样的句子、每条对应一个测试，比任何框架选择都更能防住稳定性回归。

---

## 7. 一页总结

**协议层**：三条并行推送路径（一元 RPC / 事件转发流 / 数据流）共用 Connection 载体但协议独立；数据流分快照流与日志流，恢复语义各写各的；序号体系分 `generation`、`seq`、`cursor`、`revision`、`rpcId`、`eventId` 六种，各管一段。对外协议（ACP）只保证"从已提交事件派生"，幂等与序号责任留在自己客户端。

**一致性层**：核心不是"唯一 store"，而是三条可执行规则——① 游标幂等（重复即丢弃）；② 缺口必补（补一页而不是留洞）；③ 对不齐就 rebaseline（宁可贵一次整体重取，也不显示错乱）。外层再加渲染期节流（三通道 + 累积快照 + 三帧 rAF）与懒重建，以及"引用稳定"作为显式契约。

**测试层**：七层测试网，覆盖率 per-file 100%，录制会话快照作为"组装后行为"的回归基线，性能预算作为数值红线，PR 汇总裁决把 `skipped`/`cancelled` 也判红，外加一份"真实发生过的缺陷类别"清单。最有辨识度的两条原则是"**验证世界，不验证自述**"（`testing.md:35`）与"**单独跑才绿 = spec 有缺陷**"（`testing.md:21`）。

**对 Python + Gradio 单体的最佳移植路径**：把一致性责任从客户端搬到服务端——服务端维护 `(session_id, applied_seq)`，提供幂等的 `after_seq` 拉取；前端只做渲染与提交。DSH 客户端那 580 行游标状态机可以整体删掉，但**它想解决的三个问题一个都不能少：幂等、补缺、对不齐就重取。**
