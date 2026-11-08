package bazi

import (
	"fmt"
	"math"
	"strconv"
	"strings"
	"time"

	"github.com/6tail/lunar-go/calendar"
)

// 排盘入口：把 web 端传入的生辰参数转成命盘。与 bazi/engine.py + web_server.py 的口径一致。

// Input 生辰入参（公历或农历）。
type Input struct {
	Calendar         string `json:"calendar"`
	Date             string `json:"date"`
	Time             string `json:"time"`
	LunarYear        int    `json:"lunar_year"`
	LunarMonth       int    `json:"lunar_month"`
	LunarDay         int    `json:"lunar_day"`
	LunarLeap        bool   `json:"lunar_leap"`
	Sex              int    `json:"sex"`
	Longitude        string `json:"longitude"`
	Latitude         string `json:"latitude"`
	UseTrueSolarTime bool   `json:"use_true_solar_time"`
	Timezone         string `json:"timezone"`
	Name             string `json:"name"`
}

// ChartInput 命盘内记录的实际输入口径。
type ChartInput struct {
	Calendar  string   `json:"calendar"`
	Original  string   `json:"original"`
	Sex       string   `json:"sex"`
	Solar     string   `json:"solar"`
	Longitude *float64 `json:"longitude"`
	TrueSolar bool     `json:"true_solar"`
	TimeBasis string   `json:"time_basis"`
}

type Pillar struct {
	Name           string   `json:"name"`
	GanZhi         string   `json:"ganzhi"`
	Gan            string   `json:"gan"`
	Zhi            string   `json:"zhi"`
	GanWuXing      string   `json:"gan_wuxing"`
	ZhiWuXing      string   `json:"zhi_wuxing"`
	GanYinYang     string   `json:"gan_yinyang"`
	ZhiYinYang     string   `json:"zhi_yinyang"`
	ShengXiao      string   `json:"shengxiao"`
	CangGan        []string `json:"canggan"`
	CangGanWuXing  []string `json:"canggan_wuxing"`
	ShiShenGan     string   `json:"shishen_gan"`
	ShiShenCangGan []string `json:"shishen_canggan"`
	NaYin          string   `json:"nayin"`
	NaYinJian      string   `json:"nayin_jian"`
	KongWang       []string `json:"kongwang"`
	ChangSheng     string   `json:"changsheng"`
	DiShi          string   `json:"dishi"`
}

type TrueSolar struct {
	Original    string  `json:"original"`
	CorrectDate string  `json:"correct_date"`
	Corrected   string  `json:"corrected"`
	TotalMinute float64 `json:"total_minute"`
	LonDiff     float64 `json:"lon_diff"`
	Equation    float64 `json:"equation"`
}

type ElementCount struct {
	Name  string `json:"name"`
	Count int    `json:"count"`
}

type DaYun struct {
	Index      int    `json:"index"`
	GanZhi     string `json:"ganzhi"`
	StartYear  int    `json:"start_year"`
	EndYear    int    `json:"end_year"`
	Age        string `json:"age"`
	ShiShen    string `json:"shishen"`
	ChangSheng string `json:"changsheng"`
	NaYin      string `json:"nayin"`
}

type DaYunInfo struct {
	StartYears  int     `json:"start_years"`
	StartMonths int     `json:"start_months"`
	StartDays   int     `json:"start_days"`
	StartHours  int     `json:"start_hours"`
	JiaoYun     string  `json:"jiaoyun"`
	List        []DaYun `json:"list"`
}

type LiuNian struct {
	Year       int    `json:"year"`
	GanZhi     string `json:"ganzhi"`
	ShiShen    string `json:"shishen"`
	ChangSheng string `json:"changsheng"`
	Note       string `json:"note"`
}

type ChartMeta struct {
	Engine    string `json:"engine"`
	LunarLib  string `json:"lunar_lib"`
	Knowledge string `json:"knowledge"`
	Version   string `json:"version"`
}

