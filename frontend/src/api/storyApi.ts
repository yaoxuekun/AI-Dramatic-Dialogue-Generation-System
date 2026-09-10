import request from './index';
import type { ApiResponse } from '../types/auth';
import type {
  StoryDetailResponse,
  StoryDetailUpdateRequest,
  StoryGenerateRequest,
  StoryOutlineReviseRequest,
  StoryPageResponse,
  StoryResponse,
  StoryUpdateRequest,
  StoryVolumeOutlineReviseRequest,
  StoryVolumeOutlineUpdateRequest,
} from '../types/story';

function unwrap<T>(response: ApiResponse<T>): T {
  return response.data;
}

export async function getStories(page = 1, size = 10) {
  const response = await request.get<ApiResponse<StoryPageResponse>>('/api/story/list', {
    params: {
      page,
      size,
    },
  });
  return unwrap(response.data);
}

export async function getStoryDetail(id: number) {
  const response = await request.get<ApiResponse<StoryDetailResponse>>(`/api/story/${id}`);
  return unwrap(response.data);
}

export async function generateStory(data: StoryGenerateRequest) {
  const response = await request.post<ApiResponse<StoryResponse>>('/api/story/generate', data);
  return unwrap(response.data);
}

export async function updateStory(id: number, data: StoryUpdateRequest) {
  const response = await request.put<ApiResponse<StoryResponse>>(`/api/story/${id}`, data);
  return unwrap(response.data);
}

export async function updateStoryDetail(id: number, data: StoryDetailUpdateRequest) {
  const response = await request.put<ApiResponse<StoryDetailResponse>>(`/api/story/${id}/detail`, data);
  return unwrap(response.data);
}

export async function reviseStoryOutline(id: number, data: StoryOutlineReviseRequest) {
  const response = await request.post<ApiResponse<StoryDetailResponse>>(`/api/story/${id}/outline/revise`, data);
  return unwrap(response.data);
}

export async function generateVolumeOutline(id: number) {
  const response = await request.post<ApiResponse<StoryDetailResponse>>(`/api/story/${id}/volume-outline/generate`);
  return unwrap(response.data);
}

export async function reviseVolumeOutline(id: number, data: StoryVolumeOutlineReviseRequest) {
  const response = await request.post<ApiResponse<StoryDetailResponse>>(`/api/story/${id}/volume-outline/revise`, data);
  return unwrap(response.data);
}

export async function generateVolumeSections(id: number, volumeId: number) {
  const response = await request.post<ApiResponse<StoryDetailResponse>>(`/api/story/${id}/volume-outline/${volumeId}/sections/generate`);
  return unwrap(response.data);
}

export async function generateSectionAssets(id: number, sectionId: number) {
  const response = await request.post<ApiResponse<StoryDetailResponse>>(`/api/story/${id}/volume-sections/${sectionId}/assets/generate`);
  return unwrap(response.data);
}

export async function generateSectionScript(id: number, sectionId: number) {
  const response = await request.post<ApiResponse<StoryDetailResponse>>(`/api/story/${id}/volume-sections/${sectionId}/script/generate`);
  return unwrap(response.data);
}

export async function uploadCharacterAudio(id: number, assetId: number, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await request.post<ApiResponse<StoryDetailResponse>>(`/api/story/${id}/assets/${assetId}/audio`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return unwrap(response.data);
}

export async function updateVolumeOutlines(id: number, data: StoryVolumeOutlineUpdateRequest) {
  const response = await request.put<ApiResponse<StoryDetailResponse>>(`/api/story/${id}/volume-outline`, data);
  return unwrap(response.data);
}

export async function deleteStory(id: number) {
  await request.delete<ApiResponse<null>>(`/api/story/${id}`);
}
