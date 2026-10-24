# 复刻 Beyond Compare：范围评估与路线图

生成时间：2026-10-12
目标产品：Beyond Compare 5.2.6（Pro），`D:\bc-official\app\`

---

## 一、本轮最重要的成果：建立了"可验证"能力

这一轮真正的突破不是挖到更多代码，而是**让"复刻得像不像"变成可度量的事**。

### 关键发现：BC 可以脚本化调用

`BComp.com`（控制台程序）在**评估模式下完全可用**（当前显示"30 days remaining"），可以无人值守生成报告：

```
BComp.com /silent @<script> <left> <right> <output>
```

脚本内容（官方语法，经实测确认）：
```
text-report layout:xml output-to:"%3" "%1" "%2"
```

**踩过的坑**（记录以免重犯）：`load` 命令**只接受文件夹**，对文件用 `load` 会报 `Fatal Scripting Error: Unable to load base folder`（退出码 107）。文件比对必须直接用 `text-report` 接路径，不能用 `load`。

### 已建立的验证工具链

| 工具 | 作用 |
|---|---|
| `tools/bc-oracle.py` | 驱动 BC 生成金标准报告（6 种 layout × 5 种选项，全部实测通过） |
| `tools/bc-align-verify.py` | 解析 BC 的 XML 报告，与候选实现逐行比对对齐结果 |
| `tools/bc-anchors.py` | **8 个行为锚点测试，当前 8/8 通过** |

BC 的 XML 报告是最理想的验证接口——它把每个对齐组的状态结构化了：

```xml
<linecomp status="different">
  <text ltid="2">line two</text>
  <text rtid="2">line TWO changed</text>
</linecomp>
```

状态取值：`same` / `similar` / `different` / `leftorphan` / `rightorphan`

### 实测确认的 BC 默认行为（修正了此前的推测）

跑了一组对照实验，得到 BC 的**真实默认重要性规则**：

| 差异类型 | BC 判定 | 说明 |
|---|---|---|
| 行内多余空格（`int a` vs `int  a`） | `similar` | 空白**默认不敏感** |
| 行首缩进变化 | `similar` | 同上 |
| 行尾空白变化 | `similar` | 同上 |
| 注释内空白变化 | `similar` | 同上 |
| 运算符周围空格（`a=b+c` vs `a = b + c`） | `similar` | 同上 |
| 标识符大小写（`Value` vs `value`） | `different` | 大小写**默认敏感** |
| 关键字大小写（`int` vs `INT`） | `different` | 同上 |
| 字符串内容大小写 | `different` | 同上 |
| 运算符改变（`+` vs `-`） | `different` | 强制重要 |
| 数值改变（`100` vs `200`） | `different` | 强制重要 |
| `#include` 改变 | `different` | 强制重要（Directive） |

**重要修正**：我此前以为 `StrCaseInsig`/`StrWSInsig` 默认都关闭。实测表明**空白默认已不敏感**，而大小写默认敏感。这两个是可配置项，但默认值不同。

另外验证了三态语义：开启 `ignore-unimportant` 后，`similar` 行会**合并为 `same`**（`ltid`/`rtid` 合并），而 `different` 行不受影响。

---

## 二、BC 作为产品的真实规模

从逆向数据 + 官方文档（CHM 已解出 469 个文件）交叉确认：

### 11 种视图类型

`Text Compare`、`Text Merge`（三方合并）、`Table Compare`、`Hex Compare`、`Media Compare`、`Picture Compare`、`Registry Compare`、`Version Compare`、`Folder Compare`、`Folder Merge`、`Folder Sync`，外加 `Text Edit`、`Text Patch`

### 398 条命令

按动作表分布：`TDIRACTIONS` 89、`TTEXTACTIONS` 86、`TFILEACTIONS` 43、`TBCACTIONS` 41，其余 11 个表共 139 条。

### 7 个内容比对引擎

`TextMap` / `TableMap` / `PixMap` / `HexMap` / `RegMap` / `MediaMap` / `VerMap` —— 共享同一套对齐框架（这是我逆向发现的架构要点）

### 25 套文件格式词法规则

已完整导出（19 种文本格式 + 表格/图片/媒体/版本/XML）

### VFS 层（17 个单元）

本地、FTP、SFTP、WebDAV、Amazon S3、OneDrive、便携设备、压缩包（7z/ZIP/RAR）、ClearCase

### 第三方授权组件（**复刻的真实障碍**）

| 组件 | 用途 | 性质 |
|---|---|---|
| **FlexCel** | Excel/表格解析 | 商业授权，源码需付费 |
| **SecureBlackbox** | SSH/TLS/加密 | 商业授权，价格高昂 |
| **Indy10** | 网络协议栈 | 开源（BSD） |
| **Abbrevia** | 压缩格式 | 开源（MPL） |
| **JCL** | Delphi 工具库 | 开源（MPL） |
| **GraphicEx** | 图形格式 | 开源 |
| **scp2** | SSH（旧） | 开源 |

