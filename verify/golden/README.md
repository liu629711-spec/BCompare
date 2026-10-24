# Oracle 黄金数据索引（45 锚点）

> 生成：2026-10-13，`python tools/bc-anchor-suite.py`（BCompare 5.2.6 / BComp.com /silent）。
> 用途：Rust 克隆品的回归基准——同输入字节必须产出同 status 序列（及注明的转义/结构）。
> 每例三件套：`<name>-L.<ext>` / `<name>-R.<ext>`（输入字节）+ `<name>.xml`（BC 报告）；清单 manifest.json。

## 关键行为发现（字节级实证）

| 发现 | 证据文件 | 详情 |
|---|---|---|
| **XML 头 / 行尾** | 全部 .xml | `<?xml version="1.0" encoding="utf-8"?>`（小写 utf-8）+ 全文 **CRLF** 行尾 |
| **控制字符转义** | xml-ctrl-chars / enc-ctrlz-eof | 0x01→`&#1;`、0x07→`&#7;`、0x1A→`&#26;`（十进制字符引用，SsXML 转义引擎） |
| **无效 UTF-8 替换** | enc-latin1 | `caf\xE9` → `caf\xEF\xBF\xBD`（U+FFFD）——.txt **无 Latin-1 回退** |
| **emoji 直出** | xml-unicode | U+1F600 原样 UTF-8（不转义） |
| **行尾等价** | le-* | CRLF ≡ LF ≡ CR ≡ CRCRLF（全部 same）；缺尾换行 ≡ 有尾换行 |
| **BOM 等价** | enc-* | UTF-8/UTF-16LE/BE BOM 均与无 BOM 等价（自动识别） |
| **Ctrl-Z 非 EOF** | enc-ctrlz-eof | `abc\x1adef` ≠ `abc`（0x1A 是普通字符，不作 EOF 截断——修正"Ctrl-Z as EOF"旧假设） |
| **NUL 行对比** | enc-nul-binary | 含 NUL 行按文本比较（different/same 正常产出） |
| **空白 = similar** | ws-* | 前导/尾随/内嵌空白、tab↔空格全部 similar（.txt） |
| **大小写规则随语法** | case-txt vs case-c-ident | .txt 大小写 = similar；.c 标识符/字符串 = **different** |
| **C 语法元素重要性** | case-c-*/num-c/op-c/dir-c/kw-c | 数字/操作符/指令/关键字改动 = different；**注释改动 = similar** |
| **.txt 无语法** | txt-syntax-chars | `int x = 10;` vs `long x = 20;` = different（纯文本语义） |
| **对齐模式** | al-* | 插入/删除/块替换/移动/块交换/重复行/空的完整 status 序列（见 manifest） |
| **选项语义** | opt-* | display-all=全含；display-mismatches=仅 similar/different；display-context=全含；display-matches=仅 same；**ignore-unimportant 把 similar 折叠成 same（ltid/rtid 合并）** |

## 各锚点 status 序列（快查）

见 `manifest.json` 的 `statuses` 字段。要点：
- `al-swap-blocks`: `[leftorphan×2, same×2, rightorphan×2]` —— 块交换按"删除+插入"对齐，**不做移动检测**（Myers 最短编辑脚本的预期行为）
- `al-move-down`: `[same, leftorphan, same, same, rightorphan]` —— 同上前提
- `al-duplicates`: `[same, same, leftorphan]` —— 重复行从前对齐
- `opt-ignore-unimportant`: `[same×4, different, same]` —— 与 display-all 对比：similar→same 合并

## 实盘配置文件验证（2026-10-13）

`%APPDATA%\Scooter Software\Beyond Compare 5\BCState.xml`（691B，另有升级前快照 `.bak` 266B）：

- 头部与配置规格逐字一致：`<?xml version="1.0" encoding="UTF-8"?>` + `<!-- Produced by Beyond Compare 5 from Scooter Software -->`
- 结构 = 类名元素（`<TBcState>`/`<TTextCompareState>`）+ `Value="..."` 属性
- **日期选项** `LastChecked Value="2026-10-12 22:53:50"` = SsRegistry 的 `yyyy-mm-dd hh:nn:ss`
- 列表 = 编号键 `<_0 Value="..."/>`；复合值 `;` 分隔（`"669;288;1251;744"`）
- `.bak` = 旧版本（ReplaceFileW 原子备份；升级演进证据）
- **`/silent` 报告路径不写配置**（只读操作不触发持久化 → SsPersistent 变更检测语义的旁证）

## 复现

```bash
python D:\Rea\tools\bc-anchor-suite.py    # 重跑并覆盖 golden/
```
