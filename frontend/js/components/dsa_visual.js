// frontend/js/components/dsa_visual.js - Interactive DSA Visualizer & Complexity Analysis

const DSAVisualizerComponent = {
  activeSubTab: 'tree',
  overviewData: null,
  hashData: null,
  trieData: null,
  treeData: null,
  heapData: null,
  sortBenchmarkData: null,

  async render() {
    const el = document.getElementById('view-dsa');
    if (!el) return;

    // Load overview
    try {
      this.overviewData = await API.getDSAOverview();
    } catch (_) {}

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h2 class="page-title">🧠 Data Structures & Algorithms Visualizer</h2>
          <p class="page-subtitle">Demonstrates authentic DSA implementations actively powering the offline networking architecture</p>
        </div>
      </div>

      <!-- Navigation Tabs for DSA Subsystems -->
      <div class="dsa-nav">
        <button class="dsa-tab ${this.activeSubTab === 'tree' ? 'active' : ''}" onclick="DSAVisualizerComponent.switchTab('tree')">
          📁 1. File Tree (Hierarchy & Traversals)
        </button>
        <button class="dsa-tab ${this.activeSubTab === 'hash_table' ? 'active' : ''}" onclick="DSAVisualizerComponent.switchTab('hash_table')">
          🗄 2. Hash Table (Separate Chaining)
        </button>
        <button class="dsa-tab ${this.activeSubTab === 'trie' ? 'active' : ''}" onclick="DSAVisualizerComponent.switchTab('trie')">
          🌲 3. Filename Trie (Prefix Search)
        </button>
        <button class="dsa-tab ${this.activeSubTab === 'queue' ? 'active' : ''}" onclick="DSAVisualizerComponent.switchTab('queue')">
          ⏳ 4. Transfer Queue (FIFO)
        </button>
        <button class="dsa-tab ${this.activeSubTab === 'heap' ? 'active' : ''}" onclick="DSAVisualizerComponent.switchTab('heap')">
          ⛰ 5. Priority Heap (Scheduler)
        </button>
        <button class="dsa-tab ${this.activeSubTab === 'graph' ? 'active' : ''}" onclick="DSAVisualizerComponent.switchTab('graph')">
          🕸 6. Network Graph (BFS/DFS/Dijkstra)
        </button>
        <button class="dsa-tab ${this.activeSubTab === 'sorting' ? 'active' : ''}" onclick="DSAVisualizerComponent.switchTab('sorting')">
          ⚡ 7. Merge Sort vs Quick Sort
        </button>
        <button class="dsa-tab ${this.activeSubTab === 'complexity' ? 'active' : ''}" onclick="DSAVisualizerComponent.switchTab('complexity')">
          📊 8. Algorithm Complexity Analysis
        </button>
      </div>

      <!-- Active DSA View Content -->
      <div id="dsa-active-view-container">
        ${this.renderActiveSubTab()}
      </div>
    `;

    // Trigger canvas or sub-renders if needed
    if (this.activeSubTab === 'heap') {
      setTimeout(() => this.drawHeapCanvas(), 50);
    }
  },

  async switchTab(tabName) {
    this.activeSubTab = tabName;
    if (tabName === 'hash_table' && !this.hashData) {
      this.hashData = await API.getDSAHashTable();
    } else if (tabName === 'trie' && !this.trieData) {
      this.trieData = await API.getDSATrie(3);
    } else if (tabName === 'tree' && !this.treeData) {
      this.treeData = await API.getDSATree();
    } else if (tabName === 'heap' && !this.heapData) {
      this.heapData = await API.getDSAHeap();
    }
    this.render();
  },

  renderActiveSubTab() {
    switch (this.activeSubTab) {
      case 'tree': return this.renderTreeView();
      case 'hash_table': return this.renderHashTableView();
      case 'trie': return this.renderTrieView();
      case 'queue': return this.renderQueueView();
      case 'heap': return this.renderHeapView();
      case 'graph': return this.renderGraphView();
      case 'sorting': return this.renderSortingView();
      case 'complexity': return this.renderComplexityView();
      default: return '';
    }
  },

  // 1. File Tree View
  renderTreeView() {
    const tree = this.treeData || { tree_hierarchy: State.fileTree, dfs_traversal: [], bfs_traversal: [] };
    const stats = this.overviewData?.tree_stats || { total_files: 0, total_folders: 0, total_size: 0, max_depth: 0 };

    return `
      <div class="grid-cards" style="margin-bottom: 20px;">
        <div class="glass-card stat-card">
          <div class="stat-icon purple">🌳</div>
          <div>
            <div class="stat-val">${stats.total_folders + stats.total_files}</div>
            <div class="stat-label">Total Tree Nodes</div>
          </div>
        </div>
        <div class="glass-card stat-card">
          <div class="stat-icon cyan">📏</div>
          <div>
            <div class="stat-val">${stats.max_depth}</div>
            <div class="stat-label">Max Tree Depth (Height)</div>
          </div>
        </div>
        <div class="glass-card stat-card">
          <div class="stat-icon emerald">💾</div>
          <div>
            <div class="stat-val" style="font-size: 20px;">${DashboardComponent.formatBytes(stats.total_size)}</div>
            <div class="stat-label">Subtree Aggregated Size</div>
          </div>
        </div>
      </div>

      <div class="grid-split">
        <!-- Interactive Hierarchy -->
        <div class="glass-card">
          <div class="card-title-bar">
            <h3 class="card-title"><span>📁</span> Hierarchical FileTree</h3>
            <span class="pill pill-new">O(k) Path Lookup</span>
          </div>
          <div style="max-height: 440px; overflow-y: auto; font-family: var(--font-mono); font-size: 13px;">
            ${this.renderTreeHierarchyHTML(tree.tree_hierarchy)}
          </div>
        </div>

        <!-- Traversals (DFS vs BFS) -->
        <div class="glass-card">
          <div class="card-title-bar">
            <h3 class="card-title"><span>🔄</span> Traversals (DFS & BFS)</h3>
          </div>
          <div style="margin-bottom: 18px;">
            <div style="font-size: 12px; font-weight: 700; color: var(--accent-purple); text-transform: uppercase; margin-bottom: 6px;">
              Depth-First Search (Pre-Order Traversal)
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: var(--radius-sm); font-family: var(--font-mono); font-size: 11px; max-height: 180px; overflow-y: auto;">
              ${(tree.dfs_traversal || []).map(n => `<div>${n.is_dir ? '📁' : '📄'} ${n.path || n.name}</div>`).join('')}
            </div>
          </div>

          <div>
            <div style="font-size: 12px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase; margin-bottom: 6px;">
              Breadth-First Search (Level-Order Traversal)
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: var(--radius-sm); font-family: var(--font-mono); font-size: 11px; max-height: 180px; overflow-y: auto;">
              ${(tree.bfs_traversal || []).map(n => `<div>[Level ${n.level}] ${n.is_dir ? '📁' : '📄'} ${n.name}</div>`).join('')}
            </div>
          </div>
        </div>
      </div>
    `;
  },

  renderTreeHierarchyHTML(node, depth = 0) {
    if (!node) return '<div>Empty tree</div>';
    const isDir = node.is_dir;
    const children = node.children || [];
    return `
      <div style="margin-left: ${depth * 16}px; margin-bottom: 4px;">
        <span style="color: ${isDir ? 'var(--accent-amber)' : 'var(--accent-cyan)'};">${isDir ? '📁' : '📄'}</span>
        <strong>${node.name}</strong>
        <span style="color: var(--text-muted); font-size: 11px;">(${DashboardComponent.formatBytes(node.size)})</span>
        ${children.map(c => this.renderTreeHierarchyHTML(c, depth + 1)).join('')}
      </div>
    `;
  },

  // 2. Hash Table View
  renderHashTableView() {
    const data = this.hashData || {
      id_index_stats: { capacity: 16, size: 0, load_factor: 0, total_collisions: 0 },
      id_index_buckets: []
    };
    const stats = data.id_index_stats;

    return `
      <div class="grid-cards" style="margin-bottom: 20px;">
        <div class="glass-card stat-card">
          <div class="stat-icon cyan">🗄</div>
          <div>
            <div class="stat-val">${stats.size}</div>
            <div class="stat-label">Total Key-Value Entries</div>
          </div>
        </div>
        <div class="glass-card stat-card">
          <div class="stat-icon purple">📦</div>
          <div>
            <div class="stat-val">${stats.capacity}</div>
            <div class="stat-label">Bucket Capacity (M)</div>
          </div>
        </div>
        <div class="glass-card stat-card">
          <div class="stat-icon amber">⚖</div>
          <div>
            <div class="stat-val">${stats.load_factor}</div>
            <div class="stat-label">Load Factor (λ = N/M)</div>
          </div>
        </div>
        <div class="glass-card stat-card">
          <div class="stat-icon rose">💥</div>
          <div>
            <div class="stat-val">${stats.total_collisions}</div>
            <div class="stat-label">Total Collisions Encountered</div>
          </div>
        </div>
      </div>

      <div class="glass-card">
        <div class="card-title-bar">
          <div>
            <h3 class="card-title"><span>🔍</span> Separate Chaining Bucket Inspector</h3>
            <p style="font-size: 12px; color: var(--text-muted);">
              Polynomial rolling hash indexes file_id to FileMetadata in O(1) average lookup time.
            </p>
          </div>
          <span class="pill pill-synced">Rehash Threshold: λ = 0.75</span>
        </div>

        <div class="hash-buckets-container">
          ${(data.id_index_buckets || []).map(b => `
            <div class="bucket-card">
              <div class="bucket-header">
                <span>BUCKET #${b.bucket_index}</span>
                <span class="pill ${b.chain_length > 1 ? 'pill-modified' : (b.chain_length === 1 ? 'pill-synced' : 'pill-priority-3')}">
                  ${b.chain_length} Node(s)
                </span>
              </div>
              <div class="bucket-chain">
                ${b.entries.map(e => `
                  <div class="chain-node">
                    <span style="color: var(--accent-cyan); font-weight: 700;">${e.key}</span>
                    <div style="color: var(--text-muted); font-size: 10px; margin-top: 2px;">➔ ${e.value_preview}</div>
                  </div>
                `).join('')}
                ${b.chain_length === 0 ? `
                  <div style="color: var(--text-muted); font-size: 11px; font-style: italic;">(empty bucket)</div>
                ` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  },

  // 3. Trie Prefix Search View
  renderTrieView() {
    const data = this.trieData || { stats: { total_words: 0, total_nodes: 1 }, visual_trie: {} };

    return `
      <div class="grid-cards" style="margin-bottom: 20px;">
        <div class="glass-card stat-card">
          <div class="stat-icon emerald">🔤</div>
          <div>
            <div class="stat-val">${data.stats.total_words}</div>
            <div class="stat-label">Constituent Filename Tokens</div>
          </div>
        </div>
        <div class="glass-card stat-card">
          <div class="stat-icon cyan">🌿</div>
          <div>
            <div class="stat-val">${data.stats.total_nodes}</div>
            <div class="stat-label">Total Trie Character Nodes</div>
          </div>
        </div>
        <div class="glass-card stat-card">
          <div class="stat-icon purple">⚡</div>
          <div>
            <div class="stat-val" style="font-size: 20px;">O(L)</div>
            <div class="stat-label">Prefix Evaluation Complexity</div>
          </div>
        </div>
      </div>

      <div class="glass-card">
        <div class="card-title-bar">
          <div>
            <h3 class="card-title"><span>🌲</span> Filename Trie Prefix Tree Inspector</h3>
            <p style="font-size: 12px; color: var(--text-muted);">
              Decomposes filename strings into prefix branches for instant search without scanning entire file lists.
            </p>
          </div>
        </div>

        <div style="background: rgba(10, 15, 28, 0.6); padding: 20px; border-radius: var(--radius-md); font-family: var(--font-mono); font-size: 13px; max-height: 480px; overflow-y: auto;">
          ${this.renderTrieNodeHTML(data.visual_trie)}
        </div>
      </div>
    `;
  },

  renderTrieNodeHTML(node, depth = 0) {
    if (!node) return '';
    const children = node.children || [];
    const isWord = node.is_word;
    return `
      <div style="margin-left: ${depth * 18}px; margin-bottom: 3px;">
        <span style="color: ${isWord ? 'var(--accent-emerald)' : 'var(--accent-cyan)'}; font-weight: 700;">
          [ '${node.char}' ]
        </span>
        ${isWord ? `<span class="pill pill-synced" style="font-size: 9px; padding: 1px 6px;">WORD (${node.matches_count} files)</span>` : ''}
        ${children.map(c => this.renderTrieNodeHTML(c, depth + 1)).join('')}
      </div>
    `;
  },

  // 4. FIFO Transfer Queue View
  renderQueueView() {
    const data = State.transfers || { fifo_queue: [] };
    const queue = data.fifo_queue || [];

    return `
      <div class="glass-card" style="margin-bottom: 24px;">
        <div class="card-title-bar">
          <div>
            <h3 class="card-title"><span>⏳</span> First-In First-Out (FIFO) Doubly-Linked Queue</h3>
            <p style="font-size: 12px; color: var(--text-muted);">
              Maintains strict arrival ordering (Enqueue O(1), Dequeue O(1), Cancel O(1)).
            </p>
          </div>
          <span class="pill pill-new">Current Size: ${queue.length}</span>
        </div>

        <div class="queue-visual-track">
          <div style="font-weight: 800; font-family: var(--font-mono); color: var(--accent-emerald);">FRONT ➔</div>
          ${queue.map(item => `
            <div class="queue-node-box">
              <span class="pill pill-priority-${item.priority}" style="margin-bottom: 6px;">${item.priority_name}</span>
              <div style="font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px;">
                ${item.file_name}
              </div>
              <div style="font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); margin-top: 4px;">
                ${DashboardComponent.formatBytes(item.size)}
              </div>
            </div>
            <div class="queue-arrow">➔</div>
          `).join('')}
          <div style="font-weight: 800; font-family: var(--font-mono); color: var(--accent-purple);">➔ REAR</div>
        </div>
      </div>
    `;
  },

  // 5. Priority Heap View
  renderHeapView() {
    const data = this.heapData || { heap_items: [], heap_tree: [] };
    const items = data.heap_items || [];
    const tree = data.heap_tree || [];

    return `
      <div class="grid-cards" style="margin-bottom: 20px;">
        <div class="glass-card stat-card">
          <div class="stat-icon rose">0</div>
          <div>
            <div class="stat-val">${items.filter(i => i.priority === 0).length}</div>
            <div class="stat-label">CRITICAL (Top Urgency)</div>
          </div>
        </div>
        <div class="glass-card stat-card">
          <div class="stat-icon amber">1</div>
          <div>
            <div class="stat-val">${items.filter(i => i.priority === 1).length}</div>
            <div class="stat-label">HIGH (Urgent Files)</div>
          </div>
        </div>
        <div class="glass-card stat-card">
          <div class="stat-icon cyan">2</div>
          <div>
            <div class="stat-val">${items.filter(i => i.priority === 2).length}</div>
            <div class="stat-label">NORMAL (Standard)</div>
          </div>
        </div>
        <div class="glass-card stat-card">
          <div class="stat-icon purple">3</div>
          <div>
            <div class="stat-val">${items.filter(i => i.priority === 3).length}</div>
            <div class="stat-label">LOW (Background Sync)</div>
          </div>
        </div>
      </div>

      <div class="glass-card">
        <div class="card-title-bar">
          <div>
            <h3 class="card-title"><span>⛰</span> Binary Min-Heap Array & Tree Representation</h3>
            <p style="font-size: 12px; color: var(--text-muted);">
              Min-Heap property: Parent at (i-1)//2 has lower or equal priority value than Children at 2i+1 and 2i+2.
            </p>
          </div>
        </div>

        <div style="margin-bottom: 18px;">
          <div style="font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">
            Raw Heap Array Representation
          </div>
          <div style="display: flex; gap: 8px; overflow-x: auto; padding-bottom: 8px;">
            ${tree.map(node => `
              <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border-medium); border-radius: var(--radius-sm); padding: 8px 12px; min-width: 90px; text-align: center;">
                <div style="font-size: 10px; color: var(--text-muted); font-family: var(--font-mono);">[Index ${node.index}]</div>
                <div class="pill pill-priority-${node.priority}" style="margin: 4px 0; font-size: 9px;">${node.priority_name}</div>
                <div style="font-size: 11px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 90px;">
                  ${node.title}
                </div>
              </div>
            `).join('')}
            ${tree.length === 0 ? `<div style="color: var(--text-muted); font-size: 12px;">Heap is empty</div>` : ''}
          </div>
        </div>

        <div class="heap-tree-canvas" id="heap-canvas-box">
          <canvas id="heap-visual-canvas" width="900" height="380" style="width: 100%; height: 100%;"></canvas>
        </div>
      </div>
    `;
  },

  drawHeapCanvas() {
    const canvas = document.getElementById('heap-visual-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = canvas.parentElement.clientHeight;

    ctx.clearRect(0, 0, width, height);

    const tree = this.heapData?.heap_tree || [];
    if (tree.length === 0) {
      ctx.fillStyle = '#64748b';
      ctx.font = '14px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No elements in the priority heap', width / 2, height / 2);
      return;
    }

    // Compute binary tree coordinates
    const levels = Math.floor(Math.log2(tree.length)) + 1;
    const ySpacing = height / (levels + 1);

    const coords = [];
    tree.forEach((node, i) => {
      const level = Math.floor(Math.log2(i + 1));
      const posInLevel = i - (Math.pow(2, level) - 1);
      const totalInLevel = Math.pow(2, level);
      const xSpacing = width / (totalInLevel + 1);

      const x = (posInLevel + 1) * xSpacing;
      const y = (level + 1) * ySpacing;
      coords.push({ x, y, node });
    });

    // Draw tree branches (Parent -> Children)
    coords.forEach((c, i) => {
      const leftIdx = 2 * i + 1;
      const rightIdx = 2 * i + 2;

      ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
      ctx.lineWidth = 1.5;

      if (leftIdx < coords.length) {
        ctx.beginPath();
        ctx.moveTo(c.x, c.y);
        ctx.lineTo(coords[leftIdx].x, coords[leftIdx].y);
        ctx.stroke();
      }
      if (rightIdx < coords.length) {
        ctx.beginPath();
        ctx.moveTo(c.x, c.y);
        ctx.lineTo(coords[rightIdx].x, coords[rightIdx].y);
        ctx.stroke();
      }
    });

    // Draw Heap Tree Nodes
    coords.forEach(c => {
      const p = c.node.priority;
      const color = p === 0 ? '#f43f5e' : (p === 1 ? '#f59e0b' : (p === 2 ? '#00f0ff' : '#94a3b8'));

      ctx.beginPath();
      ctx.arc(c.x, c.y, 20, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.shadowColor = color;
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0;

      ctx.fillStyle = '#04101e';
      ctx.font = 'bold 12px JetBrains Mono, monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(p.toString(), c.x, c.y);

      ctx.fillStyle = '#fff';
      ctx.font = '10px Outfit, sans-serif';
      ctx.fillText(c.node.title.substring(0, 12), c.x, c.y + 28);
    });
  },

  // 6. Network Graph View
  renderGraphView() {
    return `
      <div class="glass-card">
        <div class="card-title-bar">
          <h3 class="card-title"><span>🕸</span> Network Graph Modeling (V, E)</h3>
          <button class="btn btn-primary btn-sm" onclick="App.navigate('devices')">
            Open Interactive Topology Canvas ➔
          </button>
        </div>
        <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.6;">
          Devices on the router LAN are represented as an Adjacency List NetworkGraph.
          Edges contain connection metrics (latency and bandwidth).
          The graph subsystem supports:
        </p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-top: 16px;">
          <div style="background: rgba(15, 23, 42, 0.7); padding: 16px; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
            <h4 style="color: var(--accent-cyan); margin-bottom: 6px;">Breadth-First Search (BFS)</h4>
            <div style="font-size: 12px; color: var(--text-muted); font-family: var(--font-mono);">Time: O(V + E) | Space: O(V)</div>
            <p style="font-size: 12px; color: var(--text-secondary); margin-top: 6px;">
              Used for network diameter inspection and computing minimum hop distance to peers.
            </p>
          </div>
          <div style="background: rgba(15, 23, 42, 0.7); padding: 16px; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
            <h4 style="color: var(--accent-purple); margin-bottom: 6px;">Depth-First Search (DFS)</h4>
            <div style="font-size: 12px; color: var(--text-muted); font-family: var(--font-mono);">Time: O(V + E) | Space: O(V)</div>
            <p style="font-size: 12px; color: var(--text-secondary); margin-top: 6px;">
              Used for exhaustive device discovery traversal and connected-component verification.
            </p>
          </div>
          <div style="background: rgba(15, 23, 42, 0.7); padding: 16px; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
            <h4 style="color: var(--accent-emerald); margin-bottom: 6px;">Dijkstra's Shortest Route</h4>
            <div style="font-size: 12px; color: var(--text-muted); font-family: var(--font-mono);">Time: O((V+E) log V)</div>
            <p style="font-size: 12px; color: var(--text-secondary); margin-top: 6px;">
              Computes latency-weighted shortest communication routes across multi-peer topologies.
            </p>
          </div>
        </div>
      </div>
    `;
  },

  // 7. Sorting Benchmark View
  renderSortingView() {
    const data = this.sortBenchmarkData;

    return `
      <div class="glass-card" style="margin-bottom: 24px;">
        <div class="card-title-bar">
          <div>
            <h3 class="card-title"><span>⚡</span> Live Sorting Benchmark: Merge Sort vs Quick Sort</h3>
            <p style="font-size: 12px; color: var(--text-muted);">
              Runs custom implementations on current file datasets to observe comparisons and execution timing.
            </p>
          </div>
          <div style="display: flex; gap: 10px;">
            <select class="btn btn-secondary btn-sm" id="benchmark-sort-key" onchange="DSAVisualizerComponent.runSortBenchmark(this.value)">
              <option value="size">Sort by File Size</option>
              <option value="name">Sort by File Name</option>
              <option value="modified_time">Sort by Date Modified</option>
            </select>
            <button class="btn btn-primary btn-sm" onclick="DSAVisualizerComponent.runSortBenchmark()">
              Run Live Benchmark
            </button>
          </div>
        </div>

        ${data ? `
          <div class="grid-split">
            <!-- Merge Sort Card -->
            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(0, 240, 255, 0.3); border-radius: var(--radius-md); padding: 20px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h4 style="color: var(--accent-cyan); font-size: 18px;">Merge Sort</h4>
                <span class="pill pill-synced">Guaranteed O(N log N)</span>
              </div>
              <div style="display: flex; flex-direction: column; gap: 8px; font-size: 13px;">
                <div>Comparisons: <strong style="font-family: var(--font-mono); color: #fff;">${data.merge_sort.comparisons}</strong></div>
                <div>Elapsed Time: <strong style="font-family: var(--font-mono); color: var(--accent-cyan);">${data.merge_sort.elapsed_ms} ms</strong></div>
                <div>Stability: <strong style="color: var(--accent-emerald);">Stable (Preserves relative order)</strong></div>
                <div>Auxiliary Space: <code>O(N)</code></div>
              </div>
            </div>

            <!-- Quick Sort Card -->
            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(157, 78, 221, 0.3); border-radius: var(--radius-md); padding: 20px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h4 style="color: var(--accent-purple); font-size: 18px;">Quick Sort</h4>
                <span class="pill pill-modified">In-Place O(N log N) avg</span>
              </div>
              <div style="display: flex; flex-direction: column; gap: 8px; font-size: 13px;">
                <div>Comparisons: <strong style="font-family: var(--font-mono); color: #fff;">${data.quick_sort.comparisons}</strong></div>
                <div>Elapsed Time: <strong style="font-family: var(--font-mono); color: var(--accent-purple);">${data.quick_sort.elapsed_ms} ms</strong></div>
                <div>Stability: <strong style="color: var(--accent-amber);">Unstable</strong></div>
                <div>Auxiliary Space: <code>O(log N) recursion stack</code></div>
              </div>
            </div>
          </div>
        ` : `
          <div style="text-align: center; color: var(--text-muted); padding: 36px 0;">
            Click <strong>"Run Live Benchmark"</strong> to evaluate Merge Sort and Quick Sort on the active file catalog.
          </div>
        `}
      </div>
    `;
  },

  async runSortBenchmark(by = 'size') {
    App.showToast('Running sorting benchmark...', 'info');
    try {
      this.sortBenchmarkData = await API.benchmarkSort(by);
      this.render();
    } catch (err) {
      App.showToast(`Benchmark error: ${err.message}`, 'error');
    }
  },

  // 8. Algorithm Complexity Analysis Table
  renderComplexityView() {
    const list = this.overviewData?.complexities || [];

    return `
      <div class="glass-card" style="padding: 0;">
        <div class="card-title-bar" style="padding: 20px 24px 0;">
          <div>
            <h3 class="card-title"><span>📊</span> Comprehensive Algorithm Complexity Matrix</h3>
            <p style="font-size: 12px; color: var(--text-muted);">
              Formal asymptotic time and space bounds for all data structures utilized in the project.
            </p>
          </div>
        </div>

        <div style="padding: 16px 24px;">
          ${list.map(c => `
            <div style="margin-bottom: 24px; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 18px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h4 style="color: var(--accent-cyan); font-size: 16px; font-weight: 700;">${c.structure}</h4>
                <span class="pill pill-priority-2">${c.purpose}</span>
              </div>
              <p style="font-size: 12px; color: var(--text-secondary); margin-bottom: 12px;">${c.description}</p>

              <div class="table-wrapper">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Operation</th>
                      <th>Time (Average)</th>
                      <th>Time (Worst Case)</th>
                      <th>Space Complexity</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${c.operations.map(op => `
                      <tr>
                        <td><strong>${op.operation}</strong></td>
                        <td><code style="color: var(--accent-emerald); font-weight: 700;">${op.time_avg}</code></td>
                        <td><code style="color: var(--accent-amber);">${op.time_worst}</code></td>
                        <td><code style="color: var(--accent-cyan);">${op.space}</code></td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }
};
