package bazi

import (
	"fmt"
	"strings"
)

func runeAt(s string, i int) string {
	r := []rune(s)
	if i < 0 || i >= len(r) {
		return ""
	}
	return string(r[i])
}

func join(items []string, sep string) string { return strings.Join(items, sep) }

func signed(v float64) string {
	if v > 0 {
		return fmt.Sprintf("+%.1f", v)
	}
	return fmt.Sprintf("%.1f", v)
}

func round1(v float64) float64 {
	return float64(int64(v*10+signOf(v)*0.5)) / 10
}

func signOf(v float64) float64 {
	if v < 0 {
		return -1
	}
	return 1
}