**这是复刻最实际的成本项**：FlexCel 和 SecureBlackbox 是商业组件，自研替代（Excel 格式全兼容、SSH/TLS 栈）的工作量远超逆向本身。

### 授权约束（必须正视）

BC 许可证明确：软件、License Key、文档均为 Scooter Software 版权作品，"Customer has no rights in the foregoing except as expressly granted"。30 天试用期后可继续研究，但**用于商业分发**需要独立实现，不能复制代码或资源。

实务边界：
- **可以**：研究其行为、用规格（格式表、算法结构）指导自研实现、做互操作
- **不可以**：复制其代码/资源、分发其二进制、绕过授权

---

## 三、复刻的诚实评估

### 工作量分级

| 阶段 | 范围 | 相对工作量 |
|---|---|---|
| **A. 文本比对核心** | Text Compare + 重要性分级 + 报告输出 | 1× |
| **B. 文件夹比对** | Folder Compare + 过滤/规格 + 文件操作 | 1.5× |
| **C. 多内容类型** | Table/Hex/Pix/Reg/Ver/Media 六种引擎 | 2× |
| **D. 三方合并** | Text Merge + Folder Merge + 冲突处理 | 1× |
| **E. VFS 层** | FTP/SFTP/WebDAV/S3/OneDrive/压缩包 | 2×（含第三方替代） |
| **F. UI 层** | 211 个表单、双栏同步滚动、语法高亮 | 2.5× |
| **G. 集成** | Shell 扩展、命令行、脚本引擎、版本控制 | 1× |

合计约 **11× 阶段 A**。阶段 A 本身就是个完整的中型项目。

**结论：完整复刻 BC 是 3–5 人年的工程**（团队协作），不是本会话或几周能完成的。任何声称"几天复刻 BC"的说法都不诚实。

### 但有一个务实的切入点

**阶段 A 是自包含的、已验证可行的、且已经完成了一半规格工作。**

我们已有的资产直接支撑阶段 A：
- 差异算法（Myers + 前后缀裁剪 + 段合并）—— 伪代码级确认
- 重要性规则（字段 schema + 默认值实测 + 三态语义）—— 完整
- 25 套格式词法规则 —— 原样导出
- 报告输出格式 —— 6 种 layout 金标准样本
- **验证基准** —— BC oracle + 8 个锚点

---

## 四、建议路线图

### 第一阶段：文本比对 MVP（可度量）

**目标**：输入两个文件，输出与 BC 在锚点上一致的 XML 报告。

1. **词法层**：按 `bcfileformats-spec.json` 实现 C++/Python/JS 三套格式的 tokenizer
2. **对齐层**：实现 Myers 线性空间算法（照伪代码结构：前后缀裁剪 → 双向搜索 → 段合并）
3. **重要性层**：实现三态判定（强制重要元素 + 空白/大小写规则 + 容差）
4. **输出层**：生成 BC 兼容的 XML 报告
5. **验收**：用 `bc-anchors.py` 扩充到 30–50 个锚点，目标 100% 一致

**验收标准明确**：锚点通过率。这是可量化、可回归的。

### 第二阶段：扩面

- 补齐 25 套格式
- 实现 `ignore-unimportant` 折叠、报告的其他 layout（patch/side-by-side）
- 实现文本合并（三方）

### 第三阶段（可选）：产品化

- 文件夹比对、UI、VFS —— 这是真正的产品工程

---

## 五、本轮产出

| 文件 | 说明 |
|---|---|
| `tools/bc-oracle.py` | BC 金标准报告生成器（6 layout × 5 选项） |
| `tools/bc-align-verify.py` | 对齐结果比对器（XML 解析 + 逐组比对） |
| `tools/bc-anchors.py` | 行为锚点测试（8/8 通过） |
| `D:\Rea\help\` | **BC 官方帮助文档 469 个文件**（CHM 解出） |
| `D:\Rea\verify\oracle\` | 各 layout 的金标准输出样本 |
| `D:\Rea\verify\cases\` | 对照实验用例与结果 |

累计逆向产出：**282 个函数伪代码**，190 个源码模块，25 套格式规则，5,435 条资源字符串。

---

## 六、需要你决定的

1. **范围**：是走"文本比对 MVP"（可度量、能落地），还是坚持全产品复刻（多年工程）？
2. **第三方组件**：VFS/Excel 部分打算自研还是采购替代（FlexCel/SecureBlackbox 同类）？
3. **语言栈**：复刻用什么技术栈？（BC 是 Delphi；Rust/C++/C# 都能做，但影响 UI 层选型）

我的建议：**先做第一阶段**。理由是它自包含、验收标准明确（锚点通过率），而且规格已经齐了——做完就能得到一个"和 BC 行为一致"的文本比对核心，这既是可交付物，也是后续扩面的地基。
