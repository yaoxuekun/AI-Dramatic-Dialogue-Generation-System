import axios, { type AxiosError } from 'axios';
import { ElMessage } from 'element-plus';
import router from '../router';
import type { ApiResponse } from '../types/auth';

const request = axios.create({
  baseURL: '',
  timeout: 15000,
});

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

request.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiResponse<unknown>>) => {
    const status = error.response?.status;
    const message = error.response?.data?.message || error.message || '请求失败';

    if (status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('userInfo');

      if (router.currentRoute.value.path !== '/login') {
        router.push({
          path: '/login',
          query: {
            redirect: router.currentRoute.value.fullPath,
          },
        });
      }

      ElMessage.warning('登录已过期，请重新登录');
      return Promise.reject(error);
    }

    ElMessage.error(message);
    return Promise.reject(error);
  },
);

export default request;
