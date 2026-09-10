<template>
  <section class="user-center">
    <header class="profile-hero">
      <div class="avatar-panel">
        <el-avatar :size="112" :src="avatarPreviewUrl || undefined">{{ usernameInitial }}</el-avatar>
        <el-upload
          :show-file-list="false"
          :http-request="uploadAvatar"
          :before-upload="beforeAvatarUpload"
        >
          <el-button type="primary" plain :loading="isUploadingAvatar">上传头像</el-button>
        </el-upload>
      </div>

      <div class="profile-copy">
        <p class="eyebrow">Creator Profile</p>
        <h1>{{ userStore.userInfo?.username || '创作者' }}</h1>
        <p>{{ userStore.userInfo?.email || '登录后在这里维护你的创作者资料。' }}</p>
        <div class="profile-actions">
          <el-button type="primary" @click="openEditDialog">编辑资料</el-button>
          <el-button :loading="isRefreshing" @click="refreshDashboard">刷新数据</el-button>
        </div>
      </div>
    </header>

    <section class="stats-grid">
      <article class="stat-card warm">
        <span>Stories</span>
        <strong>{{ storyCount }}</strong>
        <p>已生成漫剧数量</p>
      </article>
      <article class="stat-card cool">
        <span>Sessions</span>
        <strong>{{ chatCount }}</strong>
        <p>当前对话会话数量</p>
      </article>
      <article class="stat-card green">
        <span>Joined</span>
        <strong>{{ registeredDate }}</strong>
        <p>注册时间</p>
      </article>
    </section>

    <section class="info-grid">
      <article class="info-card">
        <h2>账号信息</h2>
        <dl>
          <dt>用户 ID</dt>
          <dd>{{ userStore.userInfo?.id || '-' }}</dd>
          <dt>用户名</dt>
          <dd>{{ userStore.userInfo?.username || '-' }}</dd>
          <dt>邮箱</dt>
          <dd>{{ userStore.userInfo?.email || '-' }}</dd>
          <dt>头像路径</dt>
          <dd>{{ userStore.userInfo?.avatarPath || '未设置' }}</dd>
        </dl>
      </article>

      <article class="info-card guide-card">
        <h2>下一步创作</h2>
        <p>从对话继续收集设定，或进入漫剧列表查看已经生成的草稿。</p>
        <div class="quick-actions">
          <el-button type="primary" @click="router.push('/chat')">继续对话</el-button>
          <el-button @click="router.push('/stories')">查看漫剧</el-button>
        </div>
      </article>
    </section>

    <el-dialog v-model="editDialogVisible" title="编辑个人资料" width="480px">
      <el-form ref="formRef" label-position="top" :model="editForm" :rules="rules">
        <el-form-item label="用户名" prop="username">
          <el-input v-model.trim="editForm.username" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model.trim="editForm.email" maxlength="100" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="isSaving" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import dayjs from 'dayjs';
import {
  ElMessage,
  type FormInstance,
  type FormRules,
  type UploadRawFile,
  type UploadRequestOptions,
} from 'element-plus';
import { useRouter } from 'vue-router';
import * as fileApi from '../api/fileApi';
import { useChatStore } from '../stores/chatStore';
import { useStoryStore } from '../stores/storyStore';
import { useUserStore } from '../stores/userStore';

interface ProfileForm {
  username: string;
  email: string;
}

const router = useRouter();
const userStore = useUserStore();
const storyStore = useStoryStore();
const chatStore = useChatStore();
const formRef = ref<FormInstance>();
const editDialogVisible = ref(false);
const isSaving = ref(false);
const isRefreshing = ref(false);
const isUploadingAvatar = ref(false);
const avatarPreviewUrl = ref('');

const editForm = reactive<ProfileForm>({
  username: '',
  email: '',
});

const rules: FormRules<ProfileForm> = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度应为 3-50 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
};

const usernameInitial = computed(() => userStore.userInfo?.username?.slice(0, 1).toUpperCase() || '创');
const storyCount = computed(() => storyStore.pagination.total || storyStore.stories.length);
const chatCount = computed(() => chatStore.sessions.length);
const registeredDate = computed(() =>
  userStore.userInfo?.createdAt ? dayjs(userStore.userInfo.createdAt).format('YYYY-MM-DD') : '-',
);

onMounted(refreshDashboard);

watch(
  () => userStore.userInfo?.avatarPath,
  (avatarPath) => {
    refreshAvatarPreview(avatarPath);
  },
);

onBeforeUnmount(() => {
  revokeAvatarPreview();
});

