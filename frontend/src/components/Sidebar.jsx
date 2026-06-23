import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const API_BASE = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://localhost:8000';

function getAvatarSrc(url) {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `${API_BASE}${url}`;
}

export default function Sidebar({ open, onClose }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleNavClick = () => {
    // Close sidebar on mobile when navigating
    onClose?.();
  };

  const initial = user?.username?.[0]?.toUpperCase() || '?';
  const avatarSrc = getAvatarSrc(user?.avatar_url);

  return (
    <aside className={`sidebar${open ? ' open' : ''}`}>
      <div className="sidebar-logo">
        <span>💬 ChatShare</span>
      </div>

      <div className="sidebar-user">
        {avatarSrc ? (
          <img
            src={avatarSrc}
            alt="Avatar"
            style={{
              width: 36, height: 36, borderRadius: '50%',
              objectFit: 'cover', marginBottom: 8,
              border: '2px solid var(--accent-1)',
            }}
            onError={e => { e.target.style.display = 'none'; }}
          />
        ) : (
          <div className="user-avatar">{initial}</div>
        )}
        <div className="user-name">{user?.username}</div>
        <div className="user-email">{user?.email}</div>
      </div>

      <nav className="sidebar-nav">
        <NavLink
          to="/dashboard"
          className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          onClick={handleNavClick}
        >
          <span className="nav-icon">🏠</span> Dashboard
        </NavLink>
        <NavLink
          to="/profile"
          className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          onClick={handleNavClick}
        >
          <span className="nav-icon">👤</span> Profile
        </NavLink>
        <NavLink
          to="/admin"
          className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          onClick={handleNavClick}
        >
          <span className="nav-icon">🛡️</span> Admin
        </NavLink>
      </nav>

      <div className="sidebar-bottom">
        <button className="btn btn-ghost btn-full btn-sm" onClick={handleLogout}>
          🚪 Logout
        </button>
      </div>
    </aside>
  );
}
