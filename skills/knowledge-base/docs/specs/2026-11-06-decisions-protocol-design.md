# 决策协议（decisions 类型 + 绑定字段）设计

**Status:** Approved (2026-11-06)
**Created:** 2026-11-06
**Last updated:** 2026-11-06
**Active:** active
**Approval:** 设计 v1 经所有者 2026-11-06 在对话中确认（原话「yes, do it」）；本 spec 由该设计收敛而来，未逐行评审。随后本会话切换为自动批准策略。

## 0. Provenance

本 spec 是 2026-11-06 设计对话的收敛点，不是起点。输入：

- kb 引擎现状：`schema.yaml`、`scripts/kb.py`（558 行）、`decisions.md` 的 KB-1…KB-7；
- pi-ab-sdk 的文档体系：`AGENTS.md` §7（9 类文档、R1–R8）、`docs/status/STATUS_MODEL.md`、`docs/decisions/0001–0019`；
- 本机两个在用 kb 工作区：`Decision_model_jev`、`intent_loop_intent_draft_v2`。

本文件不含未经对话确认的新决策（自检：无未决项）。

## 1. 问题

kb 是**文档生命周期**引擎：类型由路径决定、状态只存索引、归档 sha256 冻结。它没有「决策」这一类。

pi-ab-sdk 有决策体系，但把 ADR 与任务状态绑死（`registry.yaml` 1027 行 + `DECISIONS.md` 账本 + 生成 `BOARD.md`）。那套是 L3，本次不接管。

本次要解决两件事：

1. **决策记录本身**：ADR 作为一种文档进入 kb 的生命周期（索引、状态、归档、冻结）；
2. **可机械校验的绑定关系**：spec 绑 ADR、plan 绑 spec，且绑定只能指向当前有效的权威。

现状证据（本次实测）：

| 证据 | 事实 |
|---|---|
| pi-ab-sdk 的 ADR 状态写在文件头 | `ADR-0014` / `ADR-0017` 的 `**Active:** pending` 不在 `active / archived` 枚举内，无人校验 |
| 两个在用 kb 工作区 | 24 份 spec 中 0 份有 `Decision:`；5 份 plan 中 3 份有可解析的 `**Spec:**`，1 份用中文冒号 `**Spec**：` 不可解析 |

## 2. 已锁定的人类决策

| # | 决策 | 理由 | 错了会怎样 |
|---|---|---|---|
| D1 | 位置即状态：有效 ADR 在 `docs/decisions/`（`active`），被取代/吸收/撤回即移入 `docs/archive/decisions/`（sha256 冻结）；文件内不写状态 | 与 kb 现有模型同构，不破 KB-1 | 若 inactive ADR 留在 active 树，就必须再引入 header 状态与生成/校验机制 |
| D2 | 引用用稳定 ID `ADR-NNNN`，靠 active + archive 两个索引解析 | 归档只换目录，ID 不变，引用不破 | 用路径引用，每次归档都要全仓改路径 |
| D3 | 区分**绑定**与**提及**；只校验绑定字段，正文提及不校验 | 绑定要求当前权威；提及保留历史 | 一条规则管两种语义，必然牺牲创建时间 |
| D4 | 单字段 `Decision:` = 当前权威；历史靠 `**Amended:**` 行 | 双字段要维护两个真相，第二个先烂 | 「当初按谁设计」只剩正文与 git，可接受 |
| D5 | ADR 没有 `draft`，新建默认 `active` | ADR 是决策**作出之后**的记录 | 提案必须先落 spec/issue，工作流多一步 |
| D6 | `Topic:` 可多值；每个 Topic 在 active 树最多一份 `active` ADR | R5a 唯一可机械化的路径；多值支持「吸收」 | 没有 Topic，一议题一权威不可校验 |
| D7 | opt-in：工作区映射 `decisions` 路径才启用全部规则 | 两个存量工作区不被打断 | 全局强制 = 24 份 spec/5 份 plan 立刻失败 |
| D8 | 不自动重指；ADR 归档后由 check 逼人三选一（改绑定 + Amended / 归档文档 / 降级为提及） | 自动重指伪造「当初就是按新决策设计的」 | 遗漏会带病运行，但不会产生假历史 |
| D9 | 链条 plan → spec → ADR；plan 不直接绑 ADR | 与 pi-ab-sdk R3 一致 | 同一决策在两条链上各写一遍 |

## 3. 数据模型

### 3.1 类型与状态（schema.yaml 增量）

```yaml
types:
  decisions: [active, archived]
defaults:
  decisions: active
archive_reasons: [superseded, absorbed, historical, withdrawn, obsolete, completed]
fields:
  decisions: [Topic]
  specs: [Decision]
  plans: [Spec]
```

