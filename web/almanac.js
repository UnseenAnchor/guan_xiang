const form = document.querySelector('#almanac-form');
const dateInput = document.querySelector('#almanac-date');
const statusLine = document.querySelector('#almanac-status');
const result = document.querySelector('#almanac-result');
const submitButton = form.querySelector('button[type="submit"]');

function escapeHTML(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]);
}

async function readJsonResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`服务端返回了非 JSON 响应（HTTP ${response.status}），请重启服务后重试`);
  }
  try {
    return await response.json();
  } catch (_error) {
    throw new Error('服务端返回的数据格式异常，请重启服务后重试');
  }
}

function localDateValue(date = new Date()) {
  const pad = (value) => String(value).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function tags(items) {
  return (items || []).length ? items.map((item) => `<span>${escapeHTML(item)}</span>`).join('') : '<small>无特别记载</small>';
}

function shortDateTime(value) {
  return String(value || '').replace(/^\d{4}-/, '').replace(/:00$/, '');
}

function renderAlmanac(data) {
  const date = data.date;
  const [, month, day] = date.solar.split('-');
  document.querySelector('#hero-day').textContent = day;
  document.querySelector('#date-year-month').textContent = `${date.solar.slice(0, 4)}年 ${Number(month)}月`;
  document.querySelector('#date-day').textContent = day;
  document.querySelector('#date-weekday').textContent = date.weekday;
  document.querySelector('#date-lunar').textContent = date.lunar;
  document.querySelector('#date-ganzhi').textContent = date.ganzhi;
  document.querySelector('#date-zodiac').textContent = `生肖 ${date.zodiac}`;
  document.querySelector('#date-constellation').textContent = `${date.western_zodiac}座`;
  document.querySelector('#date-term').textContent = data.solar_terms.current ? `今日 ${data.solar_terms.current}` : '节气之间';

  document.querySelector('#officer-name').textContent = `${data.day_officer.name}日`;
  document.querySelector('#officer-luck').textContent = data.day_officer.classification || '传统值日';
  document.querySelector('#ecliptic-deity').textContent = data.ecliptic.deity;
  document.querySelector('#ecliptic-type').textContent = `${data.ecliptic.type} · ${data.ecliptic.luck}`;
  document.querySelector('#lodge-name').textContent = data.lodge.full_name;
  document.querySelector('#lodge-detail').textContent = `${data.lodge.direction}方 · ${data.lodge.symbol}`;
  document.querySelector('#day-star').textContent = data.nine_stars.day.name;
  document.querySelector('#day-star-detail').textContent = `${data.nine_stars.day.position_desc} · ${data.nine_stars.day.element}`;

  document.querySelector('#recommended-list').innerHTML = tags(data.activities.recommended);
  document.querySelector('#avoided-list').innerHTML = tags(data.activities.avoided);
  document.querySelector('#auspicious-spirits').innerHTML = tags(data.spirits.auspicious);
  document.querySelector('#inauspicious-spirits').innerHTML = tags(data.spirits.inauspicious);
  document.querySelector('#pengzu-list').innerHTML = data.taboos.pengzu.map((item) => `<p>${escapeHTML(item)}</p>`).join('');
  document.querySelector('#fetus-position').textContent = data.taboos.fetus;
  document.querySelector('#direction-list').innerHTML = data.directions.map((item) => `<span><small>${escapeHTML(item.label)}</small><b>${escapeHTML(item.direction)}</b><em>${escapeHTML(item.trigram)}</em></span>`).join('');
  document.querySelector('#clash-text').textContent = data.clash || '无特别记载';

  document.querySelector('#nine-star-list').innerHTML = ['year', 'month', 'day'].map((key, index) => {
    const star = data.nine_stars[key];
    return `<article><small>${['年', '月', '日'][index]}九星</small><strong>${escapeHTML(star.name)}</strong><span>${escapeHTML(star.position_desc)} · ${escapeHTML(star.position)}宫</span></article>`;
  }).join('');
  const terms = data.solar_terms;
  document.querySelector('#term-timeline').innerHTML = `<article><small>上一节气</small><b>${escapeHTML(terms.previous.name)}</b><span>${escapeHTML(shortDateTime(terms.previous.datetime))}</span></article><i></i><article class="current"><small>今日</small><b>${escapeHTML(terms.current || '节气之间')}</b><span>${escapeHTML(date.solar.slice(5))}</span></article><i></i><article><small>下一节气</small><b>${escapeHTML(terms.next.name)}</b><span>${escapeHTML(shortDateTime(terms.next.datetime))}</span></article>`;
  document.querySelector('#officer-mnemonic').textContent = data.day_officer.mnemonic;

  document.querySelector('#almanac-sources').innerHTML = data.sources.map((item) => `<i>${escapeHTML(item.layer)}</i>${escapeHTML(item.title)}`).join('<em>／</em>');
  document.querySelector('#almanac-notice').textContent = data.notice;
}

async function loadAlmanac() {
  statusLine.textContent = '';
  submitButton.disabled = true;
  submitButton.querySelector('span').textContent = '展卷中';
  try {
    const response = await fetch(`/api/almanac?date=${encodeURIComponent(dateInput.value)}`);
    const payload = await readJsonResponse(response);
    if (!response.ok || !payload.ok) throw new Error(payload.error || '暂时无法读取此日黄历');
    renderAlmanac(payload.almanac);
    result.hidden = false;
    result.classList.remove('visible');
    requestAnimationFrame(() => result.classList.add('visible'));
  } catch (error) {
    statusLine.textContent = error.message;
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector('span').textContent = '观此日';
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  loadAlmanac();
});

dateInput.value = localDateValue();
loadAlmanac();
