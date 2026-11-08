package bazi

import (
	"fmt"
	"strings"
)

// 本地导出：Markdown / 纯文本。全部在客户端本地生成，不经过网络。

func (c *Chart) pillarLine(label string, pick func(Pillar) string) string {
	cells := make([]string, 0, 4)
	for _, p := range c.Pillars {
		cells = append(cells, padCenter(pick(p), 10))
	}
	return label + " " + strings.Join(cells, "")
}

func padCenter(s string, width int) string {
	r := []rune(s)
	n := len(r)
	if n >= width {
		return s
	}
	left := (width - n) / 2
	right := width - n - left
	return strings.Repeat(" ", left) + s + strings.Repeat(" ", right)
}

func (c *Chart) header() string {
	return c.Input.Original + " " + c.Input.Sex
}

// ToText 生成与网页端同口径的纯文本命盘。
func (c *Chart) ToText() string {
	var b strings.Builder
	b.WriteString(strings.Repeat("=", 42) + "\n")
	b.WriteString("【" + c.header() + "】\n")
	b.WriteString("农历: " + c.Lunar + "  生肖: " + c.ShengXiao + "\n")
	if c.TrueSolar != nil {
		b.WriteString("真太阳时: " + c.TrueSolar.Original + " → " + c.TrueSolar.Corrected +
			fmt.Sprintf(" (校正 %.1f 分)\n", c.TrueSolar.TotalMinute))
	}
	b.WriteString(strings.Repeat("-", 42) + "\n")
	b.WriteString("四柱:\n")
	b.WriteString(c.pillarLine("     ", func(p Pillar) string { return p.GanZhi }) + "\n")
	b.WriteString(c.pillarLine("藏干", func(p Pillar) string { return strings.Join(p.CangGan, "") }) + "\n")
	b.WriteString(c.pillarLine("十神", func(p Pillar) string { return p.ShiShenGan }) + "\n")
	b.WriteString(c.pillarLine("纳音", func(p Pillar) string { return p.NaYin }) + "\n")
	b.WriteString(c.pillarLine("空亡", func(p Pillar) string { return strings.Join(p.KongWang, "") }) + "\n")
	b.WriteString(c.pillarLine("地势", func(p Pillar) string { return p.DiShi }) + "\n")
	b.WriteString(c.pillarLine("自坐", func(p Pillar) string { return p.ChangSheng }) + "\n")
	b.WriteString(strings.Repeat("-", 42) + "\n")
	b.WriteString(fmt.Sprintf("日主: %s  胎元: %s  命宫: %s  身宫: %s\n", c.DayMaster, c.TaiYuan, c.MingGong, c.ShenGong))
	b.WriteString(fmt.Sprintf("旺衰: %s (评分 %.1f)  月令%s  得令%+.0f/得地%+.1f/得势%+.1f\n",
		c.Strength.Level, c.Strength.Score, c.Strength.MonthState,
		c.Strength.Parts["得令"], c.Strength.Parts["得地"], c.Strength.Parts["得势"]))
	b.WriteString(fmt.Sprintf("格局: %s (%s)\n", c.GeJu.Name, c.GeJu.Note))
	b.WriteString(fmt.Sprintf("用神: %s  忌神: %s  (%s)\n", strings.Join(c.YongShen.Use, "/"),
		emptyDash(strings.Join(c.YongShen.Avoid, "/")), c.YongShen.Method))
	b.WriteString(fmt.Sprintf("起运: %d年%d个月%d天%d小时  交运: %s\n",
		c.DaYun.StartYears, c.DaYun.StartMonths, c.DaYun.StartDays, c.DaYun.StartHours, emptyDash(c.DaYun.JiaoYun)))

	var dy []string
	for _, d := range c.DaYun.List {
		if d.GanZhi != "" {
			dy = append(dy, fmt.Sprintf("%s(%d)", d.GanZhi, d.StartYear))
		}
	}
	b.WriteString("大运: " + strings.Join(dy, " ") + "\n")
	var ln []string
	for _, l := range c.LiuNian {
		ln = append(ln, fmt.Sprintf("%d:%s", l.Year, l.GanZhi))
	}
	b.WriteString("流年: " + strings.Join(ln, " ") + "\n")
	b.WriteString(strings.Repeat("-", 42) + "\n")
	b.WriteString("神煞:\n")
	for _, s := range c.ShenSha {
		b.WriteString("  " + s.Name + "(" + s.Where + ") " + s.Note + "\n")
	}
	if len(c.Relations) > 0 {
		b.WriteString(strings.Repeat("-", 42) + "\n刑冲合会:\n")
		for _, r := range c.Relations {
			b.WriteString("  " + r.Type + " " + r.Where + " " + r.GZ + " " + r.Note + "\n")
		}
	}
	b.WriteString(strings.Repeat("=", 42) + "\n")
	return b.String()
}

func emptyDash(s string) string {
	if strings.TrimSpace(s) == "" {
		return "—"
	}
	return s
}