- 状态词表本身不变：`draft / active / final / archived`。
- `decisions` 类型**仅当工作区 kb.yaml 的 types 映射里出现 `decisions`** 时启用（D7）。
- 新增归档理由 `absorbed`：内容被并入幸存 ADR 后退役（与 `superseded` 的区别只在归档行的 `reason`）。
- `fields` 声明「每个类型必须出现的头部字段」；引擎按此解析，字段名不散落在代码里。

### 3.2 ADR 文件与 ID

| 项 | 规则 |
|---|---|
| 路径 | 有效：`docs/decisions/NNNN-<slug>.md`；归档：`docs/archive/decisions/NNNN-<slug>.md`（保留原名） |
| 文件名 | `^[0-9]{4}[a-z]?-[a-z0-9]+(?:-[a-z0-9]+)*\.md$`；数字段 = 4 位 + 可选小写字母（兼容 `0012a`） |
| ID | `ADR-` + 文件名数字段（4 位数字 + 可选小写字母），如 `ADR-0004`、`ADR-0012a` |
| 唯一性 | ID 在 active + archive 合起来唯一 |
| 编号连续性 | 不校验（允许 `ADR-0005` 缺号） |

### 3.3 字段语法

行首格式，字段名大小写敏感，每份文档每个字段最多一行：

| 字段 | 取值 | 语法 |
|---|---|---|
| `Topic:` | 逗号分隔 token 列表，至少 1 个 | token 匹配 `^[a-z0-9]+(?:-[a-z0-9]+)*$`；不允许空项、重复项 |
| `Decision:` | `ADR-NNNN` 列表；或 `N/A + 理由` | 列表项不允许重复；`N/A` 后必须跟 `—` / `-` / `:` 且理由非空 |
| `Spec:` | 仓根相对路径；或 `N/A + 理由` | 路径以 `docs/` 开头、`.md` 结尾；禁止反斜杠；N/A 规则同上 |

- 字段只在 **active 树**的文档上解析；归档文档冻结、不再校验（D1）。
- 裸 `N/A`（无理由）视为字段缺失。

### 3.4 绑定规则

| 来源 | 字段 | 目标 | 目标状态 |
|---|---|---|---|
| spec | `Decision:` | `decisions` 类型 | 必须 `active` |
| plan | `Spec:` | `specs` 类型 | 必须 `active` |

- 目标不存在 → fail；目标 archived → fail，若 ADR 的 archive 行有 `superseded_by` 则错误里带上继任者 ID。
- **必填**：opted-in 工作区里，active 树上的每份 spec 必须有 `Decision:`，每份 plan 必须有 `Spec:`（draft 也算）。
- `N/A + 理由` 是合法值，但仍要求字段行存在。

### 3.5 归档

- `kb archive <adr-path> [--superseded-by ADR-NNNN] [--reason ...]`。
- `--superseded-by` 匹配 `ADR-NNNN` 时：解析并校验目标是 **active** ADR，archive 行存 **ID 字符串**；否则沿用现有路径行为。
- 归档后 sha256 冻结；归档文档里的字段不再校验；归档行 `reason` 接受新增的 `absorbed`。
- 「被取代」与「被吸收」都归档（D1），区别只在 `reason` 与 `superseded_by`。

### 3.6 引用解析

- ID → 路径：扫描 active index 与 archive index 中 `decisions` 行，按文件名派生 ID 建映射。
- archive 行的 `superseded_by`：匹配 `ADR-NNNN` 时按 ID 解析并校验存在；否则按路径校验（保持现状）。
- 不新增索引列：`Topic` 从文件读取。

## 4. check 规则

| # | 条件 | 结果 / 错误必须包含 |
|---|---|---|
| C1 | ADR 文件名不合规 | fail：`filename` |
| C2 | ADR ID 在 active + archive 重复 | fail：`duplicate ADR id` + 两个路径 |
| C3 | ADR 缺 `Topic:` / 值为空 / token 非法或重复 | fail：`missing Topic` / `invalid topic` |
| C4 | 同一 Topic 在 active 树出现 > 1 次 | fail：`topic ... has N active ADRs` |
| C5 | `Decision:` 值非法：未知 ID / 重复 ID | fail：`unknown ADR` / `duplicate ADR in Decision` |
| C6 | `Decision:` 指向 archived ADR | fail：`is archived` + 继任者（如有） |
| C7 | opted-in 工作区，spec 缺 `Decision:` | fail：`missing Decision` |
| C8 | `Spec:` 解析不到 / 不是 specs 类型 / 含反斜杠 | fail：`unknown spec` / `Spec must be docs/...` |
| C9 | `Spec:` 指向非 active spec | fail：`is not active` |
| C10 | opted-in 工作区，plan 缺 `Spec:` | fail：`missing Spec` |
| C11 | 工作区未映射 `decisions` | C1–C10 全部跳过，行为与现在一致 |
| C12 | 正文提及 archived ADR（不在绑定字段里） | 不 fail |
| C13 | 同一文档同一字段行出现两次 | fail：`duplicate field` |

