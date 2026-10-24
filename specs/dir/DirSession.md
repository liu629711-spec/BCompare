# DirSession.pas 规格（第一遍）

> 逆向来源：语料精读全部 83 个函数的伪代码（其中 ≥100 B 的 23 个全覆盖）+ PE 直读 VMT 布局与常量表。
> 原始源码 `C:\BCBuild\BCompare\Source\Dir\DirSession.pas`（断言内嵌路径，4 处锚点）。
> 地址段 `140f59090`–`140f5bce0`（连续；相邻 SsClasses 140f58ea0、DirFilters 140f5bd00）。
> 日期 2026-10-13。**未调用任何 REA/MCP 工具**——全部结论来自本地语料 + 对 `D:\bc-official\app\BCompare.exe` 的静态字节读取。

## 1. 单元概览

### 1.1 规模

| 指标 | 值 |
|---|---|
| 函数数 | **83**（归因置信度：interior-same-unit 70 / boundary-guess 9 / anchor 4） |
| 总字节 | **9569 B** |
| 地址段 | `140f59090` – `140f5bce0` |
| ≥100 B | 23 个（主干 7 个 ≥ 200 B） |
| <100 B | 60 个（其中 <50 B 有 42 个，全部为访问器/薄包装，见 §7） |
| 断言锚点 | **4 处**（`140f593e0`:0x12f=303、`140f5b570`:0x313=787、`140f5b910`:0x35f=863、`140f5ba70`:0x372=882） |
| 字符串常量 | 单元内仅 4 条：`MultiBaseSpecs`、`NoEdit`（`140f5a270`/`140f5a7f0` 各一组）、断言路径 |

**规模含义**：DirSession 是 **9.5 KB / 83 函数**的会话层——比 DirTree（77 KB/303）小一个数量级，
比 DirFilters（25 KB/191）小。它是**薄控制器**：不含比较算法，只做**选项持有 + 持久化编排 + 对 DirTree 的转发**。

### 1.2 类身份（PE 直读，Delphi VMT）

`TDirSession` 是**三层会话类族的根**（VMT 头部 `vmtClassName` 位于 VMT−0x88，Delphi x64 布局）：

| 类 | ClassName 串地址 / 内容 | VMT | InstanceSize | 父类 VMT |
|---|---|---|---|---|
| `TDirBaseSession` | `140e4dec4` `"TDirBaseSession"` | `0x140e4db20` | `0x120` (288 B) | `140e4a428`（BcSession 族） |
| **`TDirSession`** | `140f577ff` `"TDirSession"` | **`0x140f572c8`** | **`0x1e8` (488 B)** | `0x140e4da58` = TDirBaseSession |
| `TDirCompareSession` | `140f58602` `"TDirCompareSession"` | `0x140f58368` | `0x1e8` | `0x140f57200` = **TDirSession** |
| `TDirMergeSession` | `140f58ba2` `"TDirMergeSession"` | `0x140f588f0` | `0x1e8` | `0x140f57200` = **TDirSession** |
| `TDirSessionState` | `140f3388d` `"TDirSessionState"` | `0x140f336d0` | `0x98` (152 B) | `140e49f98`（TSsPersistent 族） |
| `TDirCompareSessionState` | `140f343f6` `"TDirCompareSessionState"` | `0x140f34338` | `0x98` | `0x140f336d0` = TDirSessionState |
| `TDirMergeSessionState` | `140f34626` `"TDirMergeSessionState"` | `0x140f34568` | `0x98` | `0x140f336d0` = TDirSessionState |

> Delphi x64 VMT 布局（PE 实证）：`vmtClassName` 在 **VMT−0x88**、`vmtInstanceSize` 在 **−0x80**、
> `vmtParent` 在 **−0x78**、`vmtSelfPtr` 在 **−0xC8**（自指校验通过）。
> **本单元实现 `TDirSession`**；`TDirCompareSession`/`TDirMergeSession` 是它的两个派生具体类
> （各约 6 个新增/覆写虚方法，§2.2）。`TDirSessionState` 三件套在 **DirSessionState.pas**（23 函数 / 1762 B）。

`TDirCompareSession` 的扩展 RTTI（`0x140f5865c` 区）给出派生类插槽（PE 直读，逐字）：`ClassLongHint`、
`ClassShortCaption`、`ClassTitleEn`、`ImageIndex`、`HomeImageIndex`、**`StateClass = TDirCompareSessionState`**。
`TDirMergeSession` 同构（`0x140f58bfa` 区）。

### 1.3 在 Dir 模块中的位置

```
                BcSession.pas（会话基座：槽 +0xB0..+0x128 全部继承）
                       ▲  TDirBaseSession (288 B)
                       │
             ┌─────────┴──────────┐
             │   TDirSession      │ ← 本单元（488 B 实例 / 83 fn / 9.5 KB）
             └──┬──────────────┬──┘
     ┌──────────┴───┐      ┌───┴────────────┐
  TDirCompareSession   TDirMergeSession
  （"Folder Compare"）  （"Folder Merge"）
          └────────┬───────────┘
                   ▼ StateClass
   TDirSessionState / TDirCompareSessionState / TDirMergeSessionState
     （DirSessionState.pas，152 B，TSsPersistent 派生 → 可持久化）
```

**双向引用（语料 grep 统计；去重目标函数数）**

| 方向 | 目标单元 | 数 | 说明 |
|---|---|---|---|
| DirSession → | SsPersistent.pas | 18 | 加载/保存/区段栈/通知全走 SsPersistent 原语 |
| DirSession → | DirTree.pas | 15 | 唯一的"引擎"下行接口 |
| DirSession → | BcSession.pas | 11 | 基类虚方法调用（`140e54xx`–`140e5fxx`） |
| DirSession → | SsMapTree.pas / DirFilters.pas / SsXML.pas | 3 / 1 / 1 | 经 DirTree 间接 / `140f6abb0` 过滤器对象 / `140e5ea290`（`"%d"`） |
| → DirSession | ViewDirBase / ViewDir / DirTree | 10 / 14 / 13 | 视图层主消费者 + 引擎反向读选项 |
| → DirSession | DirFilters / FrameDirSessionComparison / DlgDirScript / OpBase / OpMoveBoth | 2 / 5 / 3 / 2 / 1 | 过滤器 / 属性面板 / 脚本引擎 / 文件操作引擎 |

**与 README 侦察结论的差异**：README 记 `DirSession → DirTree 21 目标`、`被 DirTree 引用 24`。
按 `note:` 头逐文件精确统计为 **DirSession→DirTree 15**、**DirTree→DirSession 3**（M1）。

## 2. 对象布局

### 2.1 DirSession 本体字段表（InstanceSize 0x1E8 = 488 B）

所有偏移由语料逐行提取；"证据"列为写入/读取该字段的 DirSession.pas 函数地址。
继承区 `+0x00..+0x128` 属 BcSession/SsPersistent，本单元只读不改，故仅列被引用者。

