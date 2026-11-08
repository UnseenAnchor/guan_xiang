# 第三方组件与数据来源声明

本文件随「观象桌面版」（`观象.exe`）一起分发，也可在应用内「关于 → 第三方许可」中查看。
内容按 **实际链接进二进制的依赖** 逐项核对（`go list -deps` + 各模块 LICENSE 首行），
校对日期：2026-11-07。

> 本项目自身以 MIT 许可发布，全文见仓库根目录 [`LICENSE`](../../LICENSE)。
> 版权行：`Copyright (c) 2026 UnseenAnchor and 观象 (guan_xiang) contributors`。

---

## 1. 随 EXE 分发的第三方软件

下表每一行都是**编译进二进制**的代码，不是"仅构建期使用"。

| 组件 | 版本 | 许可 | 版权行 | 在本项目中的作用 |
| :--- | :--- | :--- | :--- | :--- |
| github.com/6tail/lunar-go | v1.4.7 | MIT | Copyright (c) 2020 6tail | 农历、节气、四柱、大运的历法计算 |
| modernc.org/sqlite | v1.61.1 | BSD-3-Clause | Copyright (c) 2017 The Sqlite Authors | 纯 Go 的本地 SQLite 驱动（历史库） |
| modernc.org/libc | v1.79.0 | BSD-3-Clause | Copyright (c) 2017 The Libc Authors | sqlite 的 C 运行库替代实现 |
| modernc.org/mathutil | v1.7.1 | BSD-3-Clause | Copyright (c) 2014 The mathutil Authors | sqlite 依赖的数学工具 |
| modernc.org/memory | v1.12.1 | BSD-3-Clause | Copyright (c) 2017 The Memory Authors | sqlite 依赖的内存分配器 |
| github.com/dustin/go-humanize | v1.1.0 | MIT | Copyright (c) 2005-2008 Dustin Sallings | sqlite 依赖的数值格式化 |
| github.com/mattn/go-isatty | v0.0.24 | MIT (Expat) | Copyright (c) Yasuhiro MATSUMOTO | sqlite 依赖的终端检测 |
| github.com/ncruces/go-strftime | v1.1.0 | MIT | Copyright (c) 2022 Nuno Cruces | sqlite 依赖的时间格式化 |
| github.com/remyoudompheng/bigfft | v0.0.0-20230129092748 | BSD-3-Clause | Copyright (c) 2012 The Go Authors | sqlite 依赖的大数运算 |
| golang.org/x/sys | v0.49.0 | BSD-3-Clause | Copyright 2009 The Go Authors | Windows API 绑定 |
| github.com/jchv/go-webview2 | v0.0.0-20260205173254 | MIT | Copyright (c) 2020 John Chadwick | 原生窗口 + WebView2 承载 |
| github.com/jchv/go-winloader | v0.0.0-20250406163304 | ISC | Copyright © 2021 John Chadwick | 加载内嵌的 WebView2Loader.dll |
| Microsoft WebView2Loader.dll | 随 go-webview2 内嵌 | Microsoft 许可（BSD-3-Clause 变体） | Copyright (C) Microsoft Corporation | WebView2 的加载器（编译进 EXE） |
| 界面设计令牌 `ui/cds-theme.css` | 取自 open-claude-ui | MIT | Copyright (c) 2026 Caho1 | CDS 色彩/圆角/动效令牌层 |

补充说明：

- **modernc.org/sqlite** 内部包含 SQLite。SQLite 本身已由作者捐献至**公有领域**（见其 `LICENSE-SQLITE`）；
  模块根目录另有 `LICENSE-3RD-PARTY.md` 汇总随包第三方声明，`LICENSE-SQLITE_VEC` 对应本程序**未**链接的向量扩展。
- **WebView2Loader.dll** 是 Microsoft 的组件，以二进制形式随 EXE 分发；其许可要求「在文档或随附材料中复现版权声明与本条件」，
  本文件即该随附材料（全文见 §6.4）。
- **open-claude-ui** 的令牌层以 MIT 发布（`vendor/open-claude-ui/LICENSE`）。本项目只消费其 CSS 令牌，
  未使用其 React 组件或二进制资源；其上游仓库对逆向来源的说明由其自行承担。

## 2. 内嵌的知识数据

排盘所需的数据文件编译进 EXE（`desktop/internal/bazi/data/`），与仓库 `knowledge/` 逐字节一致。

| 文件 | 来源（仓库内声明） | 权利状态 |
| :--- | :--- | :--- |
| `ny.json` | 干支/纳音/十神/十二长生基础表，由上游项目整理 | 未单独声明许可（见下） |
| `serjson.json`（`ssxx` / `swk`） | 十神断语与日柱坐支论，由上游项目整理 | 未单独声明许可（见下） |
| `月令断语_穷通宝鉴_byAppTitle.json` | 《穷通宝鉴》条文，按上游应用的标题格式组织 | 古籍原文公有领域；编排格式来自上游 |
| `性格断语_滴天髓.json` | JSON 内 `source` 字段：`滴天髓 (维基文库 epub)` | 古籍原文公有领域；转录见 §3 |
| `大运流年_三命通会.json` | JSON 内 `source` 字段：`三命通会 卷二 (维基文库 epub)` | 同上 |
| `tiaohou_qiongtong.json`（网页端使用） | `来源` 字段：《穷通宝鉴》徐乐吾评注版，经算准网/维基文库交叉核对 | 同上 |

