# BCompare 规则引擎与合并策略逆向报告

生成时间：2026-10-12（第二轮挖掘）
目标：`D:\bc-official\app\BCompare.exe`

---

## 一、本轮结论摘要

按上一轮定的优先级继续挖，结果如下：

| 优先级 | 目标 | 结果 |
|---|---|---|
| 1 | 词法解析器 | **已排查定位**：`SsLineParse.pas` 是行切分/编码层（非分词），`TextREParser.pas` 是 BC 自研正则引擎；词法 token 切分不独立成单元 |
| 2 | 重要性规则引擎 | **完整拿到**：字段 schema + 时间/浮点容差单位换算 + 条件加载语义 |
| 3 | 三方合并策略 | **已定位**：三类策略的 vtable 与调度方法已解出 |

---

## 二、优先级 1：词法层的实际归属（否定性结论也有价值）

### `SsLineParse.pas` 不是分词器

反编译其 5 个函数后确认，它做的是**字节流 → 行**的切分，与词法无关：

`FUN_14051f690` 的核心循环：
```c
if (*(int *)(param_1 + 0x78) == 0xfde9)          // 0xfde9 = UTF-8 代码页
    iVar2 = FUN_14051c510();                      // 取 UTF-8 字符字节数
else
    iVar2 = 2;                                    // 否则按 2 字节（UTF-16）
...
if (*(char *)(param_1 + 0x20) != '\0' && (*pbVar9 == 0x1a)) break;   // 0x1a = Ctrl-Z 视为 EOF
```

它负责：换行符识别（位掩码 `DAT_14051fe38`）、多字节编码边界、Ctrl-Z 老式 EOF 语义、BOM 处理。这是**文件读取层**。

### `TextREParser.pas` 是自研正则引擎

`FUN_141002300` 显示它维护自己的 NFA/状态数组（`*(param_1+0x28)` 是状态表，`FUN_140528920` 重置），并有一处内部断言：正则编译/展开出错时报 `TextREParser.pas:0x27b`。

`FUN_141007050` 是重复计数匹配：
```c
if (param_3 == 0) iVar1 = -1;                     // 匹配 0 次 → 特殊值 -1
else {
    iVar1 = param_2;
    if (1 < param_3) {
        iVar3 = param_3 - 1;
        do { iVar1 = FUN_141007000(param_1, iVar1, param_2); iVar3--; } while (iVar3 != 0);
    }
}
```
即 `{n}` 量词按次数反复推进——**BC 没有用 PCRE，是自己实现的正则**。这对复刻是好消息：正则语义边界清晰、无外部依赖。

### 词法 token 切分在哪里

`BCFILEFORMATS.xml` 的 `ElementStr`（Keyword/Identifier/Number/String/…）规则由 `FUN_140da9ad0` **解析**，但解析结果被消费的位置不在任何独立单元里，说明切分逻辑内联在文本内容模型（`TextContent.pas`）中。

`TextContent.pas` 的 `FUN_141010970`（15 个循环，最大的一个）表现为**按语法元素逐字符推进**的扫描器：
```c
uVar7 = FUN_141011da0();
uVar7 = FUN_141015c20(uVar7);
cVar3 = FUN_141037050(uVar7);                     // 取当前格式的能力标志
...
do {                                              // 对两侧内容各自扫描
    ...
} while (iVar10 != 2);
```

结论：**复刻时把词法切分直接做进内容模型即可，不必单独建解析器**——BC 自己就是内联的。

---

## 三、优先级 2：重要性规则引擎（完整可复刻）

这是本轮最有价值的成果。BC 的"重要性"标签页里每一行规则，其完整内存布局和加载语义都拿到了。

### 规则结构体布局

来自 `FUN_140db6d90`（保存规则到 XML）与 `FUN_140db71d0`（从 XML 加载规则）的字段偏移对照：

| 偏移 | 字段名 | 类型 | 含义 |
|---|---|---|---|
| `+0x00` | `ValType` | bool | 值类型（文本 / 非文本） |
| `+0x04` | `DateTimeTolerance` | int | 日期时间容差（**已折算为秒**） |
| `+0x08` | `Insig` | bool | **规则启用开关** |
| `+0x10` | `FloatTolerance` | double | 浮点容差 |
| `+0x18` | `FloatToleranceKind` | bool | 容差类型：`ftRelative` 为真 = 相对 |
| `+0x19` | `StrCaseInsig` | bool | 大小写差异视为不重要 |
| `+0x1a` | `StrWSInsig` | bool | 空白差异视为不重要 |

### 时间容差的单位换算（精确值）

