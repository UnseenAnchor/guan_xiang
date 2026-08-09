# 观象 · 网页体验

网页直接调用项目现有的 `bazi.engine.build_chart`，无需安装额外 Web 框架。

## 启动

在 `bazi-engine` 目录执行：

```bash
python web_server.py
```

然后访问：<http://127.0.0.1:8787>

可通过环境变量修改监听地址和端口：

```powershell
$env:BAZI_HOST = "127.0.0.1"
$env:BAZI_PORT = "9000"
python web_server.py
```

网页支持公历日期、出生时刻、性别和经度输入；结果包含四柱、藏干、十神、纳音、长生、空亡、五行结构、刑冲合会、大运、神煞、古籍断语与真太阳时校正。

> 传统命理内容仅供文化研究与娱乐体验，不用于替代专业意见。
