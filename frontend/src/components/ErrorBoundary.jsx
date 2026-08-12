import { Component } from 'react';
import { Link } from 'react-router-dom';
import { LanguageContext } from '../i18n/LanguageContext';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <LanguageContext.Consumer>
          {({ t }) => (
            <div className="container not-found-page">
              <h1>{t('common.error')}</h1>
              <p>{this.state.error?.message || t('common.unexpectedError')}</p>
              <Link to="/" className="btn btn-primary">{t('common.goHome')}</Link>
            </div>
          )}
        </LanguageContext.Consumer>
      );
    }
    return this.props.children;
  }
}
