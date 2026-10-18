// frontend/js/components/devices.js - LAN Devices Registry & Interactive Graph Topology

const DevicesComponent = {
  graphData: null,
  activeHighlightNodes: new Set(),
  activeHighlightEdges: new Set(),

  async render() {
    const el = document.getElementById('view-devices');
    if (!el) return;

    const host = State.hostInfo;
    const devices = State.devices || [];

    // Fetch graph data
    try {
      this.graphData = await API.getNetworkGraph();
    } catch (_) {}

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h2 class="page-title">LAN Devices & Network Topology</h2>
          <p class="page-subtitle">Automatic UDP broadcast discovery with Adjacency List NetworkGraph modeling</p>
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
          <button class="btn btn-secondary btn-sm" onclick="App.refreshDevices()">
            <span>🔄</span> Refresh Devices
          </button>
          <button class="btn btn-primary btn-sm" onclick="App.navigate('ip-transfer')">
            <span>🌐</span> Direct IP Transfer
          </button>
          <button class="btn btn-secondary btn-sm" onclick="App.openPairModal()">
            <span>➕</span> Connect Manually
          </button>
        </div>
      </div>

      <!-- Quick Pairing Code Display Card -->
      <div class="glass-card" style="margin-bottom: 24px; background: linear-gradient(135deg, rgba(157, 78, 221, 0.1), rgba(0, 240, 255, 0.05)); border-color: rgba(157, 78, 221, 0.3);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
          <div>
            <div style="font-size: 13px; font-weight: 600; color: var(--accent-purple); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
              Host Laptop Pairing Code
            </div>
            <div style="font-size: 14px; color: var(--text-secondary);">
              Other laptops on this router must enter this 6-digit code to pair and exchange files.
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 14px;">
            <div style="background: rgba(15, 23, 42, 0.8); border: 2px solid var(--accent-purple); padding: 8px 24px; border-radius: var(--radius-md); font-family: var(--font-mono); font-size: 26px; font-weight: 800; letter-spacing: 0.2em; color: #fff; box-shadow: 0 0 20px var(--accent-purple-glow);">
              ${host.pairing_code}
            </div>
            <button class="btn btn-secondary btn-sm" onclick="App.resetPairingCode()">
              Reset Code
            </button>
          </div>
        </div>
      </div>

      <!-- Devices Table -->
      <div class="glass-card" style="margin-bottom: 24px; padding: 0;">
        <div class="card-title-bar" style="padding: 16px 20px 0;">
          <h3 class="card-title"><span>💻</span> Discovered LAN Device Registry</h3>
          <span style="font-size: 12px; color: var(--text-muted);">${devices.length + 1} device(s) registered</span>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Device ID</th>
                <th>Device Name</th>
                <th>IP Address</th>
                <th>Port</th>
                <th>Status</th>
                <th>Trust / Role</th>
                <th>Last Seen</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr style="background: rgba(0, 240, 255, 0.05);">
                <td><code>${host.device_id}</code></td>
                <td><strong>${host.device_name} (This Host)</strong></td>
                <td><code style="color: var(--accent-cyan); font-weight: 700;">${host.ip_address}</code></td>
                <td>${host.port}</td>
                <td><span class="pill pill-synced">ONLINE (HOST)</span></td>
                <td><span class="pill pill-synced">HOST (FULL ACCESS)</span></td>
                <td>Just now</td>
                <td><span style="color: var(--text-muted); font-size: 11px;">Current Node</span></td>
              </tr>
              ${devices.map(d => `
                <tr>
                  <td><code>${d.device_id}</code></td>
                  <td><strong>${d.device_name}</strong></td>
                  <td><code>${d.ip_address}</code></td>
                  <td>${d.port}</td>
                  <td>
                    <span class="pill ${d.status === 'online' ? 'pill-synced' : 'pill-priority-3'}">
                      ${d.status.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <span class="pill ${d.trusted ? 'pill-synced' : 'pill-modified'}">
                      ${d.trusted ? d.role || 'PAIRED' : 'UNPAIRED'}
                    </span>
                  </td>
                  <td style="font-size: 12px; color: var(--text-muted);">
                    ${new Date((d.last_seen || 0) * 1000).toLocaleTimeString()}
                  </td>
                  <td>
                    <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                      <button class="btn btn-secondary btn-sm" onclick="DevicesComponent.testPeerPing('${d.ip_address}', ${d.port})">
                        Ping
                      </button>
                      <button class="btn btn-primary btn-sm" onclick="IPTransferComponent.selectDeviceIP('${d.ip_address}', ${d.port})">
                        ⚡ Send File
                      </button>
                      <button class="btn btn-secondary btn-sm" onclick="App.syncWithPeer('${d.ip_address}', ${d.port})">
                        Sync
                      </button>
                    </div>
                  </td>
                </tr>
              `).join('')}
              ${devices.length === 0 ? `
                <tr>
                  <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">
                    No peers detected yet. Ensure other laptops are connected to the router or toggle Demo Mode.
                  </td>
                </tr>
              ` : ''}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Network Topology Graph & Graph Algorithms -->
      <div class="glass-card">
        <div class="card-title-bar">
          <div>
            <h3 class="card-title"><span>🕸</span> Adjacency List Network Topology Graph</h3>
            <p style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
              Visualizes connected LAN devices as vertices (V) and connection latencies as weighted edges (E).
            </p>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary btn-sm" onclick="DevicesComponent.runBFS()">
              <span>⚡</span> Run BFS Hop Search
            </button>
            <button class="btn btn-secondary btn-sm" onclick="DevicesComponent.runDFS()">
              <span>🔍</span> Run DFS Traversal
            </button>
            <button class="btn btn-primary btn-sm" onclick="DevicesComponent.runDijkstra()">
              <span>🛣</span> Dijkstra Shortest Route
            </button>
          </div>
        </div>

        <div class="graph-canvas-container" id="network-topology-container">
          <canvas id="network-graph-canvas" width="900" height="420" style="width: 100%; height: 100%;"></canvas>
        </div>

        <div id="graph-algorithm-output" style="margin-top: 14px; font-family: var(--font-mono); font-size: 13px; color: var(--accent-cyan); min-height: 20px;"></div>
      </div>
    `;

    setTimeout(() => this.drawCanvasGraph(), 50);
  },

  drawCanvasGraph() {
    const canvas = document.getElementById('network-graph-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = canvas.parentElement.clientHeight;

    ctx.clearRect(0, 0, width, height);

    if (!this.graphData || !this.graphData.nodes || this.graphData.nodes.length === 0) {
      ctx.fillStyle = '#64748b';
      ctx.font = '14px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No topology nodes to display', width / 2, height / 2);
      return;
    }

    const nodes = this.graphData.nodes;
    const edges = this.graphData.edges || [];

    // Arrange nodes in a circular or force-directed layout
    const positions = {};
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.35;

    nodes.forEach((node, i) => {
      const angle = (i / nodes.length) * 2 * Math.PI - Math.PI / 2;
      positions[node.device_id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        node: node
      };
    });

    // Draw Edges
    edges.forEach(edge => {
      const p1 = positions[edge.source];
      const p2 = positions[edge.target];
      if (p1 && p2) {
        const edgeKey = [edge.source, edge.target].sort().join('-');
        const isHighlighted = this.activeHighlightEdges.has(edgeKey);

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.strokeStyle = isHighlighted ? '#00f0ff' : 'rgba(255, 255, 255, 0.15)';
        ctx.lineWidth = isHighlighted ? 3 : 1.5;
        if (isHighlighted) {
          ctx.shadowColor = '#00f0ff';
          ctx.shadowBlur = 12;
        } else {
          ctx.shadowBlur = 0;
        }
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Draw latency pill
        const midX = (p1.x + p2.x) / 2;
        const midY = (p1.y + p2.y) / 2;
        ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
        ctx.fillRect(midX - 22, midY - 10, 44, 20);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.strokeRect(midX - 22, midY - 10, 44, 20);
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px JetBrains Mono, monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${edge.latency_ms}ms`, midX, midY);
      }
    });

    // Draw Nodes
    nodes.forEach(node => {
      const pos = positions[node.device_id];
      const isHighlighted = this.activeHighlightNodes.has(node.device_id);
      const isSelf = node.is_self;

      // Glow effect
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 24, 0, 2 * Math.PI);
      if (isHighlighted) {
        ctx.fillStyle = 'rgba(0, 240, 255, 0.3)';
        ctx.shadowColor = '#00f0ff';
        ctx.shadowBlur = 20;
      } else if (isSelf) {
        ctx.fillStyle = 'rgba(16, 185, 129, 0.2)';
        ctx.shadowColor = '#10b981';
        ctx.shadowBlur = 12;
      } else {
        ctx.fillStyle = 'rgba(157, 78, 221, 0.2)';
        ctx.shadowBlur = 0;
      }
      ctx.fill();
      ctx.shadowBlur = 0;

      // Node circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 18, 0, 2 * Math.PI);
      ctx.fillStyle = isSelf ? '#10b981' : (isHighlighted ? '#00f0ff' : '#9d4edd');
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#fff';
      ctx.stroke();

      // Node Icon / Letter
      ctx.fillStyle = '#04101e';
      ctx.font = 'bold 12px Outfit, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.device_name.charAt(0).toUpperCase(), pos.x, pos.y);

      // Node Labels
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 12px Outfit, sans-serif';
      ctx.fillText(node.device_name, pos.x, pos.y + 34);

      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px JetBrains Mono, monospace';
      ctx.fillText(node.ip_address, pos.x, pos.y + 48);
    });
  },

  async runBFS() {
    const output = document.getElementById('graph-algorithm-output');
    try {
      const res = await API.getGraphBFS();
      this.activeHighlightNodes.clear();
      this.activeHighlightEdges.clear();

      output.innerHTML = `<strong>BFS Traversal Result:</strong> ` +
        res.traversal.map(t => `${t.device_name} (Hop: ${t.hops})`).join(' ➜ ');

      // Step-by-step highlight animation
      res.traversal.forEach((t, i) => {
        setTimeout(() => {
          this.activeHighlightNodes.add(t.device_id);
          this.drawCanvasGraph();
        }, i * 350);
      });
    } catch (err) {
      output.innerText = `BFS Error: ${err.message}`;
    }
  },

  async runDFS() {
    const output = document.getElementById('graph-algorithm-output');
    try {
      const res = await API.getGraphDFS();
      this.activeHighlightNodes.clear();
      this.activeHighlightEdges.clear();

      output.innerHTML = `<strong>DFS Traversal Result:</strong> ` +
        res.traversal.map(t => `${t.device_name} (Depth: ${t.depth})`).join(' ➜ ');

      res.traversal.forEach((t, i) => {
        setTimeout(() => {
          this.activeHighlightNodes.add(t.device_id);
          this.drawCanvasGraph();
        }, i * 350);
      });
    } catch (err) {
      output.innerText = `DFS Error: ${err.message}`;
    }
  },

  async runDijkstra() {
    const output = document.getElementById('graph-algorithm-output');
    if (!this.graphData || !this.graphData.nodes || this.graphData.nodes.length < 2) {
      output.innerText = 'Dijkstra requires at least 2 nodes.';
      return;
    }

    const start = this.graphData.nodes[0].device_id;
    const end = this.graphData.nodes[this.graphData.nodes.length - 1].device_id;

    try {
      const res = await API.getShortestPath(start, end);
      this.activeHighlightNodes.clear();
      this.activeHighlightEdges.clear();

      res.path_ids.forEach(id => this.activeHighlightNodes.add(id));
      for (let i = 0; i < res.path_ids.length - 1; i++) {
        const edgeKey = [res.path_ids[i], res.path_ids[i + 1]].sort().join('-');
        this.activeHighlightEdges.add(edgeKey);
      }

      this.drawCanvasGraph();
      output.innerHTML = `<strong>Dijkstra Shortest Path:</strong> ${res.path_names.join(' ➔ ')} | Total Latency: <strong>${res.total_latency_ms} ms</strong> (${res.hop_count} hops)`;
    } catch (err) {
      output.innerText = `Dijkstra Error: ${err.message}`;
    }
  },

  async testPeerPing(ip, port) {
    App.showToast(`Pinging ${ip}:${port}...`, 'info');
    try {
      const res = await API.manualConnect(ip, port);
      App.showToast(`✓ Ping successful! Discovered ${res.peer.device_name}`, 'success');
      App.refreshDevices();
    } catch (err) {
      App.showToast(`Ping failed: ${err.message}`, 'error');
    }
  }
};