| 偏移 | 宽 | 语义 | 证据 |
|---|---|---|---|
| +0x08 | ptr | 持久化宿主指针 | `140f34ff0` 用 `FUN_140010d70(x, 14067bee8)` 判"是否 TSsPersistentParent" |
| +0x38 | u8 | 设计态/加载中标志 | `140f5a270`（4 处门控配置读写）、`140f5a7f0`、`140f5af60`（`return +0x38 == 0`） |
| **+0x78** | u8 | **会话风例子类型**（==2 时启用第三方侧） | `140f5a270` L52 `(char)param_1[0xf]==2`；DirTree `140f492e0` 同判；经 `PTR_DAT_141fb5948` 映射为存储槽号 |
| **+0x88** | ptr | **状态对象 #1**（TDirSessionState 族，152 B） | `140f5b6d0` 读；`140f5af30` 对其发虚槽 **+0xa8**；DirTree `140f4f5a0` 同读 |
| **+0x90** | ptr | **状态对象 #2**（含**比较模式 +0x8A**） | `140f5b8a0` 读；`140f5ab30` 对其发虚槽 **+0xa0**；DirTree `140f4f7d0` 同读 |
| +0x98 | ptr | **配置树 A**（TSsSettingsFiler） | `140f5a630`、`140f5a720`、`140f5aa50`/`aa70` |
| +0xB0 | ptr | 会话对象回指（load 时把会话传给子树） | `140f5a080` L461 `FUN_140f5ac60(*(void**)(self+0xb0), n)` |
| +0xB8 | ptr | **配置树 B** | `140f59f70`（`140683b10` 读值）、`140f5a080`（`140682f40` 选键）、`140f5a040`/`a550`/`a570` |
| +0x118 | ptr | **多基准规格表**，元素 stride **0x20**（[index][side] 压平） | `140f5ac40`（元素数 = `*(int*)(arr-8)`）、`140f5ad10`（读改写）、`140f5aef0`/`140f5acd0` |
| +0x120 | ptr | **锁对象**（Enter/Leave） | `140f5af70`/`b200`/`b0a0`/`b330`：`(**(code**)*p)(p)` 进、`(**(code**)(*p+8))(p)` 出 |
| **+0x128** | ptr | **配置树 C-1**（根规格） | `140f59da0`（写 4 键）、`140f5af70`/`b200`/`b0a0`/`b330`（键查询/写）、`140f5b500` |
| **+0x130** | ptr | **配置树 C-2**（次规格） | `140f59da0`（另 2 键）、`140f5b200`、`140f5b330` |
| **+0x138** | ptr | **配置树 C-3**（过滤器） | `140f59d60`（身份→通知 ID 0x1b）、`140f5b500`（`140f6abb0` 读出 DirFilters 对象） |
| **+0x140** | u8 | **比较模式副本**（0..3；3 = 三方/多基准） | `140f5b4c0`（唯一写入者）；DirTree `140f478f0`/`140f4e3b0` 消费 |
| +0x141 / +0x142 | u8 | 侧位"处理脏"标志 [side 0] / [side 1] | `140f5b570`（写，断言 787）、`140f5b520`（读）、`140f5ab30`（二者互换） |
| +0x145 | u8 | handling 脏标志（另一组） | `140f5b690`（写；变化时调 +0x1D0 回调） |
| +0x148 / +0x170 | ptr[4] | **每侧规格值槽 #2 / #3** | `140f5b8e0`/`140f5ba40` 读；`140f5b910`(断言 863)/`140f5ba70`(断言 882) 写；`140f5ad10` 清 |
| +0x168 | ptr | **DirTree 实例**（唯一引擎句柄） | 全部 15 处 DirTree 调用经此；`140f5b8b0` = `*(void**)(*(self+0x168)+0x1b0)`（取 build job） |
| **+0x1B0 / +0x1B8** | ptr | **回调对 #1 — {fn, ctx}**（选项变更通知） | `140f5b4c0`：`if (*(u64*)(self+0x1b0) & ~0xFFFF) (**(code**)(self+0x1b0))(*(void**)(self+0x1b8), self)` |
| **+0x1D0 / +0x1D8** | ptr | **回调对 #2 — {fn, ctx}**（handling 变更通知） | `140f5b690`、`140f59960` L250 |

**回调对的判空惯例（重要）**：Delphi x64 用双字宽函数指针，判空写作
`(value & 0xFFFFFFFFFFFF0000) != 0`（"高 48 位非零"）——`140f5b4c0`、`140f5b690`、`140f59960` 三处一致。
`140f5b8b0` 对 `tree+0x1B0`（当前 build job）用**同一掩码**，说明该编码是"句柄 + 标记"双字，
故两个 DirSession 回调槽**也可能不是裸函数指针**（M3）。

### 2.2 TDirSession 虚方法表（VMT `0x140f572c8`，PE 直读）

槽位 `+0xB0` 起为 BcSession 虚接口区；★ = 本单元（DirSession.pas）覆写。

**BcSession 继承槽（未覆写，只列语义已定者）**

| 槽 | 指向 | 语义 |
|---|---|---|
| +0xB0 | `140e5f8a0` 305 B | 侧位有效性判定（内调 `140e5fcc0`，参数序 3/2/0/1） |
| +0xB8 | `140e5fae0` 126 B | 全部侧规格是否均空（循环 `+0x1e8` 判非零） |
| +0xC0 | `140e5fb80` 246 B | 存在性判定（遍历 `+0x178`/`+0x1a8`/`+0x1e8`） |
| +0xD8 / +0x128 / +0x180 / +0x160 | `140e56d80` / `140e567a0` / `140e57290` / `140e57260` | 恒返回 `0` |
| +0xE0 | `140e54ea0` 379 B | "允许本次操作"门（断言 BcSession.pas 0x645/0x646） |
| +0x108 / +0x110 / +0x118 | `140e55ad0` 1195 B / `140e56080` 277 B / `140e563b0` 367 B | 基类三大方法（本单元未覆写） |
| +0x130 / +0x138 | `140e57190` / `140e571b0` 各 25 B | `清out; return out`（字符串清空） |
| +0x150 / +0x158 | `140e57240` / `140e57250` 各 4 B | `return -1` |
| +0x178 | `140e5fda0` 29 B | **侧位位掩码测试** `(1<<side) & DAT_140e5fdc0` |
| +0x188 | `140e572a0` 50 B | **侧计数**：`+0x178(3) ? 2 : 0`（2 = 三方可用） |

**★ DirSession 覆写槽（PE 直读 VMT `0x140f572c8`）**

