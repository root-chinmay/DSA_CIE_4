// frontend/js/components/transfers.js - Priority Queue & FIFO Transfer Manager

const TransfersComponent = {
  render() {
    const el = document.getElementById('view-transfers');
    if (!el) return;

    const data = State.transfers || {
      fifo_queue: [],
      priority_heap: [],
      active_tasks: [],
      history: []
    };

    const activeTasks = data.active_tasks || [];
    const fifoItems = data.fifo_queue || [];
    const heapItems = data.priority_heap || [];
    const history = data.history || [];

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h2 class="page-title">Transfer Queue & Priority Scheduler</h2>
          <p class="page-subtitle">Demonstrates FIFO Queue and Binary Min-Heap Priority Queue for urgent file dispatching</p>
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
          <button class="btn btn-secondary btn-sm" onclick="App.refreshTransfers()">
            <span>🔄</span> Refresh Queue
          </button>
          <button class="btn btn-primary btn-sm" onclick="App.navigate('ip-transfer')">
            <span>🌐</span> Direct IP Transfer
          </button>
        </div>
      </div>

      <!-- Active Transfers -->
      <div class="glass-card" style="margin-bottom: 24px;">
        <div class="card-title-bar">
          <h3 class="card-title"><span>⚡</span> Currently Executing Transfers (${activeTasks.length})</h3>
        </div>
        <div style="display: flex; flex-direction: column; gap: 16px;">
          ${activeTasks.map(t => `
            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border-medium); border-radius: var(--radius-md); padding: 18px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                  <span style="font-size: 20px;">${t.direction === 'UPLOAD' ? '⬆' : '⬇'}</span>
                  <div>
                    <div style="font-size: 15px; font-weight: 700;">${t.file_name}</div>
                    <div style="font-size: 12px; color: var(--text-muted); font-family: var(--font-mono);">
                      ${t.source_device} ➜ ${t.destination_device} • ID: ${t.transfer_id}
                    </div>
                  </div>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                  <!-- Priority Switcher -->
                  <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 11px; color: var(--text-muted);">Priority:</span>
                    <select class="btn btn-secondary btn-sm" style="padding: 4px 8px; font-size: 11px;"
                            onchange="TransfersComponent.changePriority('${t.transfer_id}', this.value)">
                      <option value="0" ${t.priority === 0 ? 'selected' : ''}>CRITICAL (0)</option>
                      <option value="1" ${t.priority === 1 ? 'selected' : ''}>HIGH (1)</option>
                      <option value="2" ${t.priority === 2 ? 'selected' : ''}>NORMAL (2)</option>
                      <option value="3" ${t.priority === 3 ? 'selected' : ''}>LOW (3)</option>
                    </select>
                  </div>
                  <button class="btn btn-danger btn-sm" onclick="TransfersComponent.cancelTransfer('${t.transfer_id}')">
                    Cancel
                  </button>
                </div>
              </div>

              <!-- Progress bar -->
              <div class="progress-container" style="height: 10px; margin-bottom: 8px;">
                <div class="progress-fill" style="width: ${t.percentage || 0}%;"></div>
              </div>

              <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-secondary); font-family: var(--font-mono);">
                <span>${t.percentage || 0}% (${DashboardComponent.formatBytes(t.transferred_bytes || 0)} / ${DashboardComponent.formatBytes(t.size)})</span>
                <span>Speed: <strong style="color: var(--accent-cyan);">${t.speed || 0} MB/s</strong> | ETA: <strong>${t.eta || 0}s</strong></span>
              </div>
            </div>
          `).join('')}

          ${activeTasks.length === 0 ? `
            <div style="text-align: center; color: var(--text-muted); padding: 24px;">
              No transfers currently running. Enqueue a transfer from the File Explorer.
            </div>
          ` : ''}
        </div>
      </div>

      <!-- DSA Transfer Scheduling Comparison (FIFO vs Priority Heap) -->
      <div class="grid-split" style="margin-bottom: 24px;">
        <!-- Left: Binary Min-Heap Priority Queue -->
        <div class="glass-card">
          <div class="card-title-bar">
            <div>
              <h3 class="card-title"><span>⛰</span> Binary Min-Heap Scheduler</h3>
              <p style="font-size: 12px; color: var(--text-muted);">Urgent tasks jump ahead based on min-heap property: O(log N) insertion & extraction</p>
            </div>
          </div>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${heapItems.map((h, idx) => `
              <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(15, 23, 42, 0.5); padding: 10px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
                <div style="display: flex; align-items: center; gap: 10px;">
                  <span style="font-family: var(--font-mono); font-weight: 700; color: var(--text-muted);">#${idx + 1}</span>
                  <span class="pill pill-priority-${h.priority}">${h.priority_name}</span>
                  <span style="font-size: 13px; font-weight: 600;">${h.title || h.item?.file_name || h.item_id}</span>
                </div>
                <div style="font-size: 11px; color: var(--text-muted);">
                  ${DashboardComponent.formatBytes(h.item?.size || 0)}
                </div>
              </div>
            `).join('')}
            ${heapItems.length === 0 ? `
              <div style="text-align: center; color: var(--text-muted); padding: 20px;">Priority heap is empty</div>
            ` : ''}
          </div>
        </div>

        <!-- Right: FIFO Transfer Queue -->
        <div class="glass-card">
          <div class="card-title-bar">
            <div>
              <h3 class="card-title"><span>⏳</span> FIFO Queue Track</h3>
              <p style="font-size: 12px; color: var(--text-muted);">Sequential First-In First-Out doubly-linked queue</p>
            </div>
          </div>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${fifoItems.map((item, idx) => `
              <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(15, 23, 42, 0.5); padding: 10px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
                <div style="display: flex; align-items: center; gap: 10px;">
                  <span style="font-family: var(--font-mono); color: var(--accent-cyan); font-weight: 700;">${idx === 0 ? 'FRONT' : (idx === fifoItems.length - 1 ? 'REAR' : `#${idx + 1}`)}</span>
                  <span style="font-size: 13px; font-weight: 600;">${item.file_name}</span>
                </div>
                <span class="pill pill-priority-${item.priority}">${item.priority_name}</span>
              </div>
            `).join('')}
            ${fifoItems.length === 0 ? `
              <div style="text-align: center; color: var(--text-muted); padding: 20px;">FIFO queue is empty</div>
            ` : ''}
          </div>
        </div>
      </div>

      <!-- Completed Transfer History -->
      <div class="glass-card" style="padding: 0;">
        <div class="card-title-bar" style="padding: 18px 20px 0;">
          <h3 class="card-title"><span>📜</span> Transfer History & Cryptographic Verification Audit</h3>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>File Name</th>
                <th>Route</th>
                <th>Direction</th>
                <th>Size</th>
                <th>Speed</th>
                <th>Duration</th>
                <th>Status</th>
                <th>SHA-256 Check</th>
              </tr>
            </thead>
            <tbody>
              ${history.map(h => `
                <tr>
                  <td><strong>${h.file_name}</strong></td>
                  <td><code>${h.source_device} ➜ ${h.destination_device}</code></td>
                  <td><span class="pill pill-new">${h.direction}</span></td>
                  <td>${DashboardComponent.formatBytes(h.size)}</td>
                  <td>${h.speed ? `${h.speed} MB/s` : '-'}</td>
                  <td>${h.completed_at && h.started_at ? `${Math.max(0.1, (h.completed_at - h.started_at)).toFixed(1)}s` : '-'}</td>
                  <td>
                    <span class="pill ${h.status === 'COMPLETED' ? 'pill-synced' : (h.status === 'FAILED' ? 'pill-conflict' : 'pill-modified')}">
                      ${h.status}
                    </span>
                  </td>
                  <td>
                    <span class="pill ${h.hash_verified ? 'pill-synced' : 'pill-conflict'}">
                      ${h.hash_verified ? '✓ VERIFIED' : 'PENDING / FAILED'}
                    </span>
                  </td>
                </tr>
              `).join('')}
              ${history.length === 0 ? `
                <tr>
                  <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">No transfer history recorded yet.</td>
                </tr>
              ` : ''}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  async changePriority(transferId, newPriority) {
    try {
      await API.updateTransferPriority(transferId, newPriority);
      App.showToast(`Elevated priority to level ${newPriority}`, 'success');
      App.refreshTransfers();
    } catch (err) {
      App.showToast(`Failed to update priority: ${err.message}`, 'error');
    }
  },

  async cancelTransfer(transferId) {
    try {
      await API.cancelTransfer(transferId);
      App.showToast(`Transfer cancelled`, 'warning');
      App.refreshTransfers();
    } catch (err) {
      App.showToast(`Cancel failed: ${err.message}`, 'error');
    }
  }
};
