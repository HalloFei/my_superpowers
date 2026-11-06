# Decisions Protocol Implementation Plan

**Status:** Approved (2026-11-06)
**Created:** 2026-11-06
**Last updated:** 2026-11-06
**Active:** active

> For agentic workers: REQUIRED SUB-SKILL: use executing-plans (apply-heavy, 3 tasks). Track steps with checkbox syntax.

**Goal:** 给 kb 增加 decisions 文档类型与三个绑定字段的机械校验，使 ADR 的位置即状态、引用稳定、spec/plan 只绑定当前有效的权威。

**Architecture:** 规则留在共享 schema.yaml（类型、默认状态、fields 声明）；引擎 scripts/kb.py 增加字段解析、ADR ID/Topic 校验、绑定检查与 refs 命令；未映射 decisions 的工作区完全保持旧行为（opt-in）。

**Tech Stack:** Python 3.8+ 标准库；unittest；沿用既有 tests/test_kb.py 的 subprocess 测试模式。

**Spec:** docs/specs/2026-11-06-decisions-protocol-design.md
**Spec hash:** sha256:eff492deecfd
**Paths:** approved 2026-11-06 — 交付物在 kb 仓内 tracked；docs/specs 与 docs/plans 为新增后提交；冻结输入（pi-ab-sdk、两个在用工作区）只读。

## Global Constraints

- 仅标准库，Python 3.8+。
- schema_version 保持 1；不给既有工作区加任何必填项。
- 未映射 decisions 的工作区：check 行为与现状一致。
- 不改索引表列/标记、不改 hook 模板、不改状态词表。
- 错误信息必须包含 spec §4 的子串：filename / duplicate ADR id / missing Topic / invalid topic / topic ... has N active ADRs / unknown ADR / duplicate ADR in Decision / is archived / missing Decision / unknown spec / Spec must be a docs/... .md path / is not active / missing Spec / duplicate field。
- 不得写 pi-ab-sdk 或两个在用工作区（只读）。
- 既有 tests/test_kb.py 用例不得修改。

## Spec Coverage

| Spec ID | Task | Evidence |
|---|---|---|
| A1 | Task 3 | python -m unittest discover -s tests -v 退出 0 |
| A2 | Task 1 | tests/test_decisions.py::test_adr_defaults_active |
| A3 | Task 1 | test_bad_adr_filename |
| A4 | Task 1 | test_duplicate_adr_id |
| A5 | Task 1 | test_topic_required / test_topic_unique / test_topic_multi |
| A6 | Task 2 | test_decision_points_to_archived |
| A7 | Task 2 | test_decision_field_required / test_na_requires_reason / test_na_with_reason_ok / test_duplicate_decision_id |
| A8 | Task 2 | test_spec_binding_archived / test_spec_binding_draft / test_spec_field_required / test_spec_binding_ok |
| A9 | Task 2 | test_refs_lists_bindings / test_refs_unknown_id |
| A10 | Task 2 | test_archive_adr_with_id |
| A11 | Task 1 | test_non_opted_workspace_unaffected |
| A12 | Task 2 | test_prose_mention_ok |
| A13 | Task 3 | python scripts/kb.py check --root D:/Jingdong/colorless_dragon/Decision_model_jev 与 .../intent_loop_intent_draft_v2 均退出 0 |

## Task 1: Decision records enter the lifecycle

**Files:** Modify schema.yaml; Modify scripts/kb.py; Create tests/test_decisions.py。

**Type:** build — 测试是 RED 工件；实现体按 Interfaces 自行设计。

**Interfaces (Produces):** decisions_enabled(cfg) -> bool；常量 ADR_ID_RE / ADR_FILE_RE / TOPIC_RE / FIELD_LINE_RE / N_A_RE；adr_id_of(relpath) -> str|None；archive_type_of(relpath, archive_dir) -> str；read_fields(path, names) -> dict；na_reason(value) -> str|None；split_list(value) -> list；build_adr_id_map(root, cfg, schema, active_map, archive_map) -> (errors, id_map)；check_decisions(root, cfg, schema, active_map, archive_map) -> (errors, id_map)；schema 的 fields 映射。

