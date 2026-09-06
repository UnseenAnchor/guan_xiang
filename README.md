# 观象 · 八字排盘

观象是一个本地优先的四柱排盘与传统命理知识展示网页。历法计算基于 `lunar-python`，排盘规则和知识数据同步自 `CYBZ_reverse` 的已验证版本。

当前版本：`0.5.0`

## 启动

```bash
pip install -r requirements.txt
python web_server.py
```

访问 <http://127.0.0.1:8787>。服务端使用 Python 标准库，前端不需要构建步骤。

## 时间与地点口径

- 默认按出生记录中的中国标准时间排盘。
- 公历、农历均可输入，农历输入包含月份天数和闰月校验。
- 出生地和经纬度均为选填；离线地点库支持中国省、市、区县及县级市搜索。
- 选择地点只记录出生地，不会自动改变命盘。
- 只有用户主动勾选“使用真太阳时校正排盘”时，才会向引擎传入经度。
- 启用真太阳时但没有经度时，请求会被拒绝；启用后会展示校正前后时间、四柱及变化柱。
- 当前地点库按 `Asia/Shanghai`（UTC+8）处理；海外地点需要时区与夏令时支持后再开放。

## 网页能力

- 四柱、十神、藏干、纳音、空亡、十二长生
- 天干五合与地支刑冲合会
- 天干、地支、藏干分项五行结构计数
- 全部有效大运、未来五年流年及运年参照
- 神煞、胎元、命宫、身宫
- 120 项月令正文、十干古籍描述及确定性知识索引
- 默认折叠并标注边界的旺衰、格局、取用实验推演
- 命盘可一键导出排版后的 Markdown 或 TXT 文档，导出过程完全在本机完成

没有确定匹配规则的知识短语不会被随机归入个人命盘。五行数量只表示结构计数，不等同于旺衰或喜用神。

## API

- `POST /api/chart`：排盘结果，包含输入口径、时间对比、知识匹配和版本化实验推演。
- `GET /api/lunar-year?year=1990`：农历月份、天数与闰月信息。
- `GET /api/health`：应用版本和服务状态。

## 命令行

```bash
# 标准时间
python main.py 1990 5 15 10 30 1

# 显式传入经度后启用真太阳时
python main.py 1990 5 15 10 30 1 --lon 113.3
```

## 数据来源分层

- `历法计算`：由 `lunar-python` 与本地基础表生成。
- `逆向确认`：来自 `CYBZ_reverse` 对目标 App 行为和数据结构的验证。
- `古籍参照`：《穷通宝鉴》《滴天髓》《三命通会》等资料。
- `实验模型`：旺衰、格局、喜忌、用神、病药和通关等程序化推断。

古籍补充不等同于 APK 原文；实验模型不代表唯一命理结论。

## 验证

```bash
pip install -r requirements-dev.txt
python -W error::ResourceWarning -m unittest discover -s tests -v
python scripts/validate_oracle.py
python scripts/validate_knowledge.py
python scripts/validate_knowledge.py E:\AI-Coding\06-apk_reverse\CYBZ_reverse\bazi-engine
python -m compileall -q bazi scripts web_server.py main.py
node --check web/app.js
```

`lunar-python` 是固定版本的生产历法底座；`sxtwl` 只作为开发与 CI 的独立校验源，不进入运行时依赖。当前 Golden 基线包含 60 位 Astro-Databank Rodden A/AA 人物（240 个四柱字段）和 10 个节气、晚子时、真太阳时边界案例。

当前自动化测试共 43 项，另有知识库校验、双引擎差分、Python 编译和前端 JavaScript 语法门禁。

## 目录

```text
bazi/       排盘引擎、规则与 Web Schema
knowledge/  运行时知识数据
scripts/    地点构建、知识校验与正文重建工具
tests/      引擎、Web 请求和前端契约测试
web/        命盘与离线地点资源
```

`web_server.py`、`web/app.js`、`web/styles.css` 分别是唯一正式服务端、命盘脚本和共享样式入口。版本历史只记录在 `CHANGELOG.md`。

## 已知边界

- 晚子时按逆向确认的目标 App 行为换至次日日柱。
- 真太阳时在当前网页中仅按中国标准时间处理。
- 《三命通会》模块是古籍条文的简化匹配，不是完整个人论命引擎。
- 旺衰、格局、喜忌和用神只在默认折叠且明确标注的实验区域展示。
- 桌面、平板、手机三档专项排版验收按产品安排后置；本轮只保留现有响应式规则和主流程验收。

本项目用于传统文化研究与娱乐体验，不构成医疗、法律、投资或人生决策建议。
