---
name: reacompare-m53-grammar-coverage
description: M5.3 文本语法覆盖全部完成（13 语法+BASH=plain 实锤，212 锚点，门禁 487/0）；五步闭环流程与逐格式大小写/跨行策略速查
metadata:
  node_type: memory
  type: project
  originSessionId: sess_ae16c106-965c-4d23-83db-b31f5213aea8
---

M5.3（语法格式扩展，2026-10-16 至 17，第八至十一例产品改动）已全部完成：25 格式条目中 **13 个文本语法落地**，其余 11 个为非文本比较器（CSV=TTableFormat、EXE/MEDIA/PIX 二进制、MSEXCEL/MSWORD/OPENOFFICE/PDF/RTF 文档、SORT），划出文本语法范围（docs/11 §28.4/§29.5）。

**流程（已定型，可复用于任何新格式）**：判别探针采活 Oracle 真值（预测先行、miss 即模型修正信息）→ 实现 `Grammar` 分支 → 探针夹具离线重放全等 → 金标锚点入库（`tools/m53{,_b,_e,p}_add_anchors.py` 追加 manifest，永不改既有键）→ 官方门禁串行。BASH 案例补充一条纪律：**先重放现状再决定实现**——plain 回退已 15/15 全等时，实现是多余的，正确动作是用锚点把实测行为钉成规格。

**逐格式策略速查（全部有金标证据）**：
- C-like（Cpp/Python/JS/Java）：全逐字；串 StopEOL+Escape；块注释跨行。
- XML/HTML：**串外全折叠**（TXMLFormat 结构比较器行为），串内容逐字；HTML 实体表（261 项公开数据）大小写敏感匹配、表内实体逐字（两个表内实体差大小写=`&Auml;`/`&auml;` 本就是不同实体）⇒ **类别配对**是 different 的机制：`&COPY;` 不在表内=Other（折叠成 `&copy;`）vs `&copy;` 在表内=Keyword（逐字），文本相同类别不同（`LineFacts.profile` S/K/O 序列，m53d/m53c 的 different 全在此）；`<!--`→`-->` 跨行且未闭合持续；串 StopEOL 无 Escape。
- SQL/PAS/VB/DFM/COBOL：Keyword/Identifier 折叠（CaseSensitive=False 语义）；**串逐字**（SQL `n` 前缀属 token）。
- REG：**全逐字**（`dword` 大小写敏感）；注释行首锚定 `^\s*;`。
- PERL：**全逐字**（m53m：`$Name`/`$name`、裸词、`0x1F` 全 different）；POD 块行锚定（停标记必须行首，停行整行归注释，未闭合持续）；串 StopText 无 StopEOL ⇒ 跨行（闭合可在列 0）；q(...)/s|tr/.../.../ 完整匹配按规格顺序、无 # 定界形；除法形 `/[^/]*/` 是真实元素。
- COBOL：列制——列 1-6/73-80 LineNum **不重要**（`Kind::LineNum`）、列 7 `*` 整行注释。
- VB：`rem ` 未锚定（行中也是注释）；串带 EOL 锚定回退（未闭合吞行尾）。
- BASH：BC 实测=纯文本（行为非差异；`m53p-bash-*` 锚点钉死）。

**门禁轨迹**：M53-java-grammar-01 305/0（121 锚点）→ M53-xml-html-sql-01 375/0（156）→ M53-pas-vb-reg-cobol-dfm-01 445/0（191）→ **M53-perl-bash-01 487/0（212 锚点）**；core 223、fuzz 120/120、m26 133/0、探针重放累计 144/144 全等。相关：[[reacompare-m5-state]] · [[reacompare-m2-state]]

**下一步候选**（未开工）：gateb 带边界 18 例攻坚；M5.3 之外文本侧已收敛。
