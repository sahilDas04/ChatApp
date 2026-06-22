import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { roomsAPI, errMsg } from '../api/client';
import Layout from '../components/Layout';
import { RoleBadge } from '../components/RoomCard';

export default function AdminPage() {
  const { user } = useAuth();
  const [rooms, setRooms] = useState([]);
  const [selectedRoom, setSelectedRoom] = useState('');
  const [members, setMembers] = useState([]);
  const [requests, setRequests] = useState([]);
  const [userRole, setUserRole] = useState(null);
  const [tab, setTab] = useState('requests');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    roomsAPI.list({ my_rooms: true, size: 100 })
      .then(data => {
        const r = data.items || [];
        setRooms(r);
        if (r.length > 0) setSelectedRoom(String(r[0].id));
      })
      .catch(e => setError(errMsg(e)));
  }, []);

  useEffect(() => {
    if (!selectedRoom) return;
    loadRoomData(parseInt(selectedRoom));
  }, [selectedRoom]);

  const loadRoomData = async (roomId) => {
    setLoading(true);
    setError('');
    try {
      const [m, r] = await Promise.all([
        roomsAPI.members(roomId),
        roomsAPI.joinRequests(roomId, 'pending'),
      ]);
      setMembers(m);
      setRequests(r);
      const me = m.find(mem => mem.user_id === user?.id);
      setUserRole(me?.role || null);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setLoading(false);
    }
  };

  const handleRequest = async (reqId, status) => {
    try {
      await roomsAPI.handleRequest(parseInt(selectedRoom), reqId, status);
      setRequests(prev => prev.filter(r => r.id !== reqId));
      if (status === 'approved') loadRoomData(parseInt(selectedRoom));
    } catch (e) { alert(errMsg(e)); }
  };

  const handleRoleChange = async (uid, newRole) => {
    try {
      const updated = await roomsAPI.updateRole(parseInt(selectedRoom), uid, newRole);
      setMembers(prev => prev.map(m => m.user_id === uid ? { ...m, role: updated.role } : m));
    } catch (e) { alert(errMsg(e)); }
  };

  const handleRemove = async (uid) => {
    if (!window.confirm('Remove this member?')) return;
    try {
      await roomsAPI.removeMember(parseInt(selectedRoom), uid);
      setMembers(prev => prev.filter(m => m.user_id !== uid));
    } catch (e) { alert(errMsg(e)); }
  };

  const isAdminOrCreator = ['creator', 'admin'].includes(userRole);

  return (
    <Layout>
      <div className="page-header">
        <h1>🛡️ Room Admin Panel</h1>
        <p>Manage your rooms, members, and join requests from one place.</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {rooms.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🏠</div>
          <p>You don't have any rooms to manage.<br />Create one from the Dashboard!</p>
        </div>
      ) : (
        <>
          <div className="form-group" style={{ maxWidth: 360, marginBottom: 24 }}>
            <label>Select Room</label>
            <select className="form-input" value={selectedRoom}
              onChange={e => setSelectedRoom(e.target.value)}>
              {rooms.map(r => (
                <option key={r.id} value={r.id}>
                  {r.name} {r.is_private ? '🔒' : '🌍'}
                </option>
              ))}
            </select>
          </div>

          {!isAdminOrCreator && (
            <div className="alert alert-warning">⚠️ You need to be an admin or creator to manage this room.</div>
          )}

          {isAdminOrCreator && !loading && (
            <>
              <div className="tabs" style={{ maxWidth: 440, marginBottom: 20 }}>
                <button className={`tab-btn${tab === 'requests' ? ' active' : ''}`} onClick={() => setTab('requests')}>
                  📩 Join Requests ({requests.length})
                </button>
                <button className={`tab-btn${tab === 'members' ? ' active' : ''}`} onClick={() => setTab('members')}>
                  👥 Members ({members.length})
                </button>
              </div>

              {/* Join Requests */}
              {tab === 'requests' && (
                <div className="page-enter">
                  {requests.length === 0 ? (
                    <div className="empty-state" style={{ padding: '24px 0' }}>
                      <div className="empty-icon">🎉</div>
                      <p>No pending join requests.</p>
                    </div>
                  ) : requests.map(req => (
                    <div key={req.id} className="card mb-1">
                      <div className="flex-between">
                        <div>
                          <strong>👤 {req.user?.username ?? `User #${req.user_id}`}</strong>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 2 }}>
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
                </div>
              )}

              {/* Member Management */}
              {tab === 'members' && (
                <div className="page-enter">
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 12 }}>
                    Total: {members.length} members
                  </div>
                  <div className="members-list">
                    {members.map(m => {
                      const isMe = m.user_id === user?.id;
                      const isCreatorRole = m.role === 'creator';
                      return (
                        <div key={m.user_id} className="member-row">
                          <div className="user-avatar" style={{ width: 32, height: 32, fontSize: '0.8rem' }}>
                            {m.user?.username?.[0]?.toUpperCase()}
                          </div>
                          <div className="member-info">
                            <div className="name">{m.user?.username}{isMe ? ' (You)' : ''}</div>
                          </div>
                          <RoleBadge role={m.role} />
                          {!isMe && !isCreatorRole && (
                            <div className="member-actions">
                              {userRole === 'creator' && (
                                <button className="btn btn-ghost btn-sm"
                                  onClick={() => handleRoleChange(m.user_id, m.role === 'admin' ? 'member' : 'admin')}
                                  title={m.role === 'admin' ? 'Demote to member' : 'Promote to admin'}>
                                  {m.role === 'admin' ? '⬇️' : '⬆️'}
                                </button>
                              )}
                              <button className="btn btn-danger btn-sm" onClick={() => handleRemove(m.user_id)}>
                                🗑️
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}

          {loading && <div className="spinner-wrap"><div className="spinner" /></div>}
        </>
      )}
    </Layout>
  );
}
