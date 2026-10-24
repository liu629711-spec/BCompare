# mode3 带引擎 → reacmp 移植规格（2026-10-16，主会话）

## 已验证（34/52 存档 oracle XML 全绿）
架构层全部定案，证据 = `runs/gateb-*`（D1、S1–S7、off≥1994 全部、1989..1993 边界、
big1、k50、K2/K200/neg 的越界例）：

1. **CLI 恒走纯 mode3**（描述符 0x140e71510 vtable[1]=140e73b40）：无锚点、无门 B、
   **每个区间从首带起分带**。D1 判别（min=4500<5000、0 重复 key、块距 4500 → 不配对）。
2. **带**：box = [cur .. min(end, cur+1992)] 两侧独立；单侧耗尽 → 每次 200 行孤儿块
   （step +199）；游程发射后盒末裁到 cursor−1（尾抑制）；无游程带 → NW 消费到盒末、
   裁剪坐标续推；H1（无游程带一次吞表末）已证伪——平推成立。
3. **游程**：盒内 wave（对角首触序）沿 key 相等延伸，**越过盒界直到表末**
   （K=200/off1900 全配证明）；候选门 `weight>500`；行权非空白 len+30 / 空白 2*len+50。
4. **消解**：按 (-weight, startR, startL) 排序，嵌套截断 min(ΔL,ΔR)/平移 max/击杀，
   发射序 (startR, startL)。
5. **param_6=1 恒真** ⇒ 候选不盒裁剪、不重加权；gap NW（游程前）用全消费模式。

## 开放细节（18/52 失败，全部带边界处 NW 交互，非架构、非打分函数）
产品 `interval_nw` 已在 120/120 fuzz + 133/133 m26 上与 BC 逐行全等 ⇒ BC 的 NW 语义
= 产品 NW 语义。模拟器失败签名均为 `want 对角 / got 孤儿`（或反向），发生在
**右/左剩余 < 盒宽** 的裁剪带。候选解释（移植后用门禁+fuzz 裁决，勿在此硬凑）：
- 140e74660 的 stop_at_edge 在**整表尾带**用 param_6=1 ⇒ 任一轴到 0 即停并裁
  `*param_4/*param_5`（sim 已实现）——但游程前 gap-NW 是 param_6=0，不裁；
- 或 140e733b0 对裁剪后 box 的 `+0x84/+0x5c` 尺寸与 NW 实际矩阵尺寸不一致
  （BC 的 NW 界取 `140e722a0` 钳制值而非盒值）。

## 接入点（product/core/src/align.rs）
- `interval_pairs_at` 现走"锚点 LIS + NW"（= 140e74b60 模型，**非 CLI 实况**）。
- 移植：新增 `mode3_interval(ls, rs, lk, rk, plan)` —— 带循环 + 游程收集/消解 +
  调用**现有** `interval_nw`（打分/平局不动）与现有 key/权重工具：
  `plan.left_key/right_key`（hash id 判等）、`plan.important_text(..).len()`（行权
  len+30 系；空白判定 = line_is_unimportant；注意 BC 权重是**去空白文本长**，
  与 sim 的 nw_text 一致 ⇒ 用 `nw_score_text(..).len()`）。
- 带尺寸 W=1993、候选门 500、块 200 全部做成模块常量（可配）。
- 小区间（两侧 < W）首带即全表 → 与现模型行为一致性由 fuzz 回归证明；
  **替换**（不是分支）`interval_pairs_at` 的区间处理为 mode3——因为 CLI 实况如此，
  双模型分支=个例门控，违背纪律。
- 性能附带收益：NW 阵被限制在 ≤1993×1993/带 ⇒ §21.6 大区间 OOM 缺口关闭。

## 验收序列
1. cargo test（core 201 单测须绿；行为改变会红——逐个对齐 oracle 真值再改测试，
   不许反向迁就）。
2. m26 133、fuzz 120（离线，产品二进制 vs 存档 XML）。
3. `cargo test --test large_input`（性能红线）。
4. Oracle 门禁串行（run_cli --candidate reacmp）+ 残留进程检查。
5. gateb-* 52 例逐行重放（产品 vs 存档 oracle XML，含 18 个开放细节例的最终裁决）。

## 收口状态（2026-10-16 夜，M5.5-17）

模拟器 **119/137**（路由器 `L>8∧R>12`→band，否则 handler；`min(L,R)<3`→band），
产品实况 **104/137**（产品未带 `min<3` 例外：该例外在 2×2 格修 2 例、但把实语料
打红 core 1/m26 2，故不采纳）。两处模拟器修复（权重版 same-key + `similar`
状态）已实证；LIS 序分歧（左序=实语料验证 vs 右序=合成格偏好）为**唯一剩余
差异源**，取舍=实语料优先。

剩余 18 例带边界族（`W-off*`/`K*-off*`/`neg-*`）为 `stop_at_edge` 裁剪次生差。
存档真值 `runs/gateb-*`（137 例）继续作为免费回归。
