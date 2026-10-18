// frontend/js/app.js - Main Application Orchestrator & Modal Controller

const App = {
  async init() {
    console.log('🚀 Initializing DSA Offline LAN File Sharing System...');
    try {
      await this.refreshHostInfo();
      await this.refreshFiles();
      await this.refreshFolders();
      await this.refreshDevices();
      await this.refreshTransfers();
      await this.refreshDuplicates();
      await this.refreshConflicts();
    } catch (err) {
      console.error('Initialization error:', err);
    }

    // Default to Dashboard
    this.navigate('dashboard');
    this.updateTopbar();
  },

  navigate(tabName) {
    State.setActiveTab(tabName);

    // Update navigation active states
    document.querySelectorAll('.nav-item').forEach(el => {
      if (el.getAttribute('data-tab') === tabName) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });

    // Update view sections
    document.querySelectorAll('.view-section').forEach(el => {
      el.classList.remove('active');
    });

    const activeSection = document.getElementById(`view-${tabName}`);
    if (activeSection) {
      activeSection.classList.add('active');
    }

    // Close mobile drawer on navigation
    this.closeMobileSidebar();

    // Render corresponding component
    switch (tabName) {
      case 'dashboard': DashboardComponent.render(); break;
      case 'files': ExplorerComponent.render(); break;
      case 'ip-transfer': IPTransferComponent.render(); break;
      case 'devices': DevicesComponent.render(); break;
      case 'transfers': TransfersComponent.render(); break;
      case 'sync': SyncComponent.render(); break;
      case 'duplicates': DuplicatesComponent.render(); break;
      case 'dsa': DSAVisualizerComponent.render(); break;
      case 'analytics': AnalyticsComponent.render(); break;
      case 'settings': SettingsComponent.render(); break;
    }

    this.updateTopbar();
  },

  async refreshHostInfo() {
    const info = await API.ping();
    State.setHostInfo(info);
    this.updateTopbar();
  },

  async refreshFiles() {
    const res = await API.getFiles();
    State.setFiles(res.files || []);
    const tree = await API.getFileTree();
    State.setFileTree(tree);

    if (State.activeTab === 'files') ExplorerComponent.render();
    if (State.activeTab === 'dashboard') DashboardComponent.render();
  },

  async refreshFolders() {
    const folders = await API.getFolders();
    State.setFolders(folders);
  },

  async refreshDevices() {
    const devices = await API.getDevices();
    State.setDevices(devices);
    if (State.activeTab === 'devices') DevicesComponent.render();
    if (State.activeTab === 'dashboard') DashboardComponent.render();
    this.updateTopbar();
  },

  async refreshTransfers() {
    const transfers = await API.getTransfers();
    State.setTransfers(transfers);
    if (State.activeTab === 'transfers') TransfersComponent.render();
    if (State.activeTab === 'dashboard') DashboardComponent.render();
  },

  async refreshDuplicates() {
    const res = await API.getDuplicates();
    State.setDuplicates(res.duplicate_groups || []);
    if (State.activeTab === 'duplicates') DuplicatesComponent.render();
    if (State.activeTab === 'dashboard') DashboardComponent.render();
  },

  async refreshConflicts() {
    const conflicts = await API.getConflicts();
    State.setConflicts(conflicts);
    if (State.activeTab === 'sync') SyncComponent.render();
    this.updateBadges();
  },

  async scanFolders(forceRehash = false) {
    this.showToast('Re-indexing shared files into Tree, Hash Table & Trie...', 'info');
    try {
      await API.scanFolders(forceRehash);
      await this.refreshFiles();
      await this.refreshDuplicates();
      this.showToast('File scan and hash indexing complete!', 'success');
    } catch (err) {
      this.showToast(`Scan error: ${err.message}`, 'error');
    }
  },

  async resetPairingCode() {
    try {
      const res = await API.resetPairingCode();
      State.setHostInfo({ pairing_code: res.pairing_code });
      this.showToast(`New pairing code generated: ${res.pairing_code}`, 'info');
      this.updateTopbar();
      if (State.activeTab === 'devices') DevicesComponent.render();
      if (State.activeTab === 'settings') SettingsComponent.render();
    } catch (err) {
      this.showToast(`Failed to reset code: ${err.message}`, 'error');
    }
  },

  async toggleDemoMode() {
    try {
      const res = await API.toggleDemoMode();
      State.setHostInfo({ demo_mode: res.demo_mode });
      this.showToast(res.demo_mode ? 'Academic Demo Mode activated with virtual peers!' : 'Demo Mode disabled. Switched to live LAN mode.', 'info');
      await this.refreshFiles();
      await this.refreshDevices();
      await this.refreshTransfers();
      await this.refreshConflicts();
      this.navigate(State.activeTab);
    } catch (err) {
      this.showToast(`Error toggling demo: ${err.message}`, 'error');
    }
  },

  syncWithPeer(ip, port) {
    SyncComponent.selectedPeer = { ip_address: ip, port: port };
    this.navigate('sync');
  },

  updateTopbar() {
    const host = State.hostInfo;
    const ipEl = document.getElementById('topbar-lan-ip');
    if (ipEl) ipEl.innerText = host.ip_address || '127.0.0.1';

    const codeEl = document.getElementById('topbar-pairing-code');
    if (codeEl) codeEl.innerText = host.pairing_code || '------';

    const demoEl = document.getElementById('topbar-demo-banner');
    if (demoEl) {
      demoEl.style.display = host.demo_mode ? 'flex' : 'none';
    }

    const peerChipEl = document.getElementById('sidebar-host-name');
    if (peerChipEl) peerChipEl.innerText = host.device_name || 'Host Laptop';

    this.updateBadges();
  },

  updateBadges() {
    const badgeTransfers = document.getElementById('badge-transfers');
    if (badgeTransfers) {
      const activeCount = (State.transfers.active_tasks || []).length;
      badgeTransfers.innerText = activeCount > 0 ? activeCount : '';
      badgeTransfers.style.display = activeCount > 0 ? 'inline-block' : 'none';
    }

    const badgeConflicts = document.getElementById('badge-conflicts');
    if (badgeConflicts) {
      const conflictCount = (State.conflicts || []).length;
      badgeConflicts.innerText = conflictCount > 0 ? conflictCount : '';
      badgeConflicts.style.display = conflictCount > 0 ? 'inline-block' : 'none';
    }
  },

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌' };
    toast.innerHTML = `
      <span style="font-size: 18px;">${icons[type] || '🔔'}</span>
      <div style="font-size: 13px; font-weight: 500; color: #fff;">${message}</div>
    `;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 400);
    }, 4000);
  },

  // Modals
  openPairModal() {
    document.getElementById('modal-pair').classList.add('active');
  },

  closePairModal() {
    document.getElementById('modal-pair').classList.remove('active');
  },

  async submitPair(e) {
    e.preventDefault();
    const ip = document.getElementById('pair-modal-ip').value.trim();
    const port = document.getElementById('pair-modal-port').value.trim();
    const code = document.getElementById('pair-modal-code').value.trim();

    this.showToast(`Connecting to ${ip}:${port}...`, 'info');
    try {
      const res = await API.manualConnect(ip, port, code);
      this.showToast(`✓ Connected to ${res.peer.device_name}!`, 'success');
      this.closePairModal();
      await this.refreshDevices();
    } catch (err) {
      this.showToast(`Pairing failed: ${err.message}`, 'error');
    }
  },

  async runDiagnosticsModal() {
    document.getElementById('modal-diagnostics').classList.add('active');
    const content = document.getElementById('diagnostics-modal-body');
    content.innerHTML = '<div style="text-align: center; padding: 20px;">Running LAN diagnostics...</div>';

    try {
      const data = await API.getNetworkDiagnostics();
      content.innerHTML = `
        <div style="margin-bottom: 16px;">
          <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 6px;">
            <span>Detected Local IP:</span>
            <code style="color: var(--accent-cyan); font-weight: 700;">${data.local_ip}</code>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 6px;">
            <span>Server Listening Port:</span>
            <code>${data.server_port}</code>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 14px;">
            <span>Network Status:</span>
            <span class="pill ${data.is_lan_connected ? 'pill-synced' : 'pill-modified'}">${data.status}</span>
          </div>
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${data.diagnostics.map(d => `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(15, 23, 42, 0.6); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <div>
                <strong style="font-size: 13px;">${d.name}</strong>
                <div style="font-size: 11px; color: var(--text-muted);">${d.details}</div>
              </div>
              <span class="pill ${d.passed ? 'pill-synced' : 'pill-conflict'}">
                ${d.passed ? '✓ PASSED' : '✕ CHECK'}
              </span>
            </div>
          `).join('')}
        </div>
      `;
    } catch (err) {
      content.innerHTML = `<div style="color: var(--accent-rose);">Error running diagnostics: ${err.message}</div>`;
    }
  },

  closeDiagnosticsModal() {
    document.getElementById('modal-diagnostics').classList.remove('active');
  },

  toggleMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('active');
  },

  closeMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('active');
  }
};


// Bootstrap when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
