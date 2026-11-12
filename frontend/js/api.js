(function () {
  async function api(path, options = {}) {
    const opts = {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    };
    // Let browser set content-type for FormData if ever used
    if (opts.body instanceof FormData) delete opts.headers['Content-Type'];
    const res = await fetch(path, opts);
    const ct = res.headers.get('content-type') || '';
    let data = null;
    if (ct.includes('application/json')) {
      data = await res.json().catch(() => null);
    } else if (ct.includes('text/') || ct.includes('application/octet-stream')) {
      // for exports we may want blob; caller can handle via apiBlob
      data = await res.text().catch(() => null);
    }
    if (!res.ok) {
      const msg = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
      const err = new Error(msg);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  async function apiBlob(path, options = {}) {
    const opts = { credentials: 'include', ...(options) };
    const res = await fetch(path, opts);
    if (!res.ok) {
      let msg = `Request failed (${res.status})`;
      try { const d = await res.json(); msg = d.detail || d.message || msg; } catch {}
      const err = new Error(msg); err.status = res.status; throw err;
    }
    return res.blob();
  }

  window.HC = window.HC || {};
  window.HC.api = api;
  window.HC.apiBlob = apiBlob;
})();
