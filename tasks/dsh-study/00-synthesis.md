# DeepSeek Harness (DSH) 稳定性实现研究 —— 兼 PhysEarth-Agent 迁移方案

> 研究对象：`github.com/deepseek-ai/DeepSeek-Harness`，本地 checkout `GeoAI_challenge/tmp/deepseek-harness`
> 版本锚点：commit `c291e7961a515f6d7af9304e7fd1d257929aef26`（2026-09-10），root version `0.1.5-rc.2`，Session format v3
> 目标项目：PhysEarth-Agent（本地 HEAD `9ccc6f3`，Python 3.13 + Gradio + 物理模型 registry）
> 分册：`A-lifecycle-and-loop.md`、`B-context-and-persistence.md`、`C-defensive-and-delegation.md`、`D-ui-streaming-and-tests.md`（同目录，含 file:line 证据）

## 0. 执行摘要

DSH 的稳定性不来自某个"防死循环算法"，而来自四条结构性约定加上一套工程纪律：

1. **唯一事实源**：追加式 Session 事件日志是模型上下文的唯一来源，历史由日志投影（`deriveMessages`）；硬性不变量 **"Model-visible ⟺ logged"**，并有运行时不变量断言（`packages/core/agent-loop/src/invariant.ts`）。
2. **提交点与双轨结算**：成功调用写 `assistant/message`，失败/重试/取消只写 `assistant/attempt`（仅日志、不进模型历史）；轮次/步骤有显式边界（`turn/start`→`step/start`→`step/end`→`turn/end`），状态只在提交点发布。
3. **策略钩子而非循环内 if**：所有限流/压缩/重试/循环卫生都是挂在瀑布事件上的插件——`agent/pre-step`（准入与压缩）、`agent/request-error`（返回 `{kind:'retry'}` 才重试）、`tools/pre|post-execute`（守卫与改写）、`agent/turn-stopping`（终检）。DSH 的 loop **没有内置轮次预算**，失控兜底由扩展点执行。
4. **可证明的恢复语义**：重试只在"表面替换生成号前进"时进行；压缩必须"可证明变小"否则回退原历史；崩溃恢复不截断中断轮次，而是补合成合法 transcript。

对 PhysEarth-Agent 的直接启示：我们的不稳定（plan/run/chart 三重漂移、gate 反复触发、跨 turn 重置、上下文硬截断、前端整树重绘）**不是缺一个 gate，而是缺第 1、2 条**；第 3、4 条决定了修复能否长期不退化。

## 1. DSH 的骨架（理解机制的前提）

