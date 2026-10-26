# /patched-subagent-driven-development 设计规格

> 版本 v0.2 · 2026-10-26 · 状态：上游 patch 已落地（brainstorming / writing-plans）；patched SDD skill 已创建；原 SDD 保留
> 实现：~/.dsh/skills/patched-subagent-driven-development/；备份：~/.dsh/skill-backups/2026-10-26-superpowers-patch/
> 证据：session-e3b76ed3-6ff0-4fb8-b8b7-c4ab0c0880e1（373 steps / 20.5 MB JSONL）+ 10 个子会话 + 仓库 .superpowers/sdd 工件
> 理论依据：D:\Jingdong\Literature\Papers\claud_sub-agent.md

---

## 0. 结论（TL;DR）

当前 SDD 的问题不是「subagent 用多了」，而是**用错了三件事**：用错了任务、用错了切分维度、用错了验证时点。

1. **默认不派 subagent。** 本会话 7 个任务里，implementer 实际做的是「把 plan 里的完整代码抄进文件、跑测试、写报告」。这类转录工作留在主循环，交接成本可以降到接近零。
2. **先做 plan↔spec 一致性门，再写第一行代码。** 本会话 12 条实质缺陷，全部可以在 plan 文本或 controller 的 ruling 里找到出处；**0 条由 implementer 自主引入**。per-task review 是在最贵的时点（代码已写完）发现 plan 的错。
3. **评审按 batch + 风险触发，不按 task。** 评审输入是 spec + diff，不是 brief + plan；只收 Critical/Important；Minor 不进循环、不修、不 re-review。
4. **测试是闸门，不是角色。** 基线一次、每个 batch 全量一次、聚焦测试按需；删掉「每个 commit 全量」「TDD RED/GREEN 仪式」「warnings 也算 finding」三条。
5. **硬限制做成脚本和结构化产物。** 一致性矩阵、负例探针、测试预算、等待规则都要可执行；prose 规则在证据里失效了——skill 已经写了「不要轮询」，controller 仍然调用了 23 次 list_agents。

现成的三个 review seat + 两条验证纪律能发现部分错位，但保证不了：spec reviewer 在 plan 之前，task reviewer 拿 brief 当需求，final reviewer 在最后（本会话日志里没有它的 dispatch）。保证来自可追溯矩阵 + 负例 + 端到端验收；reviewer 是第二张网。

预期收益（待第 7 节 A/B 验证）：token 降 40%–60%，wall time 降 30%–40%，全量测试 16 次 → ≤4 次，评审 finding 精确率提升，逃逸 Important 不增加。

---

## 1. 证据基线

### 1.1 运行画像

| 项 | 值 |
|---|---|
| 计划/规格 | plan 981 行、spec 365 行、brief 862 行 |
| 执行范围 | T1–T7 分 3 批（A=T1-3，B=T4-5，C=T6-7）；T8/T9 未执行（人审门） |
| 产物 | 1,246 行生产代码 + 1,560 行测试；117 个 test；11 个 v3 commit（区间共 13 个，含 2 个并行会话的依赖 commit） |
| 时间 | 14:46–16:31，约 100 分钟；spec 13:16、plan 13:33 由**同一个 controller 会话**在 80–100 分钟前写成 |
| 子代理 | 10 次 subagent + 4 次 send_message：3 implementer、3 reviewer、4 re-reviewer |
| 工件 | .superpowers/sdd 464 KB；review diff 包 7,763 行；报告 1,250 行 |

**第一层讽刺**：写 spec 和 plan 的模型，一个多小时后把 plan 里的代码交给 10 个没有这段上下文的子代理去重建。Claude 那篇文章说的正是这件事：*the model that writes the plan is also the one carrying it out, so it can change the plan mid-turn*（claud_sub-agent.md:59）。

### 1.2 成本结构

| 角色 | tokens | 占比 |
|---|---:|---:|
| 父会话（调度、轮询、裁决、修复消息） | 9.53M | 19.6% |
| implementer（3 个，含全部 fix round） | 26.97M | 55.6% |
| reviewer（3 个） | 5.31M | 10.9% |
| re-reviewer（4 个） | 6.71M | 13.8% |
| **合计** | **48.50M** | 100% |

分孩子明细（tokens / steps / 峰值上下文 / wall）：

| child | 角色 | tokens | steps | 峰值 ctx | wall |
|---|---|---:|---:|---:|---:|
| ddae3f44 | 实现 T1-3 + 2 轮修复 | 5.95M | 70 | 142k | 30.5 min |
| d08f8808 | 评审 T1-3 | 1.36M | 21 | 94k | 5.2 min |
| ca765411 | re-review T1-3 #1 | 1.45M | 23 | 85k | 4.0 min |
| f774df6d | re-review T1-3 #2 | 0.80M | 15 | 73k | 2.8 min |
| 56b272c4 | 实现 T4-5 + 修复 | 3.79M | 45 | 129k | 17.4 min |
| c1e63bc1 | 评审 T4-5 | 0.72M | 12 | 88k | 4.1 min |
| a9e8f202 | re-review T4-5 | 1.39M | 21 | 92k | 4.1 min |
| ceba8a73 | 实现 T6-7 + 修复 | **17.23M** | **100** | **293k** | **36.6 min** |
| 8fb503cd | 评审 T6-7 | 3.23M | 33 | 168k | 9.5 min |
| fdae0d9f | re-review T6-7 | 3.07M | 31 | 140k | 5.4 min |

关键事实：

- **ceba8a73 一个孩子吃掉 17.23M，占总成本 35.5%**。它的上下文峰值 293k，比父会话还大。所谓「fresh context」在 batch 太大时反而制造了更大的上下文。
- **每个子代理启动先付约 33k token** 的系统/工具/技能提示（10 个孩子约 330k），这还没算它要读的 brief、diff、报告。
- **轮询约 3.2M**：23 次 list_agents × 平均 140k/step。skill 明确禁止 sleep/轮询，controller 仍然把 list_agents 当成等待原语。
- **inbox 注入 95k 字符**：13 条 settlement（48.8k 字符）+ 13 条 agent-message（46.2k 字符），约 3–5 万 token，并在后续每一步被重复读取。评审 C 的单条 settlement 就有 12,959 字符。
- **dispatch prompt 66.9k 字符**（4.6k–9k/次），fix message 18.7k 字符。这些内容全部常驻父上下文。

