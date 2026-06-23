import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { roomsAPI, errMsg } from '../api/client';
import Layout from '../components/Layout';
import ChatWindow from '../components/ChatWindow';
import FileManager from '../components/FileManager';
import { RoleBadge } from '../components/RoomCard';

export default function RoomPage() {
  const { id } = useParams();
  const roomId = parseInt(id, 10);
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('chat');

  const [room, setRoom] = useState(null);
  const [members, setMembers] = useState([]);
  const [userRole, setUserRole] = useState('member');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Room Settings state
  const [settingName, setSettingName] = useState('');
  const [settingDesc, setSettingDesc] = useState('');
  const [settingPrivate, setSettingPrivate] = useState(false);
  const [settingLoading, setSettingLoading] = useState(false);
  const [settingMsg, setSettingMsg] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(false);

  // Join requests
  const [requests, setRequests] = useState([]);

  useEffect(() => {
    if (!roomId) return;
    loadRoom();
  }, [roomId]);

  const loadRoom = async () => {
    setLoading(true);
    try {
      const [r, m] = await Promise.all([
        roomsAPI.get(roomId),
        roomsAPI.members(roomId),
      ]);
      setRoom(r);
      setMembers(m);
      setSettingName(r.name);
      setSettingDesc(r.description || '');
      setSettingPrivate(r.is_private);
      const me = m.find(mem => mem.user_id === user?.id);
      setUserRole(me?.role || 'member');
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setLoading(false);
    }
  };

  const loadRequests = () => {
    roomsAPI.joinRequests(roomId, 'pending').then(setRequests).catch(() => {});
  };

  useEffect(() => {
    if (tab === 'members' && userRole !== 'member') loadRequests();
  }, [tab]);

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setSettingLoading(true);
    setSettingMsg('');
    try {
      await roomsAPI.update(roomId, { name: settingName, description: settingDesc, is_private: settingPrivate });
      setSettingMsg('✅ Room updated!');
      loadRoom();
    } catch (e) {
      setSettingMsg('❌ ' + errMsg(e));
    } finally {
      setSettingLoading(false);
    }
  };

  const handleDeleteRoom = async () => {
    try {
      await roomsAPI.delete(roomId);
      navigate('/dashboard');
    } catch (e) { alert(errMsg(e)); }
  };

  const handleLeave = async () => {
    try {
      await roomsAPI.leave(roomId);
      navigate('/dashboard');
    } catch (e) { alert(errMsg(e)); }
  };

  const handleRemoveMember = async (uid) => {
    try {
      await roomsAPI.removeMember(roomId, uid);
      setMembers(prev => prev.filter(m => m.user_id !== uid));
    } catch (e) { alert(errMsg(e)); }
  };

  const handleRoleChange = async (uid, newRole) => {
    try {
      const updated = await roomsAPI.updateRole(roomId, uid, newRole);
      setMembers(prev => prev.map(m => m.user_id === uid ? { ...m, role: updated.role } : m));
    } catch (e) { alert(errMsg(e)); }
  };

  const handleRequest = async (reqId, status) => {
    try {
      await roomsAPI.handleRequest(roomId, reqId, status);
      setRequests(prev => prev.filter(r => r.id !== reqId));
      if (status === 'approved') loadRoom();
    } catch (e) { alert(errMsg(e)); }
  };

  if (loading) return <Layout><div className="spinner-wrap"><div className="spinner" /></div></Layout>;
  if (error) return <Layout><div className="alert alert-error">{error}</div></Layout>;

  const TABS = ['chat', 'files', 'members', 'settings'];
  const TAB_LABELS = { chat: '💬 Chat', files: '📁 Files', members: '👥 Members', settings: '⚙️ Settings' };

  return (
    <Layout>
      {/* Room header */}
      <div className="room-header">
        <button className="room-header-back" onClick={() => navigate('/dashboard')}>←</button>
        <div>
          <h2>{room?.is_private ? '🔒' : '🌍'} {room?.name}</h2>
          <p>{room?.description || 'No description'} · 👥 {room?.member_count ?? members.length} members</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs" style={{ marginBottom: 20 }}>
        {TABS.map(t => (
          <button key={t} className={`tab-btn${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {/* Chat */}
      {tab === 'chat' && <ChatWindow roomId={roomId} userRole={userRole} />}

      {/* Files */}
      {tab === 'files' && (
        <FileManager roomId={roomId} userId={user?.id} userRole={userRole} />
      )}

      {/* Members */}
      {tab === 'members' && (
        <div className="page-enter">
          <div className="section-title">👥 Room Members</div>
          <div className="members-list">
            {members.map(m => {
              const isMe = m.user_id === user?.id;
              const isCreator = m.role === 'creator';
              const canAdmin = ['creator', 'admin'].includes(userRole);
              return (
                <div key={m.user_id} className="member-row">
                  <div className="user-avatar" style={{ width: 32, height: 32, fontSize: '0.8rem' }}>
                    {m.user?.username?.[0]?.toUpperCase()}
                  </div>
                  <div className="member-info">
                    <div className="name">{m.user?.username}{isMe ? ' (You)' : ''}</div>
                  </div>
                  <RoleBadge role={m.role} />
                  {canAdmin && !isCreator && !isMe && (
                    <div className="member-actions">
                      <button className="btn btn-ghost btn-sm"
                        onClick={() => handleRoleChange(m.user_id, m.role === 'admin' ? 'member' : 'admin')}>
                        {m.role === 'admin' ? '⬇️' : '⬆️'}
                      </button>
                      <button className="btn btn-danger btn-sm" onClick={() => handleRemoveMember(m.user_id)}>
                        🗑️
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Pending requests (admin/creator) */}
          {['creator', 'admin'].includes(userRole) && (
            <>
              <hr className="divider" />
              <div className="section-title">📩 Pending Join Requests</div>
              {requests.length === 0 ? (
                <div className="empty-state" style={{ padding: '20px 0' }}>
                  <p>No pending requests 🎉</p>
                </div>
              ) : requests.map(req => (
                <div key={req.id} className="card mb-1">
                  <div className="flex-between">
                    <div>
                      <strong>👤 {req.user?.username ?? `User #${req.user_id}`}</strong>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 2 }}>
                        Requested: {req.requested_at?.slice(0, 10)}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => handleRequest(req.id, 'approved')}>
                        ✅ Approve
                      </button>
                      <button className="btn btn-danger btn-sm" onClick={() => handleRequest(req.id, 'rejected')}>
                        ❌ Reject
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* Settings */}
      {tab === 'settings' && (
        <div className="page-enter" style={{ maxWidth: 540 }}>
          {userRole === 'creator' ? (
            <>
              <div className="section-title">⚙️ Room Settings</div>
              <div className="card">
                {settingMsg && (
                  <div className={`alert ${settingMsg.startsWith('✅') ? 'alert-success' : 'alert-error'} mb-2`}>
                    {settingMsg}
                  </div>
                )}
                <form onSubmit={handleSaveSettings}>
                  <div className="form-group">
                    <label>Room Name</label>
                    <input className="form-input" maxLength={100}
                      value={settingName} onChange={e => setSettingName(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label>Description</label>
                    <textarea className="form-input" maxLength={500}
                      value={settingDesc} onChange={e => setSettingDesc(e.target.value)} />
                  </div>
                  <div className="toggle-row">
                    <label>🔒 Private Room</label>
                    <label className="toggle">
                      <input type="checkbox" checked={settingPrivate} onChange={e => setSettingPrivate(e.target.checked)} />
                      <span className="toggle-slider" />
                    </label>
                  </div>
                  <button className="btn btn-primary btn-full mt-2" type="submit" disabled={settingLoading}>
                    {settingLoading ? 'Saving…' : '💾 Save Changes'}
                  </button>
                </form>
              </div>

              <div className="danger-zone">
                <h3>⚠️ Danger Zone</h3>
                {!confirmDelete ? (
                  <button className="btn btn-danger" onClick={() => setConfirmDelete(true)}>
                    🗑️ Delete Room Permanently
                  </button>
                ) : (
                  <div>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: 12, fontSize: '0.88rem' }}>
                      This will permanently delete the room and all its data. Are you sure?
                    </p>
                    <div style={{ display: 'flex', gap: 10 }}>
                      <button className="btn btn-danger" onClick={handleDeleteRoom}>✅ Confirm Delete</button>
                      <button className="btn btn-ghost" onClick={() => setConfirmDelete(false)}>Cancel</button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="card">
              <div className="alert alert-info">Only the room creator can modify settings.</div>
              <hr className="divider" />
              <button className="btn btn-danger" onClick={handleLeave}>🚪 Leave Room</button>
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}
