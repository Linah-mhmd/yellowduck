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

/** POST multipart/form-data — omit Content-Type so axios adds the boundary. */
function postFormData(url, formData, options = {}) {
  return api.post(url, formData, {
    timeout: 120000,
    ...options,
    transformRequest: [(data, headers) => {
      delete headers['Content-Type'];
      return data;
    }],
  });
}

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
    timeout: 60000,
  }),
  get: (id) => api.get(`/projects/${id}`),
  create: (formData) => postFormData('/projects', formData),
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
  downloadPDF: (data) => api.post('/funding-optimizer/pdf', data, { responseType: 'blob' }),
};

export const cashFlowAPI = {
  analyze: async (formData) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 300000);
    let res;
    try {
      res = await fetch('/api/cash-flow', {
        method: 'POST',
        body: formData,
        credentials: 'include',
        signal: controller.signal,
      });
    } catch (err) {
      if (err.name === 'AbortError') {
        throw new Error('Analysis timed out. Please try again or use manual entry.');
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }

    const text = await res.text();
    if (!text) {
      throw new Error(
        res.ok
          ? 'Empty server response. Please try again.'
          : `Server error (${res.status}). The analysis may have timed out — wait and retry.`,
      );
    }

    let data = {};
    try {
      data = JSON.parse(text);
    } catch {
      const snippet = text.replace(/\s+/g, ' ').slice(0, 120);
      throw new Error(
        `Server returned a non-JSON response (${res.status}). ${snippet.startsWith('<') ? 'Connection may have timed out — please retry.' : snippet}`,
      );
    }

    if (!res.ok) {
      throw new Error(data.error || `Request failed (${res.status})`);
    }
    return { data };
  },
  downloadPDF: (data) => api.post('/download-pdf', data, { responseType: 'blob' }),
};

export const portfolioAPI = {
  get: (email) => api.get('/portfolio', { params: email ? { user_email: email } : {} }),
  getForm: (id) => api.get(id ? `/portfolio/form/${id}` : '/portfolio/form'),
  save: (formData, id) => {
    const url = id ? `/portfolio/form/${id}` : '/portfolio/form';
    return postFormData(url, formData);
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
