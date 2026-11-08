/* ==========================================================================
   观象桌面版 · 界面逻辑
   - 纯原生 JavaScript，无框架、无外部请求；所有数据来自本机 127.0.0.1 服务。
   - 交互范式参考 open-claude-ui：分段滑块、发丝卡片、CJK 输入法守卫、滚动渐隐。
   ========================================================================== */
'use strict';

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

const ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (ch) => ESCAPES[ch]);

const state = {
  chart: null,
  record: null,
  items: [],
  query: '',
  lunarCache: new Map(),
  composing: false,
  busy: false,
};

/* ---------- 基础工具 ---------- */

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `请求失败（HTTP ${response.status}）`);
  }
  return data;
}

function toast(message, kind = 'ok') {
  const root = $('#toast-root');
  const node = document.createElement('div');
  node.className = `toast${kind === 'error' ? ' is-error' : ''}`;
  node.innerHTML = `<span class="dot"></span><span>${esc(message)}</span>`;
  root.appendChild(node);
  setTimeout(() => {
    node.style.transition = 'opacity .2s ease, transform .2s ease';
    node.style.opacity = '0';
    node.style.transform = 'translateY(6px)';
    setTimeout(() => node.remove(), 220);
  }, 2600);
}

function syncSegmented(seg) {
  const thumb = $('.segmented-thumb', seg);
  const checked = $('input:checked', seg);
  if (!thumb || !checked) return;
  const label = checked.closest('label');
  const span = label && $('span', label);
  if (!span) return;
  const segRect = seg.getBoundingClientRect();
  const rect = span.getBoundingClientRect();
  thumb.style.width = `${rect.width}px`;
  thumb.style.transform = `translateX(${rect.left - segRect.left - 2}px)`;
}

function syncAllSegmented() {
  $$('.segmented').forEach(syncSegmented);
}

/* ---------- 主题 ---------- */

function applyTheme(mode) {
  document.documentElement.dataset.mode = mode;
  localStorage.setItem('guanxiang-theme', mode);
  // 通知桌面端把原生窗口标题栏一起切到深/浅色（浏览器里运行时会 404，忽略即可）
  fetch('/api/theme', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  }).catch(() => {});
  const input = $(`#theme-seg input[value="${mode}"]`);
  if (input) input.checked = true;
  requestAnimationFrame(() => syncSegmented($('#theme-seg')));
}

/* ---------- 农历月日联动 ---------- */

async function lunarMonths(year) {
  if (state.lunarCache.has(year)) return state.lunarCache.get(year);
  const data = await api(`/api/lunar-months?year=${encodeURIComponent(year)}`);
  state.lunarCache.set(year, data);
  return data;
}

const LUNAR_MONTH_NAMES = ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '冬', '腊'];

async function refreshLunarSelects(preserve = true) {
  const year = Number($('#lunar-year').value) || 1990;
  const monthSelect = $('#lunar-month');
  const daySelect = $('#lunar-day');
  const prevMonth = preserve ? Number(monthSelect.value) : 0;
  const prevDay = preserve ? Number(daySelect.value) : 0;
  let data;
  try {
    data = await lunarMonths(year);
  } catch (error) {
    toast(error.message, 'error');
    return;
  }
  const months = data.months || [];
  const leap = data.leap_month || 0;
  monthSelect.innerHTML = months
    .map((item) => {
      const signed = item.month;
      const isLeap = signed < 0;
      const number = Math.abs(signed);
      const label = `${isLeap ? '闰' : ''}${LUNAR_MONTH_NAMES[number - 1]}月`;
      return `<option value="${signed}">${label}（${item.days}天）</option>`;
    })
    .join('');
  if (prevMonth && months.some((item) => item.month === prevMonth)) {
    monthSelect.value = String(prevMonth);
  }
  if (leap && !months.some((item) => Math.abs(item.month) === 1 && item.month < 0)) {
    // 该年无闰月时，闰月标签自然不存在，无需额外处理。
  }
  updateLunarDays(prevDay);
}

