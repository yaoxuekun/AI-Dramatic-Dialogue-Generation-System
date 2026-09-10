import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import { Client, type IMessage, type StompSubscription } from '@stomp/stompjs';
import * as chatApi from '../api/chatApi';
import type { ApiResponse } from '../types/auth';
import type { ChatSessionResponse, ChatStartRequest, MessageResponse } from '../types/chat';

export const useChatStore = defineStore('chat', () => {
  const currentSessionId = ref<number | null>(null);
  const sessions = ref<ChatSessionResponse[]>([]);
  const messages = ref<MessageResponse[]>([]);
  const isLoading = ref(false);
  const isSending = ref(false);
  const isConnected = ref(false);
  const stompClient = ref<Client | null>(null);
  const activeSubscription = ref<StompSubscription | null>(null);
  const subscribedSessionId = ref<number | null>(null);

  const currentSession = computed(() =>
    sessions.value.find((session) => session.id === currentSessionId.value) || null,
  );

  async function loadSessions() {
    const nextSessions = await chatApi.getSessions();
    sessions.value = Array.isArray(nextSessions) ? nextSessions : [];
    return sessions.value;
  }

  async function startNewSession(payload: ChatStartRequest) {
    const session = await chatApi.startSession(payload);
    upsertSession(session);
    currentSessionId.value = session.id;
    messages.value = [];
    connectWebSocket(session.id);
    return session;
  }

  async function switchSession(sessionId: number) {
    currentSessionId.value = sessionId;
    isLoading.value = true;
    try {
      const history = await chatApi.getHistory(sessionId);
      messages.value = Array.isArray(history) ? history : [];
      connectWebSocket(sessionId);
    } catch (error) {
      if (isSessionNotFoundError(error)) {
        removeLocalSession(sessionId);
      }
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function loadHistory(sessionId: number) {
    const history = await chatApi.getHistory(sessionId);
    messages.value = Array.isArray(history) ? history : [];
    return messages.value;
  }

  async function sendMessage(content: string) {
    const trimmedContent = content.trim();
    if (!trimmedContent) {
      return null;
    }

    const sessionId = currentSessionId.value;
    if (!sessionId) {
      throw new Error('请先新建对话');
    }

    const userMessage = createOptimisticUserMessage(sessionId, trimmedContent);
    messages.value.push(userMessage);
    isSending.value = true;
    try {
      const aiMessage = await chatApi.sendMessage(sessionId, trimmedContent);
      upsertMessage(aiMessage);
      await loadSessions();
      return aiMessage;
    } catch (error) {
      messages.value = messages.value.filter((message) => message.id !== userMessage.id);
      throw error;
    } finally {
      isSending.value = false;
    }
  }

  async function deleteSession(sessionId: number) {
    try {
      await chatApi.deleteSession(sessionId);
    } catch (error) {
      if (!isSessionNotFoundError(error)) {
        throw error;
      }
    }
    removeLocalSession(sessionId);
  }

  function connectWebSocket(sessionId: number) {
    const token = localStorage.getItem('token');
    if (!token) {
      return;
    }

    if (!stompClient.value) {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      stompClient.value = new Client({
        brokerURL: `${wsProtocol}//${window.location.host}/ws/chat`,
        connectHeaders: {
          Authorization: `Bearer ${token}`,
        },
        reconnectDelay: 5000,
        onConnect: () => {
          isConnected.value = true;
          subscribeSession(sessionId);
        },
        onWebSocketClose: () => {
          isConnected.value = false;
        },
        onStompError: () => {
          isConnected.value = false;
        },
      });
      stompClient.value.activate();
      return;
    }

    if (stompClient.value.connected) {
      subscribeSession(sessionId);
    }
  }

  function disconnectWebSocket() {
    activeSubscription.value?.unsubscribe();
    activeSubscription.value = null;
    subscribedSessionId.value = null;
    isConnected.value = false;
    stompClient.value?.deactivate();
    stompClient.value = null;
  }

  function subscribeSession(sessionId: number) {
    if (!stompClient.value?.connected || subscribedSessionId.value === sessionId) {
      return;
    }

    activeSubscription.value?.unsubscribe();
    activeSubscription.value = stompClient.value.subscribe(`/topic/chat/${sessionId}`, handleSocketMessage);
    subscribedSessionId.value = sessionId;
  }

  function handleSocketMessage(frame: IMessage) {
    try {
      const response = JSON.parse(frame.body) as ApiResponse<MessageResponse>;
      if (response.data && response.data.sessionId === currentSessionId.value) {
        upsertMessage(response.data);
      }
    } catch {
      // Ignore malformed socket payloads; HTTP history remains the source of truth.
    }
  }

  function upsertSession(session: ChatSessionResponse) {
    sessions.value = [
      session,
      ...sessions.value.filter((item) => item.id !== session.id),
    ];
  }

  function removeLocalSession(sessionId: number) {
    sessions.value = sessions.value.filter((session) => session.id !== sessionId);
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null;
      messages.value = [];
      disconnectWebSocket();
    }
  }

  function upsertMessage(message: MessageResponse) {
    const exists = messages.value.some((item) => item.id === message.id);
    if (!exists) {
      messages.value.push(message);
    }
  }

  function createOptimisticUserMessage(sessionId: number, content: string): MessageResponse {
    return {
      id: -Date.now(),
      sessionId,
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    };
  }

  function addLocalAiMessage(content: string, sessionId = currentSessionId.value) {
    if (!sessionId) {
      return;
    }

    messages.value.push({
      id: -Date.now(),
      sessionId,
      role: 'ai',
      content,
      createdAt: new Date().toISOString(),
    });
  }

  function isSessionNotFoundError(error: unknown) {
    if (typeof error !== 'object' || error === null) {
      return false;
    }
    const maybeAxiosError = error as { response?: { data?: { message?: string } }; message?: string };
    const message = maybeAxiosError.response?.data?.message || maybeAxiosError.message || '';
    return message.includes('Session not found');
  }

  return {
    currentSessionId,
    currentSession,
    sessions,
    messages,
    isLoading,
    isSending,
    isConnected,
    loadSessions,
    startNewSession,
    switchSession,
    loadHistory,
    sendMessage,
    deleteSession,
    connectWebSocket,
    disconnectWebSocket,
    addLocalAiMessage,
  };
});
