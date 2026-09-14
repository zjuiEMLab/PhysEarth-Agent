# DSH 源码研究：长会话的上下文管理与状态持久化

研究对象：`/Users/heihe/Desktop/Competitions/GeoAI_challenge/tmp/deepseek-harness`（TypeScript + pnpm monorepo，v0.1.5，Session format v3）。
研究范围：上下文预算/压缩、会话持久化、崩溃恢复。**只读研究，未修改该仓库任何文件。**

---

## 机制速查表

| 机制 | 作用 | 关键源码位置 | 解决什么问题 |
|---|---|---|---|
| `TokenMeter.measure()` | 单一重放式 token 计量：产出 `logRevision / baseline / surfaceDeltaTokens / totalTokens / surfaceTokens / nodes` | `packages/llm/token-meter/src/index.ts:145-190` | 预算必须只有一个权威口径；UI、压缩、裁剪都读同一份测量 |
| 固定密度启发式估值 | `CHARS_PER_TOKEN=4`、`BLOCK_OVERHEAD=4`、`ROLE_OVERHEAD=4` | `packages/llm/token-meter/src/estimate.ts:13-19, 37-61, 86-89` | 无 tokenizer 也要能廉价、可复现地定价 |
| Provider usage 锚点复用 | 最新一次成功调用的 canonical 信封匹配且 usage ≥ 估值时，用真实 usage 做基线，只对表面增量做有符号修正 | `packages/llm/token-meter/src/index.ts:51-59, 155-180` | 启发式漂移；长会话里估值与真值差距累积 |
| plan/commit 表面折叠 | 先只读校验并算出 `{tokens, deltaTokens, node, target}`，再原地提交 | `packages/llm/token-meter/src/surface-fold.ts:112-147` | 畸形事件不能半应用；重放必须幂等 |
| `agent/pre-step` 压力压缩 | 每步在请求派生之前测压，超阈值则压缩 | `packages/compaction/compaction-basic/src/index.ts:148-166, 259-333` | 主动防溢出，而不是等 provider 报错 |
| `agent/request-error` 溢出恢复 | provider 报 `CONTEXT_WINDOW_EXCEEDED` 时裁剪/压缩后返回 `{kind:'retry'}` | `packages/compaction/compaction-basic/src/index.ts:180-224` | provider 确证的溢出是可恢复错误，不是终局失败 |
| 保留尾部 + 工具配对边界 | 从尾部累加 priced tokens 直到 `retainTokens`，再回退到 tool-call/result 成对边界 | `packages/compaction/compaction-basic/src/region.ts:117-155` | 裁剪后 transcript 必须仍是 provider 合法序列 |
| 压缩区间 = 一次日志事务 | `compaction/start` 是持久锁，`compaction/summary` 记账，`user/message{surfaceOp:replace}` 是唯一表面变更，`compaction/end` 释放 | `packages/compaction/compaction-basic/src/region.ts:173-275, 456-507` | 崩溃中途可检测（孤儿 start），且摘要可追溯 |
| shadow-price 协议 | 计量事件紧邻替换事件，声明被遮蔽区间的启发式价格 | `docs/persistence-catalog.md:304-328`、`compaction-tool-result-pruner/src/index.ts:163-174` | 纯消费者 O(1) 减法理解表面总量，不需保存每节点价格 |
| 压缩失败兜底 | 摘要不比原文小 / 表面变了 / 截断 / 空 / 含图 → 拒绝；免模型 prune 先行 | `region.ts:403-407, 416-453`、`summarizer.ts:167-169, 195-211` | 压缩只能变小、不能污染历史、失败不能吞掉原错误 |
| spill 句柄 | 超大文本落盘，只把 `locator + retrievalHint + head/tail 预览` 交给模型 | `packages/spill/spill-policy/src/index.ts:125-204`、`spill/spill-local/src/store.ts:108-131` | 大对象永不进上下文，但可被 `read/grep` 按需取回 |
| tool-result 剪枝 | 确定性 head/middle/tail 截断 `tool/result` 的 content，其余字段 deep-equal | `compaction-tool-result-pruner/src/index.ts:83-122, 136-185` | 免模型的确定性降载，先于摘要压缩 |
| 事件日志 + 版本化文件 | append-only `SessionEvent`（seq 连续、JSON 可序列化），JSONL 按代存放 | `packages/core/session/src/types.ts:60-88`、`session-persistence-jsonl/src/index.ts:1194-1284` | 唯一真相；格式演进不破坏已提交数据 |
| 句柄单写者 + 内核租约 | `open(id,'write')` 原子占权，POSIX `flock(session.lock)`，Windows 命名信号量 | `packages/session/session-persistence-jsonl/src/lease.ts:1-52` | 并发 resume/repair 不会互相撕裂日志 |
| 写窗口 + flush 屏障 | `session/event` 同步通知进 200ms 批量窗口；`session/flush` 是唯一持久化屏障 | `session-persistence-jsonl/src/storage.ts:36, 274-316`、`core/session/src/index.ts:1133-1157` | 生产者不被 IO 阻塞，但语义边界可强制落盘 |
| 崩溃修复 | 物理层丢撕裂尾；语义层合成 `tool/result(isError) + step/end + turn/end{interrupted}` | `session-persistence-jsonl/src/storage.ts:319-343`、`core/session/src/repair.ts:29-135` | 不截断已完成的巨大 turn，同时让 transcript 合法 |
| 投影缓存身份校验 | 派生状态记录绑定 `(sessionId, createdAt, format, inheritedCut)` 身份 + 水位 + 行版本 | `session/session-projection-cache/src/spec.ts:34-57, 100` | 缓存滞后可以，错位不行；绝不从无关日志播种 |

---

## 一、上下文/Token 预算如何计算与强制

DSH 没有"一个总预算"，而是**三层预算 + 一个唯一计量服务**。预算的强制点分散在事件钩子上，计量集中在 `ctx.tokenMeter`。

### 1.1 计量层：`ctx.tokenMeter`（唯一口径）

`TokenMeter` 是 `Service`，按 `WeakMap<Session, ReplayState>` 持有每会话增量重放状态，从 seq 0 一直追到 `session.seq`：

```ts
// packages/llm/token-meter/src/index.ts:217-239
private _sync(session: Session): ReplayState {
  let state = this.states.get(session)
  if (state === undefined) { state = { consumedEvents: SessionLogOffset(0), header: undefined,
    surface: [], stepStart: undefined, anchor: undefined }; this.states.set(session, state) }
  while (state.consumedEvents < session.seq) {
    const event = session.eventAt(SessionSeq(state.consumedEvents))!
    this._foldEvent(state, event)
    state.consumedEvents = SessionLogOffset(state.consumedEvents + 1)
  }
  return state
}
```

关键设计点：

- **`_foldEvent` 先跑完所有可能抛错的步骤（surface plan + anchor 校验），再改状态**（`index.ts:241-316`）。注释写明理由：畸形事件必须"在每次重试时同样保持未读"，不能半应用。
- `SessionSeq` 连续性、`step/start`↔`step/end`、`assistant/message` 必须有匹配 `step/start`——三条重放不变量在 `_foldEvent` 里直接 `throw`（`index.ts:255-285`）。
- 测量结果是 `structuredClone` + `deepFreeze` 的**脱离快照**（`index.ts:182-189`），不会随底层 fold 前进而变。

定价口径（`estimate.ts`）：

```ts
const CHARS_PER_TOKEN = 4     // estimate.ts:13
const BLOCK_OVERHEAD = 4      // estimate.ts:16
export const ROLE_OVERHEAD = 4 // estimate.ts:19
```

text/reasoning 按 `ceil(len/4)+4`；`tool-call` 按 name+arguments；`tool-result` 递归；**未知/扩展块退化为 `JSON.stringify` 的结构价格**（`estimate.ts:52-58`）——这是合并可扩展类型下的保守兜底。

### 1.2 基线选择：usage 锚点 vs 纯估值

