<template>
  <section class="detail-page">
    <el-skeleton v-if="storyStore.isLoading && !story" :rows="10" animated />

    <template v-else-if="story">
      <header class="detail-hero">
        <div>
          <p class="eyebrow">Story Detail</p>
          <h1>{{ story.title }}</h1>
          <div class="tag-row">
            <el-tag v-if="story.genre" effect="plain">{{ story.genre }}</el-tag>
            <el-tag v-if="story.style" type="success" effect="plain">{{ story.style }}</el-tag>
            <el-tag type="warning" effect="light">{{ statusLabel(story.status) }}</el-tag>
          </div>
        </div>
        <div class="hero-actions">
          <el-button @click="router.push('/stories')">返回列表</el-button>
          <el-button type="primary" @click="openEditDialog">编辑信息</el-button>
          <el-button type="primary" plain @click="openManualEditDialog">手动修改大纲/角色</el-button>
          <el-button type="success" plain @click="openReviseDialog">大纲修改</el-button>
          <el-button
            type="success"
            :loading="storyStore.isGeneratingVolumeOutline"
            @click="generateVolumeOutline"
          >
            分卷大纲生成
          </el-button>
          <el-button type="warning" plain @click="ElMessage.info('封面生成将在后续 AI 图片阶段接入')">
            生成封面
          </el-button>
          <el-button type="danger" plain @click="confirmDelete">删除</el-button>
        </div>
      </header>

      <section class="summary-card">
        <div class="section-heading">
          <h2>故事摘要</h2>
          <el-button link type="primary" @click="openManualEditDialog">手动修改</el-button>
        </div>
        <p>{{ story.synopsis || '暂无摘要。' }}</p>
      </section>

      <section class="content-grid">
        <article class="panel script-panel">
          <div class="section-heading">
            <h2>剧情大纲</h2>
            <el-button link type="primary" @click="openManualEditDialog">手动修改</el-button>
          </div>
          <p class="script-text">{{ story.fullContent || '暂无剧情大纲。' }}</p>
        </article>

        <article class="panel">
          <div class="section-heading">
            <h2>主要角色设定</h2>
            <el-button link type="primary" @click="openManualEditDialog">手动修改</el-button>
          </div>
          <div v-if="story.characters.length > 0" class="character-grid">
            <CharacterCard
              v-for="character in story.characters"
              :key="character.id || character.name"
              :character="character"
            />
          </div>
          <el-empty v-else description="暂无角色设定" />
        </article>
      </section>

      <section class="panel volume-panel">
        <div class="section-heading">
          <h2>分卷大纲</h2>
          <div class="volume-toolbar">
            <el-select
              v-if="hasVolumeOutlines"
              v-model="selectedVolumeNumber"
              class="volume-filter"
              placeholder="选择显示范围"
            >
              <el-option
                v-for="volume in story.volumeOutlines"
                :key="volume.id || volume.volumeNumber"
                :label="`第 ${volume.volumeNumber} 卷`"
                :value="volume.volumeNumber"
              />
            </el-select>
            <el-button
              type="success"
              plain
              :loading="storyStore.isGeneratingVolumeOutline"
              @click="generateVolumeOutline"
            >
              {{ hasVolumeOutlines ? '重新生成分卷大纲' : '分卷大纲生成' }}
            </el-button>
            <el-button
              v-if="hasVolumeOutlines"
              type="primary"
              plain
              :loading="storyStore.isRevisingVolumeOutline"
              @click="openVolumeReviseDialog"
            >
              自动修改分卷大纲
            </el-button>
            <el-button
              v-if="hasVolumeOutlines"
              type="primary"
              plain
              @click="openVolumeManualEditDialog"
            >
              手动修改分卷大纲
            </el-button>
          </div>
        </div>
        <div v-if="hasVolumeOutlines" class="volume-list">
          <article
            v-for="volume in displayedVolumeOutlines"
            :key="volume.id"
            class="volume-card"
          >
            <div class="volume-title-row">
              <el-tag type="success" effect="light">第 {{ volume.volumeNumber }} 卷</el-tag>
              <h3>{{ volume.title }}</h3>
              <el-button
                type="primary"
                plain
                size="small"
                :loading="storyStore.generatingVolumeSectionsVolumeId === volume.id"
                @click="generateVolumeSections(volume.id)"
              >
                生成小节故事
              </el-button>
            </div>
            <p v-if="volume.summary" class="volume-summary">{{ volume.summary }}</p>
            <p v-if="volume.content" class="script-text">{{ volume.content }}</p>
            <p v-if="volume.endingHook" class="ending-hook">卷末钩子：{{ volume.endingHook }}</p>
            <div v-if="volume.sections?.length" class="volume-section-list">
              <article
                v-for="section in volume.sections"
                :key="section.id"
                class="volume-section-card"
              >
                <div class="volume-title-row">
                  <el-tag type="primary" effect="light">第 {{ section.sectionNumber }} 节</el-tag>
                  <h4>{{ section.title }}</h4>
                  <el-button
                    type="warning"
                    plain
                    size="small"
                    :loading="storyStore.generatingSectionAssetsSectionId === section.id"
                    @click="generateSectionAssets(section.id)"
                  >
                    {{ section.assets?.length ? '重新生成人物/场景图片' : '生成人物/场景图片' }}
                  </el-button>
                  <el-button
                    type="success"
                    plain
                    size="small"
                    :loading="storyStore.generatingSectionScriptSectionId === section.id"
                    @click="generateSectionScript(section.id)"
                  >
                    {{ section.scripts?.length ? '重新生成故事脚本' : '生成故事脚本' }}
                  </el-button>
                </div>
                <p v-if="section.summary" class="volume-summary">{{ section.summary }}</p>
                <p v-if="section.content" class="script-text">{{ section.content }}</p>
                <p v-if="section.endingHook" class="ending-hook">小节钩子：{{ section.endingHook }}</p>
                <div v-if="section.scripts?.length" class="section-script-board">
                  <div class="section-script-header">
                    <h5>故事脚本</h5>
                    <span>总时长约 {{ formatDuration(section.scriptTotalDurationSeconds) }}</span>
                  </div>
                  <div class="script-shot-list">
                    <article
                      v-for="shot in section.scripts"
                      :key="shot.id"
                      class="script-shot-card"
                    >
                      <div class="script-shot-meta">
                        <el-tag size="small" type="success">#{{ shot.shotNumber }}</el-tag>
                        <span>{{ formatDuration(shot.durationSeconds) }}</span>
                        <span>{{ shot.shotType }}</span>
                        <span v-if="shot.cameraMovement">{{ shot.cameraMovement }}</span>
                      </div>
                      <p class="script-shot-action">{{ shot.action }}</p>
                      <p v-if="shot.dialogue" class="script-shot-dialogue">台词：{{ shot.dialogue }}</p>
                    </article>
                  </div>
                </div>
                <div v-if="section.assets?.length" class="section-assets">
                  <h5>本节人物与场景资源</h5>
                  <div class="asset-grid">
                    <article
                      v-for="asset in section.assets"
                      :key="asset.id"
                      class="asset-card"
                    >
                      <div class="asset-image">
                        <img v-if="resolveAssetImageUrl(asset)" :src="resolveAssetImageUrl(asset)" :alt="asset.name" />
                        <span v-else>图片生成中或生成失败</span>
                      </div>
                      <div class="asset-body">
                        <el-tag size="small" :type="asset.assetType === 'CHARACTER' ? 'success' : 'warning'">
                          {{ assetTypeLabel(asset.assetType) }}
                        </el-tag>
                        <h6>{{ asset.name }}</h6>
                        <p v-if="asset.description">{{ asset.description }}</p>
                        <audio
                          v-if="asset.assetType === 'CHARACTER' && asset.audioUrl"
                          controls
                          :src="asset.audioUrl"
                        />
                        <el-upload
                          v-if="asset.assetType === 'CHARACTER'"
                          :show-file-list="false"
                          :before-upload="beforeAssetAudioUpload"
                          :http-request="createAssetAudioUploader(asset.id)"
                        >
                          <el-button
                            size="small"
                            plain
                            :loading="storyStore.uploadingAssetAudioId === asset.id"
                          >
                            {{ asset.audioUrl ? '替换人物音频' : '上传人物音频' }}
                          </el-button>
                        </el-upload>
                      </div>
                    </article>
                  </div>
                </div>
              </article>
            </div>
          </article>
        </div>
        <el-empty v-else description="暂无分卷大纲，点击按钮后会根据剧情大纲自动生成。" />
      </section>
    </template>

    <el-empty v-else description="漫剧不存在或无权访问">
      <el-button type="primary" @click="router.push('/stories')">返回列表</el-button>
    </el-empty>

    <el-dialog v-model="editDialogVisible" title="编辑漫剧信息" width="520px">
      <el-form label-position="top" :model="editForm">
        <el-form-item label="标题">
          <el-input v-model.trim="editForm.title" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="类型">
          <el-input v-model.trim="editForm.genre" maxlength="100" />
        </el-form-item>
        <el-form-item label="漫剧风格">
          <el-input v-model.trim="editForm.style" maxlength="100" />
          <p class="field-hint">修改后，新生成的人物、场景图片以及后续视频生成都会使用这个统一风格。</p>
        </el-form-item>
        <el-form-item label="摘要">
          <el-input
            v-model="editForm.synopsis"
            type="textarea"
            :autosize="{ minRows: 4, maxRows: 8 }"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="isSaving" @click="saveStory">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="manualEditDialogVisible" title="手动修改剧情大纲与角色设定" width="880px">
      <el-form label-position="top" :model="manualForm">
        <el-form-item label="故事摘要">
          <el-input
            v-model="manualForm.synopsis"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="剧情大纲">
          <el-input
            v-model="manualForm.fullContent"
            type="textarea"
            :autosize="{ minRows: 10, maxRows: 18 }"
          />
        </el-form-item>

        <div class="manual-characters-header">
          <h3>角色设定</h3>
          <el-button type="primary" plain @click="addManualCharacter">新增角色</el-button>
        </div>
        <div class="manual-character-list">
          <el-card v-for="(character, index) in manualForm.characters" :key="index" shadow="never">
            <template #header>
              <div class="character-edit-title">
                <span>角色 {{ index + 1 }}</span>
                <el-button link type="danger" @click="removeManualCharacter(index)">删除</el-button>
              </div>
            </template>
            <div class="character-edit-grid">
              <el-form-item label="姓名">
                <el-input v-model.trim="character.name" maxlength="100" />
              </el-form-item>
              <el-form-item label="定位">
                <el-input v-model.trim="character.role" maxlength="100" />
              </el-form-item>
            </div>
            <el-form-item label="描述">
              <el-input
                v-model="character.description"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 5 }"
              />
            </el-form-item>
            <el-form-item label="性格/弧光">
              <el-input
                v-model="character.personality"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 5 }"
              />
            </el-form-item>
            <el-form-item label="外观 JSON">
              <el-input
                v-model="character.appearanceText"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 5 }"
                placeholder='例如：{"hair":"黑色短发","clothing":"旧风衣"}'
              />
            </el-form-item>
          </el-card>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="manualEditDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="isManualSaving" @click="saveManualDetail">保存修改</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reviseDialogVisible" title="大纲修改意见" width="560px">
      <el-form label-position="top">
        <el-form-item label="请输入你希望如何修改剧情大纲">
          <el-input
            v-model="reviseSuggestion"
            type="textarea"
            :autosize="{ minRows: 5, maxRows: 10 }"
            maxlength="5000"
            show-word-limit
            placeholder="例如：加强反派动机，把第二幕改得更悬疑，增加女主和主角的情感冲突。"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviseDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="isRevising" @click="submitOutlineRevision">提交修改</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="volumeReviseDialogVisible" title="自动修改分卷大纲" width="620px">
      <el-form label-position="top">
        <el-form-item label="请输入你希望如何修改分卷大纲">
          <el-input
            v-model="volumeReviseSuggestion"
            type="textarea"
            :autosize="{ minRows: 5, maxRows: 10 }"
            maxlength="5000"
            show-word-limit
            placeholder="例如：第三卷增加一次重大反转，压缩前两卷铺垫，把女主线提前到第一卷结尾。"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="volumeReviseDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="storyStore.isRevisingVolumeOutline" @click="submitVolumeRevision">
          提交自动修改
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="volumeManualDialogVisible" title="手动修改分卷大纲" width="920px">
      <el-form label-position="top" :model="volumeManualForm">
        <div class="manual-characters-header">
          <h3>分卷列表</h3>
          <el-button type="primary" plain @click="addManualVolume">新增分卷</el-button>
        </div>
        <div class="manual-volume-list">
          <el-card v-for="(volume, index) in volumeManualForm.volumes" :key="index" shadow="never">
            <template #header>
              <div class="character-edit-title">
                <span>第 {{ volume.volumeNumber || index + 1 }} 卷</span>
                <el-button link type="danger" @click="removeManualVolume(index)">删除</el-button>
              </div>
            </template>
            <div class="volume-edit-grid">
              <el-form-item label="卷号">
                <el-input-number v-model="volume.volumeNumber" :min="1" :step="1" />
              </el-form-item>
              <el-form-item label="卷名">
                <el-input v-model.trim="volume.title" maxlength="200" show-word-limit />
              </el-form-item>
            </div>
            <el-form-item label="摘要">
              <el-input
                v-model="volume.summary"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 5 }"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>
            <el-form-item label="详细大纲">
              <el-input
                v-model="volume.content"
                type="textarea"
                :autosize="{ minRows: 6, maxRows: 12 }"
              />
            </el-form-item>
            <el-form-item label="卷末钩子">
              <el-input
                v-model="volume.endingHook"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 5 }"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>
          </el-card>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="volumeManualDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="storyStore.isSavingVolumeOutline" @click="saveManualVolumeOutlines">
          保存分卷大纲
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { UploadRawFile, UploadRequestOptions } from 'element-plus';
import { useRouter } from 'vue-router';
import CharacterCard from '../components/story/CharacterCard.vue';
import { useStoryStore } from '../stores/storyStore';
import type { StoryAsset, StoryCharacter, StoryVolumeOutlineUpdateItem } from '../types/story';

