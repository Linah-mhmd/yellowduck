import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.error || err.message || 'Request failed';
    return Promise.reject(new Error(message));
  }
);

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  signup: (data) => api.post('/auth/signup', data),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
  forgotPassword: (email, lang = 'en') => api.post('/auth/forgot-password', { email, lang }),
  resetPassword: (data) => api.post('/auth/reset-password', data),
  verifyEmail: (token) => api.get('/auth/verify-email', { params: { token } }),
  resendVerification: (lang = 'en') => api.post('/auth/resend-verification', { lang }),
};

export const homeAPI = {
  getData: () => api.get('/home'),
};

export const statsAPI = {
  get: () => api.get('/stats'),
};

export const pollAPI = {
  get: () => api.get('/poll'),
  submit: (answers) => api.post('/poll', answers),
};

export const projectsAPI = {
  list: (q, lang) => api.get('/projects', {
    params: {
      ...(q ? { q } : {}),
      ...(lang ? { lang } : {}),
    },
  }),
  get: (id) => api.get(`/projects/${id}`),
  create: (formData) => api.post('/projects', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  editInline: (id, data) => api.post(`/projects/${id}/edit`, data),
  delete: (id) => api.delete(`/projects/${id}`),
  invest: (id, data) => api.post(`/projects/${id}/invest`, data),
  feedback: {
    get: (id) => api.get(`/projects/${id}/feedback`),
    submit: (id, data) => api.post(`/projects/${id}/feedback`, data),
  },
};

export const controlAPI = {
  list: () => api.get('/control-projects'),
};

export const fundingAPI = {
  analyze: (data) => api.post('/funding-optimizer', data),
};

export const cashFlowAPI = {
  analyze: (formData) => api.post('/cash-flow', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  downloadPDF: (data) => api.post('/download-pdf', data, { responseType: 'blob' }),
};

export const portfolioAPI = {
  get: (email) => api.get('/portfolio', { params: email ? { user_email: email } : {} }),
  getForm: (id) => api.get(id ? `/portfolio/form/${id}` : '/portfolio/form'),
  save: (formData, id) => {
    const url = id ? `/portfolio/form/${id}` : '/portfolio/form';
    return api.post(url, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
};

export const notificationsAPI = {
  list: () => api.get('/notifications'),
  read: (id) => api.post(`/notifications/${id}/read`),
};

export const investmentAPI = {
  get: (id) => api.get(`/investments/${id}`),
  accept: (id) => api.post(`/investments/${id}/accept`),
  dismiss: (id) => api.post(`/investments/${id}/dismiss`),
};

export default api;