function updateLunarDays(preserveDay = 0) {
  const year = Number($('#lunar-year').value) || 1990;
  const monthSelect = $('#lunar-month');
  const daySelect = $('#lunar-day');
  const cached = state.lunarCache.get(year);
  const signed = Number(monthSelect.value);
  const record = cached && (cached.months || []).find((item) => item.month === signed);
  const days = record ? record.days : 30;
  const keep = preserveDay && preserveDay <= days ? preserveDay : Math.min(Number(daySelect.value) || 1, days);
  daySelect.innerHTML = Array.from({ length: days }, (_, index) => {
    const day = index + 1;
    return `<option value="${day}">${day}</option>`;
  }).join('');
  daySelect.value = String(Math.max(1, Math.min(keep, days)));
}

function daysInSolarMonth(year, month) {
  return new Date(year, month, 0).getDate();
}

function clampSolarDay() {
  const year = Number($('#solar-year').value) || 1990;
  const month = Number($('#solar-month').value) || 1;
  const dayInput = $('#solar-day');
  const max = daysInSolarMonth(year, month);
  dayInput.max = String(max);
  const day = Number(dayInput.value) || 1;
  if (day > max) dayInput.value = String(max);
}

/* ---------- 表单 ---------- */

function currentCalendar() {
  return ($('#calendar-seg input:checked') || {}).value || 'solar';
}

function currentSex() {
  return Number(($('#sex-seg input:checked') || {}).value ?? 1);
}

function toggleCalendarFields() {
  const calendar = currentCalendar();
  $('#solar-fields').hidden = calendar !== 'solar';
  $('#lunar-fields').hidden = calendar !== 'lunar';
}

function syncLongitudeSwitch() {
  const longitude = $('#longitude').value.trim();
  const toggle = $('#true-solar');
  const hint = $('#true-solar-hint');
  const hasLongitude = longitude !== '';
  toggle.disabled = !hasLongitude;
  if (!hasLongitude) {
    toggle.checked = false;
    hint.textContent = '需先填写经度；未启用时不会把经度传给排盘引擎';
  } else {
    hint.textContent = '开启后按经度与均时差校正，口径会在结果中显式标注';
  }
}