interface EditableCharacter {
  name: string;
  role: string;
  description: string;
  personality: string;
  appearanceText: string;
}

interface EditableVolumeOutline {
  volumeNumber: number;
  title: string;
  summary: string;
  content: string;
  endingHook: string;
}

const props = defineProps<{
  id: string;
}>();

const router = useRouter();
const storyStore = useStoryStore();
const editDialogVisible = ref(false);
const manualEditDialogVisible = ref(false);
const reviseDialogVisible = ref(false);
const volumeReviseDialogVisible = ref(false);
const volumeManualDialogVisible = ref(false);
const isSaving = ref(false);
const isManualSaving = ref(false);
const isRevising = ref(false);
const reviseSuggestion = ref('');
const volumeReviseSuggestion = ref('');
const editForm = reactive({
  title: '',
  genre: '',
  style: '',
  synopsis: '',
});
const manualForm = reactive({
  synopsis: '',
  fullContent: '',
  characters: [] as EditableCharacter[],
});
const volumeManualForm = reactive({
  volumes: [] as EditableVolumeOutline[],
});
const selectedVolumeNumber = ref<number>();
let storyPollingTimer: number | undefined;

const story = computed(() => storyStore.currentStory);
const hasVolumeOutlines = computed(() => (story.value?.volumeOutlines?.length || 0) > 0);
const displayedVolumeOutlines = computed(() => {
  const volumes = story.value?.volumeOutlines || [];
  if (!selectedVolumeNumber.value) {
    return volumes.length > 0 ? [volumes[0]] : [];
  }
  return volumes.filter((volume) => volume.volumeNumber === selectedVolumeNumber.value);
});