```ts
// packages/llm/token-meter/src/index.ts:155-180（节选）
if (anchor !== undefined && optionalHeaderEquals(anchor.header, header)) {
  const anchorSurfaceTokens = priceSurface(anchor.nodes, pricing, fileText).surfaceTokens + anchor.assistantTokens
  const estimatedAnchorTokens = estimateToolsTokens(header) + anchorSurfaceTokens
  const usage = anchor.usage
  baseline = usage !== undefined && usageTokens(usage) >= estimatedAnchorTokens
    ? { kind: 'usage', tokens: usageTokens(usage), usage }
    : { kind: 'estimated', tokens: estimatedAnchorTokens }
  surfaceDeltaTokens = surface.surfaceTokens - anchorSurfaceTokens
} else { baseline = { kind:'estimated', tokens: estimateToolsTokens(header) + surface.surfaceTokens }; surfaceDeltaTokens = 0 }
```

语义很关键：**只有 provider 报告的 usage 不小于同信封下的完整启发式价格时才敢用它当基线**（保守方向），否则退回估值。`surfaceDeltaTokens` 是有符号的，同时保留增长和收缩，因为两侧用同一路
由定价（`docs/subsystems/token-meter.md:29`）。

`totalTokens = max(0, baseline.tokens + surfaceDeltaTokens)`，`surfaceTokens` 是表面自身的路由定价总和，等于各节点价格之和。

### 1.3 三层预算

**第一层：整窗（provider 模型容量）**

容量不是猜的，是从路由适配器解析出来的：

```ts
// packages/compaction/compaction-basic/src/index.ts:294-305
const context = (await this.ctx.llm.resolveModelInfo(target.provider, target.model, signal)).context
assertNoActiveCompaction(agent.session, 'automatic pressure compaction')
if (context === undefined) {
  throw new TargetPressureConfigError(targetKey,
    `compaction-basic: no context capacity for ${targetKey}; configure contextWindow on that adapter model`)
}
const spec = resolveCompactSpec(policy, context.contextWindow)
if (measurement.totalTokens < spec.thresholdTokens) return null
```

容量缺失是**加载/策略期硬错**（`TargetPressureConfigError`），不是静默跳过。

```ts
// packages/compaction/compaction-basic/src/config.ts:144-154
const thresholdTokens = Math.floor(contextWindow * policy.thresholdRatio)   // 默认 0.8
const retainTokens = policy.retainTokens === undefined
  ? Math.floor(contextWindow * policy.retainRatio)                          // 默认 0.16
  : policy.retainTokens
if (retainTokens >= thresholdTokens) throw new TargetPressureConfigError(...)
```

默认值：`thresholdRatio = 0.8`（`config.ts:20`）、`retainRatio = 0.16`（`config.ts:23`）、`maxTokens = 8192`、`compactionRetries = 1`、`maxOverflowRetries = 1`（`config.ts:91-93`）。按 `provider/model` 精确路由可覆盖（`modelPolicies`，`config.ts:105-125`），且**加载时就校验 `retainRatio < thresholdRatio`**（`config.ts:180-191`），避免容量相关的矛盾拖到运行时。

**第二层：单次请求（pressure）**

触发点是 `agent/pre-step` 瀑布，在请求派生之前：

```ts
// packages/compaction/compaction-basic/src/index.ts:148-166（节选）
ctx.on('agent/pre-step', async ({ agent, signal }, next): Promise<PreStepDecision> => {
  if (!signal.aborted) {
    try {
      const result = await this.compactIfNeeded(agent, 'pressure', signal)
      if (result !== null) logResult(result, 'step pressure')
    } catch (error: unknown) {
      // 配置类错误按 target 只警告一次
      ctx.logger.warn(`step compaction failed: ${message}; continuing the turn`)
    }
  }
  return next()
})
```

注意"**自动压缩失败不打断 turn**"——只 `warn` 并继续（`index.ts:156-163`）。

溢出路径走 provider 确证：

```ts
// packages/compaction/compaction-basic/src/index.ts:180-224（节选）
ctx.on('agent/request-error', async ({ agent, failure, signal }, next) => {
  if (failure.code !== CONTEXT_WINDOW_EXCEEDED_CODE || signal.aborted) return next()
  const retries = this.overflowRetries.get(agent) ?? 0
  if (retries >= policy.maxOverflowRetries) return next()
  const generation = agent.session.surface.replaceGeneration
  ... if (agent.session.surface.replaceGeneration <= generation) return next()
  if (result !== null) logResult(result, 'context overflow recovery')
  return { kind: 'retry' }
})
```

重试计数是 `WeakMap<Agent, number>`，**成功 `assistant/message` 或回到 idle 时清零**（`index.ts:124, 168-178`）——一次成功的多步 turn 不会把溢出重试额度耗光。

**第三层：单工具输出（bytes / Unicode code points）**

- 进程输出：`maxOutputBytes` 默认 `64_000`，`maxSpillBytes` 默认 `64MiB`（`packages/shell/bash-local/src/index.ts:36-45, 109`）。超内存上限的流溢出到临时文件，并在结果里带 `spillPath`（`index.ts:60-66`）。
- 工具结果落盘：`spill-policy.maxInlineBytes`（下文第三节）。
- 存量工具结果剪枝：`thresholdChars=8192, headChars=4096, tailChars=1024`（`compaction-tool-result-pruner/src/config.ts:10-14`）。
- `read` 工具：`limit` 默认=最大=配置的 `readLimit`，`maxBytes` 截断（`packages/fs/tool-fs/src/read.ts:14-35, 55-60`）。

### 1.4 强制的实质

值得注意：`buildRequest()` 直接把 `session.deriveMessages()` 全量作为 `messages` 发出去，**没有任何请求级裁剪**：

```ts
// packages/core/agent-loop/src/agent.ts:605-616（节选）
const boundaryMessages = session.deriveMessages()
for (const message of boundaryMessages) { if (this.frozenMessages.has(message)) continue
  deepFreeze(message); this.frozenMessages.add(message) }
Object.freeze(boundaryMessages)
const request = markAgentLoopRequest(Object.freeze({ ...header.config, messages: boundaryMessages, ... }))
```

所以 DSH 的预算强制是**"进入表面之前就压住 + 事后测量触发压缩 + provider 拒绝后恢复"**三件事，而不是"发请求前按预算裁剪历史"。这一点对迁移很重要：它保证了 `messages` 与日志表面的**逐节点可重建性**（"Model-visible means logged"，`docs/architecture.md:121`）。

---

## 二、压缩：触发、内容、可追溯性、失败兜底

### 2.1 何时触发（四种入口）

| 入口 | 条件 | 源码 |
|---|---|---|
| `pressure` | 每步 `agent/pre-step`，`totalTokens ≥ thresholdTokens` | `index.ts:148-166, 305` |
| `context-overflow` | provider 返回 `CONTEXT_WINDOW_EXCEEDED`（适配器把上游错误映射到该 code） | `index.ts:180-224`、`llm/llm/src/error.ts:25`、`llm-deepseek/src/adapter.ts:346` |
| `compactNow()` | 人工命令，空闲会话，即使未到阈值也做一次有用压缩 | `index.ts:369-421` |
| `compactRegion(s,e)` | 显式区间 | `compaction/src/index.ts:164-190` |

溢出路径有一条专门的"**绕过阈值与保留尾策略**"逻辑：

```ts
// packages/compaction/compaction-basic/src/index.ts:284-292
if (trigger === 'context-overflow') {
  if (prune !== undefined) { prune.pruneSession(agent.session); measurement = meter.measure(agent.session) }
  const range = selectCompactableRange(agent.session, measurement, 0)   // retainTokens = 0
  if (range === null) return null
  return this.compactRegion(range.start, range.end, agent, signal)
}
```

压力路径则是"**先免模型 prune，再重新测量，不够再摘要**"，且摘要最多重试 `compactionRetries` 次：

