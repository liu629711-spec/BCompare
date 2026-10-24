# 08 — 文件夹五个已解锁 criteria：实现与验收（2026-10-14）

A-3 第二轮把 `version` / `owner` / `group` / `permissions` / `ignore-unimportant`
记为"BC 接受但引擎拒绝"的已知分歧。本轮把它们全部实测并实现。前置阅读：
`probes/U4-FINDINGS.md`（O 级行为表）、`06-a2-a3-acceptance.md`、`04-milestones.md`。

## 实测结论（U4 系列，11 轮探测）

细节见 `U4-FINDINGS.md`，要点：

1. **`version`** 比较 PE 的 **FileVersion**（ProductVersion 差异被忽略），
   **有方向语义**（高者 `ltnewer`/`rtnewer`），**压过其它所有判据**（包括
   size 与 timestamp）；无版本资源的一侧视为更旧；**必须是有效 PE**（只有
   `VS_FIXEDFILEINFO` 签名而没有 `MZ`/`PE\0\0` 的 blob 被当作无版本）。
2. **`owner`/`group`/`permissions`** 在 Windows 上**完全 inert**（连 NTFS
   deny ACE 差异都不影响）。
3. **判据集合语义（修正了 A-3 的一个模型错误）**：给任何一个 token 都会
   **清空**默认的 size+timestamp；`criteria X` 的含义是"只比较 X 指名的东西"。
   因此 `ignore-unimportant` 单独出现时**什么都不比较**（size 差 2048 字节、
   mtime 差 2 小时仍报 `same`）。
4. **`ignore-unimportant`** 只在 **rules-based** 内容比较下折叠（binary/CRC
   不折叠）；折叠覆盖注释差异与空白差异，语法文件与纯文本都算（u4g）。
5. **`<size>` 千分位**（`55,192`）与 **0 字节文件的 `<size>0</size>`**：前者
   与 locale 无关，后者解决了 `report.rs` 里标 **U** 的悬案。

## 代码落点

| 文件 | 改动 |
|---|---|
| `vfs/src/pe.rs`（新） | `file_version()` + `is_pe()` 结构校验；签名扫描只在有效 PE 内进行 |
| `vfs/src/lib.rs` | 导出 `pe` 模块 |
| `dir/src/criteria.rs` | `ContentCriteria` 增 `Version`/`Owner`/`Group`/`Permissions`；`Criteria.ignore_unimportant`；`parse` 改为"空串才用默认对"的集合语义；`NotProbed` 分支删除 |
| `dir/src/tree.rs` | `version_order()`（PE 目录/文件判定 + 方向 + outrank 顺序）；`rules_based_only_unimportant()`（委托 M2 引擎）；inert 三件套显式空分支 |
| `dir/src/report.rs` | `grouped_size()` 千分位；`ReportOptions.ignore_unimportant` → `<ignoreunimportant/>` |
| `dir/src/bin/reacmp-dir.rs` | 传递 `ignore_unimportant` |
| `dir/Cargo.toml` | 新增 `reacmp-core` 依赖（rules-based 复用 M2 重要性引擎） |
| `core/src/importance.rs` | 新增 `folder_rules_based_ignoring_unimportant()` |
| `dir/tools/make_fixtures.py` | 三个新树对（`versioned`/`rules-based`/`posix-metadata`）；`_pe_blob()` 改为 patch 真实系统 DLL |
| `dir/tools/make_cases.py` | 参考模型：五 criteria 建模、`version` 方向与 outrank 顺序、`rules_based_only_unimportant` 独立实现、集合语义；删 5 个 `reject-*-not-probed`，加 9 个 `crit-*` |

## 验收（全部串行）

| 关卡 | 结果 |
|---|---|
| `cargo test`（core 176 + vfs 35 + dir 88 + cli 20） | **全绿** |
| `pytest tests` | **157 全绿** |
| `compare_fixtures.py` 引擎自检 | **79/79**（observed 25/25、predicted 54/54） |
| 文件夹串行门禁 `A3-folder-gate-serial-07` | **79 = 75 过 + 4 info + 0 失败** |
| `offline_check.py`（文本语料，回归确认） | 锚点 101/101、布局 30/31 |
| 官方 harness `M2-criteria-serial-01` | **429 = 428 过 + 1 已知 + 0 错误**（锚点 101/101） |
| 残留进程 | 无 BComp/BCompare |

门禁迭代过程本身就是证据：serial-05 抓出 3 个分歧（合成 blob 不被 BC 认、
`ignore-unimportant` 单独出现的集合语义），serial-06 抓出 1 个（version 压过
size），serial-07 归零。

## 已知差异 / 后续

1. ~~`version` 的文件名掩码（BC 只对 `.exe`/`.dll` 等 EXE 格式生效？）未探测：
   当前实现对任意扩展名都尝试读 PE。若某扩展名在 BC 下被排除，会是一个新的
   分歧点（探测成本低，可作 U5）。~~
   **已探测并修复（U9，2026-10-14）——原怀疑属实，且是真实缺陷。**
   `probes/U9-FINDINGS.md` 实测：BC **只对 8 个扩展名**读版本资源
   （`.exe` `.dll` `.ocx` `.scr` `.sys` `.drv` `.vxd` `.386`），其余一律 `same`
   ——**即使文件是真的 PE**（`.cpl` 是真 PE 却被忽略；`.txt` 携带真 PE 字节也被忽略）。
   反直觉的两个成员是 `.vxd` 和 `.386`（老式驱动格式），
   而 `.cpl`/`.efi`/`.ax`/`.tsp`/`.olb`/`.vbx` 虽像可执行格式却被排除。
   名称门控与内容要求是**两个独立条件**：名称过门即比较，内容是文本也照样报方向
   （u9c `textonly.exe`）。名称形状：取**最后**一个扩展名、ASCII 大小写不敏感、
   **精确匹配**（`.exe2` 不算）；目录名中的点不影响。
   已在 `vfs/src/pe.rs::version_applies_to` 实现，并在 `u9_folder_gate.py`
   **18/18 逐字节对拍**。修复前 24 个扩展名中 16 个与 BC 不一致。
2. 三个 inert criteria 在 Linux/macOS 上应当是有意义的（文档明说 Unix）；本
   实现只覆盖 Windows 行为，跨平台语义未探测。
3. `binary`/`CRC` 与 `ignore-unimportant` 的组合已确认**不折叠**；产品实现
   与之一致。
4. ~~文件夹 `ignore-unimportant` 对**目录行/单侧行**的影响已在 u4d 观察（结构
   行不受影响），但未建锚点——如需覆盖可加一组 `iu-*` 用例。~~
   **已建锚点并实测（U10，2026-10-14）**：`u9_folder_gate.py` 的 10 个 `iu-*`
   用例逐字节通过。实测规则：
   - **目录行从不携带 `status`**（`ignore-unimportant` 下也是 6/6 无 status），
     结构行完全不受内容修饰符影响；
   - **单侧文件行仍报 `ltonly`/`rtonly`**，与默认对完全相同（单侧行无法被"不重要"折叠）；
   - `ignore-unimportant` **独立出现 ≡ 什么都不比较**（与 u4h 一致）；
     加 `rules-based` 才折叠；**token 顺序无关**（两种顺序都通过）。
   产品在这些行为上**本来就正确**，无需改代码——缺的是护栏，现已补上。