function buildPayload() {
  const calendar = currentCalendar();
  const common = {
    calendar,
    sex: currentSex(),
    name: $('#chart-name').value.trim(),
    longitude: $('#longitude').value.trim(),
    use_true_solar_time: $('#true-solar').checked,
    timezone: 'Asia/Shanghai',
  };
  if (calendar === 'solar') {
    const year = Number($('#solar-year').value);
    const month = Number($('#solar-month').value);
    const day = Number($('#solar-day').value);
    if (!year || !month || !day) throw new Error('请填写完整的公历日期');
    return {
      ...common,
      date: `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
      time: $('#birth-time').value || '12:00',
    };
  }
  const lunarMonth = Number($('#lunar-month').value);
  return {
    ...common,
    lunar_year: Number($('#lunar-year').value),
    lunar_month: Math.abs(lunarMonth),
    lunar_day: Number($('#lunar-day').value),
    lunar_leap: lunarMonth < 0,
    time: $('#lunar-time').value || '12:00',
  };
}

function setBusy(busy) {
  state.busy = busy;
  $('#thinking').hidden = !busy;
  $('#submit-btn').disabled = busy;
  const label = $('#submit-btn .btn-label');
  if (label) label.textContent = busy ? '排盘中' : '排盘';
}

/* ---------- 渲染：命盘 ---------- */

function pillarCard(pillar, index) {
  const isDay = pillar.name === '日';
  const cang = (pillar.canggan || [])
    .map((gan, i) => {
      const ss = (pillar.shishen_canggan || [])[i] || '';
      return `<span class="cg">${esc(gan)}<i>${esc(ss)}</i></span>`;
    })
    .join('');
  return `
    <article class="pillar-card${isDay ? ' is-day' : ''}" style="animation-delay:${index * 40}ms">
      <div class="pillar-name"><span>${esc(pillar.name)}柱</span><span>${esc(pillar.nayin)}</span></div>
      <div class="pillar-char"><span class="gan">${esc(pillar.gan)}</span><span class="zhi">${esc(pillar.zhi)}</span></div>
      <span class="pillar-shishen">${esc(pillar.shishen_gan || '—')}</span>
      <dl class="pillar-rows">
        <div><dt>藏干</dt><dd>${cang || '—'}</dd></div>
        <div><dt>空亡</dt><dd>${esc((pillar.kongwang || []).join('') || '—')}</dd></div>
        <div><dt>地势</dt><dd>${esc(pillar.dishi || '—')}</dd></div>
        <div><dt>自坐</dt><dd>${esc(pillar.changsheng || '—')}</dd></div>
      </dl>
    </article>`;
}

function elementBars(elements) {
  const max = Math.max(1, ...(elements || []).map((item) => item.count));
  return `
    <div class="element-bars">
      ${(elements || [])
        .map((item, index) => {
          const ratio = Math.max(0, Math.min(1, item.count / max));
          return `
            <div class="element-bar${item.count === 0 ? ' is-zero' : ''}">
              <div class="top"><span>${esc(item.name)}</span><b class="count">${item.count}</b></div>
              <div class="element-track"><div class="element-fill" style="width:${(ratio * 100).toFixed(1)}%;animation-delay:${index * 45}ms"></div></div>
            </div>`;
        })
        .join('')}
    </div>`;
}

function metrics(chart) {
  const items = [
    { label: '旺衰', value: `${chart.strength.level}（${chart.strength.score}）`, accent: true },
    { label: '月令', value: chart.strength.month_state },
    { label: '格局', value: chart.geju.name },
    { label: '用神', value: (chart.yongshen.use || []).join(' / ') || '—' },
    { label: '忌神', value: (chart.yongshen.avoid || []).join(' / ') || '—' },
    { label: '调候', value: (chart.yongshen.tiaohou || []).join('') || '—' },
    { label: '起运', value: `${chart.dayun.start_years}年${chart.dayun.start_months}月` },
  ];
  return `
    <div class="metric-row">
      ${items
        .map(
          (item) =>
            `<div class="metric${item.accent ? ' accent' : ''}"><span class="label">${esc(item.label)}</span><span class="value">${esc(item.value)}</span></div>`
        )
        .join('')}
    </div>`;
}

function relationChips(relations) {
  if (!relations || !relations.length) return '<p class="muted" style="font-size:12px;margin:0">本盘四柱无明显合冲刑害。</p>';
  return `<div class="chip-grid">${relations
    .map(
      (item) =>
        `<span class="chip"><b>${esc(item.type)}</b>${esc(item.where)} · ${esc(item.gy || item.gz || '')} ${esc(item.note)}</span>`
    )
    .join('')}</div>`;
}

function shenshaChips(list) {
  if (!list || !list.length) return '<p class="muted" style="font-size:12px;margin:0">本盘未命中常见神煞条目。</p>';
  return `<div class="chip-grid">${list
    .map((item) => `<span class="chip"><b>${esc(item.name)}</b>${esc(item.where)}${item.note ? ` · ${esc(item.note)}` : ''}</span>`)
    .join('')}</div>`;
}

function dayunTrack(chart) {
  const now = new Date().getFullYear();
  return `<div class="dayun-track">${(chart.dayun.list || [])
    .map((item) => {
      const isNow = item.ganzhi && now >= item.start_year && now <= item.end_year;
      return `
        <div class="dayun-card${isNow ? ' is-now' : ''}">
          <div class="gz">${esc(item.ganzhi || '起运前')}</div>
          <div class="yr num">${item.start_year}–${item.end_year} · ${esc(item.age)}岁</div>
          <div class="ss">${item.ganzhi ? `${esc(item.shishen)} · ${esc(item.changsheng)}` : '尚未交运'}</div>
        </div>`;
    })
    .join('')}</div>`;
}

function liunianTrack(chart) {
  return `<div class="dayun-track">${(chart.liunian || [])
    .map(
      (item) => `
        <div class="dayun-card">
          <div class="gz">${esc(item.ganzhi)}</div>
          <div class="yr num">${item.year}</div>
          <div class="ss">${esc(item.shishen || '')} · ${esc(item.changsheng || '')}</div>
        </div>`
    )
    .join('')}</div>`;
}

function accordion(title, body, tag) {
  return `
    <details class="accordion">
      <summary>
        <svg class="icon chevron"><use href="#i-chevron" /></svg>
        <span>${esc(title)}</span>
        ${tag ? `<span class="tag">${esc(tag)}</span>` : ''}
      </summary>
      <div class="acc-body"><div class="acc-inner"><div class="acc-text${body.length > 1200 ? ' is-scroll' : ''}">${esc(body)}</div></div></div>
    </details>`;
}

function renderChart(chart, record) {
  const container = $('#result');
  const name = (record && record.title) || chart.input.original;
  const trueSolar = chart.true_solar
    ? `<div class="panel" style="font-size:12px">
         <b>真太阳时校正</b>：${esc(chart.true_solar.original)} → ${esc(chart.true_solar.corrected)}
         <span class="muted">（${esc(chart.true_solar.correct_date)}，总校正 ${chart.true_solar.total_minute} 分 =
         经度差 ${chart.true_solar.lon_diff} + 均时差 ${chart.true_solar.equation}）</span>
       </div>`
    : '';

  // 古籍参照逐条展开；规则匹配的十神/日柱断语收拢为一组，避免二十多个同构折叠行。
  const allNotes = chart.notes || [];
  const classicNotes = allNotes.filter((note) => String(note.source || '').startsWith('《'));
  const ruleNotes = allNotes.filter((note) => !String(note.source || '').startsWith('《'));
  const classicAccordions = classicNotes
    .map((note) => accordion(note.title, note.body, note.source))
    .join('');
  // 上游断语正文首行往往重复标题，分组时去掉，避免同一句出现两次。
  const compactNote = (note) => {
    const lines = String(note.body || '').split('\n');
    if (lines.length > 1 && lines[0].trim() === String(note.title).trim()) lines.shift();
    return lines.join('\n');
  };
  const ruleAccordion = ruleNotes.length
    ? accordion(
        `十神与日柱断语 · ${ruleNotes.length} 条`,
        ruleNotes.map((note) => `◆ ${note.title}\n${compactNote(note)}`).join('\n\n'),
        '规则匹配'
      )
    : '';
  const dayunNotes = (chart.dayun_notes || []).join('\n');
  const liunianNotes = (chart.liunian_notes || []).join('\n');
  const sanming = (chart.sanming || []).join('\n');

  container.innerHTML = `
    <header class="result-head">
      <div class="result-title">
        <h2>${esc(name)}</h2>
        <div class="result-meta">
          <span class="pill">公历 ${esc(chart.input.solar)}</span>
          <span class="pill">农历 ${esc(chart.lunar)}</span>
          <span class="pill">生肖 ${esc(chart.shengxiao)}</span>
          <span class="pill">日主 ${esc(chart.day_master)}</span>
          <span class="pill">${esc(chart.input.time_basis)}</span>
          ${record ? `<span class="pill">已存于 ${esc(record.created_at)}</span>` : ''}
        </div>
      </div>
    </header>

    ${trueSolar}

    <section class="section">
      <div class="section-head"><h3>四柱</h3><span class="hint">年 · 月 · 日 · 时，晚子时已按次日日柱处理</span></div>
      <div class="pillar-grid">${(chart.pillars || []).map(pillarCard).join('')}</div>
      <div class="section-head"><span class="hint">胎元 ${esc(chart.taiyuan || '—')} · 命宫 ${esc(chart.minggong || '—')} · 身宫 ${esc(chart.shengong || '—')}</span></div>
    </section>

    <section class="section">
      <div class="section-head"><h3>结构分析</h3><span class="hint">格局与用神为规则推演，非确定性结论</span></div>
      ${metrics(chart)}
      <div class="panel">
        <div class="section-head" style="margin-bottom:10px">
          <h3 style="font-size:11px">五行结构计数</h3>
          <span class="hint">四干 + 四支本气共 8 字，条长按本盘最大值归一化</span>
        </div>
        ${elementBars(chart.elements)}
      </div>
      ${accordion('旺衰细节', (chart.strength.detail || []).join('\n'), '规则推演')}
      ${accordion('格局说明', `${chart.geju.name}（${chart.geju.kind}）\n${chart.geju.note}\n\n用神方法：${chart.yongshen.method}\n通关：${chart.yongshen.bridge || '—'}`, '规则推演')}
    </section>

    <section class="section">
      <div class="section-head"><h3>刑冲合会</h3><span class="hint">按四柱干支两两与三支判定</span></div>
      ${relationChips(chart.relations)}
    </section>

    <section class="section">
      <div class="section-head"><h3>神煞</h3><span class="hint">查法口径与现役网页一致</span></div>
      ${shenshaChips(chart.shensha)}
    </section>

    <section class="section">
      <div class="section-head"><h3>大运</h3><span class="hint">起运 ${esc(chart.dayun.start_years)} 年 ${esc(chart.dayun.start_months)} 个月，交运 ${esc(chart.dayun.jiaoyun || '—')}</span></div>
      ${dayunTrack(chart)}
    </section>

    <section class="section">
      <div class="section-head"><h3>流年</h3><span class="hint">自当前年份起 5 年</span></div>
      ${liunianTrack(chart)}
    </section>

    <section class="section">
      <div class="section-head"><h3>参照与断语</h3><span class="hint">古籍参照 / 规则匹配 / 实验模型分层标识</span></div>
      ${classicAccordions}
      ${ruleAccordion}
      ${dayunNotes ? accordion('运年断语（规则匹配）', dayunNotes, '规则匹配') : ''}
      ${sanming ? accordion('《三命通会》大运流年参照', sanming, '古籍参照') : ''}
      ${liunianNotes ? accordion('流年速览', liunianNotes, '规则匹配') : ''}
    </section>

    <p class="page-foot" style="border:0;padding:0;margin:0">
      以上内容由本地规则与古籍参照生成，仅供文化研究与娱乐体验，不构成任何人生或决策建议。
    </p>
  `;
  container.hidden = false;
  $('#empty-state').hidden = true;
  $('#page-title').textContent = '命盘结果';
  $('#page-sub').textContent = `${chart.input.original} · ${chart.input.time_basis}`;
  $('#save-chart').disabled = Boolean(record);
  $('#export-md').disabled = false;
  $('#export-txt').disabled = false;
  requestAnimationFrame(() => {
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

function resetResult() {
  state.chart = null;
  state.record = null;
  $('#result').hidden = true;
  $('#result').innerHTML = '';
  $('#empty-state').hidden = false;
  $('#page-title').textContent = '新建命盘';
  $('#page-sub').textContent = '本地四柱排盘与传统命理参照，不宣称任何确定性结论。';
  $('#save-chart').disabled = true;
  $('#export-md').disabled = true;
  $('#export-txt').disabled = true;
  $$('.history-item').forEach((item) => item.classList.remove('is-active'));
}

/* ---------- 历史 ---------- */

const DAY_LABEL = (isoDate) => {
  const now = new Date();
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  const yesterday = new Date(now.getTime() - 86400000);
  const yest = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, '0')}-${String(yesterday.getDate()).padStart(2, '0')}`;
  if (isoDate === today) return '今天';
  if (isoDate === yest) return '昨天';
  return isoDate;
};

function renderHistory(items) {
  const list = $('#history-list');
  const empty = $('#history-empty');
  $('#history-count').textContent = String(items.length);
  if (!items.length) {
    list.innerHTML = '';
    empty.hidden = false;
    empty.innerHTML = state.query
      ? '没有匹配的历史记录。'
      : '还没有保存的命盘。<br />排盘后点右上角「保存」，记录会写进本机 SQLite。';
    return;
  }
  empty.hidden = true;
  const groups = new Map();
  for (const item of items) {
    const day = (item.created_at || '').slice(0, 10);
    if (!groups.has(day)) groups.set(day, []);
    groups.get(day).push(item);
  }
  list.innerHTML = Array.from(groups.entries())
    .map(([day, rows]) => {
      const header = `<div class="history-group">${esc(DAY_LABEL(day))}</div>`;
      const body = rows
        .map(
          (item) => `
        <div class="history-item${state.record && state.record.id === item.id ? ' is-active' : ''}" role="button" tabindex="0" data-id="${esc(item.id)}">
          <div class="history-title">${esc(item.title)}</div>
          <div class="history-meta">
            <span class="history-gz">${esc(item.pillars)}</span>
            <span>${esc(item.sex)}</span>
          </div>
          <div class="row-actions">
            <button class="icon-btn" data-act="rename" title="重命名" aria-label="重命名"><svg class="icon"><use href="#i-pen" /></svg></button>
            <button class="icon-btn danger" data-act="delete" title="删除" aria-label="删除"><svg class="icon"><use href="#i-trash" /></svg></button>
          </div>
        </div>`
        )
        .join('');
      return header + body;
    })
    .join('');
}

async function loadHistory() {
  try {
    const data = await api(`/api/history?q=${encodeURIComponent(state.query)}`);
    state.items = data.items || [];
    renderHistory(state.items);
  } catch (error) {
    toast(error.message, 'error');
  }
}

async function openRecord(id) {
  try {
    const data = await api(`/api/history/${encodeURIComponent(id)}`);
    const record = data.item;
    state.record = record;
    state.chart = record.chart;
    fillFormFromChart(record.chart);
    renderChart(record.chart, record);
    $$('.history-item').forEach((item) => item.classList.toggle('is-active', item.dataset.id === id));
    $('#save-chart').disabled = true;
  } catch (error) {
    toast(error.message, 'error');
  }
}

function fillFormFromChart(chart) {
  if (!chart || !chart.input) return;
  const solar = (chart.input.solar || '').match(/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})/);
  if (solar) {
    $('#solar-year').value = solar[1];
    $('#solar-month').value = String(Number(solar[2]));
    $('#solar-day').value = String(Number(solar[3]));
    $('#birth-time').value = `${solar[4]}:${solar[5]}`;
    clampSolarDay();
  }
  $('#chart-name').value = chart.input.original || '';
  const sexInput = $(`#sex-seg input[value="${chart.input.sex === '女' ? 0 : 1}"]`);
  if (sexInput) sexInput.checked = true;
  if (chart.input.longitude) {
    $('#longitude').value = String(chart.input.longitude);
    $('#true-solar').checked = Boolean(chart.input.true_solar);
  }
  syncLongitudeSwitch();
  syncAllSegmented();
}