### 1.3 测试画像

| 指标 | 值 |
|---|---|
| 生产代码 | 1,246 行 |
| 测试代码 | 1,560 行（测试/代码 = 1.25） |
| 新增 test 函数 | 117 个 / 313 个 assert |
| 窗口内全量 pytest | **16 次**（ddae3f44 7 次、56b272c4 4 次、ceba8a73 5 次） |
| implementer 测试类命令 | 54 次 |
| 单个 flaky test 重跑 | 5 次 + 10 次循环，共 15 次 |
| 全量测试次数目标 | ≤4 次（基线 1 + 每 batch 1 + 最终 1） |

**第二层讽刺**：Batch B 的 27 个 measure 测试里，5 个 bootstrap interval 测试全部使用相同 cell，**一个 no-op resampler 可以通过整个文件**。测试数量在涨，测试效力没有涨。这就是「over test」的准确形态：测试通胀 + 语义空洞。

### 1.4 评审产出画像

| 批次 | Critical | Important | Minor | 修复轮次 | 结果 |
|---|---:|---:|---:|---:|---|
| A（T1-3） | 0 | 2 + 1 越界 | 7 | 2 | 全部 ADDRESSED |
| B（T4-5） | 0 | 0（4 条 Minor 被 controller 提升为必修） | 8 | 1 | 全部 ADDRESSED |
| C（T6-7） | 0 | 5 | 16 | 1 | 5 条 Important 修复 |
| **合计** | **0** | **8（含越界）+ 4 提升** | **31** | **4** | — |

- 39 条 finding，**0 Critical**；12 条实质缺陷，31 条 Minor。
- 12 条实质缺陷**全部**可追溯到 plan 文本或 controller ruling：
  - I1 coverage_missing 子串匹配（plan 明确写了 "substring is deliberate"）；
  - I2 stratified_split 用 raw intent（plan 代码）；
  - R13 renderer inline 层级用错分隔符（plan 代码 vs spec §4.2，第一轮 review 没发现，re-review 的越界观察才发现，多花一轮）；
  - A1/A4/D_conf（plan 相对 spec 的遗漏）；
  - R17a-d（plan 的 bootstrap 测试同 cell、per_label_f1 返回 0.0、D_prior 漏 failure mass、bootstrap 重实现主效应）。
- 0 条 Important 是 implementer 自己引入的新设计缺陷。implementer 的角色是转录，它忠实地把 plan 的缺陷抄了进去。
- 评审+re-review 35.1 分钟（38%），实现+修复 58.1 分钟（62%）；**其中 24.3 分钟（26%）是在修 plan 本来就能修好的缺陷**。

### 1.5 五个现场

1. **14:51 转录**：T1-3 的 brief 已经包含完整代码和测试，implementer 仍然用了 70 steps、5.95M；随后 review 找出 2 个 Important，都是 plan 代码的错。
2. **15:09 / 15:19 两轮修复**：第一轮修 coverage 与 split；re-review 的「越界观察」指出 renderer 分隔符违反 spec，controller 判定 load-bearing，追加第二轮。第一轮 review 看过同一段代码，没有发现——因为它按 brief 对，而不是按 spec 对。
3. **15:49 Batch C 失控**：T6-7 的 dispatch prompt 9,027 字符、7 条 ruling；子代理 100 steps、56 次 edit、17.23M、36.6 分钟。batch 太大 + 裁决在父、实现在子，导致子代理要重建 7 个决定的意图。
4. **轮询**：14:53–16:26 之间 23 次 list_agents。skill 的 DSH note 已经写明「end your turn 就是等待」，controller 仍然每 90 秒看一次。
5. **16:13 修复 5 条 Important**：fix message 6,192 字符，12.1 分钟，之后又 5.4 分钟 re-review。这些 finding 没有一条是代码新缺陷。

---

### 1.6 现成 reviewer 的实际覆盖：为什么给不了「保证」

Superpowers kit 里其实已经有 3 个 review seat 和 2 条验证纪律：

| Seat | 何时 | 输入 | 它保证什么 | 它保证不了什么 |
|---|---|---|---|---|
| **spec-document reviewer**（brainstorming） | plan 之前 | 只有 spec | spec 完整、自洽、可规划；Seven Elements 里每条 acceptance 必须命名证据 | plan 对不对——plan 还不存在 |
| **task reviewer**（SDD） | 每个 task 之后 | brief + controller 手抄的 global constraints + report + diff | diff 是否满足 brief、局部代码质量 | spec↔plan 对齐；brief 忠实复制 plan 的错时，它没有理由打开 spec |
| **final code reviewer**（requesting-code-review） | 全部 task 之后 | description + plan/requirements + 整条 diff | 整条分支对 plan 的对齐、架构、集成 | 太晚；absence 类缺陷；一次 2,925 行 diff 的采样 |
| **verification-before-completion** | 完成声明前 | controller 自己建的 checklist | 有证据才宣称完成 | checklist 该从 spec 哪一行来，它不管 |
| **TDD** | 写代码时 | plan 给的测试 | 实现缺失时测试会失败 | 测试是否编码了 spec；语义空洞的测试照样有 RED |

五个结构性原因：

