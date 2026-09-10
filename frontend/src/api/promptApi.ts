import request from './index';
import type { ApiResponse } from '../types/auth';
import type { AiPrompt, AiPromptRequest } from '../types/prompt';

const PROMPT_MANAGE_TIMEOUT = 60000;

function unwrap<T>(response: ApiResponse<T>): T {
  return response.data;
}

export async function getPrompts(params?: { category?: string; enabled?: boolean; keyword?: string }) {
  const response = await request.get<ApiResponse<AiPrompt[]>>('/api/prompts', {
    params,
    timeout: PROMPT_MANAGE_TIMEOUT,
  });
  return unwrap(response.data);
}

export async function getPrompt(id: number) {
  const response = await request.get<ApiResponse<AiPrompt>>(`/api/prompts/${id}`, {
    timeout: PROMPT_MANAGE_TIMEOUT,
  });
  return unwrap(response.data);
}

export async function createPrompt(data: AiPromptRequest) {
  const response = await request.post<ApiResponse<AiPrompt>>('/api/prompts', data, {
    timeout: PROMPT_MANAGE_TIMEOUT,
  });
  return unwrap(response.data);
}

export async function updatePrompt(id: number, data: AiPromptRequest) {
  const response = await request.put<ApiResponse<AiPrompt>>(`/api/prompts/${id}`, data, {
    timeout: PROMPT_MANAGE_TIMEOUT,
  });
  return unwrap(response.data);
}

export async function deletePrompt(id: number) {
  await request.delete<ApiResponse<null>>(`/api/prompts/${id}`, {
    timeout: PROMPT_MANAGE_TIMEOUT,
  });
}
