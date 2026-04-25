import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor to add Auth Token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('gv_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response Interceptor to handle errors globally
client.interceptors.response.use((response) => {
  return response.data;
}, (error) => {
  if (error.response && error.response.status === 401) {
    localStorage.removeItem('gv_token');
    // window.location.href = '/login'; // Optional: Redirect on session expiry
  }
  return Promise.reject(error);
});

export default client;
