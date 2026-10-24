# SsPersistent.pas 规格（第一遍完成版）

> 逆向来源：语料精读 40+ 非平凡函数（295 个中 ≥100B 的 95 个已覆盖主干）+ REA 交叉引用；原始源码 `C:\BCBuild\BCompare\Source\Ss\SsPersistent.pas`（断言内嵌路径）。
> 地址段 14067xxx–140687xxx 连续；295 函数。日期 2026-10-13。

## 1. 单元概览：四大子系统

SsPersistent 是 BC 的**持久化基座**——所有选项/规则/会话的存取都走这里：

1. **TSsPersistent 选项注册表**：类型标签驱动的"活对象 ↔ 配置树"双向同步（载入/保存/提交/重置/比较）。
2. **TSsSettingsFiler 配置树**（类 ref 14067e258，根构造器 140682c90）：区段栈式键值树，多行值、枚举名、原子文件保存（.tmp/.bak 轮换）。
3. **通用算子**：introsort 排序家族、带位置映射的索引堆、泛型数组 Fill/Move/Assign（带越界断言）。
4. **系统协同层**：PowerRequest 防睡眠、GDI SetAbortProc 重定向、全局按类注册表。

**外部消费面（REA 实证）**：配置树构造器 140682c90 的调用方 = 规则/重要性层（140db5980、140deede0/ef00/f210/f310）与对齐模式层（140e56320）——规则与会话持久化全部经由本单元。

## 2. TSsPersistent 选项注册表

### 2.1 注册块（描述符记录）布局

每个持久对象持有注册块；遍历骨架（140680670/1406809c0/140680be0/140681f00 共用）：

```
self+0   → 注册块 R
R-0xa8   → 父注册表
R+1      → kind 字节（选择条目数组）
R+0x12+kind → 该数组条目数（int16）
FUN_140077610(R, outArr)  枚举条目指针数组
条目对象：+0x2a = 名称字符串字段；+0x24 = int 默认值；*(byte*)entry.field0 = 类型标签
FUN_140077900(self, entry)  过滤（是否属于 self）
FUN_14067e7a0(entry)  是否容器/子配置项；FUN_14067e7c0(entry) 是否空项（断言用）
FUN_14067eb60(self)  取注册表（SameValues 用其判定同源）
```

### 2.2 类型标签分派（载入 14067f640 / 保存 140680410 各一套）

| 标签 | 语义 | Load | Save | 备注 |
|---|---|---|---|---|
| 1/2/3/6/9 | 整型子类 | 14067f510 | 140680310 | 2=byte(0xff 掩码)、9=word(0xffff)、6=**枚举名串查表**（名表在 item+3+byte(item+1)）、1=校验器路径 14067f3f0 |
| 4 | **double** | 14067ee50 | 14067fb70 | 配置里存**字符串**；特殊类 140003f18 走 BC 专用浮点格式（FUN_1405044a0 解析/1405046d0 格式化，关联 SsClasses 时长/大小格式化）；断言活值=0.0（行 501/673） |
| 5/6/0x12 | 字符串 | 内联 | 内联 | FUN_140683b10 读 / FUN_140684460 写 |
| 7 | 对象/多行 | 14067f1b0 | 14067fee0 | TStrings(1400ed810)→多行值（140683bf0 读/140684540 写）；TSsPersistent(14067aee8)→子配置（140683a10/140684310）；断言行 541/709 |
| 0x10 | 特殊编码值 | 14067f010 | 14067fd40 | 类 140503d30 专用字符串编码（FUN_1405051d0/FUN_1405051f0），否则 StrToIntDef 族（FUN_140045010）；断言行 519/689 |

选项上下文对象（Save/Load 各一）：{+0x40 item, +0x48 itemref, +0x50 校验器描述符, +0x70 注册表, +0x78 配置, +0x80 名, +0x88 键}。校验器协议：字段 == 1400258d0（System 区，默认哨兵）→ 直读直写；否则 FUN_14011e880/14011e960 提取 format/parse 函数指针做 string↔值转换，失败回落默认。

### 2.3 注册表级操作

