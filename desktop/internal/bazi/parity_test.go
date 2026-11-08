package bazi

import (
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
	"testing"
)

// 交叉验证：Go 客户端排盘必须与仓库既有 Python 引擎逐字段一致。
// 黄金样本由 desktop/tools/gen_golden.py 从 bazi.engine.build_chart 生成。

type goldenFile struct {
	SchemaVersion int          `json:"schema_version"`
	CaseCount     int          `json:"case_count"`
	Cases         []goldenCase `json:"cases"`
}

type goldenCase struct {
	Name                  string           `json:"name"`
	Input                 goldenInput      `json:"input"`
	ExpectedPillars       *string          `json:"expected_pillars"`
	ExpectedCorrectedTime *string          `json:"expected_corrected_time"`
	ExpectedCorrectedDate *string          `json:"expected_corrected_date"`
	Lunar                 string           `json:"lunar"`
	ShengXiao             string           `json:"shengxiao"`
	DayMaster             string           `json:"day_master"`
	Pillars               []goldenPillar   `json:"pillars"`
	TrueSolar             *goldenTrueSolar `json:"true_solar"`
	Strength              struct {
		Score      float64 `json:"score"`
		Level      string  `json:"level"`
		MonthState string  `json:"month_state"`
	} `json:"strength"`
	GeJu struct {
		Name string `json:"name"`
		Kind string `json:"kind"`
		Note string `json:"note"`
	} `json:"geju"`
	YongShen struct {
		Use     []string `json:"use"`
		Avoid   []string `json:"avoid"`
		TiaoHou string   `json:"tiaohou"`
		Method  string   `json:"method"`
		Bridge  *string  `json:"bridge"`
	} `json:"yongshen"`
	ShenSha    [][2]string `json:"shensha"`
	Relations  [][4]string `json:"relations"`
	DaYun      [][5]any    `json:"dayun"`
	DaYunStart []any       `json:"dayun_start"`
	LiuNian    [][2]any    `json:"liunian"`
	Notes      []string    `json:"notes"`
	TaiYuan    string      `json:"taiyuan"`
	MingGong   string      `json:"minggong"`
	ShenGong   string      `json:"shengong"`
}

type goldenInput struct {
	Date      string   `json:"date"`
	Time      string   `json:"time"`
	Sex       int      `json:"sex"`
	Longitude *float64 `json:"longitude"`
}

type goldenPillar struct {
	Name           string   `json:"name"`
	GanZhi         string   `json:"ganzhi"`
	CangGan        []string `json:"canggan"`
	ShiShenGan     string   `json:"shishen_gan"`
	ShiShenCangGan []string `json:"shishen_canggan"`
	NaYin          string   `json:"nayin"`
	KongWang       []string `json:"kongwang"`
	ChangSheng     string   `json:"changsheng"`
	DiShi          string   `json:"dishi"`
}

type goldenTrueSolar struct {
	Original    string  `json:"original"`
	CorrectDate string  `json:"correct_date"`
	Corrected   string  `json:"corrected"`
	TotalMinute float64 `json:"total_minute"`
	LonDiff     float64 `json:"lon_diff"`
	Equation    float64 `json:"equation"`
}

func loadGolden(t *testing.T) goldenFile {
	t.Helper()
	raw, err := os.ReadFile("../../testdata/golden_charts.json")
	if err != nil {
		t.Fatalf("读取黄金样本失败: %v", err)
	}
	var file goldenFile
	if err := json.Unmarshal(raw, &file); err != nil {
		t.Fatalf("解析黄金样本失败: %v", err)
	}
	if file.SchemaVersion != 1 || file.CaseCount != len(file.Cases) || len(file.Cases) < 60 {
		t.Fatalf("黄金样本结构异常: schema=%d count=%d cases=%d", file.SchemaVersion, file.CaseCount, len(file.Cases))
	}
	return file
}

func toInput(in goldenInput) Input {
	result := Input{Calendar: "solar", Date: in.Date, Time: in.Time, Sex: in.Sex, Timezone: "Asia/Shanghai"}
	if in.Longitude != nil {
		result.Longitude = strconv.FormatFloat(*in.Longitude, 'f', -1, 64)
		result.UseTrueSolarTime = true
	}
	return result
}

