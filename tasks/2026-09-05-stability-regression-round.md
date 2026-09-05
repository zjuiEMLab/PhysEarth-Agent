# PhysEarth-Agent 科研工作流稳定性回归记录（2026-09-05 第二轮）

> 驱动方式：`evaluation/runners/reproduction_eval.py`（无头驱动完整科研状态机：读文献 → research_plan → 计划人审(模拟) → 伪数据布局 → 正式执行 → Figure QA → 最终报告）
> 模型：qwen-turbo（阿里云 DashScope，OpenAI-compatible 端点）
> 本轮相关提交：`d682b40`（preserve-authored plan 修复）、`b9b6341`（gate 指纹去重 + 前端空帧）、`13f05fc`（Q4 全点计划密度响应恢复）
> 原始 record/图件保存在本地 `_state/repro-regression-2026-09-05/`（gitignored）。之所以不覆盖
> `evaluation/results/reproduction` 归档：dimension-D 对比要求同 task/prompt/build 的 ≥2 个模型记录，
> 新记录的 build（本轮 HEAD）与归档里 qwen-max/qwen-plus 的旧 build 不同，混入会污染已提交的 LLM 稳健性报表。

## 结果摘要

| 用例 | 修复前（同轮工作区） | 修复后（当前 HEAD） |
|---|---|---|
| Q3 SMRT vs MEMLS-IBA | 报告期最不稳定；历史多次 `STOPPED figure_required` / 无进展 | **完成**：`phase=completed`，3 张正式图，108 model calls / 67 tool calls；最终报告逐图解释 IBA vs IBA-original 的 TB 相关与能力限制 |
| Q4 微结构等效性 | 8 个 turn 耗尽（`evaluation_turn_limit`），0 图，~3.07M tokens；模型反复提交“单点 TB runs + x=microstructure_model 分类图”，propose 反复拒绝、无进展循环 | **完成**：`phase=completed`，1 张正式图，50 model calls / 38 tool calls，~1.12M tokens；成功 runs 中两个候选微结构被提升为 density sweep |

合计成功率（本次 2 cell 采样）由 1/2 → 2/2；token 总量显著下降（第二次 Q4 单轮约 1.12M）。

## 失败根因（修复前 Q4）

1. **分类轴图契约**：注册表绘图只允许数值扫描轴；`x=microstructure_model` 且 runs 均为单点时，
   propose 稳定返回 “no planned run produces tb_v over x=microstructure_model”。
2. **同构重复提交**：模型在收到结构化错误后仍重发近似相同的 plan（工具层每 turn 5 次上限 + runner
   每 turn 重置导致跨 turn 重复），浪费约 3M tokens。
3. 附带发现：qwen-turbo 的 tool JSON 闭合失败（本轮 6 次 `tool_arguments_invalid`）与部分参数名错误
   （`ssa`/`specific_surface_area_m2_kg` 不是 smrt 注册参数）说明弱模型在复杂 research_plan 上的
   序列化方差，demo 推荐 qwen-plus 或更强模型。

## 修复内容（`13f05fc`）

- `reproduction._repair_q4`：当 Q4 计划全部 tb/sigma 主运行都是单点（无扫描轴）且存在图表时，把
  这些运行提升为**围绕各自作者密度 ±50% 的共享 density sweep**（裁剪到注册边界 1–917 kg m⁻³，
  每段 ≥6 点、下限 12 点），作为 auditable repair 进入人审卡片；SHS inversion baseline 保持标量。
- 随后 propose 的通用 `_repair_chart_axes` 把分类 x 归一为唯一数值轴 density，图表可执行。
- 已有 sweep（radius/corr/density 等）的 Q4 计划完全不被触碰（新增回归测试锁定两侧语义）。
- 全量测试 312 passed / 1 skipped；Tier 0 不变。

## 本轮其它稳定性改动（本回合）

- `b9b6341`：research gate（formal_model_required / figure_required）以“状态指纹 + 进度标记”判定
  无进展循环：同指纹且无新 run/figure 时一次纠正轮后即停并输出结构化 stop（phase/plan_version/
  fingerprint/repeats/成功 run 列表）；有真实进展自动重置计数，不误伤多图/逐 run 恢复。
  前端：纠正轮清空草稿时保留最后非空文本，空帧不再闪烁 Conversation（新增 UI 测试）。
- `d682b40`：propose 期 Q1 repair 采用 preserve-authored 模式（只修结构、不覆盖显式标量），
  论文差异以非阻塞 `paper_context_difference` 警告进入人审。

## 后续建议

1. dimension-D 归一到同一 build 的三模型矩阵（qwen-max/qwen-plus/qwen-turbo × Q1–Q4）再入库，
   需要较多 token 配额，建议分日执行。
2. 针对 `ssa` 等论文参数别名：可在 parameter_mapping/paper_conditions 层保留语境，但 run 参数需
   映射到已注册密度/半径/相关长度公式（需文献公式来源），避免弱模型直接写非法参数。
3. Q3/Q4 在浏览器端（人工审批 + qwen-plus）再各跑 2–3 次，评估 LLM 输出方差。
