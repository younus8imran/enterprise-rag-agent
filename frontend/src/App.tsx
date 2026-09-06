import React, { createContext, useContext, useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import DocumentsPage from './pages/DocumentsPage';
import ResearchPage from './pages/ResearchPage';
import SqlPage from './pages/SqlPage';
import PlaceholderPage from './pages/PlaceholderPage';
import Shell from './components/Shell';

// ─── Types ────────────────────────────────────────────────────────────────────

interface User {
  user_id: number;
  username: string;
  role: string;
  tenant_id: number;
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

// ─── API helper ───────────────────────────────────────────────────────────────

const API_BASE = '/api/v1';

async function fetchMe(token: string): Promise<User | null> {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    return (await res.json()) as User;
  } catch {
    return null;
  }
}

// ─── Context ──────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

// ─── Provider ────────────────────────────────────────────────────────────────

const TOKEN_KEY = 'auth_token';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount: if a token exists, validate it via /me
  useEffect(() => {
    async function bootstrap() {
      const stored = localStorage.getItem(TOKEN_KEY);
      if (!stored) {
        setLoading(false);
        return;
      }
      const u = await fetchMe(stored);
      if (u) {
        setToken(stored);
        setUser(u);
      } else {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      }
      setLoading(false);
    }
    bootstrap();
  }, []);

  async function login(newToken: string): Promise<void> {
    const u = await fetchMe(newToken);
    if (!u) throw new Error('Invalid token received from server');
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
    setUser(u);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }

  // Global 401 handler — wraps fetch so any API call that returns 401 redirects to /login
  function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const token = localStorage.getItem(TOKEN_KEY);
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    };
    return fetch(url, { ...options, headers }).then(async res => {
      if (res.status === 401) {
        logout();
        window.location.href = '/login';
        throw new Error('Unauthorized');
      }
      return res;
    });
  }

  // Expose globally so pages can use apiFetch instead of raw fetch
  (window as any).__apiFetch = apiFetch;

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Protected route wrapper ───────────────────────────────────────────────────

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Shell />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/sql" element={<SqlPage />} />
          </Route>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
