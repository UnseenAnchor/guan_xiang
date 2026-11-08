package bazi

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// 内嵌知识数据必须与仓库 knowledge/ 下的原始文件逐字节一致，防止两套数据漂移。
func TestEmbeddedKnowledgeMatchesRepo(t *testing.T) {
	pairs := []struct{ embedded, source string }{
		{string(rawNy), "../../../knowledge/ny.json"},
		{string(rawSer), "../../../knowledge/serjson.json"},
		{string(rawYueling), "../../../knowledge/月令断语_穷通宝鉴_byAppTitle.json"},
		{string(rawXingge), "../../../knowledge/性格断语_滴天髓.json"},
		{string(rawSanming), "../../../knowledge/大运流年_三命通会.json"},
	}
	for _, pair := range pairs {
		want, err := os.ReadFile(filepath.Clean(pair.source))
		if err != nil {
			t.Fatalf("读取源数据 %s 失败: %v", pair.source, err)
		}
		if string(want) != pair.embedded {
			t.Errorf("%s 与内嵌副本不一致（请同步 desktop/internal/bazi/data/）", pair.source)
		}
	}
}

func TestKnowledgeCounts(t *testing.T) {
	k, err := Knowledge()
	if err != nil {
		t.Fatalf("知识库加载失败: %v", err)
	}
	if got := len(k.ny.Gan); got != 10 {
		t.Errorf("天干计数 %d", got)
	}
	if got := len(k.ny.Zhi); got != 12 {
		t.Errorf("地支计数 %d", got)
	}
	if got := len(k.ny.NaYin); got != 60 {
		t.Errorf("纳音计数 %d", got)
	}
	if got := len(k.ny.ShiShen); got != 100 {
		t.Errorf("十神计数 %d", got)
	}
	if got := len(k.ny.ChangSheng); got != 120 {
		t.Errorf("十二长生计数 %d", got)
	}
	if got := len(k.yueling); got != 120 {
		t.Errorf("月令断语计数 %d", got)
	}
	if got := len(k.xingge); got != 10 {
		t.Errorf("十干性格计数 %d", got)
	}
}

func TestGanZhiBasics(t *testing.T) {
	if NaYin("甲子") != "海中金" {
		t.Errorf("甲子纳音 %s", NaYin("甲子"))
	}
	if got := strings.Join(XunKong("甲子"), ""); got != "戌亥" {
		t.Errorf("甲子空亡 %s", got)
	}
	if ShiShen("甲", "庚") != "七杀" {
		t.Errorf("甲见庚十神 %s", ShiShen("甲", "庚"))
	}
	if ShiErChangSheng("甲", "亥") != "长生" {
		t.Errorf("甲在亥 %s", ShiErChangSheng("甲", "亥"))
	}
	if !WuXingKe("木", "土") || WuXingKe("土", "木") {
		t.Error("五行相克判定异常")
	}
	if KeWo("木") != "金" || ShengWo("木") != "水" {
		t.Error("克我/生我判定异常")
	}
}

// 未启用真太阳时不得把经度传给排盘引擎（项目硬约束）。
func TestLongitudeIgnoredWithoutTrueSolar(t *testing.T) {
	base := Input{Calendar: "solar", Date: "1990-05-15", Time: "10:30", Sex: 1}
	withLongitude := base
	withLongitude.Longitude = "116.4"
	plain, err := Build(base)
	if err != nil {
		t.Fatalf("排盘失败: %v", err)
	}
	touched, err := Build(withLongitude)
	if err != nil {
		t.Fatalf("排盘失败: %v", err)
	}
	if touched.TrueSolar != nil || touched.Input.TrueSolar {
		t.Fatalf("未启用真太阳时却产生了校正: %+v", touched.TrueSolar)
	}
	if touched.Input.Longitude != nil {
		t.Fatalf("未启用真太阳时却记录了经度")
	}
	if pillarString(touched) != pillarString(plain) {
		t.Fatalf("经度影响了四柱: %s vs %s", pillarString(touched), pillarString(plain))
	}
}

