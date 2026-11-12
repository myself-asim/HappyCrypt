(function () {
  const { api } = window.HC;

  async function render(container) {
    container.innerHTML = `<div class="page-header"><div><h2>Security Center</h2><p>Local analysis of your vault's password health.</p></div></div><div class="card">Loading...</div>`;
    try {
      const d = await api('/api/security/dashboard');
      const score = d.overall?.score ?? 0;
      container.innerHTML = `
        <div class="page-header">
          <div><h2>Security Center</h2><p>Local analysis of your vault's password health. No data leaves this device.</p></div>
        </div>
        <div class="grid cards-4 section">
          <div class="card"><h3>Total Credentials</h3><div class="metric">${d.total_credentials}</div><div class="muted small">Stored locally</div></div>
          <div class="card"><h3>Weak / Medium</h3><div class="metric bad">${d.weak_passwords}</div><div class="muted small">Need attention</div></div>
          <div class="card"><h3>Reused Passwords</h3><div class="metric warn">${d.reused_passwords}</div><div class="muted small">Used more than once</div></div>
          <div class="card"><h3>Strong / Very Strong</h3><div class="metric good">${d.strong_passwords}</div><div class="muted small">Overall score ${score}/100</div></div>
        </div>
        <div class="grid two section">
          <div class="card">
            <div class="section-title"><h3>Weak Passwords</h3></div>
            ${d.weak_items.length ? `<div class="list">${d.weak_items.map(i=>`<div class="list-item"><div><div class="title">${window.HC.esc(i.website_name)}</div><div class="sub">Strength: ${window.HC.esc(i.label)}</div></div><span class="pill bad">${window.HC.esc(i.label)}</span></div>`).join('')}</div>` : `<div class="empty-state">No weak passwords detected.</div>`}
          </div>
          <div class="card">
            <div class="section-title"><h3>Reused Passwords</h3></div>
            ${d.reused_items.length ? `<div class="list">${d.reused_items.map(i=>`<div class="list-item"><div><div class="title">${window.HC.esc(i.website_name)}</div><div class="sub">Reused ${i.count} times</div></div><span class="pill warn">Reused</span></div>`).join('')}</div>` : `<div class="empty-state">No reused passwords detected.</div>`}
          </div>
        </div>
        <div class="card section">
          <div class="section-title"><h3>Potentially Outdated Passwords</h3></div>
          <p class="helper">Credentials not modified in over 180 days (local heuristic, not breach evidence).</p>
          ${d.potentially_outdated_items.length ? `<div class="list">${d.potentially_outdated_items.map(i=>`<div class="list-item"><div><div class="title">${window.HC.esc(i.website_name)}</div><div class="sub">Last modified ${new Date(i.updated_at).toLocaleString()}</div></div><span class="pill warn">Outdated</span></div>`).join('')}</div>` : `<div class="empty-state">No potentially outdated passwords.</div>`}
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><div class="error-text">${window.HC.esc(e.message)}</div></div>`;
    }
  }

  window.HC.security = { render };
})();
