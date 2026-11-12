(function () {
  const { api } = window.HC;

  async function render(container) {
    container.innerHTML = `<div class="page-header"><div><h2>Dashboard</h2><p>Welcome to HappyCrypt.</p></div></div><div class="card">Loading...</div>`;
    try {
      const d = await api('/api/security/dashboard');
      container.innerHTML = `
        <div class="page-header">
          <div>
            <h2>Dashboard</h2>
            <p>Security overview of your local vault.</p>
          </div>
          <div class="header-actions">
            <button class="btn secondary" data-nav="vault">Open Vault</button>
            <button class="btn primary" data-nav="generator">Generate Password</button>
          </div>
        </div>
        <div class="grid cards-4 section">
          <div class="card"><h3>Total Credentials</h3><div class="metric">${d.total_credentials}</div><div class="muted small">In your vault</div></div>
          <div class="card"><h3>Weak Passwords</h3><div class="metric bad">${d.weak_passwords}</div><div class="muted small">Should be improved</div></div>
          <div class="card"><h3>Reused Passwords</h3><div class="metric warn">${d.reused_passwords}</div><div class="muted small">Unique passwords recommended</div></div>
          <div class="card"><h3>Strong Passwords</h3><div class="metric good">${d.strong_passwords}</div><div class="muted small">Overall ${d.overall?.score ?? 0}/100</div></div>
        </div>
        <div class="grid two section">
          <div class="card">
            <div class="section-title"><h3>Recently Added</h3></div>
            ${d.recently_added.length ? `<div class="list">${d.recently_added.map(i=>`<div class="list-item"><div><div class="title">${window.HC.esc(i.website_name)}</div><div class="sub">${new Date(i.created_at).toLocaleString()}</div></div></div>`).join('')}</div>` : `<div class="empty-state">No credentials yet.</div>`}
          </div>
          <div class="card">
            <div class="section-title"><h3>Recently Modified</h3></div>
            ${d.recently_modified.length ? `<div class="list">${d.recently_modified.map(i=>`<div class="list-item"><div><div class="title">${window.HC.esc(i.website_name)}</div><div class="sub">${new Date(i.updated_at).toLocaleString()}</div></div></div>`).join('')}</div>` : `<div class="empty-state">No recent changes.</div>`}
          </div>
        </div>
      `;
      container.querySelectorAll('[data-nav]').forEach(b => b.onclick = () => window.HC.app.navigate(b.dataset.nav));
    } catch (e) {
      container.innerHTML = `<div class="card"><div class="error-text">${window.HC.esc(e.message)}</div></div>`;
    }
  }

  window.HC.dashboard = { render };
})();
