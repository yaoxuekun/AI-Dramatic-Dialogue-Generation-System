import { ref } from 'vue';
import { defineStore } from 'pinia';
import * as promptApi from '../api/promptApi';
import type { AiPrompt, AiPromptRequest } from '../types/prompt';

export const usePromptStore = defineStore('prompt', () => {
  const prompts = ref<AiPrompt[]>([]);
  const currentPrompt = ref<AiPrompt | null>(null);
  const isLoading = ref(false);
  const isSaving = ref(false);

  async function fetchPrompts(params?: { category?: string; enabled?: boolean; keyword?: string }) {
    isLoading.value = true;
    try {
      prompts.value = await promptApi.getPrompts(params);
      return prompts.value;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchPrompt(id: number) {
    isLoading.value = true;
    try {
      currentPrompt.value = await promptApi.getPrompt(id);
      return currentPrompt.value;
    } finally {
      isLoading.value = false;
    }
  }

  async function createPrompt(payload: AiPromptRequest) {
    isSaving.value = true;
    try {
      const prompt = await promptApi.createPrompt(payload);
      upsertPrompt(prompt);
      currentPrompt.value = prompt;
      return prompt;
    } finally {
      isSaving.value = false;
    }
  }

  async function updatePrompt(id: number, payload: AiPromptRequest) {
    isSaving.value = true;
    try {
      const prompt = await promptApi.updatePrompt(id, payload);
      upsertPrompt(prompt);
      currentPrompt.value = prompt;
      return prompt;
    } finally {
      isSaving.value = false;
    }
  }

  async function deletePrompt(id: number) {
    isSaving.value = true;
    try {
      await promptApi.deletePrompt(id);
      prompts.value = prompts.value.filter((prompt) => prompt.id !== id);
      if (currentPrompt.value?.id === id) {
        currentPrompt.value = null;
      }
    } finally {
      isSaving.value = false;
    }
  }

  function upsertPrompt(prompt: AiPrompt) {
    prompts.value = [
      prompt,
      ...prompts.value.filter((item) => item.id !== prompt.id),
    ].sort((left, right) => `${left.category || ''}${left.promptKey}`.localeCompare(`${right.category || ''}${right.promptKey}`));
  }

  return {
    prompts,
    currentPrompt,
    isLoading,
    isSaving,
    fetchPrompts,
    fetchPrompt,
    createPrompt,
    updatePrompt,
    deletePrompt,
  };
});
