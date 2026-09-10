<template>
  <section class="story-page">
    <header class="hero-card">
      <div>
        <p class="eyebrow">Story Library</p>
        <h1>漫剧列表</h1>
        <p>管理由对话生成的漫剧草稿，快速进入详情、继续编辑或清理不需要的作品。</p>
      </div>
      <el-button type="primary" size="large" @click="router.push('/chat')">去对话生成</el-button>
    </header>

    <section class="toolbar-card">
      <el-input
        v-model.trim="keyword"
        class="search-input"
        clearable
        placeholder="搜索标题或简介"
      />
      <el-select v-model="selectedGenre" clearable placeholder="按类型筛选">
        <el-option
          v-for="genre in genreOptions"
          :key="genre"
          :label="genre"
          :value="genre"
        />
      </el-select>
      <el-select v-model="selectedStatus" clearable placeholder="按状态筛选">
        <el-option label="草稿" value="draft" />
        <el-option label="生成中" value="generating" />
        <el-option label="修改中" value="revising" />
        <el-option label="分卷处理中" value="volume_pending" />
        <el-option label="分卷正文生成中" value="volume_story_pending" />
        <el-option label="分卷小节生成中" value="volume_section_pending" />
        <el-option label="小节图片生成中" value="section_asset_pending" />
        <el-option label="故事脚本生成中" value="section_script_pending" />
        <el-option label="生成失败" value="failed" />
        <el-option label="已发布" value="published" />
        <el-option label="已归档" value="archived" />
      </el-select>
      <el-button :loading="storyStore.isLoading" @click="loadStories()">刷新</el-button>
    </section>

    <el-skeleton v-if="storyStore.isLoading && !storyStore.hasStories" :rows="8" animated />

    <section v-else-if="filteredStories.length > 0" class="story-grid">
      <article
        v-for="story in filteredStories"
        :key="story.id"
        class="story-card"
        @click="openStory(story.id)"
      >
        <div class="cover">
          <img v-if="story.coverImagePath" :src="resolveCoverUrl(story.coverImagePath)" :alt="story.title" />
          <span v-else>{{ story.title.slice(0, 2) }}</span>
        </div>
        <div class="story-body">
          <div class="meta-row">
            <el-tag v-if="story.genre" effect="plain">{{ story.genre }}</el-tag>
            <el-tag :type="statusMeta(story.status).type" effect="light">
              {{ statusMeta(story.status).label }}
            </el-tag>
          </div>
          <h2>{{ story.title }}</h2>
          <p>{{ story.synopsis || '这部漫剧还没有摘要。' }}</p>
          <div class="footer-row">
            <span>{{ formatDate(story.createdAt) }}</span>
            <div class="actions" @click.stop>
              <el-button text type="primary" @click="openStory(story.id)">查看</el-button>
              <el-button text type="danger" @click="confirmDelete(story.id)">删除</el-button>
            </div>
          </div>
        </div>
      </article>
    </section>

    <el-empty v-else description="暂无匹配的漫剧">
      <el-button type="primary" @click="router.push('/chat')">从对话开始生成</el-button>
    </el-empty>

    <footer class="pagination-bar">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :current-page="storyStore.pagination.current"
        :page-size="storyStore.pagination.size"
        :total="storyStore.pagination.total"
        @current-change="loadStories"
      />
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import dayjs from 'dayjs';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';
import { useStoryStore } from '../stores/storyStore';

const router = useRouter();
const storyStore = useStoryStore();
const keyword = ref('');
const selectedGenre = ref('');
const selectedStatus = ref('');

const genreOptions = computed(() =>
  Array.from(new Set(storyStore.stories.map((story) => story.genre).filter(Boolean))) as string[],
);

const filteredStories = computed(() => {
  const normalizedKeyword = keyword.value.toLowerCase();
  return storyStore.stories.filter((story) => {
    const matchesKeyword =
      !normalizedKeyword ||
      story.title.toLowerCase().includes(normalizedKeyword) ||
      (story.synopsis || '').toLowerCase().includes(normalizedKeyword);
    const matchesGenre = !selectedGenre.value || story.genre === selectedGenre.value;
    const matchesStatus = !selectedStatus.value || story.status === selectedStatus.value;
    return matchesKeyword && matchesGenre && matchesStatus;
  });
});

