import { Link } from 'react-router-dom';
import { USING_SAMPLE_DATA } from '../api/client';

export function Loading() {
  return (
    <div className="wrap page" role="status" aria-live="polite">
      <p className="muted">Loading scores</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="wrap page">
      <div className="notice notice-error" role="alert">
        <h2>We could not load this page</h2>
        <p>{message}</p>
        <div className="actions">
          {onRetry && <button className="btn" onClick={onRetry}>Try again</button>}
          <Link className="btn btn-ghost" to="/dashboard">Back to the dashboard</Link>
        </div>
      </div>
    </div>
  );
}

export function SampleNotice() {
  if (!USING_SAMPLE_DATA) return null;
  return (
    <p className="sample-note">
      You are looking at sample data. Set <code>VITE_API_URL</code> to show real scores.
    </p>
  );
}

export function ComingSoon({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ position: 'relative' }}>
      <div style={{ filter: 'blur(4px)', opacity: 0.6, pointerEvents: 'none' }}>
        {children}
      </div>
      <div style={{ 
        position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, 
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10
      }}>
        <div style={{ 
          background: 'var(--wash)', padding: '0.75rem 1.5rem', 
          borderRadius: 'var(--r-md)', fontWeight: 600, color: 'var(--ink)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)', border: '1px solid var(--rule)'
        }}>
          Coming Soon
        </div>
      </div>
    </div>
  );
}

export function Breadcrumb({ items }: { items: { label: string; to?: string }[] }) {
  return (
    <nav className="crumbs" aria-label="Breadcrumb">
      <ol>
        {items.map((it, i) => (
          <li key={it.label}>
            {it.to ? <Link to={it.to}>{it.label}</Link> : <span aria-current="page">{it.label}</span>}
            {i < items.length - 1 && <span className="crumb-sep" aria-hidden="true">/</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
}
