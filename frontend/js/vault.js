(function () {
  const { api } = window.HC;

  async function list(q = '', sort = 'updated_desc') {
    const params = new URLSearchParams({ q, sort });
    return api(`/api/credentials?${params.toString()}`);
  }
  async function get(id) { return api(`/api/credentials/${id}`); }
  async function create(data) { return api('/api/credentials', { method: 'POST', body: JSON.stringify(data) }); }
  async function update(id, data) { return api(`/api/credentials/${id}`, { method: 'PUT', body: JSON.stringify(data) }); }
  async function remove(id) { return api(`/api/credentials/${id}`, { method: 'DELETE' }); }

  function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

  function credentialModal(mode, data = {}) {
    const isEdit = mode === 'edit';
    const title = isEdit ? 'Edit Credential' : 'Add Credential';
    return `
      <div class="modal-backdrop" id="modal-backdrop">
        <div class="modal">
          <div class="modal-header">
            <h3>${title}</h3>
            <button class="btn ghost sm" id="modal-close">✕</button>
          </div>
          <form id="cred-form">
            <div class="modal-body">
              <div class="form-cols">
                <div class="field">
                  <label>Website/Application Name *</label>
                  <input class="input" name="website_name" required value="${esc(data.website_name||'')}" />
                </div>
                <div class="field">
                  <label>Website URL</label>
                  <input class="input" name="website_url" value="${esc(data.website_url||'')}" placeholder="https://..." />
                </div>
                <div class="field">
                  <label>Username</label>
                  <input class="input" name="username" value="${esc(data.username||'')}" />
                </div>
                <div class="field">
                  <label>Email (optional)</label>
                  <input class="input" name="email" type="email" value="${esc(data.email||'')}" />
                </div>
              </div>
              <div class="field" style="margin-top:12px;">
                <label>Password *</label>
                <div class="row">
                  <input class="input mono" id="cred-password" name="password" type="password" required value="${esc(data.password||'')}" />
                  <button class="btn secondary sm" type="button" id="toggle-pass">Show</button>
                  <button class="btn secondary sm" type="button" id="gen-pass">Generate</button>
                </div>
              </div>
              <div class="field" style="margin-top:12px;">
                <label>Notes (optional)</label>
                <textarea class="textarea" name="notes">${esc(data.notes||'')}</textarea>
              </div>
              <div id="cred-error" class="error-text" style="margin-top:8px;"></div>
            </div>
            <div class="modal-footer">
              <button class="btn secondary" type="button" id="modal-cancel">Cancel</button>
              <button class="btn primary" type="submit">${isEdit ? 'Save Changes' : 'Add Credential'}</button>
            </div>
          </form>
        </div>
      </div>`;
  }

  function viewModal(data) {
    return `
      <div class="modal-backdrop" id="modal-backdrop">
        <div class="modal">
          <div class="modal-header">
            <h3>Credential Details</h3>
            <button class="btn ghost sm" id="modal-close">✕</button>
          </div>
          <div class="modal-body">
            <div class="kv">
              <div class="k">Website/App</div><div class="v">${esc(data.website_name)}</div>
              <div class="k">URL</div><div class="v">${data.website_url ? `<a href="${esc(data.website_url)}" target="_blank" rel="noreferrer">${esc(data.website_url)}</a>` : '<span class="muted">—</span>'}</div>
              <div class="k">Username</div><div class="v row"><span>${esc(data.username || '—')}</span> ${data.username ? `<button class="btn sm secondary" data-copy="${esc(data.username)}">Copy</button>`:''}</div>
              <div class="k">Email</div><div class="v">${esc(data.email || '—')}</div>
              <div class="k">Password</div>
              <div class="v row">
                <span id="detail-pass" class="mono masked">••••••••••••</span>
                <button class="btn sm secondary" id="detail-toggle">Show</button>
                <button class="btn sm secondary" data-copy="${esc(data.password)}">Copy</button>
              </div>
              <div class="k">Notes</div><div class="v">${data.notes ? esc(data.notes) : '<span class="muted">—</span>'}</div>
              <div class="k">Created</div><div class="v">${new Date(data.created_at).toLocaleString()}</div>
              <div class="k">Last Modified</div><div class="v">${new Date(data.updated_at).toLocaleString()}</div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn secondary" id="modal-cancel">Close</button>
          </div>
        </div>
      </div>`;
  }

  function confirmModal(message) {
    return `
      <div class="modal-backdrop" id="modal-backdrop">
        <div class="modal" style="max-width:460px;">
          <div class="modal-header"><h3>Confirm Delete</h3><button class="btn ghost sm" id="modal-close">✕</button></div>
          <div class="modal-body"><p>${esc(message)}</p></div>
          <div class="modal-footer">
            <button class="btn secondary" id="modal-cancel">Cancel</button>
            <button class="btn danger" id="confirm-yes">Delete</button>
          </div>
        </div>
      </div>`;
  }

  function openModal(html) {
    const root = document.getElementById('modal-root');
    root.innerHTML = html;
    const close = () => { root.innerHTML = ''; };
    root.querySelectorAll('#modal-close,#modal-cancel,#modal-backdrop').forEach(el => {
      el.addEventListener('click', (e) => { if (el.id === 'modal-backdrop' && e.target !== el) return; close(); });
    });
    return { close, root };
  }

  async function render(container, state = {}) {
    const q = state.q || '';
    const sort = state.sort || 'updated_desc';
    const data = await list(q, sort);
    container.innerHTML = `
      <div class="page-header">
        <div>
          <h2>Password Vault</h2>
          <p>Manage your encrypted credentials locally. ${data.count} item${data.count===1?'':'s'}.</p>
        </div>
        <div class="header-actions">
          <button class="btn primary" id="add-cred-btn">Add Credential</button>
        </div>
      </div>
      <div class="card">
        <div class="toolbar">
          <input class="input" id="vault-search" placeholder="Search by website, URL, username, or email" value="${esc(q)}" />
          <select class="select" id="vault-sort">
            <option value="updated_desc" ${sort==='updated_desc'?'selected':''}>Recently modified</option>
            <option value="created_desc" ${sort==='created_desc'?'selected':''}>Recently added</option>
            <option value="name_asc" ${sort==='name_asc'?'selected':''}>Name (A–Z)</option>
            <option value="name_desc" ${sort==='name_desc'?'selected':''}>Name (Z–A)</option>
            <option value="updated_asc" ${sort==='updated_asc'?'selected':''}>Oldest modified</option>
          </select>
          <div class="spacer"></div>
        </div>
        ${data.items.length === 0 ? `<div class="empty-state">No credentials found. Add your first credential to get started.</div>` : `
        <div class="table-wrap">
          <table class="vault">
            <thead><tr><th>Website/Application</th><th>Username</th><th>Password</th><th>Updated</th><th>Actions</th></tr></thead>
            <tbody>
              ${data.items.map(i => `
                <tr data-id="${i.id}">
                  <td>
                    <div class="title">${esc(i.website_name)}</div>
                    <div class="sub">${esc(i.website_url || i.email || '')}</div>
                  </td>
                  <td>${esc(i.username || '—')}</td>
                  <td><span class="mono masked">••••••••••••</span></td>
                  <td class="small muted">${new Date(i.updated_at).toLocaleString()}</td>
                  <td>
                    <div class="actions">
                      <button class="btn sm secondary" data-action="view">View</button>
                      <button class="btn sm secondary" data-action="copy-user">Copy User</button>
                      <button class="btn sm secondary" data-action="copy-pass">Copy Pass</button>
                      <button class="btn sm secondary" data-action="edit">Edit</button>
                      <button class="btn sm danger" data-action="delete">Delete</button>
                    </div>
                  </td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>`}
      </div>
    `;

    const rerender = (patch={}) => render(container, { q: document.getElementById('vault-search')?.value ?? q, sort: document.getElementById('vault-sort')?.value ?? sort, ...patch });
    document.getElementById('vault-search').addEventListener('input', window.HC.debounce((e) => rerender({ q: e.target.value }), 250));
    document.getElementById('vault-sort').addEventListener('change', (e) => rerender({ sort: e.target.value }));
    document.getElementById('add-cred-btn').onclick = () => showAddEdit('add', null, rerender);

    container.querySelectorAll('tr[data-id]').forEach(row => {
      const id = row.dataset.id;
      row.querySelectorAll('[data-action]').forEach(btn => {
        btn.onclick = async () => {
          const action = btn.dataset.action;
          try {
            if (action === 'view') {
              const detail = await get(id);
              const m = openModal(viewModal(detail));
              const passEl = m.root.querySelector('#detail-pass');
              const toggle = m.root.querySelector('#detail-toggle');
              let shown = false;
              toggle.onclick = () => { shown = !shown; passEl.textContent = shown ? detail.password : '••••••••••••'; passEl.classList.toggle('masked', !shown); toggle.textContent = shown ? 'Hide' : 'Show'; };
              m.root.querySelectorAll('[data-copy]').forEach(b => b.onclick = () => window.HC.copyText(b.dataset.copy));
            } else if (action === 'copy-user') {
              const detail = await get(id);
              window.HC.copyText(detail.username || '');
            } else if (action === 'copy-pass') {
              const detail = await get(id);
              window.HC.copyText(detail.password || '');
            } else if (action === 'edit') {
              const detail = await get(id);
              showAddEdit('edit', detail, rerender);
            } else if (action === 'delete') {
              const detail = await get(id);
              const m = openModal(confirmModal(`Delete credential for "${detail.website_name}"? This cannot be undone.`));
              m.root.querySelector('#confirm-yes').onclick = async () => {
                await remove(id);
                m.close();
                window.HC.toast('Credential deleted', 'success');
                rerender();
              };
            }
          } catch (e) { window.HC.toast(e.message, 'error'); }
        };
      });
    });
  }

  function showAddEdit(mode, data, onDone) {
    const m = openModal(credentialModal(mode, data || {}));
    const pass = m.root.querySelector('#cred-password');
    const toggle = m.root.querySelector('#toggle-pass');
    toggle.onclick = () => { const show = pass.type === 'password'; pass.type = show ? 'text' : 'password'; toggle.textContent = show ? 'Hide' : 'Show'; };
    m.root.querySelector('#gen-pass').onclick = async () => {
      try {
        const r = await api('/api/generator/generate', { method: 'POST', body: JSON.stringify({ length: 20, uppercase: true, lowercase: true, numbers: true, special: true }) });
        pass.value = r.password; pass.type = 'text'; toggle.textContent = 'Hide';
      } catch (e) { window.HC.toast(e.message, 'error'); }
    };
    m.root.querySelector('#cred-form').onsubmit = async (e) => {
      e.preventDefault();
      const err = m.root.querySelector('#cred-error'); err.textContent = '';
      const fd = new FormData(e.target);
      const payload = Object.fromEntries(fd.entries());
      try {
        if (mode === 'edit') await update(data.id, payload); else await create(payload);
        m.close();
        window.HC.toast(mode === 'edit' ? 'Credential updated' : 'Credential added', 'success');
        onDone();
      } catch (ex) { err.textContent = ex.message; }
    };
  }

  window.HC.vault = { render, list, get };
})();