1. **权威链反了。** task reviewer 模板把 "What Was Requested" 定义为 brief；本会话的 dispatch 更是明确写 "Spec ... read only if a brief is ambiguous"。brief 是 plan 的忠实投影，plan 错了 brief 也错，reviewer 没有理由打开 spec。kit 自己还矛盾：`writing-plans/SKILL.md` 说 "the spec travels with it; executors read both"，SDD 的实际执行却把 spec 降级为歧义时才查的参考。
2. **diff 里看不到「缺失」。** reviewer 的视图是 diff；A1 的 metrics.json 缺哈希、A4 不进 verdict、D_conf 不存在、live path 没有 coverage gate——这些是 absence，不是 diff hunk。发现 absence 必须拿 spec 逐条对照，这是 checklist 的工作，不是读 diff 的工作。task reviewer 的 ⚠️ Cannot verify from diff 正是这一类，而且按设计**不阻塞**。
3. **severity 是建议，不是门。** R13 是 re-review 的 out-of-scope 观察，靠 controller 提升才进循环；Batch B 的 4 条真缺陷被标成 Minor，也靠 controller 提升。reviewer 可以「发现」，但不能「保证」。
4. **时点太晚。** final reviewer 在 10 次 dispatch、4 轮 fix 之后；本会话日志里没有它的 dispatch（final diff 包 16:35 才生成，日志 16:26 结束）。即使跑了，也是一次 2,925 行的 prose pass。
5. **采样，不是覆盖。** 365 行 spec × 981 行 plan × 7 份 brief，reviewer 读的是 diff 加 brief；它只能覆盖它想到要查的条目。

公平地说，kit 不是没有对冲规则：task reviewer 模板写了「plan-mandated 也算 Important」，final reviewer 写了「if you find issues with the plan itself, say so」。但它们只是**可选的注意**，不是**必须的覆盖**：R17a 被标成 Minor，R13 被标成 out-of-scope，A1/A4/D_conf 要等到第三批才被提起。规则存在，覆盖不存在。

还有一把现成的椅子没人坐：kit 自带 `writing-plans/plan-document-reviewer-prompt.md`（输入 plan + spec，检查 spec alignment），但 writing-plans 的 SKILL.md 从未引用它。patched 版把它接进了 Plan Review 步骤（>3 task 或任何 acceptance gate），这是一处零成本的补位。

本会话的量化：12 条实质缺陷里，R13 第一轮 review 漏掉、Batch B 的 4 条被降级为 Minor、A1/A4/D_conf 到第三批才出现。**reviewer 的检出是采样，不是覆盖；保证需要可追溯矩阵，不是另一个 prose 席位。**

**「保证」的定义**（patched 流程采用）：每个 acceptance item 都有四元组——spec 行、plan 步骤、会在违反时失败的 probe、probe 的实际输出。四者缺一，门就 FAIL。这是可审计的，不依赖 reviewer 当天的心情。

### 1.7 文章的 findings 对工作流的二次修正

| 文章 finding | 对 patched 工作流的修正 |
|---|---|
| subagent 只在三种条件下用（:17-22） | 确认 T0/T1 默认；verifier 保留，但只做 black-box verification |
| 按 context 切，不按 problem 切（:50） | batch = 接口簇；plan 的 task 列表不是执行单元；T4/T5、T5/T6 必须同 batch |
| 共享上下文、少 handoff（:43） | 转录留在主循环；brief 只给 T2；verifier 不给 plan/report，只给 spec + diff + coverage 表 |
| subagent as tool，用真实数据验证结论（:86-90） | verifier 的 verdict 只是假设；controller 必须用命令或 spec 行确认；finding 的接受/拒绝都要有证据 |
| progressive disclosure（:39-44） | SKILL.md ≤900 词（当前 832）；重内容进 references/；verifier prompt ≤50 行 |
| 硬限制进 tools（:63） | conformance-probe、test-budget、poll counter 脚本化 |
| 模型更强 → harness 可以更薄（:45） | **有保留**：文章证据是 Opus 4.5+；本会话跑 deepseek-flash，23 次轮询、100 步孩子、15 次重跑说明结构还不能撤。只撤仪式（RED/GREEN、per-task review），不撤 gate（traceability、E2E） |
| task-completion eval（:69-74） | **新增 P5 端到端验收**：dry run + live path on fixture；按 acceptance item 记 pass/fail，而不是「suite green」 |
| 看哪些 task flipped，每个 eval 跑多次（:100-102） | 评估按 item 记 flip，跑 ≥2 次；不只看总分 |
| 先折一个 subagent，比较后再折下一个（:133） | 落地先在本 plan 上 pilot，不一次重写整个 skill |
| 中央团队拥有端到端质量（:48, :105） | controller 拥有 conformance + acceptance；不能把「质量」外包给 reviewer seat |

文章对这份 spec 影响最大的一条是 **task-completion eval**：本会话的 per-task review 都在评 diff，但 live path 的聚合从未端到端跑过（Batch C 的 "Cannot verify" 自己写了这一点）。patched 的 P5 因此必须运行产物，而不只是跑测试。

---

## 2. 诊断：SDD 与文章原则的五处冲突

### D1 任务选择错误：把「转录」外包

文章给出保留 subagent 的三个条件（claud_sub-agent.md:17-22）：

> a single agent loop hits measurable performance degradation from context bloat, or multiple tasks need to be tackled in parallel with fresh context windows that can be discarded once the task is done, or a single agent struggles to select appropriate tools or there are conflicting instructions.

本会话的 T1–T7 三条都不满足：不并行、不 bloated、无工具冲突，任务本身是「按 plan 抄代码」。**subagent 在这里买到的是隔离，付出的却是 4–5 次有损交接。**

### D2 切分维度错误：按问题类型切，而不是按 context 切

文章（claud_sub-agent.md:50）：

> Decompose boundaries effectively by dividing by context: give each subagent a piece of work that needs little from the rest of the system and have it hand back a compact result. When agents are split by problem type, they engage in a "telephone game", passing information back and forth with each handoff degrading fidelity.

SDD 按 plan task 切：spec / renderer / split / harness / measure / report / CLI。但 plan 自己的 pre-flight 表证明它们**每一个都共享接口**：T4→T5 的 to_pairs（F1 冲突）、T5→T6 的 metrics dict、T2→T5 的 CELLS。controller 只能用「batch」打补丁，说明切分维度本身是错的。