onMounted(loadStory);

onBeforeUnmount(() => {
  stopStoryPolling();
});

watch(
  () => props.id,
  () => {
    selectedVolumeNumber.value = undefined;
    loadStory();
  },
);

watch(
  () => story.value?.volumeOutlines?.map((volume) => volume.volumeNumber).join(',') || '',
  () => {
    syncSelectedVolume();
  },
);

async function loadStory() {
  const storyId = Number(props.id);
  if (!Number.isFinite(storyId) || storyId <= 0) {
    router.replace('/stories');
    return;
  }

  const loadedStory = await storyStore.fetchStoryDetail(storyId);
  syncSelectedVolume();
  if (isProcessingStatus(loadedStory.status)) {
    startStoryPolling(storyId);
  } else {
    stopStoryPolling();
  }
}

function openEditDialog() {
  if (!story.value) {
    return;
  }
  editForm.title = story.value.title;
  editForm.genre = story.value.genre || '';
  editForm.style = story.value.style || '';
  editForm.synopsis = story.value.synopsis || '';
  editDialogVisible.value = true;
}

async function saveStory() {
  if (!story.value) {
    return;
  }

  isSaving.value = true;
  try {
    await storyStore.updateStory(story.value.id, {
      title: editForm.title,
      genre: editForm.genre,
      style: editForm.style,
      synopsis: editForm.synopsis,
    });
    ElMessage.success('漫剧信息已更新');
    editDialogVisible.value = false;
  } finally {
    isSaving.value = false;
  }
}

