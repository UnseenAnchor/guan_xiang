package legal

import _ "embed"

// notices 是随二进制分发的第三方组件与数据来源声明。
// 修改依赖后必须同步更新，并由 notices_test.go 校验覆盖率。
//
//go:embed notices.md
var notices []byte

// Notices 返回声明全文（Markdown）。
func Notices() []byte { return notices }

// Version 是声明的校对日期，用于界面上标注"这份名单是什么时候核对的"。
const Version = "2026-11-07"
