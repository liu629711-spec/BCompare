# TextOutput.pas 规格（第一遍·架构级）

> 语料精读（89 函数；55 个 <128B，13 个 ≥300B）。地址段 141018xxx–14101dxxx。日期 2026-10-13。
> 单元身份：**文本输出/报告生成链**——BC 报告（side-by-side/summary/interleaved/patch/statistics/xml）的产出层。

## 1. 已定性

- `FUN_14101a3a0`（2326B）/`14101c120`（1930B）/`141018ec0`（1470B）/`14101cd40`（1236B）：各布局的输出生成器。
- **直接对接 oracle**：`text-report layout:xml` 的 XML 报告由本单元产出（结构见 verify/golden/*.xml：bcreport/filecomparison/linecomp/text）。
- 与 SsXML 的分工：SsXML = 通用 XML 引擎（转义/节点/解析），本单元 = 报告语义组装。

## 1.5 五种布局的精确格式（2026-10-13 oracle 实测，verify/layouts/）

**共同头部**（除 patch/statistics）：
```
Text Compare

Produced: 2026/10/13 9:43:07
     ← yyyy/mm/dd h:nn:ss（SsRegistry 第二格式串）


Mode:  All
                        ← 与显示过滤选项对应
Left file: <path>     Right file: <path>

```

| 布局 | 结构 | 实测样本 |
|---|---|---|
| **side-by-side** | 对齐行 `左内容  =  右内容`（same 用 `=`，similar/different 用 `<>`）；分节线 = **40 个 `-`**；左孤儿行只印左侧 | `same line   =  same line` / `case diff   <> CASE DIFF` |
| **interleaved** | `左行号 右行号 内容`（缺失侧行号列留空）；分节线 = **15 个 `-`** | `1 1 same line` / `2   case diff` / `  2 CASE DIFF` |
| **patch** | **unified diff**：`diff -r L R`、`2,4c2,3`（变更范围）、`<`/`>` 前缀、`---` 分隔 | 见 mixed-patch |
| **summary** | 人类可读计数：`2 same line(s)` / `1 unimportant difference line(s)` / `1 important left orphan line(s)` / `1 important difference line(s)` + `1 difference section(s)` | 无 Mode/文件头 |
| **statistics** | **CSV**：表头 `SourceFile,CompareFile,IOriginal,IAdded,IDeleted,IChanged,UOriginal,UAdded,UDeleted,UChanged,SourceError,CompareError,Error` + 数据行（I=important，U=unimportant） | 末三列（错误）样本中为空 |

**over-under ≡ interleaved**（字节级相同，官方文档已声明废弃 over-under）。

**统计计数语义**（对照 mixed 样本：左 5 行 / 右 4 行 → `IOriginal=5, IDeleted=1, IChanged=1`；`UChanged=1` = 那个 similar 行）：
- `I*` = 重要（important），`U*` = 不重要（unimportant）
- `Original/Added/Deleted/Changed` = 原始行数/新增/删除/变更

## 2. 可测试锚点

1. 六种布局的输出与 oracle 逐字对比（golden 已捕获 xml 布局的 45 例；其余布局待捕获）。
2. XML 报告结构：`<bcreport created>`/`<filecomparison created>`/`<linecomp status>`/`<text ltid rtid>`。

## 3. 未解之谜

1. [?] 各布局生成的差异（interleaved/patch 的行前缀规则）。
2. [?] 报告选项（display-*/line-numbers/strikeout-*）在本单元的落地。
3. [?] created 时间戳格式串（yyyy/mm/dd hh:nn:ss）的调用点。
