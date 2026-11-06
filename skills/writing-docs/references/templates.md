# 模板（templates）

## T1 设计文档（spec）

```markdown
# <子系统名> — Design

**Date:** YYYY-MM-DD
**Path:** Architectural — new subsystem（没有既有流程可接）｜ extension of <既有模块>
**Supersedes as v1:** <旧 spec> 仍是 delayed stages 的完整参考（§N）
**Sources:** <仓库 / 论文 / run artifacts / 设计讨论日期>

**Scope:**
- Modified: <文件>（<改什么>）
- Tests: <测试文件>（<覆盖什么>）
- Untouched: <最容易误改的 5–10 项>

## 0. 一句话

> 本设计要解决什么、用什么机制、缺省行为是否改变。

## Context

<现状有能力：…（`file:line`）>
<但不能用，两个原因：1. `file:line` …  2. `file:line` …>
<可复用面与契约：<函数>（contract: 每条 record 携带 <keys>）>
**Goal:** <一句话：在哪、测什么、跑在什么约束下>.

## Non-goals

- 不做 <X> — <能力不可达 / 归 <别的组件> / 用户已声明是后续独立任务>

## 问题陈述（带证据）

Sources: <数据文件 / 代码位置>
1. **<现象>** — <实测数字>。⇒ <要引入的机制>
2. …

## <机制节：契约 / 常量 / 边界>

<函数签名 + 返回值 keys + 时钟与计数口径 + 明确「不重试 / 不限速」之类>

## 方案取舍（Why this layout, not extending <Y>）

- **A（chosen）:** <做法>。保留 <优点>；不违约。
- **B:** <做法>。保留 <优点>，但 <违反哪条约束 / 破坏哪个不变量>。
- **C:** <做法>。侵入度最高；<为什么不是现在>。

## 冻结 / 延后 / 未决

| Knob | Value (start) | Maps to |
|---|---|---|
| <x> | <值> — fixed in v1 (no knob) | <落点> |
| <y> | <值> (v1) → <值> later | **known v1 gap**: <缺口 + 兜底> |

## 验收 / Testing

1. <可执行判据（二元）>
- **<单元>** — 喂 <合成输入>，断言 <量 A> / <量 B>；<应当报错的反例>。

## Open questions

None at spec time. <每个曾悬而未决的点> both confirmed in <环节>.
```

**落盘**：`docs/specs/`；写完 `python $KB index`，再 `kb set-status <path> draft`（或 `active`）。**不写 Status 头。**

## T2 评审 / 报告

```markdown
# <项目> <类型>报告 —— <一句话主题>

**Date:** YYYY-MM-DD
**Source:** docs/reviews/<date>-<slug>.meta.yaml
**读者:** <who>（<style>；约 <minutes> 分钟）｜**数据截止:** YYYY-MM-DD
**证据等级（全文一致）:** <五档说明>
**Generated from <meta>; edit the source, not this file.**

## 0. 一页速览

### 0.1 结论四元组（关键结论必须进表）

| 主张 | 证据（等级 + 日期） | 支撑范围 | 越界即错 |
|---|---|---|---|
| … | `[转引 YYYY-MM-DD]` … | 只在 … 范围内成立 | 推不出 …；不能外推到 … |

### 0.2 定性、范围与角色

| 问题 | 答案 |
|---|---|
| 这是什么 | … |
| 解决什么 | … |
| 成功的定义 | … |
| 本报告的角色 | … |

### 0.3 阶段坐标与当前结论

### 0.4 有效保证（到底保证了什么）

| # | 保证 | 锚点 |
|---|---|---|

### 0.5 本报告不主张什么

- 不主张 …

### 0.6 关键数字（每行带来源）

| 指标 | 数值 | 口径 | 来源 |
|---|---|---|---|
| … | … | N=…；单位 pp | `docs/knowledge/....md` §2（`[转引 YYYY-MM-DD]`） |

## 1. Context（为什么需要）
## 2. Goal（目标与判据）
## 3. Boundary（做什么 / 不做什么）
## 4. 交付物
## 5. Constraint（约束与合规）
## 6. Gap → Fill
## 7. Acceptance（二元、可复现、离线）
## 8. Edge Cases
## 9. NFR
## 10. 当前状态
## 11. 后续

## 附录 A 术语表（本报告口径） · 附录 B 证据索引
```

