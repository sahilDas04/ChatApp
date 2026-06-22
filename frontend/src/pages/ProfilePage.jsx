import { useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { usersAPI, errMsg } from '../api/client';
import Layout from '../components/Layout';

const API_BASE = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://localhost:8000';

function getAvatarSrc(url) {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `${API_BASE}${url}`;
}

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const [tab, setTab] = useState('edit');

  // Avatar upload state
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [avatarFile, setAvatarFile] = useState(null);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const [avatarMsg, setAvatarMsg] = useState('');
  const avatarInputRef = useRef();

  // Edit profile state
  const [username, setUsername] = useState(user?.username || '');
  const [email, setEmail] = useState(user?.email || '');
  const [editMsg, setEditMsg] = useState('');
  const [editLoading, setEditLoading] = useState(false);

  // Change password state
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [pwMsg, setPwMsg] = useState('');
  const [pwLoading, setPwLoading] = useState(false);

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setAvatarFile(file);
    setAvatarPreview(URL.createObjectURL(file));
    setAvatarMsg('');
  };

  const handleAvatarUpload = async () => {
    if (!avatarFile) return;
    setAvatarLoading(true);
    setAvatarMsg('');
    try {
      const updated = await usersAPI.uploadAvatar(avatarFile);
      setUser(updated);
      setAvatarMsg('✅ Profile picture updated!');
      setAvatarPreview(null);
      setAvatarFile(null);
    } catch (e) {
      setAvatarMsg('❌ ' + errMsg(e));
    } finally {
      setAvatarLoading(false);
    }
  };

  const handleEditProfile = async (e) => {
    e.preventDefault();
    setEditMsg('');
    const updates = {};
    if (username !== user.username) updates.username = username;
    if (email !== user.email) updates.email = email;
    if (!Object.keys(updates).length) { setEditMsg('ℹ️ No changes detected.'); return; }
    setEditLoading(true);
    try {
      const updated = await usersAPI.updateProfile(updates);
      setUser(updated);
      setEditMsg('✅ Profile updated!');
    } catch (e) {
      setEditMsg('❌ ' + errMsg(e));
    } finally {
      setEditLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwMsg('');
    if (newPw !== confirmPw) { setPwMsg('❌ Passwords do not match.'); return; }
    setPwLoading(true);
    try {
      await usersAPI.changePassword(currentPw, newPw);
      setPwMsg('✅ Password changed successfully!');
      setCurrentPw(''); setNewPw(''); setConfirmPw('');
    } catch (e) {
      setPwMsg('❌ ' + errMsg(e));
    } finally {
      setPwLoading(false);
    }
  };

  const currentAvatar = getAvatarSrc(user?.avatar_url);
  const displaySrc = avatarPreview || currentAvatar;
  const initial = user?.username?.[0]?.toUpperCase() || '?';

  return (
    <Layout>
      <div className="page-header">
        <h1>👤 Profile</h1>
      </div>

      {/* Profile card with avatar */}
      <div className="card mb-2" style={{ maxWidth: 480 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          {/* Avatar */}
          <div style={{ position: 'relative', flexShrink: 0 }}>
            {displaySrc ? (
              <img
                src={displaySrc}
                alt="Avatar"
                style={{
                  width: 80, height: 80, borderRadius: '50%',
                  objectFit: 'cover',
                  border: '3px solid var(--accent-1)',
                  boxShadow: '0 0 0 4px rgba(102,126,234,0.2)',
                }}
              />
            ) : (
              <div className="user-avatar" style={{ width: 80, height: 80, fontSize: '2rem' }}>
                {initial}
              </div>
            )}
            {/* Camera overlay */}
            <button
              onClick={() => avatarInputRef.current?.click()}
              style={{
                position: 'absolute', bottom: 0, right: 0,
                width: 26, height: 26,
                borderRadius: '50%',
                background: 'var(--accent-grad)',
                border: '2px solid var(--bg-surface)',
                cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.75rem',
              }}
              title="Change profile picture"
            >
              📷
            </button>
            <input
              ref={avatarInputRef}
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              style={{ display: 'none' }}
              onChange={handleAvatarChange}
            />
          </div>

          {/* User info */}
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>{user?.username}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: 2 }}>{user?.email}</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: 4 }}>
              Member since: {user?.created_at?.slice(0, 10) ?? 'N/A'}
            </div>
          </div>
        </div>

        {/* Avatar upload actions */}
        {avatarFile && (
          <div style={{ marginTop: 14, display: 'flex', gap: 10, alignItems: 'center' }}>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleAvatarUpload}
              disabled={avatarLoading}
            >
              {avatarLoading ? 'Uploading…' : '✅ Save Photo'}
            </button>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => { setAvatarFile(null); setAvatarPreview(null); }}
            >
              ✕ Cancel
            </button>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {avatarFile.name}
            </span>
          </div>
        )}
        {avatarMsg && (
          <div className={`alert ${avatarMsg.startsWith('✅') ? 'alert-success' : 'alert-error'} mt-1`}>
            {avatarMsg}
          </div>
        )}
        {!avatarFile && (
          <p style={{ marginTop: 10, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Click the 📷 icon to change your profile picture (JPG, PNG, GIF, WebP · max 5 MB)
          </p>
        )}
      </div>

      {/* Tabs */}
      <div className="tabs" style={{ maxWidth: 420, marginBottom: 20 }}>
        <button className={`tab-btn${tab === 'edit' ? ' active' : ''}`} onClick={() => setTab('edit')}>
          ✏️ Edit Profile
        </button>
        <button className={`tab-btn${tab === 'password' ? ' active' : ''}`} onClick={() => setTab('password')}>
          🔑 Change Password
        </button>
      </div>

      {/* Edit Profile */}
      {tab === 'edit' && (
        <div className="card page-enter" style={{ maxWidth: 420 }}>
          {editMsg && (
            <div className={`alert ${editMsg.startsWith('✅') ? 'alert-success' : editMsg.startsWith('ℹ️') ? 'alert-info' : 'alert-error'} mb-2`}>
              {editMsg}
            </div>
          )}
          <form onSubmit={handleEditProfile}>
            <div className="form-group">
              <label>Username</label>
              <input className="form-input" maxLength={50}
                value={username} onChange={e => setUsername(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input className="form-input" type="email"
                value={email} onChange={e => setEmail(e.target.value)} />
            </div>
            <button className="btn btn-primary btn-full mt-2" type="submit" disabled={editLoading}>
              {editLoading ? 'Saving…' : '💾 Save Changes'}
            </button>
          </form>
        </div>
      )}

      {/* Change Password */}
      {tab === 'password' && (
        <div className="card page-enter" style={{ maxWidth: 420 }}>
          {pwMsg && (
            <div className={`alert ${pwMsg.startsWith('✅') ? 'alert-success' : 'alert-error'} mb-2`}>
              {pwMsg}
            </div>
          )}
          <form onSubmit={handleChangePassword}>
            <div className="form-group">
              <label>Current Password</label>
              <input className="form-input" type="password"
                value={currentPw} onChange={e => setCurrentPw(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>New Password</label>
              <input className="form-input" type="password" placeholder="Min 8 chars, 1 uppercase, 1 digit"
                value={newPw} onChange={e => setNewPw(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Confirm New Password</label>
              <input className="form-input" type="password"
                value={confirmPw} onChange={e => setConfirmPw(e.target.value)} required />
            </div>
            <button className="btn btn-primary btn-full mt-2" type="submit" disabled={pwLoading}>
              {pwLoading ? 'Changing…' : '🔑 Change Password'}
            </button>
          </form>
        </div>
      )}
    </Layout>
  );
}
