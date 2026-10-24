---
name: reacompare-m26-weighted-diff
 description: M2.6 RESOLVED 2026-10-14 — two-layer alignment fix (AnchorKey + closeness pairing); all gates green incl. U8 45/45.
metadata:
  type: project
---

M2.6（对齐/平局择路差异）**已于 2026-10-14 解决并全门禁验证**，不再是开放差异。文档定案在 `D:\Rea\product\docs\07-m2-importance.md` 已知差异 1。

**根因两层**（修复前曾误判为"不重要行零代价加权 diff"）：
1. **锚定层**：旧实现让无重要内容的行（注释/空白）共享一个 `AlignKey::Unimportant` 哨兵，Myers 会注释锚注释、抢占更优整体脚本。修复：`core/src/align.rs::AnchorKey` —— 有重要文本的行按重要文本锚定，无重要内容的行取每侧唯一键、永不参与锚定（配对交给块内层）。
2. **块内配对层**：BC 发射层（`FUN_140dc6c40` case 2）把 1×1 未匹配格记为成对行，`different` 行是算法选出的配对；帮助文档写明默认 Standard 对齐 + 可选 "closeness matching"。修复：`align::closeness_pairs` —— 块内单调相似度匹配，目标（重要文本 LCS 相似度总和, 配对数）字典序最大、平局取最早；全零相似度退化为位置 zip（保持 `al-replace-block` 三行 different 不变）。发射为文档序：左孤行、右孤行、配对（`emit_block`）。

**有界性**：块 >25 万格或预计工作量（cells×max_len²）>3200 万字符时回退位置配对，线性空间保证不破坏（`large_input.rs` 全绿）。

**验证链（全串行，Oracle 用 installed BComp.com 5.0.3.30240 / app 5.2.1.32035）**：
- 离线重放 `tools/m26_baseline.py`：产品 vs 磁盘 127 条已记录 BC 观测 **127/127**（修复前 5 处配对分歧：all-kinds-c、all-kinds-txt、comment-lead-c、comment-middle-c、tail-1v2-txt）。
- 配对模型离线拟合 `tools/m26_model_grade.py`：**205/205 配对**（197/205 全行；8 行失败是 lab 自身重要性近似：字符串内部、JS 正则、Python 缩进——产品分词器能处理）。
- 活 Oracle `probes/m26_weighted_diff.py` **6/6 SAME**（`runs/m26-weighted-probe-20261014T150040Z/`）。
- `cargo test` 189 全绿（含 7 个新 M2.6 回归测试）；`pytest` 157 全绿；`offline_check.py` 101/101+101/101+30/31；官方 harness `M2-gate-serial-02` 428 过+1 既有已知失败（mixed-side-by-side，与 M2 无关）。
- U8 护栏重跑 **45/45、0 已知差异**（`runs/u8-verify-20261014T153156Z/`）：唯一已知差异 `tail-tiebreak-1v2` 通过后已从 `KNOWN_DIFFERENCES` 移入 `u8_verify.py` 的 `CASES` 作回归护栏（10-m4-acceptance.md §7 已补记）。

**Why:** 平局择路差异不能靠改 Myers 权重解决——证据表明纯文本输入同样分歧，真正的规则在锚定资格与块内配对两层。
**How to apply:** 后续若再遇对齐分歧，先用 `m26_baseline.py` 对磁盘观测重放定位，再在 `m26_model_grade.py` 拟合模型，最后才动 `align.rs`；不要动 `myers.rs`（Myers 本身已与 BC 一致）。Oracle 永远串行、Job Object 包裹、结束后查残留进程。`criteria` 必须先于 `load`。相关：[[reacompare-m2-state]] · [[reacompare-m4-state]] · [[bcompare-clone-goal]]