function openManualEditDialog() {
  if (!story.value) {
    return;
  }
  manualForm.synopsis = story.value.synopsis || '';
  manualForm.fullContent = story.value.fullContent || '';
  manualForm.characters = story.value.characters.map(toEditableCharacter);
  manualEditDialogVisible.value = true;
}

function toEditableCharacter(character: StoryCharacter): EditableCharacter {
  return {
    name: character.name || '',
    role: character.role || '',
    description: character.description || '',
    personality: character.personality || '',
    appearanceText: character.appearance ? JSON.stringify(character.appearance, null, 2) : '',
  };
}

function addManualCharacter() {
  manualForm.characters.push({
    name: '',
    role: '',
    description: '',
    personality: '',
    appearanceText: '',
  });
}

function removeManualCharacter(index: number) {
  manualForm.characters.splice(index, 1);
}

async function saveManualDetail() {
  if (!story.value) {
    return;
  }

  let characters: StoryCharacter[];
  try {
    characters = manualForm.characters
      .filter((character) => character.name.trim())
      .map((character) => ({
        name: character.name.trim(),
        role: character.role.trim(),
        description: character.description,
        personality: character.personality,
        appearance: parseAppearance(character.appearanceText),
      }));
  } catch (error) {
    ElMessage.warning(error instanceof Error ? error.message : '角色外观 JSON 格式不正确');
    return;
  }

  isManualSaving.value = true;
  try {
    await storyStore.updateStoryDetail(story.value.id, {
      synopsis: manualForm.synopsis,
      fullContent: manualForm.fullContent,
      characters,
    });
    ElMessage.success('剧情大纲和角色设定已保存');
    manualEditDialogVisible.value = false;
  } finally {
    isManualSaving.value = false;
  }
}

