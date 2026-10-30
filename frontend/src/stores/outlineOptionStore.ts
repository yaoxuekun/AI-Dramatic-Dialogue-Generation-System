import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import * as outlineOptionApi from '../api/outlineOptionApi';
import type {
  StoryOutlineOption,
  StoryOutlineOptionRequest,
  StoryOutlineOptionType,
} from '../types/outlineOption';

const OPTION_TYPES: StoryOutlineOptionType[] = ['GENRE', 'STYLE'];

function emptyOptionMap(): Record<StoryOutlineOptionType, StoryOutlineOption[]> {
  return { GENRE: [], STYLE: [] };
}

export const useOutlineOptionStore = defineStore('outlineOption', () => {
  /** 按类型分表缓存，题材与漫剧风格互不覆盖 */
  const optionsByType = ref<Record<StoryOutlineOptionType, StoryOutlineOption[]>>(emptyOptionMap());
  const enabledOptions = ref<StoryOutlineOption[]>([]);
  const isLoading = ref(false);
  const isSaving = ref(false);

  /** 当前管理页正在查看的类型，用于让 options 这个单值出口跟随页签 */
  const activeType = ref<StoryOutlineOptionType>('GENRE');

  /** 兼容旧用法：返回当前激活类型的列表 */
  const options = computed(() => optionsByType.value[activeType.value] ?? []);

  const genreOptions = computed(() => enabledOptions.value.filter((option) => option.type === 'GENRE'));
  const styleOptions = computed(() => enabledOptions.value.filter((option) => option.type === 'STYLE'));

  /** 请求序号，防止切页签时慢请求覆盖新数据 */
  let requestSeq = 0;

  function setActiveType(type: StoryOutlineOptionType) {
    activeType.value = type;
  }

  function getOptions(type: StoryOutlineOptionType) {
    return optionsByType.value[type] ?? [];
  }

  async function fetchOptions(type?: StoryOutlineOptionType, enabled?: boolean) {
    const seq = ++requestSeq;
    isLoading.value = true;
    try {
      const result = await outlineOptionApi.getOutlineOptions(type, enabled);

      // 已有更新的请求发出，本次结果直接丢弃
      if (seq !== requestSeq) {
        return result;
      }

      if (enabled === true) {
        enabledOptions.value = mergeOptions(enabledOptions.value, result, type);
      } else if (type) {
        optionsByType.value = { ...optionsByType.value, [type]: result };
      } else {
        // 未指定类型时按返回结果本身的 type 分桶
        const next = emptyOptionMap();
        for (const option of result) {
          if (OPTION_TYPES.includes(option.type)) {
            next[option.type].push(option);
          }
        }
        optionsByType.value = next;
      }

      return result;
    } finally {
      if (seq === requestSeq) {
        isLoading.value = false;
      }
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
    optionsByType,
    enabledOptions,
    genreOptions,
    styleOptions,
    activeType,
    isLoading,
    isSaving,
    setActiveType,
    getOptions,
    fetchOptions,
    fetchEnabledOptions,
    createOption,
    updateOption,
    deleteOption,
  };
});
