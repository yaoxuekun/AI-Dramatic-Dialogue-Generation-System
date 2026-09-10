import request from './index';
import type { ApiResponse } from '../types/auth';
import type { FileUploadResponse } from '../types/file';

function unwrap<T>(response: ApiResponse<T>): T {
  return response.data;
}

export async function uploadFile(file: File, category = 'resources') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);

  const response = await request.post<ApiResponse<FileUploadResponse>>('/api/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return unwrap(response.data);
}

export async function loadFileBlob(filePathOrUrl: string) {
  const url = normalizeFileUrl(filePathOrUrl);
  const response = await request.get<Blob>(url, {
    responseType: 'blob',
  });
  return response.data;
}

function normalizeFileUrl(filePathOrUrl: string) {
  if (filePathOrUrl.startsWith('/api/files/')) {
    return filePathOrUrl;
  }

  return `/api/files/${filePathOrUrl.replace(/^\/+/, '')}`;
}
