const form = document.querySelector('#chart-form');
const resultShell = document.querySelector('#result-shell');
const statusLine = document.querySelector('#form-status');
const submitButton = form.querySelector('.submit-button');
const defaultButtonContent = submitButton.innerHTML;

const GAN_ELEMENT = {
  甲: ['木', '阳'], 乙: ['木', '阴'], 丙: ['火', '阳'], 丁: ['火', '阴'],
  戊: ['土', '阳'], 己: ['土', '阴'], 庚: ['金', '阳'], 辛: ['金', '阴'],
  壬: ['水', '阳'], 癸: ['水', '阴'],
};
const ELEMENT_COLORS = { 木: '#3f7452', 火: '#b64a36', 土: '#a47935', 金: '#77766e', 水: '#285d6d' };

const escapeHTML = (value = '') => String(value)
  .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;').replaceAll("'", '&#039;');

const cleanText = (value = '') => String(value)
  .replaceAll('\r', '\n').replace(/\n{3,}/g, '\n\n').trim();

document.querySelector('#longitude-help').addEventListener('click', (event) => {
  const hint = document.querySelector('#longitude-hint');
  const visible = hint.classList.toggle('visible');
  event.currentTarget.setAttribute('aria-expanded', String(visible));
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusLine.textContent = '';
  submitButton.disabled = true;
  submitButton.innerHTML = document.querySelector('#loading-template').innerHTML;
  const payload = {
    date: document.querySelector('#birth-date').value,
    time: document.querySelector('#birth-time').value,
    sex: Number(form.elements.sex.value),
    longitude: Number(document.querySelector('#longitude').value),
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
  renderHeading(chart);
  renderPillars(chart);
  renderSummary(chart);
  renderRelations(chart['刑冲合会'] || []);
  renderCycles(chart['大运'] || [], chart['起运']);
  renderSymbols(chart['神煞'] || []);
  renderAnalysis(chart['分析'] || []);
}

function renderHeading(chart) {
  const lunar = cleanText(chart['农历']);
  const shortLunar = lunar.replace(/^一?[〇零一二三四五六七八九]{4}年/, '');
  document.querySelector('#chart-title').textContent = `${chart['四柱']['年']['干支']}年 · ${shortLunar}`;
  document.querySelector('#chart-meta').innerHTML = [
    `<span>公历 <strong>${escapeHTML(chart['输入']['公历'])}</strong></span>`,
    `<br><span>${escapeHTML(chart['输入']['性别'])} · 生肖 ${escapeHTML(chart['生肖'])}</span>`,
  ].join('');
}

function renderPillars(chart) {
  const names = ['年', '月', '日', '时'];
  const subtitles = { 年: '根基', 月: '提纲', 日: '命元', 时: '归宿' };
  document.querySelector('#pillar-chart').innerHTML = names.map((name) => {
    const pillar = chart['四柱'][name];
    const hidden = (pillar['藏干'] || []).join(' · ');
    const hiddenGods = (pillar['十神(藏干)'] || []).join(' · ');
    return `
      <article class="pillar">
        <div class="pillar-label">${name}柱 · ${subtitles[name]}</div>
        <div class="pillar-gz"><span>${escapeHTML(pillar['天干'])}</span><span>${escapeHTML(pillar['地支'])}</span></div>
        <div class="pillar-ten">${escapeHTML(pillar['十神(天干)'])}</div>
        <dl class="pillar-detail">
          <div><dt>藏干</dt><dd title="${escapeHTML(hiddenGods)}">${escapeHTML(hidden)}</dd></div>
          <div><dt>纳音</dt><dd>${escapeHTML(pillar['纳音'])}</dd></div>
          <div><dt>长生</dt><dd>${escapeHTML(pillar['长生'])}</dd></div>
          <div><dt>空亡</dt><dd>${escapeHTML((pillar['空亡'] || []).join(''))}</dd></div>
        </dl>
      </article>`;
  }).join('');
}

function renderSummary(chart) {
  const dayMaster = chart['日主'];
  const [element, polarity] = GAN_ELEMENT[dayMaster] || ['', ''];
  document.querySelector('#day-master').textContent = dayMaster;
  document.querySelector('#day-master-element').textContent = `${polarity}${element}`;
  document.querySelector('#mini-facts').innerHTML = [
    `<span>胎元 <b>${escapeHTML(chart['胎元'] || '—')}</b></span>`,
    `<span>命宫 <b>${escapeHTML(chart['命宫'] || '—')}</b></span>`,
    `<span>生肖 <b>${escapeHTML(chart['生肖'])}</b></span>`,
  ].join('');
  renderElements(chart);
  const solar = chart['真太阳时'];
  document.querySelector('#solar-original').textContent = solar['原时间'];
  document.querySelector('#solar-corrected').textContent = solar['校正后'];
  const sign = Number(solar['总校正分']) > 0 ? '+' : '';
  document.querySelector('#solar-correction').textContent = `经度与均时差，共校正 ${sign}${solar['总校正分']} 分钟`;
}

function renderElements(chart) {
  const count = { 木: 0, 火: 0, 土: 0, 金: 0, 水: 0 };
  Object.values(chart['四柱']).forEach((pillar) => {
    if (count[pillar['干五行']] !== undefined) count[pillar['干五行']] += 1;
    if (count[pillar['支五行']] !== undefined) count[pillar['支五行']] += 1;
    (pillar['藏干五行'] || []).forEach((element) => {
      if (count[element] !== undefined) count[element] += 1;
    });
  });
  const max = Math.max(...Object.values(count), 1);
  const container = document.querySelector('#element-balance');
  container.innerHTML = Object.entries(count).map(([element, amount]) => `
    <div class="element-row" style="--element-color:${ELEMENT_COLORS[element]}">
      <b>${element}</b><div class="element-bar"><i data-width="${(amount / max) * 100}%"></i></div><span>${amount}</span>
    </div>`).join('');
  requestAnimationFrame(() => container.querySelectorAll('.element-bar i').forEach((bar) => {
    bar.style.width = bar.dataset.width;
  }));
}

function renderRelations(relations) {
  const list = document.querySelector('#relation-list');
  if (!relations.length) {
    list.innerHTML = '<p class="empty-state">四柱之间未检出明显的刑冲合会关系</p>';
    return;
  }
  list.innerHTML = relations.map((relation, index) => {
    const [kind, where, stems, note] = relation;
    return `
      <article class="relation-item">
        <div class="relation-kind"><i>${index + 1}</i>${escapeHTML(kind)}</div>
        <p><strong>${escapeHTML(where)}</strong> · ${escapeHTML(stems)}<br>${escapeHTML(note)}</p>
      </article>`;
  }).join('');
}

function renderCycles(cycles, startAge) {
  const usefulCycles = cycles.filter((cycle) => cycle && cycle['干支']);
  document.querySelector('#cycle-note').textContent = `起运 ${startAge ?? '—'} 岁 · 左右滑动查看`;
  const currentYear = new Date().getFullYear();
  document.querySelector('#cycle-track').innerHTML = usefulCycles.slice(0, 10).map((cycle) => {
    const active = currentYear >= cycle['起年'] && currentYear <= cycle['终年'];
    return `
      <article class="cycle${active ? ' active' : ''}">
        <span class="cycle-index">第 ${escapeHTML(cycle['序'])} 运${active ? ' · 当下' : ''}</span>
        <strong>${escapeHTML(cycle['干支'])}</strong>
        <p>${escapeHTML(cycle['年龄'])} 岁<br>${escapeHTML(cycle['起年'])}—${escapeHTML(cycle['终年'])}</p>
      </article>`;
  }).join('');
}

function renderSymbols(symbols) {
  document.querySelector('#shensha-count').textContent = symbols.length;
  document.querySelector('#symbol-list').innerHTML = symbols.length
    ? symbols.map(([name, where, detail]) => `
        <div class="symbol"><b>${escapeHTML(name)}</b><span>${escapeHTML(where)}</span><small>${escapeHTML(detail || '古法标记')}</small></div>`).join('')
    : '<p class="empty-state">未检出神煞标记</p>';
}

function renderAnalysis(analysis) {
  const container = document.querySelector('#analysis-list');
  container.innerHTML = analysis.slice(0, 12).map(([title, body], index) => `
    <article class="analysis-item${index === 0 ? ' open' : ''}">
      <button type="button" aria-expanded="${index === 0}"><span>${escapeHTML(title)}</span><i aria-hidden="true"></i></button>
      <div class="analysis-body">${escapeHTML(cleanText(body))}</div>
    </article>`).join('');
  container.querySelectorAll('.analysis-item button').forEach((button) => {
    button.addEventListener('click', () => {
      const item = button.closest('.analysis-item');
      const open = item.classList.toggle('open');
      button.setAttribute('aria-expanded', String(open));
    });
  });
}