async function refreshDashboard() {
  isRefreshing.value = true;
  try {
    await userStore.fetchProfile();
    await Promise.allSettled([
      storyStore.fetchStories(1, 1),
      chatStore.loadSessions(),
    ]);
    await refreshAvatarPreview(userStore.userInfo?.avatarPath);
  } finally {
    isRefreshing.value = false;
  }
}

function openEditDialog() {
  editForm.username = userStore.userInfo?.username || '';
  editForm.email = userStore.userInfo?.email || '';
  editDialogVisible.value = true;
}

async function saveProfile() {
  if (!formRef.value) {
    return;
  }

  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) {
    return;
  }

  isSaving.value = true;
  try {
    await userStore.updateProfile({
      username: editForm.username,
      email: editForm.email,
    });
    ElMessage.success('个人资料已更新');
    editDialogVisible.value = false;
  } finally {
    isSaving.value = false;
  }
}

function beforeAvatarUpload(file: UploadRawFile) {
  const isImage = file.type.startsWith('image/');
  const isUnderLimit = file.size <= 10 * 1024 * 1024;

  if (!isImage) {
    ElMessage.error('头像只能上传图片文件');
    return false;
  }

  if (!isUnderLimit) {
    ElMessage.error('头像大小不能超过 10MB');
    return false;
  }

  return true;
}

async function uploadAvatar(options: UploadRequestOptions) {
  isUploadingAvatar.value = true;
  try {
    const result = await fileApi.uploadFile(options.file, 'avatars');
    await userStore.updateProfile({ avatarPath: result.fileUrl });
    await refreshAvatarPreview(result.fileUrl);
    options.onSuccess?.(result);
    ElMessage.success('头像上传成功');
  } catch (error) {
    throw error;
  } finally {
    isUploadingAvatar.value = false;
  }
}

async function refreshAvatarPreview(avatarPath?: string) {
  revokeAvatarPreview();
  if (!avatarPath) {
    return;
  }

  try {
    const blob = await fileApi.loadFileBlob(avatarPath);
    avatarPreviewUrl.value = URL.createObjectURL(blob);
  } catch {
    avatarPreviewUrl.value = '';
  }
}

function revokeAvatarPreview() {
  if (avatarPreviewUrl.value) {
    URL.revokeObjectURL(avatarPreviewUrl.value);
    avatarPreviewUrl.value = '';
  }
}
</script>

<style scoped lang="scss">
.user-center {
  display: grid;
  gap: 20px;
}

.profile-hero,
.stat-card,
.info-card {
  border: 1px solid rgba(23, 37, 84, 0.1);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.1);
}

.profile-hero {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 28px;
  align-items: center;
  padding: 34px;
  border-radius: 32px;
  background:
    radial-gradient(circle at 10% 10%, rgba(15, 118, 110, 0.18), transparent 22rem),
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(255, 247, 237, 0.88));
}

.avatar-panel {
  display: grid;
  justify-items: center;
  gap: 14px;
}

.profile-copy {
  min-width: 0;
}

.eyebrow {
  margin: 0 0 12px;
  color: #0f766e;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 12px;
  color: #172554;
  font-size: clamp(34px, 6vw, 64px);
}

.profile-copy p,
.guide-card p {
  margin: 0;
  color: #475569;
  font-size: 18px;
  line-height: 1.8;
}

.profile-actions,
.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.stats-grid,
.info-grid {
  display: grid;
  gap: 18px;
}

.stats-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.info-grid {
  grid-template-columns: minmax(0, 1.1fr) minmax(280px, 0.9fr);
}

.stat-card,
.info-card {
  padding: 24px;
  border-radius: 28px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card::after {
  position: absolute;
  right: -28px;
  bottom: -36px;
  width: 120px;
  height: 120px;
  border-radius: 999px;
  content: '';
  opacity: 0.24;
}

.stat-card.warm::after {
  background: #f97316;
}

.stat-card.cool::after {
  background: #1d4ed8;
}

.stat-card.green::after {
  background: #0f766e;
}

.stat-card span {
  color: #64748b;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.stat-card strong {
  display: block;
  margin-top: 10px;
  color: #172554;
  font-size: clamp(32px, 5vw, 48px);
}

.stat-card p {
  margin: 8px 0 0;
  color: #475569;
}

h2 {
  margin: 0 0 18px;
  color: #172554;
}

dl {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  gap: 14px 16px;
  margin: 0;
}

dt {
  color: #94a3b8;
  font-weight: 800;
}

dd {
  min-width: 0;
  margin: 0;
  overflow-wrap: anywhere;
  color: #334155;
}

@media (max-width: 820px) {
  .profile-hero,
  .stats-grid,
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
