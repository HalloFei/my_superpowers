# 报告元数据源与多版本渲染

## 0. 一句话

报告的唯一真值在 meta；每个交付版本是同一份 meta 的投影。读者之间共享事实，**只**共享事实，不共享排版。

## 1. 文件与命名

| 文件 | 作用 | kb |
|---|---|---|
| `docs/reviews/<date>-<slug>.meta.yaml` | 源：读者、风格、长度、内容块、结论 | 不索引（kb 只认 `.md`） |
| `docs/reviews/<date>-<slug>.md` | 主版本（`audiences.main`） | 是，type `reviews` |
| `docs/reviews/<date>-<slug>.<audience>.md` | 其他读者版本，按需 | 是，type `reviews` |

一个报告一份 meta；所有版本头部的 `Source:` 都指向它。不要给每个版本各建一份 meta。

## 2. meta 字段

| 字段 | 必填 | 内容 |
|---|---|---|
| `kind` | 是 | kb type（报告用 `reviews`） |
| `title` | 是 | 一句话主题 |
| `updated` | 是 | 最后一次修改日期 |
| `audiences` | 是 | 读者字典；`main` 必填 |
| `audiences.<id>.who` | 是 | 谁（角色 / 团队） |
| `audiences.<id>.knows` | 是 | 已具备的背景；决定术语要不要展开、theory 要不要讲 |
| `audiences.<id>.decision` | 是 | 读完要做什么决定 / 行动；决定哪些块必留 |
| `audiences.<id>.style` | 是 | `engineering` / `executive` / `onboarding` / `public` |
| `audiences.<id>.length` | 是 | `words` + `minutes` |
| `audiences.<id>.outline` | 否 | 该版本的节顺序；缺省用 sections 顺序 |
| `sections[].id` | 是 | 稳定 id，供 outline 引用 |
| `sections[].claim` | 是 | 可判真的一句结论 |
| `sections[].evidence` | 是 | 等级 + 日期 + 锚点；没有证据就写「未验证」 |
| `sections[].theory` | 否 | 需要展开的机制；exec 版可压成一句或省略 |
| `claims[]` | 是 | 四元组：`claim` / `evidence` / `scope` / `outside` |
| `non_claims[]` | 是 | 本报告不主张什么，≥ 1 条 |
| `terms[]` | 否 | `term` / `full` / `rule` / `anchor` |

## 3. 渲染步骤

1. 取目标 audience 的 `who` / `knows` / `decision` / `style` / `length` / `outline`。
2. 按 outline 选 `sections`；没选中的块不出现——不要用「详见主版本」补救。
3. 每块先写 `claim`（结论句），`evidence` 紧跟其后（行内标签或表内来源列）。
4. `theory` 按 `style` 与 `knows` 决定：engineer 展开到机制；executive 压成一句「所以」。
5. 术语：首现按 `knows` 决定展开与否——不知道就给全称 + 一句解释；知道才用缩写。
6. 写 `claims` 四元组表；exec 版可省略证据列以外的推导，但不能删 `scope` / `outside`。
7. 头部只写模板允许的行（`Date` / `Source` / `读者` / `数据截止` / `证据等级` / `Generated from …`）；版本差异由 `audiences` 定义，不在版本里解释；长文末尾给证据索引。
8. 字数守卫：`words` 是上限，不是目标；超过 `length.words × 1.3` 时先压 `theory`，再砍低优先级块，**不要删证据**。

## 4. 长度估算

- 中文：400 字/分钟（技术文取 300–400）；英文：200 词/分钟。
- `minutes = ceil(words / 400)`（中文）或 `ceil(words / 200)`（英文）。
- 只估正文；代码块与表格不计入 `words`，但要在 `minutes` 上留余量。

## 5. 版本一致性检查（每次渲染后）

- [ ] 同一 claim 在所有版本里的数字、方向、范围逐字一致
- [ ] 每个数字都能指回 `sections` / `claims` 的对应条目
- [ ] 没有版本新增断言、新增数字、新增因果
- [ ] 版本之间没有互相矛盾的口径
- [ ] 抽查 3 个数字，5 分钟内指不回 meta = 未过关

## 6. 更新流程

| 要改什么 | 怎么改 |
|---|---|
| 事实 / 数字 / 结论 | 改 meta → 重渲染**所有**版本 |
| 某个读者版本的篇幅 / 顺序 | 改 `audiences.<id>` → 只重渲染该版本 |
| 新增一个读者版本 | 加 `audiences.<id>` → 渲染 `<slug>.<audience>.md` |
| 删除一个版本 | 删 `.md`（或 `kb archive`）；meta 保留 |

**渲染版不手改。** 版本里出现 meta 没有的数字，先把数字补进 meta，再重渲染。

## 7. 反模式

| 反模式 | 后果 |
|---|---|
| 先写主版本，再回头「抽」meta | 事实已经散在两份稿子里，必然对不上 |
| 复制一个版本再改 | 第二真值源，版本漂移 |
| 在一个版本里补另一个读者的背景 / 导读 | 每版本变重，读者还得自己挑；改成按需渲染 |
| 每个版本各写一套数字 | 无法抽查，错误会分叉 |

## 8. 最小例子

```yaml
# docs/reviews/2026-11-06-eval.meta.yaml
kind: reviews
title: 2026-09 意图评测复盘
updated: 2026-11-06
audiences:
  main:
    who: 推理 / 评测工程师
    knows: 评测框架、13 type、micro/macro 口径
    decision: 81B 能否下线；先灰度哪个 type；补测什么
    style: engineering
    length: { words: 900, minutes: 3 }
  exec:
    who: 部门总监
    knows: 业务指标，不读代码
    decision: 批不批下线与补测
    style: executive
    length: { words: 250, minutes: 1 }
sections:
  - id: verdict
    claim: 81B 三个聚合口径全末位，可下线
    evidence: "[转引 2026-11-01] docs/knowledge/2026-11-01-eval-facts.md §2"
  - id: gray-order
    claim: type 级灰度顺序缺 per-type 数据，现在定不了
    evidence: "[转引 2026-11-01] eval-runs/run2/metrics.json（无 per-type 字段）"
non_claims: [不主张线上收益幅度]
```

主版本头：`Source: docs/reviews/2026-11-06-eval.meta.yaml`、`读者: 推理 / 评测工程师（约 3 分钟）`。
exec 版头：`Source: docs/reviews/2026-11-06-eval.meta.yaml`、`读者: 部门总监（约 1 分钟）`。