- **LoadFrom(config)** `1406809c0`：两阶段——先非容器项后容器项（保证父区段先就位），逐项 FUN_14067f640。
- **SaveTo(config)** `140680be0`：容器项 FUN_1406832b0 开区段，值项 FUN_140680410 写透。
- **带变更检测** `140681100`（Load）/`140681250`（Save）：新建同类空实例 → 载入/读出 → **SameValues 比对**（14067eb70：各自存入 "junk" 临时区段 140680e20 → 区段相等性 1405e4ce0；断言行 449-451）→ 无变化跳过通知。
- **AssignValues(dst, src)** `14067e9f0`：经 "junk" 区段中转拷贝全部值。
- **ResetObjects** `140681f00`：遍历 tag=7 且类=TSsPersistentParent(14067bee8) 的项 → FUN_140682400(obj, 0) 重置（断言行 1390）。
- **特殊变量解析** `140680670`：枚举注册项，对 tag∈{4,7,0x10} 的特殊类值做替换（含 "Dummy" 占位写回 vtable+0x78；断言行 818/630/640）——BC 的 `$$(变量)` 之类文本替换机制的服务端。
- **数组型选项写入** `140681c70`：`TArray<Integer>`（ti 140006b80）打包 = [头值, values...]，写入 TSsPersistentParent；写后按需触发重置。
- **全局按类查找** `140685ad0`：全局表 DAT_141fe2248 + 锁 DAT_141fe2250；主线程特判（GetCurrentThreadId vs PTR_141fb5d90）；返回项 +0x39 标志（非零取反）。

## 3. TSsSettingsFiler 配置树

```
配置对象 {+8 父配置; +0x10 dirty/flag; +0x14 区段栈深度; +0x18 区段栈（:TSsSettingsFiler.:1 ti 14067ce20）
栈项 16B {string 名; 区段对象}}
区段类 14067e258（RTTI 字段 DefaultReader / IgnoreDefaults）
键项 16B {name: string; value: string}（ti 14067c8c0 = TSsPersistentStrItem；列表类 TSsPersistentStrList ti 14067c940）
```

- **构造** `140682c90`：根 = "junk" 区段或沿父链重建（140682b80 递归父链收集名）；断言路径 FUN_140682de0 开工。
- **区段栈**：压栈 `140682de0`（匿名新段，断言行 1772，增长 max(2n,10)）、状态修剪 `140683320`（删尾空段：段类==14067e258 或 vtable+0x30/+0x38 计数>0 即停；断言行 1899/1900）。
- **多行值**：写 `140684540(self, key, text, default)`——旧值回读 → 按 CR/LF 位图（DAT_140684814）拆行 → 行键 = FUN_1405ea290("%d", i) → 逐行 FUN_140684460 写入；读 `140683bf0(section, out, key, default)`——行键循环读、以常量（LAB_140683da8 = CRLF）拼接。**多行值 = "键名+行号" 展开的普通键**。
- **枚举值**：读 140683a90（名→索引查表）/ 写 1406843b0（索引→名）。
- **键查找** `1406827e0`：区段内二分（key 比较 FUN_140043ca0；vtable+0x68 开时连 value 一起比 FUN_140043d30）。
- **(名,值) 对插入** `140682910`：按索引移位插入 16B 记录（ti 14067c940）。
- **原子文件保存** `1406852f0(self, fileName, out err)`：断言文件名非空（行 2417）→ FileExists+属性检查 → 计数>0：写 `.tmp`（SsFileAPI 流类 140506568，**外套 TSsBufferedStream 140521750**，owns=1）→ 内容写出 `140685170` → FileAge 比较 → FUN_140509bb0(old,new,bak) 换名；空内容走删除分支。
- **磁盘格式 = XML（2026-10-13 定案）**：内容写出 `140685170` = 头部 `<?xml version="1.0" encoding="UTF-8"?>\r\n<!-- Produced by %s from Scooter Software -->\r\n`（%s = 应用版本串，FUN_14050c3a0）+ 调 **140684e20 递归序列化配置树**（+0x70 根；区段→元素、键值→缩进元素、值以 0x22 双引号经 XML 转义器 1405ea3b0 包裹，子节点缩进+1）。配置树节点协议与 XML 节点协议同构（见 SsXML.md §1.3）。
- 配置树原语（语义自 30+ 调用点归纳）：SelectKey 140682f40、GetValue 140683b10、SetValue 140684460、WriteWithUnchangedFlag 140684840/140684060/140684270/140684120/1406843b0、AddItem 140683200、EndMultiLine 140683120、ClearSection 1406835b0、EnsureSection 1406832b0、IsDirty 1406849c0、CurrentSection 1406848e0、ResetSub 140682400、Pop 140683260、SaveItems 140683f10、GetParent 140684a10。

## 4. 排序与容器算子

### introsort 家族（比较器 {fn, ctx}，fn(ctx,a,b)<0 = a<b）
- 驱动 **14067a7a0**(arr, ?, lo, hi, depthLimit, cmp)：len≤1 返回；2 → 比较交换 14067a910；3 → 三选排序 14067a950；**4–16 → 插入排序 14067a9f0**；深度耗尽 → **堆排序 14067ac80**；否则分区 14067aab0 + 右半递归/左半尾循环。
- 14067a950 = 三选中值；14067aab0 = Hoare 分区（中位放 pivot、swap hi-1、双向扫描）；14067ad90 = 堆下沉；14067ac80 = 堆排序驱动（建堆 + 逐个摘顶）。

