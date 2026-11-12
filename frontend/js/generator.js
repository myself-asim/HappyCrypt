(function () {
  const { api } = window.HC;

  function strengthClass(score){ return 's' + Math.max(0, Math.min(4, Number(score)||0)); }

  async function render(container) {
    container.innerHTML = `
      <div class="page-header">
        <div><h2>Password Generator</h2><p>Create strong, random passwords locally using secure randomness.</p></div>
      </div>
      <div class="grid two">
        <div class="card">
          <h3>Generator Options</h3>
          <div class="form-grid">
            <div class="field">
              <label>Length: <span id="len-val" class="mono">16</span></label>
              <input class="input" type="range" id="gen-length" min="4" max="64" value="16" />
            </div>
            <div class="switch-row"><span>Uppercase letters (A–Z)</span><input type="checkbox" id="opt-upper" checked></div>
            <div class="switch-row"><span>Lowercase letters (a–z)</span><input type="checkbox" id="opt-lower" checked></div>
            <div class="switch-row"><span>Numbers (0–9)</span><input type="checkbox" id="opt-num" checked></div>
            <div class="switch-row"><span>Special characters</span><input type="checkbox" id="opt-special" checked></div>
            <div class="switch-row"><span>Exclude ambiguous characters</span><input type="checkbox" id="opt-amb"></div>
            <div class="row" style="margin-top:8px;">
              <button class="btn primary" id="gen-btn">Generate Password</button>
              <button class="btn secondary" id="regen-btn">Regenerate</button>
            </div>
            <div id="gen-error" class="error-text"></div>
          </div>
        </div>
        <div class="card">
          <h3>Generated Password</h3>
          <div class="field">
            <input class="input mono" id="gen-output" readonly placeholder="Click generate" />
          </div>
          <div class="row" style="margin-top:10px;">
            <button class="btn secondary" id="copy-gen">Copy Password</button>
          </div>
          <div class="divider"></div>
          <div class="section">
            <div class="row space"><span class="muted">Strength</span><span id="gen-label" class="pill">—</span></div>
            <div class="strength-bar" style="margin-top:8px;"><span id="gen-bar"></span></div>
            <ul id="gen-issues" class="small muted" style="margin:10px 0 0 18px; padding:0;"></ul>
          </div>
        </div>
      </div>
    `;

    const len = container.querySelector('#gen-length');
    const lenVal = container.querySelector('#len-val');
    len.oninput = () => lenVal.textContent = len.value;

    async function doGenerate() {
      const err = container.querySelector('#gen-error'); err.textContent = '';
      const payload = {
        length: Number(len.value),
        uppercase: container.querySelector('#opt-upper').checked,
        lowercase: container.querySelector('#opt-lower').checked,
        numbers: container.querySelector('#opt-num').checked,
        special: container.querySelector('#opt-special').checked,
        exclude_ambiguous: container.querySelector('#opt-amb').checked,
      };
      try {
        const res = await api('/api/generator/generate', { method: 'POST', body: JSON.stringify(payload) });
        container.querySelector('#gen-output').value = res.password;
        const a = res.analysis || {};
        const label = container.querySelector('#gen-label');
        label.textContent = a.label || '—';
        label.className = 'pill ' + (a.score >= 3 ? 'good' : a.score === 2 ? 'warn' : 'bad');
        const bar = container.querySelector('#gen-bar');
        bar.className = strengthClass(a.score);
        const issues = container.querySelector('#gen-issues');
        issues.innerHTML = (a.issues && a.issues.length) ? a.issues.map(i=>`<li>${window.HC.esc(i)}</li>`).join('') : '<li>No major issues detected.</li>';
      } catch (e) { err.textContent = e.message; }
    }

    container.querySelector('#gen-btn').onclick = doGenerate;
    container.querySelector('#regen-btn').onclick = doGenerate;
    container.querySelector('#copy-gen').onclick = () => window.HC.copyText(container.querySelector('#gen-output').value);
    await doGenerate();
  }

  window.HC.generator = { render };
})();
