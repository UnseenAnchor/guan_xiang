package store

import (
	"encoding/json"
	"path/filepath"
	"testing"
)

func newTestStore(t *testing.T) *Store {
	t.Helper()
	st, err := Open(filepath.Join(t.TempDir(), "data", "test.db"))
	if err != nil {
		t.Fatalf("打开历史库失败: %v", err)
	}
	t.Cleanup(func() { st.Close() })
	return st
}

func sampleRecord(title string) Record {
	chart, _ := json.Marshal(map[string]any{"pillars": "辛丑乙未己巳甲戌"})
	return Record{
		Title: title, Solar: "1961-08-04 19:24", Lunar: "一九六一年六月廿三",
		Pillars: "辛丑乙未己巳甲戌", DayMaster: "己", Sex: "男",
		Input: json.RawMessage(`{"date":"1961-08-04"}`), Chart: chart,
	}
}

func TestSaveListGetUpdateDelete(t *testing.T) {
	st := newTestStore(t)
	saved, err := st.Save(sampleRecord("奥巴马"))
	if err != nil {
		t.Fatalf("保存失败: %v", err)
	}
	if saved.ID == "" || saved.CreatedAt == "" {
		t.Fatalf("保存结果缺少 id/时间戳: %+v", saved)
	}
	list, err := st.List("")
	if err != nil || len(list) != 1 {
		t.Fatalf("列表应有一条: %v %v", list, err)
	}
	if list[0].Pillars != "辛丑乙未己巳甲戌" {
		t.Fatalf("列表摘要异常: %+v", list[0])
	}
	got, err := st.Get(saved.ID)
	if err != nil {
		t.Fatalf("读取失败: %v", err)
	}
	if len(got.Chart) == 0 || string(got.Chart) == "{}" {
		t.Fatalf("命盘 JSON 丢失: %s", got.Chart)
	}
	updated, err := st.Update(saved.ID, "奥巴马 · 男命", "已核对")
	if err != nil || updated.Title != "奥巴马 · 男命" || updated.Note != "已核对" {
		t.Fatalf("更新失败: %+v %v", updated, err)
	}
	if hits, _ := st.List("甲戌"); len(hits) != 1 {
		t.Fatalf("按干支搜索应命中一条: %v", hits)
	}
	if hits, _ := st.List("不存在的关键词"); len(hits) != 0 {
		t.Fatalf("无关关键词不应命中: %v", hits)
	}
	if err := st.Delete(saved.ID); err != nil {
		t.Fatalf("删除失败: %v", err)
	}
	if _, err := st.Get(saved.ID); !IsNotFound(err) {
		t.Fatalf("删除后应返回 not found, got %v", err)
	}
	if err := st.Delete("missing"); !IsNotFound(err) {
		t.Fatalf("删除不存在记录应 not found, got %v", err)
	}
}

func TestDataPersistsAcrossReopen(t *testing.T) {
	path := filepath.Join(t.TempDir(), "guanxiang.db")
	st, err := Open(path)
	if err != nil {
		t.Fatalf("首次打开失败: %v", err)
	}
	saved, err := st.Save(sampleRecord("持久化检查"))
	if err != nil {
		t.Fatalf("保存失败: %v", err)
	}
	if err := st.Close(); err != nil {
		t.Fatalf("关闭失败: %v", err)
	}

	// 重新打开（等价于关掉客户端再启动）后必须还能读到。
	reopened, err := Open(path)
	if err != nil {
		t.Fatalf("重新打开失败: %v", err)
	}
	defer reopened.Close()
	got, err := reopened.Get(saved.ID)
	if err != nil {
		t.Fatalf("重开后读取失败: %v", err)
	}
	if got.Title != "持久化检查" || got.Pillars != "辛丑乙未己巳甲戌" {
		t.Fatalf("重开后数据不一致: %+v", got)
	}
	if n, _ := reopened.Count(); n != 1 {
		t.Fatalf("重开后计数应为 1, got %d", n)
	}
}
