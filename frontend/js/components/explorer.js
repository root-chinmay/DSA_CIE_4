// frontend/js/components/explorer.js - File Explorer with Tree, Dropzone, Trie Search & Sorter

const ExplorerComponent = {
  sortBy: 'name',
  sortAlgorithm: 'merge_sort',
  sortReverse: false,
  filterType: 'all',
  searchQuery: '',

  render() {
    const el = document.getElementById('view-files');
    if (!el) return;

    const files = State.files || [];
    const tree = State.fileTree;
    const currentFolder = State.currentFolder;

    // Filter files
    let filteredFiles = files.filter(f => {
      const matchFolder = !currentFolder || f.relative_path.startsWith(currentFolder);
      const matchType = this.filterType === 'all' || f.file_type.toLowerCase() === this.filterType.toLowerCase();
      const matchSearch = !this.searchQuery || f.name.toLowerCase().includes(this.searchQuery.toLowerCase());
      return matchFolder && matchType && matchSearch;
    });

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h2 class="page-title">Shared File Explorer</h2>
          <p class="page-subtitle">Hierarchical FileTree navigation with streaming transfers and SHA-256 verification</p>
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
          <button class="btn btn-secondary btn-sm" onclick="App.scanFolders(true)">
            <span>🔄</span> Re-scan & Hash
          </button>
          <button class="btn btn-primary btn-sm" onclick="App.navigate('ip-transfer')">
            <span>🌐</span> Transfer by IP
          </button>
          <button class="btn btn-primary btn-sm" onclick="document.getElementById('file-upload-input').click()">
            <span>⬆</span> Upload Files
          </button>
          <input type="file" id="file-upload-input" multiple style="display: none;" onchange="ExplorerComponent.handleFileSelect(event)" />
        </div>
      </div>

      <!-- Drag & Drop Upload Zone -->
      <div class="dropzone" id="explorer-dropzone"
           ondragover="ExplorerComponent.onDragOver(event)"
           ondragleave="ExplorerComponent.onDragLeave(event)"
           ondrop="ExplorerComponent.onDrop(event)"
           onclick="document.getElementById('file-upload-input').click()">
        <div class="dropzone-icon">📁</div>
        <div style="font-weight: 600; font-size: 15px; margin-bottom: 4px;">
          Drag & drop files here to share across LAN
        </div>
        <div style="font-size: 13px; color: var(--text-muted);">
          or <span style="color: var(--accent-cyan); text-decoration: underline;">click to browse files</span> on your computer
        </div>
      </div>

      <!-- Explorer Two-Column Layout -->
      <div class="explorer-layout">
        <!-- Left: Hierarchical FileTree Sidebar -->
        <div class="tree-panel">
          <div style="font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.05em;">
            Directory Hierarchy (Tree)
          </div>
          <div class="tree-node-item ${!currentFolder ? 'selected' : ''}" onclick="ExplorerComponent.selectFolder('')">
            <span>📁</span> <span>/ (All Shared Files)</span>
          </div>
          <div id="file-tree-render-container">
            ${this.renderTreeNodes(tree ? tree.children : [], '')}
          </div>
        </div>

        <!-- Right: File Browser Table with Trie Search and Sort Controls -->
        <div>
          <!-- Search & Filter Controls -->
          <div class="glass-card" style="padding: 16px; margin-bottom: 18px;">
            <div style="display: flex; flex-wrap: wrap; gap: 14px; align-items: center; justify-content: space-between;">
              <!-- Trie Prefix Search Bar -->
              <div class="search-wrapper">
                <span class="search-icon">🔍</span>
                <input type="text" class="search-input" id="trie-search-input"
                       placeholder="Prefix search using Trie (e.g. 'proj', 'report')..."
                       value="${this.searchQuery}"
                       oninput="ExplorerComponent.onSearchInput(event)"
                       onkeydown="ExplorerComponent.onSearchKey(event)" />
                <div class="autocomplete-dropdown" id="trie-autocomplete-dropdown"></div>
              </div>

              <!-- Sorting & Filtering Toolbar -->
              <div style="display: flex; gap: 10px; align-items: center;">
                <label style="font-size: 12px; color: var(--text-muted);">Sort By:</label>
                <select class="btn btn-secondary btn-sm" id="sort-field-select" onchange="ExplorerComponent.changeSortField(this.value)">
                  <option value="name" ${this.sortBy === 'name' ? 'selected' : ''}>Name</option>
                  <option value="size" ${this.sortBy === 'size' ? 'selected' : ''}>Size</option>
                  <option value="modified_time" ${this.sortBy === 'modified_time' ? 'selected' : ''}>Date Modified</option>
                  <option value="file_type" ${this.sortBy === 'file_type' ? 'selected' : ''}>Type</option>
                </select>

                <select class="btn btn-secondary btn-sm" id="sort-algo-select" onchange="ExplorerComponent.changeSortAlgorithm(this.value)">
                  <option value="merge_sort" ${this.sortAlgorithm === 'merge_sort' ? 'selected' : ''}>Merge Sort O(N log N)</option>
                  <option value="quick_sort" ${this.sortAlgorithm === 'quick_sort' ? 'selected' : ''}>Quick Sort O(N log N)</option>
                </select>

                <button class="btn btn-secondary btn-sm" onclick="ExplorerComponent.toggleSortDirection()" title="Reverse Sort">
                  ${this.sortReverse ? '⬇ Desc' : '⬆ Asc'}
                </button>
              </div>
            </div>
          </div>

          <!-- Files Table -->
          <div class="glass-card" style="padding: 0;">
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>File Name</th>
                    <th>Relative Path</th>
                    <th>Size</th>
                    <th>SHA-256 Hash</th>
                    <th>Modified Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  ${filteredFiles.map(f => `
                    <tr>
                      <td>
                        <div style="display: flex; align-items: center; gap: 8px;">
                          <span>${this.getFileIcon(f.file_type)}</span>
                          <strong>${f.name}</strong>
                        </div>
                      </td>
                      <td><code style="color: var(--text-secondary);">${f.relative_path}</code></td>
                      <td>${DashboardComponent.formatBytes(f.size)}</td>
                      <td>
                        <span class="pill pill-priority-3" style="font-family: var(--font-mono); cursor: pointer;"
                              title="${f.hash}" onclick="navigator.clipboard.writeText('${f.hash}'); App.showToast('Hash copied!', 'info');">
                          ${f.hash ? f.hash.substring(0, 8) + '...' : 'Pending'}
                        </span>
                      </td>
                      <td style="color: var(--text-muted); font-size: 12px;">
                        ${new Date((f.modified_time || 0) * 1000).toLocaleString()}
                      </td>
                      <td>
                        <div style="display: flex; gap: 6px;">
                          <a href="/api/files/${f.file_id}/download" class="btn btn-primary btn-sm" download title="Direct Download">
                            ⬇
                          </a>
                          <button class="btn btn-secondary btn-sm" onclick="IPTransferComponent.quickSendFileToIP('${f.file_id}', '${f.name}')" title="Send to Device IP">
                            🌐
                          </button>
                          <button class="btn btn-secondary btn-sm" onclick="ExplorerComponent.enqueueFileTransfer('${f.file_id}')" title="Queue for Priority Transfer">
                            ⚡
                          </button>
                          <button class="btn btn-secondary btn-sm" onclick="ExplorerComponent.promptRename('${f.file_id}', '${f.name}')" title="Rename">
                            ✏
                          </button>
                          <button class="btn btn-danger btn-sm" onclick="ExplorerComponent.confirmDelete('${f.file_id}', '${f.name}')" title="Delete">
                            🗑
                          </button>
                        </div>
                      </td>
                    </tr>
                  `).join('')}
                  ${filteredFiles.length === 0 ? `
                    <tr>
                      <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 36px;">
                        No files matching current folder or query. Upload or drag files into the box above.
                      </td>
                    </tr>
                  ` : ''}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  renderTreeNodes(children, parentPath, depth = 0) {
    if (!children || children.length === 0) return '';
    return children.filter(c => c.is_dir).map(dir => {
      const isSelected = State.currentFolder === dir.relative_path;
      return `
        <div style="margin-left: ${depth * 14}px;">
          <div class="tree-node-item ${isSelected ? 'selected' : ''}"
               onclick="ExplorerComponent.selectFolder('${dir.relative_path}')">
            <span>📁</span>
            <span>${dir.name}</span>
            <span style="font-size: 10px; color: var(--text-muted); margin-left: auto;">
              ${DashboardComponent.formatBytes(dir.size)}
            </span>
          </div>
          ${this.renderTreeNodes(dir.children, dir.relative_path, depth + 1)}
        </div>
      `;
    }).join('');
  },

  selectFolder(path) {
    State.currentFolder = path;
    this.render();
  },

  getFileIcon(ext) {
    const e = (ext || '').toLowerCase();
    if (['pdf'].includes(e)) return '📄';
    if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(e)) return '🖼';
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(e)) return '📦';
    if (['py', 'js', 'html', 'css', 'ts', 'cpp', 'java'].includes(e)) return '💻';
    if (['mp4', 'mkv', 'mov', 'avi'].includes(e)) return '🎬';
    if (['mp3', 'wav', 'ogg'].includes(e)) return '🎵';
    if (['docx', 'doc', 'txt', 'md'].includes(e)) return '📝';
    return '📄';
  },

  async onSearchInput(event) {
    const val = event.target.value.trim();
    this.searchQuery = val;
    const dropdown = document.getElementById('trie-autocomplete-dropdown');

    if (val.length >= 2) {
      try {
        const res = await API.searchFiles(val, true, 8);
        if (res.suggestions && res.suggestions.length > 0) {
          dropdown.style.display = 'block';
          dropdown.innerHTML = res.suggestions.map(s => `
            <div class="autocomplete-item" onclick="ExplorerComponent.applySuggestion('${s}')">
              <span>🔍</span> <span>${s}</span>
            </div>
          `).join('');
        } else {
          dropdown.style.display = 'none';
        }
      } catch (err) {
        dropdown.style.display = 'none';
      }
    } else {
      dropdown.style.display = 'none';
    }

    this.render();
  },

  applySuggestion(suggestion) {
    this.searchQuery = suggestion;
    const input = document.getElementById('trie-search-input');
    if (input) input.value = suggestion;
    document.getElementById('trie-autocomplete-dropdown').style.display = 'none';
    this.render();
  },

  onDragOver(e) {
    e.preventDefault();
    document.getElementById('explorer-dropzone').classList.add('dragover');
  },

  onDragLeave(e) {
    e.preventDefault();
    document.getElementById('explorer-dropzone').classList.remove('dragover');
  },

  async onDrop(e) {
    e.preventDefault();
    document.getElementById('explorer-dropzone').classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      this.uploadMultipleFiles(files);
    }
  },

  handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
      this.uploadMultipleFiles(files);
    }
  },

  async uploadMultipleFiles(files) {
    App.showToast(`Uploading ${files.length} file(s)...`, 'info');
    for (let file of files) {
      try {
        await API.uploadFile(file, State.currentFolder);
        App.showToast(`Uploaded: ${file.name}`, 'success');
      } catch (err) {
        App.showToast(`Upload failed for ${file.name}: ${err.message}`, 'error');
      }
    }
    App.refreshFiles();
  },

  async enqueueFileTransfer(fileId) {
    const file = State.files.find(f => f.file_id === fileId);
    if (!file) return;

    try {
      await API.enqueueTransfer({
        file_name: file.name,
        size: file.size,
        source_device: State.hostInfo.device_name,
        destination_device: "LAN Broadcast / Peers",
        direction: "UPLOAD",
        priority: 1, // High priority
        file_id: file.file_id,
        expected_hash: file.hash
      });
      App.showToast(`Enqueued ${file.name} to transfer priority queue!`, 'success');
      App.refreshTransfers();
    } catch (err) {
      App.showToast(`Failed to enqueue: ${err.message}`, 'error');
    }
  },

  async promptRename(fileId, oldName) {
    const newName = prompt('Enter new filename:', oldName);
    if (newName && newName.trim() && newName !== oldName) {
      try {
        await API.renameFile(fileId, newName.trim());
        App.showToast(`Renamed to ${newName}`, 'success');
        App.refreshFiles();
      } catch (err) {
        App.showToast(`Rename failed: ${err.message}`, 'error');
      }
    }
  },

  async confirmDelete(fileId, name) {
    if (confirm(`Are you sure you want to delete '${name}'? This cannot be undone.`)) {
      try {
        await API.deleteFile(fileId);
        App.showToast(`Deleted ${name}`, 'success');
        App.refreshFiles();
      } catch (err) {
        App.showToast(`Delete failed: ${err.message}`, 'error');
      }
    }
  },

  changeSortField(field) {
    this.sortBy = field;
    this.applySort();
  },

  changeSortAlgorithm(algo) {
    this.sortAlgorithm = algo;
    this.applySort();
  },

  toggleSortDirection() {
    this.sortReverse = !this.sortReverse;
    this.applySort();
  },

  async applySort() {
    try {
      const res = await API.getFiles({
        folder: State.currentFolder,
        sort_by: this.sortBy,
        algorithm: this.sortAlgorithm,
        reverse: this.sortReverse
      });
      State.setFiles(res.files);
      if (res.sort_metrics) {
        App.showToast(`Sorted via ${res.sort_metrics.algorithm} (${res.sort_metrics.comparisons} comparisons in ${res.sort_metrics.elapsed_ms}ms)`, 'info');
      }
      this.render();
    } catch (err) {
      console.error(err);
    }
  }
};
