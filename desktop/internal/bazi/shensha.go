package bazi

import "strings"

// 神煞查法（与 guan_xiang 的 bazi/shensha.py 逐条对齐）。

var tianYi = map[string]string{"甲": "丑未", "戊": "丑未", "庚": "丑未", "乙": "子申", "己": "子申",
	"丙": "亥酉", "丁": "亥酉", "壬": "卯巳", "癸": "卯巳", "辛": "午寅"}

var wenChang = map[string]string{"甲": "巳", "乙": "午", "丙": "申", "戊": "申", "丁": "酉",
	"己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"}

var ganLu = map[string]string{"甲": "寅", "乙": "卯", "丙": "巳", "戊": "巳", "丁": "午",
	"己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}

var yangRen = map[string]string{"甲": "卯", "乙": "辰", "丙": "午", "戊": "午", "丁": "未",
	"己": "未", "庚": "酉", "辛": "戌", "壬": "子", "癸": "丑"}

var taiJi = map[string]string{"甲": "子午", "戊": "子午", "乙": "丑未", "己": "丑未",
	"丙": "寅申", "丁": "寅申", "壬": "卯酉", "癸": "卯酉", "庚": "辰戌", "辛": "辰戌"}

var guoYin = map[string]string{"甲": "戌", "乙": "亥", "丙": "丑", "戊": "丑", "丁": "寅",
	"己": "寅", "庚": "辰", "辛": "巳", "壬": "未", "癸": "申"}

var jinYu = map[string]string{"甲": "辰", "乙": "巳", "丙": "未", "戊": "未", "丁": "申",
	"己": "申", "庚": "戌", "辛": "亥", "壬": "丑", "癸": "寅"}

var liuXia = map[string]string{"甲": "酉", "乙": "戌", "丙": "未", "戊": "未", "丁": "午",
	"己": "午", "庚": "辰", "辛": "卯", "壬": "亥", "癸": "寅"}

var hongYan = map[string]string{"甲": "午", "乙": "申", "丙": "寅", "丁": "未", "戊": "辰",
	"己": "辰", "庚": "戌", "辛": "酉", "壬": "子", "癸": "申"}

var tianDe = map[string]string{"子": "巳", "丑": "庚", "寅": "丁", "卯": "申", "辰": "壬",
	"巳": "辛", "午": "亥", "未": "甲", "申": "癸", "酉": "寅", "戌": "丙", "亥": "乙"}

var yueDe = map[string]string{"寅午戌": "丙", "申子辰": "壬", "亥卯未": "甲", "巳酉丑": "庚"}

var sanHeGroups = [][3]string{{"申", "子", "辰"}, {"寅", "午", "戌"}, {"巳", "酉", "丑"}, {"亥", "卯", "未"}}

func sanHeGroup(z string) (string, bool) {
	for _, g := range sanHeGroups {
		if g[0] == z || g[1] == z || g[2] == z {
			return g[0] + g[1] + g[2], true
		}
	}
	return "", false
}

var sanHeStars = map[string]map[string]string{
	"驿马": {"申子辰": "寅", "寅午戌": "申", "巳酉丑": "亥", "亥卯未": "巳"},
	"桃花": {"申子辰": "酉", "寅午戌": "卯", "巳酉丑": "午", "亥卯未": "子"},
	"华盖": {"申子辰": "辰", "寅午戌": "戌", "巳酉丑": "丑", "亥卯未": "未"},
	"将星": {"申子辰": "子", "寅午戌": "午", "巳酉丑": "酉", "亥卯未": "卯"},
	"劫煞": {"申子辰": "巳", "寅午戌": "亥", "巳酉丑": "寅", "亥卯未": "申"},
	"亡神": {"申子辰": "亥", "寅午戌": "巳", "巳酉丑": "申", "亥卯未": "寅"},
	"灾煞": {"申子辰": "午", "寅午戌": "子", "巳酉丑": "卯", "亥卯未": "酉"},
}

func SanHeStar(z, kind string) string {
	g, ok := sanHeGroup(z)
	if !ok {
		return ""
	}
	return sanHeStars[kind][g]
}

func TianYiStar(monthZhi string) string {
	return ZHI[(ZhiIndex(monthZhi)+11)%12]
}

func hongLuan(yearZhi string) string { return ZHI[(ZhiIndex(yearZhi)+3)%12] }
func tianXi(yearZhi string) string   { return ZHI[(ZhiIndex(yearZhi)+9)%12] }

var guChen = map[string]string{"亥子丑": "寅", "寅卯辰": "巳", "巳午未": "申", "申酉戌": "亥"}
var guaSu = map[string]string{"亥子丑": "戌", "寅卯辰": "丑", "巳午未": "辰", "申酉戌": "未"}

func jiChuGroup(z string) string {
	for k := range guChen {
		if strings.Contains(k, z) {
			return k
		}
	}
	return ""
}

var yuanChen = map[string]string{"子": "未", "丑": "辰", "寅": "酉", "卯": "戌", "辰": "亥",
	"巳": "午", "午": "丑", "未": "申", "申": "卯", "酉": "戌", "戌": "巳", "亥": "子"}

func sangMen(yearZhi string) string { return ZHI[(ZhiIndex(yearZhi)+2)%12] }
func diaoKe(yearZhi string) string  { return ZHI[(ZhiIndex(yearZhi)+10)%12] }
func piMa(yearZhi string) string    { return ZHI[(ZhiIndex(yearZhi)+9)%12] }

func gouJiao(yearZhi string) string {
	taoHua := SanHeStar(yearZhi, "桃花")
	if taoHua == "" {
		return ""
	}
	return ZHI[(ZhiIndex(taoHua)+6)%12]
}

func feiRen(riGan string) string {
	yr := yangRen[riGan]
	if yr == "" {
		return ""
	}
	return ZHI[(ZhiIndex(yr)+6)%12]
}

var (
	kuiGang    = set("庚辰", "庚戌", "壬辰", "戊戌")
	guLuan     = set("甲寅", "乙巳", "丙午", "丁巳", "戊午", "戊申", "辛亥", "壬子")
	yinChaYang = set("丙子", "丙午", "丁丑", "丁未", "戊寅", "戊申", "辛卯", "辛酉", "壬辰", "壬戌", "癸巳", "癸亥")
	baZhuan    = set("甲寅", "乙卯", "丁未", "戊申", "己未", "庚申", "辛酉", "癸丑")
	jiuChou    = set("壬子", "壬午", "戊子", "戊午", "己卯", "己酉", "辛卯", "辛酉", "乙卯", "乙酉")
	shiLing    = set("甲辰", "乙亥", "丙辰", "丁酉", "戊午", "庚戌", "庚寅", "辛亥", "壬寅", "癸未")
	shiE       = set("甲辰", "乙巳", "壬申", "丙申", "丁亥", "庚辰", "戊戌", "癸亥", "辛巳", "己丑")
	jinShen    = set("乙丑", "己巳", "癸酉")
	liuXiu     = set("丙午", "丁未", "戊子", "戊午", "己丑", "己未", "辛巳", "辛丑", "壬辰", "壬戌", "癸卯", "癸丑")
)

var siFei = map[string][]string{"春": {"庚申", "辛酉"}, "夏": {"壬子", "癸亥"}, "秋": {"甲寅", "乙卯"}, "冬": {"丙午", "丁巳"}}
var tianZhuan = map[string]string{"春": "乙卯", "夏": "丙午", "秋": "辛酉", "冬": "壬子"}
var diZhuan = map[string]string{"春": "辛卯", "夏": "戊午", "秋": "癸酉", "冬": "丙子"}
var tianShe = map[string]string{"春": "戊寅", "夏": "甲午", "秋": "戊申", "冬": "甲子"}

func set(items ...string) map[string]bool {
	m := make(map[string]bool, len(items))
	for _, item := range items {
		m[item] = true
	}
	return m
}

// Season 节气月(1-12) -> 季节。
func Season(month int) string {
	switch {
	case month >= 1 && month <= 3:
		return "春"
	case month >= 4 && month <= 6:
		return "夏"
	case month >= 7 && month <= 9:
		return "秋"
	default:
		return "冬"
	}
}

func tongZi(monthSeason, yearNaYin, riZhi, shiZhi, riGan string) []string {
	var hits []string
	if monthSeason == "春" || monthSeason == "秋" {
		if riZhi == "寅" || riZhi == "子" || shiZhi == "寅" || shiZhi == "子" {
			hits = append(hits, "春秋生人, 日支或时支见寅/子")
		}
	} else if riZhi == "卯" || riZhi == "未" || riZhi == "辰" || shiZhi == "卯" || shiZhi == "未" || shiZhi == "辰" {
		hits = append(hits, "夏冬生人, 日支或时支见卯/未/辰")
	}
	if yearNaYin == "金" || yearNaYin == "木" {
		if riZhi == "午" || riZhi == "卯" || shiZhi == "午" || shiZhi == "卯" {
			hits = append(hits, "年纳音金/木, 日支或时支见午/卯")
		}
	}
	if yearNaYin == "水" || yearNaYin == "火" {
		if riZhi == "酉" || riZhi == "戌" || shiZhi == "酉" || shiZhi == "戌" {
			hits = append(hits, "年纳音水/火, 日支或时支见酉/戌")
		}
	}
	if yearNaYin == "土" {
		for _, z := range []string{"子", "丑", "巳"} {
			if riZhi == z || shiZhi == z {
				hits = append(hits, "年纳音土, 日支或时支见子/丑/巳")
				break
			}
		}
	}
	return hits
}

// ShenSha 单条神煞记录。
type ShenSha struct {
	Name  string `json:"name"`
	Where string `json:"where"`
	Note  string `json:"note"`
}

type pillarGanZhi struct {
	Year, Month, Day, Hour             string
	YearZhi, MonthZhi, DayZhi, HourZhi string
}

func QueryShenSha(p pillarGanZhi, monthSeason int, yearNaYin string) []ShenSha {
	out := make([]ShenSha, 0, 12)
	positions := []struct {
		name string
		zhi  string
		gan  string
	}{
		{"年", p.YearZhi, p.Year},
		{"月", p.MonthZhi, p.Month},
		{"日", p.DayZhi, p.Day},
		{"时", p.HourZhi, p.Hour},
	}
	ganCombined := p.Year + p.Month + p.Day + p.Hour

	add := func(name, where, note string) {
		out = append(out, ShenSha{Name: name, Where: where, Note: note})
	}
	findZhi := func(target string) string {
		for _, pos := range positions {
			if pos.zhi == target {
				return pos.name
			}
		}
		return ""
	}
	// 上游口径：干禄/羊刃/飞刃/流霞/红艳煞命中多柱时逐柱各记一条；
	// 其余单支神煞（红鸾/天喜/孤辰/寡宿/天医/元辰/丧门/吊客/披麻/勾绞煞）只记首柱。
	scanZhiAll := func(name, target, note string) {
		if target == "" {
			return
		}
		for _, pos := range positions {
			if pos.zhi == target {
				add(name, pos.name, note)
			}
		}
	}
	scanZhi := func(name, target, note string) {
		if target == "" {
			return
		}
		for _, pos := range positions {
			if pos.zhi == target {
				add(name, pos.name, note)
				return
			}
		}
	}

	riGan := p.Day

	// 上游口径说明：现役 bazi/shensha.py 中「天乙贵人 / 文昌贵人 / 太极贵人 / 国印贵人 / 金舆」
	// 五类查法把柱名（"日"/"年"）当作天干传入查表，条件恒为空，实际从未生效。
	// 桌面端与现役网页保持同源同结果，因此同样不产出这五类，避免两个界面数据打架。
	// 查法表仍保留在下方常量中，待上游修复后同步启用。
	_ = tianYi
	_ = wenChang
	_ = taiJi
	_ = guoYin
	_ = jinYu

	scanZhiAll("干禄", ganLu[riGan], "")
	scanZhiAll("羊刃", yangRen[riGan], "")
	scanZhiAll("飞刃", feiRen(riGan), "")
	scanZhiAll("流霞", liuXia[riGan], "")
	scanZhiAll("红艳煞", hongYan[riGan], "")

	if g := tianDe[p.MonthZhi]; g != "" && strings.Contains(ganCombined, g) {
		add("天德贵人", "月", p.MonthZhi+"月见"+g)
	}
	for grp, g := range yueDe {
		if strings.Contains(grp, p.MonthZhi) && strings.Contains(ganCombined, g) {
			add("月德贵人", "月", p.MonthZhi+"月见"+g)
		}
	}
	for _, pos := range positions {
		if pos.name != "年" && pos.name != "日" {
			continue
		}
		for _, kind := range []string{"驿马", "桃花", "华盖", "将星", "劫煞", "亡神", "灾煞"} {
			target := SanHeStar(pos.zhi, kind)
			if target == "" {
				continue
			}
			if where := findZhi(target); where != "" {
				add(kind, where, pos.name+"支"+pos.zhi+"见"+target)
			}
		}
	}
	scanZhi("红鸾", hongLuan(p.YearZhi), "")
	scanZhi("天喜", tianXi(p.YearZhi), "")
	if grp := jiChuGroup(p.YearZhi); grp != "" {
		scanZhi("孤辰", guChen[grp], "")
		scanZhi("寡宿", guaSu[grp], "")
	}
	scanZhi("天医", TianYiStar(p.MonthZhi), "")
	scanZhi("元辰", yuanChen[p.YearZhi], "")
	scanZhi("丧门", sangMen(p.YearZhi), "")
	scanZhi("吊客", diaoKe(p.YearZhi), "")
	scanZhi("披麻", piMa(p.YearZhi), "")
	scanZhi("勾绞煞", gouJiao(p.YearZhi), "")

	triples := []string{"甲乙丙", "乙丙丁", "丙丁戊", "丁戊己", "戊己庚", "己庚辛", "庚辛壬", "辛壬癸", "壬癸甲", "癸甲乙"}
	runes := []rune(ganCombined)
	for i := 0; i+3 <= len(runes); i++ {
		tri := string(runes[i : i+3])
		matched := false
		for _, t := range triples {
			if t == tri {
				matched = true
				break
			}
		}
		if matched {
			label := "月日时"
			if i < 2 {
				label = string([]rune("年月日")[i : i+3])
			}
			add("三奇贵人", label, tri)
			break
		}
	}

	for _, pair := range []struct{ gz, label string }{
		{p.Day + p.DayZhi, "日柱"},
		{p.Year + p.YearZhi, "年柱"},
	} {
		for _, kong := range XunKong(pair.gz) {
			for _, pos := range positions {
				if pos.zhi == kong {
					add("空亡", pos.name, pair.label+pair.gz+"空"+kong)
				}
			}
		}
	}

	riZhu := p.Day + p.DayZhi
	seasonName := Season(monthSeason)
	// 上游对日柱固定神煞逐条独立判定，同一日柱可同时命中多条。
	for _, rule := range []struct {
		name string
		set  map[string]bool
	}{
		{"魁罡", kuiGang}, {"孤鸾煞", guLuan}, {"阴差阳错", yinChaYang}, {"八专", baZhuan},
		{"九丑", jiuChou}, {"十灵日", shiLing}, {"十恶大败", shiE}, {"六秀日", liuXiu},
	} {
		if rule.set[riZhu] {
			add(rule.name, "日", riZhu)
		}
	}
	for _, item := range siFei[seasonName] {
		if item == riZhu {
			add("四废日", "日", riZhu)
			break
		}
	}
	if riZhu == tianZhuan[seasonName] {
		add("天转", "日", riZhu)
	}
	if riZhu == diZhuan[seasonName] {
		add("地转", "日", riZhu)
	}
	if riZhu == tianShe[seasonName] {
		add("天赦日", "日", riZhu)
	}
	if jinShen[riZhu] {
		add("金神", "日", riZhu)
	}
	if hourZhu := p.Hour + p.HourZhi; jinShen[hourZhu] {
		add("金神", "时", hourZhu)
	}
	for _, rule := range tongZi(seasonName, yearNaYin, p.DayZhi, p.HourZhi, p.Day) {
		add("童子煞", "日/时", rule)
	}
	return out
}