| 槽 | 指向/大小 | 语义 |
|---|---|---|
| +0xC8 | `140f5b470` 21 B | `FUN_140f4e4b0(*(self+0x168))` → 转发 DirTree |
| +0xD0 | `140f5b490` 33 B | `tree ? FUN_140f4d4e0(tree) : 0` |
| +0xF8 | `140f59c50` 98 B | `FUN_140f41b90(tree)` + `FUN_140e555d0(self,…)` + 起后台对象 `140e456f0` |
| +0x100 | `140f59ce0` 41 B | `FUN_140e55960(self)` + 调 tree 虚槽 `+0xa8` |
| +0x120 | `140f5ab30` 257 B | **交换左右侧**（整体翻转，§3.4e） |
| +0x168 / +0x238 | `140f5bba0` / `140f5bbb0` 各 ~14 B | `mov rax,[rip+…]; ret` 全局单例跳板（目标未在语料内 — M9） |
| +0x190 / +0x198 | `140f59110` 45 B / `140f59140` 60 B | `FUN_140e5f310`+`FUN_140f4b1a0(tree,…)` / `FUN_140e5f3e0`+类型判定+`FUN_140f41e10(tree,…)` |
| +0x1A0 | `140f591a0` 495 B | **取"对齐基准侧"规格**（§3.5） |
| +0x1A8 | `140f5ae40` 45 B | `FUN_140f4d7b0(tree, out, tree+0x20, side)` — 读根节点槽 |
| +0x1B0 | `140f5ae70` 85 B | `FUN_140e54370(out,v)` → `slot+0x1F0(self, side, out)` — 由值构造侧规格 |
| +0x1B8 | `140f5af30` 35 B | `(*(*state1+0x78))(state1, 6, value)` — 写 state1 持久槽 **6** |
| +0x1C0 | `140f5b1c0` 64 B | **三态判定** `!F140f5af70 ? (!F140f5b200 ? FUN_140e5fab0 : 1) : 0` |
| +0x1C8 / +0x1D0 | `140f5b450` 21 B / `140f5b500` 21 B | `FUN_140f4e4b0(tree)` / `FUN_140f6abb0(*(self+0x138))` 读过滤器配置树 |
| +0x1D8 | `140f5b520` 73 B | `IsHandlingDirty(side)`（`+0x141+side` 与 `+0x188` 组合判定） |
| +0x1E0 | `140f5b570` 124 B | **SetHandlingDirty(side,v)**，断言 **787**；通知 ID = `side+5` |
| +0x1E8 / +0x1F0 | `140f5b820` 49 B / `140f5b860` 57 B | **GetSpec(side)** = `slot+0x220(self,side,0,out)` / **SetSpec(side,v)** = `SetCount(1)`+`slot+0x228(self,0,side,v)` |
| +0x1F8 / +0x200 | `140f5b8e0` 40 B / `140f5b910` 150 B | **GetSide#2** = `*(self+0x148+side*8)` / **SetSide#2**（断言 **863**，通知 ID `side+0x0d`） |
| +0x208 / +0x210 | `140f5ba40` 40 B / `140f5ba70` 150 B | **GetSide#3** = `*(self+0x170+side*8)` / **SetSide#3**（断言 **882**，通知 ID `side+0x11`） |
| +0x218 | `140f59180` 21 B | `FUN_140f43580(*(self+0x168))` |
| +0x220 | `140f5acd0` 54 B | **GetSideValue(index, side)** = `*(self+0x118+index*0x20+side*8)` |
| +0x228 | `140f5ad10` 299 B | **SetSideValue(index, side, v)** + 撤销栈 + 树复位（§3.4d） |
| +0x230 | `140f5b4c0` 51 B | **SetCompareMode(mode)**：写 `+0x140`，若有 `+0x1B0` 回调则调用 |

**派生类覆写（PE 直读）**

| 槽 | TDirCompareSession (`0x140f58368`) | TDirMergeSession (`0x140f588f0`) |
|---|---|---|
| +0x130 / +0x138 / +0x140 | `140f5bbc0` / `140f5bbe0` / `140f5bc00`（LEA→常量串 `140f58e38/48/58`） | `140f5bca0` / `140f5bcc0` / `140f5bce0`（LEA→`140f58e68/78/88`） |
| +0x148 | **`140f5bc20` = `"Folder Compare"`** | **`140f5bd00` = `"Folder Merge"`**（DirFilters.pas） |
| +0x150 / +0x158 | `140f5bc70` = `0` / `140f5bc80` = **`222`**(0xDE) | `140f5bd50` = `1` / `140f5bd60` = **`223`**(0xDF) |
| +0x170 | `140f5bc90`（跳板） | `140f5bd80` = `1` |

`+0x150`/`+0x158` 是**会话类型的数值判别符**（Compare = 0/222，Merge = 1/223）；
`+0x130`/`+0x138`/`+0x140` 三元组是会话的**标题/提示文本**。

### 2.3 TDirSessionState 布局（152 B，DirSessionState.pas，被本单元作为子对象持有）

| 偏移 | 宽 | 语义 | 证据 |
|---|---|---|---|
| +0x40+n | u8 | 每侧"处理"标志数组（索引 1..3） | `140f34cf0`（写，断言 386）、`140f34bf0`（读） |
| +0x50+n*4 | int32 | 每侧计数值数组 | `140f34e00`（读，断言 398）、`140f34ee0`（写，断言 404） |
| **+0x8A** | u8 | **比较模式枚举（0..3，3 = 三方/多基准）** | `140f34ff0` = **源头 setter**（通知 ID **8**）；`140f34bf0` 判 `==3` |
| +0x8B | u16 | 位标志组（对称位交换） | `140f35060` setter（通知 ID **0**）；`140f34ae0` 做 4↔8/0x10↔0x20/0x40↔0x80 镜像交换 |
| +0x89 | u8 | 侧位置换索引（0..7） | `140f34ae0`（经 `PTR_DAT_141fb53d8` 重映射）、`140f35130`（写，通知 ID **10**） |
| +0x78 | u8 | 标志（同 DirSession 判据） | `140f34ab0` 加载后调 `slot+0x78(self, 6, 0)` |

**state+0x8A 的 setter 协议（`140f34ff0`，112 B）**：
```c
if (*(char*)(self + 0x8a) == mode) {
    h = *(void**)(self + 8);                              // 持久化宿主
    if (FUN_140010d70(h, PTR_PTR_14067bee8))              // 是 TSsPersistentParent?
        FUN_140681be0(h, self, 8, 0);                     // 通知"无变化"（槽 8）
} else {
    FUN_140681c40(self, 8, 1);                            // 撤销栈：变更开始
    *(char*)(self + 0x8a) = mode;                         // 写值
    FUN_140681c40(self, 8, 0);                            // 撤销栈：变更结束
}
```
`FUN_140681c40(obj, id, begin|end)` = SsPersistent 的**撤销栈分段协议**，`id` 是**持久化槽号**。
语料中出现 8 个槽号，构成完整映射：

