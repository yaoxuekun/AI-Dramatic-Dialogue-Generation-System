export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
  timestamp: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  userId: number;
  username: string;
  role: UserRole;
}

export type UserRole = 'ROOT' | 'ADMIN' | 'USER';

export interface UserProfileResponse {
  id: number;
  username: string;
  email: string;
  avatarPath?: string;
  role: UserRole;
  createdAt: string;
}

export interface UserUpdateRequest {
  username?: string;
  email?: string;
  avatarPath?: string;
}

export interface UserManageResponse {
  id: number;
  username: string;
  email: string;
  avatarPath?: string;
  role: UserRole;
  createdAt: string;
  updatedAt?: string;
}

export interface UserRoleUpdateRequest {
  role: UserRole;
}
