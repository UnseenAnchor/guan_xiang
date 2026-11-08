package bazi

import (
	"regexp"
	"strings"
)

// 干支基础层：数据来自内嵌 ny.json，代码内只保留结构常量与查表逻辑。

var GAN = []string{"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}
var ZHI = []string{"子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"}
var JIAZI = buildJiazi()

var fontTagPattern = regexp.MustCompile(`<@font\|[^>]*?/@>`)

func buildJiazi() []string {
	out := make([]string, 60)
	for i := 0; i < 60; i++ {
		out[i] = GAN[i%10] + ZHI[i%12]
	}
	return out
}

func GanIndex(g string) int {
	for i, v := range GAN {
		if v == g {
			return i
		}
	}
	return -1
}

func ZhiIndex(z string) int {
	for i, v := range ZHI {
		if v == z {
			return i
		}
	}
	return -1
}

func mustKB() *knowledge {
	k, err := Knowledge()
	if err != nil {
		panic(err)
	}
	return k
}

func GanWuXing(g string) string  { return mustKB().ny.Gan[g].WuXing }
func GanYinYang(g string) string { return mustKB().ny.Gan[g].YinYang }
func ZhiWuXing(z string) string  { return mustKB().ny.Zhi[z].WuXing }
func ZhiYinYang(z string) string { return mustKB().ny.Zhi[z].YinYang }
func ZhiShengXiao(z string) string {
	return mustKB().ny.Zhi[z].ShengXiao
}

// ZhiCangGan 返回地支藏干（本气 -> 余气）。
func ZhiCangGan(z string) []string {
	raw := mustKB().ny.Zhi[z].GanStr
	if raw == "" {
		return nil
	}
	return strings.Split(raw, ",")
}

func ZhiCangGanWuXing(z string) []string {
	raw := mustKB().ny.Zhi[z].WuXingStr
	if raw == "" {
		return nil
	}
	return strings.Split(raw, ",")
}

// NaYin 纳音，修正上游两处异体字。
func NaYin(gz string) string {
	v := mustKB().ny.NaYin[gz].WuXing
	switch v {
	case "白腊金":
		return "白蜡金"
	case "桑拓木":
		return "桑柘木"
	}
	return v
}

func NaYinJian(gz string) string { return mustKB().ny.NaYin[gz].WuXingJian }

func XunKong(gz string) []string {
	raw := mustKB().ny.NaYin[gz].KongWang
	if raw == "" {
		return nil
	}
	return strings.Split(raw, ",")
}

// ShiShen 日干对其他天干 -> 十神。
func ShiShen(riGan, otherGan string) string { return mustKB().ny.ShiShen[riGan+otherGan] }

// ShiErChangSheng 某天干在某地支的十二长生状态。
func ShiErChangSheng(g, z string) string { return mustKB().ny.ChangSheng[g+z] }

var heGan = map[string]string{"甲": "己", "乙": "庚", "丙": "辛", "丁": "壬", "戊": "癸",
	"己": "甲", "庚": "乙", "辛": "丙", "壬": "丁", "癸": "戊"}

var heZhi = map[string]string{"子": "丑", "寅": "亥", "卯": "戌", "辰": "酉", "巳": "申",
	"午": "未", "丑": "子", "亥": "寅", "戌": "卯", "酉": "辰", "申": "巳", "未": "午"}

var chongZhi = map[string]string{"子": "午", "丑": "未", "寅": "申", "卯": "酉", "辰": "戌",
	"巳": "亥", "午": "子", "未": "丑", "申": "寅", "酉": "卯", "戌": "辰", "亥": "巳"}

var xingZhi = map[string]string{"子": "卯", "卯": "子", "寅": "巳", "巳": "申", "申": "寅",
	"丑": "戌", "戌": "未", "未": "丑", "辰": "辰", "午": "午", "酉": "酉", "亥": "亥"}

var haiZhi = map[string]string{"子": "未", "丑": "午", "寅": "巳", "卯": "辰",
	"申": "亥", "酉": "戌"}

var poZhi = map[string]string{"子": "酉", "酉": "子", "丑": "辰", "辰": "丑", "寅": "亥",
	"亥": "寅", "卯": "午", "午": "卯", "巳": "申", "申": "巳", "未": "戌", "戌": "未"}

func TianGanHe(g string) string  { return heGan[g] }
func DiZhiHe(z string) string    { return heZhi[z] }
func DiZhiChong(z string) string { return chongZhi[z] }
func DiZhiXing(z string) string  { return xingZhi[z] }
func DiZhiHai(z string) string   { return haiZhi[z] }
func DiZhiPo(z string) string    { return poZhi[z] }

// ---- 五行生克 ----

var wuXingSheng = map[string]string{"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
var wuXingKe = map[string]string{"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

func WuXingSheng(a, b string) bool { return wuXingSheng[a] == b }
func WuXingKe(a, b string) bool    { return wuXingKe[a] == b }

// ShengWo 生我者（印）。
func ShengWo(w string) string {
	for k, v := range wuXingSheng {
		if v == w {
			return k
		}
	}
	return ""
}

// KeWo 克我者（官杀）。
func KeWo(w string) string {
	for k, v := range wuXingKe {
		if v == w {
			return k
		}
	}
	return ""
}
