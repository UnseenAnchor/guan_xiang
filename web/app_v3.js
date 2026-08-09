/* v3 overrides: keep the v2 input flow, expand only result presentation. */

renderChart = function renderCompleteChart(chart) {
  renderHeading(chart);
  renderPillars(chart);
  renderSummary(chart);
  renderRelations(chart['刑冲合会'] || []);
  renderCycles(chart['大运'] || [], chart['起运'], chart['运年断语'] || {});
  renderSymbols(chart['神煞'] || []);
  renderKnowledge(chart['知识库']);
  renderAnalysis(chart['分析'] || []);
};

renderPillars = function renderCompletePillars(chart) {
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
          <div><dt>长生</dt><dd>${escapeHTML(pillar['长生'])}</dd></div>
        </dl>
      </article>`;
  }).join('');
};

renderElements = function renderCompleteElements(chart) {
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
    <div class="element-table-head"><span>五行</span><span>结构占比</span><span>天干</span><span>地支</span><span>藏干</span><span>合计</span></div>
    ${elementOrder.map((element) => {
      const item = counts[element];
      return `<div class="element-row element-row-complete" style="--element-color:${ELEMENT_COLORS[element]}">
        <b>${element}</b><div class="element-bar"><i data-width="${(item.total / max) * 100}%"></i></div>
        <span>${item.stem}</span><span>${item.branch}</span><span>${item.hidden}</span><strong>${item.total}</strong>
      </div>`;
    }).join('')}`;
  requestAnimationFrame(() => container.querySelectorAll('.element-bar i').forEach((bar) => { bar.style.width = bar.dataset.width; }));
};

renderCycles = function renderCompleteCycles(cycles, startAge, analyses) {
  const useful = cycles.filter((cycle) => cycle && cycle['干支']);
  const readings = new Map((analyses['大运'] || []).map((item) => [item['干支'], item['断语']]));
  document.querySelector('#cycle-note').textContent = `起运 ${startAge ?? '—'} 岁 · 共 ${useful.length} 步有效大运，已全部展开`;
  const currentYear = new Date().getFullYear();
  const track = document.querySelector('#cycle-track');
  track.className = 'cycle-track dayun-complete';
  track.innerHTML = useful.map((cycle) => {
    const active = currentYear >= cycle['起年'] && currentYear <= cycle['终年'];
    const readingParts = String(readings.get(cycle['干支']) || '暂无对应断语').split(' | ');
    return `
      <article class="dayun-card${active ? ' active' : ''}">
        <div class="dayun-order"><span>第 ${escapeHTML(cycle['序'])} 运</span>${active ? '<b>当下所行</b>' : ''}</div>
        <div class="dayun-main"><strong>${escapeHTML(cycle['干支'])}</strong><div><b>${escapeHTML(cycle['年龄'])} 岁</b><span>${escapeHTML(cycle['起年'])}—${escapeHTML(cycle['终年'])}</span></div></div>
        <div class="dayun-reading">
          ${readingParts.map((part, index) => `<p${index === 0 ? ' class="reading-summary"' : ''}>${escapeHTML(part)}</p>`).join('')}
        </div>
      </article>`;
  }).join('');
};

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
    <div class="knowledge-loaded"><i></i><span>扩展知识库已载入</span><small>${stats['知识分类']} 类 · ${stats['纯文本短语']} 条短语 · ${stats['检索词键']} 词键</small></div>
    <div class="knowledge-matches"><b>本命确定性命中</b>${matches.length ? matches.map((item) => `<span>${escapeHTML(item)}</span>`).join('') : '<small>暂无结构索引命中</small>'}</div>
    <p>${escapeHTML(knowledge['说明'])}</p>`;
}

renderAnalysis = function renderAllAnalysis(analysis) {
  const container = document.querySelector('#analysis-list');
  container.innerHTML = analysis.map(([title, body], index) => `
    <article class="analysis-item${index === 0 ? ' open' : ''}">
      <button type="button" aria-expanded="${index === 0}"><span>${escapeHTML(title)}</span><i aria-hidden="true"></i></button>
      <div class="analysis-body">${escapeHTML(cleanText(body))}</div>
    </article>`).join('');
  container.querySelectorAll('.analysis-item button').forEach((button) => button.addEventListener('click', () => {
    const item = button.closest('.analysis-item');
    const open = item.classList.toggle('open');
    button.setAttribute('aria-expanded', String(open));
  }));
};
