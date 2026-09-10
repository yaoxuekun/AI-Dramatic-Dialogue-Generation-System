import request from './index';
import type {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  UserProfileResponse,
  UserManageResponse,
  UserRoleUpdateRequest,
  UserUpdateRequest,
} from '../types/auth';

function unwrap<T>(response: ApiResponse<T>): T {
  return response.data;
}

export async function register(data: RegisterRequest) {
  const response = await request.post<ApiResponse<UserProfileResponse>>('/api/auth/register', data);
  return unwrap(response.data);
}

export async function login(data: LoginRequest) {
  const response = await request.post<ApiResponse<LoginResponse>>('/api/auth/login', data);
  return unwrap(response.data);
}

export async function getProfile() {
  const response = await request.get<ApiResponse<UserProfileResponse>>('/api/user/profile');
  return unwrap(response.data);
}

export async function updateProfile(data: UserUpdateRequest) {
  const response = await request.put<ApiResponse<UserProfileResponse>>('/api/user/profile', data);
  return unwrap(response.data);
}

export async function getUsers() {
  const response = await request.get<ApiResponse<UserManageResponse[]>>('/api/users');
  return unwrap(response.data);
}

export async function updateUserRole(id: number, data: UserRoleUpdateRequest) {
  const response = await request.put<ApiResponse<UserManageResponse>>(`/api/users/${id}/role`, data);
  return unwrap(response.data);
}
