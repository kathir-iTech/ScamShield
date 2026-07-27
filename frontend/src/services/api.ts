import axios from 'axios';
import type { AxiosError } from 'axios';
import type { ApiError } from '@/types';
import { diagnostics } from '@/utils/diagnostics';
import { monitor } from '@/services/monitoring';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    if (!navigator.onLine) {
      return Promise.reject(new Error('No internet connection. Please check your network and try again.'));
    }
    return config;
  },
  (error) => {
    diagnostics.recordNetworkError(error.message);
    monitor.error('Request error', { message: error.message });
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const status = error.response?.status || 0;
    const endpoint = error.config?.url || 'unknown';
    const message =
      error.response?.data?.detail ||
      (status === 429 ? 'Too many requests. Please wait a moment and try again.' : undefined) ||
      (status === 0 ? 'Unable to reach the server. Please check your connection.' : undefined) ||
      (status >= 500 ? 'The server encountered an error. Please try again later.' : undefined) ||
      error.message ||
      'An unexpected error occurred';

    if (status >= 400 || !error.response) {
      diagnostics.recordApiFailure(endpoint, status, message);
      monitor.error('API failure', { endpoint, status, message });
    }

    return Promise.reject(new Error(message));
  }
);

export function createCancelToken() {
  return axios.CancelToken.source();
}

export default api;
