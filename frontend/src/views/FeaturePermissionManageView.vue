<template>
  <section class="feature-permission-page">
    <header class="manager-hero">
      <div>
        <p class="eyebrow">Feature Access</p>
        <h1>功能权限管理</h1>
        <span>按功能操作设置允许使用的角色。root 始终拥有全部权限，用来避免系统被误锁。</span>
      </div>
      <el-button type="primary" size="large" :loading="featurePermissionStore.isLoading" @click="loadPermissions">
        刷新权限
      </el-button>
    </header>

    <div v-loading="featurePermissionStore.isLoading" class="permission-groups">
      <el-card
        v-for="group in featurePermissionStore.permissionGroups"
        :key="group.category"
        class="permission-card"
        shadow="never"
      >
        <template #header>
          <div class="card-header">
            <strong>{{ group.category }}</strong>
            <span>{{ group.items.length }} 个操作</span>
          </div>
        </template>

        <el-table :data="group.items" row-key="id" class="permission-table">
          <el-table-column prop="featureName" label="功能" min-width="160">
            <template #default="{ row }">
              <div class="feature-name">
                <strong>{{ row.featureName }}</strong>
                <small>{{ row.featureKey }}</small>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="说明" min-width="260" />
          <el-table-column label="允许角色" min-width="260">
            <template #default="{ row }">
              <el-checkbox-group
                :model-value="row.allowedRoles"
                :disabled="savingId === row.id"
                @change="handleRoleChange(row, $event)"
              >
                <el-checkbox label="ROOT" disabled>root</el-checkbox>
                <el-checkbox label="ADMIN">admin</el-checkbox>
                <el-checkbox label="USER">普通用户</el-checkbox>
              </el-checkbox-group>
            </template>
          </el-table-column>
          <el-table-column label="启用" width="110">
            <template #default="{ row }">
              <el-switch
                :model-value="row.enabled"
                :disabled="row.featureKey === 'featurePermission.manage'"
                :loading="savingId === row.id"
                @change="handleEnabledChange(row, Boolean($event))"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useFeaturePermissionStore } from '../stores/featurePermissionStore';
import type { UserRole } from '../types/auth';
import type { FeaturePermission } from '../types/featurePermission';

const featurePermissionStore = useFeaturePermissionStore();
const savingId = ref<number | null>(null);

onMounted(loadPermissions);

async function loadPermissions() {
  await featurePermissionStore.fetchPermissions();
}

async function handleRoleChange(permission: FeaturePermission, roles: unknown) {
  const nextRoles = normalizeRoles(roles);
  await savePermission(permission, nextRoles, permission.enabled);
}

async function handleEnabledChange(permission: FeaturePermission, enabled: boolean) {
  await savePermission(permission, permission.allowedRoles, enabled);
}

async function savePermission(permission: FeaturePermission, allowedRoles: UserRole[], enabled: boolean) {
  savingId.value = permission.id;
  try {
    await featurePermissionStore.updatePermission(permission.id, allowedRoles, enabled);
    ElMessage.success('功能权限已更新');
  } finally {
    savingId.value = null;
  }
}

function normalizeRoles(value: unknown): UserRole[] {
  const rawRoles = Array.isArray(value) ? value : [];
  const roles = rawRoles.filter((role): role is UserRole => role === 'ROOT' || role === 'ADMIN' || role === 'USER');
  return Array.from(new Set<UserRole>(['ROOT', ...roles]));
}
</script>

<style scoped lang="scss">
.feature-permission-page {
  display: grid;
  gap: 18px;
}

.manager-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding: 28px;
  border-radius: 30px;
  background:
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.18), transparent 24rem),
    linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(240, 249, 255, 0.86));
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.1);
}

.eyebrow {
  margin: 0 0 8px;
  color: #0369a1;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 10px;
  color: #0f172a;
  font-size: clamp(30px, 5vw, 52px);
}

.manager-hero span,
.card-header span,
.feature-name small {
  color: #64748b;
}

.permission-groups {
  display: grid;
  gap: 18px;
}

.permission-card {
  border: 0;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 18px 60px rgba(36, 56, 97, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.feature-name {
  display: grid;
  gap: 4px;
}

.permission-table :deep(.el-checkbox) {
  margin-right: 16px;
}
</style>
