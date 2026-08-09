const form = document.querySelector('#chart-form');
const resultShell = document.querySelector('#result-shell');
const statusLine = document.querySelector('#form-status');
const submitButton = form.querySelector('.submit-button');
const defaultButtonContent = submitButton.innerHTML;
const locationSearch = document.querySelector('#location-search');
const placeResults = document.querySelector('#place-results');
const longitudeInput = document.querySelector('#longitude');
const latitudeInput = document.querySelector('#latitude');
const locationStatus = document.querySelector('#location-status');

let locations = [];
let selectedPlace = null;
let lunarYearInfo = null;

const GAN_ELEMENT = {
  甲: ['木', '阳'], 乙: ['木', '阴'], 丙: ['火', '阳'], 丁: ['火', '阴'],
  戊: ['土', '阳'], 己: ['土', '阴'], 庚: ['金', '阳'], 辛: ['金', '阴'],
  壬: ['水', '阳'], 癸: ['水', '阴'],
};
const ELEMENT_COLORS = { 木: '#3f7452', 火: '#b64a36', 土: '#a47935', 金: '#77766e', 水: '#285d6d' };
const MONTH_NAMES = ['正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月'];
const DAY_NAMES = ['初一','初二','初三','初四','初五','初六','初七','初八','初九','初十','十一','十二','十三','十四','十五','十六','十七','十八','十九','二十','廿一','廿二','廿三','廿四','廿五','廿六','廿七','廿八','廿九','三十'];
const LEVEL_NAMES = ['省级', '市级', '区县'];

const escapeHTML = (value = '') => String(value)
  .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
const cleanText = (value = '') => String(value).replaceAll('\r', '\n').replace(/\n{3,}/g, '\n\n').trim();

init();

async function init() {
  fillLunarSelects();
  syncCalendarMode();
  try {
    const response = await fetch('/locations.json');
    if (!response.ok) throw new Error('地点数据加载失败');
    locations = await response.json();
  } catch (error) {
    locationStatus.innerHTML = `<i></i> ${escapeHTML(error.message)}，仍可手动填写经度`;
  }
}

function fillLunarSelects() {
  document.querySelector('#lunar-month').innerHTML = MONTH_NAMES.map((name, index) => `<option value="${index + 1}"${index === 3 ? ' selected' : ''}>${name}</option>`).join('');
  document.querySelector('#lunar-day').innerHTML = DAY_NAMES.map((name, index) => `<option value="${index + 1}"${index === 20 ? ' selected' : ''}>${name}</option>`).join('');
}

form.elements.calendar.forEach((radio) => radio.addEventListener('change', syncCalendarMode));

async function syncCalendarMode() {
  const lunarMode = form.elements.calendar.value === 'lunar';
  const solarPanel = document.querySelector('#solar-panel');
  const lunarPanel = document.querySelector('#lunar-panel');
  solarPanel.hidden = lunarMode;
  lunarPanel.hidden = !lunarMode;
  document.querySelector('#birth-date').disabled = lunarMode;
  ['#lunar-year', '#lunar-month', '#lunar-day'].forEach((selector) => {
    document.querySelector(selector).disabled = !lunarMode;
  });
  if (lunarMode) await updateLunarYear();
}

document.querySelector('#lunar-year').addEventListener('change', updateLunarYear);
document.querySelector('#lunar-month').addEventListener('change', updateLeapState);
document.querySelector('#lunar-leap').addEventListener('change', updateLunarDays);

async function updateLunarYear() {
  const year = Number(document.querySelector('#lunar-year').value);
  if (year < 1900 || year > 2099) return;
  try {
    const response = await fetch(`/api/lunar-year?year=${year}`);
    const data = await response.json();
    if (!data.ok) throw new Error(data.error);
    lunarYearInfo = data;
    updateLeapState();
  } catch (error) {
    statusLine.textContent = error.message;
  }
}

function updateLeapState() {
  if (!lunarYearInfo) return;
  const month = Number(document.querySelector('#lunar-month').value);
  const leapInput = document.querySelector('#lunar-leap');
  const leapToggle = leapInput.closest('.leap-toggle');
  const isLeapMonth = lunarYearInfo.leap_month === month;
  leapInput.disabled = !isLeapMonth;
  if (!isLeapMonth) leapInput.checked = false;
  leapToggle.classList.toggle('disabled', !isLeapMonth);
  document.querySelector('#leap-note').textContent = lunarYearInfo.leap_month
    ? (isLeapMonth ? `本年闰${MONTH_NAMES[month - 1]}` : `本年闰${MONTH_NAMES[lunarYearInfo.leap_month - 1]}`)
    : '该年无闰月';
  updateLunarDays();
}