| 槽号 | 含义 | 写入者 |
|---|---|---|
| 0 | state+0x8B（u16 标志） | `140f35060`（DirSessionState） |
| 5+side | `+0x141+side` 侧标志 | `140f5b570`（本单元，断言 787） |
| **8** | **state+0x8A 比较模式** | `140f34ff0`（DirSessionState） |
| 10 | state+0x89 侧位置换 | `140f35130`（DirSessionState） |
| 0x0D+side / 0x11+side | `+0x148`/`+0x170` 侧值 #2/#3 | `140f5b910`（863）/ `140f5ba70`（882） |
| 0x17 (23) / 0x18 (24) | `+0x118` 数组元素数 / 元素（index>0） | `140f5ac60` / `140f5ad10` |
| 9+side | `+0x118` 元素（index==0） | `140f5ad10`、`140f59960` |

**结论（线索更正）**：**DirSession 本体不含 +0x8A**。比较模式字段 `+0x8A` 属于 **state 对象**；
DirSession 经 `*(self+0x90)` 取该对象（`140f5b8a0`），把值镜像到自己的 `+0x140`（`140f5b4c0`）。
且 `FUN_140f34ff0`（任务书给定的"源头 setter"）**归属 `DirSessionState.pas`，不是 `DirSession.pas`**。

### 2.4 侧位表与常量（PE 直读）

| 符号 | 位置/值 | 用途 |
|---|---|---|
| `PTR_DAT_141fb5a78` | `.data` → `141e8b770` | **侧名表**：`[0..3] = Left, Right, Center, Output`（`[4..7]` 同序重复，供 index=1 组） |
| `PTR_DAT_141fb5948` | → `141e8b724`，字节 `00 01 03 00 01 03 …` | 会话风例 `+0x78` → 存储槽号（`2→3` 即三方用 "Output" 槽） |
| `PTR_DAT_141fafa30` / `141fafa38` | → `141e8b71a` / `141e8b720` | 顺序侧 → 存储槽映射（`140f597c0` / `140f591a0` 用） |
| `PTR_DAT_141fb53d8` | → `141e8b718`，`01 00 00 01 02 03 …` | `state+0x89` 侧位置换表 |
| `_DAT_140f351b4` / `_DAT_140f351e4` | `0x02CD` / `0x03FF`（`.text`） | state `+0x8B` 掩码（派生类 / 基类） |
| `DAT_140f34bd8` / `DAT_140f34bda` | `0x00FC` / `0x03`（`.text`） | `140f34ae0` 位交换清除掩码 / `+0x89` 重映射判据 |
| `DAT_140f4eb78` | `0x0003`（`.text`） | DirTree 侧位选掩码（`1 << side`） |
| `PTR_DAT_141fae338` | 对象表（`140def1c0`/`140deeb00`） | BcFileFormat 的"Unicode 串 ↔ 节点 ID/值"转换器 |
| `PTR_DAT_141faf3c8` | 对象表（`1400104d0`） | `140f59da0` 取 4 个键名常量（"VB"/"CPP"/"PAS"/"DFM"） |

## 3. 核心流程

### 3.1 会话创建与加载（槽 +0xD0 = `FUN_140f5a270`，732 B，本单元最大函数）

```
fun LoadFrom(self, config):                       // config = TSsSettingsFiler 对象
  buf[4] = init(PTR_DAT_140001320, 4)             // 4 元素字符串数组（"Specs" 4 侧）
  FUN_1406809c0(self, config)                     // ① 先跑基类 SsPersistent::LoadFrom
  if self+0x38 == 0:                              // ② 非"设计态"（+0x38 != 0 时跳过全部读盘）
      if config.SelectKey("MultiBaseSpecs"):      // ③ 多基准分支
          config.PushSection(); FUN_140f5a080(stackbuf); config.PopSection()
          goto L_NOMULTI                          //    ★ 不复位侧规格（跳过 ⑤⑥）
      config.SelectKey("Specs")                   // ④ 单基准：读 4 侧规格到 buf[0..3]
      FUN_140f59f70(stackbuf, &tmp)               //    ← 从 self+0xB8 配置树读键值
      copy(buf, tmp, 4)
  FUN_140f5ac60(self, 1)                          // ⑤ 基线条目数置 1（会复位树）
  for side in 0..3:                               // ⑥ 逐侧写回
      if IsSideEnabled(side) && (side != 3 || self+0x78 == 2):
          slot+0x1F0(self, side, buf[side])       //    SetSpec(side, value)
L_NOMULTI:
  if slot+0x188(self) == 0:                       // ⑦ 非三方会话才处理 NoEdit 区段
      if self+0x38 == 0:
          config.SelectKey("NoEdit"); config.PushSection()
          for side in 0..3: if IsSideEnabled(side):
              config.WriteWithUnchangedFlag(侧名表[side], 0)   // 写"无变化"标记
              slot+0x1E0(self, side)              //    SetHandlingDirty(side, 隐含值)
          config.PopSection()
      else:
          for side in 0..3: if IsSideEnabled(side): slot+0x1E0(self, side, 0)
```

**要点**
1. **两种布局互斥切换**：`MultiBaseSpecs`（N 条多基准）vs `Specs`（4 侧单基准），
   由 `self+0x38`（设计态）与配置区段存在性共同决定。
2. 多基准分支**不复位侧规格**（`goto` 跳过了步骤 ⑤⑥）——多基准下侧规格由 `140f5a080` 自行写入。
3. `NoEdit` 区段用**侧名表**（`Left/Right/Center/Output`）作键，值是布尔"无编辑"标志，
   它同时驱动 `+0x141+side`（`SetHandlingDirty`）。
4. 步骤 ⑦ 的 `slot+0x188 == 0` 门控说明：**三方/多路会话没有 NoEdit 区段**（三方是合并会话，本就可写）。

### 3.2 会话保存（槽 +0xD8 = `FUN_140f5a7f0`，603 B）

流程与加载**严格镜像**，三分支互斥：
```
fun SaveTo(self, config):
  buf[4] = init(...);  FUN_140680be0(self, config)   // 基类 SsPersistent::SaveTo
  if self+0x38 != 0: return                          // 设计态不落盘
  n = FUN_140f5ac40(self)                            // 当前基线条目数
  if n < 2:                                          // ① 单基准布局
      config.EnsureSection("MultiBaseSpecs"); config.SelectKey("Specs")
      for side in 0..3:
          if !IsSideEnabled(side) || (side==3 && self+0x78 != 2):
              clear(buf[side])                       // 不适用的侧写空串
          else: slot+0x1E8(self, &tmp, side); buf[side] = tmp   // GetSpec(side)
      FUN_140f5a630(stackbuf, buf)                   // 写入子配置树
      config.EndSection()
  else:                                              // ② 多基准布局
      config.EnsureSection("Specs"); config.SelectKey("MultiBaseSpecs")
      config.PushSection(); FUN_140f5a720(stackbuf); config.PopSection()
  if slot+0x188(self) == 0:                          // ③ 三方会话不写 NoEdit
      config.SelectKey("NoEdit"); config.PushSection()
      for side in 0..3: if IsSideEnabled(side):
          config.WriteInt(侧名表[side], slot+0x1D8(self, side), 0)   // IsHandlingDirty → int
      config.PopSection()
```
**关键不对称**：加载用 `slot+0x1F0`（SetSpec，**会复位树**），保存用 `slot+0x1E8`（GetSpec）；
加载 `NoEdit` 用 `WriteWithUnchangedFlag(名, 0)`，保存用 `WriteInt(名, 值, 0)`。

