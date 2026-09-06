import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../App';

const TOOLS = [
  { key: 'rag', label: 'RAG' },
  { key: 'sql', label: 'SQL' },
  { key: 'web', label: 'Web' },
];

export default function ResearchPage() {
  const { token } = useAuth();
  const [question, setQuestion] = useState('');
  const [selected, setSelected] = useState<string[]>(['rag', 'sql', 'web']);
  const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle');
  const [runId, setRunId] = useState<string | null>(null);
  const [progress, setProgress] = useState('Starting...');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const [history, setHistory] = useState<any[]>([]);

  // Load persisted research history (same pattern as ChatPage)
  useEffect(() => {
    async function loadHistory() {
      try {
        const res = await (window as any).__apiFetch('/api/v1/research/history');
        if (!res.ok) return;
        const data = await res.json();
        setHistory(Array.isArray(data) ? data : []);
      } catch (e) {
        console.error('[Research] history load error', e);
      }
    }
    loadHistory();
  }, [token]);

  const toggleTool = (k: string) => {
    setSelected((prev) =>
      prev.includes(k) ? prev.filter((t) => t !== k) : [...prev, k]
    );
  };

  const clearPoll = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => clearPoll();
  }, [clearPoll]);

  async function handleRun(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || selected.length === 0) return;
    setStatus('running');
    setRunId(null);
    setResult(null);
    setError('');
    setProgress('Starting...');

    try {
      const res = await (window as any).__apiFetch('/api/v1/research', {
        method: 'POST',
        body: JSON.stringify({
          question: q,
          tools: selected,
          stream: true,
        }),
      });
      const contentType = res.headers.get('content-type') || '';
      if (!res.ok) {
        let msg = `Request failed (${res.status})`;
        try {
          if (contentType.includes('application/json')) {
            const d = await res.json();
            msg = d.detail || msg;
          } else {
            const text = await res.text();
            msg = text.slice(0, 200) || msg;
          }
        } catch { /* ignore parse failure */ }
        setError(msg);
        setStatus('failed');
        return;
      }
      // For stream=response: read SSE chunks, extract run_id for polling
      if (contentType.includes('text/event-stream')) {
        const reader = res.body?.getReader?.();
        if (reader) {
          setStatus('running');
          let sseRunId: string | null = null;
          const decoder = new TextDecoder();
          let buffer = '';
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const payload = JSON.parse(line.slice(6));
                  if (payload.run_id) sseRunId = payload.run_id;
                  if (payload.status) setProgress(payload.message || payload.status);
                  if (payload.result) {
                    setStatus('completed');
                    setResult(payload.result);
                  }
                  if (line.startsWith('event: done')) {
                    // SSE stream ended — if no result yet, fall through to polling
                    break;
                  }
                } catch { /* ignore malformed chunk */ }
              }
            }
          }
          // If we got a run_id but no result streamed, poll for it
          if (sseRunId && status !== 'completed') {
            const timer = setInterval(async () => {
              try {
                const sRes = await (window as any).__apiFetch(`/api/v1/runs/${sseRunId}`);
                if (!sRes.ok) return;
                const s = await sRes.json();
                setProgress(s.progress ?? s.status ?? 'Working...');
                if (s.status === 'completed') {
                  clearInterval(timer);
                  setStatus('completed');
                  setResult(s.result || {});
                } else if (s.status === 'failed') {
                  clearInterval(timer);
                  setStatus('failed');
                  setError(s.error || 'Run failed.');
                }
              } catch { /* transient polling errors ignored */ }
            }, 2000);
            return;
          }
          return;
        }
      }
      // Non-streaming fallback
      let data: any = {};
      try {
        data = await res.json();
      } catch {
        setError('Invalid JSON from server (possible 429 / rate limit)');
        setStatus('failed');
        return;
      }
      setRunId(data.run_id);
      // Poll /runs/{run_id} (active path, not legacy — backend writes status here)
      timerRef.current = setInterval(async () => {
        try {
          const sRes = await (window as any).__apiFetch(`/api/v1/runs/${data.run_id}`);
          if (!sRes.ok) return;
          const s = await sRes.json();
          setProgress(s.progress ?? s.status ?? 'Working...');
          if (s.status === 'completed') {
            clearPoll();
            setStatus('completed');
            setResult(s.result || data);
          } else if (s.status === 'failed') {
            clearPoll();
            setStatus('failed');
            setError(s.error || 'Run failed.');
          }
        } catch {
          // Transient polling errors ignored; keep polling
        }
      }, 2000);
    } catch (err: any) {
      setStatus('failed');
      setError(err?.message || 'Network error starting research.');
    }
  }

  const toolLabels = (src: Record<string, number>) =>
    Object.entries(src || {})
      .map(([k, v]) => `${k}: ${v}`)
      .join(', ');

  return (
    <div style={{ maxWidth: '800px' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827', margin: '0 0 1rem' }}>
        Research
      </h1>

      <form onSubmit={handleRun} style={{ marginBottom: '1.5rem' }}>
        <label
          htmlFor="research-q"
          style={{
            display: 'block',
            fontSize: '0.875rem',
            color: '#374151',
            fontWeight: 500,
            marginBottom: '0.4rem',
          }}
        >
          Research Question
        </label>
        <textarea
          id="research-q"
          rows={3}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Enter your research question..."
          required
          maxLength={2000}
          disabled={status === 'running'}
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

        <div style={{ marginTop: '0.75rem', marginBottom: '0.75rem' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#4b5563', marginBottom: '0.35rem' }}>
            Tools (select one or more)
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {TOOLS.map((t) => {
              const active = selected.includes(t.key);
              return (
                <button
                  key={t.key}
                  type="button"
                  onClick={() => toggleTool(t.key)}
                  aria-pressed={active}
                  style={{
                    padding: '0.35rem 0.75rem',
                    borderRadius: '999px',
                    border: '1px solid',
                    borderColor: active ? '#111827' : '#d1d5db',
                    background: active ? '#111827' : '#fff',
                    color: active ? '#fff' : '#374151',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  title={t.key}
                >
                  {t.label}
                </button>
              );
            })}
          </div>
        </div>

        <button
          type="submit"
          disabled={status === 'running' || !question.trim() || selected.length === 0}
          style={{
            marginTop: '0.25rem',
            padding: '0.5rem 1.25rem',
            borderRadius: '8px',
            background: '#111827',
            color: '#fff',
            border: 'none',
            cursor:
              status === 'running' || !question.trim() || selected.length === 0
                ? 'not-allowed'
                : 'pointer',
            opacity:
              status === 'running' || !question.trim() || selected.length === 0 ? 0.6 : 1,
            fontWeight: 600,
            fontSize: '0.875rem',
          }}
        >
          {status === 'running' ? 'Running Research…' : 'Run Research'}
        </button>
      </form>

      {/* Loading / typing indicator */}
      {status === 'running' && (
        <div
          style={{
            background: '#f9fafb',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: '1rem',
            maxWidth: '600px',
            marginBottom: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                display: 'inline-block',
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#111827',
                animation: 'pulse 1.2s infinite',
              }}
            />
            <div style={{ color: '#374151', fontWeight: 600, fontSize: '0.95rem' }}>
              Research in progress
            </div>
            {runId && (
              <div style={{ color: '#9ca3af', fontSize: '0.8rem', marginLeft: 'auto' }}>
                run {runId.slice(0, 8)}
              </div>
            )}
          </div>
          <div style={{ color: '#6b7280', fontSize: '0.875rem', marginTop: '0.35rem' }}>
            {progress || 'Working...'}
          </div>
          <style>{`
            @keyframes pulse {
              0% { opacity: 1; }
              50% { opacity: 0.3; }
              100% { opacity: 1; }
            }
          `}</style>
        </div>
      )}

      {/* Completed */}
      {status === 'completed' && result && (
        <div
          style={{
            background: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: '1.25rem',
            maxWidth: '800px',
          }}
        >
          <h2 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '0 0 0.25rem' }}>
            {question}
          </h2>
          <div style={{ color: '#6b7280', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
            Run{' '}
            <code
              style={{
                background: '#f3f4f6',
                padding: '0.1rem 0.3rem',
                borderRadius: '4px',
                fontSize: '0.8rem',
              }}
            >
              {runId?.slice(0, 8) || result?.run_id?.slice(0, 8)}
            </code>
            {selected.length > 0 && (
              <span style={{ marginLeft: '0.5rem', fontStyle: 'italic', color: '#6b7280' }}>
                (tools: {selected.join(', ')})
              </span>
            )}
          </div>

          <div style={{ lineHeight: 1.6, color: '#111827', whiteSpace: 'pre-wrap' }}>
            {result.answer || result?.result?.answer}
          </div>

          {/* Tool contributor indicator if source info available */}
          {result.sources_consulted && (
            <div
              style={{
                marginTop: '1rem',
                borderTop: '1px solid #e5e7eb',
                paddingTop: '0.75rem',
                color: '#374151',
                fontSize: '0.875rem',
              }}
            >
              <div>
                <strong>Sources consulted:</strong>{' '}
                {toolLabels(result.sources_consulted)}
              </div>
              {result.confidence !== undefined && (
                <div style={{ marginTop: '0.25rem' }}>
                  Confidence: {Math.round(result.confidence * 100)}%
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Research History */}
      {history.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#374151', margin: '0 0 0.75rem' }}>
            Past Research ({history.length})
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {history.slice(0, 10).map((run) => (
              <details
                key={run.run_id}
                style={{
                  background: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                }}
              >
                <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem', color: '#374151', listStyle: 'none' }}>
                  {run.question || 'Research run'} — {run.status}
                  {run.created_at && (
                    <span style={{ fontWeight: 400, color: '#9ca3af', marginLeft: '0.5rem', fontSize: '0.8rem' }}>
                      {new Date(run.created_at).toLocaleDateString()}
                    </span>
                  )}
                </summary>
                <div style={{ marginTop: '0.75rem', fontSize: '0.875rem', color: '#6b7280', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                  {run.answer || 'No answer recorded.'}
                </div>
              </details>
            ))}
          </div>
        </div>
      )}

      {/* Failed */}
      {status === 'failed' && error && (
        <div
          style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '1rem',
            color: '#b91c1c',
            maxWidth: '600px',
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
}
