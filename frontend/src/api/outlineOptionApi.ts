import request from './index';
import type { ApiResponse } from '../types/auth';
import type {
  StoryOutlineOption,
  StoryOutlineOptionRequest,
  StoryOutlineOptionType,
} from '../types/outlineOption';

function unwrap<T>(response: ApiResponse<T>): T {
  return response.data;
}

export async function getOutlineOptions(type?: StoryOutlineOptionType, enabled?: boolean) {
  const response = await request.get<ApiResponse<StoryOutlineOption[]>>('/api/story-outline-options', {
    params: {
      type,
      enabled,
    },
  });
  return unwrap(response.data);
}

export async function createOutlineOption(data: StoryOutlineOptionRequest) {
  const response = await request.post<ApiResponse<StoryOutlineOption>>('/api/story-outline-options', data);
  return unwrap(response.data);
}

export async function updateOutlineOption(id: number, data: StoryOutlineOptionRequest) {
  const response = await request.put<ApiResponse<StoryOutlineOption>>(`/api/story-outline-options/${id}`, data);
  return unwrap(response.data);
}

export async function deleteOutlineOption(id: number) {
  await request.delete<ApiResponse<null>>(`/api/story-outline-options/${id}`);
}
