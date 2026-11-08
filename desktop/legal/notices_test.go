package legal

import (
	"os/exec"
	"strings"
	"testing"
)

// 声明的 §1 表格必须覆盖所有真正链接进二进制的模块，避免新增依赖时漏掉许可。
// 依赖 `go list`：Go 工具链本身是构建前提，测试环境里必然存在。
func TestNoticesCoverLinkedModules(t *testing.T) {
	out, err := exec.Command("go", "list", "-deps",
		"-f", "{{if .Module}}{{.Module.Path}}{{end}}", "..").Output()
	if err != nil {
		t.Skipf("无法运行 go list（跳过覆盖率检查）: %v", err)
	}
	text := string(Notices())
	var missing []string
	seen := map[string]bool{}
	for _, line := range strings.Split(string(out), "\n") {
		path := strings.TrimSpace(line)
		if path == "" || path == "guanxiang/desktop" || seen[path] {
			continue
		}
		seen[path] = true
		if !strings.Contains(text, path) {
			missing = append(missing, path)
		}
	}
	if len(missing) > 0 {
		t.Fatalf("notices.md 未覆盖以下链接模块，请补充版权与许可：\n  %s", strings.Join(missing, "\n  "))
	}
	if len(seen) < 10 {
		t.Fatalf("模块枚举结果异常（仅 %d 个），检查 go list 参数", len(seen))
	}
}

// 声明里必须包含实际随包分发的关键版权行，防止被误删。
func TestNoticesContainRequiredAttributions(t *testing.T) {
	text := string(Notices())
	required := []string{
		"Copyright (c) 2026 UnseenAnchor and 观象 (guan_xiang) contributors",
		"Copyright (c) 2020 6tail",                   // lunar-go
		"Copyright (c) 2017 The Sqlite Authors",      // modernc.org/sqlite
		"Copyright (c) 2020 John Chadwick",           // go-webview2
		"Copyright © 2021, John Chadwick",            // go-winloader (ISC)
		"Copyright (C) Microsoft Corporation",        // WebView2Loader.dll
		"Copyright (c) 2026 Caho1",                   // open-claude-ui 令牌
		"Copyright (c) 2019 xiangyuecn",              // AreaCity 数据
		"SQLite Is Public Domain",                    // SQLite
		"MIT License", "ISC License", "BSD-3-Clause", // 许可类型齐备
	}
	for _, needle := range required {
		if !strings.Contains(text, needle) {
			t.Errorf("notices.md 缺少必需内容: %q", needle)
		}
	}
	if Version == "" {
		t.Error("legal.Version 不能为空")
	}
}
