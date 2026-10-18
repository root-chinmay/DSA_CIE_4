// frontend/js/components/duplicates.js - Hash-Based Duplicate File Detection & Cleaner

const DuplicatesComponent = {
  render() {
    const el = document.getElementById('view-duplicates');
    if (!el) return;

    const duplicates = State.duplicates || [];
    const totalWastedBytes = duplicates.reduce((acc, d) => acc + (d.wasted_size || 0), 0);
    const totalDuplicateFiles = duplicates.reduce((acc, d) => acc + d.count, 0);

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h2 class="page-title">Duplicate File Finder</h2>
          <p class="page-subtitle">O(1) duplicate detection clustering identical SHA-256 cryptographic digests</p>
        </div>
        <div style="display: flex; gap: 10px;">
          <button class="btn btn-secondary btn-sm" onclick="App.refreshDuplicates()">
            <span>🔄</span> Refresh Duplicates
          </button>
        </div>
      </div>

      <!-- Overview Warning Card -->
      <div class="glass-card" style="margin-bottom: 24px; background: linear-gradient(135deg, rgba(244, 63, 94, 0.1), rgba(245, 158, 11, 0.05)); border-color: rgba(244, 63, 94, 0.3);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
          <div>
            <div style="font-size: 13px; font-weight: 700; color: var(--accent-rose); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
              Storage Optimization Analysis
            </div>
            <div style="font-size: 15px; color: #fff;">
              Found <strong>${duplicates.length} duplicate group(s)</strong> across <strong>${totalDuplicateFiles} files</strong>.
            </div>
            <div style="font-size: 13px; color: var(--text-muted); margin-top: 2px;">
              Wasted Disk Space: <strong style="color: var(--accent-amber); font-family: var(--font-mono);">${DashboardComponent.formatBytes(totalWastedBytes)}</strong>
            </div>
          </div>
          <div>
            <button class="btn btn-secondary btn-sm" onclick="App.scanFolders(true)">
              Re-Calculate Hashes
            </button>
          </div>
        </div>
      </div>

      <!-- Duplicate Groups List -->
      <div style="display: flex; flex-direction: column; gap: 18px;">
        ${duplicates.map((group, groupIdx) => `
          <div class="glass-card" style="padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">
              <div style="display: flex; align-items: center; gap: 10px;">
                <span class="pill pill-conflict">Group #${groupIdx + 1}</span>
                <span style="font-size: 13px; font-family: var(--font-mono); color: var(--accent-cyan); font-weight: 600;">
                  SHA-256: ${group.hash}
                </span>
              </div>
              <div style="font-size: 12px; color: var(--text-muted);">
                ${group.count} files • ${DashboardComponent.formatBytes(group.wasted_size)} wasted
              </div>
            </div>

            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Role</th>
                    <th>File Name</th>
                    <th>Relative Path</th>
                    <th>Size</th>
                    <th>Modified Date</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  ${group.files.map((f, fIdx) => `
                    <tr>
                      <td>
                        <span class="pill ${fIdx === 0 ? 'pill-synced' : 'pill-priority-1'}">
                          ${fIdx === 0 ? 'ORIGINAL' : 'DUPLICATE'}
                        </span>
                      </td>
                      <td><strong>${f.name}</strong></td>
                      <td><code>${f.relative_path}</code></td>
                      <td>${DashboardComponent.formatBytes(f.size)}</td>
                      <td style="font-size: 12px; color: var(--text-muted);">
                        ${new Date((f.modified_time || 0) * 1000).toLocaleString()}
                      </td>
                      <td>
                        ${fIdx > 0 ? `
                          <button class="btn btn-danger btn-sm" onclick="DuplicatesComponent.deleteDuplicate('${f.file_id}', '${f.name}')">
                            Delete Duplicate
                          </button>
                        ` : `
                          <span style="color: var(--accent-emerald); font-size: 12px; font-weight: 600;">Kept Safe</span>
                        `}
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
        `).join('')}

        ${duplicates.length === 0 ? `
          <div class="glass-card" style="text-align: center; color: var(--text-muted); padding: 48px;">
            <div style="font-size: 36px; margin-bottom: 10px;">✨</div>
            <div style="font-size: 16px; font-weight: 600; color: #fff;">No Duplicate Files Detected</div>
            <div style="font-size: 13px; margin-top: 4px;">All shared files possess distinct SHA-256 cryptographic digests.</div>
          </div>
        ` : ''}
      </div>
    `;
  },

  async deleteDuplicate(fileId, name) {
    if (confirm(`Delete duplicate file '${name}' to reclaim storage?`)) {
      try {
        await API.deleteFile(fileId);
        App.showToast(`Deleted duplicate: ${name}`, 'success');
        App.refreshDuplicates();
        App.refreshFiles();
      } catch (err) {
        App.showToast(`Delete failed: ${err.message}`, 'error');
      }
    }
  }
};