// ToMarkdown 生成带章节结构的 Markdown（本地保存/分享用）。
func (c *Chart) ToMarkdown() string {
	var b strings.Builder
	b.WriteString("# 观象命盘 · " + c.header() + "\n\n")
	b.WriteString("> 排盘：本地离线引擎 guanxiang-desktop/go（" + c.Meta.LunarLib + "）\n\n")
	b.WriteString("| 项目 | 内容 |\n| :--- | :--- |\n")
	b.WriteString("| 公历 | " + c.Input.Solar + " |\n")
	b.WriteString("| 农历 | " + c.Lunar + " |\n")
	b.WriteString("| 生肖 | " + c.ShengXiao + " |\n")
	b.WriteString("| 日主 | " + c.DayMaster + " |\n")
	b.WriteString("| 排盘口径 | " + c.Input.TimeBasis + " |\n\n")

	if c.TrueSolar != nil {
		b.WriteString("## 真太阳时校正\n\n")
		b.WriteString(fmt.Sprintf("- 原始时间：%s\n- 校正后：%s（%s）\n- 总校正：%.1f 分 = 经度差 %.1f + 均时差 %.1f\n\n",
			c.TrueSolar.Original, c.TrueSolar.Corrected, c.TrueSolar.CorrectDate,
			c.TrueSolar.TotalMinute, c.TrueSolar.LonDiff, c.TrueSolar.Equation))
	}

	b.WriteString("## 四柱\n\n")
	b.WriteString("| 柱 | 干支 | 十神 | 藏干 | 纳音 | 空亡 | 地势 |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
	for _, p := range c.Pillars {
		b.WriteString(fmt.Sprintf("| %s | %s | %s | %s | %s | %s | %s |\n", p.Name, p.GanZhi, p.ShiShenGan,
			strings.Join(p.CangGan, ""), p.NaYin, strings.Join(p.KongWang, ""), p.DiShi))
	}
	b.WriteString("\n")

	b.WriteString("## 结构分析\n\n")
	b.WriteString(fmt.Sprintf("- 旺衰：%s（评分 %.1f，月令%s）\n", c.Strength.Level, c.Strength.Score, c.Strength.MonthState))
	b.WriteString(fmt.Sprintf("- 格局：%s（%s）\n", c.GeJu.Name, c.GeJu.Note))
	b.WriteString(fmt.Sprintf("- 用神：%s；忌神：%s；方法：%s\n",
		strings.Join(c.YongShen.Use, "/"), emptyDash(strings.Join(c.YongShen.Avoid, "/")), c.YongShen.Method))
	b.WriteString("- 五行结构计数（四干 + 四支本气，非旺衰判断）：")
	var parts []string
	for _, e := range c.Elements {
		parts = append(parts, fmt.Sprintf("%s%d", e.Name, e.Count))
	}
	b.WriteString(strings.Join(parts, " ") + "\n\n")

	if len(c.Relations) > 0 {
		b.WriteString("## 刑冲合会\n\n")
		for _, r := range c.Relations {
			b.WriteString(fmt.Sprintf("- %s · %s（%s）：%s\n", r.Type, r.Where, r.GZ, r.Note))
		}
		b.WriteString("\n")
	}
	if len(c.ShenSha) > 0 {
		b.WriteString("## 神煞\n\n")
		for _, s := range c.ShenSha {
			b.WriteString(fmt.Sprintf("- %s（%s）%s\n", s.Name, s.Where, s.Note))
		}
		b.WriteString("\n")
	}

	b.WriteString("## 大运\n\n")
	b.WriteString(fmt.Sprintf("起运 %d 年 %d 个月 %d 天 %d 小时，交运 %s。\n\n",
		c.DaYun.StartYears, c.DaYun.StartMonths, c.DaYun.StartDays, c.DaYun.StartHours, emptyDash(c.DaYun.JiaoYun)))
	b.WriteString("| 序 | 干支 | 起年 | 终年 | 年龄 | 十神 | 长生 |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
	for _, d := range c.DaYun.List {
		b.WriteString(fmt.Sprintf("| %d | %s | %d | %d | %s | %s | %s |\n", d.Index, emptyDash(d.GanZhi),
			d.StartYear, d.EndYear, d.Age, d.ShiShen, d.ChangSheng))
	}
	b.WriteString("\n## 流年\n\n")
	for _, l := range c.LiuNian {
		b.WriteString(fmt.Sprintf("- %d %s：%s\n", l.Year, l.GanZhi, l.Note))
	}
	b.WriteString("\n")

	if len(c.Notes) > 0 {
		b.WriteString("## 参照与断语\n\n")
		b.WriteString("> 古籍参照、规则匹配与实验模型分层标注，不作确定性吉凶结论。\n\n")
		for _, n := range c.Notes {
			b.WriteString("### " + n.Title + "\n\n")
			if n.Source != "" {
				b.WriteString("*来源：" + n.Source + "*\n\n")
			}
			b.WriteString(n.Body + "\n\n")
		}
	}
	return b.String()
}