> C1–C13 每条都至少有一个测试方法；§9 的 A 表是验收锚点，不要求与 C 表一一对应。

## 5. 命令

### 5.1 `kb refs <ADR-ID>`（新增）

- 扫描 active 树所有文档的 `Decision:` 字段，列出包含该 ID 的文档：`path (type, status)`。
- 未知 ID → `kb: unknown ADR ADR-NNNN`，退出码 2。
- 无引用 → `kb refs ADR-NNNN: 0 binding(s)`，退出码 0。
- 用途：归档 ADR 前的影响面清单（C6/C7 会连锁失败，refs 先告诉你会炸哪些）。

### 5.2 `kb archive`（扩展）

见 3.5。

### 5.3 `kb index`

新 ADR 按 schema defaults 落为 `active`。

### 5.4 不变

- `check` 的一行结论格式、`status`、`set-status`、`hook` 行为不变；
- `set-status archived` 仍拒绝并提示用 `kb archive`；
- 既有检查（索引一致、归档 sha256、链接）语义不变。

## 6. 配置与 rollout

收养动作（每工作区一次）：

```yaml
# docs/kb.yaml
types:
  ...
  decisions: docs/decisions
```

并创建 `docs/decisions/` 与 `docs/archive/decisions/`。路径声明即收养，符合「工作区只写路径」。

- 未映射 `decisions` 的工作区：C1–C10 不触发，完全保持旧行为。
- `schema_version` **不升**：纯增量 + opt-in，不构成 breaking change。

## 7. 兼容与迁移

| 工作区 | 现状（本次实测） | 收养后需要 |
|---|---|---|
| `Decision_model_jev` | 3 specs / 1 plan；0 Decision、1 Spec | 建 `docs/decisions/`；3 份 spec 补 `Decision:`（无决策写 `N/A — 理由`）；1 份 plan 规范化 `Spec:` |
| `intent_loop_intent_draft_v2` | 21 specs / 4 plans；0 Decision、2 Spec（1 份中文冒号） | 同上；24 份文档补字段；2 份 `Spec:` 规范化 |
| `pi-ab-sdk`（未收养） | 19 ADR；16 份被 `ADR-0019` 取代但仍在 `docs/decisions/` | 16 份归档（`--superseded-by ADR-0019`）；spec/plan 补字段；grep 引用改 ID |

迁移顺序：**先补字段让 check 通过，再归档 ADR**。ADR 归档会触发 C6 连锁失败，一次处理一个 Topic。

## 8. 不做（Out of scope）

- 文件头状态、生成元数据块、自动重指；
- 任务/问题状态、决策账本、生成看板（L3）；
- 正文提及校验（只校验绑定字段）；
- ADR 编号连续性检查；
- 把 pi-ab-sdk 整体迁到 kb（另立 plan）；
- 给 `knowledge` / `ops` / `reviews` / `framework` 增加字段要求。

## 9. 验收标准

| ID | 验收项（二元） | 证据（命令 / 观察） | 失败条件 |
|---|---|---|---|
| A1 | 既有 + 新增单测全绿 | 技能目录下 `python -m unittest discover -s tests -v` 退出 0 | 任一用例失败/报错 |
| A2 | 新 ADR 默认 active | `test_adr_defaults_active`：`index` 后 INDEX 行 status = `active` | status 不是 `active` |
| A3 | 文件名不合规 fail | `test_bad_adr_filename`：check 退出 1 且输出含 `filename` | 退出 0 或输出无该词 |
| A4 | ID 跨树重复 fail | `test_duplicate_adr_id`：输出含 `duplicate ADR id` | 未报 |
| A5 | Topic 必填 / active 内唯一 / 多值各自计数 | `test_topic_required`、`test_topic_unique`、`test_topic_multi` | 任一不符 C3/C4 |
| A6 | 绑定 archived ADR fail 且给继任者 | `test_decision_points_to_archived`：输出含 `is archived` 与继任 ID | 缺任一 |
| A7 | spec 的 Decision：缺失 fail / 裸 N/A fail / N/A+理由通过 / 重复 ID fail | `test_decision_field_required`、`test_na_requires_reason`、`test_na_with_reason_ok`、`test_duplicate_decision_id` | 行为不符 |
| A8 | plan 的 Spec：archived fail / draft fail / 缺失 fail / 有效通过 | `test_spec_binding_archived`、`test_spec_binding_draft`、`test_spec_field_required`、`test_spec_binding_ok` | 行为不符 |
| A9 | `refs` 精确列出绑定文档；未知 ID 退出 2 | `test_refs_lists_bindings`、`test_refs_unknown_id` | 列表或退出码不符 |
| A10 | `archive --superseded-by ADR-XXXX` 记录 ID、sha256 冻结、check 通过 | `test_archive_adr_with_id` | 行内非 ID / 无 sha / check 失败 |
| A11 | 未 opt-in 的旧树 check 通过 | `test_non_opted_workspace_unaffected` | 退出非 0 |
| A12 | 正文提及 archived ADR 不 fail | `test_prose_mention_ok` | check 非 0 |
| A13 | 两个真实工作区只读回归 | `python scripts/kb.py check --root D:/Jingdong/colorless_dragon/Decision_model_jev` 与 `.../intent_loop_intent_draft_v2` 均退出 0 | 任一非 0 |

