---
name: writing-docs
description: Use when writing or editing documentation, design docs, specs, plans, READMEs, reports, ADRs, or knowledge notes — especially when a reader with limited context must find the conclusion, the evidence, and the boundary without asking.
---

# 写文档（Writing Docs）

## 0. 唯一判据

每一份文档只对**一个主读者**写。主读者只读前 15 行，就能回答：**这是什么、结论是什么、证据在哪、什么不在范围内。**

做不到，就是结构没写对，不是内容不够多。

第二个读者（总监 / 新人 / 外部）要另一份时，从同一份元数据源渲染另一个版本（见 §5）。

## 1. 先判类型，再动笔（kb 类型）

文件管理**唯一遵循 `knowledge-base` skill**（**REQUIRED SUB-SKILL**）：类型 = `docs/kb.yaml` 里配置的 type，不自己发明目录。

| # | 问题 | kb type | 默认落点 | 新文档默认状态 |
|---|---|---|---|---|
| 1 | 这是「要做什么、边界、接口」吗？ | specs | `docs/specs/` | draft |
| 2 | 这是「按什么顺序做、怎么验」吗？ | plans | `docs/plans/` | active |
| 3 | 这是读代码 / 跑命令得到的事实吗？ | knowledge | `docs/knowledge/` | active |
| 4 | 这是某时点的评审 / 汇报 / 统计复核吗？ | reviews | `docs/reviews/` | final |
| 5 | 这是操作手册 / 例行契约吗？ | ops | `docs/ops/` | active |
| 6 | 这是对外讲解 / onboarding 主文档吗？ | framework | `docs/framework/` | active |
| 7 | 已失效但需保留吗？ | —（归档目录，不是 type） | `docs/archive/` | archived（只能经 `kb archive`） |

> **决策 / ADR 不是独立 kb 类型**：并入 `docs/specs/` 的设计记录（可命名 `<date>-<topic>-decision.md`），状态仍由 kb 管。

**硬规则**

- 类型目录与状态以 `docs/kb.yaml` + `docs/INDEX.md` 为准；workspace 只配路径，不复制 schema
- 一个文档只承担一种类型：spec 里不写任务 checkbox，plan 里不重述设计论证，review 不承载状态
- 引用写仓库根相对路径
- 索引表是生成物：不手改 `docs/INDEX.md` / `docs/archive/INDEX.md`

## 2. 文件头与生命周期（kb）

**文档不写状态头。** 状态只在 `docs/INDEX.md`（活动）与 `docs/archive/INDEX.md`（归档）的生成表里；文件头写 `Status:` / `Active:` 视为缺陷（kb 决策 KB-1：state lives in the central index）。

- 状态词表封闭：`draft` / `active` / `final` / `archived`
- `final` 只允许 `plans` / `reviews`（终态记录）；`specs` / `knowledge` / `ops` / `framework` 只能 `draft` / `active` / `archived`
- 文档头可保留 `Date` / `Created` / `Last updated` 作辅助信息，但**不承载状态**
- 归档只能经 `kb archive`；归档后内容冻结（sha256 校验），不得再编辑

```bash
KB=~/.dsh/skills/knowledge-base/scripts/kb.py
python $KB index                       # 新文档落盘后重建索引
python $KB set-status docs/specs/x.md draft
python $KB archive docs/specs/old.md --superseded-by docs/specs/new.md --reason superseded
python $KB check                       # 提交前必须通过，并贴结果
```

- 转移：living（framework / specs / knowledge / ops）`draft → active → archived`；terminal（plans / reviews）`draft → active → final → archived`；回退只允许 retrieval（`archived → draft|active`，要带新的 Revision）
- 若 workspace 还没有 `docs/kb.yaml`：先按 `knowledge-base` skill 的 adopt 流程初始化路径表与两个 `INDEX.md` 标记，再建文档；不自造 `docs/status/` 或 `docs/decisions/` 替代

## 3. 设计文档（spec）的骨架

完整模板见 `references/templates.md`。最小骨架：

1. **Header**：Date / Path（新造还是接改）/ Scope（Modified / Tests / Untouched）；**不写 Status**（状态由 kb 索引承载）

> 若只写**一节**（不是完整 spec）：至少在结论块写一句「本节边界 / 不主张」，并把 Non-goals 中与本 section 相关的部分带出来。
2. **Context**：现状有什么能力（`file:line`）、为什么不能用（两个机制原因）、可复用面与其契约
3. **Non-goals**：不做 + 为什么（能力不可达 / 归别的组件 / 用户已声明后续）+ 归谁
4. **问题陈述（带证据）**：编号 + 实测数字 + 来源文件；每个设计动作回指证据编号
5. **机制**：签名 / 返回值 / 时钟与计数口径 / 常量 / 边界
6. **方案取舍 A/B/C**：保留了什么、破坏了什么、为什么选 A、为什么 B/C 不是现在
7. **冻结 / 延后 / 未决**：写进配置表，不只写在正文
8. **验收**：可执行、二元、可重复；测试写成「喂什么 → 断言什么」，至少一个应报错的反例
9. **Open questions**：清零，并写「在哪被确认」

