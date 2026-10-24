# 16 — M9 图片比较通道（picture-report）

功能 7（图片比较）全程。全部结论来自 Oracle 实测
（`product/verify/probes/m83_*.py` + m83b…m83o 归档，共 15 批探针；每批
串行、跑前/跑后残留检查 zero；m83k/m83l/m83m 三批在英文孪生参考安装上
交叉印证措辞）。**所有帧/日期裁决只用整数计数与序数**（docs/12 §3 教训：
显示层对分隔符不可信——本轮 Produced 日期实测为斜杠形 `2026-10-19`，
显示层再次改写成了连字符，用 `b"/" in line` 实锤）。

## 1. 动词与拒绝面（m83，`runs/m83-picture-*`、m83n/m83o）

| 脚本 | 退出 | 说明 |
|---|---|---|
| `picture-report layout:<l> [options:<o>] [title:<t>] output-to:"%3" "<L>" "<R>"` | **0** | 合法形态；layout 必填 |
| `layout:bogus` / 无 layout | 106（P4/P5） | parse 面 |
| `layout:SUMMARY`（大写） | **0**（m83o C4） | 本动词实测大小写不敏感 |
| `options:`（空值） | 0（m83o C3） | 等价默认 |
| `options:display-mismatches` / `display-matches` | 0，**逐字节等于默认**（m83n O1/O2/O3） | 接受但惰性 |
| `options:ignore-unimportant` | 0，见 §3 | |
| `options:line-numbers`（bogus） | 106（Q3-3） | |
| `options:display-mismatches,line-numbers`（valid+bogus 混） | 106（m83o C2） | 整条拒绝，非部分接受 |
| `options:display-mismatches,ignore-unimportant` | 0（m83o C1） | 多 token 合法 |
| `output-options:<x>` | 106（P7） | |
| **零比较文件**（有 layout） | **0** + 77B BOM shell（P8/m83n O5） | **不同于 hex 的 107**；shell 形态与 folder-report 同族：`Base folder: ` 行 |
| 一个比较文件 | 106（P9/m83n O6） | |
| 三个文件 | 106（m83n O9） | |
| 缺左文件 / 缺右文件 | **107 / 107**（P10 + m83n O7/O8） | **不同于 hex 的缺左 106**——两侧都是输入加载类 |

`title:"<t>"` 替换帧首行（P11）。

## 2. 帧（m83 P1/P3 + m83k/m83l 英文印证）

```
[title | 图片比较(P) / Picture Compare]
已产生： <斜杠日期> / Produced: <slash date>
<空行>
[正在忽略不重要 / Ignoring Unimportant]   ← 仅 options:ignore-unimportant，在文件行之前（m83g IGNORE-line）
左边文件： <L> / Left file: <L>
右边文件： <R> / Right file: <R>
[左边错误： 不被支持的类型 / Left error: Unsupported Type]
[右边错误： 无效图像 / Right error: Invalid image]
[计数行……（summary 才有；见 §3）]
```

- side-by-side **只输出帧**，差异图像也没有计数行（P1/P2/Q4/m83k E1）。
- 错误行是**行级输出**而非命令失败：exit 0，帧继续（P12/Q7/EN-mixed-error）。
- 零文件 shell（77B 实测）：BOM + 标题 + Produced + 空行 + `基点文件夹： `
  （trailing space 实测），**无**文件行、无计数。

## 3. 计数与重要性（m83b/m83c/m83e/m83f/m83h/m83i/m83j）

summary 计数行类别按实测序输出：**same → unimportant → left orphan →
right orphan → important**，零值类别省略（m83h/m83i V1/m83j）。标签措辞：

| 中文 | 英文 |
|---|---|
| `N 个相同像素` | `N same pixel(s)` |
| `N 个不重要的差异像素` | `N unimportant difference pixel(s)` |
| `N 个忽略的不重要差异像素`（ignore 时改名） | `N ignored unimportant difference pixel(s)` |
| `N 个左边独有像素` | `N left orphan pixel(s)` |
| `N 个右边独有像素` | `N right orphan pixel(s)` |
| `N 个重要差异像素` | `N important difference pixel(s)` |

**重要性规则**（全部实测钉死）：

- 每像素取 **RGB 三通道各自 max |Δ|**，`max ≥ 26 ⇒ important，≤ 25 ⇒
  unimportant`——25/26 精确边界成对实测（U4-25 / b26，其余 16..56 梯度
  m83d 二分佐证）。26 的推导式（1951-3.2.5 类公式）**残差未知**（docs
  纪律：不为凑数硬编）。
- **不求和**：+16/-16 落在不同通道 ⇒ 该像素按 max 16 ⇒ unimportant
  （U7-minusplus）。
- **alpha 通道忽略**：仅 alpha 差 ⇒ 64 same（R6/U8-alpha32）。
- 尺寸不同：重叠区正常计数，**多余像素按各自侧孤儿**计数；双侧都多余时
  36 same + 12L + 12R（m83j BS，左先右后）；单侧多余 R7 = 16+48L。
- 一侧错误（Unsupported Type / Invalid image）：另一侧**全部像素**计入
  其侧孤儿（Q7/EN-mixed-error：8×8 PNG vs 非图像 ⇒ 64 left orphan）。
- 等尺寸等戳不同内容仍 DIFF；同尺寸内容不同的 same/unimportant/important
  正常三路。
