import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import * as storyApi from '../api/storyApi';
import type {
  StoryDetailResponse,
  StoryDetailUpdateRequest,
  StoryGenerateRequest,
  StoryOutlineReviseRequest,
  StoryResponse,
  StoryUpdateRequest,
  StoryVolumeOutlineReviseRequest,
  StoryVolumeOutlineUpdateRequest,
} from '../types/story';

const DEFAULT_PAGE_SIZE = 10;

export const useStoryStore = defineStore('story', () => {
  const stories = ref<StoryResponse[]>([]);
  const currentStory = ref<StoryDetailResponse | null>(null);
  const isLoading = ref(false);
  const isGenerating = ref(false);
  const isGeneratingVolumeOutline = ref(false);
  const isRevisingVolumeOutline = ref(false);
  const generatingVolumeSectionsVolumeId = ref<number | null>(null);
  const generatingSectionAssetsSectionId = ref<number | null>(null);
  const generatingSectionScriptSectionId = ref<number | null>(null);
  const isSavingVolumeOutline = ref(false);
  const uploadingAssetAudioId = ref<number | null>(null);
  const pagination = ref({
    current: 1,
    size: DEFAULT_PAGE_SIZE,
    total: 0,
    pages: 0,
  });

  const hasStories = computed(() => stories.value.length > 0);

  async function fetchStories(page = pagination.value.current, size = pagination.value.size) {
    isLoading.value = true;
    try {
      const result = await storyApi.getStories(page, size);
      stories.value = Array.isArray(result.records) ? result.records : [];
      pagination.value = {
        current: Number(result.current) || page,
        size: Number(result.size) || size,
        total: Number(result.total) || 0,
        pages: Number(result.pages) || 0,
      };
      return stories.value;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchStoryDetail(id: number) {
    isLoading.value = true;
    try {
      return await refreshStoryDetail(id);
    } finally {
      isLoading.value = false;
    }
  }

  async function refreshStoryDetail(id: number) {
    currentStory.value = await storyApi.getStoryDetail(id);
    upsertStory(currentStory.value);
    return currentStory.value;
  }

  async function generateStory(payload: StoryGenerateRequest) {
    isGenerating.value = true;
    try {
      const story = await storyApi.generateStory(payload);
      upsertStory(story);
      return story;
    } finally {
      isGenerating.value = false;
    }
  }

  async function updateStory(id: number, data: StoryUpdateRequest) {
    const story = await storyApi.updateStory(id, data);
    upsertStory(story);
    if (currentStory.value?.id === id) {
      currentStory.value = {
        ...currentStory.value,
        ...story,
      };
    }
    return story;
  }

  async function updateStoryDetail(id: number, data: StoryDetailUpdateRequest) {
    isLoading.value = true;
    try {
      const story = await storyApi.updateStoryDetail(id, data);
      currentStory.value = story;
      upsertStory(story);
      return story;
    } finally {
      isLoading.value = false;
    }
  }

  async function reviseStoryOutline(id: number, data: StoryOutlineReviseRequest) {
    isLoading.value = true;
    try {
      const story = await storyApi.reviseStoryOutline(id, data);
      currentStory.value = story;
      upsertStory(story);
      return story;
    } finally {
      isLoading.value = false;
    }
  }

  async function generateVolumeOutline(id: number) {
    isGeneratingVolumeOutline.value = true;
    try {
      const story = await storyApi.generateVolumeOutline(id);
      currentStory.value = story;
      upsertStory(story);
      return story;
    } finally {
      isGeneratingVolumeOutline.value = false;
    }
  }

  async function reviseVolumeOutline(id: number, data: StoryVolumeOutlineReviseRequest) {
    isRevisingVolumeOutline.value = true;
    try {
      const story = await storyApi.reviseVolumeOutline(id, data);
      currentStory.value = story;
      upsertStory(story);
      return story;
    } finally {
      isRevisingVolumeOutline.value = false;
    }
  }

  async function generateVolumeSections(id: number, volumeId: number) {
    generatingVolumeSectionsVolumeId.value = volumeId;
    try {
      const story = await storyApi.generateVolumeSections(id, volumeId);
      currentStory.value = story;
      upsertStory(story);
      return story;
    } finally {
      generatingVolumeSectionsVolumeId.value = null;
    }
  }

  async function generateSectionAssets(id: number, sectionId: number) {
    generatingSectionAssetsSectionId.value = sectionId;
    try {
      const story = await storyApi.generateSectionAssets(id, sectionId);
      currentStory.value = story;
      upsertStory(story);
      return story;
    } finally {
      generatingSectionAssetsSectionId.value = null;
    }
  }

  async function generateSectionScript(id: number, sectionId: number) {
    generatingSectionScriptSectionId.value = sectionId;
    try {
      const story = await storyApi.generateSectionScript(id, sectionId);
      currentStory.value = story;
      upsertStory(story);
      return story;
    } finally {
      generatingSectionScriptSectionId.value = null;
    }
  }

  async function uploadCharacterAudio(id: number, assetId: number, file: File) {
    uploadingAssetAudioId.value = assetId;
    try {
      const story = await storyApi.uploadCharacterAudio(id, assetId, file);
      currentStory.value = story;
      upsertStory(story);
      return story;
    } finally {
      uploadingAssetAudioId.value = null;
    }
  }

  async function updateVolumeOutlines(id: number, data: StoryVolumeOutlineUpdateRequest) {
    isSavingVolumeOutline.value = true;
    try {
      const story = await storyApi.updateVolumeOutlines(id, data);
      currentStory.value = story;
      upsertStory(story);
      return story;
    } finally {
      isSavingVolumeOutline.value = false;
    }
  }

  async function deleteStory(id: number) {
    await storyApi.deleteStory(id);
    stories.value = stories.value.filter((story) => story.id !== id);
    if (currentStory.value?.id === id) {
      currentStory.value = null;
    }
    pagination.value.total = Math.max(0, pagination.value.total - 1);
  }

  function upsertStory(story: StoryResponse) {
    stories.value = [
      story,
      ...stories.value.filter((item) => item.id !== story.id),
    ];
  }

  return {
    stories,
    currentStory,
    pagination,
    isLoading,
    isGenerating,
    isGeneratingVolumeOutline,
    isRevisingVolumeOutline,
    generatingVolumeSectionsVolumeId,
    generatingSectionAssetsSectionId,
    generatingSectionScriptSectionId,
    isSavingVolumeOutline,
    uploadingAssetAudioId,
    hasStories,
    fetchStories,
    fetchStoryDetail,
    refreshStoryDetail,
    generateStory,
    updateStory,
    updateStoryDetail,
    reviseStoryOutline,
    generateVolumeOutline,
    reviseVolumeOutline,
    generateVolumeSections,
    generateSectionAssets,
    generateSectionScript,
    uploadCharacterAudio,
    updateVolumeOutlines,
    deleteStory,
  };
});