```ts
// packages/compaction/compaction-basic/src/index.ts:309-332（节选）
if (prune !== undefined) { prune.pruneSession(agent.session); measurement = meter.measure(agent.session) }
if (measurement.totalTokens < spec.thresholdTokens) return null
let result: CompactionResult | null = null
for (let attempt = 0; attempt <= spec.compactionRetries; attempt += 1) {
  const range = selectCompactableRange(agent.session, measurement, spec.retainTokens)
  if (range === null) { if (result === null) return null; break }
  result = await this.compactRegion(range.start, range.end, agent, signal)
  measurement = meter.measure(agent.session)
  if (measurement.totalTokens < spec.thresholdTokens) return result
}
throw new Error(`compaction still above threshold after ${spec.compactionRetries + 1} compaction attempts ...`)
```

### 2.2 压缩什么：区间怎么选

```ts
// packages/compaction/compaction-basic/src/region.ts:131-154
const firstIdx = systemHead(session, surfaceNodes[0]!) === undefined ? 0 : 1   // 系统提示永不入区间
let accumulated = 0
let keepFromIdx = pricedNodes.length
for (let index = pricedNodes.length - 1; index >= 0; index -= 1) {            // 从尾部累加保留预算
  accumulated += pricedNodes[index]!.tokens
  keepFromIdx = index
  if (accumulated >= retainTokens) break
}
if (keepFromIdx <= firstIdx) return null
while (keepFromIdx > firstIdx) {                                              // 回退到工具配对平衡点
  if (toolPairingBalancedBefore(session, surfaceNodes[keepFromIdx]!)) break
  keepFromIdx -= 1
}
if (keepFromIdx <= firstIdx) return null
return { start: surfaceNodes[firstIdx]!, end: surfaceNodes[keepFromIdx - 1]! }
```

三条硬约束：
1. **系统提示（surface node 0 的 `system/message`）永不被压缩**（`region.ts:131`，由 `surface.ts:398-418` 强制）。
2. **保留尾部按 route 定价累加**，不是按节点数。
3. **不按 turn 切，只保 tool-call/result 成对**——文档明确说"允许一个超大 turn 的早期已闭合步骤被压缩"（`docs/subsystems/compaction.md:86`）。

配对校验（`compaction/src/tool-pairing.ts:112-124`）在选区和显式区间两条路上都用（`region.ts:143-147, 348-354`）。

### 2.3 压缩成什么：一个 7 节结构化检查点

摘要指令**不作为独立 system prompt**，而是**作为重放对话之后的最后一条 user message**：

```ts
// packages/compaction/compaction-basic/src/summarizer.ts:24-30（JSDoc）
/**
 * The summarization directive, delivered as the FINAL user message after the
 * replayed conversation rather than as a distinct summarizer system prompt.
 * Keeping the conversation's own system prompt, tools, and message prefix in
 * front of it makes the auxiliary call a genuine prefix of the last routed
 * request, so the provider's KV cache is reused instead of invalidated.
 */
```

重放前缀的构造（`region.ts:517-548`）：`system/message` 的派生消息 + `requestHeader().tools` + 被遮蔽区间按表面顺序的派生消息；然后 `summarizer.ts:144-150` 追加 `COMPACTION_INSTRUCTION`。

模板固定 7 节：`Primary Request and Intent / Key Technical Concepts / Files and Code / Errors and Fixes / Pending Jobs / Current Work / Next Step / Critical Context`，并要求"空节写 `(none)`，绝不删节"、"保留精确路径/命令/错误串/标识符/数值"、"不要提及发生过压缩"、以及"**若对话里已有 `<compacted-summary>` 块，那是上一版检查点：保留仍为真的事实、丢弃过期的、合并成单一摘要**"（`summarizer.ts:31-66`）。这条让**反复压缩不会逐次退化**。

落地时的包装（`summarizer.ts:186-192`）：

```ts
export function frameSummary(summary: readonly ContentBlock[]): ContentBlock[] {
  return [
    { type: 'text', text: `${CHECKPOINT_PREAMBLE}\n\n${SUMMARY_OPEN_TAG}` },
    ...summary,
    { type: 'text', text: SUMMARY_CLOSE_TAG },
  ]
}
```

`CHECKPOINT_PREAMBLE`（`summarizer.ts:69-70`）明确要求模型"把捕获的上下文当作既有背景，直接继续任务，不要回应这个检查点"。

### 2.4 压缩后如何保持可追溯性

压缩产生了**三类持久记录 + 一种新表面节点**：

```ts
// packages/compaction/compaction-basic/src/region.ts:476-494（节选）
const summaryEvent = session.append('compaction/summary', {
  compactionId: startEvent.data.compactionId,
  summary,
  ...callProvenance,                       // rawOutput + llmStreamCall:true，可重建那次一次性调用
  shadowedRange: { start, end },           // 表面位置跨度，不是数值区间
  shadowedSeqs: [...shadowedSeqs],         // 权威的被遮蔽集合，按表面顺序
  shadowedTokenCount,
  provider, model, ...maxTokens, ...usage,
})
session.append('user/message', checkpointMessage, {
  surfaceOp: { op: 'replace', startSeq: start, endSeq: end },
  sourceEventSeqs: [startEvent.seq, summaryEvent.seq, ...shadowedSeqs],
})
```

要点：
- **`SurfaceEventType` 故意不扩展**：摘要本身不直接成为表面事件，而是搭在一条带 `surfaceOp: replace` 的 `user/message` 上（`docs/subsystems/compaction.md:11`）。这样"只有消息生产事件到达模型"这条不变量不被破坏。
- **`shadowedRange` 是位置跨度不是 seq 区间**：因为此前的一次 replace 会把一个高 seq 的摘要节点放到老区间的位置上，`start` 可能**大于** `end`；权威集合是 `shadowedSeqs`（`compaction/src/types.ts:44-54`）。
- **`sourceEventSeqs` 必须包含每一个被遮蔽节点**，且每个引用必须 `< event.seq`（不得自引用或前向引用），且不得重复——由 `surface.ts:269-304` 在 append 时强制。
- **原事件不会被删**：append-only 日志里被压缩的原文仍然完整存在，只是被表面遮蔽。人类 transcript 应该读 append-origin 事件（`isAppendSurfaceEvent`，`surface.ts:49-64`），而模型表面读遮蔽后的视图——**两个视角分离**。
- 检查点身份是可跨后端识别的：`compactCheckpointSource(compactionId, sourceCommandId)` + `isCompactCheckpointSource()`（`packages/compaction/compaction/src/checkpoint.ts:19-51`），且从无 cordis 依赖的子路径导出，客户端/wire 消费者也能识别。

### 2.5 失败兜底路径（这一节是 DSH 最值得抄的部分）

**（a）摘要必须严格变小，否则拒绝：**

```ts
// packages/compaction/compaction-basic/src/region.ts:399-407
const framedSummaryTokenCount = dependencies.meter.estimateMessage(checkpointMessage)
if (framedSummaryTokenCount >= prepared.shadowedRouteTokenCount) {
  throw new Error(`summary is not smaller than the shadowed content (${framedSummaryTokenCount} estimated framed tokens >= ${prepared.shadowedRouteTokenCount})`)
}
```

比较用的是**带包装的检查点消息**对**被遮蔽区间的 route 定价总和**——即"替换后下一次请求的压力是否真的更低"。

**（b）摘要期间表面被改动 → 拒绝**（`region.ts:416-453`）。两种稳定性等级：
- 自动路径 `assertWholeSurfaceUnchanged`：重新 `measure()` 后把 `current.nodes` 与 `prepared.measurement.nodes` 做 `isDeepStrictEqual`，要求**整面不变**。
- 手动路径 `assertSelectedSpanStable`：只重新校验选中跨度仍是"同一个、当前存在、连续、定价相同、配对平衡"的替换目标，因此压缩期间注入的 idle 上下文可以存活（`docs/subsystems/compaction.md:21`）。