async function saveChart() {
  if (!state.chart || state.busy) return;
  const title = $('#chart-name').value.trim() || state.chart.input.original;
  try {
    const data = await api('/api/history', {
      method: 'POST',
      body: JSON.stringify({ title, note: '', chart: state.chart }),
    });
    state.record = data.item;
    $('#save-chart').disabled = true;
    renderChart(state.chart, state.record);
    await loadHistory();
    toast('已保存到本地历史');
  } catch (error) {
    toast(error.message, 'error');
  }
}

function openModal({ title, body, fields = '', confirmText = '确认', onConfirm }) {
  const root = $('#modal-root');
  root.hidden = false;
  root.innerHTML = `
    <div class="modal" role="dialog" aria-modal="true" aria-label="${esc(title)}">
      <h3>${esc(title)}</h3>
      <p>${esc(body)}</p>
      <div class="modal-fields">${fields}</div>
      <div class="modal-foot">
        <button class="btn btn-ghost" data-close type="button">取消</button>
        <button class="btn btn-primary" data-confirm type="button">${esc(confirmText)}</button>
      </div>
    </div>`;
  const close = () => {
    root.hidden = true;
    root.innerHTML = '';
  };
  $('[data-close]', root).addEventListener('click', close);
  root.addEventListener('click', (event) => {
    if (event.target === root) close();
  });
  $('[data-confirm]', root).addEventListener('click', async () => {
    try {
      await onConfirm(root);
      close();
    } catch (error) {
      toast(error.message, 'error');
    }
  });
  const focusTarget = $('input, textarea', root);
  if (focusTarget) setTimeout(() => focusTarget.focus(), 30);
  return close;
}