function parseAppearance(value: string) {
  const text = value.trim();
  if (!text) {
    return undefined;
  }
  const parsed = JSON.parse(text) as unknown;
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('角色外观必须是 JSON 对象');
  }
  return parsed as Record<string, unknown>;
}

function openReviseDialog() {
  reviseSuggestion.value = '';
  reviseDialogVisible.value = true;
}

async function submitOutlineRevision() {
  if (!story.value) {
    return;
  }

  const suggestion = reviseSuggestion.value.trim();
  if (!suggestion) {
    ElMessage.warning('请输入大纲修改意见');
    return;
  }

  isRevising.value = true;
  try {
    await storyStore.reviseStoryOutline(story.value.id, { suggestion });
    ElMessage.success('大纲修改任务已提交，生成完成后会自动刷新');
    reviseDialogVisible.value = false;
    startStoryPolling(story.value.id);
  } finally {
    isRevising.value = false;
  }
}

async function generateVolumeOutline() {
  if (!story.value) {
    return;
  }
  if (!story.value.fullContent) {
    ElMessage.warning('请先生成或填写剧情大纲');
    return;
  }
  await storyStore.generateVolumeOutline(story.value.id);
  ElMessage.success('分卷大纲生成任务已提交，完成后会自动刷新');
  startStoryPolling(story.value.id);
}

