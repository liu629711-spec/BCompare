---
name: reacompare-maintenance-state
description: 合成语料收口 + 维护基线（762/762 门禁含 labels 佐证）、Oracle 串行纪律覆盖 pytest、冻结清单计数已清除
metadata:
  node_type: memory
  type: project
  originSessionId: sess_ae16c106-965c-4d23-83db-b31f5213aea8
---

2026-10-17 维护会话：合成语料（gateb 带边界族）正式关闭，转入回归节奏。手册在 `product/docs/12-maintenance-regression.md`（基线快照表 + 复验漏斗 + 教训），docs/11 §31 记录收口。

**当前维护基线（全部实测）**：core 223 / CLI 141+151+118 / m26 237 例 0 失配 / fuzz 120/120 / 仿真器 182/182（WT 默认已更正 2000）/ 产品重放 167/182（失败恰为 [[reacompare-m5-mode3-router]] 在案 15 例 LIS 序格）/ **官方门禁 `M5531-maintenance-02` = 762/762**（含 reference 英文 5.2.6.32774：anchor 212×2 + labels 佐证 31/31 + layout/folder 双安装全绿；[[reacompare-tailbox-state]] 那例 not_run 收口——英文安装 harness `enabled=True` 随时可用）/ harness pytest 157/157。

**三条纪律教训（本会话踩中并修复）**：
1. Oracle 串行纪律**覆盖 pytest**——`test_oracle_live.py`/`test_process_tree.py` 会真启 BComp.com，与门禁并发出过 3 例 exit 107 假阴性；串行重跑全绿。任何碰 Oracle 的电池一次只有一个。
2. **禁止冻结清单计数**——锚点 append-only（101→212），四处硬编码 `101`（test_runner、test_oracle_live ×2、run_cli 标签）已改为与 `man_mod.load_anchors()` 动态一致；今后加锚点不改测试。
3. 仿真器默认值必须等于已验证模型（§30 双盒定案后 WT 默认滞后已修）。

**How to apply:** 任何后续改动按 docs/12 §2 漏斗复验（离线→性能→仿真器→门禁串行）。合成语料若再开新攻坚，先读 §5 在案差异避免重复劳动。
