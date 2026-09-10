import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import * as authApi from '../api/authApi';
import type { RegisterRequest, UserManageResponse, UserProfileResponse, UserRole, UserUpdateRequest } from '../types/auth';

function readStoredUser() {
  const rawUser = localStorage.getItem('userInfo');
  if (!rawUser) {
    return null;
  }

  try {
    return JSON.parse(rawUser) as UserProfileResponse;
  } catch {
    localStorage.removeItem('userInfo');
    return null;
  }
}

function isUnauthorized(error: unknown) {
  return (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    (error as { response?: { status?: number } }).response?.status === 401
  );
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '');
  const userInfo = ref<UserProfileResponse | null>(readStoredUser());
  const isLoggedIn = computed(() => Boolean(token.value));
  const role = computed<UserRole>(() => userInfo.value?.role || 'USER');
  const isRoot = computed(() => role.value === 'ROOT');
  const canManageSystemConfig = computed(() => role.value === 'ROOT' || role.value === 'ADMIN');
  const users = ref<UserManageResponse[]>([]);
  const isUserLoading = ref(false);

  function persistToken(nextToken: string) {
    token.value = nextToken;
    localStorage.setItem('token', nextToken);
  }

  function persistUser(nextUser: UserProfileResponse | null) {
    userInfo.value = nextUser;
    if (nextUser) {
      localStorage.setItem('userInfo', JSON.stringify(nextUser));
      return;
    }
    localStorage.removeItem('userInfo');
  }

  async function login(username: string, password: string) {
    const loginResult = await authApi.login({ username, password });
    persistToken(loginResult.token);

    persistUser({
      id: loginResult.userId,
      username: loginResult.username,
      email: '',
      role: loginResult.role || 'USER',
      createdAt: '',
    });

    try {
      const profile = await authApi.getProfile();
      persistUser(profile);
    } catch (error) {
      if (isUnauthorized(error)) {
        logout();
        throw error;
      }
    }

    return loginResult;
  }

  async function register(payload: RegisterRequest) {
    return authApi.register(payload);
  }

  async function fetchProfile() {
    const profile = await authApi.getProfile();
    persistUser(profile);
    return profile;
  }

  async function updateProfile(payload: UserUpdateRequest) {
    const profile = await authApi.updateProfile(payload);
    persistUser(profile);
    return profile;
  }

  async function fetchUsers() {
    isUserLoading.value = true;
    try {
      users.value = await authApi.getUsers();
      return users.value;
    } finally {
      isUserLoading.value = false;
    }
  }

  async function updateUserRole(id: number, nextRole: UserRole) {
    const updated = await authApi.updateUserRole(id, { role: nextRole });
    users.value = users.value.map((user) => (user.id === updated.id ? updated : user));
    return updated;
  }

  function logout() {
    token.value = '';
    userInfo.value = null;
    localStorage.removeItem('token');
    localStorage.removeItem('userInfo');
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    role,
    isRoot,
    canManageSystemConfig,
    users,
    isUserLoading,
    login,
    register,
    fetchProfile,
    updateProfile,
    fetchUsers,
    updateUserRole,
    logout,
  };
});
