<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/chat" aria-label="AI 漫剧创作台">
        <span class="brand-mark">AI</span>
        <span>
          <strong>漫剧创作台</strong>
          <small>Dialogue to Manga</small>
        </span>
      </RouterLink>

      <nav class="nav-links" aria-label="主导航">
        <RouterLink to="/chat">对话</RouterLink>
        <RouterLink to="/stories">漫剧列表</RouterLink>
        <RouterLink v-if="canManageOutlineConfig" to="/outline-options">大纲配置</RouterLink>
        <RouterLink v-if="canManagePrompt" to="/prompts">Prompt 管理</RouterLink>
        <RouterLink v-if="userStore.isRoot" to="/users">用户权限</RouterLink>
        <RouterLink v-if="userStore.isRoot" to="/feature-permissions">功能权限</RouterLink>
      </nav>

      <el-dropdown trigger="click" @command="handleUserCommand">
        <button class="user-menu" type="button">
          <span class="avatar">{{ usernameInitial }}</span>
          <span class="username">{{ username }}</span>
          <span class="role-badge">{{ roleLabel }}</span>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人中心</el-dropdown-item>
            <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </header>

    <main class="content-panel">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useFeaturePermissionStore } from '../../stores/featurePermissionStore';
import { useUserStore } from '../../stores/userStore';

const router = useRouter();
const userStore = useUserStore();
const featurePermissionStore = useFeaturePermissionStore();

const username = computed(() => userStore.userInfo?.username || '创作者');

const usernameInitial = computed(() => username.value.slice(0, 1).toUpperCase());
const canManageOutlineConfig = computed(() =>
  featurePermissionStore.hasFeature('outlineConfig.manage', userStore.canManageSystemConfig),
);
const canManagePrompt = computed(() =>
  featurePermissionStore.hasFeature('prompt.manage', userStore.canManageSystemConfig),
);
const roleLabel = computed(() => {
  if (userStore.role === 'ROOT') {
    return 'root';
  }
  if (userStore.role === 'ADMIN') {
    return 'admin';
  }
  return '普通用户';
});

onMounted(() => {
  userStore.fetchProfile().catch(() => {
    // 资料刷新失败时仍保留当前页面，由请求拦截器统一处理 401。
  });
  featurePermissionStore.fetchMyPermissions().catch(() => {
    // 功能权限加载失败时保留本地角色兜底，真正权限仍由后端拦截。
  });
});

function handleUserCommand(command: string) {
  if (command === 'profile') {
    router.push('/user');
    return;
  }

  if (command === 'logout') {
    userStore.logout();
    featurePermissionStore.resetMyPermissions();
    router.push('/login');
  }
}
</script>

<style scoped lang="scss">
.app-shell {
  min-height: 100vh;
  padding: 20px;
  background:
    radial-gradient(circle at top left, rgba(43, 119, 255, 0.16), transparent 34rem),
    linear-gradient(135deg, #f7f3e8 0%, #e9f1ff 50%, #fffaf0 100%);
}

.topbar {
  position: sticky;
  top: 16px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 24px;
  max-width: 1180px;
  margin: 0 auto 20px;
  padding: 14px 18px;
  border: 1px solid rgba(23, 37, 84, 0.12);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(18px);
  box-shadow: 0 18px 60px rgba(36, 56, 97, 0.12);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: #172554;
  text-decoration: none;
}

.brand-mark {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 15px;
  color: #fff;
  font-weight: 800;
  letter-spacing: 0.02em;
  background: linear-gradient(135deg, #1d4ed8, #0f766e);
}

.brand strong,
.brand small {
  display: block;
}

.brand small {
  margin-top: 2px;
  color: #64748b;
  font-size: 12px;
}

.nav-links {
  display: flex;
  gap: 10px;
  margin-right: auto;
}

.nav-links a {
  padding: 10px 14px;
  border-radius: 999px;
  color: #334155;
  font-weight: 600;
  text-decoration: none;
}

.nav-links a.router-link-active {
  color: #0f766e;
  background: rgba(15, 118, 110, 0.1);
}

.user-menu {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  border: 0;
  background: transparent;
  color: #172554;
  cursor: pointer;
  font: inherit;
}

.avatar {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  font-weight: 700;
  background: #f97316;
}

.role-badge {
  padding: 3px 8px;
  border-radius: 999px;
  color: #0f766e;
  font-size: 12px;
  font-weight: 800;
  background: rgba(15, 118, 110, 0.1);
}

.content-panel {
  max-width: 1180px;
  margin: 0 auto;
}

@media (max-width: 720px) {
  .app-shell {
    padding: 12px;
  }

  .topbar {
    position: static;
    flex-wrap: wrap;
    gap: 12px;
    border-radius: 20px;
  }

  .nav-links {
    order: 3;
    width: 100%;
  }

  .nav-links a {
    flex: 1;
    text-align: center;
  }

  .username {
    display: none;
  }

  .role-badge {
    display: none;
  }
}
</style>
