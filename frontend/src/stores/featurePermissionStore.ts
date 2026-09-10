import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import * as featurePermissionApi from '../api/featurePermissionApi';
import type { UserRole } from '../types/auth';
import type { FeaturePermission } from '../types/featurePermission';

export const useFeaturePermissionStore = defineStore('featurePermission', () => {
  const permissions = ref<FeaturePermission[]>([]);
  const allowedFeatureKeys = ref<string[] | null>(null);
  const isLoading = ref(false);
  const isMyPermissionsLoading = ref(false);

  const permissionGroups = computed(() => {
    const groups = new Map<string, FeaturePermission[]>();
    for (const permission of permissions.value) {
      const category = permission.category || '未分类';
      groups.set(category, [...(groups.get(category) || []), permission]);
    }
    return Array.from(groups.entries()).map(([category, items]) => ({ category, items }));
  });

  async function fetchPermissions() {
    isLoading.value = true;
    try {
      permissions.value = await featurePermissionApi.getFeaturePermissions();
      return permissions.value;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchMyPermissions() {
    isMyPermissionsLoading.value = true;
    try {
      allowedFeatureKeys.value = await featurePermissionApi.getMyFeaturePermissions();
      return allowedFeatureKeys.value;
    } finally {
      isMyPermissionsLoading.value = false;
    }
  }

  async function updatePermission(id: number, allowedRoles: UserRole[], enabled: boolean) {
    const updated = await featurePermissionApi.updateFeaturePermission(id, { allowedRoles, enabled });
    permissions.value = permissions.value.map((item) => (item.id === updated.id ? updated : item));
    return updated;
  }

  function hasFeature(featureKey: string, fallback = false) {
    if (allowedFeatureKeys.value === null) {
      return fallback;
    }
    return allowedFeatureKeys.value.includes(featureKey);
  }

  function resetMyPermissions() {
    allowedFeatureKeys.value = null;
  }

  return {
    permissions,
    permissionGroups,
    allowedFeatureKeys,
    isLoading,
    isMyPermissionsLoading,
    fetchPermissions,
    fetchMyPermissions,
    updatePermission,
    hasFeature,
    resetMyPermissions,
  };
});
