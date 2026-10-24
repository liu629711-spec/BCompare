---
name: reacompare-a2-a3-state
description: A-2/A-3 交付与验收状态——产品 reacmp 通过官方门禁、A-3 的 21 项 Oracle 发现、子代理派发被供应商拦截的教训
metadata:
  node_type: memory
  type: project
  originSessionId: sess_5433d281-7de0-4965-9589-4247fd200b46
---

ReaCompare 于 2026-10-13 完成 A-2/A-3 交付与串行验收（接 [[reacompare-a1-harness-state]] 之后）：

- **A-2（product/core + product/cli）**：Rust 文本核心 + `reacmp.exe`。191 cargo 测试全绿；离线对拍 45/45 锚点、45/45 归一化 XML（门槛 ≥41）、29/30 布局（唯一 fail 是有案可查的 `mixed-side-by-side` candidate 已知差异，不是回归）。二进制在 harness 约定路径 `D:\Rea\product\cli\target\release\reacmp.exe`，harness 零改动接入。
- **A-3（product/dir + product/vfs）**：只读 FileSystem trait + criteria 引擎 + 75 夹具；107 cargo 测试全绿。
- **A-3 串行 Oracle 门禁**（`tools/_audit/a3-folder-gate.py`，产物在 `product/verify/runs/A3-folder-gate-serial-01/`）：17 硬过（含 4 个对活体 BC 逐字节一致的 xml 用例）、37 状态一致、**21 项发现**记录在 run 的 REPORT.md（F1-F8）：BC 时间戳不补零（U-M3-3 定案）、file-vs-dir 冲突 BC 拆成两个 orphan 行而非合并 diff（U-M3-8 推断被证伪）、`timezone:left+1` BC 退出 106、**BC 接受 version/owner/group/permissions/ignore-unimportant**（引擎的"未探测即拒绝"成已知分歧）、junction 未跟随仍判 diff、attrib+CRC 语义分歧、特殊字符名的行序不同。第二轮 = 按 BC 修引擎 + 把 61 个 predicted 期望升级为 observed。
- **产品第一次过官方 harness**：`A2-gate-serial-01`，257 项 256 过（anchor/candidate 45/45，layout/candidate 29/30）。

**Why**: 这些数字是"产品"的（is_product=True），不再是旧原型 bcx.exe 的；引用时必须区分。

**How to apply**:
- 子代理派发曾被供应商连续拦截三次（"request has been blocked due to unusual activity"，含最小探针），对策：改为主会话亲自执行；拦截可能是暂时的，重试最小探针即可判断。
- 产品/verify 曾处于"封存"状态，但产品建成使两个测试前提失效（reacmp 从缺席变为存在），已按意图改写：`test_product_candidate_seam_is_declared_and_now_built`（钉住接缝已建成）+ `test_runner_marks_unavailable_candidate_as_not_run`（改用合成缺席候选 D:\nowhere\none.exe）。
- 夹具/golden 全部只读；新探针放 `tools/_audit/`，run 产物放 `product/verify/runs/<name>/`。
- 离线对拍脚本：`product/cli/tools/offline_check.py`（绝不调 BCompare，读 golden + harness.normalize 只读导入）。
