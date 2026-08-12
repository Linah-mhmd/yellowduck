import { useState, useRef, useEffect } from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n/LanguageContext';
import LanguageSwitcher from './LanguageSwitcher';
import VerifyEmailBanner from './VerifyEmailBanner';
import Footer from './Footer';

export default function Layout() {
  const { user, notifCount, logout, isFounder } = useAuth();
  const { t } = useTranslation();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [dashboardOpen, setDashboardOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const dropdownRef = useRef(null);
  const dashboardRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const handleClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setDropdownOpen(false);
      if (dashboardRef.current && !dashboardRef.current.contains(e.target)) setDashboardOpen(false);
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <>
      <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
        <div className="navbar-inner">
          <Link to="/" className="logo">
            <span className="duck-icon">🦆</span>
            Yellow <span>Duck</span>
          </Link>

          <button className="mobile-menu-toggle" type="button" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Menu">
            ☰
          </button>

          <ul className={`nav-links ${mobileOpen ? 'show' : ''}`}>
            <li><Link to="/" onClick={() => setMobileOpen(false)}>{t('nav.home')}</Link></li>
            <li><Link to="/projects" onClick={() => setMobileOpen(false)}>{t('nav.projects')}</Link></li>
            {isFounder && (
              <li className="dashboard-dropdown" ref={dashboardRef}>
                <a href="#" onClick={(e) => { e.preventDefault(); setDashboardOpen(!dashboardOpen); }}>
                  {t('nav.dashboard')} ▾
                </a>
                <ul className={`dashboard-menu ${dashboardOpen ? 'show' : ''}`}>
                  <li><Link to="/create-project">{t('nav.createProject')}</Link></li>
                  <li><Link to="/control-projects">{t('nav.manageProjects')}</Link></li>
                  <li><Link to="/funding-optimizer">{t('nav.fundingOptimizer')}</Link></li>
                  <li><Link to="/cash-flow">{t('nav.cashFlow')}</Link></li>
                </ul>
              </li>
            )}
            {user && (
              <li>
                <Link className="notif-link" to="/notifications" onClick={() => setMobileOpen(false)}>
                  🔔 {t('nav.notifications')}
                  {notifCount > 0 && <span className="notif-count">{notifCount}</span>}
                </Link>
              </li>
            )}
          </ul>

          <div className="nav-actions">
            <LanguageSwitcher />
            <div className="account-dropdown" ref={dropdownRef}>
              <div className="account-icon" onClick={() => setDropdownOpen(!dropdownOpen)}>
                {user?.name || t('nav.guest')}
              </div>
              <ul className={`dropdown-menu ${dropdownOpen ? 'show' : ''}`}>
                {user ? (
                  <>
                    <li><Link to="/portfolio/form" onClick={() => setDropdownOpen(false)}>{t('nav.createProfile')}</Link></li>
                    <li><Link to="/portfolio" onClick={() => setDropdownOpen(false)}>{t('nav.profile')}</Link></li>
                    <li><a href="#" onClick={(e) => { e.preventDefault(); handleLogout(); }}>{t('nav.logout')}</a></li>
                  </>
                ) : (
                  <>
                    <li><Link to="/login" onClick={() => setDropdownOpen(false)}>{t('nav.login')}</Link></li>
                    <li><Link to="/signup" onClick={() => setDropdownOpen(false)}>{t('nav.signup')}</Link></li>
                  </>
                )}
              </ul>
            </div>
          </div>
        </div>
      </nav>

      <VerifyEmailBanner />

      <main className="content">
        <Outlet />
      </main>

      <Footer />
    </>
  );
}
