// frontend/js/components/dashboard.js - Overview & Quick Stats View

const DashboardComponent = {
  render() {
    const el = document.getElementById('view-dashboard');
    if (!el) return;

    const host = State.hostInfo;
    const files = State.files || [];
    const devices = State.devices || [];
    const onlineDevs = devices.filter(d => d.status === 'online');
    const transfers = State.transfers || { active_tasks: [], history: [] };
    const duplicates = State.duplicates || [];

    const totalBytes = files.reduce((acc, f) => acc + (f.size || 0), 0);
    const totalStorageStr = this.formatBytes(totalBytes);

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h2 class="page-title">Offline LAN Dashboard</h2>
          <p class="page-subtitle">Zero-Internet peer-to-peer file sharing and synchronization system</p>
        </div>
        <div>
          <button class="btn btn-secondary btn-sm" onclick="App.runDiagnosticsModal()">
            <span>🔍</span> Network Diagnostics
          </button>
        </div>
      </div>

      <!-- Quick Metrics Grid -->
      <div class="grid-cards">
        <div class="glass-card stat-card">
          <div class="stat-icon emerald">📡</div>
          <div>
            <div class="stat-val" style="font-size: 20px;">${host.ip_address || '127.0.0.1'}</div>
            <div class="stat-label">Local LAN IP</div>
          </div>
        </div>

        <div class="glass-card stat-card">
          <div class="stat-icon cyan">💻</div>
          <div>
            <div class="stat-val">${onlineDevs.length}</div>
            <div class="stat-label">Devices Online</div>
          </div>
        </div>

        <div class="glass-card stat-card">
          <div class="stat-icon purple">📁</div>
          <div>
            <div class="stat-val">${files.length}</div>
            <div class="stat-label">Shared Files</div>
          </div>
        </div>

        <div class="glass-card stat-card">
          <div class="stat-icon amber">💾</div>
          <div>
            <div class="stat-val" style="font-size: 20px;">${totalStorageStr}</div>
            <div class="stat-label">Shared Storage</div>
          </div>
        </div>

        <div class="glass-card stat-card">
          <div class="stat-icon rose">👯</div>
          <div>
            <div class="stat-val">${duplicates.length}</div>
            <div class="stat-label">Duplicate Groups</div>
          </div>
        </div>
      <!-- Direct IP Transfer & Mobile Connect Showcase Banner -->
      <div class="glass-card" style="margin-bottom: 24px; background: linear-gradient(135deg, rgba(0, 240, 255, 0.08), rgba(157, 78, 221, 0.08)); border: 1px solid rgba(0, 240, 255, 0.3);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
          <div style="display: flex; align-items: center; gap: 16px;">
            <div style="font-size: 36px; background: rgba(0, 240, 255, 0.15); width: 56px; height: 56px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; border: 1px solid rgba(0, 240, 255, 0.3);">
              📱
            </div>
            <div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <h3 style="font-size: 17px; font-weight: 700; color: #fff;">Offline IP File Transfer & Mobile Portal</h3>
                <span class="pill pill-synced" style="font-size: 10px;">ZERO INTERNET</span>
              </div>
              <p style="font-size: 13px; color: var(--text-secondary); margin-top: 3px;">
                Transfer files to/from any phone, tablet, or laptop on this Wi-Fi router or hotspot using its IP address.
              </p>
            </div>
          </div>
          <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <button class="btn btn-primary" onclick="App.navigate('ip-transfer')">
              <span>🌐</span> Open IP Transfer
            </button>
            <button class="btn btn-secondary" onclick="App.navigate('ip-transfer'); setTimeout(() => IPTransferComponent.runSubnetScan(), 100);">
              <span>🔍</span> Scan Subnet
            </button>
          </div>
        </div>
      </div>

      <!-- Main Dashboard Split Section -->
      <div class="grid-split">
        <!-- Left: Connected Devices & Topology Preview -->
        <div class="glass-card">
          <div class="card-title-bar">
            <h3 class="card-title"><span>💻</span> Connected LAN Devices</h3>
            <button class="btn btn-secondary btn-sm" onclick="App.openPairModal()">
              <span>➕</span> Pair Device
            </button>
          </div>
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Device Name</th>
                  <th>IP Address</th>
                  <th>Port</th>
                  <th>Status</th>
                  <th>Trust</th>
                </tr>
              </thead>
              <tbody>
                <tr style="background: rgba(0, 240, 255, 0.04);">
                  <td><strong>${host.device_name} (This Laptop)</strong></td>
                  <td><code style="color: var(--accent-cyan);">${host.ip_address}</code></td>
                  <td>${host.port}</td>
                  <td><span class="pill pill-synced">HOST (ONLINE)</span></td>
                  <td><span class="pill pill-synced">VERIFIED</span></td>
                </tr>
                ${devices.map(d => `
                  <tr>
                    <td><strong>${d.device_name}</strong></td>
                    <td><code>${d.ip_address}</code></td>
                    <td>${d.port}</td>
                    <td>
                      <span class="pill ${d.status === 'online' ? 'pill-synced' : 'pill-priority-3'}">
                        ${d.status.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span class="pill ${d.trusted ? 'pill-synced' : 'pill-modified'}">
                        ${d.trusted ? 'PAIRED' : 'UNVERIFIED'}
                      </span>
                    </td>
                  </tr>
                `).join('')}
                ${devices.length === 0 ? `
                  <tr>
                    <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 24px;">
                      No other devices discovered on LAN yet. Start client laptop on the same router or enable Demo Mode.
                    </td>
                  </tr>
                ` : ''}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Right: Active & Recent Transfers -->
        <div class="glass-card">
          <div class="card-title-bar">
            <h3 class="card-title"><span>⚡</span> Real-Time Transfers</h3>
            <button class="btn btn-secondary btn-sm" onclick="App.navigate('transfers')">
              View Queue
            </button>
          </div>
          <div style="display: flex; flex-direction: column; gap: 14px;">
            ${(transfers.active_tasks || []).map(t => `
              <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
                <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; margin-bottom: 6px;">
                  <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px;">${t.file_name}</span>
                  <span class="pill pill-priority-${t.priority}">${t.priority_name}</span>
                </div>
                <div class="progress-container" style="margin-bottom: 6px;">
                  <div class="progress-fill" style="width: ${t.percentage || 0}%;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">
                  <span>${t.percentage || 0}% • ${this.formatBytes(t.transferred_bytes || 0)}</span>
                  <span>${t.speed ? `${t.speed} MB/s` : 'Queued'}</span>
                </div>
              </div>
            `).join('')}

            ${(!transfers.active_tasks || transfers.active_tasks.length === 0) ? `
              <div style="text-align: center; color: var(--text-muted); padding: 32px 0;">
                <div style="font-size: 32px; margin-bottom: 8px;">💤</div>
                <div>No active file transfers</div>
                <div style="font-size: 12px; margin-top: 4px;">Select a file to transfer or trigger synchronization</div>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  },

  formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
};