async function generateVolumeSections(volumeId: number) {
  if (!story.value) {
    return;
  }

  await storyStore.generateVolumeSections(story.value.id, volumeId);
  ElMessage.success('分卷小节故事生成任务已提交，完成后会自动刷新');
  startStoryPolling(story.value.id);
}

async function generateSectionAssets(sectionId: number) {
  if (!story.value) {
    return;
  }

  await storyStore.generateSectionAssets(story.value.id, sectionId);
  ElMessage.success('小节人物/场景图片生成任务已提交');
  startStoryPolling(story.value.id);
}

async function generateSectionScript(sectionId: number) {
  if (!story.value) {
    return;
  }

  await storyStore.generateSectionScript(story.value.id, sectionId);
  ElMessage.success('故事脚本生成任务已提交，完成后会自动刷新');
  startStoryPolling(story.value.id);
}

function formatDuration(seconds?: number) {
  const normalizedSeconds = Number(seconds) || 0;
  if (normalizedSeconds <= 0) {
    return '待定';
  }
  const minutes = Math.floor(normalizedSeconds / 60);
  const restSeconds = normalizedSeconds % 60;
  if (minutes <= 0) {
    return `${restSeconds}秒`;
  }
  return restSeconds > 0 ? `${minutes}分${restSeconds}秒` : `${minutes}分钟`;
}

function assetTypeLabel(assetType?: string) {
  if (assetType === 'CHARACTER') {
    return '人物';
  }
  if (assetType === 'SCENE') {
    return '场景';
  }
  return assetType || '资源';
}

function resolveAssetImageUrl(asset: StoryAsset) {
  if (asset.imageUrl) {
    return asset.imageUrl;
  }
  if (!asset.imagePath) {
    return '';
  }
  return asset.imagePath.startsWith('/api') ? asset.imagePath : `/api/files/${asset.imagePath.replace(/^\/+/, '')}`;
}

function beforeAssetAudioUpload(file: UploadRawFile) {
  if (!file.type.startsWith('audio/')) {
    ElMessage.error('请上传音频文件');
    return false;
  }
  return true;
}

async function uploadAssetAudio(assetId: number, options: UploadRequestOptions) {
  if (!story.value) {
    return;
  }

  await storyStore.uploadCharacterAudio(story.value.id, assetId, options.file);
  ElMessage.success('人物音频已保存');
}

function createAssetAudioUploader(assetId: number) {
  return (options: UploadRequestOptions) => uploadAssetAudio(assetId, options);
}

function openVolumeReviseDialog() {
  if (!hasVolumeOutlines.value) {
    ElMessage.warning('请先生成分卷大纲');
    return;
  }
  volumeReviseSuggestion.value = '';
  volumeReviseDialogVisible.value = true;
}

async function submitVolumeRevision() {
  if (!story.value) {
    return;
  }

  const suggestion = volumeReviseSuggestion.value.trim();
  if (!suggestion) {
    ElMessage.warning('请输入分卷大纲修改意见');
    return;
  }

  await storyStore.reviseVolumeOutline(story.value.id, { suggestion });
  ElMessage.success('分卷大纲自动修改任务已提交，完成后会自动刷新');
  volumeReviseDialogVisible.value = false;
  startStoryPolling(story.value.id);
}

function openVolumeManualEditDialog() {
  if (!story.value || !hasVolumeOutlines.value) {
    ElMessage.warning('请先生成分卷大纲');
    return;
  }

  volumeManualForm.volumes = story.value.volumeOutlines.map((volume, index) => ({
    volumeNumber: volume.volumeNumber || index + 1,
    title: volume.title || '',
    summary: volume.summary || '',
    content: volume.content || '',
    endingHook: volume.endingHook || '',
  }));
  volumeManualDialogVisible.value = true;
}

function addManualVolume() {
  volumeManualForm.volumes.push({
    volumeNumber: volumeManualForm.volumes.length + 1,
    title: '',
    summary: '',
    content: '',
    endingHook: '',
  });
}

