export function getPollSections(isFounder, t) {
  if (isFounder) {
    return [
      {
        section: t('poll.founder.sections.business'),
        items: [
          { name: 'q1', label: t('poll.founder.q1'), type: 'textarea', required: true },
          { name: 'q2', label: t('poll.founder.q2'), type: 'textarea', required: true },
        ],
      },
      {
        section: t('poll.founder.sections.market'),
        items: [
          { name: 'q3', label: t('poll.founder.q3'), type: 'text', required: true },
          { name: 'q4', label: t('poll.founder.q4'), type: 'text' },
          { name: 'q5', label: t('poll.founder.q5'), type: 'select', options: ['yes', 'no', 'in_progress'], required: true },
        ],
      },
      {
        section: t('poll.founder.sections.funding'),
        items: [
          { name: 'q6', label: t('poll.founder.q6'), type: 'select', options: ['idea', 'pre_seed', 'seed', 'series_a', 'growth'], required: true },
          { name: 'q7', label: t('poll.founder.q7'), type: 'text', required: true },
          { name: 'q8', label: t('poll.founder.q8'), type: 'textarea', required: true },
        ],
      },
      {
        section: t('poll.founder.sections.team'),
        items: [
          { name: 'q9', label: t('poll.founder.q9'), type: 'textarea', required: true },
          { name: 'q10', label: t('poll.founder.q10'), type: 'select', options: ['yes', 'no', 'planning'] },
        ],
      },
      {
        section: t('poll.founder.sections.vision'),
        items: [
          { name: 'q11', label: t('poll.founder.q11'), type: 'textarea', required: true },
          { name: 'q12', label: t('poll.founder.q12'), type: 'textarea', required: true },
          { name: 'q13', label: t('poll.founder.q13'), type: 'select', options: ['yes', 'no', 'depends'] },
        ],
      },
    ];
  }

  return [
    {
      section: t('poll.investor.sections.preferences'),
      items: [
        { name: 'q1', label: t('poll.investor.q1'), type: 'text', required: true },
        { name: 'q2', label: t('poll.investor.q2'), type: 'text', required: true },
        { name: 'q3', label: t('poll.investor.q3'), type: 'select', options: ['idea', 'pre_seed', 'seed', 'series_a', 'growth'], required: true },
        { name: 'q4', label: t('poll.investor.q4'), type: 'select', options: ['equity', 'debt', 'hybrid'], required: true },
        { name: 'q5', label: t('poll.investor.q5'), type: 'select', options: ['yes', 'no'], required: true },
        { name: 'q6', label: t('poll.investor.q6'), type: 'text', required: true },
        { name: 'q7', label: t('poll.investor.q7'), type: 'select', options: ['yes', 'no', 'maybe'], required: true },
        { name: 'q8', label: t('poll.investor.q8'), type: 'text', required: true },
        { name: 'q9', label: t('poll.investor.q9'), type: 'text', required: true },
        { name: 'q10', label: t('poll.investor.q10'), type: 'select', options: ['impact', 'profit', 'balanced'], required: true },
      ],
    },
  ];
}

export function pollOptionLabel(option, t) {
  const key = `poll.options.${option}`;
  const translated = t(key);
  return translated === key ? option.replace(/_/g, ' ') : translated;
}
