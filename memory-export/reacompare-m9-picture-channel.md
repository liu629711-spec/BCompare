---
name: reacompare-m9-picture-channel
description: ReaCompare M9 picture-report channel — measured model, hermetic
  decoder, goldens/replay/gate numbers, norm-4 BOM rule, known GIF/JPEG
  difference
metadata:
  node_type: memory
  type: project
  originSessionId: sess_ae16c106-965c-4d23-83db-b31f5213aea8
---

M9（图片比较，功能 7，原缺口 U4）已完成并全绿（2026-10-19）。

**实测模型**（docs/16，探针 m83..m83o 15 批；英文安装 m83k-m83m 印证措辞）：
- 语法 `picture-report layout:<side-by-side|summary> [options:] [title:] output-to: [output-options:] [<L> <R>]`；layout 实测**大小写不敏感**（不同于其他通道的在案事实）。
- 拒绝面：bogus/无 layout、坏 options token（valid+bogus 混也整条拒）、output-options、1 或 3 个文件 = 106；**缺任一侧文件 = 107**（不同于 hex 缺左 106）；**零文件 = exit 0 + 77B BOM shell**（`Base folder: ` 行，folder-report 同族形态，不是 hex 的 107）。
- 帧：title/`已产生：`(斜杠)/空行/[`正在忽略不重要` 在文件行**之前**]/左右文件行/错误行/计数（summary only）。side-by-side 只出帧不计数。错误是**行**不是命令失败（`不被支持的类型`=Unsupported Type / `无效图像`=Invalid image）。
- 计数序：same → unimportant → left orphan → right orphan → important，零省略。重要性=**每通道 max|Δ|≥26 important，≤25 unimportant**（25/26 成对钉死，推导式残差未知；不求和 U7；alpha 忽略 R6/U8）；尺寸差按各侧像素孤儿；**错误侧 ⇒ healthy 侧全部像素算其孤儿**（Q7/EN-mixed-error）。
- options 三态：display-mismatches/display-matches **逐字节惰性**；ignore-unimportant = 头行+标签改名（`个忽略的不重要差异像素`），计数不变；空值=默认。
- 输入：PNG 8-bit 非隔行（gray/RGB/RGBA 全 5 过滤器）+ BMP 24-bit 无压缩。GIF/JPEG 签名→Invalid（无解码器，**已知产品差异**：真图内容计数 Oracle 能出）。

**实现**：新 crate `product/pic`（reacmp-pic，**零依赖**：手写 puff 转录 DEFLATE + CRC32 + PNG/BMP + 比较 + 渲染；长匹配截断缺陷=LENGTH 表 3/4/5-bit 组误抄，rep28/rep100 定向 fixture 二分定位）。CLI 执行器 `Command::PictureReport`；args.rs 移出 picture-report。测试 fixture 用 CPython zlib 独立生成锚定。

**验证**：金标准 `D:\Rea\verify\pic\` **36 例**（`tools/m91_add_pic_goldens.py`：fixture 探针字节**逐字节复制**、manifest 存**脚本原文**、在最终树就地重跑——因为报告嵌绝对路径）；norm-4（新标题/头行/错误行/像素计数对 + **normalize_text 剥开头 BOM**，先例=normalize_xml；图片 shell 是首族带 BOM 文本金标准）；CLI 集成 13 例（script_exec 183）；重放 `extracted/_scratch/pic/replay_pic_product.py` 双轨 **130/130**（A 金标准折叠 36 + B 归档 bcs 退出面 94）。**门禁 M91-gate-01 = 935/935**（anchor 424+layout 62+table 38+hex 26+pic 72+folder 2×双安装；candidate 311；pic 在 reference 英文安装同样全过）；labels 31/31（M91-labels-02；labels 依赖同 run 的 layout 产物，单跑会 not_run）。残留 0。

**本轮踩坑实录**：① 候选调用零文件 shell 必须像探针一样传**空串占位的三个位置参数**（丢参数会挪动 %3→missing_output，M91-gate-pic-02/03 抓到）；② shell 的 BOM 粘连标题行使 zh/en 折叠失败→norm-4 的 bom-stripped 规则；③ 重放分类器把 `title:"…"` 的引号串当文件参数（P11 误 107）——前一个字符是 `:` 的引号串不是文件；④ 编辑测试时把斜杠日期写成连字符又被显示层改写迷惑，用 ord 实锤字符再改。

下一缺口：功能 8（注册表/版本）或功能 2（三方合并）或 media-report。纪律不变：[[rea-project-state]]、[[reacompare-m8-sync-channel]]、[[reacompare-m7-hex-channel]]。
