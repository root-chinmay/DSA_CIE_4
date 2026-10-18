// frontend/js/components/settings.js - Configuration, Shared Folders & System Diagnostics

const SettingsComponent = {
  logsData: [],

  async render() {
    const el = document.getElementById('view-settings');
    if (!el) return;

    const host = State.hostInfo;
    const folders = State.folders || [];

    try {
      this.logsData = await API.getLogs(50);
    } catch (_) {}

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h2 class="page-title">Settings & Network Diagnostics</h2>
          <p class="page-subtitle">Configure LAN parameters, shared folder directories, and audit logging</p>
        </div>
      </div>

      <div class="grid-split" style="margin-bottom: 24px;">
        <!-- Left: Configuration Form -->
        <div class="glass-card">
          <div class="card-title-bar">
            <h3 class="card-title"><span>⚙</span> Device & LAN Configuration</h3>
          </div>
          <form onsubmit="SettingsComponent.saveSettings(event)" style="display: flex; flex-direction: column; gap: 16px;">
            <div>
              <label style="font-size: 12px; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 6px;">
                Device Name
              </label>
              <input type="text" class="search-input" id="cfg-device-name" value="${host.device_name}" required />
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
              <div>
                <label style="font-size: 12px; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 6px;">
                  Server Port
                </label>
                <input type="number" class="search-input" id="cfg-port" value="${host.port}" required />
              </div>
              <div>
                <label style="font-size: 12px; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 6px;">
                  Chunk Size (MB)
                </label>
                <input type="number" min="1" max="16" class="search-input" id="cfg-chunk" value="${host.chunk_size_mb || 2}" required />
              </div>
            </div>

            <div>
              <label style="font-size: 12px; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 6px;">
                Max Concurrent Transfers
              </label>
              <input type="number" min="1" max="10" class="search-input" id="cfg-max-tx" value="${host.max_concurrent_transfers || 3}" required />
            </div>

            <div style="display: flex; justify-content: flex-end; margin-top: 8px;">
              <button type="submit" class="btn btn-primary">
                Save Configuration
              </button>
            </div>
          </form>
        </div>

        <!-- Right: Demo Mode Toggle & Security Info -->
        <div class="glass-card">
          <div class="card-title-bar">
            <h3 class="card-title"><span>🧪</span> Simulation & Evaluation Mode</h3>
          </div>
          <div style="margin-bottom: 20px;">
            <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 14px; line-height: 1.5;">
              Demo Mode simulates three laptops (Laptop-A, Laptop-B, Laptop-C) on a virtual LAN for single-machine presentation of graph routing, priority heaps, and sync conflicts.
            </p>
            <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(15, 23, 42, 0.6); padding: 14px 18px; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
              <div>
                <strong style="font-size: 14px;">Academic Demo Mode</strong>
                <div style="font-size: 12px; color: var(--text-muted);">
                  ${host.demo_mode ? 'Currently ACTIVE with simulated peer nodes' : 'Currently DISABLED (Normal offline LAN mode)'}
                </div>
              </div>
              <button class="btn ${host.demo_mode ? 'btn-danger' : 'btn-primary'}" onclick="App.toggleDemoMode()">
                ${host.demo_mode ? 'Deactivate Demo' : 'Activate Demo'}
              </button>
            </div>
          </div>

          <div class="card-title-bar" style="margin-top: 24px;">
            <h3 class="card-title"><span>🔐</span> Security & Pairing Code</h3>
          </div>
          <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(15, 23, 42, 0.6); padding: 14px 18px; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
            <div>
              <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">6-Digit Pairing Code</div>
              <div style="font-family: var(--font-mono); font-size: 20px; font-weight: 800; color: #d8b4fe;">${host.pairing_code}</div>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="App.resetPairingCode()">
              Reset Code
            </button>
          </div>
        </div>
      </div>

      <!-- Shared Folder Paths Management -->
      <div class="glass-card" style="margin-bottom: 24px;">
        <div class="card-title-bar">
          <div>
            <h3 class="card-title"><span>📁</span> Shared Folder Directories</h3>
            <p style="font-size: 12px; color: var(--text-muted);">Folders accessible to paired LAN clients (directory traversal strictly blocked outside these paths).</p>
          </div>
        </div>

        <!-- Add Folder Input -->
        <form onsubmit="SettingsComponent.addFolder(event)" style="display: flex; gap: 10px; margin-bottom: 18px;">
          <input type="text" class="search-input" id="new-folder-path-input" placeholder="Enter absolute folder path (e.g. D:\\SharedFiles or C:\\Users\\...)..." required style="flex: 1;" />
          <input type="text" class="search-input" id="new-folder-name-input" placeholder="Display Name (optional)" style="width: 220px;" />
          <button type="submit" class="btn btn-primary">Add Folder</button>
        </form>

        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Display Name</th>
                <th>Physical Disk Path</th>
                <th>Status</th>
                <th>File Count</th>
                <th>Total Size</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${folders.map(f => `
                <tr>
                  <td><strong>${f.folder_name}</strong></td>
                  <td><code>${f.folder_path}</code></td>
                  <td><span class="pill pill-synced">ACTIVE</span></td>
                  <td>${f.file_count || 0} files</td>
                  <td>${DashboardComponent.formatBytes(f.total_size || 0)}</td>
                  <td>
                    <button class="btn btn-danger btn-sm" onclick="SettingsComponent.removeFolder(${f.id})">
                      Remove
                    </button>
                  </td>
                </tr>
              `).join('')}
              ${folders.length === 0 ? `
                <tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 20px;">No shared folders configured.</td></tr>
              ` : ''}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Recent Audit Logs -->
      <div class="glass-card" style="padding: 0;">
        <div class="card-title-bar" style="padding: 18px 20px 0;">
          <h3 class="card-title"><span>📜</span> System Operation Audit Logs</h3>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Device</th>
                <th>Operation</th>
                <th>File</th>
                <th>Status</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              ${(this.logsData || []).map(l => `
                <tr>
                  <td style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">
                    ${new Date((l.timestamp || 0) * 1000).toLocaleTimeString()}
                  </td>
                  <td><code>${l.device || 'Local'}</code></td>
                  <td><strong>${l.operation}</strong></td>
                  <td>${l.file_name || '-'}</td>
                  <td>
                    <span class="pill ${l.status === 'SUCCESS' ? 'pill-synced' : (l.status === 'ERROR' || l.status === 'ALERT' ? 'pill-conflict' : (l.status === 'WARN' ? 'pill-modified' : 'pill-priority-2'))}">
                      ${l.status}
                    </span>
                  </td>
                  <td style="font-size: 12px; color: var(--text-secondary);">${l.message || ''}</td>
                </tr>
              `).join('')}
              ${(!this.logsData || this.logsData.length === 0) ? `
                <tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 20px;">No logs recorded yet.</td></tr>
              ` : ''}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  async saveSettings(e) {
    e.preventDefault();
    const name = document.getElementById('cfg-device-name').value.trim();
    const port = parseInt(document.getElementById('cfg-port').value);
    const chunk = parseInt(document.getElementById('cfg-chunk').value);
    const maxTx = parseInt(document.getElementById('cfg-max-tx').value);

    try {
      const res = await API.updateSettings({
        device_name: name,
        port: port,
        chunk_size_mb: chunk,
        max_transfers: maxTx
      });
      State.setHostInfo(res.settings);
      App.showToast('Settings successfully updated!', 'success');
      this.render();
    } catch (err) {
      App.showToast(`Failed to update settings: ${err.message}`, 'error');
    }
  },

  async addFolder(e) {
    e.preventDefault();
    const path = document.getElementById('new-folder-path-input').value.trim();
    const name = document.getElementById('new-folder-name-input').value.trim();

    try {
      await API.addFolder(path, name || null);
      App.showToast(`Registered shared folder: ${name || path}`, 'success');
      App.refreshFolders();
      App.refreshFiles();
      this.render();
    } catch (err) {
      App.showToast(`Failed to add folder: ${err.message}`, 'error');
    }
  },

  async removeFolder(folderId) {
    if (confirm('Unregister this shared folder from LAN sharing?')) {
      try {
        await API.removeFolder(folderId);
        App.showToast('Shared folder unregistered.', 'success');
        App.refreshFolders();
        App.refreshFiles();
        this.render();
      } catch (err) {
        App.showToast(`Failed to remove folder: ${err.message}`, 'error');
      }
    }
  }
};
