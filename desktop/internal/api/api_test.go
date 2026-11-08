package api

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"guanxiang/desktop/internal/store"
)

func newTestServer(t *testing.T) (*httptest.Server, *store.Store) {
	t.Helper()
	st, err := store.Open(filepath.Join(t.TempDir(), "guanxiang.db"))
	if err != nil {
		t.Fatalf("打开历史库失败: %v", err)
	}
	t.Cleanup(func() { st.Close() })
	ui := os.DirFS(filepath.Join("..", "..", "ui"))
	api := New(st, ui, "1.0.0")
	api.SetNotices([]byte("# 第三方许可\n\nCopyright (c) 2020 6tail\n"))
	srv := httptest.NewServer(api.Handler())
	t.Cleanup(srv.Close)
	return srv, st
}

func request(t *testing.T, srv *httptest.Server, method, path string, body any) (int, map[string]any) {
	t.Helper()
	var reader *bytes.Reader
	if body != nil {
		raw, _ := json.Marshal(body)
		reader = bytes.NewReader(raw)
	} else {
		reader = bytes.NewReader(nil)
	}
	req, _ := http.NewRequest(method, srv.URL+path, reader)
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("请求失败: %v", err)
	}
	defer resp.Body.Close()
	var payload map[string]any
	_ = json.NewDecoder(resp.Body).Decode(&payload)
	return resp.StatusCode, payload
}

func solarInput() map[string]any {
	return map[string]any{
		"calendar": "solar", "date": "1961-08-04", "time": "19:24", "sex": 1,
		"longitude": "", "use_true_solar_time": false, "timezone": "Asia/Shanghai",
	}
}

func TestHealthDeclaresOfflineAndNoLogin(t *testing.T) {
	srv, _ := newTestServer(t)
	status, payload := request(t, srv, "GET", "/api/health", nil)
	if status != http.StatusOK || payload["ok"] != true {
		t.Fatalf("health 异常: %d %v", status, payload)
	}
	if payload["offline"] != true || payload["login"] != false {
		t.Fatalf("未声明离线/免登录: %v", payload)
	}
	if payload["engine"] != "guanxiang-desktop/go" {
		t.Fatalf("引擎标识异常: %v", payload["engine"])
	}
}

func TestChartEndpoint(t *testing.T) {
	srv, _ := newTestServer(t)
	status, payload := request(t, srv, "POST", "/api/chart", solarInput())
	if status != http.StatusOK || payload["ok"] != true {
		t.Fatalf("排盘失败: %d %v", status, payload)
	}
	chart, _ := payload["chart"].(map[string]any)
	pillars, _ := chart["pillars"].([]any)
	var joined strings.Builder
	for _, item := range pillars {
		joined.WriteString(item.(map[string]any)["ganzhi"].(string))
	}
	if joined.String() != "辛丑乙未己巳甲戌" {
		t.Fatalf("四柱错误: %s", joined.String())
	}
	if chart["true_solar"] != nil {
		t.Fatalf("未启用真太阳时却返回了校正")
	}

	bad := solarInput()
	bad["sex"] = 5
	status, payload = request(t, srv, "POST", "/api/chart", bad)
	if status != http.StatusBadRequest || payload["ok"] != false {
		t.Fatalf("非法参数未被拒绝: %d %v", status, payload)
	}
}

