import { Outlet } from 'react-router-dom';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { HealthDot } from './HealthDot';

const NAV = [
  { label: 'Dashboard', path: '/dashboard', roles: ['admin', 'manager', 'employee'] },
  { label: 'Chat', path: '/chat', roles: ['admin', 'manager', 'employee'] },
  { label: 'Documents', path: '/documents', roles: ['admin', 'manager', 'employee'] },
  { label: 'Research', path: '/research', roles: ['admin', 'manager', 'employee'] },
  { label: 'SQL', path: '/sql', roles: ['admin', 'manager'] },
];

export default function Shell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const visibleNav = NAV.filter(n => user && n.roles.includes(user.role));

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'system-ui, sans-serif', background: '#f3f4f6' }}>
      {/* Sidebar */}
      <aside style={{ width: '220px', background: '#111827', color: '#fff', padding: '1.25rem 0' }}>
        <div style={{ padding: '0 1.25rem', fontWeight: 700, fontSize: '1.05rem', marginBottom: '2rem' }}>
          Enterprise Agent
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', padding: '0 0.75rem' }}>
          {visibleNav.map(n => (
            <Link
              key={n.path}
              to={n.path}
              style={{
                color: pathname.startsWith(n.path) ? '#fff' : '#9ca3af',
                textDecoration: 'none',
                padding: '0.5rem 0.75rem',
                borderRadius: '6px',
                fontSize: '0.875rem',
                fontWeight: pathname.startsWith(n.path) ? 600 : 400,
                background: pathname.startsWith(n.path) ? '#1f2937' : 'transparent',
                transition: 'all 0.15s',
              }}
            >
              {n.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Header */}
        <header style={{ background: '#fff', borderBottom: '1px solid #e5e7eb', padding: '0.75rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            {user?.username} <span style={{ color: '#9ca3af' }}>·</span>{' '}
            <span style={{ textTransform: 'capitalize', color: '#374151' }}>{user?.role}</span>
            <HealthDot />
          </span>
          <button
            onClick={handleLogout}
            style={{
              padding: '0.35rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid #d1d5db',
              background: '#fff',
              cursor: 'pointer',
              fontSize: '0.875rem',
              color: '#374151',
            }}
          >
            Logout
          </button>
        </header>

        <main style={{ padding: '1.5rem', flex: 1, overflow: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
