# BcFileFormat.pas 规格（第一遍·架构级）

> 逆向来源：语料精读（188 函数；141 个 <128B——**薄包装为主的配置层**）。地址段 140dexxxx–140dfxxx。日期 2026-10-13。
> 单元身份：**文件格式定义层**——语法/元素/规则的可持久化配置对象（对接 SsPersistent XML 配置树）。

## 1. 已定性

- **持久化字段名（实测字符串）**：`UseRes`、`Value`、`ElementStr`、`Item`、`ValueBool` —— 这些是配置树的键名，说明格式定义以 **XML 配置节**存储（与 SsPersistent 的 `Value="..."` 属性模型一致）。
- **`FUN_140dee3b0`（1428B）**：格式定义装载/校验主函数。
- **`FUN_140dec9a0`（1356B）/`FUN_140dec3a0`（1135B）/`FUN_140dea0f0`（1080B）**：格式规则的读写 [二遍]。
- 与 **SsPersistent 消费面吻合**：SsPersistent 的调用方含规则/重要性层（140db5980、140deede0-310）——本单元即"规则从配置来"的落地。

## 2. 与 BCFILEFORMATS 语法的关系

- `extracted/bcfileformats-spec.json`（25 格式语法，元素序 0 Keyword/1 Identifier/2 Number/3-5 String/6 Directive/7-8 Comment/9 Operator）是本单元运行时数据的**静态导出**。
- 元素序与 SsClasses 硬编码重要性索引（6=Directive、9=Operator 恒重要）对应——本单元提供元素表，SsClasses/TextContent 消费。

## 3. 可测试锚点

1. 配置键名往返：UseRes/Value/ElementStr/Item/ValueBool 在 XML 配置中的读写。
2. 格式定义的默认值（未配置时的回落）。

## 4. 未解之谜

1. [?] 格式定义对象的完整字段表（对照 bcfileformats-spec.json 的元素序）。
2. [?] 自定义格式（用户新增语法）的持久化路径与内置格式的差异。
3. [?] 与 DlgFileFormatManager（99 函数，UI 层）的边界。