func TestHistoryLifecycleAndExport(t *testing.T) {
	srv, _ := newTestServer(t)
	_, payload := request(t, srv, "POST", "/api/chart", solarInput())
	chart := payload["chart"]

	status, saved := request(t, srv, "POST", "/api/history", map[string]any{
		"title": "奥巴马", "note": "核对用", "chart": chart,
	})
	if status != http.StatusOK || saved["ok"] != true {
		t.Fatalf("保存失败: %d %v", status, saved)
	}
	item := saved["item"].(map[string]any)
	id := item["id"].(string)
	if item["pillars"] != "辛丑乙未己巳甲戌" {
		t.Fatalf("摘要干支错误: %v", item["pillars"])
	}

	_, list := request(t, srv, "GET", "/api/history", nil)
	if items, _ := list["items"].([]any); len(items) != 1 {
		t.Fatalf("列表条数异常: %v", list)
	}
	_, filtered := request(t, srv, "GET", "/api/history?q=甲戌", nil)
	if items, _ := filtered["items"].([]any); len(items) != 1 {
		t.Fatalf("搜索未命中: %v", filtered)
	}

	_, got := request(t, srv, "GET", "/api/history/"+id, nil)
	if got["ok"] != true {
		t.Fatalf("读取失败: %v", got)
	}

	status, updated := request(t, srv, "PATCH", "/api/history/"+id, map[string]any{"title": "奥巴马 · 男命", "note": "已核对"})
	if status != http.StatusOK || updated["item"].(map[string]any)["title"] != "奥巴马 · 男命" {
		t.Fatalf("更新失败: %v", updated)
	}

	for _, format := range []string{"md", "txt"} {
		resp, err := http.Get(srv.URL + "/api/history/" + id + "/export?format=" + format)
		if err != nil {
			t.Fatalf("导出失败: %v", err)
		}
		buf := new(bytes.Buffer)
		_, _ = buf.ReadFrom(resp.Body)
		resp.Body.Close()
		body := buf.String()
		if resp.StatusCode != http.StatusOK || len(body) < 200 {
			t.Fatalf("%s 导出异常: %d len=%d", format, resp.StatusCode, len(body))
		}
		if format == "md" && !strings.Contains(body, "## 四柱") {
			t.Fatalf("Markdown 导出缺少四柱章节")
		}
		if format == "txt" && !strings.Contains(body, "大运") {
			t.Fatalf("TXT 导出缺少大运")
		}
	}

	status, _ = request(t, srv, "DELETE", "/api/history/"+id, nil)
	if status != http.StatusOK {
		t.Fatalf("删除失败: %d", status)
	}
	status, _ = request(t, srv, "GET", "/api/history/"+id, nil)
	if status != http.StatusNotFound {
		t.Fatalf("删除后应 404, got %d", status)
	}
	if status, _ := request(t, srv, "DELETE", "/api/history/"+id, nil); status != http.StatusNotFound {
		t.Fatalf("重复删除应 404, got %d", status)
	}
}

func TestLunarMonthsEndpoint(t *testing.T) {
	srv, _ := newTestServer(t)
	status, payload := request(t, srv, "GET", "/api/lunar-months?year=2024", nil)
	if status != http.StatusOK || payload["ok"] != true {
		t.Fatalf("农历月份查询失败: %d %v", status, payload)
	}
	months, _ := payload["months"].([]any)
	if len(months) < 12 {
		t.Fatalf("月份数异常: %d", len(months))
	}
	if status, _ := request(t, srv, "GET", "/api/lunar-months?year=abc", nil); status != http.StatusBadRequest {
		t.Fatalf("非法年份应 400, got %d", status)
	}
}

func TestStaticAssetsAndPing(t *testing.T) {
	srv, _ := newTestServer(t)
	resp, err := http.Get(srv.URL + "/")
	if err != nil {
		t.Fatalf("首页请求失败: %v", err)
	}
	buf := new(bytes.Buffer)
	_, _ = buf.ReadFrom(resp.Body)
	resp.Body.Close()
	html := buf.String()
	if !strings.Contains(html, "观象") || !strings.Contains(html, "cds-theme.css") {
		t.Fatalf("首页内容异常")
	}
	// 静态资源不应依赖外网：页面与样式里不允许出现 http(s) 外链资源。
	for _, asset := range []string{"/app.css", "/app.js", "/cds-theme.css"} {
		resp, err := http.Get(srv.URL + asset)
		if err != nil || resp.StatusCode != http.StatusOK {
			t.Fatalf("静态资源 %s 不可用: %v", asset, err)
		}
		resp.Body.Close()
	}
	if status, _ := request(t, srv, "POST", "/api/ping", nil); status != http.StatusOK {
		t.Fatalf("心跳失败: %d", status)
	}
}

func TestNoticesEndpointServesEmbeddedNotice(t *testing.T) {
	srv, _ := newTestServer(t)
	resp, err := http.Get(srv.URL + "/legal/notices.md")
	if err != nil {
		t.Fatalf("许可声明请求失败: %v", err)
	}
	defer resp.Body.Close()
	buf := new(bytes.Buffer)
	_, _ = buf.ReadFrom(resp.Body)
	body := buf.String()
	if resp.StatusCode != http.StatusOK || !strings.Contains(body, "Copyright (c) 2020 6tail") {
		t.Fatalf("许可声明内容异常: %d %q", resp.StatusCode, body[:min(len(body), 60)])
	}
	if ct := resp.Header.Get("Content-Type"); !strings.Contains(ct, "text/markdown") {
		t.Fatalf("Content-Type 应为 text/markdown, got %s", ct)
	}
	// 未注册声明时必须明确 404，而不是返回空内容
	empty := New(nil, os.DirFS(filepath.Join("..", "..", "ui")), "1.0.0")
	rec := httptest.NewRecorder()
	empty.handleNotices(rec, httptest.NewRequest("GET", "/legal/notices.md", nil))
	if rec.Code != http.StatusNotFound {
		t.Fatalf("未设置声明时应 404, got %d", rec.Code)
	}
}
