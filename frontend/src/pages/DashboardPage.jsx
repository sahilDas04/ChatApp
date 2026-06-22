import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { roomsAPI, errMsg } from '../api/client';
import Layout from '../components/Layout';
import RoomCard from '../components/RoomCard';

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('my');

  // My Rooms
  const [myRooms, setMyRooms] = useState([]);
  const [myLoading, setMyLoading] = useState(true);

  // Create Room
  const [createName, setCreateName] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [createPrivate, setCreatePrivate] = useState(false);
  const [createErr, setCreateErr] = useState('');
  const [createLoading, setCreateLoading] = useState(false);

  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [myRoomIds, setMyRoomIds] = useState(new Set());

  // Pending Requests
  const [pending, setPending] = useState([]);

  useEffect(() => {
    loadMyRooms();
    loadPending();
  }, []);

  const loadMyRooms = () => {
    setMyLoading(true);
    roomsAPI.list({ my_rooms: true, size: 50 })
      .then(data => {
        setMyRooms(data.items || []);
        setMyRoomIds(new Set((data.items || []).map(r => r.id)));
      })
      .catch(() => {})
      .finally(() => setMyLoading(false));
  };

  const loadPending = () => {
    roomsAPI.myRequests().then(setPending).catch(() => {});
  };

  const handleSearch = (q) => {
    setSearchQuery(q);
    setSearchLoading(true);
    roomsAPI.list({ search: q, size: 50 })
      .then(data => setSearchResults(data.items || []))
      .catch(() => {})
      .finally(() => setSearchLoading(false));
  };

  useEffect(() => {
    if (tab === 'search') handleSearch(searchQuery);
  }, [tab]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateErr('');
    if (!createName.trim()) { setCreateErr('Room name is required.'); return; }
    setCreateLoading(true);
    try {
      const room = await roomsAPI.create({ name: createName, description: createDesc, is_private: createPrivate });
      navigate(`/room/${room.id}`);
    } catch (e) {
      setCreateErr(errMsg(e));
    } finally {
      setCreateLoading(false);
    }
  };

  const handleJoin = async (roomId) => {
    try {
      const res = await roomsAPI.join(roomId);
      alert(res.message || 'Joined!');
      loadMyRooms();
      handleSearch(searchQuery);
    } catch (e) {
      alert(errMsg(e));
    }
  };

  const TABS = [
    { id: 'my', label: '📂 My Rooms' },
    { id: 'create', label: '➕ Create Room' },
    { id: 'search', label: '🔍 Search' },
    { id: 'pending', label: '📩 Pending' },
  ];

  return (
    <Layout>
      <div className="page-header">
        <h1>🏠 Dashboard</h1>
        <p>Welcome back, <strong>{user?.username}</strong>! 👋</p>
      </div>

      <div className="tabs" style={{ maxWidth: 600 }}>
        {TABS.map(t => (
          <button key={t.id} className={`tab-btn${tab === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* My Rooms */}
      {tab === 'my' && (
        <div className="page-enter">
          {myLoading ? <div className="spinner-wrap"><div className="spinner" /></div> :
            myRooms.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🔮</div>
                <p>You haven't joined any rooms yet.<br />Create one or search for existing rooms!</p>
              </div>
            ) : myRooms.map(r => <RoomCard key={r.id} room={r} />)
          }
        </div>
      )}

      {/* Create Room */}
      {tab === 'create' && (
        <div className="card page-enter" style={{ maxWidth: 520 }}>
          <div className="section-title">✨ Create a New Room</div>
          {createErr && <div className="alert alert-error">{createErr}</div>}
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label>Room Name</label>
              <input className="form-input" placeholder="e.g. Project Alpha" maxLength={100}
                value={createName} onChange={e => setCreateName(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <textarea className="form-input" placeholder="What's this room about?" maxLength={500}
                value={createDesc} onChange={e => setCreateDesc(e.target.value)} />
            </div>
            <div className="toggle-row">
              <label>🔒 Private Room</label>
              <label className="toggle">
                <input type="checkbox" checked={createPrivate} onChange={e => setCreatePrivate(e.target.checked)} />
                <span className="toggle-slider" />
              </label>
            </div>
            <button className="btn btn-primary btn-full mt-2" type="submit" disabled={createLoading}>
              {createLoading ? 'Creating…' : '🚀 Create Room'}
            </button>
          </form>
        </div>
      )}

      {/* Search */}
      {tab === 'search' && (
        <div className="page-enter">
          <div className="form-group" style={{ maxWidth: 480, marginBottom: 20 }}>
            <input className="form-input" placeholder="Search rooms by name…"
              value={searchQuery}
              onChange={e => handleSearch(e.target.value)} />
          </div>
          {searchLoading ? <div className="spinner-wrap"><div className="spinner" /></div> :
            searchResults.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🔍</div>
                <p>No rooms found. Try a different term.</p>
              </div>
            ) : searchResults.map(r => (
              <RoomCard key={r.id} room={r}
                showJoin={!myRoomIds.has(r.id)}
                onJoin={handleJoin} />
            ))
          }
        </div>
      )}

      {/* Pending Requests */}
      {tab === 'pending' && (
        <div className="page-enter">
          <div className="section-title">📩 Your Pending Join Requests</div>
          {pending.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🎉</div>
              <p>No pending requests.</p>
            </div>
          ) : pending.map(req => (
            <div key={req.id} className="card mb-1">
              <div className="flex-between">
                <div>
                  <strong>Room #{req.room_id}</strong>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                    Status: ⏳ {req.status} · {req.requested_at?.slice(0, 10)}
                  </div>
                </div>
                <span className="badge badge-private">{req.status}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
