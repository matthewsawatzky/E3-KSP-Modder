// ── State ──
let currentPath = null;
let currentMods = [];
let currentLogFilter = 'all';
let noteEditMod = null;
let selectedMods = new Set();
let appSettings = {};

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  loadSettings().then(() => loadCurrentPath());
});

// ── Tabs ──
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      const tab = document.getElementById('tab-' + btn.dataset.tab);
      tab.classList.add('active');
      onTabActivated(btn.dataset.tab);
    });
  });
}

function onTabActivated(tab) {
  if (!currentPath && tab !== 'settings') {
    checkPath(tab === 'mods' ? 'mods' : tab);
    return;
  }
  switch (tab) {
    case 'settings': loadCurrentPath(); break;
    case 'mods': loadMods(); loadProfiles(); break;
    case 'saves': loadSaves(); break;
    case 'log': loadLogs(); break;
    case 'info': loadInfo(); break;
  }
}

// ── Toast ──
function toast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  const icon = type === 'success' ? '\u2713' : '\u2717';
  el.innerHTML = '<span class="toast-icon">' + icon + '</span><span>' + escHtml(message) + '</span>';
  container.appendChild(el);
  setTimeout(() => { el.remove(); }, 4000);
}

// ── Spinner ──
let spinnerCount = 0;
function showSpinner() {
  spinnerCount++;
  document.getElementById('spinner').classList.remove('hidden');
}
function hideSpinner() {
  spinnerCount = Math.max(0, spinnerCount - 1);
  if (spinnerCount === 0) document.getElementById('spinner').classList.add('hidden');
}

// ── API helper ──
async function api(url, options = {}) {
  showSpinner();
  try {
    const resp = await fetch(url, options);
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.error || 'Request failed');
    }
    return data;
  } finally {
    hideSpinner();
  }
}

