// frontend/js/components/ip_transfer.js - Direct Offline IP-to-IP Transfer & Mobile Connect Portal

const IPTransferComponent = {
  currentSubTab: 'mobile_portal', // 'mobile_portal', 'send_ip', 'receive_ip', 'scanner'
  scanResults: null,
  isScanning: false,
  remoteFiles: [],
  isFetchingRemote: false,
  lastTransferResult: null,

  async render() {
    const el = document.getElementById('view-ip-transfer');
    if (!el) return;

    const host = State.hostInfo || {};
    const localIp = host.ip_address || '127.0.0.1';
    const port = host.port || 8000;
    const mobileUrl = `http://${localIp}:${port}/`;

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h2 class="page-title">🌐 Offline IP File Transfer & Mobile Portal</h2>
          <p class="page-subtitle">Transfer files directly using device IP addresses across Wi-Fi / Hotspot with zero Internet</p>
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
          <button class="btn btn-secondary btn-sm" onclick="IPTransferComponent.runSubnetScan()">
            <span>🔍</span> Scan Subnet IPs
          </button>
          <button class="btn btn-primary btn-sm" onclick="IPTransferComponent.copyMobileUrl('${mobileUrl}')">
            <span>📋</span> Copy LAN URL
          </button>
        </div>
      </div>

      <!-- Navigation Tabs for IP Transfer Engine -->
      <div class="ip-transfer-nav" style="display: flex; gap: 8px; margin-bottom: 24px; overflow-x: auto; padding-bottom: 6px;">
        <button class="btn ${this.currentSubTab === 'mobile_portal' ? 'btn-primary' : 'btn-secondary'}" onclick="IPTransferComponent.switchTab('mobile_portal')">
          <span>📱</span> Mobile Quick Connect & QR
        </button>
        <button class="btn ${this.currentSubTab === 'send_ip' ? 'btn-primary' : 'btn-secondary'}" onclick="IPTransferComponent.switchTab('send_ip')">
          <span>📤</span> Send File to Device IP
        </button>
        <button class="btn ${this.currentSubTab === 'receive_ip' ? 'btn-primary' : 'btn-secondary'}" onclick="IPTransferComponent.switchTab('receive_ip')">
          <span>📥</span> Fetch Files from Remote IP
        </button>
        <button class="btn ${this.currentSubTab === 'scanner' ? 'btn-primary' : 'btn-secondary'}" onclick="IPTransferComponent.switchTab('scanner')">
          <span>🔍</span> Offline Subnet Scanner
        </button>
      </div>

      <!-- Active Sub Tab View -->
      <div id="ip-transfer-content">
        ${this.renderActiveTab(localIp, port, mobileUrl, host)}
      </div>
    `;

    // Render QR Code if mobile tab is active
    if (this.currentSubTab === 'mobile_portal') {
      setTimeout(() => {
        this.drawQRCode(mobileUrl);
      }, 50);
    }
  },

  switchTab(tab) {
    this.currentSubTab = tab;
    this.render();
  },

  renderActiveTab(localIp, port, mobileUrl, host) {
    switch (this.currentSubTab) {
      case 'mobile_portal':
        return this.renderMobilePortalTab(localIp, port, mobileUrl, host);
      case 'send_ip':
        return this.renderSendIPTab(localIp, port);
      case 'receive_ip':
        return this.renderReceiveIPTab();
      case 'scanner':
        return this.renderScannerTab();
      default:
        return this.renderMobilePortalTab(localIp, port, mobileUrl, host);
    }
  },

  // 1. Mobile Portal & QR Code View
  renderMobilePortalTab(localIp, port, mobileUrl, host) {
    const files = State.files || [];

    return `
      <!-- Hero Mobile Connect Card -->
      <div class="glass-card" style="margin-bottom: 24px; background: linear-gradient(135deg, rgba(0, 240, 255, 0.08), rgba(157, 78, 221, 0.08)); border-color: rgba(0, 240, 255, 0.25);">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; align-items: center;">
          
          <!-- Left: Instructions & Details -->
          <div>
            <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(0, 240, 255, 0.15); border: 1px solid rgba(0, 240, 255, 0.3); padding: 4px 12px; border-radius: var(--radius-full); font-size: 11px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase; margin-bottom: 12px;">
              <span>📶</span> Offline LAN / Hotspot Ready
            </div>
            <h3 style="font-size: 22px; font-weight: 800; margin-bottom: 8px; color: #fff;">Connect Any Mobile Phone Without Internet</h3>
            <p style="font-size: 14px; color: var(--text-secondary); margin-bottom: 16px; line-height: 1.6;">
              Any smartphone or tablet connected to this Wi-Fi router or laptop's Mobile Hotspot can instantly transfer files at full local network speed.
            </p>

            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border-medium); border-radius: var(--radius-md); padding: 14px; margin-bottom: 16px;">
              <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; margin-bottom: 4px;">Direct Browser URL:</div>
              <div style="display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap;">
                <code style="font-size: 18px; font-weight: 800; color: var(--accent-cyan); font-family: var(--font-mono);">${mobileUrl}</code>
                <button class="btn btn-secondary btn-sm" onclick="IPTransferComponent.copyMobileUrl('${mobileUrl}')">
                  <span>📋</span> Copy URL
                </button>
              </div>
            </div>

            <!-- Steps for Phone -->
            <div style="display: flex; flex-direction: column; gap: 10px; font-size: 13px;">
              <div style="display: flex; align-items: center; gap: 10px;">
                <span style="width: 24px; height: 24px; border-radius: 50%; background: var(--accent-cyan); color: #000; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 12px;">1</span>
                <span>Connect your phone to the same <strong>Wi-Fi</strong> or <strong>Laptop Hotspot</strong></span>
              </div>
              <div style="display: flex; align-items: center; gap: 10px;">
                <span style="width: 24px; height: 24px; border-radius: 50%; background: var(--accent-purple); color: #fff; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 12px;">2</span>
                <span>Open your phone camera to scan the QR code (or type URL in browser)</span>
              </div>
              <div style="display: flex; align-items: center; gap: 10px;">
                <span style="width: 24px; height: 24px; border-radius: 50%; background: var(--accent-emerald); color: #000; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 12px;">3</span>
                <span>Instantly send photos, videos, and files directly to host storage!</span>
              </div>
            </div>
          </div>

          <!-- Right: Interactive Offline QR Code Canvas -->
          <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; background: rgba(10, 15, 28, 0.85); border: 1px solid var(--border-medium); border-radius: var(--radius-lg); text-align: center;">
            <div style="font-size: 12px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.08em;">
              Offline Scannable QR Code
            </div>
            
            <div style="padding: 12px; background: #090d16; border: 2px solid var(--accent-cyan); border-radius: var(--radius-md); box-shadow: 0 0 25px var(--accent-cyan-glow); margin-bottom: 12px;">
              <canvas id="qr-canvas" style="display: block; border-radius: 4px;"></canvas>
            </div>

            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px;">
              Pairing Code: <strong style="color: #d8b4fe; font-family: var(--font-mono); letter-spacing: 0.1em;">${host.pairing_code || '------'}</strong>
            </div>

            <button class="btn btn-secondary btn-sm" onclick="IPTransferComponent.downloadQR()">
              <span>💾</span> Save QR Code
            </button>
          </div>
        </div>
      </div>

      <!-- Quick Mobile File Actions (Touch Optimized) -->
      <div class="glass-card" style="margin-bottom: 24px;">
        <div class="card-title-bar">
          <h3 class="card-title"><span>📱</span> Quick Mobile Actions (Touch-Ready)</h3>
          <span style="font-size: 12px; color: var(--text-muted);">Direct Upload/Download on this LAN Host</span>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px;">
          <!-- 1. Send from Mobile (Upload) -->
          <div style="background: rgba(15, 23, 42, 0.7); border: 1px dashed var(--accent-cyan); border-radius: var(--radius-md); padding: 20px; text-align: center; cursor: pointer;"
               onclick="document.getElementById('mobile-quick-upload-input').click()">
            <div style="font-size: 32px; margin-bottom: 8px;">📤</div>
            <div style="font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 4px;">Upload Files from Device</div>
            <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 14px;">Select photos, videos, or documents from your phone or PC</div>
            <button class="btn btn-primary" style="width: 100%;">
              <span>📂</span> Choose & Send Files
            </button>
            <input type="file" id="mobile-quick-upload-input" multiple style="display: none;" onchange="IPTransferComponent.handleMobileQuickUpload(event)" />
          </div>

          <!-- 2. Send by Target IP -->
          <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border-medium); border-radius: var(--radius-md); padding: 20px; text-align: center; cursor: pointer;"
               onclick="IPTransferComponent.switchTab('send_ip')">
            <div style="font-size: 32px; margin-bottom: 8px;">⚡</div>
            <div style="font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 4px;">Transfer by IP Address</div>
            <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 14px;">Send file directly to any device IP on the same Wi-Fi router</div>
            <button class="btn btn-secondary" style="width: 100%;">
              <span>🎯</span> Open IP Sender
            </button>
          </div>
        </div>
      </div>

      <!-- Shared Files Quick Download List for Mobile -->
      <div class="glass-card">
        <div class="card-title-bar">
          <h3 class="card-title"><span>📥</span> Download Shared Files to Device (${files.length})</h3>
          <button class="btn btn-secondary btn-sm" onclick="App.refreshFiles()">
            <span>🔄</span> Refresh Files
          </button>
        </div>

        <div style="display: flex; flex-direction: column; gap: 10px;">
          ${files.slice(0, 15).map(f => `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); gap: 12px; flex-wrap: wrap;">
              <div style="display: flex; align-items: center; gap: 12px; min-width: 200px;">
                <span style="font-size: 22px;">📄</span>
                <div>
                  <div style="font-weight: 600; font-size: 14px; word-break: break-all;">${f.name}</div>
                  <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">
                    ${DashboardComponent.formatBytes(f.size)} • ${f.file_type.toUpperCase()} • SHA-256: ${f.hash ? f.hash.substring(0, 8) + '...' : 'pending'}
                  </div>
                </div>
              </div>
              <div style="display: flex; gap: 8px;">
                <a href="/api/files/${f.id}/download" download class="btn btn-primary btn-sm" style="text-decoration: none; display: inline-flex; align-items: center; gap: 6px;">
                  <span>⬇</span> Download
                </a>
                <button class="btn btn-secondary btn-sm" onclick="IPTransferComponent.quickSendFileToIP('${f.id}', '${f.name}')">
                  <span>⚡</span> Send to IP
                </button>
              </div>
            </div>
          `).join('')}

          ${files.length === 0 ? `
            <div style="text-align: center; color: var(--text-muted); padding: 30px;">
              No files currently shared. Upload files from above to start sharing!
            </div>
          ` : ''}
        </div>
      </div>
    `;
  },

  // 2. Direct IP File Sender View
  renderSendIPTab(localIp, port) {
    const files = State.files || [];

    return `
      <div class="grid-split" style="margin-bottom: 24px;">
        <!-- Left: File & IP Configuration -->
        <div class="glass-card">
          <div class="card-title-bar">
            <h3 class="card-title"><span>📤</span> Direct IP File Dispatcher</h3>
            <span class="pill pill-priority-1">DSA Min-Heap Scheduled</span>
          </div>

          <form onsubmit="IPTransferComponent.submitDirectTransfer(event)">
            <div style="display: flex; flex-direction: column; gap: 16px;">
              
              <!-- Source Selection (Existing File OR New Upload) -->
              <div>
                <label style="font-size: 12px; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 6px;">
                  File to Transfer
                </label>
                <div style="display: flex; gap: 10px; margin-bottom: 8px;">
                  <button type="button" class="btn btn-secondary btn-sm" id="btn-mode-existing" onclick="IPTransferComponent.toggleFileMode('existing')" style="border-color: var(--accent-cyan); color: var(--accent-cyan);">
                    Select Shared File
                  </button>
                  <button type="button" class="btn btn-secondary btn-sm" id="btn-mode-new" onclick="IPTransferComponent.toggleFileMode('new')">
                    Upload New File to Send
                  </button>
                </div>

                <!-- Existing Shared Files Dropdown -->
                <div id="file-select-existing-wrapper">
                  <select class="search-input" id="transfer-file-id" style="width: 100%;">
                    <option value="">-- Choose a shared file --</option>
                    ${files.map(f => `
                      <option value="${f.id}">${f.name} (${DashboardComponent.formatBytes(f.size)})</option>
                    `).join('')}
                  </select>
                </div>

                <!-- New File Upload Picker -->
                <div id="file-select-new-wrapper" style="display: none;">
                  <input type="file" class="search-input" id="transfer-file-upload" style="width: 100%;" />
                </div>
              </div>

              <!-- Target Device IP Address -->
              <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <label style="font-size: 12px; font-weight: 600; color: var(--text-secondary);">
                    Target Device IP Address (LAN)
                  </label>
                  <button type="button" class="btn btn-secondary btn-sm" style="font-size: 11px; padding: 2px 8px;" onclick="IPTransferComponent.switchTab('scanner')">
                    Select from Subnet Scan
                  </button>
                </div>
                <input type="text" class="search-input" id="transfer-target-ip" placeholder="e.g. 192.168.1.15" required style="font-family: var(--font-mono); font-weight: 700;" />
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
                  Current Host IP: <code>${localIp}</code> (Do not send to yourself)
                </div>
              </div>

              <!-- Target Port -->
              <div>
                <label style="font-size: 12px; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 6px;">
                  Target Port
                </label>
                <input type="number" class="search-input" id="transfer-target-port" value="8000" min="1" max="65535" required />
              </div>

              <!-- Transfer Priority (DSA Heap) -->
              <div>
                <label style="font-size: 12px; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 6px;">
                  Transfer Priority (Min-Heap Scheduling)
                </label>
                <select class="search-input" id="transfer-priority">
                  <option value="0">CRITICAL (Priority 0 - Immediate dispatch ahead of queue)</option>
                  <option value="1">HIGH (Priority 1 - Urgent file)</option>
                  <option value="2" selected>NORMAL (Priority 2 - Standard FIFO)</option>
                  <option value="3">LOW (Priority 3 - Background sync)</option>
                </select>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
                  Demonstrates <strong>Binary Min-Heap Priority Queue</strong>: priority 0 leapfrogs lower priorities.
                </div>
              </div>

              <!-- Submit Button -->
              <div style="display: flex; gap: 10px; margin-top: 10px;">
                <button type="submit" class="btn btn-primary" id="btn-submit-ip-transfer" style="flex: 1; justify-content: center; padding: 12px;">
                  <span>⚡</span> Dispatch File to Device IP
                </button>
                <button type="button" class="btn btn-secondary" onclick="IPTransferComponent.testPingTargetIP()" title="Verify reachability first">
                  <span>📶</span> Ping IP
                </button>
              </div>

            </div>
          </form>
        </div>

        <!-- Right: Real-Time Transfer Monitor & DSA Queue Stats -->
        <div class="glass-card">
          <div class="card-title-bar">
            <h3 class="card-title"><span>📊</span> IP Transfer Live Monitor</h3>
            <span class="status-dot"></span>
          </div>

          <div id="direct-transfer-live-status">
            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border-medium); border-radius: var(--radius-md); padding: 18px; margin-bottom: 16px;">
              <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 6px;">
                Offline Streaming Engine
              </div>
              <p style="font-size: 12px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">
                Transfers operate completely offline using 64KB chunk streaming and verify SHA-256 cryptographic hashes upon delivery.
              </p>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 12px;">
                <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                  <div style="color: var(--text-muted); font-size: 11px;">Algorithm</div>
                  <strong>Min-Heap O(log N)</strong>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                  <div style="color: var(--text-muted); font-size: 11px;">Integrity</div>
                  <strong>SHA-256 Checksum</strong>
                </div>
              </div>
            </div>

            <!-- Active / Recent Transfer Card -->
            <div id="direct-transfer-task-card" style="display: none; background: rgba(15, 23, 42, 0.9); border: 1px solid var(--border-medium); border-radius: var(--radius-md); padding: 16px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong id="dt-task-filename">filename.ext</strong>
                <span class="pill pill-synced" id="dt-task-status">WAITING</span>
              </div>
              <div class="progress-container" style="height: 10px; margin-bottom: 8px;">
                <div class="progress-fill" id="dt-task-progress-bar" style="width: 0%;"></div>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-secondary); font-family: var(--font-mono);">
                <span id="dt-task-bytes">0 / 0 KB</span>
                <span id="dt-task-speed">0 MB/s</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  // 3. Receive / Fetch Files from Remote IP View
  renderReceiveIPTab() {
    return `
      <div class="glass-card" style="margin-bottom: 24px;">
        <div class="card-title-bar">
          <h3 class="card-title"><span>📥</span> Pull & Download Files from Remote Device IP</h3>
          <span style="font-size: 12px; color: var(--text-muted);">Query file index of any peer on LAN</span>
        </div>

        <div style="display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap;">
          <input type="text" class="search-input" id="remote-fetch-ip" placeholder="Enter Peer IP Address (e.g. 192.168.1.18)" style="flex: 2; min-width: 200px; font-family: var(--font-mono);" />
          <input type="number" class="search-input" id="remote-fetch-port" value="8000" style="flex: 1; max-width: 120px;" />
          <button class="btn btn-primary" onclick="IPTransferComponent.fetchFilesFromRemoteIP()">
            <span>🔍</span> Fetch File Catalog
          </button>
        </div>

        <!-- Remote File List Results Container -->
        <div id="remote-files-container">
          ${this.isFetchingRemote ? `
            <div style="text-align: center; padding: 40px; color: var(--accent-cyan);">
              <div class="spinner"></div>
              <div style="margin-top: 10px;">Querying peer at entered IP over offline LAN...</div>
            </div>
          ` : this.renderRemoteFilesList()}
        </div>
      </div>
    `;
  },

  renderRemoteFilesList() {
    if (!this.remoteFiles || this.remoteFiles.length === 0) {
      return `
        <div style="text-align: center; color: var(--text-muted); padding: 30px;">
          Enter a peer device's LAN IP address above and click <strong>Fetch File Catalog</strong> to browse and download its files.
        </div>
      `;
    }

    const peerIp = document.getElementById('remote-fetch-ip')?.value || '';
    const peerPort = document.getElementById('remote-fetch-port')?.value || '8000';

    return `
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <div style="font-size: 13px; font-weight: 700; color: var(--accent-emerald); margin-bottom: 4px;">
          ✓ Found ${this.remoteFiles.length} file(s) on ${peerIp}:${peerPort}
        </div>
        ${this.remoteFiles.map(rf => `
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); gap: 12px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 12px; min-width: 200px;">
              <span style="font-size: 22px;">📁</span>
              <div>
                <div style="font-weight: 600; font-size: 14px;">${rf.name}</div>
                <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">
                  ${DashboardComponent.formatBytes(rf.size)} • ${rf.file_type} • SHA-256: ${rf.hash ? rf.hash.substring(0, 8) + '...' : 'none'}
                </div>
              </div>
            </div>
            <button class="btn btn-primary btn-sm" onclick="IPTransferComponent.downloadRemoteFile('${peerIp}', ${peerPort}, '${rf.id}', '${rf.name}', ${rf.size}, '${rf.hash || ''}')">
              <span>⬇</span> Download to Local Storage
            </button>
          </div>
        `).join('')}
      </div>
    `;
  },

  // 4. Subnet IP Scanner View
  renderScannerTab() {
    const results = this.scanResults;
    const devices = results ? results.devices_found : [];

    return `
      <div class="glass-card" style="margin-bottom: 24px;">
        <div class="card-title-bar">
          <div>
            <h3 class="card-title"><span>🔍</span> Offline LAN Subnet Scanner</h3>
            <p style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">
              Automatically discovers active phones, laptops, and tablets connected to this router/hotspot using OS ARP inspection & port probing
            </p>
          </div>
          <button class="btn btn-primary btn-sm" onclick="IPTransferComponent.runSubnetScan()" ${this.isScanning ? 'disabled' : ''}>
            <span>${this.isScanning ? '⏳' : '🔄'}</span> ${this.isScanning ? 'Scanning...' : 'Scan Subnet Now'}
          </button>
        </div>

        ${this.isScanning ? `
          <div style="text-align: center; padding: 40px; color: var(--accent-cyan);">
            <div class="spinner"></div>
            <div style="margin-top: 12px; font-weight: 600;">Probing offline subnet IP addresses in parallel...</div>
            <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Inspecting ARP table and socket ports</div>
          </div>
        ` : `
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>IP Address</th>
                  <th>Device / Host Name</th>
                  <th>MAC Address</th>
                  <th>LAN Sync Service</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${devices.map(d => `
                  <tr style="${d.has_lan_sync ? 'background: rgba(0, 240, 255, 0.05);' : ''}">
                    <td><code style="font-weight: 700; color: var(--accent-cyan); font-size: 14px;">${d.ip_address}</code></td>
                    <td><strong>${d.device_name}</strong></td>
                    <td><code>${d.mac_address || 'LAN Dynamic'}</code></td>
                    <td>
                      <span class="pill ${d.has_lan_sync ? 'pill-synced' : 'pill-priority-2'}">
                        ${d.has_lan_sync ? '⚡ ACTIVE SERVER' : (d.port_open ? 'PORT 8000 OPEN' : 'CONNECTED CLIENT')}
                      </span>
                    </td>
                    <td><span class="pill pill-synced">ONLINE</span></td>
                    <td>
                      <div style="display: flex; gap: 6px;">
                        <button class="btn btn-primary btn-sm" onclick="IPTransferComponent.selectDeviceIP('${d.ip_address}', ${d.port})">
                          <span>🎯</span> Send File
                        </button>
                        ${d.has_lan_sync ? `
                          <button class="btn btn-secondary btn-sm" onclick="IPTransferComponent.fetchFilesFromTarget('${d.ip_address}', ${d.port})">
                            <span>📥</span> Browse
                          </button>
                        ` : ''}
                      </div>
                    </td>
                  </tr>
                `).join('')}

                ${devices.length === 0 ? `
                  <tr>
                    <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">
                      Click <strong>Scan Subnet Now</strong> to inspect all connected devices on this offline network.
                    </td>
                  </tr>
                ` : ''}
              </tbody>
            </table>
          </div>
        `}
      </div>
    `;
  },

  // QR Code Rendering using embedded QRCodeGenerator
  drawQRCode(url) {
    const canvas = document.getElementById('qr-canvas');
    if (!canvas || !window.QRCodeGenerator) return;
    try {
      window.QRCodeGenerator.renderCanvas(canvas, url, {
        size: 180,
        colorDark: '#00f0ff',
        colorLight: '#090d16'
      });
    } catch (err) {
      console.error('QR rendering error:', err);
    }
  },

  copyMobileUrl(url) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url).then(() => {
        App.showToast('Copied offline URL to clipboard!', 'info');
      }).catch(() => {
        prompt('Copy this URL to open on your phone:', url);
      });
    } else {
      prompt('Copy this URL to open on your phone:', url);
    }
  },

  downloadQR() {
    const canvas = document.getElementById('qr-canvas');
    if (!canvas) return;
    const a = document.createElement('a');
    a.download = 'offline_lan_qr.png';
    a.href = canvas.toDataURL('image/png');
    a.click();
  },

  toggleFileMode(mode) {
    const existingWrapper = document.getElementById('file-select-existing-wrapper');
    const newWrapper = document.getElementById('file-select-new-wrapper');
    const btnExisting = document.getElementById('btn-mode-existing');
    const btnNew = document.getElementById('btn-mode-new');

    if (mode === 'existing') {
      if (existingWrapper) existingWrapper.style.display = 'block';
      if (newWrapper) newWrapper.style.display = 'none';
      if (btnExisting) { btnExisting.style.borderColor = 'var(--accent-cyan)'; btnExisting.style.color = 'var(--accent-cyan)'; }
      if (btnNew) { btnNew.style.borderColor = 'var(--border-subtle)'; btnNew.style.color = 'var(--text-secondary)'; }
    } else {
      if (existingWrapper) existingWrapper.style.display = 'none';
      if (newWrapper) newWrapper.style.display = 'block';
      if (btnNew) { btnNew.style.borderColor = 'var(--accent-cyan)'; btnNew.style.color = 'var(--accent-cyan)'; }
      if (btnExisting) { btnExisting.style.borderColor = 'var(--border-subtle)'; btnExisting.style.color = 'var(--text-secondary)'; }
    }
  },

  async handleMobileQuickUpload(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    App.showToast(`Uploading ${files.length} file(s) over offline LAN...`, 'info');

    for (let i = 0; i < files.length; i++) {
      try {
        await API.uploadFile(files[i]);
      } catch (err) {
        App.showToast(`Upload failed for ${files[i].name}: ${err.message}`, 'error');
      }
    }
    App.showToast(`Uploaded ${files.length} file(s) successfully!`, 'success');
    await App.refreshFiles();
    this.render();
  },

  async submitDirectTransfer(event) {
    event.preventDefault();
    const targetIp = document.getElementById('transfer-target-ip')?.value?.trim();
    const targetPort = parseInt(document.getElementById('transfer-target-port')?.value || '8000');
    const priority = parseInt(document.getElementById('transfer-priority')?.value || '2');

    if (!targetIp) {
      App.showToast('Please enter target device IP address.', 'error');
      return;
    }

    const newWrapper = document.getElementById('file-select-new-wrapper');
    const isNewUpload = newWrapper && newWrapper.style.display !== 'none';

    if (isNewUpload) {
      const fileInput = document.getElementById('transfer-file-upload');
      if (!fileInput.files || fileInput.files.length === 0) {
        App.showToast('Please select a file to transfer.', 'error');
        return;
      }
      const file = fileInput.files[0];
      App.showToast(`Enqueuing streaming upload of ${file.name} to ${targetIp}...`, 'info');
      try {
        const res = await API.uploadToIp(file, targetIp, targetPort, priority);
        App.showToast(`Transfer scheduled: ${res.message}`, 'success');
        this.trackTransferTask(res.task);
        App.refreshTransfers();
      } catch (err) {
        App.showToast(`Direct transfer error: ${err.message}`, 'error');
      }
    } else {
      const fileId = document.getElementById('transfer-file-id')?.value;
      if (!fileId) {
        App.showToast('Please select a shared file.', 'error');
        return;
      }
      App.showToast(`Submitting transfer to PriorityHeap for ${targetIp}...`, 'info');
      try {
        const res = await API.directIpTransfer({
          target_ip: targetIp,
          target_port: targetPort,
          file_id: fileId,
          priority: priority,
          direction: 'UPLOAD'
        });
        App.showToast(`Transfer queued: ${res.task.file_name}`, 'success');
        this.trackTransferTask(res.task);
        App.refreshTransfers();
      } catch (err) {
        App.showToast(`Transfer failed: ${err.message}`, 'error');
      }
    }
  },

  trackTransferTask(task) {
    const card = document.getElementById('direct-transfer-task-card');
    if (!card) return;
    card.style.display = 'block';

    const fn = document.getElementById('dt-task-filename');
    const st = document.getElementById('dt-task-status');
    const bar = document.getElementById('dt-task-progress-bar');
    const bytes = document.getElementById('dt-task-bytes');
    const spd = document.getElementById('dt-task-speed');

    if (fn) fn.textContent = task.file_name;
    if (st) st.textContent = task.status;
    if (bar) bar.style.width = `${task.percentage || 0}%`;
    if (bytes) bytes.textContent = `${DashboardComponent.formatBytes(task.transferred_bytes || 0)} / ${DashboardComponent.formatBytes(task.size)}`;
    if (spd) spd.textContent = `${task.speed || 0} MB/s`;

    // Listen for real-time WebSocket progress updates
    wsClient.on('TRANSFER_PROGRESS', (updated) => {
      if (updated.transfer_id === task.transfer_id) {
        if (st) st.textContent = updated.status;
        if (bar) bar.style.width = `${updated.percentage || 0}%`;
        if (bytes) bytes.textContent = `${DashboardComponent.formatBytes(updated.transferred_bytes || 0)} / ${DashboardComponent.formatBytes(updated.size)}`;
        if (spd) spd.textContent = `${updated.speed || 0} MB/s`;
      }
    });

    wsClient.on('TRANSFER_COMPLETED', (completed) => {
      if (completed.transfer_id === task.transfer_id) {
        if (st) {
          st.textContent = 'COMPLETED';
          st.className = 'pill pill-synced';
        }
        if (bar) bar.style.width = '100%';
        App.showToast(`Transfer of ${completed.file_name} completed with SHA-256 verification!`, 'success');
      }
    });
  },

  async testPingTargetIP() {
    const ip = document.getElementById('transfer-target-ip')?.value?.trim();
    const port = parseInt(document.getElementById('transfer-target-port')?.value || '8000');
    if (!ip) {
      App.showToast('Please enter an IP to ping.', 'error');
      return;
    }
    App.showToast(`Pinging ${ip}:${port}...`, 'info');
    try {
      const res = await API.pingIp(ip, port);
      if (res.reachable) {
        if (res.has_lan_sync) {
          App.showToast(`✓ Found LAN Sync Peer "${res.peer.device_name}" on ${ip}!`, 'success');
        } else {
          App.showToast(`✓ Port ${port} is reachable on ${ip}`, 'info');
        }
      } else {
        App.showToast(`Device at ${ip}:${port} is unreachable. Ensure it is on the same Wi-Fi router.`, 'error');
      }
    } catch (err) {
      App.showToast(`Ping error: ${err.message}`, 'error');
    }
  },

  quickSendFileToIP(fileId, fileName) {
    this.switchTab('send_ip');
    setTimeout(() => {
      const sel = document.getElementById('transfer-file-id');
      if (sel) sel.value = fileId;
      const ipInput = document.getElementById('transfer-target-ip');
      if (ipInput) ipInput.focus();
      App.showToast(`Selected "${fileName}". Enter target device IP to send.`, 'info');
    }, 100);
  },

  selectDeviceIP(ip, port) {
    this.switchTab('send_ip');
    setTimeout(() => {
      const ipInput = document.getElementById('transfer-target-ip');
      const portInput = document.getElementById('transfer-target-port');
      if (ipInput) ipInput.value = ip;
      if (portInput) portInput.value = port || 8000;
      App.showToast(`Selected device IP: ${ip}. Choose a file to send.`, 'info');
    }, 100);
  },

  fetchFilesFromTarget(ip, port) {
    this.switchTab('receive_ip');
    setTimeout(() => {
      const ipInput = document.getElementById('remote-fetch-ip');
      const portInput = document.getElementById('remote-fetch-port');
      if (ipInput) ipInput.value = ip;
      if (portInput) portInput.value = port || 8000;
      this.fetchFilesFromRemoteIP();
    }, 100);
  },

  async fetchFilesFromRemoteIP() {
    const ip = document.getElementById('remote-fetch-ip')?.value?.trim();
    const port = parseInt(document.getElementById('remote-fetch-port')?.value || '8000');
    if (!ip) {
      App.showToast('Please enter peer IP address.', 'error');
      return;
    }

    this.isFetchingRemote = true;
    const container = document.getElementById('remote-files-container');
    if (container) {
      container.innerHTML = `
        <div style="text-align: center; padding: 40px; color: var(--accent-cyan);">
          <div class="spinner"></div>
          <div style="margin-top: 10px;">Querying peer at ${ip}:${port}...</div>
        </div>
      `;
    }

    try {
      const res = await API.request(`/api/files?folder=`, {
        headers: { 'X-Remote-IP': ip }
      }).catch(async () => {
        // Direct peer query fallback
        const r = await fetch(`http://${ip}:${port}/api/files`);
        return await r.json();
      });

      this.remoteFiles = res.files || [];
      this.isFetchingRemote = false;
      if (container) {
        container.innerHTML = this.renderRemoteFilesList();
      }
      App.showToast(`Fetched ${this.remoteFiles.length} file(s) from ${ip}`, 'success');
    } catch (err) {
      this.isFetchingRemote = false;
      if (container) {
        container.innerHTML = `
          <div style="text-align: center; color: var(--accent-rose); padding: 30px;">
            Failed to query peer at ${ip}:${port}. Ensure the LAN Sync application is running on that device.
          </div>
        `;
      }
      App.showToast(`Failed to fetch peer files: ${err.message}`, 'error');
    }
  },

  async downloadRemoteFile(peerIp, peerPort, fileId, fileName, size, expectedHash) {
    App.showToast(`Queueing download of ${fileName} from ${peerIp}...`, 'info');
    try {
      const res = await API.directIpTransfer({
        target_ip: peerIp,
        target_port: peerPort,
        file_id: fileId,
        file_name: fileName,
        direction: 'DOWNLOAD',
        expected_hash: expectedHash,
        priority: 1
      });
      App.showToast(`Download enqueued in PriorityHeap: ${fileName}`, 'success');
      App.refreshTransfers();
      App.navigate('transfers');
    } catch (err) {
      App.showToast(`Download failed: ${err.message}`, 'error');
    }
  },

  async runSubnetScan() {
    this.isScanning = true;
    if (this.currentSubTab !== 'scanner') {
      this.switchTab('scanner');
    } else {
      this.render();
    }

    try {
      this.scanResults = await API.scanSubnet();
      this.isScanning = false;
      this.render();
      App.showToast(`Subnet scan complete! Found ${this.scanResults.total_found} device(s).`, 'success');
    } catch (err) {
      this.isScanning = false;
      this.render();
      App.showToast(`Subnet scan error: ${err.message}`, 'error');
    }
  }
};
