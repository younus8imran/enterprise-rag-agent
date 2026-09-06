import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../App';

interface Doc {
  id: number;
  name: string;
  type: string;
  source: string;
  tenant_id: number;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
}

type IngestState = 'idle' | 'submitting' | 'success' | 'error';

export default function DocumentsPage() {
  const { token, user } = useAuth();
  const [docs, setDocs] = useState<Doc[]>([]);
  const [total, setTotal] = useState(0);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [loadError, setLoadError] = useState('');

  // Ingest form
  const [showForm, setShowForm] = useState(false);
  const [ingestState, setIngestState] = useState<IngestState>('idle');
  const [ingestMsg, setIngestMsg] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  async function loadDocs() {
    setLoadingDocs(true);
    setLoadError('');
    try {
      const res = await (window as any).__apiFetch('/api/v1/documents');
      if (!res.ok) {
        const b = await res.json().catch(() => ({}));
        setLoadError(b.detail || `Error ${res.status}`);
        return;
      }
      const data = await res.json();
      setDocs(data.documents);
      setTotal(data.total);
    } catch {
      setLoadError('Failed to load documents.');
    } finally {
      setLoadingDocs(false);
    }
  }

  useEffect(() => { loadDocs(); }, []);

  async function handleIngest(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIngestState('submitting');
    setIngestMsg('');

    const form = e.currentTarget;
    const fileInput = form.elements.namedItem('file') as HTMLInputElement;
    const file = fileInput?.files?.[0];
    if (!file) {
      setIngestMsg('Please select a file.');
      setIngestState('error');
      return;
    }

    const fd = new FormData();
    fd.append('file', file);
    fd.append('tenant_id', String(user?.tenant_id ?? 1));
    fd.append('access_level', (form.elements.namedItem('access_level') as HTMLSelectElement)?.value ?? '1');
    fd.append('metadata_json', '{}');

    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch('/api/v1/documents/ingest', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });
      if (res.status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
        return;
      }
      const b = await res.json().catch(() => ({}));
      if (!res.ok) {
        setIngestMsg(b.detail || 'Ingest failed.');
        setIngestState('error');
      } else {
        setIngestMsg(`Ingested "${file.name}" — ${b.chunks_created} chunks created.`);
        setIngestState('success');
        loadDocs();
        form.reset();
        if (fileRef.current) fileRef.current.value = '';
      }
    } catch {
      setIngestMsg('Network error during ingest.');
      setIngestState('error');
    }
  }

  function formatDate(s: string | null) {
    if (!s) return '—';
    return new Date(s).toLocaleDateString();
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827', margin: 0 }}>Documents</h1>
        <button
          onClick={() => setShowForm(v => !v)}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '6px',
            background: '#111827',
            color: '#fff',
            border: 'none',
            cursor: 'pointer',
            fontSize: '0.875rem',
            fontWeight: 600,
          }}
        >
          {showForm ? 'Cancel' : 'Ingest Document'}
        </button>
      </div>

      {/* Ingest Form */}
      {showForm && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.25rem', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, margin: '0 0 1rem', color: '#374151' }}>Ingest Document</h2>
          <form onSubmit={handleIngest} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxWidth: '440px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', color: '#374151', marginBottom: '0.25rem' }}>File</label>
              <input
                ref={fileRef}
                name="file"
                type="file"
                required
                style={{ fontSize: '0.875rem' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', color: '#374151', marginBottom: '0.25rem' }}>Access Level</label>
              <select name="access_level" defaultValue="1" style={{ padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.875rem' }}>
                <option value="1">1 — Basic</option>
                <option value="2">2 — Confidential</option>
                <option value="3">3 — Top Secret</option>
              </select>
            </div>
            {ingestMsg && (
              <div style={{
                padding: '0.5rem 0.75rem',
                borderRadius: '6px',
                fontSize: '0.875rem',
                background: ingestState === 'success' ? '#f0fdf4' : '#fef2f2',
                color: ingestState === 'success' ? '#166534' : '#b91c1c',
                border: `1px solid ${ingestState === 'success' ? '#bbf7d0' : '#fecaca'}`,
              }}>
                {ingestMsg}
              </div>
            )}
            <button
              type="submit"
              disabled={ingestState === 'submitting'}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                background: '#111827',
                color: '#fff',
                border: 'none',
                cursor: ingestState === 'submitting' ? 'not-allowed' : 'pointer',
                opacity: ingestState === 'submitting' ? 0.6 : 1,
                fontSize: '0.875rem',
                fontWeight: 600,
                alignSelf: 'flex-start',
              }}
            >
              {ingestState === 'submitting' ? 'Ingesting...' : 'Ingest'}
            </button>
          </form>
        </div>
      )}

      {/* Document Table */}
      {loadingDocs ? (
        <div style={{ color: '#6b7280', padding: '2rem', textAlign: 'center' }}>Loading...</div>
      ) : loadError ? (
        <div style={{ color: '#dc2626', padding: '2rem', textAlign: 'center' }}>{loadError}</div>
      ) : docs.length === 0 ? (
        <div style={{ color: '#9ca3af', padding: '2rem', textAlign: 'center' }}>No documents ingested yet.</div>
      ) : (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                {['Name', 'Type', 'Source', 'Access', 'Ingested', 'Updated'].map(h => (
                  <th key={h} style={{ padding: '0.6rem 0.75rem', textAlign: 'left', color: '#6b7280', fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {docs.map(d => (
                <tr key={d.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '0.6rem 0.75rem', color: '#111827', fontWeight: 500, maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.name}</td>
                  <td style={{ padding: '0.6rem 0.75rem', color: '#374151' }}>{d.type}</td>
                  <td style={{ padding: '0.6rem 0.75rem', color: '#374151' }}>{d.source}</td>
                  <td style={{ padding: '0.6rem 0.75rem' }}>
                    <span style={{
                      padding: '0.15rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      background: d.metadata?.access_level === 3 ? '#fef2f2' : d.metadata?.access_level === 2 ? '#eff6ff' : '#f0fdf4',
                      color: d.metadata?.access_level === 3 ? '#b91c1c' : d.metadata?.access_level === 2 ? '#1d4ed8' : '#166534',
                    }}>
                      {d.metadata?.access_level ?? 1}
                    </span>
                  </td>
                  <td style={{ padding: '0.6rem 0.75rem', color: '#6b7280' }}>{formatDate(d.created_at)}</td>
                  <td style={{ padding: '0.6rem 0.75rem', color: '#6b7280' }}>{formatDate(d.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {total > docs.length && (
            <div style={{ padding: '0.5rem 0.75rem', color: '#6b7280', fontSize: '0.8rem', borderTop: '1px solid #f3f4f6' }}>
              Showing {docs.length} of {total} documents
            </div>
          )}
        </div>
      )}
    </div>
  );
}
