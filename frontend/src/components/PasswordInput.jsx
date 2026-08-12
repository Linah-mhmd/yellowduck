import { useState } from 'react';
import { useTranslation } from '../i18n/LanguageContext';
import { EyeIcon, EyeOffIcon } from './Icons';

export default function PasswordInput({ value, onChange, placeholder, required, id }) {
  const [visible, setVisible] = useState(false);
  const { t } = useTranslation();

  return (
    <div className="password-field">
      <input
        id={id}
        type={visible ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
      />
      <button
        type="button"
        className="password-toggle"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? t('auth.hidePassword') : t('auth.showPassword')}
      >
        {visible ? <EyeOffIcon /> : <EyeIcon />}
      </button>
    </div>
  );
}
