---
name: github-publish-copyright-rule
description: 公开仓库红线——BC 商业软件的字节（原样拷贝/等长补丁/反编译/资源 dump/随附文档）一律不得进 git 提交；重建走
  verify/FIXTURE-MANIFEST.json + tools/fetch_fixtures.py
metadata:
  node_type: memory
  type: project
  originSessionId: session_fdf8d09c7ac13c4514ac21cab82d7eb5
---

2026-10-24 首推 https://github.com/liu629711-spec/BCompare（PUBLIC/main）时定案：
凡 Beyond Compare 专有字节不得出现在 git 历史/任何公开面——
verify/ver、product/ver/tests/fixtures 里的 50MB `v-*.exe`/`V*.exe` 是
BCompare.exe 逐字节拷贝（sha256 与 `D:\BCompare\BCompare\BCompare.exe` 比对实锤），
`.com`/`W*`/`v-w*` 是 BComp.com 拷贝或其等长字节补丁变体，另有 cmd/notepad
系统拷贝、`help/`=BC 随附文档、`extracted/resources|rcdata`=原样抽取的二进制资源、
`extracted/pseudocode`=Ghidra 反编译（衍生代码）。全部进 .gitignore，本地保留。

**Why:** 商业软件原样再分发是明确侵权且公开仓库几乎不可撤回；oracle 纪律=
只引用行为与哈希，不传播二进制（[[reacompare-product-direction]] 的
"不复制 BC 代码/资源"的延伸）。

**How to apply:** 以后新 fixture 若是 BC 字节/补丁变体，加进
verify/FIXTURE-MANIFEST.json（只存路径+sha256）并 ignore；恢复用
`python tools/fetch_fixtures.py`（--verify 只校验；--source KEY=PATH 指安装位置）；
补丁变体再生=product/verify/probes/m112b_ver_fields_probe.py。推前扫描：
密钥模式全库扫、>90MB 文件、用户名路径（可接受=金标准字节一部分）。
Windows 保留名文件（nul）会让 git add fatal——先 `\\?\` UNC 删或 ignore。
提交邮箱必须用 GitHub noreply（否则 GH007 隐私拦截）。