type Chart struct {
	Input        ChartInput     `json:"input"`
	Lunar        string         `json:"lunar"`
	ShengXiao    string         `json:"shengxiao"`
	DayMaster    string         `json:"day_master"`
	Pillars      []Pillar       `json:"pillars"`
	TrueSolar    *TrueSolar     `json:"true_solar"`
	TaiYuan      string         `json:"taiyuan"`
	MingGong     string         `json:"minggong"`
	ShenGong     string         `json:"shengong"`
	Strength     Strength       `json:"strength"`
	GeJu         GeJu           `json:"geju"`
	YongShen     YongShen       `json:"yongshen"`
	Elements     []ElementCount `json:"elements"`
	Relations    []Relation     `json:"relations"`
	ShenSha      []ShenSha      `json:"shensha"`
	DaYun        DaYunInfo      `json:"dayun"`
	LiuNian      []LiuNian      `json:"liunian"`
	Notes        []Note         `json:"notes"`
	DaYunNotes   []string       `json:"dayun_notes"`
	LiuNianNotes []string       `json:"liunian_notes"`
	SanMing      []string       `json:"sanming"`
	Meta         ChartMeta      `json:"meta"`
}

var timezoneAllowed = map[string]bool{"Asia/Shanghai": true, "UTC+08:00": true}

func (in Input) parseTime() (int, int, error) {
	parts := strings.Split(strings.TrimSpace(in.Time), ":")
	if len(parts) != 2 {
		return 0, 0, fmt.Errorf("时间格式应为 HH:MM")
	}
	h, err1 := strconv.Atoi(parts[0])
	m, err2 := strconv.Atoi(parts[1])
	if err1 != nil || err2 != nil || h < 0 || h > 23 || m < 0 || m > 59 {
		return 0, 0, fmt.Errorf("时间格式应为 HH:MM")
	}
	return h, m, nil
}

// LunarMonths 返回农历年各月天数，供前端闰月/月日联动。
type LunarMonthInfo struct {
	Month int `json:"month"`
	Days  int `json:"days"`
}

func LunarMonths(year int) (int, []LunarMonthInfo, error) {
	if year < 1900 || year > 2099 {
		return 0, nil, fmt.Errorf("农历年份超出支持范围")
	}
	ly := calendar.NewLunarYear(year)
	var out []LunarMonthInfo
	for item := ly.GetMonthsInYear().Front(); item != nil; item = item.Next() {
		month := item.Value.(*calendar.LunarMonth)
		out = append(out, LunarMonthInfo{Month: month.GetMonth(), Days: month.GetDayCount()})
	}
	return ly.GetLeapMonth(), out, nil
}

func (in Input) resolveBirth() (time.Time, string, string, error) {
	hour, minute, err := in.parseTime()
	if err != nil {
		return time.Time{}, "", "", err
	}
	switch in.Calendar {
	case "solar":
		dateValue := strings.TrimSpace(in.Date)
		layout := "2006-01-02"
		if dateValue == "" {
			return time.Time{}, "", "", fmt.Errorf("公历日期不能为空")
		}
		born, err := time.ParseInLocation(layout, dateValue, time.Local)
		if err != nil {
			return time.Time{}, "", "", fmt.Errorf("公历日期格式应为 YYYY-MM-DD")
		}
		t := time.Date(born.Year(), born.Month(), born.Day(), hour, minute, 0, 0, time.Local)
		original := fmt.Sprintf("%d年%d月%d日 %02d:%02d", t.Year(), int(t.Month()), t.Day(), hour, minute)
		return t, "公历", original, nil
	case "lunar":
		if in.LunarYear < 1900 || in.LunarYear > 2099 || in.LunarMonth < 1 || in.LunarMonth > 12 || in.LunarDay < 1 || in.LunarDay > 30 {
			return time.Time{}, "", "", fmt.Errorf("农历日期超出支持范围")
		}
		leap, months, err := LunarMonths(in.LunarYear)
		if err != nil {
			return time.Time{}, "", "", err
		}
		signed := in.LunarMonth
		if in.LunarLeap {
			signed = -signed
		}
		found := false
		for _, m := range months {
			if m.Month == signed {
				found = true
				if in.LunarDay > m.Days {
					return time.Time{}, "", "", fmt.Errorf("该农历月份只有 %d 天", m.Days)
				}
			}
		}
		if !found {
			if in.LunarLeap {
				return time.Time{}, "", "", fmt.Errorf("农历 %d 年没有闰%d月", in.LunarYear, in.LunarMonth)
			}
			return time.Time{}, "", "", fmt.Errorf("农历月份无效")
		}
		_ = leap
		lunar := calendar.NewLunar(in.LunarYear, signed, in.LunarDay, hour, minute, 0)
		solar := lunar.GetSolar()
		t := time.Date(solar.GetYear(), time.Month(solar.GetMonth()), solar.GetDay(),
			solar.GetHour(), solar.GetMinute(), solar.GetSecond(), 0, time.Local)
		leapLabel := ""
		if in.LunarLeap {
			leapLabel = "闰"
		}
		original := fmt.Sprintf("%d年%s%d月%d日 %02d:%02d", in.LunarYear, leapLabel, in.LunarMonth, in.LunarDay, hour, minute)
		return t, "农历", original, nil
	}
	return time.Time{}, "", "", fmt.Errorf("历法参数无效")
}