func pillarString(c *Chart) string {
	var b strings.Builder
	for _, p := range c.Pillars {
		b.WriteString(p.GanZhi)
	}
	return b.String()
}

func TestParityWithPythonEngine(t *testing.T) {
	file := loadGolden(t)
	for _, tc := range file.Cases {
		tc := tc
		t.Run(tc.Name, func(t *testing.T) {
			chart, err := Build(toInput(tc.Input))
			if err != nil {
				t.Fatalf("排盘失败: %v", err)
			}
			if tc.ExpectedPillars != nil && pillarString(chart) != *tc.ExpectedPillars {
				t.Fatalf("四柱不一致: go=%s py=%s", pillarString(chart), *tc.ExpectedPillars)
			}
			if chart.Lunar != tc.Lunar {
				t.Errorf("农历不一致: go=%q py=%q", chart.Lunar, tc.Lunar)
			}
			if chart.ShengXiao != tc.ShengXiao || chart.DayMaster != tc.DayMaster {
				t.Errorf("生肖/日主不一致: go=%s/%s py=%s/%s", chart.ShengXiao, chart.DayMaster, tc.ShengXiao, tc.DayMaster)
			}
			if chart.TaiYuan != tc.TaiYuan || chart.MingGong != tc.MingGong || chart.ShenGong != tc.ShenGong {
				t.Errorf("胎元/命宫/身宫不一致: go=%s/%s/%s py=%s/%s/%s",
					chart.TaiYuan, chart.MingGong, chart.ShenGong, tc.TaiYuan, tc.MingGong, tc.ShenGong)
			}
			for i, want := range tc.Pillars {
				got := chart.Pillars[i]
				if got.Name != want.Name || got.GanZhi != want.GanZhi || got.ShiShenGan != want.ShiShenGan ||
					got.NaYin != want.NaYin || got.ChangSheng != want.ChangSheng || got.DiShi != want.DiShi {
					t.Errorf("柱 %s 不一致: go=%+v py=%+v", want.Name, got, want)
				}
				if strings.Join(got.CangGan, ",") != strings.Join(want.CangGan, ",") {
					t.Errorf("柱 %s 藏干不一致: go=%v py=%v", want.Name, got.CangGan, want.CangGan)
				}
				if strings.Join(got.ShiShenCangGan, ",") != strings.Join(want.ShiShenCangGan, ",") {
					t.Errorf("柱 %s 藏干十神不一致: go=%v py=%v", want.Name, got.ShiShenCangGan, want.ShiShenCangGan)
				}
				if strings.Join(got.KongWang, ",") != strings.Join(want.KongWang, ",") {
					t.Errorf("柱 %s 空亡不一致: go=%v py=%v", want.Name, got.KongWang, want.KongWang)
				}
			}
			if chart.Strength.Score != tc.Strength.Score || chart.Strength.Level != tc.Strength.Level ||
				chart.Strength.MonthState != tc.Strength.MonthState {
				t.Errorf("旺衰不一致: go=%.1f/%s/%s py=%.1f/%s/%s", chart.Strength.Score, chart.Strength.Level,
					chart.Strength.MonthState, tc.Strength.Score, tc.Strength.Level, tc.Strength.MonthState)
			}
			if chart.GeJu.Name != tc.GeJu.Name || chart.GeJu.Kind != tc.GeJu.Kind || chart.GeJu.Note != tc.GeJu.Note {
				t.Errorf("格局不一致: go=%+v py=%+v", chart.GeJu, tc.GeJu)
			}
			if strings.Join(chart.YongShen.Use, "/") != strings.Join(tc.YongShen.Use, "/") ||
				strings.Join(chart.YongShen.Avoid, "/") != strings.Join(tc.YongShen.Avoid, "/") ||
				chart.YongShen.Method != tc.YongShen.Method {
				t.Errorf("用神不一致: go=%+v py=%+v", chart.YongShen, tc.YongShen)
			}
			if chart.YongShen.Bridge != ptrValue(tc.YongShen.Bridge) {
				t.Errorf("通关不一致: go=%q py=%q", chart.YongShen.Bridge, ptrValue(tc.YongShen.Bridge))
			}
			if len(chart.ShenSha) != len(tc.ShenSha) {
				t.Errorf("神煞条数不一致: go=%d py=%d %v", len(chart.ShenSha), len(tc.ShenSha), chart.ShenSha)
			} else {
				for i, want := range tc.ShenSha {
					if chart.ShenSha[i].Name != want[0] || chart.ShenSha[i].Where != want[1] {
						t.Errorf("神煞[%d] 不一致: go=%s/%s py=%s/%s", i, chart.ShenSha[i].Name,
							chart.ShenSha[i].Where, want[0], want[1])
					}
				}
			}
			if len(chart.Relations) != len(tc.Relations) {
				t.Errorf("刑冲合会条数不一致: go=%d py=%d %+v", len(chart.Relations), len(tc.Relations), chart.Relations)
			} else {
				for i, want := range tc.Relations {
					got := chart.Relations[i]
					if got.Type != want[0] || got.Where != want[1] || got.GZ != want[2] || got.Note != want[3] {
						t.Errorf("刑冲合会[%d] 不一致: go=%+v py=%v", i, got, want)
					}
				}
			}
			if len(chart.DaYun.List) != len(tc.DaYun) {
				t.Errorf("大运条数不一致: go=%d py=%d", len(chart.DaYun.List), len(tc.DaYun))
			} else {
				for i, want := range tc.DaYun {
					got := chart.DaYun.List[i]
					if got.Index != anyInt(want[0]) || got.GanZhi != anyString(want[1]) ||
						got.StartYear != anyInt(want[2]) || got.EndYear != anyInt(want[3]) || got.Age != anyString(want[4]) {
						t.Errorf("大运[%d] 不一致: go=%+v py=%v", i, got, want)
					}
				}
			}
			start := []any{chart.DaYun.StartYears, chart.DaYun.StartMonths, chart.DaYun.StartDays,
				chart.DaYun.StartHours, chart.DaYun.JiaoYun}
			if fmt.Sprint(start) != fmt.Sprint(tc.DaYunStart) {
				t.Errorf("起运详情不一致: go=%v py=%v", start, tc.DaYunStart)
			}
			if len(chart.LiuNian) != len(tc.LiuNian) {
				t.Errorf("流年条数不一致: go=%d py=%d", len(chart.LiuNian), len(tc.LiuNian))
			} else {
				for i, want := range tc.LiuNian {
					if chart.LiuNian[i].Year != anyInt(want[0]) || chart.LiuNian[i].GanZhi != anyString(want[1]) {
						t.Errorf("流年[%d] 不一致: go=%+v py=%v", i, chart.LiuNian[i], want)
					}
				}
			}
			var titles []string
			for _, note := range chart.Notes {
				titles = append(titles, note.Title)
			}
			if strings.Join(titles, "|") != strings.Join(tc.Notes, "|") {
				t.Errorf("断语标题不一致:\n go=%v\n py=%v", titles, tc.Notes)
			}
			if tc.TrueSolar != nil {
				if chart.TrueSolar == nil {
					t.Fatalf("真太阳时缺失")
				}
				got, want := chart.TrueSolar, tc.TrueSolar
				if got.Original != want.Original || got.CorrectDate != want.CorrectDate || got.Corrected != want.Corrected ||
					got.TotalMinute != want.TotalMinute || got.LonDiff != want.LonDiff || got.Equation != want.Equation {
					t.Errorf("真太阳时不一致: go=%+v py=%+v", got, want)
				}
			} else if chart.TrueSolar != nil {
				t.Errorf("不应产生真太阳时校正: %+v", chart.TrueSolar)
			}
			if tc.ExpectedCorrectedTime != nil && chart.TrueSolar != nil && chart.TrueSolar.Corrected != *tc.ExpectedCorrectedTime {
				t.Errorf("校正时间与边界样本不一致: go=%s want=%s", chart.TrueSolar.Corrected, *tc.ExpectedCorrectedTime)
			}
			if tc.ExpectedCorrectedDate != nil && chart.TrueSolar != nil && chart.TrueSolar.CorrectDate != *tc.ExpectedCorrectedDate {
				t.Errorf("校正日期与边界样本不一致: go=%s want=%s", chart.TrueSolar.CorrectDate, *tc.ExpectedCorrectedDate)
			}
		})
	}
}

func ptrValue(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}

func anyString(v any) string {
	if v == nil {
		return ""
	}
	return fmt.Sprint(v)
}

func anyInt(v any) int {
	switch n := v.(type) {
	case float64:
		return int(n)
	case int:
		return n
	}
	return -1
}
