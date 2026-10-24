# bcx — BC 兼容文本比较核心（规格验证原型）

> **定位**：这不是产品实现，是**规格的可执行验证器**。用途：证明 `specs/` 里的规格足以复现 BC 的观测行为，并把差异精确定位到规格条目。

## 已实现（45/45 通过）

- **行切分**（SsLineParse）：CRLF/LF/CR/CRCRLF 等价、缺尾换行等价、UTF-8 BOM、无效 UTF-8 → U+FFFD、含 NUL 按文本处理
- **对齐**（SsLineList）：LCS 最短编辑脚本、孤儿块配对、重复行前对齐、**不做移动检测**
- **重要性归一化**：空白（前导/尾随/tab↔空格）similar、.txt 大小写 similar
- **XML 报告**（SsXML）：头/CRLF/制表符缩进、控制字符十进制字符引用、ltid/rtid 编号

## 全部通过的锚点类别

- **行切分/编码**（SsLineParse）：CRLF/LF/CR/CRCRLF 等价、缺尾换行、UTF-8 BOM、**UTF-16LE/BE BOM**、无效 UTF-8→U+FFFD、NUL 按文本
- **重要性**（SsClasses/BcSyntaxElements）：**全空白忽略**（含标点邻接 `f( a )`≡`f(a)`）、.txt 大小写 similar、**.c 大小写 different**、**.c 注释 similar**、数字/操作符/指令/关键字 different
- **对齐**（SsLineList）：LCS 最短编辑脚本、孤儿配对、重复行前对齐、不做移动检测、空文件
- **XML 报告**（SsXML/TextOutput）：头/CRLF/制表符缩进、控制字符十进制引用、ltid/rtid
- **报告选项**：display-all/mismatches/context/matches、ignore-unimportant

## 用法

```bash
cargo build
python ..\tools\bcx-verify.py     # 对拍全部 45 锚点
```
