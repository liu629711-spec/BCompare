---
name: reacompare-tailbox-state
description: 带边界 18 例攻坚收口——尾 NW 盒独立于采集窗（cursor+1999，第十例产品改动），137/137 模拟器、门禁
  487/0、+7 来源为在案残留未知
metadata:
  node_type: memory
  type: project
  originSessionId: sess_ae16c106-965c-4d23-83db-b31f5213aea8
---

**M5.5-30（2026-10-17，第十例产品改动：mode3 尾 NW 双盒）**。关闭 [[reacompare-m5-mode3-router]] 记录的 gateb 合成语料 104/137 中的带边界族 18 例。

- **根因**：`140e73b40/140e733b0/140e74100` 解码里采集盒与尾 NW 盒同源（都应 cursor+1992），但 BC 真值要求**尾盒 = cursor+1999（宽 2000）、采集盒保持 1993**。W=1993+WT=2000 双盒 ⇒ 模拟器 **137/137 全过**；WT 邻值（1994-96、2001-03）、4000/5000/∞ 全劣（114-118），全局 W=2000 仅 121 且破 off1992/1993 收集边界——两盒必须是两个量。
- **判别探针**（诚实门控后才动产品）：`gateb_tailbox_probe.py`（K=2 判别力不足，如实记录）、`gateb_tailreach_probe.py` **TB1-k20-off1990** 把游标推到新位置 (20,2010) 独立钉死 2000（单盒 DIFF/双盒 MATCH）、`gateb-tailbox2`（12 例两模型无分歧）。runs: gateb-tailbox/tailreach/tailbox2-20261017。
- **产品**：`align.rs::MODE3_TAIL_WINDOW=2000`，仅 `runs.is_empty()` 尾分支；裁剪回写 `cl = tail_l + 1 - rem_l`。
- **验证**：core 223、CLI 141+151+118、m26 0 失配、fuzz 120/120、large_input 5/5（1.06s）、产品重放 167/182（剩 15 = 在案 handler LIS 序小区间格，非新机制）、门禁 **M5530-tailbox-01 = 487/0**。
- **在案残留**：+7 的代码级来源未定位（候选：游标前进回写 / 窗口格阵取整 / param_6 分支）。行为已钉死，来源待大语料再攻。
- **制品**：`_scratch/mode3/simulate_mode3.py`（SIM_W/SIM_WT/S_RAW/NW_TIE 旋钮，S_RAW/NW_TIE 两个假设已证伪）、`align.rs.final-tailbox-20261017`。
- **方法教训**：分数变体扫描排除法 + 角部格级对照（oracle 路径在我们的 S 下总分更高 ⇒ DP 盒几何问题而非平局/分数）是定位引擎级差异的高效组合；NW_TIE=up 曾把 5 例小区间格"顺带"变好但 -2 例——参数实验必须全量对拍防局部巧合。

**How to apply:** 动带引擎前跑 `gateb_product_replay.py`（现为 182 例含 45 新探针夹具）+ m26/fuzz。带边界族不再是差异；剩余合成差异只有 AX/MF/GR 15 格（LIS 序取舍）。相关：[[reacompare-m5-state]]、[[reacompare-m26-weighted-diff]]。
