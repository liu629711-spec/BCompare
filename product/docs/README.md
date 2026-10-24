# ReaCompare — 架构审计文档集

> 审计日期：2026-10-13
> 状态：**审计完成**。本目录是架构决策的依据，不是产品代码。
> 边界：审计期间**未修改** `clone/`、`extracted/`、`verify/`、`ghidra-project/`、`report-*.md`。

## 文档索引

| 文档 | 内容 | 何时读 |
|---|---|---|
| [00-current-state.md](00-current-state.md) | 现状审计：目标二进制身份、clone 实测、资产清单、环境陷阱 | **先读这份** |
| [01-feature-matrix.md](01-feature-matrix.md) | 16 项功能矩阵：流程/输入输出/证据/难度/依赖/验收/状态 | 规划时 |
| [02-version-and-evidence.md](02-version-and-evidence.md) | 证据分级（O/D/I/U）、版本归属、逐条主张的可信度 | **引用任何结论前** |
| [03-architecture-options.md](03-architecture-options.md) | GUI/核心/VFS/远程/脚本的备选方案与 ADR | 动工前 |
| [04-milestones.md](04-milestones.md) | 2–4 周 MVP 计划、并行性、失败处理 | 排期时 |
| [05-acceptance-strategy.md](05-acceptance-strategy.md) | Oracle 对拍规范、验收清单、反假功能检查 | 每个里程碑 |
| [06-a2-a3-acceptance.md](06-a2-a3-acceptance.md) | A-2/A-3 验收：产品首过官方门禁、Oracle 发现 F1–F8 | 回溯验收时 |
| [07-m2-importance.md](07-m2-importance.md) | M2 重要性引擎：真分词器、leftsimilar、加权 diff | 改重要性/分词前 |
| [08-folder-criteria.md](08-folder-criteria.md) | 文件夹比较五 criteria 定案 + U9/U10 门控 | 改文件夹比较前 |
| [09-m4-interfaces.md](09-m4-interfaces.md) | M4 接口：退出码实测表、/qc 判定模型、脚本语义 | 改 CLI/脚本前 |
| [10-m4-acceptance.md](10-m4-acceptance.md) | M4 验收（MVP 完成里程碑） | 回溯 M4 时 |
| [11-m5-acceptance.md](11-m5-acceptance.md) | M5 对齐引擎：模式 3 双盒、12 语法、十例产品改动全记录（§23–§30） | **改 align 前必读** |
| [12-maintenance-regression.md](12-maintenance-regression.md) | 维护/回归手册：基线快照、复验漏斗、串行纪律教训、**§6 GUI 门禁换代（自家 golden 套件+Oracle 退役说明）** | **每次改动后照此复验** |
| [13-m6-table-channel.md](13-m6-table-channel.md) | M6 表格比较：通道定案 + 行对齐模型（§4/§5）+ M6.3 引擎落地（§6）+ M6.4 收尾（§7：帧更正/宽度残差收口/自动检测/表格门禁 810）+ m67 空格攻坚定案（§8：永久 KNOWN）+ m68 残差收口（§9：混合扩展名 pin/interleaved rawline，门禁 819） | **改表格/引擎前必读** |
| [14-m7-hex-channel.md](14-m7-hex-channel.md) | M7 二进制/十六进制比较：动词面（106/107 类）+ 字节对齐/槽/块模型 + interleaved 两趟 diff（V3 缺陷）+ 13 格 golden 门禁（858） | **改 hex 前必读** |
| [15-m8-folder-sync-channel.md](15-m8-folder-sync-channel.md) | M8 文件夹同步：sync 语法/拒绝面（半载=100）+ update/mirror 语义 + 副作用只在 CLI 执行器（先计划后应用） | **改 sync 前必读** |
| [16-m9-picture-channel.md](16-m9-picture-channel.md) | M9 图片比较：picture-report 动词面（零文件=BOM shell、缺任一侧=107）+ 像素计数/25-26 边界/alpha 忽略 + 零依赖解码（DEFLATE/PNG/BMP）+ 36 格 golden、norm-4、门禁 935 | **改 pic 前必读** |
| [17-m10-m11-registry-channel.md](17-m10-m11-registry-channel.md) | M10/M11 注册表比较：registry-report 动词面（零文件=BOM shell 带 Mode、缺任一侧=107、内容坏=错误行非失败）+ 解析器（T1 逗号续行翻案、编码嗅探）+ locale 参数化几何（列下界=表头标签宽度，中文窄于英文）+ 盒模型/排序 + 23 格 golden（英文安装生成）、norm-5、门禁 1018/1035（17=在案双语几何差异） | **改 reg 前必读** |
| [18-m112-version-channel.md](18-m112-version-channel.md) | M112 版本比较：version-report 动词面（零文件=BOM shell 带 Mode、单/三文件=106、layout 大小写折叠）+ PE 版本资源解析（CheckSum@0x40 双形、wValueLength=码元、PE 头/资源两级独立、UTC+8 时区、分秒补零）+ 字段模型（端序按机器、变化双层排序、空值键剔除、按侧连接符、已知键 `|`）+ 全字符索引几何（文件行打包 109、ignore 双形）+ 25 格 golden（英文安装生成）、norm-6、门禁 1056/1110（54=在案：17 reg 几何 + 19 ver 几何 + 18 U-ver-1） | **改 ver 前必读** |
| [19-gui-replication-spec.md](19-gui-replication-spec.md) | GUI 复刻侦察（功能 16 前置）：双安装 211 DFM 对照（201 逐字节相同、10 处为版本漂移非汉化）+ 三类复刻面 + **活体枚举全收口**：路线定案（`click_input` 顶级项→`TTBPopupWindow`→UIA RawViewWalker、悬停子菜单、归属校验+ESC 兜底）、**12 视图菜单矩阵**（四种顶级菜单形态、Tools=9/Help=7 恒定、可见性双因子驱动）+ 工具栏/状态栏 chrome 基线 + DFM 结构金标准 `extracted/guibaseline/`（381 动作/96 快捷键/13 Category）+ EN↔ZH 逐位同构 + U-gui-1..5（含视图分派实测 `.reg`≠注册表、`/fv=` 无效；**U-gui-2 活体收口**=presence-matrix 逐视图存在表 + enabled-matrix 六组内容态谓词，反编译路线已探明死路勿重试） + §6 WPF 端到端验收闭环（结构层 0 diff + UIA 自检 23/23，含 PanelHost 坑）+ **§6.10/6.11 引擎接线与过滤钮（活体取色 colors.json/filter-map.json）** | **动 GUI 前必读**（像素对拍纪律已被 docs/20 取代，成果转为参考证据库） |
| [20-product-direction.md](20-product-direction.md) | **产品方向定案（2026-10-22，最高优先级）**：能力轴全量继承 BC（16 功能 backlog+阶段表）、表现轴自主设计（7 条设计基线=卖点清单）、验收判据更替（语义/结构/视觉三类门禁换代+低频对标走查）、待拍板 D1–D6、行动清单 | **每次动工前先读这份** |

