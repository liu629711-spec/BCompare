---
name: reacompare-folder-criteria
description: 文件夹五个已解锁 criteria 的实现定案——version 方向语义/PE 必需、owner 组 inert、判据集合清空语义、size 千分位
metadata:
  node_type: memory
  type: project
  originSessionId: sess_5433d281-7de0-4965-9589-4247fd200b46
---

文件夹侧 `version`/`owner`/`group`/`permissions`/`ignore-unimportant` 已完成并验收
（2026-10-14）。接续 [[reacompare-m2-state]]。归档：`product/docs/08-folder-criteria.md`、
`product/verify/probes/U4-FINDINGS.md`（11 轮探测 u4…u4k）。

- **version**：比较 PE **FileVersion**（ProductVersion 忽略），**方向语义**（高者
  `ltnewer`/`rtnewer`），**压过 size 和 timestamp**；无版本资源一侧视为更旧；
  **必须有效 PE**——只有 `VS_FIXEDFILEINFO` 签名而无 `MZ`/`PE\0\0` 的 blob 被
  BC 当作无版本（u4h），所以 fixture 现在 patch 真实 `C:\Windows\System32\version.dll`。
- **owner/group/permissions**：Windows 上**完全 inert**（NTFS deny ACE 差异都不影响）。
- **判据集合语义（修正 A-3 的模型错误）**：给任何 token 都**清空**默认 size+timestamp。
  `ignore-unimportant` 单独出现 = 什么都不比较（u4i：size 差 2048B + mtime 差 2h 仍
  报 same）。`criteria X` = 只比较 X 指名的。
- **ignore-unimportant** 只在 **rules-based** 下折叠（binary/CRC 不折叠），折叠覆盖
  注释与空白差异（纯文本也算，u4g）。
- **格式**：`<size>` 千分位逗号（`55,192`，与 locale 无关）；0 字节文件 `<size>0</size>`
  （原 report.rs 标 U 的悬案已解决）。
- **验收**：cargo 全绿、pytest 157、引擎自检 79/79、门禁 serial-07 = 75过+4info+**0失败**、
  官方 harness 428过+1已知（mixed-side-by-side）+0错。门禁迭代 serial-05→06→07 本身
  就是发现证据（3→1→0 分歧）。

## U9/U10 收尾（2026-10-14 已完成，两项"未探测"均已钉死）

**U9 `version` 扩展名门控 —— 原怀疑属实，是真实缺陷，已修复。**
实测（`probes/U9-FINDINGS.md`）：BC **只对 8 个扩展名**读版本资源：
`.exe` `.dll` `.ocx` `.scr` `.sys` `.drv` **`.vxd`** **`.386`**；其余一律 `same`
——**即使文件是真 PE**（`.cpl` 是真 PE 被忽略；`.txt` 带真 PE 字节也被忽略）。
- 两个**反直觉**成员是 `.vxd`/`.386`（老式驱动格式）；`.cpl`/`.efi`/`.ax`/`.tsp`/`.olb`/`.vbx`
  虽像可执行却被排除 → 这是**具体名单**，不是内容嗅探、也不是"所有 PE 类型"。
- 名称形状：取**最后**一个扩展名（`prog.tar.exe` 比较）、ASCII 大小写不敏感、
  **精确匹配**（`.exe2`/`.dllx` 不算）、目录名中的点不影响、无扩展名/尾部点忽略。
- **名称门控与内容要求是两个独立条件**：名称过门即比较，内容是文本也照报方向（u9c `textonly.exe`）。
- 修复前 **24 个扩展名中 16 个与 BC 不一致**。实现 `vfs/src/pe.rs::version_applies_to`；
  同步参考模型 `dir/tools/make_cases.py` + 夹具 `versioned` 树新增 `masked.*`/`included.vxd|.386`。

**U10 文件夹 `ignore-unimportant` 范围 —— 产品本来正确，只补了护栏。**
实测：**目录行从不携带 `status`**（结构行不受内容修饰符影响）；**单侧文件行仍报
`ltonly`/`rtonly`**（无法折叠）；修饰符**独立出现 ≡ 什么都不比较**；加 `rules-based`
才折叠；**token 顺序无关**。

**护栏**：`product/verify/tools/u9_folder_gate.py`（U9+U10 共 **18 例，逐字节一致**）。

**⚠ 探针陷阱（务必记住）**：`criteria` **必须写在 `load` 之前**才对报告生效。
首轮写反 → BC 对全部 24 个扩展名（含 `.exe`/`.dll`）都返回 `same`，看起来像"BC 完全不
比较版本"，与既有 serial-07 里 `left_higher.dll` 真报 `ltnewer` **矛盾**。
**结论与既有证据矛盾时先怀疑自己的探针**；照首轮结果行动会把本来正确的 `.dll` 改坏。

- **仍未探测**：其他老式驱动扩展名（`.mpd`/`.mup` 等）；掩码是否可配置（本次只测默认态）；
  三个 inert criteria 在 Linux/macOS 的语义。
