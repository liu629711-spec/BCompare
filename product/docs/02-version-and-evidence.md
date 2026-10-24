# 02 — 版本与证据分级

> 审计日期：2026-10-13
> 目的：把工作区所有证据按**版本归属**与**证据强度**分开，杜绝「把推断当观察」「把 5.2.6 当 5.2.1」。
> 分级定义见 §1。所有条目均标注复核方式。

---

## 1. 证据分级定义

本审计采用四级，**任何结论必须落到其中一级**：

| 级别 | 名称 | 判据 | 可否作为实现依据 |
|---|---|---|---|
| **O** | 已观察（Observed） | 本次审计**亲自执行**命令/程序得到的输出 | ✅ 可直接依据 |
| **D** | 已派生（Derived） | 由 O 级证据经**确定性变换**得到（解析、统计、格式转换） | ✅ 可依据，须附变换链 |
| **I** | 推断（Inferred） | 从结构/字符串/命名**推测**语义，未用行为验证 | ⚠️ 须先用 Oracle 复核 |
| **U** | 未知（Unknown） | 无证据，或证据不足以判定 | ❌ 不得实现，须先探测 |

**纪律**：`report-clone-roadmap.md` 记录过一次自我修正（误以为 `StrCaseInsig` 默认关闭，实测相反）。这说明**逆向推断必须用黑盒对拍复核**——本审计继承并强化该纪律。

---

## 2. 版本归属总表

### 2.1 两个安装的实测身份（O 级）

| 项 | 当前目标 | 旧参考 |
|---|---|---|
| 路径 | `D:\BCompare\BCompare\` | `D:\bc-official\app\` |
| FileVersion | **5.2.1.32035** | **5.2.6.32774** |
| ProductVersion | 5.2 | 5.2 |
| 文件大小 | 50,680,536 | 50,565,160 |
| 写入时间 | 2026-03-25 | 2026-09-16 |
| SHA-256 | `7b6033aa 8b2777f5 d009e4af 5fd2e0ff 4045c20d 7fe646ac 4ceb9acf b35ce762` | `4e44c526 722d6420 e89b3724 60c519e2 93c41772 3305b83e d0eff853 db16ce5d` |
| 本地化 | **中文汉化 repack**（含 `BCompare.tr`） | **英文原版**（无 `.tr`） |
| CompanyName | Scooter Software | Scooter Software |

> 哈希以 8 位十六进制分组给出：本环境工具输出会把 64 位连续十六进制渲染成全零占位，分组可稳定读回（见 `00-current-state.md` §7）。

### 2.2 BComp.com（Oracle 引擎）（O 级）

| 项 | 当前 | 旧 |
|---|---|---|
| 大小 | 125,592 | 125,592 |
| SHA-256 | `d8d9d88a 203feb47 3761b54f 0979520d 405baf19 8ea2eee5 9833a8e1 e0359cc9` | **完全相同** |

**结论（D 级）**：两个安装的**控制台 Oracle 是同一个二进制**。因此「用 BComp.com 做 Oracle」这件事在版本维度上是稳定的；版本差异来自 `BCompare.exe`（真正的比较引擎宿主）。

### 2.3 关于「5.0 旧报告」假设的纠正（O 级）

任务假设「哪些报告是旧版 5.0」。实测**不成立**：

```
$ grep -rn "5\.0\." report-*.md specs/    → 无命中
```

实际是 **5.2.6 vs 5.2.1** 的差异。工作区**不存在 5.0 时代证据**。

---

## 3. 黄金数据归属：定案

### 3.1 事实（O 级）

| 数据集 | 生成者（README 声明） | 规模 |
|---|---|---|
| `verify/golden/` | BCompare 5.2.6 / BComp.com `/silent` | 45 锚点（XML） |
| `verify/layouts/` | 同上 | 30 布局（文本） |
| `verify/dir/` | 同上 | **失败**（exit 106） |

### 3.2 跨版本等价性实测（O 级，本次审计核心）

方法：让**两个安装**跑同一批输入，且**保持输入路径与 golden 一致**（因报告头回显输入路径）。探针：`tools/_audit/probe-anchor-both.py`、`probe-provenance.py`、`probe-body-only.py`。

| 指标 | 5.2.1.32035（当前） | 5.2.6.32774（旧） |
|---|---|---|
| 45 锚点 status 序列 == golden | **45/45** | **45/45** |
| 45 锚点 XML 字节等价（忽略 `created=`） | 41/45 | 45/45 |
| 30 布局字节等价 | 5/30 | 30/30 |
| 30 布局**去头部后**数据体等价 | **25/30** | 30/30 |

### 3.3 差异归因（O 级，逐条核对）

当前版本的全部 9 处差异，**逐条都是汉化标签**，无一为行为差异：

```
# XML 锚点（4 处）
enc-latin1              <error1>文件编码错误 (第 1 行)</error1>   vs  File Encoding Error (Line 1)
opt-display-context     <mode>差异, 带上下文</mode>              vs  Differences, With Context
opt-display-matches     <mode>相同</mode>                        vs  Same
opt-display-mismatches  <mode>差异</mode>                        vs  Differences

