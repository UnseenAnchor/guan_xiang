# 项目协作说明

## 定位

观象是本地优先的四柱排盘与传统命理知识展示网页；排盘与知识数据同步自已验证的 `CYBZ_reverse` 资料。

## 启动与验证

```bash
pip install -r requirements.txt
python web_server.py
python -W error::ResourceWarning -m unittest discover -s tests -v
python scripts/validate_knowledge.py
node --check web/app_v2.js
node --check web/app_v3.js
```

默认访问 <http://127.0.0.1:8787>。`web_server.py` 是唯一正式入口。

## 技术栈

- Python 标准库 HTTP 服务与 `lunar-python`
- 原生 HTML、CSS、JavaScript
- 本地 JSON/文本知识库与离线中国行政区地点库

## 目录与约定

- `bazi/`：排盘、规则和独立黄历模块；`knowledge/`：知识数据。
- `web/`：当前页面；V3 结果层暂时覆盖 V2 输入层，后续再模块化合并。
- `tests/` 与 `scripts/validate_knowledge.py`：合并前门禁。
- `README.md` 是现役使用与能力边界；`CHANGELOG.md` 只记版本历史；`WEB-*.md` 只记实现分层，不作为用户合同。
- 逆向证据与过程文档以 `CYBZ_reverse` 为真身，本仓库不复制维护第二套逆向结论。
- 出生地选填，真太阳时默认关闭；未启用时不得把经度传给排盘引擎。
- 五行数量只称结构计数；古籍参照、规则匹配和实验模型必须分层标识。
- 旺衰、格局、喜忌、用神、病药和通关不得宣称唯一正确，也不得在网页默认作确定性吉凶判断。
- 以 `main` 为最终基线；改动先建 `agent/...` 分支，经测试、推送和 PR 对抗审查后合并。

## 当前状态与下一步

当前版本 `0.3.0`，基线为30项自动化测试。黄历页面、章节导航与实验推演已接入；下一阶段优先整理 V2/V3 前端分层、地点搜索键盘与无障碍交互，并执行已后置的桌面、平板、手机三档专项排版验收。
