package bazi

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"strings"
	"sync"
)

// 知识数据内嵌：与仓库 knowledge/ 下的 UTF-8 原始文件逐字节一致（见 data_test.go）。
// 内嵌后客户端完全离线运行，不依赖任何外部文件或网络。

//go:embed data/ny.json
var rawNy []byte

//go:embed data/serjson.json
var rawSer []byte

//go:embed data/yueling.json
var rawYueling []byte

//go:embed data/xingge.json
var rawXingge []byte

//go:embed data/sanming.json
var rawSanming []byte

type ganInfo struct {
	WuXing  string `json:"wu_xing"`
	YinYang string `json:"yin_yang"`
}

type zhiInfo struct {
	WuXing    string `json:"wu_xing"`
	ShengXiao string `json:"sheng_xiao"`
	YinYang   string `json:"yin_yang"`
	GanStr    string `json:"gan_str"`
	WuXingStr string `json:"wuxing_str"`
}

type nayinInfo struct {
	WuXing        string `json:"wuxing"`
	WuXingJian    string `json:"wuxing_jian"`
	KongWang      string `json:"kong_wang"`
	GanShengWang  string `json:"gan_sheng_wang"`
	GanZhiShengKe string `json:"gan_zhi_sheng_ke"`
	XunMing       string `json:"xun_ming"`
	Ming          string `json:"ming"`
}

type nyFile struct {
	Gan        map[string]ganInfo   `json:"天干"`
	Zhi        map[string]zhiInfo   `json:"地支"`
	NaYin      map[string]nayinInfo `json:"纳音"`
	ShiShen    map[string]string    `json:"十神"`
	ChangSheng map[string]string    `json:"十二长生"`
}

type serFile struct {
	ShengSha json.RawMessage   `json:"shengsha"`
	SSXX     map[string]string `json:"ssxx"`
	SWK      map[string]string `json:"swk"`
}

type knowledge struct {
	ny         nyFile
	ssxx       map[string]string
	swk        map[string]string
	yueling    map[string]string
	xingge     map[string]string
	xinggeAll  string
	sanmingDun string
	sanmingTai string
}

var (
	kb     *knowledge
	kbOnce sync.Once
	kbErr  error
)

func mustJSON(raw []byte, target any, name string) {
	if err := json.Unmarshal(raw, target); err != nil {
		panic(fmt.Sprintf("内嵌知识数据 %s 解析失败: %v", name, err))
	}
}

// Knowledge 返回进程内单例知识库，任何一次读取失败都会以 error 返回而不是静默降级。
func Knowledge() (*knowledge, error) {
	kbOnce.Do(func() {
		k := &knowledge{}
		mustJSON(rawNy, &k.ny, "ny.json")
		var ser serFile
		mustJSON(rawSer, &ser, "serjson.json")
		k.ssxx, k.swk = ser.SSXX, ser.SWK
		mustJSON(rawYueling, &k.yueling, "yueling.json")

		var xg struct {
			XingQingZongLun string            `json:"xingqing_zonglun"`
			ShiGanXingGe    map[string]string `json:"shigan_xingge"`
		}
		mustJSON(rawXingge, &xg, "xingge.json")
		k.xinggeAll = xg.XingQingZongLun
		k.xingge = xg.ShiGanXingGe

		var sm struct {
			LunDaYun  string `json:"论大运"`
			LunTaiSui string `json:"论太岁"`
		}
		mustJSON(rawSanming, &sm, "sanming.json")
		k.sanmingDun = sm.LunDaYun
		k.sanmingTai = sm.LunTaiSui

		if len(k.ny.Gan) != 10 || len(k.ny.Zhi) != 12 || len(k.ny.NaYin) != 60 {
			kbErr = fmt.Errorf("基础干支表计数异常: gan=%d zhi=%d nayin=%d", len(k.ny.Gan), len(k.ny.Zhi), len(k.ny.NaYin))
			kb = k
			return
		}
		if len(k.ny.ShiShen) != 100 || len(k.ny.ChangSheng) != 120 {
			kbErr = fmt.Errorf("十神/十二长生表计数异常: %d/%d", len(k.ny.ShiShen), len(k.ny.ChangSheng))
			kb = k
			return
		}
		kb = k
	})
	return kb, kbErr
}

// stripTags 去除上游富文本标签并还原换行。
func stripTags(text string) string {
	cleaned := fontTagPattern.ReplaceAllString(text, "")
	cleaned = strings.ReplaceAll(cleaned, `\n`, "\n")
	cleaned = strings.ReplaceAll(cleaned, `\u003c`, "<")
	return strings.ReplaceAll(cleaned, `\u003e`, ">")
}
