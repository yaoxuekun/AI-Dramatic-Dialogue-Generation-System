<template>
  <section class="user-manager">
    <header class="manager-hero">
      <div>
        <p class="eyebrow">Access Control</p>
        <h1>用户权限</h1>
        <span>root 可以调整其他用户的权限等级；admin 可以管理大纲配置和 Prompt，普通用户只保留创作入口。</span>
      </div>
      <el-button type="primary" size="large" :loading="userStore.isUserLoading" @click="loadUsers">
        刷新用户
      </el-button>
    </header>

    <el-card class="manager-card" shadow="never">
      <el-table
        v-loading="userStore.isUserLoading"
        :data="userStore.users"
        class="user-table"
        row-key="id"
      >
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column prop="username" label="用户名" min-width="150" />
        <el-table-column prop="email" label="邮箱" min-width="220" />
        <el-table-column label="权限等级" width="150">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" effect="light">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="注册时间" min-width="180" />
        <el-table-column label="设置权限" width="220" fixed="right">
          <template #default="{ row }">
            <el-select
              :model-value="row.role"
              :disabled="row.id === userStore.userInfo?.id"
              :loading="savingUserId === row.id"
              placeholder="选择权限"
              @change="handleRoleChange(row.id, $event)"
            >
              <el-option label="root" value="ROOT" />
              <el-option label="admin" value="ADMIN" />
              <el-option label="普通用户" value="USER" />
            </el-select>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useUserStore } from '../stores/userStore';
import type { UserRole } from '../types/auth';

const userStore = useUserStore();
const savingUserId = ref<number | null>(null);

onMounted(loadUsers);

async function loadUsers() {
  await userStore.fetchUsers();
}

function handleRoleChange(userId: number, role: unknown) {
  updateRole(userId, role as UserRole);
}

async function updateRole(userId: number, role: UserRole) {
  const target = userStore.users.find((user) => user.id === userId);
  if (!target || target.role === role) {
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定将用户“${target.username}”设置为 ${roleLabel(role)} 吗？`,
      '修改用户权限',
      {
        type: 'warning',
        confirmButtonText: '确认修改',
        cancelButtonText: '取消',
      },
    );
  } catch {
    return;
  }

  savingUserId.value = userId;
  try {
    await userStore.updateUserRole(userId, role);
    ElMessage.success('用户权限已更新');
  } finally {
    savingUserId.value = null;
  }
}

function roleLabel(role: UserRole) {
  if (role === 'ROOT') {
    return 'root';
  }
  if (role === 'ADMIN') {
    return 'admin';
  }
  return '普通用户';
}

function roleTagType(role: UserRole) {
  if (role === 'ROOT') {
    return 'danger';
  }
  if (role === 'ADMIN') {
    return 'warning';
  }
  return 'success';
}
</script>

<style scoped lang="scss">
.user-manager {
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
    radial-gradient(circle at top right, rgba(220, 38, 38, 0.16), transparent 24rem),
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(255, 247, 237, 0.84));
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.1);
}

.eyebrow {
  margin: 0 0 8px;
  color: #b45309;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 10px;
  color: #172554;
  font-size: clamp(30px, 5vw, 52px);
}

.manager-hero span {
  color: #64748b;
}

.manager-card {
  border: 0;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 18px 60px rgba(36, 56, 97, 0.1);
}

.user-table {
  width: 100%;
}

@media (max-width: 720px) {
  .manager-hero {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
