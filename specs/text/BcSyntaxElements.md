# BcSyntaxElements.pas 规格（第一遍·架构级）

> 逆向来源：语料精读（31 函数；22 个 <128B）。地址段 140de5xxx。日期 2026-10-13。
> 单元身份：**语法元素定义**（元素类型枚举 + 配置字段名），BcFileFormat 的配套层。

## 1. 已定性

- **配置字段名（实测）**：`ElementStr`、`Item`、`ValueBool` —— 语法元素的持久化键名。
- **`FUN_140de5470`（465B）**：元素装载/校验。
- **`FUN_140de5840`（347B）**：元素操作。
- 元素序（与 `bcfileformats-spec.json` 一致）：**0 Keyword、1 Identifier、2 Number、3-5 String、6 Directive、7-8 Comment、9 Operator**。
- **重要性联动**：SsClasses 的 `FUN_140de5a40` 硬编码索引 6（Directive）与 9（Operator）恒重要 + 不重要的行索引数组（二分查找 FUN_140de51f0）——**就落在本单元地址段 140de5xxx**，故该"重要性硬编码"实为本单元的元素属性（元素 → 重要性类别）。

## 2. 可测试锚点

1. 元素序 0-9 的固定顺序（Keyword…Operator）。
2. 元素 → 重要性映射：6/9 恒重要；注释（7-8）默认不重要（oracle 校准：.c 注释 similar）。
3. 配置键名往返（ElementStr/Item/ValueBool）。

## 3. 未解之谜

1. [?] 每元素的属性表（颜色/字体/是否重要/是否忽略空白）。
2. [?] 重要性索引数组（FUN_140de51f0 二分查找的目标）的构建来源（配置 or 内置默认）。
3. [?] 与 BcFileFormat 的对象归属（元素挂在格式定义下？）。