### D3 评审时点错误：在转录后评审 plan 的缺陷

文章（claud_sub-agent.md:43）：

> Shared context produces better answers... It also means fewer context windows and fewer lossy handoffs.

12 条实质缺陷全部是 plan 缺陷。per-task review 在代码写完、测试跑完、报告写完、上下文重建完之后，才发现 plan 的错——这是**最贵的发现时点**。正确时点是写第一行代码之前：spec ↔ plan 的一致性门，成本是一两小时的主循环，而不是 4 轮 fix + 4 次 re-review。

### D4 测试通胀：测试变成角色和仪式

- 「Run the repo test suite before and after each task」被写进 Global Constraints，并被复制进每一次 dispatch → 16 次全量。
- 「TDD: write the failing test first... report needs RED/GREEN evidence per task」→ 对「plan 已给出完整测试」的转录任务毫无意义。
- 「Warnings or other noise in the reported test output are findings」→ 制造噪音 finding。
- 「Coverage-could-be-broader is Minor」→ 31 条 Minor 的大部分来源。
- 结果：测试行数 > 生产行数，但 batch B 的 5 个 interval 测试语义空洞。**测试的度量是「能不能失败」，不是「写了多少」。**

### D5 harness 反向适配：prose 规则、轮询、失效的 model 路由

- **prose 规则失效**：skill 写了「不要 sleep/轮询」，controller 仍然 23 次 list_agents。文章说 *Hard limits (validation, approval gates) ... move into the tools*（claud_sub-agent.md:63）。等待必须由 harness 的通知机制承担，规则要变成「0 次轮询」的可检查指标。
- **model 路由是死代码**：skill 有整节 Model Selection，但 DSH 的 subagent binding 不暴露 model 参数（ledger 自己记了这条限制）。所有孩子都跑会话模型，成本控制只剩「少派、派小、少轮次」。
- **handoff 体积失控**：reviewer 的最终消息就是完整报告（12,959 字符），settlement 再复制一遍；fix message 再粘贴 6,192 字符。文章说 subagent 应该 *hand back a compact result*。
- **没有 eval**：整个会话没有测量「folded vs kept」。文章的最后一条建议是 *measure, change one thing at a time, and keep what holds up*（claud_sub-agent.md:131）。

---

## 3. 设计原则

| # | 原则 | 可执行含义 |
|---|---|---|
| P1 | **能留在主循环的，不外包** | 默认主循环；只有 T2/T3 才派 subagent |
| P2 | **subagent 只买两种东西**：隔离的 context、并行的探索 | 转录、单文件修改、串行集成一律不派 |
| P3 | **先验证 plan 与 spec 一致，再写代码** | P1 一致性门是硬门；不过门不 dispatch |
| P4 | **测试是闸门，不是角色** | 每个 gate 必须有负例；测试次数有预算 |
| P5 | **交接只传文件路径 + 结构化短消息** | prompt ≤6k 字符；report 落盘；review 落盘；父不粘贴 |
| P6 | **硬限制做成脚本/工具** | 一致性矩阵、负例探针、测试预算、轮询计数都由脚本产出 |

---

## 4. 规格

### 4.1 适用与不适用

**适用**：当前会话执行一份已写好的实现 plan，任务 ≥2 个；plan 可能包含完整代码；需要 review/验证；需要断点恢复。

**不适用**：
- 单一 task 或 <100 行的修改 → 直接做。
- 纯探索/调研 → 用并行 researcher（T3），不要走 SDD。
- 需要人审门的操作（发布、merge、付费实验）→ 停下来问。

### 4.2 执行分级（核心决策表）

| Tier | 触发条件（满足任一） | 执行者 | 评审 | 本会话对应 |
|---|---|---|---|---|
| **T0 转录** | plan/brief 的代码块已完整给出目标文件内容；无新设计决策 | 主循环（write/edit） | 无；由 P1 门 + 测试兜底 | T1、T2、T3 的大部分；T6 的报告渲染部分 |
| **T1 主循环实现** | ≤2 文件、≤30 步；接口已定；需要局部判断 | 主循环 | 仅风险触发 | T4/T5 的 F1 修正、T7 的 ruling 落地 |
| **T2 委派实现** | >3 文件或 >400 LoC；或需要长等待/长命令；且 context 确实可分离（自有文件/数据、无共享接口） | 1 个 implementer subagent | 每 batch 1 次 verifier（仅风险触发） | 本会话的 T6-7 看似 T2，但裁决在父、batch 超限，正确做法是拆成父执行的 T1/T0，而不是派 100 steps 的孩子 |
| **T3 并行探索** | 任务彼此独立、结果可丢弃、可并行 | N 个 subagent 并行（≤4） | 聚合检查 | 10-23 的 4 篇论文阅读 |

伪代码：

~~~text
if plan_block_is_complete and no_new_decision:      T0
elif files <= 2 and steps <= 30 and no_long_wait:   T1
elif context_separable and (files > 3 or loc > 400 or long_wait): T2
elif independent and disposable:                    T3
else:                                               T1   # 默认回主循环
~~~

**反直觉规则**：只要 dispatch prompt 里出现「Ruling: ...」这类父级裁决，就说明决定是在父上下文做的 → 由父实现（T1），或先把裁决写进 plan/brief 文件再走 T0。**不要把裁决翻译成 9k 字符的 prompt 让子代理重建意图**（本会话 Batch C 的 17.23M 就是这么来的）。

### 4.3 执行单元：batch，不是 task

- 一个 batch = 一个接口簇，最多 3 个生产文件 / 400 changed LoC（含测试）/ 3 个 plan task；任一超限就按接口拆。
- 同一接口的 producer 与 consumer 必须同 batch（T4→T5 的 to_pairs、T5→T6 的 metrics dict）。
- 超过上限 → 按接口再切，不按行数切。
- batch 内只允许 1 个 implementer；不同 batch 不并行实现（除非文件集完全不相交）。

### 4.4 流程

~~~text
P0 工作区 + 账本（复用）
  ↓
