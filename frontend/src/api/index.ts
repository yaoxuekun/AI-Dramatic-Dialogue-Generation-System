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
  (error: AxiosError<any>) => {
    const status = error.response?.status;
    const data = error.response?.data;
    // FastAPI 的 HTTPException 走 {"detail": "..."}，
    // 统一响应走 {"code","message","data"}，两边都要读得到
    const detail = typeof data?.detail === 'string'
      ? data.detail
      : Array.isArray(data?.detail)
        ? data.detail.map((item: any) => item?.msg).filter(Boolean).join('；')
        : undefined;
    const message = data?.message || detail || error.message || '请求失败';

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
