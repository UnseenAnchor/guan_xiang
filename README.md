# 观象

观象是一款在 Windows 上离线运行的四柱排盘软件。无须注册或登录，排盘和历史记录都在本机完成。

![观象桌面版，空白历史记录](https://raw.githubusercontent.com/UnseenAnchor/guan_xiang/main/docs/screenshot-desktop-empty.png)

## 下载

前往 [GitHub Releases](https://github.com/UnseenAnchor/guan_xiang/releases/latest)，下载文件名包含 `windows-x64` 的版本。

- 系统：Windows 10 / 11，64 位（x64）
- 单文件程序，无须安装
- 窗口使用系统已有的 WebView2；未安装时会尝试使用 Edge 或 Chrome
- 程序没有代码签名，Windows 可能显示安全提示。发布页附有 SHA-256，可用于核对文件

## 功能

- 公历、农历输入，支持闰月和晚子时
- 四柱、十神、藏干、纳音、空亡、神煞、十二长生、刑冲合会
- 大运、流年、旺衰、格局、用神和古籍参照
- 可选真太阳时校正，默认关闭
- 本地保存历史记录，支持搜索、改名、备注和删除
- 导出 Markdown 或 TXT
- 浅色、深色两种界面

## 数据保存位置

历史记录保存在本机 SQLite 数据库：

```text
%APPDATA%\GuanXiang\guanxiang.db
```

删除软件不会自动删除这份数据库。软件不需要账号，也不会上传命盘数据。

## 从源码构建桌面版

需要 Go 1.24 或更高版本。桌面版只支持 Windows x64。

```powershell
cd desktop
powershell -ExecutionPolicy Bypass -File build.ps1
```

构建完成后运行：

```text
desktop\build\观象.exe
```

详细参数和开发说明见 [desktop/README.md](desktop/README.md)。

## 网页版本

仓库保留了原来的 Python 网页版本：

```bash
pip install -r requirements.txt
python web_server.py
```

打开 <http://127.0.0.1:8787>。

## 使用范围

真太阳时按东八区处理，界面支持 1900—2099 年。旺衰、格局和用神属于规则推演，古籍内容仅供参照。本项目用于传统文化研究与娱乐，不作为医疗、法律、投资或人生决策依据。

## 验证

```bash
python -W error::ResourceWarning -m unittest discover -s tests -v
python scripts/validate_oracle.py
python scripts/validate_knowledge.py
python -m compileall -q bazi scripts web_server.py main.py
node --check web/app.js

cd desktop
go test ./...
```

## 许可

项目使用 [MIT 许可](LICENSE)。桌面版包含的第三方组件、字体轮廓和知识数据说明见 [desktop/legal/notices.md](desktop/legal/notices.md)。网页版地名数据说明见 [web/LOCATION-DATA-LICENSE.txt](web/LOCATION-DATA-LICENSE.txt)。

版本记录见 [CHANGELOG.md](CHANGELOG.md)。
