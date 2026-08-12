export function formatMoney(amount, currency = 'EGP') {
  const num = Number(amount) || 0;
  if (currency === 'EGP') {
    return `${num.toLocaleString('en-EG')} EGP`;
  }
  if (currency === 'USD') {
    return `$${num.toLocaleString('en-US')}`;
  }
  return `${num.toLocaleString()} ${currency}`;
}

export function formatStatNumber(value, lang = 'en') {
  const num = Number(value);
  if (Number.isNaN(num)) return '0';
  return new Intl.NumberFormat(lang === 'ar' ? 'ar-EG' : 'en-US').format(num);
}
