import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';

function BrandMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 34 24" width="34" height="24" aria-hidden="true">
      <circle cx="11" cy="12" r="9" className="brand-disc brand-disc-ehs" />
      <circle cx="21" cy="12" r="11" className="brand-disc brand-disc-opi" />
    </svg>
  );
}

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function Layout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  // Close mobile menu whenever location changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  return (
    <div className="site-shell">
      <a className="skip" href="#main">Skip to content</a>
      <ScrollToTop />
      <header className="site-header">
        <div className="wrap bar">
          <Link to="/" className="brand" aria-label="EngageIQ home">
            <BrandMark />
            <span>EngageIQ</span>
            <span className="brand-tag">PACE</span>
          </Link>

          <nav aria-label="Main" className={`nav ${mobileMenuOpen ? 'nav-open' : ''}`}>
            <NavLink to="/" end>Overview</NavLink>
            <NavLink to="/dashboard">Dashboard</NavLink>
            <NavLink to="/pace-score">PACE score</NavLink>
          </nav>

          <div className="header-actions">
            <ThemeToggle />
            <button
              type="button"
              className="mobile-menu-btn"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={mobileMenuOpen}
            >
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </header>

      <main id="main">
        <Outlet />
      </main>

      <footer className="site-footer">
        <div className="wrap footer-content">
          <div className="footer-lead">
            <div className="footer-brand">
              <BrandMark />
              <strong>EngageIQ</strong>
            </div>
            <p>PACE points to patterns that deserve a conversation. It never decides anything about a person.</p>
            <p className="muted">Built from work metadata only. No keystrokes, screenshots, webcam or message contents.</p>
          </div>
          <div className="footer-links">
            <div className="footer-col">
              <h4>Platform</h4>
              <Link to="/">Overview & Principles</Link>
              <Link to="/dashboard">Organization Dashboard</Link>
              <Link to="/pace-score">PACE Score Simulator</Link>
            </div>
            <div className="footer-col">
              <h4>Privacy First</h4>
              <span className="footer-badge">40% EHS · 60% OPI</span>
              <span className="footer-pill">Human-in-the-Loop</span>
            </div>
          </div>
        </div>
        <div className="wrap footer-bottom">
          <p className="fineprint">© EngageIQ · Privacy-Preserving Team Health & Performance Analytics</p>
        </div>
      </footer>
    </div>
  );
}
