export function statusLabel(status, t) {
  const s = (status || 'open').toLowerCase().replace(/_/g, ' ');
  const map = {
    open: 'status.open',
    'in progress': 'status.inProgress',
    closed: 'status.closed',
    pending: 'status.pending',
  };
  return t(map[s] || 'status.open');
}

export function roleLabel(role, t) {
  const r = role?.toLowerCase();
  if (r === 'founder') return t('roles.founder');
  if (r === 'investor') return t('roles.investor');
  return role || '';
}

export function formatLocaleDate(ts, lang = 'en') {
  if (!ts) return '';
  try {
    const locale = lang === 'ar' ? 'ar-EG' : 'en-US';
    return new Date(ts).toLocaleDateString(locale, {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return '';
  }
}

export function fieldLabel(field, t) {
  const map = {
    Technology: 'fields.technology',
    Healthcare: 'fields.healthcare',
    Education: 'fields.education',
    Finance: 'fields.finance',
    Agriculture: 'fields.agriculture',
    Other: 'fields.other',
  };
  return t(map[field] || field);
}