两者都抛 `SurfaceChangedError`，手动调用方据此报 `'changed'` 而不是 `'summary'`。

**（c）摘要器的其它拒绝路径**（`summarizer.ts`）：`max-tokens` 截断视为错误"incomplete checkpoint"，**不接受半截摘要**（`203-207`）；摘要文本全空 → 抛错（`167-169`）；摘要含图片输出 → `UNSUPPORTED_CONTENT`（`217-219`）；找不到可用 provider/model → 抛错并列出三种修法（`136-141`）。

**（d）免模型 prune 是"先手降载"：** 压力路径与溢出路径都**先跑 `pruneSession()` 并重新测量**，很多情况根本不进摘要（`index.ts:284-292, 309-313`）。这是"能不用模型就不用模型"的兜底。

**（e）溢出恢复的"部分成功也算成功"**（`index.ts:196-217`）：catch 里判断 `agent.session.surface.replaceGeneration > generation`，若成立则说明**免模型 prune 已经落盘**，"那次持久缩减本身就是重试的充分证据"，不因后续摘要抛错而丢弃，直接 `return { kind: 'retry' }`；取消仍然优先。

**（f）失败也留可追溯记录：** 事务 `catch` 里**一定尝试写一条 `compaction/end { error }`**（`region.ts:239-250`），`stage` 在 `assertStable` 之后从 `summary` 切到 `commit`（`region.ts:232-238`），因此失败能区分"表面未变"与"可能已部分变更"。

**（g）手动压缩的错误分类**（`compaction/src/types.ts`）：`'busy' | 'cancelled' | 'changed' | 'summary' | 'commit' | 'persistence'`。`changed`/`summary` 不动表面但仍持久化失败尝试；`commit` 可能已部分变更；`persistence` 表示内存括号已闭合但 flush 失败（分类逻辑 `region.ts:277-298`）。

**（h）崩溃中途 = 孤儿锁，而不是假成功：** 锁的顺序是 `start` → 摘要 → `summary` → `user/message` 替换 → `end`，**最后才释放**：

> Releasing the lock last turns a crash mid-operation into a detectable orphaned lock (a `compaction/start` with no matching `compaction/end`) rather than a `compaction/end` that falsely claims compaction finished. —— `docs/subsystems/compaction.md:19`

进入检测逻辑（`region.ts:307-333, 551-585`）反向扫描日志，独立解析三件事：是否有开着的 turn、是否有未匹配的 `compaction/start`、最新的 `session/end-seed` 在哪。**如果孤儿 start 早于更新的 seed 边界，说明它属于上一个生命周期的构造种子，可以视为死锁并忽略**（`region.ts:312-314`）。

---

## 三、大对象如何避免进入上下文：句柄/引用机制

### 3.1 spill：能力缝（Service Definition / Provider / Consumer）

```ts
// packages/spill/spill/src/types.ts:70-86（类型摘要）
interface SpillRef { locator: SpillLocator; bytes: number; retrievalHint: string }
type SpillLocator = Branded<'SpillLocator'>   // 不透明，消费者不得解析
```

- **Definition**：`ctx.spillStore` 只有一个方法 `saveText(input) → Promise<SpillRef>`，**原样持久化全量 content**，真实存储失败必须 reject（`docs/subsystems/spill.md:90`）。
- **Local Provider**：

```ts
// packages/spill/spill-local/src/store.ts:104-124（节选）
export async function saveTextFile(options: SaveTextOptions): Promise<SavedText> {
  const dir = sessionDir(options.root, options.sessionId)     // <root>/session-<sha256(sessionId) 前12位hex>
  const path = join(dir, `${randomBytes(6).toString('hex')}-${encodeSegment(options.suggestedName)}`)
  for (;;) {
    await mkdir(dir, { recursive: true, mode: 0o700 })        // 私有目录
    try { handle = await open(path, 'wx', 0o600); break }      // 独占创建，防植入符号链接重定向
    catch (error: unknown) { if (isErrno(error, 'ENOENT')) continue; throw error }
  }
  ...
}
```

  安全设计：`0700` 目录 + `0600` 文件 + `wx`（O_EXCL）标志；`suggestedName` 只作命名提示，永远不等于最终文件名（`docs/subsystems/spill.md:92`）。
- **Consumer（策略）**：`spill-policy` 是 `tools/post-execute` 的结果变换器。

### 3.2 替换内容的构造与"绝不超 cap"不变量

`spill-policy` 是 `tools/post-execute` 的结果变换器，核心是 `spillReplacement()`（`packages/spill/spill-policy/src/index.ts:125-183`）：

```ts
// index.ts:158-181（节选）
// Reserve the notice's byte cost INSIDE maxInlineBytes ...
const reserve = Buffer.byteLength(formatSpillNotice({ kind: 'exact', count: totalBytes }, ref), 'utf8') + 2
const previewBudget = Math.max(0, cap - reserve)
const { text: previewText, omitted } = preview(text, previewBudget)
const notice = formatSpillNotice(omitted, ref)
const replacedText = previewText.length > 0 ? `${previewText}\n\n${notice}` : notice
if (Buffer.byteLength(replacedText, 'utf8') > cap) {
  ctx.logger.warn(`spill-policy: spill notice for ${toolName} exceeds maxInlineBytes; keeping the inline content`)
  return undefined
}
return replacedText
```

预览用 `TextRetainer({ kind:'headTail', headBytes: ceil(budget/2), tailBytes: floor(budget/2) })`（`index.ts:96-103`）。两个不变量：**notice 的字节成本在预算内预留**（以"最坏遗漏计数"估上界，因此最终永不超 cap）；notice 本身放不下（极小 cap 或很长的 spill root）时**放弃 spill、保留原文**——宁可超预算也不发一个比原文还大的"压缩结果"。

### 3.3 兜底语义：spill 失败绝不改变调用结果

`spillPolicy.saveText` 抛错时（权限、ENOSPC、后端不可用）的注释就是设计声明（`index.ts:151-155`）：*"Best-effort: a storage failure must never fail the call or hide the content — keep the original inline."* 同页 JSDoc（`index.ts:18-42`）列出一整套"故意收窄"的边界：未配置 `maxInlineBytes` 就**什么都不注册**（真 no-op）；只处理纯文本结果；嵌套复合调用走 `tools/ptc-dispatch-log` 分支；**`read` 被模型面对的那条分支跳过以避免 `read → spill → read again` 死循环**（但 dispatch-log 分支仍然限制 `read`，因为日志副本不是模型上下文，而 `read` 恰恰最容易产生巨型日志）；没有会话属主 / 没有后端 / 保存失败都保留原文。

### 3.4 存量结果剪枝（免模型、确定性）

`pruneContent()`（`compaction-tool-result-pruner/src/index.ts:83-121`）按 `thresholdChars` 判定，用 `Array.from(text)` **按 Unicode code point 切（不劈代理对）**，保留头 `headChars` 与尾 `tailChars`，中间插固定 `PRUNE_MARKER`，最后断言"必须更小且在上限内"否则抛错。`pruneSession()`（`index.ts:136-185`）逐个替换超预算的当前表面 `tool/result`：

```ts
// index.ts:163-174
session.append('compaction/prune', {           // ← shadow-price：紧邻在前的计量事件
  shadowedRange: { start: seq, end: seq }, shadowedSeqs: [seq],
  shadowedTokenCount: this.ctx.tokenMeter.estimateMessage(event.data.message),
})
const replacement = session.append('tool/result', { ...event.data, message }, {
  surfaceOp: { op: 'replace', startSeq: seq, endSeq: seq },
  sourceEventSeqs: [seq],
})
```

三个可迁移的设计点：
1. **替换事件的字段限制由日志层强制**：`surface.ts:365-396` 的 `assertToolResultRewrite` 把 `content` 挖空后做深度相等比较，**除了 `content` 之外任何字段都不许改**。这堵住了"以剪枝为名篡改调用元数据"的路。
2. **shadow-price 协议**：计量事件与替换事件**同步紧邻**追加，因此纯消费者无需保留每节点价格就能 O(1) 地做减法（`docs/persistence-catalog.md:306-326`）。
3. **部分成功即持久**：一次 pass 中前面已提交的替换保持有效（`index.ts:130-135` 显式声明）。