**关于 `ny.json` / `serjson.json` 等结构化文件**：仓库未对其单独声明许可，也未记录可追溯的授权链条。
本声明不替上游主张任何许可；如需对外再分发这些数据文件，请先自行核实来源与授权。

## 3. 古籍原文与转录

- 《穷通宝鉴》（徐乐吾评注版）、《滴天髓》、《三命通会》均为清代/民国文献，其**原文在中国大陆及多数司法辖区已进入公有领域**
  （作者逝世逾 50 年）。
- 部分内容的转录参照了**维基文库**（zh.wikisource.org）的电子文本。维基文库对页面文本通常采用 CC BY-SA 4.0 提供；
  本项目仅引用条文原文并标注出处，未复制其页面结构、注释或校勘成果。若再分发涉及维基文库的转录文本，请遵守其许可条款。
- 条文中的断语为古籍摘录，不代表本项目对命理结论的认可；相关免责说明见 `README.md` 的「内容口径」。

## 4. 仅网页端使用、不随桌面 EXE 分发

| 内容 | 来源 | 许可 |
| :--- | :--- | :--- |
| `web/locations.json`（3257 条地名与经纬度） | AreaCity-JsSpider-StatsGov，数据集版本 `2025.251231.260403` | MIT，Copyright (c) 2019 xiangyuecn |

完整许可见 [`web/LOCATION-DATA-LICENSE.txt`](../../web/LOCATION-DATA-LICENSE.txt)。该数据集由上游聚合自国家地名信息库、
高德地图与腾讯地图的行政区划数据，上游以 MIT 发布；下游再分发时建议同时核对上述数据源的条款。

## 5. 运行时与构建期依赖（不随二进制分发）

**运行时**：Microsoft Edge WebView2 Runtime（Windows 系统组件，由 Microsoft 提供与更新；本程序不自带、不修改）。
若系统缺少该运行时，程序回退为浏览器应用窗口。

**构建期工具**（不进入产物）：

- Go 工具链 — BSD-3-Clause，The Go Authors
- `github.com/tc-hib/go-winres` — MIT，用于生成 `rsrc_windows_amd64.syso`（图标与版本信息）
- Playwright — Apache-2.0，Microsoft，用于界面自动化取证
- Pillow — HPND，用于生成多尺寸 PNG / ICO
- Noto Serif SC（思源宋体）— SIL OFL-1.1，仅在设计期用于把「观象」二字转为矢量轮廓；
  仓库与分发包均**不含字体文件**，只含转曲后的路径
- Python `lunar-python` — MIT，6tail，仅在开发期作为排盘结果的对照实现，未随任何产物分发

---

## 6. 许可全文

### 6.1 MIT License（本项目）

```
Copyright (c) 2026 UnseenAnchor and 观象 (guan_xiang) contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 6.2 MIT License（open-claude-ui 令牌层）

```
Copyright (c) 2026 Caho1

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 6.3 ISC License（go-winloader）

```
Copyright © 2021, John Chadwick <john@jchw.io>

Permission to use, copy, modify, and/or distribute this software for any purpose
with or without fee is hereby granted, provided that the above copyright notice
and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
THIS SOFTWARE.
```

### 6.4 Microsoft WebView2Loader 许可

```
Copyright (C) Microsoft Corporation. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

   * Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
   * Redistributions in binary form must reproduce the above
copyright notice, this list of conditions and the following disclaimer
in the documentation and/or other materials provided with the
distribution.
   * The name of Microsoft Corporation, or the names of its contributors
may not be used to endorse or promote products derived from this
software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

### 6.5 BSD-3-Clause（modernc 系列、golang.org/x/sys、bigfft）

以下组件统一使用 BSD-3-Clause，各自版权行见 §1 表格：

```
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

### 6.6 SQLite

SQLite 已由作者捐献至公有领域：

```
SQLite Is Public Domain

All of the code and documentation in SQLite has been dedicated to the public
domain by the authors. All code authors, and representatives of the companies
they work for, have signed affidavits dedicating their contributions to the
public domain and originals of those signed affidavits are stored in a firesafe
at the main offices of Hwaci. Anyone is free to copy, modify, publish, use,
compile, sell, or distribute the original SQLite code, either in source code
form or as a compiled binary, for any purpose, commercial or non-commercial,
and by any means.
```

---

## 7. 如何重新核对

```bash
cd desktop

# 1) 列出真正链接进二进制的模块
go list -deps -f '{{if .Module}}{{.Module.Path}} {{.Module.Version}}{{end}}' . | sort -u

# 2) 打印每个模块的许可首行
MOD=$(go env GOPATH)/pkg/mod
for m in $(go list -deps -f '{{if .Module}}{{.Module.Path}}@{{.Module.Version}}{{end}}' . | grep -v guanxiang | sort -u); do
  d="$MOD/$m"; f=$(ls "$d" | grep -iE '^(LICENSE|LICENCE|COPYING)' | head -1)
  printf '%-58s %s\n' "${m%@*}" "$(head -1 "$d/$f")"
done
```

改动依赖或数据文件后，请同步更新本文件与 §1 表格，并运行
`go test ./internal/legal -run TestNoticesCoverLinkedModules` 校验表格未遗漏链接模块。
