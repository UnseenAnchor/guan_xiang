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
const trueSolarInput = document.querySelector('#use-true-solar-time');

let locations = [];
let selectedPlace = null;
let lunarYearInfo = null;
let currentChart = null;
let currentChartPayload = null;

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

async function readJsonResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    if (response.status === 404) {
      throw new Error('服务端接口尚未更新，请重启 python web_server.py 后刷新页面');
    }
    throw new Error(`服务端返回了非 JSON 响应（HTTP ${response.status}），请重启服务后重试`);
  }
  try {
    return await response.json();
  } catch (_error) {
    throw new Error('服务端返回的数据格式异常，请重启服务后重试');
  }
}

init();

async function init() {
  initializeChapterNav();
  fillSolarSelects();
  fillLunarSelects();
  syncCalendarMode();
  try {
    const response = await fetch('/locations.json');
    if (!response.ok) throw new Error('地点数据加载失败');
    locations = await readJsonResponse(response);
  } catch (error) {
    locationStatus.innerHTML = `<i></i> ${escapeHTML(error.message)}，仍可手动填写经度`;
  }
}

function initializeChapterNav() {
  const links = [...document.querySelectorAll('.chart-nav a[href^="#"]')];
  const sections = links.map((link) => document.querySelector(link.getAttribute('href'))).filter(Boolean);
  const setActive = (id) => links.forEach((link) => {
    const active = link.getAttribute('href') === `#${id}`;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
  links.forEach((link) => link.addEventListener('click', (event) => {
    event.preventDefault();
    const target = document.querySelector(link.getAttribute('href'));
    if (!target) return;
    setActive(target.id);
    target.scrollIntoView({
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
      block: 'start',
    });
    history.replaceState(null, '', link.hash);
  }));
  if (!('IntersectionObserver' in window)) return;
  const observer = new IntersectionObserver((entries) => {
    const visible = entries.filter((entry) => entry.isIntersecting)
      .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
    if (visible) setActive(visible.target.id);
  }, { rootMargin: '-12% 0px -68% 0px', threshold: 0 });
  sections.forEach((section) => observer.observe(section));
}

function fillSolarSelects() {
  document.querySelector('#solar-month').innerHTML = Array.from(
    { length: 12 },
    (_, index) => `<option value="${index + 1}"${index === 4 ? ' selected' : ''}>${index + 1}月</option>`,
  ).join('');
  updateSolarDays(15);
}

function updateSolarDays(defaultDay) {
  const year = Number(document.querySelector('#solar-year').value);
  const month = Number(document.querySelector('#solar-month').value);
  if (year < 1900 || year > 2099 || month < 1 || month > 12) return;
  const daySelect = document.querySelector('#solar-day');
  const previous = Number(daySelect.value) || defaultDay || 1;
  const days = new Date(year, month, 0).getDate();
  daySelect.innerHTML = Array.from(
    { length: days },
    (_, index) => `<option value="${index + 1}">${index + 1}日</option>`,
  ).join('');
  daySelect.value = String(Math.min(previous, days));
}

function solarDateValue() {
  const pad = (value) => String(value).padStart(2, '0');
  return `${document.querySelector('#solar-year').value}-${pad(document.querySelector('#solar-month').value)}-${pad(document.querySelector('#solar-day').value)}`;
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
  ['#solar-year', '#solar-month', '#solar-day'].forEach((selector) => {
    document.querySelector(selector).disabled = lunarMode;
  });
  ['#lunar-year', '#lunar-month', '#lunar-day'].forEach((selector) => {
    document.querySelector(selector).disabled = !lunarMode;
  });
  if (lunarMode) await updateLunarYear();
}

document.querySelector('#solar-year').addEventListener('input', () => updateSolarDays());
document.querySelector('#solar-month').addEventListener('change', () => updateSolarDays());
document.querySelector('#lunar-year').addEventListener('change', updateLunarYear);
document.querySelector('#lunar-month').addEventListener('change', updateLeapState);
document.querySelector('#lunar-leap').addEventListener('change', updateLunarDays);

async function updateLunarYear() {
  const year = Number(document.querySelector('#lunar-year').value);
  if (year < 1900 || year > 2099) return;
  try {
    const response = await fetch(`/api/lunar-year?year=${year}`);
    const data = await readJsonResponse(response);
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
  syncLocationStatus();
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
  trueSolarInput.checked = false;
  if (clearSearch) locationSearch.value = '';
  document.querySelector('#clear-location').hidden = true;
  locationStatus.classList.remove('selected');
  locationStatus.innerHTML = '<i></i> 未选择地点，将使用标准时间排盘';
}

function syncLocationStatus() {
  if (!longitudeInput.value) {
    locationStatus.classList.remove('selected');
    locationStatus.innerHTML = '<i></i> 未填写经度，将使用标准时间排盘';
    return;
  }
  locationStatus.classList.add('selected');
  const place = selectedPlace ? `已定位 ${escapeHTML(selectedPlace.path)}` : `已记录经度 ${escapeHTML(longitudeInput.value)}°`;
  const mode = trueSolarInput.checked ? '将用于真太阳时校正' : '真太阳时未启用';
  locationStatus.innerHTML = `<i></i> ${place} · ${mode}`;
}

[longitudeInput, latitudeInput].forEach((input) => input.addEventListener('input', () => {
  selectedPlace = null;
  syncLocationStatus();
}));

trueSolarInput.addEventListener('change', () => {
  syncLocationStatus();
  if (trueSolarInput.checked && !longitudeInput.value) {
    statusLine.textContent = '启用真太阳时前，请先选择出生地或填写经度。';
  } else {
    statusLine.textContent = '';
  }
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusLine.textContent = '';
  submitButton.disabled = true;
  submitButton.innerHTML = document.querySelector('#loading-template').innerHTML;
  const calendar = form.elements.calendar.value;
  const payload = {
    calendar,
    date: solarDateValue(),
    lunar_year: Number(document.querySelector('#lunar-year').value),
    lunar_month: Number(document.querySelector('#lunar-month').value),
    lunar_day: Number(document.querySelector('#lunar-day').value),
    lunar_leap: document.querySelector('#lunar-leap').checked,
    time: document.querySelector('#birth-time').value,
    sex: Number(form.elements.sex.value),
    location_name: selectedPlace?.path || (longitudeInput.value ? locationSearch.value.trim() : ''),
    longitude: longitudeInput.value,
    latitude: latitudeInput.value,
    use_true_solar_time: trueSolarInput.checked,
    timezone: 'Asia/Shanghai',
  };
  try {
    const response = await fetch('/api/chart', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
    const data = await readJsonResponse(response);
    if (!response.ok || !data.ok) throw new Error(data.error || '暂时无法完成排盘');
    currentChart = data.chart;
    currentChartPayload = payload;
    renderChart(data.chart);
    resultShell.hidden = false;
    requestAnimationFrame(() => {
      document.querySelectorAll('.reveal').forEach((item, index) => {
        item.classList.remove('visible');
        item.style.animationDelay = `${Math.min(index * 70, 350)}ms`;
        requestAnimationFrame(() => item.classList.add('visible'));
      });
      resultShell.scrollIntoView({
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
        block: 'start',
      });
    });
  } catch (error) {
    statusLine.textContent = error.message;
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = defaultButtonContent;
  }
});

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

function renderSummary(chart) {
  const dayMaster = chart['日主'];
  const [element, polarity] = GAN_ELEMENT[dayMaster] || ['', ''];
  document.querySelector('#day-master').textContent = dayMaster;
  document.querySelector('#day-master-element').textContent = `${polarity}${element}`;
  document.querySelector('#mini-facts').innerHTML = `<span>胎元 <b>${escapeHTML(chart['胎元'] || '—')}</b></span><span>命宫 <b>${escapeHTML(chart['命宫'] || '—')}</b></span><span>身宫 <b>${escapeHTML(chart['身宫'] || '—')}</b></span><span>生肖 <b>${escapeHTML(chart['生肖'])}</b></span>`;
  renderElements(chart);
  const solarCard = document.querySelector('#solar-card');
  const solar = chart['真太阳时'];
  const comparison = chart['时间对比'];
  const mode = chart['排盘口径'] || {};
  const comparisonPanel = document.querySelector('#solar-comparison');
  solarCard.classList.toggle('uncorrected', !solar);
  if (solar) {
    document.querySelector('#time-mode-title').textContent = '真太阳时排盘';
    document.querySelector('#solar-original').textContent = comparison?.['标准日期时间'] || solar['原时间'];
    document.querySelector('#solar-corrected').textContent = comparison?.['真太阳日期时间'] || solar['校正后'];
    const sign = Number(solar['总校正分']) > 0 ? '+' : '';
    document.querySelector('#solar-correction').textContent = `按出生地经度与均时差，共校正 ${sign}${solar['总校正分']} 分钟`;
    const changed = comparison?.['变化柱'] || [];
    if (changed.length) {
      comparisonPanel.innerHTML = `<b>校正改变了${escapeHTML(changed.join('、'))}柱</b>${changed.map((name) => {
        const before = comparison['标准四柱'][name];
        const after = comparison['真太阳时四柱'][name];
        return `<span>${escapeHTML(name)}柱 ${escapeHTML(before)} → ${escapeHTML(after)}</span>`;
      }).join('')}`;
    } else {
      comparisonPanel.innerHTML = '<b>校正未改变四柱</b><span>校正后的时间仍处于相同排盘口径边界内</span>';
    }
    comparisonPanel.hidden = false;
  } else {
    document.querySelector('#time-mode-title').textContent = '标准时间排盘';
    document.querySelector('#solar-original').textContent = chart['输入']['公历'].slice(-5);
    document.querySelector('#solar-corrected').textContent = '未校正';
    document.querySelector('#solar-correction').textContent = mode['说明'] || '按出生记录中的标准时间排盘。';
    comparisonPanel.hidden = true;
    comparisonPanel.innerHTML = '';
  }
}

function renderRelations(relations) {
  const list = document.querySelector('#relation-list');
  if (!relations.length) { list.innerHTML = '<p class="empty-state">四柱之间未检出明显的刑冲合会关系</p>'; return; }
  list.innerHTML = relations.map(([kind, where, stems, note], index) => `<article class="relation-item"><div class="relation-kind"><i>${index + 1}</i>${escapeHTML(kind)}</div><p><strong>${escapeHTML(where)}</strong> · ${escapeHTML(stems)}<br>${escapeHTML(note)}</p></article>`).join('');
}

function renderSymbols(symbols) {
  document.querySelector('#shensha-count').textContent = symbols.length;
  document.querySelector('#symbol-list').innerHTML = symbols.length ? symbols.map(([name, where, detail]) => `<div class="symbol"><b>${escapeHTML(name)}</b><span>${escapeHTML(where)}</span><small>${escapeHTML(detail || '古法标记')}</small></div>`).join('') : '<p class="empty-state">未检出神煞标记</p>';
}

function renderChart(chart) {
  renderHeading(chart);
  renderPillars(chart);
  renderSummary(chart);
  renderRelations(chart['刑冲合会'] || []);
  renderExperimental(chart['实验推演']);
  renderCycles(chart['大运'] || [], chart['起运'], chart['起运详情'], chart['运年断语'] || {});
  renderAnnualLuck(chart['流年'] || [], chart['运年断语'] || {});
  renderSymbols(chart['神煞'] || []);
  renderKnowledge(chart['知识库']);
  renderAnalysis(chart['分析'] || []);
}

const markdownCell = (value) => cleanText(value ?? '—').replaceAll('|', '\\|').replaceAll('\n', '<br>');

function buildChartMarkdown(chart) {
  const pillars = ['年', '月', '日', '时'];
  const lines = [
    '# 观象 · 八字命盘', '',
    `> ${chart['输入']['性别']} · ${chart['输入']['公历']} · 农历 ${cleanText(chart['农历'])}`,
    `> 排盘口径：${chart['排盘口径']?.['模式'] || '标准时间'}${chart['出生地'] ? ` · ${chart['出生地']['名称']}` : ''}`,
    '', '## 四柱总览', '',
    '| 柱位 | 干支 | 天干十神 | 藏干（十神） | 纳音 | 空亡 | 日主地势 | 自坐长生 |',
    '| --- | --- | --- | --- | --- | --- | --- | --- |',
  ];
  pillars.forEach((name) => {
    const item = chart['四柱'][name];
    const hidden = (item['藏干'] || []).map((stem, index) => `${stem}（${(item['十神(藏干)'] || [])[index] || '—'}）`).join('、');
    lines.push(`| ${name}柱 | ${markdownCell(item['干支'])} | ${markdownCell(item['十神(天干)'])} | ${markdownCell(hidden)} | ${markdownCell(item['纳音'])} | ${markdownCell((item['空亡'] || []).join('、'))} | ${markdownCell(item['日主地势'])} | ${markdownCell(item['自坐长生'] || item['长生'])} |`);
  });
  lines.push(
    '', '## 命盘摘要', '',
    `- 日主：**${chart['日主']}**`,
    `- 生肖：${chart['生肖']}`,
    `- 胎元：${chart['胎元'] || '—'}；命宫：${chart['命宫'] || '—'}；身宫：${chart['身宫'] || '—'}`,
    '', '## 刑冲合会', '',
  );
  if ((chart['刑冲合会'] || []).length) {
    chart['刑冲合会'].forEach(([kind, where, stems, note]) => lines.push(`- **${kind}**｜${where}｜${stems}：${cleanText(note)}`));
  } else {
    lines.push('- 未检出明显的刑冲合会关系。');
  }

  const model = chart['实验推演'] || {};
  lines.push('', '## 实验推演', '', `> ${model.notice || '此部分为程序规则推演，不代表唯一命理结论。'}`);
  if (model.strength) lines.push(`- 旺衰观察：${model.strength.label}（评分 ${model.strength.score}）`);
  if (model.pattern) lines.push(`- 格局候选：${model.pattern.candidate}；依据：${cleanText(model.pattern.evidence)}`);
  if (model.guidance) {
    lines.push(`- 模型建议关注：${(model.guidance.focus_elements || []).join('、') || '—'}；提示制衡：${(model.guidance.balancing_elements || []).join('、') || '—'}`);
  }

  lines.push('', '## 大运', '', '| 序 | 干支 | 年龄 | 起年 | 终年 |', '| --- | --- | --- | --- | --- |');
  const start = chart['起运详情'];
  if (start) lines.push('', `> 起运：${start['年']}年${start['月']}个月${start['日']}天${start['时']}小时；交运时间：${start['交运时间'] || '—'}；${start['算法'] || ''}`, '');
  (chart['大运'] || []).filter((item) => item['干支']).forEach((item) => {
    lines.push(`| ${item['序']} | ${item['干支']} | ${item['年龄'] || '—'} | ${item['起年']} | ${item['终年']} |`);
  });
  lines.push('', '## 未来五年流年', '');
  (chart['流年'] || []).forEach((item) => lines.push(`- ${item['年']} 年：**${item['干支']}**`));

  lines.push('', '## 神煞', '');
  (chart['神煞'] || []).forEach(([name, where, detail]) => lines.push(`- ${name}（${where}）${detail ? `：${cleanText(detail)}` : ''}`));
  if (!(chart['神煞'] || []).length) lines.push('- 未检出神煞标记。');

  lines.push('', '## 古籍与规则参照', '');
  (chart['分析'] || []).forEach(([title, body]) => lines.push(`### ${cleanText(title)}`, '', cleanText(body), ''));
  lines.push('---', '', '本报告用于传统文化研究与娱乐体验，不构成医疗、法律、投资或人生决策建议。', '');
  return lines.join('\n');
}

function buildChartText(chart) {
  const pillars = ['年', '月', '日', '时'];
  const lines = [
    '观象 · 八字命盘',
    '============================================================',
    `性别：${chart['输入']['性别']}`,
    `公历：${chart['输入']['公历']}`,
    `农历：${cleanText(chart['农历'])}`,
    `口径：${chart['排盘口径']?.['模式'] || '标准时间'}`,
    '', '【四柱】',
  ];
  pillars.forEach((name) => {
    const item = chart['四柱'][name];
    const hidden = (item['藏干'] || []).map((stem, index) => `${stem}(${(item['十神(藏干)'] || [])[index] || '—'})`).join('、');
    lines.push(`${name}柱  ${item['干支']}  天干十神：${item['十神(天干)']}  藏干：${hidden}`);
    lines.push(`      纳音：${item['纳音']}  空亡：${(item['空亡'] || []).join('、')}  日主地势：${item['日主地势']}  自坐长生：${item['自坐长生'] || item['长生']}`);
  });
  lines.push('', '【命盘摘要】', `日主：${chart['日主']}  生肖：${chart['生肖']}`, `胎元：${chart['胎元'] || '—'}  命宫：${chart['命宫'] || '—'}  身宫：${chart['身宫'] || '—'}`);
  lines.push('', '【刑冲合会】');
  (chart['刑冲合会'] || []).forEach(([kind, where, stems, note]) => lines.push(`- ${kind}｜${where}｜${stems}：${cleanText(note)}`));
  if (!(chart['刑冲合会'] || []).length) lines.push('- 未检出明显关系');
  lines.push('', '【大运】');
  const start = chart['起运详情'];
  if (start) lines.push(`起运：${start['年']}年${start['月']}个月${start['日']}天${start['时']}小时  交运：${start['交运时间'] || '—'}  ${start['算法'] || ''}`);
  (chart['大运'] || []).filter((item) => item['干支']).forEach((item) => lines.push(`${item['序']}. ${item['干支']}  ${item['年龄'] || '—'}岁  ${item['起年']}—${item['终年']}`));
  lines.push('', '【未来五年流年】', (chart['流年'] || []).map((item) => `${item['年']}：${item['干支']}`).join('  '));
  lines.push('', '【神煞】');
  (chart['神煞'] || []).forEach(([name, where, detail]) => lines.push(`- ${name}（${where}）${detail ? `：${cleanText(detail)}` : ''}`));
  lines.push('', '【古籍与规则参照】');
  (chart['分析'] || []).forEach(([title, body]) => lines.push('', `〔${cleanText(title)}〕`, cleanText(body)));
  lines.push('', '------------------------------------------------------------', '仅供传统文化研究与娱乐体验，不构成医疗、法律、投资或人生决策建议。');
  return lines.join('\n');
}

function downloadChart(format) {
  if (!currentChart) return;
  const content = format === 'md' ? buildChartMarkdown(currentChart) : buildChartText(currentChart);
  const pillars = ['年', '月', '日', '时'].map((name) => currentChart['四柱'][name]['干支']).join('');
  const filename = `观象命盘_${pillars}.${format}`;
  const blob = new Blob(['\ufeff', content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

document.querySelectorAll('[data-export]').forEach((button) => button.addEventListener('click', () => downloadChart(button.dataset.export)));

function renderExperimental(model) {
  const root = document.querySelector('#experimental-root');
  const summary = document.querySelector('#experimental-summary');
  if (!model) {
    root.innerHTML = '<p class="empty-state">实验推演数据尚未生成</p>';
    summary.textContent = '暂无实验数据';
    return;
  }

  const strength = model.strength || {};
  const pattern = model.pattern || {};
  const guidance = model.guidance || {};
  const axis = strength.axis || { min: -2, max: 9 };
  const axisRange = Math.max(Number(axis.max) - Number(axis.min), 1);
  const scorePosition = Math.max(0, Math.min(100, ((Number(strength.score) - Number(axis.min)) / axisRange) * 100));
  const joinOrDash = (items) => (items || []).length ? items.join(' · ') : '—';

  summary.textContent = `模型观测：${strength.label || '未判定'} · 格局候选：${pattern.candidate || '未命中'}`;
  root.innerHTML = `
    <p class="model-notice"><b>边界说明</b>${escapeHTML(model.notice || '')}</p>
    <div class="strength-sheet">
      <div class="strength-heading"><span><small>气势轴 · 规则合计</small><b>${escapeHTML(strength.label || '未判定')}</b></span><strong>${Number(strength.score) >= 0 ? '+' : ''}${escapeHTML(strength.score ?? 0)}</strong></div>
      <div class="strength-axis" style="--score-position:${scorePosition}%"><span>偏弱侧</span><i><b></b></i><span>偏强侧</span></div>
      <div class="evidence-list">${(strength.dimensions || []).map((item) => `
        <article><div><b>${escapeHTML(item.key)}</b><strong>${Number(item.score) >= 0 ? '+' : ''}${escapeHTML(item.score)}</strong></div><p>${escapeHTML(item.evidence)}</p></article>`).join('')}</div>
    </div>
    <div class="model-grid">
      <article class="pattern-sheet"><p class="model-kicker">${escapeHTML(pattern.wording || '程序规则命中')}</p><div><strong>${escapeHTML(pattern.candidate || '未命中')}</strong><span>${escapeHTML(pattern.label || '')}</span></div><p>${escapeHTML(pattern.evidence || '暂无对应证据')}</p></article>
      <article class="guidance-sheet"><p class="model-kicker">取用路径 · ${escapeHTML(guidance.method || '未判定')}</p><dl>
        <div><dt>${escapeHTML(guidance.wording?.focus || '模型建议关注')}</dt><dd>${escapeHTML(joinOrDash(guidance.focus_elements))}</dd></div>
        <div><dt>${escapeHTML(guidance.wording?.balance || '模型提示制衡')}</dt><dd>${escapeHTML(joinOrDash(guidance.balancing_elements))}</dd></div>
        <div><dt>调候参考天干</dt><dd>${escapeHTML(joinOrDash(guidance.climate_stems))}</dd></div>
        <div><dt>病 / 药</dt><dd>${escapeHTML(joinOrDash(guidance.illness_elements))} / ${escapeHTML(joinOrDash(guidance.remedy_elements))}</dd></div>
        <div><dt>通关提示</dt><dd>${escapeHTML(guidance.bridge_element || '—')}</dd></div>
      </dl></article>
    </div>
    <div class="model-sources"><b>推导来源分层</b>${(model.sources || []).map((item) => `<span><i>${escapeHTML(item.layer)}</i>${escapeHTML(item.title)}</span>`).join('')}</div>`;
}

function renderPillars(chart) {
  const subtitles = { 年: '根基', 月: '提纲', 日: '命元', 时: '归宿' };
  document.querySelector('#pillar-chart').innerHTML = ['年', '月', '日', '时'].map((name) => {
    const pillar = chart['四柱'][name];
    const hiddenStems = (pillar['藏干'] || []).map((stem, index) => {
      const gods = (pillar['十神(藏干)'] || [])[index] || '—';
      const element = (pillar['藏干五行'] || [])[index] || '';
      const polarity = GAN_ELEMENT[stem]?.[1] || '';
      return `<span class="hidden-stem"><b>${escapeHTML(stem)}</b><em>${escapeHTML(polarity + element)}</em><small>${escapeHTML(gods)}</small></span>`;
    }).join('');
    return `
      <article class="pillar pillar-complete">
        <div class="pillar-label">${name}柱 · ${subtitles[name]}</div>
        <div class="pillar-gz"><span>${escapeHTML(pillar['天干'])}</span><span>${escapeHTML(pillar['地支'])}</span></div>
        <div class="pillar-ten">天干十神 · ${escapeHTML(pillar['十神(天干)'])}</div>
        <div class="stem-branch-nature">
          <span><small>天干</small><b>${escapeHTML(pillar['干阴阳'] + pillar['干五行'])}</b></span>
          <span><small>地支</small><b>${escapeHTML(pillar['支阴阳'] + pillar['支五行'])} · ${escapeHTML(pillar['生肖'])}</b></span>
        </div>
        <div class="hidden-stems"><p>藏干 · 五行 · 十神</p>${hiddenStems}</div>
        <dl class="pillar-detail pillar-detail-complete">
          <div><dt>纳音</dt><dd>${escapeHTML(pillar['纳音'])}<small>${escapeHTML(pillar['纳音简'] || '')}</small></dd></div>
          <div><dt>空亡</dt><dd>${escapeHTML((pillar['空亡'] || []).join(' · '))}</dd></div>
          <div><dt>日主地势</dt><dd>${escapeHTML(pillar['日主地势'])}</dd></div>
          <div><dt>自坐长生</dt><dd>${escapeHTML(pillar['自坐长生'] || pillar['长生'])}</dd></div>
        </dl>
      </article>`;
  }).join('');
}

function renderElements(chart) {
  const elementOrder = ['木', '火', '土', '金', '水'];
  const counts = Object.fromEntries(elementOrder.map((element) => [element, { stem: 0, branch: 0, hidden: 0, total: 0 }]));
  Object.values(chart['四柱']).forEach((pillar) => {
    if (counts[pillar['干五行']]) counts[pillar['干五行']].stem += 1;
    if (counts[pillar['支五行']]) counts[pillar['支五行']].branch += 1;
    (pillar['藏干五行'] || []).forEach((element) => { if (counts[element]) counts[element].hidden += 1; });
  });
  Object.values(counts).forEach((item) => { item.total = item.stem + item.branch + item.hidden; });
  const max = Math.max(...Object.values(counts).map((item) => item.total), 1);
  const container = document.querySelector('#element-balance');
  container.innerHTML = `
    <div class="element-table-head"><span>五行</span><span>数量对比</span><span>天干</span><span>地支</span><span>藏干</span><span>合计</span></div>
    ${elementOrder.map((element) => {
      const item = counts[element];
      return `<div class="element-row element-row-complete" style="--element-color:${ELEMENT_COLORS[element]}">
        <b>${element}</b><div class="element-bar"><i data-width="${(item.total / max) * 100}%"></i></div>
        <span>${item.stem}</span><span>${item.branch}</span><span>${item.hidden}</span><strong>${item.total}</strong>
      </div>`;
    }).join('')}`;
  requestAnimationFrame(() => container.querySelectorAll('.element-bar i').forEach((bar) => { bar.style.width = bar.dataset.width; }));
}

function renderCycles(cycles, startAge, startDetail, analyses) {
  const useful = cycles.filter((cycle) => cycle && cycle['干支']);
  const readings = new Map((analyses['大运'] || []).map((item) => [item['干支'], item['断语']]));
  const classicalReadings = new Map((analyses['三命通会'] || []).map((item) => [item['干支'], item['断语']]));
  const startCopy = startDetail
    ? `${startDetail['年']}年${startDetail['月']}个月${startDetail['日']}天${startDetail['时']}小时 · 交运 ${startDetail['交运时间'] || '—'}`
    : `${startAge ?? '—'} 岁`;
  document.querySelector('#cycle-note').textContent = `起运 ${startCopy} · 共 ${useful.length} 步有效大运，已全部展开`;
  const currentYear = new Date().getFullYear();
  const track = document.querySelector('#cycle-track');
  track.className = 'cycle-track dayun-complete';
  track.innerHTML = useful.map((cycle) => {
    const active = currentYear >= cycle['起年'] && currentYear <= cycle['终年'];
    const readingParts = cleanText(readings.get(cycle['干支']) || '暂无对应断语').split(/\s*\|\s*|\n+/).filter(Boolean);
    const classical = classicalReadings.get(cycle['干支']);
    return `
      <article class="dayun-card${active ? ' active' : ''}">
        <div class="dayun-order"><span>第 ${escapeHTML(cycle['序'])} 运</span>${active ? '<b>当下所行</b>' : ''}</div>
        <div class="dayun-main"><strong>${escapeHTML(cycle['干支'])}</strong><div><b>${escapeHTML(cycle['年龄'])} 岁</b><span>${escapeHTML(cycle['起年'])}—${escapeHTML(cycle['终年'])}</span></div></div>
        <div class="dayun-reading">
          ${readingParts.map((part, index) => `<p${index === 0 ? ' class="reading-summary"' : ''}>${escapeHTML(part)}</p>`).join('')}
          ${classical ? `<details class="reference-block"><summary>《三命通会》古籍参照</summary><p>${escapeHTML(cleanText(classical))}</p></details>` : ''}
        </div>
      </article>`;
  }).join('');
}

function renderAnnualLuck(years, analyses) {
  const readings = new Map((analyses['流年'] || []).map((item) => [String(item['年']), item['断语']]));
  const classical = new Map((analyses['三命通会流年'] || []).map((item) => [item['干支'], item['断语']]));
  const currentYear = new Date().getFullYear();
  const note = document.querySelector('#annual-note');
  const track = document.querySelector('#annual-track');
  note.textContent = years.length ? `${years[0]['年']}—${years[years.length - 1]['年']} · 以当前年份为起点` : '暂无流年数据';
  track.innerHTML = years.map((item) => {
    const active = Number(item['年']) === currentYear;
    const reading = readings.get(String(item['年'])) || '暂无对应规则说明';
    const source = classical.get(item['干支']);
    return `<article class="annual-card${active ? ' active' : ''}">
      <div class="annual-heading"><span>${escapeHTML(item['年'])}</span>${active ? '<b>今年</b>' : ''}</div>
      <strong>${escapeHTML(item['干支'])}</strong>
      <p>${escapeHTML(cleanText(reading))}</p>
      ${source ? `<details class="reference-block"><summary>太岁古籍参照</summary><p>${escapeHTML(cleanText(source))}</p></details>` : ''}
    </article>`;
  }).join('');
}

function renderKnowledge(knowledge) {
  const analysisSection = document.querySelector('.analysis-section');
  let panel = document.querySelector('#knowledge-panel');
  if (!panel) {
    panel = document.createElement('div');
    panel.id = 'knowledge-panel';
    panel.className = 'knowledge-panel';
    analysisSection.insertBefore(panel, document.querySelector('#analysis-list'));
  }
  if (!knowledge) {
    panel.innerHTML = '<p>扩展知识库尚未载入</p>';
    return;
  }
  const stats = knowledge['载入统计'];
  const matches = [knowledge['月令索引']['命中'] ? knowledge['月令索引']['条目'] : null]
    .concat(knowledge['天干五合'] || [], knowledge['关系索引'] || []).filter(Boolean);
  panel.innerHTML = `
    <div class="knowledge-loaded"><i></i><span>扩展知识库已载入</span><small>${stats['知识分类']} 类 · ${stats['纯文本短语']} 条短语</small></div>
    <div class="knowledge-matches"><b>本命确定性命中</b>${matches.length ? matches.map((item) => `<span>${escapeHTML(item)}</span>`).join('') : '<small>暂无结构索引命中</small>'}</div>
    <p>${escapeHTML(knowledge['说明'])}</p>`;
}

function renderAnalysis(analysis) {
  const container = document.querySelector('#analysis-list');
  container.innerHTML = analysis.map(([title, body], index) => {
    const source = title.startsWith('月令断语') || title.startsWith('日主性格') ? '古籍参照' : '规则匹配';
    return `
    <article class="analysis-item${index === 0 ? ' open' : ''}">
      <button type="button" aria-expanded="${index === 0}"><span>${escapeHTML(title)}<small class="source-badge">${source}</small></span><i aria-hidden="true"></i></button>
      <div class="analysis-body">${escapeHTML(cleanText(body))}</div>
    </article>`;
  }).join('');
  container.querySelectorAll('.analysis-item button').forEach((button) => button.addEventListener('click', () => {
    const item = button.closest('.analysis-item');
    const open = item.classList.toggle('open');
    button.setAttribute('aria-expanded', String(open));
  }));
}
