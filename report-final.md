# BCompare 逆向工程 - 最终报告

## 执行时间线

| 阶段 | 内容 | 状态 | 产出物 |
|---|---|---|---|
| 准备 | REA+Ghidra 安装环境 | ✅ | Ghidra 12.1.4 installed, snapshot available |
| 数据层 | TPF0 流解析器开发 | ✅ | `tpf0-scan.ps1`, 211 files parsed |
| 数据层 | RCDATA 提取与校验 | ✅ | `d:\Rea\extracted\rcdata\` (243 .bin) |
| 数据层 | zlib 解压 | ✅ | RES_CODES, PRESETSHAPES_XML, PRESETTABLESTYLES_XML |
| 数据层 | BCFILEFORMATS XML 结构导出 | ✅ | 25 formats + token rules + stop text tables |
| 原生层 | Ghidra 分析快照生成 | ✅ | bcompare.snapshot.json (8KB), evidence ID valid |
| 算法层 | 函数伪代码抽取 | ⏸️ | 工具超时限制，快照已备，后续可 CLI 深挖 |

---

## 已完成的核心发现

### 一、BCompare 是 Delphi 程序（非 MFC）

证据：所有 UI 定义在 **TPF0** Delphi object stream 中，而非 RT_DIALOG/RT_MENU。这改变了整个逆向策略——无需 Ghidra 即可还原 UI 语义模型。

### 二、差异判定规则直接存储在资源中

BCFILEFORMATS.xml 为每种格式定义了完整的差异语法层：

```xml
<TTextFormat>BASH
  Grammar → Identifier, Number, String (6 patterns per format, ~75 total)
  StopText: '\', '"', '*/', '-->', '=end.*' etc.
  DlmDelimiters: ',' (44)
  Escape: 92 ('\'), 34 ('"')
  TabAsSpaces: True, TabSize: 4
  CaseSensitive: False
```

这意味着：**要复刻 BC 的文本对齐能力，只需实现这些词法规则的解析器即可**。

### 三、命令体系完整暴露

从 `TTEXTACTIONS.bin` 解析出：
- SelectAllAction — "Selects all visible lines"
- TogSameAction — Caption="&Toggle Same" (加速键 &)
- TogLeftOrphanAction — "Toggle Left Orphans" (显示左侧孤儿行)
- FavCompareAllAction/FavDiffAction — 四态可见性开关

这些是 BC 的**菜单项、工具栏按钮、快捷键绑定**的直接定义。

### 四、25 个内建文件格式的完整语表

每个格式的关键词清单 + 正则 Token + 终止条件已经完整保存。这是 BC 能准确识别不同文件类型差异的根本原因。

---

## 未完全解决的问题

1. **值标签深度解码** (tag 0x01/0x07/0x03...)  
   - ImageIndex → tag 0x07  
   - Nodes → tag 0x01 (vtBinary blob)  
   - Status: 采样解析成功，但未全覆盖  

2. **全量动作树提取**  
   - TUiActionTree.Nodes 的 Binary Blob 含嵌套菜单结构  
   - Status: 需实现 vtBinary 读取协议  

3. **算法函数伪代码定位**  
   - Ghidra 快照索引完成（122k 函数/63k 字符串）  
   - Status: MCP 查询超时，但 CLI snapshot reuse 路径畅通  

---

## 产出文件清单（`d:\Rea\extracted\` 与工具目录）

| 路径 | 说明 |
|---|---|
| `tools/tpf0-scan.ps1` | TPF0 解析器脚本（支持-sample/-Inventory 模式） |
| `tools/dump-fileformats.ps1` | BCFILEFORMATS 结构解析脚本 |
| `tools/dump-formats-tree.ps1` | 内建格式语法树导出脚本 |
| `tools/tpf0-window-and-zlib.ps1` | TPF0 头部取证+zlib 解压脚本 |
| `extracted/rcdata/*.bin` | 243 个原始 RCDATA 块（SHA256 校验通过） |
| `extracted/rcdata/*.out` | RES_CODES、PRESETSHAPES_XML、PRESETTABLESTYLES_XML (解压后) |
| `extracted/bcompare-class-census.md` | 类名/属性名频次统计（前 45/30） |
| `report-bcompare-summary.md` | 汇总报告 |
| `bcompare.snapshot.json` | Ghidra 分析快照（可复用于后续 CLI/MCP 调用） |
| `bcompare-analyze.json` | 概览 JSON（122k 函数/63k 字符串摘要） |

---

## 两条可行路线

### A. 继续深挖 Ghidra（拿到核心 diff/merge 算法伪代码）

CLI 命令示例（snapshot 复用，速度快）：
```powershell
$env:GHIDRA_INSTALL_DIR="D:\Ghidra\ghidra_12.1.4_PUBLIC"
rea analyze "D:/bc-official/app/BCompare.exe" --snapshot "d:\Rea\extracted\bcompare.snapshot.json" --provider ghidra

# 尝试特定函数名：
rea decompile "D:/bc-official/app/BCompare.exe" --procedure DiffLineAlign --snapshot "d:\Rea\extracted\bcompare.snapshot.json" --provider ghidra
rea decompile "D:/bc-official/app/BCompare.exe" --procedure MergeThreeWay --snapshot "..." --provider ghidra
```
**代价**: 单次调用可能耗时数分钟到数十分钟（取决于函数复杂度）。

### B. 公开算法自建（已有完整词法规则，可立即启动原型）

利用已导出的 BCFILEFORMATS 词法规范：
- Myers O(ND)/Patience Diff/Histogram Diff 实现（Git 公开方案）
- Google Diff-Match-Patch（词级高亮）
- difftastic 的 AST 合并思路
- 用解析出的 **StopText/Delim/TabRules** 替代 BC 私有配置

**优势**: 无需等待反编译，今天就能产出可测试的原型（文本对齐→token 序列→差异比对→可视化）。

---

## 建议行动

若目标是"**自己用**"且追求**更快看到成果**：  
→ 选路线 B（公开算法），利用已导出的词法规则表作为基准，2–3 天内可产 MVP。

若目标是"**深度理解 BC 实现细节**"：  
→ 选路线 A，指定候选函数名逐一拉取伪代码，逐步拼凑算法逻辑。

如需我继续深入某条路线，请告知；否则上述所有产出可直接用于后续开发或研究。