function removeManualVolume(index: number) {
  volumeManualForm.volumes.splice(index, 1);
  volumeManualForm.volumes.forEach((volume, volumeIndex) => {
    if (!volume.volumeNumber) {
      volume.volumeNumber = volumeIndex + 1;
    }
  });
}

async function saveManualVolumeOutlines() {
  if (!story.value) {
    return;
  }
  if (volumeManualForm.volumes.length === 0) {
    ElMessage.warning('请至少保留一个分卷');
    return;
  }

  const volumes: StoryVolumeOutlineUpdateItem[] = volumeManualForm.volumes.map((volume, index) => ({
    volumeNumber: Number(volume.volumeNumber) || index + 1,
    title: volume.title.trim(),
    summary: volume.summary,
    content: volume.content,
    endingHook: volume.endingHook,
  }));
  if (volumes.some((volume) => !volume.title)) {
    ElMessage.warning('每个分卷都需要填写卷名');
    return;
  }

  await storyStore.updateVolumeOutlines(story.value.id, { volumes });
  ElMessage.success('分卷大纲已手动保存');
  volumeManualDialogVisible.value = false;
}

async function confirmDelete() {
  if (!story.value) {
    return;
  }

  try {
    await ElMessageBox.confirm('删除后该漫剧不可恢复，确定继续吗？', '删除漫剧', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    });
  } catch {
    return;
  }

  await storyStore.deleteStory(story.value.id);
  ElMessage.success('漫剧已删除');
  router.push('/stories');
}

function statusLabel(status?: string) {
  if (status === 'generating') {
    return '生成中';
  }
  if (status === 'revising') {
    return '修改中';
  }
  if (status === 'volume_pending') {
    return '分卷处理中';
  }
  if (status === 'volume_story_pending') {
    return '分卷正文生成中';
  }
  if (status === 'volume_section_pending') {
    return '分卷小节生成中';
  }
  if (status === 'section_asset_pending') {
    return '小节图片生成中';
  }
  if (status === 'section_script_pending') {
    return '故事脚本生成中';
  }
  if (status === 'failed') {
    return '生成失败';
  }
  if (status === 'published') {
    return '已发布';
  }
  if (status === 'archived') {
    return '已归档';
  }
  return '草稿';
}

function startStoryPolling(storyId: number) {
  stopStoryPolling();
  storyPollingTimer = window.setInterval(async () => {
    const latestStory = await storyStore.refreshStoryDetail(storyId);
    syncSelectedVolume();
    if (!isProcessingStatus(latestStory.status)) {
      stopStoryPolling();
      if (latestStory.status === 'failed') {
        ElMessage.error('AI 任务执行失败，请稍后重试或查看 Python 控制台日志');
      } else {
        ElMessage.success('AI 任务已完成，页面已刷新');
      }
    }
  }, 5000);
}

function stopStoryPolling() {
  if (storyPollingTimer) {
    window.clearInterval(storyPollingTimer);
    storyPollingTimer = undefined;
  }
}

function isProcessingStatus(status?: string) {
  return status === 'generating' || status === 'revising' || status === 'volume_pending' || status === 'volume_story_pending' || status === 'volume_section_pending' || status === 'section_asset_pending' || status === 'section_script_pending';
}

function syncSelectedVolume() {
  const volumes = story.value?.volumeOutlines || [];
  if (volumes.length === 0) {
    selectedVolumeNumber.value = undefined;
    return;
  }
  const stillExists = volumes.some((volume) => volume.volumeNumber === selectedVolumeNumber.value);
  if (!stillExists) {
    selectedVolumeNumber.value = volumes[0].volumeNumber;
  }
}
</script>

<style scoped lang="scss">
.detail-page {
  display: grid;
  gap: 20px;
}

.detail-hero,
.summary-card,
.panel {
  border: 1px solid rgba(23, 37, 84, 0.1);
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.1);
}

.detail-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding: 34px;
  background:
    radial-gradient(circle at top right, rgba(29, 78, 216, 0.16), transparent 24rem),
    linear-gradient(135deg, rgba(255, 247, 237, 0.95), rgba(240, 249, 255, 0.92));
}