## 4. 证据纪律

详见 `references/evidence.md`。五条底线：

1. **断言分级**：写回答/评审时每条实质断言二选一 —— `[代码事实]`（必须带 `<repo>@<rev>:<path>:<line>`，且真在该修订上读过）或 `[提案]`（只能写「我建议 / 我的判断是」）
2. **文档级五档**：`[实测 YYYY-MM-DD]` / `[转引 YYYY-MM-DD]` / `[设计]` / `[假设]` / `[未验证]`；`[转引]` 不声称今天仍成立
3. **锚点分层**：跨仓 `<repo>@<rev>:<path>:<line>`；仓内按符号/文句（行号必须带基线日期）
4. **没有证据就写没有**：不得给估计值、不得写占位数字；「0 命中」必须换一种方式复核后才能当「不存在」
5. **报告必须带证据块与来源列**：头部放「证据等级（全文一致）」块；关键数字表每一行带「来源」列（文件 + 节 / 命令 + 日期）。抽查任意 3 个数字，5 分钟内指不到来源 = 未过关

## 5. 报告：先写元数据源，再渲染版本

报告 / 评审（kb type `reviews`）不直接动笔。**先写源，再从源渲染交付版本。** 完整 schema、渲染步骤与一致性检查见 `references/report-meta.md`。

### 5.1 源文件

`docs/reviews/<date>-<slug>.meta.yaml`（`.yaml` 不被 kb 索引；kb 只认 `.md`）。必有字段：

| 字段 | 内容 | 判定 |
|---|---|---|
| `kind` / `title` | kb type + 标题 | `kind` 必须是 `docs/kb.yaml` 里的 type |
| `audiences` | 每个读者一个条目，`main` 必填 | 每条：`who`（谁）、`knows`（已知什么）、`decision`（读完做什么决定） |
| `style` | 正式 / 工程 / 管理 / 科普 | 每个 audience 一个值 |
| `length` | `words` + `minutes` | 中文 400 字/分钟、英文 200 词/分钟；`words` 只估正文，不含代码块 |
| `sections[]` | 内容块 | 每块：`id`、`claim`（可判真的一句）、`evidence`（等级 + 锚点）、`theory`（要展开的机制，可空） |
| `claims[]` | 结论四元组 | `claim` / `evidence` / `scope` / `outside` |
| `non_claims[]` | 不主张什么 | ≥ 1 条 |
| `terms[]` | 术语表 | 术语 / 全称 / 本文口径 / 锚点 |

### 5.2 渲染规则

- **主版本**：`docs/reviews/<date>-<slug>.md`，读者 = `audiences.main`；用户没要第二个版本时只交这一份。
- **其他版本**：`docs/reviews/<date>-<slug>.<audience>.md`，按需渲染；每份也都是 kb 里的 review（各自 `kb index` / `set-status`）。
- **头部（只这些行）**：`**Date:**`、`**Source:** docs/reviews/<date>-<slug>.meta.yaml`、`**读者:** <who>（<style>；约 <minutes> 分钟）`、`**数据截止:**`、`**证据等级（全文一致）:**`、`**Generated from <meta>; edit the source, not this file.**`。版本之间的关系写在 meta 的 `audiences` 里，不在版本里解释「这版和主版有什么区别」或补导读。
- **只允许这些差异**：选块、排序、详略（`theory` 展开或压成一句）、呈现（表格 / 段落）、按 `knows` 决定术语首现是否展开。
- **不得新增断言**：数字、结论、证据都来自 `sections` / `claims`，等级标签随行；需要新事实 → 先改 meta，再重渲染全部版本。
- **不手改渲染版**：唯一真值在 meta。抽查 3 个数字，指不回 meta 的对应块 = 未过关。

## 6. 语言：低认知负荷，不是短句化

- **结论先行**：每节第一句给结论（`> **结论**：…`），正文只做支撑
- **表格承载对照**：两个易混概念、清单、状态，用表不用长段落
- **加粗只给承重词**：不拿加粗当语气
- **只对主读者写**：不解释本版读者已知的背景；第二读者的需求由另一个渲染版本解决（§5），不写「其他读者请读 §X」
- **一段一主题，一句一命题**：一句话只放一个可判真的命题
- **负空间定义**：核心概念同时写「它不是什么」「不能由此推出什么」
- **判据可操作**：不用「有效/可靠/值得」这类形容词；给判定式
- **禁止无维度比较**：「A 优于 B」必须绑定维度与前提
- 术语按 `term-discipline` 执行（**REQUIRED SUB-SKILL**）

