import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL;

if (!BASE_URL) {
  const msg =
    '⚠️  VITE_API_URL is not set!\n' +
    'Add it to your Vercel project:\n' +
    'Settings → Environment Variables → VITE_API_URL = https://<your-render-app>.onrender.com/api/v1';
  console.error(msg);
}

const API_BASE = BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach access token to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401, try refresh once
api.interceptors.response.use(
  r => r,
  async error => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const res = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh });
          localStorage.setItem('access_token', res.data.access_token);
          original.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(original);
        } catch {
          localStorage.clear();
          window.location.href = '/';
        }
      }
    }
    return Promise.reject(error);
  }
);

// ── Helper ─────────────────────────────────────────────────
const unwrap = res => res.data;
const errMsg = e => e.response?.data?.detail || e.message || 'Something went wrong';

export { errMsg };

// ── Auth ───────────────────────────────────────────────────
export const authAPI = {
  register: (username, email, password) => api.post('/auth/register', { username, email, password }).then(unwrap),
  login: (email, password) => api.post('/auth/login', { email, password }).then(unwrap),
  logout: () => api.post('/auth/logout').then(unwrap),
  me: () => api.get('/auth/me').then(unwrap),
  refresh: (token) => api.post('/auth/refresh', { refresh_token: token }).then(unwrap),
};

// ── Users ──────────────────────────────────────────────────
export const usersAPI = {
  updateProfile: (data) => api.put('/users/me', data).then(unwrap),
  changePassword: (current_password, new_password) =>
    api.put('/users/me/password', { current_password, new_password }).then(unwrap),
  uploadAvatar: (file) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/users/me/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(unwrap);
  },
};

// ── Rooms ──────────────────────────────────────────────────
export const roomsAPI = {
  list: (params) => api.get('/rooms', { params }).then(unwrap),
  get: (id) => api.get(`/rooms/${id}`).then(unwrap),
  create: (data) => api.post('/rooms', data).then(unwrap),
  update: (id, data) => api.put(`/rooms/${id}`, data).then(unwrap),
  delete: (id) => api.delete(`/rooms/${id}`).then(unwrap),
  join: (id) => api.post(`/rooms/${id}/join`).then(unwrap),
  leave: (id) => api.post(`/rooms/${id}/leave`).then(unwrap),
  members: (id) => api.get(`/rooms/${id}/members`).then(unwrap),
  removeMember: (roomId, userId) => api.delete(`/rooms/${roomId}/members/${userId}`).then(unwrap),
  updateRole: (roomId, userId, role) => api.put(`/rooms/${roomId}/members/${userId}/role`, { role }).then(unwrap),
  joinRequests: (id, status) => api.get(`/rooms/${id}/requests`, { params: status ? { status } : {} }).then(unwrap),
  handleRequest: (roomId, reqId, status) => api.put(`/rooms/${roomId}/requests/${reqId}`, { status }).then(unwrap),
  myRequests: () => api.get('/rooms/me/requests').then(unwrap),
};

// ── Messages ───────────────────────────────────────────────
export const messagesAPI = {
  list: (roomId, params) => api.get(`/rooms/${roomId}/messages`, { params }).then(unwrap),
  send: (roomId, content) => api.post(`/rooms/${roomId}/messages`, { content }).then(unwrap),
  delete: (roomId, messageId) => api.delete(`/rooms/${roomId}/messages/${messageId}`).then(unwrap),
};

// ── Files ──────────────────────────────────────────────────
export const filesAPI = {
  list: (roomId) => api.get(`/rooms/${roomId}/files`).then(unwrap),
  upload: (roomId, file) => {
    const form = new FormData();
    form.append('file', file);
    return api.post(`/rooms/${roomId}/files`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(unwrap);
  },
  download: (roomId, fileId) =>
    api.get(`/rooms/${roomId}/files/${fileId}/download`, { responseType: 'blob' }),
  delete: (roomId, fileId) => api.delete(`/rooms/${roomId}/files/${fileId}`).then(unwrap),
};

export default api;
