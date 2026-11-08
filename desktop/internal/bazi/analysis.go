package bazi

import "strings"

// 断语分析（与 bazi/analysis.py 对齐，数据来自内嵌 serjson.json 的 ssxx/swk）。

type Note struct {
	Title  string `json:"title"`
	Body   string `json:"body"`
	Source string `json:"source"`
}

func shiShenDuanYu(riGan, gan, pillar string) (string, string) {
	ss := ShiShen(riGan, gan)
	if body, ok := mustKB().ssxx[ss+pillar]; ok {
		return ss, stripTags(body)
	}
	return ss, ""
}

func riZuoNotes(riGan, riZhi string) []Note {
	cang := ZhiCangGan(riZhi)
	if len(cang) == 0 {
		return nil
	}
	ss := ShiShen(riGan, cang[0])
	var out []Note
	if body, ok := mustKB().ssxx[ss+"日坐"]; ok {
		out = append(out, Note{Title: "日坐" + ss, Body: stripTags(body), Source: "十神断语"})
	}
	gz := riGan + riZhi
	if raw, ok := mustKB().swk[gz]; ok {
		state, body := "", raw
		if idx := strings.Index(raw, "#"); idx >= 0 {
			state, body = raw[:idx], raw[idx+1:]
		}
		out = append(out, Note{Title: gz + "日(" + state + ")", Body: body, Source: "日柱坐支论"})
	}
	return out
}

// FullAnalysis 返回十神总论、各柱透干、日坐月坐与十神坐十神断语。
func FullAnalysis(pillars map[string]string, riGan string) []Note {
	out := make([]Note, 0, 8)
	if body, ok := mustKB().ssxx[riGan]; ok {
		out = append(out, Note{Title: "日主" + riGan + "十神总论", Body: stripTags(body), Source: "十神断语"})
	}
	for _, pillar := range []string{"年", "月", "时"} {
		ss, body := shiShenDuanYu(riGan, runeAt(pillars[pillar], 0), pillar)
		if body != "" {
			out = append(out, Note{Title: pillar + "柱透" + ss, Body: body, Source: "十神断语"})
		}
	}
	out = append(out, riZuoNotes(riGan, runeAt(pillars["日"], 1))...)

	monthSS := ShiShen(riGan, ZhiCangGan(runeAt(pillars["月"], 1))[0])
	if body, ok := mustKB().ssxx[monthSS+"月坐"]; ok {
		out = append(out, Note{Title: "月坐" + monthSS, Body: stripTags(body), Source: "十神断语"})
	}
	for _, pillar := range positions {
		gz := pillars[pillar]
		ssGan := ShiShen(riGan, runeAt(gz, 0))
		for _, cang := range ZhiCangGan(runeAt(gz, 1)) {
			key := ssGan + "坐" + ShiShen(riGan, cang)
			if body, ok := mustKB().ssxx[key]; ok {
				out = append(out, Note{Title: key, Body: stripTags(body), Source: "十神断语"})
			}
		}
	}
	return out
}
