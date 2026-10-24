---
name: reacompare-m7-hex-channel
description: M7 二进制/十六进制通道收口：hex-report 动词面（options 106 ≠ 表格 105、缺左 106/缺右 107/零文件 107/单文件 106）+ 字节对齐槽/块模型 + interleaved diff 两趟行序（V3 缺陷）+ verify/hex 13 golden + 门禁 858/858
metadata:
  node_type: memory
  type: project
  originSessionId: sess_7c8a1e10-9f31-4a52-8f0e-2b6d9c3a5e11
---

2026-10-18 M7（功能 5，U5）全程收口，文档 `product/docs/14-m7-hex-channel.md`。探针 `probes/m70_hex_surface / m70b_hex_model / m70c_hex_orphan / m70d/m70e/m70e2/m70f/m70g`（后四批为会话内联跑，exit 已归档为 `runs/m70*/m70-session-exits.json` sidecar）→ `runs/m70*`（~40 报告；每批跑前/跑后残留 zero）。

**通道**：唯一动词 `hex-report`（`file-report`/`binary-report`/无 layout/`load` 两段式全 106）。帧与表格路同构：`16 进制比较(H)`/`Hex Compare`（m70e 英文孪生）、斜杠 `Produced:`、空行、`Mode:  All`（summary 无）、双文件行；`title:` 换首帧行。**拒绝面与表格路不同，勿复制**：options/output-options/bogus-layout/单文件/缺左文件 = **106**，缺右文件/零文件 = **107**（m70/O1-O3/V2/Y8-Y10）。data-report 跑 .bin 会走表格路写编码错误（H6），非本通道。

**模型**：字节对齐=现有 Myers 字节 diff；间隙先 `min(gl,gr)` 配对变更槽（summary 各算 1 差异字节）再孤儿槽；行=8 槽；块=同质行极大段（Y11 收尾块把配对+孤儿混成单 `<>` 块）；sbs 行=左字段(33)+' '+标记区+' '+右字段(33)，标记区宽=2 当且仅当报告有 diff 行（Y1 vs Y2），标记文本只在块首行；某侧全程无字节⇒该列整体省略（Y13）；规则线=全局最大行宽（Y4）；interleaved 同行合并输出 `offL(8hex) offR field`，偏移恒 8 位不回绕（Z7）；**diff 块两趟输出：先该块所有含左字节的行、再含右字节的**（V3）；summary 序 same→left→right→diff，零行省略（V5 双侧 56/31/1/1 钉死配对模型）。空-空无体行（Z6）。

**本轮抓到并修复的产品缺陷**：interleaved diff 块行序（产品原逐行 L/R 交错；重放 29/30 抓到）。core/hex.rs +16 单测；`core` 269、CLI 141/161/118。

**How to apply:** hex 改动按 [[reacompare-maintenance-state]] 漏斗：`cd extracted/_scratch/hex && python replay_hex_product.py`（30/0/1skip；唯一 skip = m70 H6 表格路细胞）→ core/CLI → 门禁 `--suite hex`（`--install current --install reference --candidate reacmp`）。golden 树 `verify/hex/` append-only 13 格（`tools/m71_add_hex_goldens.py`），harness 第六套件 + norm-3（hex 标题/四个 `…字节` 计数标签）。基线：门禁 `M71-gate-01` = **858/858**（819 + hex 26 oracle + 13 candidate）、pytest 158。残差：hex 的 `load` 组合未探、结构化偏移导航（PE/ELF 段映射）范围外未做。下一缺口：功能 4 文件夹同步/复制（U8）。
