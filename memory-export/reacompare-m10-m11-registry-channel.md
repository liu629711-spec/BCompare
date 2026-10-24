---
name: reacompare-m10-m11-registry-channel
description: ReaCompare M10/M11 registry-report channel — locale-parameterized
  geometry (the key discovery), parse/encoding rules, goldens authored from
  the ENGLISH install and why, norm-5, gate 1018/1035 with the 17 in-case
  geometry failures
metadata:
  node_type: memory
  type: project
  originSessionId: sess_ae16c106-965c-4d23-83db-b31f5213aea8
---

M10/M11（注册表比较，功能 8 的 registry 部分，原缺口 U6 的 registry 半边）
已完成并全绿（2026-10-19）。`version-report` 仍未做。

**最重要的发现——sbs 表格几何是 locale 参数的**：列下界 = **表头标签宽度**
（中文 名称/类型/数据 = 2，英文 Name/Type/Data = 4），所以**同一 fixture
在中英文安装上表格宽度不同**（m101f 29 格双语同 fixture 对照实测）。后果链：
①产品渲染英文帧（dir/pic/hex 先例）→ ②金标准必须用**英文参考安装**生成
（中文金标准永远不可能被产品字节匹配）→ ③中文安装的 oracle 重放必然在表格
行 fail（17/23），这是**在案差异不是缺陷**，REPORT.md 的 "Registry suite
scope note" 记录完整轨迹 → ④中文几何由 `reacmp-reg/tests/corpus_cases.rs`
的 103 格归档表格（85 中文+18 英文）字节级锁定。**以后任何 locale 参数化
通道都先查这条**，别重复踩。

**实测模型**（docs/17，探针 m101..m101n 14 批；m101f/m101i 中英孪生）：
- 语法 `registry-report layout:<side-by-side|summary> [options:] [title:] output-to: [output-options:] [<L> <R>]`；layout 大小写不敏感（R17）。拒绝面：bogus/无 layout、坏 option token、output-options、1/3 文件 = 106；**缺任一侧 = 107**；**零文件 = exit 0 + BOM shell，带 `模式：  全部` 行**（picture shell 没有 Mode 行——两通道 shell 的实测差别）。
- 四个选项 token 全接受（display-all/matches/mismatches/ignore-unimportant）；ignore 无效果（注册表没有"不重要"类别，I1/I2）。display 设 Mode 行 + 过滤 sbs 表格（mismatches 丢 Same 行、matches 只留 Same 行），**几何在保留行上重算**（I4：规则线 24 vs 28）。
- **内容坏 ≠ 命令失败**：`parse_reg` 先嗅原始字节——**无 BOM + 含 NUL → Encoding 错误**（PNG 实证：PNG 含 NUL，ANSI 垃圾不含）→ `文件编码错误 (第 1 行)`，且**该侧无 basekey 后缀**；无 NUL 垃圾 → 头部检查 → `不被支持的类型`。错误行不产生计数。
- 文件行后缀 `:\\<basekey>`（**冒号后双反斜杠**）：公共键路径前缀（大小写折叠）；**解析出错但键行存活时后缀仍保留**（G3/C10，`compute_basekey` 必须无条件跑——曾因 gate 在 `error.is_none()` 上而 17 个测试挂）。
- **T1 翻案**：逗号续行**永不拼接**（`hex:68,65,6c,6c,6f,` + 缩进行 → 缩进行是新语句 → 解析错误 5:3）。早期"续行拼接"假设是错的，archived m101g fixture 字节为证。
- 计数（summary only）：same → left orphan → right orphan → difference，零省略，**无 unimportant 类别**。repack 的 的 不对称：左边独有带 的、右边独有不带、差异项**也带**。
- 排序：CompareStringW NORM_IGNORECASE + ASCII 数字串按数值，**先键后值**每层各自。
- 二进制数据按字节渲染 `XX `——**每字节带一个尾部空格且计入宽度**（F13 64B→192）。行末 multi_sz NUL 只在行末剥（右行丢、左行留）。

**实现**：新 crate `product/reg`（reacmp-reg，**零外部依赖**：parse/values/
collation/engine/report）。`Locale{ZH,EN}` 两个常量参数化几何。CLI
`Command::RegistryReport` + `do_registry_report`；args.rs 移出 registry-report。

**验证**：金标准 `D:\Rea\verify\reg\` **23 例**（`tools/m111_add_reg_goldens.py`
从**参考英文安装**生成；manifest 每条带 `authored_by` 说明为何用英文安装；
fixture 逐字节复制、最终树就地重跑）；norm-5（注册表标题、两个 Mode 行、
四条错误行模式——解析/重复/编码，**数据保留**、四个计数标签；未观测变体
按设计拒绝为 unparseable）；CLI 集成 12 例；reg 单测 27 解析 + 103 语料 +
9 帧。**门禁 M111-gate-01 = 1018/1035**（reg/candidate 23/23 逐字节；
17 fail = 上述中文几何在案差异）。残留：T6 右名称列宽 3 vs 模型 2
（**U-reg-1 未解释**，已从语料排除并标注）、N6 归档 fixture 缺陷（引号数据
内 CRLF，同旧 `\\r\\n` 字面量 bug 家族）。
