(function () {
  const { api, apiBlob } = window.HC;

  async function render(container) {
    container.innerHTML = `<div class="page-header"><div><h2>Settings</h2><p>Configure HappyCrypt on this device.</p></div></div><div class="card">Loading...</div>`;
    try {
      const data = await api('/api/settings');
      const s = data.settings || {};
      container.innerHTML = `
        <div class="page-header"><div><h2>Settings</h2><p>Local preferences, security, and backup controls.</p></div></div>
        <div class="grid two">
          <div class="card">
            <h3>Preferences</h3>
            <div class="form-grid">
              <div class="field">
                <label>Theme</label>
                <select class="select" id="set-theme">
                  <option value="dark" ${s.theme==='dark'?'selected':''}>Dark</option>
                  <option value="light" ${s.theme==='light'?'selected':''}>Light</option>
                </select>
              </div>
              <div class="field">
                <label>Auto-lock timeout (minutes)</label>
                <input class="input" type="number" min="1" max="240" id="set-autolock" value="${Number(s.auto_lock_minutes||10)}" />
              </div>
              <div class="field">
                <label>Clipboard clear timeout (seconds)</label>
                <input class="input" type="number" min="5" max="300" id="set-clipboard" value="${Number(s.clipboard_clear_seconds||20)}" />
              </div>
              <button class="btn primary" id="save-settings">Save Settings</button>
              <div id="settings-msg" class="helper"></div>
            </div>
          </div>
          <div class="card">
            <h3>Application Information</h3>
            <div class="kv">
              <div class="k">App</div><div class="v">${window.HC.esc(data.app.name)} v${window.HC.esc(data.app.version)}</div>
              <div class="k">Mode</div><div class="v"><span class="pill good">Offline / Local-only</span></div>
              <div class="k">Database location</div><div class="v"><span class="inline-code">${window.HC.esc(data.app.database_path)}</span></div>
              <div class="k">Backup directory</div><div class="v"><span class="inline-code">${window.HC.esc(data.app.backup_dir)}</span></div>
            </div>
          </div>
        </div>

        <div class="grid two section">
          <div class="card">
            <h3>Change Master Password</h3>
            <form id="change-master-form" class="form-grid">
              <div class="field"><label>Current Master Password</label><input class="input" type="password" name="current" required /></div>
              <div class="field"><label>New Master Password</label><input class="input" type="password" name="next" minlength="8" required /></div>
              <div class="field"><label>Confirm New Master Password</label><input class="input" type="password" name="confirm" minlength="8" required /></div>
              <div id="change-msg" class="helper"></div>
              <button class="btn primary" type="submit">Change Password</button>
              <div class="helper">Changing the master password re-encrypts the vault and logs you out.</div>
            </form>
          </div>
          <div class="card">
            <h3>Backup & Restore</h3>
            <p class="helper">Backups are encrypted and exported locally. Plaintext credentials are never exported.</p>
            <div class="form-grid">
              <button class="btn secondary" id="export-backup">Export Encrypted Backup</button>
              <div class="divider"></div>
              <div class="field">
                <label>Import Encrypted Backup (.json)</label>
                <input class="input" type="file" id="import-file" accept="application/json,.json" />
              </div>
              <button class="btn danger" id="import-backup">Import Backup (Replaces Current Vault)</button>
              <div id="backup-msg" class="helper"></div>
            </div>
          </div>
        </div>
      `;

      container.querySelector('#save-settings').onclick = async () => {
        const msg = container.querySelector('#settings-msg'); msg.textContent = '';
        try {
          const payload = {
            theme: container.querySelector('#set-theme').value,
            auto_lock_minutes: Number(container.querySelector('#set-autolock').value),
            clipboard_clear_seconds: Number(container.querySelector('#set-clipboard').value),
          };
          const res = await api('/api/settings', { method: 'PUT', body: JSON.stringify(payload) });
          window.HC.app.applySettings(res.settings);
          msg.textContent = 'Settings saved.';
          window.HC.toast('Settings saved', 'success');
        } catch (e) { msg.textContent = e.message; window.HC.toast(e.message, 'error'); }
      };

      container.querySelector('#change-master-form').onsubmit = async (e) => {
        e.preventDefault();
        const msg = container.querySelector('#change-msg'); msg.textContent = '';
        const fd = new FormData(e.target);
        const current = fd.get('current'), next = fd.get('next'), confirm = fd.get('confirm');
        if (next !== confirm) { msg.textContent = 'New passwords do not match.'; return; }
        try {
          await window.HC.auth.changeMaster(current, next, confirm);
          window.HC.toast('Master password changed. Please log in again.', 'success');
          await window.HC.app.bootstrap();
        } catch (ex) { msg.textContent = ex.message; }
      };

      container.querySelector('#export-backup').onclick = async () => {
        const msg = container.querySelector('#backup-msg'); msg.textContent = '';
        try {
          const blob = await apiBlob('/api/backup/export');
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = 'happycrypt-backup.json'; document.body.appendChild(a); a.click(); a.remove();
          URL.revokeObjectURL(url);
          window.HC.toast('Encrypted backup exported', 'success');
        } catch (e) { msg.textContent = e.message; window.HC.toast(e.message, 'error'); }
      };

      container.querySelector('#import-backup').onclick = async () => {
        const msg = container.querySelector('#backup-msg'); msg.textContent = '';
        const file = container.querySelector('#import-file').files[0];
        if (!file) { msg.textContent = 'Select a backup file first.'; return; }
        if (!confirm('Importing a backup will replace the current vault on this device. Continue?')) return;
        try {
          const text = await file.text();
          // send base64
          const b64 = btoa(unescape(encodeURIComponent(text)));
          const res = await api('/api/backup/import', { method: 'POST', body: JSON.stringify({ backup_base64: b64 }) });
          window.HC.toast(res.message || 'Backup imported. Please log in again.', 'success');
          await window.HC.app.bootstrap();
        } catch (e) { msg.textContent = e.message; window.HC.toast(e.message, 'error'); }
      };

    } catch (e) {
      container.innerHTML = `<div class="card"><div class="error-text">${window.HC.esc(e.message)}</div></div>`;
    }
  }

  window.HC.settings = { render };
})();