### 索引堆（TIndexedHeap：堆 + 位置映射）
- 节点 16B {payload, heapIndex}；容器在 14012xxxx 集合单元（GetItem FUN_140129dc0 / SetItem FUN_14012a0a0 / DeleteAt FUN_14012a270 / Count at +0x10）。
- 下沉 1406868f0、上浮 1406865e0、**Delete(index)** 1406866f0（尾节点补洞 → 上浮或下沉修复，index 回写 payload[1]）。比较器存 self+8（方法指针对），ctx self+0x10。

### 泛型数组算子（同族 ti：ByteArray 1406e61b0 / UInt64Array 1406e63b8）
- **MoveRange** 140686da0(dst, dstPos, src, srcPos, n)：双向越界断言（消息 141fb5af0，类 1406e27c0）→ FUN_140686d80 搬移。
- **AssignInto** 140686ba0(dst, src)：dstLen≥srcLen 断言 → Move(src, dst, dstLen*8)。
- **FillRange** 140687270(arr, idx, n, v) / 变体 140687090：count<1 或越界跳过；nil 断言（141fb2d20/141fb2e28，类 1406e2680）；夹取后 FillChar（FUN_14000dce0）。

## 5. 系统协同层（本地址段的意外收获）

- **PowerRequest 防睡眠**：`1406857f0` 单元级解析 kernel32 的 PowerCreateRequest/PowerSetRequest（DAT_141fe2228/2230，引用计数 DAT_141fe2220）；不可用则 `SetThreadExecutionState(ES_CONTINUOUS)`。`140685700(reason)`：PowerRequestContext{Version=0, Flags=1} + Create + **PowerSetRequest(handle, 1=PowerRequestSystemRequired)**，失败关闭返回 nil。
- **GDI SetAbortProc 重定向** `140685c10`：从 FUN_1402eaaf0 起扫 `E8` 调用定位 SetAbortProc 调用点 → VirtualProtect 0x40 → **改写 rel32 目标为 0x40685beb**（自有桩）→ FlushInstructionCache → 恢复保护。BC 用自己的桩接管打印/绘制中止路径。
- 资源辅助：`140684c90` FindResource/装载类（LPCWSTR 名 + HRSRC）。

## 6. TRIVIAL 登记（代表）

- 通知对：vtable+0x20 Begin/EndUpdate、+0x48 Changed、+0x58/+0x60 dirty 查询、+0x68/+0x70 项增删通知（140681450 = 反向 Clear 全部）。
- 140681b30 = 取子项 i；140681210/230/360 = 无变化路径桩；1406818d0 = 按编号枚举写子对象（"%d" 键 + 140684310）。
- 其余 <150B 为上述原语的薄包装，全量见 inventory/SsPersistent.tsv。

## 7. 已定名的类/类型（PE 直读）

| 引用 | 身份 |
|---|---|
| 1400ed810 | **TStrings**（System.Classes，多行选项持有者） |
| 14067aee8 | **TSsPersistent**（子持久对象选项） |
| 14067bee8 | **TSsPersistentParent**（SsPersistent 单元） |
| 14067e258 | 区段类（RTTI 字段 DefaultReader/IgnoreDefaults）[类名 ?] |
| 140521750 | **TSsBufferedStream**（含 RTTI 枚举 TSsBufferedMode{bmReading, bmWriting}） |
| 140506568 | SsFileAPI 单元流类（邻近 ESsPathTooLong） |
| 14067c940/14067c8c0 | TSsPersistentStrList / TSsPersistentStrItem（ti） |
| 14067ce20 | :TSsSettingsFiler.:1（区段栈 dynarray ti） |
| 1406e61b0 / 1406e63b8 | ByteArray / UInt64Array（ti） |
| 140003f18 | 浮点特殊类 [名 ?，System 地址段] |
| 140503d30 | 0x10 编码特殊类 [名 ?，140503 段] |
| 1400258d0 | 校验器"无"哨兵 [名 ?，System/UITypes 段] |
| 14067ce70 / 14067b648 | 配置类 / 其子类判断 [名 ?] |

## 8. 断言原始行号登记（SsPersistent.pas）

0x1c1-0x1c3(449-451 SameValues), 0x1f5(501), 0x207(519), 0x21d(541), 0x259(601), 0x276(630), 0x280(640), 0x2a1(673), 0x2b1(689), 0x2c5(709), 0x30a(778), 0x332(818), 0x56e(1390), 0x6ec(1772), 0x76b/0x76c(1899/1900), 0x971(2417)。