function updateLunarDays() {
  if (!lunarYearInfo) return;
  const month = Number(document.querySelector('#lunar-month').value);
  const isLeap = document.querySelector('#lunar-leap').checked;
  const signedMonth = isLeap ? -month : month;
  const monthInfo = lunarYearInfo.months.find((item) => item.month === signedMonth);
  if (!monthInfo) return;
  const daySelect = document.querySelector('#lunar-day');
  const previous = Number(daySelect.value) || 1;
  daySelect.innerHTML = DAY_NAMES.slice(0, monthInfo.days)
    .map((name, index) => `<option value="${index + 1}">${name}</option>`).join('');
  daySelect.value = String(Math.min(previous, monthInfo.days));
}

document.querySelector('#location-help').addEventListener('click', (event) => {
  const hint = document.querySelector('#location-hint');
  const visible = hint.classList.toggle('visible');
  event.currentTarget.setAttribute('aria-expanded', String(visible));
});

locationSearch.addEventListener('input', () => {
  if (selectedPlace && locationSearch.value !== selectedPlace.path) clearCoordinates(false);
  renderPlaceResults(locationSearch.value.trim());
});

locationSearch.addEventListener('focus', () => renderPlaceResults(locationSearch.value.trim()));
document.addEventListener('click', (event) => {
  if (!event.target.closest('.location-field')) placeResults.hidden = true;
});

function renderPlaceResults(query) {
  if (!query) {
    placeResults.hidden = true;
    return;
  }
  if (!locations.length) {
    placeResults.innerHTML = '<p class="place-empty">地点索引正在加载，请稍候</p>';
    placeResults.hidden = false;
    return;
  }
  const matches = locations
    .filter((place) => place.name.includes(query) || place.path.includes(query))
    .map((place) => ({
      ...place,
      score: place.name === query ? 0 : place.name.startsWith(query) ? 1 : place.path.includes(` ${query}`) ? 2 : 3,
    }))
    .sort((a, b) => a.score - b.score || b.level - a.level || a.path.length - b.path.length)
    .slice(0, 9);

  if (!matches.length) {
    placeResults.innerHTML = '<p class="place-empty">未找到该地点，可尝试输入完整区县名</p>';
  } else {
    placeResults.innerHTML = matches.map((place, index) => `
      <button class="place-option" type="button" data-index="${index}">
        <span><b>${escapeHTML(place.name)}</b><span>${escapeHTML(place.path)}</span></span>
        <small>${LEVEL_NAMES[place.level] || '行政区'}</small>
      </button>`).join('');
    placeResults.querySelectorAll('.place-option').forEach((button) => {
      button.addEventListener('click', () => selectPlace(matches[Number(button.dataset.index)]));
    });
  }
  placeResults.hidden = false;
}

function selectPlace(place) {
  selectedPlace = place;
  locationSearch.value = place.path;
  longitudeInput.value = place.longitude;
  latitudeInput.value = place.latitude;
  placeResults.hidden = true;
  document.querySelector('#clear-location').hidden = false;
  locationStatus.classList.add('selected');
  locationStatus.innerHTML = `<i></i> 已定位 ${escapeHTML(place.path)} · ${place.longitude.toFixed(4)}° E`;
}

document.querySelector('#clear-location').addEventListener('click', () => {
  locationSearch.value = '';
  clearCoordinates(true);
  locationSearch.focus();
});

function clearCoordinates(clearSearch) {
  selectedPlace = null;
  longitudeInput.value = '';
  latitudeInput.value = '';
  if (clearSearch) locationSearch.value = '';
  document.querySelector('#clear-location').hidden = true;
  locationStatus.classList.remove('selected');
  locationStatus.innerHTML = '<i></i> 未选择地点，将使用标准时间排盘';
}