onMounted(() => {
  loadStories();
});

async function loadStories(page = storyStore.pagination.current) {
  await storyStore.fetchStories(page, storyStore.pagination.size);
}

function openStory(id: number) {
  router.push(`/story/${id}`);
}

async function confirmDelete(id: number) {
  try {
    await ElMessageBox.confirm('删除后漫剧和关联角色、场景会一并移除，确定继续吗？', '删除漫剧', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    });
  } catch {
    return;
  }

  await storyStore.deleteStory(id);
  ElMessage.success('漫剧已删除');
  if (storyStore.stories.length === 0 && storyStore.pagination.current > 1) {
    await loadStories(storyStore.pagination.current - 1);
  }
}

function resolveCoverUrl(path: string) {
  return path.startsWith('/api') ? path : `/api/files/${path}`;
}

function formatDate(value: string) {
  return value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '暂无时间';
}

function statusMeta(status?: string): { label: string; type: 'primary' | 'success' | 'info' | 'warning' | 'danger' } {
  if (status === 'generating') {
    return { label: '生成中', type: 'primary' };
  }
  if (status === 'revising') {
    return { label: '修改中', type: 'primary' };
  }
  if (status === 'volume_pending') {
    return { label: '分卷处理中', type: 'primary' };
  }
  if (status === 'volume_story_pending') {
    return { label: '分卷正文生成中', type: 'primary' };
  }
  if (status === 'volume_section_pending') {
    return { label: '分卷小节生成中', type: 'primary' };
  }
  if (status === 'section_asset_pending') {
    return { label: '小节图片生成中', type: 'primary' };
  }
  if (status === 'section_script_pending') {
    return { label: '故事脚本生成中', type: 'primary' };
  }
  if (status === 'failed') {
    return { label: '生成失败', type: 'danger' };
  }
  if (status === 'published') {
    return { label: '已发布', type: 'success' };
  }
  if (status === 'archived') {
    return { label: '已归档', type: 'info' };
  }
  return { label: '草稿', type: 'warning' };
}
</script>

<style scoped lang="scss">
.story-page {
  display: grid;
  gap: 20px;
}

.hero-card,
.toolbar-card,
.story-card {
  border: 1px solid rgba(23, 37, 84, 0.1);
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.1);
}

.hero-card {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  padding: 36px;
  border-radius: 30px;
  background:
    radial-gradient(circle at top right, rgba(249, 115, 22, 0.2), transparent 24rem),
    linear-gradient(145deg, rgba(255, 255, 255, 0.92), rgba(239, 246, 255, 0.9));
}

.eyebrow {
  margin: 0 0 12px;
  color: #c2410c;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 12px;
  color: #172554;
  font-size: clamp(34px, 6vw, 64px);
}

.hero-card p {
  max-width: 680px;
  margin: 0;
  color: #475569;
  font-size: 18px;
  line-height: 1.8;
}

.toolbar-card {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) 180px 180px auto;
  gap: 12px;
  padding: 16px;
  border-radius: 24px;
}

.story-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 18px;
}

.story-card {
  overflow: hidden;
  border-radius: 28px;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.story-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 30px 90px rgba(15, 23, 42, 0.16);
}

.cover {
  display: grid;
  height: 170px;
  place-items: center;
  color: #fff;
  font-size: 42px;
  font-weight: 900;
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.34), transparent 12rem),
    linear-gradient(135deg, #1d4ed8, #0f766e 55%, #f97316);
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.story-body {
  display: grid;
  gap: 12px;
  padding: 18px;
}

.meta-row,
.footer-row,
.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-row {
  justify-content: space-between;
  color: #64748b;
  font-size: 13px;
}

h2 {
  margin: 0;
  color: #172554;
  font-size: 22px;
}

.story-body p {
  display: -webkit-box;
  min-height: 72px;
  margin: 0;
  overflow: hidden;
  color: #475569;
  line-height: 1.7;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.pagination-bar {
  display: flex;
  justify-content: center;
  padding: 12px 0;
}

@media (max-width: 840px) {
  .hero-card,
  .toolbar-card {
    grid-template-columns: 1fr;
  }

  .hero-card {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