## 三条最重要的结论

1. **本项目最难的一步已经解决了——可验证性。** Oracle 工具链（BComp.com 脚本）已跑通，45 个锚点的 status 序列对**当前 5.2.1.32035 与旧 5.2.6.32774 均 45/45 通过**。任何功能都能用黑盒对拍定义完成。

2. **当前目标安装是中文汉化版（repack）。** 它会把报告**标签**翻译成中文（`差异` vs `Differences`、`2 个相同行` vs `2 same line(s)`），但**比较引擎行为与英文版逐条等价**（已逐项核对 9 处差异，全部是标签）。

3. **工作区里没有产品代码。** `clone/` 是 661 行的**规格验证器**（`cargo test` 跑 **0 个测试**，`tests/` 是空目录；45/45 来自 Python 对拍脚本）。它覆盖文本比较核心约 40%，是**算法起点**而非产品。

## 审计期间修复的真实缺陷

`verify/dir/` 的文件夹比较 Oracle **完全失败**（exit 106，0 字节）。根因：`folder-report` 报告的是**已 load 的基准文件夹**，必须先 `load`；旧脚本误用了 `text-report` 的调用形式。

```bash
# 正确配方（已实测 exit=0）
load "%1" "%2"
expand all
folder-report layout:xml output-to:"%3"
```

顺带实测出**文件夹比较的默认判据是时间戳+大小，不是内容**：夹具 `diff.txt` 内容为 `aaaa` vs `bbbb`，默认报告判 `same`；只有 `criteria CRC` / `binary` / `rules-based` 才判 `diff`。此行为此前**工作区无记录**。

## 下一批可独立派发任务

见 [04-milestones.md](04-milestones.md) 的 M0–M4。批次划分：

| 批次 | 任务 | 依赖 | 文件所有权（避免冲突） |
|---|---|---|---|
| **A-1** | M0 验证基建归一（对拍 harness + 标签/头部归一） | 无（**阻塞项**） | `product/verify/**` |
| **A-2** | M1 文本核心（新工程 + Myers + 报告迁移） | 无（与 A-3 并行） | `product/core/**`、`product/cli/**` |
| **A-3** | M3 文件夹比较只读（FileSystem trait + criteria） | 无（与 A-2 并行） | `product/dir/**`、`product/vfs/**` |
| **A-4** | U1 探测：强制重要元素验证 | 建议后于 A-1 | `product/verify/probes/**` |
| **B-1** | M2 重要性引擎（分词器 + 逐元素规则） | A-2 | `product/core/importance/**` |
| **B-2** | M4 CLI/脚本子集 | A-2、A-3、B-1 | `product/cli/**` |

**并行规则**：同批次内**不得**让多个代理编辑同一组文件。A-2 与 A-3 目录不重叠，可并行；A-1 是阻塞项，须先完成。

## 审计产出物（新增，与既有资产隔离）

```
product/docs/                     6 份文档（本目录）
tools/_audit/
  probe-current-oracle.py         Oracle 可用性 + 就地运行验证
  probe-provenance.py             跨版本黄金数据归属（保持输入路径一致）
  probe-body-only.py              剥离本地化头部后的数据体对比
  probe-anchor-both.py            45 锚点 × 2 安装全量对拍
  probe-dir-oracle.py             文件夹 Oracle 配方修复验证
  probe-dir-criteria.py           文件夹判据模型实测
```

## 复现审计结论

```bash
cd D:\Rea

# 基线（本次审计实测）
python tools/bcx-verify.py           # → 45/45 status
python tools/bcx-layout-verify.py    # → 29/30 layout

# 本次审计新增
python tools/_audit/probe-anchor-both.py    # → 两版本 status 均 45/45
python tools/_audit/probe-provenance.py     # → 5.2.6: 30/30, 5.2.1: 5/30（汉化标签）
python tools/_audit/probe-body-only.py      # → 去头后 25/30
python tools/_audit/probe-dir-oracle.py     # → load+expand 形式 exit=0
python tools/_audit/probe-dir-criteria.py   # → 默认 size+timestamp 判 same
```

## 两条操作禁忌

1. **Oracle 必须就地运行**。把 `BCompare.exe`/`BComp.com` 复制到别处会触发授权失败（`Trial mode error`，exit 104）。始终用真实安装路径。
2. **哈希不得抄录单行工具输出**。本环境会把 64 位连续十六进制渲染成全零占位；必须分块给出（如 8 位一组）或交叉验证，否则产生假证据。