> A13 是人工 gate（路径依赖本机），plan 里单独列一步。

## 10. For the Plan Author

- **必须覆盖**：A1–A13。
- **不得改**：状态词表（`draft/active/final/archived`）、索引表格式与标记、未 opt-in 工作区的既有 check 语义、hook 模板。
- **不得引入**：第三方依赖（stdlib only）、`schema_version` 变更、对 `pi-ab-sdk` 或两个存量工作区的写操作。
- **测试方式**：沿用 `tests/test_kb.py` 的 `make_ws` / `run` 模式，fixture 放临时目录；新增用例可放该文件，或新增 `tests/test_decisions.py` 并在 `unittest discover` 下可发现。
- **文档同步**：`SKILL.md`（命令与规则摘要）、`README.md`（类型表 + 收养步骤）、`decisions.md` 追加 KB-8…KB-11（本协议的 ADR：位置即状态 / 稳定 ID 与绑定-提及分离 / decisions 类型 opt-in 且无 draft / 一议题一权威靠 Topic）。
- **实现顺序建议**：schema → 解析与 ID/Topic 检查 → 绑定检查 → refs → archive 扩展 → 文档 → 真实工作区回归。

## 11. 路径表

| 类别 | 路径 | git 状态 |
|---|---|---|
| 冻结输入（只读） | `pi-ab-sdk/AGENTS.md`、`pi-ab-sdk/docs/status/*`、`pi-ab-sdk/docs/decisions/*` | 外部仓，只读 |
| 冻结输入（只读） | `Decision_model_jev`、`intent_loop_intent_draft_v2` | 外部仓，只读 |
| 交付物（改） | `schema.yaml` | tracked |
| 交付物（改） | `scripts/kb.py` | tracked |
| 交付物（改） | `tests/test_kb.py`（或新增 `tests/test_decisions.py`） | tracked |
| 交付物（改） | `SKILL.md` | tracked |
| 交付物（改） | `README.md` | tracked |
| 交付物（改） | `decisions.md` | tracked |
| 交付物（新） | `docs/specs/2026-11-06-decisions-protocol-design.md`（本文件） | untracked，待提交 |
| 交付物（新） | `docs/plans/2026-11-06-decisions-protocol.md`（plan 阶段产出） | untracked |
| 草稿 | 无 | — |

> 路径表签字：所有者 2026-11-06 批准设计 v1（含该路径表）。

> 本 spec 编写环境不提供 shell/git（沙箱），`git check-ignore -v` 未能执行、spec 也未能提交；**plan 第一步补跑 `git check-ignore -v` 确认 `docs/specs/` 与 `docs/plans/` 未被忽略，并提交本 spec**。

## 12. 残余风险

1. **连锁失败是特性不是缺陷**：ADR 归档会一次炸出所有绑定它的 spec/plan；迁移期按 Topic 分批。
2. **字段行格式是新增要求**：opt-in 之前既有文档不被要求；opt-in 之后 24 份 spec / 5 份 plan 需要一次补字段。
3. **`superseded_by` 混存 ID 与路径**：两个分支都要测（A10 覆盖 ID；既有路径行为不能回归）。
4. **`Topic` 的粒度是人定的**：引擎只保证唯一性，不保证「议题划分得对」。

## 13. 附：与 pi-ab-sdk 的映射

| pi-ab-sdk | 本协议 |
|---|---|
| `docs/decisions/000N-*.md` | `docs/decisions/` + `decisions` 类型 |
| ADR header 的 `Status: Accepted` | 位置 + 索引状态 `active`（文件不写状态） |
| header 的 `Superseded by:` / `Absorbed by:` | archive 行 `superseded_by` + `reason` |
| R5a 一议题一权威 | `Topic:` 在 active 树内唯一 |
| R3 plan 必须写 `**Spec:**` | `Spec:` 绑定且必须 active |
| `registry.yaml` 的 `closed_by: ADR-xxxx` | 不做（L3）；`kb refs` 只回答「谁还在绑定它」 |
| `Active: pending` 这类 header 漂移 | 结构上不可能（没有 header 状态） |
