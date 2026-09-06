import { useState } from 'react';
import { useAuth } from '../App';

interface SQLResultData {
  success: boolean;
  sql: string;
  row_count: number;
  data?: Record<string, unknown>[];
  error?: string;
  attempts: number;
}

export default function SqlPage() {
  const { user, token } = useAuth();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SQLResultData | null>(null);
  const [error, setError] = useState('');

  // RBAC: SQL only for admin and manager (matches permissions.py:49)
  if (user && !['admin', 'manager'].includes(user.role)) {
    return (
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827', margin: '0 0 1rem' }}>SQL</h1>
        <div style={{ color: '#dc2626', fontSize: '0.95rem', padding: '1rem', background: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca' }}>
          Access denied. SQL queries require an <strong>admin</strong> or <strong>manager</strong> role.
          Your role: <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{user.role}</span>.
        </div>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    setLoading(true);
    setResult(null);
    setError('');

    try {
      const res = await (window as any).__apiFetch('/api/v1/sql', {
        method: 'POST',
        body: JSON.stringify({ query: trimmed }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || `Query failed (${res.status})`);
        setLoading(false);
        return;
      }
      setResult(data as SQLResultData);
    } catch {
      setError('Network error.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827', margin: '0 0 0.5rem' }}>SQL</h1>
      <p style={{ color: '#6b7280', fontSize: '0.875rem', margin: '0 0 1rem' }}>
        Ask a question in natural language and the agent will generate, validate, and execute a SQL query.
        RBAC: <code>admin</code>, <code>manager</code> only.
      </p>

      <form onSubmit={handleSubmit} style={{ maxWidth: '640px', marginBottom: '1.5rem' }}>
        <textarea
          rows={3}
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="e.g. Show total orders by region"
          disabled={loading}
          maxLength={2000}
          style={{
            width: '100%',
            padding: '0.6rem 0.85rem',
            borderRadius: '8px',
            border: '1px solid #d1d5db',
            fontSize: '0.95rem',
            resize: 'vertical',
            boxSizing: 'border-box',
          }}
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          style={{
            marginTop: '0.75rem',
            padding: '0.5rem 1.25rem',
            borderRadius: '8px',
            background: '#111827',
            color: '#fff',
            border: 'none',
            cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !query.trim() ? 0.6 : 1,
            fontWeight: 600,
            fontSize: '0.875rem',
          }}
        >
          {loading ? 'Running...' : 'Run SQL'}
        </button>
      </form>

      {error && (
        <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#dc2626', fontSize: '0.9rem' }}>
          {error}
        </div>
      )}

      {result && !result.success && (
        <div style={{ marginTop: '1rem', padding: '1rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#dc2626' }}>
          <strong>Query failed</strong>
          <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', fontFamily: 'monospace' }}>{result.error}</div>
          {result.sql && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#6b7280' }}>
              Generated SQL: <code style={{ background: '#fff', padding: '0.1rem 0.3rem' }}>{result.sql}</code>
            </div>
          )}
        </div>
      )}

      {result && result.success && (
        <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Stats bar */}
          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: '#6b7280' }}>
            <span>{result.row_count} row{result.row_count !== 1 ? 's' : ''}</span>
            <span>·</span>
            <span>{result.attempts} attempt{result.attempts !== 1 ? 's' : ''}</span>
            <span>·</span>
            <code style={{ background: '#f3f4f6', padding: '0.1rem 0.4rem', borderRadius: '4px', color: '#374151' }}>{result.sql}</code>
          </div>

          {/* Results table */}
          {result.data && result.data.length > 0 ? (
            <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'auto', maxHeight: '400px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb', position: 'sticky', top: 0 }}>
                    {Object.keys(result.data[0]).map(col => (
                      <th key={col} style={{ padding: '0.5rem 0.75rem', textAlign: 'left', color: '#6b7280', fontWeight: 500, whiteSpace: 'nowrap' }}>
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.data.map((row, i) => (
                    <tr key={i} style={{ borderBottom: i < result.data.length - 1 ? '1px solid #f3f4f6' : 'none' }}>
                      {Object.values(row).map((val, j) => (
                        <td key={j} style={{ padding: '0.5rem 0.75rem', color: '#111827', whiteSpace: 'nowrap' }}>
                          {val === null ? (
                            <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>NULL</span>
                          ) : String(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ color: '#9ca3af', fontSize: '0.875rem', padding: '1rem', textAlign: 'center' }}>
              Query returned 0 rows.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