// EquationOfTime 均时差（分钟），NOAA/Spencer 日角近似。
func EquationOfTime(y int, m time.Month, d int) float64 {
	dayOfYear := time.Date(y, m, d, 0, 0, 0, 0, time.UTC).YearDay()
	days := 365.0
	if isLeap(y) {
		days = 366.0
	}
	gamma := 2 * math.Pi / days * float64(dayOfYear-1)
	return 229.18 * (0.000075 +
		0.001868*math.Cos(gamma) -
		0.032077*math.Sin(gamma) -
		0.014615*math.Cos(2*gamma) -
		0.040849*math.Sin(2*gamma))
}

func isLeap(y int) bool {
	return (y%4 == 0 && y%100 != 0) || y%400 == 0
}

// TrueSolarTime 真太阳时校正：平太阳时 + 经度时差 + 均时差。
func TrueSolarTime(y int, m time.Month, d, hour, minute int, longitude float64) (int, int, float64, float64, float64) {
	lonDiff := (longitude - 8*15.0) * 4.0
	eot := EquationOfTime(y, m, d)
	total := lonDiff + eot
	totalMinutes := int(math.Round(float64(hour*60+minute) + total))
	// 与 Python floor 整除保持同口径（负分钟跨日前收）。
	nh := int(math.Floor(float64(totalMinutes)/60)) % 24
	if nh < 0 {
		nh += 24
	}
	nm := totalMinutes - int(math.Floor(float64(totalMinutes)/60))*60
	return nh, nm, total, lonDiff, eot
}

func (in Input) validate() (float64, bool, error) {
	if in.Sex != 0 && in.Sex != 1 {
		return 0, false, fmt.Errorf("性别参数无效")
	}
	tz := in.Timezone
	if tz == "" {
		tz = "Asia/Shanghai"
	}
	if !timezoneAllowed[tz] {
		return 0, false, fmt.Errorf("当前客户端仅支持中国标准时间（UTC+8）")
	}
	var longitude float64
	hasLongitude := false
	raw := strings.TrimSpace(in.Longitude)
	if raw != "" {
		v, err := strconv.ParseFloat(raw, 64)
		if err != nil {
			return 0, false, fmt.Errorf("经度参数无效")
		}
		if v < -180 || v > 180 {
			return 0, false, fmt.Errorf("经度应在 -180 到 180 之间")
		}
		longitude, hasLongitude = v, true
	}
	if lat := strings.TrimSpace(in.Latitude); lat != "" {
		v, err := strconv.ParseFloat(lat, 64)
		if err != nil {
			return 0, false, fmt.Errorf("纬度参数无效")
		}
		if v < -90 || v > 90 {
			return 0, false, fmt.Errorf("纬度应在 -90 到 90 之间")
		}
	}
	// 未启用真太阳时不得把经度传给排盘引擎（项目硬约束）。
	if !in.UseTrueSolarTime {
		return 0, false, nil
	}
	if !hasLongitude {
		return 0, false, fmt.Errorf("启用真太阳时需要填写出生地经度")
	}
	return longitude, true, nil
}

