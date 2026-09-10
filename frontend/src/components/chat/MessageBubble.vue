<template>
  <article class="message-row" :class="{ 'is-user': isUser }">
    <div class="avatar">{{ isUser ? '我' : 'AI' }}</div>
    <div class="bubble">
      <div class="content" v-html="renderedContent" />
      <time>{{ formattedTime }}</time>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import dayjs from 'dayjs';
import MarkdownIt from 'markdown-it';

const props = defineProps<{
  role: string;
  content: string;
  timestamp: string;
}>();

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
});

const isUser = computed(() => props.role === 'user');
const renderedContent = computed(() => markdown.render(props.content || ''));
const formattedTime = computed(() => dayjs(props.timestamp).format('MM-DD HH:mm'));
</script>

<style scoped lang="scss">
.message-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.message-row.is-user {
  flex-direction: row-reverse;
}

.avatar {
  display: grid;
  flex: 0 0 38px;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 14px;
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  background: linear-gradient(135deg, #0f766e, #1d4ed8);
}

.is-user .avatar {
  background: linear-gradient(135deg, #f97316, #ea580c);
}

.bubble {
  max-width: min(72%, 720px);
  padding: 14px 16px 10px;
  border-radius: 20px 20px 20px 6px;
  color: #172554;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
}

.is-user .bubble {
  border-radius: 20px 20px 6px 20px;
  color: #fff;
  background: linear-gradient(135deg, #1d4ed8, #0f766e);
}

.content {
  font-size: 15px;
  line-height: 1.75;
  word-break: break-word;
}

.content :deep(p) {
  margin: 0 0 8px;
}

.content :deep(p:last-child) {
  margin-bottom: 0;
}

.content :deep(a) {
  color: inherit;
  font-weight: 700;
}

time {
  display: block;
  margin-top: 8px;
  color: rgba(71, 85, 105, 0.72);
  font-size: 12px;
}

.is-user time {
  color: rgba(255, 255, 255, 0.76);
}

@media (max-width: 720px) {
  .bubble {
    max-width: calc(100% - 54px);
  }
}
</style>