### 3.3 多基准规格的读写（`140f5a080` / `140f5a720`）

**读（`140f5a080`，411 B）**——配置树 → `+0x118` 数组：
```
tmp = init(PTR_DAT_140f59f28)                        // 动态数组容器，元素 stride 0x20
i = 0
while (config(self+0xB8).SelectKey("%d" % i)):       // 键名 = 十进制序号（SsXML 140e5ea290）
    tmp.setLength(i+1); FUN_140f59f70(self, &tmp[i]); i += 1   // 读该条目的 4 侧规格
FUN_140f5ac60(*(void**)(self+0xb0), max(i,1))        // 置条目数（≥1）
for r in 0..i-1: for side in 0..3: if IsSideEnabled(side):
    slot+0x228(会话, r, side, tmp[r*0x20 + side*8])  // SetSideValue(r, side, v)
```
> **键名 = `"%d"` 十进制串**，与 SsPersistent 多行值/列表值机制同构（BCState.xml 的 `<_0>`/`<_1>` 同源）。

**写（`140f5a720`，170 B）**——`+0x118` 数组 → 配置树：镜像，逐条 `config.AddItem("%d"%r)` +
`140f5a630(self+0x98, &array[r*0x20])`。**写侧用 `self+0x98`（配置树 A），读侧用 `self+0xB8`（配置树 B）** — M2。

### 3.4 比较模式切换与侧位值变更

**(a) DirSession 层（`140f5b4c0`，槽 +0x230）—— 纯镜像 + 回调**
```c
void SetCompareMode(self, u8 mode) {
    *(u8*)(self + 0x140) = mode;                       // 无条件写
    if ((*(u64*)(self + 0x1b0) & ~0xFFFF) != 0)        // 回调对 #1 非空
        (*(fn_t)(self + 0x1b0))(*(void**)(self + 0x1b8), self);
}
```
**无等值短路、无撤销栈**——本单元的镜像 setter 是"哑"的；真正的持久化 setter 在 state 对象上
（§2.3，`140f34ff0`，撤销栈槽 **8**）。

**(b) 引擎同步（DirTree `140f478f0`，非本单元，作为消费方记录）**：`tree+0x140` 是
`session+0x140` 的镜像值（同一枚举）；DirTree 只在二者不一致时才更新副本并置 `tree+0x200` 待办位
（0x20/0x200/8/0x80/0x40）。**变更传播链**：
`UI/脚本 → FUN_140f34ff0(state,mode)`[槽 8] `→ FUN_140f5b4c0(session,mode)` [写 `+0x140`、
调 `+0x1B0` 回调] `→ DirTree 比对 tree+0x140 → 置待办位`。

**(c) 侧位值变更（`140f5ad10`，槽 +0x228，299 B）—— 带条件撤销栈**
```c
void SetSideValue(self, int index, u8 side, void* value) {
    if (FUN_140016350(*(void**)(self+0x118 + index*0x20 + side*8), value) == 0)
        return;                                     // 值相同 → 完全不动
    id = (index == 0) ? side + 9 : 0x18;            // ① 首条基准槽=9+side；② 附加基准槽=24
    FUN_140681c40(self, id, 1);
    FUN_140f41b90(*(void**)(self+0x168));           // ★ 复位 DirTree（丢弃整棵树）
    *(void**)(self+0x118 + index*0x20 + side*8) = value;
    if (index == 0) { clear(self+0x148+side*8); clear(self+0x170+side*8); }  // 清侧值#2/#3
    FUN_140681c40(self, id, 0);
}
```
**反直觉处**：即使改的是 index ≥ 1（附加基准）**也复位整棵树**；且 `FUN_140f41b90` 出现在
**写值之前**（先作废树再写值）→ 树是"脏了就丢"的纯派生结构。
**条目数变更（`140f5ac60`，102 B）**：长度不同才动 → 撤销栈槽 **0x17(23)** → 复位树 →
`resize(self+0x118, PTR_DAT_140f571b8, 1, n)`（重建 n 个 stride-0x20 元素）→ 结束。

**(d) 整体左右交换（`140f5ab30`，槽 +0x120，257 B）** —— 本单元语义最完整的操作：
```
1. FUN_140e55160(self)                       -- 基类前置（可能有确认/抑制）
2. for r in 0 .. FUN_140f5ac40(self)-1:      -- ★ 交换多基准表每行的两侧
       FUN_14052a8e0(arr+r*0x20+0, arr+r*0x20+8)   -- 字符串交换（temp←a, a←b, b←temp）
3. swap(+0x141, +0x142)                      -- 交换 per-side 标志
4. (*(*state1 + 0xa0))(state1)               -- ★ state#1(+0x88) 虚槽 +0xa0：通知交换
5. (*(*state2 + 0xa0))(state2)               -- ★ state#2(+0x90) 虚槽 +0xa0
6. swap(self+0x29, self+0x2a)                -- 即 +0x148 ↔ +0x150（侧值#2 对）
7. tree 虚槽 +0xb8(tree, 0, 1)               -- 通知树"整树作废/重扫"
8. swap(self+0x2e, self+0x2f)                -- 即 +0x170 ↔ +0x178（侧值#3 对）
9. FUN_140682400(self, 1)                    -- SsPersistent: ResetObjects（标记全重置）
10. slot+0xe8(self)                          -- 变更广播
```
**步骤 6/8 只交换 side 0/1 两槽**（`param_1+0x29`=`+0x148`，`+0x2a`=`+0x150`），
**side 2/3 不参与交换**——三方模式下 Center/Output 是"承载侧"。

### 3.5 对 DirTree 的驱动接口（15 个目标函数）

本单元**不直接构造任何 Job**，全部通过 `*(self+0x168)`（DirTree 实例）转发。
下表按 DirTree 目标函数分组（括号内为 DirSession 侧入口）：

