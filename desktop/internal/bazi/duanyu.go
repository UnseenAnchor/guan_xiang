package bazi

// 古籍与运年断语：月令《穷通宝鉴》、日主性格《滴天髓》、大运流年《三命通会》。

func YueLing(riGan, monthZhi string) (string, string) {
	key := riGan + "日" + monthZhi + "月"
	body, ok := mustKB().yueling[key]
	if !ok {
		return key, ""
	}
	return key, body
}

func XingGe(riGan string) (string, string) {
	body, ok := mustKB().xingge[riGan]
	if !ok {
		return "", ""
	}
	prefix := []rune(body)
	if len(prefix) > 12 {
		prefix = prefix[:12]
	}
	return "日主性格·" + riGan + "日(" + string(prefix) + "…)", body
}

func DaYunDuanYu(riGan, gz string) string {
	gan, zhi := runeAt(gz, 0), runeAt(gz, 1)
	ss := ShiShen(riGan, gan)
	cs := ShiErChangSheng(gan, zhi)
	cang := ZhiCangGan(zhi)
	parts := []string{gz + "运: 天干" + ss + ", 坐" + cs}
	if len(cang) > 0 {
		parts = append(parts, "支藏"+cang[0]+"("+ShiShen(riGan, cang[0])+")")
	}
	parts = append(parts, "纳音"+NaYinJian(gz))
	key := ss + "月"
	body := ""
	if v, ok := mustKB().ssxx[key]; ok {
		body = v
	} else if v, ok := mustKB().ssxx[ss]; ok {
		body = v
	}
	if body != "" {
		parts = append(parts, truncateRunes(stripTags(body), 120))
	}
	if raw, ok := mustKB().swk[gan+zhi]; ok {
		tail := raw
		for i, r := range raw {
			if r == '#' {
				tail = raw[i+1:]
				break
			}
		}
		parts = append(parts, truncateRunes(stripTags(tail), 80))
	}
	return join(parts, " | ")
}

func LiuNianDuanYu(riGan, gz string) string {
	gan, zhi := runeAt(gz, 0), runeAt(gz, 1)
	return gz + "年: 十神" + ShiShen(riGan, gan) + ", 坐" + ShiErChangSheng(gan, zhi)
}

var changShengRule = map[string]string{
	"长生": "行长生，主有创建作新之事。",
	"临官": "行临官，主兴盛快乐，发福进财，生子骨肉之庆。",
	"帝旺": "行帝旺，主兴盛快乐，发福进财，生子骨肉之庆。",
	"衰":  "行至衰乡，多退败、破财、疾病等事。",
	"病":  "行至病乡，多退败、破财、疾病等事。",
	"死":  "行至死乡，主骨肉死丧，自身衰祸钝闷，百事蹇塞。",
	"绝":  "行至绝乡，主骨肉死丧，自身衰祸钝闷，百事蹇塞。",
	"墓":  "行至墓库成形之乡，百事得中，安康平易。",
	"胎":  "行至胎库成形之乡，百事得中，安康平易。",
	"养":  "行至胎库成形、冠带之乡，百事得中，安康平易。",
	"冠带": "行至冠带之乡，百事得中，安康平易。",
	"沐浴": "行至败运，主落魄懒惰，酒色昏迷。",
}

func DaYunZhengyi(riGan, gz string) string {
	cs := ShiErChangSheng(riGan, runeAt(gz, 1))
	return gz + "运: 运干" + ShiShen(riGan, runeAt(gz, 0)) + "，运支为日主十二长生之" + cs + "。" + changShengRule[cs]
}

func TaiSuiZhengyi(riGan, gz string) string {
	gan := runeAt(gz, 0)
	ss := ShiShen(riGan, gan)
	yearWuXing, dayWuXing := GanWuXing(gan), GanWuXing(riGan)
	relation := ""
	switch {
	case yearWuXing == dayWuXing:
		relation = "岁干与日干比和"
	case WuXingKe(yearWuXing, dayWuXing):
		relation = "岁伤日干（岁干克日干）——譬君治臣，虽有灾晦，不为大害，何则？上治其下，顺也，其情尚未尽绝。"
	case WuXingKe(dayWuXing, yearWuXing):
		relation = "日犯岁君（日干克岁干）——譬臣犯君，深为不利，下凌上，逆也，其凶决不能免。若五行有救，四柱有情，则灾可解。"
	case WuXingSheng(yearWuXing, dayWuXing):
		relation = "岁干生日干"
	default:
		relation = "日干生岁干"
	}
	return gz + "年: 岁干为日主之" + ss + "。" + relation
}

func truncateRunes(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n])
}
