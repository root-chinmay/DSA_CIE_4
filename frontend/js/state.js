// frontend/js/state.js - Reactive State Store & WebSocket Event Listeners

const State = {
  hostInfo: {
    device_id: '',
    device_name: '',
    ip_address: '127.0.0.1',
    port: 8000,
    pairing_code: '------',
    demo_mode: false
  },
  devices: [],
  files: [],
  fileTree: null,
  folders: [],
  transfers: {
    fifo_queue: [],
    priority_heap: [],
    active_tasks: [],
    history: []
  },
  duplicates: [],
  conflicts: [],
  currentFolder: '',
  activeTab: 'dashboard',
  dsaOverview: null,

  listeners: new Map(),

  subscribe(key, callback) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, []);
    }
    this.listeners.get(key).push(callback);
  },

  notify(key) {
    const cbs = this.listeners.get(key) || [];
    cbs.forEach(cb => cb(this[key]));
  },

  setHostInfo(info) {
    this.hostInfo = { ...this.hostInfo, ...info };
    this.notify('hostInfo');
  },

  setDevices(devices) {
    this.devices = devices;
    this.notify('devices');
  },

  setFiles(files) {
    this.files = files;
    this.notify('files');
  },

  setFileTree(tree) {
    this.fileTree = tree;
    this.notify('fileTree');
  },

  setFolders(folders) {
    this.folders = folders;
    this.notify('folders');
  },

  setTransfers(transfersData) {
    this.transfers = transfersData;
    this.notify('transfers');
  },

  setDuplicates(duplicates) {
    this.duplicates = duplicates;
    this.notify('duplicates');
  },

  setConflicts(conflicts) {
    this.conflicts = conflicts;
    this.notify('conflicts');
  },

  setDSAOverview(data) {
    this.dsaOverview = data;
    this.notify('dsaOverview');
  },

  setActiveTab(tabName) {
    this.activeTab = tabName;
    this.notify('activeTab');
  }
};

// WebSocket Event Subscriptions
wsClient.on('TRANSFER_PROGRESS', (task) => {
  // Update progress in active task list without full refetch
  if (State.transfers && State.transfers.active_tasks) {
    const idx = State.transfers.active_tasks.findIndex(t => t.transfer_id === task.transfer_id);
    if (idx !== -1) {
      State.transfers.active_tasks[idx] = task;
    } else {
      State.transfers.active_tasks.push(task);
    }
    State.notify('transfers');
  }
});

wsClient.on('TRANSFER_COMPLETED', (task) => {
  App.showToast(`✓ Transfer completed: ${task.file_name}`, 'success');
  App.refreshTransfers();
  App.refreshFiles();
});

wsClient.on('TRANSFER_FAILED', (task) => {
  App.showToast(`✕ Transfer failed: ${task.file_name}`, 'error');
  App.refreshTransfers();
});

wsClient.on('DEVICE_CONNECTED', (device) => {
  App.showToast(`💻 New device discovered: ${device.device_name}`, 'info');
  App.refreshDevices();
});

wsClient.on('DEVICE_DISCONNECTED', (data) => {
  App.refreshDevices();
});

wsClient.on('CONFLICT_DETECTED', (data) => {
  App.showToast(`⚠ Synchronization conflict: ${data.file_path}`, 'warning');
  App.refreshConflicts();
});

wsClient.on('FILES_UPDATED', () => {
  App.refreshFiles();
});