---

## 四、会话状态如何持久化

### 4.1 唯一真相：append-only 事件日志

```ts
// packages/core/session/src/types.ts:60-83（节选）
export type SessionEvent<T extends SessionEventType = SessionEventType> = {
  [K in SessionEventType]: {
    type: K
    seq: SessionSeq      // 会话内单调序号
    time: number         // Unix epoch ms
    data: SessionEventMap[K]
    ignorable?: true     // 未知类型可跳过标记；缺省 = required = 必须拒绝重建
  } & (K extends SurfaceEventType ? SurfaceIntent<K> : { surfaceOp?: never; sourceEventSeqs?: never })
}[T]
```

- 只有 4 种 `SurfaceEventType` 会产生 LLM 消息：`system/message / user/message / assistant/message / tool/result`（`types.ts:24-28`）。其余是 **log-only**（可持久、可重放，但不进派生历史）。
- `ignorable` 的默认语义是 fail-closed："**缺省表示 required**：读到一个不认识的类型且没有这个标记，必须拒绝重建整个会话，而不是静默丢事件——未识别的必读事件可能改变其余日志的解释方式。写者只在纯信息记录上设 `true`。"（`docs/persistence-catalog.md:68-78`）默认过度拒绝（不便）优于静默恢复一个被掏空的会话。
- `surfaceOp` / `sourceEventSeqs` **只允许出现在 surface 事件上**，且由编译器在 `Session.append()` 调用点强制（`types.ts:53-58`）；JSON 可序列化也由 `Session.append` 在源头强制，坏事件永不入日志（`docs/subsystems/session.md:679`）。
- 已知事件类型目录完整生成于 `docs/persistence-catalog.md`（`compaction/*` 在 288-397 行，`request/*` 在 592-628 行，`session/*` 在 670-732 行，`tool/*` 在 927-1021 行）。

### 4.2 格式版本化：写者常量 + 不可变代

```ts
// packages/core/session/src/types.ts:88
export const SESSION_FORMAT_VERSION = 3
```

- 唯一的"用手维护的当前写者版本号"就是它；codec 顺序由 `scripts/gen-session-format-catalog.ts` 派生并校验相邻迁移恰好抵达它（`docs/session-format-status.md`）。
- 物理文件：JSONL v0 用 `session.jsonl[.zstd]`，**v1 起用 `session.vN.jsonl[.zstd]`；已提交的代永不重命名、替换或删除**（`docs/architecture.md:119`）。
- `stat`/`list` 只做**头部级**扫描（选数值最高的规范代 + 翻译受支持的历史头部），**不读事件体会**，所以缓存或格式升级不会把启动变成全量 body 扫描（`docs/subsystems/persistence.md:119, 323`）。
- 无法忠实解释的日志用 `SessionFormatUnsupportedError` 拒绝（与"损坏"区分开），报文里带上原始日志路径供用户定位（`persistence.md:118, 189`）。
- 版本状态用一份 YAML 记录 + 证据 tag 表达（`latestReleasedVersion: 3`，`evidenceTag: dsh-v0.1.5-alpha.1`），并把"写者常量 ≥ 已发布版本"做成 keyless 文档门禁（`docs/session-format-status.md`）。

### 4.3 元数据在日志之外：`SessionHeader`

```ts
// docs/subsystems/persistence.md:143-185 对应的 packages/core/session/src/types.ts
interface SessionHeader {
  readonly version; readonly id; readonly createdAt; readonly cwd?
  readonly parentSession?; readonly isSeeded
  readonly origin?: 'subagent'; readonly delegationDepth?; readonly agentPreset?
}
```

三个字段的持久化理由直接写在了 JSDoc 里，很值得抄：
- `delegationDepth`：**"持久化是为了让递归预算在重启和 resume 后仍然生效——一个纯运行时深度会让被恢复的子 agent 重置为顶层。"**
- `agentPreset`：**"持久化是因为 preset 决定了会话的工具与提示词：resume 后恢复成另一种组装，就会重放一段模型已无法据以行动的历史。"**
- `isSeeded` + `inheritedEventCount`：fork 血缘位与精确继承切口，**不是事件日志的一部分**，不进 `deriveMessages()`。

### 4.4 句柄模型与单写者

```
SessionPersistence: create(header) → write handle
                    open(id, 'read'|'write') → handle
                    stat(id) → { header, revision, eventCount?, sizeBytes? }
                    list() → snapshots
SessionHandle:      read(offset, length) / append(events) / flush() / close()
```

引用计数语义（`docs/subsystems/persistence.md:9-40`）：
- **所有日志读写都走句柄**，没有按 id 寻址的服务方法——句柄是跨进程写租约守护的唯一入口。
- `read` 句柄上做变更 → 运行时 `SessionReadOnlyError`（不做类型分裂）；同进程内第二次 `open(id,'write')` → `SessionAlreadyOwnedError`。
- `read` **永不回退到本句柄已观察过的更早状态**；`append` 解析成功后，之后开始的任何读（任何句柄、`stat`、`list`）至少看到该前缀。
- `close()` 幂等、不可取消，`Symbol.asyncDispose` 委托给它。

### 4.5 写路径：批量窗口 + 显式屏障

`LIVE_WRITE_BATCH_MAX_DELAY_MS = 200`（`session-persistence-jsonl/src/storage.ts:35-36`）是"一次路由到来事件的刻意等待上限"。`enqueueLive`（`storage.ts:267-281`）先把事件 `structuredClone` 成持久化自有的副本推入 `buffered`，然后在**定时器空闲时**启动一个固定窗口；`drainLive`（`storage.ts:288-316`）清除定时器、串行地 `splice(0)` 取批次并 `persistContiguous()`。

- 后端只安装一次监听（持久化本身已强制每 id 一个活跃写句柄）：`storage.ts:535-549` 把 `session/event` → `enqueueLive`、`session/flush` → `drainLive()`、`session/disposed` → 最终 drain + close。
- **第一个待写事件启动固定窗口，后续事件加入但不重置截止时间**；到期触发一次持久 `append`；写入期间到达的事件获得自己的截止时间、形成后续批次（`docs/subsystems/persistence.md:106`）。
- 写失败时 `this.buffered = batch.concat(this.buffered)`——**按原顺序放回队首**、`drainPaused = true` 暂停自动路径、经 logger 报告；下一次显式 flush 重试并向上抛出（`storage.ts:307-312`）。
- 所有变更串行在一条 per-handle promise 链上（`storage.ts:86, 356-370`）。
- `append` 只承诺"被接受、有序、对本后端实例可见"；**只有解析成功的 `flush` 才承诺崩溃后仍在**（`persistence.md:67-79`）。

### 4.6 提交点：语义检查点策略

`dsh-session-checkpoint-policy` 把"什么时候必须真的落盘"做成独立插件（`packages/session/session-checkpoint-policy/src/index.ts:29-82`）：

- `llm/stream`：把下游流包成一个 async generator，**先 `await ctx.sessions.flush(session)` 再 `yield* next()`**——完整日志前缀必须先持久，才允许适配器发出请求。
- `tools/execute`：顶层工具调用前 flush；若此时 `exec.signal.aborted` 就返回规范化的"dispatch 前已中止"错误结果，**不调用工具体**。
- `agent/pre-step`：每步开始前 flush 上一步已提交的一切。

JSDoc 明确：**检查点失败在模型与工具副作用边界上是 fail-closed**——下游适配器或工具体根本不会被调用（`index.ts:56-60`）。而 `ctx.sessions.flush(session)` 是**唯一** flush 入口（`packages/core/session/src/index.ts:1130-1157`），JSDoc 要求所有调用者（检查点策略、goal-round-driver 的空闲检查点、拆卸 drain、读存储前自 flush 的消费者）都走它而不是裸派发 `ctx.parallel('session/flush', …)`——"one owner, one spelling"。

