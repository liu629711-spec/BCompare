---
name: reacompare-m2-state
description: M2 重要性引擎完成态——分词器/逐元素规则/leftsimilar 状态/101 锚点全绿，以及剩余已知差异和下一步
metadata:
  node_type: memory
  type: project
  originSessionId: sess_5433d281-7de0-4965-9589-4247fd200b46
---

M2（重要性引擎）已于 2026-10-14 完成并验收。接续 [[reacompare-a2-a3-state]]。

- **实现**：`product/core/src/importance.rs` 重写为真分词器（4 格式 + 25 格式 mask 表 + 跨行块注释/三引号状态）；align/xml/layouts 接线。关键词表用公开语言知识实现——**关键认识：verdict 只取决于"是否注释/空白"+重要元素逐字文本，关键词表内容不影响行为**，所以不复制 BC 格式表（合规红线）。
- **四个探测定案**（`product/verify/probes/U2-FINDINGS.md`，O 级）：①逐元素规则适用于混合行/跨行块注释/三引号体；Python Indent 重要、未知扩展名=纯文本（推翻 M1 假设）；②整行不重要的落单行报 `leftsimilar`/`rightsimilar`（非 leftorphan），iu 下折叠成 same 并**借用**最近成对行的 id（右借用渲染成自闭合空 `<text/>`）；③块内配对 tie-break：锚定配对（内容↔内容）在配对数不少于位置配对时胜出；④summary 计数顺序 + reference 英文安装版确认标签措辞。
- **验收**：cargo 196 绿 + pytest 157 绿 + offline_check 101/101 + 官方 harness M2-gate-serial-01 = 428过+1已知失败（mixed-side-by-side，A-2 遗留）+0错误；锚点 45→101（`tools/m2_add_golden_anchors.py` 生成，金标布局用 reference 英文版生成）。
- **已知差异（未锚定）**：多不重要行挨着替换块时 BC 的加权 diff 平局选择不同（需"删注释零代价"加权 diff，M2.6 候选）；21 个未实现格式回退纯文本（.java 大小写会误报 similar）；statistics 布局 I/U 列模型未实现。
- **下一步**：五个已解锁 criteria（version/owner/group/permissions/ignore-unimportant 文件夹侧，serial-04 归档即规格）或 M4 CLI 子集；见 [[reacompare-audit-findings]]。