P1 一致性门（主循环，无 subagent）  ← 新增，硬门
  ↓
P2 按 Tier 执行（默认 T0/T1；必要时 T2）
  ↓
P3 评审（仅 T2 或风险触发；每 batch 一次）
  ↓
P4 修复（≤2 轮；仅 Critical/Important）
  ↓
P5 最终门（验收测试 + 一致性矩阵 + 联合 diff）
  ↓
finishing-a-development-branch
~~~

### 4.5 P1：Plan–Spec 一致性门

**输入**：spec（权威）、plan、briefs、ledger。
**输出**：conformance.md，一行一个 spec 项，全部 PASS 或 RULED 才允许进入 P2。
**时限**：约 1,000 行 plan 用 30 分钟；超时就把 C2 探针交给 verifier，而不是把实现交给 implementer。

五项检查：

| 检查 | 做什么 | 本会话会抓到什么 |
|---|---|---|
| **C1 可追溯** | spec 的每条 MUST/验收项/阈值/精确字符串 → plan 的步骤 + 测试；缺一即 finding | A1 的 metrics.json 哈希、A4 的 gating、D_conf |
| **C2 负例探针** | 对每个 gate/格式/阈值，现在就跑一个负例：删 token、改阈值、用同 cell 的 vacuous double | I1 子串匹配、R17a 空洞 bootstrap、R13 分隔符 |
| **C3 接口** | producer 签名 vs consumer 调用（复用现有 pre-flight 表） | F1 to_pairs、T5→T6 metrics dict |
| **C4 裁决一致** | 每条 controller ruling 对回 spec；与 spec 冲突的重新裁决 | R2 vs R17b（zero-support label） |
| **C5 环境** | plan 引用的精确路径/长度/数据文件存在；人审门标注 | 32,793 字符 prompt、data/intent_dataset.jsonl 缺失 |

C2 的具体探针（本会话可直接复用）：

1. 从 render 里删掉 music 标签行 → coverage_missing 必须非空。（抓 I1）
2. 用 no-op resampler 跑 bootstrap → interval 测试必须失败。（抓 R17a）
3. 把 inline 层级的「：」改成「=」→ spec §4.2 检查必须失败。（抓 R13）
4. 省略 --s2-spec → dry run 必须 warn/refuse。（抓 I4）
5. metrics.json 必须包含全部哈希与 A4 证据。（抓 A1）

conformance.md 行格式：

~~~text
| id | spec line | plan line | check | evidence (command/output) | verdict |
| A1-3 | design.md:220 | plan:268 | C2-probe | pytest ...; metrics.json lacks hashes | FAIL -> R18 |
~~~

**上游依赖**：如果 plan 带 Spec coverage 表（acceptance id → task → test），C1 只验证这张表；没有就先补表。补表 10 分钟，补在代码后是 1–2 轮 fix。

**成本论证**：一条 C2 探针是一条 bash 命令；漏掉它的代价是 1–2 轮 fix + re-review（本会话 24.3 分钟、6.71M re-review token）。

### 4.6 测试政策

| 时点 | 允许 | 次数上限 |
|---|---|---:|
| plan 开始 | 一次全量 baseline（记录 commit + 结果） | 1 / plan |
| 每个 task | plan 指定的聚焦测试 | ≤2 / task |
| batch 结束 | 一次全量 | 1 / batch |
| 修复轮 | 覆盖修复点的测试 + 相关文件 | 1 / round |
| 最终 | 全量 + 验收脚本 | 1 |
| flaky | 同一条测试重跑 | ≤1；仍 flaky 记为 bug，继续 |

规则：

- T0 转录**不需要** RED/GREEN 仪式；plan 里的测试代码就是 RED 产物，跑一次 GREEN 即可。
- 新测试只在「修复改变了未被覆盖的行为」时添加；每条 finding ≤1 个新测试。
- 禁止以「覆盖率可以更广」「test output 不够 pristine」「测试风格」开 finding。
- 每个 gate 测试必须有负例；负例在 C2 已跑过，不重复。
- 测试的验收标准是「删掉实现后它会失败」，不是行数、不是数量。

### 4.7 评审政策

**何时评**：只有 T2 batch，或命中风险触发（auth/权限、金钱、删除数据、并发、公共 API、验收 gate、>300 LoC 新逻辑）。T0/T1 不评，靠 P1 门 + 测试 + 最终门。

**输入**：spec（权威）、联合 diff 文件、conformance.md（含 coverage 表）、implementer 的报告文件。**不给 brief/plan**——plan 是被怀疑对象，不是评审依据。

**定位**：verifier 是第二张网，不是保证。它负责找矩阵和探针没预见到的东西；它的每一条 verdict 都要由 controller 用命令或 spec 行复核后才生效（文章的 *verify the conclusion against real data*）。

**输出预算**：最多 10 条；只收 Critical / Important；Minor 一行一条进 deferred.md，不修。

**严重度定义**：

- **Critical**：错误输出、数据丢失、安全问题。
- **Important**：spec 验收项未满足；会让后续 task 建立在错误上；会浪费一次 >1 小时的运行。
- **Minor**：风格、文档、覆盖率、健壮性——不影响验收。

**输出契约**：完整 review.md 落盘；消息 ≤20 行（verdict、finding id 列表、文件路径）。评审者可以跑 ≤1 条聚焦命令验证一个具名疑点；不重跑测试；不评 style；不要求补测试。

**plan-mandated**：仍然报告，但 controller 对回 spec 裁决；spec 同意 plan 的，不是缺陷。

**提升规则**：controller 可以把一条与验收项直接相关的 Minor 提升为 Important（必须写明 spec 行）。Batch B 的 4 条「Minor」就是这样变成必修的；这条规则把那次例外固化成流程。

### 4.8 修复循环