### 4.7 派生状态（投影）的持久化

除了事件日志，DSH 还有一层**可丢弃、可重建的派生状态缓存**，其设计回答"缓存与真相不一致怎么办"：

- 缓存记录绑定**日志身份**：`(sessionId, createdAt, format generation, inheritedCut)`（`session-projection-cache/src/spec.ts:34-57`）。理由写在注释里："session id 命名的是一个槽位而不是一个生命周期——被删除后重建的同 id 会话，或一个更旧的记录，会通过所有水位检查"（`spec.ts:34-42`）。读取时 `identityMatches` 不匹配直接丢弃。
- 写入策略：两个节流触发（每 N 个已提交事件 / 最长 T 毫秒脏期）+ **三个强制写点**（会话创建、以及其它关键生命周期点）（`session-projection-cache/src/index.ts:57-66, 85`）。
- 语义："**缓存检查点可以滞后于日志，但绝不能领先日志**"（`index.ts:156-162`）。
- 层内还有 per-row `ver` 守卫（当前 `version: 7`，`spec.ts:100`），与身份匹配一起丢弃不兼容的旧行。

只读查询侧同样以廉价版本令牌做缓存键：`session-query` 的冷读缓存按 **(持久化实例, `stat` revision)** 键控，revision 未变则复用已恢复的 `Session`，不重读日志（`session-query/src/observation.ts:72-88, 202-`）。`stat().revision` 只是变更令牌：**相等可视为未变，不等则不承诺任何事，写权更替不改变 revision**（`persistence.md:294-303`）。

---

## 五、崩溃恢复与状态漂移防护

### 5.1 物理层：撕裂尾（torn tail）

```ts
// packages/session/session-persistence-jsonl/src/storage.ts:318-343（节选）
private async persistContiguous(batch: readonly SessionEvent[]): Promise<void> {
  if (this.access !== 'write') throw new SessionReadOnlyError(this.id, 'append')
  if (batch.length === 0) return
  await this.ensureLease()
  assertContiguous(this.id, batch, this.state.cursor)       // ← 序号连续性校验
  if (this.state.tornTruncateTo !== undefined) {            // ← 截断撕裂字节
    await this.storage.truncateTornTail(this.header, this.state.tornTruncateTo)
    this.state.tornTruncateTo = undefined
  }
  if (this.state.recoveredTail !== undefined) {             // ← 从撕裂帧里完整解出的记录，持久重写
    if (this.state.recoveredTail.length > 0) await this.storage.persistBatch(
      this.header, this.state.recoveredTail, this.state.materialized, this.state.inheritedEventCount)
    this.state.recoveredTail = undefined
  }
  await this.storage.persistBatch(this.header, batch, this.state.materialized, this.state.inheritedEventCount)
  this.state.materialized = true; this.state.cursor += batch.length
}
```

关键点：**只有"属于一次从未 resolve 的 append"的撕裂物理尾片段会被丢弃**；JSONL 后端还能从撕裂的 Zstandard 帧里**部分解码出完整记录**，这些记录由写路径在句柄的第一次新 append 之前持久重写（`persistence.md:110`）。读句柄永远不返回撕裂尾。

### 5.2 语义层：**不截断中断的 turn**，而是补全

这是最重要的一条设计判断，理由必须记住：

> A log crashed mid-turn ends with an open `turn/start` and no `turn/end`. Persistence does **not** truncate or repair it — a single turn can be huge in a long-horizon task (many steps, large tool output), and those events were durably appended before the crash. —— `docs/subsystems/persistence.md:110`

补全由 agent 层完成（`packages/core/session/src/repair.ts:29-135`）：`interruptedTurnClosers(events)` 单趟扫描日志，跟踪 `openTurn` / `openStep` / `pendingCalls`（`assistant/message` 里的 `tool-call` 块登记调用，`tool/call` 补上 `callSeq`，`tool/result` 时移除；每个 turn 边界重置，防止早先调用泄漏进尾部修复）。扫描完后按顺序合成：

1. 每个未结算调用一条 `tool/result`，`isError: true`——注释的理由是"**provider 会拒绝悬空的 assistant 调用，`Map` 插入顺序保留了它们的 transcript 顺序**"。
2. 若 step 开着，一条 `step/end`（"turn/end 时 step 还开着是不变量违规，所以 step 边界必须先于 turn 边界合成"）。
3. 一条 `turn/end { turn, reason: { kind: 'interrupted' } }`。

合成的 `tool/result` **区分两种情形并给模型明确的行动指引**（`repair.ts:104-108`）：

- 已记录 `tool/call` 但无结果 → `TOOL_OUTCOME_UNKNOWN` → *"…其结果是未知的。根据工具语义判断是否重试：仅当操作是只读或幂等时才重试；如果它可能有副作用，先核实外部状态或询问用户。不要盲目重试。"*
- 未记录 `tool/call` → `TOOL_NOT_STARTED` → *"如果仍然需要就重试它。"*

合成事件复用最后一条真实事件的时间戳，"使其确定且永不发明一个未来时间"（`repair.ts:84-88`）。`turn/end { reason: { kind: 'interrupted' } }` 是**循环本身永远不会发出**的唯一一种 `TurnEndReason`（`persistence.md:110`）。

### 5.3 resume 的精确顺序

`packages/core/agent-loop/src/index.ts:876-901` 的顺序是**先拿写权 → 冷读 → 补 closers → prepare → 补未存后缀**：

```ts
handle = await raceAbortCall(() => persistence.open(id, 'write', { signal: fused }), ...)  // 先占写权
const coldRead = await handle.read(0, undefined, { signal: fused })
const persisted = coldRead.events
const closers = interruptedTurnClosers(persisted)
if (closers.length > 0) await handle.append(closers)          // 以普通批次写回
preparation = SessionPreparation.create(this.runtime.ctx.sessions.prepare(id, {
  seed: [...persisted, ...closers], meta: structuredClone(handle.header),
  inheritedEventCount: handle.inheritedEventCount, eventState: coldRead.eventState,
}))
stored = { handle, storedCount: persisted.length + closers.length }
await this.appendUnstoredSuffix(stored, preparation.session)
```

源码注释把两个理由写得很直白：**"先拿写权排除同 id 的并发 resume（本进程内活跃 agent 的句柄已持有该声明）"**；**"语义崩溃修复是 agent 层的职责：持久化只交还物理上有效的日志；被打断的最后一个 turn 收到合成的 closers（缺失的工具错误、step/end、turn/end），它们作为普通批次通过同一个句柄追加。"**

`appendUnstoredSuffix`（`index.ts:749-757`）里有一个反漂移细节：追加后 `stored.storedCount += suffix.length`，注释是 *"Advance by what was stored, not to `session.seq`: an event appended during the await must stay unstored for the next flush."* ——**按"实际存了多少"推进游标，而不是推进到 `session.seq`**，否则 await 期间新追加的事件会漏存。

只读观察者（session-query）用**同一套 closers 但只作用于内存**，不写回（`persistence.md:112`）——所以"只读"不产生副作用，同一份日志在只读视角与 resume 视角下 transcript 一致。

### 5.4 跨进程写租约

`packages/session/session-persistence-jsonl/src/lease.ts:1-28` 的 JSDoc 就是设计说明：POSIX 在 `session.lock` 上做**非阻塞 `flock(2)`**（经原生系统支持）；Windows 用由该路径派生的**命名内核信号量**，"从不是文件锁或句柄，因此读、搜索、目录删除在持锁期间自由进行"；争用映射为 `SessionAlreadyOwnedError`；**内核在持有者描述符关闭（含任何进程死亡）时释放锁，所以崩溃的持有者永不阻塞后继者**；"活但卡死的持有者会一直持锁到进程退出：**故意不设过期**，因为过期会让一个停滞写者的恢复 append 撕裂日志"；POSIX 锁命名的是 inode 而非路径，所以持锁后要验证所锁 inode 仍是锁路径上的文件，否则重试。

