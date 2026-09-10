export interface ChatSessionResponse {
  id: number;
  storyId?: number;
  sessionKey: string;
  title: string;
  status: string;
  startedAt: string;
  lastActive: string;
}

export interface MessageResponse {
  id: number;
  sessionId: number;
  role: 'user' | 'ai' | string;
  content: string;
  createdAt: string;
}

export interface ChatStartRequest {
  storyId?: number;
  title?: string;
}

export interface SendMessageRequest {
  sessionId: number;
  content: string;
}
