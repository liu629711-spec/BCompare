# Text 模块规格索引（第一遍进行中）

> 项目：Beyond Compare 全产品复刻。本目录为 Text（文本比较）模块规格。
> 日期：2026-10-13。上游：S 地基 14 单元已全部完成（`../ss/`）。

## 模块地图（函数数）

| 单元 | 函数数 | 大小(B) | 角色 | 规格 |
|---|---|---|---|---|
| **TextContent.pas** | 112 | 32155 | 内容引擎：按语法元素表做符号级标记（重要性来源） | ✓ 本目录 |
| **TextREParser.pas** | 77 | 19100 | 自研正则引擎（NFA + 字符类节点树） | ✓ 本目录 |
| **TextMap.pas** | 189 | 37290 | 行号 ↔ 位置映射层 | ✓ 本目录 |
| **BcFileFormat.pas** | 188 | 22339 | 文件格式定义（对接 XML 配置） | ✓ 本目录 |
| **BcSyntaxElements.pas** | 31 | 2951 | 语法元素枚举 + 重要性映射 | ✓ 本目录 |
| **TextFormat.pas** | 95 | 6156 | 格式化委托层（薄） | ✓ 本目录 |
| TextFiltered.pas | 51 | 9584 | 过滤（含 2086B 大函数） | 待第一遍 |
| TextOutput.pas | 89 | 18028 | 输出（报告生成链） | 待第一遍 |
| TextSession.pas | 121 | 11632 | 会话层 | 待第一遍 |
| ViewText.pas | 503 | 93786 | 视图层（UI 大头） | 待（UI 战役） |
| UiTextEditor.pas | 435 | 74247 | 编辑器 UI | 待（UI 战役） |

清单：`inventory/*.tsv`（entry/size/confidence）。

## 已确认的调用链（跨单元）

```
BcFileFormat/BcSyntaxElements（配置定义，XML 持久化）
        ↓ 元素表（0-9 顺序：Keyword..Operator）
TextContent（符号级标记，每字符状态位图 + 上下文窗口）
        ↓ 符号类别
SsClasses 重要性判定（6/9 恒重要；注释不重要）
        ↓
diff 对齐（Myers；SsLineList/SsLineParse 提供行）
```

## 与 oracle 锚点的对应（verify/golden/45 锚点）

- `.c` 注释 similar、标识符/字符串/数字/操作符/指令 different → TextContent 符号类别 → BcSyntaxElements 重要性属性。
- `.txt` 只有空白/大小写不重要 → 无语法表路径（TextContent 不标记，纯文本比较）。
- 空白跨语法 similar → SsClasses 空白规则。

## 下一步

1. TextContent/TextREParser 二遍（大函数分块精读，补全类别/指令集）。
2. TextFiltered/TextOutput/TextSession 第一遍。
3. 用 oracle 做**正则/过滤**锚点（正则语法行为可被测——通过 find-in-files 或过滤规则配置）。