对一个 Python 单体 Agent 的直接启示：**不要用"锁文件 + TTL"**，那正是注释里点名要避免的撕日志风险。

### 5.5 状态漂移的防线清单

| 防线 | 机制 | 位置 |
|---|---|---|
| 唯一真相 | 一切模型可见内容都必须能从日志重建（"Model-visible means logged"，有运行时 invariant 断言） | `docs/architecture.md:121` |
| 请求可重建 | `deriveMessages()` 从表面投影，每节点投影一次并缓存；表面重写才重建 | `docs/subsystems/session.md:597-607` |
| 单节点投影规则共享 | `deriveEventMessage(event)` 是公开纯函数，外部重建器与 dev invariant 用同一规则，不可能与缓存分歧 | `core/session/src/surface.ts:92-126` |
| 替换有据可查 | `sourceEventSeqs` 必须包含每一个被遮蔽节点，必须早于自身 seq，不得重复 | `surface.ts:269-304` |
| 替换范围受限 | `surface replace` 的 startSeq/endSeq 必须 < 自身 seq 且在当前位置存在、start 位置 ≤ end 位置 | `surface.ts:313-321, 324-344` |
| 只改内容 | `tool/result` 替换除 `content` 外深度相等，且只能改写恰好一个当前节点 | `surface.ts:365-396` |
| 系统提示受保护 | node 0 上的 `system/message` 只能被"恰好覆盖该节点的一条 `system/message`"替换 | `surface.ts:398-418` |
| 序号连续 | 追加批次首个事件的 `seq` 必须等于已存 next-seq | `storage.ts:323`、`persistence.md:345` |
| 表面代数 | `replaceGeneration` 单调计数，供增量消费者区分"纯尾部增长"与"重写" | `surface.ts:189-195, 466-479` |
| 未知事件 fail-closed | 没有 `ignorable: true` 的未知类型 → 拒绝重建 | `types.ts:68-78` |
| 缓存不错位 | 投影/冷读缓存绑定日志身份 + 水位 + 行版本 | `session-projection-cache/src/spec.ts:34-57`、`session-query/src/observation.ts:72-88` |

### 5.6 避免重复执行

DSH 的态度是"**不用假装工具调用幂等**"：
- 崩溃时未结算的工具调用一律合成为 `isError` 结果，并把"是否可以重试"的判断**交给模型**，附上两条不同措辞的指引（只读/幂等才重试、可能有副作用先核实外部状态）（`repair.ts:104-108`）。
- `assistant/attempt` 保留失败/重试/取消/流错误的尝试（含 provider usage），**且不虚构 assistant 消息**（`docs/subsystems/session.md:597-607`）；`assistant/message` 内嵌产生它的精确紧凑定时流（`docs/architecture.md:117`）。
- 硬进程丢失在结算前**不会留下持久 attempt 流**——这是被明确接受的设计（同上）。

---

## 六、幂等性、事务性提交、版本/序号机制

### 6.1 幂等性

| 操作 | 幂等机制 |
|---|---|
| `SessionHandle.close()` | `this.closing ??= (async () => {...})()`——只执行一次；重复调用返回同一个 promise（`storage.ts:223-224`） |
| `read` 重复调用 | 单调视图：不允许观察到比先前读更短的前缀（`storage.ts:172-174`） |
| `flush` 于未落盘会话 | 无待写内容时直接返回 `// appends are durable on resolution`（`storage.ts:207`） |
| `materialize` | 用 `link()`（EEXIST 失败）而**不是 `rename()`**（会静默覆盖），并先 `rejectExistingLog` 拒绝覆盖已提交日志（`index.ts:1130-1157, 1182-1192`） |
| spill | `open(path, 'wx', 0o600)` 独占创建 + 随机 6 字节前缀，重名不可能 |
| append 失败 | 记录 before size 并 `truncate` 回滚：注释写明"不变的游标会重试该批次，留下部分字节会产生重复序号"（`index.ts:1241-1284`） |
| 压缩 | 一次事务一个 `compactionId`（`randomUUID`），贯穿 start/summary/end 与 checkpoint source（`region.ts:204-210`、`checkpoint.ts:33-42`） |

### 6.2 事务性提交

压缩事务的提交点是**同步不 yield 的一段**：`commitCompactionBody()` 的 JSDoc 就是 *"Append one completed summary record and replacement body without yielding."*（`region.ts:455-459`）——摘要记录与替换体在同一同步块里落盘，中间不给其它生产者插队的机会。阶段标记 `stage: 'summary' | 'commit'` 在 `assertStable` 之后切换到 `commit` 并置 `closing = true`（`region.ts:232-238`），于是失败分类能正确区分"表面未变"与"可能已部分变更"。

持久化侧的"事务"是句柄级的：`append`（接受并有序）→ `flush`（durability barrier）。`close()` 在释放写权前**先把路由缓冲 drain 到静默**，即使 backend 拆卸顺序不同也不丢事件（`storage.ts:214-259`）。

批处理的物理写入则是三种崩溃安全原语的组合：
1. **首次落盘**：私有目录逐级 `mkdir` + 逐级 `fsync` 父目录 → 写临时文件并 `handle.sync()` → `link()` 发布 → `fsync` 目录（`index.ts:1124-1156`）。
2. **增量追加**：`open(path,'a')` → `handle.writeFile` → `handle.sync()`，失败则 `truncate` 回滚（`index.ts:1246-1284`）。
3. **发布语义**：注释明确写"`link()` 成功后日志已发布；**未同步父目录元数据前，新 link 还不具备崩溃持久性**"。

### 6.3 版本/序号机制汇总

- **`seq`**：会话内单调、连续、永不重写；连续性是追加时的断言、读取时的切片前提（`storage.ts:323`、`persistence.md:345`）。
- **`logRevision`**：测量快照消费到的持久事件数，等于下一个未读 seq（`token-meter/types.ts`、`docs/subsystems/token-meter.md:5`）。
- **`replaceGeneration`**：位置替换的单调计数，用作"表面是否真的前进了"的廉价证据（`surface.ts:537-541`；用于 `index.ts:192, 202, 220` 的重试判断）。
- **`SESSION_FORMAT_VERSION = 3`** + 代际文件名 `session.vN.jsonl` + 相邻迁移包（`session-format-v0-to-v1` / `v1-to-v2` / `v2-to-v3`）+ 不可变发布。
- **`SessionPersistenceRevision`**：后端特有的廉价变更令牌，仅用于派生读模型缓存（`persistence.md:294-303`）；投影缓存另有自己的行版本 `version: 7` + 身份匹配（`spec.ts:100`）。
- **`session/end-seed`**：种子与实时工作的分界标记，让"未匹配的 `compaction/start`"能区分"崩溃中的压缩"与"当前正在压缩"（`docs/subsystems/session.md:661-670`）。

---

## 七、迁移到 Python 单体 Agent（无插件框架）的做法

1. **先立"事件日志即唯一真相"，再谈上下文管理。** 一个 append-only 的 JSONL 事件文件，`{seq, ts, type, data}`，只允许追加，`seq` 连续且写入时断言；模型历史永远由 `derive_messages(log)` 投影出来，**绝不维护一个单独的 `messages` 列表作为真相**。这条一旦破了，后面的压缩/恢复/回放全部无从下手。对应 `core/session/src/types.ts:60-83` + `surface.ts:92-126`。

2. **用"表面 + 替换"表达历史改写，而不是删/改历史。** 维护一个 `surface: list[int]`（当前可见的 seq 列表），压缩和新旧内容替换都追加一条新事件，带 `surface_op = {"op":"replace","start_seq":..,"end_seq":..}` 与 `source_seqs=[...]`。校验三件事：被替换的 seq 必须在当前表面里、必须早于自身 seq、`source_seqs` 必须覆盖全部被遮蔽节点。原文永久保留，人类 transcript 读 append-origin 事件，模型读表面视图。对应 `surface.ts:269-344`。

