# 网页体验 V2（历史实现）

V2 保留为当前输入流程和兼容层，不是正式启动入口。请使用 `python web_server.py`，现役规则以 [README.md](README.md) 为准。

与早期 V2 行为不同，当前版本中选择出生地只会记录地点；只有用户另行勾选“使用真太阳时校正排盘”才会改变排盘时间。出生地仍为选填。

离线地点库为 `web/locations.json`，包含 3,257 个中国省、市、区县/县级行政区中心点；完整数据许可见 `web/LOCATION-DATA-LICENSE.txt`。
