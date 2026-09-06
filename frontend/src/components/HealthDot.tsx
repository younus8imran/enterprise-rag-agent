import { useEffect, useState } from 'react';

export function HealthDot() {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    function check() {
      fetch('/api/v1/health')
        .then(r => setOk(r.ok))
        .catch(() => setOk(false));
    }
    check();
    const id = setInterval(check, 30000);
    return () => clearInterval(id);
  }, []);

  return (
    <span
      title={ok === null ? 'Checking...' : ok ? 'Backend healthy' : 'Backend down'}
      style={{
        display: 'inline-block',
        width: 9,
        height: 9,
        borderRadius: '50%',
        background: ok === null ? '#9ca3af' : ok ? '#22c55e' : '#ef4444',
        marginLeft: 6,
        verticalAlign: 'middle',
        transition: 'background 0.3s',
      }}
    />
  );
}
