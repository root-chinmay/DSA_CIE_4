// frontend/js/api.js - Unified REST & WebSocket LAN Client

const API = {
  baseUrl: window.location.origin,

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = options.headers || {};
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let errDetail = `HTTP ${response.status}`;
        try {
          const errJson = await response.json();
          errDetail = errJson.detail || errDetail;
        } catch (_) {}
        throw new Error(errDetail);
      }
      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  },

  // Devices & Network
  async getDevices() { return (await this.request('/api/devices')).devices; },
  async ping() { return await this.request('/api/devices/ping'); },
  async getNetworkDiagnostics() { return await this.request('/api/devices/network'); },
  async pairDevice(deviceId, deviceName, pairingCode) {
    return await this.request('/api/devices/pair', {
      method: 'POST',
      body: JSON.stringify({ device_id: deviceId, device_name: deviceName, pairing_code: pairingCode })
    });
  },
  async manualConnect(ip, port, pairingCode) {
    return await this.request('/api/devices/connect', {
      method: 'POST',
      body: JSON.stringify({ ip_address: ip, port: parseInt(port), pairing_code: pairingCode })
    });
  },
  async getNetworkGraph() { return await this.request('/api/devices/graph'); },
  async getGraphBFS(startId) { return await this.request(`/api/devices/graph/bfs${startId ? `?start_id=${startId}` : ''}`); },
  async getGraphDFS(startId) { return await this.request(`/api/devices/graph/dfs${startId ? `?start_id=${startId}` : ''}`); },
  async getShortestPath(startId, endId) {
    return await this.request(`/api/devices/graph/shortest_path?start_id=${startId}&end_id=${endId}`);
  },
  async scanSubnet(port = 8000) { return await this.request(`/api/devices/scan-subnet?port=${port}`); },
  async getMobileInfo() { return await this.request('/api/devices/mobile-info'); },
  async pingIp(ip, port = 8000) {
    return await this.request('/api/devices/ping-ip', {
      method: 'POST',
      body: JSON.stringify({ ip_address: ip, port: parseInt(port) })
    });
  },

  // Files
  async getFiles(params = {}) {
    const query = new URLSearchParams(params).toString();
    return await this.request(`/api/files${query ? `?${query}` : ''}`);
  },
  async getFileTree(maxDepth = null) {
    return await this.request(`/api/files/tree${maxDepth ? `?max_depth=${maxDepth}` : ''}`);
  },
  async getFileDetails(fileId) { return await this.request(`/api/files/${fileId}`); },
  async deleteFile(fileId) {
    return await this.request(`/api/files/${fileId}/delete`, { method: 'POST' });
  },
  async renameFile(fileId, newName) {
    return await this.request(`/api/files/${fileId}/rename`, {
      method: 'POST',
      body: JSON.stringify({ new_name: newName })
    });
  },
  async getDuplicates() { return await this.request('/api/files/duplicates'); },
  async searchFiles(q, autocomplete = false, limit = 20) {
    return await this.request(`/api/files/search?q=${encodeURIComponent(q)}&autocomplete=${autocomplete}&limit=${limit}`);
  },
  async uploadFile(fileObj, folderPath = '') {
    const formData = new FormData();
    formData.append('file', fileObj);
    formData.append('folder_path', folderPath);
    return await this.request('/api/files/upload', {
      method: 'POST',
      body: formData
    });
  },

  // Folders
  async getFolders() { return (await this.request('/api/folders')).folders; },
  async addFolder(folderPath, folderName = null) {
    return await this.request('/api/folders', {
      method: 'POST',
      body: JSON.stringify({ folder_path: folderPath, folder_name: folderName })
    });
  },
  async removeFolder(folderId) {
    return await this.request(`/api/folders/${folderId}`, { method: 'DELETE' });
  },
  async scanFolders(forceRehash = false) {
    return await this.request(`/api/folders/scan?force_rehash=${forceRehash}`, { method: 'POST' });
  },

  // Transfers
  async getTransfers() { return await this.request('/api/transfers'); },
  async enqueueTransfer(payload) {
    return await this.request('/api/transfers', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  async updateTransferPriority(transferId, priority) {
    return await this.request(`/api/transfers/${transferId}/priority`, {
      method: 'POST',
      body: JSON.stringify({ priority: parseInt(priority) })
    });
  },
  async cancelTransfer(transferId) {
    return await this.request(`/api/transfers/${transferId}/cancel`, { method: 'POST' });
  },
  async directIpTransfer(payload) {
    return await this.request('/api/transfers/direct-ip', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  async uploadToIp(fileObj, targetIp, targetPort = 8000, priority = 2) {
    const formData = new FormData();
    formData.append('file', fileObj);
    formData.append('target_ip', targetIp);
    formData.append('target_port', targetPort);
    formData.append('priority', priority);
    return await this.request('/api/transfers/upload-to-ip', {
      method: 'POST',
      body: formData
    });
  },

  // Synchronization
  async getSyncDiff(peerIp = null, peerPort = 8000) {
    const query = peerIp ? `?peer_ip=${peerIp}&peer_port=${peerPort}` : '';
    return await this.request(`/api/sync/diff${query}`);
  },
  async startSync(payload = {}) {
    return await this.request('/api/sync/start', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  async getConflicts() { return (await this.request('/api/sync/conflicts')).conflicts; },
  async resolveConflict(conflictId, resolution) {
    return await this.request(`/api/sync/conflicts/${conflictId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution })
    });
  },

  // DSA Visualizer
  async getDSAOverview() { return await this.request('/api/dsa/overview'); },
  async getDSATree() { return await this.request('/api/dsa/tree'); },
  async getDSAHashTable() { return await this.request('/api/dsa/hash_table'); },
  async getDSATrie(depth = 3) { return await this.request(`/api/dsa/trie?depth=${depth}`); },
  async getDSAHeap() { return await this.request('/api/dsa/heap'); },
  async benchmarkSort(by = 'size') {
    return await this.request(`/api/dsa/benchmark_sort?by=${by}`, { method: 'POST' });
  },

  // Settings & Analytics
  async getSettings() { return await this.request('/api/settings'); },
  async updateSettings(payload) {
    return await this.request('/api/settings', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  async resetPairingCode() { return await this.request('/api/settings/pairing-code/reset', { method: 'POST' }); },
  async toggleDemoMode() { return await this.request('/api/settings/demo/toggle', { method: 'POST' }); },
  async getLogs(limit = 100) { return (await this.request(`/api/settings/logs?limit=${limit}`)).logs; },
  async getAnalytics() { return await this.request('/api/analytics'); }
};

// Real-time WebSocket Client
class WebSocketClient {
  constructor() {
    this.ws = null;
    this.listeners = new Map();
    this.connect();
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('✓ WebSocket connected to LAN host.');
    };

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const eventType = payload.type;
        const listeners = this.listeners.get(eventType) || [];
        listeners.forEach(cb => cb(payload.data, payload.timestamp));

        // Global wildcard listeners
        const allListeners = this.listeners.get('*') || [];
        allListeners.forEach(cb => cb(eventType, payload.data, payload.timestamp));
      } catch (err) {
        console.error('WebSocket message parse error:', err);
      }
    };

    this.ws.onclose = () => {
      console.warn('WebSocket disconnected. Reconnecting in 3s...');
      setTimeout(() => this.connect(), 3000);
    };
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
  }
}

const wsClient = new WebSocketClient();
