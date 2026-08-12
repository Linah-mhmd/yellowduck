import { Link } from 'react-router-dom';
import { useTranslation } from '../i18n/LanguageContext';

export default function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="site-footer">
      <div className="footer-grid">
        <div className="footer-brand">
          <div className="footer-logo">
            <span className="duck-icon">🦆</span>
            Yellow <span>Duck</span>
          </div>
          <p>{t('footer.tagline')}</p>
        </div>
        <div className="footer-links">
          <h4>{t('footer.platform')}</h4>
          <Link to="/projects">{t('nav.projects')}</Link>
          <Link to="/signup">{t('nav.signup')}</Link>
          <Link to="/funding-optimizer">{t('nav.fundingOptimizer')}</Link>
        </div>
        <div className="footer-links">
          <h4>{t('footer.company')}</h4>
          <a href="#about">{t('footer.about')}</a>
          <a href="#contact">{t('footer.contact')}</a>
          <a href="#privacy">{t('footer.privacy')}</a>
        </div>
        <div className="footer-links">
          <h4>{t('footer.connect')}</h4>
          <a href="https://linkedin.com" target="_blank" rel="noreferrer">LinkedIn</a>
          <a href="https://twitter.com" target="_blank" rel="noreferrer">Twitter</a>
          <a href="mailto:hello@yellowduck.com">hello@yellowduck.com</a>
        </div>
      </div>
      <div className="footer-bottom">
        <span>© 2026 Yellow Duck. {t('footer.rights')}</span>
        <span className="footer-tagline">{t('footer.slogan')}</span>
      </div>
    </footer>
  );
}