## 8.5 实盘验证：BCState.xml（2026-10-13，决定性证据）

`%APPDATA%\Scooter Software\Beyond Compare 5\BCState.xml`（691B）逐项命中规格预测：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Produced by Beyond Compare 5 from Scooter Software -->
<BCState Version="2" MinVersion="2">
	<TBcState>
		<FirstStartup Value="False"/>
		<FormPositions>
			<TDirScriptDialog Value="669;288;1251;744"/>
		</FormPositions>
	</TBcState>
	<TCheckForUpdatesState>
		<Build Value="32774"/>
		<LastChecked Value="2026-10-12 22:53:50"/>
	</TCheckForUpdatesState>
	<TTextCompareState>
		<LeftMRUSpecs><_0 Value="D:\Reaerify\left.txt"/></LeftMRUSpecs>
		<MRUFonts><_0 Value="Consolas;10;;;F"/></MRUFonts>
	...
```

| 规格预测 | 实盘 |
|---|---|
| 头 `<?xml ... UTF-8?>` + `<!-- Produced by %s from Scooter Software -->` | **逐字一致**（%s = "Beyond Compare 5"） |
| 配置树 → 元素嵌套、值 0x22 引号 | `<TTextCompareState>` 元素（**类名做元素名**）+ `Value="..."` 属性 |
| 日期选项 = `yyyy-mm-dd hh:nn:ss` | `<LastChecked Value="2026-10-12 22:53:50"/>` **逐字符命中** |
| 多行/列表值 = "名+行号" | `<_0 Value="..."/>` 编号键 |
| 原子保存 .tmp→ReplaceFileW→.bak | `BCState.xml` + `BCState.xml.bak` 并存 |

复合值以 `;` 分隔（FormPositions="左;上;右;下"、字体 "Consolas;10;;;F"）。

## 9. 可测试锚点

1. 原子保存：产物 = 目标文件；旧文件变 .bak；失败残留 .tmp；只读目标 → err 标志。
2. 多行值往返：含 CR/LF/CRCRLF 的字符串写入后按行展开（行键 "%d" 0 基），读回以 CRLF 拼接。
3. 枚举选项：存名串、读查表；未知名回落默认。
4. byte/word 选项：写读按 0xff/0xffff 掩码截断。
5. 浮点选项：配置内为字符串；BC 特殊格式（时长/大小）双向可解析。
6. SameValues：值全等 → 加载/保存走无变更路径（不触发 Changed）。
7. introsort：4-16 元素走插入排序；深度耗尽退堆排序（结果等价有序）。
8. 索引堆 Delete(中间)：尾补洞 + 上浮/下沉择一，位置映射一致。
9. FillRange/MoveRange 越界：断言或夹取行为（记录为 oracle 断言）。
10. 重置：ResetObjects 只动 TSsPersistentParent 型对象。
11. 区段栈：尾空段自动修剪；匿名压栈名 = 空串。
12. 变量解析：tag 4/7/0x10 特殊类值被替换，未命中走 "Dummy" 写回（对象分支）。

## 10. 未解之谜

1. [?] 140003f18/140503d30/1400258d0 三个特殊类的确切类名与定义单元（140503d30 疑在 SsMapTree/Pix 域；0x10 编码格式细节待这两个类定名后补）。
2. [?] 区段类 14067e258 的类名（DefaultReader/IgnoreDefaults 字段暗示"默认值忽略"语义）。
3. ~~配置文件磁盘格式~~ **已解决（2026-10-13）**：**XML 文本**——头部 `<?xml version="1.0" encoding="UTF-8"?>` + `<!-- Produced by %s from Scooter Software -->`（140685170），配置树经 140684e20 递归序列化（值 0x22 双引号 + XML 转义 1405ea3b0）。加载侧对应 SsXML 解析器 1405e8210。
4. [?] FUN_140077610/77900/77960/77ac0/79320/79740/7b150/7b180/791e0/79630 注册块访问器族的精确布局（回归 R+kind 数组结构后可整体定性）。
5. [?] 140686da0/687090/687170 系列的元素宽度（ti 为 ByteArray/UInt64Array，实例化处各自决定）。
6. [?] 140685ad0 全局注册表的生命周期（何时注册/注销）与 +0x39 标志语义。
7. ~~140684e20 树序列化器的调用方~~ **已解决（REA procedure_callers）**：唯一调用方 = 140685170（配置文件内容写出）→ 用途 = 会话/配置 XML 落盘。
8. [?] 校验器对象（+0x50/+0x48 描述符）的注册来源（14011e880/960 所在单元的身份）。
