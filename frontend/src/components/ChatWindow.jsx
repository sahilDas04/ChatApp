import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { messagesAPI, filesAPI, errMsg } from '../api/client';
import useWebSocket from '../hooks/useWebSocket';

const API_BASE = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://localhost:8000';

function formatTime(ts) {
  if (!ts) return '';
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function getAvatarSrc(url) {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `${API_BASE}${url}`;
}

/** Small avatar icon — shows image if available, falls back to initial letter */
function MsgAvatar({ sender }) {
  const src = getAvatarSrc(sender?.avatar_url);
  const initial = (sender?.username?.[0] || '?').toUpperCase();
  if (src) {
    return (
      <img
        src={src}
        alt={sender?.username}
        className="msg-avatar"
        onError={e => {
          e.target.style.display = 'none';
          e.target.nextSibling?.style && (e.target.nextSibling.style.display = 'flex');
        }}
      />
    );
  }
  return <div className="msg-avatar-placeholder" title={sender?.username}>{initial}</div>;
}

/**
 * Messages can be plain text OR an attachment marker:
 *   __attachment__:{"id":1,"name":"photo.png","content_type":"image/png","file_id":5}
 */
function parseContent(content) {
  if (content?.startsWith('__attachment__:')) {
    try {
      return { type: 'attachment', data: JSON.parse(content.slice(15)) };
    } catch { /* fallback to text */ }
  }
  return { type: 'text', data: content };
}

const IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']);

function AttachmentBubble({ data, roomId }) {
  const isImage = IMAGE_TYPES.has(data.content_type);

  const handleDownload = async () => {
    try {
      const res = await filesAPI.download(roomId, data.file_id);
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url; a.download = data.name; a.click();
      URL.revokeObjectURL(url);
    } catch { /* ignore */ }
  };

  if (isImage) {
    const imgSrc = data.url ? `${API_BASE}${data.url}` : null;
    return (
      <div style={{ cursor: 'pointer' }} onClick={handleDownload} title="Click to download">
        {imgSrc ? (
          <img
            src={imgSrc}
            alt={data.name}
            style={{ maxWidth: 220, maxHeight: 180, borderRadius: 8, display: 'block', objectFit: 'cover' }}
            onError={e => { e.target.style.display = 'none'; }}
          />
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '1.4rem' }}>🖼️</span>
            <span style={{ fontSize: '0.88rem' }}>{data.name}</span>
          </div>
        )}
        <div style={{ fontSize: '0.7rem', marginTop: 4, opacity: 0.7 }}>🖼️ {data.name} · click to download</div>
      </div>
    );
  }

  const icons = {
    'application/pdf': '📄',
    'application/zip': '🗜️',
    'text/plain': '📃',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '📝',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '📊',
  };
  const icon = icons[data.content_type] || '📎';

  return (
    <button
      onClick={handleDownload}
      style={{
        display: 'flex', alignItems: 'center', gap: 8,
        background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)',
        borderRadius: 8, padding: '8px 12px', cursor: 'pointer', color: 'inherit', maxWidth: 220,
      }}
    >
      <span style={{ fontSize: '1.4rem' }}>{icon}</span>
      <div style={{ textAlign: 'left' }}>
        <div style={{ fontSize: '0.85rem', fontWeight: 500 }}>{data.name}</div>
        <div style={{ fontSize: '0.7rem', opacity: 0.7 }}>Click to download</div>
      </div>
    </button>
  );
}

