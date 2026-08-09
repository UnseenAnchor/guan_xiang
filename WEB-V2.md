# 网页体验 v2

启动优化版：

```bash
python web_server_v2.py
```

然后访问 <http://127.0.0.1:8787>。

## 输入规则

- 支持公历与农历输入；农历支持闰月，并按具体年份校验大小月。
- 出生地为选填项，不影响基础排盘流程。
- 选择出生地后，网页使用离线行政区中心经度计算真太阳时；不填写时保留输入的标准时间，并在结果中显示“未校正”。
- 当前真太阳时算法只使用经度；纬度作为地点记录保留。
- 接近时辰交界时，建议填写地点并根据实际情况核对出生时间。

## 地点隐私

地点搜索使用项目内的 `web/locations.json`，不会把搜索词发送给第三方地图服务。索引包含 3,257 个省、市、区县/县级行政区中心点。

离线数据派生自 MIT 许可的 [AreaCity-JsSpider-StatsGov](https://github.com/xiangyuecn/AreaCity-JsSpider-StatsGov)，完整许可见 `web/LOCATION-DATA-LICENSE.txt`。
