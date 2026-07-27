import axios from 'axios';
import type { AxiosError } from 'axios';
import type { ApiError } from '@/types';
import { diagnostics } from '@/utils/diagnostics';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => config,
  (error) => {
    diagnostics.recordNetworkError(error.message);
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
      error.message ||
      'An unexpected error occurred';

    if (status >= 400 || !error.response) {
      diagnostics.recordApiFailure(endpoint, status, message);
    }

    return Promise.reject(new Error(message));
  }
);

export default api;
