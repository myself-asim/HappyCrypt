(function () {
  const { auth, dashboard, vault, generator, security, settings, api } = window.HC;
  const root = document.getElementById('app-root');

  const state = {
    view: 'dashboard',
    auth: { initialized: false, logged_in: false, locked: true },
    settings: { theme: 'dark', auto_lock_minutes: 10, clipboard_clear_seconds: 20 },
    clipboardTimer: null,
  };

  function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function debounce(fn, ms){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), ms); }; }
  function toast(message, type='success') {
    const wrap = document.getElementById('toast-root');
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = message;
    wrap.appendChild(el);
    setTimeout(()=>{ el.remove(); }, 3200);
  }
  async function copyText(text) {
    try {
      if (!text) { toast('Nothing to copy', 'warn'); return; }
      await navigator.clipboard.writeText(text);
      toast('Copied to clipboard', 'success');
      if (state.clipboardTimer) clearTimeout(state.clipboardTimer);
      const secs = Number(state.settings.clipboard_clear_seconds || 20);
      state.clipboardTimer = setTimeout(async () => {
        try { await navigator.clipboard.writeText(''); } catch {}
      }, Math.max(5, secs) * 1000);
    } catch (e) {
      toast('Clipboard copy failed', 'error');
    }
  }

  function applySettings(s) {
    state.settings = { ...state.settings, ...(s||{}) };
    document.documentElement.setAttribute('data-theme', state.settings.theme || 'dark');
  }

  async function loadSettingsIfPossible() {
    try {
      const res = await api('/api/settings');
      if (res && res.settings) applySettings(res.settings);
    } catch {}
  }

  function layout(contentHtml) {
    return `
      <div class="app-shell">
        <aside class="sidebar">
          <div class="brand">
            <div class="logo">HC</div>
            <div>
              <h1>HappyCrypt</h1>
              <p class="tagline">Your Passwords. Your Privacy. Your Control.</p>
            </div>
          </div>
          <nav class="nav" id="main-nav">
            ${navItem('dashboard','Dashboard')}
            ${navItem('vault','Password Vault')}
            ${navItem('generator','Password Generator')}
            ${navItem('security','Security Center')}
            ${navItem('settings','Settings')}
          </nav>
          <div class="nav-spacer"></div>
          <button class="nav-item danger" id="lock-btn"><span class="dot"></span>Lock Vault</button>
        </aside>
        <main class="main" id="main-content">${contentHtml || ''}</main>
      </div>`;
  }

  function navItem(id, label) {
    const active = state.view === id ? 'active' : '';
    return `<button class="nav-item ${active}" data-view="${id}"><span class="dot"></span>${label}</button>`;
  }

  async function navigate(view) {
    state.view = view;
    await renderApp();
  }

  async function renderApp() {
    // auth states
    const st = state.auth;
    if (!st.initialized) { auth.renderWelcome(root); return; }
    if (!st.logged_in) { auth.renderLogin(root); return; }
    if (st.locked) { auth.renderLocked(root); return; }

    root.innerHTML = layout('<div class="card">Loading...</div>');
    root.querySelectorAll('[data-view]').forEach(btn => btn.onclick = () => navigate(btn.dataset.view));
    root.querySelector('#lock-btn').onclick = async () => {
      try { await auth.lock(); toast('Vault locked', 'success'); } catch (e) { toast(e.message, 'error'); }
      await bootstrap();
    };

    const main = root.querySelector('#main-content');
    try {
      if (state.view === 'dashboard') await dashboard.render(main);
      else if (state.view === 'vault') await vault.render(main, {});
      else if (state.view === 'generator') await generator.render(main);
      else if (state.view === 'security') await security.render(main);
      else if (state.view === 'settings') await settings.render(main);
      else await dashboard.render(main);
    } catch (e) {
      if (e && (e.status === 401 || e.status === 423)) { await bootstrap(); return; }
      main.innerHTML = `<div class="card"><div class="error-text">${esc(e.message || 'Error')}</div></div>`;
    }
  }

  async function bootstrap() {
    try {
      state.auth = await auth.getStatus();
      // show setup screen when uninitialized but allow welcome->setup flow
      if (!state.auth.initialized) { auth.renderWelcome(root); return; }
      if (state.auth.logged_in && !state.auth.locked) await loadSettingsIfPossible();
      await renderApp();
    } catch (e) {
      root.innerHTML = `<div class="auth-wrap"><div class="auth-card"><h2>HappyCrypt</h2><p class="error-text">Unable to reach local backend.</p><p class="helper">Start the app with <code>python run.py</code>.</p></div></div>`;
    }
  }

  function showSetup() { auth.renderSetup(root); }

  window.HC.esc = esc;
  window.HC.debounce = debounce;
  window.HC.toast = toast;
  window.HC.copyText = copyText;
  window.HC.app = { bootstrap, navigate, showSetup, applySettings, state };

  // Periodic status check to reflect auto-lock
  setInterval(async () => {
    try {
      const st = await auth.getStatus();
      const prev = JSON.stringify(state.auth);
      state.auth = st;
      if (JSON.stringify(st) !== prev) {
        // if became locked/unauthed while in app, rerender
        if (st.initialized) await renderApp();
      }
    } catch {}
  }, 15000);

  bootstrap();
})();