func TestValidation(t *testing.T) {
	cases := []struct {
		name  string
		input Input
		want  string
	}{
		{"性别非法", Input{Calendar: "solar", Date: "1990-05-15", Time: "10:30", Sex: 2}, "性别参数无效"},
		{"日期格式", Input{Calendar: "solar", Date: "1990/05/15", Time: "10:30", Sex: 1}, "公历日期格式"},
		{"时间格式", Input{Calendar: "solar", Date: "1990-05-15", Time: "25:00", Sex: 1}, "时间格式"},
		{"历法非法", Input{Calendar: "julian", Date: "1990-05-15", Time: "10:30", Sex: 1}, "历法参数无效"},
		{"时区非法", Input{Calendar: "solar", Date: "1990-05-15", Time: "10:30", Sex: 1, Timezone: "UTC"}, "中国标准时间"},
		{"经度越界", Input{Calendar: "solar", Date: "1990-05-15", Time: "10:30", Sex: 1, UseTrueSolarTime: true, Longitude: "200"}, "经度应在"},
		{"缺经度", Input{Calendar: "solar", Date: "1990-05-15", Time: "10:30", Sex: 1, UseTrueSolarTime: true}, "需要填写出生地经度"},
		{"农历闰月不存在", Input{Calendar: "lunar", Time: "10:30", Sex: 1, LunarYear: 2024, LunarMonth: 5, LunarDay: 1, LunarLeap: true}, "没有闰"},
		{"农历日数越界", Input{Calendar: "lunar", Time: "10:30", Sex: 1, LunarYear: 2024, LunarMonth: 1, LunarDay: 30}, "只有"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if _, err := Build(tc.input); err == nil || !strings.Contains(err.Error(), tc.want) {
				t.Fatalf("期望包含 %q 的错误，实际 %v", tc.want, err)
			}
		})
	}
}

func TestLunarInputMatchesSolarInput(t *testing.T) {
	lunar, err := Build(Input{Calendar: "lunar", LunarYear: 1990, LunarMonth: 4, LunarDay: 21, Time: "10:30", Sex: 1})
	if err != nil {
		t.Fatalf("农历排盘失败: %v", err)
	}
	solar, err := Build(Input{Calendar: "solar", Date: "1990-05-15", Time: "10:30", Sex: 1})
	if err != nil {
		t.Fatalf("公历排盘失败: %v", err)
	}
	if pillarString(lunar) != pillarString(solar) {
		t.Fatalf("农历与公历同一天结果不一致: %s vs %s", pillarString(lunar), pillarString(solar))
	}
	if lunar.Input.Calendar != "农历" {
		t.Fatalf("农历输入口径未标注: %s", lunar.Input.Calendar)
	}
}

func TestExportContainsKeySections(t *testing.T) {
	chart, err := Build(Input{Calendar: "solar", Date: "1961-08-04", Time: "19:24", Sex: 1})
	if err != nil {
		t.Fatalf("排盘失败: %v", err)
	}
	md := chart.ToMarkdown()
	for _, keyword := range []string{"# 观象命盘", "## 四柱", "## 大运", "## 参照与断语", "辛丑", "乙未", "己巳", "甲戌"} {
		if !strings.Contains(md, keyword) {
			t.Errorf("Markdown 缺少 %q", keyword)
		}
	}
	text := chart.ToText()
	for _, keyword := range []string{"四柱", "大运", "神煞", "日主: 己"} {
		if !strings.Contains(text, keyword) {
			t.Errorf("纯文本缺少 %q", keyword)
		}
	}
}

// 农历输入（含闰月）与 Python 引擎逐例一致：期望值由 web_server.build_chart_from_request 生成。
func TestLunarInputParityWithPython(t *testing.T) {
	cases := []struct {
		year, month, day, hour, minute, sex int
		leap                                bool
		wantPillars, wantLunar              string
	}{
		{2023, 2, 15, 8, 0, 0, true, "癸卯乙卯癸巳丙辰", "二〇二三年闰二月十五"},
		{1990, 4, 21, 10, 30, 1, false, "庚午辛巳庚辰辛巳", "一九九〇年四月廿一"},
		{2024, 1, 1, 23, 30, 0, false, "甲辰丙寅乙巳丙子", "二〇二四年正月初一"},
		{2000, 11, 30, 12, 0, 1, false, "庚辰戊子丁巳丙午", "二〇〇〇年冬月三十"},
		{2020, 4, 29, 6, 15, 0, true, "庚子壬午甲午丁卯", "二〇二〇年闰四月廿九"},
	}
	for _, tc := range cases {
		chart, err := Build(Input{
			Calendar: "lunar", LunarYear: tc.year, LunarMonth: tc.month, LunarDay: tc.day,
			LunarLeap: tc.leap, Time: fmt.Sprintf("%02d:%02d", tc.hour, tc.minute), Sex: tc.sex,
		})
		if err != nil {
			t.Fatalf("%d-%d-%d 农历排盘失败: %v", tc.year, tc.month, tc.day, err)
		}
		if got := pillarString(chart); got != tc.wantPillars {
			t.Errorf("农历 %d 年 %d 月 %d 日 四柱: go=%s py=%s", tc.year, tc.month, tc.day, got, tc.wantPillars)
		}
		if chart.Lunar != tc.wantLunar {
			t.Errorf("农历文本: go=%s py=%s", chart.Lunar, tc.wantLunar)
		}
		if chart.Input.Calendar != "农历" {
			t.Errorf("历法口径未标注: %s", chart.Input.Calendar)
		}
	}
}
