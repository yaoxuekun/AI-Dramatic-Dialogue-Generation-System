<template>
  <main class="auth-page">
    <section class="auth-card">
      <p class="eyebrow">Welcome Back</p>
      <h1>登录创作台</h1>
      <p>使用后端真实登录接口获取 JWT，进入你的 AI 漫剧创作空间。</p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model.trim="form.username" placeholder="请输入用户名" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-alert
          v-if="loginError"
          class="login-error"
          :title="loginError"
          type="error"
          show-icon
          :closable="false"
        />
        <el-button
          type="primary"
          size="large"
          native-type="button"
          :loading="isSubmitting"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>

      <RouterLink class="switch-link" to="/register">还没有账号？去注册</RouterLink>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '../stores/userStore';

interface LoginForm {
  username: string;
  password: string;
}

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const formRef = ref<FormInstance>();
const isSubmitting = ref(false);
const loginError = ref('');

const form = reactive<LoginForm>({
  username: '',
  password: '',
});

const rules: FormRules<LoginForm> = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度应为 3-50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度应为 6-100 个字符', trigger: 'blur' },
  ],
};

async function handleLogin() {
  if (!formRef.value) {
    return;
  }

  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) {
    return;
  }

  isSubmitting.value = true;
  loginError.value = '';
  try {
    await userStore.login(form.username, form.password);
    ElMessage.success('登录成功');
    await navigateAfterLogin();
  } catch (error) {
    loginError.value = getErrorMessage(error);
  } finally {
    isSubmitting.value = false;
  }
}

async function navigateAfterLogin() {
  const target = getSafeRedirectPath();
  const resolvedTarget = router.resolve(target).fullPath;

  try {
    await router.replace(resolvedTarget);
  } catch {
    window.location.assign(resolvedTarget);
    return;
  }

  if (router.currentRoute.value.fullPath !== resolvedTarget) {
    window.location.assign(resolvedTarget);
  }
}

function getSafeRedirectPath() {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/chat';

  if (!redirect.startsWith('/') || redirect.startsWith('//') || redirect.startsWith('/login')) {
    return '/chat';
  }

  return redirect;
}

function getErrorMessage(error: unknown) {
  if (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    (error as { response?: { data?: { message?: string } } }).response?.data?.message
  ) {
    return (error as { response: { data: { message: string } } }).response.data.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return '登录失败，请检查用户名、密码或后端服务状态';
}
</script>

<style scoped lang="scss">
.auth-page {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 20% 20%, rgba(249, 115, 22, 0.22), transparent 24rem),
    radial-gradient(circle at 80% 10%, rgba(15, 118, 110, 0.18), transparent 22rem),
    #f8fafc;
}

.auth-card {
  width: min(100%, 460px);
  padding: 38px;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 24px 90px rgba(15, 23, 42, 0.14);
}

.eyebrow {
  margin: 0 0 12px;
  color: #f97316;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 12px;
  color: #172554;
  font-size: 42px;
}

p {
  color: #475569;
  line-height: 1.8;
}

.el-button {
  width: 100%;
}

.login-error {
  margin-bottom: 16px;
}

.switch-link {
  display: inline-block;
  margin-top: 18px;
  color: #0f766e;
  font-weight: 700;
  text-decoration: none;
}
</style>
