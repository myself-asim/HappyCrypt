(function () {
  const { api } = window.HC;

  async function getStatus() {
    return api('/api/auth/status');
  }
  async function setup(master_password, confirm_password) {
    return api('/api/auth/setup', { method: 'POST', body: JSON.stringify({ master_password, confirm_password }) });
  }
  async function login(master_password) {
    return api('/api/auth/login', { method: 'POST', body: JSON.stringify({ master_password }) });
  }
  async function unlock(master_password) {
    return api('/api/auth/unlock', { method: 'POST', body: JSON.stringify({ master_password }) });
  }
  async function lock() {
    return api('/api/auth/lock', { method: 'POST' });
  }
  async function logout() {
    return api('/api/auth/logout', { method: 'POST' });
  }
  async function changeMaster(current_password, new_password, confirm_new_password) {
    return api('/api/auth/change-master', {
      method: 'POST',
      body: JSON.stringify({ current_password, new_password, confirm_new_password }),
    });
  }

  function authShell(innerHtml, subtitle = '') {
    return `
      <div class="auth-wrap">
        <div class="auth-card">
          <div class="auth-brand">
            <div class="logo">HC</div>
            <div>
              <h1 style="margin:0;font-size:1.1rem;">HappyCrypt</h1>
              <div class="tagline">Your Passwords. Your Privacy. Your Control.</div>
            </div>
          </div>
          ${subtitle ? `<p class="lead">${subtitle}</p>` : ''}
          ${innerHtml}
        </div>
      </div>`;
  }

  function renderWelcome(root) {
    root.innerHTML = authShell(`
      <h2>Welcome</h2>
      <p class="lead">A fully local, encrypted password manager. Your vault stays on this computer.</p>
      <div class="form-grid">
        <button class="btn primary block" id="go-setup">Create Master Password</button>
        <div class="helper">No cloud. No internet required. Everything runs on 127.0.0.1.</div>
      </div>
    `, '');
    document.getElementById('go-setup').onclick = () => window.HC.app.showSetup();
  }

  function renderSetup(root) {
    root.innerHTML = authShell(`
      <h2>Create Master Password</h2>
      <p class="lead">This password protects your vault. It cannot be recovered if lost.</p>
      <form id="setup-form" class="form-grid">
        <div class="field">
          <label>Master Password</label>
          <input class="input" type="password" name="master" minlength="8" required autocomplete="new-password" />
          <div class="helper">Use at least 8 characters (longer is stronger).</div>
        </div>
        <div class="field">
          <label>Confirm Master Password</label>
          <input class="input" type="password" name="confirm" minlength="8" required autocomplete="new-password" />
        </div>
        <div id="setup-error" class="error-text"></div>
        <button class="btn primary block" type="submit">Create Vault</button>
      </form>
    `);
    document.getElementById('setup-form').onsubmit = async (e) => {
      e.preventDefault();
      const err = document.getElementById('setup-error');
      err.textContent = '';
      const fd = new FormData(e.target);
      const master = fd.get('master');
      const confirm = fd.get('confirm');
      if (master !== confirm) { err.textContent = 'Passwords do not match.'; return; }
      try {
        await setup(master, confirm);
        window.HC.toast('Vault created and unlocked', 'success');
        await window.HC.app.bootstrap();
      } catch (ex) { err.textContent = ex.message; }
    };
  }

  function renderLogin(root) {
    root.innerHTML = authShell(`
      <h2>Unlock HappyCrypt</h2>
      <p class="lead">Enter your master password to access your local vault.</p>
      <form id="login-form" class="form-grid">
        <div class="field">
          <label>Master Password</label>
          <input class="input" type="password" name="master" required autocomplete="current-password" />
        </div>
        <div id="login-error" class="error-text"></div>
        <button class="btn primary block" type="submit">Login</button>
      </form>
    `);
    document.getElementById('login-form').onsubmit = async (e) => {
      e.preventDefault();
      const err = document.getElementById('login-error'); err.textContent = '';
      const master = new FormData(e.target).get('master');
      try {
        await login(master);
        window.HC.toast('Welcome back', 'success');
        await window.HC.app.bootstrap();
      } catch (ex) { err.textContent = ex.message || 'Invalid master password'; }
    };
  }

  function renderLocked(root) {
    root.innerHTML = authShell(`
      <h2>Vault Locked</h2>
      <p class="lead">Your session is locked. Enter your master password to continue.</p>
      <form id="unlock-form" class="form-grid">
        <div class="field">
          <label>Master Password</label>
          <input class="input" type="password" name="master" required autocomplete="current-password" />
        </div>
        <div id="unlock-error" class="error-text"></div>
        <button class="btn primary block" type="submit">Unlock Vault</button>
        <button class="btn secondary block" type="button" id="logout-btn">Logout</button>
      </form>
    `);
    document.getElementById('unlock-form').onsubmit = async (e) => {
      e.preventDefault();
      const err = document.getElementById('unlock-error'); err.textContent = '';
      const master = new FormData(e.target).get('master');
      try {
        await unlock(master);
        window.HC.toast('Vault unlocked', 'success');
        await window.HC.app.bootstrap();
      } catch (ex) { err.textContent = ex.message || 'Invalid master password'; }
    };
    document.getElementById('logout-btn').onclick = async () => {
      await logout();
      await window.HC.app.bootstrap();
    };
  }

  window.HC.auth = { getStatus, setup, login, unlock, lock, logout, changeMaster, renderWelcome, renderSetup, renderLogin, renderLocked };
})();
