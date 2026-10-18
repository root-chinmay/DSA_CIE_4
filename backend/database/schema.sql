-- SQLite Database Schema for Offline LAN File Sharing & Synchronization

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE NOT NULL,
    device_name TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    port INTEGER DEFAULT 8000,
    status TEXT DEFAULT 'online', -- 'online', 'offline', 'unpaired'
    last_seen REAL NOT NULL,
    trusted INTEGER DEFAULT 0,    -- 0 = unverified, 1 = paired/trusted
    role TEXT DEFAULT 'READ_ONLY', -- 'READ_ONLY', 'DOWNLOADER', 'CONTRIBUTOR', 'FULL_ACCESS'
    pairing_code TEXT,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS shared_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_name TEXT NOT NULL,
    folder_path TEXT UNIQUE NOT NULL,
    enabled INTEGER DEFAULT 1,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT UNIQUE NOT NULL,
    folder_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    size INTEGER DEFAULT 0,
    hash TEXT,
    modified_time REAL NOT NULL,
    file_type TEXT,
    FOREIGN KEY(folder_id) REFERENCES shared_folders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_id TEXT UNIQUE NOT NULL,
    file_id TEXT,
    file_name TEXT NOT NULL,
    source_device TEXT NOT NULL,
    destination_device TEXT NOT NULL,
    direction TEXT NOT NULL, -- 'UPLOAD' or 'DOWNLOAD'
    size INTEGER DEFAULT 0,
    transferred_bytes INTEGER DEFAULT 0,
    status TEXT DEFAULT 'WAITING', -- 'WAITING', 'TRANSFERRING', 'COMPLETED', 'FAILED', 'CANCELLED'
    priority INTEGER DEFAULT 2,     -- 0=Critical, 1=High, 2=Normal, 3=Low
    started_at REAL,
    completed_at REAL,
    speed REAL DEFAULT 0.0,
    hash_verified INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS sync_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    local_hash TEXT,
    remote_hash TEXT,
    local_modified REAL,
    remote_modified REAL,
    status TEXT DEFAULT 'PENDING', -- 'PENDING', 'RESOLVED'
    resolution TEXT,              -- 'KEEP_LOCAL', 'KEEP_REMOTE', 'KEEP_BOTH'
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    device TEXT,
    operation TEXT NOT NULL,
    file_name TEXT,
    status TEXT NOT NULL,
    message TEXT
);

CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash);
CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder_id);
CREATE INDEX IF NOT EXISTS idx_transfers_status ON transfers(status);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
