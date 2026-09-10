import request from './index';
import type { ApiResponse } from '../types/auth';
import type { ChatSessionResponse, ChatStartRequest, MessageResponse } from '../types/chat';

const CHAT_MESSAGE_TIMEOUT = 0;

function unwrap<T>(response: ApiResponse<T>): T {
  return response.data;
}

export async function startSession(data: ChatStartRequest) {
  const response = await request.post<ApiResponse<ChatSessionResponse>>('/api/chat/start', data);
  return unwrap(response.data);
}

export async function sendMessage(sessionId: number, content: string) {
  const response = await request.post<ApiResponse<MessageResponse>>(
    '/api/chat/message',
    { sessionId, content },
    {
      // Chat replies may wait for a slow LLM call; keep the HTTP request open until the backend responds.
      timeout: CHAT_MESSAGE_TIMEOUT,
    },
  );
  return unwrap(response.data);
}

export async function getHistory(sessionId: number) {
  const response = await request.get<ApiResponse<MessageResponse[]>>(`/api/chat/history/${sessionId}`);
  return unwrap(response.data);
}

export async function getSessions() {
  const response = await request.get<ApiResponse<ChatSessionResponse[]>>('/api/chat/sessions');
  return unwrap(response.data);
}

export async function deleteSession(sessionId: number) {
  await request.delete<ApiResponse<null>>(`/api/chat/session/${sessionId}`);
}