- `ignore-unimportant`：帧加头行 + 标签改名（`个忽略的不重要差异像素`），
  **计数值不变**（O4 vs O1；m83i V2）。

## 4. 输入格式（m83b/m83e/m83i/m83l/m83m）

- **PNG**：8-bit 非隔行，colour type 0（gray）/2（RGB）/6（RGBA），
  五种行过滤器全实测支持。
- **BMP**：24-bit 无压缩（Q5/U10）。gray PNG 与 BMP 都参与计数（m83e）。
- **GIF / JPEG**：签名可识别 ⇒ **Invalid image 错误行**（V3a/V3b/m83l
  EN-gif-invalid）。**无解码器**——本 build 与实测行为一致（BC 5.x 对
  不支持类型正是此错误行）；畸形 GIF 的表现**证据不足**，在案残差。
- 其他任意字节（非上述签名）：`Unsupported Type`（P12/n-L.bin）。

## 5. 产品实现（reacmp-pic + CLI 执行器）

- 新 crate `product/pic`（`reacmp-pic`），**零第三方依赖**（离线 `cargo
  test` 纪律不破）：手写 puff.c 转录 DEFLATE（stored/fixed/dynamic、
  RFC1951 长度/距离表、overflow 校验）、CRC-32（0xEDB88320）、
  PNG chunk/IHDR/IDAT/unfilter（RFC2083 §6 含 Paeth）、24-bit BMP。
  解码正确性锚定在 **CPython zlib 独立生成**的 fixture（非本 decoder
  产物）；长匹配截断缺陷由 rep28/rep100 定向 fixture 二分定位（LENGTH
  表 3/4/5-bit 组误抄）。
- `report.rs`：帧/计数/shell 渲染 + `SideImage::decode`；错误侧的
  healthy 侧全像素孤儿规则在此实现。
- CLI：`Command::PictureReport`（ast/parse/exec）；`options:` 词表按
  §1 惰性/改名/拒绝三态；`output-options:`/坏 layout/坏 token/1 或 3 个
  文件 ⇒ 106；缺文件 ⇒ 107（两侧）；零文件 ⇒ BOM shell 写出。
  `picture-report` 从 args.rs 的 KNOWN_UNSUPPORTED 名单移出（M7/M9 先例：
  留 `@<script>` 面）。
- **限制（划出范围，明示不实现）**：GIF/JPEG 解码；16-bit PNG、隔行
  PNG、调色板 PNG、压缩/顶层 BMP、BMP 调色板、icon 资源——全部走
  Invalid/Unsupported 错误行（与 Oracle 对其"不被支持类型"的实测输出
  一致，但对真实 GIF/JPEG 图片 Oracle 会给出内容计数，此处为**已知
  产品差异**，重放语料不含真 GIF/JPEG 计数单元）。

## 6. 验证落点

- **金标准**：`D:\Rea\verify\pic\`——36 例（manifest.json，append-only，
  由 `product/verify/tools/m91_add_pic_goldens.py` 串行 Oracle 生成；
  fixture 为探针字节**逐字节复制**，重跑发生在最终树就地）。覆盖帧、
  计数序、25/26 边界、alpha/gray/通道 max 规则、单双侧多余、BMP、GIF
  Invalid、非图像错误、混合错误孤儿、选项惰性/改名/多 token/空值/大写
  layout、双形态 BOM shell、title。
- **normalizer**：norm-4 —— 新增 picture 标题/头行/shell/错误行/像素
  计数对（m83 中文实测 vs m83k-m83m 英文印证）；`normalize_text` 剥离
  开头 BOM（先例 normalize_xml 行 434；图片 shell 是第一族带 BOM 的
  文本金标准）。版本 bump 测试钉 `norm-4`。
- **CLI 集成**：`script_exec.rs` 13 例图片测试（每例映射实测单元）。
- **门禁**：M91-gate-01 全量 **935/935**（anchor 424 + layout 62 + table 38
  + hex 26 + pic 72 + folder 2，current+reference 双安装；candidate 311；
  pic/oracle 72 = 36 × 两安装——英文安装同样逐例通过，即 norm-4 的英文
  侧折叠直接实测）。labels 佐证 M91-labels-02 **31/31**（norm-4 不扰动旧
  文本折叠）。pic 单项 M91-gate-pic-03 72/72（Oracle 36 + 产品 36）。
- **产品重放**：`extracted/_scratch/pic/replay_pic_product.py` 双轨
  ——A 金标准逐字节折叠比对 36/36；B 归档 m83* 全部 bcs 单元的
  退出码/是否写出重放 94/94。分类规则（106/107/0）全部引用在案
  单元格号；无记录单元用报告存在性回退。

## 7. 已知差异 / 残差未知

1. GIF/JPEG 解码缺失 → 真图片内容计数场景 Oracle 能出而本 build 出
   错误行（§5 限制）。
2. 26 阈值的推导式未在案；边界值本身成对钉死，推导留残差。
3. 畸形 GIF 是 Invalid 还是 Unsupported 证据不足（V3 系列只用合法
   GIF 头）。
4. side-by-side 的 ignore 头行只实测于 summary——side-by-side+ignore
   组合在 EN-mixed-error 批（m83m EN-sbs-ignore）实测：帧含头行、
   无计数——产品按同规则实现。
