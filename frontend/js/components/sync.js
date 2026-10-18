// frontend/js/components/sync.js - File Synchronization & Conflict Resolution Center

const SyncComponent = {
  diffData: null,
  selectedPeer: null,

  async render() {
    const el = document.getElementById('view-sync');
    if (!el) return;

    const devices = State.devices || [];
    const conflicts = State.conflicts || [];

    // Fetch diff data
    try {
      this.diffData = await API.getSyncDiff(this.selectedPeer?.ip_address, this.selectedPeer?.port);
    } catch (_) {}

    const diff = this.diffData || {
      diff_matrix: [],
      synced_count: 0,
      new_local_count: 0,
      new_remote_count: 0,
      modified_count: 0,
      conflict_count: 0
    };

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h2 class="page-title">Intelligent File Synchronization</h2>
          <p class="page-subtitle">Cryptographic SHA-256 diffing eliminates redundant transfers and handles concurrent conflicts safely</p>
        </div>
        <div style="display: flex; gap: 10px;">
          <button class="btn btn-primary btn-sm" onclick="SyncComponent.triggerSync()">
            <span>🔄</span> Sync All Pending Files
          </button>
        </div>
      </div>

      <!-- Peer Target Selector & Status -->
      <div class="glass-card" style="margin-bottom: 24px;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <label style="font-size: 13px; font-weight: 600; color: var(--text-secondary);">Target Peer Device:</label>
            <select class="btn btn-secondary btn-sm" onchange="SyncComponent.onPeerChange(this.value)">
              <option value="">Simulation / Local Baseline</option>
              ${devices.map(d => `
                <option value="${d.device_id}" ${this.selectedPeer?.device_id === d.device_id ? 'selected' : ''}>
                  ${d.device_name} (${d.ip_address})
                </option>
              `).join('')}
            </select>
          </div>
          <div style="display: flex; gap: 12px; font-size: 13px;">
            <span>🟢 Synced: <strong>${diff.synced_count}</strong></span>
            <span>🔵 New: <strong>${diff.new_local_count + diff.new_remote_count}</strong></span>
            <span>🟠 Modified: <strong>${diff.modified_count}</strong></span>
            <span>🔴 Conflicts: <strong style="color: var(--accent-rose);">${diff.conflict_count}</strong></span>
          </div>
        </div>
      </div>

      <!-- Conflicts Alert Section if any -->
      ${conflicts.length > 0 ? `
        <div class="glass-card" style="margin-bottom: 24px; border: 1px solid rgba(244, 63, 94, 0.4); background: rgba(244, 63, 94, 0.05);">
          <div class="card-title-bar">
            <h3 class="card-title" style="color: var(--accent-rose);">
              <span>⚠</span> Synchronization Conflicts Detected (${conflicts.length})
            </h3>
          </div>
          <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 16px;">
            The following files were modified concurrently on both laptops with differing content. Choose how to resolve them to prevent data loss:
          </p>
          <div style="display: flex; flex-direction: column; gap: 12px;">
            ${conflicts.map(c => `
              <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border-medium); border-radius: var(--radius-md); padding: 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                  <div style="font-weight: 700; font-size: 14px; color: #fff;">${c.file_path}</div>
                  <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); margin-top: 4px;">
                    Local Hash: ${c.local_hash ? c.local_hash.substring(0, 12) + '...' : 'N/A'} | Remote Hash: ${c.remote_hash ? c.remote_hash.substring(0, 12) + '...' : 'N/A'}
                  </div>
                </div>
                <div style="display: flex; gap: 8px;">
                  <button class="btn btn-secondary btn-sm" onclick="SyncComponent.resolveConflict(${c.id}, 'KEEP_LOCAL')">
                    Keep Local
                  </button>
                  <button class="btn btn-secondary btn-sm" onclick="SyncComponent.resolveConflict(${c.id}, 'KEEP_REMOTE')">
                    Keep Remote
                  </button>
                  <button class="btn btn-primary btn-sm" onclick="SyncComponent.resolveConflict(${c.id}, 'KEEP_BOTH')">
                    Keep Both (Rename)
                  </button>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}

      <!-- Sync Diff Matrix Table -->
      <div class="glass-card" style="padding: 0;">
        <div class="card-title-bar" style="padding: 18px 20px 0;">
          <h3 class="card-title"><span>📊</span> FileTree Synchronization Matrix</h3>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Relative Path</th>
                <th>File Name</th>
                <th>Sync State</th>
                <th>Local SHA-256</th>
                <th>Remote SHA-256</th>
                <th>Sync Action</th>
              </tr>
            </thead>
            <tbody>
              ${diff.diff_matrix.map(row => `
                <tr>
                  <td><code style="color: var(--accent-cyan);">${row.relative_path}</code></td>
                  <td><strong>${row.file_name}</strong></td>
                  <td>
                    <span class="pill ${
                      row.state === 'SYNCED' ? 'pill-synced' :
                      (row.state.includes('NEW') ? 'pill-new' :
                      (row.state === 'CONFLICT' ? 'pill-conflict' : 'pill-modified'))
                    }">
                      ${row.state}
                    </span>
                  </td>
                  <td><code style="font-size: 11px; color: var(--text-muted);">${row.local_hash ? row.local_hash.substring(0, 8) + '...' : '-'}</code></td>
                  <td><code style="font-size: 11px; color: var(--text-muted);">${row.remote_hash ? row.remote_hash.substring(0, 8) + '...' : '-'}</code></td>
                  <td>
                    <span style="font-weight: 600; font-size: 12px; color: ${row.action === 'NONE' ? 'var(--text-muted)' : 'var(--accent-cyan)'};">
                      ${row.action === 'NONE' ? '✓ Identical (No Transfer)' : row.action}
                    </span>
                  </td>
                </tr>
              `).join('')}
              ${diff.diff_matrix.length === 0 ? `
                <tr>
                  <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 24px;">No files to compare.</td>
                </tr>
              ` : ''}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  onPeerChange(deviceId) {
    this.selectedPeer = State.devices.find(d => d.device_id === deviceId) || null;
    this.render();
  },

  async triggerSync() {
    App.showToast('Starting file synchronization...', 'info');
    try {
      const res = await API.startSync({
        peer_ip: this.selectedPeer?.ip_address,
        peer_port: this.selectedPeer?.port || 8000
      });
      App.showToast(`Enqueued ${res.enqueued_count} files for background synchronization!`, 'success');
      App.refreshTransfers();
      this.render();
    } catch (err) {
      App.showToast(`Sync failed: ${err.message}`, 'error');
    }
  },

  async resolveConflict(conflictId, resolution) {
    try {
      await API.resolveConflict(conflictId, resolution);
      App.showToast(`Conflict resolved via ${resolution}`, 'success');
      App.refreshConflicts();
      this.render();
    } catch (err) {
      App.showToast(`Failed to resolve conflict: ${err.message}`, 'error');
    }
  }
};