| DirTree 目标（大小） | 入口 | 语义 |
|---|---|---|
| `140f6780b0`(64) `140f679b50`(49) `140f679d00`(47) `140f4d7b0`(195) | `140f59960`（670 B，被 DirTree `140f55200` 反向调用） | **逐节点同步检查**：遍历"目录节点"流，比较**会话侧规格 vs 树节点槽内容**，不同则发撤销栈通知（槽 `9+side`）并写回、`ResetObjects`、广播 |
| `140f4d880`(737) | `140f5aef0`（62 B） | **写槽值**（`tree+0x20` = 根哨兵）；随后 `FUN_140e55990(self, side+0xd)` 发变更通知**槽 13+side** |
| `140f4d7b0`(195) | `140f5ae40` (+0x1A8) | 读某节点某侧的槽值 |
| `140f4e4b0`(43) | `140f5b450`(+0x1C8) / `140f5b470`(+0xC8) | 同源转发 |
| `140f4d4e0`(61) | `140f5b490` (+0xD0) | 按索引取每侧对象 |
| `140f6abb0`（DirFilters 228） | `140f5b500` (+0x1D0) | 读过滤器配置（配置树 `+0x138`） |
| `140f4f2d0`(114) `140f49600`(33) `140f4d7b0`(195) `140f4e250`(165) | `140f5b6e0`（258 B，外部 4 单元调用） | **"该侧是否有内容可构建"判定**（下详） |
| `140f4f7f0`(191) / `140f43580`(244) | `140f5b8c0`(21 B) / `140f59180`(+0x218) | — |
| `140f4b1a0`(1500) / `140f41e10`(684) | `140f59110`(+0x190) / `140f59140`(+0x198) | — |
| `140f45ab0`(420) `140f4d7b0`(195) `140f679d00`(47) | `140f591a0` (+0x1A0) | 取"对齐基准"规格（下详） |
| `140f41b90`(186) | `140f59c50`(+0xF8) / `140f5ad10`(+0x228) / `140f5ac60` | **复位整棵树**（三处：槽 +0xF8、侧位值变更、条目数变更） |
| tree 虚槽 `+0xa8` | `140f59ce0` (+0x100) | — |
| （读 `tree+0x1B0`） | `140f5b8b0`（15 B） | 取当前 build job |

**`140f5b6e0` 详解（258 B）**——最关键的"驱动"入口：仅"单基准"会话（`GetBaseCount()==1`）下，
若树根侧**无修饰位**、该侧**槽存在且为空**、而**会话规格非空**，则返回
`FUN_140f4e250(tree, tree+0x20, 4)`（测根节点修饰位 4）——即"会话规格非空但树根对应侧槽为空"时
报告"需要构建"。

**`140f591a0` (+0x1A0) 详解（495 B）**——取"对齐基准/第三方规格"：
```c
clear(out);
u8 k = PTR_DAT_141fafa38[side];                        // 顺序侧 → 存储槽
(*slot+0x1a8)(self, &p, k); if (!p) return;
node2 = FUN_140f45ab0(tree, tree_node, 0);             // 找对齐伙伴节点
if (!node2) return;
for (other in 0..3) if (other != k && (*slot+0x1a8)(self, &q, other)) {
    FUN_140f4d7b0(tree, &r, node2, other);
    (*r->vtbl+0x18)(r, out); break;                    // 取伙伴"名称/路径"
}
if (*out != 0) {
    u = FUN_140f679d00(tree, node2);                   // 父节点
    FUN_140f4d7b0(tree, &t, u, k);
    if (t) { (*t->vtbl+0x20)(t, &nm); concat(out, 3, nm, "<分隔符>", *out); }
    else clear(out);
}
```
（`LAB_140f593d8` / `DAT_140f597b8` 是拼接分隔符常量，见 M5。）

### 3.6 选项 / 文件名过滤器的读写

`140f5af70` / `140f5b200`（各 217 B）是**同构双胞胎**——只差配置树指针（`+0x128` vs `+0x130`）：
```
u8 GetFiltered(self, arg2) {
    lock(self+0x120).Enter();
    FUN_140def1c0(PTR_DAT_141fae338, &key, arg2);     // arg2 → 键字符串（BcFileFormat）
    FUN_140deeb00(PTR_DAT_141fae338, &val, arg2);     // arg2 → 值字符串
    r = FUN_140f58ea0(*(void**)(self+0x128/0x130), key, val);   // 配置树内二分查询
    lock(self+0x120).Leave();
    return r;
}
```
`140f5b0a0` / `140f5b330`（各 203 B）是**写入版**：同样的键值转换 + `FUN_140f58ec0(tree, key, val, flag)`
（内部 `FUN_1406827e0` 二分 → 存在则 `FUN_140682760` / 否则 `FUN_1406828c0` 插入）。

`FUN_140f58ea0`/`140f58ec0` 被 attribution 归到 **SsClasses.pas**（地址在 `140f59090` 之前），
但内部调 SsPersistent 原语（`1406827e0`/`140682760`/`1406828c0`）→ 实为**配置树键查询/写入的薄包装**。
**四个函数都持 `+0x120` 锁** → 配置树**不是线程安全的**，会话层自己加锁。

## 4. 对外 API：跨单元引用排行

**口径**：语料 19100 个 `.c` 文件的 `FUN_<addr>` 文本引用，按 `note:` 头归属单元，
统计**引用该目标函数的外部单元函数个数**（去重）。脚本 `tools/_scratch/` 可复现。

| # | 地址 | 大小 | 外部调用者 | 主要调用方（单元:函数数） | 语义 |
|---|---|---|---|---|---|
| 1 | **`140f5b8a0`** | 8 B | **26** | ViewDir:10, ViewDirBase:8, DirFilters:2, OpBase:2, DlgDirScript:2, DirTree:1, DlgDirReport:1 | **`GetState2()`** = `*(void**)(self+0x90)` — 全模块**最热**；取含比较模式的状态对象 |
| 2 | **`140f5b6d0`** | 8 B | **20** | DirTree:10, FrameDirSessionComparison:6, ViewDir:2, DirFilters:1, DlgDirScript:1 | **`GetState1()`** = `*(void**)(self+0x88)` |
| 3 | **`140f5ac40`** | 17 B | **13** | DirTree:9, ViewDirBase:3, ViewDir:1 | **`GetBaseCount()`** = `+0x118` 数组元素数（0 = 无数组） |
| 4 | `140f5b6e0` | 258 B | 4 | ViewDirBase:2, DlgDirScript:1, ViewDir:1 | "该侧有内容可构建"判定（§3.5） |
| 5 | `140f597c0` | 372 B | 3 | DlgDirScript:2, ViewDir:1 | 导出"每节点 × 每侧"槽值矩阵（stride 0x18，3 侧/行） |
| 6 | `140f5b8c0` / `140f5b690` | 21 / 59 B | 2 / 2 | DirFilters:2 / DirTree:2 | `FUN_140f4f7f0(tree)` 转发 / **`SetHandlingDirty`（无撤销栈版）**+ 调 `+0x1D0` 回调 |
| 7 | `140f593e0` | 725 B | 2 | ViewDirBase:1, OpMoveBoth:1 | 取某节点某侧的最佳规格值（对齐基准，断言 303） |
| 8 | `140f5af70`/`b200`/`b0a0`/`b330`/`140f5aef0`/`140f59960` | 62–217 B | 各 1 | FrameDirSessionComparison / DirTree | 过滤器读写对、槽值写入、节点同步回写 |

**单元内热访问器（不跨单元）**：`140f5b8e0`(+0x1F8)、`140f5ba40`(+0x208)、`140f5acd0`(+0x220)、
`140f5af60`、`140f5b8b0`。