3. **压缩做成"有锁的日志事务"，锁的最后才释放。** 顺序固定为 `compact/start`（带 `compaction_id`）→ 摘要 → `compact/summary`（记账：被遮蔽 seq 列表 + 价格 + provider/model/usage）→ 替换事件 → `compact/end`。崩溃就会留一个**没有 end 的 start**，这正是"上一次压缩没做完"的可检测信号。不需要真正的分布式事务，只需要"**标记先写、释放标记最后写**"。对应 `region.ts:173-275` 与 `docs/subsystems/compaction.md:19`。

4. **压缩必须"可证明变小"，失败一律回退到原历史。** 用固定密度估值（`len/4 + 4/块 + 4/消息`）算出被遮蔽区间的价格和替换消息的价格，**若替换不小于原文就抛错回滚**；摘要被 max_tokens 截断、摘要为空、摘要期间表面被改动，一律拒绝。再加一条"能不用模型就不用模型"的先手：先做确定性的 tool-result head/tail 截断并重新测量，不够才调摘要模型。对应 `region.ts:399-407, 416-453`、`summarizer.ts:167-169, 195-211`、`compaction-tool-result-pruner`。

5. **大对象一律外置为"文件句柄 + 取回指引"，并让降级永不改变调用语义。** 工具结果超过阈值就写到一个会话私有目录（`0700` 目录、`0600` 文件、`O_EXCL` 独占创建），把 `head/tail 预览 + 路径 + "用 read/grep 取回"的提示` 交给模型。**预留提示文本的字节预算，保证替换结果永不超上限**；若连提示都放不下就**放弃外置、保留原文**（宁可超预算也不发一个比原文更大的"压缩结果"）；存储失败只记日志，**绝不把成功的工具调用变成 error**。对应 `spill-policy/src/index.ts:125-204`、`spill-local/src/store.ts:104-131`。

6. **崩溃恢复不截断中断的 turn，而是补全成合法 transcript。** 单趟扫描日志找出开着的 turn/step 与未结算的工具调用，然后按顺序合成：每个未结算调用一条 `isError` 的 tool result（**区分"已记录 call 但无结果"与"未记录 call"，并附上"只读/幂等才重试，可能有副作用先核实外部状态"的指引**）→ 一个 `step/end` → 一个 `turn/end{reason:"interrupted"}`。合成事件的序号接在日志尾部，时间戳复用最后一条真实事件。对应 `core/session/src/repair.ts:29-135`。

7. **写入用"追加 + 显式 flush 屏障"，恢复顺序固定为"先占写权、再读、再补"。** 生产侧事件先入内存缓冲、定时/定量批量落盘（DSH 用 200ms 窗口），但**在每次模型请求前、每次工具副作用前、每步开始时显式 flush**——检查点失败就不发请求/不调用工具（fail-closed）。单写者用一个进程级 + 文件级的排他句柄（Python 用 `fcntl.flock` 非阻塞，**不要用"锁文件 + TTL"**，过期会让停滞的写者恢复后撕日志）。恢复时**第一步就是拿写权**，然后读、补 closers、再落盘；落盘游标按"实际写了多少"推进，不要推进到最新序号。对应 `session-checkpoint-policy/src/index.ts:29-82`、`session-persistence-jsonl/src/{storage.ts,lease.ts}`、`agent-loop/src/index.ts:876-901, 749-757`。

8. **给派生缓存加"日志身份 + 水位 + 版本"三重护栏，并默认 fail-closed。** 任何缓存（标题、摘要、token 计数、搜索索引）都必须记录它是从哪个日志身份（`session_id + created_at + format_version + inherited_cut`）和水位（已折叠到第几个 seq）算出来的；身份不匹配**直接丢弃而不是修复**——注意 `session_id` 命名的是槽位而非生命周期，删除后重建的同 id 会话会让单纯的 id 匹配蒙混过关。未知事件类型默认**拒绝重建**，只有显式标了 `ignorable` 的纯信息记录才允许跳过（默认过度拒绝，好过静默恢复一个被掏空的会话）。对应 `session-projection-cache/src/spec.ts:34-57`、`types.ts:68-78`、`docs/persistence-catalog.md:68-78`。

---

## 八、依赖 DSH 插件/事件框架、难以直接迁移的部分

1. **`ctx.on(...)` 瀑布钩子（`agent/pre-step` / `agent/request-error` / `llm/stream` / `tools/execute` / `tools/post-execute`）承载了全部预算强制点。** 压缩"在请求派生之前"运行、溢出恢复通过返回 `{kind:'retry'}` 让循环重试、检查点作为流包装器延迟真正的适配器调用——这些都依赖瀑布的"必须调用 `next()` 才委派"语义与有序监听器。Python 单体里需要显式设计等价的**有序中间件链 + 明确的短路/重试返回类型**，否则容易退化成散落各处的 `if`。

2. **声明合并（declaration merging）扩展 `SessionEventMap` / `Context`。** `compaction/*`、各插件的 log-only 事件都是通过 `declare module '@deepseek-ai/dsh-session/types'` 合并进来的，客户端与 wire 消费者靠同一机制获知事件。Python 没有编译期合并：需要一张**集中注册表 + 运行时 schema 校验**来替代，且必须自己实现"未知类型缺 `ignorable` 就拒绝重建"的 fail-closed 行为。

3. **能力缝的三段式（Service Definition / Provider / Consumer）与 `ctx.get(name)` 可选服务。** 压缩缝故意不依赖 session/llm 之外的东西，"prune 服务可选加载所以 compaction-basic 仍可独立组合"（`index.ts:279-282`）；spill 缝只定义存储、策略由消费者拥有。迁移到单体后这些抽象如果没有多个真实实现，会变成纯开销——**保留接口形状（便于测试替身）但不必保留 cordis 式的服务注册与 effect/disposer 生命周期**。

4. **`SessionProjection` / `SessionProjectionCache` 的注册表 + `session/event` 增量供应。** token-meter 把自己的三个投影注册进 `ctx.sessionProjections`，并靠 `ctx.on('session/event')` 做"只对已被读过的会话做 eager 追赶"（`token-meter/index.ts:113-122`）。单体里可以退化为"在日志追加时同步通知订阅者"的回调列表，但**增量折叠的 plan/commit 纪律必须保留**。

5. **`AbortSignal` 贯穿、`raceAbortCall`、owner fiber 跟随（`ownerCtx.effect`）。** resume/压缩/摘要的取消语义（"取消永远优先"、"aborted 请求保留精确 abort reason"）建立在 cordis 的 fiber 生命周期与 `AbortSignal.any` 组合上。Python 里需要用 `asyncio.Task` + `CancelledError` 语义重新设计，且要注意 `finally` 中"清理不可取消"的部分（对应 `SessionHandle.close()` 的"幂等且故意不可取消"）。

6. **跨进程内核写租约（原生 `flock` / Win32 命名信号量）。** 这是仓库自带的原生插件（`@deepseek-ai/node-addon-system/flock`），且明确拒绝 TTL 方案。Python 有 `fcntl.flock` 可以直接对应 POSIX 侧，但 Windows 侧与"浏览器 worker stub"这类环境分支需要自行取舍；单进程单体通常只需要进程内声明 + 文件锁防止第二个进程误开同一会话。

7. **快照/回放测试基建（`snapshots/`、`test:snapshot`、双语文档门禁、`verify-type-equiv`、生成式目录门禁）。** "模型可见文本逐字固定、动态行为用快照或端到端覆盖"这类纪律靠一整套 keyless 重放与文档生成门禁执行（`AGENTS.md` 多处）。单体项目可以只取其中两条：**(a) 记录真实会话日志作为回归 fixture；(b) 关键提示词文本逐字固定并断言**。
