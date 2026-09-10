<template>
  <form class="input-area" @submit.prevent="submit">
    <el-input
      v-model="draft"
      class="message-input"
      type="textarea"
      :autosize="{ minRows: 2, maxRows: 6 }"
      resize="none"
      placeholder="描述你想创作的漫剧设定，Enter 发送，Shift+Enter 换行"
      :disabled="disabled || loading"
      @keydown.enter="handleEnter"
    />
    <el-button type="primary" :loading="loading" :disabled="disabled || !draft.trim()" @click="submit">
      发送
    </el-button>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{
  loading?: boolean;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  send: [content: string];
}>();

const draft = ref('');

function handleEnter(event: KeyboardEvent) {
  if (event.shiftKey) {
    return;
  }
  event.preventDefault();
  submit();
}

function submit() {
  const content = draft.value.trim();
  if (!content) {
    return;
  }
  emit('send', content);
  draft.value = '';
}
</script>

<style scoped lang="scss">
.input-area {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
}

.message-input :deep(.el-textarea__inner) {
  border: 0;
  box-shadow: none;
  background: transparent;
  font-size: 15px;
  line-height: 1.7;
}

.el-button {
  align-self: end;
  min-width: 92px;
  height: 44px;
  border-radius: 14px;
}

@media (max-width: 640px) {
  .input-area {
    grid-template-columns: 1fr;
  }

  .el-button {
    width: 100%;
  }
}
</style>
