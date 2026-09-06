import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../App';

interface DocCount {
  total: number;
  loaded: boolean;
  error: boolean;
}

const FEATURES = [
  {
    to: '/chat',
    label: 'Chat',
    desc: 'Ask questions across all data sources',
    icon: '💬',
    color: '#111827',
    bg: '#f9fafb',
    border: '#e5e7eb',
  },
  {
    to: '/documents',
    label: 'Documents',
    desc: 'Upload and manage knowledge base',
    icon: '📄',
    color: '#1d4ed8',
    bg: '#eff6ff',
    border: '#bfdbfe',
  },
  {
    to: '/research',
    label: 'Research',
    desc: 'Multi-tool deep research',
    icon: '🔍',
    color: '#15803d',
    bg: '#f0fdf4',
    border: '#bbf7d0',
  },
  {
    to: '/sql',
    label: 'SQL',
    desc: 'Query enterprise data',
    icon: '🗄️',
    color: '#7c3aed',
    bg: '#f5f3ff',
    border: '#ddd6fe',
  },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const [docCount] = useDocCount();

  const roleColor =
    user?.role === 'admin' ? '#7c3aed' :
    user?.role === 'manager' ? '#2563eb' : '#059669';
  const roleBg =
    user?.role === 'admin' ? '#ede9fe' :
    user?.role === 'manager' ? '#eff6ff' : '#ecfdf5';

  return (
    <div style={{ maxWidth: '720px' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827', margin: '0 0 0.25rem' }}>
          Welcome, {user?.username}
        </h1>
        <p style={{ color: '#6b7280', margin: 0 }}>
          Signed in as{' '}
          <span style={{
            display: 'inline-block',
            padding: '0.15rem 0.6rem',
            borderRadius: '6px',
            fontWeight: 600,
            fontSize: '0.8rem',
            background: roleBg,
            color: roleColor,
            textTransform: 'capitalize',
          }}>
            {user?.role}
          </span>
        </p>
      </div>

      {/* Identity cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.75rem', marginBottom: '1.5rem' }}>
        {[
          { label: 'Role', value: user?.role ?? '—', capitalize: true },
          { label: 'Tenant ID', value: String(user?.tenant_id ?? '—') },
          { label: 'User ID', value: String(user?.user_id ?? '—') },
        ].map(({ label, value, capitalize }) => (
          <div key={label} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '0.875rem 1rem' }}>
            <div style={{ fontSize: '0.7rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.2rem' }}>{label}</div>
            <div style={{ fontSize: '1rem', fontWeight: 600, color: '#111827', textTransform: capitalize ? 'capitalize' : 'none' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Feature cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem', marginBottom: '1.5rem' }}>
        {FEATURES.map((f) => (
          <Link
            key={f.to}
            to={f.to}
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.3rem',
              padding: '1rem',
              borderRadius: '10px',
              background: f.bg,
              border: `1px solid ${f.border}`,
              textDecoration: 'none',
              transition: 'box-shadow 0.15s ease',
            }}
            onMouseEnter={e => (e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)')}
            onMouseLeave={e => (e.currentTarget.style.boxShadow = 'none')}
          >
            <div style={{ fontSize: '1.4rem', lineHeight: 1 }}>{f.icon}</div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', color: f.color }}>{f.label}</div>
            <div style={{ fontSize: '0.78rem', color: '#6b7280', lineHeight: 1.35 }}>{f.desc}</div>
          </Link>
        ))}
      </div>

      {/* Document count stat */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '0.875rem 1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div>
              <div style={{ fontSize: '0.7rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.15rem' }}>
                Documents Ingested
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827' }}>
                {docCount.error ? '—' : docCount.loaded ? docCount.total : '…'}
              </div>
            </div>
            <div style={{ fontSize: '1.4rem' }}>📄</div>
          </div>
          {docCount.error && (
            <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
              Could not load document count
            </div>
          )}
        </div>
      </div>

      {/* API Key hint */}
      <div style={{ padding: '0.875rem 1rem', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', marginBottom: '1rem' }}>
        <label htmlFor="mistral-key" style={{ fontSize: '0.75rem', fontWeight: 600, color: '#374151', display: 'block', marginBottom: '0.35rem' }}>
          Mistral API Key (optional)
        </label>
        <input
          id="mistral-key"
          type="password"
          placeholder="Enter MISTRAL_API_KEY"
          style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.9rem', boxSizing: 'border-box' }}
          onChange={(e) => {
            (window as any).mistralApiKey = e.target.value;
          }}
        />
        <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem', marginBottom: 0 }}>
          Used by Research and Chat; does not persist across reloads.
        </p>
      </div>

      {/* Access notice */}
      <div style={{ padding: '0.875rem 1rem', background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '0.875rem', color: '#6b7280' }}>
        <strong style={{ color: '#374151' }}>Access:</strong> All employees can use Chat, Documents, and Research.{' '}
        {user?.role !== 'employee' && 'SQL queries are available to your role.'}
        {user?.role === 'employee' && ' Contact your manager to request SQL access.'}
      </div>
    </div>
  );
}

function useDocCount() {
  const [state, setState] = useState<DocCount>({ total: 0, loaded: false, error: false });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await (window as any).__apiFetch?.('/api/v1/documents?limit=1');
        if (!res?.ok) throw new Error('non-ok');
        const data = await res.json();
        if (!cancelled) setState({ total: data.total ?? 0, loaded: true, error: false });
      } catch {
        if (!cancelled) setState(s => ({ ...s, error: true, loaded: true }));
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return [state] as const;
}