.eyebrow {
  margin: 0 0 12px;
  color: #1d4ed8;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 14px;
  color: #172554;
  font-size: clamp(34px, 6vw, 64px);
}

h2,
h3 {
  margin: 0;
  color: #172554;
}

.tag-row,
.hero-actions,
.section-heading,
.manual-characters-header,
.character-edit-title {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.hero-actions {
  justify-content: flex-end;
}

.volume-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.volume-filter {
  width: 160px;
}

.section-heading,
.manual-characters-header,
.character-edit-title {
  align-items: center;
  justify-content: space-between;
}

.summary-card,
.panel {
  padding: 24px;
}

.summary-card p,
.script-text {
  color: #475569;
  line-height: 1.8;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(320px, 0.95fr);
  gap: 20px;
}

.script-text {
  margin: 16px 0 0;
  white-space: pre-wrap;
}

.character-grid,
.manual-character-list,
.manual-volume-list {
  display: grid;
  gap: 14px;
  margin-top: 16px;
}

.character-edit-grid,
.volume-edit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.volume-panel {
  background:
    radial-gradient(circle at top left, rgba(16, 185, 129, 0.12), transparent 22rem),
    rgba(255, 255, 255, 0.88);
}

.volume-list {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.volume-card {
  padding: 18px;
  border: 1px solid rgba(16, 185, 129, 0.16);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.82);
}

.volume-section-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.volume-section-card {
  padding: 14px;
  border: 1px solid rgba(29, 78, 216, 0.14);
  border-radius: 18px;
  background: rgba(240, 249, 255, 0.72);
}

.section-assets {
  margin-top: 16px;
}

.section-script-board {
  display: grid;
  gap: 12px;
  margin-top: 16px;
  padding: 14px;
  border: 1px solid rgba(22, 163, 74, 0.18);
  border-radius: 16px;
  background:
    radial-gradient(circle at top right, rgba(187, 247, 208, 0.7), transparent 18rem),
    rgba(240, 253, 244, 0.72);
}

.section-script-header,
.script-shot-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.section-script-header {
  justify-content: space-between;
  color: #166534;
  font-weight: 800;
}

.section-script-header h5 {
  margin: 0;
  color: #14532d;
}

.script-shot-list {
  display: grid;
  gap: 10px;
}

.script-shot-card {
  padding: 12px;
  border: 1px solid rgba(20, 83, 45, 0.1);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
}

.script-shot-meta {
  color: #166534;
  font-size: 13px;
  font-weight: 800;
}

.script-shot-action,
.script-shot-dialogue {
  margin: 8px 0 0;
  color: #334155;
  line-height: 1.7;
}

.script-shot-dialogue {
  color: #0f766e;
  font-weight: 700;
}

.section-assets h5 {
  margin: 0 0 10px;
  color: #0f172a;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 12px;
}

.asset-card {
  overflow: hidden;
  border: 1px solid rgba(15, 118, 110, 0.16);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
}

.asset-image {
  display: grid;
  min-height: 140px;
  place-items: center;
  background: linear-gradient(135deg, rgba(204, 251, 241, 0.72), rgba(219, 234, 254, 0.72));
  color: #64748b;
  font-size: 13px;
}

.asset-image img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  display: block;
}

.asset-body {
  display: grid;
  gap: 8px;
  padding: 12px;
}

.asset-body h6 {
  margin: 0;
  font-size: 15px;
  color: #0f172a;
}

.asset-body p {
  margin: 0;
  color: #475569;
  line-height: 1.6;
}

.asset-body audio {
  width: 100%;
}

.volume-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.volume-summary,
.ending-hook {
  margin: 12px 0 0;
  color: #0f766e;
  line-height: 1.7;
  font-weight: 700;
}

.ending-hook {
  color: #b45309;
}

.field-hint {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 900px) {
  .detail-hero,
  .content-grid,
  .character-edit-grid,
  .volume-edit-grid {
    grid-template-columns: 1fr;
  }

  .detail-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-actions {
    justify-content: flex-start;
  }

  .volume-toolbar,
  .volume-filter {
    width: 100%;
  }
}
</style>
