---
name: reacompare-m5-mode3-router
description: M5.5-17 mode3 带引擎移植收口——CLI 是双引擎+路由器（L>8∧R>12 走 band，否则 handler），实语料全绿、门禁 265/0、gateb 合成 104/137 已知取舍
metadata:
  node_type: memory
  type: project
  originSessionId: sess_5433d281-7de0-4965-9589-4247fd200b46
---

**M5.5-17（2026-10-16，第七例产品改动：mode3 带引擎移植 + 双引擎路由器）**。M5.5-16 只是"移植前必须解决的张力"，本会话把移植做完并定案架构。

**架构定案（推翻"CLI 恒走纯 mode3"）**：CLI 是**双引擎 + 按区间侧数路由**。
对 42 个 `runs/gateb-mode*` 存档 cell 逐格核对形状签名（ANCHOR=有 `similar`
行/非位置配对；WINDOW=头右孤+位置 `different`），得规则 **`L > 8 且 R > 12`
→ band（`140e73b40`），否则 handler（`140e74b60` 锚点 LIS 链）**，**42/42
零误分类**。关键词是**按侧且不对称**：(22,12) 是 handler 形状而 (12,22) 是
band 形状，不能写成 min/max 谓词。§23.4/§24.3 的"锚点不抢先外层门"张力由
此消解：**不需要额外门**，两个引擎各管一段。`min(L,R)<3` 的 2×2 格由 band
的 NW 反走产生 oracle 形状（`a,B` vs `b,A` → `L0` 孤 + `B~b` similar）。

**离线模拟器 `_scratch/mode3/simulate_mode3.py`（102→119/137）**，两处修复：
① **same-key 分数用权重族**（`FUN_140e74a70` = `job+0xb0` 数组 = `140e75c50`
的 `len+30` 族），**不是文本长度**——单字符行同键分数 4→124，正是小区间形状
判据；② 模拟器缺 `similar` 状态（raw 等→`same`、折叠 key 等→`similar`）。
另加 `handler_rows`（`140e74b60` 忠实模型：前缀/后缀裁剪+唯一-唯一配对+
patience LIS+递归+头侧 NW）与路由器；`ENGINE=band|handler|auto` 可单引擎对照
（band-only 114、handler-only 32、router 119）。

**产品落地**：`align.rs::interval_pairs` 改为路由器（band 分支保留全部解码
细节 W=1993/候选门 500/200 行孤儿块/param_6=1 尾抑制），handler 从
`pre-mode3-backup/align.rs.20261016` 恢复。**实语料全绿**：core **201/201**
（修前 5 红）、CLI 141+151+118、fuzz **120/120**、m26 **133/133（0 失配）**、
offline_check 101+101+31、large_input 5/5、官方门禁
`M5525-mode3-router-01` **265 pass/0 fail**（唯一 not_run = reference 安装
不可用的 labels 佐证）、无残留进程。

**已知差异（记录，不硬凑）= gateb 合成语料 104/137**。剩 33 例含带边界族
（`W-off*`/`K*-off*`/`neg-*`，18 例，`140e74660` 的 `stop_at_edge` 裁剪次生差）
与 5 个小区间格。小区间格根因单点：**LIS 迭代序**——实语料验证的
`lis_overwrite_left`（左序）与 oracle 的右序臂在**交叉平局**上相反。
右序实测 fuzz 116/120、m26 4 失配、gateb 117/137（+13 合成格）⇒ **实语料
优先，保留左序**。两变量（权重版 same-key、LIS 序）已由 A–F 六配置矩阵隔离：
权重版对实语料零效应，LIS 序是唯一剩余分歧源。

**Why:** 单看合成夹具会得出"纯 band 正确"的错误结论并打红实语料；真实
BC 的行为按**区间规模**分派两套引擎，夹具设计必须覆盖路由器两侧。
**How to apply:** 改对齐层先跑 `gateb_product_replay.py`（137 例存档 oracle，
零成本）与 m26/fuzz 双基线；**实语料（m26 133 + fuzz 120）是质量闸，
合成格分歧不得反过来牺牲实语料**。制品 `_scratch/mode3/{simulate_mode3.py,
gateb_product_replay.py,sim_replay_fuzz.py,align.rs.final-20261016,
reacmp-anchor.exe}`；存档 `runs/gateb-*` 为免费回归真值。
相关：[[reacompare-m5-state]]（§23/§24 的移植阻塞与本轮收口）、
[[reacompare-m26-weighted-diff]]、[[bcompare-clone-goal]]。
