import { useState, useEffect, useRef } from 'react';
import { filesAPI, errMsg } from '../api/client';

const EXT_ICONS = {
  pdf: '📄', docx: '📝', xlsx: '📊', txt: '📃',
  png: '🖼️', jpg: '🖼️', jpeg: '🖼️', gif: '🖼️',
  zip: '🗜️',
};

function fileIcon(name) {
  const ext = name?.split('.').pop()?.toLowerCase();
  return EXT_ICONS[ext] || '📎';
}

function fmtSize(bytes) {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function fmtDate(ts) {
  if (!ts) return '';
  return new Date(ts).toLocaleDateString();
}

export default function FileManager({ roomId, userId, userRole }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const loadFiles = () => {
    filesAPI.list(roomId)
      .then(data => setFiles(data.items || []))
      .catch(e => setError(errMsg(e)));
  };

  useEffect(() => { if (roomId) loadFiles(); }, [roomId]);

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setError('');
    setSuccess('');
    try {
      await filesAPI.upload(roomId, file);
      setSuccess('✅ File uploaded!');
      loadFiles();
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const handleDownload = async (file) => {
    try {
      const res = await filesAPI.download(roomId, file.id);
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.file_name;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(errMsg(e));
    }
  };

  const handleDelete = async (fileId) => {
    if (!window.confirm('Delete this file?')) return;
    try {
      await filesAPI.delete(roomId, fileId);
      setFiles(prev => prev.filter(f => f.id !== fileId));
    } catch (e) {
      setError(errMsg(e));
    }
  };

  const canDelete = (file) => userRole === 'creator' || userRole === 'admin' || file.uploaded_by === userId;

  return (
    <div>
      {/* Upload zone */}
      <div
        className={`upload-zone${dragging ? ' drag-over' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <div style={{ fontSize: '2rem' }}>📁</div>
        <p>{uploading ? 'Uploading…' : 'Click or drag a file here to upload'}</p>
        <p style={{ fontSize: '0.76rem', marginTop: 4 }}>PDF, DOCX, XLSX, TXT, PNG, JPG, GIF, ZIP (max 50 MB)</p>
        <input
          ref={inputRef}
          type="file"
          style={{ display: 'none' }}
          onChange={e => handleUpload(e.target.files[0])}
          accept=".pdf,.docx,.xlsx,.txt,.png,.jpg,.jpeg,.gif,.zip"
        />
      </div>

      {error && <div className="alert alert-error mt-1">⚠️ {error}</div>}
      {success && <div className="alert alert-success mt-1">{success}</div>}

      {/* File list */}
      {files.length > 0 && (
        <div className="file-list">
          <div className="section-title mt-2">📂 Room Files</div>
          {files.map(file => (
            <div key={file.id} className="file-row">
              <div className="file-icon">{fileIcon(file.file_name)}</div>
              <div className="file-info">
                <div className="file-name">{file.file_name}</div>
                <div className="file-meta">
                  {fmtSize(file.file_size)} · Uploaded {fmtDate(file.upload_time)}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button className="btn btn-secondary btn-sm" onClick={() => handleDownload(file)}>
                  ⬇️ Download
                </button>
                {canDelete(file) && (
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(file.id)}>
                    🗑️
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {files.length === 0 && !uploading && (
        <div className="empty-state mt-2">
          <div className="empty-icon">📭</div>
          <p>No files shared yet.</p>
        </div>
      )}
    </div>
  );
}
