import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../App';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        if (res.status === 401) {
          setError('Invalid credentials');
        } else {
          const data = await res.json().catch(() => ({}));
          setError(data.detail || 'Login failed');
        }
        setSubmitting(false);
        return;
      }

      const data = await res.json();
      await login(data.access_token);
      navigate('/dashboard');
    } catch {
      setError('Network error');
      setSubmitting(false);
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f3f4f6', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ background: '#fff', padding: '2rem', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', width: '320px' }}>
        <h2 style={{ margin: '0 0 1.5rem', textAlign: 'center', fontSize: '1.25rem', color: '#111' }}>Sign In</h2>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <input
            type="text"
            placeholder="Username"
            required
            value={username}
            onChange={e => setUsername(e.target.value)}
            style={{ padding: '0.6rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.95rem' }}
          />
          <input
            type="password"
            placeholder="Password"
            required
            value={password}
            onChange={e => setPassword(e.target.value)}
            style={{ padding: '0.6rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.95rem' }}
          />

          {error && (
            <div style={{ color: '#dc2626', fontSize: '0.85rem', textAlign: 'center' }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            style={{ padding: '0.6rem', borderRadius: '6px', background: '#111827', color: '#fff', border: 'none', fontWeight: 600, cursor: submitting ? 'not-allowed' : 'pointer', opacity: submitting ? 0.7 : 1 }}
          >
            {submitting ? 'Signing in...' : 'Login'}
          </button>
        </form>

        <div style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.85rem', color: '#6b7280' }}>
          No account? <Link to="/signup" style={{ color: '#2563eb', textDecoration: 'none' }}>Sign up</Link>
        </div>
      </div>
    </div>
  );
}