- [ ] Step 1: 写失败测试（A2–A5、A11、C13）。fixture 规则：opt-in 工作区的每份 spec 必须有 **Decision:** 行（N/A 加理由），每份 plan 必须有 **Spec:** 行；ADR 必须有 **Topic:**；测试用 subprocess 调 python scripts/kb.py，与 test_kb.py 同模式。测试用例：
  - test_adr_defaults_active：建 docs/decisions/0001-first.md 后 index，断言 INDEX 行为 decisions | active。
  - test_bad_adr_filename：docs/decisions/1-first.md → check 退出 1 且输出含 filename。
  - test_duplicate_adr_id：active 与 archive 各一份 0001-*.md → 输出含 duplicate ADR id。
  - test_topic_required：ADR 无 Topic → 输出含 missing Topic。
  - test_topic_unique：两份 active ADR 同 topic → 输出含 topic 与 has 2 active ADRs。
  - test_topic_multi：一份 Topic 为 bucketing, canvas，另一份 canvas 时失败；把第二份改成 gateway 后通过。
  - test_duplicate_field：ADR 写两行 Topic → 输出含 duplicate field。
  - test_non_opted_workspace_unaffected：kb.yaml 不映射 decisions、spec/plan 无字段 → check 退出 0。
- [ ] Step 2: 跑 RED：python -m unittest discover -s tests -p "test_decisions.py" -v（技能仓根）。Expected: FAIL。
- [ ] Step 3: 实现。schema.yaml 与 kb.py 的 FALLBACK_SCHEMA 同步加：types.decisions [active, archived]；defaults.decisions active；archive_reasons 加 absorbed；fields 映射 decisions:[Topic], specs:[Decision], plans:[Spec]。引擎要点：decision 协议仅在 decisions 类型被映射时启用；ADR 文件名按 ^[0-9]{4}[a-z]?-[a-z0-9]+(?:-[a-z0-9]+)*\.md$ 校验；ID 由文件名派生 ADR-NNNN；Topic 必填、token 合法、active 树内每个 topic 最多一份；字段按行首 **Name:** 解析，重复字段行报 duplicate field；cmd_check 合并 check_decisions 的错误并让 ADR 形式的 superseded_by 按 ID 解析。
- [ ] Step 4: 跑 focused GREEN：同上命令。Expected: PASS（8 tests）。
- [ ] Step 5: 全量：python -m unittest discover -s tests -v。Expected: PASS。
- [ ] Step 6: 提交：git add schema.yaml scripts/kb.py tests/test_decisions.py && git commit -m "feat(kb): decisions type with ADR identity and topic checks"。

## Task 2: Bindings, refs, archive by ADR ID

**Files:** Modify scripts/kb.py; Modify tests/test_decisions.py。

**Type:** build — 测试是 RED 工件；实现体按 Interfaces 自行设计。

**Interfaces (Produces):** check_binding(root, cfg, f, name, value, id_map, active_map) -> list；cmd_refs(args) -> int；cmd_archive 支持 --superseded-by ADR-NNNN；main() 注册 refs。

- [ ] Step 1: 追加失败测试（A6–A10、A12）：
  - test_decision_points_to_archived：两份 ADR，archive 旧 ADR 时 --superseded-by ADR-0002；spec 的 Decision 指向 ADR-0001 → check 退出 1，输出含 is archived 与 ADR-0002。
  - test_decision_field_required：spec 无 Decision → 输出含 missing Decision。
  - test_na_requires_reason：Decision 值为裸 N/A → 输出含 N/A requires a reason。
  - test_na_with_reason_ok：默认 fixture 的 N/A — reason → check 退出 0。
  - test_duplicate_decision_id：Decision 写同一个 ID 两次 → 输出含 duplicate ADR in Decision。
  - test_spec_binding_archived：plan 的 Spec 指向 docs/archive/specs/old.md → 输出含 is not active。
  - test_spec_binding_draft：plan 的 Spec 指向 draft spec → 输出含 is not active。
  - test_spec_field_required：plan 无 Spec → 输出含 missing Spec。
  - test_spec_binding_ok：spec set-status active 后 plan 指它 → check 退出 0。
  - test_refs_lists_bindings：refs ADR-0001 输出 1 binding(s) 与 spec 路径。
  - test_refs_unknown_id：refs ADR-9999 退出 2 且输出含 unknown ADR。
  - test_archive_adr_with_id：archive --superseded-by ADR-0002 --reason absorbed 后 archive INDEX 含 ADR-0002 与 absorbed，check 退出 0。
  - test_prose_mention_ok：正文提及已归档 ADR、Decision 写 N/A — reason → check 退出 0。
