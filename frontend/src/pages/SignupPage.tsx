import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function SignupPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('employee');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, role, tenant_id: 1 }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || 'Signup failed');
        setSubmitting(false);
        return;
      }
      navigate('/login');
    } catch {
      setError('Network error');
      setSubmitting(false);
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f3f4f6', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ background: '#fff', padding: '2rem', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', width: '340px' }}>
        <h2 style={{ margin: '0 0 1.5rem', textAlign: 'center', fontSize: '1.25rem', color: '#111' }}>Create Account</h2>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <input placeholder="Username" required value={username} onChange={e => setUsername(e.target.value)} style={{ padding: '0.6rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.95rem' }} />
          <input type="email" placeholder="Email" required value={email} onChange={e => setEmail(e.target.value)} style={{ padding: '0.6rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.95rem' }} />
          <input type="password" placeholder="Password" required value={password} onChange={e => setPassword(e.target.value)} style={{ padding: '0.6rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.95rem' }} />
          <select value={role} onChange={e => setRole(e.target.value)} style={{ padding: '0.6rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.95rem', background: '#fff' }}>
            <option value="employee">Employee</option>
            <option value="manager">Manager</option>
            <option value="admin">Admin</option>
          </select>
          {error && <div style={{ color: '#dc2626', fontSize: '0.85rem', textAlign: 'center' }}>{error}</div>}
          <button type="submit" disabled={submitting} style={{ padding: '0.6rem', borderRadius: '6px', background: '#111827', color: '#fff', border: 'none', fontWeight: 600, cursor: submitting ? 'not-allowed' : 'pointer', opacity: submitting ? 0.7 : 1 }}>
            {submitting ? 'Creating...' : 'Sign Up'}
          </button>
        </form>
        <div style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.85rem', color: '#6b7280' }}>
          Already have an account? <Link to="/login" style={{ color: '#2563eb', textDecoration: 'none' }}>Log in</Link>
        </div>
      </div>
    </div>
  );
}