function confirmDelete(item) {
  openModal({
    title: '删除这条历史？',
    body: `${item.title}（${item.pillars}）将从本机数据库中移除，此操作不可撤销。`,
    confirmText: '删除',
    onConfirm: async () => {
      await api(`/api/history/${encodeURIComponent(item.id)}`, { method: 'DELETE' });
      if (state.record && state.record.id === item.id) resetResult();
      await loadHistory();
      toast('已删除');
    },
  });
}

function renameRecord(item) {
  openModal({
    title: '重命名与备注',
    body: '仅修改本机记录，不影响命盘数据。',
    fields: `
      <label class="field"><span class="field-label">标题</span>
        <input id="rename-title" type="text" maxlength="60" value="${esc(item.title)}" /></label>
      <label class="field"><span class="field-label">备注</span>
        <textarea id="rename-note" maxlength="500">${esc(item.note || '')}</textarea></label>`,
    confirmText: '保存修改',
    onConfirm: async (root) => {
      const title = $('#rename-title', root).value.trim();
      const note = $('#rename-note', root).value;
      if (!title) throw new Error('标题不能为空');
      await api(`/api/history/${encodeURIComponent(item.id)}`, {
        method: 'PATCH',
        body: JSON.stringify({ title, note }),
      });
      await loadHistory();
      if (state.record && state.record.id === item.id) await openRecord(item.id);
      toast('已更新');
    },
  });
}