### 4.1 两大状态对象的区别（由调用方行为反推）

| 访问器 | 槽 | 外部调用方典型用法 | 推断身份 |
|---|---|---|---|
| `140f5b6d0` | +0x88 | DirTree 10 处；`140f5af30` 对它调虚槽 **+0x78 (6, v)**；DirFilters `140f6b9c0` 调槽 **+0xa8 (3)** | **"编辑/处理状态"**：持 u16 位组（+0x8B）与 NoEdit 标志 |
| `140f5b8a0` | +0x90 | ViewDir/ViewDirBase 各 8–10 处；DirFilters 把它交给 **`FUN_140f34ff0` 设比较模式**；DirTree `140f4f7d0` 读它的 **+0x8A** | **"比较模式状态"**：持比较模式枚举（+0x8A） |

两者都实现 TDirSessionState 接口（虚槽 `+0xa0`/`+0xa8` 在同一批函数上），
但**实例化的具体类不同**：由派生会话的 `StateClass` 插槽（§1.2）决定。

## 5. 对外行为契约（复刻可测锚点）

1. **加载/保存往返**：`SaveTo` → `LoadFrom` 必须恢复 `+0x118` 全部元素；配置键为
   `"Specs"`（4 侧）与 `"MultiBaseSpecs"/"0","1",…`（多基准）。
2. **`MultiBaseSpecs` 与 `Specs` 互斥**：`BaseCount < 2` → 写 `Specs`；`≥ 2` → 写 `MultiBaseSpecs`。
3. **三方门控**：`session+0x78 == 2` 是 side 3（"Output"/Center）参与读写的**唯一**条件
   （`140f5a270` L52、`140f5a7f0` L301、`140f5b520`）。否则 side 3 被跳过或写空串。
4. **`NoEdit` 区段三方不写**：`slot+0x188(self) != 0`（= 2）时加载、保存**均跳过** NoEdit。
5. **比较模式 setter 无等值短路**：`140f5b4c0` 每次写 `+0x140` 并调回调（与 state 层 `140f34ff0` 不同
   ——后者有 `==` 短路 + "无变化"通知）。
6. **侧位值变更必复位树**：`140f5ad10` 在**任何** index 下都调 `FUN_140f41b90`，且在**写值之前**
   → "规格变了，整棵树作废重扫"。
7. **值相等时零副作用**：`140f5ad10`/`b910`/`ba70`/`b570`/`140f34cf0`/`140f34ee0` 全部以
   `FUN_140016350(a,b) != 0` 为前置门——值相同连撤销栈都不开。
8. **撤销栈槽号是持久化槽契约**：槽 8 = 比较模式、0 = state u16 位组、10 = 侧位置换、
   13+n / 17+n = 侧值 #2/#3、23/24 及 9+n = 多基准数组。复刻必须保持这些 ID。
9. **交换作用域**：`140f5ab30` 交换 `+0x141/142`、`+0x148/150`、`+0x170/178` 及 `+0x118` 每行的
   [0]↔[1]，**不触碰 side 2/3**。
10. **配置树访问加锁**：`140f5af70`/`b200`/`b0a0`/`b330` 全持 `+0x120` 锁。
11. **断言契约**（保留为 debug 断言）：`140f593e0` 要求 `slot+0x178(self,2)` 真（303）；
    `140f5b570` 要求 `slot+0x188(self)==0`（787）；`140f5b910`/`ba70` 要求 `param_3!=0` 时侧位有效（863/882）。

## 6. 平凡函数登记（<100 B，共 60 个；<50 B 的 42 个）

登记格式：`地址  大小  [VMT槽]  语义`。`+0xN` 表示"读/写 `self+N`"。

**6.1 虚方法表槽（<50 B，构成 API 表面）**
```
140f5b470  21  +0xC8   FUN_140f4e4b0(*(self+0x168))          140f5b450  21  +0x1C8  同上
140f5b490  33  +0xD0   tree ? FUN_140f4d4e0(tree) : 0        140f5b500  21  +0x1D0  FUN_140f6abb0(*(self+0x138))
140f59ce0  41  +0x100  FUN_140e55960(self) + tree 虚槽 +0xa8  140f59180  21  +0x218  FUN_140f43580(*(self+0x168))
140f5ae40  45  +0x1A8  FUN_140f4d7b0(tree, out, tree+0x20, side)
140f5b8e0  40  +0x1F8  *out = *(void**)(self+0x148+side*8)     140f5ba40  40  +0x208  *out = *(self+0x170+side*8)
140f5acd0  54  +0x220  *out = *(self+0x118+index*0x20+side*8) 140f5b8c0  21  —      FUN_140f4f7f0(*(self+0x168))
```
**6.2 访问器 / 判定器（8–73 B）**
```
140f5b8a0   8  return *(void**)(self+0x90)         ← 全模块最热（26 外部调用者）
140f5b6d0   8  return *(void**)(self+0x88)         ← 第二热（20）
140f5ac40  17  *(self+0x118) ? *(int*)(*(self+0x118)-8) : 0    ← 第三热（13）
140f5af60   8  return *(char*)(self+0x38) == 0     （"非设计态"谓词）
140f5b8b0  15  return *(void**)(*(self+0x168)+0x1b0)  （取当前 build job）
140f5b520  73  IsHandlingDirty(side)（+0x141+side 与 +0x188 组合判定）
```
**6.3 析构片段（23–82 B；清理栈/局部结构，被 VMT 或 RTTI 表引用）**
```
140f596c0 82 清 p2+0x50/0x58/0x68/0x70/0x78   140f59c00 78 清 p2+0x48..0x70
140f59390 59 清 p2+0x50/0x58/0x60             140f5a220 66 清 p2+0x28/0x30 + init 0x58
140f5a590 63 清 p2+0x28/0x68                  140f5aa90 50 清 p2+0x20/0x48
140f5b7f0 37 清 p2+0x30/0x38                  140f59eb0 28 清 p2+0x30（4 元素）
140f59940/140f59cc0/140f5aed0 23 各 清 p2+0x38    140f5a060 23 清 p2+0x20    140f5a7d0 23 清 p2+0x28
140f5b080/140f5b1a0/140f5b310/140f5b430 28 各 清 p2+0x28（2 元素）
```
**6.4 配置树区段端点 / RTTI 桩（26–32 B）**
```
140f5aa50 26 / 140f5aa70 26   config(self+0x98) PopSection（成对）
140f5a550 26 / 140f5a570 26   config(self+0xB8) PopSection（成对）
140f5a700 30 / 140f5a040 30   config(*(p2+0x60)+0x98/0xB8) PopSection
140f5bca0 / bcc0 / bce0  32   TDirMergeSession 三槽：lea rdx,[140f58e68/78/88] + jmp FUN_14001e690
```
**6.5 其他（<100 B 但语义已定）**
```
140f59c50  98  +0xF8   FUN_140f41b90(tree) + FUN_140e555d0(self,…) + 起 140e456f0 后台对象
140f5ae70  85  +0x1B0  FUN_140e54370(out, v) 后转 slot+0x1F0
140f59d10  76  FUN_140e5f570(self,…) + tree 虚槽 +0xb0
140f59d60  62  按配置树指针（+0x128/+0x130/+0x138）→ 通知 ID 0x19/0x1a/0x1b 的映射
140f5aef0  62  FUN_140f4d880(tree,…) + FUN_140e55990(self, side+0xd)
140f5b860  57  +0x1F0  SetSpec(side,v) = SetCount(1) + slot+0x228(self,0,side,v)
140f5af30  35  +0x1B8  对 state1 写持久槽 6
140f5b820  49  +0x1E8  GetSpec(side,out) = slot+0x220(self,side,0,out)
140f59140  60  +0x198  FUN_140e5f3e0 + 类型判定(PTR_PTR_140e50b78) + FUN_140f41e10(tree,…)
140f59110  45  +0x190  FUN_140e5f310 + FUN_140f4b1a0(tree,…)
140f59da0 265  在 +0x128 写 4 键、+0x130 写 2 键（键名常量 = 四个扩展名：
               140f59ed8="VB"、140f59eec="CPP"、140f59f04="PAS"、140f59f1c="DFM"）
140f597c0 372  导出"每节点 × 每侧"槽值矩阵（stride 0x18，3 侧/行；见 §4 第 5 行）
```