**落盘**：`docs/reviews/`（kb type `reviews`，默认 `final`）；写完 `kb index`，需要时 `kb set-status`。**不写 Status 头。**

**头部只这 6 行**；版本差异写进 meta 的 `audiences`，不在版本里解释「这版和主版有什么区别」。

## T3 知识卡（knowledge）

```markdown
---
id: kb-<slug>
title: <一句话>
type: knowledge-base
created: YYYY-MM-DD
last_verified: YYYY-MM-DD
verified_by: file read + git show + grep (3-way)
evidence_level: file-line
scope: [<仓>]
tags: [...]
related: [...]
---

# <标题>

## 0. 一句话

> …

## 1. 判据 / 定义

## 2. 事实（逐条带 `file:line`）

## 3. 结论

## 附录：证据索引

| 断言 | 位置 |
|---|---|
```

## T4 证据索引

```markdown
## 附录：证据索引（按符号 / 文句定位，不按行号）

| 断言 | 位置 |
|---|---|
| 分桶是确定性的 | `pi_ab_sdk/core/split/fnv1a32_v2.py` `hash32`; `tests/split/test_split.py::test_deterministic` |
```

## T5 报告元数据源（meta）

```yaml
# docs/reviews/YYYY-MM-DD-<slug>.meta.yaml
kind: reviews                      # 必须是 docs/kb.yaml 里的 type
title: <一句话主题>
updated: YYYY-MM-DD

audiences:
  main:                            # 默认交付版本
    who: <主读者：角色 / 团队>
    knows: <已知背景；决定术语是否展开>
    decision: <读完要做什么决定 / 行动>
    style: engineering             # engineering | executive | onboarding | public
    length: { words: 900, minutes: 3 }
    outline: [claims, numbers, risks, next]
  <audience-id>:                   # 第二个读者，按需渲染
    who: <谁>
    knows: <已知什么>
    decision: <读完做什么>
    style: executive
    length: { words: 250, minutes: 1 }
    outline: [verdict, ask]

sections:                          # 内容块：事实与理论都在这里，版本只能选和排
  - id: verdict
    claim: <可判真的一句>
    evidence: "[转引 YYYY-MM-DD] docs/knowledge/....md §2"
    theory: <要展开的机制；可空>
  - id: numbers
    claim: <数字结论>
    evidence: "[实测 YYYY-MM-DD] eval-runs/run2/metrics.json"

claims:                            # 结论四元组
  - claim: <主张>
    evidence: <等级 + 日期 + 锚点>
    scope: <只在 ... 范围内成立>
    outside: <推不出 ...>

non_claims: [<本报告不主张什么>]

terms:
  - term: <术语>
    full: <全称>
    rule: <本文口径>
    anchor: <锚点>
```

渲染：主版本 = `audiences.main`；其他版本 = `<slug>.<audience>.md`；步骤与一致性检查见 `references/report-meta.md`。

## 使用顺序

1. 先按 `references/doc-types.md` 判类型，落到 `docs/kb.yaml` 配置的类型目录
2. 报告 / 评审：先写 `<date>-<slug>.meta.yaml`（T5），再渲染主版本；其他读者版本按 `references/report-meta.md`
3. 选模板，补 Header（**不写状态**；报告写 `Source:` + `读者:` + 分钟）
4. `python $KB index` → `kb set-status`；提交前 `kb check`
5. 按 `references/evidence.md` 给每条断言加锚点 / 标签
6. 按 `scientific-writing` 检查数字与结论范围
7. 占位符扫描 + 自查清单
