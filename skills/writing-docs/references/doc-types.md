# 文档类型与文件管理（kb）

> 本文件服从 `knowledge-base` skill。**规则不在 workspace 里**：状态词表、每类型允许的状态、转移规则、索引列由全局 `schema.yaml` 定义；workspace 只提供 `docs/kb.yaml`（路径配置）。这两份都不要在本仓复制。

## 1. 类型（kb type）

类型 = `docs/` 下第一段目录名，由 `docs/kb.yaml` 配置。默认六类加归档：

| type | 放什么 | 默认状态 | 允许的状态 | 命名 |
|---|---|---|---|---|
| `framework` | 对外讲解 / onboarding 主文档 | active | draft / active / archived | `<topic>.md` |
| `specs` | 设计权威：做什么 / 为什么 / 边界 / 接口冻结 | draft | draft / active / archived | `YYYY-MM-DD-<slug>.md`（design 类以 `-design.md` 结尾） |
| `plans` | 按什么顺序做、改哪些文件、怎么验 | active | draft / active / final / archived | `YYYY-MM-DD-<slug>.md` |
| `knowledge` | 读代码 / 跑命令得到的**事实** | active | draft / active / archived | `YYYY-MM-DD-<slug>.md` |
| `reviews` | 某时点的评审 / 汇报 / 统计复核（终态记录） | final | active / final / archived | `YYYY-MM-DD-<slug>.md` |
| `ops` | 操作手册 / 例行契约 | active | draft / active / archived | `UPPER_SNAKE.md` |
| `archive`（归档目录，不是 type） | 已退出语料、冻结保留 | archived | archived | 保留原文件名 |

**决策 / ADR 不是 kb 类型**：并入 `docs/specs/` 的设计记录（可命名 `YYYY-MM-DD-<topic>-decision.md`），状态仍由 kb 管理。不要再建 `docs/decisions/` 这类 kb 不认识的目录。

## 2. 状态语义（封闭四值）

| 状态 | 含义 | 可编辑 | 谁用 |
|---|---|---|---|
| `draft` | 在写 / 待评审，不可作为依据 | 是 | specs / plans 起始 |
| `active` | 现行权威或正在使用，可依赖、可追加 Revision | 是 | living docs |
| `final` | 终态记录：已执行 / 已观测完毕，冻结、可引用但不可当指令 | 否 | **仅 plans / reviews** |
| `archived` | 已退出语料，冻结，必须在 archive 目录 | 否 | 所有类型 |

- **`superseded` / `historical` 不是状态**：它是归档行的 `superseded_by` 列（有后继 = superseded）。
- 只有「有真实终态事件」的 plan 与 review 允许 `final`；把 living doc 标 final 会把权威冻结，而现实还在动。
- 归档时才写 `--reason`（superseded / historical / withdrawn / obsolete / completed）。

## 3. 生命周期

```text
living  (framework / specs / knowledge / ops)
    draft ──approve──> active ──replaced|retired──> archived
      └────────────────abandon──────────────────────^

terminal (plans / reviews)
    draft ──start──> active ──done──> final ──no longer cited──> archived
      └────────────────abandon──────────────────────────────────^
```

回退只有 retrieval 一条：`archived → draft|active`，且要先移回活动树、标新的 Revision，再编辑。

## 4. 各类型骨架

### specs

- Header：Date / Path（新造 / 接改）/ Scope（Modified / Tests / Untouched）；**不写状态**
- Context：现状有什么能力（`file:line`）、为什么不能用、可复用面与契约
- Non-goals：不做 + 为什么 + 归谁
- 问题陈述：编号 + 实测数字 + 来源
- 机制：签名 / 返回值 / 口径 / 常量 / 边界
- 方案取舍 A/B/C：保留什么、破坏什么、为什么选 A
- 冻结 / 延后 / 未决：写进配置表
- 验收：二元、可执行、可重复；测试 = 喂什么 → 断言什么；含反例
- Open questions：清零并写明在哪确认

### plans

- 必须有 `**Spec:**` 行（无 spec 写 N/A + 原因）
- Goal / Architecture / Tech Stack
- Global Constraints（每个任务隐含包含）
- File Structure 表：文件 / 动作 / 职责
- 每个 Task：Files / Interfaces / 步骤 / Commit
- Self-Review：占位符扫描、覆盖表、反空转说明
- 执行完：`kb set-status docs/plans/....md final`（final = 已执行记录，不是待办）

### knowledge

```yaml
---
id: kb-<slug>
title: <一句话>
type: knowledge-base
created: YYYY-MM-DD
last_verified: YYYY-MM-DD
verified_by: file read + git show + grep (3-way)
evidence_level: file-line
scope: [<仓 / 模块>]
tags: [...]
related: [...]
---
```

正文：结论性引言 → `## 0. TL;DR` → 编号正文（判据 → 逐条判定 → 结论）→ `## 附录：证据索引`。
**不写 `status:`**（状态在 index）。

### reviews

- 先写源 `docs/reviews/<date>-<slug>.meta.yaml`（不被 kb 索引），再渲染版本；主版本 `<date>-<slug>.md`，其他读者 `<slug>.<audience>.md`（规则见 `references/report-meta.md`）
- 每个版本头写 `Source:` + `读者:` + 估算分钟；正文只服务本版读者
- 结论四元组表 + 关键数字表（每行带来源）
- 不主张什么 / 已知局限
- 默认 `final`；被后续报告取代时经 `kb archive --superseded-by`

### ops

- 前置：环境、路径、权限
- 一条可复制命令（注明本机是否执行过）
- 成功判据（≤5 条，二元）
- 常见故障与处理
- 日志归档方式

### framework

- 对外讲解 / onboarding 主文档；是「当前框架卷」，不承载实验细节与逐臂数字
- 结论先行；术语按 `term-discipline`

## 5. 新文档流程

1. 按上表放进类型目录（必要时先建目录并在 `docs/kb.yaml` 配路径）
2. 报告 / 评审：先写 `<date>-<slug>.meta.yaml`（源，不被索引），再渲染主版本；其他读者版本按需
3. `python $KB index` —— 它出现在 `docs/INDEX.md`，带该类型默认状态
4. `python $KB set-status <path> <status>` 设成真实状态（新 spec 默认 draft）
5. 提交前 `python $KB check`，结果贴进交付说明

```bash
KB=~/.dsh/skills/knowledge-base/scripts/kb.py
python $KB index
python $KB set-status docs/specs/2026-11-06-x-design.md draft
python $KB check
```

## 6. 归档流程

```bash
python $KB archive docs/specs/old.md --superseded-by docs/specs/new.md --reason superseded
python $KB check
```

- 用 `git mv` 时保留历史；工具会重建两张索引表并记录 sha256
- 归档后**不得编辑**；要改 → retrieval 流程
- `superseded_by` 必须指向真实存在的后继

## 7. 硬规则

- **索引是唯一权威**：状态只改 `kb set-status`；表只由 `kb index` 生成；不手改 `docs/INDEX.md` / `docs/archive/INDEX.md`
- **不要复制 schema**：workspace 只写 `docs/kb.yaml`（路径 + `root_files`）
- **一个文档只承担一种类型**：spec 不写任务 checkbox，plan 不重述设计论证，review 不承载状态
- **根级文件**（AGENTS.md / README.md 等）放在 `root_files`，不强行塞进类型目录
- **引用写仓库根相对路径**；`kb check` 会查活动文档里的裸 `docs/...` 与相对链接
- **改完必须报 `kb check` 的一行结果**——没有这一行，不算一致