`FUN_140db71d0` 把带单位的容差折算成秒：

```c
iVar4 = 1;                                        // 默认：秒
iVar2 = FUN_140016350(local_20, L"dtMins");
if (iVar2 == 0) iVar4 = 0x3c;                     // 60     → 分钟
else {
    iVar2 = FUN_140016350(local_20, L"dtHours");
    if (iVar2 == 0) iVar4 = 0xe10;                // 3600   → 小时
    else {
        iVar2 = FUN_140016350(local_20, L"dtDays");
        if (iVar2 == 0) iVar4 = 0x15180;          // 86400  → 天
    }
}
...
*(int *)(param_3 + 4) = iVar2 * iVar4;            // 容差 × 单位因子
```

即支持四种单位（秒/分/时/天），内部统一存秒。

### 规则的条件加载（一个重要设计）

```c
if ((param_5 == '\0') && (*(char *)(param_3 + 8) == '\0')) {   // 仅当 Insig 为假
    ... 加载 DateTimeTolerance / FloatTolerance / StrCaseInsig / StrWSInsig ...
}
```

**规则被关闭（`Insig` 为真）时，其下所有容差子参数不加载、不生效。** 复刻时照此实现即可，避免"半开启"状态。

### 浮点容差

```c
uVar5 = FUN_1404fd530(local_38, DAT_140db7478);    // 字符串 → double
*(undefined8 *)(param_3 + 0x10) = uVar5;
iVar2 = FUN_140016350(local_40, L"ftRelative");
*(bool *)(param_3 + 0x18) = (iVar2 == 0);          // ftRelative → 相对容差模式
```

### 与上一轮"强制重要"规则的配合

上一轮已确认 `FUN_140de5a40` 把语法元素索引 **6（Directive）、9（Operator）** 硬编码为永久重要。现在两条规则合起来构成完整的重要性体系：

1. **硬规则**（不可配置）：Directive、Operator 永远重要
2. **软规则**（用户可配置）：其余元素按 `*CaseSig`、容差、`Weights` 判定

---

## 四、优先级 3：三方合并策略

### 已解出三个策略类

`BcAlignLines.pas` 的对齐入口 `FUN_140e71a10` 按模式选择类引用常量，交给分配器实例化：

```c
cVar1 = (**(code **)*param_1)(param_1);            // 取模式
if (cVar1 == 1)      local_30 = FUN_1400107b0(PTR_PTR_140e718c0, 1);
else if (cVar1 == 2) local_30 = FUN_1400107b0(PTR_PTR_140e70f20, 1);
else                 local_30 = FUN_1400107b0(PTR_PTR_140e71510, 1);
```

用 `FollowPointers.java` 解引用得到实际 vtable：

| 类引用常量 | vtable 地址 | 方法槽（前几项） |
|---|---|---|
| `0x140e718c0` | `0x140e71988` | `0x140e72f50`、`0x140e75a70`、`0x140e719c0`(不可反编译) |
| `0x140e70f20` | `0x140e70fe8` | `0x140e71ea0` |
| `0x140e71510` | `0x140e715d8` | `0x140e72f50`（与模式 1 共享）、`0x140e73b40` |

注意 vtable 第 2 槽之后混入了字符串数据（可读出 `BcPcAlign...` 的字节残留），说明 Delphi 对象实例的方法表只占前几槽，其后紧跟对象数据。**这也是之前 `ReadPointers` 读到"unmapped"地址的原因**——不是解引用失败，而是那些槽位本就不是指针。

### 策略调度逻辑

`FUN_140e72f50`（模式 1）：
```c
uVar1 = (**(code **)(**(longlong **)(param_1 + 0x10) + 0x20))(...);   // 虚调用：取标志
*(undefined1 *)(param_1 + 0x80) = uVar1;
cVar2 = (**(code **)**(undefined8 **)(param_1 + 0x10))(...);          // 虚调用槽 0
if (cVar2 == '\0') {
    *(undefined4 *)(param_1 + 0x98) = 1;                              // 默认对齐数
    *(undefined1 *)(param_1 + 0xac) = 0;
} else {
    uVar4 = (**(code **)(...(param_1 + 0x10) + 0x38))(...);           // 虚调用槽 7
    *(undefined4 *)(param_1 + 0x98) = uVar4;                          // 对齐数量
    cVar2 = (**(code **)(...(param_1 + 0x10) + 0x48))(...);           // 虚调用槽 9
    // 只有在「槽9为真」且「槽5标志为假」时才启用，否则关闭
    *(undefined1 *)(param_1 + 0xac) = ((cVar2 != '\0') && (*(char *)(param_1 + 0x80) == '\0'));
}
```

