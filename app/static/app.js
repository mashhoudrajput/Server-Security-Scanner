const API = '/api';
let currentJobId = null;

const serversList = document.getElementById('servers-list');
const addServerBtn = document.getElementById('add-server');

function addServerRow(host = '', user = 'ubuntu') {
  const row = document.createElement('div');
  row.className = 'server-row';
  row.innerHTML = `
    <input type="text" placeholder="IP or hostname" value="${host}" data-field="host" />
    <input type="text" placeholder="ubuntu" value="${user}" data-field="user" />
    <label class="file-label">
      <input type="file" class="key-file" data-field="key" accept=".pem,.key,*" />
      <span class="file-btn">Choose file</span>
    </label>
    <button type="button" class="btn btn-danger" data-remove>Remove</button>
  `;
  row.querySelector('[data-remove]').addEventListener('click', () => { row.remove(); updateStartButton(); });
  row.querySelector('.key-file').addEventListener('change', async (e) => {
    const f = e.target.files[0];
    row.querySelector('.file-btn').textContent = f ? f.name : 'Choose file';
    if (f) {
      try {
        e.target._base64 = await readKeyAsBase64(f);
      } catch (err) {
        e.target._base64 = null;
      }
    } else {
      e.target._base64 = null;
    }
    updateStartButton();
  });
  serversList.appendChild(row);
}

addServerBtn.addEventListener('click', () => addServerRow());
addServerRow();

const startScanBtn = document.getElementById('start-scan');
const progressContainer = document.getElementById('progress-container');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const progressPct = document.getElementById('progress-pct');
const reportPlaceholder = document.getElementById('report-placeholder');
const downloadLink = document.getElementById('download-link');
const downloadContainer = document.getElementById('download-container');
const reportSection = document.getElementById('report-section');

function getServers() {
  const rows = serversList.querySelectorAll('.server-row');
  return Array.from(rows)
    .map(row => {
      const host = row.querySelector('[data-field="host"]').value.trim();
      const user = row.querySelector('[data-field="user"]').value.trim() || 'ubuntu';
      const keyInput = row.querySelector('[data-field="key"]');
      const keyBase64 = keyInput && keyInput._base64 ? keyInput._base64 : null;
      return { host, user, key_base64: keyBase64 };
    })
    .filter(s => s.host && s.key_base64);
}

async function readKeyAsBase64(file) {
  const buf = await file.arrayBuffer();
  const bytes = new Uint8Array(buf);
  let binary = '';
  bytes.forEach(b => binary += String.fromCharCode(b));
  return btoa(binary);
}

function updateStartButton() {
  const servers = getServers();
  startScanBtn.disabled = !servers.length;
}

serversList.addEventListener('input', updateStartButton);

startScanBtn.addEventListener('click', async () => {
  const servers = getServers();
  if (!servers.length) return;

  startScanBtn.disabled = true;
  progressContainer.classList.remove('hidden');
  progressFill.style.width = '0%';
  progressText.textContent = 'Starting scan...';
  progressPct.textContent = '0%';
  reportPlaceholder.textContent = 'Scan in progress...';
  downloadContainer.classList.add('hidden');

  try {
    const res = await fetch(`${API}/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ servers, auto_mode: true }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to start scan');
    currentJobId = data.job_id;
    pollStatus();
  } catch (err) {
    alert(err.message);
    startScanBtn.disabled = false;
    progressContainer.classList.add('hidden');
  }
});

async function pollStatus() {
  if (!currentJobId) return;
  try {
    const res = await fetch(`${API}/scan/${currentJobId}/status`);
    const data = await res.json();
    const pct = data.progress || 0;
    progressFill.style.width = `${pct}%`;
    progressPct.textContent = `${pct}%`;
    progressText.textContent = pct >= 100 ? 'Complete' : `Scanning... ${pct}%`;

    if (data.status === 'completed' || data.status === 'error') {
      progressFill.style.width = '100%';
      progressPct.textContent = '100%';
      progressText.textContent = 'Complete';
      startScanBtn.disabled = false;
      renderResults(data);
      reportPlaceholder.textContent = 'Generating report...';
      await autoGenerateReport();
      return;
    }
    setTimeout(pollStatus, 1500);
  } catch (err) {
    startScanBtn.disabled = false;
    progressContainer.classList.add('hidden');
  }
}

async function autoGenerateReport() {
  if (!currentJobId) return;
  try {
    const res = await fetch(`${API}/report/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: currentJobId }),
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok && data.filename) {
      downloadLink.href = `${API}/report/download/${data.filename}`;
      downloadLink.download = data.filename;
      downloadContainer.classList.remove('hidden');
      reportPlaceholder.textContent = 'Report ready.';
      reportSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
      const errMsg = data.detail || data.message || (typeof data === 'string' ? data : '');
      reportPlaceholder.textContent = 'Report generation failed.' + (errMsg ? ' ' + errMsg : '');
    }
  } catch (err) {
    reportPlaceholder.textContent = 'Report generation failed. ' + (err.message || '');
  }
}

function renderResults(data) {
  const placeholder = document.getElementById('results-placeholder');
  const content = document.getElementById('results-content');
  placeholder.classList.add('hidden');
  content.classList.remove('hidden');
  content.innerHTML = '';

  if (data.error) {
    content.innerHTML = `<p class="status-fail">Error: ${data.error}</p>`;
    return;
  }

  const servers = data.servers || {};
  for (const [name, srv] of Object.entries(servers)) {
    const card = document.createElement('div');
    card.className = `result-server ${srv.reachable ? 'reachable' : 'unreachable'}`;
    let html = `<h4>${name} (${srv.host}) — ${srv.reachable ? 'Reachable' : 'Unreachable'}</h4>`;
    if (srv.error) html += `<p class="status-fail">${srv.error}</p>`;
    if (srv.checks) {
      for (const [k, v] of Object.entries(srv.checks)) {
        const status = v.status || 'info';
        const msg = v.message || (v.findings && v.findings[0]) || '';
        html += `<div class="result-check"><span>${k.replace(/_/g, ' ')}</span><span class="status-${status}">${status} ${msg}</span></div>`;
      }
    }
    if (srv.lynis && srv.lynis.status !== 'n/a') {
      html += `<div class="result-check"><span>Lynis</span><span>Index: ${srv.lynis.hardening_index || 'N/A'}</span></div>`;
    }
    card.innerHTML = html;
    content.appendChild(card);
  }

  const network = data.network_scans || {};
  for (const [tool, result] of Object.entries(network)) {
    const card = document.createElement('div');
    card.className = 'result-server';
    card.innerHTML = `<h4>${tool.toUpperCase()}</h4><p>${result.message || result.status || ''}</p>`;
    content.appendChild(card);
  }
}