# 布局（5 处，仅 summary 布局）
                        2 个相同行                                vs  2 same line(s)
```

### 3.4 归属结论（D 级）

> **两个版本的比较引擎在本语料上行为等价。**
> **45 锚点的 status 序列对当前版本 5.2.1.32035 同样成立**（45/45）。
> **30 布局的数据体对当前版本同样成立**（去头部后 25/30；余 5 处为 summary 标签汉化）。

**因此黄金数据的可用性判定为**：

| 用途 | 对 5.2.1 是否可用 | 条件 |
|---|---|---|
| status 序列对拍 | ✅ **可用** | 无 |
| XML 结构对拍 | ✅ 可用 | 须忽略/归一化 `created=` 与本地化标签 |
| 布局数据体对拍 | ✅ 可用 | 须归一化头部与 summary 标签 |
| 布局**字节**对拍 | ❌ 不可用（当前版本） | 仅对 5.2.6 成立 |

**须补记**：`verify/golden/README.md` 声明「生成：BCompare 5.2.6」是**事实且诚实**，但**未说明对 5.2.1 的适用性**。本审计不改动该文件（遵守「不修改既有资产」），此结论记录于此。

### 3.5 附带发现：报告头折行与路径长度相关（O 级）

追查 §3.2 差异时发现：报告头 `Left file: …  Right file: …` 在路径较长时**折成两行**。实测与 `COLUMNS`（80/120/200）**无关**，与**路径字符串长度**相关。

> **对后续工具的硬性要求**：任何对拍脚本必须**固定输入路径**或**归一化头部**，否则会把折行误判为行为差异。

---

## 4. 现有报告的逐份分级

### 4.1 归属表

| 文件 | 目标路径 | SHA-256 声明 | 版本归属 | 分级 |
|---|---|---|---|---|
| `report-algorithm.md` | `bc-official` | 明写 `4e44c526…` | **5.2.6** | O/D |
| `report-verified.md` | `bc-official` | 明写 `4e44c526…` | **5.2.6** | O/D |
| `report-rules-and-merge.md` | `bc-official` | **未写** | 推定 5.2.6 | I |
| `report-clone-roadmap.md` | 明写「5.2.6（Pro）」 | 未写 | **5.2.6** | O/D |
| `report-bcompare-summary.md` | **未写** | 未写 | **无法判定** | U |
| `report-final.md` | 命令行含 `bc-official` | 未写 | 推定 5.2.6 | I |

> **无任何报告针对 5.2.1.32035。** 但它们针对的 5.2.6 与当前版本在本语料上行为等价（§3.4），故结论**大概率仍适用**，唯须按 §5 分级使用。

### 4.2 关键主张的逐条分级

| 主张 | 来源 | 分级 | 复核方式 / 备注 |
|---|---|---|---|
| Myers 线性空间（V 数组 `2D+1`、步长 2、`delta` 奇偶、重叠二分递归） | `report-algorithm.md` | **O**（结构证据） | 伪代码特征唯一匹配；存于 `extracted/pseudocode/` |
| 公共前后缀裁剪 | 同上 | **O** | 伪代码直读 |
| 差异段游程合并（相邻差异并入一段） | 同上 | **O** | 伪代码直读 |
| 可取消设计（每轮 D 回调） | 同上 | **O** | 伪代码直读 |
| 语法元素索引 6/9（Directive/Operator）**强制重要** | 同上 | **I** ⚠️ | 依赖「索引→类型」映射假设，**未行为验证**。须用 Oracle 复核 |
| `CaseSig`/`Weights` 等 70 字段 schema | 同上 | **O**（结构） | 但**默认值**须另证 |
| 空白默认不敏感 | `report-clone-roadmap.md` | **O**（黑盒实测） | 45 锚点 `ws-*` 独立复现 ✅ |
| 大小写：`.txt` 不敏感、`.c` 敏感 | 同上 | **O**（黑盒实测） | 45 锚点 `case-txt` / `case-c-ident` 复现 ✅ |
| `ignore-unimportant` 把 `similar` 折叠为 `same` | 同上 | **O**（黑盒实测） | 45 锚点 `opt-ignore-unimportant` 复现 ✅ |
| 383 条命令 / 11 种视图 / 25 套格式 | `report-clone-roadmap.md` | **O**（资源统计） | 但**未逐条验证可用性** |
| 271 条源码路径 / 190 模块 | `report-algorithm.md` | **O** | 已存 `extracted/source-modules.json` |
| `*Map.pas` 命名规律 → 统一对齐框架 | 同上 | **I** ⚠️ | 命名推断，合理但未验证 |
| 第三方组件清单（FlexCel / SecureBlackbox…） | `report-clone-roadmap.md` | **O**（字符串） | 授权影响真实 |
| 「完整复刻 = 3–5 人年」 | 同上 | **I** | 量级估计，非测量值 |

**须特别标注的 I 级项**：`语法元素 6/9 强制重要` 是**重要性引擎的核心语义**，一旦实现错误，会导致整类差异被误判。**必须在 MVP 阶段用 Oracle 显式验证**（见 `05-acceptance-strategy.md`）。

---

## 5. `extracted/` 与 `specs/` 的可用性分级

| 资产 | 分级 | 说明 |
|---|---|---|
| `help/*.html`（231 份） | **O** | 官方文档，与版本一致。**最干净的规格来源** |
| `extracted/bcfileformats-spec.json` | **D** | 由资源确定性解析（19 格式语法规则） |
| `extracted/ui-spec.json` + `forms/*.dfm`（212） | **D** | DFM 二进制文法已反推并验证 |
| `extracted/delphi-classes.json`（5,121 类） | **D** | VMT 解析 |
| `extracted/source-modules.json` | **D** | 断言路径提取 |
| `extracted/function-attribution.json` | **D** ⚠️ | 12 万函数中仅 2.8 万已归属；**部分单元标注 edge-nearest 低可靠性** |
| `extracted/pseudocode/*.c`（263） | **D** | 反编译产物，**不等于原源码** |
| `specs/ss|text|dir/ui/` | **D** | 基于上述派生证据；`specs/dir/README.md` **自带置信度标注**（优良实践） |

**纪律**：`extracted/pseudocode/*.c` 是**反编译伪代码**，非原始源码，不得声称「还原了 BC 源码」；`function-attribution.json` 的低置信度归属不得直接作为实现依据。

---

## 6. 未知清单（U 级，须探测后才可实现）

| # | 未知项 | 影响 | 建议探测方式 |
|---|---|---|---|
| U1 | 语法元素索引 6/9 是否真为 Directive/Operator | 重要性引擎核心语义 | Oracle 构造 `#include` / 运算符变更用例 |
| U2 | 三方合并的冲突判定与自动合并规则 | Text Merge 全部 | `text-merge` 脚本 + 构造冲突夹具 |
| U3 | 表格比较的行/列/单元格匹配算法 | Table Compare | `table-report` 脚本 |
| U4 | 图片比较的容差与对齐模型 | Picture Compare | `picture-report` 脚本 |
| U5 | 十六进制比较的对齐粒度 | Hex Compare | `hex-report` 脚本 |
| U6 | 注册表/版本比较的字段映射 | Reg/Ver Compare | `registry-report` / `version-report` |
| U7 | 压缩包内比较的 VFS 抽象边界 | Archive Compare | 构造 zip/7z 夹具 |
| U8 | 文件夹**同步**的方向判定与冲突策略 | Folder Sync | `sync` 脚本 + 构造双向差异 |
| U9 | 会话持久化格式（`BCSessions.xml`）的完整 schema | 会话保存/恢复 | 已有 `BCSessions.xml`（40 KB）可解析 |
| U10 | 命令行/脚本引擎的完整命令语义 | 脚本接口 | `help/scripting_reference.html` + 实测 |
| U11 | 文件格式规则的用户可配置边界 | 自定义格式 | `BCFILEFORMATS.xml`（93 KB）已提取 |
| U12 | GUI 主题/高 DPI 的具体行为 | GUI 验收 | 需 GUI 自动化（当前无） |

**U1 优先级最高**：它是文本比较「重要性」的正确性基础，且探测成本低（构造用例即可）。

---

## 7. 证据管理规则（供后续任务遵守）

1. **每次引用结论必须标级别**（O/D/I/U）。I 级不得直接实现。
2. **跨版本引用必须标注**：写「5.2.6 实测」或「5.2.1 实测」，不得写「BC 实测」。
3. **哈希不得抄录单行工具输出**（本环境会渲染成全零占位）；须分块或交叉验证。
4. **对拍必须固定输入路径**，否则报告头折行会造成假差异。
5. **Oracle 必须从真实安装目录调用**（复制到别处触发授权失败，exit 104）。
6. **不得声称还原源码**：`pseudocode/*.c` 是反编译产物。
7. **新增证据写入 `tools/_audit/` 或 `product/docs/`**，不改动既有 `verify/`、`extracted/`、`report-*.md`。
