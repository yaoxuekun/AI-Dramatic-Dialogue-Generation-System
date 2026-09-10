<template>
  <aside class="session-list">
    <div class="header">
      <div>
        <p>Sessions</p>
        <h2>对话</h2>
      </div>
      <el-button circle type="primary" :loading="creating" @click="$emit('create')">+</el-button>
    </div>

    <el-scrollbar class="scroll">
      <button
        v-for="session in sessions"
        :key="session.id"
        class="session-item"
        :class="{ active: session.id === currentSessionId }"
        type="button"
        @click="$emit('select', session.id)"
      >
        <span class="title">{{ session.title || '新对话' }}</span>
        <span class="time">{{ formatTime(session.lastActive || session.startedAt) }}</span>
        <span class="delete" @click.stop="$emit('delete', session.id)">删除</span>
      </button>

      <el-empty v-if="!loading && sessions.length === 0" description="还没有对话" />
      <div v-if="loading" class="loading">加载会话中...</div>
    </el-scrollbar>
  </aside>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import type { ChatSessionResponse } from '../../types/chat';

defineProps<{
  sessions: ChatSessionResponse[];
  currentSessionId: number | null;
  loading?: boolean;
  creating?: boolean;
}>();

defineEmits<{
  create: [];
  select: [sessionId: number];
  delete: [sessionId: number];
}>();

function formatTime(value: string) {
  return value ? dayjs(value).format('MM-DD HH:mm') : '';
}
</script>

<style scoped lang="scss">
.session-list {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 0;
  padding: 18px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.12);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.header p,
.header h2 {
  margin: 0;
}

.header p {
  color: #f97316;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.header h2 {
  color: #172554;
  font-size: 26px;
}

.scroll {
  min-height: 0;
}

.session-item {
  display: grid;
  width: 100%;
  gap: 6px;
  margin-bottom: 10px;
  padding: 14px;
  border: 1px solid transparent;
  border-radius: 18px;
  text-align: left;
  background: rgba(248, 250, 252, 0.9);
  cursor: pointer;
}

.session-item.active {
  border-color: rgba(15, 118, 110, 0.24);
  background: rgba(15, 118, 110, 0.1);
}

.title {
  overflow: hidden;
  color: #172554;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.time {
  color: #64748b;
  font-size: 12px;
}

.delete {
  color: #ef4444;
  font-size: 12px;
  font-weight: 700;
}

.loading {
  padding: 18px;
  color: #64748b;
  text-align: center;
}
</style>