// Build 依据入参排盘；返回的命盘可直接序列化给 UI 或历史存储。
func Build(in Input) (*Chart, error) {
	longitude, useTrue, err := in.validate()
	if err != nil {
		return nil, err
	}
	born, calendarLabel, original, err := in.resolveBirth()
	if err != nil {
		return nil, err
	}
	// 引擎本身可覆盖更早年份（仓库黄金样本含 19 世纪案例）；界面层再按产品口径限制 1900—2099。
	if born.Year() < 1800 || born.Year() > 2200 {
		return nil, fmt.Errorf("目前支持 1800—2200 年的出生日期")
	}

	chartDate := born
	var solarInfo *TrueSolar
	if useTrue {
		nh, nm, total, lonDiff, eot := TrueSolarTime(born.Year(), born.Month(), born.Day(), born.Hour(), born.Minute(), longitude)
		minutes := int(math.Round(float64(born.Hour()*60+born.Minute()) + total))
		chartDate = time.Date(born.Year(), born.Month(), born.Day(), 0, 0, 0, 0, time.Local).Add(time.Duration(minutes) * time.Minute)
		solarInfo = &TrueSolar{
			Original:    fmt.Sprintf("%02d:%02d", born.Hour(), born.Minute()),
			CorrectDate: chartDate.Format("2006-01-02"),
			Corrected:   fmt.Sprintf("%02d:%02d", nh, nm),
			TotalMinute: round1(total),
			LonDiff:     round1(lonDiff),
			Equation:    round1(eot),
		}
	}

	solar := calendar.NewSolar(chartDate.Year(), int(chartDate.Month()), chartDate.Day(), chartDate.Hour(), chartDate.Minute(), chartDate.Second())
	lunar := solar.GetLunar()
	ec := lunar.GetEightChar()

	pillars := map[string]string{
		"年": ec.GetYear(),
		"月": ec.GetMonth(),
		"日": ec.GetDay(),
		"时": ec.GetTime(),
	}
	// 晚子时（>=23 点）：日柱换次日，与上游行为一致。
	if chartDate.Hour() >= 23 {
		next := solar.Next(1, false).GetLunar()
		pillars["日"] = next.GetDayInGanZhi()
	}
	riGan := runeAt(pillars["日"], 0)

	monthIndexValue := ((ZhiIndex(runeAt(pillars["月"], 1))-2)%12+12)%12 + 1
	shensha := QueryShenSha(pillarGanZhi{
		Year: runeAt(pillars["年"], 0), Month: runeAt(pillars["月"], 0),
		Day: runeAt(pillars["日"], 0), Hour: runeAt(pillars["时"], 0),
		YearZhi: runeAt(pillars["年"], 1), MonthZhi: runeAt(pillars["月"], 1),
		DayZhi: runeAt(pillars["日"], 1), HourZhi: runeAt(pillars["时"], 1),
	}, monthIndexValue, NaYinJian(pillars["年"]))

	strength := StrengthAnalysis(pillars, riGan)
	geju := JudgeGeJu(pillars, riGan, strength)
	yongShen := PickYongShen(pillars, riGan, strength, runeAt(pillars["月"], 1))

	chart := &Chart{
		Input: ChartInput{
			Calendar:  calendarLabel,
			Original:  original,
			Sex:       map[bool]string{true: "男", false: "女"}[in.Sex == 1],
			Solar:     chartDate.Format("2006-01-02 15:04"),
			Longitude: nil,
			TrueSolar: useTrue,
		},
		Lunar:     lunar.String(),
		ShengXiao: lunar.GetYearShengXiao(),
		DayMaster: riGan,
		TrueSolar: solarInfo,
		TaiYuan:   ec.GetTaiYuan(),
		MingGong:  ec.GetMingGong(),
		ShenGong:  ec.GetShenGong(),
		Strength:  strength,
		GeJu:      geju,
		YongShen:  yongShen,
		ShenSha:   shensha,
		Meta: ChartMeta{
			Engine:    "guanxiang-desktop/go",
			LunarLib:  "lunar-go v1.4.7",
			Knowledge: "knowledge/*.json (内嵌)",
			Version:   "1.0.0",
		},
	}
	if useTrue {
		lon := longitude
		chart.Input.Longitude = &lon
		chart.Input.TimeBasis = "真太阳时（东八区 UTC+8）"
	} else {
		chart.Input.TimeBasis = "标准时间（东八区 UTC+8）"
	}

	for _, name := range positions {
		chart.Pillars = append(chart.Pillars, buildPillar(name, pillars[name], riGan))
	}

	// 五行结构计数：四干 + 四支本气，共 8 个字符。只作结构计数，不代表旺衰。
	counts := map[string]int{"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
	for _, name := range positions {
		counts[GanWuXing(runeAt(pillars[name], 0))]++
		counts[ZhiWuXing(runeAt(pillars[name], 1))]++
	}
	for _, element := range []string{"木", "火", "土", "金", "水"} {
		chart.Elements = append(chart.Elements, ElementCount{Name: element, Count: counts[element]})
	}

	chart.Relations = AnalyzeRelations(pillars)
	chart.Notes = FullAnalysis(pillars, riGan)

	// 月令断语《穷通宝鉴》与日主性格《滴天髓》，作为古籍参照前置。
	if title, body := YueLing(riGan, runeAt(pillars["月"], 1)); body != "" {
		chart.Notes = append([]Note{{Title: "月令断语·" + title, Body: body, Source: "《穷通宝鉴》古籍参照"}}, chart.Notes...)
	}
	if title, body := XingGe(riGan); body != "" {
		chart.Notes = append([]Note{{Title: title, Body: body, Source: "《滴天髓》古籍参照"}}, chart.Notes...)
	}

	// 大运
	yun := ec.GetYun(in.Sex)
	chart.DaYun = DaYunInfo{
		StartYears:  yun.GetStartYear(),
		StartMonths: yun.GetStartMonth(),
		StartDays:   yun.GetStartDay(),
		StartHours:  yun.GetStartHour(),
	}
	if start := yun.GetStartSolar(); start != nil {
		text := start.ToYmdHms()
		if len(text) >= 16 {
			text = text[:16]
		}
		chart.DaYun.JiaoYun = text
	}
	for _, dy := range yun.GetDaYun() {
		gz := dy.GetGanZhi()
		item := DaYun{
			Index: dy.GetIndex(), GanZhi: gz, StartYear: dy.GetStartYear(), EndYear: dy.GetEndYear(),
			Age: fmt.Sprintf("%d-%d", dy.GetStartAge(), dy.GetEndAge()),
		}
		if gz != "" {
			item.ShiShen = ShiShen(riGan, runeAt(gz, 0))
			item.ChangSheng = ShiErChangSheng(runeAt(gz, 0), runeAt(gz, 1))
			item.NaYin = NaYinJian(gz)
		}
		chart.DaYun.List = append(chart.DaYun.List, item)
	}

	// 流年：自当前年份起 5 年
	currentYear := time.Now().Year()
	for i := 0; i < 5; i++ {
		y := currentYear + i
		gz := JIAZI[((y-4)%60+60)%60]
		chart.LiuNian = append(chart.LiuNian, LiuNian{
			Year: y, GanZhi: gz,
			ShiShen:    ShiShen(riGan, runeAt(gz, 0)),
			ChangSheng: ShiErChangSheng(runeAt(gz, 0), runeAt(gz, 1)),
			Note:       LiuNianDuanYu(riGan, gz),
		})
	}

	for _, dy := range chart.DaYun.List {
		if dy.GanZhi == "" {
			continue
		}
		chart.DaYunNotes = append(chart.DaYunNotes, DaYunDuanYu(riGan, dy.GanZhi))
		chart.SanMing = append(chart.SanMing, DaYunZhengyi(riGan, dy.GanZhi))
	}
	for _, ln := range chart.LiuNian {
		chart.LiuNianNotes = append(chart.LiuNianNotes, ln.Note)
	}
	for _, ln := range chart.LiuNian {
		chart.SanMing = append(chart.SanMing, TaiSuiZhengyi(riGan, ln.GanZhi))
	}
	return chart, nil
}

func buildPillar(name, gz, riGan string) Pillar {
	gan, zhi := runeAt(gz, 0), runeAt(gz, 1)
	cang := ZhiCangGan(zhi)
	var shiShenCang []string
	for _, c := range cang {
		shiShenCang = append(shiShenCang, ShiShen(riGan, c))
	}
	return Pillar{
		Name: name, GanZhi: gz, Gan: gan, Zhi: zhi,
		GanWuXing: GanWuXing(gan), ZhiWuXing: ZhiWuXing(zhi),
		GanYinYang: GanYinYang(gan), ZhiYinYang: ZhiYinYang(zhi), ShengXiao: ZhiShengXiao(zhi),
		CangGan: cang, CangGanWuXing: ZhiCangGanWuXing(zhi),
		ShiShenGan: ShiShen(riGan, gan), ShiShenCangGan: shiShenCang,
		NaYin: NaYin(gz), NaYinJian: NaYinJian(gz),
		KongWang:   XunKong(gz),
		ChangSheng: ShiErChangSheng(gan, zhi),
		DiShi:      ShiErChangSheng(riGan, zhi),
	}
}