- 只修 controller 确认的 Critical/Important。
- **Round 1**：resume 同一个 implementer（T2）或主循环（T0/T1）。fix message = findings 文件路径 + 每条一行裁决，≤1.5k 字符。
- **Round 2**：fresh implementer（T2；如有 model 路由则升一档）。仍不收敛 → 第 3 轮禁止，controller 裁决（park 或改计划）。
- **re-review 条件**：修复触及验收 gate / spec 行才 re-review；否则 controller 重跑 C2 探针验证。
- Minor 永不进循环；deferred.md 在最终门一次性 triage（只 triage 与验收相关的）。

### 4.9 上下文契约

| 产物 | 位置 | 消息里返回 |
|---|---|---|
| implementer 报告 | report.md（任意长度） | ≤15 行：status、commits、一行测试、concerns、路径 |
| reviewer 报告 | review.md（任意长度） | ≤20 行：verdict、finding id、路径 |
| 裁决 | decisions.md 或 conformance.md | 只传路径 |
| diff | review-package 生成的文件 | 只传路径 |

- dispatch prompt ≤6k 字符；裁决超过 1k 字符 → 写 decisions.md。
- 禁止粘贴前序 task 的总结、整份 plan、整份 brief。
- 父会话不粘贴 findings；传文件路径。
- settlement 只应带短消息；长报告落盘。

**三上下文模型（回应「brief-only 省 context」）**

| 角色 | 读什么 | 不读什么 | 为什么 |
|---|---|---|---|
| controller | spec + plan + ledger + conformance | — | 它拥有对齐，不能外包 |
| implementer（仅 T2） | brief + 接口 + **binding spec slice** | 完整 spec、完整 plan | 上下文保持小；它只负责执行 |
| verifier | **完整 spec** + diff + coverage 表 | brief、plan、report | 独立检查 absence；不受 plan 的框架影响 |

brief 的目标不是「不含 spec」，而是「只含本 task 的规范性 spec 行」。推荐 schema：

~~~text
## Task
## Interfaces (exact signatures)
## Binding spec lines (verbatim, with line refs)   ← 5–15 行
## Evidence this task must produce (command + expected)
## Out of scope for this task
## Report contract
~~~

- 切片必须是**规范性**的（MUST、验收项、阈值、精确字符串），不是设计 rationale；365 行 spec 里与本 task 相关的通常只有 5–15 行。
- 切片从 spec 的 acceptance id 机械抽取（依赖 5.1 的 coverage 表）；不要由 plan 作者手选，否则会复制他的误解。
- brief 带 spec hash；spec 变了，brief 失效，重新过 P1。
- **数字**：本会话 implementer brief 4.6–9k 字符，spec 365 行约 15k 字符。每个 implementer 多读 2k token 的切片，3 个也只有 6k token；而 4 轮 review/fix 是 12M token。比例约 1:2000。
- **真正的 bug 不是 implementer 读得少，是 reviewer 也读得少**：brief 同时发给了 implementer 和 task reviewer，省下的 2k token 让两个席位都失去了权威。implementer 可以 brief-only；verifier 不行。

### 4.10 等待、预算与停止

**等待**：dispatch 之后，父只能做「不依赖该结果」的本地工作，或者**结束 turn**。`list_agents` 在等待期间 0 次；收到 settlement 后允许 1 次 reconcile。任何等待期轮询都是流程缺陷，记入 ledger。

**预算**：

| 对象 | 软上限 | 硬上限 / 动作 |
|---|---|---|
| 单个 child | 30 steps | 45 steps 必须报告 partial + blocker |
| batch | 400 changed LoC / 3 个生产文件 | 超限拆 batch |
| child 上下文 | 150k | 超限拆 batch（本会话峰值 293k） |
| 每个 plan | ≤5 次 dispatch（含 verifier）、≤2 轮 fix | 超限停下来裁决 |
| 测试 | 见 4.6 | 超限视为流程缺陷 |

**停止条件**（原有 4 条 + 新增 2 条）：
1. 不可逆/破坏性操作；
2. 安全敏感操作；
3. worktree 外的副作用（merge/push/publish）；
4. plan 坏到每条路都是猜；
5. **spec 不可达/自相矛盾**（一致性门无法 PASS，且裁决也没有依据）；
6. **预算耗尽且没有可裁决的下一步**。

### 4.11 账本与恢复

保留现有 ledger 的身份行和恢复能力，但行格式压缩：

~~~text
# SDD ledger — plan: <path> · spec: <path>
B1 base=<sha> -> head=<sha> tests=<cmd/result> review=<verdict> findings=<ids>
R18 metrics.json = {...} — why — cost if wrong
D1 <minor one-liner>  (deferred)
~~~

- 每条 finding 有稳定 id（I1、M3），fix/review 都引用 id。
- 裁决一行一条；长论证放 conformance.md。
- 恢复时先读 ledger，再 `git log`，不重新 dispatch 已完成的 batch。

### 4.12 最终门

1. 端到端验收：跑 plan 的 **Definition of Done**——acceptance 证据 + E2E 命令 on fixture（或最小真实输入）+ 全量一次 + 无 open Critical/Important；只有单测 green 不算完成。
2. 跑全量测试（一次）。
3. 跑 conformance.md 的完整矩阵；每个验收项 PASS。
4. 只有存在 T2/风险 batch 时才做联合 diff review（最强模型，一次）。
5. 残余 Important → 报告给人，不做第二波 fix。
6. 清理 workspace；收集所有 Ruling 行。

### 4.13 SKILL.md 形态

- SKILL.md ≤900 词（当前 832），只放：触发条件、决策表、6 条硬规则、流程指针。
- 重内容放 references/：conformance-gate.md、testing-policy.md、review-policy.md、cost-model.md。
- 模板放 templates/：implementer.md、verifier.md、researcher.md。
- 脚本放 scripts/：sdd-workspace、task-brief（仅 T2 用）、review-package、conformance-probe。
- description 只写「何时用」，不写流程（writing-skills 的 SDO 规则）。

---

## 5. 与现 SKILL.md 的逐节 diff