export default function ChatWindow({ roomId, userRole }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [typingUsers, setTypingUsers] = useState([]);
  const bottomRef = useRef(null);
  const fileInputRef = useRef(null);
  const typingTimer = useRef(null);

  // Load history
  useEffect(() => {
    if (!roomId) return;
    messagesAPI.list(roomId, { limit: 50 })
      .then(data => setMessages(data.items || []))
      .catch(e => setError(errMsg(e)));
  }, [roomId]);

  // Scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const onWsMessage = useCallback((data) => {
    if (data.type === 'message') {
      setMessages(prev => {
        if (prev.some(m => m.id === data.data.id)) return prev;
        return [...prev, data.data];
      });
    } else if (data.type === 'message_deleted') {
      const deletedId = data.data.message_id;
      setMessages(prev => prev.filter(m => m.id !== deletedId));
    } else if (data.type === 'typing') {
      const { username, is_typing } = data.data;
      setTypingUsers(prev =>
        is_typing ? [...new Set([...prev, username])] : prev.filter(u => u !== username)
      );
    }
  }, []);

  const { sendTyping } = useWebSocket(roomId, onWsMessage);

  const handleInputChange = (e) => {
    setInput(e.target.value);
    sendTyping(true);
    clearTimeout(typingTimer.current);
    typingTimer.current = setTimeout(() => sendTyping(false), 2000);
  };

  const handleSend = async (e) => {
    e.preventDefault();
    const content = input.trim();
    if (!content || sending) return;
    setSending(true);
    setError('');
    try {
      const msg = await messagesAPI.send(roomId, content);
      setMessages(prev => prev.some(m => m.id === msg.id) ? prev : [...prev, msg]);
      setInput('');
      sendTyping(false);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setSending(false);
    }
  };

  const handleDelete = async (msgId) => {
    // Optimistic removal
    setMessages(prev => prev.filter(m => m.id !== msgId));
    try {
      await messagesAPI.delete(roomId, msgId);
      // WS broadcast will also remove it for other clients
    } catch (e) {
      setError(errMsg(e));
      // Re-fetch to restore if delete failed
      messagesAPI.list(roomId, { limit: 50 }).then(data => setMessages(data.items || []));
    }
  };

  const sendFile = async (file) => {
    setUploading(true);
    setError('');
    try {
      const fileRecord = await filesAPI.upload(roomId, file);
      const isImage = IMAGE_TYPES.has(file.type);
      const attachmentData = {
        file_id: fileRecord.id,
        name: fileRecord.file_name,
        content_type: fileRecord.content_type || file.type,
        url: isImage ? `/uploads/${fileRecord.room_id}/${fileRecord.file_name}` : null,
      };
      const content = `__attachment__:${JSON.stringify(attachmentData)}`;
      const msg = await messagesAPI.send(roomId, content);
      setMessages(prev => prev.some(m => m.id === msg.id) ? prev : [...prev, msg]);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    e.target.value = '';
    await sendFile(file);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) await sendFile(file);
  };

  const canDelete = (msg) => {
    return msg.sender_id === user?.id || ['creator', 'admin'].includes(userRole);
  };

  return (
    <div className="chat-window" onDragOver={e => e.preventDefault()} onDrop={handleDrop}>
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">💬</div>
            <p>No messages yet. Say hello!</p>
          </div>
        ) : messages.map((msg, i) => {
          const mine = msg.sender_id === user?.id;
          const parsed = parseContent(msg.content);
          const sender = msg.sender || { username: msg.sender_username, avatar_url: null };

          return (
            <div key={msg.id ?? i} className={`msg-row ${mine ? 'mine' : 'theirs'}`}>
              {/* Avatar — only on "theirs" side */}
              {!mine && <MsgAvatar sender={sender} />}

              {/* Bubble column */}
              <div className={`msg-bubble ${mine ? 'mine' : 'theirs'}`}>
                {!mine && (
                  <div className="msg-sender">{sender.username}</div>
                )}
                <div
                  className="msg-content"
                  style={parsed.type === 'attachment' ? { padding: '8px 10px', minWidth: 120 } : {}}
                >
                  {parsed.type === 'attachment'
                    ? <AttachmentBubble data={parsed.data} roomId={roomId} />
                    : parsed.data
                  }
                </div>
                <div className="msg-time">{formatTime(msg.timestamp)}</div>
              </div>

              {/* Avatar — only on "mine" side */}
              {mine && <MsgAvatar sender={user ? { username: user.username, avatar_url: user.avatar_url } : sender} />}

              {/* Delete button — shown on hover */}
              {canDelete(msg) && (
                <button
                  className="msg-delete-btn"
                  onClick={() => handleDelete(msg.id)}
                  title="Delete message"
                >
                  ✕
                </button>
              )}
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {/* Typing indicator */}
      <div className="typing-indicator">
        {typingUsers.length > 0 && `${typingUsers.join(', ')} is typing…`}
      </div>

      {error && <div className="alert alert-error" style={{ margin: '0 0 8px' }}>⚠️ {error}</div>}
      {uploading && (
        <div className="alert alert-info" style={{ margin: '0 0 8px' }}>📤 Uploading file…</div>
      )}

      {/* Input bar */}
      <form className="chat-input-bar" onSubmit={handleSend}>
        <button
          type="button"
          className="btn btn-ghost btn-icon"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          title="Attach a file or image"
        >
          📎
        </button>
        <input
          ref={fileInputRef}
          type="file"
          style={{ display: 'none' }}
          onChange={handleFileSelect}
          accept="image/*,.pdf,.docx,.xlsx,.txt,.zip"
        />
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="Type a message… or drag & drop a file"
          autoComplete="off"
          disabled={sending || uploading}
        />
        <button type="submit" className="btn btn-primary" disabled={!input.trim() || sending || uploading}>
          {sending ? '…' : '📨 Send'}
        </button>
      </form>
    </div>
  );
}