[longitudeInput, latitudeInput].forEach((input) => input.addEventListener('input', () => {
  if (!longitudeInput.value) {
    locationStatus.classList.remove('selected');
    locationStatus.innerHTML = '<i></i> 未填写经度，将使用标准时间排盘';
    return;
  }
  locationStatus.classList.add('selected');
  locationStatus.innerHTML = `<i></i> 将按经度 ${escapeHTML(longitudeInput.value)}° 校正真太阳时`;
}));

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusLine.textContent = '';
  submitButton.disabled = true;
  submitButton.innerHTML = document.querySelector('#loading-template').innerHTML;
  const calendar = form.elements.calendar.value;
  const payload = {
    calendar,
    date: document.querySelector('#birth-date').value,
    lunar_year: Number(document.querySelector('#lunar-year').value),
    lunar_month: Number(document.querySelector('#lunar-month').value),
    lunar_day: Number(document.querySelector('#lunar-day').value),
    lunar_leap: document.querySelector('#lunar-leap').checked,
    time: document.querySelector('#birth-time').value,
    sex: Number(form.elements.sex.value),
    location_name: selectedPlace?.path || (longitudeInput.value ? locationSearch.value.trim() : ''),
    longitude: longitudeInput.value,
    latitude: latitudeInput.value,
  };
  try {
    const response = await fetch('/api/chart', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || '暂时无法完成排盘');
    renderChart(data.chart);
    resultShell.hidden = false;
    requestAnimationFrame(() => {
      document.querySelectorAll('.reveal').forEach((item, index) => {
        item.classList.remove('visible');
        item.style.animationDelay = `${Math.min(index * 70, 350)}ms`;
        requestAnimationFrame(() => item.classList.add('visible'));
      });
      resultShell.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  } catch (error) {
    statusLine.textContent = error.message;
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = defaultButtonContent;
  }
});

function renderChart(chart) {
  renderHeading(chart); renderPillars(chart); renderSummary(chart);
  renderRelations(chart['刑冲合会'] || []); renderCycles(chart['大运'] || [], chart['起运']);
  renderSymbols(chart['神煞'] || []); renderAnalysis(chart['分析'] || []);
}

function renderHeading(chart) {
  const lunar = cleanText(chart['农历']);
  const shortLunar = lunar.replace(/^[〇零一二三四五六七八九]{4}年/, '');
  document.querySelector('#chart-title').textContent = `${chart['四柱']['年']['干支']}年 · ${shortLunar}`;
  const source = chart['输入']['历法'] === '农历'
    ? `农历输入 <strong>${escapeHTML(chart['输入']['原始日期'])}</strong><br>换算公历 ${escapeHTML(chart['输入']['公历'])}`
    : `公历输入 <strong>${escapeHTML(chart['输入']['公历'])}</strong>`;
  const location = chart['出生地']
    ? `<br><span class="meta-location">${escapeHTML(chart['出生地']['名称'])} · ${chart['出生地']['经度'].toFixed(4)}° E</span>`
    : '<br><span>未填写出生地 · 标准时间</span>';
  document.querySelector('#chart-meta').innerHTML = `${source}<br>${escapeHTML(chart['输入']['性别'])} · 生肖 ${escapeHTML(chart['生肖'])}${location}`;
}

function renderPillars(chart) {
  const subtitles = { 年: '根基', 月: '提纲', 日: '命元', 时: '归宿' };
  document.querySelector('#pillar-chart').innerHTML = ['年', '月', '日', '时'].map((name) => {
    const pillar = chart['四柱'][name];
    const hidden = (pillar['藏干'] || []).join(' · ');
    const hiddenGods = (pillar['十神(藏干)'] || []).join(' · ');
    return `<article class="pillar"><div class="pillar-label">${name}柱 · ${subtitles[name]}</div><div class="pillar-gz"><span>${escapeHTML(pillar['天干'])}</span><span>${escapeHTML(pillar['地支'])}</span></div><div class="pillar-ten">${escapeHTML(pillar['十神(天干)'])}</div><dl class="pillar-detail"><div><dt>藏干</dt><dd title="${escapeHTML(hiddenGods)}">${escapeHTML(hidden)}</dd></div><div><dt>纳音</dt><dd>${escapeHTML(pillar['纳音'])}</dd></div><div><dt>长生</dt><dd>${escapeHTML(pillar['长生'])}</dd></div><div><dt>空亡</dt><dd>${escapeHTML((pillar['空亡'] || []).join(''))}</dd></div></dl></article>`;
  }).join('');
}

