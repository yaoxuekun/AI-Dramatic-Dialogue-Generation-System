import request from './index';
import type { ApiResponse } from '../types/auth';
import type { FeaturePermission, FeaturePermissionUpdateRequest } from '../types/featurePermission';

function unwrap<T>(response: ApiResponse<T>): T {
  return response.data;
}

export async function getFeaturePermissions() {
  const response = await request.get<ApiResponse<FeaturePermission[]>>('/api/feature-permissions');
  return unwrap(response.data);
}

export async function updateFeaturePermission(id: number, data: FeaturePermissionUpdateRequest) {
  const response = await request.put<ApiResponse<FeaturePermission>>(`/api/feature-permissions/${id}`, data);
  return unwrap(response.data);
}

export async function getMyFeaturePermissions() {
  const response = await request.get<ApiResponse<string[]>>('/api/feature-permissions/me');
  return unwrap(response.data);
}
