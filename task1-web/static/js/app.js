/**
 * Currency Viewer — клиентская логика.
 * Без сторонних зависимостей, чистый ES2022.
 */

// ── DOM-элементы ─────────────────────────────────────────────────────────────

const baseSelect   = document.getElementById('baseSelect');
const loadBtn      = document.getElementById('loadBtn');
const searchInput  = document.getElementById('searchInput');
const statusBar    = document.getElementById('statusBar');
const metaRow      = document.getElementById('metaRow');
const metaBase     = document.getElementById('metaBase');
const metaUpdated  = document.getElementById('metaUpdated');
const metaCount    = document.getElementById('metaCount');
const tableSection = document.getElementById('tableSection');
const ratesBody    = document.getElementById('ratesBody');
const emptyState   = document.getElementById('emptyState');

// ── Состояние приложения ─────────────────────────────────────────────────────

let allRates  = [];   // все загруженные курсы
let sortKey   = 'code';
let sortAsc   = true;

// ── Статусные сообщения ──────────────────────────────────────────────────────

function showStatus(type, message) {
  statusBar.hidden = false;
  statusBar.className = `status-bar ${type}`;

  const spinner = type === 'loading'
    ? '<span class="spinner"></span>'
    : '';

  const icon = type === 'error' ? '✕' : type === 'success' ? '✓' : '';

  statusBar.innerHTML = `${spinner}${icon ? `<span>${icon}</span>` : ''}<span>${message}</span>`;
}

function hideStatus() {
  statusBar.hidden = true;
}

// ── Рендеринг таблицы ────────────────────────────────────────────────────────

/**
 * Фильтрует и сортирует курсы, затем отрисовывает строки таблицы.
 */
function renderTable() {
  const query = searchInput.value.trim().toLowerCase();

  let filtered = query
    ? allRates.filter(r =>
        r.code.toLowerCase().includes(query) ||
        r.name.toLowerCase().includes(query)
      )
    : [...allRates];

  // Сортировка
  filtered.sort((a, b) => {
    const va = a[sortKey];
    const vb = b[sortKey];
    if (typeof va === 'number') return sortAsc ? va - vb : vb - va;
    return sortAsc
      ? String(va).localeCompare(String(vb))
      : String(vb).localeCompare(String(va));
  });

  // Обновляем стрелки в заголовках
  document.querySelectorAll('.rates-table th[data-sort]').forEach(th => {
    const key = th.dataset.sort;
    th.classList.toggle('sorted', key === sortKey);
    const arrow = th.querySelector('.sort-arrow');
    if (key === sortKey) {
      arrow.textContent = sortAsc ? '↑' : '↓';
    } else {
      arrow.textContent = '↕';
    }
  });

  // Отрисовка строк
  ratesBody.innerHTML = '';

  if (filtered.length === 0) {
    ratesBody.innerHTML = `
      <tr>
        <td colspan="4" style="text-align:center; padding:2rem; color:var(--text-dim); font-family:var(--font-mono);">
          Ничего не найдено по запросу «${escapeHtml(searchInput.value.trim())}»
        </td>
      </tr>`;
    return;
  }

  const fragment = document.createDocumentFragment();

  filtered.forEach((r, i) => {
    const tr = document.createElement('tr');
    tr.style.animationDelay = `${Math.min(i * 15, 300)}ms`;

    const inverse = r.rate > 0 ? (1 / r.rate).toFixed(6) : '—';
    const rateFormatted = formatRate(r.rate);

    tr.innerHTML = `
      <td class="cell-code">${escapeHtml(r.code)}</td>
      <td class="cell-name">${escapeHtml(r.name)}</td>
      <td class="cell-rate">${rateFormatted}</td>
      <td class="cell-inv">${inverse}</td>
    `;

    fragment.appendChild(tr);
  });

  ratesBody.appendChild(fragment);

  // Обновляем счётчик
  metaCount.innerHTML = `Показано: <strong>${filtered.length} / ${allRates.length}</strong>`;
}

/** Форматирует курс: крупные значения без лишних нулей, мелкие — 6 знаков. */
function formatRate(rate) {
  if (rate >= 1000) return rate.toFixed(2);
  if (rate >= 1)    return rate.toFixed(4);
  return rate.toFixed(6);
}

function escapeHtml(str) {
  return str.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// ── Загрузка данных ──────────────────────────────────────────────────────────

async function loadRates() {
  const base = baseSelect.value;
  if (!base) return;

  // Блокируем UI
  loadBtn.disabled = true;
  searchInput.disabled = true;
  tableSection.hidden = true;
  emptyState.hidden = true;
  metaRow.hidden = true;

  showStatus('loading', `Загружаю курсы для ${base}…`);

  try {
    const response = await fetch(`/api/rates/${base}`);
    const data = await response.json();

    if (!response.ok) {
      // Ошибка от нашего API
      throw new Error(data.detail || `HTTP ${response.status}`);
    }

    // Сохраняем и отображаем
    allRates = data.rates;

    metaBase.innerHTML    = `База: <strong>${data.base} — ${data.base_name}</strong>`;
    metaUpdated.innerHTML = `Обновлено: <strong>${data.updated_at}</strong>`;
    metaCount.innerHTML   = `Всего: <strong>${allRates.length}</strong>`;

    metaRow.hidden = false;
    tableSection.hidden = false;
    searchInput.disabled = false;
    searchInput.value = '';

    renderTable();
    showStatus('success', `Загружено ${allRates.length} курсов для ${base}`);

    // Скрываем статус через 3 секунды
    setTimeout(hideStatus, 3000);

  } catch (err) {
    allRates = [];
    emptyState.hidden = false;
    showStatus('error', `Ошибка: ${err.message}`);
    console.error('Ошибка загрузки курсов:', err);
  } finally {
    loadBtn.disabled = false;
  }
}

// ── Сортировка ───────────────────────────────────────────────────────────────

document.querySelectorAll('.rates-table th[data-sort]').forEach(th => {
  th.addEventListener('click', () => {
    const key = th.dataset.sort;
    if (sortKey === key) {
      sortAsc = !sortAsc;
    } else {
      sortKey = key;
      sortAsc = key !== 'rate'; // для курса по умолчанию DESC
    }
    renderTable();
  });
});

// ── Поиск / фильтр ───────────────────────────────────────────────────────────

let searchTimer;
searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(renderTable, 180);
});

// ── Быстрый выбор Enter ──────────────────────────────────────────────────────

baseSelect.addEventListener('keydown', e => {
  if (e.key === 'Enter') loadRates();
});

// ── Запуск ───────────────────────────────────────────────────────────────────

loadBtn.addEventListener('click', loadRates);