async function ensureSaved() {
  if (state.record) return state.record;
  await saveChart();
  return state.record;
}

async function exportChart(format) {
  const record = await ensureSaved();
  if (!record) throw new Error('导出前需要先保存记录');
  window.location.href = `/api/history/${encodeURIComponent(record.id)}/export?format=${format}`;
  toast(`正在导出 ${format.toUpperCase()} 文件`);
}

/* ---------- 事件绑定 ---------- */

function bindEvents() {
  // 主题
  $$('#theme-seg input').forEach((input) =>
    input.addEventListener('change', () => applyTheme(input.value))
  );

  // 分段控件滑块
  $$('.segmented input').forEach((input) =>
    input.addEventListener('change', () => {
      syncSegmented(input.closest('.segmented'));
      if (input.name === 'calendar') {
        toggleCalendarFields();
        if (currentCalendar() === 'lunar') refreshLunarSelects(false);
      }
    })
  );
  window.addEventListener('resize', syncAllSegmented);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(syncAllSegmented);

  // 公历联动
  ['#solar-year', '#solar-month'].forEach((selector) =>
    $(selector).addEventListener('input', clampSolarDay)
  );
  // 农历联动
  $('#lunar-year').addEventListener('change', () => refreshLunarSelects(false));
  $('#lunar-month').addEventListener('change', () => updateLunarDays());

  // 经度与真太阳时
  $('#longitude').addEventListener('input', syncLongitudeSwitch);

  // 出生地折叠
  $('#extra-toggle').addEventListener('click', () => {
    const body = $('#extra-body');
    const open = body.hidden;
    body.hidden = !open;
    $('#extra-toggle').setAttribute('aria-expanded', String(open));
  });

  // CJK 输入法守卫：合成中不触发任何提交
  document.addEventListener('compositionstart', () => {
    state.composing = true;
  });
  document.addEventListener('compositionend', () => {
    state.composing = false;
  });

  $('#chart-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (state.composing || state.busy) return;
    let payload;
    try {
      payload = buildPayload();
    } catch (error) {
      toast(error.message, 'error');
      return;
    }
    setBusy(true);
    try {
      const data = await api('/api/chart', { method: 'POST', body: JSON.stringify(payload) });
      state.chart = data.chart;
      state.record = null;
      renderChart(data.chart, null);
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      setBusy(false);
    }
  });

  // Enter 提交守卫（输入框内回车不直接排盘，避免误触；按钮或 Ctrl/Cmd+Enter 才提交）
  $('#chart-form').addEventListener('keydown', (event) => {
    if (event.key !== 'Enter') return;
    if (event.isComposing || event.keyCode === 229 || state.composing) {
      event.preventDefault();
      return;
    }
    if (event.target.tagName === 'INPUT' && !(event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      $('#submit-btn').focus();
    }
  });

  $('#save-chart').addEventListener('click', () => saveChart().catch((error) => toast(error.message, 'error')));
  $('#export-md').addEventListener('click', () => exportChart('md').catch((error) => toast(error.message, 'error')));
  $('#export-txt').addEventListener('click', () => exportChart('txt').catch((error) => toast(error.message, 'error')));

  $('#new-chart').addEventListener('click', () => {
    resetResult();
    document.body.classList.remove('sidebar-open');
    $('#solar-year').focus();
  });

  // 历史搜索
  let searchTimer = null;
  $('#history-search').addEventListener('input', (event) => {
    state.query = event.target.value.trim();
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadHistory, 160);
  });

  // 历史列表交互（事件委托）
  $('#history-list').addEventListener('click', (event) => {
    const row = event.target.closest('.history-item');
    if (!row) return;
    const action = event.target.closest('[data-act]');
    if (action) {
      event.stopPropagation();
      const item = state.items.find((entry) => entry.id === row.dataset.id);
      if (!item) return;
      if (action.dataset.act === 'delete') confirmDelete(item);
      if (action.dataset.act === 'rename') renameRecord(item);
      return;
    }
    openRecord(row.dataset.id);
  });
  $('#history-list').addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const row = event.target.closest('.history-item');
    if (!row || event.target !== row) return;
    event.preventDefault();
    openRecord(row.dataset.id);
  });

  // 移动端侧栏
  $('#sidebar-toggle').addEventListener('click', () => document.body.classList.toggle('sidebar-open'));
  document.addEventListener('click', (event) => {
    if (!document.body.classList.contains('sidebar-open')) return;
    if (event.target.closest('.sidebar') || event.target.closest('#sidebar-toggle')) return;
    document.body.classList.remove('sidebar-open');
  });

  // 关于
  $('#about-btn').addEventListener('click', async () => {
    let health = {};
    try {
      health = await api('/api/health');
    } catch {
      health = {};
    }
    openModal({
      title: '观象桌面版',
      body: '',
      fields: `<div class="muted" style="font-size:12px;line-height:1.9">
        <div>版本：${esc(health.version || '1.0.0')}</div>
        <div style="overflow-wrap:anywhere">数据库：${esc(health.history_db || '—')}</div>
      </div>`,
      confirmText: '知道了',
      onConfirm: async () => {},
    });
  });

  // Esc 关闭弹层
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const root = $('#modal-root');
    if (!root.hidden) {
      root.hidden = true;
      root.innerHTML = '';
    }
    document.body.classList.remove('sidebar-open');
  });

  // 滚动渐隐
  const scroll = $('#scroll');
  const updateFade = () => {
    const top = scroll.scrollTop;
    const bottom = scroll.scrollHeight - scroll.clientHeight - top;
    scroll.style.setProperty('--cds-scroll-fade-top', `${Math.min(24, top)}px`);
    scroll.style.setProperty('--cds-scroll-fade-bottom', `${Math.min(24, Math.max(0, bottom))}px`);
    scroll.classList.toggle('has-fade-top', top > 2);
    scroll.classList.toggle('has-fade-bottom', bottom > 2);
  };
  scroll.addEventListener('scroll', updateFade, { passive: true });
  window.addEventListener('resize', updateFade);
  updateFade();
}

/* ---------- 启动 ---------- */

async function bootstrap() {
  applyTheme(localStorage.getItem('guanxiang-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  bindEvents();
  clampSolarDay();
  syncLongitudeSwitch();
  toggleCalendarFields();
  await refreshLunarSelects(false);
  syncAllSegmented();

  try {
    const health = await api('/api/health');
    $('#version-pill').textContent = `v${health.version || '1.0.0'}`;
    $('#local-note').title = `历史库：${health.history_db || '—'}`;
  } catch {
    /* 健康检查失败不阻塞界面 */
  }
  await loadHistory();

  // 心跳：窗口关闭后主进程据此退出
  const ping = () => fetch('/api/ping', { method: 'POST' }).catch(() => {});
  ping();
  setInterval(ping, 4000);
}

document.addEventListener('DOMContentLoaded', bootstrap);