## 7. 规范句的子句检查（写 spec / 验收时）

把每个「当…则…」「A 与 B 都…」「每个/任意/仅当」拆成**可独立判真的 clause**，逐条锚到实现点与测试点：

- **对称句双侧都要有实现与测试**：`A ⇒ X; B ⇒ X` 只实现一侧 = 未实现
- **量词与辖域写清**：上限/预算是「每个 X」还是「整场」？在哪重置？用文档自己的估算数字做交叉算术
- **守卫写在外层**：`若 P 则报错` 不能嵌在 `if P:` 里面，否则 ¬P 分支永远不触发
- **断言反空转**：每个测试能说出「什么情况下会红」；有 `or` 兜底、异常永不抛 = placebo
- 详细方法见 `scientific-writing` skill 的 `references/clause-check.md`（**REQUIRED BACKGROUND:** `scientific-writing`）

## 8. 交付前扫描

- [ ] 类型判定正确，落点在 `docs/kb.yaml` 配置的类型目录
- [ ] 新文档已 `kb index` + `kb set-status`；状态合法（`final` 仅 plans / reviews）
- [ ] 没有手写 `Status:` / `Active:` 头；没有手改 `INDEX.md`
- [ ] 提交前 `kb check` 通过（贴一行结果）
- [ ] 报告先有 `<date>-<slug>.meta.yaml`；主版本头有 `Source:` + `读者:` + 估算分钟
- [ ] 每个版本只对一个读者（`audiences` 里的 `who`）；没有为第二个读者补的背景或导读
- [ ] 版本之间只做选块 / 排序 / 详略 / 呈现 / 术语展开，没有新增断言
- [ ] 改过 meta 后重渲染所有版本；渲染版没有手改（改了就不是同一来源）
- [ ] 前 15 行能回答「是什么 / 结论 / 证据 / 边界」
- [ ] 术语按 `term-discipline` 过关（含标题 / 小节标题 / 表头 / 图注里的缩写）
- [ ] 每条事实断言有锚点或等级标签
- [ ] 报告有「证据等级」块；关键数字表每行有「来源」列；抽查 3 个数字能指到来源
- [ ] 有「不主张什么 / 非目标 / 已知局限」
- [ ] 占位符扫描：`TBD|TODO|待定|implement later|fill in|稍后补` = 0 命中；未决项已登记（owner + 触发条件）
- [ ] 关键结论有四元组或等价的范围声明（支撑范围 + 越界即错）
- [ ] 结论与证据范围匹配，没有把未验证写成已验证
- [ ] 长文文末有「断言 → 位置」证据索引

## 9. 常见错误

| 错法 | 后果 | 改法 |
|---|---|---|
| 手写 `Status:` 头 / 手改 `INDEX.md` | 出现第二个真值源，`kb check` 失败 | 用 `kb set-status` / `kb index` |
| spec 写成教程 | 边界丢失 | 用第 3 节骨架 |
| 只有「做了什么」，没有「为什么不是 B」 | 重复讨论已被否决的方案 | 方案取舍 A/B/C |
| 结论埋在文末 | 只读开头就误判 | 结论先行 |
| 数字没有口径 | 无法复核 | 见 `scientific-writing` |
| 用「已验证」但没有命令 | 假证据 | 改为「静态核对（E0，file:line）」或 `UNVERIFIED` |
| 术语同义词轮换 | 检索与引用失效 | 见 `term-discipline` |
| 一份文档服务多个读者，越写越重 | 读者还是要自己挑哪段属于自己 | 一个版本只对一个读者；其他读者从 meta 渲染（§5） |
| 直接手改渲染版 | 第二真值源，版本漂移 | 改 meta，重渲染所有版本 |
| 每个读者版本各写一遍 | 数字对不上、证据对不上 | 只渲染，不重写 |
| 版本头解释「这版和主版有什么区别」 | 多一行导读，读者不需要 | 差异写进 meta 的 `audiences`；头部只留模板那几行 |

## 10. 参考

- `references/doc-types.md` —— kb 类型、生命周期、命名与骨架
- `references/report-meta.md` —— 报告元数据源 schema、渲染步骤、跨版本一致性检查
- `references/templates.md` —— 设计文档模板、报告模板、报告元数据源模板、证据索引
- `references/evidence.md` —— 五档标签、锚点格式、四元组、禁编造
- `knowledge-base` —— 文件落盘 / 状态 / 索引 / 归档（**REQUIRED SUB-SKILL**）
- `scientific-writing` —— 数字与实验结论的写法；写报告时**必须先加载**
