---
name: reacompare-a3-round2-u1
description: A-3 第二轮门禁清零（49/49 XML 逐字节一致）与 U1 定案的实测结论——BC 报告格式的全部实测规则
metadata:
  node_type: memory
  type: project
  originSessionId: sess_5433d281-7de0-4965-9589-4247fd200b46
---

ReaCompare A-3 第二轮（2026-10-13）把首轮门禁的 21 项发现全部闭环，终态
`A3-folder-gate-serial-04`：75 = 66 过 + 9 已知分歧 + 0 失败，**49/49 XML
与活体 BCompare 逐字节一致**。接 [[reacompare-a2-a3-state]]。

BC 文件夹报告的实测规则（全部 O 级，写在 `product/dir/docs/EVIDENCE.md` §9）：
- `<modified>` 月/日/时不补零，分/秒两位（`2026/1/1 8:00:00`）
- 行序 = 数字段按数值 + 首个差异位置用 `CompareStringW(NORM_IGNORECASE)`；
  **`CompareStringW` 不支持 `SORT_DIGITSASNUMBERS`（传了返回 0），那是
  CompareStringEx 的旗标**——这个坑实测过
- kind 冲突 = 两个单侧行（目录侧展开 + 文件侧），不合并 diff
- 未跟随 junction：自身 mtime、`<size>0</size>`、目标不同判 diff（默认判据下）
- `timezone:left/right±N` 被 BC 拒绝（106），只有 `timezone:ignore` 有效
- `attrib:z` 被接受（未知字母惰性）；命名属性集**取代**默认 size+timestamp
- 内容判据（CRC/binary/rules-based）**取代**属性比较
- 目录 `<size>` = 整个子树文件字节和，**按侧分别渲染**（两侧不同字节数时
  侧盲求和会露馅——deep 夹具抓到的）
- 容差边界 `diff<=N`、IgnoreDST 整小时、timezone:ignore 语义第一版就对

U1 定案（`product/verify/probes/U1-FINDINGS.md`）：.c 下除注释/空白外一切
单类差异都重要且不被 ignore-unimportant 折叠。

**Why**: 这些是第二轮用活体 Oracle 定案的格式规则，引擎已按它们实现并通过
字节级门禁；后续任何重构以 `A3-folder-gate-serial-04/` 为回归基准。

**How to apply**:
- 门禁驱动 `tools/_audit/a3-folder-gate.py` 会把 `bc_criteria`（含 cli_flag
  等价 token）写进 gate-results.json；`make_cases.py` check 4 用它锚定清单，
  锚定指向 serial-04，该目录不可删。
- BC 接受 version/owner/group/permissions/ignore-unimportant（exit 0），
  引擎拒绝是已记录分歧，实现它们时门禁产物 `oracle/*.out` 就是规格。
- 子代理派发通道整轮被供应商拦截（探针也拦），全部工作在主会话完成——
  再遇拦截直接主会话干，别反复重试派发。