| 现章节 | 处置 | 理由 |
|---|---|---|
| Why subagents / Core principle | **改写** | 「fresh subagent per task」改为「default main loop; subagent 只买隔离/并行」 |
| When to Use 流程图 | **替换** | 换成 4.2 的 Tier 决策表 |
| The Process 流程图 | **替换** | 换成 4.4 的六阶段 |
| Setup / ledger | **保留** | 恢复能力是这版 skill 最有价值的部分 |
| Pre-flight scan | **升级为 P1 门** | 加 C1/C2/C4/C5；输出 conformance.md |
| Model Selection | **删除** | DSH 不暴露 model 参数；改为「成本 = dispatch 数 × context × 轮次」 |
| Batch small same-shape work | **升级为默认** | 不是例外，是执行单元 |
| Dispatch implementer | **收窄** | 只 T2 用；T0/T1 主循环 |
| Handle the report | **保留** | 四种 status 仍然适用 |
| Review the task | **改为按 batch + 风险** | 输入改 spec；输出改文件；只收 C/I |
| Fix loop 5 rounds | **改为 ≤2 轮** | 本会话 4 轮里 3 轮是 plan 缺陷；第 2 轮后应裁决 |
| Complete the task | **改为 batch 完成** | 与执行单元一致 |
| Final Review | **保留但瘦身** | 联合 diff + 验收矩阵；不做第二波 |
| Common Rationalizations | **重写** | 新失败模式：转录 FOMO、review everything、test more |
| Example Workflow | **重写** | 用 T0/T1 为主的例子 |

---

### 5.1 上游 skill 的最小改动（推荐，但不属于本 skill 的范围）

| 上游 | 改动 | 为什么 |
|---|---|---|
| **writing-plans** | task 边界按 context 切，不按 "a fresh reviewer's gate"；plan header 增加 Spec coverage 表（A1 → Task N → test/probe） | 现行 Task Right-Sizing 明确按 reviewer gate 切任务，与文章的 context 切分冲突；没有 coverage 表，P1 每次都要重新推导 |
| **brainstorming** | spec 的 acceptance item 必须有稳定 id（A1..An）；spec reviewer 已经要求每条命名 evidence，只补 id | P1、plan、review 要引用同一个 id，否则矩阵对不上 |
| **verification-before-completion** | 不改；controller 用它建 line-by-line checklist，输入是 conformance.md | 它已经要求 "Requirements met = line-by-line checklist"，SDD 没有实例化 |
| **test-driven-development** | 语义 RED：no-op 实现必须让测试失败，不只是 ModuleNotFoundError | 抓 R17a 这类空洞测试；这正是 TDD 的核心原则 |

### 5.2 brainstorming / writing-plans 的具体改造

| # | 位置 | 现状 | 改动 |
|---|---|---|---|
| P0 | writing-plans 的 plan reviewer | prompt 存在，但 SKILL.md 从未引用 | 接进 Plan Review（>3 task 或任何 acceptance gate），输入 plan + spec + coverage 表 |
| B1 | brainstorming 的 spec | acceptance 是 prose，ID 和证据命令靠自觉 | 每条 acceptance 给稳定 ID、evidence command、失败条件；spec reviewer 输出 ID 清单 |
| B2 | brainstorming 的 handoff | spec 批准后直接写 plan | 加 "For the plan author" 段：必须覆盖的 ID、阈值、禁止事项 |
| B4 | brainstorming 的 user review gate | 要求人类读完整 spec | 改成 approval brief：acceptance 表 + 决策 + out-of-scope + 机械验证说明；人类批准合同，不批准 prose |
| B3 | brainstorming 的 spec reviewer | 只审 spec，plan 之前 | 保持；Seven Elements 已经够用，不要扩成 plan reviewer |
| P1 | writing-plans 的 Task Right-Sizing | 按 "worth a fresh reviewer's gate" 切 | 按 context 切：需要另一 task 的代码才能工作 → 同一 task |
| P2 | plan header | 只有 Spec path | 加 Spec hash、Coverage（A1–A7）、Task type（apply/build） |
| P3 | plan self-review | "skim each section" 人工 | 生成 coverage 表；每个 gate 写一个「会失败的负例」 |
| P4 | Global Constraints | 手抄 spec | 带 spec 行号，机械抽取 |
| P5 | 每个 task 的 TDD 步骤 | 固定 5 步 RED/GREEN | apply 类型改成 apply → run → commit；build 类型保留 TDD |
| P6 | Execution Handoff | 默认推荐 SDD | 按 Tier 推荐：apply/≤3 task → inline；context 可分离 → T2；否则 patched |
| P7 | 接口块 | 只有签名 | 加 consumer test：谁调用、什么形状、失败会怎样 |
| P8 | 测试 | 无预算 | 每个 acceptance 行为一个测试；不为转录写测试；每个 gate 一个负例 |
| P9 | writing-plans 的 Done | 只有「跑测试」 | 加 Definition of Done：acceptance 证据 + E2E 命令/fixture + human-gated deferral |
| P10 | writing-plans 的 spec 输入 | 可以从 Draft spec 直接写 plan | 加 Spec Freeze Gate：Approved + 完整 acceptance 表 + 无 TBD；记录 hash；spec 变更后重过门 |
| B5 | brainstorming 的 spec 状态 | 批准后仍是 Draft | 把 Approved + hash 写进 spec；plan 只从 Approved spec 开始 |

其中 P1/P2/P3 是 P1 一致性门的前置条件。不做的话，patched SDD 每次都要从 365 行 spec 重新推导矩阵；做了的话，门只是验证一张已经存在的表。


---

## 6. 文件布局（落地时）

~~~text
skills/patched-subagent-driven-development/
  SKILL.md                      # ≤900 词（当前 832）
  references/
    decision-table.md           # Tier + 触发条件
    conformance-gate.md         # C1-C5 + 探针模板
    testing-policy.md           # 预算表 + 反例
    review-policy.md            # 严重度 + 输出契约
    cost-model.md               # 本会话基线 + 预算
  templates/
    implementer.md              # ≤60 行（只 T2）
    verifier.md                 # ≤50 行（只 spec + diff）
    researcher.md               # ≤30 行（T3）
  scripts/
    sdd-workspace               # 复用
    task-brief                  # 复用（仅 T2）
    review-package              # 复用
    conformance-probe           # 新增：跑 C2 负例，输出 JSON
