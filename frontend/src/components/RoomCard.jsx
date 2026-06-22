import { useNavigate } from 'react-router-dom';

export function RoleBadge({ role }) {
  return <span className={`badge badge-${role}`}>{role}</span>;
}

export default function RoomCard({ room, showJoin = false, onJoin }) {
  const navigate = useNavigate();

  const handleClick = (e) => {
    if (e.target.closest('button')) return;
    navigate(`/room/${room.id}`);
  };

  return (
    <div className="room-card" onClick={handleClick} role="button" tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && handleClick(e)}>
      <div className="room-card-info">
        <h3>
          {room.is_private ? '🔒' : '🌍'} {room.name}
        </h3>
        <p>{room.description || 'No description'} · 👥 {room.member_count ?? 0} members</p>
      </div>
      <div className="room-card-meta">
        <span className={`badge badge-${room.is_private ? 'private' : 'public'}`}>
          {room.is_private ? 'Private' : 'Public'}
        </span>
        {showJoin && (
          <button
            className="btn btn-secondary btn-sm"
            onClick={e => { e.stopPropagation(); onJoin?.(room.id); }}
          >
            Join
          </button>
        )}
      </div>
    </div>
  );
}