function renderSummary(chart) {
  const dayMaster = chart['日主'];
  const [element, polarity] = GAN_ELEMENT[dayMaster] || ['', ''];
  document.querySelector('#day-master').textContent = dayMaster;
  document.querySelector('#day-master-element').textContent = `${polarity}${element}`;
  document.querySelector('#mini-facts').innerHTML = `<span>胎元 <b>${escapeHTML(chart['胎元'] || '—')}</b></span><span>命宫 <b>${escapeHTML(chart['命宫'] || '—')}</b></span><span>生肖 <b>${escapeHTML(chart['生肖'])}</b></span>`;
  renderElements(chart);
  const solarCard = document.querySelector('#solar-card');
  const solar = chart['真太阳时'];
  solarCard.classList.toggle('uncorrected', !solar);
  if (solar) {
    document.querySelector('#solar-original').textContent = solar['原时间'];
    document.querySelector('#solar-corrected').textContent = solar['校正后'];
    const sign = Number(solar['总校正分']) > 0 ? '+' : '';
    document.querySelector('#solar-correction').textContent = `按出生地经度与均时差，共校正 ${sign}${solar['总校正分']} 分钟`;
  } else {
    document.querySelector('#solar-original').textContent = chart['输入']['公历'].slice(-5);
    document.querySelector('#solar-corrected').textContent = '未校正';
    document.querySelector('#solar-correction').textContent = '出生地为选填项；未填写时保留输入的标准时间。';
  }
}

function renderElements(chart) {
  const count = { 木: 0, 火: 0, 土: 0, 金: 0, 水: 0 };
  Object.values(chart['四柱']).forEach((pillar) => {
    if (count[pillar['干五行']] !== undefined) count[pillar['干五行']] += 1;
    if (count[pillar['支五行']] !== undefined) count[pillar['支五行']] += 1;
    (pillar['藏干五行'] || []).forEach((element) => { if (count[element] !== undefined) count[element] += 1; });
  });
  const max = Math.max(...Object.values(count), 1);
  const container = document.querySelector('#element-balance');
  container.innerHTML = Object.entries(count).map(([element, amount]) => `<div class="element-row" style="--element-color:${ELEMENT_COLORS[element]}"><b>${element}</b><div class="element-bar"><i data-width="${(amount / max) * 100}%"></i></div><span>${amount}</span></div>`).join('');
  requestAnimationFrame(() => container.querySelectorAll('.element-bar i').forEach((bar) => { bar.style.width = bar.dataset.width; }));
}

function renderRelations(relations) {
  const list = document.querySelector('#relation-list');
  if (!relations.length) { list.innerHTML = '<p class="empty-state">四柱之间未检出明显的刑冲合会关系</p>'; return; }
  list.innerHTML = relations.map(([kind, where, stems, note], index) => `<article class="relation-item"><div class="relation-kind"><i>${index + 1}</i>${escapeHTML(kind)}</div><p><strong>${escapeHTML(where)}</strong> · ${escapeHTML(stems)}<br>${escapeHTML(note)}</p></article>`).join('');
}

function renderCycles(cycles, startAge) {
  const useful = cycles.filter((cycle) => cycle && cycle['干支']);
  document.querySelector('#cycle-note').textContent = `起运 ${startAge ?? '—'} 岁 · 左右滑动查看`;
  const currentYear = new Date().getFullYear();
  document.querySelector('#cycle-track').innerHTML = useful.slice(0, 10).map((cycle) => {
    const active = currentYear >= cycle['起年'] && currentYear <= cycle['终年'];
    return `<article class="cycle${active ? ' active' : ''}"><span class="cycle-index">第 ${escapeHTML(cycle['序'])} 运${active ? ' · 当下' : ''}</span><strong>${escapeHTML(cycle['干支'])}</strong><p>${escapeHTML(cycle['年龄'])} 岁<br>${escapeHTML(cycle['起年'])}—${escapeHTML(cycle['终年'])}</p></article>`;
  }).join('');
}

function renderSymbols(symbols) {
  document.querySelector('#shensha-count').textContent = symbols.length;
  document.querySelector('#symbol-list').innerHTML = symbols.length ? symbols.map(([name, where, detail]) => `<div class="symbol"><b>${escapeHTML(name)}</b><span>${escapeHTML(where)}</span><small>${escapeHTML(detail || '古法标记')}</small></div>`).join('') : '<p class="empty-state">未检出神煞标记</p>';
}

function renderAnalysis(analysis) {
  const container = document.querySelector('#analysis-list');
  container.innerHTML = analysis.slice(0, 12).map(([title, body], index) => `<article class="analysis-item${index === 0 ? ' open' : ''}"><button type="button" aria-expanded="${index === 0}"><span>${escapeHTML(title)}</span><i aria-hidden="true"></i></button><div class="analysis-body">${escapeHTML(cleanText(body))}</div></article>`).join('');
  container.querySelectorAll('.analysis-item button').forEach((button) => button.addEventListener('click', () => {
    const item = button.closest('.analysis-item'); const open = item.classList.toggle('open'); button.setAttribute('aria-expanded', String(open));
  }));
}