~~~

SKILL.md 骨架：

~~~yaml
---
name: patched-subagent-driven-development
description: Use when executing a written implementation plan with two or more tasks in the current session, especially when the plan already contains code or when the previous run's review and test cost outweighed the implementation.
---
~~~

正文只保留：决策表、P1 门、测试预算、评审触发、等待规则、文件契约。其余全部指向 references/。

---

## 7. 评估方案

### 7.1 基线

本会话即基线：48.50M token、约 100 分钟、10 次 dispatch、16 次全量测试、39 条 finding、12 条实质缺陷、0 Critical。

### 7.2 回放集（暂缓）

用户判断 v3 回放太重，本阶段不执行。保留为未来评估方案：选 8–10 份历史 plan+spec 对（含本会话），在全新会话里分别用原 SDD 和 patched 跑。

| 指标 | 目标 |
|---|---|
| token | -40% 以上 |
| wall time | -30% 以上 |
| dispatch 数 | -50% 以上 |
| 全量测试 | ≤4 次 |
| 轮询次数 | 0 |
| 评审 finding 精确率（确认/报告） | ≥60% |
| 逃逸 Important（最终门后 7 天内发现） | 不高于基线 |
| spec 项在 P1 门的覆盖率 | 100% |
| acceptance item 级 flip | 逐项 PASS/FAIL，记录哪一项翻转；不只看 suite green |
| 每个回放重复次数 | ≥2 次，报告中位数与翻转项 |

### 7.3 压力场景（writing-skills 的 RED/GREEN）

1. plan 含完整代码：基线 agent 会派 transcriber；patched 必须不派。
2. reviewer 报 12 条 Minor：基线 agent 可能修；patched 必须只记 deferred。
3. child 长时间运行：基线 agent 会 list_agents；patched 必须 0 次。
4. plan 与 spec 冲突：基线在 2 轮 fix 后才发现；patched 必须在 P1 门发现。
5. 测试 flaky：基线 15 次重跑；patched 必须 ≤2 次并记录。

### 7.4 判定

只有同时满足「token/wall 达标 + 逃逸 Important 不增加 + 压力场景 5/5」才把原 skill 标记为 deprecated；否则保留双 skill，patched 只作为默认入口。

---

## 8. 风险与反例

| 风险 | 缓解 |
|---|---|
| P1 门自己变成成本黑洞 | 30 分钟时限；C2 用脚本；超时转 verifier |
| 取消 per-task review 导致新缺陷逃逸 | 风险触发 + 最终验收矩阵；本会话证据显示 per-task review 抓的是 plan 缺陷 |
| T0 直接抄 plan 代码，抄进坏代码 | C2 负例必须在抄之前跑；测试失败即回 T1 |
| batch 太大重演 ceba8a73 | 400 LoC / 3 个生产文件 / 150k context 三个上限 |
| 团队肌肉记忆仍然派 per-task | 把「dispatch 数」写进 eval；超过预算即失败 |
| 原 skill 仍有适用场景 | 保留原 SDD 给 T2/T3；patched 是默认入口，不删除原技能 |

---

## 9. 落地状态与下一步

1. **方向**：已按「默认主循环、subagent 只用于 T2/T3」实现。
2. **并存**：已实现为并存——原 subagent-driven-development 未改动，patched 是新 skill。
3. **下一步**：pilot 暂缓（用户判断 v3 回放太重）。先用 gate-check 的合成 fixture 做轻量 smoke test；真实 A/B 留到下一次有合适 plan 时再做。

---

## 10. 还必须问/考虑的问题

1. **谁拥有 spec？** 同一个 agent 写 spec、plan、code 时，唯一的独立检查是 verifier。brainstorming 有 spec 的人工 review gate，但本会话是否真的逐条看过 A1–A7？如果没有，P1 门就是唯一防线。
2. **phase 的 done 是什么？** 已定：plan 的 Definition of Done（acceptance 证据 + E2E 命令/fixture + 全量一次 + 无 open C/I）；P5 按它验收，单测 green 不算完成。
3. **哪些 ruling 必须人类批准？** 已定：consequential ruling——改 acceptance criterion、threshold、analysis definition 或 scope 时停下来问；其余 controller 裁决并记入 ledger。
4. **spec 变更怎么办？** 已定：Spec Freeze Gate + spec hash；spec 变更后受影响的 acceptance 行与 task 重新过 P1，不允许平行修改后继续。
5. **预算按模型校准。** deepseek-flash 的 30 steps 和 Opus 的 30 steps 不是一回事；换模型时，Tier 阈值、prompt 上限、上下文上限都要重测。
6. **人类审批成本。** 建议只保留三个人类门：spec 批准、consequential ruling、最终验收；其余自动化。门太多会变成橡皮图章。
7. **是否愿意改 harness？** 如果 DSH 的 subagent 增加 model / wait / token budget 参数，patched 可以用硬限制；不加，只能靠 end-turn + prose，轮询仍可能复发。
8. **eval 谁跑、多久一次？** 暂缓：用户判断 v3 回放太重。保留为未来标准——每次架构变更跑 2–3 个历史 plan，季度复跑一次；本阶段只保留 gate-check 的合成 fixture smoke test。

---

## 附：本规格不做什么

- 不修改 DSH harness（不给 subagent 加 model 参数、不改通知机制）。
- 上游 patch 已按 5.1 / 5.2 落地；原 skill 保留，备份在 ~/.dsh/skill-backups/2026-10-26-superpowers-patch/。
- patched SDD skill 已实现于 ~/.dsh/skills/patched-subagent-driven-development/。
- 不把本会话的临时分析文件写进你的仓库；分析脚本在 D:\Personal_project\side-tasks\.analysis\，可随时删除。
