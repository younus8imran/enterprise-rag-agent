import { useState, useEffect } from 'react';
import { useAuth } from '../App';

interface HistoryMessage {
  id: number;
  role: string;
  content: string;
  created_at: string | null;
}

interface Message {
  id?: number;
  role: 'user' | 'agent';
  text: string;
  confidence?: number;
  toolsUsed?: string[];
  error?: boolean;
  created_at?: string;
}

function classifyError(err: unknown): { message: string; category: 'network' | 'auth' | 'server' | 'unknown' } {
  if (err instanceof TypeError && err.message.includes('fetch')) {
    return { message: 'Cannot reach the server. Is the backend running?', category: 'network' };
  }
  if (err instanceof Error) {
    if (err.message.includes('401') || err.message.includes('Unauthorized')) {
      return { message: 'Session expired — please log in again.', category: 'auth' };
    }
    if (err.message.includes('500') || err.message.includes('502') || err.message.includes('503')) {
      return { message: `Server error (${err.message}). Try again shortly.`, category: 'server' };
    }
    return { message: err.message, category: 'unknown' };
  }
  return { message: String(err), category: 'unknown' };
}

export default function ChatPage() {
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Load persisted history from backend on mount / token change (cross-device)
  useEffect(() => {
    async function loadHistory() {
      const apiFetch = (window as any).__apiFetch;
      if (!apiFetch) return;
      try {
        const res = await apiFetch('/api/v1/chat/history');
        if (!res.ok) return;
        const data = await res.json();
        const history: Message[] = (data.messages || []).map((m: HistoryMessage) => ({
          id: m.id,
          role: m.role === 'agent' ? 'agent' : 'user',
          text: m.content,
          created_at: m.created_at || undefined,
        }));
        setMessages(history);
      } catch (e) {
        console.error('[ChatPage] history load error:', e);
      }
    }
    loadHistory();
  }, [token]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = { role: 'user', text: trimmed };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const apiFetch = (window as any).__apiFetch;
      if (!apiFetch) {
        throw new Error('API helper not initialized — reload the page.');
      }

      const res = await apiFetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed, stream: false }),
      });

      if (!res.ok) {
        const contentType = res.headers.get('content-type') || '';
        let detail = `Request failed (${res.status})`;
        if (contentType.includes('application/json')) {
          try {
            const d = await res.json();
            detail = d?.detail || detail;
          } catch { /* ignore */ }
        } else {
          try {
            const text = await res.text();
            detail = text.slice(0, 200) || detail;
          } catch { /* ignore */ }
        }
        setMessages(prev => [
          ...prev,
          { role: 'agent', text: detail, error: true },
        ]);
        setLoading(false);
        return;
      }

      const contentType = res.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        throw new Error(`Unexpected response type: ${contentType}`);
      }

      const data = await res.json();
      setMessages(prev => [
        ...prev,
        {
          role: 'agent',
          text: data.answer,
          confidence: data.confidence,
          toolsUsed: data.tools_used,
        },
      ]);
    } catch (err) {
      console.error('[ChatPage] uncaught error:', err);
      const { message } = classifyError(err);
      setMessages(prev => [
        ...prev,
        { role: 'agent', text: message, error: true },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 110px)', maxWidth: '800px' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827', margin: '0 0 1rem' }}>
        Chat
      </h1>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '1rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}
      >
        {messages.length === 0 && !loading && (
          <div style={{ color: '#9ca3af', textAlign: 'center', margin: 'auto', fontSize: '0.9rem' }}>
            Ask a question to get started.
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                maxWidth: '75%',
                padding: '0.6rem 0.85rem',
                borderRadius: '10px',
                fontSize: '0.9rem',
                lineHeight: 1.4,
                background: m.role === 'user' ? '#111827' : (m.error ? '#fef2f2' : '#f3f4f6'),
                color: m.role === 'user' ? '#fff' : (m.error ? '#b91c1c' : '#111827'),
                border: m.error ? '1px solid #fecaca' : '1px solid transparent',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {m.text}
              {m.role === 'agent' && !m.error && m.toolsUsed && m.toolsUsed.length > 0 && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#6b7280' }}>
                  Tools: {m.toolsUsed.join(', ')}
                  {typeof m.confidence === 'number' && ` · confidence: ${(m.confidence * 100).toFixed(0)}%`}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div
              style={{
                padding: '0.6rem 0.85rem',
                borderRadius: '10px',
                background: '#f3f4f6',
                fontSize: '0.9rem',
                color: '#6b7280',
                fontStyle: 'italic',
              }}
            >
              Agent is thinking...
            </div>
          </div>
        )}
      </div>

      <form
        onSubmit={handleSend}
        style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}
      >
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={loading}
          maxLength={2000}
          style={{
            flex: 1,
            padding: '0.6rem 0.85rem',
            borderRadius: '8px',
            border: '1px solid #d1d5db',
            fontSize: '0.95rem',
          }}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            padding: '0.6rem 1.25rem',
            borderRadius: '8px',
            background: '#111827',
            color: '#fff',
            border: 'none',
            fontWeight: 600,
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !input.trim() ? 0.6 : 1,
          }}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
