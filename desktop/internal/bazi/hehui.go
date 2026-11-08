package bazi

import (
	"sort"
	"strings"
)

// 刑冲合会（与 bazi/hehui.py 对齐：天干五合 / 六合 / 三合 / 半合 / 六冲 / 三刑 / 六害 / 相破 / 三会）。

type Relation struct {
	Type  string `json:"type"`
	Where string `json:"where"`
	GZ    string `json:"gz"`
	Note  string `json:"note"`
}

var positions = []string{"年", "月", "日", "时"}

func AnalyzeRelations(pillars map[string]string) []Relation {
	out := make([]Relation, 0, 8)
	gans := map[string]string{}
	zhis := map[string]string{}
	for _, p := range positions {
		gz := pillars[p]
		if len([]rune(gz)) < 2 {
			continue
		}
		r := []rune(gz)
		gans[p] = string(r[0])
		zhis[p] = string(r[1])
	}
	present := func(members string) []string {
		var list []string
		for _, p := range positions {
			if strings.Contains(members, zhis[p]) {
				list = append(list, p)
			}
		}
		return list
	}
	allPresent := func(members string) bool {
		list := present(members)
		seen := map[string]bool{}
		for _, p := range list {
			seen[zhis[p]] = true
		}
		for _, m := range []rune(members) {
			if !seen[string(m)] {
				return false
			}
		}
		return true
	}

	for i := 0; i < 4; i++ {
		for j := i + 1; j < 4; j++ {
			gi, gj := gans[positions[i]], gans[positions[j]]
			if TianGanHe(gi) == gj {
				out = append(out, Relation{"天干五合", positions[i] + positions[j], gi + gj, gi + "与" + gj + "合"})
			}
		}
	}
	for i := 0; i < 4; i++ {
		for j := i + 1; j < 4; j++ {
			zi, zj := zhis[positions[i]], zhis[positions[j]]
			if DiZhiHe(zi) == zj {
				out = append(out, Relation{"地支六合", positions[i] + positions[j], zi + zj, zi + "与" + zj + "合"})
			}
		}
	}
	for _, group := range []struct{ name, members string }{
		{"水局", "申子辰"}, {"火局", "寅午戌"}, {"金局", "巳酉丑"}, {"木局", "亥卯未"},
	} {
		if allPresent(group.members) {
			list := present(group.members)
			where := strings.Join(list, "")
			var zs []string
			for _, p := range list {
				zs = append(zs, zhis[p])
			}
			sort.Strings(zs)
			out = append(out, Relation{"地支三合", where, strings.Join(zs, ""), group.name + "成局"})
		}
	}
	for _, group := range []struct{ name, members string }{
		{"水局", "申子辰"}, {"火局", "寅午戌"}, {"金局", "巳酉丑"}, {"木局", "亥卯未"},
	} {
		list := present(group.members)
		seen := map[string]bool{}
		for _, p := range list {
			seen[zhis[p]] = true
		}
		mid := string([]rune(group.members)[1])
		if len(seen) == 2 && seen[mid] {
			where := strings.Join(list, "")
			var zs []string
			for _, p := range list {
				zs = append(zs, zhis[p])
			}
			out = append(out, Relation{"地支半合", where, strings.Join(zs, ""), group.name + "半合"})
		}
	}
	for i := 0; i < 4; i++ {
		for j := i + 1; j < 4; j++ {
			zi, zj := zhis[positions[i]], zhis[positions[j]]
			if DiZhiChong(zi) == zj {
				out = append(out, Relation{"地支六冲", positions[i] + positions[j], zi + zj, zi + "冲" + zj})
			}
		}
	}
	for _, trio := range []struct {
		members []string
		name    string
	}{
		{[]string{"寅", "巳", "申"}, "无恩之刑"},
		{[]string{"丑", "戌", "未"}, "恃势之刑"},
	} {
		found := true
		var list []string
		for _, p := range positions {
			for _, m := range trio.members {
				if zhis[p] == m {
					list = append(list, p)
				}
			}
		}
		seen := map[string]bool{}
		for _, p := range list {
			seen[zhis[p]] = true
		}
		for _, m := range trio.members {
			if !seen[m] {
				found = false
			}
		}
		if found {
			var zs []string
			for _, p := range list {
				zs = append(zs, zhis[p])
			}
			out = append(out, Relation{"地支三刑", strings.Join(list, ""), strings.Join(zs, ""), trio.name + "成局"})
		}
	}
	for i := 0; i < 4; i++ {
		for j := i + 1; j < 4; j++ {
			zi, zj := zhis[positions[i]], zhis[positions[j]]
			if DiZhiXing(zi) != zj {
				continue
			}
			if zi == zj {
				out = append(out, Relation{"地支自刑", positions[i] + positions[j], zi + zj, zi + "自刑"})
				continue
			}
			if (zi == "子" && zj == "卯") || (zi == "卯" && zj == "子") {
				out = append(out, Relation{"地支相刑", positions[i] + positions[j], zi + zj, zi + "刑" + zj})
				continue
			}
			out = append(out, Relation{"地支相刑", positions[i] + positions[j], zi + zj, zi + "刑" + zj})
		}
	}
	for i := 0; i < 4; i++ {
		for j := i + 1; j < 4; j++ {
			zi, zj := zhis[positions[i]], zhis[positions[j]]
			if DiZhiHai(zi) == zj {
				out = append(out, Relation{"地支六害", positions[i] + positions[j], zi + zj, zi + "害" + zj})
			}
		}
	}
	for i := 0; i < 4; i++ {
		for j := i + 1; j < 4; j++ {
			zi, zj := zhis[positions[i]], zhis[positions[j]]
			if DiZhiPo(zi) == zj {
				out = append(out, Relation{"地支相破", positions[i] + positions[j], zi + zj, zi + "破" + zj})
			}
		}
	}
	for _, group := range []struct{ name, members string }{
		{"东方木", "寅卯辰"}, {"南方火", "巳午未"}, {"西方金", "申酉戌"}, {"北方水", "亥子丑"},
	} {
		if allPresent(group.members) {
			list := present(group.members)
			var zs []string
			for _, p := range list {
				zs = append(zs, zhis[p])
			}
			out = append(out, Relation{"地支三会", strings.Join(list, ""), strings.Join(zs, ""), group.name + "会方"})
		}
	}
	return out
}
