# 验证记录

本目录保存桌面客户端的可复现验证结果。截图由 `tools/verify_ui.py` 在真实 EXE（`--serve` 模式）+ 本机
Edge 上生成；JSON 为同一次运行的断言结果。

| 文件 | 内容 |
| :--- | :--- |
| `ui-light-1440.png` | 浅色、1440×900：侧栏历史 + 输入终端 + 四柱 + 结构分析 |
| `ui-structure.png` | 结构分析：旺衰/格局/用神指标 + 五行结构计数 + 规则推演折叠区 |
| `ui-dayun.png` | 大运轨道（含「起运前」期）与交运时间 |
| `ui-shensha.png` | 神煞与刑冲合会 chips |
| `ui-notes-expanded.png` | 「十神与日柱断语」分组展开（内部滚动、去重复标题） |
| `ui-dark-1440.png` | 深色模式 |
| `ui-history-1440.png` | 刷新页面后从本机 SQLite 回读历史命盘 |
| `ui-mobile-390.png` | 手机断点（390×844），侧栏收起 |
| `ui-mobile-drawer-390.png` | 手机端侧栏抽屉展开 |
| `ui-verification.json` | 断言结果：0 失败、0 控制台报错、0 外网请求 |
| `ui-about.png` | 精简后的「关于」弹层：仅版本与数据库位置 |
| `brand-512.png` | 当前字标（陶土底 + 纸白「观象」） |
| `wordmark-variants.png` / `wordmark-final.png` | 排版三选一与最终矢量成品 |
| `icon-sizes-check.png` | 16/24/32/48px 实际尺寸检查 |
| `logo-options.png` / `logo-options-32px-zoom.png` | 几何方案 A–F 横向对比（含 32px 实际尺寸） |
| `glyph-check-g4.png` | GPT Image 2 字标与真宋体的逐笔对照（说明为何最终不用生图） |
| `ui-brand-light.png` / `ui-brand-dark.png` | 品牌版界面（侧栏改字标排印，空状态用图标块） |
| `native-window.png` | 原生 WebView2 窗口整窗截图（标题栏左侧为品牌图标） |
| `native-titlebar-light.png` / `native-titlebar-dark.png` | 标题栏深浅两版（验证跟随界面主题） |
| `native-window-icon.png` / `exe-icon-extracted.png` | 从窗口句柄与 EXE 资源分别提取的图标 |
| `ico-sizes-audit.png` | 7 个 ICO 帧审计：16/24px 单字「观」，32px 起「观象」 |
| `exe-icon-16-zoom.png` / `exe-icon-32-zoom.png` | 从最终 EXE 反向提取并放大的小图标 |

## 复现命令

```bash
cd desktop
bash build.sh
./build/观象.exe --serve --port 8801 --data-dir .testdata &
python tools/verify_ui.py --base http://127.0.0.1:8801 --out evidence
```

## 窗口与品牌（实测记录）

```text
# 启动窗口版（无 --serve）
build\观象.exe --data-dir .testwin

# 原生 WebView2 窗口（主路径）
hwnd=267128  pid=3792  rect=377,167,1817,1067  title='观象 · 本地命盘'
  → 1440x900 DIP（DPI 175%，物理像素 2520x1575）
  → PrintWindow 截图：evidence/native-window.png（页面正常渲染）

# 窗口图标（Win32 类图标）
GCLP_HICON → 56x56、247 种颜色（非空白），即 EXE 内 RT_GROUP_ICON #1
EXE 图标：ExtractAssociatedIcon → evidence/exe-icon-extracted.png

# 标题栏主题跟随
POST /api/theme {"mode":"dark"}  → evidence/native-titlebar-dark.png（DWM 沉浸式暗色）
POST /api/theme {"mode":"light"} → evidence/native-titlebar-light.png

# 回退路径（机器无 WebView2 运行时时）
msedge.exe --app=http://127.0.0.1:8791/ --window-size=1440,900
           --user-data-dir=.testwin\ui-profile ...
#   → 无地址栏独立窗口；此时任务栏图标为浏览器图标
```

## 其他实测结论

| 检查 | 证据 |
| :--- | :--- |
| 单文件 EXE | `build/观象.exe` 11.7 MB，`CGO_ENABLED=0`，内嵌界面与知识数据 |
| 独立运行 | 把 EXE 单独复制到空目录后启动，界面、排盘、历史均正常 |
| 历史持久化 | `go test ./internal/store`（重开数据库后数据仍在）+ 重启 EXE 后 `/api/history` 仍返回原记录 |
| 无登录 | `/api/health` 返回 `"login": false, "offline": true`；界面无密码框与登录按钮 |
| 无外网 | Playwright 采集 29 个请求，全部指向 `127.0.0.1`；界面无外链字体/脚本 |
| 与网页端一致 | `go test ./internal/bazi -run TestParity`：80 例逐字段一致 |
| 农历与闰月 | `TestLunarInputParityWithPython`：5 例农历（含 2023 闰二月、2020 闰四月、晚子时）与 Python 引擎一致 |
| 数据未漂移 | `TestEmbeddedKnowledgeMatchesRepo`：内嵌 JSON 与 `knowledge/` 逐字节相同 |
| 许可声明随包 | `/legal/notices.md` 由 EXE 内嵌提供，与 `desktop/legal/notices.md` **逐字节一致**（14,147 B） |
| EXE 图标帧正确 | 从 EXE 提取 ICO，16/24/32/256px 四帧与对应专属 PNG 逐像素一致 |
| 声明不遗漏依赖 | `TestNoticesCoverLinkedModules`：用 `go list -deps` 比对 12 个链接模块，缺项即失败 |
| 关键版权行齐全 | `TestNoticesContainRequiredAttributions`：lunar-go / modernc / go-webview2 / ISC / Microsoft / CDS / AreaCity / SQLite 公有领域 |
