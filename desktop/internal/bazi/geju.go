package bazi

// 格局喜忌（与 bazi/geju.py 对齐）：五行旺衰量化 / 身强弱 / 月令取格 / 沈氏用神 / 调候用神。

var wangXing = map[string]map[string]string{
	"木": {"水": "相", "木": "旺", "火": "休", "土": "囚", "金": "死"},
	"火": {"木": "相", "火": "旺", "土": "休", "金": "囚", "水": "死"},
	"土": {"火": "相", "土": "旺", "金": "休", "水": "囚", "木": "死"},
	"金": {"土": "相", "金": "旺", "水": "休", "木": "囚", "火": "死"},
	"水": {"金": "相", "水": "旺", "木": "休", "火": "囚", "土": "死"},
}

var stateWeight = map[string]float64{"旺": 2, "相": 1, "休": 0, "囚": -1, "死": -2}

var changShengStrength = map[string]float64{
	"长生": 1, "沐浴": .6, "冠带": .8, "临官": 1, "帝旺": 1,
	"衰": .4, "病": .2, "死": 0, "墓": .8, "绝": 0, "胎": .3, "养": .5,
}

var luBranch = map[string]string{"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
	"己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}

var renBranch = map[string]string{"甲": "卯", "乙": "寅", "丙": "午", "丁": "巳", "戊": "午",
	"己": "巳", "庚": "酉", "辛": "申", "壬": "子", "癸": "亥"}

// 调候用神表《穷通宝鉴》徐乐吾评注版：十干 x 12 月（寅卯辰巳午未申酉戌亥子丑）。
var tiaoHou = map[string][]string{
	"甲": {"丙癸", "庚丙丁", "庚丁壬", "癸庚丁", "癸庚丁", "癸庚丁", "庚丁壬", "庚丁丙", "庚甲丁壬癸", "庚丁丙戊", "丁庚丙", "庚丁丙"},
	"乙": {"丙癸", "丙癸", "癸丙戊", "癸", "癸丙", "癸丙", "丙癸己", "癸丙丁", "癸辛", "丙戊", "丙", "丙"},
	"丙": {"壬庚", "壬己", "壬甲", "壬癸庚", "壬庚", "壬庚癸", "壬戊", "壬癸", "甲壬", "甲戊庚壬", "壬戊己", "壬甲"},
	"丁": {"甲庚", "甲庚", "甲庚", "甲庚", "壬庚癸", "甲壬庚", "甲庚丙戊", "甲庚丙戊", "甲庚戊", "甲庚", "甲庚", "甲庚"},
	"戊": {"丙甲癸", "丙甲癸", "甲丙癸", "甲丙癸", "壬甲丙", "癸丙甲", "丙癸甲", "丙癸", "甲丙癸", "甲丙", "丙甲", "丙甲"},
	"己": {"丙庚甲", "甲癸丙", "丙癸甲", "癸丙", "癸丙", "癸丙", "丙癸", "丙癸", "甲丙癸", "丙甲戊", "丙甲戊", "丙甲戊"},
	"庚": {"戊甲壬丙丁", "丁甲庚丙", "甲丁壬癸", "壬戊丙丁", "壬癸", "丁甲", "丁甲", "丁甲", "甲壬", "丁丙", "丁甲丙", "丙丁甲"},
	"辛": {"己壬庚", "壬甲", "壬甲", "壬甲癸", "壬己癸", "壬庚甲", "壬甲戊", "壬甲", "壬甲", "壬", "丙戊壬", "壬戊己"},
	"壬": {"庚丙戊", "戊辛庚", "甲庚", "壬辛庚癸", "癸庚辛", "辛甲", "戊丁", "甲庚", "甲丙", "戊丙庚", "戊丙", "丙丁甲"},
	"癸": {"辛丙", "庚辛", "丙辛甲", "辛", "庚辛壬癸", "庚辛壬癸", "丁", "辛丙", "辛甲壬癸", "庚辛戊丁", "丙辛", "丙丁"},
}

var monthIndex = map[string]int{"寅": 0, "卯": 1, "辰": 2, "巳": 3, "午": 4, "未": 5,
	"申": 6, "酉": 7, "戌": 8, "亥": 9, "子": 10, "丑": 11}

type Strength struct {
	Score      float64            `json:"score"`
	Level      string             `json:"level"`
	MonthState string             `json:"month_state"`
	Detail     []string           `json:"detail"`
	Parts      map[string]float64 `json:"parts"`
}

func StrengthAnalysis(pillars map[string]string, riGan string) Strength {
	riWuXing := GanWuXing(riGan)
	yearZhi, monthZhi, dayZhi, hourZhi := runeAt(pillars["年"], 1), runeAt(pillars["月"], 1), runeAt(pillars["日"], 1), runeAt(pillars["时"], 1)
	yearGan, monthGan, hourGan := runeAt(pillars["年"], 0), runeAt(pillars["月"], 0), runeAt(pillars["时"], 0)

	monthState := wangXing[riWuXing][ZhiWuXing(monthZhi)]
	score := stateWeight[monthState]
	detail := []string{"月令" + ZhiWuXing(monthZhi) + "(" + monthZhi + "): " + monthState + " " + signed(stateWeight[monthState])}

	rootScore := 0.0
	var roots []string
	for _, item := range []struct{ name, zhi string }{{"年", yearZhi}, {"月", monthZhi}, {"日", dayZhi}, {"时", hourZhi}} {
		cs := ShiErChangSheng(riGan, item.zhi)
		hidden := ZhiCangGanWuXing(item.zhi)
		contains := false
		for _, h := range hidden {
			if h == riWuXing {
				contains = true
			}
		}
		if !contains {
			continue
		}
		w := changShengStrength[cs]
		if len(hidden) > 0 && hidden[0] == riWuXing && w < 1.0 {
			w = 1.0
		}
		if w > 0 {
			rootScore += w
			roots = append(roots, item.zhi+"("+cs+" "+signed(w)+")")
		}
	}
	score += rootScore
	if len(roots) > 0 {
		detail = append(detail, "地支根: "+join(roots, ", ")+" ("+signed(rootScore)+")")
	} else {
		detail = append(detail, "地支根: 无根 ("+signed(rootScore)+")")
	}

	shiScore := 0.0
	var shiParts []string
	for _, item := range []struct{ name, gan string }{{"年", yearGan}, {"月", monthGan}, {"时", hourGan}} {
		if item.gan == riGan {
			shiScore += 1
			shiParts = append(shiParts, item.name+item.gan+"比肩")
		} else if GanWuXing(item.gan) == riWuXing {
			shiScore += .5
			shiParts = append(shiParts, item.name+item.gan+"同气")
		}
	}
	score += shiScore
	if len(shiParts) > 0 {
		detail = append(detail, "天干助身: "+join(shiParts, ", ")+" ("+signed(shiScore)+")")
	} else {
		detail = append(detail, "天干助身: 无助 ("+signed(shiScore)+")")
	}

	level := "身弱"
	switch {
	case score >= 4:
		level = "身强"
	case score >= 3:
		level = "偏强"
	case score >= 2:
		level = "中和"
	case score >= .5:
		level = "偏弱"
	}
	return Strength{
		Score: round1(score), Level: level, MonthState: monthState, Detail: detail,
		Parts: map[string]float64{"得令": stateWeight[monthState], "得地": round1(rootScore), "得势": round1(shiScore)},
	}
}

type GeJu struct {
	Name string `json:"name"`
	Kind string `json:"kind"`
	Note string `json:"note"`
}

func JudgeGeJu(pillars map[string]string, riGan string, strength Strength) GeJu {
	monthZhi := runeAt(pillars["月"], 1)
	yearGan, monthGan, hourGan := runeAt(pillars["年"], 0), runeAt(pillars["月"], 0), runeAt(pillars["时"], 0)
	benQi := ZhiCangGan(monthZhi)[0]
	benQiSS := ShiShen(riGan, benQi)

	count := map[string]int{}
	for _, g := range []string{yearGan, monthGan, riGan, hourGan} {
		count[GanWuXing(g)]++
	}
	for _, p := range positions {
		count[ZhiWuXing(runeAt(pillars[p], 1))]++
	}
	total := 0
	maxKey, maxCount := "", 0
	for k, v := range count {
		total += v
		if v > maxCount {
			maxKey, maxCount = k, v
		}
	}
	ratio := float64(maxCount) / float64(total)

	if (strength.Level == "身弱" || strength.Level == "偏弱") && ratio >= .75 {
		if maxKey == GanWuXing(riGan) {
			return GeJu{Name: "专旺格", Kind: "外格", Note: maxKey + "局成气"}
		}
		return GeJu{Name: "从格", Kind: "外格", Note: "日主弱极, 全局" + maxKey + "旺, 从" + maxKey}
	}
	if monthZhi == luBranch[riGan] {
		return GeJu{Name: "建禄格", Kind: "建禄格", Note: "月支" + monthZhi + "为日主之禄"}
	}
	if monthZhi == renBranch[riGan] {
		return GeJu{Name: "羊刃格", Kind: "羊刃格", Note: "月支" + monthZhi + "为日主之刃"}
	}
	for _, item := range []struct{ gan, label string }{{yearGan, "年"}, {monthGan, "月"}, {hourGan, "时"}} {
		if item.gan == benQi {
			return GeJu{Name: benQiSS + "格", Kind: benQiSS + "格", Note: "月令" + monthZhi + "本气" + benQi + "透于" + item.label}
		}
	}
	return GeJu{Name: benQiSS + "格", Kind: benQiSS + "格", Note: "月令" + monthZhi + "本气" + benQi + "不透, 按本气取格"}
}

type YongShen struct {
	Use      []string `json:"use"`
	Avoid    []string `json:"avoid"`
	Disease  []string `json:"disease"`
	Medicine []string `json:"medicine"`
	TiaoHou  []string `json:"tiaohou"`
	Method   string   `json:"method"`
	Bridge   string   `json:"bridge"`
}

func PickYongShen(pillars map[string]string, riGan string, strength Strength, monthZhi string) YongShen {
	riWuXing := GanWuXing(riGan)
	sheng := wuXingSheng
	ke := wuXingKe
	keWo := KeWo(riWuXing)

	var use, avoid []string
	method := ""
	switch strength.Level {
	case "身强", "偏强":
		use = []string{ke[riWuXing], sheng[riWuXing], keWo}
		avoid = []string{riWuXing, sheng[keWo]}
		method = "扶抑(身强用克泄耗)"
	case "身弱", "偏弱":
		use = []string{riWuXing, sheng[keWo]}
		avoid = []string{ke[riWuXing], sheng[riWuXing]}
		method = "扶抑(身弱用印比)"
	default:
		use = []string{riWuXing}
		method = "中和(酌情扶抑)"
	}

	var disease, medicine []string
	if len(avoid) > 0 {
		disease = avoid[:1]
		if w := KeWo(disease[0]); w != "" {
			medicine = []string{w}
		}
	}

	th := tiaoHou[riGan][monthIndex[monthZhi]]

	bridge := ""
	monthWuXing := ZhiWuXing(monthZhi)
	if ke[riWuXing] == monthWuXing || ke[monthWuXing] == riWuXing {
		if ke[monthWuXing] == riWuXing {
			bridge = sheng[monthWuXing]
		} else {
			bridge = sheng[riWuXing]
		}
	}

	thGan := make([]string, 0, len([]rune(th)))
	for _, r := range th {
		thGan = append(thGan, string(r))
	}
	thWuXing := make([]string, 0, len(thGan))
	for _, g := range thGan {
		thWuXing = append(thWuXing, GanWuXing(g))
	}
	return YongShen{Use: use, Avoid: avoid, Disease: disease, Medicine: medicine,
		TiaoHou: thWuXing, Method: method, Bridge: bridge}
}