## 7. 断言行号登记（DirSession.pas，**4 处 / 4 函数**）

| 函数 | 行（十六进制 / 十进制） | 断言内容 |
|---|---|---|
| `140f593e0` | `0x12f` / **303** | `slot+0x178(self, 2)` 为真（第 2 侧必须可用）——"取对齐基准"前置条件 |
| `140f5b570` | `0x313` / **787** | `slot+0x188(self) == 0`（非三方会话）——`SetHandlingDirty` 前置条件 |
| `140f5b910` | `0x35f` / **863** | `param_3 != 0` 时 `slot+0x178(self, side)` 必须为真（侧位有效才能写非空值） |
| `140f5ba70` | `0x372` / **882** | 同上（侧值 #3 版本） |

**相邻单元**：`DirSessionState.pas` 4 处——`140f34bf0`:0x179(377)、`140f34cf0`:0x182(386)、
`140f34e00`:0x18e(398)、`140f34ee0`:0x194(404)；
`FrameDirSessionComparison.pas` 1 处——`141b16240`:0x112(274)。

## 8. 未解之谜

**M1 `[?]` DirTree ↔ DirSession 双向引用计数与 attribution 冲突。**
任务书/README 记「DirSession 调 DirTree 21 目标、被 DirTree 引用 24」；本地精确统计为
**DirSession→DirTree 15**、**DirTree→DirSession 3**（`140f5b8a0`+`140f5b6d0`+`140f5ac40` 共 20 个调用者函数）。
差额来自 attribution 的 `edge-nearest`/`boundary-guess` 归属（本单元 9 个 boundary-guess）。**需一次 attribution 边界复核。**

**M2 `[?]` 多基准读用 `+0xB8`、写用 `+0x98` 的配置树不一致。**
`140f5a080`（读）用 `*(self+0xb8)`，`140f5a720`（写）用 `self+0x98`；但 `140f5a630`/`140f59f70`
（4 侧规格读写）内部都用 `*(self+0xb8)`。可能：(a) 两者指向同一配置树的**不同区段**；
(b) 其中一个是**当前区段句柄缓存**。**未定论**——需追 `+0x98`/`+0xB8` 的写入点。

**M3 `[?]` 回调槽 +0x1B0/+0x1B8 与 +0x1D0/+0x1D8 的指针编码。**
判空写法 `(value & 0xFFFFFFFFFFFF0000) != 0` 与 DirTree `tree+0x1B0`（当前 build job，**已知非函数指针**）
完全相同 → 可能是"低 16 位为标签"的双字句柄。语料内**无任何写入这两对槽的代码**，来源不明。

**M4 `[?]` 两个 TDirSessionState 实例的角色分化。**
`session+0x88` 与 `session+0x90` 都实现 TDirSessionState 接口，但 `StateClass` 只声明**一个**具体类：
(a) 同一 `StateClass` 的两个实例（编辑状态 / 比较模式）；(b) `+0x88` 基类实例、`+0x90` 派生类实例。
**未定论**——需追两槽的构造赋值点（语料内未找到）。

**M5 `[?]` `LAB_140f593d8` / `DAT_140f597b8` 拼接分隔符内容。**
`140f591a0`/`140f593e0` 用 `FUN_140016280(out, 3, a, 分隔符, b)` 拼接；分隔符常量**未能从 PE 解码**
（位于 `.text`，字节不像 UTF-16 常量）。需定点 dump。

**M6 `[?]` 各配置树（`+0x98`/`+0xB8`/`+0x128`/`+0x130`/`+0x138`）的区段名。**
`PushSection` 调用均为 `FUN_140682de0(config)`（**匿名新区段**，无语段名参数）→ 区段名未知，
由 §3.1 推断应属 `"Specs"`/`"MultiBaseSpecs"`/`"NoEdit"` 之一。

**M7 `[?]` `+0x78` 字段的完整值域。** 已知值 `2` 使 side 3 生效（`140f5a270` L52、`140f5a7f0` L301、
`140f492e0`、`140f5b520`）；0/1/3 语义未知。且它写作 `(char)param_1[0xf]`（而非 `*(char*)(self+0x78)`）
——LE 下等价，但字段归属需确认。

**M8 `[?]` DirTree（`+0x168`）的构造时机与 `TDirSession` 的构造者。** `140f5a270`（LoadFrom）
第 45 行即调 `FUN_140f5ac60(self,1)`，后者**无条件**访问 `*(self+0x168)` 并复位树
→ **Loading 前 DirTree 必须已构造**。但本单元 83 函数中**无任何构造函数**，实例化者（BcSession 类工厂？）未知。

**M9 `[?]` `140f5bba0`/`140f5bbb0`/`140f5bc90` 三个 VMT 槽目标未在语料内。** 均为
`mov rax,[rip+disp32]; ret`（全局单例跳板），被槽 `+0x168`/`+0x238`/`+0x170` 引用，
但 attribution 为 0 函数（落在函数边界之间）→ 全局对象身份未知。

**M10 `[?]` `140f59960` 的"反向调用"语义与触发时机。** 它是 DirSession.pas 内**唯一**被 DirTree
调用的函数（调用者 `140f55200`）：遍历 `FUN_1406780b0(tree,1,·)`（目录节点流）×4 侧，比较
**会话规格 vs 树节点槽**，不同则发撤销栈通知并写回。形似"树 → 会话"回写。**触发时机未定**
——需读 `140f55200`（在 DirTree 内）。
