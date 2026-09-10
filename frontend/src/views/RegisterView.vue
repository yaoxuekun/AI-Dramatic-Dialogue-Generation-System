<template>
  <main class="auth-page">
    <section class="auth-card">
      <p class="eyebrow">New Creator</p>
      <h1>注册账号</h1>
      <p>创建账号后即可返回登录页，使用真实后端认证进入创作台。</p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model.trim="form.username" placeholder="3-50 个字符" autocomplete="username" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model.trim="form.email" placeholder="name@example.com" autocomplete="email" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="至少 6 个字符"
            autocomplete="new-password"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="再次输入密码"
            autocomplete="new-password"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>
        <el-button type="primary" size="large" :loading="isSubmitting" @click="handleRegister">
          注册
        </el-button>
      </el-form>

      <RouterLink class="switch-link" to="/login">已有账号？返回登录</RouterLink>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { useRouter } from 'vue-router';
import { useUserStore } from '../stores/userStore';

interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

const router = useRouter();
const userStore = useUserStore();
const formRef = ref<FormInstance>();
const isSubmitting = ref(false);

const form = reactive<RegisterForm>({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
});

const validateConfirmPassword = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (!value) {
    callback(new Error('请再次输入密码'));
    return;
  }
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'));
    return;
  }
  callback();
};

const rules: FormRules<RegisterForm> = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度应为 3-50 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱地址', trigger: ['blur', 'change'] },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度应为 6-100 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: ['blur', 'change'] },
  ],
};

async function handleRegister() {
  if (!formRef.value) {
    return;
  }

  await formRef.value.validate(async (valid) => {
    if (!valid) {
      return;
    }

    isSubmitting.value = true;
    try {
      await userStore.register({
        username: form.username,
        email: form.email,
        password: form.password,
      });
      ElMessage.success('注册成功，请登录');
      router.push('/login');
    } finally {
      isSubmitting.value = false;
    }
  });
}
</script>

<style scoped lang="scss">
.auth-page {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 20% 20%, rgba(29, 78, 216, 0.2), transparent 24rem),
    radial-gradient(circle at 80% 70%, rgba(249, 115, 22, 0.18), transparent 22rem),
    #f8fafc;
}

.auth-card {
  width: min(100%, 480px);
  padding: 38px;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 24px 90px rgba(15, 23, 42, 0.14);
}

.eyebrow {
  margin: 0 0 12px;
  color: #1d4ed8;
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

.switch-link {
  display: inline-block;
  margin-top: 18px;
  color: #0f766e;
  font-weight: 700;
  text-decoration: none;
}
</style>