- **一切皆插件**：基于 [Cordis](https://github.com/cordiverse/cordis)，插件向共享上下文贡献服务、类型化事件与可撤销副作用；agent loop 本身也是插件，没有特权内核。运行时是一棵由 profile + 组合包（bundle）+ 有序 patch 文件叠出的插件树（`docs/architecture.zh.md:9-45`）。
- **三种事件域**：会话事件（持久事实，`session/event`）、Agent 事件（活跃协调，`agent/*`）、能力事件（`fs/*`、`tools/*` 等 seam 策略）（`docs/architecture.zh.md:70-80`）。
- **能力 seam 三段式**：Service Definition / Service Provider / Consumer，替换 provider 即可改变整个产品（如 fs 指向远程沙箱则 Bash/PTY/LSP 一起搬走）（`docs/architecture.zh.md:129-135`）。
- **轮次/步骤模型**：一个步骤＝一次模型请求＋它调用的工具；一个轮次包含零或多个步骤（`docs/architecture.zh.md:84-107`）。
- **瀑布事件语义**：监听器必须调用 `next()` 才委派，返回即短路——这是"策略可插拔又不破坏流程"的机制基础（`AGENTS.md` conventions）。

## 2. 八大稳定性支柱（机制 → 证据 → 对 PhysEarth 的启示）

### 支柱 1：日志即真相 + 可投影（Model-visible ⟺ logged）

- 机制：`Session` 是 append-only 事件日志（`seq` 单调连续且写入时断言）；`deriveMessages()` 从日志投影模型历史；投影 seam（`ctx.sessionProjections`）把派生状态折叠为类型化状态，载体用 `snapshot()` 取裁剪视图。新增任何"模型能看到的东西"都必须新增会话事件（`docs/architecture.zh.md:119-127`）。
- 证据：`packages/core/session/src/types.ts:60-88`；`packages/core/agent-loop/src/invariant.ts`（从日志重建请求的不变量）；token-meter 的 `_sync()` 从 seq 0 重放折叠（`packages/llm/token-meter/src/index.ts:217-239`）。
- 对 PhysEarth：`session["research"]["plan"]`、`session["successful_runs"]`、`session["figures"]`、agent 局部 `review_attempts` 是四个并行事实源，正是"run 已成功仍被判缺失/图表覆盖对不上"的根因。**改造目标**：research 事实改为追加事件，plan/run/chart/target 的覆盖关系全部由投影算出，gate 不再直接读散装 dict。

### 支柱 2：提交点、双轨结算与显式轮次/步骤边界

- 机制：成功调用在 `assistant/message` 结算（并内嵌精确流），失败/重试/取消到达 settlement 时写 `assistant/attempt` 且**不进入派生历史**（`docs/architecture.zh.md:85`、`packages/core/agent-loop/src/agent.ts:441-483`）。
- 机制：`agent/pre-step` 决定准入；被拒或首批为空则"关闭一个不含步骤的轮次"；`agent/turn-stopping` 是序列终检点（`docs/agent-lifecycle.zh.md:33-35,71-72`）。
- 纪律：`packages/AGENTS.md`「**Publish state only at its commit point**」——通知与派生状态只在操作成功后发布。
- 对 PhysEarth：我们已有"只把非 fault 轮次写入历史"和"correction 不保留草稿"的雏形；缺的是**步骤边界**：现在 gate 的判定、工具的副作用、回答的提交都混在一个 while 循环里，导致"状态在 gate 里被改、但历史没有记录"。

### 支柱 3：重试的"有进展才重试"语义

- 机制：模型请求失败进 `agent/request-error`；监听器返回 `{kind:'retry'}` 才重试，否则抛原错误结束（`packages/core/agent-loop/src/agent.ts:441-464`）。压缩恢复只在"剪枝或摘要推进了 surface replacement generation"时重试，否则保留原始请求错误（`docs/agent-lifecycle.zh.md:87`）；token-meter 用 `replaceGeneration` 作为"表面是否真的前进"的廉价证据（`packages/llm/token-meter/src/index.ts:192-220`）。
- 对 PhysEarth：这正是我们上一轮 P0"gate 状态指纹"的推广版——但 DSH 把它做成**策略返回值**（retry / 不 retry），而不是散落在循环里的计数器。**改造目标**：抽出 `RetryDecision` 语义（`retry | fail | degrade`）+ "generation 前进"判据，plan/figure/run 三类 gate 共用。

### 支柱 4：循环卫生守卫是"顾问式"的，且有分级阈值

- 机制：`guard/repeat-tool-reminder` 在 3/5/8 次**完全相同**（同一工具、同一规范化参数）调用时注入提醒（首条温和、后续详细），**永不阻断**合法重复；`exclude` 的工具既不计数也不重置；按 agent 计数，新用户消息清零（`packages/guard/repeat-tool-reminder/README.md`、`src/index.ts:22-40,60-160`）。
- 机制：`guard/timeout-policy` 给声明了时限的工具调用超时；DSH loop 无内置轮次预算，失控由 `agent/turn-stopping` 执行取消（`packages/core/agent-loop/README.zh.md:200`）。
- 对 PhysEarth：我们用"第 N 次即硬停"，代价是长流程被误杀；且计数在 agent.run 内，runner/UI 每个 turn 重建 → 跨 turn 重复不被发现（Q4 实测 8 turn 各刷 5 次）。**改造目标**：分级顾问提醒（3/5/8）→ 仍无进展才停；计数提升到 session 级并随真实进展清零；参数规范化用"排序后的 JSON"做同一性判据。

### 支柱 5：上下文压缩参数化、可证明变小、先剪枝

- 机制：`compaction-basic` 在 `agent/pre-step` 测压（`thresholdRatio=0.8`，逐字保留 `retainRatio=0.16` 或 `retainTokens`），provider 报 `CONTEXT_WINDOW_EXCEEDED` 时压缩后重试（`maxOverflowRetries=1`）；**先做确定性工具结果剪枝，再调摘要模型**；摘要被截断/为空/不比原文小 → 拒绝并回退原历史；保留尾部必须在 tool-call/result 成对边界回退，保证 transcript 仍是合法序列（`packages/compaction/compaction-basic/README.zh.md`、`src/index.ts:148-333`、`src/region.ts:117-155,399-453`）。
- 机制：压缩是一次日志事务 `compaction/start → summary → 替换事件 → end`，崩溃会留下"孤儿 start"作为可检测信号（`region.ts:173-275`）。
- 对 PhysEarth：`CONTEXT_CEILING_TOKENS=96000` + `_compact_messages()` 是"到顶就砍"，且砍完不再重试。**改造目标**：比例阈值 + 保留窗口 + 剪枝优先 + 溢出后压缩重试路径；压缩写入日志事务（有锁、可检测半途失败）。

### 支柱 6：大对象外置为句柄，降级永不改变调用语义

- 机制：`spill` 把超大文本落盘为 0700 目录/0600 文件/O_EXCL 独占创建，只把 `locator + retrievalHint + head/tail 预览` 交给模型；**预留提示文本的预算，保证替换结果永不超上限；若连提示都放不下就放弃外置保留原文；存储失败只记日志，绝不把成功的工具调用变成 error**（`packages/spill/spill-policy/src/index.ts:125-204`、`spill-local/src/store.ts:104-131`）。
- 纪律：`packages/AGENTS.md`「**Apply bounds to the complete result**」——字节/token/条数/时间上限在"完整发射值已知处"执行。
- 对 PhysEarth：已有 result handle + 有限预览，方向正确；缺"边界处对完整结果设限"与"外置失败降级"纪律。

### 支柱 7：崩溃恢复补齐语义，而不是截断

- 机制：物理层丢弃撕裂尾（`storage.ts:319-343`）；语义层扫描日志找开着的 turn/step 与未结算工具调用，按序合成 `tool/result(isError)` → `step/end` → `turn/end{reason:'interrupted'}`（`packages/core/session/src/repair.ts:29-135`）；恢复第一步是拿写权（`open(id,'write')` + `flock`，明确拒绝"锁文件+TTL"方案），追加走 200ms 批量窗口但**在每个模型请求/副作用/步骤前显式 flush**（fail-closed）（`core/agent-loop/src/index.ts:749-757,876-901`）。
- 对 PhysEarth：本地 Studio 重启后无法诊断"上一轮停在哪"，服务生命周期问题（报告 S11）也只是重启了事。**改造目标**：会话日志 + 半途轮次合成收尾 + 显式 flush 屏障。

### 支柱 8：UI 一致性由序号协议保证，且"对不齐就 rebaseline"

- 机制：Assistant 流帧携带 `attemptId + revision（单调，替换重置为 1）+ 稠密 index`，客户端校验 `revision == expected`，不符即判丢帧；瞬时增量（transient）与持久结算（durable）双轨，持久事件到达后原子替换临时行；**任何无法对齐（重复、跳变、未知 attempt）→ 请求整页重读**（`packages/api/session-controller/src/client/sessions/assistant-stream.ts:108-183`、`transport.ts:206-216`）。
- 机制：连接代次（generation）+ ready 握手（先挂监听后报就绪）+ 指数退避抖动 + 离线暂停 + 状态去重 + 回调异常隔离（`packages/client/connection/src/client/connection.ts:58-101,139-199,270-284`）。
- 纪律：`docs/subsystems/conversation.md:245-256` 把"历史+实时追加 ≡ 整窗重放"写成**验收条件**。
- 对 PhysEarth：Gradio 无客户端可控流，正解是**把一致性责任搬到服务端**——服务端持有 `(session_id, applied_seq)`，只发可幂等重取的内容；回答用 `attempt_id + revision` 包裹并只在真正变化时推送（我们已做一半：面板级 HTML 去重 + 空帧保留）。

## 3. 工程纪律网（比机制更值钱的部分）

| 纪律 | DSH 的做法 | PhysEarth 可落地的等价物 |
|---|---|---|
| 缺陷类别 → 规则 | `docs/defensive-patterns.md`：每条模式都是"实际发布或差点发布的缺陷" | 把已有 S1–S11 报告改写成"规则 + 断言 + 测试"三件套 |
| 事故复盘 | `docs/postmortem/`：Executive summary → Timeline → Root cause → Guardrails | 现有分析报告升级为 `docs/postmortem/` 目录，每条给出新增的 guardrail 链接 |
| 决策记录 | `.agents/notes/{implemented,proposed,rejected}/`，路径编码生命周期与类别 | `tasks/decisions/` 或 `docs/agent-notes/` |
| 测试网 | unit / coverage(per-file 100%) / e2e(真 key) / snapshot(录制回放) / perf 预算 | 复用 `evaluation/results/**/record.json` 做 **trace 回放断言**；Tier0 已是确定性网 |
| 两条测试原则 | "验证世界，不验证自述"；"单独跑才绿 = spec 有缺陷" | 评测指标一律从 record 重算（已有此传统），并禁止依赖顺序的测试 |
| fail-loud 配置 | 未知字段/重复项/矛盾组合在加载时抛错，禁止静默兜底 | 模型卡校验已如此；扩展到 research/gate 配置 |

## 4. 差距表：PhysEarth 现存不稳定点 → 支柱

| 编号 | 现象（代码位置） | 缺失的支柱 | 最小改造 |
|---|---|---|---|
| P-1 | plan/run/chart 覆盖漂移（`research.py::execution_gaps/_validate_chart_runs/_target_coverage`） | 1 日志即真相 | research 事实追加事件 + 投影计算覆盖关系 |
| P-2 | 复杂 plan 反复被拒 → 全文重写（`research.py::propose` 校验链） | 2 提交点 + 3 重试语义 | 失败返回可执行 patch；generation 前进才允许再提交 |
| P-3 | 无进展循环靠次数上限、跨 turn 重置（`agent.py::gate_watch/review_attempts`） | 4 顾问式分级守卫 | 3/5/8 提醒；session 级计数；参数规范化同一性 |
| P-4 | 上下文硬截断（`session.py::CONTEXT_CEILING_TOKENS`、`agent.py::_compact_messages`） | 5 压缩策略 | 0.8/0.16 阈值 + 剪枝优先 + 溢出重试 |
| P-5 | 前端整树重绘闪烁（`app.py::respond`、`ui/render.py`） | 8 序号协议 | 服务端 revision + 只推变化面板（已起步） |
| P-6 | 大数组/大输出入上下文（`tools.py`/`results.py`） | 6 句柄外置 + 完整结果设限 | 边界处尺寸上限 + 降级不变语义 |

## 5. 迁移路线（建议）

### P0（离线可测，1 周内）
1. ✅ **已实施**（commit `bcbb5d3`）`physearth/guards.py`：分级重复提醒（3/5/8，顾问式，永不阻断）+ 参数规范化同一性 + 按会话计数 + 新问题清零；`agent.py` 在每次工具结果后注入提醒消息与 `harness_warning` 事件；identical-success 硬停移到最后一个阈值之后（第 9 次）。
2. ✅ **已实施**（commit `b179429`）失败记忆提升到会话级：`guards.remember_failure/failure_count/clear_failure` + `agent.py` 的 `plan_loop_no_progress`——同一 `research_plan` 校验失败跨 turn 复现时不再免费重启 5 次预算，第二次消息里一次相同失败即停并给出改变计划/问题/模型的指引；计划被接受即清除链条。
3. ⏳ gate 计数提升到 session 级 + "状态指纹/生成号前进才重试"统一判据（`_research_gate_fingerprint` 已具备，缺"跨 turn 会话级"这一层）。
4. ⏳ research 事实**双写**追加日志（先写不读），为投影做准备。
5. ✅ 部分完成 UI：回答面板级去重 + 空帧保留（commit `b9b6341`）；仍缺 `attempt_id + revision` 帧协议。

### P1（结构性，1–2 周）
5. research 投影层：runs/figures/targets 覆盖关系由日志投影；gate 不再直读 dict。
6. 压缩策略改造（阈值比例 + 保留窗口 + 剪枝优先 + 溢出重试 + 压缩日志事务）。
7. plan 提交点与局部补丁：`replace /runs/2/parameters/thickness_m` 形式的修复指令。

### P2（大改，需评估）
8. 轮次/步骤语义重构（turn/step 事件 + `turn-stopping` 终检 + 会话级半途收尾）。
9. trace 回放测试网 + 不变量断言（CI 门禁）。
10. 子代理/委派：Q3/Q4 这类多阶段实验交给子 agent，主 agent 只持句柄与结论（见 C 册）。

## 6. 证据索引（关键文件）

- `docs/architecture.zh.md:84-127`（轮次流程、会话日志、Model-visible ⟺ logged、投影 seam）
- `docs/agent-lifecycle.zh.md:10-93`（时序图、`assistant/message` vs `assistant/attempt`、压缩与重试语义）
- `docs/tool-execution-pipeline.zh.md:10-64`（pre/guards/approval/execute/post/finalize 与结果规范化）
- `docs/defensive-patterns.zh.md:7-35`（缺陷类别规则清单）
- `packages/core/agent-loop/README.zh.md:73-125`（步骤语义、请求冻结、失败与取消、无内置轮次预算）
- `packages/core/agent-loop/src/agent.ts:441-489`（失败结算 + `agent/request-error` retry 判定）
- `packages/guard/repeat-tool-reminder/{README.md,src/index.ts}`（3/5/8 顾问提醒与同一性判据）
- `packages/compaction/compaction-basic/README.zh.md`（压缩参数面与 fail-loud 配置）
- `packages/llm/token-meter/src/index.ts:145-239`（唯一计量口径与 plan/commit 折叠）
- `packages/core/session/src/repair.ts:29-135`（语义层崩溃修复）
- `packages/api/session-controller/src/client/sessions/assistant-stream.ts:108-183`（revision + 双轨结算 + rebaseline）
- 分册：`A-lifecycle-and-loop.md`、`B-context-and-persistence.md`、`C-defensive-and-delegation.md`、`D-ui-streaming-and-tests.md`

## 7. 补充机制（A 册 / C 册）与规划调整

### 7.1 A 册：循环与失败处理的四条硬规则

| 规则 | DSH 证据 | PhysEarth 现状对照 |
|---|---|---|
| **全仓只有一处循环**，退出条件是"模型不欠回答 **且** 队列为空"，且在终检钩子之后再读一次 | `agent-loop/src/agent.ts:225-238,269-350,352-498` | `agent.py::stream` 是单循环，但 gate 分支里散落 `break/continue/return`（≥12 处），退出语义难以一眼判定 |
| **失败降级为数据**：工具层永不向上抛异常，每层 catch 转 `isError` 结果 | `core/tools/src/index.ts:1453-1497,1559-1588,1621-1636` | `tools.call` 已返回结构化 status，但 agent 侧仍有多处 `except Exception` 兜底 |
| **重试由显式决策点授权，默认不重试**；恢复的授权判据是"可观测状态真前进了"（`replaceGeneration`） | `agent.ts:441-463`；`compaction-basic/src/index.ts:180-224` | 已有指纹式判据（`b9b6341`），但未统一为"决策对象" |
| **每个可能永久挂起的 await 都有可归属的中止来源**：工具自声明超时（`TOOL_TIMEOUT`）、流空闲看门狗（默认 300s，只在"读挂起"计时）、取消时先排空已启动调用再补合成结果 | `guard/timeout-policy/src/index.ts:51-78`；`util/timeout/src/index.ts:126-173`；`tool-calls.ts:96-99,249-260` | 物理模型是同步长计算（SMRT sweep 可达分钟级），`timeout` 目前只在 LLM 请求层；缺"工具级 deadline + 可归属超时码" |
| **致命留白（必须自己补）**：DSH 的 turn 既无步数上限也无墙钟 deadline | A 册第 4.9 节全树复核 | 我们已有预算/指纹/守卫三层兜底，反而比 DSH 更严 |

其它可直接抄的细节：`max-tokens` 终态并**丢弃被截断的 tool-call 参数**（`agent.ts:484`、`llm/src/assembler.ts:130-146`）；空响应提升为可重试错误（`llm-deepseek/src/translate.ts:132-142`）；工具结果**按模型调用顺序提交**（`tool-calls.ts:146-161`）；未知工具的"可路由拒绝"（`tools/index.ts:1363-1434`）；重复检测必须覆盖**被拒调用**（deny 与抛错都流经同一后置处理，`tools/index.ts:181-188`）。

### 7.2 C 册：计划骨架、子代理与长任务

- **计划（plan）是 log-only 持久状态**，恢复/分支后不丢，且不改工具目录以保 KV cache（`plan/plan-mode/src/index.ts:40-49,192-220`）。→ 对应我们的 plan 应进日志而非只存 `session["research"]`。
- **待办 `todo_write` 整表替换**，计数回显，杜绝部分更新造成的"清单与事实漂移"（`todo/tool-todo/src/index.ts:91-111,203-219`）。→ 我们 research plan 的 `runs/charts/targets` 可借鉴"整表替换 + 版本号"。
- **子代理终态是数据**：`stop_reason ∈ {completed, aborted, error, max_tokens, refusal}`，未知值按未完成处理；父侧把非 completed 转成工具错误但保留部分输出与诊断（`subagent/src/types.ts:252-266`、`tool-subagent/src/index.ts:207-215`）。→ Q3/Q4 这类多阶段实验可交给子代理，主代理只持句柄与结论。
- **权限只减不增**：子代理审批策略强制"从不提问"，沙箱只继承父的显式覆盖（`child-agent.ts:242-247`）。→ 我们的 `approval.ASK` 门必须在委派时显式降级，不能借子代理绕过人工审批。
- **子代理层没有自动重试**，重试留给父代理决策（它才懂语义上是否可重放）。→ 与"副作用未知不要盲目重试"同一原则。
- **工作流 runner 区分致命与每项失败**：`FatalWorkflowError`（配置错/触顶/schema 不支持）整轮失败，单项失败记为 `None` 并继续（`workflow/src/index.ts:121-148`）。→ 我们的 evaluation runner 应显式区分这两类。
- **长任务**：检查点=**副作用前刷持久且 fail-closed**（`session-checkpoint-policy/src/index.ts:52-75`）；半途中断**补合成收尾不截断**，并区分 `TOOL_OUTCOME_UNKNOWN`（提示"只有只读/幂等才可重试"）与 `TOOL_NOT_STARTED`（`core/session/src/repair.ts:104-107`）；预算**具名、可配、有默认**且超限给可执行指引（`jobs-local/src/index.ts:143-148`）；僵尸清理要**显式记录"可能已泄漏"**而不是假装清理成功（`jobs-local/src/index.ts:502-528`）。

### 7.3 规划调整（在 §5 基础上）

- P0 增补：**被拒/失败调用也走同一后置处理**（否则重复检测漏掉最该打断的循环）；**截断的 tool-call 参数一律丢弃**（我们已有 "not replayed" 测试，补齐 `max-tokens` 终态语义）。
- P0 增补：**工具级 deadline**（物理模型运行按 sweep 点数估算上限，超时返回结构化 `TOOL_TIMEOUT` 结果而不是抛异常）。
- P1 增补：plan 与 todo 采用**整表替换 + 版本号**，并把 plan 状态写入追加日志。
- P1 增补：research runner 区分**致命错误**与**单 cell 失败**，后者记 `None` 继续。
- P2 增补：Q3/Q4 类多阶段实验改为**子代理委派**（终态作为数据返回，主代理持句柄）；委派时权限只减不增。