- [ ] Step 2: 跑 RED：python -m unittest discover -s tests -p "test_decisions.py" -v。Expected: FAIL。
- [ ] Step 3: 实现。Decision 绑定：N/A 必须有理由；否则逐项校验 ID 格式、重复、存在性、状态必须 active，归档错误带 successor。Spec 绑定：必须 docs/ 开头且 .md 结尾、无反斜杠；不存在报 unknown spec；不在 active 索引报 is not active；类型非 specs 报 not a specs doc；状态非 active 报 is not active (status ...)。refs：校验 decisions 已启用与 ID 存在，扫描 active 文档的 Decision 字段输出 kb refs <ID>: N binding(s) 与逐行 path (type, status)，未知 ID 退出 2。archive：--superseded-by 匹配 ADR-NNNN 时校验目标为 active ADR，archive 行存 ID 字符串。main 注册 refs 子命令。
- [ ] Step 4: 跑 focused GREEN：同上。Expected: PASS（21 tests）。
- [ ] Step 5: 全量：python -m unittest discover -s tests -v。Expected: PASS。
- [ ] Step 6: 提交：git add scripts/kb.py tests/test_decisions.py && git commit -m "feat(kb): bind spec/plan to active decisions, add refs and ADR-id archive"。

## Task 3: Docs, full suite, real-workspace regression

**Files:** Modify SKILL.md; Modify README.md; Modify decisions.md。**Type:** apply。

- [ ] Step 1: SKILL.md 加 Decisions (opt-in) 一节：decisions 类型、位置即状态、Topic 唯一、三个字段、绑定只指向 active、kb refs、opt-in 方式。
- [ ] Step 2: README.md 类型表加 decisions；收养步骤加 decisions: docs/decisions 与 archive/decisions；命令表加 kb refs。
- [ ] Step 3: decisions.md 追加 KB-8（位置即状态）、KB-9（稳定 ID 与绑定/提及分离）、KB-10（opt-in 且无 draft）、KB-11（一议题一权威靠 Topic）。
- [ ] Step 4: 全量 python -m unittest discover -s tests -v。Expected: PASS。
- [ ] Step 5: 真实工作区只读回归：python scripts/kb.py check --root D:/Jingdong/colorless_dragon/Decision_model_jev 与 .../intent_loop_intent_draft_v2，两条均 kb check: OK 且退出 0。
- [ ] Step 6: 提交：git add SKILL.md README.md decisions.md && git commit -m "docs(kb): document decisions protocol"。

## Definition of Done

- A1–A13 全部 PASS，证据见 Spec Coverage。
- 端到端：临时 fixture 工作区跑通 新建 ADR → spec 绑定 → 归档 ADR → refs 报告，并留下输出。
- 全量 suite 一次通过；无未关闭 Critical/Important。
- 人工 gate：无（A13 由本会话执行并记录）。

## Self-Review Notes

- 覆盖：A1–A13 全部映射；无空任务。
- 负向探针：删 Topic 行 → A5 失败；Decision 指归档 ADR → A6 失败；Spec 指 draft → A8 失败；删 refs 子命令 → A9 失败。
- 类型一致：build_adr_id_map 统一返回 (errors, id_map)。
- 路径：交付物均在 kb 仓；docs/specs 与 docs/plans 已验证不被忽略。