// ── HTML escape ──
function escHtml(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Check path for non-settings tabs ──
function checkPath(tabName) {
  const noPath = document.getElementById(tabName + '-no-path');
  const content = document.getElementById(tabName + '-content');
  if (!currentPath) {
    if (noPath) noPath.classList.remove('hidden');
    if (content) content.style.display = 'none';
    return false;
  }
  if (noPath) noPath.classList.add('hidden');
  if (content) content.style.display = '';
  return true;
}

// ══════════════════════════════════════
// SETTINGS
// ══════════════════════════════════════

async function loadSettings() {
  try {
    appSettings = await api('/api/settings');
    applyAccentColor(appSettings.accent_color || '#8AC04A');

    const colorInput = document.getElementById('accent-color-input');
    const hexInput = document.getElementById('accent-color-hex');
    if (colorInput) colorInput.value = appSettings.accent_color || '#8AC04A';
    if (hexInput) hexInput.value = appSettings.accent_color || '#8AC04A';

    const sortSelect = document.getElementById('sort-mods-select');
    if (sortSelect) sortSelect.value = appSettings.sort_mods_by || 'name';

    const confirmCb = document.getElementById('confirm-remove-cb');
    if (confirmCb) confirmCb.checked = appSettings.confirm_remove !== false;

    const logLines = document.getElementById('log-lines-input');
    if (logLines) logLines.value = appSettings.log_lines || 500;

    updateSwatchActive(appSettings.accent_color || '#8AC04A');
  } catch (e) {
    // use defaults
  }
}

function applyAccentColor(color) {
  if (!color || !color.match(/^#[0-9A-Fa-f]{6}$/)) return;
  const r = parseInt(color.slice(1,3), 16);
  const g = parseInt(color.slice(3,5), 16);
  const b = parseInt(color.slice(5,7), 16);
  const hoverR = Math.min(255, r + 20);
  const hoverG = Math.min(255, g + 20);
  const hoverB = Math.min(255, b + 20);
  const hover = '#' + [hoverR, hoverG, hoverB].map(c => c.toString(16).padStart(2, '0')).join('');

  document.documentElement.style.setProperty('--accent', color);
  document.documentElement.style.setProperty('--accent-hover', hover);
  document.documentElement.style.setProperty('--accent-alpha', `rgba(${r},${g},${b},0.2)`);
  document.documentElement.style.setProperty('--success', color);
}

function previewAccentColor(color) {
  applyAccentColor(color);
  document.getElementById('accent-color-hex').value = color;
  updateSwatchActive(color);
}

function onHexInput(val) {
  if (val.match(/^#[0-9A-Fa-f]{6}$/)) {
    document.getElementById('accent-color-input').value = val;
    applyAccentColor(val);
    updateSwatchActive(val);
  }
}

function setAccentPreset(color) {
  document.getElementById('accent-color-input').value = color;
  document.getElementById('accent-color-hex').value = color;
  applyAccentColor(color);
  updateSwatchActive(color);
}

function updateSwatchActive(color) {
  document.querySelectorAll('.color-swatch').forEach(s => {
    s.classList.toggle('active', s.style.background.toLowerCase() === color.toLowerCase() ||
      rgbToHex(s.style.backgroundColor) === color.toLowerCase());
  });
}

function rgbToHex(rgb) {
  const m = rgb.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
  if (!m) return '';
  return '#' + [m[1],m[2],m[3]].map(n => parseInt(n).toString(16).padStart(2,'0')).join('');
}

async function saveSetting(key, value) {
  appSettings[key] = value;
}

async function saveAllSettings() {
  const settings = {
    accent_color: document.getElementById('accent-color-hex').value,
    sort_mods_by: document.getElementById('sort-mods-select').value,
    confirm_remove: document.getElementById('confirm-remove-cb').checked,
    log_lines: parseInt(document.getElementById('log-lines-input').value) || 500,
  };
  try {
    const data = await api('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    appSettings = data.settings;
    toast('Settings saved');
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function resetSettings() {
  setAccentPreset('#8AC04A');
  document.getElementById('sort-mods-select').value = 'name';
  document.getElementById('confirm-remove-cb').checked = true;
  document.getElementById('log-lines-input').value = 500;
  await saveAllSettings();
}

// ══════════════════════════════════════
// SETUP (inside Settings tab)
// ══════════════════════════════════════

async function loadCurrentPath() {
  try {
    const data = await api('/api/current-path');
    currentPath = data.path;
    const el = document.getElementById('current-path-display');
    if (data.path) {
      el.textContent = data.path;
      if (data.exists) {
        el.className = 'current-path set';
      } else {
        el.className = 'current-path missing';
        el.textContent = data.path + '  (folder not found!)';
      }
      loadGameVersion();
    } else {
      el.textContent = 'No KSP install selected';
      el.className = 'current-path';
      document.getElementById('game-version-display').textContent = '';
    }
  } catch (e) {
    document.getElementById('current-path-display').textContent = 'Error loading path';
  }
}

async function loadGameVersion() {
  try {
    const data = await api('/api/info');
    document.getElementById('game-version-display').textContent = 'Game version: ' + data.version;
  } catch (e) {
    document.getElementById('game-version-display').textContent = '';
  }
}

async function detectInstalls() {
  try {
    const installs = await api('/api/detect-installs');
    const list = document.getElementById('installs-list');
    if (installs.length === 0) {
      list.innerHTML = '<div class="empty-state">No KSP installs detected automatically. Use the manual path option below.</div>';
      return;
    }
    list.innerHTML = installs.map(inst =>
      '<div class="card">' +
        '<div class="card-info">' +
          '<div class="card-label">' + escHtml(inst.label) + '</div>' +
          '<div class="card-path">' + escHtml(inst.path) + '</div>' +
        '</div>' +
        '<button class="btn btn-primary btn-sm" onclick="selectInstall(\'' + escHtml(inst.path).replace(/'/g, "\\'").replace(/\\/g, "\\\\") + '\')">Select</button>' +
      '</div>'
    ).join('');
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function selectInstall(path) {
  try {
    await api('/api/set-path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    });
    toast('KSP path set successfully');
    loadCurrentPath();
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function setManualPath() {
  const input = document.getElementById('manual-path');
  const path = input.value.trim();
  if (!path) {
    toast('Please enter a path', 'error');
    return;
  }
  try {
    await api('/api/set-path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    });
    toast('KSP path set successfully');
    input.value = '';
    loadCurrentPath();
  } catch (e) {
    toast(e.message, 'error');
  }
}

// ══════════════════════════════════════
// MODS TAB
// ══════════════════════════════════════

async function loadMods() {
  if (!checkPath('mods')) return;
  try {
    const data = await api('/api/mods');
    currentMods = data.mods;
    document.getElementById('mod-count').textContent = data.total_count + ' mods';
    document.getElementById('mod-total-size').textContent = data.total_size_mb + ' MB (GameData)';
    sortMods(currentMods);
    renderModTable(currentMods);
    clearSelection();
  } catch (e) {
    toast(e.message, 'error');
  }
}

function sortMods(mods) {
  const sortBy = appSettings.sort_mods_by || 'name';
  switch (sortBy) {
    case 'name':
      mods.sort((a, b) => a.name.localeCompare(b.name));
      break;
    case 'name_desc':
      mods.sort((a, b) => b.name.localeCompare(a.name));
      break;
    case 'size':
      mods.sort((a, b) => b.size_mb - a.size_mb);
      break;
    case 'status':
      mods.sort((a, b) => (b.enabled ? 1 : 0) - (a.enabled ? 1 : 0) || a.name.localeCompare(b.name));
      break;
  }
}

function renderModTable(mods) {
  const tbody = document.getElementById('mod-tbody');
  if (mods.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No mods found in GameData</td></tr>';
    return;
  }
  tbody.innerHTML = mods.map(mod => {
    const statusBadge = mod.enabled
      ? '<span class="badge badge-enabled">Enabled</span>'
      : '<span class="badge badge-disabled">Disabled</span>';
    const conflictCell = mod.conflicts && mod.conflicts.length > 0
      ? '<span class="conflict-icon" title="Conflicts with: ' + escHtml(mod.conflicts.map(c => c.shared_with.join(', ')).join('; ')) + '">\u26A0</span>'
      : '';
    const noteText = mod.note
      ? '<span class="note-preview" onclick="openNoteModal(\'' + escHtml(mod.name).replace(/'/g, "\\'") + '\')" title="' + escHtml(mod.note) + '">' + escHtml(mod.note.substring(0, 40)) + (mod.note.length > 40 ? '...' : '') + '</span>'
      : '<span class="note-add" onclick="openNoteModal(\'' + escHtml(mod.name).replace(/'/g, "\\'") + '\')">+ note</span>';
    const toggleLabel = mod.enabled ? 'Disable' : 'Enable';
    const checked = selectedMods.has(mod.name) ? ' checked' : '';
    const rowClass = selectedMods.has(mod.name) ? ' selected' : '';

    return '<tr data-mod="' + escHtml(mod.name.toLowerCase()) + '" data-modname="' + escHtml(mod.name) + '" class="' + rowClass + '">' +
      '<td><input type="checkbox" class="mod-cb" data-name="' + escHtml(mod.name) + '"' + checked + ' onchange="onModCheckbox(this)"></td>' +
      '<td><strong>' + escHtml(mod.name) + '</strong></td>' +
      '<td>' + (mod.version || '-') + '</td>' +
      '<td>' + mod.size_mb + ' MB</td>' +
      '<td>' + statusBadge + '</td>' +
      '<td>' + conflictCell + '</td>' +
      '<td>' + noteText + '</td>' +
      '<td class="mod-actions">' +
        '<button class="btn btn-sm" onclick="toggleMod(\'' + escHtml(mod.name).replace(/'/g, "\\'") + '\')">' + toggleLabel + '</button>' +
        '<button class="btn btn-sm btn-danger" onclick="removeMod(\'' + escHtml(mod.name).replace(/'/g, "\\'") + '\')">Remove</button>' +
      '</td>' +
    '</tr>';
  }).join('');
}

function filterMods() {
  const query = document.getElementById('mod-search').value.toLowerCase();
  document.querySelectorAll('#mod-tbody tr').forEach(row => {
    const name = row.getAttribute('data-mod') || '';
    row.classList.toggle('hidden-row', !name.includes(query));
  });
}

// ── Selection / Bulk ──

function onModCheckbox(cb) {
  const name = cb.dataset.name;
  if (cb.checked) {
    selectedMods.add(name);
    cb.closest('tr').classList.add('selected');
  } else {
    selectedMods.delete(name);
    cb.closest('tr').classList.remove('selected');
  }
  updateBulkBar();
}

function toggleSelectAll() {
  const headerCb = document.getElementById('header-select-all');
  const selectAllCb = document.getElementById('select-all-cb');
  const checked = headerCb ? headerCb.checked : (selectAllCb ? selectAllCb.checked : false);

  // sync both checkboxes
  if (headerCb) headerCb.checked = checked;
  if (selectAllCb) selectAllCb.checked = checked;

  const visibleRows = document.querySelectorAll('#mod-tbody tr:not(.hidden-row)');
  visibleRows.forEach(row => {
    const cb = row.querySelector('.mod-cb');
    if (!cb) return;
    const name = cb.dataset.name;
    cb.checked = checked;
    if (checked) {
      selectedMods.add(name);
      row.classList.add('selected');
    } else {
      selectedMods.delete(name);
      row.classList.remove('selected');
    }
  });
  updateBulkBar();
}

function clearSelection() {
  selectedMods.clear();
  document.querySelectorAll('.mod-cb').forEach(cb => { cb.checked = false; });
  document.querySelectorAll('#mod-tbody tr').forEach(row => row.classList.remove('selected'));
  const headerCb = document.getElementById('header-select-all');
  const selectAllCb = document.getElementById('select-all-cb');
  if (headerCb) headerCb.checked = false;
  if (selectAllCb) selectAllCb.checked = false;
  updateBulkBar();
}

function updateBulkBar() {
  const count = selectedMods.size;
  const bar = document.getElementById('bulk-bar');
  const countEl = document.getElementById('bulk-count-num');
  const selectedCountSpan = document.getElementById('mod-selected-count');
  const selectedNum = document.getElementById('selected-num');

  if (count > 0) {
    bar.classList.remove('hidden');
    countEl.textContent = count;
    selectedCountSpan.classList.remove('hidden');
    selectedNum.textContent = count;
  } else {
    bar.classList.add('hidden');
    selectedCountSpan.classList.add('hidden');
  }
}

async function bulkAction(action) {
  if (selectedMods.size === 0) {
    toast('No mods selected', 'error');
    return;
  }

  const names = Array.from(selectedMods);
  const confirmRemove = appSettings.confirm_remove !== false;

  if (action === 'remove' && confirmRemove) {
    if (!confirm('Remove ' + names.length + ' mod(s)? This cannot be undone.\n\n' + names.join(', '))) return;
  }

  try {
    const data = await api('/api/mods/bulk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, mods: names })
    });

    const verb = action === 'enable' ? 'enabled' : action === 'disable' ? 'disabled' : 'removed';
    toast(data.affected.length + ' mod(s) ' + verb);
    if (data.errors.length > 0) {
      toast('Errors: ' + data.errors.join(', '), 'error');
    }
    loadMods();
  } catch (e) {
    toast(e.message, 'error');
  }
}

// ── Single mod actions ──

async function toggleMod(name) {
  try {
    const data = await api('/api/mods/' + encodeURIComponent(name) + '/toggle', { method: 'POST' });
    toast(name + ' ' + (data.enabled ? 'enabled' : 'disabled'));
    loadMods();
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function removeMod(name) {
  const confirmRemove = appSettings.confirm_remove !== false;
  if (confirmRemove && !confirm('Remove mod "' + name + '"? This cannot be undone.')) return;
  try {
    const data = await api('/api/mods/' + encodeURIComponent(name), { method: 'DELETE' });
    let msg = name + ' removed';
    if (data.warning) msg += ' (' + data.warning + ')';
    toast(msg);
    loadMods();
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function uploadMod() {
  const input = document.getElementById('mod-file-input');
  if (!input.files.length) return;

  const formData = new FormData();
  formData.append('file', input.files[0]);

  showSpinner();
  try {
    const resp = await fetch('/api/mods/add', { method: 'POST', body: formData });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'Upload failed');
    toast('Added: ' + data.added.join(', '));
    loadMods();
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    hideSpinner();
    input.value = '';
  }
}

// ── Export ──
function exportMods() {
  if (!currentMods.length) {
    toast('No mods to export', 'error');
    return;
  }

  const date = new Date().toISOString().slice(0, 10);
  const enabled = currentMods.filter(m => m.enabled).length;
  const disabled = currentMods.length - enabled;

  const COL_NAME = 40;
  const COL_VER  = 12;
  const COL_ST   = 10;
  const COL_SIZE = 10;

  const pad = (s, n) => String(s).padEnd(n);
  const header = pad('Mod Name', COL_NAME) + pad('Version', COL_VER) + pad('Status', COL_ST) + 'Size (MB)';
  const divider = '-'.repeat(COL_NAME + COL_VER + COL_ST + COL_SIZE);

  const lines = [
    'KSP Mod List Export',
    'Date: ' + date,
    'Total: ' + currentMods.length + ' mods (' + enabled + ' enabled, ' + disabled + ' disabled)',
    '',
    header,
    divider,
    ...currentMods.map(m =>
      pad(m.name, COL_NAME) +
      pad(m.version || 'N/A', COL_VER) +
      pad(m.enabled ? 'Enabled' : 'Disabled', COL_ST) +
      m.size_mb
    )
  ];

  const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'ksp-mods-' + date + '.txt';
  a.click();
  URL.revokeObjectURL(url);
  toast('Mod list exported');
}

// ── Notes ──
function openNoteModal(modName) {
  noteEditMod = modName;
  document.getElementById('note-modal-mod').textContent = modName;
  const mod = currentMods.find(m => m.name === modName);
  document.getElementById('note-modal-text').value = mod ? (mod.note || '') : '';
  document.getElementById('note-modal').classList.remove('hidden');
  document.getElementById('note-modal-text').focus();
}

function closeNoteModal() {
  document.getElementById('note-modal').classList.add('hidden');
  noteEditMod = null;
}

async function saveNote() {
  if (!noteEditMod) return;
  const note = document.getElementById('note-modal-text').value;
  try {
    await api('/api/mods/notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mod: noteEditMod, note })
    });
    toast('Note saved');
    closeNoteModal();
    loadMods();
  } catch (e) {
    toast(e.message, 'error');
  }
}

// ── Profiles ──
async function loadProfiles() {
  try {
    const profiles = await api('/api/profiles');
    const select = document.getElementById('profile-select');
    const names = Object.keys(profiles);
    select.innerHTML = '<option value="">-- Select Profile --</option>' +
      names.map(n => '<option value="' + escHtml(n) + '">' + escHtml(n) + ' (' + profiles[n].length + ' mods)</option>').join('');
  } catch (e) {
    // silent
  }
}

async function saveProfile() {
  const name = document.getElementById('profile-name').value.trim();
  if (!name) {
    toast('Enter a profile name', 'error');
    return;
  }
  try {
    const data = await api('/api/profiles/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    toast('Profile "' + name + '" saved (' + data.mods.length + ' mods)');
    document.getElementById('profile-name').value = '';
    loadProfiles();
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function loadProfile() {
  const select = document.getElementById('profile-select');
  const name = select.value;
  if (!name) {
    toast('Select a profile first', 'error');
    return;
  }
  try {
    await api('/api/profiles/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    toast('Profile "' + name + '" applied');
    loadMods();
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function deleteProfile() {
  const select = document.getElementById('profile-select');
  const name = select.value;
  if (!name) {
    toast('Select a profile first', 'error');
    return;
  }
  if (!confirm('Delete profile "' + name + '"?')) return;
  try {
    await api('/api/profiles/' + encodeURIComponent(name), { method: 'DELETE' });
    toast('Profile "' + name + '" deleted');
    loadProfiles();
  } catch (e) {
    toast(e.message, 'error');
  }
}

// ══════════════════════════════════════
// SAVES TAB
// ══════════════════════════════════════

async function loadSaves() {
  if (!checkPath('saves')) return;
  try {
    const saves = await api('/api/saves');
    const list = document.getElementById('saves-list');
    if (saves.length === 0) {
      list.innerHTML = '<div class="empty-state">No save games found</div>';
      return;
    }
    list.innerHTML = saves.map(save => {
      let backupsHtml = '';
      if (save.backups && save.backups.length > 0) {
        backupsHtml = '<div class="save-backups"><h4>Backups</h4>' +
          save.backups.map(b =>
            '<div class="backup-item">' + escHtml(b.filename) + ' (' + b.size_mb + ' MB, ' + escHtml(b.created) + ')</div>'
          ).join('') + '</div>';
      }
      return '<div class="save-card">' +
        '<div class="save-header">' +
          '<span class="save-name">' + escHtml(save.name) + '</span>' +
          '<button class="btn btn-primary btn-sm" onclick="backupSave(\'' + escHtml(save.name).replace(/'/g, "\\'") + '\')">Backup</button>' +
        '</div>' +
        '<div class="save-meta">' + save.size_mb + ' MB &middot; Modified: ' + escHtml(save.modified) + '</div>' +
        backupsHtml +
      '</div>';
    }).join('');
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function backupSave(name) {
  try {
    const data = await api('/api/saves/' + encodeURIComponent(name) + '/backup', { method: 'POST' });
    toast('Backup created: ' + data.filename + ' (' + data.size_mb + ' MB)');
    loadSaves();
  } catch (e) {
    toast(e.message, 'error');
  }
}

// ══════════════════════════════════════
// LOG TAB
// ══════════════════════════════════════

function setLogFilter(filter) {
  currentLogFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === filter);
  });
  loadLogs();
}

async function loadLogs() {
  if (!checkPath('log')) return;
  try {
    const data = await api('/api/logs?filter=' + currentLogFilter);
    const output = document.getElementById('log-output');
    const info = document.getElementById('log-info');

    if (data.path) {
      info.textContent = 'Log file: ' + data.path + ' | Total lines: ' + (data.total_lines || '?') + ' | Showing: ' + data.lines.length;
    } else {
      info.textContent = '';
    }

    if (data.error && data.lines.length === 0) {
      output.textContent = data.error;
    } else {
      output.textContent = data.lines.join('\n');
    }

    output.scrollTop = output.scrollHeight;
  } catch (e) {
    document.getElementById('log-output').textContent = 'Error loading log: ' + e.message;
  }
}

// ══════════════════════════════════════
// INFO TAB
// ══════════════════════════════════════

async function loadInfo() {
  if (!checkPath('info')) return;
  loadDiskInfo();
  loadScreenshots();
  loadCrafts();
}

async function loadDiskInfo() {
  try {
    const data = await api('/api/info');
    document.getElementById('info-version').innerHTML =
      '<strong>Game Version:</strong> ' + escHtml(data.version) +
      '<br><strong>Install Path:</strong> <span style="font-family:monospace;font-size:0.9em;">' + escHtml(data.path) + '</span>';

    const usage = data.disk_usage;
    const total = usage.Total || 1;
    const grid = document.getElementById('disk-usage');

    const items = Object.entries(usage).map(([name, mb]) => {
      const pct = Math.max(2, Math.round((mb / total) * 100));
      return '<div class="disk-item">' +
        '<div class="disk-item-label">' + escHtml(name) + '</div>' +
        '<div class="disk-item-value">' + mb + ' MB</div>' +
        '<div class="disk-item-bar"><div class="disk-item-bar-fill" style="width:' + pct + '%"></div></div>' +
      '</div>';
    });
    grid.innerHTML = items.join('');
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function loadScreenshots() {
  try {
    const screenshots = await api('/api/screenshots');
    const gallery = document.getElementById('screenshots-gallery');
    if (screenshots.length === 0) {
      gallery.innerHTML = '<div class="empty-state">No screenshots found</div>';
      return;
    }
    gallery.innerHTML = screenshots.map(ss =>
      '<div class="gallery-thumb" onclick="openLightbox(\'/screenshots/' + encodeURIComponent(ss.filename) + '\')">' +
        '<img src="/screenshots/' + encodeURIComponent(ss.filename) + '" alt="' + escHtml(ss.filename) + '" loading="lazy">' +
        '<div class="gallery-name">' + escHtml(ss.filename) + ' (' + ss.size_mb + ' MB)</div>' +
      '</div>'
    ).join('');
  } catch (e) {
    document.getElementById('screenshots-gallery').innerHTML = '<div class="empty-state">Could not load screenshots</div>';
  }
}

async function loadCrafts() {
  try {
    const crafts = await api('/api/crafts');
    const tbody = document.getElementById('crafts-tbody');
    if (crafts.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No craft files found</td></tr>';
      return;
    }
    tbody.innerHTML = crafts.map(c =>
      '<tr>' +
        '<td>' + escHtml(c.name) + '</td>' +
        '<td><span class="badge ' + (c.type === 'VAB' ? 'badge-enabled' : 'badge-disabled') + '">' + c.type + '</span></td>' +
        '<td>' + c.size_kb + ' KB</td>' +
        '<td>' + escHtml(c.modified) + '</td>' +
      '</tr>'
    ).join('');
  } catch (e) {
    document.getElementById('crafts-tbody').innerHTML = '<tr><td colspan="4" class="empty-state">Could not load crafts</td></tr>';
  }
}

// ── Mod Error Scan ──

async function scanModErrors() {
  if (!currentPath) {
    toast('No KSP path set', 'error');
    return;
  }
  const container = document.getElementById('mod-errors-results');
  container.innerHTML = '<div class="empty-state">Scanning log…</div>';
  try {
    const data = await api('/api/logs/mod-errors');
    renderModErrors(data);
  } catch (e) {
    toast(e.message, 'error');
    container.innerHTML = '<div class="empty-state">' + escHtml(e.message) + '</div>';
  }
}

function renderModErrors(data) {
  const container = document.getElementById('mod-errors-results');

  if (data.error) {
    container.innerHTML = '<div class="empty-state">' + escHtml(data.error) + '</div>';
    return;
  }

  const entries = Object.entries(data.results);

  if (entries.length === 0) {
    container.innerHTML =
      '<div class="empty-state" style="padding:20px 0;">No mod-related errors found in the log ✓</div>';
    return;
  }

  let html =
    '<div class="mod-errors-summary">' +
      '<span class="mod-errors-stat">' + entries.length + ' mod' + (entries.length !== 1 ? 's' : '') + ' with errors</span>' +
      '<span class="sep">|</span>' +
      '<span class="mod-errors-stat">' + data.total_errors + ' total error lines</span>' +
      (data.unattributed_count > 0
        ? '<span class="sep">|</span><span class="mod-errors-stat">' + data.unattributed_count + ' unattributed</span>'
        : '') +
    '</div>';

  html += entries.map(([modName, info]) => {
    const hasMore = info.total > info.lines.length;
    const errLines = info.lines.map(l =>
      '<div class="mod-error-line">' + escHtml(l) + '</div>'
    ).join('');
    const moreNote = hasMore
      ? '<div class="mod-error-more">… and ' + (info.total - info.lines.length) + ' more error' + (info.total - info.lines.length !== 1 ? 's' : '') + ' (showing first ' + info.lines.length + ')</div>'
      : '';

    return (
      '<div class="mod-error-card">' +
        '<div class="mod-error-header" onclick="toggleModErrorCard(this)">' +
          '<span class="mod-error-name">' + escHtml(modName) + '</span>' +
          '<span class="mod-error-count">' + info.total + ' error' + (info.total !== 1 ? 's' : '') + '</span>' +
          '<span class="mod-error-arrow">&#9654;</span>' +
        '</div>' +
        '<div class="mod-error-lines collapsed">' + errLines + moreNote + '</div>' +
      '</div>'
    );
  }).join('');

  container.innerHTML = html;
}

function toggleModErrorCard(header) {
  const lines = header.nextElementSibling;
  const arrow = header.querySelector('.mod-error-arrow');
  const nowCollapsed = lines.classList.toggle('collapsed');
  arrow.innerHTML = nowCollapsed ? '&#9654;' : '&#9660;';
}

// ── Lightbox ──
function openLightbox(src) {
  document.getElementById('lightbox-img').src = src;
  document.getElementById('lightbox').classList.remove('hidden');
}

function closeLightbox() {
  document.getElementById('lightbox').classList.add('hidden');
  document.getElementById('lightbox-img').src = '';
}

// ── Keyboard shortcuts ──
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeNoteModal();
    closeLightbox();
  }
});