`FUN_140e71ea0`（模式 2）是**按数量对齐**：对每个待对齐位置（`param_1 + 0x20 + i*4`，值为 `-1` 表示未设置）逐个推进，用虚调用槽 `0x18` 做单步对齐、槽 `0x50` 做复位。

`FUN_140e73b40`（模式 3）是**按范围对齐**，以 199 行为默认步长分块推进：

```c
iVar2 = param_3 + 199;
if (local_30 <= param_3 + 199) iVar2 = local_30;
local_30 = iVar2;
FUN_140e722a0(param_1, 1, iVar2, &local_30);
FUN_140e71e30(param_1, 0xffffffff, param_3, (local_30 - param_3) + 1);   // 记录该段长度
```

即三种模式共享同一接口（`param_1 + 0x10` 指向的实现对象），差异仅在推进策略：

| 模式 | 类引用 | 推进方式 |
|---|---|---|
| 1 | `0x140e718c0` | 按标志位决定启用，对齐数量取自实现对象槽 7 |
| 2 | `0x140e70f20` | 逐位置推进（`-1` = 未设置），单步用槽 `0x18` |
| 3 | `0x140e71510` | 按范围分块，默认步长 199 行 |

---

## 五、可直接用于复刻的规格汇总

### 重要性判定（完整）

```
对每个差异行：
  1. 按文件格式的词法规则切分该行
  2. 逐元素比对两侧：
       - 元素类型 ∈ {Directive(6), Operator(9)} → 该差异【重要】，终止
       - 非文本值：|左-右| <= NumTolerance → 不重要
                  相对模式时：|左-右| / max(|左|,|右|) <= NumTolerance → 不重要
       - 日期时间：|左-右| <= DateTimeTolerance（内部已折算秒） → 不重要
       - 字符串：忽略大小写（StrCaseInsig）/ 忽略空白（StrWSInsig）后相等 → 不重要
       - 否则按 Weights 权重表累加
  3. 全部元素均判定为不重要 → 该行进入"不重要"集合
  4. 集合以【有序 int 数组】存储，查询用二分（O(log n)）
```

### 对齐模式（三种）

- 模式 1：`0x140e718c0`，按标志位决定是否启用，对齐数量来自实现对象槽 7
- 模式 2：`0x140e70f20`，按数量逐位置推进，`-1` 表示该位置未设置
- 模式 3：`0x140e71510`（vtable 待解）

### 差异计算（上一轮已确认）

Myers 线性空间 + 公共前后缀裁剪 + 差异段游程合并。见 `report-algorithm.md`。

---

## 六、本轮新增文件

| 文件 | 说明 |
|---|---|
| `extracted/pseudocode/140db6d90.c` | **重要性规则保存器**（完整字段 schema） |
| `extracted/pseudocode/140db71d0.c` | **重要性规则加载器**（单位换算 + 条件加载） |
| `extracted/pseudocode/140e72f50.c` | 对齐策略模式 1 调度 |
| `extracted/pseudocode/140e71ea0.c` | 对齐策略模式 2（按数量对齐） |
| `extracted/pseudocode/14051f690.c` | 行切分器（编码/BOM/Ctrl-Z 处理） |
| `extracted/pseudocode/141002300.c` `141007050.c` | 自研正则引擎 |
| `extracted/align-strategy-classes.txt` | 策略类 vtable 解引用结果 |
| `tools/ghidra-scripts/FollowPointers.java` | 指针链追踪 + vtable 转储 |
| `extracted/pseudocode/140e73b40.c` | 对齐策略模式 3（按范围分块，步长 199） |
| `extracted/mode3-vtable.txt` | 模式 3 vtable 解引用结果 |
| `extracted/wave9-13.txt` | 本轮波次目标清单 |

累计：**282 个函数伪代码**，13 个波次，0 失败。

---

## 七、下一步建议

优先级 1 和 2 已经收口。剩下的选项：

1. ~~解模式 3 的 vtable~~ —— **已完成**（`0x140e715d8`）
2. **`Weights` 权重表的具体数值**——目前知道机制，不知道默认权重；可能在 `RES_CODES` 或 `BcSyntaxElements` 的初始化代码里
3. **转向落地**：现在算法（Myers）、分级（三态重要性）、规则（完整 schema）、格式（25 套词法）四块规格齐了，**已经可以搭一个能跑的核心比对器**

我建议第 3 项。前两项属于细节补全，不影响主体实现；而且实际写代码时会更快暴露"还缺什么"，比继续盲挖更有效率。
