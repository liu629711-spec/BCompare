---
name: reacompare-m112-version-channel
description: M112 版本通道收口——version-report 全链路（ver crate + CLI + 25 金标准 + norm-6 +
  门禁 1056/1110），U-ver-1/2/3 残差与两起回归教训
metadata:
  node_type: memory
  type: project
  originSessionId: sess_ae16c106-965c-4d23-83db-b31f5213aea8
---

# M112 版本比较通道（2026-10-20 收口）

`version-report` 全链路完成，功能 8（注册表+版本）至此**全部收口**。

## 实测模型（docs/18，全条目有格证明）

- **解析**：CheckSum 在 Optional 头 **0x40**（PE32/PE32+ 同址；0x3c 是错的，读到 0x400）。`wValueLength` 计 **UTF-16 码元**（字节=×2）。**PE 头与版本资源两级独立**：资源不可达（截断 PE）→ header-only 降级（W8）。时区 UTC+8、分秒补零时不补零。
- **字段**：COFF 端序对（小端序/大端序）按**机器**（I386 打、AMD64 不打）不按位。DLL 旗帜 0x4000=控制流防护（非 0x400）。变化排序=已知键英文字典序在前 + 未知键字典序在后（非资源序）。两侧皆空的键整行剔除。**连接符按侧独立**：每组每侧最后一个有值行打 `\`（Field 需要 name/rname 双名）。**已知键**缺侧名字列打 `|`；未知键/缺整侧资源则整半空。
- **几何（全字符索引，非显示列）**：ld=LN+1；mcol=ld+LV+(3 只'='/4 有宽标记)；rn=mcol+widest+1；rd=rn+RN+1；rule=rd+RV。缺侧（V7 型）与空表（V8 型）各有实测槽宽（docs/18 §6）。
- **帧**：文件行**打包**（左右同行 + 5 空格 HEADER_GAP）阈值 **109**（108 打包/110 分行双侧夹出，U-ver-2）；左右路径相同=单行 `文件：`。ignore-unimportant **sbs 折进 Mode 行、summary 独立行**（与 pic 通道不同）。

## 残差（在案）

- **U-ver-1**：`数据/Data` 大小字段推导开放——文件大小/SizeOfImage/节和/FileAlignment/证书表/调试目录/尾零全否决；delta−blob 残差 504/516/520 无常数。**norm-6 对该行做"仅大小不同"折叠**，其余字节必须全同。
- U-ver-2（打包阈值一般化）、U-ver-3（EN 缺侧值槽=dispw+1、ZH=dispw 的不对称）。

## 基线

- ver crate 语料 18/18；CLI 206+141+118 全绿、clippy 零新增；harness pytest 160（norm-6）。
- 25 金标准 `verify/ver/`（英文参考安装生成）；重放 37 非 PASS=18 U-ver-1+19 几何；**门禁 M112-gate-03：1056/1110**（54 fail=17 reg 几何+19 ver 几何+18 U-ver-1，全部在案）。REPORT.md 带 "Version suite scope note"。

## 两起回归教训

1. **monkey-patch 破坏 harness**：给 VerCase 补 `missing` 时把 property 型（LayoutCase/AnchorCase/TableCase 等用 `@property missing`）与 method 型混改，正则批量替换 `cs.missing()` 打碎了 table/hex/pic/reg/folder 五个套件（门禁只跑出 729 结果）。修复=只改 ver 两处。**教训：改 harness 公共调用面时必须先审计每个 suite 的 case 类**。
2. **写错文件**：一次脚本复用文件句柄把 report.rs 内容覆盖进 engine.rs（版本通道引擎全丢）。靠会话内知识+lib.rs API 面完整重建。**教训：批量脚本里 file 变量必须每步重赋值；破坏性写前先确认目标路径**。

相关：[[reacompare-m10-m11-registry-channel]]、[[reacompare-maintenance-state]]、[[bcompare-clone-goal]]
