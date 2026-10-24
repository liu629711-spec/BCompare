---
name: reacompare-m8-sync-channel
description: M8 folder-sync (function 4, U8) — measured sync grammar/semantics,
  the update-vs-mirror model, flags, and the honest residual unknowns
metadata:
  node_type: memory
  type: project
  originSessionId: sess_ae16c106-965c-4d23-83db-b31f5213aea8
---

功能 4（文件夹同步，U8）于 2026-10-18 收口，docs/15 为正文。

**语法**：`sync [visible] [create-empty] (update|mirror):(left->right|right->left|all)`，
两旗标必须在 mode 之前、相对顺序任意；`mirror:all`/缩写 `lr`/旗标后置/畸形全 106；
无 load → exit 0 静默无操作；**半载（`load "<L>"`）→ exit 100**（既有 100 是 /qc 读不到输入，
此处复用）；命令行上的 `sync` 仍按名拒绝，只有脚本里的显式 mirror 才触发删除。

**语义**（Status 直接映射，`timestamp:2sec` 容差 = 实测边界 Δ2s Same / Δ3s 较新）：
update 拷"源较新 + 源孤儿"、保留源 mtime、**永不删除**、目标较新对不动；
mirror = update + 拷 Diff 对（源赢不论大小）+ **删目标侧孤儿（文件与非空目录，空源则清空目标）**；
kind-conflict 下 update 双方不动、mirror 删目标且不落地源项。
`create-empty` 只让"无文件子树"的源孤儿目录落地；**`visible` 会禁用 `create-empty`**，
但对删除/拷贝本身无效果。sync 服从 criteria（`criteria size` 下同尺寸判 Same 不拷）。

**How to apply**：副作用只出现在 CLI 执行器（`do_sync` 先建 SyncAction 计划再应用，
拷贝在前删除在后），`reacmp_dir` 保持只读（ADR-3 不变）。改 sync 语义前先跑
`cargo test --test script_exec`（9 个集成测试逐格对应实测）。

**在案残留未知**：(1) Oracle 的 filter 会约束 sync（H2b/F4b 不匹配则不删不拷），
产品 sync 用 `Filter::none()`，是已知差异而非静默行为；(2) kind-conflict 的
内部判定顺序无证据，按结果建模；(3) m81c C1 的两例单发（单对未拷贝、`criteria timestamp:2sec`
+update=105）在 m82 三次重复中均未复现，不入产品语义。

门禁 M82-gate-01：276/277（labels 因 reference install 不可用 not_run，既有状态）；
CLI 170（sync 9/9）、core 269、pytest 158、table 重放 175/0/12known、hex 30/0/1skip、残留 0。
下一缺口见 [[reacompare-maintenance-state]]。
