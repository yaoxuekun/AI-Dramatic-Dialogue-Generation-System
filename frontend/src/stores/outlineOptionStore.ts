import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import * as outlineOptionApi from '../api/outlineOptionApi';
import type {
  StoryOutlineOption,
  StoryOutlineOptionRequest,
  StoryOutlineOptionType,
} from '../types/outlineOption';

export const useOutlineOptionStore = defineStore('outlineOption', () => {
  const options = ref<StoryOutlineOption[]>([]);
  const enabledOptions = ref<StoryOutlineOption[]>([]);
  const isLoading = ref(false);
  const isSaving = ref(false);

  const genreOptions = computed(() => enabledOptions.value.filter((option) => option.type === 'GENRE'));
  const styleOptions = computed(() => enabledOptions.value.filter((option) => option.type === 'STYLE'));

  async function fetchOptions(type?: StoryOutlineOptionType, enabled?: boolean) {
    isLoading.value = true;
    try {
      const result = await outlineOptionApi.getOutlineOptions(type, enabled);
      if (enabled === true) {
        enabledOptions.value = mergeOptions(enabledOptions.value, result, type);
      } else {
        options.value = result;
      }
      return result;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchEnabledOptions() {
    isLoading.value = true;
    try {
      enabledOptions.value = await outlineOptionApi.getOutlineOptions(undefined, true);
      return enabledOptions.value;
    } finally {
      isLoading.value = false;
    }
  }

  async function createOption(payload: StoryOutlineOptionRequest) {
    isSaving.value = true;
    try {
      const option = await outlineOptionApi.createOutlineOption(payload);
      await refreshAfterMutation(payload.type);
      return option;
    } finally {
      isSaving.value = false;
    }
  }

  async function updateOption(id: number, payload: StoryOutlineOptionRequest) {
    isSaving.value = true;
    try {
      const option = await outlineOptionApi.updateOutlineOption(id, payload);
      await refreshAfterMutation(payload.type);
      return option;
    } finally {
      isSaving.value = false;
    }
  }

  async function deleteOption(id: number, type: StoryOutlineOptionType) {
    isSaving.value = true;
    try {
      await outlineOptionApi.deleteOutlineOption(id);
      await refreshAfterMutation(type);
    } finally {
      isSaving.value = false;
    }
  }

  async function refreshAfterMutation(type: StoryOutlineOptionType) {
    await Promise.all([
      fetchOptions(type),
      fetchEnabledOptions(),
    ]);
  }

  function mergeOptions(
    current: StoryOutlineOption[],
    incoming: StoryOutlineOption[],
    type?: StoryOutlineOptionType,
  ) {
    if (!type) {
      return incoming;
    }
    return [
      ...current.filter((option) => option.type !== type),
      ...incoming,
    ];
  }

  return {
    options,
    enabledOptions,
    genreOptions,
    styleOptions,
    isLoading,
    isSaving,
    fetchOptions,
    fetchEnabledOptions,
    createOption,
    updateOption,
    deleteOption,
  };
});
