// frontend/js/components/analytics.js - System Storage & Throughput Analytics

const AnalyticsComponent = {
  analyticsData: null,

  async render() {
    const el = document.getElementById('view-analytics');
    if (!el) return;

    try {
      this.analyticsData = await API.getAnalytics();
    } catch (_) {}

    const data = this.analyticsData || {
      overview: { total_files: 0, total_storage_mb: 0, online_devices_count: 0, wasted_duplicate_mb: 0 },
      type_distribution: { counts: {}, sizes: {} },
      transfers: { total_count: 0, completed_count: 0, failed_count: 0, total_data_transferred_mb: 0, average_speed_mbps: 0 }
    };

    const types = Object.keys(data.type_distribution.counts || {});

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h2 class="page-title">Storage & Network Analytics</h2>
          <p class="page-subtitle">Real-time telemetry on storage distribution, duplicate ratio, and LAN transfer throughput</p>
        </div>
      </div>

      <!-- Quick Metrics Grid -->
      <div class="grid-cards" style="margin-bottom: 24px;">
        <div class="glass-card stat-card">
          <div class="stat-icon cyan">📊</div>
          <div>
            <div class="stat-val">${data.overview.total_storage_mb} MB</div>
            <div class="stat-label">Total Shared Storage</div>
          </div>
        </div>

        <div class="glass-card stat-card">
          <div class="stat-icon emerald">⚡</div>
          <div>
            <div class="stat-val">${data.transfers.average_speed_mbps} MB/s</div>
            <div class="stat-label">Avg Transfer Speed</div>
          </div>
        </div>

        <div class="glass-card stat-card">
          <div class="stat-icon purple">🚀</div>
          <div>
            <div class="stat-val">${data.transfers.total_data_transferred_mb} MB</div>
            <div class="stat-label">Total LAN Data Moved</div>
          </div>
        </div>

        <div class="glass-card stat-card">
          <div class="stat-icon amber">👯</div>
          <div>
            <div class="stat-val">${data.overview.wasted_duplicate_mb} MB</div>
            <div class="stat-label">Wasted Duplicate Space</div>
          </div>
        </div>
      </div>

      <!-- Breakdown Split -->
      <div class="grid-split">
        <!-- File Type Distribution -->
        <div class="glass-card">
          <div class="card-title-bar">
            <h3 class="card-title"><span>📂</span> Storage by File Extension</h3>
          </div>
          <div style="display: flex; flex-direction: column; gap: 14px;">
            ${types.map(t => {
              const count = data.type_distribution.counts[t];
              const size = data.type_distribution.sizes[t] || 0;
              const pct = data.overview.total_storage_bytes > 0
                ? Math.round((size / data.overview.total_storage_bytes) * 100)
                : 0;
              return `
                <div>
                  <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; margin-bottom: 4px;">
                    <span>.${t.toUpperCase()} (${count} files)</span>
                    <span style="font-family: var(--font-mono); color: var(--accent-cyan);">${DashboardComponent.formatBytes(size)} (${pct}%)</span>
                  </div>
                  <div class="progress-container">
                    <div class="progress-fill" style="width: ${pct}%;"></div>
                  </div>
                </div>
              `;
            }).join('')}
            ${types.length === 0 ? `<div style="color: var(--text-muted); padding: 20px; text-align: center;">No files indexed.</div>` : ''}
          </div>
        </div>

        <!-- Transfer Success Metrics -->
        <div class="glass-card">
          <div class="card-title-bar">
            <h3 class="card-title"><span>📈</span> Transfer Reliability Metrics</h3>
          </div>
          <div style="display: flex; flex-direction: column; gap: 16px;">
            <div style="display: flex; justify-content: space-between; padding: 12px; background: rgba(15, 23, 42, 0.6); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <span>Total Transfers Initiated</span>
              <strong style="font-family: var(--font-mono);">${data.transfers.total_count}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 12px; background: rgba(16, 185, 129, 0.1); border-radius: var(--radius-sm); border: 1px solid rgba(16, 185, 129, 0.3);">
              <span style="color: var(--accent-emerald);">Successful & SHA-256 Verified</span>
              <strong style="font-family: var(--font-mono); color: var(--accent-emerald);">${data.transfers.completed_count}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 12px; background: rgba(244, 63, 94, 0.1); border-radius: var(--radius-sm); border: 1px solid rgba(244, 63, 94, 0.3);">
              <span style="color: var(--accent-rose);">Failed / Interrupted</span>
              <strong style="font-family: var(--font-mono); color: var(--accent-rose);">${data.transfers.failed_count}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 12px; background: rgba(15, 23, 42, 0.6); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <span>Cancelled by User</span>
              <strong style="font-family: var(--font-mono);">${data.transfers.cancelled_count || 0}</strong>
            </div>
          </div>
        </div>
      </div>
    `;
  }
};
